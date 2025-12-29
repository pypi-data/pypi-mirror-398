"""Tests for synapse_sdk.clients.base.AsyncBaseClient."""

from __future__ import annotations

import httpx
import pytest
from pydantic import BaseModel

from synapse_sdk.clients.base import AsyncBaseClient
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


class TestAsyncClient(AsyncBaseClient):
    """Test async client with custom headers."""

    name = 'TestAsyncClient'

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


class TestAsyncBaseClientInit:
    """Tests for AsyncBaseClient initialization."""

    def test_base_url_normalized(self):
        """Trailing slash is removed from base_url."""
        client = TestAsyncClient('https://api.example.com/')
        assert client.base_url == 'https://api.example.com'

    def test_base_url_without_trailing_slash(self):
        """Base URL without trailing slash is unchanged."""
        client = TestAsyncClient('https://api.example.com')
        assert client.base_url == 'https://api.example.com'

    def test_default_timeout(self):
        """Default timeout is set."""
        client = TestAsyncClient('https://api.example.com')
        assert isinstance(client.timeout, httpx.Timeout)

    def test_custom_timeout_float(self):
        """Custom float timeout is used."""
        client = TestAsyncClient('https://api.example.com', timeout=30.0)
        assert client.timeout == 30.0

    def test_custom_timeout_object(self):
        """Custom Timeout object is used."""
        timeout = httpx.Timeout(10.0, connect=5.0)
        client = TestAsyncClient('https://api.example.com', timeout=timeout)
        assert client.timeout == timeout

    def test_default_page_size(self):
        """Default page_size is 100."""
        client = TestAsyncClient('https://api.example.com')
        assert client.page_size == 100

    def test_client_not_created_on_init(self):
        """HTTP client is not created during initialization."""
        client = TestAsyncClient('https://api.example.com')
        assert client._client is None


# -----------------------------------------------------------------------------
# Context Manager Tests
# -----------------------------------------------------------------------------


class TestContextManager:
    """Tests for async context manager."""

    @pytest.mark.asyncio
    async def test_async_context_manager_enter(self):
        """Async context manager returns client on enter."""
        async with TestAsyncClient('https://api.example.com') as client:
            assert isinstance(client, TestAsyncClient)

    @pytest.mark.asyncio
    async def test_async_context_manager_closes_on_exit(self):
        """Async context manager closes client on exit."""
        client = TestAsyncClient('https://api.example.com')
        async with client:
            # Access client to create it
            await client._get_client()
            assert client._client is not None
        # After exit, client should be closed
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_method(self):
        """close() method closes the client."""
        client = TestAsyncClient('https://api.example.com')
        await client._get_client()
        assert client._client is not None
        await client.close()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_when_not_opened(self):
        """close() works when client was never opened."""
        client = TestAsyncClient('https://api.example.com')
        assert client._client is None
        await client.close()  # Should not raise
        assert client._client is None


# -----------------------------------------------------------------------------
# Client Management Tests
# -----------------------------------------------------------------------------


class TestClientManagement:
    """Tests for HTTP client management."""

    @pytest.mark.asyncio
    async def test_client_lazy_init(self):
        """Client is created on first access."""
        client = TestAsyncClient('https://api.example.com')
        assert client._client is None
        http_client = await client._get_client()
        assert http_client is not None
        assert client._client is http_client

    @pytest.mark.asyncio
    async def test_client_reused(self):
        """Same client is returned on multiple accesses."""
        client = TestAsyncClient('https://api.example.com')
        client1 = await client._get_client()
        client2 = await client._get_client()
        assert client1 is client2
        await client.close()

    @pytest.mark.asyncio
    async def test_client_recreated_after_close(self):
        """New client is created after close."""
        client = TestAsyncClient('https://api.example.com')
        client1 = await client._get_client()
        await client.close()
        client2 = await client._get_client()
        assert client1 is not client2
        await client.close()


# -----------------------------------------------------------------------------
# Request Handling Tests
# -----------------------------------------------------------------------------


class TestAsyncRequestHandling:
    """Tests for async _request method."""

    @pytest.mark.asyncio
    async def test_get_request(self, respx_mock):
        """GET request works correctly."""
        respx_mock.get('https://api.example.com/users/1/').mock(
            return_value=httpx.Response(200, json={'id': 1, 'name': 'Test User'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._request('GET', 'users/1/')
            assert result == {'id': 1, 'name': 'Test User'}

    @pytest.mark.asyncio
    async def test_post_request(self, respx_mock):
        """POST request works correctly."""
        respx_mock.post('https://api.example.com/users/').mock(
            return_value=httpx.Response(201, json={'id': 1, 'name': 'New User'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._request('POST', 'users/', json={'name': 'New User'})
            assert result == {'id': 1, 'name': 'New User'}

    @pytest.mark.asyncio
    async def test_put_request(self, respx_mock):
        """PUT request works correctly."""
        respx_mock.put('https://api.example.com/users/1/').mock(
            return_value=httpx.Response(200, json={'id': 1, 'name': 'Updated User'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._request('PUT', 'users/1/', json={'name': 'Updated'})
            assert result == {'id': 1, 'name': 'Updated User'}

    @pytest.mark.asyncio
    async def test_patch_request(self, respx_mock):
        """PATCH request works correctly."""
        respx_mock.patch('https://api.example.com/users/1/').mock(
            return_value=httpx.Response(200, json={'id': 1, 'name': 'Patched'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._request('PATCH', 'users/1/', json={'name': 'Patched'})
            assert result == {'id': 1, 'name': 'Patched'}

    @pytest.mark.asyncio
    async def test_delete_request(self, respx_mock):
        """DELETE request works correctly."""
        respx_mock.delete('https://api.example.com/users/1/').mock(return_value=httpx.Response(204))
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._request('DELETE', 'users/1/')
            assert result is None

    @pytest.mark.asyncio
    async def test_headers_merged(self, respx_mock):
        """Custom headers are merged with default headers."""
        route = respx_mock.get('https://api.example.com/test/').mock(
            return_value=httpx.Response(200, json={'ok': True})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            await client._request('GET', 'test/', headers={'X-Custom': 'custom-value'})

        # Check that both headers were sent
        request = route.calls[0].request
        assert request.headers['X-Test-Header'] == 'test-value'
        assert request.headers['X-Custom'] == 'custom-value'


# -----------------------------------------------------------------------------
# Error Handling Tests
# -----------------------------------------------------------------------------


class TestAsyncErrorHandling:
    """Tests for async error handling."""

    @pytest.mark.asyncio
    async def test_401_raises_authentication_error(self, respx_mock):
        """401 response raises AuthenticationError."""
        respx_mock.get('https://api.example.com/protected/').mock(
            return_value=httpx.Response(401, json={'detail': 'Invalid token'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            with pytest.raises(AuthenticationError) as exc_info:
                await client._request('GET', 'protected/')
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_403_raises_authorization_error(self, respx_mock):
        """403 response raises AuthorizationError."""
        respx_mock.get('https://api.example.com/admin/').mock(
            return_value=httpx.Response(403, json={'detail': 'Forbidden'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            with pytest.raises(AuthorizationError) as exc_info:
                await client._request('GET', 'admin/')
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_404_raises_not_found_error(self, respx_mock):
        """404 response raises NotFoundError."""
        respx_mock.get('https://api.example.com/missing/').mock(
            return_value=httpx.Response(404, json={'detail': 'Not found'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            with pytest.raises(NotFoundError) as exc_info:
                await client._request('GET', 'missing/')
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_400_raises_validation_error(self, respx_mock):
        """400 response raises ValidationError."""
        respx_mock.post('https://api.example.com/users/').mock(
            return_value=httpx.Response(400, json={'detail': 'Invalid data'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            with pytest.raises(ValidationError) as exc_info:
                await client._request('POST', 'users/', json={})
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error(self, respx_mock):
        """429 response raises RateLimitError."""
        respx_mock.get('https://api.example.com/rate-limited/').mock(
            return_value=httpx.Response(429, json={'detail': 'Too many requests'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client._request('GET', 'rate-limited/')
            assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_500_raises_server_error(self, respx_mock):
        """500 response raises ServerError."""
        respx_mock.get('https://api.example.com/error/').mock(
            return_value=httpx.Response(500, json={'detail': 'Internal error'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            with pytest.raises(ServerError) as exc_info:
                await client._request('GET', 'error/')
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_connect_timeout_raises_client_timeout_error(self, respx_mock):
        """Connect timeout raises ClientTimeoutError."""
        respx_mock.get('https://api.example.com/slow/').mock(side_effect=httpx.ConnectTimeout('Timeout'))
        async with TestAsyncClient('https://api.example.com') as client:
            with pytest.raises(ClientTimeoutError):
                await client._request('GET', 'slow/')

    @pytest.mark.asyncio
    async def test_read_timeout_raises_client_timeout_error(self, respx_mock):
        """Read timeout raises ClientTimeoutError."""
        respx_mock.get('https://api.example.com/slow/').mock(side_effect=httpx.ReadTimeout('Timeout'))
        async with TestAsyncClient('https://api.example.com') as client:
            with pytest.raises(ClientTimeoutError):
                await client._request('GET', 'slow/')

    @pytest.mark.asyncio
    async def test_connect_error_raises_client_connection_error(self, respx_mock):
        """Connect error raises ClientConnectionError."""
        respx_mock.get('https://api.example.com/unreachable/').mock(side_effect=httpx.ConnectError('Connection failed'))
        async with TestAsyncClient('https://api.example.com') as client:
            with pytest.raises(ClientConnectionError):
                await client._request('GET', 'unreachable/')


# -----------------------------------------------------------------------------
# Response Handling Tests
# -----------------------------------------------------------------------------


class TestAsyncResponseHandling:
    """Tests for async response handling."""

    @pytest.mark.asyncio
    async def test_json_response_parsed(self, respx_mock):
        """JSON response is parsed correctly."""
        respx_mock.get('https://api.example.com/data/').mock(
            return_value=httpx.Response(200, json={'key': 'value', 'nested': {'a': 1}})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._request('GET', 'data/')
            assert result == {'key': 'value', 'nested': {'a': 1}}

    @pytest.mark.asyncio
    async def test_204_returns_none(self, respx_mock):
        """204 No Content returns None."""
        respx_mock.delete('https://api.example.com/item/').mock(return_value=httpx.Response(204))
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._request('DELETE', 'item/')
            assert result is None

    @pytest.mark.asyncio
    async def test_text_response_fallback(self, respx_mock):
        """Non-JSON response returns text."""
        respx_mock.get('https://api.example.com/text/').mock(
            return_value=httpx.Response(200, text='Plain text response')
        )
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._request('GET', 'text/')
            assert result == 'Plain text response'


# -----------------------------------------------------------------------------
# Validation Integration Tests
# -----------------------------------------------------------------------------


class TestAsyncValidationIntegration:
    """Tests for async Pydantic validation integration."""

    @pytest.mark.asyncio
    async def test_get_with_response_model(self, respx_mock):
        """GET with response_model validates response."""
        respx_mock.get('https://api.example.com/users/1/').mock(
            return_value=httpx.Response(200, json={'id': 1, 'name': 'Test'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._get('users/1/', response_model=ResponseModel)
            assert result == {'id': 1, 'name': 'Test'}

    @pytest.mark.asyncio
    async def test_post_with_request_model(self, respx_mock):
        """POST with request_model validates request."""
        respx_mock.post('https://api.example.com/items/').mock(
            return_value=httpx.Response(201, json={'id': 1, 'name': 'Test'})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._post('items/', request_model=RequestModel, json={'name': 'Test', 'value': 42})
            assert result == {'id': 1, 'name': 'Test'}

    @pytest.mark.asyncio
    async def test_post_with_invalid_request_data(self):
        """POST with invalid request data raises ValidationError."""
        from pydantic import ValidationError as PydanticValidationError

        async with TestAsyncClient('https://api.example.com') as client:
            with pytest.raises(PydanticValidationError):
                await client._post('items/', request_model=RequestModel, json={'name': 'Test'})  # Missing 'value'


# -----------------------------------------------------------------------------
# Pagination Tests
# -----------------------------------------------------------------------------


class TestAsyncPagination:
    """Tests for async pagination handling."""

    @pytest.mark.asyncio
    async def test_list_returns_page(self, respx_mock):
        """_list returns paginated response dict."""
        respx_mock.get('https://api.example.com/items/').mock(
            return_value=httpx.Response(
                200,
                json={'count': 25, 'next': None, 'previous': None, 'results': [{'id': 1}]},
            )
        )
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._list('items/')
            assert result['count'] == 25
            assert result['results'] == [{'id': 1}]

    @pytest.mark.asyncio
    async def test_list_all_returns_generator_and_count(self, respx_mock):
        """_list with list_all=True returns (generator, count)."""
        respx_mock.get('https://api.example.com/items/').mock(
            return_value=httpx.Response(
                200,
                json={'count': 2, 'next': None, 'previous': None, 'results': [{'id': 1}, {'id': 2}]},
            )
        )
        async with TestAsyncClient('https://api.example.com') as client:
            generator, count = await client._list('items/', list_all=True)
            assert count == 2
            items = [item async for item in generator]
            assert len(items) == 2

    @pytest.mark.asyncio
    async def test_list_all_pagination(self, respx_mock):
        """_list_all follows pagination."""
        # First page
        respx_mock.get('https://api.example.com/items/', params__contains={'page_size': '100'}).mock(
            return_value=httpx.Response(
                200,
                json={
                    'count': 3,
                    'next': 'items/?page=2',  # Relative URL for next page
                    'results': [{'id': 1}],
                },
            )
        )
        # Second page (relative path)
        respx_mock.get('https://api.example.com/items/', params__contains={'page': '2'}).mock(
            return_value=httpx.Response(
                200,
                json={
                    'count': 3,
                    'next': None,
                    'results': [{'id': 2}, {'id': 3}],
                },
            )
        )
        async with TestAsyncClient('https://api.example.com') as client:
            items = [item async for item in client._list_all('items/')]
            assert len(items) == 3
            assert items[0]['id'] == 1
            assert items[2]['id'] == 3

    @pytest.mark.asyncio
    async def test_list_all_empty_results(self, respx_mock):
        """_list_all handles empty results."""
        respx_mock.get('https://api.example.com/items/').mock(
            return_value=httpx.Response(200, json={'count': 0, 'next': None, 'results': []})
        )
        async with TestAsyncClient('https://api.example.com') as client:
            items = [item async for item in client._list_all('items/')]
            assert items == []


# -----------------------------------------------------------------------------
# HTTP Method Shortcut Tests
# -----------------------------------------------------------------------------


class TestAsyncHTTPMethodShortcuts:
    """Tests for async HTTP method shortcut methods."""

    @pytest.mark.asyncio
    async def test_get_method(self, respx_mock):
        """_get method works."""
        respx_mock.get('https://api.example.com/resource/').mock(return_value=httpx.Response(200, json={'id': 1}))
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._get('resource/')
            assert result == {'id': 1}

    @pytest.mark.asyncio
    async def test_post_method(self, respx_mock):
        """_post method works."""
        respx_mock.post('https://api.example.com/resource/').mock(return_value=httpx.Response(201, json={'id': 1}))
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._post('resource/', json={'name': 'test'})
            assert result == {'id': 1}

    @pytest.mark.asyncio
    async def test_put_method(self, respx_mock):
        """_put method works."""
        respx_mock.put('https://api.example.com/resource/1/').mock(return_value=httpx.Response(200, json={'id': 1}))
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._put('resource/1/', json={'name': 'updated'})
            assert result == {'id': 1}

    @pytest.mark.asyncio
    async def test_patch_method(self, respx_mock):
        """_patch method works."""
        respx_mock.patch('https://api.example.com/resource/1/').mock(return_value=httpx.Response(200, json={'id': 1}))
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._patch('resource/1/', json={'name': 'patched'})
            assert result == {'id': 1}

    @pytest.mark.asyncio
    async def test_delete_method(self, respx_mock):
        """_delete method works."""
        respx_mock.delete('https://api.example.com/resource/1/').mock(return_value=httpx.Response(204))
        async with TestAsyncClient('https://api.example.com') as client:
            result = await client._delete('resource/1/')
            assert result is None
