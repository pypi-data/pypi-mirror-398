---
id: agent
title: AgentClient
sidebar_position: 2
---

# AgentClient

Client for agent-specific operations, job management, and distributed execution.

## Overview

The `AgentClient` provides access to agent operations, including plugin execution, Ray job management, and real-time log streaming. Both synchronous (`AgentClient`) and asynchronous (`AsyncAgentClient`) versions are available.

## Installation

```bash
pip install synapse-sdk
```

For WebSocket streaming support:

```bash
pip install synapse-sdk websocket-client  # Sync client
pip install synapse-sdk websockets        # Async client
```

---

## AgentClient (Sync)

### Constructor

```python
AgentClient(
    base_url: str,
    agent_token: str,
    *,
    user_token: str = None,
    tenant: str = None,
    timeout: dict = None
)
```

### Parameters

- `base_url` (str): Agent server URL (e.g., `"https://agent.example.com"`)
- `agent_token` (str): Agent authentication token
- `user_token` (str, optional): User authentication token for user-scoped operations
- `tenant` (str, optional): Tenant identifier for multi-tenant deployments
- `timeout` (dict, optional): Connection and read timeout configuration

### Usage

```python
from synapse_sdk.clients.agent import AgentClient

client = AgentClient(
    base_url="https://agent.example.com",
    agent_token="your-agent-token"
)

# Health check
status = client.health_check()
print(f"Agent status: {status}")

# List Ray jobs
jobs = client.list_jobs()

# Stream job logs
for line in client.tail_job_logs('raysubmit_abc123'):
    print(line)
```

---

## AsyncAgentClient (Async)

### Constructor

```python
AsyncAgentClient(
    base_url: str,
    agent_token: str,
    *,
    user_token: str = None,
    tenant: str = None,
    timeout: dict = None
)
```

### Usage with Context Manager

```python
from synapse_sdk.clients.agent import AsyncAgentClient

async with AsyncAgentClient(
    base_url="https://agent.example.com",
    agent_token="your-agent-token"
) as client:
    # Health check
    status = await client.health_check()

    # List Ray jobs
    jobs = await client.list_jobs()

    # Stream job logs asynchronously
    async for line in client.tail_job_logs('raysubmit_abc123'):
        print(line)
```

### Usage without Context Manager

```python
client = AsyncAgentClient(base_url, agent_token)
try:
    jobs = await client.list_jobs()
finally:
    await client.close()
```

---

## Log Streaming

Both clients support real-time log streaming via WebSocket or HTTP protocols.

### Unified Method

```python
# Sync
for line in client.tail_job_logs('job-id', protocol='auto'):
    print(line)

# Async
async for line in client.tail_job_logs('job-id', protocol='auto'):
    print(line)
```

### Protocol Options

- `'auto'` (default): Try WebSocket first, fall back to HTTP on connection failure
- `'websocket'`: Use WebSocket only (lowest latency)
- `'http'`: Use HTTP chunked streaming only (more compatible)

### Stream Limits

Configure resource limits for streaming operations:

```python
from synapse_sdk.utils.network import StreamLimits

client.stream_limits = StreamLimits(
    max_messages=10_000,    # Max WebSocket messages
    max_lines=50_000,       # Max HTTP lines
    max_bytes=50*1024*1024, # 50MB total
    max_message_size=10_240 # 10KB per message
)
```

See [RayClient](./ray.md) for detailed streaming method documentation.

---

## Ray Operations

The AgentClient includes all Ray cluster management methods via mixin:

### Job Operations

```python
# List all jobs
jobs = client.list_jobs()

# Get job details
job = client.get_job('raysubmit_abc123')

# Get job logs (non-streaming)
logs = client.get_job_logs('raysubmit_abc123')

# Stop a running job
result = client.stop_job('raysubmit_abc123')
```

### Node Operations

```python
# List cluster nodes
nodes = client.list_nodes()

# Get node details
node = client.get_node('node-abc123')
```

### Task Operations

```python
# List all tasks
tasks = client.list_tasks()

# Get task details
task = client.get_task('task-xyz789')
```

### Ray Serve Operations

```python
# List serve applications
apps = client.list_serve_applications()

# Get application details
app = client.get_serve_application('my-app')

# Delete application
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
        print("Invalid job ID or parameters")
    elif e.status_code == 404:
        print("Job not found")
    elif e.status_code == 503:
        print("Connection to agent failed")
    else:
        print(f"Error: {e}")
```

### Common Error Codes

| Code | Meaning |
|------|---------|
| 400 | Invalid parameters (job ID, timeout, protocol) |
| 404 | Resource not found |
| 408 | Connection or read timeout |
| 429 | Stream limits exceeded |
| 500 | Internal error or library unavailable |
| 503 | Agent connection failed |

---

## See Also

- [RayClient](./ray.md) - Detailed Ray streaming methods
- [BackendClient](./backend.md) - Backend operations
- [BaseClient](./base.md) - Base client implementation
- [Network Utilities](../../features/utils/network.md) - StreamLimits and validation
