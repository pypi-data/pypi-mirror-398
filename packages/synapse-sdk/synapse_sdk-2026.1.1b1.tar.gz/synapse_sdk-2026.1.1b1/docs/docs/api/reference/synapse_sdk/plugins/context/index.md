---
sidebar_label: context
title: synapse_sdk.plugins.context
---

## RuntimeContext Objects

```python
@dataclass
class RuntimeContext()
```

Runtime context injected into actions.

Provides access to logging, environment, and client dependencies.
All action dependencies are accessed through this context object.

**Attributes**:

- `logger` - Logger instance for progress, metrics, and event logging.
- `env` - Environment variables and configuration as PluginEnvironment.
- `job_id` - Optional job identifier for tracking.
- `client` - Optional backend client for API access.
- `agent_client` - Optional agent client for Ray operations.
- `checkpoint` - Optional checkpoint info for pretrained models.
  Contains 'category' ('base' or fine-tuned) and 'path' to model.
  

**Example**:

  >>> ctx = RuntimeContext(
  ...     logger=ConsoleLogger(),
  ...     env=PluginEnvironment.from_environ(),
  ...     job_id='job-123',
  ...     checkpoint=\{'category': 'base', 'path': '/models/yolov8n.pt'\},
  ... )
  >>> ctx.set_progress(50, 100)
  >>> ctx.log('checkpoint', \{'epoch': 5\})

#### log

```python
def log(event: str, data: dict[str, Any], file: str | None = None) -> None
```

Log an event with data.

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

Set progress for the current operation.

**Arguments**:

- `current` - Current progress value (0 to total).
- `total` - Total progress value.
- `category` - Optional category name for multi-phase progress.

#### set\_metrics

```python
def set_metrics(value: dict[str, Any], category: str) -> None
```

Set metrics for a category.

**Arguments**:

- `value` - Dictionary of metric values.
- `category` - Non-empty category name.

#### log\_message

```python
def log_message(message: str, context: str = 'info') -> None
```

Log a user-facing message.

**Arguments**:

- `message` - Message content.
- `context` - Message context/level ('info', 'warning', 'danger', 'success').

#### log\_dev\_event

```python
def log_dev_event(message: str, data: dict[str, Any] | None = None) -> None
```

Log a development/debug event.

For plugin developers to log custom events during execution.
Not shown to end users by default.

**Arguments**:

- `message` - Event message.
- `data` - Optional additional data.

#### end\_log

```python
def end_log() -> None
```

Signal that plugin execution is complete.

