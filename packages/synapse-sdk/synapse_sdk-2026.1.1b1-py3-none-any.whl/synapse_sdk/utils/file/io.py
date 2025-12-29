from __future__ import annotations

import base64
import json
import mimetypes
from collections.abc import Generator
from pathlib import Path
from typing import Any

import yaml

# Default chunk size: 50MB
DEFAULT_CHUNK_SIZE = 1024 * 1024 * 50


def read_file_in_chunks(
    file_path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Generator[bytes, None, None]:
    """Read a file in chunks, yielding each chunk.

    Memory-efficient generator for processing large files.

    Args:
        file_path: Path to the file to read.
        chunk_size: Size of each chunk in bytes (default 50MB).

    Yields:
        Bytes chunks of the file.

    Raises:
        FileNotFoundError: If file doesn't exist.
        PermissionError: If file cannot be read.

    Example:
        >>> for chunk in read_file_in_chunks('/path/to/large_file.zip'):
        ...     process(chunk)
    """
    path = Path(file_path)
    with path.open('rb') as f:
        while chunk := f.read(chunk_size):
            yield chunk


def convert_file_to_base64(file_path: str | Path) -> str:
    """Convert a file to base64 data URI format.

    Args:
        file_path: Path to the file to encode.

    Returns:
        Data URI string: "data:{mime_type};base64,{encoded_content}"

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If MIME type cannot be determined.

    Example:
        >>> uri = convert_file_to_base64('/path/to/image.png')
        >>> uri.startswith('data:image/png;base64,')
        True
    """
    path = Path(file_path)

    # Check if already base64 encoded
    if isinstance(file_path, str) and file_path.startswith('data:'):
        return file_path

    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None:
        raise ValueError(f'Cannot determine MIME type for: {path}')

    content = path.read_bytes()
    encoded = base64.b64encode(content).decode('ascii')

    return f'data:{mime_type};base64,{encoded}'


def get_temp_path(sub_path: str | None = None) -> Path:
    """Get a temporary directory path for SDK operations.

    Args:
        sub_path: Optional subdirectory name to append.

    Returns:
        Path object pointing to /tmp/datamaker or /tmp/datamaker/{sub_path}.

    Examples:
        >>> get_temp_path()
        PosixPath('/tmp/datamaker')
        >>> get_temp_path('media')
        PosixPath('/tmp/datamaker/media')
    """
    path = Path('/tmp/datamaker')
    if sub_path:
        path = path / sub_path
    return path


def get_dict_from_file(file_path: str | Path) -> dict[str, Any]:
    """Load a dictionary from a JSON or YAML file.

    Args:
        file_path: Path to the file (JSON or YAML).

    Returns:
        Dictionary parsed from the file.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If JSON parsing fails.
        yaml.YAMLError: If YAML parsing fails.
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    with open(file_path) as f:
        if file_path.suffix in ('.yaml', '.yml'):
            return yaml.safe_load(f)
        return json.load(f)


__all__ = [
    'DEFAULT_CHUNK_SIZE',
    'read_file_in_chunks',
    'convert_file_to_base64',
    'get_temp_path',
    'get_dict_from_file',
]
