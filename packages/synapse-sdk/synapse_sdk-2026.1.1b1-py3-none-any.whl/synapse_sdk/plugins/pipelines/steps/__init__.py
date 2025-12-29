"""Step-based workflow pipeline.

Provides a sequential step execution framework with:
- BaseStep: Abstract base for defining workflow steps
- StepResult: Dataclass for step execution results
- StepRegistry: Ordered step management
- Orchestrator: Step execution with progress tracking and rollback
- BaseStepContext: Abstract context for sharing state between steps

Example:
    >>> from synapse_sdk.plugins.pipelines.steps import (
    ...     BaseStep,
    ...     BaseStepContext,
    ...     Orchestrator,
    ...     StepRegistry,
    ...     StepResult,
    ... )
    >>>
    >>> @dataclass
    ... class MyContext(BaseStepContext):
    ...     data: list[str] = field(default_factory=list)
    >>>
    >>> class LoadStep(BaseStep[MyContext]):
    ...     @property
    ...     def name(self) -> str:
    ...         return 'load'
    ...
    ...     @property
    ...     def progress_weight(self) -> float:
    ...         return 0.3
    ...
    ...     def execute(self, context: MyContext) -> StepResult:
    ...         context.data.append('loaded')
    ...         return StepResult(success=True)
"""

from synapse_sdk.plugins.pipelines.steps.base import BaseStep, StepResult
from synapse_sdk.plugins.pipelines.steps.context import BaseStepContext
from synapse_sdk.plugins.pipelines.steps.orchestrator import Orchestrator
from synapse_sdk.plugins.pipelines.steps.registry import StepRegistry
from synapse_sdk.plugins.pipelines.steps.utils import (
    LoggingStep,
    TimingStep,
    ValidationStep,
)

__all__ = [
    # Core
    'BaseStep',
    'BaseStepContext',
    'Orchestrator',
    'StepRegistry',
    'StepResult',
    # Utilities
    'LoggingStep',
    'TimingStep',
    'ValidationStep',
]
