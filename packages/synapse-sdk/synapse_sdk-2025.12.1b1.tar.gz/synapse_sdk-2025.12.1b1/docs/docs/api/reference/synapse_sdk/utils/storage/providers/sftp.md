---
sidebar_label: sftp
title: synapse_sdk.utils.storage.providers.sftp
---

SFTP storage provider.

## SFTPStorage Objects

```python
class SFTPStorage(_BaseStorageMixin)
```

Storage provider for SFTP servers.

Requires: universal-pathlib[sftp] (pip install universal-pathlib[sftp])

Supports both password and private key authentication.

**Arguments**:

- `config` - Configuration dict with SFTP credentials.
  

**Example**:

  >>> # Password authentication
  >>> storage = SFTPStorage(\{
  ...     'host': 'sftp.example.com',
  ...     'username': 'user',
  ...     'password': 'secret',
  ...     'root_path': '/data',
  ... \})
  >>>
  >>> # Private key authentication
  >>> storage = SFTPStorage(\{
  ...     'host': 'sftp.example.com',
  ...     'username': 'user',
  ...     'private_key': '/path/to/id_rsa',
  ...     'root_path': '/data',
  ... \})

#### upload

```python
def upload(source: Path, target: str) -> str
```

Upload a file via SFTP.

**Arguments**:

- `source` - Local file path to upload.
- `target` - Target path on SFTP server.
  

**Returns**:

  sftp:// URL of uploaded file.

#### exists

```python
def exists(target: str) -> bool
```

Check if file exists on SFTP server.

**Arguments**:

- `target` - Path to check.
  

**Returns**:

  True if exists, False otherwise.

#### get\_url

```python
def get_url(target: str) -> str
```

Get sftp:// URL for target.

**Arguments**:

- `target` - Target path.
  

**Returns**:

  sftp:// URL string.

#### get\_pathlib

```python
def get_pathlib(path: str) -> UPath
```

Get UPath object for path.

**Arguments**:

- `path` - Path relative to root_path.
  

**Returns**:

  UPath object.

#### get\_path\_file\_count

```python
def get_path_file_count(pathlib_obj: UPath) -> int
```

Count files in SFTP path.

**Arguments**:

- `pathlib_obj` - UPath object from get_pathlib().
  

**Returns**:

  Number of files.

#### get\_path\_total\_size

```python
def get_path_total_size(pathlib_obj: UPath) -> int
```

Calculate total size of files in SFTP path.

**Arguments**:

- `pathlib_obj` - UPath object from get_pathlib().
  

**Returns**:

  Total size in bytes.

#### glob

```python
def glob(pattern: str) -> list[UPath]
```

Glob pattern matching on SFTP.

**Arguments**:

- `pattern` - Glob pattern.
  

**Returns**:

  List of matching UPath objects.

