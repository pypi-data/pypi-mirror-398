---
sidebar_label: discovery
title: synapse_sdk.plugins.discovery
---

Plugin discovery and introspection.

## PluginDiscovery Objects

```python
class PluginDiscovery()
```

Plugin discovery and introspection.

Provides methods to discover actions from configuration files or Python modules.
Supports both class-based (BaseAction subclasses) and function-based (@action decorator)
action definitions.

Example from config:
    >>> discovery = PluginDiscovery.from_path('/path/to/plugin')
    >>> discovery.list_actions()
    ['train', 'inference', 'export']
    >>> action_cls = discovery.get_action_class('train')

Example from module:
    >>> import my_plugin
    >>> discovery = PluginDiscovery.from_module(my_plugin)
    >>> discovery.list_actions()
    ['train', 'export']

#### from\_path

```python
@classmethod
def from_path(cls, path: Path | str) -> PluginDiscovery
```

Load plugin from config.yaml path.

**Arguments**:

- `path` - Path to config.yaml file or directory containing it
  

**Returns**:

  PluginDiscovery instance
  

**Raises**:

- `FileNotFoundError` - If config.yaml doesn't exist
- `ValueError` - If config.yaml is invalid

#### from\_module

```python
@classmethod
def from_module(
        cls,
        module: ModuleType,
        *,
        name: str | None = None,
        category: PluginCategory = PluginCategory.CUSTOM) -> PluginDiscovery
```

Discover plugin from Python module by introspection.

Scans module for:
- Functions decorated with @action
- Classes that subclass BaseAction

**Arguments**:

- `module` - Python module to introspect
- `name` - Plugin name (defaults to module name)
- `category` - Plugin category
  

**Returns**:

  PluginDiscovery instance with discovered actions

#### list\_actions

```python
def list_actions() -> list[str]
```

Get available action names.

**Returns**:

  List of action names

#### get\_action\_config

```python
def get_action_config(name: str) -> ActionConfig
```

Get configuration for a specific action.

**Arguments**:

- `name` - Action name
  

**Returns**:

  ActionConfig instance
  

**Raises**:

- `ActionNotFoundError` - If action doesn't exist

#### get\_action\_method

```python
def get_action_method(name: str) -> RunMethod
```

Get execution method for an action.

**Arguments**:

- `name` - Action name
  

**Returns**:

  RunMethod enum value

#### get\_action\_class

```python
def get_action_class(name: str) -> type[BaseAction] | Callable
```

Load action class/function from entrypoint.

Injects action_name and category from config if not defined on the class.
This allows plugin developers to write minimal action classes without
redundant metadata when using config.yaml-based discovery.

**Arguments**:

- `name` - Action name
  

**Returns**:

  Action class (BaseAction subclass) or decorated function
  

**Raises**:

- `ActionNotFoundError` - If action doesn't exist or has no entrypoint

#### has\_action

```python
def has_action(name: str) -> bool
```

Check if an action exists.

**Arguments**:

- `name` - Action name
  

**Returns**:

  True if action exists, False otherwise

#### get\_action\_params\_model

```python
def get_action_params_model(name: str) -> type[BaseModel] | None
```

Get the params model for an action.

**Arguments**:

- `name` - Action name
  

**Returns**:

  Pydantic model class for parameters, or None if not defined

#### get\_action\_ui\_schema

```python
def get_action_ui_schema(name: str) -> list[dict[str, Any]]
```

Get UI schema for an action's parameters.

Auto-generates FormKit-compatible UI schema from the action's params_model.

**Arguments**:

- `name` - Action name
  

**Returns**:

  List of FormKit schema items, or empty list if no params_model
  

**Example**:

  >>> discovery = PluginDiscovery.from_path('/path/to/plugin')
  >>> schema = discovery.get_action_ui_schema('train')
  >>> schema
- `[\{'$formkit'` - 'number', 'name': 'epochs', 'label': 'Epochs', ...\}]

#### to\_config\_dict

```python
def to_config_dict(*, include_ui_schemas: bool = True) -> dict[str, Any]
```

Export plugin configuration as a dictionary.

Generates a config dict compatible with the backend API format,
with optional auto-generation of UI schemas from params_model.

**Arguments**:

- `include_ui_schemas` - If True, auto-generate train_ui_schemas
  from each action's params_model
  

**Returns**:

  Config dictionary ready for serialization or API submission
  

**Example**:

  >>> discovery = PluginDiscovery.from_module(my_plugin)
  >>> config = discovery.to_config_dict()
  >>> # config['actions']['train']['hyperparameters']['train_ui_schemas']
  >>> # is auto-populated from TrainParams model

#### to\_yaml

```python
def to_yaml(*, include_ui_schemas: bool = True) -> str
```

Export plugin configuration as YAML string.

**Arguments**:

- `include_ui_schemas` - If True, auto-generate train_ui_schemas
  

**Returns**:

  YAML-formatted configuration string

