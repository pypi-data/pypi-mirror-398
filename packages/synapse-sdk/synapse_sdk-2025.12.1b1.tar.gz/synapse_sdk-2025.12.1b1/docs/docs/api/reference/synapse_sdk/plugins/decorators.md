---
sidebar_label: decorators
title: synapse_sdk.plugins.decorators
---

#### action

```python
def action(name: str | None = None,
           description: str = '',
           params: type[BaseModel] | None = None) -> Callable[[F], F]
```

Decorator to register a function as a plugin action.

Use this decorator to define function-based actions. The decorated function
should accept (params, context) arguments where params is a Pydantic model
instance and context is a RunContext.

**Arguments**:

- `name` - Action name (defaults to function name).
- `description` - Human-readable description of the action.
- `params` - Pydantic model class for parameter validation.
  

**Returns**:

  Decorated function with action metadata attached.
  

**Example**:

  >>> from pydantic import BaseModel
  >>> from synapse_sdk.plugins.decorators import action
  >>>
  >>> class TrainParams(BaseModel):
  ...     epochs: int = 10
  ...     learning_rate: float = 0.001
  >>>
  >>> @action(params=TrainParams, description='Train a model')
  ... def train(params: TrainParams, context: RunContext) -> dict:
  ...     # Training logic
  ...     return \{'epochs_trained': params.epochs\}
  >>>
  >>> # Access action metadata
  >>> train._action_name  # 'train'
  >>> train._action_params  # TrainParams

