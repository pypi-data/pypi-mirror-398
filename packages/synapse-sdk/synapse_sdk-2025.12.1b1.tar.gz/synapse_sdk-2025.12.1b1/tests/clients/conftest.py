"""Shared fixtures for client tests."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# Pydantic Models for Testing
# -----------------------------------------------------------------------------


class SampleRequestModel(BaseModel):
    """Sample request model for validation tests."""

    name: str
    value: int
    optional_field: str | None = None


class SampleResponseModel(BaseModel):
    """Sample response model for validation tests."""

    id: int
    name: str
    status: str


class NestedModel(BaseModel):
    """Nested model for complex validation tests."""

    items: list[SampleResponseModel]
    count: int


# -----------------------------------------------------------------------------
# Mock Response Objects
# -----------------------------------------------------------------------------


class MockResponse:
    """Configurable mock response for testing."""

    def __init__(
        self,
        status_code: int = 200,
        json_data: dict | None = None,
        text: str = '',
        reason: str = 'OK',
        ok: bool | None = None,
    ):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.reason = reason
        self.reason_phrase = reason  # httpx style
        self.ok = ok if ok is not None else (200 <= status_code < 400)
        self.is_success = self.ok  # httpx style

    def json(self) -> dict:
        if self._json_data is None:
            raise ValueError('No JSON data')
        return self._json_data


@pytest.fixture
def mock_response():
    """Factory fixture for creating mock responses."""

    def _create_response(
        status_code: int = 200,
        json_data: dict | None = None,
        text: str = '',
        reason: str = 'OK',
        ok: bool | None = None,
    ) -> MockResponse:
        return MockResponse(
            status_code=status_code,
            json_data=json_data,
            text=text,
            reason=reason,
            ok=ok,
        )

    return _create_response


@pytest.fixture
def success_response() -> MockResponse:
    """Mock successful JSON response."""
    return MockResponse(
        status_code=200,
        json_data={'id': 1, 'name': 'test'},
        reason='OK',
    )


@pytest.fixture
def error_response() -> MockResponse:
    """Mock error response with detail."""
    return MockResponse(
        status_code=404,
        json_data={'detail': 'Not found'},
        reason='Not Found',
        ok=False,
    )


@pytest.fixture
def no_content_response() -> MockResponse:
    """Mock 204 No Content response."""
    return MockResponse(
        status_code=204,
        json_data=None,
        text='',
        reason='No Content',
    )


# -----------------------------------------------------------------------------
# Pydantic Model Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_request_model():
    """Sample request Pydantic model."""
    return SampleRequestModel


@pytest.fixture
def sample_response_model():
    """Sample response Pydantic model."""
    return SampleResponseModel


@pytest.fixture
def nested_model():
    """Nested Pydantic model."""
    return NestedModel


# -----------------------------------------------------------------------------
# Client Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def base_url() -> str:
    """Base URL for testing."""
    return 'https://api.example.com'


@pytest.fixture
def base_client(base_url):
    """Create a BaseClient instance for testing."""
    from synapse_sdk.clients.base import BaseClient

    class TestClient(BaseClient):
        name = 'TestClient'

        def _get_headers(self) -> dict[str, str]:
            return {'X-Test-Header': 'test-value'}

    return TestClient(base_url)


@pytest.fixture
def async_client(base_url):
    """Create an AsyncBaseClient instance for testing."""
    from synapse_sdk.clients.base import AsyncBaseClient

    class TestAsyncClient(AsyncBaseClient):
        name = 'TestAsyncClient'

        def _get_headers(self) -> dict[str, str]:
            return {'X-Test-Header': 'test-value'}

    return TestAsyncClient(base_url)


# -----------------------------------------------------------------------------
# File Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for upload testing."""
    file_path = tmp_path / 'test_file.txt'
    file_path.write_text('test content')
    return file_path


@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file for upload testing."""
    import json

    file_path = tmp_path / 'test_data.json'
    file_path.write_text(json.dumps({'key': 'value'}))
    return file_path


# -----------------------------------------------------------------------------
# Pagination Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def paginated_response() -> dict[str, Any]:
    """Sample paginated response."""
    return {
        'count': 25,
        'next': 'https://api.example.com/items/?page=2',
        'previous': None,
        'results': [{'id': i, 'name': f'Item {i}'} for i in range(1, 11)],
    }


@pytest.fixture
def last_page_response() -> dict[str, Any]:
    """Sample last page response (no next URL)."""
    return {
        'count': 25,
        'next': None,
        'previous': 'https://api.example.com/items/?page=2',
        'results': [{'id': i, 'name': f'Item {i}'} for i in range(21, 26)],
    }


@pytest.fixture
def empty_results_response() -> dict[str, Any]:
    """Sample empty results response."""
    return {
        'count': 0,
        'next': None,
        'previous': None,
        'results': [],
    }


# -----------------------------------------------------------------------------
# HTTP Mocking Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def respx_mock():
    """RESPX mock for async httpx testing."""
    import respx

    with respx.mock(assert_all_called=False) as mock:
        yield mock
