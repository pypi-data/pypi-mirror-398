from __future__ import annotations

import json
from typing import Generator

from synapse_sdk.clients.exceptions import ClientError


def stream_websocket(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> Generator[dict, None, None]:
    """Stream raw events from a WebSocket connection.

    Args:
        url: WebSocket URL (ws:// or wss://).
        headers: Optional headers dict.
        timeout: Connection timeout in seconds.

    Yields:
        Parsed JSON events from the WebSocket.

    Raises:
        ClientError: On connection or protocol errors.
    """
    try:
        import websocket
    except ImportError:
        raise ClientError(500, 'websocket-client package required for streaming')

    header_list = [f'{k}: {v}' for k, v in (headers or {}).items()]

    try:
        ws = websocket.create_connection(url, header=header_list, timeout=timeout)
    except websocket.WebSocketException as e:
        raise ClientError(503, f'WebSocket connection failed: {e}')
    except Exception as e:
        raise ClientError(503, f'Connection error: {e}')

    try:
        while True:
            try:
                data = ws.recv()
            except websocket.WebSocketTimeoutException:
                break
            except websocket.WebSocketConnectionClosedException:
                break

            if not data:
                break

            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                event = {'message': data}

            yield event
    finally:
        ws.close()


def stream_websocket_logs(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> Generator[str, None, None]:
    """Stream log messages from a WebSocket connection.

    Handles the standard log streaming protocol:
    - 'log' events: yields the message
    - 'error' events: raises ClientError
    - 'complete' events: stops iteration

    Args:
        url: WebSocket URL (ws:// or wss://).
        headers: Optional headers dict.
        timeout: Connection timeout in seconds.

    Yields:
        Log message strings.

    Raises:
        ClientError: On connection, protocol, or server errors.
    """
    for event in stream_websocket(url, headers, timeout):
        match event.get('type'):
            case 'error':
                raise ClientError(500, event.get('message', 'Unknown error'))
            case 'complete':
                return
            case _:
                if msg := event.get('message'):
                    yield msg


def http_to_ws_url(url: str) -> str:
    """Convert HTTP URL to WebSocket URL."""
    return url.replace('http://', 'ws://').replace('https://', 'wss://')
