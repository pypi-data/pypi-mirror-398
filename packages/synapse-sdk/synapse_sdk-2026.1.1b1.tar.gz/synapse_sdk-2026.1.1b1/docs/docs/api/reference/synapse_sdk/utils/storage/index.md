---
sidebar_label: storage
title: synapse_sdk.utils.storage
---

Storage utilities module.

This module provides a unified interface for working with different storage
backends including local filesystem, S3, GCS, SFTP, and HTTP.

**Example**:

  >>> from synapse_sdk.utils.storage import get_storage, get_pathlib
  >>>
  >>> # Local filesystem
  >>> storage = get_storage(\{
  ...     'provider': 'local',
  ...     'configuration': \{'location': '/data'\}
  ... \})
  >>>
  >>> # S3-compatible storage
  >>> storage = get_storage(\{
  ...     'provider': 's3',
  ...     'configuration': \{
  ...         'bucket_name': 'my-bucket',
  ...         'access_key': 'AKIAIOSFODNN7EXAMPLE',
  ...         'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
  ...     \}
  ... \})
  >>>
  >>> # Get pathlib object for path operations
  >>> path = get_pathlib(storage_config, '/uploads')
  >>> for file in path.rglob('*'):
  ...     print(file)

## StorageProtocol Objects

```python
@runtime_checkable
class StorageProtocol(Protocol)
```

Protocol defining the storage provider interface.

All storage providers must implement these methods to be compatible
with the storage system. Uses structural typing (duck typing) rather
than inheritance, allowing third-party implementations.

**Example**:

  >>> class CustomStorage:
  ...     def upload(self, source: Path, target: str) -> str: ...
  ...     def exists(self, target: str) -> bool: ...
  ...     def get_url(self, target: str) -> str: ...
  ...     def get_pathlib(self, path: str) -> Path: ...
  ...     def get_path_file_count(self, pathlib_obj: Path) -> int: ...
  ...     def get_path_total_size(self, pathlib_obj: Path) -> int: ...
  >>>
  >>> isinstance(CustomStorage(), StorageProtocol)  # True

#### upload

```python
def upload(source: Path, target: str) -> str
```

Upload a file from local source to target path.

**Arguments**:

- `source` - Local file path to upload.
- `target` - Target path in storage (relative to storage root).
  

**Returns**:

  URL or identifier of the uploaded file.
  

**Raises**:

- `StorageNotFoundError` - If source file doesn't exist.
- `StorageUploadError` - If upload fails.

#### exists

```python
def exists(target: str) -> bool
```

Check if a file or directory exists at target path.

**Arguments**:

- `target` - Path to check (relative to storage root).
  

**Returns**:

  True if path exists, False otherwise.

#### get\_url

```python
def get_url(target: str) -> str
```

Get the URL for accessing a file.

**Arguments**:

- `target` - Path to file (relative to storage root).
  

**Returns**:

  URL string for accessing the file.

#### get\_pathlib

```python
def get_pathlib(path: str) -> Path | UPath
```

Get a pathlib-compatible object for the path.

**Arguments**:

- `path` - Path relative to storage root.
  

**Returns**:

  Path object (local) or UPath object (cloud/remote).

#### get\_path\_file\_count

```python
def get_path_file_count(pathlib_obj: Path | UPath) -> int
```

Count files recursively in the given path.

**Arguments**:

- `pathlib_obj` - Path object from get_pathlib().
  

**Returns**:

  Number of files (excluding directories).

#### get\_path\_total\_size

```python
def get_path_total_size(pathlib_obj: Path | UPath) -> int
```

Calculate total size of files recursively.

**Arguments**:

- `pathlib_obj` - Path object from get_pathlib().
  

**Returns**:

  Total size in bytes.

#### get\_storage

```python
def get_storage(connection_param: dict[str, Any]) -> StorageProtocol
```

Get a storage provider instance from configuration.

**Arguments**:

- `connection_param` - Dictionary with 'provider' and 'configuration' keys.
- `Example` - \{'provider': 's3', 'configuration': \{'bucket_name': '...'\}\}
  

**Returns**:

  Storage provider instance implementing StorageProtocol.
  

**Raises**:

- `StorageConfigError` - If configuration is invalid.
- `StorageProviderNotFoundError` - If provider is not registered.
  

**Example**:

  >>> config = \{
  ...     'provider': 's3',
  ...     'configuration': \{
  ...         'bucket_name': 'my-bucket',
  ...         'access_key': 'AKIAIOSFODNN7EXAMPLE',
  ...         'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
  ...     \}
  ... \}
  >>> storage = get_storage(config)

#### get\_pathlib

```python
def get_pathlib(storage_config: dict[str, Any],
                path_root: str) -> Path | UPath
```

Get pathlib object for a path in storage.

Convenience function that combines get_storage() and get_pathlib().

**Arguments**:

- `storage_config` - Storage configuration dict.
- `path_root` - Root path to get pathlib for.
  

**Returns**:

  Path or UPath object.
  

**Example**:

  >>> config = \{'provider': 'local', 'configuration': \{'location': '/data'\}\}
  >>> path = get_pathlib(config, '/uploads')
  >>> path.exists()
  True

#### get\_path\_file\_count

```python
def get_path_file_count(storage_config: dict[str, Any], path_root: str) -> int
```

Get file count in a storage path.

**Arguments**:

- `storage_config` - Storage configuration dict.
- `path_root` - Root path to count files in.
  

**Returns**:

  Number of files.
  

**Example**:

  >>> config = \{'provider': 'local', 'configuration': \{'location': '/data'\}\}
  >>> count = get_path_file_count(config, '/uploads')
  >>> print(f'Found \{count\} files')

#### get\_path\_total\_size

```python
def get_path_total_size(storage_config: dict[str, Any], path_root: str) -> int
```

Get total size of files in a storage path.

**Arguments**:

- `storage_config` - Storage configuration dict.
- `path_root` - Root path to calculate size for.
  

**Returns**:

  Total size in bytes.
  

**Example**:

  >>> config = \{'provider': 'local', 'configuration': \{'location': '/data'\}\}
  >>> size = get_path_total_size(config, '/uploads')
  >>> print(f'Total size: \{size / 1024 / 1024:.2f\} MB')

