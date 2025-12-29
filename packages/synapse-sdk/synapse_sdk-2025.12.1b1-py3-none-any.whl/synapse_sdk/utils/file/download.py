from __future__ import annotations

import asyncio
import hashlib
import operator
from functools import reduce
from pathlib import Path
from typing import Any, Callable, TypeVar
from urllib.parse import urlparse, urlunparse

import aiohttp
import requests

from .io import get_temp_path

T = TypeVar('T')

# Default chunk size: 50MB
_CHUNK_SIZE = 1024 * 1024 * 50


def _hash_text(text: str) -> str:
    """Generate MD5 hash of text for cache keys."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def _clean_url(url: str) -> str:
    """Remove query params and fragment from URL."""
    parsed = urlparse(url)
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        '',  # no query
        '',  # no fragment
    ))


def download_file(
    url: str,
    path_download: str | Path,
    *,
    name: str | None = None,
    coerce: Callable[[Path], T] | None = None,
    use_cached: bool = True,
) -> Path | T:
    """Download a file from a URL to a specified directory.

    Downloads are streamed in chunks for memory efficiency. Supports caching
    based on URL hash to avoid redundant downloads.

    Args:
        url: The URL to download from.
        path_download: Directory path where the file will be saved.
        name: Custom filename (without extension). Disables caching if provided.
        coerce: Optional function to transform the downloaded Path.
        use_cached: If True, skip download if file already exists.

    Returns:
        Path to the downloaded file, or coerce(path) if coerce is provided.

    Raises:
        requests.HTTPError: If the HTTP request fails.
        OSError: If file write fails.

    Examples:
        >>> path = download_file('https://example.com/image.jpg', '/tmp/downloads')
        >>> path = download_file(url, '/tmp', name='my_file')  # Custom name
        >>> path_str = download_file(url, '/tmp', coerce=str)  # As string
    """
    cleaned_url = _clean_url(url)

    if name:
        use_cached = False
    else:
        name = _hash_text(cleaned_url)

    name += Path(cleaned_url).suffix
    path = Path(path_download) / name

    if not use_cached or not path.is_file():
        response = requests.get(url, allow_redirects=True, stream=True, timeout=30)
        response.raise_for_status()

        with path.open('wb') as file:
            for chunk in response.iter_content(chunk_size=_CHUNK_SIZE):
                file.write(chunk)

    if coerce:
        return coerce(path)
    return path


async def adownload_file(
    url: str,
    path_download: str | Path,
    *,
    name: str | None = None,
    coerce: Callable[[Path], T] | None = None,
    use_cached: bool = True,
) -> Path | T:
    """Asynchronously download a file from a URL.

    Async version of download_file() using aiohttp for concurrent downloads.

    Args:
        url: The URL to download from.
        path_download: Directory path where the file will be saved.
        name: Custom filename (without extension). Disables caching if provided.
        coerce: Optional function to transform the downloaded Path.
        use_cached: If True, skip download if file already exists.

    Returns:
        Path to the downloaded file, or coerce(path) if coerce is provided.

    Examples:
        >>> path = await adownload_file('https://example.com/large.zip', '/tmp')
        >>> paths = await asyncio.gather(*[adownload_file(u, '/tmp') for u in urls])
    """
    cleaned_url = _clean_url(url)

    if name:
        use_cached = False
    else:
        name = _hash_text(cleaned_url)

    name += Path(cleaned_url).suffix
    path = Path(path_download) / name

    if not use_cached or not path.is_file():
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                with path.open('wb') as file:
                    while chunk := await response.content.read(_CHUNK_SIZE):
                        file.write(chunk)

    if coerce:
        return coerce(path)
    return path


def files_url_to_path(
    files: dict[str, Any],
    *,
    coerce: Callable[[Path], Any] | None = None,
    file_field: str | None = None,
) -> None:
    """Convert file URLs to local paths by downloading them in-place.

    Args:
        files: Dictionary containing file URLs or file objects.
            - String values: treated as URLs, replaced with local paths
            - Dict values with 'url' key: 'url' is replaced with 'path'
        coerce: Function to transform downloaded paths.
        file_field: If provided, only process this specific field.

    Examples:
        >>> files = {'image': 'https://example.com/img.jpg'}
        >>> files_url_to_path(files)
        >>> files['image']  # Path('/tmp/datamaker/media/abc123.jpg')

        >>> files = {'video': {'url': 'https://example.com/vid.mp4', 'size': 1024}}
        >>> files_url_to_path(files)
        >>> files['video']  # {'path': Path(...), 'size': 1024}
    """
    path_download = get_temp_path('media')
    path_download.mkdir(parents=True, exist_ok=True)

    if file_field:
        files[file_field] = download_file(files[file_field], path_download, coerce=coerce)
    else:
        for file_name in files:
            if isinstance(files[file_name], str):
                files[file_name] = download_file(files[file_name], path_download, coerce=coerce)
            else:
                files[file_name]['path'] = download_file(files[file_name].pop('url'), path_download, coerce=coerce)


async def afiles_url_to_path(
    files: dict[str, Any],
    *,
    coerce: Callable[[Path], Any] | None = None,
) -> None:
    """Asynchronously convert file URLs to local paths.

    All files are downloaded concurrently for better performance.

    Args:
        files: Dictionary containing file URLs or file objects.
        coerce: Function to transform downloaded paths.
    """
    path_download = get_temp_path('media')
    path_download.mkdir(parents=True, exist_ok=True)

    for file_name in files:
        if isinstance(files[file_name], str):
            files[file_name] = await adownload_file(files[file_name], path_download, coerce=coerce)
        else:
            files[file_name]['path'] = await adownload_file(files[file_name].pop('url'), path_download, coerce=coerce)


def files_url_to_path_from_objs(
    objs: dict[str, Any] | list[dict[str, Any]],
    files_fields: list[str],
    *,
    coerce: Callable[[Path], Any] | None = None,
    is_list: bool = False,
    is_async: bool = False,
) -> None:
    """Convert file URLs to paths for multiple objects with nested field support.

    Args:
        objs: Single object or list of objects to process.
        files_fields: List of field paths (supports dot notation like 'data.files').
        coerce: Function to transform downloaded paths.
        is_list: If True, objs is treated as a list.
        is_async: If True, uses async download for better performance.

    Examples:
        >>> obj = {'files': {'image': 'https://example.com/img.jpg'}}
        >>> files_url_to_path_from_objs(obj, files_fields=['files'])

        >>> objs = [{'data': {'files': {...}}}, ...]
        >>> files_url_to_path_from_objs(objs, ['data.files'], is_list=True, is_async=True)
    """
    if is_async:
        asyncio.run(afiles_url_to_path_from_objs(objs, files_fields, coerce=coerce, is_list=is_list))
    else:
        if not is_list:
            objs = [objs]

        for obj in objs:
            for files_field in files_fields:
                try:
                    files = reduce(operator.getitem, files_field.split('.'), obj)
                    if isinstance(files, str):
                        files_url_to_path(obj, coerce=coerce, file_field=files_field)
                    else:
                        files_url_to_path(files, coerce=coerce)
                except KeyError:
                    pass


async def afiles_url_to_path_from_objs(
    objs: dict[str, Any] | list[dict[str, Any]],
    files_fields: list[str],
    *,
    coerce: Callable[[Path], Any] | None = None,
    is_list: bool = False,
) -> None:
    """Asynchronously convert file URLs to paths for multiple objects.

    All file downloads happen concurrently using asyncio.gather().

    Args:
        objs: Single object or list of objects to process.
        files_fields: List of field paths (supports dot notation).
        coerce: Function to transform downloaded paths.
        is_list: If True, objs is treated as a list.
    """
    if not is_list:
        objs = [objs]

    tasks = []

    for obj in objs:
        for files_field in files_fields:
            try:
                files = reduce(operator.getitem, files_field.split('.'), obj)
                tasks.append(afiles_url_to_path(files, coerce=coerce))
            except KeyError:
                pass

    await asyncio.gather(*tasks)


__all__ = [
    'download_file',
    'adownload_file',
    'files_url_to_path',
    'afiles_url_to_path',
    'files_url_to_path_from_objs',
    'afiles_url_to_path_from_objs',
]
