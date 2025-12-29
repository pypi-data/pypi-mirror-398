---
sidebar_label: local
title: synapse_sdk.plugins.executors.local
---

## LocalExecutor Objects

```python
class LocalExecutor()
```

Execute actions in the current process.

Best for development and testing. Uses ConsoleLogger by default.

**Example**:

  >>> executor = LocalExecutor()
  >>> result = executor.execute(TrainAction, \{'epochs': 10\})

#### execute

```python
def execute(action_cls: type[BaseAction], params: dict[str, Any],
            **kwargs: Any) -> Any
```

Execute action synchronously in current process.

**Arguments**:

- `action_cls` - BaseAction subclass to execute.
- `params` - Parameters dict to validate and pass.
- `**kwargs` - Ignored (for protocol compatibility).
  

**Returns**:

  Action result from execute().
  

**Raises**:

- `ValidationError` - If params fail validation.
- `ExecutionError` - If action raises an exception.

