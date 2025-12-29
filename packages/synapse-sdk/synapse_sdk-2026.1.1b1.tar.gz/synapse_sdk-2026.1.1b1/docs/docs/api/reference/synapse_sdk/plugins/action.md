---
sidebar_label: action
title: synapse_sdk.plugins.action
---

## BaseAction Objects

```python
class BaseAction(ABC, Generic[P])
```

Base class for plugin actions.

Subclass this to create class-based actions. For function-based actions,
use the @action decorator instead.

Class Attributes:
action_name: Action name used for invocation.
category: Category for grouping actions (e.g., 'neural_net', 'export').
params_model: Pydantic model class for parameter validation.

Instance Attributes:
params: Pre-validated parameters (Pydantic model instance).
ctx: Runtime context with logger, env, etc.

**Example**:

  >>> class TrainParams(BaseModel):
  ...     epochs: int = 10
  ...     learning_rate: float = 0.001
  >>>
  >>> # Minimal - action_name/category injected from config.yaml
  >>> class TrainAction(BaseAction[TrainParams]):
  ...     params_model = TrainParams
  ...
  ...     def execute(self) -> dict:
  ...         return \{'status': 'completed'\}
  >>>
  >>> # Explicit - override config values
  >>> class TrainAction(BaseAction[TrainParams]):
  ...     action_name = 'train'
  ...     category = 'neural_net'
  ...     params_model = TrainParams
  ...
  ...     def execute(self) -> dict:
  ...         return \{'status': 'completed'\}

#### execute

```python
@abstractmethod
def execute() -> Any
```

Execute the action.

Implement this method with your action's main logic.
Use self.params for input and self.ctx for dependencies.

**Returns**:

  Action result (should be serializable).
  

**Raises**:

- `ExecutionError` - If execution fails.

#### logger

```python
@property
def logger()
```

Access the logger from context.

#### log

```python
def log(event: str, data: dict[str, Any], file: str | None = None) -> None
```

Log an event with data.

**Arguments**:

- `event` - Event name/type.
- `data` - Dictionary of event data.
- `file` - Optional file path associated with the event.

#### set\_progress

```python
def set_progress(current: int,
                 total: int,
                 category: str | None = None) -> None
```

Set progress for the current operation.

**Arguments**:

- `current` - Current progress value (0 to total).
- `total` - Total progress value.
- `category` - Optional category name for multi-phase progress.

#### set\_metrics

```python
def set_metrics(value: dict[str, Any], category: str) -> None
```

Set metrics for a category.

**Arguments**:

- `value` - Dictionary of metric values.
- `category` - Non-empty category name.

