"""Shared utility functions for HTTP clients.

This module contains utility functions extracted from BaseClient
and AsyncBaseClient to reduce code duplication.
"""

from __future__ import annotations

import json
from typing import Any, Union

# Type alias for response objects (requests.Response or httpx.Response)
ResponseType = Any


def build_url(base_url: str, path: str, trailing_slash: bool = False) -> str:
    """Construct a full URL from base URL and path.

    Args:
        base_url: The base URL (e.g., 'https://api.example.com').
        path: The path to append (e.g., 'users/123').
        trailing_slash: Whether to ensure the URL ends with a slash.

    Returns:
        The constructed URL.

    Examples:
        >>> build_url('https://api.example.com', 'users/123')
        'https://api.example.com/users/123'
        >>> build_url('https://api.example.com/', '/users/123/')
        'https://api.example.com/users/123/'
        >>> build_url('https://api.example.com', 'users', trailing_slash=True)
        'https://api.example.com/users/'
    """
    # If path is already a full URL, use it directly
    if path.startswith(('http://', 'https://')):
        url = path
    else:
        # Normalize: strip trailing slash from base and leading slash from path
        base = base_url.rstrip('/')
        clean_path = path.lstrip('/')
        url = f'{base}/{clean_path}'

    # Handle trailing slash
    if trailing_slash and not url.endswith('/'):
        url += '/'

    return url


def extract_error_detail(response: ResponseType) -> Any:
    """Extract error detail from response, preferring JSON.

    Args:
        response: A requests.Response or httpx.Response object.

    Returns:
        The parsed JSON response if available, otherwise the text content
        or reason phrase.
    """
    try:
        return response.json()
    except (ValueError, json.JSONDecodeError):
        # For requests.Response, use 'reason'; for httpx.Response, use 'reason_phrase'
        text = getattr(response, 'text', '')
        reason = getattr(response, 'reason', None) or getattr(response, 'reason_phrase', '')
        return text or reason


def parse_json_response(response: ResponseType) -> Union[dict, str, None]:
    """Parse response, preferring JSON.

    Args:
        response: A requests.Response or httpx.Response object.

    Returns:
        The parsed JSON response if available, otherwise the text content.
        Returns None for 204 No Content responses.
    """
    # Handle 204 No Content
    status_code = getattr(response, 'status_code', None)
    if status_code == 204:
        return None

    try:
        return response.json()
    except (ValueError, json.JSONDecodeError):
        return response.text
