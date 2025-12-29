---
id: index
title: Client APIs
sidebar_position: 1
---

# Client APIs

The Synapse SDK provides comprehensive client libraries for interacting with various backend services and systems. This section documents all available client APIs and their usage.

## Overview

The client APIs are organized into several categories:

### Core Clients

- **[BackendClient](./backend.md)** - Main client for Synapse backend operations
- **[BaseClient](./base.md)** - Base client with common functionality
- **[AgentClient](./agent.md)** - Agent-specific operations
- **[RayClient](./ray.md)** - Ray distributed computing integration

### Backend Client Mixins

The BackendClient is composed of several specialized mixins that provide focused functionality:

- **[AnnotationClientMixin](./annotation-mixin.md)** - Task and annotation management
- **[CoreClientMixin](./core-mixin.md)** - Core file upload operations
- **[DataCollectionClientMixin](./data-collection-mixin.md)** - Data collection and file management
- **[HITLClientMixin](./hitl-mixin.md)** - Human-in-the-loop workflows
- **[IntegrationClientMixin](./integration-mixin.md)** - Plugin and job management
- **[MLClientMixin](./ml-mixin.md)** - Machine learning operations

## Quick Start

### Basic Backend Client Usage

```python
from synapse_sdk.clients.backend import BackendClient

# Initialize client
client = BackendClient(
    base_url="https://api.synapse.sh",
    api_token="your-api-token"
)

# Use annotation operations
tasks = client.list_tasks(params={'project': 123})

# Use data collection operations
collections = client.list_data_collection()

# Use ML operations
models = client.list_models(params={'project': 123})
```

### Environment Configuration

```python
import os

# Set environment variables
os.environ['SYNAPSE_API_TOKEN'] = "your-api-token"
os.environ['SYNAPSE_AGENT_TOKEN'] = "your-agent-token"

# Client will automatically use environment variables
client = BackendClient(base_url="https://api.synapse.sh")
```

## Authentication

All clients support multiple authentication methods:

### API Token Authentication

```python
client = BackendClient(
    base_url="https://api.synapse.sh",
    api_token="your-api-token"
)
```

### Environment Variable Authentication

```python
# Set SYNAPSE_API_TOKEN environment variable
client = BackendClient(base_url="https://api.synapse.sh")
```

### Agent Token Authentication (for agents)

```python
client = BackendClient(
    base_url="https://api.synapse.sh",
    agent_token="your-agent-token"
)
```

## Common Patterns

### Error Handling

```python
from synapse_sdk.clients.exceptions import ClientError

try:
    result = client.get_project(123)
except ClientError as e:
    if e.status_code == 404:
        print("Project not found")
    elif e.status_code == 403:
        print("Permission denied")
    else:
        print(f"API Error: {e}")
```

### Pagination

```python
# Manual pagination
page1 = client.list_tasks(params={'page': 1, 'page_size': 50})

# Automatic pagination (recommended)
all_tasks = client.list_tasks(list_all=True)
```

### Batch Operations

```python
# Create multiple tasks
tasks_data = [
    {'project': 123, 'data_unit': 789},
    {'project': 123, 'data_unit': 790},
    {'project': 123, 'data_unit': 791}
]
created_tasks = client.create_tasks(tasks_data)

# Set tags for multiple assignments
client.set_tags_assignments({
    'assignment_ids': [1, 2, 3],
    'tag_ids': [10, 11]
})
```

### File Operations

```python
from pathlib import Path

# Upload large files with chunked upload
result = client.create_chunked_upload(Path('/path/to/large_file.zip'))

# Create data file
data_file = client.create_data_file(
    Path('/path/to/data.jpg'),
    use_chunked_upload=True
)
```

## Client Capabilities by Use Case

### Annotation Workflows

Use **AnnotationClientMixin** for:

- Managing annotation projects
- Creating and assigning tasks
- Submitting annotation data
- Task tagging and organization

**Key Methods:**

- `list_tasks()`, `create_tasks()`, `annotate_task_data()`
- `get_project()`, `set_tags_tasks()`

### Data Management

Use **DataCollectionClientMixin** for:

- Managing data collections
- Uploading files and datasets
- Creating data units
- Batch data processing

**Key Methods:**

- `list_data_collection()`, `get_data_collection()`
- `create_data_file()`, `upload_data_file()`
- `create_data_units()`

### Human-in-the-Loop

Use **HITLClientMixin** for:

- Managing human review assignments
- Quality control workflows
- Assignment distribution
- Performance analytics

**Key Methods:**

- `list_assignments()`, `get_assignment()`
- `set_tags_assignments()`

### System Integration

Use **IntegrationClientMixin** for:

- Plugin development and management
- Job execution and monitoring
- Storage configuration
- Agent health monitoring

**Key Methods:**

- `create_plugin()`, `run_plugin()`
- `list_jobs()`, `update_job()`
- `create_storage()`, `health_check_agent()`

### Machine Learning

Use **MLClientMixin** for:

- Model management and deployment
- Ground truth data operations
- Model evaluation workflows
- Training data preparation

**Key Methods:**

- `create_model()`, `list_models()`
- `list_ground_truth_events()`, `get_ground_truth_version()`

### Core Operations

Use **CoreClientMixin** for:

- Large file uploads
- Chunked upload operations
- File integrity verification

**Key Methods:**

- `create_chunked_upload()`

## Complete Workflow Examples

### End-to-End Data Processing

```python
def complete_data_workflow():
    client = BackendClient(
        base_url="https://api.synapse.sh",
        api_token="your-token"
    )

    # 1. Data ingestion
    collection = client.get_data_collection(123)
    data_file = client.create_data_file(Path('/data/image.jpg'))

    # 2. Task creation
    tasks = client.create_tasks([
        {'project': 123, 'data_unit': data_file['data_unit_id']}
    ])

    # 3. Assignment management
    assignments = client.list_assignments(params={'project': 123})

    # 4. Model operations
    models = client.list_models(params={'project': 123})

    return {
        'data_file': data_file,
        'tasks': tasks,
        'assignments': assignments,
        'models': models
    }
```

### Plugin Development and Deployment

```python
def plugin_deployment_workflow():
    client = BackendClient(
        base_url="https://api.synapse.sh",
        api_token="your-token"
    )

    # 1. Create plugin
    plugin = client.create_plugin({
        'name': 'My Plugin',
        'description': 'Custom processing plugin'
    })

    # 2. Create release
    with open('plugin.zip', 'rb') as f:
        release = client.create_plugin_release({
            'plugin': plugin['id'],
            'version': '1.0.0',
            'file': f
        })

    # 3. Execute plugin
    job = client.run_plugin(plugin['id'], {
        'parameters': {'threshold': 0.8}
    })

    # 4. Monitor execution
    job_status = client.get_job(job['job_id'])

    return {
        'plugin': plugin,
        'release': release,
        'job': job_status
    }
```

## Best Practices

### Performance Optimization

- Use `list_all=True` for complete datasets to handle pagination automatically
- Use chunked upload for files larger than 50MB
- Implement retry logic for critical operations
- Use batch operations when available

### Error Handling

- Always wrap API calls in try-catch blocks
- Check for specific error codes (404, 403, 429, 500)
- Implement exponential backoff for rate limiting
- Log errors with sufficient context

### Resource Management

- Close file handles promptly
- Use context managers for file operations
- Monitor memory usage with large uploads
- Clean up temporary resources

### Security

- Store API tokens securely (environment variables)
- Use HTTPS endpoints only
- Validate file paths and inputs
- Implement proper access controls

## Migration Guide

When migrating from older SDK versions:

1. **Update imports**: New mixin structure may require import updates
2. **Check method signatures**: Some methods may have updated parameters
3. **Error handling**: Error types and status codes may have changed
4. **Configuration**: Authentication methods may have been enhanced

## Troubleshooting

### Common Issues

**Authentication Errors (401/403)**

- Verify API token is correct and not expired
- Check token permissions for the requested operations
- Ensure correct base URL

**Rate Limiting (429)**

- Implement exponential backoff
- Reduce request frequency
- Use batch operations when available

**File Upload Failures**

- Check file size limits
- Verify file permissions
- Use chunked upload for large files
- Check network connectivity

**Connection Timeouts**

- Increase timeout settings
- Check network stability
- Verify server availability

## Support

For additional support:

- Check the [troubleshooting guide](../../troubleshooting.md)
- Review [examples](../../examples/index.md)
- Consult the [FAQ](../../faq.md)
