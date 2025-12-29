"""Template for creating new HTTP clients.

This module provides template classes for building new sync and async
HTTP clients. Copy this file and modify it to create a new client.

Usage:
    1. Copy this file to a new module (e.g., my_api/__init__.py)
    2. Rename TemplateClient and AsyncTemplateClient
    3. Implement _get_headers() with your authentication
    4. Add domain-specific methods

Example:
    >>> from synapse_sdk.clients.my_api import MyApiClient
    >>> client = MyApiClient('https://api.example.com', api_key='secret')
    >>> users = client.list_users()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from synapse_sdk.clients.base import AsyncBaseClient, BaseClient

if TYPE_CHECKING:
    from pydantic import BaseModel


class TemplateClient(BaseClient):
    """Synchronous HTTP client template.

    This template demonstrates how to create a new sync client by
    extending BaseClient with custom authentication and methods.

    Attributes:
        name: Client name for error messages.
        api_key: API key for authentication.
    """

    name = 'TemplateAPI'

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: dict[str, int] | None = None,
    ):
        """Initialize the template client.

        Args:
            base_url: The base URL for all API requests.
            api_key: API key for authentication.
            timeout: Optional timeout configuration.
        """
        super().__init__(base_url, timeout=timeout)
        self.api_key = api_key

    def _get_headers(self) -> dict[str, str]:
        """Return authentication headers.

        Override this method to implement your authentication scheme.
        Common patterns include:
        - API key: {'X-API-Key': self.api_key}
        - Bearer token: {'Authorization': f'Bearer {self.token}'}
        - Basic auth: {'Authorization': f'Basic {base64_credentials}'}
        """
        return {'X-API-Key': self.api_key}

    # -------------------------------------------------------------------------
    # Example API Methods
    # -------------------------------------------------------------------------

    def list_resources(
        self,
        params: dict[str, Any] | None = None,
        *,
        list_all: bool = False,
    ) -> dict[str, Any] | tuple[Any, int]:
        """List resources with optional pagination.

        Args:
            params: Query parameters for filtering.
            list_all: If True, returns (generator, count).

        Returns:
            Paginated list or (generator, count).
        """
        return self._list('resources/', params=params, list_all=list_all)

    def get_resource(self, resource_id: int) -> dict[str, Any]:
        """Get a resource by ID.

        Args:
            resource_id: The resource ID.

        Returns:
            Resource data.
        """
        return self._get(f'resources/{resource_id}/')

    def create_resource(
        self,
        data: dict[str, Any],
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> dict[str, Any]:
        """Create a new resource.

        Args:
            data: Resource data to create.
            request_model: Optional Pydantic model for request validation.
            response_model: Optional Pydantic model for response validation.

        Returns:
            Created resource data.
        """
        return self._post(
            'resources/',
            request_model=request_model,
            response_model=response_model,
            data=data,
        )

    def update_resource(
        self,
        resource_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update a resource.

        Args:
            resource_id: The resource ID to update.
            data: Fields to update.

        Returns:
            Updated resource data.
        """
        return self._patch(f'resources/{resource_id}/', data=data)

    def delete_resource(self, resource_id: int) -> None:
        """Delete a resource.

        Args:
            resource_id: The resource ID to delete.
        """
        self._delete(f'resources/{resource_id}/')


class AsyncTemplateClient(AsyncBaseClient):
    """Asynchronous HTTP client template.

    This template demonstrates how to create a new async client by
    extending AsyncBaseClient with custom authentication and methods.

    Attributes:
        name: Client name for error messages.
        api_key: API key for authentication.
    """

    name = 'TemplateAPI'

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float | httpx.Timeout | None = None,
    ):
        """Initialize the async template client.

        Args:
            base_url: The base URL for all API requests.
            api_key: API key for authentication.
            timeout: Optional timeout configuration.
        """
        super().__init__(base_url, timeout=timeout)
        self.api_key = api_key

    def _get_headers(self) -> dict[str, str]:
        """Return authentication headers."""
        return {'X-API-Key': self.api_key}

    # -------------------------------------------------------------------------
    # Example API Methods (Async versions)
    # -------------------------------------------------------------------------

    async def list_resources(
        self,
        params: dict[str, Any] | None = None,
        *,
        list_all: bool = False,
    ) -> dict[str, Any] | tuple[Any, int]:
        """List resources with optional pagination.

        Args:
            params: Query parameters for filtering.
            list_all: If True, returns (generator, count).

        Returns:
            Paginated list or (generator, count).
        """
        return await self._list('resources/', params=params, list_all=list_all)

    async def get_resource(self, resource_id: int) -> dict[str, Any]:
        """Get a resource by ID.

        Args:
            resource_id: The resource ID.

        Returns:
            Resource data.
        """
        return await self._get(f'resources/{resource_id}/')

    async def create_resource(
        self,
        data: dict[str, Any],
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> dict[str, Any]:
        """Create a new resource.

        Args:
            data: Resource data to create.
            request_model: Optional Pydantic model for request validation.
            response_model: Optional Pydantic model for response validation.

        Returns:
            Created resource data.
        """
        return await self._post(
            'resources/',
            request_model=request_model,
            response_model=response_model,
            json=data,
        )

    async def update_resource(
        self,
        resource_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update a resource.

        Args:
            resource_id: The resource ID to update.
            data: Fields to update.

        Returns:
            Updated resource data.
        """
        return await self._patch(f'resources/{resource_id}/', json=data)

    async def delete_resource(self, resource_id: int) -> None:
        """Delete a resource.

        Args:
            resource_id: The resource ID to delete.
        """
        await self._delete(f'resources/{resource_id}/')


# Note: This file is a template. Do not import or use these classes directly.
# Copy and modify them for your specific API client implementation.
