# Synapse SDK v2

> To be merged into [synapse-sdk](https://github.com/datamaker-kr/synapse-sdk) after development

## Table of Contents

- [Installation](#installation)
- [Migration Guide](#migration-guide)
  - [Plugin Utils](#plugin-utils)
  - [Plugin Types](#plugin-types)
  - [Plugin Discovery](#plugin-discovery)
  - [Storage Utils](#storage-utils)
- [API Reference](#api-reference)
  - [get_plugin_actions](#get_plugin_actions)
  - [get_action_method](#get_action_method)
  - [get_action_config](#get_action_config)
  - [read_requirements](#read_requirements)
  - [run_plugin](#run_plugin)
  - [PluginDiscovery](#plugindiscovery)
  - [Storage](#storage)
- [Action Base Classes](#action-base-classes)
  - [BaseTrainAction](#basetrainaction)
  - [BaseExportAction](#baseexportaction)
  - [BaseUploadAction](#baseuploadaction)
- [Agent Client Streaming](#agent-client-streaming)

---

## Installation

```bash
pip install synapse-sdk
```

---

## Migration Guide

### Plugin Utils

**Old (synapse-sdk v1):**
```python
from synapse_sdk.plugins.utils import get_action_class, get_plugin_actions, read_requirements

# Get run method by loading the action class
action_method = get_action_class(config['category'], action).method
```

**New (synapse-sdk v2):**
```python
from synapse_sdk.plugins.utils import get_action_method, get_plugin_actions, read_requirements

# Get run method directly from config (no class loading needed)
action_method = get_action_method(config, action)
```

### Plugin Types

**Old:**
```python
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.base import RunMethod
```

**New:**
```python
from synapse_sdk.plugins.enums import PluginCategory, RunMethod
```

**Provider renames:**
- `file_system` -> `local` (alias `file_system` still works)
- `FileSystemStorage` -> `LocalStorage`
- `GCPStorage` -> `GCSStorage`

---

## API Reference

### get_plugin_actions

Extract action names from plugin configuration.

```python
from synapse_sdk.plugins.utils import get_plugin_actions

# From dict
actions = get_plugin_actions({'actions': {'train': {}, 'export': {}}})
# Returns: ['train', 'export']

# From PluginConfig
actions = get_plugin_actions(plugin_config)

# From path
actions = get_plugin_actions('/path/to/plugin')  # reads config.yaml
```

### get_action_method

Get the execution method (job/task/serve_application) for an action.

```python
from synapse_sdk.plugins.utils import get_action_method
from synapse_sdk.plugins.enums import RunMethod

method = get_action_method(config, 'train')
if method == RunMethod.JOB:
    # Create job record, run async
    pass
elif method == RunMethod.TASK:
    # Run as Ray task
    pass
```

### get_action_config

Get full configuration for a specific action.

```python
from synapse_sdk.plugins.utils import get_action_config

config = get_action_config(plugin_config, 'train')
# Returns: {'name': 'train', 'method': 'job', 'entrypoint': '...', ...}
```

### read_requirements

Parse a requirements.txt file.

```python
from synapse_sdk.plugins.utils import read_requirements

reqs = read_requirements('/path/to/requirements.txt')
# Returns: ['numpy>=1.20', 'torch>=2.0'] or None if file doesn't exist
```

### run_plugin

Execute plugin actions with automatic discovery.

```python
from synapse_sdk.plugins.runner import run_plugin

# Auto-discover from Python module path
result = run_plugin('plugins.yolov8', 'train', {'epochs': 10})

# Auto-discover from config.yaml path
result = run_plugin('/path/to/plugin', 'train', {'epochs': 10})

# Execution modes
result = run_plugin('plugin', 'train', params, mode='local')  # Current process (default)
result = run_plugin('plugin', 'train', params, mode='task')   # Ray Actor (fast startup)
job_id = run_plugin('plugin', 'train', params, mode='job')    # Ray Job API (async)

# Explicit action class (skips discovery)
result = run_plugin('yolov8', 'train', {'epochs': 10}, action_cls=TrainAction)
```

**Option 1: Define actions with `@action` decorator (recommended for Python modules):**

```python
# plugins/yolov8.py
from synapse_sdk.plugins.decorators import action
from pydantic import BaseModel

class TrainParams(BaseModel):
    epochs: int = 10
    batch_size: int = 32

@action(name='train', description='Train YOLOv8 model', params=TrainParams)
def train(params: TrainParams, ctx):
    # Training logic here
    return {'accuracy': 0.95}

@action(name='infer')
def infer(params, ctx):
    # Inference logic
    return {'predictions': [...]}

# Run it:
# run_plugin('plugins.yolov8', 'train', {'epochs': 20})
```

**Option 2: Define actions with `BaseAction` class:**

```python
# plugins/yolov8.py
from synapse_sdk.plugins.action import BaseAction
from pydantic import BaseModel

class TrainParams(BaseModel):
    epochs: int = 10

class TrainAction(BaseAction[TrainParams]):
    action_name = 'train'
    params_model = TrainParams

    def execute(self):
        # self.params contains validated TrainParams
        # self.ctx contains RuntimeContext (logger, env, job_id)
        return {'accuracy': 0.95}

# Run it:
# run_plugin('plugins.yolov8', 'train', {'epochs': 20})
```

**Option 3: Define actions with `config.yaml` (recommended for packaged plugins):**

```yaml
# plugin/config.yaml
name: YOLOv8 Plugin
code: yolov8
version: 1.0.0
category: neural_net
description: YOLOv8 object detection plugin

actions:
  train:
    entrypoint: plugin.train.TrainAction   # or plugin.train:TrainAction
    method: job
    description: Train YOLOv8 model

  infer:
    entrypoint: plugin.inference.InferAction
    method: task
    description: Run inference

  export:
    entrypoint: plugin.export.export_model
    method: task
```

```python
# Run from config path:
run_plugin('/path/to/plugin', 'train', {'epochs': 20})
```

**Entrypoint formats:**
- Dot notation: `plugin.train.TrainAction` (module.submodule.ClassName)
- Colon notation: `plugin.train:TrainAction` (module.submodule:ClassName)

### PluginDiscovery

Comprehensive plugin introspection.

```python
from synapse_sdk.plugins.discovery import PluginDiscovery

# Load from config.yaml
discovery = PluginDiscovery.from_path('/path/to/plugin')

# Or introspect a Python module
discovery = PluginDiscovery.from_module(my_module)

# Available methods
discovery.list_actions()           # ['train', 'export']
discovery.has_action('train')      # True
discovery.get_action_method('train')  # RunMethod.JOB
discovery.get_action_config('train')  # ActionConfig instance
discovery.get_action_class('train')   # Loads class from entrypoint
```

### Storage

Storage utilities for working with different storage backends.

**Installation for cloud providers:**
```bash
pip install synapse-sdk[storage-s3]    # S3/MinIO
pip install synapse-sdk[storage-gcs]   # Google Cloud Storage
pip install synapse-sdk[storage-sftp]  # SFTP
pip install synapse-sdk[storage-all]   # All cloud providers
```

**Available providers:**
- `local` / `file_system` - Local filesystem
- `s3` / `amazon_s3` / `minio` - S3-compatible storage
- `gcs` / `gs` / `gcp` - Google Cloud Storage
- `sftp` - SFTP servers
- `http` / `https` - HTTP file servers

**Basic usage:**
```python
from synapse_sdk.utils.storage import (
    get_storage,
    get_pathlib,
    get_path_file_count,
    get_path_total_size,
)

# Get storage instance
storage = get_storage({
    'provider': 'local',
    'configuration': {'location': '/data'}
})

# Upload a file
url = storage.upload(Path('/tmp/file.txt'), 'uploads/file.txt')

# Check existence
exists = storage.exists('uploads/file.txt')

# Get pathlib object for path operations
path = get_pathlib(config, '/uploads')
for file in path.rglob('*.txt'):
    print(file)

# Get file count and total size
count = get_path_file_count(config, '/uploads')
size = get_path_total_size(config, '/uploads')
```

**Provider configurations:**

```python
# Local filesystem
{'provider': 'local', 'configuration': {'location': '/data'}}

# S3/MinIO
{'provider': 's3', 'configuration': {
    'bucket_name': 'my-bucket',
    'access_key': 'AKIAIOSFODNN7EXAMPLE',
    'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    'region_name': 'us-east-1',
    'endpoint_url': 'http://minio:9000',  # optional, for MinIO
}}

# Google Cloud Storage
{'provider': 'gcs', 'configuration': {
    'bucket_name': 'my-bucket',
    'credentials': '/path/to/service-account.json',
}}

# SFTP
{'provider': 'sftp', 'configuration': {
    'host': 'sftp.example.com',
    'username': 'user',
    'password': 'secret',  # or 'private_key': '/path/to/id_rsa'
    'root_path': '/data',
}}

# HTTP
{'provider': 'http', 'configuration': {
    'base_url': 'https://files.example.com/uploads/',
    'timeout': 60,
}}
```

---

## Changes from v1

### Breaking Changes

These changes **require code updates** when migrating from v1:

| v1 | v2 | Migration |
|----|----|----|
| `get_action_class(category, action)` | `get_action_method(config, action)` | Pass config dict instead of category string |
| `action_class.method` | `get_action_method(config, action)` | Method is now read from config, not class attribute |
| `@register_action` decorator | Removed | Define actions in `config.yaml` or use `PluginDiscovery.from_module()` |
| `_REGISTERED_ACTIONS` global | Removed | Use `PluginDiscovery` for action introspection |
| `get_storage('s3://...')` URL strings | Dict-only config | Use `get_storage({'provider': 's3', 'configuration': {...}})` |
| `from ... import FileSystemStorage` | `from ... import LocalStorage` | Class renamed |
| `from ... import GCPStorage` | `from ... import GCSStorage` | Class renamed |
| Subclassing `BaseStorage` ABC | Implement `StorageProtocol` | Use structural typing (duck typing) instead of inheritance |

### Non-Breaking Changes

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

### New Features in v2

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
| `BaseTrainAction` | Training base class with dataset/model helpers |
| `BaseExportAction` | Export base class with filtered results helper |
| `BaseUploadAction` | Upload base class with step-based workflow and rollback |

---

## Action Base Classes

Category-specific base classes that provide helper methods and progress tracking for common workflows.

### BaseTrainAction

For training workflows with dataset/model helpers.

```python
from synapse_sdk.plugins import BaseTrainAction, TrainProgressCategories
from pydantic import BaseModel

class TrainParams(BaseModel):
    dataset_id: int
    epochs: int = 10

class MyTrainAction(BaseTrainAction[TrainParams]):
    action_name = 'train'
    params_model = TrainParams

    def execute(self) -> dict:
        # Helper methods use self.client (from RuntimeContext)
        dataset = self.get_dataset()  # Uses params.dataset_id
        self.set_progress(1, 3, self.progress.DATASET)

        model_path = self._train(dataset)
        self.set_progress(2, 3, self.progress.TRAIN)

        model = self.create_model(model_path, name='my-model')
        self.set_progress(3, 3, self.progress.MODEL_UPLOAD)

        return {'model_id': model['id']}
```

**Progress categories:** `DATASET`, `TRAIN`, `MODEL_UPLOAD`

**Helper methods:**
- `get_dataset()` - Fetch dataset using `params.dataset_id`
- `create_model(path, **kwargs)` - Upload trained model
- `get_model(model_id)` - Retrieve existing model

### BaseExportAction

For export workflows with filtered data retrieval.

```python
from typing import Any

from synapse_sdk.plugins import BaseExportAction, ExportProgressCategories
from pydantic import BaseModel

class ExportParams(BaseModel):
    filter: dict
    output_path: str

class MyExportAction(BaseExportAction[ExportParams]):
    action_name = 'export'
    params_model = ExportParams

    def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
        # Override for your target type
        return self.client.get_assignments(filters)

    def execute(self) -> dict:
        results, count = self.get_filtered_results(self.params.filter)
        self.set_progress(0, count, self.progress.DATASET_CONVERSION)

        for i, item in enumerate(results, 1):
            # Process and export item
            self.set_progress(i, count, self.progress.DATASET_CONVERSION)

        return {'exported': count}
```