"""Protocol definitions for HTTP clients.

This module defines protocols for sync and async HTTP clients,
enabling proper type hints in mixins with IDE autocompletion support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pydantic import BaseModel


@runtime_checkable
class ClientProtocol(Protocol):
    """Protocol for synchronous HTTP clients.

    This protocol enables proper type hints in mixin classes,
    providing IDE autocompletion for client methods.

    Attributes:
        name: Client name for error messages.
        base_url: Base URL for API requests.
        page_size: Default page size for pagination.
    """

    name: str | None
    base_url: str
    page_size: int

    def _get_headers(self) -> dict[str, str]:
        """Return headers for requests."""
        ...

    def _get(
        self,
        path: str,
        url_conversion: dict | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a GET request."""
        ...

    def _post(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a POST request."""
        ...

    def _put(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a PUT request."""
        ...

    def _patch(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a PATCH request."""
        ...

    def _delete(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a DELETE request."""
        ...

    def _list(
        self,
        path: str,
        url_conversion: dict | None = None,
        list_all: bool = False,
        params: dict | None = None,
        **kwargs,
    ) -> dict | tuple[Any, int]:
        """List resources from a paginated API endpoint."""
        ...


@runtime_checkable
class AsyncClientProtocol(Protocol):
    """Protocol for asynchronous HTTP clients.

    This protocol enables proper type hints in async mixin classes,
    providing IDE autocompletion for async client methods.

    Attributes:
        name: Client name for error messages.
        base_url: Base URL for API requests.
        page_size: Default page size for pagination.
    """

    name: str | None
    base_url: str
    page_size: int

    def _get_headers(self) -> dict[str, str]:
        """Return headers for requests."""
        ...

    async def _get(
        self,
        path: str,
        url_conversion: dict | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a GET request."""
        ...

    async def _post(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a POST request."""
        ...

    async def _put(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a PUT request."""
        ...

    async def _patch(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a PATCH request."""
        ...

    async def _delete(
        self,
        path: str,
        request_model: type[BaseModel] | None = None,
        response_model: type[BaseModel] | None = None,
        **kwargs,
    ) -> Any:
        """Perform a DELETE request."""
        ...

    async def _list(
        self,
        path: str,
        url_conversion: dict | None = None,
        list_all: bool = False,
        params: dict | None = None,
        **kwargs,
    ) -> dict | tuple[Any, int]:
        """List resources from a paginated API endpoint."""
        ...
