"""ML client mixin for model and ground truth operations."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.clients.backend.models import ModelCreateRequest

if TYPE_CHECKING:
    from synapse_sdk.clients.protocols import ClientProtocol


class MLClientMixin:
    """Mixin for ML-related API endpoints.

    Provides methods for managing models and ground truth data.
    """

    def list_models(
        self: ClientProtocol,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List models with optional filtering.

        Args:
            params: Query parameters for filtering.

        Returns:
            Paginated model list.
        """
        return self._get('models/', params=params)

    def get_model(
        self: ClientProtocol,
        model_id: int,
        *,
        params: dict[str, Any] | None = None,
        url_conversion: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get model details by ID.

        Args:
            model_id: Model ID.
            params: Optional query parameters.
            url_conversion: URL-to-path conversion config.

        Returns:
            Model data including file URL and metadata.
        """
        if url_conversion is None:
            url_conversion = {'files_fields': ['file'], 'is_list': False}

        return self._get(
            f'models/{model_id}/',
            params=params,
            url_conversion=url_conversion,
        )

    def create_model(
        self: ClientProtocol,
        data: dict[str, Any],
        *,
        file: str | Path | None = None,
    ) -> dict[str, Any]:
        """Create a new model with file upload.

        Large files are automatically uploaded using chunked upload.

        Args:
            data: Model metadata (name, plugin, version, etc.).
            file: Model file to upload (uses chunked upload).

        Returns:
            Created model data.

        Example:
            >>> client.create_model(
            ...     {'name': 'My Model', 'plugin': 123},
            ...     file='/path/to/model.pt'
            ... )
        """
        # Handle file upload via chunked upload
        if file is not None:
            path = Path(file)
            if not path.exists():
                raise FileNotFoundError(f'Model file not found: {path}')

            # Upload file in chunks
            upload_result = self.create_chunked_upload(path)
            data['chunked_upload'] = upload_result['id']

        return self._post(
            'models/',
            request_model=ModelCreateRequest,
            data=data,
        )

    def list_ground_truth_events(
        self: ClientProtocol,
        params: dict[str, Any] | None = None,
        *,
        url_conversion: dict[str, Any] | None = None,
        list_all: bool = False,
    ) -> dict[str, Any] | tuple[Any, int]:
        """List ground truth events.

        Args:
            params: Query parameters for filtering.
            url_conversion: URL-to-path conversion config.
            list_all: If True, returns (generator, count).

        Returns:
            Paginated list or (generator, count).
        """
        if url_conversion is None:
            url_conversion = {'files_fields': ['files']}

        return self._list(
            'sdk/ground_truth_events/',
            params=params,
            url_conversion=url_conversion,
            list_all=list_all,
        )

    def get_ground_truth_version(
        self: ClientProtocol,
        version_id: int,
    ) -> dict[str, Any]:
        """Get ground truth dataset version by ID.

        Args:
            version_id: Version ID.

        Returns:
            Version data including file manifest.
        """
        return self._get(f'ground_truth_dataset_versions/{version_id}/')


__all__ = ['MLClientMixin']
