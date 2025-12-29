"""Storage-specific exceptions."""

from __future__ import annotations

from typing import Any


class StorageError(Exception):
    """Base exception for storage-related errors."""

    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(message)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(message={self.message!r}, details={self.details!r})'


class StorageConfigError(StorageError):
    """Raised when storage configuration is invalid."""


class StorageProviderNotFoundError(StorageError):
    """Raised when requested provider is not registered."""


class StorageConnectionError(StorageError):
    """Raised when connection to storage fails."""


class StorageUploadError(StorageError):
    """Raised when file upload fails."""


class StorageNotFoundError(StorageError):
    """Raised when requested path does not exist."""


class StoragePermissionError(StorageError):
    """Raised when access to storage is denied."""


__all__ = [
    'StorageError',
    'StorageConfigError',
    'StorageProviderNotFoundError',
    'StorageConnectionError',
    'StorageUploadError',
    'StorageNotFoundError',
    'StoragePermissionError',
]
