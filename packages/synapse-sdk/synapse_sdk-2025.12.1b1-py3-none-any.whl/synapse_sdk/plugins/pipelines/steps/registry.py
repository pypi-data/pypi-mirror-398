"""Step registry for managing ordered workflow steps."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from synapse_sdk.plugins.pipelines.steps.base import BaseStep
    from synapse_sdk.plugins.pipelines.steps.context import BaseStepContext


class StepRegistry[C: BaseStepContext]:
    """Registry for managing ordered workflow steps.

    Type parameter C is the context type for steps in this registry.
    Maintains an ordered list of steps and provides methods for
    registration, removal, and insertion at specific positions.

    Example:
        >>> registry = StepRegistry[MyContext]()
        >>> registry.register(InitStep())
        >>> registry.register(ProcessStep())
        >>> registry.insert_before('process', ValidateStep())
        >>> for step in registry.get_steps():
        ...     print(step.name)  # init, validate, process
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._steps: list[BaseStep[C]] = []

    def register(self, step: BaseStep[C]) -> None:
        """Add step to end of workflow.

        Args:
            step: Step instance to register.
        """
        self._steps.append(step)

    def unregister(self, name: str) -> None:
        """Remove step by name.

        Args:
            name: Name of step to remove.
        """
        self._steps = [s for s in self._steps if s.name != name]

    def get_steps(self) -> list[BaseStep[C]]:
        """Get ordered list of steps.

        Returns:
            Copy of the step list in execution order.
        """
        return list(self._steps)

    def insert_after(self, after_name: str, step: BaseStep[C]) -> None:
        """Insert step after another step.

        Args:
            after_name: Name of existing step to insert after.
            step: Step instance to insert.

        Raises:
            ValueError: If step with after_name not found.
        """
        for i, s in enumerate(self._steps):
            if s.name == after_name:
                self._steps.insert(i + 1, step)
                return
        raise ValueError(f"Step '{after_name}' not found")

    def insert_before(self, before_name: str, step: BaseStep[C]) -> None:
        """Insert step before another step.

        Args:
            before_name: Name of existing step to insert before.
            step: Step instance to insert.

        Raises:
            ValueError: If step with before_name not found.
        """
        for i, s in enumerate(self._steps):
            if s.name == before_name:
                self._steps.insert(i, step)
                return
        raise ValueError(f"Step '{before_name}' not found")

    @property
    def total_weight(self) -> float:
        """Sum of all step weights.

        Returns:
            Total progress weight across all registered steps.
        """
        return sum(s.progress_weight for s in self._steps)

    def __len__(self) -> int:
        """Return number of registered steps."""
        return len(self._steps)

    def __bool__(self) -> bool:
        """Return True if any steps are registered."""
        return bool(self._steps)
