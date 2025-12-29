---
sidebar_label: steps
title: synapse_sdk.plugins.pipelines.steps
---

Step-based workflow pipeline.

Provides a sequential step execution framework with:
- BaseStep: Abstract base for defining workflow steps
- StepResult: Dataclass for step execution results
- StepRegistry: Ordered step management
- Orchestrator: Step execution with progress tracking and rollback
- BaseStepContext: Abstract context for sharing state between steps

**Example**:

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

