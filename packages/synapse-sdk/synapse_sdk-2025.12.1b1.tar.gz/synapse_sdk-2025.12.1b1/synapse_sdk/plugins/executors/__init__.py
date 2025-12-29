from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from synapse_sdk.plugins.action import BaseAction


@runtime_checkable
class ExecutorProtocol(Protocol):
    """Protocol for plugin action executors.

    Executors handle the lifecycle of action execution:
    1. Build RuntimeContext (logger, env, job_id)
    2. Instantiate the action with validated params
    3. Call execute() and handle errors
    4. Clean up and return result
    """

    def execute(
        self,
        action_cls: type[BaseAction],
        params: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """Execute an action class with parameters.

        Args:
            action_cls: The BaseAction subclass to execute.
            params: Raw parameters dict (will be validated).
            **kwargs: Executor-specific options.

        Returns:
            Action result.

        Raises:
            ValidationError: If params fail validation.
            ExecutionError: If action execution fails.
        """
        ...


__all__ = ['ExecutorProtocol']
