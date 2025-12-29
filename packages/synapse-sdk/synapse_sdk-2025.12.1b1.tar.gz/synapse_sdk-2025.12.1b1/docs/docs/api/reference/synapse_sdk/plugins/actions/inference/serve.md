---
sidebar_label: serve
title: synapse_sdk.plugins.actions.inference.serve
---

Base Ray Serve deployment class for inference endpoints.

## BaseServeDeployment Objects

```python
class BaseServeDeployment(ABC)
```

Base class for Ray Serve inference deployments.

Provides model loading with multiplexing support. Subclasses implement
_get_model() to load their specific model format and infer() to run
inference.

This class is designed to be used with Ray Serve's @serve.deployment
decorator and supports model multiplexing via @serve.multiplexed().

**Attributes**:

- `backend_url` - URL of the Synapse backend for model fetching.
- `_model_cache` - Internal cache for loaded models.
  

**Example**:

  >>> from ray import serve
  >>> from fastapi import FastAPI
  >>>
  >>> app = FastAPI()
  >>>
  >>> @serve.deployment
  >>> @serve.ingress(app)
  >>> class MyInference(BaseServeDeployment):
  ...     async def _get_model(self, model_info: dict) -> Any:
  ...         import torch
  ...         return torch.load(model_info['path'] / 'model.pt')
  ...
  ...     async def infer(self, inputs: list[dict]) -> list[dict]:
  ...         model = await self.get_model()
  ...         return [\{'prediction': model(inp)\} for inp in inputs]
  >>>
  >>> # Deploy with:
  >>> deployment = MyInference.bind(backend_url='https://api.example.com')
  >>> serve.run(deployment)

#### get\_model

```python
async def get_model() -> Any
```

Get the current model for inference.

Uses Ray Serve's multiplexing to load the appropriate model
based on the request's multiplexed model ID header.

**Returns**:

  Loaded model object.
  

**Notes**:

  This method uses Ray Serve's @serve.multiplexed() decorator
  internally. Ensure requests include the appropriate header.

#### infer

```python
@abstractmethod
async def infer(*args: Any, **kwargs: Any) -> Any
```

Run inference on inputs.

Override this method to implement your inference logic.
Use self.get_model() to obtain the loaded model.

**Arguments**:

- `*args` - Inference inputs (format depends on implementation).
- `**kwargs` - Additional inference parameters.
  

**Returns**:

  Inference results (format depends on implementation).
  

**Example**:

  >>> async def infer(self, inputs: list[dict]) -> list[dict]:
  ...     model = await self.get_model()
  ...     results = []
  ...     for inp in inputs:
  ...         prediction = model.predict(inp['data'])
  ...         results.append(\{'prediction': prediction.tolist()\})
  ...     return results

#### create\_serve\_multiplexed\_model\_id

```python
def create_serve_multiplexed_model_id(model_id: int | str,
                                      token: str,
                                      backend_url: str,
                                      tenant: str | None = None) -> str
```

Create a JWT-encoded model ID for serve multiplexing.

This helper creates the token that should be passed in the
'serve_multiplexed_model_id' header for inference requests.

**Arguments**:

- `model_id` - The model ID to encode.
- `token` - User access token for authentication.
- `backend_url` - Backend URL (used as JWT secret).
- `tenant` - Optional tenant identifier.
  

**Returns**:

  JWT-encoded model token string.
  

**Example**:

  >>> model_token = create_serve_multiplexed_model_id(
  ...     model_id=123,
  ...     token='user_access_token',
  ...     backend_url='https://api.example.com',
  ...     tenant='my-tenant',
  ... )
  >>> # Use in request headers:
  >>> headers = \{'serve_multiplexed_model_id': model_token\}

