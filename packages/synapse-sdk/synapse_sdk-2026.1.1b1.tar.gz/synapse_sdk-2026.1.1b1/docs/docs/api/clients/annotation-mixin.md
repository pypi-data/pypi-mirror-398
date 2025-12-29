---
id: annotation-mixin
title: AnnotationClientMixin
sidebar_position: 2
---

# AnnotationClientMixin

Provides annotation and task management operations for the Synapse backend.

## Overview

The `AnnotationClientMixin` handles all operations related to tasks, annotations, projects, and task tagging. This mixin is automatically included in the `BackendClient` and provides methods for annotation workflows.

## Project Operations

### `get_project(pk)`

Retrieve detailed information about a specific project.

```python
project = client.get_project(123)
print(f"Project: {project['name']}")
print(f"Description: {project['description']}")
```

**Parameters:**

- `pk` (int): Project ID

**Returns:**

- `dict`: Project details including configuration, metadata, and settings

## Task Operations

### `get_task(pk, params)`

Get detailed information about a specific task.

```python
# Basic task details
task = client.get_task(456)

# Task with expanded data unit
task = client.get_task(456, params={'expand': 'data_unit'})

# Task with multiple expansions
task = client.get_task(456, params={
    'expand': ['data_unit', 'assignment', 'annotations']
})
```

**Parameters:**

- `pk` (int): Task ID
- `params` (dict): Query parameters for filtering and expansion

**Common params:**

- `expand`: List or string of related objects to include
- `include_annotations`: Whether to include annotation data

### `annotate_task_data(pk, data)`

Submit annotation data for a task.

```python
# Submit bounding box annotations
annotation_data = {
    'annotations': [
        {
            'type': 'bbox',
            'coordinates': [10, 10, 100, 100],
            'label': 'person',
            'confidence': 0.95
        },
        {
            'type': 'polygon',
            'points': [[0, 0], [50, 0], [50, 50], [0, 50]],
            'label': 'vehicle'
        }
    ],
    'metadata': {
        'annotator_id': 'user123',
        'timestamp': '2023-10-01T12:00:00Z'
    }
}

result = client.annotate_task_data(456, annotation_data)
```

**Parameters:**

- `pk` (int): Task ID
- `data` (dict): Annotation data structure

**Returns:**

- `dict`: Updated task with submitted annotations

### `list_tasks(params=None, url_conversion=None, list_all=False)`

List tasks with filtering and pagination support.

```python
# List tasks for a specific project
tasks = client.list_tasks(params={'project': 123})

# List tasks with status filter
tasks = client.list_tasks(params={
    'project': 123,
    'status': 'pending'
})

# Get all tasks (handles pagination automatically)
all_tasks = client.list_tasks(list_all=True)

# List tasks with custom URL conversion for files
tasks = client.list_tasks(
    params={'project': 123},
    url_conversion={'files': lambda url: f"https://cdn.example.com{url}"}
)
```

**Parameters:**

- `params` (dict, optional): Filtering parameters
- `url_conversion` (dict, optional): Custom URL conversion for file fields
- `list_all` (bool): If True, automatically handles pagination to get all results

**Common filtering params:**

- `project`: Filter by project ID
- `status`: Filter by task status (`pending`, `in_progress`, `completed`)
- `assignee`: Filter by assigned user ID
- `created_after`: Filter by creation date
- `search`: Text search in task content

**Returns:**

- `tuple`: (tasks_list, total_count) if `list_all=False`
- `list`: All tasks if `list_all=True`

### `create_tasks(data)`

Create one or more new tasks.

```python
# Create single task
new_task = client.create_tasks({
    'project': 123,
    'data_unit': 789,
    'priority': 'high',
    'metadata': {'batch': 'batch_001'}
})

# Create multiple tasks
new_tasks = client.create_tasks([
    {'project': 123, 'data_unit': 789},
    {'project': 123, 'data_unit': 790},
    {'project': 123, 'data_unit': 791}
])
```

**Parameters:**

- `data` (dict or list): Task data or list of task data

**Task data structure:**

- `project` (int, required): Project ID
- `data_unit` (int, required): Data unit ID
- `priority` (str, optional): Task priority (`low`, `normal`, `high`)
- `assignee` (int, optional): User ID to assign task to
- `metadata` (dict, optional): Additional task metadata

**Returns:**

- `dict` or `list`: Created task(s) with generated IDs

### `set_tags_tasks(data, params=None)`

Set tags for multiple tasks in batch.

```python
# Set tags for multiple tasks
client.set_tags_tasks({
    'task_ids': [456, 457, 458],
    'tag_ids': [1, 2, 3]  # Tag IDs to apply
})

# Set tags with additional parameters
client.set_tags_tasks(
    {
        'task_ids': [456, 457],
        'tag_ids': [1, 2]
    },
    params={'replace': True}  # Replace existing tags
)
```

**Parameters:**

- `data` (dict): Batch tagging data
- `params` (dict, optional): Additional parameters

**Data structure:**

- `task_ids` (list): List of task IDs to tag
- `tag_ids` (list): List of tag IDs to apply

**Optional params:**

- `replace` (bool): If True, replace existing tags; if False, add to existing

## Task Tag Operations

### `get_task_tag(pk)`

Get details about a specific task tag.

```python
tag = client.get_task_tag(123)
print(f"Tag: {tag['name']} - {tag['description']}")
```

**Parameters:**

- `pk` (int): Tag ID

**Returns:**

- `dict`: Tag details including name, description, and meta

### `list_task_tags(params)`

List available task tags with filtering.

```python
# List all tags
tags = client.list_task_tags({})

# List tags for a specific project
project_tags = client.list_task_tags({
    'project': 123
})

# Search tags by name
search_tags = client.list_task_tags({
    'search': 'quality'
})
```

**Parameters:**

- `params` (dict): Filtering parameters

**Common filtering params:**

- `project`: Filter by project ID
- `search`: Text search in tag names
- `color`: Filter by tag color

**Returns:**

- `tuple`: (tags_list, total_count)

## Example Workflows

### Complete Annotation Workflow

```python
from synapse_sdk.clients.backend import BackendClient

client = BackendClient(
    base_url="https://api.synapse.sh",
    api_token="your-token"
)

# 1. Get project details
project = client.get_project(123)
print(f"Working on project: {project['name']}")

# 2. List pending tasks
pending_tasks = client.list_tasks(params={
    'project': 123,
    'status': 'pending'
})

# 3. Process first task
if pending_tasks[0]:
    task = pending_tasks[0][0]  # First task from results
    task_id = task['id']

    # Get detailed task info
    detailed_task = client.get_task(task_id, params={'expand': 'data_unit'})

    # Submit annotations
    annotations = {
        'annotations': [
            {
                'type': 'bbox',
                'coordinates': [10, 10, 100, 100],
                'label': 'person'
            }
        ]
    }

    result = client.annotate_task_data(task_id, annotations)
    print(f"Annotations submitted for task {task_id}")

    # Add quality tag
    quality_tags = client.list_task_tags({'search': 'quality'})
    if quality_tags[0]:
        tag_id = quality_tags[0][0]['id']
        client.set_tags_tasks({
            'task_ids': [task_id],
            'tag_ids': [tag_id]
        })
```

### Batch Task Creation

```python
# Create tasks for multiple data units
data_units = [789, 790, 791, 792, 793]

tasks_data = []
for data_unit_id in data_units:
    tasks_data.append({
        'project': 123,
        'data_unit': data_unit_id,
        'priority': 'normal',
        'metadata': {
            'batch': 'automated_batch_001',
            'source': 'data_import'
        }
    })

# Create all tasks in one request
created_tasks = client.create_tasks(tasks_data)
print(f"Created {len(created_tasks)} tasks")

# Get IDs of created tasks
task_ids = [task['id'] for task in created_tasks]

# Apply initial tags
initial_tags = client.list_task_tags({'search': 'new'})
if initial_tags[0]:
    tag_id = initial_tags[0][0]['id']
    client.set_tags_tasks({
        'task_ids': task_ids,
        'tag_ids': [tag_id]
    })
```

## Error Handling

```python
from synapse_sdk.clients.exceptions import ClientError

try:
    task = client.get_task(999999)
except ClientError as e:
    if e.status_code == 404:
        print("Task not found")
    elif e.status_code == 403:
        print("Permission denied")
    else:
        print(f"API Error: {e}")
```

## See Also

- [BackendClient](./backend.md) - Main backend client
- [HITLClientMixin](./hitl-mixin.md) - Human-in-the-loop operations
- [DataCollectionClientMixin](./data-collection-mixin.md) - Data management
