---
sidebar_label: loggers
title: synapse_sdk.loggers
---

## LoggerBackend Objects

```python
class LoggerBackend(Protocol)
```

Protocol for logger backends that handle data synchronization.

## ProgressData Objects

```python
@dataclass
class ProgressData()
```

Immutable progress data snapshot.

## LogEntry Objects

```python
@dataclass
class LogEntry()
```

Single log entry.

## BaseLogger Objects

```python
class BaseLogger(ABC)
```

Base class for logging progress, metrics, and events.

All state is instance-level to prevent cross-instance contamination.
Uses composition over inheritance for backend communication.

#### log

```python
def log(event: str, data: dict[str, Any], file: str | None = None) -> None
```

Log an event with data.

**Arguments**:

- `event` - Event name/type.
- `data` - Dictionary of event data.
- `file` - Optional file path associated with the event.
  

**Raises**:

- `TypeError` - If data is not a dictionary.
- `RuntimeError` - If logger is already finished.

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
  

**Raises**:

- `ValueError` - If current/total values are invalid.
- `RuntimeError` - If logger is already finished.

#### set\_progress\_failed

```python
def set_progress_failed(category: str | None = None) -> None
```

Mark progress as failed.

**Arguments**:

- `category` - Optional category name.
  

**Raises**:

- `RuntimeError` - If logger is already finished.

#### set\_metrics

```python
def set_metrics(value: dict[str, Any], category: str) -> None
```

Set metrics for a category.

**Arguments**:

- `value` - Dictionary of metric values.
- `category` - Non-empty category name.
  

**Raises**:

- `ValueError` - If category is empty.
- `TypeError` - If value is not a dictionary.
- `RuntimeError` - If logger is already finished.

#### get\_progress

```python
def get_progress(category: str | None = None) -> ProgressData | None
```

Get progress for a category.

#### get\_metrics

```python
def get_metrics(category: str | None = None) -> dict[str, Any]
```

Get metrics, optionally filtered by category.

#### finish

```python
def finish() -> None
```

Mark the logger as finished. No further logging is allowed.

## ConsoleLogger Objects

```python
class ConsoleLogger(BaseLogger)
```

Logger that prints to console.

## BackendLogger Objects

```python
class BackendLogger(BaseLogger)
```

Logger that syncs with a remote backend.

Uses a backend interface for decoupled communication.

## NoOpLogger Objects

```python
class NoOpLogger(BaseLogger)
```

Logger that does nothing. Useful for testing or disabled logging.

