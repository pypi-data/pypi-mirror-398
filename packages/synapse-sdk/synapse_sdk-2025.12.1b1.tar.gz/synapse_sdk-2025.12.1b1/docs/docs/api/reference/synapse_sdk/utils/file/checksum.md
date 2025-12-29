---
sidebar_label: checksum
title: synapse_sdk.utils.file.checksum
---

Checksum utilities for file integrity verification.

#### calculate\_checksum

```python
def calculate_checksum(file_path: str | Path,
                       *,
                       algorithm: HashAlgorithm = 'md5',
                       chunk_size: int = DEFAULT_CHUNK_SIZE,
                       prefix: str = '') -> str
```

Calculate file checksum using specified algorithm.

Reads file in chunks for memory efficiency with large files.

**Arguments**:

- `file_path` - Path to file to hash.
- `algorithm` - Hash algorithm ('md5', 'sha1', 'sha256', 'sha512').
- `chunk_size` - Size of chunks to read (default 1MB).
- `prefix` - Optional prefix to prepend to result.
  

**Returns**:

  Hex digest string, optionally with prefix.
  

**Raises**:

- `FileNotFoundError` - If file does not exist.
- `ValueError` - If algorithm is not supported.
  

**Example**:

  >>> checksum = calculate_checksum('/path/to/file.zip')
  >>> checksum_with_prefix = calculate_checksum('/path/to/file.zip', prefix='dev-')

#### calculate\_checksum\_from\_bytes

```python
def calculate_checksum_from_bytes(data: bytes,
                                  *,
                                  algorithm: HashAlgorithm = 'md5') -> str
```

Calculate checksum from bytes data.

**Arguments**:

- `data` - Bytes to hash.
- `algorithm` - Hash algorithm.
  

**Returns**:

  Hex digest string.
  

**Example**:

  >>> checksum = calculate_checksum_from_bytes(b'hello world')

#### calculate\_checksum\_from\_file\_object

```python
def calculate_checksum_from_file_object(
        file: IO[bytes],
        *,
        algorithm: HashAlgorithm = 'md5',
        chunk_size: int = DEFAULT_CHUNK_SIZE) -> str
```

Calculate checksum from file-like object.

Resets file pointer to beginning if the object supports seek().
Does not close the file after reading.

**Arguments**:

- `file` - File-like object opened in binary mode.
- `algorithm` - Hash algorithm.
- `chunk_size` - Size of chunks to read.
  

**Returns**:

  Hex digest string.
  

**Example**:

  >>> with open('/path/to/file', 'rb') as f:
  ...     checksum = calculate_checksum_from_file_object(f)

#### verify\_checksum

```python
def verify_checksum(file_path: str | Path,
                    expected: str,
                    *,
                    algorithm: HashAlgorithm = 'md5') -> bool
```

Verify file checksum matches expected value.

**Arguments**:

- `file_path` - Path to file.
- `expected` - Expected checksum hex string (may include prefix).
- `algorithm` - Hash algorithm used.
  

**Returns**:

  True if checksum matches, False otherwise.
  

**Example**:

  >>> is_valid = verify_checksum('/path/to/file.zip', 'abc123...')

