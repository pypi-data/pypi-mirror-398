---
sidebar_label: ray
title: synapse_sdk.clients.agent.ray
---

## RayClientMixin Objects

```python
class RayClientMixin()
```

Mixin for Ray cluster management endpoints.

#### stream\_limits

```python
@property
def stream_limits() -> StreamLimits
```

Get stream limits configuration.

#### stream\_limits

```python
@stream_limits.setter
def stream_limits(value: StreamLimits) -> None
```

Set stream limits configuration.

#### list\_jobs

```python
def list_jobs() -> list[dict]
```

List all Ray jobs.

#### get\_job

```python
def get_job(job_id: str) -> dict
```

Get a Ray job by ID.

#### get\_job\_logs

```python
def get_job_logs(job_id: str) -> str
```

Get all logs for a job (non-streaming).

#### stop\_job

```python
def stop_job(job_id: str) -> dict
```

Stop a running job.

#### websocket\_tail\_job\_logs

```python
def websocket_tail_job_logs(job_id: str,
                            timeout: float = 30.0
                            ) -> Generator[str, None, None]
```

Stream job logs via WebSocket protocol.

Establishes a WebSocket connection for real-time log streaming.
Preferred method for low-latency log monitoring.

**Arguments**:

- `job_id` - The Ray job ID to tail logs for.
- `timeout` - Connection and read timeout in seconds.
  

**Yields**:

  Log message strings.
  

**Raises**:

- `ClientError` - On connection, protocol, or validation errors.
  

**Example**:

  >>> for line in client.websocket_tail_job_logs('raysubmit_abc123'):
  ...     print(line)

#### stream\_tail\_job\_logs

```python
def stream_tail_job_logs(job_id: str,
                         timeout: float = 30.0) -> Generator[str, None, None]
```

Stream job logs via HTTP chunked transfer encoding.

Uses HTTP streaming as an alternative when WebSocket is unavailable.

**Arguments**:

- `job_id` - The Ray job ID to tail logs for.
- `timeout` - Connection timeout in seconds (read timeout is infinite).
  

**Yields**:

  Log lines as strings.
  

**Raises**:

- `ClientError` - On connection, protocol, or validation errors.
  

**Example**:

  >>> for line in client.stream_tail_job_logs('raysubmit_abc123'):
  ...     print(line)

#### tail\_job\_logs

```python
def tail_job_logs(
        job_id: str,
        timeout: float = 30.0,
        *,
        protocol: StreamProtocol = 'auto') -> Generator[str, None, None]
```

Stream job logs with automatic protocol selection.

Unified method that supports WebSocket, HTTP, and auto-selection.

**Arguments**:

- `job_id` - The Ray job ID to tail logs for.
- `timeout` - Connection timeout in seconds.
- `protocol` - Protocol to use:
  - 'websocket': Use WebSocket only
  - 'http': Use HTTP streaming only
  - 'auto': Try WebSocket, fall back to HTTP on connection failure
  

**Yields**:

  Log message strings.
  

**Raises**:

- `ClientError` - On connection, protocol, or validation errors.
  

**Example**:

  >>> # Auto protocol selection (recommended)
  >>> for line in client.tail_job_logs('raysubmit_abc123'):
  ...     print(line)
  
  >>> # Explicit WebSocket
  >>> for line in client.tail_job_logs('raysubmit_abc123', protocol='websocket'):
  ...     print(line)
  
  >>> # Explicit HTTP streaming
  >>> for line in client.tail_job_logs('raysubmit_abc123', protocol='http'):
  ...     print(line)

#### list\_nodes

```python
def list_nodes() -> list[dict]
```

List all Ray nodes.

#### get\_node

```python
def get_node(node_id: str) -> dict
```

Get a Ray node by ID.

#### list\_tasks

```python
def list_tasks() -> list[dict]
```

List all Ray tasks.

#### get\_task

```python
def get_task(task_id: str) -> dict
```

Get a Ray task by ID.

#### list\_serve\_applications

```python
def list_serve_applications() -> list[dict]
```

List all Ray Serve applications.

#### get\_serve\_application

```python
def get_serve_application(name: str) -> dict
```

Get a Ray Serve application by name.

#### delete\_serve\_application

```python
def delete_serve_application(name: str) -> None
```

Delete a Ray Serve application.

