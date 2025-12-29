"""Tests for synapse_sdk.clients.base.BaseClient."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import responses
from pydantic import BaseModel

from synapse_sdk.clients.base import BaseClient
from synapse_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ClientConnectionError,
    ClientTimeoutError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

# -----------------------------------------------------------------------------
# Test Client Implementation
# -----------------------------------------------------------------------------


class TestClient(BaseClient):
    """Test client with custom headers."""

    name = 'TestClient'

    def _get_headers(self) -> dict[str, str]:
        return {'X-Test-Header': 'test-value', 'Authorization': 'Bearer test-token'}


# -----------------------------------------------------------------------------
# Test Models
# -----------------------------------------------------------------------------


class RequestModel(BaseModel):
    name: str
    value: int


class ResponseModel(BaseModel):
    id: int
    name: str


# -----------------------------------------------------------------------------
# Initialization Tests
# -----------------------------------------------------------------------------


class TestBaseClientInit:
    """Tests for BaseClient initialization."""

    def test_base_url_normalized(self):
        """Trailing slash is removed from base_url."""
        client = TestClient('https://api.example.com/')
        assert client.base_url == 'https://api.example.com'

    def test_base_url_without_trailing_slash(self):
        """Base URL without trailing slash is unchanged."""
        client = TestClient('https://api.example.com')
        assert client.base_url == 'https://api.example.com'

    def test_default_timeout(self):
        """Default timeout values are set."""
        client = TestClient('https://api.example.com')
        assert client.timeout == {'connect': 5, 'read': 15}

    def test_custom_timeout(self):
        """Custom timeout is used."""
        client = TestClient('https://api.example.com', timeout={'connect': 10, 'read': 30})
        assert client.timeout == {'connect': 10, 'read': 30}

    def test_default_page_size(self):
        """Default page_size is 100."""
        client = TestClient('https://api.example.com')
        assert client.page_size == 100

    def test_session_not_created_on_init(self):
        """Session is not created during initialization."""
        client = TestClient('https://api.example.com')
        assert client._session is None

    def test_retry_config_set(self):
        """Retry configuration is set."""
        client = TestClient('https://api.example.com')
        assert client._retry_config['total'] == 3
        assert client._retry_config['backoff_factor'] == 1
        assert 502 in client._retry_config['status_forcelist']


# -----------------------------------------------------------------------------
# Session Management Tests
# -----------------------------------------------------------------------------


class TestSessionManagement:
    """Tests for session management."""

    def test_session_lazy_init(self):
        """Session is created on first access."""
        client = TestClient('https://api.example.com')
        assert client._session is None
        session = client.requests_session
        assert session is not None
        assert client._session is session

    def test_session_reused(self):
        """Same session is returned on multiple accesses."""
        client = TestClient('https://api.example.com')
        session1 = client.requests_session
        session2 = client.requests_session
        assert session1 is session2

    def test_create_session_has_retry_adapter(self):
        """Created session has retry adapter mounted."""
        client = TestClient('https://api.example.com')
        session = client._create_session()
        # Check adapters are mounted
        assert 'https://' in session.adapters
        assert 'http://' in session.adapters


# -----------------------------------------------------------------------------
# Request Handling Tests
# -----------------------------------------------------------------------------


class TestRequestHandling:
    """Tests for _request method."""

    @responses.activate
    def test_get_request(self):
        """GET request works correctly."""
        responses.add(
            responses.GET,
            'https://api.example.com/users/1/',
            json={'id': 1, 'name': 'Test User'},
            status=200,
        )
        client = TestClient('https://api.example.com')
        result = client._request('get', 'users/1/')
        assert result == {'id': 1, 'name': 'Test User'}

    @responses.activate
    def test_post_request(self):
        """POST request works correctly."""
        responses.add(
            responses.POST,
            'https://api.example.com/users/',
            json={'id': 1, 'name': 'New User'},
            status=201,
        )
        client = TestClient('https://api.example.com')
        result = client._request('post', 'users/', data={'name': 'New User'})
        assert result == {'id': 1, 'name': 'New User'}

    @responses.activate
    def test_put_request(self):
        """PUT request works correctly."""
        responses.add(
            responses.PUT,
            'https://api.example.com/users/1/',
            json={'id': 1, 'name': 'Updated User'},
            status=200,
        )
        client = TestClient('https://api.example.com')
        result = client._request('put', 'users/1/', data={'name': 'Updated User'})
        assert result == {'id': 1, 'name': 'Updated User'}

    @responses.activate
    def test_patch_request(self):
        """PATCH request works correctly."""
        responses.add(
            responses.PATCH,
            'https://api.example.com/users/1/',
            json={'id': 1, 'name': 'Patched User'},
            status=200,
        )
        client = TestClient('https://api.example.com')
        result = client._request('patch', 'users/1/', data={'name': 'Patched User'})
        assert result == {'id': 1, 'name': 'Patched User'}

    @responses.activate
    def test_delete_request(self):
        """DELETE request works correctly."""
        responses.add(
            responses.DELETE,
            'https://api.example.com/users/1/',
            status=204,
        )
        client = TestClient('https://api.example.com')
        result = client._request('delete', 'users/1/')
        assert result is None

    @responses.activate
    def test_headers_merged(self):
        """Custom headers are merged with default headers."""

        def request_callback(request):
            assert request.headers['X-Test-Header'] == 'test-value'
            assert request.headers['X-Custom'] == 'custom-value'
            return (200, {}, '{"ok": true}')

        responses.add_callback(
            responses.GET,
            'https://api.example.com/test/',
            callback=request_callback,
        )
        client = TestClient('https://api.example.com')
        client._request('get', 'test/', headers={'X-Custom': 'custom-value'})


# -----------------------------------------------------------------------------
# Error Handling Tests
# -----------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for error handling in requests."""

    @responses.activate
    def test_401_raises_authentication_error(self):
        """401 response raises AuthenticationError."""
        responses.add(
            responses.GET,
            'https://api.example.com/protected/',
            json={'detail': 'Invalid token'},
            status=401,
        )
        client = TestClient('https://api.example.com')
        with pytest.raises(AuthenticationError) as exc_info:
            client._request('get', 'protected/')
        assert exc_info.value.status_code == 401

    @responses.activate
    def test_403_raises_authorization_error(self):
        """403 response raises AuthorizationError."""
        responses.add(
            responses.GET,
            'https://api.example.com/admin/',
            json={'detail': 'Forbidden'},
            status=403,
        )
        client = TestClient('https://api.example.com')
        with pytest.raises(AuthorizationError) as exc_info:
            client._request('get', 'admin/')
        assert exc_info.value.status_code == 403

    @responses.activate
    def test_404_raises_not_found_error(self):
        """404 response raises NotFoundError."""
        responses.add(
            responses.GET,
            'https://api.example.com/missing/',
            json={'detail': 'Not found'},
            status=404,
        )
        client = TestClient('https://api.example.com')
        with pytest.raises(NotFoundError) as exc_info:
            client._request('get', 'missing/')
        assert exc_info.value.status_code == 404

    @responses.activate
    def test_400_raises_validation_error(self):
        """400 response raises ValidationError."""
        responses.add(
            responses.POST,
            'https://api.example.com/users/',
            json={'detail': 'Invalid data'},
            status=400,
        )
        client = TestClient('https://api.example.com')
        with pytest.raises(ValidationError) as exc_info:
            client._request('post', 'users/', data={})
        assert exc_info.value.status_code == 400

    @responses.activate
    def test_429_raises_rate_limit_error(self):
        """429 response raises RateLimitError."""
        responses.add(
            responses.GET,
            'https://api.example.com/rate-limited/',
            json={'detail': 'Too many requests'},
            status=429,
        )
        client = TestClient('https://api.example.com')
        with pytest.raises(RateLimitError) as exc_info:
            client._request('get', 'rate-limited/')
        assert exc_info.value.status_code == 429

    @responses.activate
    def test_500_raises_server_error(self):
        """500 response raises ServerError."""
        responses.add(
            responses.GET,
            'https://api.example.com/error/',
            json={'detail': 'Internal error'},
            status=500,
        )
        client = TestClient('https://api.example.com')
        with pytest.raises(ServerError) as exc_info:
            client._request('get', 'error/')
        assert exc_info.value.status_code == 500

    def test_connection_error_raises_client_connection_error(self):
        """Connection error raises ClientConnectionError."""
        client = TestClient('https://api.example.com')
        with patch.object(client.requests_session, 'get') as mock_get:
            import requests

            mock_get.side_effect = requests.exceptions.ConnectionError('Connection refused')
            with pytest.raises(ClientConnectionError):
                client._request('get', 'test/')

    def test_connect_timeout_raises_client_timeout_error(self):
        """Connect timeout raises ClientTimeoutError."""
        client = TestClient('https://api.example.com')
        with patch.object(client.requests_session, 'get') as mock_get:
            import requests

            mock_get.side_effect = requests.exceptions.ConnectTimeout('Connection timed out')
            with pytest.raises(ClientTimeoutError) as exc_info:
                client._request('get', 'test/')
            assert 'connection timeout' in str(exc_info.value.detail).lower()

    def test_read_timeout_raises_client_timeout_error(self):
        """Read timeout raises ClientTimeoutError."""
        client = TestClient('https://api.example.com')
        with patch.object(client.requests_session, 'get') as mock_get:
            import requests

            mock_get.side_effect = requests.exceptions.ReadTimeout('Read timed out')
            with pytest.raises(ClientTimeoutError) as exc_info:
                client._request('get', 'test/')
            assert 'read timeout' in str(exc_info.value.detail).lower()


# -----------------------------------------------------------------------------
# Response Handling Tests
# -----------------------------------------------------------------------------


class TestResponseHandling:
    """Tests for response handling."""

    @responses.activate
    def test_json_response_parsed(self):
        """JSON response is parsed correctly."""
        responses.add(
            responses.GET,
            'https://api.example.com/data/',
            json={'key': 'value', 'nested': {'a': 1}},
            status=200,
        )
        client = TestClient('https://api.example.com')
        result = client._request('get', 'data/')
        assert result == {'key': 'value', 'nested': {'a': 1}}

    @responses.activate
    def test_204_returns_none(self):
        """204 No Content returns None."""
        responses.add(
            responses.DELETE,
            'https://api.example.com/item/',
            status=204,
        )
        client = TestClient('https://api.example.com')
        result = client._request('delete', 'item/')
        assert result is None

    @responses.activate
    def test_text_response_fallback(self):
        """Non-JSON response returns text."""
        responses.add(
            responses.GET,
            'https://api.example.com/text/',
            body='Plain text response',
            status=200,
            content_type='text/plain',
        )
        client = TestClient('https://api.example.com')
        result = client._request('get', 'text/')
        assert result == 'Plain text response'


# -----------------------------------------------------------------------------
# File Handling Tests
# -----------------------------------------------------------------------------


class TestFileHandling:
    """Tests for file upload handling."""

    @responses.activate
    def test_file_upload_with_path(self, temp_file):
        """File upload with Path object works."""
        responses.add(
            responses.POST,
            'https://api.example.com/upload/',
            json={'id': 1, 'filename': 'test_file.txt'},
            status=201,
        )
        client = TestClient('https://api.example.com')
        result = client._request('post', 'upload/', files={'file': temp_file})
        assert result == {'id': 1, 'filename': 'test_file.txt'}

    @responses.activate
    def test_file_upload_with_string_path(self, temp_file):
        """File upload with string path works."""
        responses.add(
            responses.POST,
            'https://api.example.com/upload/',
            json={'id': 1},
            status=201,
        )
        client = TestClient('https://api.example.com')
        result = client._request('post', 'upload/', files={'file': str(temp_file)})
        assert result == {'id': 1}


# -----------------------------------------------------------------------------
# Validation Integration Tests
# -----------------------------------------------------------------------------


class TestValidationIntegration:
    """Tests for Pydantic validation integration."""

    @responses.activate
    def test_get_with_response_model(self):
        """GET with response_model validates response."""
        responses.add(
            responses.GET,
            'https://api.example.com/users/1/',
            json={'id': 1, 'name': 'Test'},
            status=200,
        )
        client = TestClient('https://api.example.com')
        result = client._get('users/1/', response_model=ResponseModel)
        assert result == {'id': 1, 'name': 'Test'}

    @responses.activate
    def test_post_with_request_model(self):
        """POST with request_model validates request."""
        responses.add(
            responses.POST,
            'https://api.example.com/items/',
            json={'id': 1, 'name': 'Test'},
            status=201,
        )
        client = TestClient('https://api.example.com')
        result = client._post('items/', request_model=RequestModel, data={'name': 'Test', 'value': 42})
        assert result == {'id': 1, 'name': 'Test'}

    @responses.activate
    def test_post_with_invalid_request_data(self):
        """POST with invalid request data raises ValidationError."""
        client = TestClient('https://api.example.com')
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            client._post('items/', request_model=RequestModel, data={'name': 'Test'})  # Missing 'value'


# -----------------------------------------------------------------------------
# Pagination Tests
# -----------------------------------------------------------------------------


class TestPagination:
    """Tests for pagination handling."""

    @responses.activate
    def test_list_returns_page(self):
        """_list returns paginated response dict."""
        responses.add(
            responses.GET,
            'https://api.example.com/items/',
            json={'count': 25, 'next': None, 'previous': None, 'results': [{'id': 1}]},
            status=200,
        )
        client = TestClient('https://api.example.com')
        result = client._list('items/')
        assert result['count'] == 25
        assert result['results'] == [{'id': 1}]

    @responses.activate
    def test_list_all_returns_generator_and_count(self):
        """_list with list_all=True returns (generator, count)."""
        responses.add(
            responses.GET,
            'https://api.example.com/items/',
            json={'count': 2, 'next': None, 'previous': None, 'results': [{'id': 1}, {'id': 2}]},
            status=200,
        )
        client = TestClient('https://api.example.com')
        generator, count = client._list('items/', list_all=True)
        assert count == 2
        items = list(generator)
        assert len(items) == 2

    @responses.activate
    def test_list_all_pagination(self):
        """_list_all follows pagination."""
        responses.add(
            responses.GET,
            'https://api.example.com/items/',
            json={
                'count': 3,
                'next': 'https://api.example.com/items/?page=2',
                'results': [{'id': 1}],
            },
            status=200,
        )
        responses.add(
            responses.GET,
            'https://api.example.com/items/?page=2',
            json={
                'count': 3,
                'next': None,
                'results': [{'id': 2}, {'id': 3}],
            },
            status=200,
        )
        client = TestClient('https://api.example.com')
        items = list(client._list_all('items/'))
        assert len(items) == 3
        assert items[0]['id'] == 1
        assert items[2]['id'] == 3

    @responses.activate
    def test_list_all_empty_results(self):
        """_list_all handles empty results."""
        responses.add(
            responses.GET,
            'https://api.example.com/items/',
            json={'count': 0, 'next': None, 'results': []},
            status=200,
        )
        client = TestClient('https://api.example.com')
        items = list(client._list_all('items/'))
        assert items == []

    @responses.activate
    def test_exists_true(self):
        """exists returns True when count > 0."""
        responses.add(
            responses.GET,
            'https://api.example.com/items/',
            json={'count': 5, 'next': None, 'results': [{'id': 1}]},
            status=200,
        )
        client = TestClient('https://api.example.com')
        result = client.exists('_list', 'items/')
        assert result is True

    @responses.activate
    def test_exists_false(self):
        """exists returns False when count == 0."""
        responses.add(
            responses.GET,
            'https://api.example.com/items/',
            json={'count': 0, 'next': None, 'results': []},
            status=200,
        )
        client = TestClient('https://api.example.com')
        result = client.exists('_list', 'items/')
        assert result is False


# -----------------------------------------------------------------------------
# HTTP Method Shortcut Tests
# -----------------------------------------------------------------------------


class TestHTTPMethodShortcuts:
    """Tests for HTTP method shortcut methods."""

    @responses.activate
    def test_get_method(self):
        """_get method works."""
        responses.add(
            responses.GET,
            'https://api.example.com/resource/',
            json={'id': 1},
            status=200,
        )
        client = TestClient('https://api.example.com')
        result = client._get('resource/')
        assert result == {'id': 1}

    @responses.activate
    def test_post_method(self):
        """_post method works."""
        responses.add(
            responses.POST,
            'https://api.example.com/resource/',
            json={'id': 1},
            status=201,
        )
        client = TestClient('https://api.example.com')
        result = client._post('resource/', data={'name': 'test'})
        assert result == {'id': 1}

    @responses.activate
    def test_put_method(self):
        """_put method works."""
        responses.add(
            responses.PUT,
            'https://api.example.com/resource/1/',
            json={'id': 1},
            status=200,
        )
        client = TestClient('https://api.example.com')
        result = client._put('resource/1/', data={'name': 'updated'})
        assert result == {'id': 1}

    @responses.activate
    def test_patch_method(self):
        """_patch method works."""
        responses.add(
            responses.PATCH,
            'https://api.example.com/resource/1/',
            json={'id': 1},
            status=200,
        )
        client = TestClient('https://api.example.com')
        result = client._patch('resource/1/', data={'name': 'patched'})
        assert result == {'id': 1}

    @responses.activate
    def test_delete_method(self):
        """_delete method works."""
        responses.add(
            responses.DELETE,
            'https://api.example.com/resource/1/',
            status=204,
        )
        client = TestClient('https://api.example.com')
        result = client._delete('resource/1/')
        assert result is None
