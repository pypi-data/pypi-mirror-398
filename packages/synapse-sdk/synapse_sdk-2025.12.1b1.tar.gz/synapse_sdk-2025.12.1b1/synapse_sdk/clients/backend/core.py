"""Core backend client mixin with chunked upload support."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.clients.backend.models import (
    ChunkedUploadFinalizeResponse,
    ChunkedUploadResponse,
)
from synapse_sdk.utils.file.io import DEFAULT_CHUNK_SIZE, read_file_in_chunks

if TYPE_CHECKING:
    from collections.abc import Callable

    from synapse_sdk.clients.protocols import ClientProtocol


class CoreClientMixin:
    """Mixin providing chunked upload functionality.

    Supports resumable uploads with MD5 integrity verification.
    Files are uploaded in 50MB chunks by default.
    """

    def create_chunked_upload(
        self: ClientProtocol,
        file_path: str | Path,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Upload a file in chunks with MD5 integrity verification.

        Files are uploaded in configurable chunks (default 50MB) with
        Content-Range headers for resumable uploads. MD5 hash is calculated
        incrementally during upload and verified on finalization.

        Args:
            file_path: Path to the file to upload.
            chunk_size: Size of each chunk in bytes (default 50MB).
            on_progress: Optional callback(bytes_uploaded, total_bytes) for progress.

        Returns:
            Finalized upload response with file ID and checksum.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ClientError: If upload fails.

        Example:
            >>> def progress(uploaded, total):
            ...     print(f'{uploaded}/{total} bytes')
            >>> result = client.create_chunked_upload('/path/to/file.zip', on_progress=progress)
            >>> result['id']
            123
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f'File not found: {path}')

        total_size = os.path.getsize(path)
        hash_md5 = hashlib.md5()

        # Initial upload URL
        url = 'chunked_upload/'
        offset = 0

        # Upload each chunk
        for chunk in read_file_in_chunks(path, chunk_size):
            hash_md5.update(chunk)

            response = self._put(
                url,
                data={'filename': path.name},
                files={'file': ('chunk', chunk)},
                headers={'Content-Range': f'bytes {offset}-{offset + len(chunk) - 1}/{total_size}'},
            )

            # Validate response
            chunk_response = ChunkedUploadResponse.model_validate(response)
            offset = chunk_response.offset
            url = chunk_response.url

            # Progress callback
            if on_progress:
                on_progress(offset, total_size)

        # Finalize with MD5 checksum
        result = self._post(url, data={'md5': hash_md5.hexdigest()})

        # Validate final response
        ChunkedUploadFinalizeResponse.model_validate(result)

        return result


__all__ = ['CoreClientMixin']
