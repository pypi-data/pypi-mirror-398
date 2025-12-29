---
id: models
title: Plugin Models
sidebar_position: 1
---

# Plugin Models

Core data models and structures for the plugin system.

## PluginRelease

Represents a specific version of a plugin.

```python
from synapse_sdk.plugins.models import PluginRelease

release = PluginRelease(plugin_path="./my-plugin")
```

### Properties

- `plugin`: Plugin code identifier
- `version`: Plugin version
- `code`: Combined plugin and version string
- `category`: Plugin category
- `name`: Human-readable plugin name
- `actions`: Available plugin actions

## PluginAction

Represents a plugin action execution request.

```python
from synapse_sdk.plugins.models import PluginAction

action = PluginAction(
    plugin="my-plugin",
    version="1.0.0",
    action="process",
    params={"input": "data"}
)
```

## Run

Execution context for plugin actions.

```python
def start(self):
    # Log messages
    self.run.log("Processing started")

    # Update progress
    self.run.set_progress(0.5)

    # Set metrics
    self.run.set_metrics({"processed": 100})
```

### Development Logging

The `Run` class includes a specialized logging system for plugin developers with the `log_dev_event()` method and `DevLog` model.

#### DevLog Model

Structured model for development event logging:

```python
from synapse_sdk.shared.enums import Context

class DevLog(BaseModel):
    event_type: str          # Event category (automatically generated as '{action_name}_dev_log')
    message: str             # Descriptive message
    data: dict | None        # Optional additional data
    level: Context           # Event severity level
    created: str             # ISO timestamp
```

#### log_dev_event Method

Log custom development events for debugging and monitoring:

```python
def start(self):
    # Basic event logging (event_type automatically set to '{action_name}_dev_log')
    self.run.log_dev_event('Data validation completed', {'records_count': 100})

    # Performance tracking
    self.run.log_dev_event('Processing time recorded', {'duration_ms': 1500})

    # Debug with warning level
    self.run.log_dev_event('Variable state checkpoint',
                          {'variable_x': 42}, level=Context.WARNING)

    # Simple event without data
    self.run.log_dev_event('Plugin initialization complete')
```

**Parameters:**

- `message` (str): Human-readable description
- `data` (dict, optional): Additional context data
- `level` (Context, optional): Event severity (default: Context.INFO)

**Note:** The `event_type` is automatically generated as `{action_name}_dev_log` and cannot be modified by plugin developers.

**Use Cases:**

- **Debugging**: Track variable states and execution flow
- **Performance**: Record processing times and resource usage
- **Validation**: Log data validation results
- **Error Tracking**: Capture detailed error information
- **Progress Monitoring**: Record intermediate states in long-running tasks
