---
sidebar_label: container
title: synapse_sdk.clients.agent.container
---

## ContainerClientMixin Objects

```python
class ContainerClientMixin()
```

Mixin for container management endpoints.

#### list\_docker\_containers

```python
def list_docker_containers() -> list[dict]
```

List all Docker containers on the host.

#### get\_docker\_container

```python
def get_docker_container(container_id: str) -> dict
```

Get a specific Docker container by ID.

#### create\_docker\_container

```python
def create_docker_container(plugin_release: str,
                            *,
                            params: dict[str, Any] | None = None,
                            envs: dict[str, str] | None = None,
                            metadata: dict[str, Any] | None = None,
                            labels: list[str] | None = None) -> dict
```

Build and run a Docker container for a plugin.

**Arguments**:

- `plugin_release` - Plugin identifier (e.g., "plugin_code@version").
- `params` - Parameters forwarded to the plugin.
- `envs` - Environment variables injected into the container.
- `metadata` - Additional metadata stored with the container record.
- `labels` - Container labels for display or filtering.

#### delete\_docker\_container

```python
def delete_docker_container(container_id: str) -> None
```

Stop and remove a Docker container.

#### list\_containers

```python
def list_containers(params: dict | None = None,
                    *,
                    list_all: bool = False) -> dict | tuple[Any, int]
```

List tracked containers from database.

#### get\_container

```python
def get_container(container_id: int) -> dict
```

Get a tracked container by database ID.

#### update\_container

```python
def update_container(container_id: int, *, status: str | None = None) -> dict
```

Update a tracked container's status.

#### delete\_container

```python
def delete_container(container_id: int) -> None
```

Delete a tracked container (stops Docker container too).

