---
sidebar_label: agent
title: synapse_sdk.clients.agent
---

## AgentClient Objects

```python
class AgentClient(ContainerClientMixin, PluginClientMixin, RayClientMixin,
                  BaseClient)
```

Sync client for synapse-agent API.

#### health\_check

```python
def health_check() -> dict
```

Check agent health.

## AsyncAgentClient Objects

```python
class AsyncAgentClient(AsyncRayClientMixin, AsyncBaseClient)
```

Async client for synapse-agent API.

Provides async/await interface for all agent operations including
WebSocket and HTTP streaming for job log tailing.

**Example**:

  >>> async with AsyncAgentClient(base_url, agent_token) as client:
  ...     jobs = await client.list_jobs()
  ...     async for line in client.tail_job_logs('job-123'):
  ...         print(line)

#### health\_check

```python
async def health_check() -> dict
```

Check agent health.

