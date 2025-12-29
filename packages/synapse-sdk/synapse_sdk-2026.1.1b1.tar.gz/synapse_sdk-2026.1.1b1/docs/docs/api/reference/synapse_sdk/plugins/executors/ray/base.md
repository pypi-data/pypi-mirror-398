---
sidebar_label: base
title: synapse_sdk.plugins.executors.ray.base
---

Base class for Ray executors with shared runtime env logic.

#### read\_requirements

```python
def read_requirements(file_path: str | Path) -> list[str] | None
```

Read and parse a requirements.txt file.

**Arguments**:

- `file_path` - Path to the requirements.txt file.
  

**Returns**:

  List of requirement strings, or None if file doesn't exist.

## BaseRayExecutor Objects

```python
class BaseRayExecutor()
```

Base class for Ray executors with shared runtime env building logic.

