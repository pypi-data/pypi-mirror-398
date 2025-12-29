"""Google Cloud Storage provider."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.utils.storage.config import GCSStorageConfig
from synapse_sdk.utils.storage.errors import (
    StorageConnectionError,
    StorageNotFoundError,
    StorageUploadError,
)
from synapse_sdk.utils.storage.providers.base import _BaseStorageMixin

if TYPE_CHECKING:
    from upath import UPath


class GCSStorage(_BaseStorageMixin):
    """Storage provider for Google Cloud Storage.

    Requires: universal-pathlib[gcs] (pip install universal-pathlib[gcs])

    Args:
        config: Configuration dict with GCS credentials.

    Example:
        >>> storage = GCSStorage({
        ...     'bucket_name': 'my-bucket',
        ...     'credentials': '/path/to/service-account.json',
        ... })
        >>> storage.upload(Path('/tmp/file.txt'), 'data/file.txt')
        'gs://my-bucket/data/file.txt'
    """

    def __init__(self, config: dict[str, Any]):
        try:
            from upath import UPath
        except ImportError as e:
            raise ImportError(
                'GCSStorage requires universal-pathlib[gcs]. Install with: pip install universal-pathlib[gcs]'
            ) from e

        validated = GCSStorageConfig.model_validate(config)

        self._bucket_name = validated.bucket_name
        upath_kwargs: dict[str, Any] = {'token': validated.credentials}
        if validated.project:
            upath_kwargs['project'] = validated.project

        try:
            self._upath = UPath(
                f'gs://{validated.bucket_name}',
                **upath_kwargs,
            )
        except Exception as e:
            raise StorageConnectionError(
                f'Failed to connect to GCS: {e}',
                details={'bucket': validated.bucket_name},
            ) from e

    def upload(self, source: Path, target: str) -> str:
        """Upload a file to GCS.

        Args:
            source: Local file path to upload.
            target: Target path in GCS bucket.

        Returns:
            gs:// URL of uploaded file.
        """
        source_path = Path(source) if isinstance(source, str) else source

        if not source_path.exists():
            raise StorageNotFoundError(
                f'Source file not found: {source_path}',
                details={'source': str(source_path)},
            )

        target_path = self._normalize_path(target)

        try:
            with open(source_path, 'rb') as f:
                (self._upath / target_path).write_bytes(f.read())
        except Exception as e:
            raise StorageUploadError(
                f'Failed to upload to GCS: {e}',
                details={'source': str(source_path), 'target': target_path},
            ) from e

        return self.get_url(target)

    def exists(self, target: str) -> bool:
        """Check if file exists in GCS.

        Args:
            target: Path to check.

        Returns:
            True if exists, False otherwise.
        """
        target_path = self._normalize_path(target)
        return (self._upath / target_path).exists()

    def get_url(self, target: str) -> str:
        """Get gs:// URL for target.

        Args:
            target: Target path.

        Returns:
            gs:// URL string.
        """
        target_path = self._normalize_path(target)
        if target_path:
            return f'gs://{self._bucket_name}/{target_path}'
        return f'gs://{self._bucket_name}'

    def get_pathlib(self, path: str) -> UPath:
        """Get UPath object for path.

        Args:
            path: Path relative to bucket root.

        Returns:
            UPath object.
        """
        normalized = self._normalize_path(path)
        if not normalized:
            return self._upath
        return self._upath / normalized

    def get_path_file_count(self, pathlib_obj: UPath) -> int:
        """Count files in GCS path.

        Args:
            pathlib_obj: UPath object from get_pathlib().

        Returns:
            Number of files.
        """
        return self._count_files(pathlib_obj)

    def get_path_total_size(self, pathlib_obj: UPath) -> int:
        """Calculate total size of files in GCS path.

        Args:
            pathlib_obj: UPath object from get_pathlib().

        Returns:
            Total size in bytes.
        """
        return self._calculate_total_size(pathlib_obj)

    def glob(self, pattern: str) -> list[UPath]:
        """Glob pattern matching in GCS.

        Args:
            pattern: Glob pattern.

        Returns:
            List of matching UPath objects.
        """
        return list(self._upath.glob(pattern))


__all__ = ['GCSStorage']
