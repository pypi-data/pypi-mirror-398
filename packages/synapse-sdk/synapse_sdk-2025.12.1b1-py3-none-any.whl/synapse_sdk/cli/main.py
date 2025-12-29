"""Synapse SDK CLI main entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel

cli = typer.Typer(
    name='synapse',
    help='Synapse SDK CLI.',
    no_args_is_help=True,
    rich_markup_mode='rich',
)
console = Console()
err_console = Console(stderr=True)

# Plugin subcommand group
plugin_app = typer.Typer(help='Plugin development commands.')
cli.add_typer(plugin_app, name='plugin')

# Job subcommand group (under plugin)
job_app = typer.Typer(help='Job management commands.')
plugin_app.add_typer(job_app, name='job')

# Agent subcommand group
agent_app = typer.Typer(help='Agent configuration commands.')
cli.add_typer(agent_app, name='agent')

# MCP subcommand group
mcp_app = typer.Typer(help='MCP server commands.')
cli.add_typer(mcp_app, name='mcp')


@job_app.command('get')
def job_get(
    job_id: Annotated[
        str,
        typer.Argument(help='Job ID (UUID) to get details for.'),
    ],
    host: Annotated[
        Optional[str],
        typer.Option('--host', help='Synapse API host.'),
    ] = None,
    token: Annotated[
        Optional[str],
        typer.Option('--token', '-t', help='Access token.'),
    ] = None,
) -> None:
    """Get job details.

    [bold]Examples:[/bold]

        synapse plugin job get 123
    """
    from synapse_sdk.cli.auth import get_auth_config
    from synapse_sdk.cli.plugin.job import display_job, get_job
    from synapse_sdk.plugins.errors import PluginError

    try:
        auth = get_auth_config(host=host, token=token, console=console, interactive=False)
        job = get_job(job_id, auth, console)
        display_job(job, console)

    except PluginError as e:
        err_console.print(f'[red]Error:[/red] {e.message}')
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f'[red]Error:[/red] {e}')
        raise typer.Exit(1)


@job_app.command('logs')
def job_logs(
    job_id: Annotated[
        str,
        typer.Argument(help='Job ID (UUID) to get logs for.'),
    ],
    follow: Annotated[
        bool,
        typer.Option('--follow', '-f', help='Follow log output (stream).'),
    ] = False,
    host: Annotated[
        Optional[str],
        typer.Option('--host', help='Synapse API host.'),
    ] = None,
    token: Annotated[
        Optional[str],
        typer.Option('--token', '-t', help='Access token.'),
    ] = None,
) -> None:
    """Get job logs.

    [bold]Examples:[/bold]

        synapse plugin job logs 123
        synapse plugin job logs 123 -f
    """
    from synapse_sdk.cli.auth import get_auth_config
    from synapse_sdk.cli.plugin.job import get_job_logs, tail_job_logs
    from synapse_sdk.plugins.errors import PluginError

    try:
        auth = get_auth_config(host=host, token=token, console=console, interactive=False)

        if follow:
            tail_job_logs(job_id, auth, console)
        else:
            logs = get_job_logs(job_id, auth, console)
            # Display logs
            if isinstance(logs, list):
                for line in logs:
                    if line:
                        console.print(line)
            elif isinstance(logs, dict):
                for entry in logs.get('results', []):
                    console.print(entry.get('message', ''))
            else:
                console.print(logs)

    except PluginError as e:
        err_console.print(f'[red]Error:[/red] {e.message}')
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f'[red]Error:[/red] {e}')
        raise typer.Exit(1)


@plugin_app.command('publish')
def plugin_publish(
    path: Annotated[
        Optional[Path],
        typer.Option('--path', '-p', help='Plugin directory (default: current).'),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option('--config', '-c', help='Config file path.'),
    ] = None,
    host: Annotated[
        Optional[str],
        typer.Option('--host', help='Synapse API host.'),
    ] = None,
    token: Annotated[
        Optional[str],
        typer.Option('--token', '-t', help='Access token.'),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option('--dry-run', help='Preview without uploading.'),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option('--debug', help='Debug mode (bypasses backend validation).'),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option('--yes', '-y', help='Skip confirmation.'),
    ] = False,
) -> None:
    """Publish a plugin release to Synapse.

    Archives plugin files and creates a new release.

    [bold]Examples:[/bold]

        synapse plugin publish
        synapse plugin publish -p ./my-plugin --dry-run
    """
    import questionary

    from synapse_sdk.cli.auth import get_auth_config
    from synapse_sdk.cli.plugin.publish import publish_plugin
    from synapse_sdk.plugins.errors import PluginError

    # Resolve path
    plugin_path = (path or Path.cwd()).resolve()

    if not plugin_path.exists():
        err_console.print(f'[red]Error:[/red] Path not found: {plugin_path}')
        raise typer.Exit(1)

    try:
        # Get authentication (never interactive - require login first)
        auth = get_auth_config(
            host=host,
            token=token,
            console=console,
            interactive=False,
        )

        # Confirmation prompt
        if not yes and not dry_run:
            if not questionary.confirm(
                f'Publish plugin to {auth.host}?',
                default=True,
            ).ask():
                console.print('[yellow]Cancelled[/yellow]')
                raise typer.Exit(0)

        # Execute publish
        result = publish_plugin(
            path=plugin_path,
            auth=auth,
            console=console,
            config_path=config,
            dry_run=dry_run,
            debug=debug,
        )

        # Success output
        if not dry_run:
            console.print(
                Panel(
                    f'[green]Published successfully![/green]\n\n'
                    f'Release ID: [bold]{result.release_id}[/bold]\n'
                    f'Version: [bold]{result.version}[/bold]\n'
                    f'Checksum: [dim]{result.checksum[:12]}...[/dim]',
                    title='Success',
                    border_style='green',
                )
            )

    except typer.BadParameter as e:
        err_console.print(f'[red]Error:[/red] {e.message}')
        raise typer.Exit(1)
    except PluginError as e:
        err_console.print(f'[red]Error:[/red] {e.message}')
        if e.details:
            err_console.print(f'[dim]Details:[/dim] {e.details}')
        raise typer.Exit(1)
    except FileNotFoundError as e:
        err_console.print(f'[red]Error:[/red] {e}')
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f'[red]Unexpected error:[/red] {e}')
        raise typer.Exit(1)


@plugin_app.command('create')
def plugin_create(
    path: Annotated[
        Optional[Path],
        typer.Option('--path', '-p', help='Output directory (default: current).'),
    ] = None,
    name: Annotated[
        Optional[str],
        typer.Option('--name', '-n', help='Plugin name.'),
    ] = None,
    code: Annotated[
        Optional[str],
        typer.Option('--code', help='Plugin code (slug).'),
    ] = None,
    category: Annotated[
        Optional[str],
        typer.Option('--category', '-c', help='Plugin category.'),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option('--yes', '-y', help='Skip confirmation.'),
    ] = False,
) -> None:
    """Create a new plugin from template.

    Interactively creates a new plugin with the specified category.

    [bold]Examples:[/bold]

        synapse plugin create
        synapse plugin create --name "My Plugin" --category neural_net
    """
    from synapse_sdk.cli.plugin.create import create_plugin_interactive

    try:
        output_dir = (path or Path.cwd()).resolve()

        result = create_plugin_interactive(
            output_dir=output_dir,
            name=name,
            code=code,
            category=category,
            console=console,
            yes=yes,
        )

        if result:
            console.print()
            console.print('[bold green]Next steps:[/bold green]')
            console.print(f'  cd {result.plugin_dir.name}')
            console.print('  uv sync')
            console.print('  synapse plugin publish --dry-run')

    except ValueError as e:
        err_console.print(f'[red]Error:[/red] {e}')
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f'[red]Unexpected error:[/red] {e}')
        raise typer.Exit(1)


@plugin_app.command('update-config')
def plugin_update_config(
    path: Annotated[
        Optional[Path],
        typer.Option('--path', '-p', help='Plugin directory (default: current).'),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option('--config', '-c', help='Config file path.'),
    ] = None,
) -> None:
    """Auto-discover actions and sync to config.yaml.

    Scans plugin source files for BaseAction subclasses and updates config.yaml:
    - Discovers new actions from code and adds them to config
    - Syncs entrypoints, input_type, output_type from code
    - Preserves other config fields (description, etc.)

    This is automatically run during `synapse plugin publish`,
    but can be run manually during development.

    [bold]Examples:[/bold]

        synapse plugin update-config
        synapse plugin update-config -p ./my-plugin
    """
    from synapse_sdk.cli.plugin.publish import find_config_file
    from synapse_sdk.plugins.discovery import PluginDiscovery
    from synapse_sdk.plugins.errors import PluginError

    # Resolve path
    plugin_path = (path or Path.cwd()).resolve()

    if not plugin_path.exists():
        err_console.print(f'[red]Error:[/red] Path not found: {plugin_path}')
        raise typer.Exit(1)

    try:
        import sys

        # Find config file
        config_file = find_config_file(plugin_path, config)
        console.print(f'[dim]Config file:[/dim] {config_file}')

        # Add plugin path to sys.path so action classes can be imported
        plugin_dir = str(plugin_path)
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)

        # Load discovery
        discovery = PluginDiscovery.from_path(config_file)

        # Sync types
        changes = discovery.sync_config_file(config_file)

        if changes:
            console.print('\n[green]Updated config.yaml:[/green]')
            for action_name, type_info in changes.items():
                console.print(f'  [cyan]{action_name}[/cyan]: {type_info}')
        else:
            console.print('[yellow]No changes needed.[/yellow]')
            console.print(
                '[dim]Actions have no input_type/output_type declarations, or config is already up to date.[/dim]'
            )

    except FileNotFoundError as e:
        err_console.print(f'[red]Error:[/red] {e}')
        raise typer.Exit(1)
    except PluginError as e:
        err_console.print(f'[red]Error:[/red] {e.message}')
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f'[red]Error:[/red] {e}')
        raise typer.Exit(1)


@plugin_app.command('run')
def plugin_run(
    action: Annotated[
        str,
        typer.Argument(help='Action to run (e.g., test, train, deploy, infer).'),
    ],
    plugin: Annotated[
        Optional[str],
        typer.Option('--plugin', '-p', help='Plugin code. Auto-detects from config.yaml if not provided.'),
    ] = None,
    plugin_path: Annotated[
        Optional[Path],
        typer.Option('--path', help='Plugin directory (default: current).'),
    ] = None,
    params: Annotated[
        Optional[str],
        typer.Option('--params', help='JSON parameters to pass to the action.'),
    ] = None,
    mode: Annotated[
        Optional[str],
        typer.Option('--mode', '-m', help='Executor mode: local, task, job, or remote.'),
    ] = None,
    ray_address: Annotated[
        str,
        typer.Option('--ray-address', help='Ray cluster address (for task/job modes).'),
    ] = 'auto',
    num_gpus: Annotated[
        Optional[int],
        typer.Option('--gpus', help='Number of GPUs to request.'),
    ] = None,
    num_cpus: Annotated[
        Optional[int],
        typer.Option('--cpus', help='Number of CPUs to request.'),
    ] = None,
    input_data: Annotated[
        Optional[str],
        typer.Option('--input', '-i', help='JSON input for inference (for infer action).'),
    ] = None,
    infer_path: Annotated[
        str,
        typer.Option('--infer-path', help='Inference endpoint path (for infer action).'),
    ] = '/',
    host: Annotated[
        Optional[str],
        typer.Option('--host', help='Synapse API host (for remote mode).'),
    ] = None,
    token: Annotated[
        Optional[str],
        typer.Option('--token', '-t', help='Access token (for remote mode).'),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option('--debug/--no-debug', help='Debug mode (default: enabled).'),
    ] = True,
    debug_sdk: Annotated[
        bool,
        typer.Option('--debug-sdk', help='Bundle local SDK with upload (for SDK development).'),
    ] = False,
) -> None:
    """Run a plugin action.

    [bold]Executor Modes:[/bold]
      - local:  In-process execution (best for debugging)
      - task:   Ray Actor execution (simulates agent)
      - job:    Ray Job submission (async, heavy workloads)
      - remote: Run via Synapse backend API (requires auth)

    [bold]Examples:[/bold]

        synapse plugin run test
        synapse plugin run test --mode local
        synapse plugin run test --mode task --gpus 1
        synapse plugin run train --mode job --params '{"epochs": 10}'
        synapse plugin run deploy --mode remote
    """
    import json

    import questionary
    from rich.panel import Panel

    from synapse_sdk.plugins.errors import PluginError

    try:
        path = (plugin_path or Path.cwd()).resolve()

        if not path.exists():
            err_console.print(f'[red]Error:[/red] Path not found: {path}')
            raise typer.Exit(1)

        # Parse params JSON
        parsed_params: dict = {}
        if params:
            try:
                parsed_params = json.loads(params)
            except json.JSONDecodeError as e:
                err_console.print(f'[red]Error:[/red] Invalid JSON params: {e}')
                raise typer.Exit(1)

        # Interactive executor selection if not provided
        if mode is None:
            mode = questionary.select(
                'Select executor mode:',
                choices=[
                    questionary.Choice('local  - In-process (best for debugging)', value='local'),
                    questionary.Choice('task   - Ray Actor (simulates agent)', value='task'),
                    questionary.Choice('job    - Ray Job (async, heavy workloads)', value='job'),
                    questionary.Choice('remote - through Synapse Backend API', value='remote'),
                ],
                default='local',
            ).ask()

            if mode is None:
                console.print('[yellow]Cancelled[/yellow]')
                raise typer.Exit(0)

        # Validate mode
        if mode not in ('local', 'task', 'job', 'remote'):
            err_console.print(f'[red]Error:[/red] Invalid mode: {mode}. Use local, task, job, or remote.')
            raise typer.Exit(1)

        # Handle local/task/job modes
        if mode in ('local', 'task', 'job'):
            from synapse_sdk.cli.plugin.test import test_plugin

            # For task/job modes, get agent config for Ray address
            resolved_ray_address = ray_address
            if mode in ('task', 'job') and ray_address == 'auto':
                from urllib.parse import urlparse

                from synapse_sdk.cli.agent.config import get_agent_config
                from synapse_sdk.cli.agent.select import select_agent_interactive
                from synapse_sdk.cli.auth import get_auth_config

                agent = get_agent_config()
                if not agent:
                    console.print('[yellow]No agent configured. Please select one.[/yellow]\n')
                    try:
                        auth = get_auth_config(host=host, token=token, console=console, interactive=False)
                        agent = select_agent_interactive(auth, console)
                        if not agent:
                            console.print('[yellow]Cancelled[/yellow]')
                            raise typer.Exit(0)
                    except Exception as e:
                        err_console.print(f'[red]Error:[/red] Failed to get agent: {e}')
                        err_console.print('[dim]Run `synapse agent select` to configure an agent.[/dim]')
                        raise typer.Exit(1)

                if agent and agent.url:
                    # Convert HTTP URL to Ray address (ray://<host>:10001)
                    parsed = urlparse(agent.url)
                    ray_host = parsed.hostname or 'localhost'
                    resolved_ray_address = f'ray://{ray_host}:10001'
                    console.print(f'[dim]Using agent:[/dim] {agent.name or agent.id}')
                    console.print(f'[dim]Ray address:[/dim] {resolved_ray_address}')

            result = test_plugin(
                action=action,
                console=console,
                path=path,
                params=parsed_params if parsed_params else None,
                mode=mode,
                ray_address=resolved_ray_address,
                num_gpus=num_gpus,
                num_cpus=num_cpus,
                include_sdk=debug_sdk,
            )

            # Success output
            console.print(
                Panel(
                    f'[green]Action completed![/green]\n\n'
                    f'Plugin: [bold]{result.plugin}[/bold]\n'
                    f'Action: [bold]{result.action}[/bold]\n'
                    f'Mode: [bold]{result.mode}[/bold]',
                    title='Success',
                    border_style='green',
                )
            )

            if result.result:
                console.print('\n[bold]Result:[/bold]')
                if isinstance(result.result, dict):
                    for key, value in result.result.items():
                        console.print(f'  {key}: {value}')
                else:
                    console.print(f'  {result.result}')

        else:  # mode == 'remote'
            from synapse_sdk.cli.agent.config import get_agent_config
            from synapse_sdk.cli.auth import get_auth_config
            from synapse_sdk.cli.plugin.run import resolve_plugin_code, run_plugin

            # Get auth configuration
            auth = get_auth_config(host=host, token=token, console=console, interactive=False)

            # Get agent configuration
            agent = get_agent_config()
            if not agent:
                err_console.print('[red]Error:[/red] No agent configured.')
                err_console.print('[dim]Run `synapse agent select` to configure an agent.[/dim]')
                raise typer.Exit(1)

            # Resolve plugin code
            plugin_code = resolve_plugin_code(plugin, path)

            # Map short action names to API action names
            action_map = {'infer': 'inference', 'deploy': 'deployment'}
            api_action = action_map.get(action, action)

            # Handle infer action
            if action == 'infer' and input_data:
                try:
                    parsed_input = json.loads(input_data)
                    parsed_params['input'] = parsed_input
                    parsed_params['path'] = infer_path
                except json.JSONDecodeError as e:
                    err_console.print(f'[red]Error:[/red] Invalid JSON input: {e}')
                    raise typer.Exit(1)

            # Execute run
            result = run_plugin(
                action=api_action,
                auth=auth,
                agent=agent,
                console=console,
                plugin=plugin_code,
                params=parsed_params if parsed_params else None,
                debug=debug,
            )

            # Success output
            console.print(
                Panel(
                    f'[green]Action completed![/green]\n\n'
                    f'Plugin: [bold]{result.plugin}[/bold]\n'
                    f'Action: [bold]{result.action}[/bold]',
                    title='Success',
                    border_style='green',
                )
            )

            if result.result:
                console.print(f'[dim]Result:[/dim] {result.result}')

    except PluginError as e:
        err_console.print(f'[red]Error:[/red] {e.message}')
        if e.details:
            err_console.print(f'[dim]Details:[/dim] {e.details}')
        raise typer.Exit(1)
    except FileNotFoundError as e:
        err_console.print(f'[red]Error:[/red] {e}')
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f'[red]Unexpected error:[/red] {e}')
        raise typer.Exit(1)


@agent_app.command('select')
def agent_select(
    host: Annotated[
        Optional[str],
        typer.Option('--host', help='Synapse API host.'),
    ] = None,
    token: Annotated[
        Optional[str],
        typer.Option('--token', '-t', help='Access token.'),
    ] = None,
) -> None:
    """Interactively select an agent.

    Fetches available agents from the backend and prompts for selection.

    [bold]Examples:[/bold]

        synapse agent select
    """
    from synapse_sdk.cli.agent.select import select_agent_interactive
    from synapse_sdk.cli.auth import get_auth_config

    try:
        auth = get_auth_config(host=host, token=token, console=console, interactive=False)
        result = select_agent_interactive(auth, console)

        if not result:
            console.print('[yellow]Cancelled[/yellow]')
            raise typer.Exit(0)

    except typer.BadParameter as e:
        err_console.print(f'[red]Error:[/red] {e.message}')
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f'[red]Error:[/red] {e}')
        raise typer.Exit(1)


@agent_app.command('show')
def agent_show() -> None:
    """Show current agent configuration.

    [bold]Examples:[/bold]

        synapse agent show
    """
    from rich.table import Table

    from synapse_sdk.cli.agent.config import get_agent_config

    agent = get_agent_config()

    if not agent:
        console.print('[yellow]No agent configured.[/yellow]')
        console.print('[dim]Use `synapse agent select` or `synapse agent set` to configure.[/dim]')
        raise typer.Exit(0)

    table = Table(title='Current Agent', show_header=False, box=None, padding=(0, 2))
    table.add_column('Key', style='dim')
    table.add_column('Value')
    table.add_row('ID', str(agent.id))
    table.add_row('Name', agent.name or '-')
    table.add_row('URL', agent.url or '-')
    table.add_row('Token', (agent.token[:12] + '...') if agent.token else '-')

    console.print(table)


@agent_app.command('clear')
def agent_clear(
    yes: Annotated[
        bool,
        typer.Option('--yes', '-y', help='Skip confirmation.'),
    ] = False,
) -> None:
    """Clear agent configuration.

    [bold]Examples:[/bold]

        synapse agent clear
        synapse agent clear -y
    """
    import questionary

    from synapse_sdk.cli.agent.config import clear_agent_config, get_agent_config

    agent = get_agent_config()

    if not agent:
        console.print('[yellow]No agent configured.[/yellow]')
        raise typer.Exit(0)

    if not yes:
        confirmed = questionary.confirm(
            f'Clear agent configuration for "{agent.name or agent.id}"?',
            default=False,
        ).ask()

        if not confirmed:
            console.print('[yellow]Cancelled[/yellow]')
            raise typer.Exit(0)

    clear_agent_config()
    console.print('[green]Agent configuration cleared.[/green]')


@mcp_app.command('serve')
def mcp_serve(
    config: Annotated[
        Optional[Path],
        typer.Option('--config', '-c', help='Path to config file (default: ~/.synapse/config.yaml).'),
    ] = None,
) -> None:
    """Start the MCP server for AI assistant integration.

    Runs the Synapse MCP server which provides tools for:
    - Managing environments (prod, test, demo, local)
    - Listing and running plugins
    - Viewing job logs and status
    - Managing Ray Serve deployments

    [bold]Configuration:[/bold]

    Run `synapse mcp init` to create ~/.synapse/config.yaml
    (uses existing credentials from ~/.synapse/credentials if available)

        default_environment: prod

        environments:
          prod:
            backend_url: https://api.synapse.sh
            access_token: your-token
            # Agent is set via list_agents() + select_agent() tools

    [bold]Cursor Setup:[/bold]

    Add to ~/.cursor/mcp.json:

        {
          "mcpServers": {
            "synapse": {
              "command": "uvx",
              "args": ["--from", "synapse-sdk[mcp]", "synapse", "mcp", "serve"]
            }
          }
        }

    [bold]Claude Code Setup:[/bold]

        claude mcp add synapse -- uvx --from 'synapse-sdk[mcp]' synapse mcp serve

    [bold]Examples:[/bold]

        synapse mcp serve
        synapse mcp serve --config ~/my-config.yaml
    """
    try:
        from synapse_sdk.mcp import serve
        from synapse_sdk.mcp.config import ConfigManager

        # Initialize config manager with custom path if provided
        if config:
            from synapse_sdk.mcp.config import reset_config_manager

            reset_config_manager()
            # Import and set up with custom path
            import synapse_sdk.mcp.config as config_module

            config_module._config_manager = ConfigManager(config_path=config)

        serve()

    except ImportError:
        err_console.print('[red]Error:[/red] MCP dependencies not installed.')
        err_console.print('[dim]Install with: pip install synapse-sdk[mcp][/dim]')
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f'[red]Error:[/red] {e}')
        raise typer.Exit(1)


@mcp_app.command('init')
def mcp_init(
    config: Annotated[
        Optional[Path],
        typer.Option('--config', '-c', help='Path to config file (default: ~/.synapse/config.yaml).'),
    ] = None,
    force: Annotated[
        bool,
        typer.Option('--force', '-f', help='Overwrite existing config file.'),
    ] = False,
) -> None:
    """Initialize MCP configuration file with example environments.

    [bold]Examples:[/bold]

        synapse mcp init
        synapse mcp init --force
    """
    import questionary

    from synapse_sdk.cli.auth import CREDENTIALS_FILE, load_credentials_file

    config_path = config or (Path.home() / '.synapse' / 'config.yaml')

    if config_path.exists() and not force:
        console.print(f'[yellow]Config file already exists:[/yellow] {config_path}')
        console.print('[dim]Use --force to overwrite.[/dim]')
        raise typer.Exit(0)

    # Check for existing credentials
    backend_url = 'https://api.synapse.example.com'
    access_token = 'your-access-token'
    use_existing = False

    if CREDENTIALS_FILE.exists():
        creds = load_credentials_file()
        existing_host = creds.get('SYNAPSE_HOST')
        existing_token = creds.get('SYNAPSE_ACCESS_TOKEN')

        if existing_host or existing_token:
            console.print(f'[dim]Found existing credentials at {CREDENTIALS_FILE}[/dim]')
            if existing_host:
                console.print(f'  Host: {existing_host}')
            if existing_token:
                console.print(f'  Token: {existing_token[:12]}...')

            use_existing = questionary.confirm(
                'Use existing credentials for MCP?',
                default=True,
            ).ask()

            if use_existing:
                if existing_host:
                    backend_url = existing_host
                if existing_token:
                    access_token = existing_token

    # Create config
    example_config = f"""# Synapse MCP Server Configuration
#
# Agent setup:
#   1. Start MCP server: synapse mcp serve
#   2. Use list_agents() tool to fetch available agents
#   3. Use select_agent(id) tool to configure agent

default_environment: profile_1

environments:
  profile_1:
    backend_url: {backend_url}
    access_token: {access_token}
    # Tenant and Agent are configured via mcp tool after connecting

"""

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write config
    config_path.write_text(example_config)
    config_path.chmod(0o600)

    console.print(f'[green]Created config file:[/green] {config_path}')
    console.print()

    if use_existing:
        console.print('[bold]Next steps:[/bold]')
        console.print('  1. Run: synapse mcp serve')
        console.print('  2. Use list_agents() and select_agent() to configure agent')
    else:
        console.print('[bold]Next steps:[/bold]')
        console.print(f'  1. Edit {config_path} with your credentials')
        console.print('  2. Run: synapse mcp serve')

    console.print()
    console.print('[bold]Cursor setup:[/bold]')
    console.print('  Add to ~/.cursor/mcp.json:')
    console.print()
    console.print('    {')
    console.print('      "mcpServers": {')
    console.print('        "synapse": {')
    console.print('          "command": "uvx",')
    console.print('          "args": ["--from", "synapse-sdk[mcp]", "synapse", "mcp", "serve"]')
    console.print('        }')
    console.print('      }')
    console.print('    }')
    console.print()
    console.print('[bold]Claude Code setup:[/bold]')
    console.print("  claude mcp add synapse -- uvx --from 'synapse-sdk[mcp]' synapse mcp serve")
    console.print()
    console.print('[dim]For local development:[/dim]')
    console.print('  claude mcp add synapse -- uv run --directory <path-to-synapse-sdk> synapse mcp serve')


@cli.command('login')
def login(
    host: Annotated[
        Optional[str],
        typer.Option('--host', help='Synapse API host.'),
    ] = None,
    token: Annotated[
        Optional[str],
        typer.Option('--token', '-t', help='Access token (will prompt if not provided).'),
    ] = None,
) -> None:
    """Authenticate with Synapse.

    Saves credentials to ~/.synapse/credentials for future use.

    [bold]Examples:[/bold]

        synapse login
        synapse login --token YOUR_TOKEN
    """
    import questionary

    from synapse_sdk.cli.auth import DEFAULT_HOST

    # Prompt for host if not provided
    if not host:
        host = questionary.text(
            'Synapse API host:',
            default=DEFAULT_HOST,
        ).ask()

        if not host:
            console.print('[yellow]Cancelled[/yellow]')
            raise typer.Exit(0)

    # Prompt for token if not provided
    if not token:
        token = questionary.text(
            'Enter your Synapse access token:',
            validate=lambda x: len(x) > 0 or 'Token cannot be empty',
        ).ask()

        if not token:
            console.print('[yellow]Cancelled[/yellow]')
            raise typer.Exit(0)

    # Save to credentials file
    config_dir = Path.home() / '.synapse'
    config_dir.mkdir(exist_ok=True)

    credentials_file = config_dir / 'credentials'
    credentials_file.write_text(f'SYNAPSE_HOST={host}\nSYNAPSE_ACCESS_TOKEN={token}\n')
    credentials_file.chmod(0o600)

    console.print('[green]Logged in successfully![/green]')
    console.print(f'[dim]Credentials saved to {credentials_file}[/dim]')


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        from importlib.metadata import version

        try:
            ver = version('synapse-sdk')
        except Exception:
            ver = 'unknown'
        console.print(f'synapse-sdk [bold cyan]{ver}[/bold cyan]')
        raise typer.Exit()


@cli.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option('--version', '-v', callback=version_callback, is_eager=True, help='Show version and exit.'),
    ] = None,
) -> None:
    """Synapse SDK CLI."""
    pass


if __name__ == '__main__':
    cli()
