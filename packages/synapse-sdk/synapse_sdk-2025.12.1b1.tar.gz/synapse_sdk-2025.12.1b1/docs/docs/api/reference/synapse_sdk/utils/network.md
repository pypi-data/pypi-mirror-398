---
sidebar_label: network
title: synapse_sdk.utils.network
---

## StreamLimits Objects

```python
@dataclass
class StreamLimits()
```

Configuration for streaming resource limits.

Prevents resource exhaustion during long-running streaming operations.

**Attributes**:

- `max_messages` - Maximum WebSocket messages before termination.
- `max_lines` - Maximum lines for HTTP streaming.
- `max_bytes` - Maximum total bytes to receive.
- `max_message_size` - Maximum size of a single message/line in bytes.
- `queue_size` - Bounded queue size for async operations.

#### max\_bytes

50MB

#### max\_message\_size

10KB per message

#### validate\_resource\_id

```python
def validate_resource_id(resource_id: Any,
                         resource_name: str = 'resource') -> str
```

Validate resource ID to prevent injection attacks.

**Arguments**:

- `resource_id` - The ID to validate.
- `resource_name` - Human-readable name for error messages.
  

**Returns**:

  Validated ID as string.
  

**Raises**:

- `ClientError` - If ID is invalid (400 status code).
  

**Example**:

  >>> validate_resource_id('job-abc123', 'job')
  'job-abc123'
  >>> validate_resource_id('', 'job')
  Traceback (most recent call last):
  ...
- `ClientError` - job ID cannot be empty

#### validate\_timeout

```python
def validate_timeout(timeout: Any, max_timeout: float = 300.0) -> float
```

Validate timeout value with bounds checking.

**Arguments**:

- `timeout` - Timeout value to validate.
- `max_timeout` - Maximum allowed timeout in seconds.
  

**Returns**:

  Validated timeout as float.
  

**Raises**:

- `ClientError` - If timeout is invalid (400 status code).
  

**Example**:

  >>> validate_timeout(30.0)
  30.0
  >>> validate_timeout(-1)
  Traceback (most recent call last):
  ...
- `ClientError` - Timeout must be a positive number

#### sanitize\_error\_message

```python
def sanitize_error_message(error_msg: str, context: str = '') -> str
```

Sanitize error messages to prevent information disclosure.

Redacts potentially sensitive information like credentials, paths, etc.

**Arguments**:

- `error_msg` - Raw error message.
- `context` - Optional context prefix.
  

**Returns**:

  Sanitized error message.
  

**Example**:

  >>> sanitize_error_message('Failed with token="secret123"', 'connection')
- `'connection` - Failed with token="[REDACTED]"'

#### http\_to\_websocket\_url

```python
def http_to_websocket_url(url: str) -> str
```

Convert HTTP/HTTPS URL to WebSocket URL.

**Arguments**:

- `url` - HTTP or HTTPS URL.
  

**Returns**:

  WebSocket URL (ws:// or wss://).
  

**Raises**:

- `ClientError` - If URL scheme is invalid.
  

**Example**:

  >>> http_to_websocket_url('https://example.com/ws/')
  'wss://example.com/ws/'
  >>> http_to_websocket_url('http://localhost:8000/ws/')
  'ws://localhost:8000/ws/'

