---
sidebar_label: utils
title: synapse_sdk.plugins.utils
---

Plugin utilities for configuration parsing and action discovery.

#### get\_plugin\_actions

```python
def get_plugin_actions(config: dict | PluginConfig | Path | str) -> list[str]
```

Extract action names from plugin configuration.

**Arguments**:

- `config` - Plugin config dict, PluginConfig instance, or path to config.yaml
  

**Returns**:

  List of action names. Returns empty list on error.

#### get\_action\_method

```python
def get_action_method(config: dict | PluginConfig, action: str) -> RunMethod
```

Get the run method for an action from config.

**Arguments**:

- `config` - Plugin config dict or PluginConfig instance
- `action` - Action name
  

**Returns**:

  RunMethod enum value. Defaults to TASK if not found.

#### get\_action\_config

```python
def get_action_config(config: dict | PluginConfig, action: str) -> dict
```

Get the full configuration for a specific action.

**Arguments**:

- `config` - Plugin config dict or PluginConfig instance
- `action` - Action name
  

**Returns**:

  Action configuration dictionary
  

**Raises**:

- `KeyError` - If action not found
- `ValueError` - If config type is invalid

#### pydantic\_to\_ui\_schema

```python
def pydantic_to_ui_schema(model: type[BaseModel]) -> list[dict[str, Any]]
```

Convert a Pydantic model to FormKit UI schema format.

This generates a UI schema compatible with the legacy config.yaml format,
suitable for rendering forms in the frontend.

**Arguments**:

- `model` - Pydantic BaseModel class with field definitions
  

**Returns**:

  List of FormKit schema items, one per field
  

**Example**:

  >>> from pydantic import BaseModel, Field
  >>>
  >>> class TrainParams(BaseModel):
  ...     epochs: int = Field(default=50, ge=1, le=1000)
  ...     batch_size: int = Field(default=8, ge=1, le=512)
  ...     learning_rate: float = Field(default=0.001)
  ...
  >>> schema = pydantic_to_ui_schema(TrainParams)
  >>> schema[0]
  \{
- `'$formkit'` - 'number',
- `'name'` - 'epochs',
- `'label'` - 'Epochs',
- `'value'` - 50,
- `'placeholder'` - 50,
- `'min'` - 1,
- `'max'` - 1000,
- `'number'` - True
  \}
  
  Custom UI via json_schema_extra:
  >>> class Params(BaseModel):
  ...     model_size: str = Field(
  ...         default="medium",
  ...         json_schema_extra=\{
  ...             "formkit": "select",
  ...             "options": ["small", "medium", "large"],
  ...             "help": "Model size selection"
  ...         \}
  ...     )

#### get\_action\_ui\_schema

```python
def get_action_ui_schema(model: type[BaseModel],
                         action_name: str | None = None) -> dict[str, Any]
```

Get UI schema for an action's parameters.

Returns the schema in the format expected by the backend API.

**Arguments**:

- `model` - Pydantic model class for action parameters
- `action_name` - Optional action name for the response
  

**Returns**:

  Dict with action name and ui_schemas list
  

**Example**:

  >>> schema = get_action_ui_schema(TrainParams, 'train')
  >>> schema
  \{
- `'action'` - 'train',
- `'ui_schemas'` - [...]
  \}

