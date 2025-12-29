"""Agent selection and connection utilities."""

from __future__ import annotations

from dataclasses import dataclass

import questionary
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from synapse_sdk.cli.agent.config import AgentConfig, set_agent_config
from synapse_sdk.cli.auth import AuthConfig
from synapse_sdk.clients.backend import Agent, BackendClient


@dataclass
class ConnectionResult:
    """Result of connection test."""

    success: bool
    message: str


def fetch_agents(auth: AuthConfig) -> list[Agent]:
    """Fetch available agents from the backend.

    Args:
        auth: Authentication configuration.

    Returns:
        List of Agent objects.
    """
    client = BackendClient(auth.host, access_token=auth.access_token)
    return client.list_agents()


def check_agent_connection(url: str, token: str, *, timeout: int = 5) -> ConnectionResult:
    """Test agent connection.

    Args:
        url: Agent URL.
        token: Agent authentication token.
        timeout: Request timeout in seconds.

    Returns:
        ConnectionResult with success status and message.
    """
    if not url or not token:
        return ConnectionResult(success=True, message='Agent configured (no URL/token to test)')

    try:
        response = requests.get(
            f'{url.rstrip("/")}/health/',
            headers={'Authorization': token},
            timeout=timeout,
        )

        if response.status_code == 200:
            return ConnectionResult(success=True, message='Connection successful')
        elif response.status_code == 401:
            return ConnectionResult(success=False, message='Invalid agent token (401)')
        elif response.status_code == 403:
            return ConnectionResult(success=False, message='Access forbidden (403)')
        else:
            return ConnectionResult(success=False, message=f'HTTP {response.status_code}')

    except requests.exceptions.Timeout:
        return ConnectionResult(success=False, message=f'Connection timeout (>{timeout}s)')
    except requests.exceptions.ConnectionError:
        return ConnectionResult(success=False, message='Connection failed')
    except Exception as e:
        return ConnectionResult(success=False, message=f'Error: {e}')


def display_agents_table(agents: list[Agent], console: Console) -> None:
    """Display agents in a table format.

    Args:
        agents: List of agents to display.
        console: Rich console for output.
    """
    table = Table(title='Available Agents', show_header=True, header_style='bold')
    table.add_column('ID', style='dim')
    table.add_column('Name')
    table.add_column('Status')
    table.add_column('URL', style='dim')

    for agent in agents:
        status = agent.status or 'unknown'
        status_style = 'green' if agent.is_connected else 'red'
        table.add_row(
            str(agent.id),
            agent.name,
            f'[{status_style}]{status}[/{status_style}]',
            agent.url or '-',
        )

    console.print(table)


def select_agent_interactive(
    auth: AuthConfig,
    console: Console,
) -> AgentConfig | None:
    """Interactively select an agent from the backend.

    Args:
        auth: Authentication configuration.
        console: Rich console for output.

    Returns:
        Selected AgentConfig if successful, None if cancelled.
    """
    console.print('[dim]Fetching available agents...[/dim]')

    try:
        agents = fetch_agents(auth)
    except Exception as e:
        console.print(f'[red]Error fetching agents:[/red] {e}')
        return None

    if not agents:
        console.print('[yellow]No agents found in current workspace.[/yellow]')
        return None

    # Create ID lookup map
    agents_by_id = {agent.id: agent for agent in agents}

    # Display the nice Rich table
    console.print()
    display_agents_table(agents, console)
    console.print()

    # Prompt for agent ID
    agent_id_str = questionary.text(
        'Enter agent ID (leave empty to cancel):',
    ).ask()

    if not agent_id_str:
        return None

    try:
        agent_id = int(agent_id_str)
    except ValueError:
        console.print(f'[red]Invalid ID:[/red] {agent_id_str}')
        return None

    selected = agents_by_id.get(agent_id)
    if not selected:
        console.print(f'[red]Agent not found:[/red] {agent_id}')
        return None

    # Save configuration
    set_agent_config(
        selected.id,
        name=selected.name,
        url=selected.url,
        token=selected.token,
    )

    # Display success
    console.print()
    console.print(
        Panel(
            f'[bold]{selected.name}[/bold]\n\nID: {selected.id}\nURL: {selected.url or "Not set"}',
            title='Agent Selected',
            border_style='green',
        )
    )

    # Test connection if URL and token are available
    if selected.url and selected.token:
        console.print()
        console.print('[dim]Testing connection...[/dim]')
        result = check_agent_connection(selected.url, selected.token)
        if result.success:
            console.print(f'[green]{result.message}[/green]')
        else:
            console.print(f'[red]{result.message}[/red]')

    return AgentConfig(
        id=selected.id,
        name=selected.name,
        url=selected.url,
        token=selected.token,
    )


__all__ = [
    'ConnectionResult',
    'fetch_agents',
    'check_agent_connection',
    'display_agents_table',
    'select_agent_interactive',
]
