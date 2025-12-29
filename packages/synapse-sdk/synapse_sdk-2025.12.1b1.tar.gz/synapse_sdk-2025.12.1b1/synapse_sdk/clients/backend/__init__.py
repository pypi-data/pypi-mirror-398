"""Backend API client for synapse-backend.

This module provides the BackendClient for interacting with the synapse-backend API.
It composes functionality from multiple mixins for different API domains.

Example:
    >>> from synapse_sdk.clients.backend import BackendClient
    >>>
    >>> client = BackendClient(
    ...     'https://api.example.com',
    ...     access_token='your_token',
    ...     tenant='your_tenant',
    ... )
    >>>
    >>> # Get a project
    >>> project = client.get_project(123)
    >>>
    >>> # Upload data collection
    >>> client.upload_data_collection(456, data, project_id=789)
"""

from __future__ import annotations

from synapse_sdk.clients.backend.annotation import AnnotationClientMixin
from synapse_sdk.clients.backend.core import CoreClientMixin
from synapse_sdk.clients.backend.data_collection import DataCollectionClientMixin
from synapse_sdk.clients.backend.hitl import HITLClientMixin
from synapse_sdk.clients.backend.integration import IntegrationClientMixin
from synapse_sdk.clients.backend.ml import MLClientMixin
from synapse_sdk.clients.base import BaseClient


class BackendClient(
    AnnotationClientMixin,
    CoreClientMixin,
    DataCollectionClientMixin,
    HITLClientMixin,
    IntegrationClientMixin,
    MLClientMixin,
    BaseClient,
):
    """Synchronous client for synapse-backend API.

    Composes functionality from multiple mixins:
    - AnnotationClientMixin: Project and task operations
    - CoreClientMixin: Chunked file upload
    - DataCollectionClientMixin: Data collection management
    - HITLClientMixin: Assignment operations
    - IntegrationClientMixin: Plugin, job, and storage operations
    - MLClientMixin: Model and ground truth operations

    Args:
        base_url: Backend API base URL.
        access_token: API access token.
        authorization_token: Optional authorization token (legacy).
        tenant: Optional tenant identifier for multi-tenancy.
        agent_token: Optional agent token for agent-initiated requests.
        timeout: Request timeout dict with 'connect' and 'read' keys.

    Example:
        >>> client = BackendClient(
        ...     'https://api.example.com',
        ...     access_token='abc123',
        ...     tenant='my-tenant',
        ... )
        >>> project = client.get_project(1)
    """

    name = 'Backend'

    def __init__(
        self,
        base_url: str,
        access_token: str | None = None,
        *,
        authorization_token: str | None = None,
        tenant: str | None = None,
        agent_token: str | None = None,
        timeout: dict[str, int] | None = None,
    ):
        """Initialize the backend client.

        Args:
            base_url: Backend API base URL.
            access_token: API access token for authentication.
            authorization_token: Legacy auth token (deprecated, use access_token).
            tenant: Tenant code for multi-tenant deployments.
            agent_token: Agent token for agent-initiated requests.
            timeout: Request timeout configuration.
        """
        super().__init__(base_url, timeout=timeout)
        self.access_token = access_token
        self.authorization_token = authorization_token
        self.tenant = tenant
        self.agent_token = agent_token

    def _get_headers(self) -> dict[str, str]:
        """Return authentication headers.

        Multiple authentication methods are supported:
        - Synapse-Access-Token: Primary authentication
        - Authorization: Legacy token authentication
        - Synapse-Tenant: Multi-tenant identifier
        - SYNAPSE-Agent: Agent-initiated request identifier
        """
        headers: dict[str, str] = {}

        if self.access_token:
            headers['Synapse-Access-Token'] = f'Token {self.access_token}'

        if self.authorization_token:
            headers['Authorization'] = f'Token {self.authorization_token}'

        if self.tenant:
            headers['Synapse-Tenant'] = f'Token {self.tenant}'

        if self.agent_token:
            headers['SYNAPSE-Agent'] = f'Token {self.agent_token}'

        return headers

    def close(self) -> None:
        """Close the HTTP session.

        Call this when done with the client to release resources.
        """
        if self._session is not None:
            self._session.close()
            self._session = None

    def __enter__(self) -> BackendClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit - closes session."""
        self.close()


# Re-export models for convenience
from synapse_sdk.clients.backend.models import (  # noqa: E402
    Agent,
    JobStatus,
    Storage,
    StorageCategory,
    StorageProvider,
    UpdateJobRequest,
)

__all__ = [
    # Client
    'BackendClient',
    # Models
    'Agent',
    'JobStatus',
    'Storage',
    'StorageCategory',
    'StorageProvider',
    'UpdateJobRequest',
]
