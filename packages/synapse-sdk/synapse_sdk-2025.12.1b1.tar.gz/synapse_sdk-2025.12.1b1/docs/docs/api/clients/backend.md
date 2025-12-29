---
id: backend
title: BackendClient
sidebar_position: 1
---

# BackendClient

Main client for interacting with the Synapse backend API.

## Overview

The `BackendClient` provides comprehensive access to all backend operations including data management, plugin execution, annotations, and machine learning workflows. It aggregates functionality from multiple specialized mixins:

- **AnnotationClientMixin**: Task and annotation management
- **CoreClientMixin**: File upload and core operations
- **DataCollectionClientMixin**: Data collection and file management
- **HITLClientMixin**: Human-in-the-loop assignment operations
- **IntegrationClientMixin**: Plugin and job management
- **MLClientMixin**: Machine learning models and ground truth operations

## Constructor

```python
BackendClient(
    base_url: str,
    api_token: str = None,
    agent_token: str = None,
    timeout: dict = None
)
```

### Parameters

- **base_url** (`str`): The base URL of the Synapse backend API
- **api_token** (`str`, optional): API authentication token. Can also be set via `SYNAPSE_API_TOKEN` environment variable
- **agent_token** (`str`, optional): Agent authentication token. Can also be set via `SYNAPSE_AGENT_TOKEN` environment variable
- **timeout** (`dict`, optional): Custom timeout settings. Defaults to `{'connect': 5, 'read': 30}`

### Example

```python
from synapse_sdk.clients.backend import BackendClient

# Create client with explicit token
client = BackendClient(
    base_url="https://api.synapse.sh",
    api_token="your-api-token"
)

# Or use environment variables
import os
os.environ['SYNAPSE_API_TOKEN'] = "your-api-token"
client = BackendClient(base_url="https://api.synapse.sh")
```

## API Methods

### Annotation Operations

#### `get_project(pk)`

Get project details by ID.

```python
project = client.get_project(123)
```

#### `get_task(pk, params)`

Get task details with optional parameters.

```python
task = client.get_task(456, params={'expand': 'data_unit'})
```

#### `annotate_task_data(pk, data)`

Submit annotation data for a task.

```python
result = client.annotate_task_data(456, {
    'annotations': [
        {'type': 'bbox', 'coordinates': [10, 10, 100, 100]}
    ]
})
```

#### `list_tasks(params=None, url_conversion=None, list_all=False)`

List tasks with filtering and pagination.

```python
# Get tasks for a project
tasks = client.list_tasks(params={'project': 123})

# Get all tasks (handles pagination automatically)
all_tasks = client.list_tasks(list_all=True)
```

#### `create_tasks(data)`

Create new tasks.

```python
new_tasks = client.create_tasks([
    {'project': 123, 'data_unit': 789},
    {'project': 123, 'data_unit': 790}
])
```

#### `set_tags_tasks(data, params=None)`

Set tags for multiple tasks.

```python
client.set_tags_tasks({
    'task_ids': [456, 457],
    'tag_ids': [1, 2, 3]
})
```

### Core Operations

#### `create_chunked_upload(file_path)`

Upload large files using chunked upload for optimal performance.

```python
from pathlib import Path

result = client.create_chunked_upload(Path('/path/to/large_file.zip'))
print(f"Upload completed: {result}")
```

**Features:**

- Uses 50MB chunks for optimal performance
- Automatic retry and resume capability
- MD5 integrity verification
- Progress tracking support

### Data Collection Operations

#### `list_data_collection()`

List all available data collections.

```python
collections = client.list_data_collection()
```

#### `get_data_collection(data_collection_id)`

Get detailed information about a specific data collection.

```python
collection = client.get_data_collection(123)
file_specs = collection['file_specifications']
```

#### `create_data_file(file_path, use_chunked_upload=False)`

Create and upload a data file to the backend.

```python
from pathlib import Path

# Regular upload
data_file = client.create_data_file(Path('/path/to/file.jpg'))

# Chunked upload for large files
large_file = client.create_data_file(
    Path('/path/to/large_file.zip'),
    use_chunked_upload=True
)
```

#### `upload_data_file(organized_file, collection_id, use_chunked_upload=False)`

Upload organized file data to a collection.

```python
result = client.upload_data_file(
    organized_file={'files': {...}, 'meta': {...}},
    collection_id=123,
    use_chunked_upload=False
)
```

#### `create_data_units(uploaded_files)`

Create data units from uploaded files.

```python
data_units = client.create_data_units([
    {'id': 1, 'file': {...}},
    {'id': 2, 'file': {...}}
])
```

### HITL (Human-in-the-Loop) Operations

#### `get_assignment(pk)`

Get assignment details by ID.

```python
assignment = client.get_assignment(789)
```

#### `list_assignments(params=None, url_conversion=None, list_all=False)`

List assignments with filtering options.

```python
# Get assignments for a project
assignments = client.list_assignments(params={'project': 123})

# Get all assignments
all_assignments = client.list_assignments(list_all=True)
```

#### `set_tags_assignments(data, params=None)`

Set tags for multiple assignments.

```python
client.set_tags_assignments({
    'assignment_ids': [789, 790],
    'tag_ids': [1, 2]
})
```

### Integration Operations

#### `health_check_agent(token)`

Check agent health status.

```python
status = client.health_check_agent('agent-token-123')
```

#### `get_plugin(pk)` / `create_plugin(data)` / `update_plugin(pk, data)`

Manage plugins.

```python
# Get plugin
plugin = client.get_plugin(123)

# Create plugin
new_plugin = client.create_plugin({
    'name': 'My Plugin',
    'description': 'Plugin description'
})

# Update plugin
updated = client.update_plugin(123, {'description': 'Updated description'})
```

#### `run_plugin(pk, data)`

Execute a plugin with provided data.

```python
result = client.run_plugin(123, {
    'parameters': {'input': 'value'},
    'context': {...}
})
```

#### Plugin Release Management

```python
# Create plugin release
release = client.create_plugin_release({
    'plugin': 123,
    'version': '1.0.0',
    'file': open('/path/to/plugin.zip', 'rb')
})

# Get release details
release_info = client.get_plugin_release(456)
```

#### Job Management

```python
# List jobs
jobs = client.list_jobs(params={'status': 'running'})

# Get job details
job = client.get_job(789, params={'expand': 'logs'})

# Update job status
client.update_job(789, {'status': 'completed'})

# Get job console logs
logs = client.list_job_console_logs(789)
```

#### Storage Operations

```python
# List storages
storages = client.list_storages()

# Get storage details
storage = client.get_storage(123)

# Create storage
new_storage = client.create_storage({
    'name': 'My Storage',
    'provider': 'amazon_s3',
    'configuration': {...}
})
```

### Machine Learning Operations

#### `list_models(params=None)` / `get_model(pk, params=None, url_conversion=None)`

Manage ML models.

```python
# List models
models = client.list_models(params={'project': 123})

# Get model details
model = client.get_model(456, params={'expand': 'metrics'})
```

#### `create_model(data)`

Create a new ML model with file upload.

```python
new_model = client.create_model({
    'name': 'My Model',
    'project': 123,
    'file': '/path/to/model.pkl'
})
```

#### Ground Truth Operations

```python
# List ground truth events
events = client.list_ground_truth_events(
    params={'ground_truth_dataset_versions': [123]},
    list_all=True
)

# Get ground truth version
version = client.get_ground_truth_version(123)
```

## Storage Models

The backend client includes predefined models for storage operations:

### StorageCategory

- `INTERNAL`: Internal storage systems
- `EXTERNAL`: External storage providers

### StorageProvider

- `AMAZON_S3`: Amazon S3
- `AZURE`: Microsoft Azure Blob Storage
- `DIGITAL_OCEAN`: DigitalOcean Spaces
- `FILE_SYSTEM`: Local file system
- `FTP` / `SFTP`: FTP protocols
- `MINIO`: MinIO storage
- `GCP`: Google Cloud Storage

## Error Handling

All API methods may raise `ClientError` exceptions for various error conditions:

```python
from synapse_sdk.clients.exceptions import ClientError

try:
    project = client.get_project(999)
except ClientError as e:
    print(f"API Error: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"Response: {e.response}")
```

## Pagination

Methods supporting `list_all=True` will automatically handle pagination:

```python
# Manual pagination
tasks_page1 = client.list_tasks(params={'page': 1, 'page_size': 100})

# Automatic pagination (recommended)
all_tasks = client.list_tasks(list_all=True)
```

## URL Conversion

Some methods support URL conversion for file fields:

```python
# Custom URL conversion
tasks = client.list_tasks(
    url_conversion={'files': lambda url: f"https://cdn.example.com{url}"}
)
```

## See Also

- [AgentClient](./agent.md) - For agent-specific operations
- [BaseClient](./base.md) - Base client implementation
