---
sidebar_label: local
title: synapse_sdk.utils.storage.providers.local
---

Local filesystem storage provider.

## LocalStorage Objects

```python
class LocalStorage(_BaseStorageMixin)
```

Storage provider for local filesystem.

**Arguments**:

- `config` - Configuration dict with 'location' key.
  

**Example**:

  >>> storage = LocalStorage(\{'location': '/data'\})
  >>> storage.upload(Path('/tmp/file.txt'), 'uploads/file.txt')
  'file:///data/uploads/file.txt'

#### upload

```python
def upload(source: Path, target: str) -> str
```

Upload a file from source to target location.

**Arguments**:

- `source` - Path to source file.
- `target` - Target path relative to base path.
  

**Returns**:

  file:// URL of uploaded file.
  

**Raises**:

- `StorageNotFoundError` - If source file doesn't exist.
- `StorageUploadError` - If copy operation fails.

#### exists

```python
def exists(target: str) -> bool
```

Check if target file exists.

**Arguments**:

- `target` - Target path relative to base path.
  

**Returns**:

  True if file exists, False otherwise.

#### get\_url

```python
def get_url(target: str) -> str
```

Get file:// URL for target file.

**Arguments**:

- `target` - Target path relative to base path.
  

**Returns**:

  file:// URL string.

#### get\_pathlib

```python
def get_pathlib(path: str) -> Path
```

Get pathlib.Path object for the path.

**Arguments**:

- `path` - Path relative to storage root.
  

**Returns**:

  pathlib.Path object.

#### get\_path\_file\_count

```python
def get_path_file_count(pathlib_obj: Path) -> int
```

Get file count in the path.

**Arguments**:

- `pathlib_obj` - Path object from get_pathlib().
  

**Returns**:

  Number of files.

#### get\_path\_total\_size

```python
def get_path_total_size(pathlib_obj: Path) -> int
```

Get total size of files in the path.

**Arguments**:

- `pathlib_obj` - Path object from get_pathlib().
  

**Returns**:

  Total size in bytes.

