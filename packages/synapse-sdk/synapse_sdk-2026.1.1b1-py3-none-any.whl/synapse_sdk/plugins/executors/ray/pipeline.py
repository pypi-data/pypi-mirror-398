"""Ray Pipeline executor for multi-action pipeline execution."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from synapse_sdk.plugins.context import PluginEnvironment
from synapse_sdk.plugins.enums import PackageManager
from synapse_sdk.plugins.errors import ExecutionError
from synapse_sdk.plugins.executors.ray.base import BaseRayExecutor
from synapse_sdk.plugins.pipelines.models import (
    ActionProgress,
    ActionStatus,
    PipelineProgress,
    RunStatus,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from synapse_sdk.clients.pipeline import PipelineServiceClient
    from synapse_sdk.plugins.action import BaseAction

logger = logging.getLogger(__name__)


def _serialize_paths(obj: Any) -> Any:
    """Recursively convert Path objects to strings for JSON serialization."""
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _serialize_paths(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_paths(item) for item in obj]
    return obj


@dataclass
class PipelineDefinition:
    """Definition of a pipeline to execute.

    Attributes:
        name: Pipeline name.
        actions: List of action classes or entrypoint strings.
        description: Optional description.
    """

    name: str
    actions: list[type['BaseAction'] | str]
    description: str | None = None

    def to_api_format(self) -> list[dict[str, Any]]:
        """Convert actions to API format."""
        result = []
        for action in self.actions:
            if isinstance(action, str):
                entrypoint = action
                name = action.rsplit('.', 1)[-1]
            else:
                entrypoint = f'{action.__module__}.{action.__name__}'
                name = action.action_name or action.__name__
            result.append({'name': name, 'entrypoint': entrypoint})
        return result


class RayPipelineExecutor(BaseRayExecutor):
    """Ray-based executor for multi-action pipelines.

    Submits pipelines as a single Ray actor that executes actions sequentially.
    Integrates with dev-api for progress tracking and checkpointing.

    Example:
        >>> executor = RayPipelineExecutor(
        ...     ray_address='auto',
        ...     working_dir='/path/to/plugin',
        ...     pipeline_service_url='http://localhost:8100',
        ... )
        >>> pipeline = PipelineDefinition(
        ...     name='YOLO Training',
        ...     actions=[DownloadAction, ConvertAction, TrainAction],
        ... )
        >>> run_id = executor.submit(pipeline, params={'dataset_id': 123})
        >>> progress = executor.get_progress(run_id)
        >>> result = executor.wait(run_id)
    """

    def __init__(
        self,
        env: PluginEnvironment | dict[str, Any] | None = None,
        *,
        ray_address: str = 'auto',
        runtime_env: dict[str, Any] | None = None,
        working_dir: str | Path | None = None,
        requirements_file: str | Path | None = None,
        package_manager: PackageManager | Literal['pip', 'uv'] = PackageManager.PIP,
        package_manager_options: list[str] | None = None,
        wheels_dir: str = 'wheels',
        num_cpus: int | None = None,
        num_gpus: int | None = None,
        include_sdk: bool = False,
        pipeline_service_url: str = 'http://localhost:8100',
        actor_pipeline_service_url: str | None = None,
    ) -> None:
        """Initialize Ray pipeline executor.

        Args:
            env: Environment config for actions.
            ray_address: Ray cluster address. Defaults to 'auto'.
            runtime_env: Ray runtime environment config.
            working_dir: Plugin working directory.
            requirements_file: Path to requirements.txt.
            package_manager: Package manager to use.
            package_manager_options: Additional package manager options.
            wheels_dir: Directory containing .whl files.
            num_cpus: Number of CPUs to request.
            num_gpus: Number of GPUs to request.
            include_sdk: If True, bundle local SDK with upload.
            pipeline_service_url: URL of the pipeline service API (for local SDK).
            actor_pipeline_service_url: URL for the Ray actor to reach the pipeline
                service. If None, uses pipeline_service_url. Use this when the actor
                runs on a remote cluster that needs a different URL (e.g., via VPN).
        """
        super().__init__(
            env=env,
            runtime_env=runtime_env,
            working_dir=working_dir,
            requirements_file=requirements_file,
            package_manager=package_manager,
            package_manager_options=package_manager_options,
            wheels_dir=wheels_dir,
            ray_address=ray_address,
            include_sdk=include_sdk,
        )
        self._num_cpus = num_cpus
        self._num_gpus = num_gpus
        self._pipeline_service_url = pipeline_service_url
        self._actor_pipeline_service_url = actor_pipeline_service_url or pipeline_service_url
        self._submitted_refs: dict[str, Any] = {}  # run_id -> (actor_ref, result_ref)
        self._pipeline_client: PipelineServiceClient | None = None

    @property
    def pipeline_client(self) -> 'PipelineServiceClient':
        """Get or create the pipeline service client."""
        if self._pipeline_client is None:
            from synapse_sdk.clients.pipeline import PipelineServiceClient

            self._pipeline_client = PipelineServiceClient(self._pipeline_service_url)
        return self._pipeline_client

    def submit(
        self,
        pipeline: PipelineDefinition | list[type['BaseAction'] | str],
        params: dict[str, Any],
        *,
        name: str | None = None,
        resume_from: str | None = None,
    ) -> str:
        """Submit a pipeline for execution (non-blocking).

        Args:
            pipeline: PipelineDefinition or list of action classes/entrypoints.
            params: Initial parameters for the pipeline.
            name: Pipeline name (required if pipeline is a list).
            resume_from: Run ID to resume from. If provided, the pipeline will
                skip completed actions and restore accumulated params from the
                latest checkpoint of that run.

        Returns:
            Run ID for tracking.

        Raises:
            ValueError: If pipeline is a list and name is not provided.
        """
        import ray

        self._ray_init()

        # Normalize pipeline definition
        if isinstance(pipeline, list):
            if name is None:
                name = 'pipeline'
            pipeline = PipelineDefinition(name=name, actions=pipeline)

        # Fetch resume checkpoint if resuming
        resume_checkpoint: dict[str, Any] | None = None
        if resume_from:
            resume_checkpoint = self.pipeline_client.get_latest_checkpoint(resume_from)
            if resume_checkpoint:
                logger.info(
                    f'Resuming from checkpoint: action={resume_checkpoint.get("action_name")}, '
                    f'index={resume_checkpoint.get("action_index")}'
                )
            else:
                logger.warning(f'No checkpoint found for run {resume_from}, starting fresh')

        # Register pipeline with dev-api
        api_actions = pipeline.to_api_format()
        pipeline_data = self.pipeline_client.create_pipeline(
            name=pipeline.name,
            actions=api_actions,
            description=pipeline.description,
        )
        pipeline_id = pipeline_data['id']

        # Create run
        run_data = self.pipeline_client.create_run(
            pipeline_id=pipeline_id,
            params=params,
        )
        run_id = run_data['id']

        # Convert action classes to entrypoint strings
        entrypoints = []
        for action in pipeline.actions:
            if isinstance(action, str):
                entrypoints.append(action)
            else:
                entrypoints.append(f'{action.__module__}.{action.__name__}')

        # Build remote options
        remote_options: dict[str, Any] = {'runtime_env': self._build_runtime_env()}
        if self._num_cpus is not None:
            remote_options['num_cpus'] = self._num_cpus
        if self._num_gpus is not None:
            remote_options['num_gpus'] = self._num_gpus

        # Create actor and submit pipeline
        # Use actor_pipeline_service_url for the remote actor
        PipelineActor = ray.remote(**remote_options)(_PipelineExecutorActor)
        actor = PipelineActor.remote(
            run_id=run_id,
            pipeline_id=pipeline_id,
            pipeline_service_url=self._actor_pipeline_service_url,
        )
        result_ref = actor.run_pipeline.remote(entrypoints, params, resume_checkpoint=resume_checkpoint)

        self._submitted_refs[run_id] = (actor, result_ref)
        logger.info(f'Submitted pipeline run {run_id}')

        return run_id

    def get_status(self, run_id: str) -> RunStatus:
        """Get run status from the pipeline service.

        Args:
            run_id: Run ID from submit().

        Returns:
            Current run status.
        """
        progress = self.pipeline_client.get_progress(run_id)
        return progress.status

    def get_progress(self, run_id: str) -> PipelineProgress:
        """Get detailed progress for a run.

        Args:
            run_id: Run ID from submit().

        Returns:
            PipelineProgress with current state.
        """
        return self.pipeline_client.get_progress(run_id)

    def get_result(self, run_id: str, timeout: float | None = None) -> Any:
        """Get pipeline result (blocks until complete).

        Args:
            run_id: Run ID from submit().
            timeout: Optional timeout in seconds.

        Returns:
            Final pipeline result.

        Raises:
            ExecutionError: If pipeline failed or not found.
        """
        import ray

        refs = self._submitted_refs.get(run_id)
        if refs is None:
            # Try to get from API
            run_data = self.pipeline_client.get_run(run_id)
            if run_data.get('status') == 'completed':
                return run_data.get('result')
            elif run_data.get('status') == 'failed':
                raise ExecutionError(f'Pipeline {run_id} failed: {run_data.get("error")}')
            raise ExecutionError(f'Run {run_id} not found in local cache')

        _, result_ref = refs
        try:
            return ray.get(result_ref, timeout=timeout)
        except Exception as e:
            raise ExecutionError(f'Pipeline {run_id} failed: {e}') from e

    def wait(
        self,
        run_id: str,
        timeout_seconds: float = 3600,
        poll_interval: float = 5.0,
    ) -> PipelineProgress:
        """Wait for pipeline to complete, polling for progress.

        Args:
            run_id: Run ID from submit().
            timeout_seconds: Maximum time to wait.
            poll_interval: Seconds between progress polls.

        Returns:
            Final PipelineProgress.

        Raises:
            ExecutionError: If pipeline fails or times out.
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                raise ExecutionError(f'Pipeline {run_id} timed out after {timeout_seconds}s')

            progress = self.get_progress(run_id)

            if progress.status == RunStatus.COMPLETED:
                return progress
            elif progress.status == RunStatus.FAILED:
                raise ExecutionError(f'Pipeline {run_id} failed: {progress.error}')
            elif progress.status == RunStatus.CANCELLED:
                raise ExecutionError(f'Pipeline {run_id} was cancelled')

            time.sleep(poll_interval)

    def stream_progress(
        self,
        run_id: str,
        timeout: float = 3600.0,
    ) -> 'Iterator[PipelineProgress]':
        """Stream progress updates via SSE.

        This method connects to the pipeline service's SSE endpoint and yields
        PipelineProgress objects as updates are received. More efficient than
        polling for long-running pipelines.

        Args:
            run_id: Run ID from submit().
            timeout: Maximum time to stream in seconds.

        Yields:
            PipelineProgress objects with current state.

        Raises:
            ExecutionError: If streaming fails or pipeline errors.

        Example:
            >>> run_id = executor.submit(pipeline, params)
            >>> for progress in executor.stream_progress(run_id):
            ...     print(f"Action: {progress.current_action}, Status: {progress.status}")
            ...     if progress.status == RunStatus.COMPLETED:
            ...         break
        """
        try:
            yield from self.pipeline_client.stream_progress(run_id, timeout=timeout)
        except Exception as e:
            raise ExecutionError(f'Failed to stream progress for {run_id}: {e}') from e

    async def stream_progress_async(
        self,
        run_id: str,
        timeout: float = 3600.0,
    ) -> 'AsyncIterator[PipelineProgress]':
        """Stream progress updates via SSE (async version).

        This method connects to the pipeline service's SSE endpoint and yields
        PipelineProgress objects as updates are received. More efficient than
        polling for long-running pipelines.

        Args:
            run_id: Run ID from submit().
            timeout: Maximum time to stream in seconds.

        Yields:
            PipelineProgress objects with current state.

        Raises:
            ExecutionError: If streaming fails or pipeline errors.

        Example:
            >>> run_id = executor.submit(pipeline, params)
            >>> async for progress in executor.stream_progress_async(run_id):
            ...     print(f"Action: {progress.current_action}, Status: {progress.status}")
        """
        try:
            async for progress in self.pipeline_client.stream_progress_async(run_id, timeout=timeout):
                yield progress
        except Exception as e:
            raise ExecutionError(f'Failed to stream progress for {run_id}: {e}') from e

    def cancel(self, run_id: str) -> None:
        """Cancel a running pipeline.

        Args:
            run_id: Run ID to cancel.
        """
        import ray

        refs = self._submitted_refs.get(run_id)
        if refs is not None:
            actor, result_ref = refs
            try:
                ray.kill(actor)
            except Exception as e:
                logger.warning(f'Failed to kill actor for {run_id}: {e}')

        # Update status in API
        try:
            self.pipeline_client.update_run(run_id, status='cancelled')
        except Exception as e:
            logger.warning(f'Failed to update cancelled status for {run_id}: {e}')

    def close(self) -> None:
        """Close the executor and clean up resources."""
        if self._pipeline_client is not None:
            self._pipeline_client.close()
            self._pipeline_client = None


class _PipelineLogger:
    """Logger that wraps ConsoleLogger and reports progress to pipeline service.

    Forwards progress updates to the dev-api for real-time pipeline monitoring.
    """

    def __init__(
        self,
        base_logger: Any,
        pipeline_client: Any,
        run_id: str,
        action_index: int,
        action_name: str,
    ) -> None:
        self._base = base_logger
        self._client = pipeline_client
        self._run_id = run_id
        self._action_index = action_index
        self._action_name = action_name

    def __getattr__(self, name: str) -> Any:
        # Forward all other methods to base logger
        return getattr(self._base, name)

    def set_progress(self, current: int, total: int, category: str | None = None) -> None:
        """Set progress and report to pipeline service."""
        self._base.set_progress(current, total, category)

        # Report to pipeline service
        try:
            percent = current / total if total > 0 else 0
            self._client.report_progress(
                run_id=self._run_id,
                current_action_index=self._action_index,
                action_progress=ActionProgress(
                    name=self._action_name,
                    status=ActionStatus.RUNNING,
                    progress=percent,
                    progress_category=category,
                    message=f'{current}/{total}',
                ),
            )
        except Exception as e:
            print(f'[PipelineLogger] Failed to report progress: {e}')

    def info(self, message: str) -> None:
        self._base.info(message)

    def debug(self, message: str) -> None:
        self._base.debug(message)

    def warning(self, message: str) -> None:
        self._base.warning(message)

    def error(self, message: str) -> None:
        self._base.error(message)

    def log(self, event: str, data: dict, file: str | None = None) -> None:
        self._base.log(event, data, file)


class _PipelineExecutorActor:
    """Ray Actor that executes a pipeline of actions.

    This actor runs within the Ray cluster and executes actions sequentially,
    reporting progress to the pipeline service API after each action.
    """

    def __init__(
        self,
        run_id: str,
        pipeline_id: str,
        pipeline_service_url: str,
    ) -> None:
        """Initialize the pipeline executor actor.

        Args:
            run_id: Run identifier.
            pipeline_id: Pipeline identifier.
            pipeline_service_url: URL of the pipeline service.
        """
        self._run_id = run_id
        self._pipeline_id = pipeline_id
        self._pipeline_service_url = pipeline_service_url
        self._client: Any = None

    @property
    def client(self) -> Any:
        """Get or create the pipeline service client."""
        if self._client is None:
            from synapse_sdk.clients.pipeline import PipelineServiceClient

            self._client = PipelineServiceClient(self._pipeline_service_url)
        return self._client

    def run_pipeline(
        self,
        entrypoints: list[str],
        params: dict[str, Any],
        resume_checkpoint: dict[str, Any] | None = None,
    ) -> Any:
        """Execute all actions in the pipeline sequentially.

        Args:
            entrypoints: List of action entrypoint strings.
            params: Initial parameters.
            resume_checkpoint: Checkpoint data to resume from (optional).
                If provided, actions up to and including the checkpoint's
                action_index will be skipped, and accumulated params will
                be restored from params_snapshot.

        Returns:
            Result from the final action.
        """
        import importlib
        import os
        import sys
        import traceback

        from pydantic import BaseModel

        from synapse_sdk.loggers import ConsoleLogger
        from synapse_sdk.plugins.context import PluginEnvironment, RuntimeContext
        from synapse_sdk.plugins.pipelines.context import PipelineContext
        from synapse_sdk.plugins.pipelines.models import LogEntry, LogLevel

        # Ensure working directory is in sys.path
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)

        # Create pipeline context for shared working directory
        # TODO: Pass pipeline_ctx to actions via RuntimeContext
        _pipeline_ctx = PipelineContext(
            pipeline_id=self._pipeline_id,
            run_id=self._run_id,
        )

        # Determine resume index and restore params if resuming
        resume_from_index = -1
        if resume_checkpoint:
            resume_from_index = resume_checkpoint.get('action_index', -1)
            # Restore accumulated params from checkpoint
            if resume_checkpoint.get('params_snapshot'):
                params = resume_checkpoint['params_snapshot']

        # Report pipeline started
        self.client.report_progress(
            run_id=self._run_id,
            status='running',
        )

        # Try to create BackendClient from environment
        from synapse_sdk.utils.auth import create_backend_client

        backend_client = create_backend_client()

        # Create base runtime context
        base_logger = ConsoleLogger()
        env = PluginEnvironment.from_environ()

        # Accumulated params (passed between actions)
        accumulated_params = dict(params)
        final_result = None

        try:
            for idx, entrypoint in enumerate(entrypoints):
                action_name = entrypoint.rsplit('.', 1)[-1]

                # Skip completed actions when resuming
                if idx <= resume_from_index:
                    # Report action as skipped
                    self.client.report_progress(
                        run_id=self._run_id,
                        current_action=action_name,
                        current_action_index=idx,
                        action_progress=ActionProgress(
                            name=action_name,
                            status=ActionStatus.SKIPPED,
                            progress=1.0,
                            completed_at=datetime.utcnow(),
                        ),
                    )
                    self.client.append_logs(
                        run_id=self._run_id,
                        entries=[
                            LogEntry(
                                message=f'Skipping action (resumed): {action_name}',
                                level=LogLevel.INFO,
                                action_name=action_name,
                            )
                        ],
                    )
                    continue

                # Report action started
                self.client.report_progress(
                    run_id=self._run_id,
                    current_action=action_name,
                    current_action_index=idx,
                    action_progress=ActionProgress(
                        name=action_name,
                        status=ActionStatus.RUNNING,
                        progress=0.0,
                        started_at=datetime.utcnow(),
                    ),
                )

                # Log action start
                self.client.append_logs(
                    run_id=self._run_id,
                    entries=[
                        LogEntry(
                            message=f'Starting action: {action_name}',
                            level=LogLevel.INFO,
                            action_name=action_name,
                        )
                    ],
                )

                # Import action class
                try:
                    module_path, class_name = entrypoint.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    action_cls = getattr(module, class_name)
                except Exception as e:
                    raise ExecutionError(f'Failed to import action {entrypoint}: {e}') from e

                # Validate params
                try:
                    validated_params = action_cls.params_model.model_validate(accumulated_params)
                except Exception as e:
                    raise ExecutionError(f'Parameter validation failed for {action_name}: {e}') from e

                # Build context with pipeline logger for progress reporting
                action_logger = _PipelineLogger(
                    base_logger=base_logger,
                    pipeline_client=self.client,
                    run_id=self._run_id,
                    action_index=idx,
                    action_name=action_name,
                )
                ctx = RuntimeContext(
                    logger=action_logger,
                    env=env,
                    job_id=self._run_id,
                    client=backend_client,
                )

                # Execute action
                action = action_cls(validated_params, ctx)
                try:
                    if hasattr(action, 'run'):
                        result = action.run()
                    else:
                        result = action.execute()
                except Exception as e:
                    # Report action failed
                    self.client.report_progress(
                        run_id=self._run_id,
                        current_action_index=idx,
                        action_progress=ActionProgress(
                            name=action_name,
                            status=ActionStatus.FAILED,
                            error=str(e),
                            completed_at=datetime.utcnow(),
                        ),
                    )
                    raise ExecutionError(f'Action {action_name} failed: {e}') from e

                # Merge result into accumulated params
                # Use mode='json' for Pydantic models to serialize Path objects
                if isinstance(result, BaseModel):
                    result_dict = result.model_dump(mode='json')
                elif isinstance(result, dict):
                    result_dict = _serialize_paths(result)
                else:
                    result_dict = {}

                accumulated_params.update(result_dict)
                final_result = result

                # Report action completed
                self.client.report_progress(
                    run_id=self._run_id,
                    current_action_index=idx,
                    action_progress=ActionProgress(
                        name=action_name,
                        status=ActionStatus.COMPLETED,
                        progress=1.0,
                        completed_at=datetime.utcnow(),
                    ),
                )

                # Create checkpoint with JSON-serializable data
                self.client.create_checkpoint(
                    run_id=self._run_id,
                    action_name=action_name,
                    action_index=idx,
                    status='completed',
                    params_snapshot=_serialize_paths(accumulated_params),
                    result=result_dict,
                )

                # Log action complete
                self.client.append_logs(
                    run_id=self._run_id,
                    entries=[
                        LogEntry(
                            message=f'Completed action: {action_name}',
                            level=LogLevel.INFO,
                            action_name=action_name,
                        )
                    ],
                )

            # Report pipeline completed
            result_for_api = final_result
            if isinstance(result_for_api, BaseModel):
                result_for_api = result_for_api.model_dump(mode='json')
            elif isinstance(result_for_api, dict):
                result_for_api = _serialize_paths(result_for_api)

            self.client.update_run(
                run_id=self._run_id,
                status='completed',
                result=result_for_api if isinstance(result_for_api, dict) else None,
            )

            base_logger.finish()
            return final_result

        except Exception as e:
            # Report pipeline failed
            error_msg = f'{type(e).__name__}: {str(e)}'
            self.client.update_run(
                run_id=self._run_id,
                status='failed',
                error=error_msg,
            )

            self.client.append_logs(
                run_id=self._run_id,
                entries=[
                    LogEntry(
                        message=f'Pipeline failed: {error_msg}\n{traceback.format_exc()}',
                        level=LogLevel.ERROR,
                    )
                ],
            )

            base_logger.finish()
            raise


__all__ = ['RayPipelineExecutor', 'PipelineDefinition']
