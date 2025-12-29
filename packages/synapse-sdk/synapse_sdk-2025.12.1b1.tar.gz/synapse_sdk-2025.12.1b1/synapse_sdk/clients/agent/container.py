from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from synapse_sdk.clients.protocols import ClientProtocol


class ContainerClientMixin:
    """Mixin for container management endpoints."""

    # Docker containers
    def list_docker_containers(self: ClientProtocol) -> list[dict]:
        """List all Docker containers on the host."""
        return self._get('containers/docker/')

    def get_docker_container(self: ClientProtocol, container_id: str) -> dict:
        """Get a specific Docker container by ID."""
        return self._get(f'containers/docker/{container_id}')

    def create_docker_container(
        self: ClientProtocol,
        plugin_release: str,
        *,
        params: dict[str, Any] | None = None,
        envs: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
        labels: list[str] | None = None,
    ) -> dict:
        """Build and run a Docker container for a plugin.

        Args:
            plugin_release: Plugin identifier (e.g., "plugin_code@version").
            params: Parameters forwarded to the plugin.
            envs: Environment variables injected into the container.
            metadata: Additional metadata stored with the container record.
            labels: Container labels for display or filtering.
        """
        data = {'plugin_release': plugin_release}
        if params is not None:
            data['params'] = params
        if envs is not None:
            data['envs'] = envs
        if metadata is not None:
            data['metadata'] = metadata
        if labels is not None:
            data['labels'] = labels

        return self._post('containers/docker/', data=data)

    def delete_docker_container(self: ClientProtocol, container_id: str) -> None:
        """Stop and remove a Docker container."""
        self._delete(f'containers/docker/{container_id}')

    # Database container records
    def list_containers(
        self: ClientProtocol,
        params: dict | None = None,
        *,
        list_all: bool = False,
    ) -> dict | tuple[Any, int]:
        """List tracked containers from database."""
        return self._list('containers/', params=params, list_all=list_all)

    def get_container(self: ClientProtocol, container_id: int) -> dict:
        """Get a tracked container by database ID."""
        return self._get(f'containers/{container_id}')

    def update_container(
        self: ClientProtocol,
        container_id: int,
        *,
        status: str | None = None,
    ) -> dict:
        """Update a tracked container's status."""
        data = {}
        if status is not None:
            data['status'] = status
        return self._patch(f'containers/{container_id}', data=data)

    def delete_container(self: ClientProtocol, container_id: int) -> None:
        """Delete a tracked container (stops Docker container too)."""
        self._delete(f'containers/{container_id}')
