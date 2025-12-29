---
id: step-orchestration
title: Step Orchestration
sidebar_position: 1
---

# Step Orchestration

Step Orchestration is a powerful workflow pattern that enables you to break down complex operations into discrete, manageable steps. Each step can have its own execution logic, progress weight, skip conditions, and rollback behavior.

## Why Use Step Orchestration?

### Benefits

| Benefit | Description |
|---------|-------------|
| **Separation of Concerns** | Each step handles one specific task, making code easier to understand and maintain |
| **Reusability** | Steps can be shared across different workflows and actions |
| **Testability** | Individual steps can be unit tested in isolation |
| **Progress Tracking** | Weighted progress calculation provides accurate progress reporting |
| **Error Recovery** | Automatic rollback on failure cleans up partial operations |
| **Flexibility** | Steps can be inserted, removed, or reordered dynamically |
| **Observability** | Built-in logging and timing utilities for debugging |

### When to Use

Step orchestration is ideal for:

- **Multi-phase operations**: Upload workflows (init -> validate -> upload -> cleanup)
- **Long-running tasks**: Training pipelines (load data -> train -> save model)
- **Operations requiring cleanup**: File processing with temp file cleanup on failure
- **Composable workflows**: Building workflows from reusable step components

### When NOT to Use

Step orchestration adds overhead. For simple operations, use direct `execute()`:

- Single-phase operations (e.g., simple data fetch)
- Operations without cleanup requirements
- Workflows with fewer than 3 logical phases

## Core Concepts

### Step

A step is a discrete unit of work in a workflow. Each step:

- Has a unique **name** for identification
- Specifies a **progress weight** (0.0 to 1.0) for progress calculation
- Implements **execute()** to perform the actual work
- Can optionally implement **can_skip()** and **rollback()**

```python
from synapse_sdk.plugins.pipelines.steps import BaseStep, StepResult

class ValidateFilesStep(BaseStep[UploadContext]):
    @property
    def name(self) -> str:
        return 'validate_files'

    @property
    def progress_weight(self) -> float:
        return 0.1  # 10% of total workflow progress

    def execute(self, context: UploadContext) -> StepResult:
        invalid_files = []
        for file in context.files:
            if not self._is_valid(file):
                invalid_files.append(file)

        if invalid_files:
            return StepResult(
                success=False,
                error=f'Invalid files: {invalid_files}'
            )

        return StepResult(success=True, data={'validated': len(context.files)})

    def can_skip(self, context: UploadContext) -> bool:
        # Skip validation if explicitly disabled
        return context.params.get('skip_validation', False)

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        # Nothing to rollback for validation
        pass

    def _is_valid(self, file: dict) -> bool:
        # Validation logic
        return file.get('size', 0) > 0
```

### StepResult

Every step returns a `StepResult` containing:

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether the step completed successfully |
| `data` | `dict[str, Any]` | Output data from the step |
| `error` | `str | None` | Error message if step failed |
| `rollback_data` | `dict[str, Any]` | Data needed for rollback |
| `skipped` | `bool` | Whether the step was skipped |
| `timestamp` | `datetime` | When the step completed |

```python
# Success result
return StepResult(success=True, data={'files_processed': 10})

# Failure result
return StepResult(success=False, error='Connection timeout')

# Result with rollback data
return StepResult(
    success=True,
    data={'uploaded_ids': [1, 2, 3]},
    rollback_data={'uploaded_ids': [1, 2, 3]}  # For cleanup on failure
)
```

### Context

Context is a shared state object passed between all steps. It:

- Extends `BaseStepContext` with workflow-specific fields
- Provides access to `RuntimeContext` for logging/progress
- Accumulates data as steps execute
- Tracks step results and errors

```python
from dataclasses import dataclass, field
from synapse_sdk.plugins.pipelines.steps import BaseStepContext

@dataclass
class UploadContext(BaseStepContext):
    """Shared context for upload workflow."""
    # Workflow parameters
    params: dict = field(default_factory=dict)

    # Accumulated state
    files_to_upload: list[str] = field(default_factory=list)
    uploaded_files: list[dict] = field(default_factory=list)
    total_bytes: int = 0

    # Access backend client
    @property
    def client(self):
        return self.runtime_ctx.client
```

### Registry

The `StepRegistry` manages an ordered list of steps:

```python
from synapse_sdk.plugins.pipelines.steps import StepRegistry

registry = StepRegistry[UploadContext]()

# Register steps in order
registry.register(InitializeStep())
registry.register(ValidateStep())
registry.register(UploadStep())
registry.register(CleanupStep())

# Dynamic step manipulation
registry.insert_before('upload', CompressionStep())  # Add compression before upload
registry.insert_after('validate', SanitizeStep())    # Add sanitization after validate
registry.unregister('cleanup')                        # Remove cleanup step

# Get step count and total weight
print(f"Steps: {len(registry)}")
print(f"Total weight: {registry.total_weight}")
```

### Orchestrator

The `Orchestrator` executes steps and handles:

- Sequential step execution
- Weighted progress tracking
- Automatic rollback on failure
- Skip condition evaluation

```python
from synapse_sdk.plugins.pipelines.steps import Orchestrator

orchestrator = Orchestrator(
    registry=registry,
    context=context,
    progress_callback=lambda current, total: print(f'{current}/{total}%')
)

try:
    result = orchestrator.execute()
    # {'success': True, 'steps_executed': 4, 'steps_total': 4}
except RuntimeError as e:
    # Step failed, rollback was performed
    print(f"Workflow failed: {e}")
```

## Progress Tracking

Progress is calculated based on step weights:

```python
class Step1(BaseStep[MyContext]):
    @property
    def progress_weight(self) -> float:
        return 0.2  # 20%

class Step2(BaseStep[MyContext]):
    @property
    def progress_weight(self) -> float:
        return 0.6  # 60%

class Step3(BaseStep[MyContext]):
    @property
    def progress_weight(self) -> float:
        return 0.2  # 20%

# Progress updates:
# After Step1: 20%
# After Step2: 80%
# After Step3: 100%
```

The orchestrator normalizes weights, so they don't need to sum exactly to 1.0.

## Rollback Behavior

When a step fails, the orchestrator:

1. Stops execution immediately
2. Calls `rollback()` on all previously executed steps **in reverse order**
3. Raises `RuntimeError` with the failure details

```python
class UploadFilesStep(BaseStep[UploadContext]):
    def execute(self, context: UploadContext) -> StepResult:
        uploaded_ids = []
        for file in context.files:
            file_id = self._upload(file)
            uploaded_ids.append(file_id)

        return StepResult(
            success=True,
            rollback_data={'uploaded_ids': uploaded_ids}
        )

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        # Clean up uploaded files
        for file_id in result.rollback_data.get('uploaded_ids', []):
            try:
                self._delete(file_id)
            except Exception:
                context.errors.append(f'Failed to rollback file {file_id}')
```

## Utility Steps

The SDK provides utility step wrappers for common patterns:

### LoggingStep

Wraps a step with start/end logging:

```python
from synapse_sdk.plugins.pipelines.steps import LoggingStep

# Wrap any step with logging
logged_step = LoggingStep(UploadFilesStep())
registry.register(logged_step)

# Logs:
# step_start {'step': 'upload_files'}
# step_end {'step': 'upload_files', 'elapsed': 1.234, 'success': True}
```

### TimingStep

Measures step execution duration:

```python
from synapse_sdk.plugins.pipelines.steps import TimingStep

timed_step = TimingStep(ProcessDataStep())
registry.register(timed_step)

# Result includes duration:
# result.data['duration_seconds'] = 1.234567
```

### ValidationStep

Validates context state before proceeding:

```python
from synapse_sdk.plugins.pipelines.steps import ValidationStep

def check_files_exist(context: UploadContext) -> tuple[bool, str | None]:
    if not context.files:
        return False, 'No files to upload'
    return True, None

registry.register(ValidationStep(
    validator=check_files_exist,
    name='validate_files_exist',
    progress_weight=0.05
))
```

## Integration with Actions

All base action classes support optional step-based execution via `setup_steps()`:

### Upload Action

```python
from synapse_sdk.plugins import BaseUploadAction
from synapse_sdk.plugins.actions.upload import UploadContext

class MyUploadAction(BaseUploadAction[UploadParams]):
    def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
        registry.register(InitStorageStep())
        registry.register(OrganizeFilesStep())
        registry.register(UploadFilesStep())
        registry.register(GenerateMetadataStep())
        registry.register(CleanupStep())
```

### Train Action

```python
from synapse_sdk.plugins import BaseTrainAction
from synapse_sdk.plugins.actions.train import TrainContext

class MyTrainAction(BaseTrainAction[TrainParams]):
    def setup_steps(self, registry: StepRegistry[TrainContext]) -> None:
        registry.register(LoadDatasetStep())     # 20%
        registry.register(TrainModelStep())       # 60%
        registry.register(UploadModelStep())      # 20%

    # If setup_steps() is not overridden or registers no steps,
    # the action uses simple execute() mode instead
```

### Export Action

```python
from synapse_sdk.plugins import BaseExportAction
from synapse_sdk.plugins.actions.export import ExportContext

class MyExportAction(BaseExportAction[ExportParams]):
    def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
        registry.register(FetchResultsStep())
        registry.register(ProcessBatchStep())
        registry.register(WriteOutputStep())
```

## Complete Example

Here's a complete example of a file upload workflow:

```python
from dataclasses import dataclass, field
from pathlib import Path
from synapse_sdk.plugins import BaseUploadAction
from synapse_sdk.plugins.pipelines.steps import (
    BaseStep, StepResult, StepRegistry, BaseStepContext, LoggingStep
)

# Define context
@dataclass
class FileUploadContext(BaseStepContext):
    source_path: Path | None = None
    files: list[Path] = field(default_factory=list)
    uploaded_ids: list[int] = field(default_factory=list)

# Define steps
class DiscoverFilesStep(BaseStep[FileUploadContext]):
    @property
    def name(self) -> str:
        return 'discover_files'

    @property
    def progress_weight(self) -> float:
        return 0.1

    def execute(self, context: FileUploadContext) -> StepResult:
        if not context.source_path or not context.source_path.exists():
            return StepResult(success=False, error='Source path not found')

        context.files = list(context.source_path.glob('**/*'))
        context.files = [f for f in context.files if f.is_file()]

        if not context.files:
            return StepResult(success=False, error='No files found')

        return StepResult(success=True, data={'file_count': len(context.files)})

class UploadFilesStep(BaseStep[FileUploadContext]):
    @property
    def name(self) -> str:
        return 'upload_files'

    @property
    def progress_weight(self) -> float:
        return 0.8

    def execute(self, context: FileUploadContext) -> StepResult:
        for i, file in enumerate(context.files):
            # Upload each file
            file_id = context.client.upload_file(file)
            context.uploaded_ids.append(file_id)

            # Update progress within step
            progress = (i + 1) / len(context.files)
            context.set_progress(int(progress * 100), 100, 'upload')

        return StepResult(
            success=True,
            rollback_data={'uploaded_ids': context.uploaded_ids.copy()}
        )

    def rollback(self, context: FileUploadContext, result: StepResult) -> None:
        for file_id in result.rollback_data.get('uploaded_ids', []):
            try:
                context.client.delete_file(file_id)
            except Exception:
                context.errors.append(f'Failed to delete file {file_id}')

class FinalizeStep(BaseStep[FileUploadContext]):
    @property
    def name(self) -> str:
        return 'finalize'

    @property
    def progress_weight(self) -> float:
        return 0.1

    def execute(self, context: FileUploadContext) -> StepResult:
        context.log('upload_complete', {
            'file_count': len(context.uploaded_ids),
            'file_ids': context.uploaded_ids
        })
        return StepResult(success=True)

# Use in action
class FileUploadAction(BaseUploadAction[FileUploadParams]):
    def setup_steps(self, registry: StepRegistry) -> None:
        # Wrap steps with logging for debugging
        registry.register(LoggingStep(DiscoverFilesStep()))
        registry.register(LoggingStep(UploadFilesStep()))
        registry.register(LoggingStep(FinalizeStep()))

    def create_context(self) -> FileUploadContext:
        return FileUploadContext(
            runtime_ctx=self.ctx,
            source_path=Path(self.params.source_path)
        )
```

## Best Practices

### 1. Keep Steps Focused

Each step should do one thing well:

```python
# Good: Focused steps
class ValidateFilesStep(BaseStep): ...
class CompressFilesStep(BaseStep): ...
class UploadFilesStep(BaseStep): ...

# Bad: Monolithic step
class ProcessEverythingStep(BaseStep): ...  # Does validation, compression, and upload
```

### 2. Use Meaningful Progress Weights

Assign weights based on actual time/complexity:

```python
# Good: Weights reflect actual time distribution
LoadDataStep:    0.1   # Quick file read
TrainModelStep:  0.8   # Long training loop
SaveModelStep:   0.1   # Quick save

# Bad: Equal weights don't reflect reality
LoadDataStep:    0.33
TrainModelStep:  0.33  # Training takes 10x longer!
SaveModelStep:   0.33
```

### 3. Implement Rollback for Destructive Steps

Any step that creates resources should clean them up on failure:

```python
class CreateResourcesStep(BaseStep):
    def execute(self, context) -> StepResult:
        resource_id = create_resource()
        return StepResult(
            success=True,
            rollback_data={'resource_id': resource_id}
        )

    def rollback(self, context, result) -> None:
        resource_id = result.rollback_data.get('resource_id')
        if resource_id:
            delete_resource(resource_id)
```

### 4. Use can_skip() for Conditional Steps

```python
class CompressionStep(BaseStep):
    def can_skip(self, context) -> bool:
        # Skip if files are already compressed
        return all(f.suffix == '.gz' for f in context.files)
```

### 5. Log Important Events

Use context logging for debugging:

```python
def execute(self, context) -> StepResult:
    context.log('step_progress', {'phase': 'starting', 'item_count': 100})
    # ... work ...
    context.log('step_progress', {'phase': 'complete', 'processed': 100})
    return StepResult(success=True)
```

## API Reference

### BaseStep[C]

| Method/Property | Description |
|-----------------|-------------|
| `name: str` | Unique step identifier (abstract property) |
| `progress_weight: float` | Relative progress weight 0.0-1.0 (abstract property) |
| `execute(context: C) -> StepResult` | Execute the step (abstract method) |
| `can_skip(context: C) -> bool` | Check if step can be skipped (default: False) |
| `rollback(context: C, result: StepResult) -> None` | Cleanup on failure (default: no-op) |

### StepResult

| Field | Type | Default |
|-------|------|---------|
| `success` | `bool` | `True` |
| `data` | `dict[str, Any]` | `{}` |
| `error` | `str | None` | `None` |
| `rollback_data` | `dict[str, Any]` | `{}` |
| `skipped` | `bool` | `False` |
| `timestamp` | `datetime` | `datetime.now()` |

### StepRegistry[C]

| Method | Description |
|--------|-------------|
| `register(step)` | Add step to end of workflow |
| `unregister(name)` | Remove step by name |
| `insert_before(name, step)` | Insert step before another |
| `insert_after(name, step)` | Insert step after another |
| `get_steps()` | Get ordered list of steps |
| `total_weight` | Sum of all step weights |

### Orchestrator[C]

| Method | Description |
|--------|-------------|
| `__init__(registry, context, progress_callback=None)` | Create orchestrator |
| `execute() -> dict` | Execute all steps with rollback |

### BaseStepContext

| Field/Method | Description |
|--------------|-------------|
| `runtime_ctx: RuntimeContext` | Parent runtime context |
| `step_results: list[StepResult]` | Results from executed steps |
| `errors: list[str]` | Accumulated error messages |
| `log(event, data, file=None)` | Log via runtime context |
| `set_progress(current, total, category=None)` | Update progress |
| `set_metrics(value, category)` | Set metrics |
