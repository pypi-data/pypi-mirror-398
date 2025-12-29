"""Storage utilities module.

This module provides a unified interface for working with different storage
backends including local filesystem, S3, GCS, SFTP, and HTTP.

Example:
    >>> from synapse_sdk.utils.storage import get_storage, get_pathlib
    >>>
    >>> # Local filesystem
    >>> storage = get_storage({
    ...     'provider': 'local',
    ...     'configuration': {'location': '/data'}
    ... })
    >>>
    >>> # S3-compatible storage
    >>> storage = get_storage({
    ...     'provider': 's3',
    ...     'configuration': {
    ...         'bucket_name': 'my-bucket',
    ...         'access_key': 'AKIAIOSFODNN7EXAMPLE',
    ...         'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    ...     }
    ... })
    >>>
    >>> # Get pathlib object for path operations
    >>> path = get_pathlib(storage_config, '/uploads')
    >>> for file in path.rglob('*'):
    ...     print(file)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from upath import UPath


@runtime_checkable
class StorageProtocol(Protocol):
    """Protocol defining the storage provider interface.

    All storage providers must implement these methods to be compatible
    with the storage system. Uses structural typing (duck typing) rather
    than inheritance, allowing third-party implementations.

    Example:
        >>> class CustomStorage:
        ...     def upload(self, source: Path, target: str) -> str: ...
        ...     def exists(self, target: str) -> bool: ...
        ...     def get_url(self, target: str) -> str: ...
        ...     def get_pathlib(self, path: str) -> Path: ...
        ...     def get_path_file_count(self, pathlib_obj: Path) -> int: ...
        ...     def get_path_total_size(self, pathlib_obj: Path) -> int: ...
        >>>
        >>> isinstance(CustomStorage(), StorageProtocol)  # True
    """

    def upload(self, source: Path, target: str) -> str:
        """Upload a file from local source to target path.

        Args:
            source: Local file path to upload.
            target: Target path in storage (relative to storage root).

        Returns:
            URL or identifier of the uploaded file.

        Raises:
            StorageNotFoundError: If source file doesn't exist.
            StorageUploadError: If upload fails.
        """
        ...

    def exists(self, target: str) -> bool:
        """Check if a file or directory exists at target path.

        Args:
            target: Path to check (relative to storage root).

        Returns:
            True if path exists, False otherwise.
        """
        ...

    def get_url(self, target: str) -> str:
        """Get the URL for accessing a file.

        Args:
            target: Path to file (relative to storage root).

        Returns:
            URL string for accessing the file.
        """
        ...

    def get_pathlib(self, path: str) -> Path | UPath:
        """Get a pathlib-compatible object for the path.

        Args:
            path: Path relative to storage root.

        Returns:
            Path object (local) or UPath object (cloud/remote).
        """
        ...

    def get_path_file_count(self, pathlib_obj: Path | UPath) -> int:
        """Count files recursively in the given path.

        Args:
            pathlib_obj: Path object from get_pathlib().

        Returns:
            Number of files (excluding directories).
        """
        ...

    def get_path_total_size(self, pathlib_obj: Path | UPath) -> int:
        """Calculate total size of files recursively.

        Args:
            pathlib_obj: Path object from get_pathlib().

        Returns:
            Total size in bytes.
        """
        ...


def get_storage(connection_param: dict[str, Any]) -> StorageProtocol:
    """Get a storage provider instance from configuration.

    Args:
        connection_param: Dictionary with 'provider' and 'configuration' keys.
            Example: {'provider': 's3', 'configuration': {'bucket_name': '...'}}

    Returns:
        Storage provider instance implementing StorageProtocol.

    Raises:
        StorageConfigError: If configuration is invalid.
        StorageProviderNotFoundError: If provider is not registered.

    Example:
        >>> config = {
        ...     'provider': 's3',
        ...     'configuration': {
        ...         'bucket_name': 'my-bucket',
        ...         'access_key': 'AKIAIOSFODNN7EXAMPLE',
        ...         'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        ...     }
        ... }
        >>> storage = get_storage(config)
    """
    from synapse_sdk.utils.storage.config import StorageConfig
    from synapse_sdk.utils.storage.registry import get_provider_class

    # Validate configuration with Pydantic
    storage_config = StorageConfig.model_validate(connection_param)

    # Get provider class and instantiate
    provider_cls = get_provider_class(storage_config.provider)
    return provider_cls(storage_config.configuration)


def get_pathlib(storage_config: dict[str, Any], path_root: str) -> Path | UPath:
    """Get pathlib object for a path in storage.

    Convenience function that combines get_storage() and get_pathlib().

    Args:
        storage_config: Storage configuration dict.
        path_root: Root path to get pathlib for.

    Returns:
        Path or UPath object.

    Example:
        >>> config = {'provider': 'local', 'configuration': {'location': '/data'}}
        >>> path = get_pathlib(config, '/uploads')
        >>> path.exists()
        True
    """
    storage = get_storage(storage_config)
    return storage.get_pathlib(path_root)


def get_path_file_count(storage_config: dict[str, Any], path_root: str) -> int:
    """Get file count in a storage path.

    Args:
        storage_config: Storage configuration dict.
        path_root: Root path to count files in.

    Returns:
        Number of files.

    Example:
        >>> config = {'provider': 'local', 'configuration': {'location': '/data'}}
        >>> count = get_path_file_count(config, '/uploads')
        >>> print(f'Found {count} files')
    """
    storage = get_storage(storage_config)
    pathlib_obj = storage.get_pathlib(path_root)
    return storage.get_path_file_count(pathlib_obj)


def get_path_total_size(storage_config: dict[str, Any], path_root: str) -> int:
    """Get total size of files in a storage path.

    Args:
        storage_config: Storage configuration dict.
        path_root: Root path to calculate size for.

    Returns:
        Total size in bytes.

    Example:
        >>> config = {'provider': 'local', 'configuration': {'location': '/data'}}
        >>> size = get_path_total_size(config, '/uploads')
        >>> print(f'Total size: {size / 1024 / 1024:.2f} MB')
    """
    storage = get_storage(storage_config)
    pathlib_obj = storage.get_pathlib(path_root)
    return storage.get_path_total_size(pathlib_obj)


__all__ = [
    # Protocol
    'StorageProtocol',
    # Public API functions
    'get_storage',
    'get_pathlib',
    'get_path_file_count',
    'get_path_total_size',
]
