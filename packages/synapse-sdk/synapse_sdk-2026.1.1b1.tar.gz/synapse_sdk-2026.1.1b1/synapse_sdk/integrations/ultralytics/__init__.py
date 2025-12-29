"""Ultralytics YOLO autolog integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from synapse_sdk.integrations._base import BaseIntegration, register_integration
from synapse_sdk.integrations._context import AutologContext, set_autolog_context

if TYPE_CHECKING:
    from synapse_sdk.plugins.action import BaseAction


@register_integration('ultralytics')
class UltralyticsIntegration(BaseIntegration):
    """Ultralytics YOLO autologging integration.

    Automatically logs training progress, metrics, and artifacts
    when using Ultralytics YOLO models.

    Logged metrics:
        - train: box_loss, cls_loss, dfl_loss (per epoch)
        - validation: mAP50, mAP50_95 (per epoch)

    Logged artifacts:
        - validation_samples: Validation batch prediction images
        - model_weights: best.pt weights file
        - training_results: results.csv file

    Example:
        >>> class TrainAction(BaseTrainAction[TrainParams]):
        ...     def execute(self):
        ...         self.autolog('ultralytics')
        ...         model = YOLO('yolov8n.pt')
        ...         model.train(data='coco.yaml', epochs=100)
    """

    name = 'ultralytics'

    def is_available(self) -> bool:
        """Check if ultralytics is installed."""
        try:
            import ultralytics  # noqa: F401

            return True
        except ImportError:
            return False

    def enable(self, action: BaseAction) -> None:
        """Enable autologging for Ultralytics.

        Args:
            action: The action instance to log to.

        Raises:
            ImportError: If ultralytics is not installed.
        """
        if not self.is_available():
            raise ImportError('ultralytics is not installed. Install with: pip install ultralytics')

        # Set context for callbacks
        set_autolog_context(AutologContext(action=action))

        # Apply patches (idempotent)
        from synapse_sdk.integrations.ultralytics._patches import patch_yolo

        patch_yolo()

    def disable(self) -> None:
        """Disable autologging for Ultralytics.

        Clears the context but keeps patches in place for efficiency.
        Callbacks check context before logging.
        """
        set_autolog_context(None)


__all__ = ['UltralyticsIntegration']
