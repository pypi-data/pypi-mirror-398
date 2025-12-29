---
sidebar_label: base
title: synapse_sdk.plugins.pipelines.steps.base
---

Workflow step base class and result dataclass.

Provides the foundation for defining workflow steps
with execution, skip conditions, and rollback support.

## StepResult Objects

```python
@dataclass
class StepResult()
```

Result of a workflow step execution.

**Attributes**:

- `success` - Whether the step completed successfully.
- `data` - Output data from the step.
- `error` - Error message if step failed.
- `rollback_data` - Data needed for rollback on failure.
- `skipped` - Whether the step was skipped.
- `timestamp` - When the step completed.
  

**Example**:

  >>> result = StepResult(success=True, data=\{'files': 10\})
  >>> if not result.success:
  ...     print(f"Failed: \{result.error\}")

## BaseStep Objects

```python
class BaseStep()
```

Abstract base class for workflow steps.

Type parameter C is the context type (must extend BaseStepContext).
Implement this class to define custom workflow steps with
execution, skip conditions, and rollback support.

**Attributes**:

- `name` - Unique identifier for the step.
- `progress_weight` - Relative weight (0.0-1.0) for progress calculation.
  

**Example**:

  >>> class ValidateStep(BaseStep[MyContext]):
  ...     @property
  ...     def name(self) -> str:
  ...         return 'validate'
  ...
  ...     @property
  ...     def progress_weight(self) -> float:
  ...         return 0.1
  ...
  ...     def execute(self, context: MyContext) -> StepResult:
  ...         if not context.data:
  ...             return StepResult(success=False, error='No data')
  ...         return StepResult(success=True)

#### name

```python
@property
@abstractmethod
def name() -> str
```

Step identifier.

**Returns**:

  Unique name for this step.

#### progress\_weight

```python
@property
@abstractmethod
def progress_weight() -> float
```

Relative weight for progress calculation.

**Returns**:

  Float between 0.0 and 1.0 representing this step's
  portion of total workflow progress.

#### execute

```python
@abstractmethod
def execute(context: C) -> StepResult
```

Execute the step.

**Arguments**:

- `context` - Shared context with params and state.
  

**Returns**:

  StepResult indicating success/failure and any output data.

#### can\_skip

```python
def can_skip(context: C) -> bool
```

Check if step can be skipped.

Override to implement conditional step execution.

**Arguments**:

- `context` - Shared context.
  

**Returns**:

  True if step should be skipped, False otherwise.
- `Default` - False.

#### rollback

```python
def rollback(context: C, result: StepResult) -> None
```

Rollback step on workflow failure.

Override to implement cleanup when a later step fails.
Called in reverse order for all executed steps.

**Arguments**:

- `context` - Shared context.
- `result` - The result from this step's execution.

