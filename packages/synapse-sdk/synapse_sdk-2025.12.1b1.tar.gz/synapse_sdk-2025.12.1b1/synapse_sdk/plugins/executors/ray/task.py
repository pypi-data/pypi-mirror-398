"""Ray Actor executor for plugin actions."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from synapse_sdk.plugins.context import PluginEnvironment
from synapse_sdk.plugins.enums import PackageManager
from synapse_sdk.plugins.errors import ExecutionError
from synapse_sdk.plugins.executors.ray.base import BaseRayExecutor, read_requirements

if TYPE_CHECKING:
    from synapse_sdk.plugins.action import BaseAction


class RayActorExecutor(BaseRayExecutor):
    """Ray Actor based synchronous task execution.

    Executes actions using a persistent Ray Actor. Best for fast startup
    with pre-warmed workers. The actor maintains state across executions
    and methods are executed serially within each actor.

    Example:
        >>> executor = RayActorExecutor(
        ...     ray_address='auto',
        ...     working_dir='/path/to/plugin',  # Auto-reads requirements.txt
        ... )
        >>> result = executor.execute(TrainAction, {'epochs': 10})
        >>> # Reuse the same actor for subsequent executions
        >>> result2 = executor.execute(InferAction, {'batch_size': 32})
    """

    def __init__(
        self,
        env: PluginEnvironment | dict[str, Any] | None = None,
        job_id: str | None = None,
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
    ) -> None:
        """Initialize Ray actor executor.

        Args:
            env: Environment config for the action. If None, loads from os.environ.
            job_id: Optional job identifier for tracking.
            ray_address: Ray cluster address. Defaults to 'auto'.
            runtime_env: Ray runtime environment config (pip packages, working_dir, env_vars).
            working_dir: Plugin working directory. Sets runtime_env['working_dir'] and
                auto-reads requirements.txt if requirements_file is not specified.
            requirements_file: Path to requirements.txt. If None and working_dir is set,
                looks for requirements.txt in working_dir.
            package_manager: Package manager to use ('pip' or 'uv'). Defaults to 'pip'.
            package_manager_options: Additional options for the package manager.
                For uv: defaults to ['--no-cache']. For pip: defaults to ['--upgrade'].
            wheels_dir: Directory containing .whl files relative to working_dir (default: 'wheels').
            num_cpus: Number of CPUs to request for the actor.
            num_gpus: Number of GPUs to request for the actor.
            include_sdk: If True, bundle local SDK with upload (for development).
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
        self._job_id = job_id
        self._num_cpus = num_cpus
        self._num_gpus = num_gpus
        self._actor: Any | None = None

    def _get_or_create_actor(self) -> Any:
        """Get existing actor or create a new one."""
        import ray

        if self._actor is not None:
            return self._actor

        self._ray_init()

        # Build remote options
        remote_options: dict[str, Any] = {'runtime_env': self._build_runtime_env()}
        if self._num_cpus is not None:
            remote_options['num_cpus'] = self._num_cpus
        if self._num_gpus is not None:
            remote_options['num_gpus'] = self._num_gpus

        # Create the actor class dynamically with ray.remote
        ActionExecutorActor = ray.remote(**remote_options)(_ActionExecutorActor)
        self._actor = ActionExecutorActor.remote(self._job_id)
        return self._actor

    def execute(
        self,
        action_cls: type[BaseAction] | str,
        params: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """Execute action using the Ray actor.

        Args:
            action_cls: BaseAction subclass or entrypoint string (e.g., 'plugin.test.TestAction').
            params: Parameters dict to validate and pass.
            **kwargs: Ignored (for protocol compatibility).

        Returns:
            Action result from execute().

        Raises:
            ValidationError: If params fail validation.
            ExecutionError: If action execution fails.
        """
        import ray
        from ray.exceptions import RayActorError, RayTaskError

        # Convert class to entrypoint string for remote import
        if isinstance(action_cls, str):
            entrypoint = action_cls
        else:
            entrypoint = f'{action_cls.__module__}.{action_cls.__name__}'

        actor = self._get_or_create_actor()

        try:
            return ray.get(actor.run_action.remote(entrypoint, params))
        except (RayTaskError, RayActorError) as e:
            # Actor may have died, reset it for next call
            self._actor = None
            cause = getattr(e, 'cause', e)
            raise ExecutionError(f'Ray actor execution failed: {cause}') from e

    def shutdown(self) -> None:
        """Shutdown the actor."""
        import ray

        if self._actor is not None:
            ray.kill(self._actor)
            self._actor = None


class _ActionExecutorActor:
    """Ray Actor that executes plugin actions.

    This actor maintains state across executions and provides
    serial execution guarantees for methods called on it.
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

        Raises:
            ValidationError: If params fail validation.
            ExecutionError: If action execution fails.
        """
        import importlib
        import os
        import sys

        from synapse_sdk.loggers import ConsoleLogger
        from synapse_sdk.plugins.action import NoResult, validate_result
        from synapse_sdk.plugins.context import RuntimeContext
        from synapse_sdk.plugins.errors import ExecutionError, ValidationError
        from synapse_sdk.utils.auth import create_backend_client

        # Dynamically import action class from entrypoint
        try:
            # Ensure working directory is in sys.path (Ray should do this, but be explicit)
            cwd = os.getcwd()
            if cwd not in sys.path:
                sys.path.insert(0, cwd)

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
        client = create_backend_client()

        # Build context (inside actor)
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

        # Validate result with warning-only mode
        result_model = getattr(action_cls, 'result_model', NoResult)
        if result_model is not NoResult:
            result = validate_result(result, result_model, logger)

        logger.finish()
        return result


# Keep old name as alias for backwards compatibility
RayTaskExecutor = RayActorExecutor

__all__ = ['RayActorExecutor', 'RayTaskExecutor', 'read_requirements']
