"""Tests for synapse_sdk.exceptions module."""

from __future__ import annotations

import pytest

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

# -----------------------------------------------------------------------------
# ClientError Tests
# -----------------------------------------------------------------------------


class TestClientError:
    """Tests for ClientError base exception."""

    def test_with_status_and_detail(self):
        """ClientError stores status_code and detail."""
        error = ClientError(status_code=500, detail='Server error')
        assert error.status_code == 500
        assert error.detail == 'Server error'

    def test_without_status_code(self):
        """ClientError works with None status_code."""
        error = ClientError(status_code=None, detail='Connection failed')
        assert error.status_code is None
        assert error.detail == 'Connection failed'
        assert str(error) == 'Connection failed'

    def test_without_detail(self):
        """ClientError works with None detail."""
        error = ClientError(status_code=404, detail=None)
        assert error.status_code == 404
        assert error.detail is None
        assert '404' in str(error)

    def test_empty_init(self):
        """ClientError works with no arguments."""
        error = ClientError()
        assert error.status_code is None
        assert error.detail is None
        assert str(error) == ''

    def test_message_format_with_status(self):
        """ClientError message includes status code and detail."""
        error = ClientError(status_code=400, detail='Bad request')
        assert str(error) == '400: Bad request'

    def test_message_format_without_status(self):
        """ClientError message is detail when no status code."""
        error = ClientError(detail='Custom error')
        assert str(error) == 'Custom error'

    def test_repr(self):
        """ClientError has useful repr."""
        error = ClientError(status_code=403, detail='Forbidden')
        repr_str = repr(error)
        assert 'ClientError' in repr_str
        assert '403' in repr_str
        assert 'Forbidden' in repr_str

    def test_with_dict_detail(self):
        """ClientError accepts dict as detail."""
        detail = {'error': 'validation_failed', 'fields': ['name']}
        error = ClientError(status_code=422, detail=detail)
        assert error.detail == detail
        assert str(detail) in str(error)


# -----------------------------------------------------------------------------
# Connection and Timeout Error Tests
# -----------------------------------------------------------------------------


class TestClientConnectionError:
    """Tests for ClientConnectionError."""

    def test_no_status_code(self):
        """ClientConnectionError has None status_code."""
        error = ClientConnectionError('Connection refused')
        assert error.status_code is None
        assert error.detail == 'Connection refused'

    def test_inherits_from_client_error(self):
        """ClientConnectionError inherits from ClientError."""
        assert issubclass(ClientConnectionError, ClientError)


class TestClientTimeoutError:
    """Tests for ClientTimeoutError."""

    def test_status_code_408(self):
        """ClientTimeoutError has status_code 408."""
        error = ClientTimeoutError('Read timeout')
        assert error.status_code == 408
        assert error.detail == 'Read timeout'

    def test_inherits_from_client_error(self):
        """ClientTimeoutError inherits from ClientError."""
        assert issubclass(ClientTimeoutError, ClientError)


# -----------------------------------------------------------------------------
# HTTP Error Tests
# -----------------------------------------------------------------------------


class TestHTTPError:
    """Tests for HTTPError and its subclasses."""

    def test_http_error_inherits_from_client_error(self):
        """HTTPError inherits from ClientError."""
        assert issubclass(HTTPError, ClientError)

    def test_http_error_with_status_and_detail(self):
        """HTTPError stores status_code and detail."""
        error = HTTPError(status_code=418, detail="I'm a teapot")
        assert error.status_code == 418
        assert error.detail == "I'm a teapot"


class TestAuthenticationError:
    """Tests for AuthenticationError (401)."""

    def test_status_code_401(self):
        """AuthenticationError has status_code 401."""
        error = AuthenticationError('Invalid token')
        assert error.status_code == 401
        assert error.detail == 'Invalid token'

    def test_inherits_from_http_error(self):
        """AuthenticationError inherits from HTTPError."""
        assert issubclass(AuthenticationError, HTTPError)


class TestAuthorizationError:
    """Tests for AuthorizationError (403)."""

    def test_status_code_403(self):
        """AuthorizationError has status_code 403."""
        error = AuthorizationError('Access denied')
        assert error.status_code == 403
        assert error.detail == 'Access denied'

    def test_inherits_from_http_error(self):
        """AuthorizationError inherits from HTTPError."""
        assert issubclass(AuthorizationError, HTTPError)


class TestNotFoundError:
    """Tests for NotFoundError (404)."""

    def test_status_code_404(self):
        """NotFoundError has status_code 404."""
        error = NotFoundError('Resource not found')
        assert error.status_code == 404
        assert error.detail == 'Resource not found'

    def test_inherits_from_http_error(self):
        """NotFoundError inherits from HTTPError."""
        assert issubclass(NotFoundError, HTTPError)


class TestValidationError:
    """Tests for ValidationError (400/422)."""

    def test_default_status_code_400(self):
        """ValidationError defaults to status_code 400."""
        error = ValidationError(detail='Invalid data')
        assert error.status_code == 400
        assert error.detail == 'Invalid data'

    def test_custom_status_code_422(self):
        """ValidationError accepts custom status_code 422."""
        error = ValidationError(status_code=422, detail='Unprocessable entity')
        assert error.status_code == 422
        assert error.detail == 'Unprocessable entity'

    def test_inherits_from_http_error(self):
        """ValidationError inherits from HTTPError."""
        assert issubclass(ValidationError, HTTPError)


class TestRateLimitError:
    """Tests for RateLimitError (429)."""

    def test_status_code_429(self):
        """RateLimitError has status_code 429."""
        error = RateLimitError('Too many requests')
        assert error.status_code == 429
        assert error.detail == 'Too many requests'

    def test_inherits_from_http_error(self):
        """RateLimitError inherits from HTTPError."""
        assert issubclass(RateLimitError, HTTPError)


class TestServerError:
    """Tests for ServerError (5xx)."""

    def test_default_status_code_500(self):
        """ServerError defaults to status_code 500."""
        error = ServerError(detail='Internal server error')
        assert error.status_code == 500
        assert error.detail == 'Internal server error'

    def test_custom_status_code_502(self):
        """ServerError accepts custom 5xx status_code."""
        error = ServerError(status_code=502, detail='Bad gateway')
        assert error.status_code == 502
        assert error.detail == 'Bad gateway'

    def test_custom_status_code_503(self):
        """ServerError accepts custom 503 status_code."""
        error = ServerError(status_code=503, detail='Service unavailable')
        assert error.status_code == 503

    def test_inherits_from_http_error(self):
        """ServerError inherits from HTTPError."""
        assert issubclass(ServerError, HTTPError)


# -----------------------------------------------------------------------------
# Stream Error Tests
# -----------------------------------------------------------------------------


class TestStreamError:
    """Tests for StreamError and its subclasses."""

    def test_stream_error_inherits_from_client_error(self):
        """StreamError inherits from ClientError."""
        assert issubclass(StreamError, ClientError)

    def test_stream_limit_exceeded_error(self):
        """StreamLimitExceededError inherits from StreamError."""
        assert issubclass(StreamLimitExceededError, StreamError)

    def test_websocket_error(self):
        """WebSocketError inherits from StreamError."""
        assert issubclass(WebSocketError, StreamError)


# -----------------------------------------------------------------------------
# Exception Hierarchy Tests
# -----------------------------------------------------------------------------


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_client_error(self):
        """All custom exceptions inherit from ClientError."""
        exceptions = [
            ClientConnectionError,
            ClientTimeoutError,
            HTTPError,
            AuthenticationError,
            AuthorizationError,
            NotFoundError,
            ValidationError,
            RateLimitError,
            ServerError,
            StreamError,
            StreamLimitExceededError,
            WebSocketError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, ClientError), f'{exc_class.__name__} should inherit from ClientError'

    def test_catch_client_error_catches_all(self):
        """Catching ClientError catches all subclasses."""
        exceptions_to_raise = [
            ClientConnectionError('test'),
            ClientTimeoutError('test'),
            AuthenticationError('test'),
            NotFoundError('test'),
            ServerError(detail='test'),
        ]
        for exc in exceptions_to_raise:
            with pytest.raises(ClientError):
                raise exc

    def test_catch_http_error_catches_http_subclasses(self):
        """Catching HTTPError catches HTTP subclasses but not connection errors."""
        http_exceptions = [
            AuthenticationError('test'),
            AuthorizationError('test'),
            NotFoundError('test'),
            ValidationError(detail='test'),
            RateLimitError('test'),
            ServerError(detail='test'),
        ]
        for exc in http_exceptions:
            with pytest.raises(HTTPError):
                raise exc


# -----------------------------------------------------------------------------
# raise_for_status Tests
# -----------------------------------------------------------------------------


class TestRaiseForStatus:
    """Tests for raise_for_status function."""

    def test_success_codes_do_not_raise(self):
        """Success codes (1xx-3xx) do not raise."""
        for status_code in [100, 200, 201, 204, 301, 302, 304]:
            # Should not raise
            raise_for_status(status_code)
            raise_for_status(status_code, detail='some detail')

    def test_raises_authentication_error_for_401(self):
        """401 raises AuthenticationError."""
        with pytest.raises(AuthenticationError) as exc_info:
            raise_for_status(401, 'Invalid token')
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == 'Invalid token'

    def test_raises_authorization_error_for_403(self):
        """403 raises AuthorizationError."""
        with pytest.raises(AuthorizationError) as exc_info:
            raise_for_status(403, 'Forbidden')
        assert exc_info.value.status_code == 403

    def test_raises_not_found_error_for_404(self):
        """404 raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc_info:
            raise_for_status(404, 'Not found')
        assert exc_info.value.status_code == 404

    def test_raises_validation_error_for_400(self):
        """400 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise_for_status(400, 'Bad request')
        assert exc_info.value.status_code == 400

    def test_raises_validation_error_for_422(self):
        """422 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise_for_status(422, 'Unprocessable entity')
        assert exc_info.value.status_code == 422

    def test_raises_rate_limit_error_for_429(self):
        """429 raises RateLimitError."""
        with pytest.raises(RateLimitError) as exc_info:
            raise_for_status(429, 'Too many requests')
        assert exc_info.value.status_code == 429

    def test_raises_server_error_for_500(self):
        """500 raises ServerError."""
        with pytest.raises(ServerError) as exc_info:
            raise_for_status(500, 'Internal error')
        assert exc_info.value.status_code == 500

    def test_raises_server_error_for_502(self):
        """502 raises ServerError."""
        with pytest.raises(ServerError) as exc_info:
            raise_for_status(502, 'Bad gateway')
        assert exc_info.value.status_code == 502

    def test_raises_server_error_for_503(self):
        """503 raises ServerError."""
        with pytest.raises(ServerError) as exc_info:
            raise_for_status(503, 'Service unavailable')
        assert exc_info.value.status_code == 503

    def test_raises_http_error_for_other_4xx(self):
        """Other 4xx codes raise HTTPError."""
        for status_code in [402, 405, 406, 409, 410, 415, 418]:
            with pytest.raises(HTTPError) as exc_info:
                raise_for_status(status_code, f'Error {status_code}')
            assert exc_info.value.status_code == status_code
            # Should NOT be a more specific subclass
            assert type(exc_info.value) is HTTPError

    def test_with_dict_detail(self):
        """raise_for_status passes dict detail correctly."""
        detail = {'error': 'invalid_field', 'field': 'email'}
        with pytest.raises(ValidationError) as exc_info:
            raise_for_status(400, detail)
        assert exc_info.value.detail == detail

    def test_with_none_detail(self):
        """raise_for_status works with None detail."""
        with pytest.raises(NotFoundError) as exc_info:
            raise_for_status(404, None)
        assert exc_info.value.detail is None
