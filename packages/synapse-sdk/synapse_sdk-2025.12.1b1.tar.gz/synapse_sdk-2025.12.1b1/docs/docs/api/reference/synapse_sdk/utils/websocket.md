---
sidebar_label: websocket
title: synapse_sdk.utils.websocket
---

#### stream\_websocket

```python
def stream_websocket(url: str,
                     headers: dict[str, str] | None = None,
                     timeout: float = 30.0) -> Generator[dict, None, None]
```

Stream raw events from a WebSocket connection.

**Arguments**:

- `url` - WebSocket URL (ws:// or wss://).
- `headers` - Optional headers dict.
- `timeout` - Connection timeout in seconds.
  

**Yields**:

  Parsed JSON events from the WebSocket.
  

**Raises**:

- `ClientError` - On connection or protocol errors.

#### stream\_websocket\_logs

```python
def stream_websocket_logs(url: str,
                          headers: dict[str, str] | None = None,
                          timeout: float = 30.0) -> Generator[str, None, None]
```

Stream log messages from a WebSocket connection.

Handles the standard log streaming protocol:
- 'log' events: yields the message
- 'error' events: raises ClientError
- 'complete' events: stops iteration

**Arguments**:

- `url` - WebSocket URL (ws:// or wss://).
- `headers` - Optional headers dict.
- `timeout` - Connection timeout in seconds.
  

**Yields**:

  Log message strings.
  

**Raises**:

- `ClientError` - On connection, protocol, or server errors.

#### http\_to\_ws\_url

```python
def http_to_ws_url(url: str) -> str
```

Convert HTTP URL to WebSocket URL.

