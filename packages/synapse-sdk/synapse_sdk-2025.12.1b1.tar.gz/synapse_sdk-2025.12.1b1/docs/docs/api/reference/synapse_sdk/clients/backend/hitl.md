---
sidebar_label: hitl
title: synapse_sdk.clients.backend.hitl
---

HITL (Human-in-the-Loop) client mixin for assignment operations.

## HITLClientMixin Objects

```python
class HITLClientMixin()
```

Mixin for HITL-related API endpoints.

Provides methods for managing annotation assignments.

#### get\_assignment

```python
def get_assignment(assignment_id: int) -> dict[str, Any]
```

Get assignment details by ID.

**Arguments**:

- `assignment_id` - Assignment ID.
  

**Returns**:

  Assignment data including task and annotator info.

#### list\_assignments

```python
def list_assignments(
        params: dict[str, Any] | None = None,
        *,
        url_conversion: dict[str, Any] | None = None,
        list_all: bool = False) -> dict[str, Any] | tuple[Any, int]
```

List assignments with optional pagination.

**Arguments**:

- `params` - Query parameters for filtering.
- `url_conversion` - URL-to-path conversion config.
- `list_all` - If True, returns (generator, count).
  

**Returns**:

  Paginated list or (generator, count).

#### set\_tags\_assignments

```python
def set_tags_assignments(
        data: dict[str, Any],
        *,
        params: dict[str, Any] | None = None) -> dict[str, Any]
```

Set tags on multiple assignments.

**Arguments**:

- `data` - Tag assignment data with 'ids', 'tags', and 'action'.
- `params` - Optional query parameters.
  

**Returns**:

  Operation result.
  

**Example**:

  >>> client.set_tags_assignments(\{
  ...     'ids': [1, 2, 3],
  ...     'tags': [10, 20],
  ...     'action': 'add'  # or 'remove'
  ... \})

