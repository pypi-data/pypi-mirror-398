"""Logging step wrapper for workflow steps."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from synapse_sdk.plugins.pipelines.steps.base import BaseStep, StepResult

if TYPE_CHECKING:
    from synapse_sdk.plugins.pipelines.steps.context import BaseStepContext


class LoggingStep[C: BaseStepContext](BaseStep[C]):
    """Wraps a step with start/end logging including timing.

    Logs step_start event before execution and step_end event after,
    including elapsed time in seconds.

    Example:
        >>> logged_step = LoggingStep(MyProcessStep())
        >>> registry.register(logged_step)
        >>> # Logs: step_start {'step': 'process'}
        >>> # Logs: step_end {'step': 'process', 'elapsed': 1.23, 'success': True}
    """

    def __init__(self, step: BaseStep[C]) -> None:
        """Initialize with step to wrap.

        Args:
            step: The step to wrap with logging.
        """
        self._wrapped = step

    @property
    def name(self) -> str:
        """Return wrapped step name with 'logged_' prefix."""
        return f'logged_{self._wrapped.name}'

    @property
    def progress_weight(self) -> float:
        """Return wrapped step's progress weight."""
        return self._wrapped.progress_weight

    def execute(self, context: C) -> StepResult:
        """Execute wrapped step with logging.

        Args:
            context: Shared context.

        Returns:
            Result from wrapped step execution.
        """
        step_name = self._wrapped.name
        context.log('step_start', {'step': step_name})

        start = time.perf_counter()
        result = self._wrapped.execute(context)
        elapsed = time.perf_counter() - start

        context.log(
            'step_end',
            {
                'step': step_name,
                'elapsed': round(elapsed, 3),
                'success': result.success,
                'skipped': result.skipped,
            },
        )

        return result

    def can_skip(self, context: C) -> bool:
        """Delegate to wrapped step."""
        return self._wrapped.can_skip(context)

    def rollback(self, context: C, result: StepResult) -> None:
        """Delegate rollback to wrapped step with logging.

        Args:
            context: Shared context.
            result: Result from this step's execution.
        """
        context.log('step_rollback', {'step': self._wrapped.name})
        self._wrapped.rollback(context, result)
