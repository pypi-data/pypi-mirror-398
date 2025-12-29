---
id: storage
title: Storage Providers
sidebar_position: 2
---

# Storage Providers

Storage abstraction layer supporting multiple cloud providers with dict-based configuration.

## Installation

```bash
pip install synapse-sdk                    # Local storage only
pip install synapse-sdk[storage-s3]        # S3/MinIO support
pip install synapse-sdk[storage-gcs]       # Google Cloud Storage
pip install synapse-sdk[storage-sftp]      # SFTP support
pip install synapse-sdk[storage-all]       # All providers
```

---

## Available Providers

| Provider | Aliases | Description |
|----------|---------|-------------|
| `local` | `file_system` | Local filesystem |
| `s3` | `amazon_s3`, `minio` | S3-compatible storage |
| `gcs` | `gs`, `gcp` | Google Cloud Storage |
| `sftp` | - | SFTP servers |
| `http` | `https` | HTTP file servers (read-only) |

---

## Basic Usage

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
from pathlib import Path
url = storage.upload(Path('/tmp/file.txt'), 'uploads/file.txt')

# Check existence
exists = storage.exists('uploads/file.txt')

# Get pathlib object for path operations
path = get_pathlib(config, '/uploads')
for file in path.rglob('*.txt'):
    print(file)

# Get statistics
count = get_path_file_count(config, '/uploads')
size = get_path_total_size(config, '/uploads')
```

---

## Provider Configurations

### Local Filesystem

```python
config = {
    'provider': 'local',  # or 'file_system'
    'configuration': {
        'location': '/data'
    }
}
```

### S3 / MinIO

```python
config = {
    'provider': 's3',  # or 'amazon_s3', 'minio'
    'configuration': {
        'bucket_name': 'my-bucket',
        'access_key': 'AKIAIOSFODNN7EXAMPLE',
        'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        'region_name': 'us-east-1',
        'endpoint_url': 'http://minio:9000',  # Optional, for MinIO
    }
}
```

### Google Cloud Storage

```python
config = {
    'provider': 'gcs',  # or 'gs', 'gcp'
    'configuration': {
        'bucket_name': 'my-bucket',
        'credentials': '/path/to/service-account.json',
    }
}
```

### SFTP

```python
config = {
    'provider': 'sftp',
    'configuration': {
        'host': 'sftp.example.com',
        'username': 'user',
        'password': 'secret',  # or use private_key
        # 'private_key': '/path/to/id_rsa',
        'root_path': '/data',
    }
}
```

### HTTP (Read-only)

```python
config = {
    'provider': 'http',  # or 'https'
    'configuration': {
        'base_url': 'https://files.example.com/uploads/',
        'timeout': 60,
    }
}
```

---

## Storage Protocol

All storage providers implement the `StorageProtocol`:

```python
from typing import Protocol
from pathlib import Path

class StorageProtocol(Protocol):
    def upload(self, local_path: Path, remote_path: str) -> str: ...
    def download(self, remote_path: str, local_path: Path) -> Path: ...
    def exists(self, remote_path: str) -> bool: ...
    def delete(self, remote_path: str) -> None: ...
    def list_files(self, prefix: str = '') -> list[str]: ...
```

### Custom Storage Implementation

```python
from synapse_sdk.utils.storage import StorageProtocol
from pathlib import Path

class MyCustomStorage:
    """Implement StorageProtocol via duck typing."""

    def upload(self, local_path: Path, remote_path: str) -> str:
        # Upload implementation
        return f"custom://{remote_path}"

    def download(self, remote_path: str, local_path: Path) -> Path:
        # Download implementation
        return local_path

    def exists(self, remote_path: str) -> bool:
        # Check existence
        return True

    def delete(self, remote_path: str) -> None:
        # Delete implementation
        pass

    def list_files(self, prefix: str = '') -> list[str]:
        # List files
        return []
```

---

## Utility Functions

### get_storage()

Create storage instance from configuration.

```python
from synapse_sdk.utils.storage import get_storage

storage = get_storage({
    'provider': 's3',
    'configuration': {
        'bucket_name': 'my-bucket',
        # ...
    }
})
```

### get_pathlib()

Get a pathlib-like object for cloud storage navigation.

```python
from synapse_sdk.utils.storage import get_pathlib

path = get_pathlib(config, '/uploads')

# Iterate files
for file in path.rglob('*.json'):
    print(file.name)
```

### get_path_file_count()

Count files in a storage path.

```python
from synapse_sdk.utils.storage import get_path_file_count

count = get_path_file_count(config, '/uploads')
print(f"Files: {count}")
```

### get_path_total_size()

Get total size of files in a storage path.

```python
from synapse_sdk.utils.storage import get_path_total_size

size = get_path_total_size(config, '/uploads')
print(f"Total size: {size} bytes")
```

---

## Migration from v1

### Breaking Changes

| v1 | v2 |
|----|----|
| `get_storage('s3://bucket?key=value')` | Dict config only |
| `FileSystemStorage` class | `LocalStorage` class |
| `GCPStorage` class | `GCSStorage` class |
| Subclass `BaseStorage` | Implement `StorageProtocol` |

### Provider Aliases (Backwards Compatible)

| Alias | Maps To |
|-------|---------|
| `file_system` | `local` / `LocalStorage` |
| `gcp`, `gs` | `gcs` / `GCSStorage` |
| `amazon_s3`, `minio` | `s3` / `S3Storage` |

---

## Examples

### Upload with Progress

```python
from synapse_sdk.utils.storage import get_storage
from pathlib import Path

storage = get_storage({
    'provider': 's3',
    'configuration': {
        'bucket_name': 'ml-models',
        'access_key': '...',
        'secret_key': '...',
    }
})

# Upload model file
model_path = Path('/models/model.pt')
url = storage.upload(model_path, 'models/v1/model.pt')
print(f"Uploaded to: {url}")
```

### Download and Process

```python
from synapse_sdk.utils.storage import get_storage
from pathlib import Path
import tempfile

storage = get_storage({
    'provider': 'gcs',
    'configuration': {
        'bucket_name': 'datasets',
        'credentials': '/path/to/creds.json',
    }
})

# Download to temp file
with tempfile.NamedTemporaryFile(suffix='.csv') as tmp:
    local_path = storage.download('data/dataset.csv', Path(tmp.name))
    # Process the file
    import pandas as pd
    df = pd.read_csv(local_path)
```

### List and Filter Files

```python
from synapse_sdk.utils.storage import get_pathlib

path = get_pathlib(config, '/experiments')

# Find all checkpoints
checkpoints = list(path.rglob('*.ckpt'))
print(f"Found {len(checkpoints)} checkpoints")

# Filter by pattern
recent = [f for f in checkpoints if 'epoch_10' in f.name]
```

---

## See Also

- [Migration Guide](../../migration.md) - v1 to v2 migration
- [Installation](../../installation.md) - Storage extras installation
- [Network Utilities](./network.md) - Network streaming utilities
