---
sidebar_label: context
title: synapse_sdk.plugins.actions.train.context
---

Train context for sharing state between workflow steps.

## TrainContext Objects

```python
@dataclass
class TrainContext(BaseStepContext)
```

Shared context passed between training workflow steps.

Extends BaseStepContext with training-specific state fields.
Carries parameters and accumulated state as the workflow
progresses through steps.

**Attributes**:

- `params` - Training parameters (from action params).
- `dataset` - Loaded dataset (populated by dataset step).
- `model_path` - Path to trained model (populated by training step).
- `model` - Created model metadata (populated by upload step).
  

**Example**:

  >>> context = TrainContext(
  ...     runtime_ctx=runtime_ctx,
  ...     params=\{'dataset_id': 1, 'epochs': 10\},
  ... )
  >>> # Steps populate state as they execute
  >>> context.dataset = loaded_dataset

#### client

```python
@property
def client() -> BackendClient
```

Backend client from runtime context.

**Returns**:

  BackendClient instance.
  

**Raises**:

- `RuntimeError` - If no client in runtime context.

