"""Plugin publish command implementation."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from synapse_sdk.clients.backend import BackendClient
from synapse_sdk.plugins.discovery import PluginDiscovery
from synapse_sdk.plugins.errors import ArchiveError, PluginUploadError
from synapse_sdk.utils.file.archive import (
    ArchiveFilter,
    create_archive,
    get_archive_size,
    list_archive_contents,
)
from synapse_sdk.utils.file.checksum import calculate_checksum

if TYPE_CHECKING:
    from synapse_sdk.cli.auth import AuthConfig


@dataclass
class PublishResult:
    """Result of plugin publish operation."""

    release_id: int
    version: str
    checksum: str
    file_count: int
    archive_size: int


def load_synapseignore(path: Path) -> list[str]:
    """Load patterns from .synapseignore file.

    Supports gitignore-style patterns:
    - `*.pyc` - glob patterns
    - `__pycache__/` - directories
    - `# comment` - comments

    Args:
        path: Plugin directory path.

    Returns:
        List of exclude patterns.
    """
    ignore_file = path / '.synapseignore'
    patterns: list[str] = []

    if ignore_file.exists():
        with ignore_file.open() as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    patterns.append(line)

    return patterns


def find_config_file(path: Path, config_path: Path | None = None) -> Path:
    """Find plugin configuration file.

    Search order:
    1. Explicit --config path
    2. config.yaml in path
    3. synapse.yaml in path

    Args:
        path: Plugin directory.
        config_path: Explicit config path from --config.

    Returns:
        Path to config file.

    Raises:
        FileNotFoundError: If no config found.
    """
    if config_path:
        if not config_path.exists():
            raise FileNotFoundError(f'Config file not found: {config_path}')
        return config_path

    for name in ('config.yaml', 'synapse.yaml'):
        candidate = path / name
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f'No config.yaml or synapse.yaml found in {path}. Use --config to specify a custom path.')


def create_plugin_archive(
    source_path: Path,
    console: Console,
) -> tuple[Path, str, list[str]]:
    """Create plugin archive with progress display.

    Args:
        source_path: Plugin directory.
        console: Rich console for output.

    Returns:
        Tuple of (archive_path, checksum, file_list).

    Raises:
        ArchiveError: If archive creation fails.
    """
    # Load ignore patterns
    ignore_patterns = load_synapseignore(source_path)

    # Create filter with custom and default excludes
    archive_filter = ArchiveFilter.from_patterns(
        exclude=ignore_patterns,
        use_defaults=True,
    )

    # Create temp archive
    temp_dir = tempfile.mkdtemp()
    archive_path = Path(temp_dir) / 'plugin.zip'

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn('[progress.description]{task.description}'),
            console=console,
        ) as progress:
            task = progress.add_task('Creating archive...', total=None)

            create_archive(
                source_path,
                archive_path,
                filter=archive_filter,
            )

            progress.update(task, description='Calculating checksum...')
            checksum = calculate_checksum(archive_path)

    except Exception as e:
        raise ArchiveError(f'Failed to create archive: {e}') from e

    # Get file list for display
    file_list = list_archive_contents(archive_path)

    return archive_path, checksum, file_list


def display_files_preview(
    file_list: list[str],
    archive_size: int,
    console: Console,
) -> None:
    """Display preview of files to be uploaded.

    Args:
        file_list: List of files in archive.
        archive_size: Archive size in bytes.
        console: Rich console for output.
    """
    table = Table(title='Files to upload', show_lines=False, show_header=False)
    table.add_column('File', style='cyan')

    # Show first 15 files
    for file_path in sorted(file_list)[:15]:
        table.add_row(file_path)

    if len(file_list) > 15:
        table.add_row(f'... and {len(file_list) - 15} more files', style='dim')

    console.print(table)
    console.print(f'\nTotal: [bold]{len(file_list)}[/bold] files, [bold]{archive_size / 1024:.1f} KB[/bold]')


def publish_plugin(
    path: Path,
    auth: AuthConfig,
    console: Console,
    *,
    config_path: Path | None = None,
    dry_run: bool = False,
    debug: bool = False,
) -> PublishResult:
    """Execute plugin publish workflow.

    Args:
        path: Plugin directory.
        auth: Authentication config.
        console: Rich console.
        config_path: Optional explicit config path.
        dry_run: If True, skip actual upload.

    Returns:
        PublishResult with release details.

    Raises:
        FileNotFoundError: If config not found.
        ArchiveError: If archive creation fails.
        PluginUploadError: If upload fails.
    """
    # 0. Check authentication
    if not auth.access_token:
        console.print('[red]Error:[/red] Not authenticated. Run [bold]synapse login[/bold] to authenticate.')
        raise PluginUploadError('Not authenticated. Run `synapse login` to authenticate.')

    # 1. Find and load config
    config_file = find_config_file(path, config_path)
    console.print(f'[dim]Using config:[/dim] {config_file}')

    discovery = PluginDiscovery.from_path(config_file)
    config = discovery.config

    # 1.5. Sync input_type/output_type from code to config.yaml
    try:
        changes = discovery.sync_config_file(config_file)
        if changes:
            console.print('[dim]Synced types from code:[/dim]')
            for action_name, type_info in changes.items():
                console.print(f'  [cyan]{action_name}[/cyan]: {type_info}')
            # Reload discovery after sync
            discovery = PluginDiscovery.from_path(config_file)
            config = discovery.config
    except Exception as e:
        console.print(f'[yellow]Warning: Could not sync types: {e}[/yellow]')

    # Display plugin info
    actions_str = ', '.join(discovery.list_actions())
    console.print(
        Panel(
            f'[bold]{config.name}[/bold] v{config.version}\n'
            f'Code: {config.code}\n'
            f'Category: {config.category.value}\n'
            f'Actions: {actions_str}',
            title='Plugin',
            border_style='blue',
        )
    )

    # 2. Create archive
    archive_path, checksum, file_list = create_plugin_archive(path, console)
    archive_size = get_archive_size(archive_path)

    # 3. Display preview
    display_files_preview(file_list, archive_size, console)

    if dry_run:
        console.print('\n[yellow]Dry run - skipping upload[/yellow]')
        # Clean up temp file
        archive_path.unlink(missing_ok=True)
        return PublishResult(
            release_id=0,
            version=config.version,
            checksum=checksum,
            file_count=len(file_list),
            archive_size=archive_size,
        )

    # 4. Upload to backend
    try:
        client = BackendClient(
            base_url=auth.host,
            access_token=auth.access_token,
        )

        with Progress(
            SpinnerColumn(),
            TextColumn('[progress.description]{task.description}'),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task('Uploading...', total=100)

            # Prepare release data
            release_data = {
                'plugin': config.code,
                'version': config.version,
                'config': discovery.to_config_dict(include_ui_schemas=True),
                'debug': debug,
            }

            # Create release with file upload
            response = client.create_plugin_release(
                release_data,
                file=archive_path,
            )

            progress.update(task, completed=100)

        if debug:
            console.print(f'[dim]Response: {response}[/dim]')

        release_id = response.get('id', 0)

    except Exception as e:
        raise PluginUploadError(f'Failed to upload plugin: {e}') from e
    finally:
        # Clean up temp file
        archive_path.unlink(missing_ok=True)

    return PublishResult(
        release_id=release_id,
        version=config.version,
        checksum=checksum,
        file_count=len(file_list),
        archive_size=archive_size,
    )


__all__ = [
    'PublishResult',
    'load_synapseignore',
    'find_config_file',
    'create_plugin_archive',
    'display_files_preview',
    'publish_plugin',
]
