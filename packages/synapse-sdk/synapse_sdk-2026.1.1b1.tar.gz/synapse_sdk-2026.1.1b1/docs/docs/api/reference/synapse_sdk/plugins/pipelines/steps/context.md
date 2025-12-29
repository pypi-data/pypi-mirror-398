---
sidebar_label: context
title: synapse_sdk.plugins.pipelines.steps.context
---

Base context for step-based workflows.

Provides the abstract base class for sharing state between workflow steps.

## BaseStepContext Objects

```python
@dataclass
class BaseStepContext()
```

Abstract base context for step-based workflows.

Provides the common interface for step contexts. Subclass this
to add action-specific state fields.

**Attributes**:

- `runtime_ctx` - Parent RuntimeContext with logger, env, client.
- `step_results` - Results from each executed step.
- `errors` - Accumulated error messages.
  

**Example**:

  >>> @dataclass
  ... class UploadContext(BaseStepContext):
  ...     params: dict[str, Any] = field(default_factory=dict)
  ...     uploaded_files: list[str] = field(default_factory=list)
  >>>
  >>> ctx = UploadContext(runtime_ctx=runtime_ctx)
  >>> ctx.log('upload_start', \{'count': 10\})

#### log

```python
def log(event: str, data: dict[str, Any], file: str | None = None) -> None
```

Log an event via runtime context.

**Arguments**:

- `event` - Event name/type.
- `data` - Dictionary of event data.
- `file` - Optional file path associated with the event.

#### set\_progress

```python
def set_progress(current: int,
                 total: int,
                 category: str | None = None) -> None
```

Set progress via runtime context.

**Arguments**:

- `current` - Current progress value.
- `total` - Total progress value.
- `category` - Optional category name.

#### set\_metrics

```python
def set_metrics(value: dict[str, Any], category: str) -> None
```

Set metrics via runtime context.

**Arguments**:

- `value` - Dictionary of metric values.
- `category` - Non-empty category name.

