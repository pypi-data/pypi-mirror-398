"""Integration client mixin for plugin, job, and storage operations."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.clients.backend.models import (
    Agent,
    PluginReleaseCreateRequest,
    PluginRunRequest,
    ServeApplicationCreateRequest,
    Storage,
    UpdateJobRequest,
)
from synapse_sdk.utils.file.io import convert_file_to_base64

if TYPE_CHECKING:
    from synapse_sdk.clients.protocols import ClientProtocol


class IntegrationClientMixin:
    """Mixin for integration-related API endpoints.

    Provides methods for managing plugins, jobs, logs, and serve applications.
    """

    # -------------------------------------------------------------------------
    # Agent Operations
    # -------------------------------------------------------------------------

    def list_agents(
        self: ClientProtocol,
        params: dict[str, Any] | None = None,
    ) -> list[Agent]:
        """List available agents.

        Args:
            params: Optional query parameters for filtering.

        Returns:
            List of Agent objects.
        """
        response = self._get('agents/', params=params)
        results = response.get('results', [])
        agents = []
        for item in results:
            agent = Agent.model_validate(item)
            # Extract token from node_install_script if not set
            if not agent.token:
                agent.token = agent.extract_token()
            agents.append(agent)
        return agents

    def health_check_agent(self: ClientProtocol, agent_token: str) -> dict[str, Any]:
        """Check agent health and connectivity.

        Args:
            agent_token: Agent authentication token.

        Returns:
            Agent health status and metadata.
        """
        return self._post(f'agents/{agent_token}/connect/')

    # -------------------------------------------------------------------------
    # Plugin Operations
    # -------------------------------------------------------------------------

    def get_plugin(self: ClientProtocol, plugin_id: int) -> dict[str, Any]:
        """Get plugin details by ID.

        Args:
            plugin_id: Plugin ID.

        Returns:
            Plugin data including configuration and releases.
        """
        return self._get(f'plugins/{plugin_id}/')

    def create_plugin(self: ClientProtocol, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new plugin.

        Args:
            data: Plugin creation data (name, category, etc.).

        Returns:
            Created plugin data.
        """
        return self._post('plugins/', data=data)

    def update_plugin(
        self: ClientProtocol,
        plugin_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update an existing plugin.

        Args:
            plugin_id: Plugin ID to update.
            data: Fields to update.

        Returns:
            Updated plugin data.
        """
        return self._put(f'plugins/{plugin_id}/', data=data)

    def run_plugin(
        self: ClientProtocol,
        plugin: int | str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Run a plugin action.

        Args:
            plugin: Plugin ID or code.
            data: Run parameters including action, agent, and params.

        Returns:
            Job data or direct result.

        Example:
            >>> client.run_plugin('yolov8', {
            ...     'agent': 1,
            ...     'action': 'deployment',
            ...     'params': {'num_cpus': 8},
            ... })
        """
        return self._post(
            f'plugins/{plugin}/run/',
            request_model=PluginRunRequest,
            data=data,
        )

    # -------------------------------------------------------------------------
    # Plugin Release Operations
    # -------------------------------------------------------------------------

    def get_plugin_release(
        self: ClientProtocol,
        release_id: int,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get plugin release details by ID.

        Args:
            release_id: Plugin release ID.
            params: Optional query parameters.

        Returns:
            Plugin release data including config and requirements.
        """
        return self._get(f'plugin_releases/{release_id}/', params=params)

    def create_plugin_release(
        self: ClientProtocol,
        data: dict[str, Any],
        *,
        file: str | Path | None = None,
    ) -> dict[str, Any]:
        """Create a new plugin release.

        Args:
            data: Release data (plugin, version, config, requirements).
            file: Optional plugin archive file to upload.

        Returns:
            Created plugin release data.

        Example:
            >>> client.create_plugin_release(
            ...     {'plugin': 123, 'version': '1.0.0'},
            ...     file='/path/to/plugin.zip'
            ... )
        """
        files = None
        if file is not None:
            files = {'file': file}

        return self._post(
            'plugin_releases/',
            request_model=PluginReleaseCreateRequest,
            data=data,
            files=files,
        )

    # -------------------------------------------------------------------------
    # Job Operations
    # -------------------------------------------------------------------------

    def get_job(
        self: ClientProtocol,
        job_id: int | str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get job details by ID.

        Args:
            job_id: Job ID (integer or UUID string).
            params: Optional query parameters.

        Returns:
            Job data including status and progress.
        """
        return self._get(f'jobs/{job_id}/', params=params)

    def list_jobs(
        self: ClientProtocol,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List jobs with optional filtering.

        Args:
            params: Query parameters (status, plugin, etc.).

        Returns:
            Paginated job list.
        """
        return self._get('jobs/', params=params)

    def update_job(
        self: ClientProtocol,
        job_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update job status and data.

        Args:
            job_id: Job ID to update.
            data: Update payload (status, progress_record, metrics_record, etc.).

        Returns:
            Updated job data.

        Example:
            >>> client.update_job(123, {
            ...     'status': 'running',
            ...     'progress_record': {'step': 5, 'total': 100}
            ... })
        """
        return self._patch(
            f'jobs/{job_id}/',
            request_model=UpdateJobRequest,
            data=data,
        )

    def list_job_console_logs(self: ClientProtocol, job_id: int) -> dict[str, Any]:
        """Get console logs for a job.

        Args:
            job_id: Job ID.

        Returns:
            Console log entries.
        """
        return self._get(f'jobs/{job_id}/console_logs/')

    def tail_job_console_logs(
        self: ClientProtocol,
        job_id: int | str,
    ) -> Generator[str, None, None]:
        """Stream console logs for a running job.

        Yields log lines as they become available.

        Args:
            job_id: Job ID (integer or UUID string) to tail.

        Yields:
            Log lines as strings.

        Example:
            >>> for line in client.tail_job_console_logs('abc-123'):
            ...     print(line)
        """
        # Use async endpoint for streaming
        # The async endpoint is at /async/jobs/{id}/tail_console_logs/
        base = self.base_url.rstrip('/')
        url = f'{base}/async/jobs/{job_id}/tail_console_logs/'
        headers = self._get_headers()

        response = self.requests_session.get(
            url,
            headers=headers,
            stream=True,
            timeout=(self.timeout['connect'], None),  # No read timeout for streaming
        )
        response.raise_for_status()

        yield from response.iter_lines(decode_unicode=True)

    # -------------------------------------------------------------------------
    # Log Operations
    # -------------------------------------------------------------------------

    def create_logs(
        self: ClientProtocol,
        data: dict[str, Any] | list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create log entries with optional file attachments.

        File fields are automatically converted to base64 data URIs.

        Args:
            data: Single log entry or list of entries.

        Returns:
            Created log entries response.

        Example:
            >>> client.create_logs({
            ...     'message': 'Training complete',
            ...     'level': 'info',
            ...     'file': '/path/to/result.png'  # Auto-converted to base64
            ... })
        """
        # Normalize to list
        items = data if isinstance(data, list) else [data]

        # Convert file fields to base64
        for item in items:
            if 'file' in item and item['file']:
                file_path = item['file']
                if not isinstance(file_path, str) or not file_path.startswith('data:'):
                    item['file'] = convert_file_to_base64(file_path)

        return self._post('logs/', data=items if len(items) > 1 else items[0])

    # -------------------------------------------------------------------------
    # Serve Application Operations
    # -------------------------------------------------------------------------

    def create_serve_application(
        self: ClientProtocol,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a Ray Serve application.

        Args:
            data: Application config (name, plugin_release, action, params).

        Returns:
            Created serve application data.
        """
        return self._post(
            'serve_applications/',
            request_model=ServeApplicationCreateRequest,
            data=data,
        )

    def list_serve_applications(
        self: ClientProtocol,
        params: dict[str, Any] | None = None,
        *,
        list_all: bool = False,
    ) -> dict[str, Any] | tuple[Any, int]:
        """List Ray Serve applications.

        Args:
            params: Query parameters for filtering.
            list_all: If True, returns (generator, count).

        Returns:
            Paginated list or (generator, count).
        """
        return self._list('serve_applications/', params=params, list_all=list_all)

    # -------------------------------------------------------------------------
    # Storage Operations
    # -------------------------------------------------------------------------

    def get_storage(self: ClientProtocol, storage_id: int) -> Storage:
        """Get storage configuration by ID.

        Args:
            storage_id: Storage ID.

        Returns:
            Storage model with provider configuration.
        """
        response = self._get(
            f'storages/{storage_id}/',
            params={'with_configuration': 'true'},
        )
        return Storage.model_validate(response)


__all__ = ['IntegrationClientMixin']
