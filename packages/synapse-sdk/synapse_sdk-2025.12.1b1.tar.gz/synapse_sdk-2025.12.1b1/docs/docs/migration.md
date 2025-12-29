---
id: migration
title: Migration Guide (v1 to v2)
sidebar_position: 4
---

# Migration Guide (v1 to v2)

This guide covers the changes between synapse-sdk v1 and v2, including breaking changes that require code updates and new features.

## Breaking Changes

These changes **require code updates** when migrating from v1:

| v1 | v2 | Migration |
|----|----|-----------|
| `get_action_class(category, action)` | `get_action_method(config, action)` | Pass config dict instead of category string |
| `action_class.method` | `get_action_method(config, action)` | Method is now read from config, not class attribute |
| `@register_action` decorator | Removed | Define actions in `config.yaml` or use `PluginDiscovery.from_module()` |
| `_REGISTERED_ACTIONS` global | Removed | Use `PluginDiscovery` for action introspection |
| `get_storage('s3://...')` URL strings | Dict-only config | Use `get_storage({'provider': 's3', 'configuration': {...}})` |
| `from ... import FileSystemStorage` | `from ... import LocalStorage` | Class renamed |
| `from ... import GCPStorage` | `from ... import GCSStorage` | Class renamed |
| Subclassing `BaseStorage` ABC | Implement `StorageProtocol` | Use structural typing (duck typing) instead of inheritance |

## Non-Breaking Changes

These changes are **backwards compatible** - existing code continues to work:

| Feature | Notes |
|---------|-------|
| Provider alias `file_system` | Still works, maps to `LocalStorage` |
| Provider aliases `gcp`, `gs` | Still work, map to `GCSStorage` |
| `get_plugin_actions()` | Same API |
| `read_requirements()` | Same API |
| `get_pathlib()` | Same API |
| `get_path_file_count()` | Same API |
| `get_path_total_size()` | Same API |

---

## Plugin Utils

### Old (synapse-sdk v1)

```python
from synapse_sdk.plugins.utils import get_action_class, get_plugin_actions, read_requirements

# Get run method by loading the action class
action_method = get_action_class(config['category'], action).method
```

### New (synapse-sdk v2)

```python
from synapse_sdk.plugins.utils import get_action_method, get_plugin_actions, read_requirements

# Get run method directly from config (no class loading needed)
action_method = get_action_method(config, action)
```

---

## Plugin Types

### Old

```python
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.base import RunMethod
```

### New

```python
from synapse_sdk.plugins.enums import PluginCategory, RunMethod
```

---

## Plugin Discovery

**New feature** - Discover actions from config files or Python modules:

```python
from synapse_sdk.plugins.discovery import PluginDiscovery

# From config.yaml
discovery = PluginDiscovery.from_path('/path/to/plugin')
discovery.list_actions()  # ['train', 'inference', 'export']

# From Python module (auto-discovers @action decorators and BaseAction subclasses)
import plugin
discovery = PluginDiscovery.from_module(plugin)
```

---

## Storage Utils

### Old (synapse-sdk v1)

```python
from synapse_sdk.utils.storage import get_storage, get_pathlib

# URL string or dict config
storage = get_storage('s3://bucket?access_key=KEY&secret_key=SECRET')
# Or dict config
storage = get_storage({'provider': 'file_system', 'configuration': {'location': '/data'}})
```

### New (synapse-sdk v2)

```python
from synapse_sdk.utils.storage import get_storage, get_pathlib

# Dict-only config (URL string parsing removed)
storage = get_storage({'provider': 'local', 'configuration': {'location': '/data'}})

# S3 example
storage = get_storage({
    'provider': 's3',
    'configuration': {
        'bucket_name': 'my-bucket',
        'access_key': 'AKIAIOSFODNN7EXAMPLE',
        'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        'region_name': 'us-east-1',
    }
})
```

### Provider Renames

- `file_system` -> `local` (alias `file_system` still works)
- `FileSystemStorage` -> `LocalStorage`
- `GCPStorage` -> `GCSStorage`

---

## New Features in v2

| Feature | Description |
|---------|-------------|
| `PluginDiscovery` | Discover actions from config files or Python modules |
| `PluginDiscovery.from_module()` | Auto-discover `@action` decorators and `BaseAction` subclasses |
| `StorageProtocol` | Protocol-based interface for custom storage implementations |
| `HTTPStorage` provider | New provider for HTTP file servers |
| Plugin Upload utilities | `archive_and_upload()`, `build_and_upload()`, `download_and_upload()` |
| File utilities | `calculate_checksum()`, `create_archive()`, `create_archive_from_git()` |
| `AsyncAgentClient` | Async client with WebSocket/HTTP streaming for job logs |
| `tail_job_logs()` | Stream job logs with protocol auto-selection |

---

## See Also

- [Installation](./installation.md) - Installation options including storage extras
- [Storage Providers](./features/utils/storage.md) - Detailed storage configuration
- [AgentClient](./api/clients/agent.md) - Sync and async client usage
- [RayClient](./api/clients/ray.md) - Job log streaming
