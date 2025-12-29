---
sidebar_label: data_collection
title: synapse_sdk.clients.backend.data_collection
---

Data collection client mixin for dataset management.

## DataCollectionClientMixin Objects

```python
class DataCollectionClientMixin()
```

Mixin for data collection API endpoints.

Provides methods for managing data collections, files, and units.

#### list\_data\_collections

```python
def list_data_collections() -> dict[str, Any]
```

List all data collections.

**Returns**:

  Paginated list of data collections.

#### get\_data\_collection

```python
def get_data_collection(collection_id: int) -> dict[str, Any]
```

Get data collection details by ID.

Automatically expands file specifications.

**Arguments**:

- `collection_id` - Data collection ID.
  

**Returns**:

  Collection data including file specifications.

#### create\_data\_file

```python
def create_data_file(file_path: str | Path,
                     *,
                     use_chunked_upload: bool | None = None) -> dict[str, Any]
```

Upload a data file.

Automatically uses chunked upload for files >50MB unless
explicitly specified.

**Arguments**:

- `file_path` - Path to the file to upload.
- `use_chunked_upload` - Force chunked (True) or direct (False) upload.
  None = auto-detect based on file size.
  

**Returns**:

  File data with ID, checksum, and size.
  

**Raises**:

- `FileNotFoundError` - If file doesn't exist.

#### get\_data\_unit

```python
def get_data_unit(unit_id: int,
                  *,
                  params: dict[str, Any] | None = None) -> dict[str, Any]
```

Get data unit details by ID.

**Arguments**:

- `unit_id` - Data unit ID.
- `params` - Optional query parameters.
  

**Returns**:

  Data unit with files and metadata.

#### create\_data\_units

```python
def create_data_units(
        data: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]
```

Create data unit bindings.

Links uploaded files to a data collection.

**Arguments**:

- `data` - Data unit(s) to create.
  

**Returns**:

  Created data unit(s).

#### list\_data\_units

```python
def list_data_units(
        params: dict[str, Any] | None = None,
        *,
        url_conversion: dict[str, Any] | None = None,
        list_all: bool = False) -> dict[str, Any] | tuple[Any, int]
```

List data units with optional pagination.

**Arguments**:

- `params` - Query parameters for filtering.
- `url_conversion` - URL-to-path conversion config.
- `list_all` - If True, returns (generator, count).
  

**Returns**:

  Paginated list or (generator, count).

#### verify\_data\_files\_checksums

```python
def verify_data_files_checksums(checksums: list[str]) -> dict[str, Any]
```

Verify if data files with given checksums exist.

**Arguments**:

- `checksums` - List of MD5 checksums to verify.
  

**Returns**:

  Verification result with existing checksums.

#### upload\_data\_file

```python
def upload_data_file(data: dict[str, Any],
                     collection_id: int,
                     *,
                     use_chunked_upload: bool | None = None) -> dict[str, Any]
```

Upload individual files for a data unit and return binding data.

**Arguments**:

- `data` - Data unit definition with 'files' dict mapping names to paths.
- `collection_id` - Target data collection ID.
- `use_chunked_upload` - Force chunked (True) or direct (False) upload.
  

**Returns**:

  Data ready for create_data_units() with checksums.
  

**Example**:

  >>> result = client.upload_data_file(
  ...     \{'files': \{'image': '/path/to/img.jpg'\}, 'meta': \{'label': 1\}\},
  ...     collection_id=123
  ... )
  >>> # result['files']['image']['checksum'] is populated

#### upload\_data\_collection

```python
def upload_data_collection(
        collection_id: int,
        data: list[dict[str, Any]],
        *,
        project_id: int | None = None,
        batch_size: int = 1000,
        max_workers: int = 10,
        on_progress: Callable[[int, int], None] | None = None) -> None
```

Bulk upload data to a collection.

Uploads files in parallel using a thread pool, then creates
data units in batches. Optionally creates annotation tasks.

**Arguments**:

- `collection_id` - Target data collection ID.
- `data` - List of data unit definitions.
- `project_id` - Optional project ID to create tasks for.
- `batch_size` - Number of data units per batch (default 1000).
- `max_workers` - Number of parallel upload threads (default 10).
- `on_progress` - Optional callback(completed, total) for progress.
  

**Example**:

  >>> data = [
  ...     \{'files': \{'image': '/path/1.jpg'\}, 'meta': \{'label': 'cat'\}\},
  ...     \{'files': \{'image': '/path/2.jpg'\}, 'meta': \{'label': 'dog'\}\},
  ... ]
  >>> client.upload_data_collection(123, data, project_id=456)

