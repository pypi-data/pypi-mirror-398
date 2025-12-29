"""SFTP storage provider."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.utils.storage.config import SFTPStorageConfig
from synapse_sdk.utils.storage.errors import (
    StorageConnectionError,
    StorageNotFoundError,
    StorageUploadError,
)
from synapse_sdk.utils.storage.providers.base import _BaseStorageMixin

if TYPE_CHECKING:
    from upath import UPath


class SFTPStorage(_BaseStorageMixin):
    """Storage provider for SFTP servers.

    Requires: universal-pathlib[sftp] (pip install universal-pathlib[sftp])

    Supports both password and private key authentication.

    Args:
        config: Configuration dict with SFTP credentials.

    Example:
        >>> # Password authentication
        >>> storage = SFTPStorage({
        ...     'host': 'sftp.example.com',
        ...     'username': 'user',
        ...     'password': 'secret',
        ...     'root_path': '/data',
        ... })
        >>>
        >>> # Private key authentication
        >>> storage = SFTPStorage({
        ...     'host': 'sftp.example.com',
        ...     'username': 'user',
        ...     'private_key': '/path/to/id_rsa',
        ...     'root_path': '/data',
        ... })
    """

    def __init__(self, config: dict[str, Any]):
        try:
            from upath import UPath
        except ImportError as e:
            raise ImportError(
                'SFTPStorage requires universal-pathlib[sftp]. Install with: pip install universal-pathlib[sftp]'
            ) from e

        validated = SFTPStorageConfig.model_validate(config)
        self._config = validated

        # Build UPath kwargs based on auth method
        upath_kwargs: dict[str, Any] = {
            'username': validated.username,
        }

        if validated.password:
            upath_kwargs['password'] = validated.password

        if validated.private_key:
            upath_kwargs['key_filename'] = validated.private_key
            if validated.private_key_passphrase:
                upath_kwargs['passphrase'] = validated.private_key_passphrase

        # Construct base URL with port if non-default
        if validated.port != 22:
            base_url = f'sftp://{validated.host}:{validated.port}'
        else:
            base_url = f'sftp://{validated.host}'

        try:
            self._base_upath = UPath(base_url, **upath_kwargs)
            self._root_path = validated.root_path.rstrip('/')
            self._host = validated.host
            self._port = validated.port
        except Exception as e:
            raise StorageConnectionError(
                f'Failed to connect to SFTP: {e}',
                details={'host': validated.host, 'port': validated.port},
            ) from e

    def _get_full_path(self, path: str) -> UPath:
        """Get full UPath including root_path."""
        normalized = self._normalize_path(path)
        if self._root_path:
            full_path = f'{self._root_path}/{normalized}' if normalized else self._root_path
        else:
            full_path = normalized or '/'
        return self._base_upath / full_path.lstrip('/')

    def upload(self, source: Path, target: str) -> str:
        """Upload a file via SFTP.

        Args:
            source: Local file path to upload.
            target: Target path on SFTP server.

        Returns:
            sftp:// URL of uploaded file.
        """
        source_path = Path(source) if isinstance(source, str) else source

        if not source_path.exists():
            raise StorageNotFoundError(
                f'Source file not found: {source_path}',
                details={'source': str(source_path)},
            )

        target_upath = self._get_full_path(target)

        try:
            # Ensure parent directory exists
            target_upath.parent.mkdir(parents=True, exist_ok=True)

            with open(source_path, 'rb') as f:
                target_upath.write_bytes(f.read())
        except Exception as e:
            raise StorageUploadError(
                f'Failed to upload via SFTP: {e}',
                details={'source': str(source_path), 'target': str(target_upath)},
            ) from e

        return self.get_url(target)

    def exists(self, target: str) -> bool:
        """Check if file exists on SFTP server.

        Args:
            target: Path to check.

        Returns:
            True if exists, False otherwise.
        """
        return self._get_full_path(target).exists()

    def get_url(self, target: str) -> str:
        """Get sftp:// URL for target.

        Args:
            target: Target path.

        Returns:
            sftp:// URL string.
        """
        normalized = self._normalize_path(target)
        if self._root_path:
            full_path = f'{self._root_path}/{normalized}' if normalized else self._root_path
        else:
            full_path = normalized or '/'

        if self._port != 22:
            return f'sftp://{self._host}:{self._port}{full_path}'
        return f'sftp://{self._host}{full_path}'

    def get_pathlib(self, path: str) -> UPath:
        """Get UPath object for path.

        Args:
            path: Path relative to root_path.

        Returns:
            UPath object.
        """
        return self._get_full_path(path)

    def get_path_file_count(self, pathlib_obj: UPath) -> int:
        """Count files in SFTP path.

        Args:
            pathlib_obj: UPath object from get_pathlib().

        Returns:
            Number of files.
        """
        return self._count_files(pathlib_obj)

    def get_path_total_size(self, pathlib_obj: UPath) -> int:
        """Calculate total size of files in SFTP path.

        Args:
            pathlib_obj: UPath object from get_pathlib().

        Returns:
            Total size in bytes.
        """
        return self._calculate_total_size(pathlib_obj)

    def glob(self, pattern: str) -> list[UPath]:
        """Glob pattern matching on SFTP.

        Args:
            pattern: Glob pattern.

        Returns:
            List of matching UPath objects.
        """
        base = self._get_full_path('')
        return list(base.glob(pattern))


__all__ = ['SFTPStorage']
