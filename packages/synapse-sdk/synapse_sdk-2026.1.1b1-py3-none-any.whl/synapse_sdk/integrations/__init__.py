"""Framework integrations for automatic logging.

This module provides automatic logging integrations for popular ML frameworks.
Enable autolog to automatically capture training progress, metrics, and artifacts.

Example:
    >>> from synapse_sdk.plugins.actions.train import BaseTrainAction
    >>> from ultralytics import YOLO
    >>>
    >>> class TrainAction(BaseTrainAction[TrainParams]):
    ...     def execute(self):
    ...         self.autolog('ultralytics')  # Enable autologging
    ...
    ...         model = YOLO('yolov8n.pt')   # Callbacks auto-attached
    ...         model.train(epochs=100)       # Metrics logged automatically
    ...
    ...         return TrainResult(...)

Supported frameworks:
    - ultralytics: YOLO object detection models
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from synapse_sdk.integrations._base import get_integration, list_integrations

if TYPE_CHECKING:
    from synapse_sdk.plugins.action import BaseAction

# Import integrations to register them
from synapse_sdk.integrations import ultralytics as _ultralytics  # noqa: F401


def autolog(framework: str, action: BaseAction) -> None:
    """Enable automatic logging for an ML framework.

    Call this before creating model objects. The SDK will automatically
    attach callbacks to log progress, metrics, and artifacts.

    Args:
        framework: Framework name (e.g., 'ultralytics').
        action: The current action instance (typically `self` in execute()).

    Raises:
        ValueError: If framework is not recognized.
        ImportError: If framework package is not installed.

    Example:
        >>> class TrainAction(BaseTrainAction[TrainParams]):
        ...     def execute(self):
        ...         autolog('ultralytics', self)
        ...         model = YOLO('yolov8n.pt')
        ...         model.train(epochs=100)
    """
    integration = get_integration(framework)
    integration.enable(action)


def disable_autolog(framework: str) -> None:
    """Disable autologging for a framework.

    Args:
        framework: Framework name (e.g., 'ultralytics').

    Raises:
        ValueError: If framework is not recognized.
    """
    integration = get_integration(framework)
    integration.disable()


__all__ = ['autolog', 'disable_autolog', 'list_integrations']
