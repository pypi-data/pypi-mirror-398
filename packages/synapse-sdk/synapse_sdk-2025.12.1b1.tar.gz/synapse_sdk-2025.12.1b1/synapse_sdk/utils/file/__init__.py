"""File utilities module."""

from .archive import (
    ArchiveFilter,
    ProgressCallback,
    create_archive,
    create_archive_from_git,
    extract_archive,
    get_archive_size,
    list_archive_contents,
)
from .checksum import (
    HashAlgorithm,
    calculate_checksum,
    calculate_checksum_from_bytes,
    calculate_checksum_from_file_object,
    verify_checksum,
)
from .download import (
    adownload_file,
    afiles_url_to_path,
    afiles_url_to_path_from_objs,
    download_file,
    files_url_to_path,
    files_url_to_path_from_objs,
)
from .io import get_dict_from_file, get_temp_path
from .requirements import read_requirements

__all__ = [
    # I/O
    'get_temp_path',
    'get_dict_from_file',
    # Download (sync)
    'download_file',
    'files_url_to_path',
    'files_url_to_path_from_objs',
    # Download (async)
    'adownload_file',
    'afiles_url_to_path',
    'afiles_url_to_path_from_objs',
    # Requirements
    'read_requirements',
    # Checksum
    'HashAlgorithm',
    'calculate_checksum',
    'calculate_checksum_from_bytes',
    'calculate_checksum_from_file_object',
    'verify_checksum',
    # Archive
    'ProgressCallback',
    'ArchiveFilter',
    'create_archive',
    'create_archive_from_git',
    'extract_archive',
    'list_archive_contents',
    'get_archive_size',
]
