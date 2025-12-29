"""Archive utilities for creating and extracting ZIP files."""

from __future__ import annotations

import fnmatch
import subprocess
import zipfile
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Literal

# Progress callback signature: (current_file_index, total_files)
ProgressCallback = Callable[[int, int], None]

# Compression method mapping
COMPRESSION_METHODS = {
    'stored': zipfile.ZIP_STORED,
    'deflated': zipfile.ZIP_DEFLATED,
    'bzip2': zipfile.ZIP_BZIP2,
    'lzma': zipfile.ZIP_LZMA,
}


class ArchiveFilter:
    """Filter for selecting files to include in archive.

    Supports glob patterns for include/exclude filtering.
    Default excludes common non-essential directories and files.

    Example:
        >>> filter = ArchiveFilter.from_patterns(exclude=['*.pyc', '__pycache__'])
        >>> filter.should_include(Path('src/main.py'), Path('/project'))
        True
        >>> filter.should_include(Path('__pycache__/cache.pyc'), Path('/project'))
        False
    """

    DEFAULT_EXCLUDES: frozenset[str] = frozenset({
        # Python
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.python-version',
        '*.egg-info',
        '*.egg',
        # Virtual environments
        '.venv',
        'venv',
        '.env',
        'env',
        # Version control
        '.git',
        '.gitignore',
        '.gitattributes',
        '.svn',
        '.hg',
        # IDE/Editor
        '.idea',
        '.vscode',
        '*.swp',
        '*.swo',
        '.DS_Store',
        'Thumbs.db',
        # Build artifacts
        'dist',
        'build',
        'node_modules',
        # Cache
        '.mypy_cache',
        '.pytest_cache',
        '.ruff_cache',
        '.cache',
        '.tox',
        # Test coverage
        '.coverage',
        'htmlcov',
        # Logs
        '*.log',
    })

    def __init__(
        self,
        include_patterns: frozenset[str] | None = None,
        exclude_patterns: frozenset[str] | None = None,
    ) -> None:
        """Initialize archive filter.

        Args:
            include_patterns: Glob patterns for files to include (None = all).
            exclude_patterns: Glob patterns for files to exclude.
        """
        self._include_patterns = include_patterns
        self._exclude_patterns = exclude_patterns or self.DEFAULT_EXCLUDES

    @classmethod
    def from_patterns(
        cls,
        include: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
        *,
        use_defaults: bool = True,
    ) -> ArchiveFilter:
        """Create filter from glob patterns.

        Args:
            include: Patterns for files to include.
            exclude: Patterns for files to exclude.
            use_defaults: Include DEFAULT_EXCLUDES in exclude patterns.

        Returns:
            Configured ArchiveFilter instance.
        """
        include_set = frozenset(include) if include else None

        exclude_set: frozenset[str]
        if exclude:
            if use_defaults:
                exclude_set = frozenset(exclude) | cls.DEFAULT_EXCLUDES
            else:
                exclude_set = frozenset(exclude)
        elif use_defaults:
            exclude_set = cls.DEFAULT_EXCLUDES
        else:
            exclude_set = frozenset()

        return cls(include_patterns=include_set, exclude_patterns=exclude_set)

    def _matches_any_pattern(self, path_str: str, patterns: frozenset[str]) -> bool:
        """Check if path matches any of the patterns."""
        # Check the full path and each component
        path_parts = Path(path_str).parts

        for pattern in patterns:
            # Match against full path
            if fnmatch.fnmatch(path_str, pattern):
                return True
            # Match against filename only
            if fnmatch.fnmatch(path_parts[-1], pattern):
                return True
            # Match against any path component (for directory patterns)
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
        return False

    def should_include(self, path: Path, relative_to: Path) -> bool:
        """Check if path should be included in archive.

        Args:
            path: Absolute path to check.
            relative_to: Base path for relative path calculation.

        Returns:
            True if file should be included.
        """
        # Only include files, not directories
        if path.is_dir():
            return False

        try:
            rel_path = str(path.relative_to(relative_to))
        except ValueError:
            rel_path = str(path)

        # Check exclude patterns first
        if self._matches_any_pattern(rel_path, self._exclude_patterns):
            return False

        # If include patterns specified, file must match at least one
        if self._include_patterns is not None:
            return self._matches_any_pattern(rel_path, self._include_patterns)

        return True


def create_archive(
    source_path: str | Path,
    archive_path: str | Path,
    *,
    filter: ArchiveFilter | None = None,
    compression: Literal['stored', 'deflated', 'bzip2', 'lzma'] = 'deflated',
    compression_level: int = 6,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    """Create a ZIP archive from source directory.

    Uses pure Python zipfile module for cross-platform compatibility
    and security (no shell execution).

    Args:
        source_path: Directory to archive.
        archive_path: Output ZIP file path.
        filter: File filter (defaults to ArchiveFilter with DEFAULT_EXCLUDES).
        compression: Compression method.
        compression_level: Compression level (1-9 for deflated, ignored for others).
        progress_callback: Optional callback for progress updates.

    Returns:
        Path to created archive.

    Raises:
        FileNotFoundError: If source_path does not exist.
        NotADirectoryError: If source_path is not a directory.

    Example:
        >>> archive_path = create_archive('/path/to/project', '/tmp/project.zip')
    """
    source = Path(source_path).resolve()
    archive = Path(archive_path).resolve()

    if not source.exists():
        raise FileNotFoundError(f'Source path not found: {source}')
    if not source.is_dir():
        raise NotADirectoryError(f'Source path is not a directory: {source}')

    # Ensure archive parent directory exists
    archive.parent.mkdir(parents=True, exist_ok=True)

    # Use default filter if not provided
    if filter is None:
        filter = ArchiveFilter.from_patterns()

    # Collect files to archive
    files_to_archive: list[Path] = []
    for file_path in source.rglob('*'):
        if filter.should_include(file_path, source):
            files_to_archive.append(file_path)

    total_files = len(files_to_archive)
    compression_method = COMPRESSION_METHODS[compression]

    # Set compression level for deflated
    compresslevel = compression_level if compression == 'deflated' else None

    with zipfile.ZipFile(
        archive,
        mode='w',
        compression=compression_method,
        compresslevel=compresslevel,
    ) as zf:
        for idx, file_path in enumerate(files_to_archive):
            rel_path = file_path.relative_to(source)
            zf.write(file_path, rel_path)

            if progress_callback:
                progress_callback(idx + 1, total_files)

    return archive


def create_archive_from_git(
    source_path: str | Path,
    archive_path: str | Path,
    *,
    include_untracked: bool = True,
    compression: Literal['stored', 'deflated', 'bzip2', 'lzma'] = 'deflated',
    compression_level: int = 6,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    """Create archive from git-tracked files only.

    Uses `git ls-files` to determine which files to include,
    but creates the archive with pure Python zipfile (no shell=True).

    Args:
        source_path: Git repository directory.
        archive_path: Output ZIP file path.
        include_untracked: Include untracked files (--others --exclude-standard).
        compression: Compression method.
        compression_level: Compression level (1-9 for deflated).
        progress_callback: Optional callback for progress updates.

    Returns:
        Path to created archive.

    Raises:
        FileNotFoundError: If source_path does not exist.
        RuntimeError: If not a git repository or git command fails.

    Example:
        >>> archive_path = create_archive_from_git('/path/to/repo', '/tmp/repo.zip')
    """
    source = Path(source_path).resolve()
    archive = Path(archive_path).resolve()

    if not source.exists():
        raise FileNotFoundError(f'Source path not found: {source}')

    # Check if it's a git repository
    git_dir = source / '.git'
    if not git_dir.exists():
        raise RuntimeError(f'Not a git repository: {source}')

    # Ensure archive parent directory exists
    archive.parent.mkdir(parents=True, exist_ok=True)

    # Build git ls-files command (no shell=True)
    git_cmd = ['git', 'ls-files', '--cached']

    if include_untracked:
        git_cmd.extend(['--others', '--exclude-standard'])

    # Run git ls-files
    try:
        result = subprocess.run(
            git_cmd,
            cwd=source,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'git ls-files failed: {e.stderr}') from e
    except FileNotFoundError as e:
        raise RuntimeError('git command not found. Is git installed?') from e

    # Parse output - each line is a file path
    files_str = result.stdout.strip()
    if not files_str:
        # Empty repository or no files
        file_list: list[str] = []
    else:
        file_list = files_str.split('\n')

    # Filter out any empty strings
    file_list = [f for f in file_list if f]

    total_files = len(file_list)
    compression_method = COMPRESSION_METHODS[compression]
    compresslevel = compression_level if compression == 'deflated' else None

    with zipfile.ZipFile(
        archive,
        mode='w',
        compression=compression_method,
        compresslevel=compresslevel,
    ) as zf:
        for idx, rel_path in enumerate(file_list):
            file_path = source / rel_path
            if file_path.exists() and file_path.is_file():
                zf.write(file_path, rel_path)

            if progress_callback:
                progress_callback(idx + 1, total_files)

    return archive


def extract_archive(
    archive_path: str | Path,
    output_path: str | Path,
    *,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    """Extract a ZIP archive.

    Args:
        archive_path: Path to ZIP file.
        output_path: Directory to extract to.
        progress_callback: Optional callback for progress updates.

    Returns:
        Path to extraction directory.

    Raises:
        FileNotFoundError: If archive does not exist.
        zipfile.BadZipFile: If archive is invalid.

    Example:
        >>> output_dir = extract_archive('/path/to/archive.zip', '/tmp/extracted')
    """
    archive = Path(archive_path).resolve()
    output = Path(output_path).resolve()

    if not archive.exists():
        raise FileNotFoundError(f'Archive not found: {archive}')

    output.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive, 'r') as zf:
        members = zf.namelist()
        total = len(members)

        for idx, member in enumerate(members):
            zf.extract(member, output)

            if progress_callback:
                progress_callback(idx + 1, total)

    return output


def list_archive_contents(archive_path: str | Path) -> list[str]:
    """List files in archive without extracting.

    Args:
        archive_path: Path to ZIP file.

    Returns:
        List of file paths in archive.

    Raises:
        FileNotFoundError: If archive does not exist.
        zipfile.BadZipFile: If archive is invalid.

    Example:
        >>> files = list_archive_contents('/path/to/archive.zip')
        >>> print(files)
        ['src/main.py', 'src/utils.py', 'README.md']
    """
    archive = Path(archive_path).resolve()

    if not archive.exists():
        raise FileNotFoundError(f'Archive not found: {archive}')

    with zipfile.ZipFile(archive, 'r') as zf:
        return zf.namelist()


def get_archive_size(archive_path: str | Path) -> int:
    """Get the size of an archive file in bytes.

    Args:
        archive_path: Path to ZIP file.

    Returns:
        Size in bytes.

    Raises:
        FileNotFoundError: If archive does not exist.
    """
    archive = Path(archive_path).resolve()

    if not archive.exists():
        raise FileNotFoundError(f'Archive not found: {archive}')

    return archive.stat().st_size


__all__ = [
    'ProgressCallback',
    'ArchiveFilter',
    'create_archive',
    'create_archive_from_git',
    'extract_archive',
    'list_archive_contents',
    'get_archive_size',
]
