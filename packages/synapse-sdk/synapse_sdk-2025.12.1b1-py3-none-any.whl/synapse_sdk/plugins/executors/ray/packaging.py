"""Utilities for packaging and uploading working directories to Ray GCS."""

from __future__ import annotations

import tempfile
from pathlib import Path


def upload_working_dir_to_gcs(working_dir: str | Path) -> str:
    """Package a local directory and upload to Ray's Global Control Store.

    Ray's working_dir with remote clusters requires the directory to be
    uploaded to a location Ray workers can access. This function:
    1. Creates a zip archive of the directory
    2. Uploads it to Ray's GCS (content-addressable storage)
    3. Returns the gcs:// URI for use in runtime_env

    Args:
        working_dir: Local directory path to package and upload.

    Returns:
        gcs:// URI that Ray can use for working_dir.
        Example: "gcs://_ray_pkg_abc123def456.zip"

    Raises:
        RuntimeError: If Ray is not initialized or not connected.
        FileNotFoundError: If working_dir doesn't exist.

    Example:
        >>> ray.init('ray://10.0.0.4:10001')
        >>> gcs_uri = upload_working_dir_to_gcs('/path/to/plugin')
        >>> runtime_env = {'working_dir': gcs_uri}
    """
    try:
        import ray
    except ImportError:
        raise RuntimeError('Ray is not installed. Install with: pip install ray')

    if not ray.is_initialized():
        raise RuntimeError(
            'Ray must be initialized before uploading to GCS. Call ray.init() or connect to a cluster first.'
        )

    from ray._private.runtime_env.packaging import (
        get_uri_for_package,
        package_exists,
        upload_package_to_gcs,
    )

    working_dir = Path(working_dir).resolve()
    if not working_dir.exists():
        raise FileNotFoundError(f'Working directory not found: {working_dir}')

    # Import archive utilities
    from synapse_sdk.utils.file.archive import ArchiveFilter, create_archive

    # Create zip in temporary location
    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / 'working_dir.zip'

        # Create archive with default excludes
        archive_filter = ArchiveFilter.from_patterns()
        create_archive(working_dir, archive_path, filter=archive_filter)

        # Generate content-addressable gcs:// URI
        gcs_uri = get_uri_for_package(archive_path)

        # Upload if not already present (deduplication)
        if not package_exists(gcs_uri):
            upload_package_to_gcs(gcs_uri, archive_path.read_bytes())

        return gcs_uri


def upload_module_to_gcs(module_dir: str | Path) -> str:
    """Package a Python module directory and upload to Ray's GCS.

    Unlike upload_working_dir_to_gcs which archives directory contents,
    this preserves the module name in the archive so it can be imported.

    Args:
        module_dir: Path to the module directory (e.g., /path/to/synapse_sdk).

    Returns:
        gcs:// URI for use in runtime_env py_modules.

    Example:
        >>> gcs_uri = upload_module_to_gcs('/path/to/synapse_sdk')
        >>> runtime_env = {'py_modules': [gcs_uri]}
        >>> # Remote can now `import synapse_sdk`
    """
    import zipfile

    try:
        import ray
    except ImportError:
        raise RuntimeError('Ray is not installed. Install with: pip install ray')

    if not ray.is_initialized():
        raise RuntimeError('Ray must be initialized before uploading to GCS.')

    from ray._private.runtime_env.packaging import (
        get_uri_for_package,
        package_exists,
        upload_package_to_gcs,
    )

    module_dir = Path(module_dir).resolve()
    if not module_dir.exists():
        raise FileNotFoundError(f'Module directory not found: {module_dir}')

    module_name = module_dir.name  # e.g., 'synapse_sdk'

    from synapse_sdk.utils.file.archive import ArchiveFilter

    archive_filter = ArchiveFilter.from_patterns()

    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / 'module.zip'

        # Create archive with module name as root directory
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in module_dir.rglob('*'):
                if file_path.is_file() and archive_filter.should_include(file_path, module_dir):
                    # Prefix with module name so synapse_sdk/... structure is preserved
                    arcname = f'{module_name}/{file_path.relative_to(module_dir)}'
                    zf.write(file_path, arcname)

        gcs_uri = get_uri_for_package(archive_path)

        if not package_exists(gcs_uri):
            upload_package_to_gcs(gcs_uri, archive_path.read_bytes())

        return gcs_uri


__all__ = ['upload_module_to_gcs', 'upload_working_dir_to_gcs']
