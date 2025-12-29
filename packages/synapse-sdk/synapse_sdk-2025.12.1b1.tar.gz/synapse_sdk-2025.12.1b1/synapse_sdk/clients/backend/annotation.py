"""Annotation client mixin for project and task operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from synapse_sdk.clients.backend.models import SetTagsRequest, TaskCreateRequest

if TYPE_CHECKING:
    from synapse_sdk.clients.protocols import ClientProtocol


class AnnotationClientMixin:
    """Mixin for annotation-related API endpoints.

    Provides methods for managing projects, tasks, and task tags.
    """

    def get_project(self: ClientProtocol, project_id: int) -> dict[str, Any]:
        """Get project details by ID.

        Args:
            project_id: Project ID.

        Returns:
            Project data including configuration and statistics.
        """
        return self._get(f'projects/{project_id}/')

    def get_task(
        self: ClientProtocol,
        task_id: int,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get task details by ID.

        Args:
            task_id: Task ID.
            params: Optional query parameters (e.g., expand, fields).

        Returns:
            Task data including annotations and metadata.
        """
        return self._get(f'tasks/{task_id}/', params=params)

    def annotate_task_data(
        self: ClientProtocol,
        task_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Submit annotation data for a task.

        Args:
            task_id: Task ID to annotate.
            data: Annotation data payload.

        Returns:
            Updated task data.
        """
        return self._put(f'tasks/{task_id}/annotate_task_data/', data=data)

    def get_task_tag(self: ClientProtocol, tag_id: int) -> dict[str, Any]:
        """Get task tag details by ID.

        Args:
            tag_id: Tag ID.

        Returns:
            Tag data including name and color.
        """
        return self._get(f'task_tags/{tag_id}/')

    def list_task_tags(
        self: ClientProtocol,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List available task tags.

        Args:
            params: Optional query parameters for filtering.

        Returns:
            Paginated list of task tags.
        """
        return self._get('task_tags/', params=params)

    def list_tasks(
        self: ClientProtocol,
        params: dict[str, Any] | None = None,
        *,
        url_conversion: dict[str, Any] | None = None,
        list_all: bool = False,
    ) -> dict[str, Any] | tuple[Any, int]:
        """List tasks with optional pagination.

        Args:
            params: Query parameters for filtering (project, status, etc.).
            url_conversion: URL-to-path conversion config for file fields.
            list_all: If True, returns (generator, count) for all results.

        Returns:
            Paginated task list, or (generator, count) if list_all=True.

        Example:
            >>> # Get first page
            >>> tasks = client.list_tasks({'project': 123})
            >>> # Get all tasks as generator
            >>> tasks_gen, count = client.list_tasks({'project': 123}, list_all=True)
        """
        if url_conversion is None:
            url_conversion = {'files_fields': ['files']}

        return self._list(
            'sdk/tasks/',
            params=params,
            url_conversion=url_conversion,
            list_all=list_all,
        )

    def create_tasks(
        self: ClientProtocol,
        data: dict[str, Any] | list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create one or more annotation tasks.

        Args:
            data: Task data or list of task data.

        Returns:
            Created task(s) response.

        Example:
            >>> client.create_tasks({
            ...     'project': 123,
            ...     'data': [{'image': 'path/to/image.jpg'}]
            ... })
        """
        return self._post('tasks/', request_model=TaskCreateRequest, data=data)

    def set_tags_tasks(
        self: ClientProtocol,
        data: dict[str, Any],
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Set tags on multiple tasks.

        Args:
            data: Tag assignment data with 'ids', 'tags', and 'action'.
            params: Optional query parameters.

        Returns:
            Operation result.

        Example:
            >>> client.set_tags_tasks({
            ...     'ids': [1, 2, 3],
            ...     'tags': [10, 20],
            ...     'action': 'add'  # or 'remove'
            ... })
        """
        return self._post(
            'tasks/set_tags/',
            request_model=SetTagsRequest,
            data=data,
            params=params,
        )


__all__ = ['AnnotationClientMixin']
