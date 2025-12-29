"""Base integration infrastructure for autolog."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from synapse_sdk.plugins.action import BaseAction


class BaseIntegration(ABC):
    """Base class for framework integrations.

    Subclasses implement framework-specific autologging by patching
    the framework's training methods to automatically log metrics,
    progress, and artifacts.

    Example:
        >>> @register_integration('my_framework')
        ... class MyFrameworkIntegration(BaseIntegration):
        ...     name = 'my_framework'
        ...
        ...     def enable(self, action):
        ...         # Patch framework methods
        ...         ...
        ...
        ...     def disable(self):
        ...         # Restore original methods
        ...         ...
        ...
        ...     def is_available(self):
        ...         try:
        ...             import my_framework
        ...             return True
        ...         except ImportError:
        ...             return False
    """

    name: str

    @abstractmethod
    def enable(self, action: BaseAction) -> None:
        """Enable autologging for this framework.

        Args:
            action: The current action instance to log to.
        """
        ...

    @abstractmethod
    def disable(self) -> None:
        """Disable autologging and restore original behavior."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the framework is installed.

        Returns:
            True if framework is available, False otherwise.
        """
        ...


# Registry of available integrations
_integrations: dict[str, type[BaseIntegration]] = {}


def register_integration(name: str) -> Callable[[type[BaseIntegration]], type[BaseIntegration]]:
    """Decorator to register an integration.

    Args:
        name: Integration name (e.g., 'ultralytics').

    Returns:
        Decorator function.

    Example:
        >>> @register_integration('ultralytics')
        ... class UltralyticsIntegration(BaseIntegration):
        ...     ...
    """

    def decorator(cls: type[BaseIntegration]) -> type[BaseIntegration]:
        _integrations[name] = cls
        return cls

    return decorator


def get_integration(name: str) -> BaseIntegration:
    """Get integration instance by name.

    Args:
        name: Integration name (e.g., 'ultralytics').

    Returns:
        BaseIntegration instance.

    Raises:
        ValueError: If integration is not registered.
    """
    if name not in _integrations:
        available = list(_integrations.keys()) or ['none']
        raise ValueError(f"Unknown integration: '{name}'. Available: {available}")
    return _integrations[name]()


def list_integrations() -> list[str]:
    """List all registered integration names.

    Returns:
        List of integration names.
    """
    return list(_integrations.keys())


__all__ = ['BaseIntegration', 'register_integration', 'get_integration', 'list_integrations']
