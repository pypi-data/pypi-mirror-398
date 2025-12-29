"""Local filesystem storage provider."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from synapse_sdk.utils.storage.config import LocalStorageConfig
from synapse_sdk.utils.storage.errors import StorageNotFoundError, StorageUploadError
from synapse_sdk.utils.storage.providers.base import _BaseStorageMixin


class LocalStorage(_BaseStorageMixin):
    """Storage provider for local filesystem.

    Args:
        config: Configuration dict with 'location' key.

    Example:
        >>> storage = LocalStorage({'location': '/data'})
        >>> storage.upload(Path('/tmp/file.txt'), 'uploads/file.txt')
        'file:///data/uploads/file.txt'
    """

    def __init__(self, config: dict[str, Any]):
        validated = LocalStorageConfig.model_validate(config)
        self.base_path = Path(validated.location)

    def upload(self, source: Path, target: str) -> str:
        """Upload a file from source to target location.

        Args:
            source: Path to source file.
            target: Target path relative to base path.

        Returns:
            file:// URL of uploaded file.

        Raises:
            StorageNotFoundError: If source file doesn't exist.
            StorageUploadError: If copy operation fails.
        """
        source_path = Path(source) if isinstance(source, str) else source

        if not source_path.exists():
            raise StorageNotFoundError(
                f'Source file not found: {source_path}',
                details={'source': str(source_path)},
            )

        target_path = self.base_path / self._normalize_path(target)

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
        except OSError as e:
            raise StorageUploadError(
                f'Failed to upload file: {e}',
                details={'source': str(source_path), 'target': str(target_path)},
            ) from e

        return self.get_url(target)

    def exists(self, target: str) -> bool:
        """Check if target file exists.

        Args:
            target: Target path relative to base path.

        Returns:
            True if file exists, False otherwise.
        """
        target_path = self.base_path / self._normalize_path(target)
        return target_path.exists()

    def get_url(self, target: str) -> str:
        """Get file:// URL for target file.

        Args:
            target: Target path relative to base path.

        Returns:
            file:// URL string.
        """
        target_path = self.base_path / self._normalize_path(target)
        return f'file://{target_path.absolute()}'

    def get_pathlib(self, path: str) -> Path:
        """Get pathlib.Path object for the path.

        Args:
            path: Path relative to storage root.

        Returns:
            pathlib.Path object.
        """
        normalized = self._normalize_path(path)
        if not normalized:
            return self.base_path
        return self.base_path / normalized

    def get_path_file_count(self, pathlib_obj: Path) -> int:
        """Get file count in the path.

        Args:
            pathlib_obj: Path object from get_pathlib().

        Returns:
            Number of files.
        """
        return self._count_files(pathlib_obj)

    def get_path_total_size(self, pathlib_obj: Path) -> int:
        """Get total size of files in the path.

        Args:
            pathlib_obj: Path object from get_pathlib().

        Returns:
            Total size in bytes.
        """
        return self._calculate_total_size(pathlib_obj)


__all__ = ['LocalStorage']
