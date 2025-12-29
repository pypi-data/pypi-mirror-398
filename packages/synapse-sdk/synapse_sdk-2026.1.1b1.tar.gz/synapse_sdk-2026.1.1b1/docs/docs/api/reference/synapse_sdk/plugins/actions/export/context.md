---
sidebar_label: context
title: synapse_sdk.plugins.actions.export.context
---

Export context for sharing state between workflow steps.

## ExportContext Objects

```python
@dataclass
class ExportContext(BaseStepContext)
```

Shared context passed between export workflow steps.

Extends BaseStepContext with export-specific state fields.
Carries parameters and accumulated state as the workflow
progresses through steps.

**Attributes**:

- `params` - Export parameters (from action params).
- `results` - Fetched results to export (populated by fetch step).
- `total_count` - Total number of items to export.
- `exported_count` - Number of items successfully exported.
- `output_path` - Path to export output file/directory.
  

**Example**:

  >>> context = ExportContext(
  ...     runtime_ctx=runtime_ctx,
  ...     params=\{'format': 'coco', 'filter': \{\}\},
  ... )
  >>> # Steps populate state as they execute
  >>> context.results = fetched_data

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

