"""Base HTTP client classes for sync and async operations.

This module provides BaseClient (sync) and AsyncBaseClient (async) classes
that serve as the foundation for all API clients in the SDK.
"""

from __future__ import annotations

import json
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from synapse_sdk.clients.utils import build_url, extract_error_detail, parse_json_response
from synapse_sdk.clients.validation import ValidationMixin
from synapse_sdk.exceptions import (
    ClientConnectionError,
    ClientError,
    ClientTimeoutError,
    ServerError,
    raise_for_status,
)
from synapse_sdk.utils.file import files_url_to_path_from_objs

if TYPE_CHECKING:
    from pydantic import BaseModel


class BaseClient(ValidationMixin):
    """Synchronous HTTP client base using requests.

    This class provides a foundation for building API clients with
    session management, retry logic, and request/response handling.

    Attributes:
        name: Client name for error messages.
        page_size: Default page size for paginated requests.
    """

    name: str | None = None
    page_size: int = 100

    def __init__(self, base_url: str, timeout: dict[str, int] | None = None):
        """Initialize the base client.

        Args:
            base_url: The base URL for all API requests.
            timeout: Optional timeout configuration with 'connect' and 'read' keys.
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout or {
            'connect': 5,
            'read': 15,
        }
        self._session: requests.Session | None = None
        self._retry_config = {
            'total': 3,
            'backoff_factor': 1,
            'status_forcelist': [502, 503, 504],
            'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
        }

    def _create_session(self) -> requests.Session:
        """Create a new requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(**self._retry_config)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    @property
    def requests_session(self) -> requests.Session:
        """Get or create the requests session."""
        if self._session is None:
            self._session = self._create_session()
        return self._session

    def _get_headers(self) -> dict[str, str]:
        """Return headers for requests. Override in subclasses."""
        return {}

    def _request(self, method: str, path: str, **kwargs) -> dict | str | None:
        """Request handler for all HTTP methods.

        Args:
            method: HTTP method (get, post, put, patch, delete).
            path: URL path to request.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Parsed response data.

        Raises:
            ClientTimeoutError: If the request times out.
            ClientConnectionError: If connection fails.
            HTTPError subclasses: For HTTP error responses.
        """
        url = build_url(self.base_url, path)
        headers = self._get_headers()
        headers.update(kwargs.pop('headers', {}))

        if 'timeout' not in kwargs:
            kwargs['timeout'] = (self.timeout['connect'], self.timeout['read'])

        with ExitStack() as stack:
            if method in ('post', 'put', 'patch'):
                self._prepare_request_body(kwargs, headers, stack)

            try:
                response = getattr(self.requests_session, method)(url, headers=headers, **kwargs)
                if not response.ok:
                    raise_for_status(response.status_code, extract_error_detail(response))
            except (
                ClientError,
                ClientTimeoutError,
                ClientConnectionError,
            ):
                raise
            except requests.exceptions.ConnectTimeout:
                raise ClientTimeoutError(f'{self.name} connection timeout (>{self.timeout["connect"]}s)')
            except requests.exceptions.ReadTimeout:
                raise ClientTimeoutError(f'{self.name} read timeout (>{self.timeout["read"]}s)')
            except requests.exceptions.ConnectionError as e:
                error_str = str(e)
                if 'Name or service not known' in error_str or 'nodename nor servname provided' in error_str:
                    raise ClientConnectionError(f'{self.name} host unreachable')
                elif 'Connection refused' in error_str:
                    raise ClientConnectionError(f'{self.name} connection refused')
                else:
                    raise ClientConnectionError(f'{self.name} connection error: {error_str[:100]}')
            except requests.exceptions.RequestException as e:
                raise ServerError(500, f'{self.name} request failed: {str(e)[:100]}')

        return parse_json_response(response)

    def _prepare_request_body(self, kwargs: dict, headers: dict, stack: ExitStack) -> None:
        """Prepare request body, handling files and JSON serialization."""
        if kwargs.get('files') is not None:
            for name, file in kwargs['files'].items():
                if isinstance(file, (str, Path)):
                    file = Path(file)
                    opened_file = stack.enter_context(file.open(mode='rb'))
                    kwargs['files'][name] = (file.name, opened_file)
            if 'data' in kwargs:
                for name, value in kwargs['data'].items():
                    if isinstance(value, dict):
                        kwargs['data'][name] = json.dumps(value)
        else:
            headers['Content-Type'] = 'application/json'
            if 'data' in kwargs:
                kwargs['data'] = json.dumps(kwargs['data'])

    def _get(
        self,
        path: str,
        url_conversion: dict | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a GET request.

        Args:
            path: URL path to request.
            url_conversion: Optional URL conversion config for file paths.
            response_model: Optional Pydantic model for response validation.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Parsed and optionally validated response data.
        """
        response = self._request('get', path, **kwargs)

        if url_conversion and isinstance(response, dict):
            is_list = url_conversion.get('is_list', False)
            if is_list:
                files_url_to_path_from_objs(response['results'], **url_conversion, is_async=True)
            else:
                files_url_to_path_from_objs(response, **url_conversion)

        if response_model:
            return self._validate_response(response, response_model)
        return response

    def _mutate(
        self,
        method: str,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a mutating request (POST, PUT, PATCH, DELETE).

        Args:
            method: HTTP method.
            path: URL path to request.
            request_model: Optional Pydantic model for request validation.
            response_model: Optional Pydantic model for response validation.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Parsed and optionally validated response data.
        """
        if kwargs.get('data') and request_model:
            kwargs['data'] = self._validate_request(kwargs['data'], request_model)

        response = self._request(method, path, **kwargs)

        if response_model:
            return self._validate_response(response, response_model)
        return response

    def _post(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a POST request."""
        return self._mutate('post', path, request_model, response_model, **kwargs)

    def _put(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a PUT request."""
        return self._mutate('put', path, request_model, response_model, **kwargs)

    def _patch(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a PATCH request."""
        return self._mutate('patch', path, request_model, response_model, **kwargs)

    def _delete(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a DELETE request."""
        return self._mutate('delete', path, request_model, response_model, **kwargs)

    def _list(
        self,
        path: str,
        url_conversion: dict | None = None,
        list_all: bool = False,
        params: dict | None = None,
        **kwargs,
    ) -> dict | tuple[Any, int]:
        """List resources from a paginated API endpoint.

        Args:
            path: URL path to request.
            url_conversion: Optional URL conversion config for file paths.
            list_all: If True, return a generator for all pages.
            params: Optional query parameters.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response dict, or tuple of (generator, count) if list_all=True.
        """
        if params is None:
            params = {}

        if list_all:
            response = self._get(path, params=params, **kwargs)
            return self._list_all(path, url_conversion, params=params, **kwargs), response.get('count')
        return self._get(path, params=params, **kwargs)

    def _list_all(self, path: str, url_conversion: dict | None = None, params: dict | None = None, **kwargs):
        """Generator yielding all results from a paginated endpoint."""
        if params is None:
            params = {}

        request_params = params.copy()
        if 'page_size' not in request_params:
            request_params['page_size'] = self.page_size

        next_url = path
        is_first_request = True

        while next_url:
            if is_first_request:
                response = self._get(next_url, url_conversion, params=request_params, **kwargs)
                is_first_request = False
            else:
                response = self._get(next_url, url_conversion, **kwargs)

            yield from response['results']
            next_url = response.get('next')

    def exists(self, api: str, *args, **kwargs) -> bool:
        """Check if any results exist for the given API method."""
        return getattr(self, api)(*args, **kwargs)['count'] > 0


class AsyncBaseClient(ValidationMixin):
    """Asynchronous HTTP client base using httpx.

    This class provides a foundation for building async API clients with
    connection management and request/response handling.

    Attributes:
        name: Client name for error messages.
        page_size: Default page size for paginated requests.
    """

    name: str | None = None
    page_size: int = 100

    def __init__(
        self,
        base_url: str,
        timeout: float | httpx.Timeout | None = None,
    ):
        """Initialize the async base client.

        Args:
            base_url: The base URL for all API requests.
            timeout: Optional timeout configuration.
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout if timeout is not None else httpx.Timeout(15.0, connect=5.0)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> AsyncBaseClient:
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    def _get_headers(self) -> dict[str, str]:
        """Return headers for requests. Override in subclasses."""
        return {}

    async def _request(self, method: str, path: str, **kwargs) -> dict | str | None:
        """Request handler for all HTTP methods.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: URL path to request.
            **kwargs: Additional arguments passed to httpx.

        Returns:
            Parsed response data.

        Raises:
            ClientTimeoutError: If the request times out.
            ClientConnectionError: If connection fails.
            HTTPError subclasses: For HTTP error responses.
        """
        client = await self._get_client()
        # Handle full URLs (e.g., pagination next links) vs relative paths
        if path.startswith(('http://', 'https://')):
            url = path
        else:
            url = path.lstrip('/')
        headers = self._get_headers()
        headers.update(kwargs.pop('headers', {}))

        try:
            response = await client.request(method, url, headers=headers, **kwargs)
            if not response.is_success:
                raise_for_status(response.status_code, extract_error_detail(response))
        except (
            ClientError,
            ClientTimeoutError,
            ClientConnectionError,
        ):
            raise
        except httpx.ConnectTimeout:
            raise ClientTimeoutError(f'{self.name} connection timeout')
        except httpx.ReadTimeout:
            raise ClientTimeoutError(f'{self.name} read timeout')
        except httpx.ConnectError as e:
            raise ClientConnectionError(f'{self.name} connection error: {str(e)[:100]}')
        except httpx.HTTPStatusError as e:
            raise_for_status(e.response.status_code, extract_error_detail(e.response))
            raise  # unreachable, but helps type checker
        except httpx.HTTPError as e:
            raise ServerError(500, f'{self.name} request failed: {str(e)[:100]}')

        return parse_json_response(response)

    async def _get(
        self,
        path: str,
        url_conversion: dict | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a GET request.

        Args:
            path: URL path to request.
            url_conversion: Optional URL conversion config for file paths.
            response_model: Optional Pydantic model for response validation.
            **kwargs: Additional arguments passed to httpx.

        Returns:
            Parsed and optionally validated response data.
        """
        response = await self._request('GET', path, **kwargs)

        if url_conversion and isinstance(response, dict):
            is_list = url_conversion.get('is_list', False)
            if is_list:
                files_url_to_path_from_objs(response['results'], **url_conversion, is_async=True)
            else:
                files_url_to_path_from_objs(response, **url_conversion)

        if response_model:
            return self._validate_response(response, response_model)
        return response

    async def _mutate(
        self,
        method: str,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a mutating request (POST, PUT, PATCH, DELETE).

        Args:
            method: HTTP method.
            path: URL path to request.
            request_model: Optional Pydantic model for request validation.
            response_model: Optional Pydantic model for response validation.
            **kwargs: Additional arguments passed to httpx.

        Returns:
            Parsed and optionally validated response data.
        """
        if kwargs.get('json') and request_model:
            kwargs['json'] = self._validate_request(kwargs['json'], request_model)

        response = await self._request(method, path, **kwargs)

        if response_model:
            return self._validate_response(response, response_model)
        return response

    async def _post(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a POST request."""
        return await self._mutate('POST', path, request_model, response_model, **kwargs)

    async def _put(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a PUT request."""
        return await self._mutate('PUT', path, request_model, response_model, **kwargs)

    async def _patch(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a PATCH request."""
        return await self._mutate('PATCH', path, request_model, response_model, **kwargs)

    async def _delete(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a DELETE request."""
        return await self._mutate('DELETE', path, request_model, response_model, **kwargs)

    async def _list(
        self,
        path: str,
        url_conversion: dict | None = None,
        list_all: bool = False,
        params: dict | None = None,
        **kwargs,
    ) -> dict | tuple[Any, int]:
        """List resources from a paginated API endpoint.

        Args:
            path: URL path to request.
            url_conversion: Optional URL conversion config for file paths.
            list_all: If True, return a generator for all pages.
            params: Optional query parameters.
            **kwargs: Additional arguments passed to httpx.

        Returns:
            Response dict, or tuple of (generator, count) if list_all=True.
        """
        if params is None:
            params = {}

        if list_all:
            response = await self._get(path, params=params, **kwargs)
            return self._list_all(path, url_conversion, params=params, **kwargs), response.get('count')
        return await self._get(path, params=params, **kwargs)

    async def _list_all(
        self,
        path: str,
        url_conversion: dict | None = None,
        params: dict | None = None,
        **kwargs,
    ):
        """Async generator yielding all results from a paginated endpoint."""
        if params is None:
            params = {}

        request_params = params.copy()
        if 'page_size' not in request_params:
            request_params['page_size'] = self.page_size

        next_url: str | None = path
        is_first_request = True

        while next_url:
            if is_first_request:
                response = await self._get(next_url, url_conversion, params=request_params, **kwargs)
                is_first_request = False
            else:
                response = await self._get(next_url, url_conversion, **kwargs)

            for item in response['results']:
                yield item
            next_url = response.get('next')
