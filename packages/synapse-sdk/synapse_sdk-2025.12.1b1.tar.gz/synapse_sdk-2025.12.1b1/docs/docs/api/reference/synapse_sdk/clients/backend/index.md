---
sidebar_label: backend
title: synapse_sdk.clients.backend
---

Backend API client for synapse-backend.

This module provides the BackendClient for interacting with the synapse-backend API.
It composes functionality from multiple mixins for different API domains.

**Example**:

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

## BackendClient Objects

```python
class BackendClient(AnnotationClientMixin, CoreClientMixin,
                    DataCollectionClientMixin, HITLClientMixin,
                    IntegrationClientMixin, MLClientMixin, BaseClient)
```

Synchronous client for synapse-backend API.

Composes functionality from multiple mixins:
- AnnotationClientMixin: Project and task operations
- CoreClientMixin: Chunked file upload
- DataCollectionClientMixin: Data collection management
- HITLClientMixin: Assignment operations
- IntegrationClientMixin: Plugin, job, and storage operations
- MLClientMixin: Model and ground truth operations

**Arguments**:

- `base_url` - Backend API base URL.
- `access_token` - API access token.
- `authorization_token` - Optional authorization token (legacy).
- `tenant` - Optional tenant identifier for multi-tenancy.
- `agent_token` - Optional agent token for agent-initiated requests.
- `timeout` - Request timeout dict with 'connect' and 'read' keys.
  

**Example**:

  >>> client = BackendClient(
  ...     'https://api.example.com',
  ...     access_token='abc123',
  ...     tenant='my-tenant',
  ... )
  >>> project = client.get_project(1)

#### close

```python
def close() -> None
```

Close the HTTP session.

Call this when done with the client to release resources.

