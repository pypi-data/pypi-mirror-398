---
sidebar_label: io
title: synapse_sdk.utils.file.io
---

#### read\_file\_in\_chunks

```python
def read_file_in_chunks(
        file_path: str | Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE) -> Generator[bytes, None, None]
```

Read a file in chunks, yielding each chunk.

Memory-efficient generator for processing large files.

**Arguments**:

- `file_path` - Path to the file to read.
- `chunk_size` - Size of each chunk in bytes (default 50MB).
  

**Yields**:

  Bytes chunks of the file.
  

**Raises**:

- `FileNotFoundError` - If file doesn't exist.
- `PermissionError` - If file cannot be read.
  

**Example**:

  >>> for chunk in read_file_in_chunks('/path/to/large_file.zip'):
  ...     process(chunk)

#### convert\_file\_to\_base64

```python
def convert_file_to_base64(file_path: str | Path) -> str
```

Convert a file to base64 data URI format.

**Arguments**:

- `file_path` - Path to the file to encode.
  

**Returns**:

  Data URI string: "data:\{mime_type\};base64,\{encoded_content\}"
  

**Raises**:

- `FileNotFoundError` - If file doesn't exist.
- `ValueError` - If MIME type cannot be determined.
  

**Example**:

  >>> uri = convert_file_to_base64('/path/to/image.png')
  >>> uri.startswith('data:image/png;base64,')
  True

#### get\_temp\_path

```python
def get_temp_path(sub_path: str | None = None) -> Path
```

Get a temporary directory path for SDK operations.

**Arguments**:

- `sub_path` - Optional subdirectory name to append.
  

**Returns**:

  Path object pointing to /tmp/datamaker or /tmp/datamaker/\{sub_path\}.
  

**Examples**:

  >>> get_temp_path()
  PosixPath('/tmp/datamaker')
  >>> get_temp_path('media')
  PosixPath('/tmp/datamaker/media')

#### get\_dict\_from\_file

```python
def get_dict_from_file(file_path: str | Path) -> dict[str, Any]
```

Load a dictionary from a JSON or YAML file.

**Arguments**:

- `file_path` - Path to the file (JSON or YAML).
  

**Returns**:

  Dictionary parsed from the file.
  

**Raises**:

- `FileNotFoundError` - If the file doesn't exist.
- `json.JSONDecodeError` - If JSON parsing fails.
- `yaml.YAMLError` - If YAML parsing fails.

