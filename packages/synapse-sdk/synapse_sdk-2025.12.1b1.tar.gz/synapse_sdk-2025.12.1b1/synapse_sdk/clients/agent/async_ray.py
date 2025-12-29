from __future__ import annotations

import json
from typing import TYPE_CHECKING, AsyncGenerator, Literal

from synapse_sdk.exceptions import ClientError
from synapse_sdk.utils.network import (
    StreamLimits,
    http_to_websocket_url,
    sanitize_error_message,
    validate_resource_id,
    validate_timeout,
)

if TYPE_CHECKING:
    from synapse_sdk.clients.protocols import AsyncClientProtocol

StreamProtocol = Literal['websocket', 'http', 'auto']


class AsyncRayClientMixin:
    """Async mixin for Ray cluster management endpoints."""

    _stream_limits: StreamLimits | None = None

    @property
    def stream_limits(self) -> StreamLimits:
        """Get stream limits configuration."""
        if self._stream_limits is None:
            self._stream_limits = StreamLimits()
        return self._stream_limits

    @stream_limits.setter
    def stream_limits(self, value: StreamLimits) -> None:
        """Set stream limits configuration."""
        self._stream_limits = value

    # -------------------------------------------------------------------------
    # Jobs
    # -------------------------------------------------------------------------

    async def list_jobs(self: AsyncClientProtocol) -> list[dict]:
        """List all Ray jobs."""
        return await self._get('ray/jobs/')

    async def get_job(self: AsyncClientProtocol, job_id: str) -> dict:
        """Get a Ray job by ID."""
        return await self._get(f'ray/jobs/{job_id}')

    async def get_job_logs(self: AsyncClientProtocol, job_id: str) -> str:
        """Get all logs for a job (non-streaming)."""
        return await self._get(f'ray/jobs/{job_id}/logs')

    async def stop_job(self: AsyncClientProtocol, job_id: str) -> dict:
        """Stop a running job."""
        return await self._post(f'ray/jobs/{job_id}/stop/')

    async def websocket_tail_job_logs(
        self: AsyncClientProtocol,
        job_id: str,
        timeout: float = 30.0,
    ) -> AsyncGenerator[str, None]:
        """Stream job logs via WebSocket protocol (async).

        Establishes an async WebSocket connection for real-time log streaming.

        Args:
            job_id: The Ray job ID to tail logs for.
            timeout: Connection and read timeout in seconds.

        Yields:
            Log message strings.

        Raises:
            ClientError: On connection, protocol, or validation errors.

        Example:
            >>> async for line in client.websocket_tail_job_logs('raysubmit_abc123'):
            ...     print(line)
        """
        validated_id = validate_resource_id(job_id, 'job')
        validated_timeout = validate_timeout(timeout)

        url = self._get_url(f'ray/jobs/{validated_id}/logs/')
        ws_url = http_to_websocket_url(f'{self.base_url}/{url}')
        headers = self._get_headers()

        try:
            import websockets
        except ImportError:
            raise ClientError(500, 'websockets package required for async WebSocket streaming')

        limits = self.stream_limits
        message_count = 0

        try:
            async with websockets.connect(
                ws_url,
                additional_headers=headers,
                close_timeout=validated_timeout,
                ping_timeout=validated_timeout,
            ) as ws:
                async for data in ws:
                    if not data:
                        break

                    message_count += 1
                    if message_count > limits.max_messages:
                        raise ClientError(429, 'Stream message limit exceeded')

                    if len(str(data)) > limits.max_message_size:
                        continue

                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        event = {'message': data}

                    event_type = event.get('type')
                    if event_type == 'error':
                        raise ClientError(500, event.get('message', 'Unknown error'))
                    elif event_type == 'complete':
                        return

                    if msg := event.get('message'):
                        yield msg

        except ClientError:
            raise
        except Exception as e:
            if 'ConnectionClosed' in type(e).__name__:
                return  # Normal close
            raise ClientError(503, sanitize_error_message(str(e), 'WebSocket error'))

    async def stream_tail_job_logs(
        self: AsyncClientProtocol,
        job_id: str,
        timeout: float = 30.0,
    ) -> AsyncGenerator[str, None]:
        """Stream job logs via HTTP chunked transfer (async).

        Uses HTTP streaming as an alternative when WebSocket is unavailable.

        Args:
            job_id: The Ray job ID to tail logs for.
            timeout: Connection timeout in seconds.

        Yields:
            Log lines as strings.

        Raises:
            ClientError: On connection, protocol, or validation errors.

        Example:
            >>> async for line in client.stream_tail_job_logs('raysubmit_abc123'):
            ...     print(line)
        """
        validated_id = validate_resource_id(job_id, 'job')
        validated_timeout = validate_timeout(timeout)

        url = self._get_url(f'ray/jobs/{validated_id}/logs/')
        headers = self._get_headers()

        client = await self._get_client()
        limits = self.stream_limits
        line_count = 0
        total_bytes = 0

        try:
            async with client.stream(
                'GET',
                url,
                headers=headers,
                timeout=validated_timeout,
            ) as response:
                if not response.is_success:
                    raise ClientError(response.status_code, 'HTTP streaming failed')

                async for line in response.aiter_lines():
                    if line:
                        line_count += 1
                        total_bytes += len(line.encode('utf-8'))

                        if line_count > limits.max_lines:
                            raise ClientError(429, 'Stream line limit exceeded')

                        if total_bytes > limits.max_bytes:
                            raise ClientError(429, 'Stream size limit exceeded')

                        if len(line) > limits.max_message_size:
                            continue

                        yield line

        except ClientError:
            raise
        except Exception as e:
            raise ClientError(503, sanitize_error_message(str(e), 'HTTP streaming error'))

    async def tail_job_logs(
        self: AsyncClientProtocol,
        job_id: str,
        timeout: float = 30.0,
        *,
        protocol: StreamProtocol = 'auto',
    ) -> AsyncGenerator[str, None]:
        """Stream job logs with automatic protocol selection (async).

        Unified method that supports WebSocket, HTTP, and auto-selection.

        Args:
            job_id: The Ray job ID to tail logs for.
            timeout: Connection timeout in seconds.
            protocol: Protocol to use:
                - 'websocket': Use WebSocket only
                - 'http': Use HTTP streaming only
                - 'auto': Try WebSocket, fall back to HTTP on connection failure

        Yields:
            Log message strings.

        Raises:
            ClientError: On connection, protocol, or validation errors.

        Example:
            >>> async for line in client.tail_job_logs('raysubmit_abc123'):
            ...     print(line)
        """
        validate_resource_id(job_id, 'job')
        validate_timeout(timeout)

        if protocol == 'websocket':
            async for msg in self.websocket_tail_job_logs(job_id, timeout):
                yield msg
        elif protocol == 'http':
            async for msg in self.stream_tail_job_logs(job_id, timeout):
                yield msg
        elif protocol == 'auto':
            try:
                async for msg in self.websocket_tail_job_logs(job_id, timeout):
                    yield msg
            except ClientError as e:
                if e.status_code in (500, 503):
                    async for msg in self.stream_tail_job_logs(job_id, timeout):
                        yield msg
                else:
                    raise
        else:
            raise ClientError(400, f'Invalid protocol: {protocol}')

    # -------------------------------------------------------------------------
    # Nodes
    # -------------------------------------------------------------------------

    async def list_nodes(self: AsyncClientProtocol) -> list[dict]:
        """List all Ray nodes."""
        return await self._get('ray/nodes/')

    async def get_node(self: AsyncClientProtocol, node_id: str) -> dict:
        """Get a Ray node by ID."""
        return await self._get(f'ray/nodes/{node_id}')

    # -------------------------------------------------------------------------
    # Tasks
    # -------------------------------------------------------------------------

    async def list_tasks(self: AsyncClientProtocol) -> list[dict]:
        """List all Ray tasks."""
        return await self._get('ray/tasks/')

    async def get_task(self: AsyncClientProtocol, task_id: str) -> dict:
        """Get a Ray task by ID."""
        return await self._get(f'ray/tasks/{task_id}')

    # -------------------------------------------------------------------------
    # Serve Applications
    # -------------------------------------------------------------------------

    async def list_serve_applications(self: AsyncClientProtocol) -> list[dict]:
        """List all Ray Serve applications."""
        return await self._get('ray/serve_applications/')

    async def get_serve_application(self: AsyncClientProtocol, name: str) -> dict:
        """Get a Ray Serve application by name."""
        return await self._get(f'ray/serve_applications/{name}')

    async def delete_serve_application(self: AsyncClientProtocol, name: str) -> None:
        """Delete a Ray Serve application."""
        await self._delete(f'ray/serve_applications/{name}')
