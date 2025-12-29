---
id: gradio-playground
title: Synapse Playground (Container)
sidebar_position: 2
---

# Synapse Playground

Synapse Playground provides an interactive web UI environment where users can test and experience plugin functionality directly in their browser. The system launches plugins as isolated Docker containers that host Gradio applications, managed through the Agent's container API.

## Overview

### What is Synapse Playground?

Synapse Playground allows users to interact with plugin functionality through a web-based Gradio interface without installing the plugin or configuring a separate environment. The SDK provides `ContainerClientMixin` to communicate with the Agent, which handles all Docker container lifecycle management.

### Key Features

- **Agent-managed Containers**: The Agent handles Docker container creation, monitoring, and cleanup
- **Automatic Restart**: Existing containers with the same plugin and model are restarted instead of recreated
- **Dynamic Port Allocation**: Automatic port assignment prevents conflicts between concurrent containers
- **Plugin Archive Upload**: Support for uploading local plugin archives directly
- **Container Tracking**: Database-backed container state tracking for reliability

## Architecture

### System Components

```
SDK (ContainerClientMixin)
    |
    | HTTP API calls
    v
Agent (Container ViewSet)
    |
    | Docker SDK
    v
Docker Engine
    |
    v
Plugin Container (Gradio App on port 7860)
```

| Component | Role | Description |
|-----------|------|-------------|
| **SDK ContainerClientMixin** | Client Interface | Provides Python methods to interact with Agent's container API |
| **Agent Container ViewSet** | Container Management | Handles Docker operations: build, run, stop, remove |
| **Docker Engine** | Runtime | Executes isolated containers on the host |
| **Plugin Container** | Gradio Host | Runs the plugin's Gradio interface on port 7860 |

### Container Lifecycle

1. **Create Request**: SDK sends container creation request to Agent
2. **Duplicate Check**: Agent checks if container with same `plugin_release` + `model` exists
3. **Restart or Build**: If exists, restart; otherwise build new image from plugin
4. **Port Allocation**: Agent finds available port in range 7860-8860
5. **Container Run**: Docker container launched with port mapping and environment variables
6. **Endpoint Return**: Agent returns the Gradio endpoint URL to SDK

## SDK Usage

### ContainerClientMixin

The `ContainerClientMixin` is included in `AgentClient` and provides container management methods.

```python
from synapse_sdk.clients.agent import AgentClient

client = AgentClient(host="http://agent-url:8000", token="your-token")
```

### Creating a Container

#### Using Plugin Release String

```python
response = client.create_container(
    plugin_release="my-plugin@1.0.0",
    model=123,  # Optional: associates container with a model
    params={"input_size": 512},  # Passed to plugin as PLUGIN_PARAMS env var
    envs={"CUDA_VISIBLE_DEVICES": "0"},  # Additional environment variables
    labels=["gradio", "production"],  # Container labels for filtering
    metadata={"created_by": "admin"}  # Stored metadata
)

# Response
{
    'id': 'abc123def456...',
    'status': 'running',
    'name': 'quirky_einstein',
    'image': 'synapse-plugin-my-plugin-1.0.0',
    'endpoint': 'http://10.0.22.1:7860'
}
```

#### Using PluginRelease Object

```python
from synapse_sdk.plugins.models import PluginRelease

# PluginRelease with config containing action definitions
plugin_release = PluginRelease(config={
    'code': 'my-plugin',
    'version': '1.0.0',
    'actions': {
        'gradio': {'entrypoint': 'plugin.gradio_interface.app'}
    }
})

response = client.create_container(
    plugin_release=plugin_release,
    params={"batch_size": 32}
)
```

#### Uploading Plugin Archive

```python
# Upload local plugin archive and create container
response = client.create_container(
    plugin_release="my-plugin@1.0.0",
    plugin_file="/path/to/plugin-release.zip"
)
```

### Container Restart Behavior

When a container with the same `plugin_release` and `model` already exists, the Agent restarts it instead of creating a new one:

```python
# First call - creates new container
response1 = client.create_container("my-plugin@1.0.0", model=123)
# {'id': 'abc...', 'status': 'running', 'endpoint': 'http://host:7860'}

# Second call with same plugin_release + model - restarts existing
response2 = client.create_container("my-plugin@1.0.0", model=123)
# {'id': 'abc...', 'status': 'running', 'endpoint': 'http://host:7860', 'restarted': True}
```

### Listing Containers

```python
# List all containers
result = client.list_containers()
# {'results': [...], 'count': 5}

# Filter by status
result = client.list_containers(params={"status": "running"})

# Get all containers with pagination handling
containers, count = client.list_containers(list_all=True)
for container in containers:
    print(f"{container['name']}: {container['status']}")
```

### Getting Container Details

```python
container = client.get_container("abc123def456")
# {
#     'id': 'abc123def456...',
#     'name': 'quirky_einstein',
#     'status': 'running',
#     'image': 'synapse-plugin-my-plugin-1.0.0',
#     'attrs': {...}  # Full Docker container attributes
# }
```

### Deleting a Container

```python
client.delete_container("abc123def456")
# Stops and removes the container
```

### Health Check

```python
# Check if Docker socket is accessible
health = client.health_check()
```

## Agent-Side Implementation

### How the Agent Handles Containers

The Agent's `ContainerViewSet` manages the full Docker lifecycle:

1. **Image Building**: Creates Dockerfile, copies plugin files, installs requirements
2. **Port Management**: Scans database and running containers to find available ports
3. **Container Tracking**: Stores container metadata in database for state management
4. **Restart Logic**: Checks for existing containers before creating new ones

### Container Database Model

The Agent tracks containers with these fields:

| Field | Description |
|-------|-------------|
| `container_id` | Docker container ID |
| `plugin_release` | Plugin identifier (e.g., "my-plugin@1.0.0") |
| `model` | Associated model ID (nullable) |
| `host_port` | Allocated host port |
| `status` | Container status |
| `created_at` / `updated_at` | Timestamps |

### Unique Constraint

Containers are uniquely identified by `(plugin_release, model)` combination, enabling the restart-instead-of-recreate behavior.

## Plugin Requirements

### Plugin Structure for Playground

Plugins must include a Gradio interface file:

```
my-plugin/
├── config.yaml
├── plugin/
│   ├── __init__.py
│   ├── gradio_interface.py    # Required: Gradio app definition
│   └── ...
└── requirements.txt           # Dependencies (gradio included automatically)
```

### gradio_interface.py Example

```python
import gradio as gr

def predict(image):
    # Your inference logic
    result = model.predict(image)
    return result

demo = gr.Interface(
    fn=predict,
    inputs=gr.Image(type="pil"),
    outputs=gr.Label(),
    title="My Plugin Playground"
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

### config.yaml with Gradio Action

```yaml
code: my-plugin
name: My Plugin
version: 1.0.0
category: neural_net

actions:
  gradio:
    entrypoint: plugin.gradio_interface.app
    method: job
```

## Environment Variables

Containers receive these environment variables:

| Variable | Description |
|----------|-------------|
| `PLUGIN_PARAMS` | JSON-encoded params from `create_container()` |
| Custom `envs` | Any additional variables passed to `create_container()` |

Access in your Gradio app:

```python
import os
import json

params = json.loads(os.environ.get('PLUGIN_PARAMS', '{}'))
input_size = params.get('input_size', 512)
```

## Docker Requirements

### Host Requirements

- Docker Engine running on the Agent host
- `/var/run/docker.sock` mounted (for containerized Agents)
- Port range 7860-8860 available

### Base Image

The Agent uses a configurable base image:

```python
base_image = config.GRADIO_CONTAINER_BASE_IMAGE
```

### Generated Dockerfile

The Agent generates a Dockerfile for each plugin:

```dockerfile
FROM {base_image}

COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

## API Reference

### create_container()

```python
def create_container(
    plugin_release: Optional[Union[str, PluginRelease]] = None,
    *,
    model: Optional[int] = None,
    params: Optional[Dict[str, Any]] = None,
    envs: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    labels: Optional[Iterable[str]] = None,
    plugin_file: Optional[Union[str, Path]] = None,
) -> dict
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `plugin_release` | str or PluginRelease | Plugin identifier: `"code@version"` string or PluginRelease object |
| `model` | int | Optional model ID for container uniqueness |
| `params` | dict | Parameters passed as `PLUGIN_PARAMS` environment variable |
| `envs` | dict | Additional environment variables |
| `metadata` | dict | Metadata stored with container record |
| `labels` | list[str] | Container labels for display/filtering |
| `plugin_file` | str or Path | Local plugin archive to upload |

**Returns**: Container info dict with `id`, `status`, `name`, `image`, `endpoint`, and optionally `restarted`

**Raises**:
- `ValueError`: Neither `plugin_release` nor `plugin_file` provided
- `TypeError`: Invalid `plugin_release` type
- `FileNotFoundError`: `plugin_file` path doesn't exist

### list_containers()

```python
def list_containers(
    params: Optional[Dict[str, Any]] = None,
    *,
    list_all: bool = False
) -> Union[dict, tuple]
```

### get_container()

```python
def get_container(container_id: Union[int, str]) -> dict
```

### delete_container()

```python
def delete_container(container_id: Union[int, str]) -> None
```

### health_check()

```python
def health_check() -> dict
```

## Related Documentation

- [Plugin System Overview](../../plugins.md)
- [Agent Client API](../../../api/clients/agent.md)
