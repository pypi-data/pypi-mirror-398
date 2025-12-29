---
sidebar_label: config
title: synapse_sdk.plugins.config
---

## ActionConfig Objects

```python
class ActionConfig(BaseModel)
```

Configuration for a single plugin action.

**Attributes**:

- `name` - Action name (e.g., 'train', 'infer', 'export').
- `description` - Human-readable description of the action.
- `entrypoint` - Module path to action class (e.g., 'my_plugin.actions:TrainAction').
- `method` - Execution method (job, task, or serve_application).
- `params_schema` - Pydantic model class for parameter validation.

## PluginConfig Objects

```python
class PluginConfig(BaseModel)
```

Configuration for a plugin.

**Attributes**:

- `name` - Human-readable plugin name.
- `code` - Unique identifier for the plugin (e.g., 'yolov8').
- `version` - Semantic version string.
- `category` - Plugin category for organization.
- `description` - Human-readable description.
- `readme` - Path to README file relative to plugin root.
- `package_manager` - Package manager for dependencies ('pip' or 'uv').
- `package_manager_options` - Additional options for package manager.
- `wheels_dir` - Directory containing .whl files for local installation (default: 'wheels').
- `data_type` - Primary data type handled by the plugin.
- `code`0 - List of tasks in format 'data_type.task_name' (e.g., 'image.object_detection').
- `code`1 - Data types supported by upload plugins.
- `code`2 - Annotation category for smart tools.
- `code`3 - Annotation type for smart tools.
- `code`4 - Smart tool implementation type.
- `code`5 - Dictionary of action name to ActionConfig.

