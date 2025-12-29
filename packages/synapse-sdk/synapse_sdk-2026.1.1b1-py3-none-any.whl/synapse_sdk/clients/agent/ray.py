from __future__ import annotations

import json
from typing import TYPE_CHECKING, Generator, Literal

from synapse_sdk.exceptions import ClientError
from synapse_sdk.utils.network import (
    StreamLimits,
    http_to_websocket_url,
    sanitize_error_message,
    validate_resource_id,
    validate_timeout,
)

if TYPE_CHECKING:
    from synapse_sdk.clients.protocols import ClientProtocol

StreamProtocol = Literal['websocket', 'http', 'auto']


class RayClientMixin:
    """Mixin for Ray cluster management endpoints."""

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

    def list_jobs(self: ClientProtocol) -> list[dict]:
        """List all Ray jobs."""
        return self._get('ray/jobs/')

    def get_job(self: ClientProtocol, job_id: str) -> dict:
        """Get a Ray job by ID."""
        return self._get(f'ray/jobs/{job_id}')

    def get_job_logs(self: ClientProtocol, job_id: str) -> str:
        """Get all logs for a job (non-streaming)."""
        return self._get(f'ray/jobs/{job_id}/logs')

    def stop_job(self: ClientProtocol, job_id: str) -> dict:
        """Stop a running job."""
        return self._post(f'ray/jobs/{job_id}/stop/')

    def websocket_tail_job_logs(
        self: ClientProtocol,
        job_id: str,
        timeout: float = 30.0,
    ) -> Generator[str, None, None]:
        """Stream job logs via WebSocket protocol.

        Establishes a WebSocket connection for real-time log streaming.
        Preferred method for low-latency log monitoring.

        Args:
            job_id: The Ray job ID to tail logs for.
            timeout: Connection and read timeout in seconds.

        Yields:
            Log message strings.

        Raises:
            ClientError: On connection, protocol, or validation errors.

        Example:
            >>> for line in client.websocket_tail_job_logs('raysubmit_abc123'):
            ...     print(line)
        """
        validated_id = validate_resource_id(job_id, 'job')
        validated_timeout = validate_timeout(timeout)

        url = self._get_url(f'ray/jobs/{validated_id}/logs/')
        ws_url = http_to_websocket_url(url)
        headers = self._get_headers()

        try:
            import websocket
        except ImportError:
            raise ClientError(500, 'websocket-client package required for WebSocket streaming')

        header_list = [f'{k}: {v}' for k, v in headers.items()]

        try:
            ws = websocket.create_connection(
                ws_url,
                header=header_list,
                timeout=validated_timeout,
            )
        except websocket.WebSocketException as e:
            raise ClientError(503, f'WebSocket connection failed: {e}')
        except Exception as e:
            raise ClientError(503, sanitize_error_message(str(e), 'connection error'))

        limits = self.stream_limits
        message_count = 0

        try:
            while True:
                try:
                    data = ws.recv()
                except websocket.WebSocketTimeoutException:
                    break
                except websocket.WebSocketConnectionClosedException:
                    break

                if not data:
                    break

                message_count += 1
                if message_count > limits.max_messages:
                    raise ClientError(429, 'Stream message limit exceeded')

                # Skip oversized messages
                if len(data) > limits.max_message_size:
                    continue

                # Parse JSON event format
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    event = {'message': data}

                # Handle event types
                event_type = event.get('type')
                if event_type == 'error':
                    raise ClientError(500, event.get('message', 'Unknown error'))
                elif event_type == 'complete':
                    return

                if msg := event.get('message'):
                    yield msg
        finally:
            ws.close()

    def stream_tail_job_logs(
        self: ClientProtocol,
        job_id: str,
        timeout: float = 30.0,
    ) -> Generator[str, None, None]:
        """Stream job logs via HTTP chunked transfer encoding.

        Uses HTTP streaming as an alternative when WebSocket is unavailable.

        Args:
            job_id: The Ray job ID to tail logs for.
            timeout: Connection timeout in seconds (read timeout is infinite).

        Yields:
            Log lines as strings.

        Raises:
            ClientError: On connection, protocol, or validation errors.

        Example:
            >>> for line in client.stream_tail_job_logs('raysubmit_abc123'):
            ...     print(line)
        """
        validated_id = validate_resource_id(job_id, 'job')
        validated_timeout = validate_timeout(timeout)

        url = self._get_url(f'ray/jobs/{validated_id}/logs/')
        headers = self._get_headers()

        response = None
        try:
            response = self.requests_session.get(
                url,
                headers=headers,
                stream=True,
                timeout=(validated_timeout, None),  # No read timeout for streaming
            )
            response.raise_for_status()

            limits = self.stream_limits
            line_count = 0
            total_bytes = 0

            for line in response.iter_lines(decode_unicode=True):
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
        finally:
            if response is not None:
                response.close()

    def tail_job_logs(
        self: ClientProtocol,
        job_id: str,
        timeout: float = 30.0,
        *,
        protocol: StreamProtocol = 'auto',
    ) -> Generator[str, None, None]:
        """Stream job logs with automatic protocol selection.

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
            >>> # Auto protocol selection (recommended)
            >>> for line in client.tail_job_logs('raysubmit_abc123'):
            ...     print(line)

            >>> # Explicit WebSocket
            >>> for line in client.tail_job_logs('raysubmit_abc123', protocol='websocket'):
            ...     print(line)

            >>> # Explicit HTTP streaming
            >>> for line in client.tail_job_logs('raysubmit_abc123', protocol='http'):
            ...     print(line)
        """
        # Pre-validate to fail fast
        validate_resource_id(job_id, 'job')
        validate_timeout(timeout)

        if protocol == 'websocket':
            yield from self.websocket_tail_job_logs(job_id, timeout)
        elif protocol == 'http':
            yield from self.stream_tail_job_logs(job_id, timeout)
        elif protocol == 'auto':
            try:
                yield from self.websocket_tail_job_logs(job_id, timeout)
            except ClientError as e:
                # Fall back to HTTP on WebSocket failures
                if e.status_code in (500, 503):
                    yield from self.stream_tail_job_logs(job_id, timeout)
                else:
                    raise
        else:
            raise ClientError(400, f'Invalid protocol: {protocol}')

    # -------------------------------------------------------------------------
    # Nodes
    # -------------------------------------------------------------------------

    def list_nodes(self: ClientProtocol) -> list[dict]:
        """List all Ray nodes."""
        return self._get('ray/nodes/')

    def get_node(self: ClientProtocol, node_id: str) -> dict:
        """Get a Ray node by ID."""
        return self._get(f'ray/nodes/{node_id}')

    # -------------------------------------------------------------------------
    # Tasks
    # -------------------------------------------------------------------------

    def list_tasks(self: ClientProtocol) -> list[dict]:
        """List all Ray tasks."""
        return self._get('ray/tasks/')

    def get_task(self: ClientProtocol, task_id: str) -> dict:
        """Get a Ray task by ID."""
        return self._get(f'ray/tasks/{task_id}')

    # -------------------------------------------------------------------------
    # Serve Applications
    # -------------------------------------------------------------------------

    def list_serve_applications(self: ClientProtocol) -> list[dict]:
        """List all Ray Serve applications."""
        return self._get('ray/serve_applications/')

    def get_serve_application(self: ClientProtocol, name: str) -> dict:
        """Get a Ray Serve application by name."""
        return self._get(f'ray/serve_applications/{name}')

    def delete_serve_application(self: ClientProtocol, name: str) -> None:
        """Delete a Ray Serve application."""
        self._delete(f'ray/serve_applications/{name}')
