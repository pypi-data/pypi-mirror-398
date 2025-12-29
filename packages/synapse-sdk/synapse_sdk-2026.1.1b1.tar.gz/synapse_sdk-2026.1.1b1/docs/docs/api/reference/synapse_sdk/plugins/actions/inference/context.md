---
sidebar_label: context
title: synapse_sdk.plugins.actions.inference.context
---

Inference context for step-based workflows.

## InferenceContext Objects

```python
@dataclass
class InferenceContext(BaseStepContext)
```

Context for inference action step-based workflows.

Extends BaseStepContext with inference-specific state including
model information, request/response tracking, and batch processing.

**Attributes**:

- `params` - Action parameters dict.
- `model_id` - ID of the model being used for inference.
- `model` - Loaded model information from backend.
- `model_path` - Local path to downloaded/extracted model.
- `requests` - Input requests to process.
- `results` - Inference results.
- `batch_size` - Batch size for processing.
- `processed_count` - Number of processed items.
  

**Example**:

  >>> context = InferenceContext(
  ...     runtime_ctx=self.ctx,
  ...     params=\{'model_id': 123\},
  ...     model_id=123,
  ... )
  >>> context.results.append(\{'prediction': 0.95\})

## DeploymentContext Objects

```python
@dataclass
class DeploymentContext(BaseStepContext)
```

Context for deployment action step-based workflows.

Extends BaseStepContext with deployment-specific state including
model information, serve application configuration, and deployment status.

**Attributes**:

- `params` - Action parameters dict.
- `model_id` - ID of the model to deploy.
- `model` - Model information from backend.
- `model_path` - Local path to model artifacts.
- `serve_app_name` - Name of the Ray Serve application.
- `serve_app_id` - ID of the created serve application.
- `route_prefix` - URL route prefix for the deployment.
- `ray_actor_options` - Ray actor configuration options.
- `deployed` - Whether deployment succeeded.
  

**Example**:

  >>> context = DeploymentContext(
  ...     runtime_ctx=self.ctx,
  ...     params=\{'model_id': 123\},
  ...     serve_app_name='my-model-v1',
  ... )

