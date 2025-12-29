"""Orchestrator for executing workflow steps with rollback support."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.pipelines.steps.base import BaseStep, StepResult

if TYPE_CHECKING:
    from synapse_sdk.plugins.pipelines.steps.context import BaseStepContext
    from synapse_sdk.plugins.pipelines.steps.registry import StepRegistry


class Orchestrator[C: BaseStepContext]:
    """Executes workflow steps with progress tracking and rollback.

    Type parameter C is the context type shared between steps.
    Runs steps in order, tracking progress based on step weights.
    On failure, automatically rolls back executed steps in reverse order.

    Attributes:
        registry: StepRegistry containing ordered steps.
        context: Shared context for step communication.
        progress_callback: Optional callback for progress updates.

    Example:
        >>> registry = StepRegistry[MyContext]()
        >>> registry.register(InitStep())
        >>> registry.register(ProcessStep())
        >>> context = MyContext(runtime_ctx=runtime_ctx)
        >>> orchestrator = Orchestrator(registry, context)
        >>> result = orchestrator.execute()
    """

    def __init__(
        self,
        registry: StepRegistry[C],
        context: C,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        """Initialize orchestrator.

        Args:
            registry: StepRegistry with steps to execute.
            context: Shared context for steps.
            progress_callback: Optional callback(current, total) for progress.
        """
        self._registry = registry
        self._context = context
        self._progress_callback = progress_callback
        self._executed_steps: list[tuple[BaseStep[C], StepResult]] = []

    def execute(self) -> dict[str, Any]:
        """Execute all steps in order with rollback on failure.

        Returns:
            Dict with success status and step count.

        Raises:
            RuntimeError: If any step fails (after rollback).
        """
        steps = self._registry.get_steps()
        total_weight = self._registry.total_weight
        completed_weight = 0.0

        for step in steps:
            # Check skip condition
            if step.can_skip(self._context):
                result = StepResult(success=True, skipped=True)
                self._context.step_results.append(result)
                completed_weight += step.progress_weight
                self._update_progress(completed_weight, total_weight)
                continue

            # Execute step
            try:
                result = step.execute(self._context)
            except Exception as e:
                result = StepResult(success=False, error=str(e))

            self._context.step_results.append(result)
            self._executed_steps.append((step, result))

            if not result.success:
                self._rollback()
                raise RuntimeError(f"Step '{step.name}' failed: {result.error}")

            # Update progress
            completed_weight += step.progress_weight
            self._update_progress(completed_weight, total_weight)

        return {
            'success': True,
            'steps_executed': len(self._executed_steps),
            'steps_total': len(steps),
        }

    def _update_progress(self, completed: float, total: float) -> None:
        """Update progress via callback.

        Args:
            completed: Completed weight sum.
            total: Total weight sum.
        """
        if self._progress_callback and total > 0:
            progress_pct = int((completed / total) * 100)
            self._progress_callback(progress_pct, 100)

    def _rollback(self) -> None:
        """Rollback executed steps in reverse order.

        Best-effort rollback - errors during rollback are logged but
        do not prevent other steps from rolling back.
        """
        for step, result in reversed(self._executed_steps):
            try:
                step.rollback(self._context, result)
            except Exception:
                # Best effort rollback - log but continue
                self._context.errors.append(f"Rollback failed for step '{step.name}'")
