---
sidebar_label: core
title: synapse_sdk.clients.backend.core
---

Core backend client mixin with chunked upload support.

## CoreClientMixin Objects

```python
class CoreClientMixin()
```

Mixin providing chunked upload functionality.

Supports resumable uploads with MD5 integrity verification.
Files are uploaded in 50MB chunks by default.

#### create\_chunked\_upload

```python
def create_chunked_upload(
        file_path: str | Path,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        on_progress: Callable[[int, int], None] | None = None
) -> dict[str, Any]
```

Upload a file in chunks with MD5 integrity verification.

Files are uploaded in configurable chunks (default 50MB) with
Content-Range headers for resumable uploads. MD5 hash is calculated
incrementally during upload and verified on finalization.

**Arguments**:

- `file_path` - Path to the file to upload.
- `chunk_size` - Size of each chunk in bytes (default 50MB).
- `on_progress` - Optional callback(bytes_uploaded, total_bytes) for progress.
  

**Returns**:

  Finalized upload response with file ID and checksum.
  

**Raises**:

- `FileNotFoundError` - If file doesn't exist.
- `ClientError` - If upload fails.
  

**Example**:

  >>> def progress(uploaded, total):
  ...     print(f'\{uploaded\}/\{total\} bytes')
  >>> result = client.create_chunked_upload('/path/to/file.zip', on_progress=progress)
  >>> result['id']
  123

