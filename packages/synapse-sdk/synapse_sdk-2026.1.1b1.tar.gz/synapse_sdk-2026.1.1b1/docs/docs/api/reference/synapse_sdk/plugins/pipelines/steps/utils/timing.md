---
sidebar_label: timing
title: synapse_sdk.plugins.pipelines.steps.utils.timing
---

Timing step wrapper for workflow steps.

## TimingStep Objects

```python
class TimingStep()
```

Wraps a step with duration measurement.

Measures execution time and adds 'duration_seconds' to result data.

**Example**:

  >>> timed_step = TimingStep(MyProcessStep())
  >>> registry.register(timed_step)
  >>> result = orchestrator.execute()
  >>> print(result.data['duration_seconds'])  # 1.234

#### name

```python
@property
def name() -> str
```

Return wrapped step name with 'timed_' prefix.

#### progress\_weight

```python
@property
def progress_weight() -> float
```

Return wrapped step's progress weight.

#### execute

```python
def execute(context: C) -> StepResult
```

Execute wrapped step with timing.

**Arguments**:

- `context` - Shared context.
  

**Returns**:

  Result from wrapped step with duration_seconds added.

#### can\_skip

```python
def can_skip(context: C) -> bool
```

Delegate to wrapped step.

#### rollback

```python
def rollback(context: C, result: StepResult) -> None
```

Delegate rollback to wrapped step.

**Arguments**:

- `context` - Shared context.
- `result` - Result from this step's execution.

