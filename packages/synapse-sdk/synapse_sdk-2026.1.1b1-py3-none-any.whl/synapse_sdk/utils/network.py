from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse

from synapse_sdk.exceptions import ClientError


@dataclass
class StreamLimits:
    """Configuration for streaming resource limits.

    Prevents resource exhaustion during long-running streaming operations.

    Attributes:
        max_messages: Maximum WebSocket messages before termination.
        max_lines: Maximum lines for HTTP streaming.
        max_bytes: Maximum total bytes to receive.
        max_message_size: Maximum size of a single message/line in bytes.
        queue_size: Bounded queue size for async operations.
    """

    max_messages: int = 10_000
    max_lines: int = 50_000
    max_bytes: int = 50 * 1024 * 1024  # 50MB
    max_message_size: int = 10_240  # 10KB per message
    queue_size: int = 1_000


# Resource ID validation pattern - alphanumeric, hyphens, underscores
_RESOURCE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]+$')
_MAX_RESOURCE_ID_LENGTH = 100


def validate_resource_id(resource_id: Any, resource_name: str = 'resource') -> str:
    """Validate resource ID to prevent injection attacks.

    Args:
        resource_id: The ID to validate.
        resource_name: Human-readable name for error messages.

    Returns:
        Validated ID as string.

    Raises:
        ClientError: If ID is invalid (400 status code).

    Example:
        >>> validate_resource_id('job-abc123', 'job')
        'job-abc123'
        >>> validate_resource_id('', 'job')
        Traceback (most recent call last):
        ...
        ClientError: job ID cannot be empty
    """
    if not resource_id:
        raise ClientError(400, f'{resource_name} ID cannot be empty')

    id_str = str(resource_id)

    if not _RESOURCE_ID_PATTERN.match(id_str):
        raise ClientError(400, f'Invalid {resource_name} ID format')

    if len(id_str) > _MAX_RESOURCE_ID_LENGTH:
        raise ClientError(400, f'{resource_name} ID too long')

    return id_str


def validate_timeout(timeout: Any, max_timeout: float = 300.0) -> float:
    """Validate timeout value with bounds checking.

    Args:
        timeout: Timeout value to validate.
        max_timeout: Maximum allowed timeout in seconds.

    Returns:
        Validated timeout as float.

    Raises:
        ClientError: If timeout is invalid (400 status code).

    Example:
        >>> validate_timeout(30.0)
        30.0
        >>> validate_timeout(-1)
        Traceback (most recent call last):
        ...
        ClientError: Timeout must be a positive number
    """
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ClientError(400, 'Timeout must be a positive number')

    if timeout > max_timeout:
        raise ClientError(400, f'Timeout cannot exceed {max_timeout} seconds')

    return float(timeout)


def sanitize_error_message(error_msg: str, context: str = '') -> str:
    """Sanitize error messages to prevent information disclosure.

    Redacts potentially sensitive information like credentials, paths, etc.

    Args:
        error_msg: Raw error message.
        context: Optional context prefix.

    Returns:
        Sanitized error message.

    Example:
        >>> sanitize_error_message('Failed with token="secret123"', 'connection')
        'connection: Failed with token="[REDACTED]"'
    """
    sanitized = str(error_msg)[:200]
    # Redact quoted strings which may contain sensitive data
    sanitized = re.sub(r'["\']([^"\']*)["\']', '"[REDACTED]"', sanitized)

    if context:
        return f'{context}: {sanitized}'
    return sanitized


def http_to_websocket_url(url: str) -> str:
    """Convert HTTP/HTTPS URL to WebSocket URL.

    Args:
        url: HTTP or HTTPS URL.

    Returns:
        WebSocket URL (ws:// or wss://).

    Raises:
        ClientError: If URL scheme is invalid.

    Example:
        >>> http_to_websocket_url('https://example.com/ws/')
        'wss://example.com/ws/'
        >>> http_to_websocket_url('http://localhost:8000/ws/')
        'ws://localhost:8000/ws/'
    """
    try:
        parsed = urlparse(url)

        if parsed.scheme == 'http':
            ws_scheme = 'ws'
        elif parsed.scheme == 'https':
            ws_scheme = 'wss'
        elif parsed.scheme in ('ws', 'wss'):
            return url  # Already a WebSocket URL
        else:
            raise ClientError(400, f'Invalid URL scheme: {parsed.scheme}')

        return urlunparse((
            ws_scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        ))
    except ClientError:
        raise
    except Exception as e:
        raise ClientError(400, f'Invalid URL format: {str(e)[:50]}')
