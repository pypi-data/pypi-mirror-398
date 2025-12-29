"""Data collection client mixin for dataset management."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.clients.backend.models import DataFileResponse, DataUnitCreateRequest

if TYPE_CHECKING:
    from collections.abc import Callable

    from synapse_sdk.clients.protocols import ClientProtocol


# Auto-use chunked upload for files larger than 50MB
CHUNKED_UPLOAD_THRESHOLD = 1024 * 1024 * 50


def _batch_list(items: list, batch_size: int) -> list[list]:
    """Split a list into batches of specified size."""
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


class DataCollectionClientMixin:
    """Mixin for data collection API endpoints.

    Provides methods for managing data collections, files, and units.
    """

    def list_data_collections(self: ClientProtocol) -> dict[str, Any]:
        """List all data collections.

        Returns:
            Paginated list of data collections.
        """
        return self._get('data_collections/')

    def get_data_collection(
        self: ClientProtocol,
        collection_id: int,
    ) -> dict[str, Any]:
        """Get data collection details by ID.

        Automatically expands file specifications.

        Args:
            collection_id: Data collection ID.

        Returns:
            Collection data including file specifications.
        """
        return self._get(
            f'data_collections/{collection_id}/',
            params={'expand': 'file_specifications'},
        )

    def create_data_file(
        self: ClientProtocol,
        file_path: str | Path,
        *,
        use_chunked_upload: bool | None = None,
    ) -> dict[str, Any]:
        """Upload a data file.

        Automatically uses chunked upload for files >50MB unless
        explicitly specified.

        Args:
            file_path: Path to the file to upload.
            use_chunked_upload: Force chunked (True) or direct (False) upload.
                None = auto-detect based on file size.

        Returns:
            File data with ID, checksum, and size.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f'File not found: {path}')

        # Auto-detect upload method based on file size
        if use_chunked_upload is None:
            use_chunked_upload = path.stat().st_size > CHUNKED_UPLOAD_THRESHOLD

        if use_chunked_upload:
            upload_result = self.create_chunked_upload(path)
            response = self._post(
                'data_files/',
                data={'chunked_upload': upload_result['id']},
            )
        else:
            response = self._post('data_files/', files={'file': path})

        DataFileResponse.model_validate(response)
        return response

    def get_data_unit(
        self: ClientProtocol,
        unit_id: int,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get data unit details by ID.

        Args:
            unit_id: Data unit ID.
            params: Optional query parameters.

        Returns:
            Data unit with files and metadata.
        """
        return self._get(f'data_units/{unit_id}/', params=params)

    def create_data_units(
        self: ClientProtocol,
        data: dict[str, Any] | list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create data unit bindings.

        Links uploaded files to a data collection.

        Args:
            data: Data unit(s) to create.

        Returns:
            Created data unit(s).
        """
        return self._post(
            'data_units/',
            request_model=DataUnitCreateRequest,
            data=data,
        )

    def list_data_units(
        self: ClientProtocol,
        params: dict[str, Any] | None = None,
        *,
        url_conversion: dict[str, Any] | None = None,
        list_all: bool = False,
        page_size: int = 100,
        timeout: int = 60,
    ) -> dict[str, Any] | tuple[Any, int]:
        """List data units with optional pagination.

        Args:
            params: Query parameters for filtering.
            url_conversion: URL-to-path conversion config.
            list_all: If True, returns (generator, count).
            page_size: Number of items per page. Default 100 (larger pages
                reduce API calls; timeout increased to handle heavy payloads).
            timeout: Read timeout in seconds. Default 60 (longer timeout
                for large page sizes with heavy file metadata).

        Returns:
            Paginated list or (generator, count).
        """
        if url_conversion is None:
            url_conversion = {'files_fields': ['files']}

        if params is None:
            params = {}
        params.setdefault('page_size', page_size)

        return self._list(
            'data_units/',
            params=params,
            url_conversion=url_conversion,
            list_all=list_all,
            timeout=(5, timeout),  # (connect_timeout, read_timeout)
        )

    def verify_data_files_checksums(
        self: ClientProtocol,
        checksums: list[str],
    ) -> dict[str, Any]:
        """Verify if data files with given checksums exist.

        Args:
            checksums: List of MD5 checksums to verify.

        Returns:
            Verification result with existing checksums.
        """
        return self._post('data_files/verify_checksums/', data={'checksums': checksums})

    def upload_data_file(
        self: ClientProtocol,
        data: dict[str, Any],
        collection_id: int,
        *,
        use_chunked_upload: bool | None = None,
    ) -> dict[str, Any]:
        """Upload individual files for a data unit and return binding data.

        Args:
            data: Data unit definition with 'files' dict mapping names to paths.
            collection_id: Target data collection ID.
            use_chunked_upload: Force chunked (True) or direct (False) upload.

        Returns:
            Data ready for create_data_units() with checksums.

        Example:
            >>> result = client.upload_data_file(
            ...     {'files': {'image': '/path/to/img.jpg'}, 'meta': {'label': 1}},
            ...     collection_id=123
            ... )
            >>> # result['files']['image']['checksum'] is populated
        """
        files_data = {}

        for name, file_path in data.get('files', {}).items():
            if isinstance(file_path, str):
                path = Path(file_path)
            else:
                path = file_path

            upload_result = self.create_data_file(path, use_chunked_upload=use_chunked_upload)

            files_data[name] = {
                'checksum': upload_result['checksum'],
                'path': str(path),
            }

        return {
            'files': files_data,
            'data_collection': collection_id,
            'meta': data.get('meta', {}),
        }

    def upload_data_collection(
        self: ClientProtocol,
        collection_id: int,
        data: list[dict[str, Any]],
        *,
        project_id: int | None = None,
        batch_size: int = 1000,
        max_workers: int = 10,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> None:
        """Bulk upload data to a collection.

        Uploads files in parallel using a thread pool, then creates
        data units in batches. Optionally creates annotation tasks.

        Args:
            collection_id: Target data collection ID.
            data: List of data unit definitions.
            project_id: Optional project ID to create tasks for.
            batch_size: Number of data units per batch (default 1000).
            max_workers: Number of parallel upload threads (default 10).
            on_progress: Optional callback(completed, total) for progress.

        Example:
            >>> data = [
            ...     {'files': {'image': '/path/1.jpg'}, 'meta': {'label': 'cat'}},
            ...     {'files': {'image': '/path/2.jpg'}, 'meta': {'label': 'dog'}},
            ... ]
            >>> client.upload_data_collection(123, data, project_id=456)
        """
        total = len(data)
        completed = 0
        upload_results: list[dict[str, Any]] = []

        # Upload files in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.upload_data_file, item, collection_id): i for i, item in enumerate(data)}

            for future in as_completed(futures):
                result = future.result()
                upload_results.append(result)
                completed += 1

                if on_progress:
                    on_progress(completed, total)

        # Create data units in batches
        for batch in _batch_list(upload_results, batch_size):
            created_units = self.create_data_units(batch)

            # Optionally create tasks
            if project_id is not None:
                task_data = [{'data_unit': unit['id']} for unit in created_units.get('results', [created_units])]
                if task_data:
                    self._post('tasks/', data={'project': project_id, 'data': task_data})


__all__ = ['DataCollectionClientMixin']
