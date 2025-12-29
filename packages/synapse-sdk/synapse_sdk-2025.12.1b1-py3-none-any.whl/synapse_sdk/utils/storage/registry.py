"""Storage provider registry with lazy loading."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from synapse_sdk.utils.storage.errors import StorageProviderNotFoundError

if TYPE_CHECKING:
    from synapse_sdk.utils.storage import StorageProtocol

# Registry stores factory functions for lazy loading
_PROVIDER_REGISTRY: dict[str, Callable[[], type[StorageProtocol]]] = {}


def _register_builtin_providers() -> None:
    """Register built-in storage providers with lazy loading."""

    def local_factory() -> type:
        from synapse_sdk.utils.storage.providers.local import LocalStorage

        return LocalStorage

    def s3_factory() -> type:
        from synapse_sdk.utils.storage.providers.s3 import S3Storage

        return S3Storage

    def gcs_factory() -> type:
        from synapse_sdk.utils.storage.providers.gcs import GCSStorage

        return GCSStorage

    def sftp_factory() -> type:
        from synapse_sdk.utils.storage.providers.sftp import SFTPStorage

        return SFTPStorage

    def http_factory() -> type:
        from synapse_sdk.utils.storage.providers.http import HTTPStorage

        return HTTPStorage

    # Local filesystem
    _PROVIDER_REGISTRY['local'] = local_factory
    _PROVIDER_REGISTRY['file_system'] = local_factory  # backward compatibility

    # S3-compatible
    _PROVIDER_REGISTRY['s3'] = s3_factory
    _PROVIDER_REGISTRY['amazon_s3'] = s3_factory
    _PROVIDER_REGISTRY['minio'] = s3_factory

    # Google Cloud Storage
    _PROVIDER_REGISTRY['gcs'] = gcs_factory
    _PROVIDER_REGISTRY['gs'] = gcs_factory
    _PROVIDER_REGISTRY['gcp'] = gcs_factory

    # SFTP
    _PROVIDER_REGISTRY['sftp'] = sftp_factory

    # HTTP
    _PROVIDER_REGISTRY['http'] = http_factory
    _PROVIDER_REGISTRY['https'] = http_factory


def get_provider_class(provider: str) -> type[StorageProtocol]:
    """Get the storage provider class for the given provider name.

    Args:
        provider: Provider name (e.g., 's3', 'gcs', 'local').

    Returns:
        Storage provider class.

    Raises:
        StorageProviderNotFoundError: If provider is not registered.
    """
    if not _PROVIDER_REGISTRY:
        _register_builtin_providers()

    factory = _PROVIDER_REGISTRY.get(provider)
    if not factory:
        available = ', '.join(sorted(_PROVIDER_REGISTRY.keys()))
        raise StorageProviderNotFoundError(
            f"Provider '{provider}' not found. Available: {available}",
            details={'provider': provider, 'available': list(_PROVIDER_REGISTRY.keys())},
        )

    return factory()


def register_provider(name: str, factory: Callable[[], type[StorageProtocol]]) -> None:
    """Register a custom storage provider.

    Args:
        name: Provider name to register.
        factory: Factory function that returns the provider class.

    Example:
        >>> def custom_factory():
        ...     from my_module import CustomStorage
        ...     return CustomStorage
        >>> register_provider('custom', custom_factory)
    """
    if not _PROVIDER_REGISTRY:
        _register_builtin_providers()
    _PROVIDER_REGISTRY[name] = factory


def get_registered_providers() -> list[str]:
    """Get list of registered provider names.

    Returns:
        List of registered provider names.
    """
    if not _PROVIDER_REGISTRY:
        _register_builtin_providers()
    return list(_PROVIDER_REGISTRY.keys())


__all__ = [
    'get_provider_class',
    'register_provider',
    'get_registered_providers',
]
