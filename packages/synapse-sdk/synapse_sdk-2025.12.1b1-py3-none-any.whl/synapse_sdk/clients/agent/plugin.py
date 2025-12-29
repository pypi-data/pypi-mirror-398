from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from synapse_sdk.clients.protocols import ClientProtocol


class PluginClientMixin:
    """Mixin for plugin release endpoints."""

    def list_plugin_releases(
        self: ClientProtocol,
        params: dict | None = None,
        *,
        list_all: bool = False,
    ) -> dict | tuple[Any, int]:
        """List all plugin releases."""
        return self._list('plugin_releases/', params=params, list_all=list_all)

    def get_plugin_release(self: ClientProtocol, lookup: str) -> dict:
        """Get a plugin release by ID or code@version."""
        return self._get(f'plugin_releases/{lookup}')

    def create_plugin_release(
        self: ClientProtocol,
        plugin: str,
        version: str,
    ) -> dict:
        """Fetch and cache a plugin release."""
        return self._post('plugin_releases/', data={'plugin': plugin, 'version': version})

    def delete_plugin_release(self: ClientProtocol, lookup: str) -> None:
        """Delete a plugin release."""
        self._delete(f'plugin_releases/{lookup}')

    def run_plugin_release(
        self: ClientProtocol,
        lookup: str,
        action: str,
        params: dict[str, Any] | None = None,
        *,
        requirements: list[str] | None = None,
        job_id: str | None = None,
    ) -> Any:
        """Run a plugin release action.

        Args:
            lookup: Plugin identifier (ID or "plugin@version").
            action: Action name to execute.
            params: Parameters to pass to the action.
            requirements: Additional pip requirements.
            job_id: Optional job ID for tracking.
        """
        data: dict[str, Any] = {'action': action}
        if params is not None:
            data['params'] = params
        if requirements is not None:
            data['requirements'] = requirements
        if job_id is not None:
            data['job_id'] = job_id

        return self._post(f'plugin_releases/{lookup}/run/', data=data)

    def run_debug_plugin_release(
        self: ClientProtocol,
        action: str,
        params: dict[str, Any] | None = None,
        *,
        plugin_path: str | None = None,
        config: dict[str, Any] | None = None,
        modules: dict[str, str] | None = None,
        requirements: list[str] | None = None,
        job_id: str | None = None,
    ) -> Any:
        """Run a plugin in debug mode (from source path).

        Args:
            action: Action name to execute.
            params: Parameters to pass to the action.
            plugin_path: Path to the plugin source directory.
            config: Plugin configuration override.
            modules: Module source code mapping.
            requirements: Additional pip requirements.
            job_id: Optional job ID for tracking.
        """
        data: dict[str, Any] = {'action': action}
        if params is not None:
            data['params'] = params
        if plugin_path is not None:
            data['plugin_path'] = plugin_path
        if config is not None:
            data['config'] = config
        if modules is not None:
            data['modules'] = modules
        if requirements is not None:
            data['requirements'] = requirements
        if job_id is not None:
            data['job_id'] = job_id

        return self._post('plugin_releases/run_debug/', data=data)
