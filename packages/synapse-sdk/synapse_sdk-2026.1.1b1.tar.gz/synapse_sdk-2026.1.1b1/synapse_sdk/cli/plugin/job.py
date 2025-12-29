"""Plugin job command implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from synapse_sdk.clients.backend import BackendClient
from synapse_sdk.plugins.errors import PluginRunError

if TYPE_CHECKING:
    from synapse_sdk.cli.auth import AuthConfig


def get_job(
    job_id: str,
    auth: AuthConfig,
    console: Console,
) -> dict:
    """Get job details.

    Args:
        job_id: Job ID.
        auth: Authentication configuration.
        console: Rich console.

    Returns:
        Job details dict.

    Raises:
        PluginRunError: If not authenticated or request fails.
    """
    if not auth.access_token:
        raise PluginRunError('Not authenticated. Run `synapse login` to authenticate.')

    client = BackendClient(
        base_url=auth.host,
        access_token=auth.access_token,
    )

    try:
        return client.get_job(job_id)
    except Exception as e:
        raise PluginRunError(f'Failed to get job: {e}') from e


def display_job(job: dict, console: Console) -> None:
    """Display job details in a formatted table.

    Args:
        job: Job details dict.
        console: Rich console.
    """
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column('Key', style='dim')
    table.add_column('Value')

    table.add_row('ID', str(job.get('id', '-')))
    table.add_row('Status', job.get('status', '-'))
    table.add_row('Action', job.get('action', '-'))

    if job.get('plugin_release'):
        pr = job.get('plugin_release', {})
        if isinstance(pr, dict):
            table.add_row('Plugin', pr.get('plugin', '-'))
            table.add_row('Version', pr.get('version', '-'))

    if job.get('agent'):
        agent = job.get('agent', {})
        if isinstance(agent, dict):
            table.add_row('Agent', agent.get('name', '-'))

    if job.get('created'):
        table.add_row('Created', str(job.get('created')))

    if job.get('started'):
        table.add_row('Started', str(job.get('started')))

    if job.get('finished'):
        table.add_row('Finished', str(job.get('finished')))

    console.print(Panel(table, title=f'Job: {job.get("id", "Unknown")}', border_style='blue'))


def get_job_logs(
    job_id: str,
    auth: AuthConfig,
    console: Console,
) -> dict:
    """Get job logs (non-streaming).

    Args:
        job_id: Job ID.
        auth: Authentication configuration.
        console: Rich console.

    Returns:
        Job logs response.

    Raises:
        PluginRunError: If not authenticated or request fails.
    """
    if not auth.access_token:
        raise PluginRunError('Not authenticated. Run `synapse login` to authenticate.')

    client = BackendClient(
        base_url=auth.host,
        access_token=auth.access_token,
    )

    try:
        return client.list_job_console_logs(job_id)
    except Exception as e:
        raise PluginRunError(f'Failed to get job logs: {e}') from e


def tail_job_logs(
    job_id: str,
    auth: AuthConfig,
    console: Console,
) -> None:
    """Tail job logs (streaming).

    Args:
        job_id: Job ID.
        auth: Authentication configuration.
        console: Rich console.

    Raises:
        PluginRunError: If not authenticated or request fails.
    """
    import json

    if not auth.access_token:
        raise PluginRunError('Not authenticated. Run `synapse login` to authenticate.')

    client = BackendClient(
        base_url=auth.host,
        access_token=auth.access_token,
    )

    console.print(f'[dim]Tailing logs for job {job_id}...[/dim]')
    console.print('[dim]Press Ctrl+C to stop.[/dim]\n')

    try:
        for line in client.tail_job_console_logs(job_id):
            if not line:
                continue

            # Parse SSE format: "data: {...}"
            if line.startswith('data: '):
                data_str = line[6:]  # Remove "data: " prefix
                try:
                    event = json.loads(data_str)
                    event_type = event.get('type')

                    if event_type == 'connected':
                        continue  # Skip connection message
                    elif event_type == 'complete':
                        break  # Done
                    elif event_type == 'log':
                        # The data field contains another SSE message
                        inner_data = event.get('data', '')
                        if inner_data.startswith('data: '):
                            inner_str = inner_data[6:].rstrip('\n')
                            try:
                                inner_event = json.loads(inner_str)
                                if inner_event.get('type') == 'log':
                                    message = inner_event.get('message', '')
                                    if message:
                                        console.print(message, end='')
                                elif inner_event.get('type') == 'complete':
                                    break
                            except json.JSONDecodeError:
                                console.print(inner_data)
                        else:
                            console.print(inner_data)
                except json.JSONDecodeError:
                    console.print(data_str)
            else:
                console.print(line)
    except KeyboardInterrupt:
        console.print('\n[dim]Stopped.[/dim]')
    except Exception as e:
        raise PluginRunError(f'Failed to tail job logs: {e}') from e


__all__ = [
    'get_job',
    'display_job',
    'get_job_logs',
    'tail_job_logs',
]
