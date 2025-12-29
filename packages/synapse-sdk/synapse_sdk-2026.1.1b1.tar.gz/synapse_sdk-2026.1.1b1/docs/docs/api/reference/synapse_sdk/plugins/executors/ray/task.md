---
sidebar_label: task
title: synapse_sdk.plugins.executors.ray.task
---

Ray Actor executor for plugin actions.

## RayActorExecutor Objects

```python
class RayActorExecutor(BaseRayExecutor)
```

Ray Actor based synchronous task execution.

Executes actions using a persistent Ray Actor. Best for fast startup
with pre-warmed workers. The actor maintains state across executions
and methods are executed serially within each actor.

**Example**:

  >>> executor = RayActorExecutor(
  ...     ray_address='auto',
  ...     working_dir='/path/to/plugin',  # Auto-reads requirements.txt
  ... )
  >>> result = executor.execute(TrainAction, \{'epochs': 10\})
  >>> # Reuse the same actor for subsequent executions
  >>> result2 = executor.execute(InferAction, \{'batch_size': 32\})

#### execute

```python
def execute(action_cls: type[BaseAction], params: dict[str, Any],
            **kwargs: Any) -> Any
```

Execute action using the Ray actor.

**Arguments**:

- `action_cls` - BaseAction subclass to execute.
- `params` - Parameters dict to validate and pass.
- `**kwargs` - Ignored (for protocol compatibility).
  

**Returns**:

  Action result from execute().
  

**Raises**:

- `ValidationError` - If params fail validation.
- `ExecutionError` - If action execution fails.

#### shutdown

```python
def shutdown() -> None
```

Shutdown the actor.

