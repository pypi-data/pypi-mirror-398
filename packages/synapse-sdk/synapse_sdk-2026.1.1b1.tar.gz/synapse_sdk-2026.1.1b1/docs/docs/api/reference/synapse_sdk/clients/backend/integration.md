---
sidebar_label: integration
title: synapse_sdk.clients.backend.integration
---

Integration client mixin for plugin, job, and storage operations.

## IntegrationClientMixin Objects

```python
class IntegrationClientMixin()
```

Mixin for integration-related API endpoints.

Provides methods for managing plugins, jobs, logs, and serve applications.

#### health\_check\_agent

```python
def health_check_agent(agent_token: str) -> dict[str, Any]
```

Check agent health and connectivity.

**Arguments**:

- `agent_token` - Agent authentication token.
  

**Returns**:

  Agent health status and metadata.

#### get\_plugin

```python
def get_plugin(plugin_id: int) -> dict[str, Any]
```

Get plugin details by ID.

**Arguments**:

- `plugin_id` - Plugin ID.
  

**Returns**:

  Plugin data including configuration and releases.

#### create\_plugin

```python
def create_plugin(data: dict[str, Any]) -> dict[str, Any]
```

Create a new plugin.

**Arguments**:

- `data` - Plugin creation data (name, category, etc.).
  

**Returns**:

  Created plugin data.

#### update\_plugin

```python
def update_plugin(plugin_id: int, data: dict[str, Any]) -> dict[str, Any]
```

Update an existing plugin.

**Arguments**:

- `plugin_id` - Plugin ID to update.
- `data` - Fields to update.
  

**Returns**:

  Updated plugin data.

#### run\_plugin

```python
def run_plugin(plugin_id: int, data: dict[str, Any]) -> dict[str, Any]
```

Run a plugin action.

**Arguments**:

- `plugin_id` - Plugin ID to run.
- `data` - Run parameters including action and params.
  

**Returns**:

  Job data or direct result.
  

**Example**:

  >>> client.run_plugin(123, \{
  ...     'action': 'train',
  ...     'params': \{'epochs': 10\},
  ...     'job_id': 456
  ... \})

#### get\_plugin\_release

```python
def get_plugin_release(release_id: int,
                       *,
                       params: dict[str, Any] | None = None) -> dict[str, Any]
```

Get plugin release details by ID.

**Arguments**:

- `release_id` - Plugin release ID.
- `params` - Optional query parameters.
  

**Returns**:

  Plugin release data including config and requirements.

#### create\_plugin\_release

```python
def create_plugin_release(data: dict[str, Any],
                          *,
                          file: str | Path | None = None) -> dict[str, Any]
```

Create a new plugin release.

**Arguments**:

- `data` - Release data (plugin, version, config, requirements).
- `file` - Optional plugin archive file to upload.
  

**Returns**:

  Created plugin release data.
  

**Example**:

  >>> client.create_plugin_release(
  ...     \{'plugin': 123, 'version': '1.0.0'\},
  ...     file='/path/to/plugin.zip'
  ... )

#### get\_job

```python
def get_job(job_id: int,
            *,
            params: dict[str, Any] | None = None) -> dict[str, Any]
```

Get job details by ID.

**Arguments**:

- `job_id` - Job ID.
- `params` - Optional query parameters.
  

**Returns**:

  Job data including status and progress.

#### list\_jobs

```python
def list_jobs(params: dict[str, Any] | None = None) -> dict[str, Any]
```

List jobs with optional filtering.

**Arguments**:

- `params` - Query parameters (status, plugin, etc.).
  

**Returns**:

  Paginated job list.

#### update\_job

```python
def update_job(job_id: int, data: dict[str, Any]) -> dict[str, Any]
```

Update job status and data.

**Arguments**:

- `job_id` - Job ID to update.
- `data` - Update payload (status, progress_record, metrics_record, etc.).
  

**Returns**:

  Updated job data.
  

**Example**:

  >>> client.update_job(123, \{
  ...     'status': 'running',
  ...     'progress_record': \{'step': 5, 'total': 100\}
  ... \})

#### list\_job\_console\_logs

```python
def list_job_console_logs(job_id: int) -> dict[str, Any]
```

Get console logs for a job.

**Arguments**:

- `job_id` - Job ID.
  

**Returns**:

  Console log entries.

#### tail\_job\_console\_logs

```python
def tail_job_console_logs(job_id: int) -> Generator[str, None, None]
```

Stream console logs for a running job.

Yields log lines as they become available.

**Arguments**:

- `job_id` - Job ID to tail.
  

**Yields**:

  Log lines as strings.
  

**Example**:

  >>> for line in client.tail_job_console_logs(123):
  ...     print(line)

#### create\_logs

```python
def create_logs(data: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]
```

Create log entries with optional file attachments.

File fields are automatically converted to base64 data URIs.

**Arguments**:

- `data` - Single log entry or list of entries.
  

**Returns**:

  Created log entries response.
  

**Example**:

  >>> client.create_logs(\{
  ...     'message': 'Training complete',
  ...     'level': 'info',
  ...     'file': '/path/to/result.png'  # Auto-converted to base64
  ... \})

#### create\_serve\_application

```python
def create_serve_application(data: dict[str, Any]) -> dict[str, Any]
```

Create a Ray Serve application.

**Arguments**:

- `data` - Application config (name, plugin_release, action, params).
  

**Returns**:

  Created serve application data.

#### list\_serve\_applications

```python
def list_serve_applications(
        params: dict[str, Any] | None = None,
        *,
        list_all: bool = False) -> dict[str, Any] | tuple[Any, int]
```

List Ray Serve applications.

**Arguments**:

- `params` - Query parameters for filtering.
- `list_all` - If True, returns (generator, count).
  

**Returns**:

  Paginated list or (generator, count).

#### get\_storage

```python
def get_storage(storage_id: int) -> Storage
```

Get storage configuration by ID.

**Arguments**:

- `storage_id` - Storage ID.
  

**Returns**:

  Storage model with provider configuration.

