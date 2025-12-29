---
sidebar_label: context
title: synapse_sdk.plugins.actions.upload.context
---

Upload context for sharing state between workflow steps.

## UploadContext Objects

```python
@dataclass
class UploadContext(BaseStepContext)
```

Shared context passed between upload workflow steps.

Extends BaseStepContext with upload-specific state fields.
Carries parameters and accumulated state as the workflow
progresses through steps.

**Attributes**:

- `params` - Upload parameters (from action params).
- `storage` - Storage configuration (populated by init step).
- `pathlib_cwd` - Working directory path (populated by init step).
- `organized_files` - Files organized for upload (populated by organize step).
- `uploaded_files` - Successfully uploaded files (populated by upload step).
- `data_units` - Created data units (populated by generate step).
  

**Example**:

  >>> context = UploadContext(
  ...     runtime_ctx=runtime_ctx,
  ...     params=\{'storage': 1, 'path': '/data'\},
  ... )
  >>> # Steps populate state as they execute
  >>> context.organized_files.append(\{'path': 'file1.jpg'\})

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

