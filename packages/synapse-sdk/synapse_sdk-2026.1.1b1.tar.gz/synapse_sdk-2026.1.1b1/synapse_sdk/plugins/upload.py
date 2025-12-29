"""Plugin upload utilities for archiving and uploading plugins to storage."""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.errors import ArchiveError, BuildError, PluginUploadError
from synapse_sdk.utils.file.archive import create_archive_from_git, get_archive_size
from synapse_sdk.utils.file.checksum import calculate_checksum

if TYPE_CHECKING:
    from synapse_sdk.utils.storage import StorageProtocol


# Progress callback signature: (stage, current, total)
UploadProgressCallback = Callable[[str, int, int], None]


class PackageManager(StrEnum):
    """Supported package managers for building wheels."""

    UV = 'uv'
    POETRY = 'poetry'
    PIP = 'pip'


class UploadStage(StrEnum):
    """Upload operation stages for progress tracking."""

    ARCHIVING = 'archiving'
    CHECKSUMMING = 'checksumming'
    BUILDING = 'building'
    UPLOADING = 'uploading'
    VERIFYING = 'verifying'


@dataclass
class UploadResult:
    """Result of a plugin upload operation.

    Attributes:
        url: Storage URL of uploaded file.
        checksum: MD5 checksum of uploaded file.
        filename: Name of uploaded file.
        size: Size in bytes.
        is_cached: True if file already existed in storage.
    """

    url: str
    checksum: str
    filename: str
    size: int
    is_cached: bool = False


@dataclass
class BuildConfig:
    """Configuration for wheel building.

    Attributes:
        package_manager: Build tool to use (uv, poetry, pip).
        python_path: Path to Python interpreter (auto-detected if None).
        extra_args: Additional arguments to pass to build command.
    """

    package_manager: PackageManager = PackageManager.UV
    python_path: Path | None = None
    extra_args: list[str] = field(default_factory=list)


def _get_storage(storage: StorageProtocol | dict[str, Any]) -> StorageProtocol:
    """Convert storage config to StorageProtocol instance.

    Args:
        storage: StorageProtocol instance or config dict.

    Returns:
        StorageProtocol instance.

    Raises:
        PluginUploadError: If storage configuration is invalid.
    """
    # Check if it's already a StorageProtocol instance
    # We check for the presence of required methods
    if hasattr(storage, 'upload') and hasattr(storage, 'exists') and hasattr(storage, 'get_url'):
        return storage  # type: ignore[return-value]

    # Convert dict config to storage instance
    if isinstance(storage, dict):
        from synapse_sdk.utils.storage import get_storage

        try:
            return get_storage(storage)
        except Exception as e:
            raise PluginUploadError(
                f'Invalid storage configuration: {e}',
                details={'config': storage},
            ) from e

    raise PluginUploadError(
        'Invalid storage type. Expected StorageProtocol or dict.',
        details={'type': type(storage).__name__},
    )


def _report_progress(
    callback: UploadProgressCallback | None,
    stage: UploadStage,
    current: int,
    total: int,
) -> None:
    """Report progress if callback is provided."""
    if callback:
        callback(stage.value, current, total)


def _get_build_command(config: BuildConfig, source_path: Path) -> list[str]:
    """Generate build command based on package manager.

    Args:
        config: Build configuration.
        source_path: Plugin source directory.

    Returns:
        Command as list of strings.

    Raises:
        BuildError: If package manager is not supported.
    """
    python = str(config.python_path) if config.python_path else 'python'

    match config.package_manager:
        case PackageManager.UV:
            return ['uv', 'build', '--wheel', *config.extra_args]
        case PackageManager.POETRY:
            return ['poetry', 'build', '--format', 'wheel', *config.extra_args]
        case PackageManager.PIP:
            return [python, '-m', 'build', '--wheel', *config.extra_args]
        case _:
            raise BuildError(
                f'Unsupported package manager: {config.package_manager}',
                details={'package_manager': config.package_manager},
            )


def archive_plugin(
    source_path: str | Path,
    archive_path: str | Path | None = None,
    *,
    use_git: bool = True,
    progress_callback: UploadProgressCallback | None = None,
) -> tuple[Path, str]:
    """Archive a plugin directory.

    Creates a ZIP archive of the plugin source code. When use_git=True,
    uses git ls-files to determine which files to include.

    Args:
        source_path: Plugin source directory.
        archive_path: Output path (auto-generated in temp dir if None).
        use_git: Use git ls-files for file selection.
        progress_callback: Optional progress callback.

    Returns:
        Tuple of (archive_path, checksum).

    Raises:
        ArchiveError: If archiving fails.
        FileNotFoundError: If source_path does not exist.

    Example:
        >>> archive_path, checksum = archive_plugin('/path/to/plugin')
        >>> print(f'Created {archive_path} with checksum {checksum}')
    """
    source = Path(source_path).resolve()

    if not source.exists():
        raise FileNotFoundError(f'Source path not found: {source}')

    # Generate archive path if not provided
    if archive_path is None:
        temp_dir = tempfile.mkdtemp()
        archive = Path(temp_dir) / 'archive.zip'
    else:
        archive = Path(archive_path).resolve()

    _report_progress(progress_callback, UploadStage.ARCHIVING, 0, 100)

    try:
        if use_git:
            create_archive_from_git(source, archive)
        else:
            from synapse_sdk.utils.file.archive import create_archive

            create_archive(source, archive)
    except Exception as e:
        raise ArchiveError(
            f'Failed to create archive: {e}',
            details={'source': str(source), 'archive': str(archive)},
        ) from e

    _report_progress(progress_callback, UploadStage.ARCHIVING, 100, 100)

    # Calculate checksum
    _report_progress(progress_callback, UploadStage.CHECKSUMMING, 0, 1)
    checksum = calculate_checksum(archive)
    _report_progress(progress_callback, UploadStage.CHECKSUMMING, 1, 1)

    return archive, checksum


def archive_and_upload(
    source_path: str | Path,
    storage: StorageProtocol | dict[str, Any],
    *,
    target_prefix: str = '',
    use_git: bool = True,
    skip_existing: bool = True,
    progress_callback: UploadProgressCallback | None = None,
) -> UploadResult:
    """Archive plugin and upload to storage.

    Creates a ZIP archive with checksum-based naming (dev-{checksum}.zip).
    If skip_existing=True and file exists in storage, returns cached URL.

    Args:
        source_path: Plugin source directory.
        storage: Storage provider or config dict.
        target_prefix: Optional prefix for target path.
        use_git: Use git ls-files for file selection.
        skip_existing: Skip upload if file exists in storage.
        progress_callback: Optional progress callback.

    Returns:
        UploadResult with URL, checksum, and metadata.

    Raises:
        ArchiveError: If archiving fails.
        PluginUploadError: If upload fails.

    Example:
        >>> result = archive_and_upload(
        ...     '/path/to/plugin',
        ...     {'provider': 's3', 'configuration': {...}},
        ... )
        >>> print(result.url)
    """
    storage_provider = _get_storage(storage)
    source = Path(source_path).resolve()

    # Create archive and get checksum
    archive_path, checksum = archive_plugin(
        source,
        use_git=use_git,
        progress_callback=progress_callback,
    )

    # Build target filename with checksum
    filename = f'dev-{checksum}.zip'
    target_path = f'{target_prefix}{filename}' if target_prefix else filename

    try:
        # Check if already exists in storage
        if skip_existing and storage_provider.exists(target_path):
            url = storage_provider.get_url(target_path)
            return UploadResult(
                url=url,
                checksum=checksum,
                filename=filename,
                size=get_archive_size(archive_path),
                is_cached=True,
            )

        # Upload to storage
        _report_progress(progress_callback, UploadStage.UPLOADING, 0, 100)
        url = storage_provider.upload(archive_path, target_path)
        _report_progress(progress_callback, UploadStage.UPLOADING, 100, 100)

        return UploadResult(
            url=url,
            checksum=checksum,
            filename=filename,
            size=get_archive_size(archive_path),
            is_cached=False,
        )

    except Exception as e:
        if isinstance(e, PluginUploadError):
            raise
        raise PluginUploadError(
            f'Failed to upload archive: {e}',
            details={'target': target_path},
        ) from e
    finally:
        # Clean up temp archive
        if archive_path.exists():
            archive_path.unlink(missing_ok=True)


def modify_wheel_build_tag(
    wheel_path: str | Path,
    build_tag: str,
) -> Path:
    """Modify wheel filename to embed build tag (checksum).

    Converts: package-1.0.0-py3-none-any.whl
    To:       package-1.0.0+{build_tag}-py3-none-any.whl

    Args:
        wheel_path: Path to wheel file.
        build_tag: Build tag to embed (typically checksum).

    Returns:
        Path to renamed wheel file.

    Raises:
        ValueError: If wheel filename format is invalid.

    Example:
        >>> new_path = modify_wheel_build_tag('/path/to/pkg-1.0.0-py3-none-any.whl', 'abc123')
        >>> print(new_path.name)
        'pkg-1.0.0+abc123-py3-none-any.whl'
    """
    path = Path(wheel_path)

    # Wheel filename format: {name}-{version}[-{build}]-{python}-{abi}-{platform}.whl
    # Minimum components: name-version-python-abi-platform.whl = 5 parts
    parts = path.stem.split('-')

    if len(parts) < 5:
        raise ValueError(f'Invalid wheel filename format: {path.name}')

    # Version is always the second part
    # It may already contain a build tag (after +)
    version = parts[1].split('+')[0]

    # Insert build tag into version
    parts[1] = f'{version}+{build_tag}'

    # Reconstruct filename
    new_name = '-'.join(parts) + '.whl'
    new_path = path.parent / new_name

    # Rename the file
    path.rename(new_path)

    return new_path


def build_and_upload(
    source_path: str | Path,
    storage: StorageProtocol | dict[str, Any],
    *,
    build_config: BuildConfig | None = None,
    target_prefix: str = '',
    skip_existing: bool = True,
    progress_callback: UploadProgressCallback | None = None,
) -> UploadResult:
    """Build wheel and upload to storage.

    Creates archive, calculates checksum, builds wheel, embeds checksum
    in wheel filename build tag, and uploads to storage.

    Args:
        source_path: Plugin source directory with pyproject.toml.
        storage: Storage provider or config dict.
        build_config: Build configuration (defaults to uv).
        target_prefix: Optional prefix for target path.
        skip_existing: Skip upload if file exists in storage.
        progress_callback: Optional progress callback.

    Returns:
        UploadResult with wheel URL, checksum, and metadata.

    Raises:
        BuildError: If wheel build fails.
        PluginUploadError: If upload fails.

    Example:
        >>> result = build_and_upload(
        ...     '/path/to/plugin',
        ...     {'provider': 's3', 'configuration': {...}},
        ...     build_config=BuildConfig(package_manager=PackageManager.UV),
        ... )
        >>> print(result.url)
    """
    storage_provider = _get_storage(storage)
    source = Path(source_path).resolve()

    if build_config is None:
        build_config = BuildConfig()

    # Check for pyproject.toml
    if not (source / 'pyproject.toml').exists():
        raise BuildError(
            'No pyproject.toml found in source directory',
            details={'source': str(source)},
        )

    # Create archive and get checksum
    archive_path, checksum = archive_plugin(
        source,
        use_git=True,
        progress_callback=progress_callback,
    )

    # Check if already exists in storage (use checksum-based wheel name pattern)
    # The wheel name will contain the checksum as build tag
    if skip_existing:
        # Try to find existing wheel with this checksum
        # Format: name-version+checksum-py3-none-any.whl
        # We can't know the exact name without building, so we check after build
        pass

    # Build wheel
    _report_progress(progress_callback, UploadStage.BUILDING, 0, 100)

    dist_dir = source / 'dist'
    dist_dir.mkdir(exist_ok=True)

    # Clean existing wheel files
    for whl_file in dist_dir.glob('*.whl'):
        whl_file.unlink()

    build_cmd = _get_build_command(build_config, source)

    try:
        subprocess.run(
            build_cmd,
            cwd=source,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise BuildError(
            f'Wheel build failed: {e.stderr}',
            details={
                'command': ' '.join(build_cmd),
                'returncode': e.returncode,
                'stdout': e.stdout,
                'stderr': e.stderr,
            },
        ) from e
    except FileNotFoundError as e:
        raise BuildError(
            f'Build command not found: {build_cmd[0]}. Is it installed?',
            details={'command': build_cmd[0]},
        ) from e

    _report_progress(progress_callback, UploadStage.BUILDING, 100, 100)

    # Find built wheel
    wheel_files = list(dist_dir.glob('*.whl'))
    if not wheel_files:
        raise BuildError(
            'No wheel file found after build',
            details={'dist_dir': str(dist_dir)},
        )

    wheel_path = wheel_files[0]

    # Embed checksum in wheel filename
    wheel_path = modify_wheel_build_tag(wheel_path, checksum)

    filename = wheel_path.name
    target_path = f'{target_prefix}{filename}' if target_prefix else filename

    try:
        # Check if already exists
        if skip_existing and storage_provider.exists(target_path):
            url = storage_provider.get_url(target_path)
            return UploadResult(
                url=url,
                checksum=checksum,
                filename=filename,
                size=wheel_path.stat().st_size,
                is_cached=True,
            )

        # Upload wheel
        _report_progress(progress_callback, UploadStage.UPLOADING, 0, 100)
        url = storage_provider.upload(wheel_path, target_path)
        _report_progress(progress_callback, UploadStage.UPLOADING, 100, 100)

        return UploadResult(
            url=url,
            checksum=checksum,
            filename=filename,
            size=wheel_path.stat().st_size,
            is_cached=False,
        )

    except Exception as e:
        if isinstance(e, (PluginUploadError, BuildError)):
            raise
        raise PluginUploadError(
            f'Failed to upload wheel: {e}',
            details={'target': target_path},
        ) from e
    finally:
        # Clean up temp archive
        if archive_path.exists():
            archive_path.unlink(missing_ok=True)


def download_and_upload(
    source_url: str,
    storage: StorageProtocol | dict[str, Any],
    *,
    target_prefix: str = '',
    skip_existing: bool = True,
    progress_callback: UploadProgressCallback | None = None,
) -> UploadResult:
    """Download file from URL and upload to storage.

    Downloads the file, calculates checksum, and re-uploads with
    checksum-based naming to the target storage.

    Args:
        source_url: URL to download from.
        storage: Storage provider or config dict.
        target_prefix: Optional prefix for target path.
        skip_existing: Skip upload if file exists in storage.
        progress_callback: Optional progress callback.

    Returns:
        UploadResult with storage URL, checksum, and metadata.

    Raises:
        PluginUploadError: If download or upload fails.

    Example:
        >>> result = download_and_upload(
        ...     'https://example.com/plugin.zip',
        ...     {'provider': 's3', 'configuration': {...}},
        ... )
        >>> print(result.url)
    """
    from synapse_sdk.utils.file.download import download_file

    storage_provider = _get_storage(storage)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Download file
        try:
            downloaded_path = download_file(source_url, temp_path)
        except Exception as e:
            raise PluginUploadError(
                f'Failed to download file: {e}',
                details={'url': source_url},
            ) from e

        # Calculate checksum
        _report_progress(progress_callback, UploadStage.CHECKSUMMING, 0, 1)
        checksum = calculate_checksum(downloaded_path)
        _report_progress(progress_callback, UploadStage.CHECKSUMMING, 1, 1)

        # Build target filename with checksum
        filename = f'dev-{checksum}.zip'
        target_path = f'{target_prefix}{filename}' if target_prefix else filename

        try:
            # Check if already exists
            if skip_existing and storage_provider.exists(target_path):
                url = storage_provider.get_url(target_path)
                return UploadResult(
                    url=url,
                    checksum=checksum,
                    filename=filename,
                    size=downloaded_path.stat().st_size,
                    is_cached=True,
                )

            # Upload to storage
            _report_progress(progress_callback, UploadStage.UPLOADING, 0, 100)
            url = storage_provider.upload(downloaded_path, target_path)
            _report_progress(progress_callback, UploadStage.UPLOADING, 100, 100)

            return UploadResult(
                url=url,
                checksum=checksum,
                filename=filename,
                size=downloaded_path.stat().st_size,
                is_cached=False,
            )

        except Exception as e:
            if isinstance(e, PluginUploadError):
                raise
            raise PluginUploadError(
                f'Failed to upload file: {e}',
                details={'target': target_path},
            ) from e


__all__ = [
    # Enums
    'PackageManager',
    'UploadStage',
    # Dataclasses
    'UploadResult',
    'BuildConfig',
    # Type aliases
    'UploadProgressCallback',
    # Functions
    'archive_plugin',
    'archive_and_upload',
    'build_and_upload',
    'download_and_upload',
    'modify_wheel_build_tag',
]
