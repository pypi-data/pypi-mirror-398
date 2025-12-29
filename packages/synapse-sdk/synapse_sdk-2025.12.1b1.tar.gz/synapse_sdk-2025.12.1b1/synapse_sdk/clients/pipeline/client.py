"""Pipeline Service Client for communicating with dev-api.

This client provides methods to interact with the pipeline orchestration
backend for registering pipelines, creating runs, and reporting progress.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Iterator
from datetime import datetime
from typing import Any

import httpx

from synapse_sdk.plugins.pipelines.models import (
    ActionProgress,
    LogEntry,
    PipelineProgress,
    RunStatus,
)

logger = logging.getLogger(__name__)


class PipelineServiceClient:
    """Client for the Pipeline Service API.

    Provides methods to manage pipelines, runs, progress, checkpoints, and logs.

    Attributes:
        base_url: Base URL of the pipeline service.
        timeout: Request timeout in seconds.

    Example:
        >>> client = PipelineServiceClient("http://localhost:8100")
        >>> pipeline = client.create_pipeline(
        ...     name="YOLO Training",
        ...     actions=[{"name": "download", "entrypoint": "plugin.download.DownloadAction"}]
        ... )
        >>> run = client.create_run(pipeline["id"], params={"dataset_id": 123})
        >>> client.report_progress(run["id"], current_action="download", status="running")
    """

    def __init__(
        self,
        base_url: str = 'http://localhost:8100',
        timeout: float = 30.0,
    ):
        """Initialize the pipeline service client.

        Args:
            base_url: Base URL of the pipeline service.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'},
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> 'PipelineServiceClient':
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # -------------------------------------------------------------------------
    # Pipeline CRUD
    # -------------------------------------------------------------------------

    def create_pipeline(
        self,
        name: str,
        actions: list[dict[str, Any]],
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new pipeline definition.

        Args:
            name: Pipeline name.
            actions: List of action definitions, each with 'name' and 'entrypoint'.
            description: Optional pipeline description.

        Returns:
            Created pipeline data including 'id'.
        """
        payload = {
            'name': name,
            'actions': actions,
            'description': description,
        }
        response = self.client.post('/api/v1/pipelines/', json=payload)
        response.raise_for_status()
        return response.json()

    def get_pipeline(self, pipeline_id: str) -> dict[str, Any]:
        """Get a pipeline by ID.

        Args:
            pipeline_id: Pipeline identifier.

        Returns:
            Pipeline data.
        """
        response = self.client.get(f'/api/v1/pipelines/{pipeline_id}')
        response.raise_for_status()
        return response.json()

    def list_pipelines(self, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        """List all pipelines.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of pipeline data.
        """
        response = self.client.get('/api/v1/pipelines/', params={'skip': skip, 'limit': limit})
        response.raise_for_status()
        return response.json()

    def delete_pipeline(self, pipeline_id: str) -> None:
        """Delete a pipeline.

        Args:
            pipeline_id: Pipeline identifier.
        """
        response = self.client.delete(f'/api/v1/pipelines/{pipeline_id}')
        response.raise_for_status()

    # -------------------------------------------------------------------------
    # Run Management
    # -------------------------------------------------------------------------

    def create_run(
        self,
        pipeline_id: str,
        params: dict[str, Any] | None = None,
        work_dir: str | None = None,
    ) -> dict[str, Any]:
        """Create a new run for a pipeline.

        Args:
            pipeline_id: Pipeline to run.
            params: Initial parameters for the run.
            work_dir: Working directory path.

        Returns:
            Created run data including 'id' and initial progress.
        """
        payload: dict[str, Any] = {}
        if params is not None:
            payload['params'] = params
        if work_dir is not None:
            payload['work_dir'] = work_dir

        response = self.client.post(f'/api/v1/pipelines/{pipeline_id}/runs/', json=payload)
        response.raise_for_status()
        return response.json()

    def get_run(self, run_id: str) -> dict[str, Any]:
        """Get a run by ID.

        Args:
            run_id: Run identifier.

        Returns:
            Run data including status and progress.
        """
        response = self.client.get(f'/api/v1/runs/{run_id}')
        response.raise_for_status()
        return response.json()

    def list_runs(
        self,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List all runs, optionally filtered by status.

        Args:
            status: Filter by run status.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of run data.
        """
        params: dict[str, Any] = {'skip': skip, 'limit': limit}
        if status:
            params['status_filter'] = status
        response = self.client.get('/api/v1/runs/', params=params)
        response.raise_for_status()
        return response.json()

    def update_run(
        self,
        run_id: str,
        status: str | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Update a run's status or result.

        Args:
            run_id: Run identifier.
            status: New status.
            result: Final result data.
            error: Error message if failed.

        Returns:
            Updated run data.
        """
        payload: dict[str, Any] = {}
        if status is not None:
            payload['status'] = status
        if result is not None:
            payload['result'] = result
        if error is not None:
            payload['error'] = error

        response = self.client.patch(f'/api/v1/runs/{run_id}', json=payload)
        response.raise_for_status()
        return response.json()

    def delete_run(self, run_id: str) -> None:
        """Delete a run.

        Args:
            run_id: Run identifier.
        """
        response = self.client.delete(f'/api/v1/runs/{run_id}')
        response.raise_for_status()

    # -------------------------------------------------------------------------
    # Progress Reporting
    # -------------------------------------------------------------------------

    def report_progress(
        self,
        run_id: str,
        current_action: str | None = None,
        current_action_index: int | None = None,
        status: str | None = None,
        action_progress: ActionProgress | dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Report progress update for a run.

        Args:
            run_id: Run identifier.
            current_action: Name of current action.
            current_action_index: Index of current action.
            status: Overall run status.
            action_progress: Progress for the current action.
            error: Error message if any.

        Returns:
            Updated run data.
        """
        payload: dict[str, Any] = {}
        if current_action is not None:
            payload['current_action'] = current_action
        if current_action_index is not None:
            payload['current_action_index'] = current_action_index
        if status is not None:
            payload['status'] = status
        if action_progress is not None:
            if isinstance(action_progress, ActionProgress):
                payload['action_progress'] = action_progress.to_dict()
            else:
                payload['action_progress'] = action_progress
        if error is not None:
            payload['error'] = error

        response = self.client.post(f'/api/v1/runs/{run_id}/progress', json=payload)
        response.raise_for_status()
        return response.json()

    def get_progress(self, run_id: str) -> PipelineProgress:
        """Get current progress for a run.

        Args:
            run_id: Run identifier.

        Returns:
            PipelineProgress object with current state.
        """
        response = self.client.get(f'/api/v1/runs/{run_id}/progress')
        response.raise_for_status()
        data = response.json()

        # Map API response to PipelineProgress
        return PipelineProgress(
            run_id=data['run_id'],
            pipeline_id=data.get('pipeline_id', ''),
            status=RunStatus(data.get('status', 'pending')),
            current_action=data.get('current_action'),
            current_action_index=data.get('current_action_index', 0),
            actions=[ActionProgress.from_dict(a) for a in data.get('progress', [])],
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error=data.get('error'),
        )

    # -------------------------------------------------------------------------
    # Checkpoints
    # -------------------------------------------------------------------------

    def create_checkpoint(
        self,
        run_id: str,
        action_name: str,
        action_index: int,
        status: str,
        params_snapshot: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        artifacts_path: str | None = None,
    ) -> dict[str, Any]:
        """Create a checkpoint for a run.

        Args:
            run_id: Run identifier.
            action_name: Name of the action.
            action_index: Index of the action.
            status: Action status at checkpoint.
            params_snapshot: Parameters at time of checkpoint.
            result: Result from the action if completed.
            artifacts_path: Path to saved artifacts.

        Returns:
            Created checkpoint data.
        """
        payload = {
            'action_name': action_name,
            'action_index': action_index,
            'status': status,
            'params_snapshot': params_snapshot,
            'result': result,
            'artifacts_path': artifacts_path,
        }
        response = self.client.post(f'/api/v1/runs/{run_id}/checkpoints/', json=payload)
        response.raise_for_status()
        return response.json()

    def get_checkpoints(self, run_id: str) -> list[dict[str, Any]]:
        """Get all checkpoints for a run.

        Args:
            run_id: Run identifier.

        Returns:
            List of checkpoint data.
        """
        response = self.client.get(f'/api/v1/runs/{run_id}/checkpoints/')
        response.raise_for_status()
        return response.json()

    def get_latest_checkpoint(self, run_id: str) -> dict[str, Any] | None:
        """Get the latest checkpoint for a run.

        Args:
            run_id: Run identifier.

        Returns:
            Latest checkpoint data or None if no checkpoints.
        """
        try:
            response = self.client.get(f'/api/v1/runs/{run_id}/checkpoints/latest')
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_checkpoint_by_action(self, run_id: str, action_name: str) -> dict[str, Any] | None:
        """Get checkpoint for a specific action.

        Args:
            run_id: Run identifier.
            action_name: Action name.

        Returns:
            Checkpoint data or None if not found.
        """
        try:
            response = self.client.get(f'/api/v1/runs/{run_id}/checkpoints/{action_name}')
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    # -------------------------------------------------------------------------
    # Logs
    # -------------------------------------------------------------------------

    def append_logs(
        self,
        run_id: str,
        entries: list[LogEntry] | list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Append log entries for a run.

        Args:
            run_id: Run identifier.
            entries: List of log entries.

        Returns:
            Created log entries.
        """
        # Convert LogEntry objects to dicts
        entry_dicts = []
        for entry in entries:
            if isinstance(entry, LogEntry):
                entry_dicts.append({
                    'message': entry.message,
                    'level': entry.level.value,
                    'action_name': entry.action_name,
                })
            else:
                entry_dicts.append(entry)

        payload = {'entries': entry_dicts}
        response = self.client.post(f'/api/v1/runs/{run_id}/logs/', json=payload)
        response.raise_for_status()
        return response.json()

    def get_logs(
        self,
        run_id: str,
        action_name: str | None = None,
        level: str | None = None,
        since: datetime | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Get logs for a run with optional filters.

        Args:
            run_id: Run identifier.
            action_name: Filter by action name.
            level: Filter by log level.
            since: Only return logs after this time.
            limit: Maximum number of logs to return.

        Returns:
            List of log entries.
        """
        params: dict[str, Any] = {'limit': limit}
        if action_name:
            params['action_name'] = action_name
        if level:
            params['level'] = level
        if since:
            params['since'] = since.isoformat()

        response = self.client.get(f'/api/v1/runs/{run_id}/logs/', params=params)
        response.raise_for_status()
        return response.json()

    # -------------------------------------------------------------------------
    # Progress Streaming
    # -------------------------------------------------------------------------

    def stream_progress(
        self,
        run_id: str,
        timeout: float = 3600.0,
    ) -> 'Iterator[PipelineProgress]':
        """Stream progress updates via SSE.

        Yields PipelineProgress objects as updates are received from the server.
        Continues until the run completes, fails, or is cancelled.

        Args:
            run_id: Run identifier.
            timeout: Maximum time to stream in seconds.

        Yields:
            PipelineProgress objects with current state.

        Example:
            >>> for progress in client.stream_progress(run_id):
            ...     print(f"Status: {progress.status}, Action: {progress.current_action}")
        """
        url = f'{self.base_url}/api/v1/runs/{run_id}/progress/stream'

        with httpx.stream('GET', url, timeout=timeout) as response:
            response.raise_for_status()

            event_type = None
            data_buffer = []

            for line in response.iter_lines():
                line = line.strip()

                if line.startswith('event:'):
                    event_type = line[6:].strip()
                elif line.startswith('data:'):
                    data_buffer.append(line[5:].strip())
                elif line == '' and data_buffer:
                    # End of event - process it
                    data_str = ''.join(data_buffer)
                    data_buffer = []

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    # Convert to PipelineProgress
                    progress = PipelineProgress(
                        run_id=data['run_id'],
                        pipeline_id=data.get('pipeline_id', ''),
                        status=RunStatus(data.get('status', 'pending')),
                        current_action=data.get('current_action'),
                        current_action_index=data.get('current_action_index', 0),
                        actions=[ActionProgress.from_dict(a) for a in data.get('progress', []) or []],
                        started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
                        completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
                        error=data.get('error'),
                    )

                    yield progress

                    # Stop on terminal events
                    if event_type in ('completed', 'failed', 'cancelled', 'error'):
                        return

    async def stream_progress_async(
        self,
        run_id: str,
        timeout: float = 3600.0,
    ) -> AsyncIterator[PipelineProgress]:
        """Stream progress updates via SSE (async version).

        Yields PipelineProgress objects as updates are received from the server.
        Continues until the run completes, fails, or is cancelled.

        Args:
            run_id: Run identifier.
            timeout: Maximum time to stream in seconds.

        Yields:
            PipelineProgress objects with current state.

        Example:
            >>> async for progress in client.stream_progress_async(run_id):
            ...     print(f"Status: {progress.status}, Action: {progress.current_action}")
        """
        url = f'{self.base_url}/api/v1/runs/{run_id}/progress/stream'

        async with httpx.AsyncClient(timeout=timeout) as async_client:
            async with async_client.stream('GET', url) as response:
                response.raise_for_status()

                event_type = None
                data_buffer: list[str] = []

                async for line in response.aiter_lines():
                    line = line.strip()

                    if line.startswith('event:'):
                        event_type = line[6:].strip()
                    elif line.startswith('data:'):
                        data_buffer.append(line[5:].strip())
                    elif line == '' and data_buffer:
                        # End of event - process it
                        data_str = ''.join(data_buffer)
                        data_buffer = []

                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        # Convert to PipelineProgress
                        started = data.get('started_at')
                        completed = data.get('completed_at')
                        progress = PipelineProgress(
                            run_id=data['run_id'],
                            pipeline_id=data.get('pipeline_id', ''),
                            status=RunStatus(data.get('status', 'pending')),
                            current_action=data.get('current_action'),
                            current_action_index=data.get('current_action_index', 0),
                            actions=[ActionProgress.from_dict(a) for a in data.get('progress', []) or []],
                            started_at=datetime.fromisoformat(started) if started else None,
                            completed_at=datetime.fromisoformat(completed) if completed else None,
                            error=data.get('error'),
                        )

                        yield progress

                        # Stop on terminal events
                        if event_type in ('completed', 'failed', 'cancelled', 'error'):
                            return

    # -------------------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------------------

    def health_check(self) -> bool:
        """Check if the pipeline service is healthy.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            response = self.client.get('/health')
            return response.status_code == 200
        except Exception:
            return False


__all__ = ['PipelineServiceClient']
