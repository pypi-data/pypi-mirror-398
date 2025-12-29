"""Base context for step-based workflows.

Provides the abstract base class for sharing state between workflow steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from synapse_sdk.plugins.context import RuntimeContext
    from synapse_sdk.plugins.pipelines.steps.base import StepResult


@dataclass
class BaseStepContext:
    """Abstract base context for step-based workflows.

    Provides the common interface for step contexts. Subclass this
    to add action-specific state fields.

    Attributes:
        runtime_ctx: Parent RuntimeContext with logger, env, client.
        step_results: Results from each executed step.
        errors: Accumulated error messages.

    Example:
        >>> @dataclass
        ... class UploadContext(BaseStepContext):
        ...     params: dict[str, Any] = field(default_factory=dict)
        ...     uploaded_files: list[str] = field(default_factory=list)
        >>>
        >>> ctx = UploadContext(runtime_ctx=runtime_ctx)
        >>> ctx.log('upload_start', {'count': 10})
    """

    runtime_ctx: RuntimeContext
    step_results: list[StepResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def log(self, event: str, data: dict[str, Any], file: str | None = None) -> None:
        """Log an event via runtime context.

        Args:
            event: Event name/type.
            data: Dictionary of event data.
            file: Optional file path associated with the event.
        """
        self.runtime_ctx.log(event, data, file)

    def set_progress(self, current: int, total: int, category: str | None = None) -> None:
        """Set progress via runtime context.

        Args:
            current: Current progress value.
            total: Total progress value.
            category: Optional category name.
        """
        self.runtime_ctx.set_progress(current, total, category)

    def set_metrics(self, value: dict[str, Any], category: str) -> None:
        """Set metrics via runtime context.

        Args:
            value: Dictionary of metric values.
            category: Non-empty category name.
        """
        self.runtime_ctx.set_metrics(value, category)
