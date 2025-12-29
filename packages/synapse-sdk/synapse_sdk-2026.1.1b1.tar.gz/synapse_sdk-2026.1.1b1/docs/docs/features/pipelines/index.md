---
id: pipelines
title: Pipeline Patterns
sidebar_position: 3
---

# Pipeline Patterns

The Synapse SDK provides powerful pipeline patterns for orchestrating complex workflows. These patterns enable you to break down complex operations into discrete, manageable steps with built-in progress tracking, error handling, and automatic rollback.

## Available Pipeline Patterns

### [Step Orchestration](./step-orchestration.md)

A sequential step-based workflow system with:

- **Ordered step execution** - Steps run in sequence with dependencies
- **Automatic progress tracking** - Weighted progress calculation across all steps
- **Rollback on failure** - Automatic cleanup when steps fail
- **Step composition** - Combine and reorder steps easily
- **Utility wrappers** - Built-in logging, timing, and validation steps

## When to Use Pipelines

Pipeline patterns are ideal for:

| Scenario | Example |
|----------|---------|
| Multi-phase workflows | Upload: initialize -> validate -> upload -> cleanup |
| Operations requiring cleanup | File processing with cleanup on failure |
| Progress-tracked operations | Training: dataset (20%) -> train (60%) -> upload (20%) |
| Composable workflows | Reusable steps shared across actions |

## Quick Example

```python
from synapse_sdk.plugins.pipelines.steps import (
    BaseStep, StepResult, StepRegistry, Orchestrator, BaseStepContext
)
from dataclasses import dataclass, field

@dataclass
class MyContext(BaseStepContext):
    """Custom context for my workflow."""
    data: list[str] = field(default_factory=list)
    processed_count: int = 0

class LoadDataStep(BaseStep[MyContext]):
    @property
    def name(self) -> str:
        return 'load_data'

    @property
    def progress_weight(self) -> float:
        return 0.2  # 20% of total progress

    def execute(self, context: MyContext) -> StepResult:
        context.data = ['item1', 'item2', 'item3']
        return StepResult(success=True)

class ProcessDataStep(BaseStep[MyContext]):
    @property
    def name(self) -> str:
        return 'process_data'

    @property
    def progress_weight(self) -> float:
        return 0.7  # 70% of total progress

    def execute(self, context: MyContext) -> StepResult:
        for item in context.data:
            # Process each item
            context.processed_count += 1
        return StepResult(success=True)

    def rollback(self, context: MyContext, result: StepResult) -> None:
        # Cleanup on failure
        context.processed_count = 0

class FinalizeStep(BaseStep[MyContext]):
    @property
    def name(self) -> str:
        return 'finalize'

    @property
    def progress_weight(self) -> float:
        return 0.1  # 10% of total progress

    def execute(self, context: MyContext) -> StepResult:
        return StepResult(
            success=True,
            data={'processed': context.processed_count}
        )

# Execute the workflow
registry = StepRegistry[MyContext]()
registry.register(LoadDataStep())
registry.register(ProcessDataStep())
registry.register(FinalizeStep())

context = MyContext(runtime_ctx=runtime_ctx)
orchestrator = Orchestrator(registry, context)
result = orchestrator.execute()
# {'success': True, 'steps_executed': 3, 'steps_total': 3}
```

## Core Components

| Component | Description |
|-----------|-------------|
| `BaseStep[C]` | Abstract base class for workflow steps |
| `StepResult` | Dataclass containing step execution results |
| `StepRegistry[C]` | Manages ordered list of steps |
| `Orchestrator[C]` | Executes steps with progress and rollback |
| `BaseStepContext` | Base context for sharing state between steps |

## Utility Steps

| Utility | Description |
|---------|-------------|
| `LoggingStep` | Wraps a step with start/end logging |
| `TimingStep` | Measures step execution duration |
| `ValidationStep` | Validates context state before proceeding |

## Integration with Actions

All base action classes (Train, Export, Upload) support optional step-based execution:

```python
from synapse_sdk.plugins import BaseUploadAction
from synapse_sdk.plugins.pipelines.steps import BaseStep, StepRegistry

class MyUploadAction(BaseUploadAction[MyParams]):
    def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
        registry.register(InitializeStep())
        registry.register(ValidateStep())
        registry.register(UploadFilesStep())
        registry.register(CleanupStep())
```

See the [Step Orchestration](./step-orchestration.md) guide for complete documentation.
