---
sidebar_label: env
title: synapse_sdk.plugins.context.env
---

## PluginEnvironment Objects

```python
class PluginEnvironment()
```

Environment configuration for plugin execution.

Auto-loads from:
1. os.environ (lowest priority)
2. Config file if provided (highest priority)

**Example**:

  >>> env = PluginEnvironment.from_environ()
  >>> env.get_str('API_KEY')
  >>> env.get_int('BATCH_SIZE', default=32)
  >>> env.get_bool('DEBUG', default=False)

#### from\_environ

```python
@classmethod
def from_environ(cls, prefix: str = '') -> PluginEnvironment
```

Load from os.environ, optionally filtering by prefix.

#### from\_file

```python
@classmethod
def from_file(cls, path: str | Path) -> PluginEnvironment
```

Load from TOML config file.

#### merge

```python
@classmethod
def merge(cls, *envs: PluginEnvironment) -> PluginEnvironment
```

Merge multiple environments (later overrides earlier).

#### get

```python
def get(key: str, default: Any = None) -> Any
```

Get raw value.

#### get\_str

```python
def get_str(key: str, default: str | None = None) -> str | None
```

Get string value.

#### get\_int

```python
def get_int(key: str, default: int | None = None) -> int | None
```

Get integer value.

#### get\_float

```python
def get_float(key: str, default: float | None = None) -> float | None
```

Get float value.

#### get\_bool

```python
def get_bool(key: str, default: bool | None = None) -> bool | None
```

Get boolean value (handles string 'true'/'false').

#### get\_list

```python
def get_list(key: str, default: list | None = None) -> list | None
```

Get list value (splits comma-separated strings).

#### to\_dict

```python
def to_dict() -> dict[str, Any]
```

Export as dictionary.

