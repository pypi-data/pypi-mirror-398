from __future__ import annotations

from typing import Any


class ClientError(Exception):
    """Base exception for all HTTP client errors.

    This is the root of the exception hierarchy for HTTP client operations.
    All client-related exceptions inherit from this class, allowing for
    both broad and granular error handling.

    Exception Hierarchy::

        ClientError (base)
        ├── ClientConnectionError  # Network/connection failures
        ├── ClientTimeoutError     # Request timeouts
        ├── HTTPError              # HTTP status code errors
        │   ├── AuthenticationError   # 401 Unauthorized
        │   ├── AuthorizationError    # 403 Forbidden
        │   ├── NotFoundError         # 404 Not Found
        │   ├── ValidationError       # 400/422 Bad Request
        │   ├── RateLimitError        # 429 Too Many Requests
        │   └── ServerError           # 5xx Server Errors
        └── StreamError            # Streaming/WebSocket errors
            ├── StreamLimitExceededError
            └── WebSocketError

    Attributes:
        status_code: HTTP status code if applicable, None for non-HTTP errors.
        detail: Error details from the response or underlying exception.

    Example:
        >>> from synapse_sdk.exceptions import ClientError, NotFoundError
        >>>
        >>> try:
        ...     result = client.get_resource(123)
        ... except NotFoundError:
        ...     print("Resource not found")
        ... except ClientError as e:
        ...     print(f"Client error: {e.status_code} - {e.detail}")
    """

    def __init__(self, status_code: int | None = None, detail: Any = None):
        self.status_code = status_code
        self.detail = detail
        if status_code is not None:
            super().__init__(f'{status_code}: {detail}')
        else:
            super().__init__(str(detail) if detail else '')

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(status_code={self.status_code}, detail={self.detail!r})'


class ClientConnectionError(ClientError):
    """Connection failed."""

    def __init__(self, detail: Any = None):
        super().__init__(status_code=None, detail=detail)


class ClientTimeoutError(ClientError):
    """Request timed out."""

    def __init__(self, detail: Any = None):
        super().__init__(status_code=408, detail=detail)


class HTTPError(ClientError):
    """HTTP status code error."""

    pass


class AuthenticationError(HTTPError):
    """401 Unauthorized."""

    def __init__(self, detail: Any = None):
        super().__init__(status_code=401, detail=detail)


class AuthorizationError(HTTPError):
    """403 Forbidden."""

    def __init__(self, detail: Any = None):
        super().__init__(status_code=403, detail=detail)


class NotFoundError(HTTPError):
    """404 Not Found."""

    def __init__(self, detail: Any = None):
        super().__init__(status_code=404, detail=detail)


class ValidationError(HTTPError):
    """400/422 Bad Request or Unprocessable Entity."""

    def __init__(self, status_code: int = 400, detail: Any = None):
        super().__init__(status_code=status_code, detail=detail)


class RateLimitError(HTTPError):
    """429 Too Many Requests."""

    def __init__(self, detail: Any = None):
        super().__init__(status_code=429, detail=detail)


class ServerError(HTTPError):
    """5xx Server Error."""

    def __init__(self, status_code: int = 500, detail: Any = None):
        super().__init__(status_code=status_code, detail=detail)


class StreamError(ClientError):
    """Stream processing error."""

    pass


class StreamLimitExceededError(StreamError):
    """Stream limit exceeded."""

    pass


class WebSocketError(StreamError):
    """WebSocket connection error."""

    pass


def raise_for_status(status_code: int, detail: Any = None) -> None:
    """Raise an appropriate exception based on HTTP status code.

    Args:
        status_code: HTTP status code.
        detail: Error detail from response.

    Raises:
        AuthenticationError: For 401 status.
        AuthorizationError: For 403 status.
        NotFoundError: For 404 status.
        ValidationError: For 400 or 422 status.
        RateLimitError: For 429 status.
        ServerError: For 5xx status.
        HTTPError: For other error status codes.
    """
    if status_code < 400:
        return

    if status_code == 401:
        raise AuthenticationError(detail)
    elif status_code == 403:
        raise AuthorizationError(detail)
    elif status_code == 404:
        raise NotFoundError(detail)
    elif status_code in (400, 422):
        raise ValidationError(status_code, detail)
    elif status_code == 429:
        raise RateLimitError(detail)
    elif status_code >= 500:
        raise ServerError(status_code, detail)
    else:
        raise HTTPError(status_code, detail)
