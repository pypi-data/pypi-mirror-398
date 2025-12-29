"""Timing step wrapper for workflow steps."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from synapse_sdk.plugins.pipelines.steps.base import BaseStep, StepResult

if TYPE_CHECKING:
    from synapse_sdk.plugins.pipelines.steps.context import BaseStepContext


class TimingStep[C: BaseStepContext](BaseStep[C]):
    """Wraps a step with duration measurement.

    Measures execution time and adds 'duration_seconds' to result data.

    Example:
        >>> timed_step = TimingStep(MyProcessStep())
        >>> registry.register(timed_step)
        >>> result = orchestrator.execute()
        >>> print(result.data['duration_seconds'])  # 1.234
    """

    def __init__(self, step: BaseStep[C]) -> None:
        """Initialize with step to wrap.

        Args:
            step: The step to wrap with timing.
        """
        self._wrapped = step

    @property
    def name(self) -> str:
        """Return wrapped step name with 'timed_' prefix."""
        return f'timed_{self._wrapped.name}'

    @property
    def progress_weight(self) -> float:
        """Return wrapped step's progress weight."""
        return self._wrapped.progress_weight

    def execute(self, context: C) -> StepResult:
        """Execute wrapped step with timing.

        Args:
            context: Shared context.

        Returns:
            Result from wrapped step with duration_seconds added.
        """
        start = time.perf_counter()
        result = self._wrapped.execute(context)
        elapsed = time.perf_counter() - start

        result.data['duration_seconds'] = round(elapsed, 6)
        return result

    def can_skip(self, context: C) -> bool:
        """Delegate to wrapped step."""
        return self._wrapped.can_skip(context)

    def rollback(self, context: C, result: StepResult) -> None:
        """Delegate rollback to wrapped step.

        Args:
            context: Shared context.
            result: Result from this step's execution.
        """
        self._wrapped.rollback(context, result)
