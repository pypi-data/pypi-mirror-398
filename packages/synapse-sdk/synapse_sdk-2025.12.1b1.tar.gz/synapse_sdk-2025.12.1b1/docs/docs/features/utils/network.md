---
id: network
title: Network Utilities
sidebar_position: 4
---

# Network Utilities

Utilities for streaming configuration, input validation, and URL handling.

## Overview

The `synapse_sdk.utils.network` module provides essential utilities for streaming operations and input validation used by the Ray client mixins.

## StreamLimits

Configuration for streaming resource limits to prevent memory exhaustion.

### Constructor

```python
from synapse_sdk.utils.network import StreamLimits

limits = StreamLimits(
    max_messages=10_000,
    max_lines=50_000,
    max_bytes=50 * 1024 * 1024,  # 50MB
    max_message_size=10_240,     # 10KB
    queue_size=1_000
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_messages` | int | 10,000 | Maximum WebSocket messages before termination |
| `max_lines` | int | 50,000 | Maximum lines for HTTP streaming |
| `max_bytes` | int | 50MB | Maximum total bytes to receive |
| `max_message_size` | int | 10KB | Maximum size per message (oversized messages are skipped) |
| `queue_size` | int | 1,000 | Internal queue size for async operations |

### Usage with Clients

```python
from synapse_sdk.clients.agent import AgentClient
from synapse_sdk.utils.network import StreamLimits

client = AgentClient(base_url, agent_token)

# Configure custom limits
client.stream_limits = StreamLimits(
    max_messages=50_000,
    max_lines=100_000,
    max_bytes=200 * 1024 * 1024  # 200MB
)

# Stream with custom limits
for line in client.tail_job_logs('job-123'):
    print(line)
```

---

## Validation Functions

### validate_resource_id()

Validates resource identifiers to prevent injection attacks.

```python
from synapse_sdk.utils.network import validate_resource_id

# Valid usage
job_id = validate_resource_id('raysubmit_abc123', 'job')
node_id = validate_resource_id('node_abc_123', 'node')

# Invalid usage raises ClientError (400)
try:
    validate_resource_id('', 'job')  # Empty
except ClientError as e:
    print(e)  # "job ID cannot be empty"

try:
    validate_resource_id('job/../malicious', 'job')  # Invalid chars
except ClientError as e:
    print(e)  # "Invalid job ID format"
```

**Validation Rules:**

- Must not be empty
- Only alphanumeric, hyphens (`-`), and underscores (`_`) allowed
- Maximum length: 100 characters
- Pattern: `^[a-zA-Z0-9\-_]+$`

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `resource_id` | Any | The ID to validate (converted to string) |
| `resource_name` | str | Name for error messages (default: `'resource'`) |

**Returns:** `str` - Validated resource ID

**Raises:** `ClientError` (400) if validation fails

---

### validate_timeout()

Validates timeout values with bounds checking.

```python
from synapse_sdk.utils.network import validate_timeout

# Valid timeouts
timeout = validate_timeout(30)      # 30 seconds -> 30.0
timeout = validate_timeout(10.5)    # 10.5 seconds -> 10.5

# Invalid timeouts raise ClientError (400)
try:
    validate_timeout(-1)  # Negative
except ClientError as e:
    print(e)  # "Timeout must be a positive number"

try:
    validate_timeout(500)  # Exceeds max (default 300)
except ClientError as e:
    print(e)  # "Timeout cannot exceed 300 seconds"
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | int/float | - | Timeout value in seconds |
| `max_timeout` | float | 300.0 | Maximum allowed timeout |

**Returns:** `float` - Validated timeout value

**Raises:** `ClientError` (400) if invalid

---

## URL Utilities

### http_to_websocket_url()

Converts HTTP/HTTPS URLs to WebSocket URLs.

```python
from synapse_sdk.utils.network import http_to_websocket_url

# HTTP -> WS
ws_url = http_to_websocket_url("http://localhost:8000/ws/")
# Result: "ws://localhost:8000/ws/"

# HTTPS -> WSS
wss_url = http_to_websocket_url("https://api.example.com/stream/")
# Result: "wss://api.example.com/stream/"

# Already WebSocket (returns unchanged)
url = http_to_websocket_url("wss://api.example.com/")
# Result: "wss://api.example.com/"
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | str | HTTP, HTTPS, WS, or WSS URL |

**Returns:** `str` - WebSocket URL (ws:// or wss://)

**Raises:** `ClientError` (400) if URL scheme is invalid

---

## Error Utilities

### sanitize_error_message()

Sanitizes error messages to prevent information leakage.

```python
from synapse_sdk.utils.network import sanitize_error_message

# Redacts quoted strings
clean = sanitize_error_message('Failed with token="secret123"', 'connection')
# Result: 'connection: Failed with token="[REDACTED]"'

# Truncates long messages (200 char limit)
clean = sanitize_error_message('Very long error...' * 50, 'error')
# Result: 'error: Very long error...' (truncated)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `error_msg` | str | Original error message |
| `context` | str | Optional context prefix |

**Returns:** `str` - Sanitized error message

---

## Complete Example

```python
from synapse_sdk.utils.network import (
    StreamLimits,
    validate_resource_id,
    validate_timeout,
    http_to_websocket_url,
    sanitize_error_message,
)
from synapse_sdk.clients.exceptions import ClientError

def stream_job_logs(client, job_id: str, timeout: float = 30.0):
    """Stream job logs with proper validation."""
    # Validate inputs
    validated_id = validate_resource_id(job_id, 'job')
    validated_timeout = validate_timeout(timeout)

    # Configure limits for this operation
    client.stream_limits = StreamLimits(max_lines=10_000)

    try:
        for line in client.tail_job_logs(validated_id, validated_timeout):
            yield line
    except ClientError as e:
        clean_msg = sanitize_error_message(str(e), f'job {job_id}')
        raise ClientError(e.status_code, clean_msg)

# Usage
for line in stream_job_logs(client, 'raysubmit_abc123', 60.0):
    print(line)
```

---

## Error Codes

| Code | Cause |
|------|-------|
| 400 | Invalid resource ID, timeout, or URL format |
| 429 | Stream limits exceeded |

---

## See Also

- [RayClient](../../api/clients/ray.md) - Uses these utilities for streaming
- [AgentClient](../../api/clients/agent.md) - Client with StreamLimits support
- [Storage](./storage.md) - Storage provider utilities
