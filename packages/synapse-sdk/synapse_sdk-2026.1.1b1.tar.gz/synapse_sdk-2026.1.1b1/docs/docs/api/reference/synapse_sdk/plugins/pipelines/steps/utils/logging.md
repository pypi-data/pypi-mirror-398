---
sidebar_label: logging
title: synapse_sdk.plugins.pipelines.steps.utils.logging
---

Logging step wrapper for workflow steps.

## LoggingStep Objects

```python
class LoggingStep()
```

Wraps a step with start/end logging including timing.

Logs step_start event before execution and step_end event after,
including elapsed time in seconds.

**Example**:

  >>> logged_step = LoggingStep(MyProcessStep())
  >>> registry.register(logged_step)
  >>> # Logs: step_start \{'step': 'process'\}
  >>> # Logs: step_end \{'step': 'process', 'elapsed': 1.23, 'success': True\}

#### name

```python
@property
def name() -> str
```

Return wrapped step name with 'logged_' prefix.

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

Execute wrapped step with logging.

**Arguments**:

- `context` - Shared context.
  

**Returns**:

  Result from wrapped step execution.

#### can\_skip

```python
def can_skip(context: C) -> bool
```

Delegate to wrapped step.

#### rollback

```python
def rollback(context: C, result: StepResult) -> None
```

Delegate rollback to wrapped step with logging.

**Arguments**:

- `context` - Shared context.
- `result` - Result from this step's execution.

