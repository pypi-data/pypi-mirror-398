---
sidebar_label: requirements
title: synapse_sdk.utils.file.requirements
---

Requirements file parsing utilities.

#### read\_requirements

```python
def read_requirements(path: str | Path) -> list[str] | None
```

Parse requirements.txt file.

Reads a requirements.txt file and returns a list of requirement strings,
filtering out empty lines and comments.

**Arguments**:

- `path` - Path to requirements.txt file
  

**Returns**:

  List of requirement strings, or None if file doesn't exist.
  Returns None if file exists but contains no valid requirements.

