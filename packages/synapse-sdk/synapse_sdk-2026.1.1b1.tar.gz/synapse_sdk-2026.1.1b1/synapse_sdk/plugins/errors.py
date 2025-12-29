from __future__ import annotations

from typing import Any


class PluginError(Exception):
    """Base exception for plugin-related errors."""

    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(message)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(message={self.message!r}, details={self.details!r})'


class ValidationError(PluginError):
    """Raised when plugin parameters fail validation."""

    pass


class ActionNotFoundError(PluginError):
    """Raised when the requested action doesn't exist in the plugin."""

    pass


class ExecutionError(PluginError):
    """Raised when action execution fails."""

    pass


class PluginUploadError(PluginError):
    """Raised when plugin upload fails.

    Covers storage upload failures, network errors during upload,
    and other upload-related issues.
    """

    pass


class ArchiveError(PluginError):
    """Raised when archive creation fails.

    Covers ZIP creation failures, git ls-files failures,
    and file permission errors during archiving.
    """

    pass


class BuildError(PluginError):
    """Raised when wheel build fails.

    Covers wheel build failures, missing pyproject.toml,
    and package manager not found errors.
    """

    pass


class ChecksumMismatchError(PluginError):
    """Raised when checksum verification fails.

    Indicates file integrity issues - the actual checksum
    does not match the expected value.
    """

    pass


class PluginRunError(PluginError):
    """Raised when plugin run fails."""

    pass


__all__ = [
    'ActionNotFoundError',
    'ArchiveError',
    'BuildError',
    'ChecksumMismatchError',
    'ExecutionError',
    'PluginError',
    'PluginRunError',
    'PluginUploadError',
    'ValidationError',
]
