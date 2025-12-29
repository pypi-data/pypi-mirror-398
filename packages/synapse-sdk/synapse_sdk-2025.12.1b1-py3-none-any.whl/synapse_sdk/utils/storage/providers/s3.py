"""S3-compatible storage provider (AWS S3, MinIO)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.utils.storage.config import S3StorageConfig
from synapse_sdk.utils.storage.errors import (
    StorageConnectionError,
    StorageNotFoundError,
    StorageUploadError,
)
from synapse_sdk.utils.storage.providers.base import _BaseStorageMixin

if TYPE_CHECKING:
    from upath import UPath


class S3Storage(_BaseStorageMixin):
    """Storage provider for S3-compatible services (AWS S3, MinIO).

    Requires: universal-pathlib[s3] (pip install universal-pathlib[s3])

    Args:
        config: Configuration dict with S3 credentials.

    Example:
        >>> storage = S3Storage({
        ...     'bucket_name': 'my-bucket',
        ...     'access_key': 'AKIAIOSFODNN7EXAMPLE',
        ...     'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        ...     'region_name': 'us-east-1',
        ... })
        >>> storage.upload(Path('/tmp/file.txt'), 'data/file.txt')
        's3://my-bucket/data/file.txt'
    """

    DEFAULT_REGION = 'us-east-1'

    def __init__(self, config: dict[str, Any]):
        try:
            from upath import UPath
        except ImportError as e:
            raise ImportError(
                'S3Storage requires universal-pathlib[s3]. Install with: pip install universal-pathlib[s3]'
            ) from e

        validated = S3StorageConfig.model_validate(config)

        self._bucket_name = validated.bucket_name
        client_kwargs: dict[str, Any] = {
            'region_name': validated.region_name or self.DEFAULT_REGION,
        }

        if validated.endpoint_url:
            client_kwargs['endpoint_url'] = validated.endpoint_url

        try:
            self._upath = UPath(
                f's3://{validated.bucket_name}',
                key=validated.access_key,
                secret=validated.secret_key,
                client_kwargs=client_kwargs,
            )
        except Exception as e:
            raise StorageConnectionError(
                f'Failed to connect to S3: {e}',
                details={'bucket': validated.bucket_name},
            ) from e

    def upload(self, source: Path, target: str) -> str:
        """Upload a file to S3.

        Args:
            source: Local file path to upload.
            target: Target path in S3 bucket.

        Returns:
            s3:// URL of uploaded file.
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
                f'Failed to upload to S3: {e}',
                details={'source': str(source_path), 'target': target_path},
            ) from e

        return self.get_url(target)

    def exists(self, target: str) -> bool:
        """Check if file exists in S3.

        Args:
            target: Path to check.

        Returns:
            True if exists, False otherwise.
        """
        target_path = self._normalize_path(target)
        return (self._upath / target_path).exists()

    def get_url(self, target: str) -> str:
        """Get s3:// URL for target.

        Args:
            target: Target path.

        Returns:
            s3:// URL string.
        """
        target_path = self._normalize_path(target)
        if target_path:
            return f's3://{self._bucket_name}/{target_path}'
        return f's3://{self._bucket_name}'

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
        """Count files in S3 path.

        Args:
            pathlib_obj: UPath object from get_pathlib().

        Returns:
            Number of files.
        """
        return self._count_files(pathlib_obj)

    def get_path_total_size(self, pathlib_obj: UPath) -> int:
        """Calculate total size of files in S3 path.

        Args:
            pathlib_obj: UPath object from get_pathlib().

        Returns:
            Total size in bytes.
        """
        return self._calculate_total_size(pathlib_obj)

    def glob(self, pattern: str) -> list[UPath]:
        """Glob pattern matching in S3.

        Args:
            pattern: Glob pattern.

        Returns:
            List of matching UPath objects.
        """
        return list(self._upath.glob(pattern))


__all__ = ['S3Storage']
