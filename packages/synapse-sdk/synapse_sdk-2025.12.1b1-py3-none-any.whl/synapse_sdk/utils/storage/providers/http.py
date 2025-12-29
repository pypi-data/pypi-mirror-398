"""HTTP storage provider."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests

from synapse_sdk.utils.storage.config import HTTPStorageConfig
from synapse_sdk.utils.storage.errors import (
    StorageError,
    StorageNotFoundError,
    StorageUploadError,
)


class HTTPStorage:
    """Storage provider for HTTP file servers.

    Note: This provider has limited functionality as HTTP servers typically
    don't support directory listing. File counting and size calculation
    are not supported.

    Args:
        config: Configuration dict with HTTP server details.

    Example:
        >>> storage = HTTPStorage({
        ...     'base_url': 'https://files.example.com/uploads/',
        ...     'timeout': 60,
        ... })
        >>> storage.exists('data/file.txt')
        True
    """

    def __init__(self, config: dict[str, Any]):
        validated = HTTPStorageConfig.model_validate(config)

        self._base_url = validated.base_url
        self._timeout = validated.timeout
        self._headers = validated.headers

        # Setup session for connection pooling
        self._session = requests.Session()
        if self._headers:
            self._session.headers.update(self._headers)

    def _get_full_url(self, path: str) -> str:
        """Get full URL for a path."""
        if path.startswith('/'):
            path = path[1:]
        return urljoin(self._base_url, path)

    def upload(self, source: Path, target: str) -> str:
        """Upload a file to HTTP server.

        Note: Requires server to support PUT or POST for file uploads.

        Args:
            source: Local file path to upload.
            target: Target path on server.

        Returns:
            URL of uploaded file.
        """
        source_path = Path(source) if isinstance(source, str) else source

        if not source_path.exists():
            raise StorageNotFoundError(
                f'Source file not found: {source_path}',
                details={'source': str(source_path)},
            )

        url = self._get_full_url(target)

        try:
            with open(source_path, 'rb') as f:
                files = {'file': (os.path.basename(str(source_path)), f)}

                # Try PUT first, fallback to POST
                response = self._session.put(url, files=files, timeout=self._timeout)

                if response.status_code == 405:
                    f.seek(0)
                    response = self._session.post(url, files=files, timeout=self._timeout)

                response.raise_for_status()
        except requests.RequestException as e:
            raise StorageUploadError(
                f'Failed to upload to HTTP server: {e}',
                details={'url': url},
            ) from e

        return url

    def exists(self, target: str) -> bool:
        """Check if file exists on HTTP server.

        Uses HEAD request to check existence.

        Args:
            target: Path to check.

        Returns:
            True if file exists (HTTP 200), False otherwise.
        """
        url = self._get_full_url(target)

        try:
            response = self._session.head(url, timeout=self._timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_url(self, target: str) -> str:
        """Get full URL for target.

        Args:
            target: Target path.

        Returns:
            Full HTTP URL.
        """
        return self._get_full_url(target)

    def get_pathlib(self, path: str) -> HTTPPath:
        """Get HTTPPath object for path.

        Args:
            path: Path on server.

        Returns:
            HTTPPath object (pathlib-like interface).
        """
        return HTTPPath(self, path)

    def get_path_file_count(self, pathlib_obj: HTTPPath) -> int:
        """Not supported for HTTP storage.

        Raises:
            StorageError: Always, as HTTP servers don't support directory listing.
        """
        raise StorageError(
            'File counting not supported for HTTP storage',
            details={'reason': 'HTTP servers do not provide directory listing'},
        )

    def get_path_total_size(self, pathlib_obj: HTTPPath) -> int:
        """Not supported for HTTP storage.

        Raises:
            StorageError: Always, as HTTP servers don't support directory listing.
        """
        raise StorageError(
            'Size calculation not supported for HTTP storage',
            details={'reason': 'HTTP servers do not provide directory listing'},
        )


class HTTPPath:
    """Pathlib-like interface for HTTP paths.

    Provides a subset of pathlib.Path functionality for HTTP resources.
    """

    def __init__(self, storage: HTTPStorage, path: str):
        self._storage = storage
        self._path = path.strip('/')

    def __str__(self) -> str:
        return self._storage.get_url(self._path)

    def __repr__(self) -> str:
        return f"HTTPPath('{self}')"

    def __truediv__(self, other: str) -> HTTPPath:
        """Join paths using / operator."""
        new_path = f'{self._path}/{other}' if self._path else str(other)
        return HTTPPath(self._storage, new_path)

    def joinuri(self, *parts: str) -> HTTPPath:
        """Join path parts."""
        all_parts = [self._path] + [str(p).strip('/') for p in parts]
        new_path = '/'.join(p for p in all_parts if p)
        return HTTPPath(self._storage, new_path)

    @property
    def name(self) -> str:
        """Get the final component of the path."""
        return os.path.basename(self._path)

    @property
    def parent(self) -> HTTPPath:
        """Get the parent directory."""
        parent_path = os.path.dirname(self._path)
        return HTTPPath(self._storage, parent_path)

    def exists(self) -> bool:
        """Check if this path exists."""
        return self._storage.exists(self._path)

    def is_file(self) -> bool:
        """Check if this path is a file (assumes exists = is_file for HTTP)."""
        return self.exists()

    def is_dir(self) -> bool:
        """Check if this path is a directory.

        Note: HTTP servers don't typically distinguish directories.
        This always returns False.
        """
        return False

    def read_bytes(self) -> bytes:
        """Read file contents as bytes."""
        url = self._storage.get_url(self._path)
        response = self._storage._session.get(url, timeout=self._storage._timeout)
        response.raise_for_status()
        return response.content

    def read_text(self, encoding: str = 'utf-8') -> str:
        """Read file contents as text."""
        return self.read_bytes().decode(encoding)

    def stat(self) -> HTTPStat:
        """Get file statistics.

        Note: Only st_size is populated via Content-Length header.
        """
        url = self._storage.get_url(self._path)
        response = self._storage._session.head(url, timeout=self._storage._timeout)
        response.raise_for_status()

        content_length = response.headers.get('Content-Length')
        size = int(content_length) if content_length else 0

        return HTTPStat(st_size=size)


class HTTPStat:
    """Minimal stat result for HTTP files."""

    def __init__(self, st_size: int = 0):
        self.st_size = st_size


__all__ = ['HTTPStorage', 'HTTPPath']
