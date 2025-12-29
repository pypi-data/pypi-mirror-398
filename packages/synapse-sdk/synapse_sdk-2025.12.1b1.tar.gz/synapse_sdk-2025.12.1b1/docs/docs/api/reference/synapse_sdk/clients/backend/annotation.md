---
sidebar_label: annotation
title: synapse_sdk.clients.backend.annotation
---

Annotation client mixin for project and task operations.

## AnnotationClientMixin Objects

```python
class AnnotationClientMixin()
```

Mixin for annotation-related API endpoints.

Provides methods for managing projects, tasks, and task tags.

#### get\_project

```python
def get_project(project_id: int) -> dict[str, Any]
```

Get project details by ID.

**Arguments**:

- `project_id` - Project ID.
  

**Returns**:

  Project data including configuration and statistics.

#### get\_task

```python
def get_task(task_id: int,
             *,
             params: dict[str, Any] | None = None) -> dict[str, Any]
```

Get task details by ID.

**Arguments**:

- `task_id` - Task ID.
- `params` - Optional query parameters (e.g., expand, fields).
  

**Returns**:

  Task data including annotations and metadata.

#### annotate\_task\_data

```python
def annotate_task_data(task_id: int, data: dict[str, Any]) -> dict[str, Any]
```

Submit annotation data for a task.

**Arguments**:

- `task_id` - Task ID to annotate.
- `data` - Annotation data payload.
  

**Returns**:

  Updated task data.

#### get\_task\_tag

```python
def get_task_tag(tag_id: int) -> dict[str, Any]
```

Get task tag details by ID.

**Arguments**:

- `tag_id` - Tag ID.
  

**Returns**:

  Tag data including name and color.

#### list\_task\_tags

```python
def list_task_tags(params: dict[str, Any] | None = None) -> dict[str, Any]
```

List available task tags.

**Arguments**:

- `params` - Optional query parameters for filtering.
  

**Returns**:

  Paginated list of task tags.

#### list\_tasks

```python
def list_tasks(params: dict[str, Any] | None = None,
               *,
               url_conversion: dict[str, Any] | None = None,
               list_all: bool = False) -> dict[str, Any] | tuple[Any, int]
```

List tasks with optional pagination.

**Arguments**:

- `params` - Query parameters for filtering (project, status, etc.).
- `url_conversion` - URL-to-path conversion config for file fields.
- `list_all` - If True, returns (generator, count) for all results.
  

**Returns**:

  Paginated task list, or (generator, count) if list_all=True.
  

**Example**:

  >>> # Get first page
  >>> tasks = client.list_tasks(\{'project': 123\})
  >>> # Get all tasks as generator
  >>> tasks_gen, count = client.list_tasks(\{'project': 123\}, list_all=True)

#### create\_tasks

```python
def create_tasks(
        data: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]
```

Create one or more annotation tasks.

**Arguments**:

- `data` - Task data or list of task data.
  

**Returns**:

  Created task(s) response.
  

**Example**:

  >>> client.create_tasks(\{
  ...     'project': 123,
  ...     'data': [\{'image': 'path/to/image.jpg'\}]
  ... \})

#### set\_tags\_tasks

```python
def set_tags_tasks(data: dict[str, Any],
                   *,
                   params: dict[str, Any] | None = None) -> dict[str, Any]
```

Set tags on multiple tasks.

**Arguments**:

- `data` - Tag assignment data with 'ids', 'tags', and 'action'.
- `params` - Optional query parameters.
  

**Returns**:

  Operation result.
  

**Example**:

  >>> client.set_tags_tasks(\{
  ...     'ids': [1, 2, 3],
  ...     'tags': [10, 20],
  ...     'action': 'add'  # or 'remove'
  ... \})

