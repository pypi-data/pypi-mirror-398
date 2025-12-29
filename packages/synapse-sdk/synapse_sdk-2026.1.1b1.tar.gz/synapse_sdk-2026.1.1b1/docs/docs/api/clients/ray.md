---
id: ray
title: RayClientMixin
sidebar_position: 4
---

# RayClientMixin

Mixin for Ray cluster management and real-time log streaming.

## Overview

The `RayClientMixin` provides Ray cluster operations including job management, real-time log streaming (WebSocket/HTTP), node monitoring, and Ray Serve application control. It's included in both `AgentClient` (sync) and `AsyncAgentClient` (async).

## Key Features

- **Job Management**: List, get, stop Ray jobs
- **Real-time Log Streaming**: WebSocket and HTTP-based log tailing with auto-fallback
- **Node Monitoring**: Monitor cluster nodes
- **Task Monitoring**: Track task execution
- **Ray Serve**: Deploy and manage serve applications
- **Resource Protection**: StreamLimits to prevent memory exhaustion

---

## Log Streaming

### tail_job_logs()

Unified streaming method with automatic protocol selection.

```python
def tail_job_logs(
    job_id: str,
    timeout: float = 30.0,
    *,
    protocol: Literal['websocket', 'http', 'auto'] = 'auto'
) -> Generator[str, None, None]
```

**Parameters:**

- `job_id` (str): Ray job ID (e.g., `'raysubmit_abc123'`)
- `timeout` (float): Connection timeout in seconds (default: 30)
- `protocol`: Protocol selection:
  - `'auto'` (default): Try WebSocket, fall back to HTTP on failure
  - `'websocket'`: WebSocket only (lowest latency)
  - `'http'`: HTTP chunked streaming only (more compatible)

**Yields:** Log lines as strings

**Example:**

```python
# Auto protocol selection (recommended)
for line in client.tail_job_logs('raysubmit_abc123'):
    print(line)

# Explicit WebSocket
for line in client.tail_job_logs('raysubmit_abc123', protocol='websocket'):
    print(line)

# Explicit HTTP streaming
for line in client.tail_job_logs('raysubmit_abc123', protocol='http'):
    print(line)

# With custom timeout
for line in client.tail_job_logs('raysubmit_abc123', timeout=60):
    if 'ERROR' in line:
        break
```

### websocket_tail_job_logs()

Direct WebSocket streaming for lowest latency.

```python
def websocket_tail_job_logs(
    job_id: str,
    timeout: float = 30.0
) -> Generator[str, None, None]
```

**Requires:** `websocket-client` package (sync) or `websockets` package (async)

```python
for line in client.websocket_tail_job_logs('raysubmit_abc123'):
    print(line)
```

### stream_tail_job_logs()

HTTP chunked transfer streaming as fallback.

```python
def stream_tail_job_logs(
    job_id: str,
    timeout: float = 30.0
) -> Generator[str, None, None]
```

```python
for line in client.stream_tail_job_logs('raysubmit_abc123'):
    print(line)
```

---

## Async Streaming

For `AsyncAgentClient`, all streaming methods return `AsyncGenerator`:

```python
from synapse_sdk.clients.agent import AsyncAgentClient

async with AsyncAgentClient(base_url, agent_token) as client:
    # Auto protocol
    async for line in client.tail_job_logs('raysubmit_abc123'):
        print(line)

    # WebSocket
    async for line in client.websocket_tail_job_logs('raysubmit_abc123'):
        print(line)

    # HTTP
    async for line in client.stream_tail_job_logs('raysubmit_abc123'):
        print(line)
```

---

## Stream Limits

Configure resource limits to prevent memory exhaustion:

```python
from synapse_sdk.utils.network import StreamLimits

# Set custom limits
client.stream_limits = StreamLimits(
    max_messages=10_000,     # Max WebSocket messages
    max_lines=50_000,        # Max HTTP lines
    max_bytes=50*1024*1024,  # 50MB total
    max_message_size=10_240  # 10KB per message
)
```

When limits are exceeded, `ClientError` with status code 429 is raised.

---

## Job Operations

### list_jobs()

List all Ray jobs in the cluster.

```python
jobs = client.list_jobs()
for job in jobs:
    print(f"Job {job['job_id']}: {job['status']}")
```

### get_job()

Get details for a specific job.

```python
job = client.get_job('raysubmit_abc123')
print(f"Status: {job['status']}")
print(f"Start time: {job['start_time']}")
```

### get_job_logs()

Get all logs for a job (non-streaming).

```python
logs = client.get_job_logs('raysubmit_abc123')
print(logs)
```

### stop_job()

Stop a running job.

```python
result = client.stop_job('raysubmit_abc123')
print(f"Stopped: {result}")
```

---

## Node Operations

### list_nodes()

List all nodes in the Ray cluster.

```python
nodes = client.list_nodes()
for node in nodes:
    print(f"Node {node['node_id']}: {node['state']}")
```

### get_node()

Get details for a specific node.

```python
node = client.get_node('node-abc123')
print(f"Alive: {node['alive']}")
```

---

## Task Operations

### list_tasks()

List all tasks in the cluster.

```python
tasks = client.list_tasks()
```

### get_task()

Get details for a specific task.

```python
task = client.get_task('task-xyz789')
```

---

## Ray Serve Operations

### list_serve_applications()

List all Ray Serve applications.

```python
apps = client.list_serve_applications()
```

### get_serve_application()

Get details for a serve application.

```python
app = client.get_serve_application('my-app')
print(f"Status: {app['status']}")
```

### delete_serve_application()

Delete a serve application.

```python
client.delete_serve_application('my-app')
```

---

## Error Handling

```python
from synapse_sdk.clients.exceptions import ClientError

try:
    for line in client.tail_job_logs('invalid-job'):
        print(line)
except ClientError as e:
    if e.status_code == 400:
        print("Invalid job ID format")
    elif e.status_code == 429:
        print("Stream limits exceeded")
    elif e.status_code == 500:
        print("WebSocket library not installed")
    elif e.status_code == 503:
        print("Connection failed")
```

### Error Codes

| Code | Meaning |
|------|---------|
| 400 | Invalid job ID, timeout, or protocol |
| 404 | Resource not found |
| 408 | Connection timeout |
| 429 | Stream limits exceeded |
| 500 | Library unavailable or internal error |
| 503 | Connection failed or closed |

---

## Best Practices

### Protocol Selection

```python
# Let auto handle fallback (recommended for production)
for line in client.tail_job_logs(job_id, protocol='auto'):
    process(line)

# Use WebSocket for interactive monitoring
for line in client.tail_job_logs(job_id, protocol='websocket'):
    display_realtime(line)

# Use HTTP for compatibility with proxies/firewalls
for line in client.tail_job_logs(job_id, protocol='http'):
    log(line)
```

### Error Recovery

```python
import time

def robust_streaming(client, job_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            for line in client.tail_job_logs(job_id):
                yield line
            break
        except ClientError as e:
            if e.status_code == 503 and attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
```

### Stream Limit Configuration

```python
# High-volume production logs
client.stream_limits = StreamLimits(
    max_messages=50_000,
    max_lines=100_000,
    max_bytes=200 * 1024 * 1024  # 200MB
)

# Limited development environment
client.stream_limits = StreamLimits(
    max_messages=1_000,
    max_lines=5_000,
    max_bytes=10 * 1024 * 1024  # 10MB
)
```

---

## See Also

- [AgentClient](./agent.md) - Main client with Ray mixin
- [Network Utilities](../../features/utils/network.md) - StreamLimits and validation
- [BaseClient](./base.md) - Base client implementation
