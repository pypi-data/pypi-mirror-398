---
sidebar_label: plugin
title: synapse_sdk.clients.agent.plugin
---

## PluginClientMixin Objects

```python
class PluginClientMixin()
```

Mixin for plugin release endpoints.

#### list\_plugin\_releases

```python
def list_plugin_releases(params: dict | None = None,
                         *,
                         list_all: bool = False) -> dict | tuple[Any, int]
```

List all plugin releases.

#### get\_plugin\_release

```python
def get_plugin_release(lookup: str) -> dict
```

Get a plugin release by ID or code@version.

#### create\_plugin\_release

```python
def create_plugin_release(plugin: str, version: str) -> dict
```

Fetch and cache a plugin release.

#### delete\_plugin\_release

```python
def delete_plugin_release(lookup: str) -> None
```

Delete a plugin release.

#### run\_plugin\_release

```python
def run_plugin_release(lookup: str,
                       action: str,
                       params: dict[str, Any] | None = None,
                       *,
                       requirements: list[str] | None = None,
                       job_id: str | None = None) -> Any
```

Run a plugin release action.

**Arguments**:

- `lookup` - Plugin identifier (ID or "plugin@version").
- `action` - Action name to execute.
- `params` - Parameters to pass to the action.
- `requirements` - Additional pip requirements.
- `job_id` - Optional job ID for tracking.

#### run\_debug\_plugin\_release

```python
def run_debug_plugin_release(action: str,
                             params: dict[str, Any] | None = None,
                             *,
                             plugin_path: str | None = None,
                             config: dict[str, Any] | None = None,
                             modules: dict[str, str] | None = None,
                             requirements: list[str] | None = None,
                             job_id: str | None = None) -> Any
```

Run a plugin in debug mode (from source path).

**Arguments**:

- `action` - Action name to execute.
- `params` - Parameters to pass to the action.
- `plugin_path` - Path to the plugin source directory.
- `config` - Plugin configuration override.
- `modules` - Module source code mapping.
- `requirements` - Additional pip requirements.
- `job_id` - Optional job ID for tracking.

