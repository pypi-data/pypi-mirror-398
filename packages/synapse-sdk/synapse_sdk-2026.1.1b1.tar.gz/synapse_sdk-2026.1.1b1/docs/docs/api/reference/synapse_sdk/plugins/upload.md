---
sidebar_label: upload
title: synapse_sdk.plugins.upload
---

Plugin upload utilities for archiving and uploading plugins to storage.

## PackageManager Objects

```python
class PackageManager(StrEnum)
```

Supported package managers for building wheels.

## UploadStage Objects

```python
class UploadStage(StrEnum)
```

Upload operation stages for progress tracking.

## UploadResult Objects

```python
@dataclass
class UploadResult()
```

Result of a plugin upload operation.

**Attributes**:

- `url` - Storage URL of uploaded file.
- `checksum` - MD5 checksum of uploaded file.
- `filename` - Name of uploaded file.
- `size` - Size in bytes.
- `is_cached` - True if file already existed in storage.

## BuildConfig Objects

```python
@dataclass
class BuildConfig()
```

Configuration for wheel building.

**Attributes**:

- `package_manager` - Build tool to use (uv, poetry, pip).
- `python_path` - Path to Python interpreter (auto-detected if None).
- `extra_args` - Additional arguments to pass to build command.

#### archive\_plugin

```python
def archive_plugin(
    source_path: str | Path,
    archive_path: str | Path | None = None,
    *,
    use_git: bool = True,
    progress_callback: UploadProgressCallback | None = None
) -> tuple[Path, str]
```

Archive a plugin directory.

Creates a ZIP archive of the plugin source code. When use_git=True,
uses git ls-files to determine which files to include.

**Arguments**:

- `source_path` - Plugin source directory.
- `archive_path` - Output path (auto-generated in temp dir if None).
- `use_git` - Use git ls-files for file selection.
- `progress_callback` - Optional progress callback.
  

**Returns**:

  Tuple of (archive_path, checksum).
  

**Raises**:

- `ArchiveError` - If archiving fails.
- `FileNotFoundError` - If source_path does not exist.
  

**Example**:

  >>> archive_path, checksum = archive_plugin('/path/to/plugin')
  >>> print(f'Created \{archive_path\} with checksum \{checksum\}')

#### archive\_and\_upload

```python
def archive_and_upload(
        source_path: str | Path,
        storage: StorageProtocol | dict[str, Any],
        *,
        target_prefix: str = '',
        use_git: bool = True,
        skip_existing: bool = True,
        progress_callback: UploadProgressCallback | None = None
) -> UploadResult
```

Archive plugin and upload to storage.

Creates a ZIP archive with checksum-based naming (dev-\{checksum\}.zip).
If skip_existing=True and file exists in storage, returns cached URL.

**Arguments**:

- `source_path` - Plugin source directory.
- `storage` - Storage provider or config dict.
- `target_prefix` - Optional prefix for target path.
- `use_git` - Use git ls-files for file selection.
- `skip_existing` - Skip upload if file exists in storage.
- `progress_callback` - Optional progress callback.
  

**Returns**:

  UploadResult with URL, checksum, and metadata.
  

**Raises**:

- `ArchiveError` - If archiving fails.
- `PluginUploadError` - If upload fails.
  

**Example**:

  >>> result = archive_and_upload(
  ...     '/path/to/plugin',
  ...     \{'provider': 's3', 'configuration': \{...\}\},
  ... )
  >>> print(result.url)

#### modify\_wheel\_build\_tag

```python
def modify_wheel_build_tag(wheel_path: str | Path, build_tag: str) -> Path
```

Modify wheel filename to embed build tag (checksum).

Converts: package-1.0.0-py3-none-any.whl
To:       package-1.0.0+\{build_tag\}-py3-none-any.whl

**Arguments**:

- `wheel_path` - Path to wheel file.
- `build_tag` - Build tag to embed (typically checksum).
  

**Returns**:

  Path to renamed wheel file.
  

**Raises**:

- `ValueError` - If wheel filename format is invalid.
  

**Example**:

  >>> new_path = modify_wheel_build_tag('/path/to/pkg-1.0.0-py3-none-any.whl', 'abc123')
  >>> print(new_path.name)
  'pkg-1.0.0+abc123-py3-none-any.whl'

#### build\_and\_upload

```python
def build_and_upload(
        source_path: str | Path,
        storage: StorageProtocol | dict[str, Any],
        *,
        build_config: BuildConfig | None = None,
        target_prefix: str = '',
        skip_existing: bool = True,
        progress_callback: UploadProgressCallback | None = None
) -> UploadResult
```

Build wheel and upload to storage.

Creates archive, calculates checksum, builds wheel, embeds checksum
in wheel filename build tag, and uploads to storage.

**Arguments**:

- `source_path` - Plugin source directory with pyproject.toml.
- `storage` - Storage provider or config dict.
- `build_config` - Build configuration (defaults to uv).
- `target_prefix` - Optional prefix for target path.
- `skip_existing` - Skip upload if file exists in storage.
- `progress_callback` - Optional progress callback.
  

**Returns**:

  UploadResult with wheel URL, checksum, and metadata.
  

**Raises**:

- `BuildError` - If wheel build fails.
- `PluginUploadError` - If upload fails.
  

**Example**:

  >>> result = build_and_upload(
  ...     '/path/to/plugin',
  ...     \{'provider': 's3', 'configuration': \{...\}\},
  ...     build_config=BuildConfig(package_manager=PackageManager.UV),
  ... )
  >>> print(result.url)

#### download\_and\_upload

```python
def download_and_upload(
        source_url: str,
        storage: StorageProtocol | dict[str, Any],
        *,
        target_prefix: str = '',
        skip_existing: bool = True,
        progress_callback: UploadProgressCallback | None = None
) -> UploadResult
```

Download file from URL and upload to storage.

Downloads the file, calculates checksum, and re-uploads with
checksum-based naming to the target storage.

**Arguments**:

- `source_url` - URL to download from.
- `storage` - Storage provider or config dict.
- `target_prefix` - Optional prefix for target path.
- `skip_existing` - Skip upload if file exists in storage.
- `progress_callback` - Optional progress callback.
  

**Returns**:

  UploadResult with storage URL, checksum, and metadata.
  

**Raises**:

- `PluginUploadError` - If download or upload fails.
  

**Example**:

  >>> result = download_and_upload(
  ...     'https://example.com/plugin.zip',
  ...     \{'provider': 's3', 'configuration': \{...\}\},
  ... )
  >>> print(result.url)

