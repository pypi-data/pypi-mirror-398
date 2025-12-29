---
sidebar_label: download
title: synapse_sdk.utils.file.download
---

#### download\_file

```python
def download_file(url: str,
                  path_download: str | Path,
                  *,
                  name: str | None = None,
                  coerce: Callable[[Path], T] | None = None,
                  use_cached: bool = True) -> Path | T
```

Download a file from a URL to a specified directory.

Downloads are streamed in chunks for memory efficiency. Supports caching
based on URL hash to avoid redundant downloads.

**Arguments**:

- `url` - The URL to download from.
- `path_download` - Directory path where the file will be saved.
- `name` - Custom filename (without extension). Disables caching if provided.
- `coerce` - Optional function to transform the downloaded Path.
- `use_cached` - If True, skip download if file already exists.
  

**Returns**:

  Path to the downloaded file, or coerce(path) if coerce is provided.
  

**Raises**:

- `requests.HTTPError` - If the HTTP request fails.
- `OSError` - If file write fails.
  

**Examples**:

  >>> path = download_file('https://example.com/image.jpg', '/tmp/downloads')
  >>> path = download_file(url, '/tmp', name='my_file')  # Custom name
  >>> path_str = download_file(url, '/tmp', coerce=str)  # As string

#### adownload\_file

```python
async def adownload_file(url: str,
                         path_download: str | Path,
                         *,
                         name: str | None = None,
                         coerce: Callable[[Path], T] | None = None,
                         use_cached: bool = True) -> Path | T
```

Asynchronously download a file from a URL.

Async version of download_file() using aiohttp for concurrent downloads.

**Arguments**:

- `url` - The URL to download from.
- `path_download` - Directory path where the file will be saved.
- `name` - Custom filename (without extension). Disables caching if provided.
- `coerce` - Optional function to transform the downloaded Path.
- `use_cached` - If True, skip download if file already exists.
  

**Returns**:

  Path to the downloaded file, or coerce(path) if coerce is provided.
  

**Examples**:

  >>> path = await adownload_file('https://example.com/large.zip', '/tmp')
  >>> paths = await asyncio.gather(*[adownload_file(u, '/tmp') for u in urls])

#### files\_url\_to\_path

```python
def files_url_to_path(files: dict[str, Any],
                      *,
                      coerce: Callable[[Path], Any] | None = None,
                      file_field: str | None = None) -> None
```

Convert file URLs to local paths by downloading them in-place.

**Arguments**:

- `files` - Dictionary containing file URLs or file objects.
  - String values: treated as URLs, replaced with local paths
  - Dict values with 'url' key: 'url' is replaced with 'path'
- `coerce` - Function to transform downloaded paths.
- `file_field` - If provided, only process this specific field.
  

**Examples**:

  >>> files = \{'image': 'https://example.com/img.jpg'\}
  >>> files_url_to_path(files)
  >>> files['image']  # Path('/tmp/datamaker/media/abc123.jpg')
  
  >>> files = \{'video': \{'url': 'https://example.com/vid.mp4', 'size': 1024\}\}
  >>> files_url_to_path(files)
  >>> files['video']  # \{'path': Path(...), 'size': 1024\}

#### afiles\_url\_to\_path

```python
async def afiles_url_to_path(
        files: dict[str, Any],
        *,
        coerce: Callable[[Path], Any] | None = None) -> None
```

Asynchronously convert file URLs to local paths.

All files are downloaded concurrently for better performance.

**Arguments**:

- `files` - Dictionary containing file URLs or file objects.
- `coerce` - Function to transform downloaded paths.

#### files\_url\_to\_path\_from\_objs

```python
def files_url_to_path_from_objs(objs: dict[str, Any] | list[dict[str, Any]],
                                files_fields: list[str],
                                *,
                                coerce: Callable[[Path], Any] | None = None,
                                is_list: bool = False,
                                is_async: bool = False) -> None
```

Convert file URLs to paths for multiple objects with nested field support.

**Arguments**:

- `objs` - Single object or list of objects to process.
- `files_fields` - List of field paths (supports dot notation like 'data.files').
- `coerce` - Function to transform downloaded paths.
- `is_list` - If True, objs is treated as a list.
- `is_async` - If True, uses async download for better performance.
  

**Examples**:

  >>> obj = \{'files': \{'image': 'https://example.com/img.jpg'\}\}
  >>> files_url_to_path_from_objs(obj, files_fields=['files'])
  
  >>> objs = [\{'data': \{'files': \{...\}\}\}, ...]
  >>> files_url_to_path_from_objs(objs, ['data.files'], is_list=True, is_async=True)

#### afiles\_url\_to\_path\_from\_objs

```python
async def afiles_url_to_path_from_objs(objs: dict[str, Any]
                                       | list[dict[str, Any]],
                                       files_fields: list[str],
                                       *,
                                       coerce: Callable[[Path], Any]
                                       | None = None,
                                       is_list: bool = False) -> None
```

Asynchronously convert file URLs to paths for multiple objects.

All file downloads happen concurrently using asyncio.gather().

**Arguments**:

- `objs` - Single object or list of objects to process.
- `files_fields` - List of field paths (supports dot notation).
- `coerce` - Function to transform downloaded paths.
- `is_list` - If True, objs is treated as a list.

