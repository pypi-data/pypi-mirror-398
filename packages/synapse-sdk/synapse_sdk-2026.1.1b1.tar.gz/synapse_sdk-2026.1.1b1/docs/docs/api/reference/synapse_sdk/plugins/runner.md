---
sidebar_label: runner
title: synapse_sdk.plugins.runner
---

#### run\_plugin

```python
def run_plugin(plugin_code: str,
               action: str,
               params: dict[str, Any] | None = None,
               *,
               mode: Literal['local', 'task', 'job'] = 'local',
               **executor_kwargs: Any) -> Any
```

Run a plugin action.

This is the main entry point for executing plugin actions. It handles
plugin discovery, parameter validation, and execution delegation to
the appropriate executor based on the mode.

**Arguments**:

- `plugin_code` - Plugin identifier. Can be:
  - Module path: 'my_plugins.yolov8' (discovers via @action decorators or BaseAction classes)
  - Filesystem path: '/path/to/plugin' or '/path/to/config.yaml'
- `action` - Action name to execute (e.g., 'train', 'infer', 'export').
- `params` - Action parameters as a dictionary. Will be validated against
  the action's params schema if defined.
- `mode` - Execution mode:
  - 'local': Run in the current process (default, good for dev).
  - 'task': Run via Ray Actor pool (fast startup, \<1s).
  - 'job': Run via Ray Job API (for heavy/long-running workloads).
- `**executor_kwargs` - Additional executor options:
  - action_cls: Optional explicit action class (skips discovery).
  - env: PluginEnvironment or dict for environment config.
  - job_id: Optional job identifier for tracking.
  

**Returns**:

  For 'local' and 'task' modes: Action result (type depends on the action).
  For 'job' mode: Job ID string for tracking (async submission).
  

**Raises**:

- `ActionNotFoundError` - If the action doesn't exist in the plugin.
- `ValidationError` - If params fail schema validation.
- `ExecutionError` - If action execution fails.
  

**Example**:

  >>> from synapse_sdk.plugins.runner import run_plugin
  >>>
  >>> # Auto-discover from module path
  >>> result = run_plugin('my_plugins.yolov8', 'train', \{'epochs': 10\})
  >>>
  >>> # Auto-discover from config.yaml path
  >>> result = run_plugin('/path/to/plugin', 'train', \{'epochs': 10\})
  >>>
  >>> # Explicit action class (skips discovery)
  >>> result = run_plugin('yolov8', 'train', \{'epochs': 10\}, action_cls=TrainAction)

