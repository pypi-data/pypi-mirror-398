---
id: integration-mixin
title: IntegrationClientMixin
sidebar_position: 4
---

# IntegrationClientMixin

Provides plugin management, job execution, and system integration operations for the Synapse backend.

## Overview

The `IntegrationClientMixin` handles all operations related to plugins, jobs, agents, and storage management. This mixin is automatically included in the `BackendClient` and provides methods for system integration and automation workflows.

## Agent Operations

### `health_check_agent(token)`

Check the health status of an agent.

```python
# Check agent health
status = client.health_check_agent('agent-token-123')
print(f"Agent status: {status}")

# Verify agent connectivity
try:
    health = client.health_check_agent('my-agent-token')
    print("Agent is healthy and connected")
except ClientError as e:
    print(f"Agent health check failed: {e}")
```

**Parameters:**

- `token` (str): Agent authentication token

**Returns:**

- `dict`: Agent health status and connectivity information

## Plugin Management

### `get_plugin(pk)`

Retrieve detailed information about a specific plugin.

```python
plugin = client.get_plugin(123)
print(f"Plugin: {plugin['name']}")
print(f"Version: {plugin['version']}")
print(f"Description: {plugin['description']}")
print(f"Author: {plugin['author']}")
```

**Parameters:**

- `pk` (int): Plugin ID

**Returns:**

- `dict`: Complete plugin information including metadata and configuration

### `create_plugin(data)`

Create a new plugin in the system.

```python
plugin_data = {
    'name': 'My Custom Plugin',
    'description': 'A plugin for custom data processing',
    'version': '1.0.0',
    'author': 'Your Name',
    'category': 'data_processing',
    'configuration': {
        'parameters': {
            'threshold': {'type': 'float', 'default': 0.5},
            'max_items': {'type': 'int', 'default': 100}
        }
    }
}

new_plugin = client.create_plugin(plugin_data)
print(f"Created plugin with ID: {new_plugin['id']}")
```

**Parameters:**

- `data` (dict): Plugin configuration and metadata

**Plugin data structure:**

- `name` (str, required): Plugin name
- `description` (str): Plugin description
- `version` (str): Plugin version
- `author` (str): Plugin author
- `category` (str): Plugin category
- `configuration` (dict): Plugin configuration schema

**Returns:**

- `dict`: Created plugin with generated ID

### `update_plugin(pk, data)`

Update an existing plugin.

```python
# Update plugin description and version
updated_data = {
    'description': 'Updated plugin description',
    'version': '1.1.0',
    'configuration': {
        'parameters': {
            'threshold': {'type': 'float', 'default': 0.7},
            'max_items': {'type': 'int', 'default': 200},
            'new_param': {'type': 'string', 'default': 'default_value'}
        }
    }
}

updated_plugin = client.update_plugin(123, updated_data)
```

**Parameters:**

- `pk` (int): Plugin ID
- `data` (dict): Updated plugin data

**Returns:**

- `dict`: Updated plugin information

### `run_plugin(pk, data)`

Execute a plugin with specified parameters.

```python
# Run plugin with parameters
execution_data = {
    'parameters': {
        'threshold': 0.8,
        'max_items': 150,
        'input_path': '/data/input/',
        'output_path': '/data/output/'
    },
    'context': {
        'project_id': 123,
        'user_id': 456,
        'execution_mode': 'batch'
    }
}

result = client.run_plugin(123, execution_data)
print(f"Plugin execution started: {result['job_id']}")
```

**Parameters:**

- `pk` (int): Plugin ID
- `data` (dict): Execution parameters and context

**Execution data structure:**

- `parameters` (dict): Plugin-specific parameters
- `context` (dict): Execution context information

**Returns:**

- `dict`: Execution result with job information

## Plugin Release Management

### `get_plugin_release(pk, params=None)`

Get information about a specific plugin release.

```python
# Get release information
release = client.get_plugin_release(456)
print(f"Release {release['version']} for plugin {release['plugin']}")

# Get release with expanded plugin info
release = client.get_plugin_release(456, params={'expand': 'plugin'})
```

**Parameters:**

- `pk` (int): Plugin release ID
- `params` (dict, optional): Query parameters

**Returns:**

- `dict`: Plugin release information

### `create_plugin_release(data)`

Create a new plugin release with file upload.

```python
# Create plugin release
release_data = {
    'plugin': 123,
    'version': '2.0.0',
    'changelog': 'Added new features and bug fixes',
    'is_stable': True,
    'file': open('/path/to/plugin_v2.zip', 'rb')
}

new_release = client.create_plugin_release(release_data)
print(f"Created release: {new_release['id']}")
```

**Parameters:**

- `data` (dict): Release data including file

**Release data structure:**

- `plugin` (int, required): Plugin ID
- `version` (str, required): Release version
- `changelog` (str): Release notes
- `is_stable` (bool): Whether this is a stable release
- `file` (file object, required): Plugin package file

**Returns:**

- `dict`: Created plugin release information

## Job Management

### `get_job(pk, params=None)`

Get detailed information about a job.

```python
# Get basic job info
job = client.get_job(789)
print(f"Job {job['id']}: {job['status']}")

# Get job with logs
job = client.get_job(789, params={'expand': 'logs'})
print(f"Job logs: {job['logs']}")
```

**Parameters:**

- `pk` (int): Job ID
- `params` (dict, optional): Query parameters

**Common params:**

- `expand`: Include additional data (`logs`, `metrics`, `result`)

**Returns:**

- `dict`: Complete job information

### `list_jobs(params=None)`

List jobs with filtering options.

```python
# List all jobs
jobs = client.list_jobs()

# List jobs by status
running_jobs = client.list_jobs(params={'status': 'running'})

# List jobs for a specific plugin
plugin_jobs = client.list_jobs(params={'plugin': 123})

# List recent jobs
from datetime import datetime, timedelta
recent_date = (datetime.now() - timedelta(days=7)).isoformat()
recent_jobs = client.list_jobs(params={'created_after': recent_date})
```

**Parameters:**

- `params` (dict, optional): Filtering parameters

**Common filtering params:**

- `status`: Filter by job status (`queued`, `running`, `completed`, `failed`)
- `plugin`: Filter by plugin ID
- `created_after`: Filter by creation date
- `user`: Filter by user ID

**Returns:**

- `tuple`: (jobs_list, total_count)

### `update_job(pk, data)`

Update job status or metadata.

```python
# Update job status
client.update_job(789, {'status': 'completed'})

# Update job with result data
client.update_job(789, {
    'status': 'completed',
    'result': {
        'output_files': ['file1.txt', 'file2.txt'],
        'metrics': {'accuracy': 0.95, 'processing_time': 120}
    }
})

# Update job progress
client.update_job(789, {
    'progress': 75,
    'status': 'running',
    'metadata': {'current_step': 'processing_images'}
})
```

**Parameters:**

- `pk` (int): Job ID
- `data` (dict): Update data

**Updatable fields:**

- `status`: Job status
- `progress`: Progress percentage (0-100)
- `result`: Job result data
- `metadata`: Additional job metadata

**Returns:**

- `dict`: Updated job information

### `list_job_console_logs(pk)`

Get console logs for a specific job.

```python
# Get job console logs
logs = client.list_job_console_logs(789)
for log_entry in logs:
    print(f"[{log_entry['timestamp']}] {log_entry['level']}: {log_entry['message']}")
```

**Parameters:**

- `pk` (int): Job ID

**Returns:**

- `list`: Console log entries with timestamps and levels

## Storage Management

### `list_storages()`

List all available storage configurations.

```python
storages = client.list_storages()
for storage in storages:
    print(f"Storage: {storage['name']} ({storage['provider']})")
```

**Returns:**

- `list`: Available storage configurations

### `get_storage(pk)`

Get detailed information about a specific storage.

```python
storage = client.get_storage(123)
print(f"Storage: {storage['name']}")
print(f"Provider: {storage['provider']}")
print(f"Configuration: {storage['configuration']}")
```

**Parameters:**

- `pk` (int): Storage ID

**Returns:**

- `dict`: Complete storage configuration

### `create_storage(data)`

Create a new storage configuration.

```python
# Create Amazon S3 storage
s3_storage = client.create_storage({
    'name': 'My S3 Storage',
    'provider': 'amazon_s3',
    'category': 'external',
    'configuration': {
        'bucket_name': 'my-bucket',
        'region': 'us-west-2',
        'access_key_id': 'YOUR_ACCESS_KEY',
        'secret_access_key': 'YOUR_SECRET_KEY'
    }
})

# Create local file system storage
local_storage = client.create_storage({
    'name': 'Local Storage',
    'provider': 'file_system',
    'category': 'internal',
    'configuration': {
        'base_path': '/data/storage',
        'permissions': '755'
    }
})
```

**Parameters:**

- `data` (dict): Storage configuration

**Storage data structure:**

- `name` (str, required): Storage name
- `provider` (str, required): Storage provider type
- `category` (str): Storage category (`internal`, `external`)
- `configuration` (dict): Provider-specific configuration

**Supported providers:**

- `amazon_s3`: Amazon S3
- `azure`: Azure Blob Storage
- `gcp`: Google Cloud Storage
- `file_system`: Local file system
- `ftp`, `sftp`: FTP protocols
- `minio`: MinIO storage

**Returns:**

- `dict`: Created storage configuration

## Complete Integration Workflow

```python
from synapse_sdk.clients.backend import BackendClient
import time

def complete_plugin_workflow():
    """Complete workflow for plugin development and deployment."""
    client = BackendClient(
        base_url="https://api.synapse.sh",
        api_token="your-token"
    )

    # 1. Create plugin
    plugin_data = {
        'name': 'Image Processing Plugin',
        'description': 'Advanced image processing capabilities',
        'version': '1.0.0',
        'author': 'Development Team',
        'category': 'image_processing',
        'configuration': {
            'parameters': {
                'quality': {'type': 'float', 'default': 0.8},
                'format': {'type': 'string', 'default': 'jpeg'}
            }
        }
    }

    plugin = client.create_plugin(plugin_data)
    plugin_id = plugin['id']
    print(f"Created plugin: {plugin_id}")

    # 2. Create plugin release
    with open('/path/to/plugin.zip', 'rb') as plugin_file:
        release_data = {
            'plugin': plugin_id,
            'version': '1.0.0',
            'changelog': 'Initial release',
            'is_stable': True,
            'file': plugin_file
        }
        release = client.create_plugin_release(release_data)

    print(f"Created release: {release['id']}")

    # 3. Run plugin
    execution_data = {
        'parameters': {
            'quality': 0.9,
            'format': 'png'
        },
        'context': {
            'project_id': 123,
            'batch_size': 100
        }
    }

    job_result = client.run_plugin(plugin_id, execution_data)
    job_id = job_result['job_id']
    print(f"Started job: {job_id}")

    # 4. Monitor job progress
    while True:
        job = client.get_job(job_id)
        status = job['status']
        progress = job.get('progress', 0)

        print(f"Job {job_id}: {status} ({progress}%)")

        if status in ['completed', 'failed']:
            break

        time.sleep(5)  # Wait 5 seconds before checking again

    # 5. Get job logs if failed
    if status == 'failed':
        logs = client.list_job_console_logs(job_id)
        print("Job failed. Recent logs:")
        for log in logs[-10:]:  # Last 10 log entries
            print(f"  {log['timestamp']}: {log['message']}")
    else:
        print("Job completed successfully!")
        if 'result' in job:
            print(f"Result: {job['result']}")

    return plugin_id, job_id

# Run the workflow
if __name__ == "__main__":
    plugin_id, job_id = complete_plugin_workflow()
```

## Error Handling

```python
from synapse_sdk.clients.exceptions import ClientError

def robust_plugin_execution(plugin_id, parameters, max_retries=3):
    """Execute plugin with error handling and retries."""
    for attempt in range(max_retries):
        try:
            result = client.run_plugin(plugin_id, {
                'parameters': parameters,
                'context': {'retry_attempt': attempt}
            })
            return result
        except ClientError as e:
            if e.status_code == 404:
                print(f"Plugin {plugin_id} not found")
                break
            elif e.status_code == 400:
                print(f"Invalid parameters: {e.response}")
                break
            elif e.status_code >= 500:
                print(f"Server error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Unexpected error: {e}")
                break

    return None
```

## See Also

- [BackendClient](./backend.md) - Main backend client
- [AnnotationClientMixin](./annotation-mixin.md) - Task and annotation operations
- [MLClientMixin](./ml-mixin.md) - Machine learning operations
