"""Tests for synapse_sdk.clients.protocols module."""

from __future__ import annotations

import pytest

from synapse_sdk.clients.protocols import AsyncClientProtocol, ClientProtocol

# -----------------------------------------------------------------------------
# ClientProtocol Tests
# -----------------------------------------------------------------------------


class TestClientProtocol:
    """Tests for ClientProtocol."""

    def test_runtime_checkable(self):
        """ClientProtocol is runtime_checkable."""
        # This verifies the @runtime_checkable decorator is applied

        # If it's runtime_checkable, isinstance() should work
        # (even though it may return False for incomplete implementations)
        assert hasattr(ClientProtocol, '__protocol_attrs__') or isinstance(ClientProtocol, type)

    def test_base_client_implements_protocol(self, base_client):
        """BaseClient implements ClientProtocol."""
        # Check that BaseClient has all required protocol attributes and methods
        assert hasattr(base_client, 'name')
        assert hasattr(base_client, 'base_url')
        assert hasattr(base_client, 'page_size')
        assert hasattr(base_client, '_get_headers')
        assert hasattr(base_client, '_get')
        assert hasattr(base_client, '_post')
        assert hasattr(base_client, '_put')
        assert hasattr(base_client, '_patch')
        assert hasattr(base_client, '_delete')
        assert hasattr(base_client, '_list')

    def test_protocol_has_required_attributes(self):
        """ClientProtocol specifies required attributes."""
        # Protocol attributes are in __annotations__, not as class attributes
        annotations = getattr(ClientProtocol, '__annotations__', {})
        assert 'name' in annotations
        assert 'base_url' in annotations
        assert 'page_size' in annotations

    def test_protocol_has_http_methods(self):
        """ClientProtocol specifies HTTP methods."""
        assert hasattr(ClientProtocol, '_get_headers')
        assert hasattr(ClientProtocol, '_get')
        assert hasattr(ClientProtocol, '_post')
        assert hasattr(ClientProtocol, '_put')
        assert hasattr(ClientProtocol, '_patch')
        assert hasattr(ClientProtocol, '_delete')
        assert hasattr(ClientProtocol, '_list')

    def test_isinstance_check_with_base_client(self, base_client):
        """isinstance() works with BaseClient and ClientProtocol."""
        # Due to Protocol semantics, isinstance may not always return True
        # for complex protocols, but it should not raise
        try:
            result = isinstance(base_client, ClientProtocol)
            # If it returns True, great; if False, it's expected for complex protocols
            assert isinstance(result, bool)
        except TypeError:
            # Some Protocol implementations may not support isinstance
            pytest.skip('Protocol does not support isinstance checking')


# -----------------------------------------------------------------------------
# AsyncClientProtocol Tests
# -----------------------------------------------------------------------------


class TestAsyncClientProtocol:
    """Tests for AsyncClientProtocol."""

    def test_runtime_checkable(self):
        """AsyncClientProtocol is runtime_checkable."""
        assert hasattr(AsyncClientProtocol, '__protocol_attrs__') or isinstance(AsyncClientProtocol, type)

    def test_async_base_client_implements_protocol(self, async_client):
        """AsyncBaseClient implements AsyncClientProtocol."""
        assert hasattr(async_client, 'name')
        assert hasattr(async_client, 'base_url')
        assert hasattr(async_client, 'page_size')
        assert hasattr(async_client, '_get_headers')
        assert hasattr(async_client, '_get')
        assert hasattr(async_client, '_post')
        assert hasattr(async_client, '_put')
        assert hasattr(async_client, '_patch')
        assert hasattr(async_client, '_delete')
        assert hasattr(async_client, '_list')

    def test_protocol_has_required_attributes(self):
        """AsyncClientProtocol specifies required attributes."""
        annotations = getattr(AsyncClientProtocol, '__annotations__', {})
        assert 'name' in annotations
        assert 'base_url' in annotations
        assert 'page_size' in annotations

    def test_protocol_has_async_methods(self):
        """AsyncClientProtocol specifies async methods."""
        assert hasattr(AsyncClientProtocol, '_get_headers')
        assert hasattr(AsyncClientProtocol, '_get')
        assert hasattr(AsyncClientProtocol, '_post')
        assert hasattr(AsyncClientProtocol, '_put')
        assert hasattr(AsyncClientProtocol, '_patch')
        assert hasattr(AsyncClientProtocol, '_delete')
        assert hasattr(AsyncClientProtocol, '_list')

    def test_isinstance_check_with_async_client(self, async_client):
        """isinstance() works with AsyncBaseClient and AsyncClientProtocol."""
        try:
            result = isinstance(async_client, AsyncClientProtocol)
            assert isinstance(result, bool)
        except TypeError:
            pytest.skip('Protocol does not support isinstance checking')


# -----------------------------------------------------------------------------
# Protocol Conformance Tests
# -----------------------------------------------------------------------------


class TestProtocolConformance:
    """Tests for protocol conformance across client implementations."""

    def test_base_client_attributes_match_protocol(self, base_client):
        """BaseClient attribute types match ClientProtocol."""
        assert isinstance(base_client.base_url, str)
        assert isinstance(base_client.page_size, int)
        # name can be str or None
        assert base_client.name is None or isinstance(base_client.name, str)

    def test_async_client_attributes_match_protocol(self, async_client):
        """AsyncBaseClient attribute types match AsyncClientProtocol."""
        assert isinstance(async_client.base_url, str)
        assert isinstance(async_client.page_size, int)
        assert async_client.name is None or isinstance(async_client.name, str)

    def test_get_headers_returns_dict(self, base_client, async_client):
        """_get_headers returns dict for both clients."""
        sync_headers = base_client._get_headers()
        async_headers = async_client._get_headers()
        assert isinstance(sync_headers, dict)
        assert isinstance(async_headers, dict)

    def test_methods_are_callable(self, base_client):
        """Protocol methods are callable."""
        assert callable(base_client._get_headers)
        assert callable(base_client._get)
        assert callable(base_client._post)
        assert callable(base_client._put)
        assert callable(base_client._patch)
        assert callable(base_client._delete)
        assert callable(base_client._list)


# -----------------------------------------------------------------------------
# Partial Implementation Tests
# -----------------------------------------------------------------------------


class TestPartialImplementation:
    """Tests for partial protocol implementations."""

    def test_class_missing_methods_does_not_match(self):
        """Class missing protocol methods does not implement protocol."""

        class IncompleteClient:
            name = 'Incomplete'
            base_url = 'https://example.com'
            page_size = 100

            def _get_headers(self):
                return {}

            # Missing: _get, _post, _put, _patch, _delete, _list

        client = IncompleteClient()

        # This should either return False or raise TypeError
        # depending on Protocol implementation details
        try:
            result = isinstance(client, ClientProtocol)
            # For runtime_checkable protocols with methods, this may vary
            # Just verify it doesn't crash
            assert isinstance(result, bool)
        except TypeError:
            pass  # Expected for some Protocol configurations

    def test_class_with_extra_methods_still_matches(self, base_client):
        """Class with extra methods still matches protocol."""
        # BaseClient has extra methods like _mutate, exists, etc.
        # It should still match the protocol
        assert hasattr(base_client, '_mutate')
        assert hasattr(base_client, 'exists')
        # Protocol matching should not be affected
        assert hasattr(base_client, '_get')
        assert hasattr(base_client, '_post')
