"""Plugin run command implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from synapse_sdk.cli.plugin.publish import find_config_file
from synapse_sdk.clients.backend import BackendClient
from synapse_sdk.plugins.discovery import PluginDiscovery
from synapse_sdk.plugins.errors import PluginRunError

if TYPE_CHECKING:
    from synapse_sdk.cli.agent.config import AgentConfig
    from synapse_sdk.cli.auth import AuthConfig


@dataclass
class RunResult:
    """Result of plugin run operation."""

    action: str
    plugin: str
    result: Any


def resolve_plugin_code(
    plugin: str | None,
    path: Path | None = None,
) -> str:
    """Resolve plugin code from argument or config file.

    Args:
        plugin: Explicit plugin code.
        path: Directory to search for config file.

    Returns:
        Plugin code string.

    Raises:
        FileNotFoundError: If no config found when plugin not specified.
    """
    if plugin:
        return plugin

    config_file = find_config_file(path or Path.cwd())
    discovery = PluginDiscovery.from_path(config_file)
    return discovery.config.code


def run_plugin(
    action: str,
    auth: AuthConfig,
    agent: AgentConfig,
    console: Console,
    *,
    plugin: str,
    params: dict[str, Any] | None = None,
    debug: bool = False,
) -> RunResult:
    """Execute plugin run workflow.

    Args:
        action: Action name to execute (e.g., deployment, train).
        auth: Authentication config with host and access token.
        agent: Agent configuration with id.
        console: Rich console.
        plugin: Plugin code.
        params: Optional parameters to pass to the action.
        debug: Debug mode flag.

    Returns:
        RunResult with action result.

    Raises:
        PluginRunError: If auth/agent not configured or run fails.
    """
    # Validate auth configuration
    if not auth.access_token:
        raise PluginRunError('Not authenticated. Run `synapse login` to authenticate.')

    console.print(f'[dim]Plugin:[/dim] {plugin}')
    console.print(f'[dim]Action:[/dim] {action}')
    console.print(f'[dim]Agent:[/dim] {agent.name or agent.id}')

    # Create backend client
    client = BackendClient(
        base_url=auth.host,
        access_token=auth.access_token,
    )

    # Build request data
    data: dict[str, Any] = {
        'agent': agent.id,
        'action': action,
    }
    if params:
        data['params'] = params
    if debug:
        data['debug'] = debug

    # Run the action
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn('[progress.description]{task.description}'),
            console=console,
        ) as progress:
            progress.add_task(f'Running {action}...', total=None)

            result = client.run_plugin(plugin, data)

    except Exception as e:
        raise PluginRunError(f'Failed to run plugin: {e}') from e

    return RunResult(
        action=action,
        plugin=plugin,
        result=result,
    )


__all__ = [
    'RunResult',
    'resolve_plugin_code',
    'run_plugin',
]
