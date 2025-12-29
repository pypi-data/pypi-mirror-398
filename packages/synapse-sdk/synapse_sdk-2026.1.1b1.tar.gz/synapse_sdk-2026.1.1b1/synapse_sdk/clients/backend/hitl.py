"""HITL (Human-in-the-Loop) client mixin for assignment operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from synapse_sdk.clients.backend.models import SetTagsRequest

if TYPE_CHECKING:
    from synapse_sdk.clients.protocols import ClientProtocol


class HITLClientMixin:
    """Mixin for HITL-related API endpoints.

    Provides methods for managing annotation assignments.
    """

    def get_assignment(self: ClientProtocol, assignment_id: int) -> dict[str, Any]:
        """Get assignment details by ID.

        Args:
            assignment_id: Assignment ID.

        Returns:
            Assignment data including task and annotator info.
        """
        return self._get(f'assignments/{assignment_id}/')

    def list_assignments(
        self: ClientProtocol,
        params: dict[str, Any] | None = None,
        *,
        url_conversion: dict[str, Any] | None = None,
        list_all: bool = False,
    ) -> dict[str, Any] | tuple[Any, int]:
        """List assignments with optional pagination.

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
            'sdk/assignments/',
            params=params,
            url_conversion=url_conversion,
            list_all=list_all,
        )

    def set_tags_assignments(
        self: ClientProtocol,
        data: dict[str, Any],
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Set tags on multiple assignments.

        Args:
            data: Tag assignment data with 'ids', 'tags', and 'action'.
            params: Optional query parameters.

        Returns:
            Operation result.

        Example:
            >>> client.set_tags_assignments({
            ...     'ids': [1, 2, 3],
            ...     'tags': [10, 20],
            ...     'action': 'add'  # or 'remove'
            ... })
        """
        return self._post(
            'assignments/set_tags/',
            request_model=SetTagsRequest,
            data=data,
            params=params,
        )


__all__ = ['HITLClientMixin']
