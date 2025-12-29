---
sidebar_label: archive
title: synapse_sdk.utils.file.archive
---

Archive utilities for creating and extracting ZIP files.

## ArchiveFilter Objects

```python
class ArchiveFilter()
```

Filter for selecting files to include in archive.

Supports glob patterns for include/exclude filtering.
Default excludes common non-essential directories and files.

**Example**:

  >>> filter = ArchiveFilter.from_patterns(exclude=['*.pyc', '__pycache__'])
  >>> filter.should_include(Path('src/main.py'), Path('/project'))
  True
  >>> filter.should_include(Path('__pycache__/cache.pyc'), Path('/project'))
  False

#### from\_patterns

```python
@classmethod
def from_patterns(cls,
                  include: Iterable[str] | None = None,
                  exclude: Iterable[str] | None = None,
                  *,
                  use_defaults: bool = True) -> ArchiveFilter
```

Create filter from glob patterns.

**Arguments**:

- `include` - Patterns for files to include.
- `exclude` - Patterns for files to exclude.
- `use_defaults` - Include DEFAULT_EXCLUDES in exclude patterns.
  

**Returns**:

  Configured ArchiveFilter instance.

#### should\_include

```python
def should_include(path: Path, relative_to: Path) -> bool
```

Check if path should be included in archive.

**Arguments**:

- `path` - Absolute path to check.
- `relative_to` - Base path for relative path calculation.
  

**Returns**:

  True if file should be included.

#### create\_archive

```python
def create_archive(source_path: str | Path,
                   archive_path: str | Path,
                   *,
                   filter: ArchiveFilter | None = None,
                   compression: Literal['stored', 'deflated', 'bzip2',
                                        'lzma'] = 'deflated',
                   compression_level: int = 6,
                   progress_callback: ProgressCallback | None = None) -> Path
```

Create a ZIP archive from source directory.

Uses pure Python zipfile module for cross-platform compatibility
and security (no shell execution).

**Arguments**:

- `source_path` - Directory to archive.
- `archive_path` - Output ZIP file path.
- `filter` - File filter (defaults to ArchiveFilter with DEFAULT_EXCLUDES).
- `compression` - Compression method.
- `compression_level` - Compression level (1-9 for deflated, ignored for others).
- `progress_callback` - Optional callback for progress updates.
  

**Returns**:

  Path to created archive.
  

**Raises**:

- `FileNotFoundError` - If source_path does not exist.
- `NotADirectoryError` - If source_path is not a directory.
  

**Example**:

  >>> archive_path = create_archive('/path/to/project', '/tmp/project.zip')

#### create\_archive\_from\_git

```python
def create_archive_from_git(
        source_path: str | Path,
        archive_path: str | Path,
        *,
        include_untracked: bool = True,
        compression: Literal['stored', 'deflated', 'bzip2',
                             'lzma'] = 'deflated',
        compression_level: int = 6,
        progress_callback: ProgressCallback | None = None) -> Path
```

Create archive from git-tracked files only.

Uses `git ls-files` to determine which files to include,
but creates the archive with pure Python zipfile (no shell=True).

**Arguments**:

- `source_path` - Git repository directory.
- `archive_path` - Output ZIP file path.
- `include_untracked` - Include untracked files (--others --exclude-standard).
- `compression` - Compression method.
- `compression_level` - Compression level (1-9 for deflated).
- `progress_callback` - Optional callback for progress updates.
  

**Returns**:

  Path to created archive.
  

**Raises**:

- `FileNotFoundError` - If source_path does not exist.
- `RuntimeError` - If not a git repository or git command fails.
  

**Example**:

  >>> archive_path = create_archive_from_git('/path/to/repo', '/tmp/repo.zip')

#### extract\_archive

```python
def extract_archive(archive_path: str | Path,
                    output_path: str | Path,
                    *,
                    progress_callback: ProgressCallback | None = None) -> Path
```

Extract a ZIP archive.

**Arguments**:

- `archive_path` - Path to ZIP file.
- `output_path` - Directory to extract to.
- `progress_callback` - Optional callback for progress updates.
  

**Returns**:

  Path to extraction directory.
  

**Raises**:

- `FileNotFoundError` - If archive does not exist.
- `zipfile.BadZipFile` - If archive is invalid.
  

**Example**:

  >>> output_dir = extract_archive('/path/to/archive.zip', '/tmp/extracted')

#### list\_archive\_contents

```python
def list_archive_contents(archive_path: str | Path) -> list[str]
```

List files in archive without extracting.

**Arguments**:

- `archive_path` - Path to ZIP file.
  

**Returns**:

  List of file paths in archive.
  

**Raises**:

- `FileNotFoundError` - If archive does not exist.
- `zipfile.BadZipFile` - If archive is invalid.
  

**Example**:

  >>> files = list_archive_contents('/path/to/archive.zip')
  >>> print(files)
  ['src/main.py', 'src/utils.py', 'README.md']

#### get\_archive\_size

```python
def get_archive_size(archive_path: str | Path) -> int
```

Get the size of an archive file in bytes.

**Arguments**:

- `archive_path` - Path to ZIP file.
  

**Returns**:

  Size in bytes.
  

**Raises**:

- `FileNotFoundError` - If archive does not exist.

