"""Context management for autolog integrations."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from synapse_sdk.plugins.action import BaseAction


@dataclass
class AutologContext:
    """Holds action context for autolog callbacks.

    Attributes:
        action: The current BaseAction instance.
        total_epochs: Total epochs (auto-detected from train() kwargs).
        extra: Additional framework-specific data.
    """

    action: BaseAction[Any]
    total_epochs: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


# Thread/async safe context storage
_autolog_context: ContextVar[AutologContext | None] = ContextVar(
    'synapse_autolog_context',
    default=None,
)


def get_autolog_context() -> AutologContext | None:
    """Get current autolog context.

    Returns:
        AutologContext if autolog is active, None otherwise.
    """
    return _autolog_context.get()


def set_autolog_context(ctx: AutologContext | None) -> None:
    """Set autolog context.

    Args:
        ctx: AutologContext to set, or None to clear.
    """
    _autolog_context.set(ctx)


__all__ = ['AutologContext', 'get_autolog_context', 'set_autolog_context']
