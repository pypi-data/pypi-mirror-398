"""Shared implementation for storage providers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from upath import UPath


class _BaseStorageMixin:
    """Shared implementation for storage providers.

    This mixin provides common implementations for file counting
    and size calculation that work with both Path and UPath objects.
    """

    def _count_files(self, pathlib_obj: Path | UPath) -> int:
        """Count files recursively in the given path.

        Args:
            pathlib_obj: Path object to count files in.

        Returns:
            Number of files.
        """
        if not pathlib_obj.exists():
            return 0

        if pathlib_obj.is_file():
            return 1

        count = 0
        for item in pathlib_obj.rglob('*'):
            if item.is_file():
                count += 1
        return count

    def _calculate_total_size(self, pathlib_obj: Path | UPath) -> int:
        """Calculate total size of files recursively.

        Args:
            pathlib_obj: Path object to calculate size for.

        Returns:
            Total size in bytes.
        """
        if not pathlib_obj.exists():
            return 0

        if pathlib_obj.is_file():
            return pathlib_obj.stat().st_size

        total_size = 0
        for item in pathlib_obj.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
        return total_size

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize path by removing leading slashes.

        Args:
            path: Path string to normalize.

        Returns:
            Normalized path without leading slashes.
        """
        if path in ('/', ''):
            return ''
        return path.lstrip('/')


__all__ = ['_BaseStorageMixin']
