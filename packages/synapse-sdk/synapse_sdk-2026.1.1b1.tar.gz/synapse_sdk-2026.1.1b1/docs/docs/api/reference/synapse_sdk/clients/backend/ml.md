---
sidebar_label: ml
title: synapse_sdk.clients.backend.ml
---

ML client mixin for model and ground truth operations.

## MLClientMixin Objects

```python
class MLClientMixin()
```

Mixin for ML-related API endpoints.

Provides methods for managing models and ground truth data.

#### list\_models

```python
def list_models(params: dict[str, Any] | None = None) -> dict[str, Any]
```

List models with optional filtering.

**Arguments**:

- `params` - Query parameters for filtering.
  

**Returns**:

  Paginated model list.

#### get\_model

```python
def get_model(model_id: int,
              *,
              params: dict[str, Any] | None = None,
              url_conversion: dict[str, Any] | None = None) -> dict[str, Any]
```

Get model details by ID.

**Arguments**:

- `model_id` - Model ID.
- `params` - Optional query parameters.
- `url_conversion` - URL-to-path conversion config.
  

**Returns**:

  Model data including file URL and metadata.

#### create\_model

```python
def create_model(data: dict[str, Any],
                 *,
                 file: str | Path | None = None) -> dict[str, Any]
```

Create a new model with file upload.

Large files are automatically uploaded using chunked upload.

**Arguments**:

- `data` - Model metadata (name, plugin, version, etc.).
- `file` - Model file to upload (uses chunked upload).
  

**Returns**:

  Created model data.
  

**Example**:

  >>> client.create_model(
  ...     \{'name': 'My Model', 'plugin': 123\},
  ...     file='/path/to/model.pt'
  ... )

#### list\_ground\_truth\_events

```python
def list_ground_truth_events(
        params: dict[str, Any] | None = None,
        *,
        url_conversion: dict[str, Any] | None = None,
        list_all: bool = False) -> dict[str, Any] | tuple[Any, int]
```

List ground truth events.

**Arguments**:

- `params` - Query parameters for filtering.
- `url_conversion` - URL-to-path conversion config.
- `list_all` - If True, returns (generator, count).
  

**Returns**:

  Paginated list or (generator, count).

#### get\_ground\_truth\_version

```python
def get_ground_truth_version(version_id: int) -> dict[str, Any]
```

Get ground truth dataset version by ID.

**Arguments**:

- `version_id` - Version ID.
  

**Returns**:

  Version data including file manifest.

