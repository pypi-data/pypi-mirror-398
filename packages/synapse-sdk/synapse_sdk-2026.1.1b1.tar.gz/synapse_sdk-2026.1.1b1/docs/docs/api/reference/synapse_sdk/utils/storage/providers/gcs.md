---
sidebar_label: gcs
title: synapse_sdk.utils.storage.providers.gcs
---

Google Cloud Storage provider.

## GCSStorage Objects

```python
class GCSStorage(_BaseStorageMixin)
```

Storage provider for Google Cloud Storage.

Requires: universal-pathlib[gcs] (pip install universal-pathlib[gcs])

**Arguments**:

- `config` - Configuration dict with GCS credentials.
  

**Example**:

  >>> storage = GCSStorage(\{
  ...     'bucket_name': 'my-bucket',
  ...     'credentials': '/path/to/service-account.json',
  ... \})
  >>> storage.upload(Path('/tmp/file.txt'), 'data/file.txt')
  'gs://my-bucket/data/file.txt'

#### upload

```python
def upload(source: Path, target: str) -> str
```

Upload a file to GCS.

**Arguments**:

- `source` - Local file path to upload.
- `target` - Target path in GCS bucket.
  

**Returns**:

  gs:// URL of uploaded file.

#### exists

```python
def exists(target: str) -> bool
```

Check if file exists in GCS.

**Arguments**:

- `target` - Path to check.
  

**Returns**:

  True if exists, False otherwise.

#### get\_url

```python
def get_url(target: str) -> str
```

Get gs:// URL for target.

**Arguments**:

- `target` - Target path.
  

**Returns**:

  gs:// URL string.

#### get\_pathlib

```python
def get_pathlib(path: str) -> UPath
```

Get UPath object for path.

**Arguments**:

- `path` - Path relative to bucket root.
  

**Returns**:

  UPath object.

#### get\_path\_file\_count

```python
def get_path_file_count(pathlib_obj: UPath) -> int
```

Count files in GCS path.

**Arguments**:

- `pathlib_obj` - UPath object from get_pathlib().
  

**Returns**:

  Number of files.

#### get\_path\_total\_size

```python
def get_path_total_size(pathlib_obj: UPath) -> int
```

Calculate total size of files in GCS path.

**Arguments**:

- `pathlib_obj` - UPath object from get_pathlib().
  

**Returns**:

  Total size in bytes.

#### glob

```python
def glob(pattern: str) -> list[UPath]
```

Glob pattern matching in GCS.

**Arguments**:

- `pattern` - Glob pattern.
  

**Returns**:

  List of matching UPath objects.

