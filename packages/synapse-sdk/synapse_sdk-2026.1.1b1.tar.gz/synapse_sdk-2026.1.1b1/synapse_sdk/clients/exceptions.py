from __future__ import annotations

# Re-export from the shared exceptions module for backwards compatibility
from synapse_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ClientConnectionError,
    ClientError,
    ClientTimeoutError,
    HTTPError,
    NotFoundError,
    RateLimitError,
    ServerError,
    StreamError,
    StreamLimitExceededError,
    ValidationError,
    WebSocketError,
    raise_for_status,
)

__all__ = [
    'ClientError',
    'ClientConnectionError',
    'ClientTimeoutError',
    'HTTPError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'ValidationError',
    'RateLimitError',
    'ServerError',
    'StreamError',
    'StreamLimitExceededError',
    'WebSocketError',
    'raise_for_status',
]
