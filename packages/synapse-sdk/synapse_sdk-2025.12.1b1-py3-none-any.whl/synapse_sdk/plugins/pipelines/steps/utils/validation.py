"""Validation step for checking context state."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from synapse_sdk.plugins.pipelines.steps.base import BaseStep, StepResult

if TYPE_CHECKING:
    from synapse_sdk.plugins.pipelines.steps.context import BaseStepContext


class ValidationStep[C: BaseStepContext](BaseStep[C]):
    """Validates context state before proceeding.

    Takes a validator function that checks context and returns
    (is_valid, error_message). Fails the step if validation fails.

    Example:
        >>> def check_data(ctx: MyContext) -> tuple[bool, str | None]:
        ...     if not ctx.data:
        ...         return False, 'No data loaded'
        ...     return True, None
        >>>
        >>> registry.register(ValidationStep(check_data, name='validate_data'))
    """

    def __init__(
        self,
        validator: Callable[[C], tuple[bool, str | None]],
        name: str = 'validate',
        progress_weight: float = 0.05,
    ) -> None:
        """Initialize validation step.

        Args:
            validator: Function that takes context and returns (is_valid, error).
            name: Step name (default: 'validate').
            progress_weight: Progress weight (default: 0.05).
        """
        self._validator = validator
        self._name = name
        self._progress_weight = progress_weight

    @property
    def name(self) -> str:
        """Return step name."""
        return self._name

    @property
    def progress_weight(self) -> float:
        """Return progress weight."""
        return self._progress_weight

    def execute(self, context: C) -> StepResult:
        """Execute validation.

        Args:
            context: Shared context to validate.

        Returns:
            StepResult with success=False if validation fails.
        """
        is_valid, error = self._validator(context)
        if not is_valid:
            return StepResult(success=False, error=error)
        return StepResult(success=True)
