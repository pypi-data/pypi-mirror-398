"""Checksum utilities for file integrity verification."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import IO, Any, Literal

HashAlgorithm = Literal['md5', 'sha1', 'sha256', 'sha512']

# Default chunk size for reading large files: 1MB
DEFAULT_CHUNK_SIZE = 1024 * 1024


def _get_hasher(algorithm: HashAlgorithm) -> Any:
    """Get a hashlib hasher for the specified algorithm."""
    match algorithm:
        case 'md5':
            return hashlib.md5()
        case 'sha1':
            return hashlib.sha1()
        case 'sha256':
            return hashlib.sha256()
        case 'sha512':
            return hashlib.sha512()
        case _:
            raise ValueError(f'Unsupported hash algorithm: {algorithm}')


def calculate_checksum(
    file_path: str | Path,
    *,
    algorithm: HashAlgorithm = 'md5',
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    prefix: str = '',
) -> str:
    """Calculate file checksum using specified algorithm.

    Reads file in chunks for memory efficiency with large files.

    Args:
        file_path: Path to file to hash.
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256', 'sha512').
        chunk_size: Size of chunks to read (default 1MB).
        prefix: Optional prefix to prepend to result.

    Returns:
        Hex digest string, optionally with prefix.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If algorithm is not supported.

    Example:
        >>> checksum = calculate_checksum('/path/to/file.zip')
        >>> checksum_with_prefix = calculate_checksum('/path/to/file.zip', prefix='dev-')
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f'File not found: {path}')

    hasher = _get_hasher(algorithm)

    with path.open('rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    digest = hasher.hexdigest()
    return f'{prefix}{digest}' if prefix else digest


def calculate_checksum_from_bytes(
    data: bytes,
    *,
    algorithm: HashAlgorithm = 'md5',
) -> str:
    """Calculate checksum from bytes data.

    Args:
        data: Bytes to hash.
        algorithm: Hash algorithm.

    Returns:
        Hex digest string.

    Example:
        >>> checksum = calculate_checksum_from_bytes(b'hello world')
    """
    hasher = _get_hasher(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def calculate_checksum_from_file_object(
    file: IO[bytes],
    *,
    algorithm: HashAlgorithm = 'md5',
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> str:
    """Calculate checksum from file-like object.

    Resets file pointer to beginning if the object supports seek().
    Does not close the file after reading.

    Args:
        file: File-like object opened in binary mode.
        algorithm: Hash algorithm.
        chunk_size: Size of chunks to read.

    Returns:
        Hex digest string.

    Example:
        >>> with open('/path/to/file', 'rb') as f:
        ...     checksum = calculate_checksum_from_file_object(f)
    """
    hasher = _get_hasher(algorithm)

    # Reset to beginning if possible
    if hasattr(file, 'seek'):
        file.seek(0)

    while chunk := file.read(chunk_size):
        hasher.update(chunk)

    return hasher.hexdigest()


def verify_checksum(
    file_path: str | Path,
    expected: str,
    *,
    algorithm: HashAlgorithm = 'md5',
) -> bool:
    """Verify file checksum matches expected value.

    Args:
        file_path: Path to file.
        expected: Expected checksum hex string (may include prefix).
        algorithm: Hash algorithm used.

    Returns:
        True if checksum matches, False otherwise.

    Example:
        >>> is_valid = verify_checksum('/path/to/file.zip', 'abc123...')
    """
    actual = calculate_checksum(file_path, algorithm=algorithm)

    # Handle expected values with prefixes (e.g., 'dev-abc123...')
    # Compare just the hex portion if expected has a prefix
    if '-' in expected:
        expected_hash = expected.split('-', 1)[-1]
    else:
        expected_hash = expected

    return actual.lower() == expected_hash.lower()


__all__ = [
    'HashAlgorithm',
    'DEFAULT_CHUNK_SIZE',
    'calculate_checksum',
    'calculate_checksum_from_bytes',
    'calculate_checksum_from_file_object',
    'verify_checksum',
]
