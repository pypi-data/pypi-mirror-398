---
sidebar_label: http
title: synapse_sdk.utils.storage.providers.http
---

HTTP storage provider.

## HTTPStorage Objects

```python
class HTTPStorage()
```

Storage provider for HTTP file servers.

Note: This provider has limited functionality as HTTP servers typically
don't support directory listing. File counting and size calculation
are not supported.

**Arguments**:

- `config` - Configuration dict with HTTP server details.
  

**Example**:

  >>> storage = HTTPStorage(\{
  ...     'base_url': 'https://files.example.com/uploads/',
  ...     'timeout': 60,
  ... \})
  >>> storage.exists('data/file.txt')
  True

#### upload

```python
def upload(source: Path, target: str) -> str
```

Upload a file to HTTP server.

Note: Requires server to support PUT or POST for file uploads.

**Arguments**:

- `source` - Local file path to upload.
- `target` - Target path on server.
  

**Returns**:

  URL of uploaded file.

#### exists

```python
def exists(target: str) -> bool
```

Check if file exists on HTTP server.

Uses HEAD request to check existence.

**Arguments**:

- `target` - Path to check.
  

**Returns**:

  True if file exists (HTTP 200), False otherwise.

#### get\_url

```python
def get_url(target: str) -> str
```

Get full URL for target.

**Arguments**:

- `target` - Target path.
  

**Returns**:

  Full HTTP URL.

#### get\_pathlib

```python
def get_pathlib(path: str) -> HTTPPath
```

Get HTTPPath object for path.

**Arguments**:

- `path` - Path on server.
  

**Returns**:

  HTTPPath object (pathlib-like interface).

#### get\_path\_file\_count

```python
def get_path_file_count(pathlib_obj: HTTPPath) -> int
```

Not supported for HTTP storage.

**Raises**:

- `StorageError` - Always, as HTTP servers don't support directory listing.

#### get\_path\_total\_size

```python
def get_path_total_size(pathlib_obj: HTTPPath) -> int
```

Not supported for HTTP storage.

**Raises**:

- `StorageError` - Always, as HTTP servers don't support directory listing.

## HTTPPath Objects

```python
class HTTPPath()
```

Pathlib-like interface for HTTP paths.

Provides a subset of pathlib.Path functionality for HTTP resources.

#### joinuri

```python
def joinuri(*parts: str) -> HTTPPath
```

Join path parts.

#### name

```python
@property
def name() -> str
```

Get the final component of the path.

#### parent

```python
@property
def parent() -> HTTPPath
```

Get the parent directory.

#### exists

```python
def exists() -> bool
```

Check if this path exists.

#### is\_file

```python
def is_file() -> bool
```

Check if this path is a file (assumes exists = is_file for HTTP).

#### is\_dir

```python
def is_dir() -> bool
```

Check if this path is a directory.

Note: HTTP servers don't typically distinguish directories.
This always returns False.

#### read\_bytes

```python
def read_bytes() -> bytes
```

Read file contents as bytes.

#### read\_text

```python
def read_text(encoding: str = 'utf-8') -> str
```

Read file contents as text.

#### stat

```python
def stat() -> HTTPStat
```

Get file statistics.

Note: Only st_size is populated via Content-Length header.

## HTTPStat Objects

```python
class HTTPStat()
```

Minimal stat result for HTTP files.

