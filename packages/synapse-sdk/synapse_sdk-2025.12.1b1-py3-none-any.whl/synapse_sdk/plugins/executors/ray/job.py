"""Ray Job executor for plugin actions."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from synapse_sdk.plugins.context import PluginEnvironment
from synapse_sdk.plugins.enums import PackageManager
from synapse_sdk.plugins.errors import ExecutionError
from synapse_sdk.plugins.executors.ray.base import BaseRayExecutor

if TYPE_CHECKING:
    from synapse_sdk.plugins.action import BaseAction


class RayJobExecutor(BaseRayExecutor):
    """Ray Job based asynchronous execution.

    Submits actions as detached Ray tasks. Best for heavy/long-running
    workloads that don't need immediate results.

    Example:
        >>> executor = RayJobExecutor(
        ...     ray_address='auto',
        ...     working_dir='/path/to/plugin',
        ... )
        >>> job_id = executor.submit(TrainAction, {'epochs': 100})
        >>> status = executor.get_status(job_id)
        >>> result = executor.get_result(job_id)
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
        job_id: str | None = None,
    ) -> None:
        """Initialize Ray job executor.

        Args:
            env: Environment config for the action. If None, loads from os.environ.
            ray_address: Ray cluster address. Defaults to 'auto'.
            runtime_env: Ray runtime environment config.
            working_dir: Plugin working directory.
            requirements_file: Path to requirements.txt.
            package_manager: Package manager to use ('pip' or 'uv').
            package_manager_options: Additional options for the package manager.
            wheels_dir: Directory containing .whl files relative to working_dir.
            num_cpus: Number of CPUs to request.
            num_gpus: Number of GPUs to request.
            include_sdk: If True, bundle local SDK with upload (for development).
            job_id: Optional job identifier for tracking.
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
        self._job_id = job_id
        self._submitted_refs: dict[str, Any] = {}  # job_id -> ObjectRef

    def submit(
        self,
        action_cls: type[BaseAction] | str,
        params: dict[str, Any],
        *,
        job_id: str | None = None,
    ) -> str:
        """Submit action as a Ray task (non-blocking).

        Args:
            action_cls: BaseAction subclass or entrypoint string.
            params: Parameters dict for the action.
            job_id: Optional job identifier. If None, generates one.

        Returns:
            Job ID for tracking.
        """
        import uuid

        import ray

        self._ray_init()

        # Convert class to entrypoint string
        if isinstance(action_cls, str):
            entrypoint = action_cls
        else:
            entrypoint = f'{action_cls.__module__}.{action_cls.__name__}'

        # Generate job_id if not provided
        job_id = job_id or self._job_id or str(uuid.uuid4())[:8]

        # Build remote options
        remote_options: dict[str, Any] = {'runtime_env': self._build_runtime_env()}
        if self._num_cpus is not None:
            remote_options['num_cpus'] = self._num_cpus
        if self._num_gpus is not None:
            remote_options['num_gpus'] = self._num_gpus

        # Create actor and submit (actor pattern works with remote clusters)
        JobActor = ray.remote(**remote_options)(_JobExecutorActor)
        actor = JobActor.remote(job_id)
        ref = actor.run_action.remote(entrypoint, params)

        self._submitted_refs[job_id] = ref
        return job_id

    def get_status(self, job_id: str) -> str:
        """Get job status.

        Args:
            job_id: Job ID from submit().

        Returns:
            'PENDING', 'RUNNING', 'SUCCEEDED', or 'FAILED'.
        """
        import ray

        ref = self._submitted_refs.get(job_id)
        if ref is None:
            return 'UNKNOWN'

        ready, _ = ray.wait([ref], timeout=0)
        if ready:
            try:
                ray.get(ref)
                return 'SUCCEEDED'
            except Exception:
                return 'FAILED'
        return 'RUNNING'

    def get_result(self, job_id: str, timeout: float | None = None) -> Any:
        """Get job result (blocks until complete).

        Args:
            job_id: Job ID from submit().
            timeout: Optional timeout in seconds.

        Returns:
            Action result.

        Raises:
            ExecutionError: If job failed or not found.
        """
        import ray

        ref = self._submitted_refs.get(job_id)
        if ref is None:
            raise ExecutionError(f'Job {job_id} not found')

        try:
            return ray.get(ref, timeout=timeout)
        except Exception as e:
            raise ExecutionError(f'Job {job_id} failed: {e}') from e

    def wait(self, job_id: str, timeout_seconds: float = 300) -> str:
        """Wait for job to complete.

        Args:
            job_id: Job ID from submit().
            timeout_seconds: Maximum time to wait.

        Returns:
            Final job status.

        Raises:
            ExecutionError: If job fails or times out.
        """
        import ray

        ref = self._submitted_refs.get(job_id)
        if ref is None:
            raise ExecutionError(f'Job {job_id} not found')

        try:
            ray.get(ref, timeout=timeout_seconds)
            return 'SUCCEEDED'
        except ray.exceptions.GetTimeoutError:
            raise ExecutionError(f'Job {job_id} timed out after {timeout_seconds}s')
        except Exception as e:
            raise ExecutionError(f'Job {job_id} failed: {e}') from e

    def get_logs(self, job_id: str) -> str:
        """Get job logs (not available for ray.remote tasks)."""
        return ''


class _JobExecutorActor:
    """Ray Actor that executes plugin actions for job mode.

    Each job gets its own actor instance (not reused like task mode).
    """

    def __init__(self, job_id: str | None = None) -> None:
        """Initialize the actor.

        Args:
            job_id: Optional job identifier for tracking.
        """
        self._job_id = job_id

    def run_action(
        self,
        entrypoint: str,
        params: dict[str, Any],
    ) -> Any:
        """Execute an action within this actor.

        Args:
            entrypoint: Action entrypoint string (e.g., 'plugin.test.TestAction').
            params: Parameters dict to validate and pass.

        Returns:
            Action result from execute().
        """
        import importlib
        import os
        import sys

        from synapse_sdk.loggers import ConsoleLogger
        from synapse_sdk.plugins.context import RuntimeContext
        from synapse_sdk.plugins.errors import ExecutionError, ValidationError

        # Ensure working directory is in sys.path
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)

        # Dynamically import action class
        try:
            module_path, class_name = entrypoint.rsplit('.', 1)
            module = importlib.import_module(module_path)
            action_cls = getattr(module, class_name)
        except Exception as e:
            raise ExecutionError(f'Failed to import action {entrypoint}: {e}') from e

        # Validate params
        try:
            validated_params = action_cls.params_model.model_validate(params)
        except Exception as e:
            raise ValidationError(f'Parameter validation failed: {e}') from e

        # Try to create BackendClient from environment/credentials
        from synapse_sdk.utils.auth import create_backend_client

        client = create_backend_client()

        # Build context
        logger = ConsoleLogger()
        ctx = RuntimeContext(
            logger=logger,
            env=dict(os.environ),
            job_id=self._job_id,
            client=client,
        )

        # Execute
        action = action_cls(validated_params, ctx)
        try:
            result = action.execute()
        except Exception as e:
            logger.finish()
            raise ExecutionError(f'Action execution failed: {e}') from e

        logger.finish()
        return result


__all__ = ['RayJobExecutor']
