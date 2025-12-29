from __future__ import annotations

from synapse_sdk.clients.agent.async_ray import AsyncRayClientMixin
from synapse_sdk.clients.agent.container import ContainerClientMixin
from synapse_sdk.clients.agent.plugin import PluginClientMixin
from synapse_sdk.clients.agent.ray import RayClientMixin
from synapse_sdk.clients.base import AsyncBaseClient, BaseClient


class AgentClient(ContainerClientMixin, PluginClientMixin, RayClientMixin, BaseClient):
    """Sync client for synapse-agent API."""

    name = 'Agent'

    def __init__(
        self,
        base_url: str,
        agent_token: str,
        *,
        user_token: str | None = None,
        tenant: str | None = None,
        timeout: dict[str, int] | None = None,
    ):
        """Initialize the agent client.

        Args:
            base_url: Agent API base URL.
            agent_token: Agent authentication token.
            user_token: Optional user token for impersonation.
            tenant: Optional tenant identifier.
            timeout: Request timeout dict with 'connect' and 'read' keys.
        """
        super().__init__(base_url, timeout=timeout or {'connect': 3, 'read': 10})
        self.agent_token = agent_token
        self.user_token = user_token
        self.tenant = tenant

    def _get_headers(self) -> dict[str, str]:
        """Return authentication headers."""
        headers = {'Authorization': self.agent_token}
        if self.user_token:
            headers['SYNAPSE-User'] = f'Token {self.user_token}'
        if self.tenant:
            headers['SYNAPSE-Tenant'] = f'Token {self.tenant}'
        return headers

    def health_check(self) -> dict:
        """Check agent health."""
        path = 'health/'
        return self._get(path)


class AsyncAgentClient(AsyncRayClientMixin, AsyncBaseClient):
    """Async client for synapse-agent API.

    Provides async/await interface for all agent operations including
    WebSocket and HTTP streaming for job log tailing.

    Example:
        >>> async with AsyncAgentClient(base_url, agent_token) as client:
        ...     jobs = await client.list_jobs()
        ...     async for line in client.tail_job_logs('job-123'):
        ...         print(line)
    """

    name = 'Agent'

    def __init__(
        self,
        base_url: str,
        agent_token: str,
        *,
        user_token: str | None = None,
        tenant: str | None = None,
        timeout: float | None = None,
    ):
        """Initialize the async agent client.

        Args:
            base_url: Agent API base URL.
            agent_token: Agent authentication token.
            user_token: Optional user token for impersonation.
            tenant: Optional tenant identifier.
            timeout: Request timeout in seconds.
        """
        super().__init__(base_url, timeout=timeout)
        self.agent_token = agent_token
        self.user_token = user_token
        self.tenant = tenant

    def _get_headers(self) -> dict[str, str]:
        """Return authentication headers."""
        headers = {'Authorization': self.agent_token}
        if self.user_token:
            headers['SYNAPSE-User'] = f'Token {self.user_token}'
        if self.tenant:
            headers['SYNAPSE-Tenant'] = f'Token {self.tenant}'
        return headers

    async def health_check(self) -> dict:
        """Check agent health."""
        path = 'health/'
        return await self._get(path)


__all__ = ['AgentClient', 'AsyncAgentClient']
