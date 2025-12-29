from __future__ import annotations

from typing import TYPE_CHECKING, Any

from synapse_sdk.loggers import ConsoleLogger
from synapse_sdk.plugins.action import NoResult, validate_result
from synapse_sdk.plugins.context import PluginEnvironment, RuntimeContext
from synapse_sdk.plugins.errors import ExecutionError, ValidationError
from synapse_sdk.utils.auth import create_backend_client

if TYPE_CHECKING:
    from synapse_sdk.plugins.action import BaseAction


class LocalExecutor:
    """Execute actions in the current process.

    Best for development and testing. Uses ConsoleLogger by default.

    Example:
        >>> executor = LocalExecutor()
        >>> result = executor.execute(TrainAction, {'epochs': 10})
    """

    def __init__(
        self,
        env: PluginEnvironment | dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> None:
        """Initialize executor.

        Args:
            env: Environment config. If None, loads from os.environ.
            job_id: Optional job identifier.
        """
        if env is None:
            self._env = PluginEnvironment.from_environ()
        elif isinstance(env, dict):
            self._env = PluginEnvironment(env)
        else:
            self._env = env
        self._job_id = job_id
        self._client = create_backend_client()

    def execute(
        self,
        action_cls: type[BaseAction],
        params: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """Execute action synchronously in current process.

        Args:
            action_cls: BaseAction subclass to execute.
            params: Parameters dict to validate and pass.
            **kwargs: Ignored (for protocol compatibility).

        Returns:
            Action result from execute().

        Raises:
            ValidationError: If params fail validation.
            ExecutionError: If action raises an exception.
        """
        del kwargs  # Unused, for protocol compatibility

        # Validate params
        try:
            validated_params = action_cls.params_model.model_validate(params)
        except Exception as e:
            raise ValidationError(f'Parameter validation failed: {e}') from e

        # Build context
        logger = ConsoleLogger()
        ctx = RuntimeContext(
            logger=logger,
            env=self._env.to_dict(),
            job_id=self._job_id,
            client=self._client,
        )

        # Instantiate and execute
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


__all__ = ['LocalExecutor']
