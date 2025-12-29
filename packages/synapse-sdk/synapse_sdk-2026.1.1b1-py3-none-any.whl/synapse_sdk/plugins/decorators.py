from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from pydantic import BaseModel

from synapse_sdk.plugins.enums import PluginCategory

F = TypeVar('F', bound=Callable[..., Any])


def action(
    name: str | None = None,
    description: str = '',
    params: type[BaseModel] | None = None,
    result: type[BaseModel] | None = None,
    category: PluginCategory | None = None,
) -> Callable[[F], F]:
    """Decorator to register a function as a plugin action.

    Use this decorator to define function-based actions. The decorated function
    should accept (params, context) arguments where params is a Pydantic model
    instance and context is a RunContext.

    Args:
        name: Action name (defaults to function name).
        description: Human-readable description of the action.
        params: Pydantic model class for parameter validation.
        result: Pydantic model class for result validation (optional).
        category: Plugin category for grouping actions (optional).

    Returns:
        Decorated function with action metadata attached.

    Example (without result schema):
        >>> from pydantic import BaseModel
        >>> from synapse_sdk.plugins.decorators import action
        >>>
        >>> class TrainParams(BaseModel):
        ...     epochs: int = 10
        >>>
        >>> @action(params=TrainParams, description='Train a model')
        ... def train(params: TrainParams, context: RunContext) -> dict:
        ...     return {'epochs_trained': params.epochs}

    Example (with result schema):
        >>> class TrainResult(BaseModel):
        ...     weights_path: str
        ...     final_loss: float
        >>>
        >>> @action(params=TrainParams, result=TrainResult)
        ... def train(params: TrainParams, context: RunContext) -> TrainResult:
        ...     return TrainResult(weights_path='/model.pt', final_loss=0.05)
        >>>
        >>> # Access action metadata
        >>> train._action_name  # 'train'
        >>> train._action_params  # TrainParams
        >>> train._action_result  # TrainResult
        >>> train._action_category  # PluginCategory.NEURAL_NET
    """

    def decorator(func: F) -> F:
        action_name = name or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        # Attach action metadata
        wrapper._is_action = True  # type: ignore[attr-defined]
        wrapper._action_name = action_name  # type: ignore[attr-defined]
        wrapper._action_description = description  # type: ignore[attr-defined]
        wrapper._action_params = params  # type: ignore[attr-defined]
        wrapper._action_result = result  # type: ignore[attr-defined]
        wrapper._action_category = category  # type: ignore[attr-defined]

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = ['action']
