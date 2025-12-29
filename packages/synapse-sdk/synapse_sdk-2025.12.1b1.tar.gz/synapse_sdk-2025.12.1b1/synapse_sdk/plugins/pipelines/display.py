"""Rich console progress display for pipeline execution.

Provides a real-time progress display using the Rich library for
monitoring pipeline execution in the terminal. Supports both sync and async.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from rich.panel import Panel

    from synapse_sdk.plugins.pipelines.models import PipelineProgress


def _create_display_panel(
    progress: 'PipelineProgress',
    show_actions: bool = True,
) -> 'Panel':
    """Create the Rich display panel for progress."""
    from rich.console import Group
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
    from rich.table import Table

    from synapse_sdk.plugins.pipelines.models import ActionStatus, RunStatus

    # Main progress bar
    main_progress = Progress(
        SpinnerColumn(),
        TextColumn('[bold blue]{task.description}'),
        BarColumn(),
        TextColumn('[progress.percentage]{task.percentage:>3.0f}%'),
    )

    # Calculate overall progress including current action progress
    total_actions = len(progress.actions) if progress.actions else 1
    completed_actions = sum(1 for a in (progress.actions or []) if a.status == ActionStatus.COMPLETED)

    # Find current running action and its progress
    current_action_progress = 0.0
    if progress.actions:
        for a in progress.actions:
            if a.status == ActionStatus.RUNNING and a.progress:
                current_action_progress = a.progress
                break

    if progress.status == RunStatus.COMPLETED:
        percentage = 100.0
    elif progress.status == RunStatus.FAILED:
        percentage = (completed_actions / total_actions) * 100
    else:
        # Include current action's partial progress
        base_progress = (completed_actions / total_actions) * 100
        action_contribution = (current_action_progress / total_actions) * 100
        percentage = base_progress + action_contribution

    main_progress.add_task(
        description=f'Pipeline: {progress.run_id[:8]}...',
        total=100,
        completed=percentage,
    )

    # Status text
    status_colors = {
        RunStatus.PENDING: 'yellow',
        RunStatus.RUNNING: 'blue',
        RunStatus.COMPLETED: 'green',
        RunStatus.FAILED: 'red',
        RunStatus.CANCELLED: 'orange3',
    }
    status_color = status_colors.get(progress.status, 'white')
    status_text = f'[{status_color}]Status: {progress.status.value.upper()}[/]'

    if progress.current_action:
        status_text += f'  |  Current: [cyan]{progress.current_action}[/]'

    # Find current action's detailed progress message
    current_action_msg = None
    if progress.actions:
        for a in progress.actions:
            if a.status == ActionStatus.RUNNING:
                if a.message:
                    current_action_msg = a.message
                elif a.progress_category and a.progress:
                    current_action_msg = f'{a.progress_category}: {a.progress * 100:.0f}%'
                break

    # Build content
    content_parts: list = [main_progress, '', status_text]

    # Add detailed progress message if available
    if current_action_msg:
        content_parts.append(f'[dim]  {current_action_msg}[/]')

    # Action table (if enabled and actions exist)
    if show_actions and progress.actions:
        action_table = Table(show_header=True, header_style='bold magenta')
        action_table.add_column('#', style='dim', width=3)
        action_table.add_column('Action', min_width=20)
        action_table.add_column('Status', width=12)
        action_table.add_column('Progress', width=15)

        action_status_icons = {
            ActionStatus.PENDING: '[dim]-[/]',
            ActionStatus.RUNNING: '[blue]...[/]',
            ActionStatus.COMPLETED: '[green]OK[/]',
            ActionStatus.FAILED: '[red]FAIL[/]',
            ActionStatus.SKIPPED: '[yellow]SKIP[/]',
        }

        for i, action in enumerate(progress.actions):
            icon = action_status_icons.get(action.status, '?')
            if action.message:
                prog_text = action.message
            elif action.progress:
                prog_text = f'{action.progress * 100:.0f}%'
            else:
                prog_text = '-'
            action_table.add_row(
                str(i + 1),
                action.name,
                icon,
                prog_text,
            )

        content_parts.extend(['', action_table])

    # Error message (if any)
    if progress.error:
        content_parts.extend(['', f'[red]Error: {progress.error}[/]'])

    return Panel(
        Group(*content_parts),
        title='[bold]Pipeline Progress[/]',
        border_style='blue' if progress.status == RunStatus.RUNNING else 'green',
    )


def display_progress(
    progress_stream: 'Iterator[PipelineProgress]',
    *,
    show_actions: bool = True,
    refresh_rate: float = 4.0,
) -> 'PipelineProgress':
    """Display pipeline progress in the console using Rich (sync version).

    Creates a live-updating display showing:
    - Overall pipeline status and progress bar
    - Current action being executed
    - Individual action statuses in a table

    Args:
        progress_stream: Iterator yielding PipelineProgress updates.
        show_actions: If True, show individual action statuses.
        refresh_rate: Refreshes per second for the live display.

    Returns:
        Final PipelineProgress after completion.

    Example:
        >>> from synapse_sdk.plugins.pipelines.display import display_progress
        >>> run_id = executor.submit(pipeline, params)
        >>> final = display_progress(executor.stream_progress(run_id))
        >>> print(f"Completed with status: {final.status}")
    """
    try:
        from rich.console import Console
        from rich.live import Live
    except ImportError as e:
        raise ImportError('Rich library is required for progress display. Install it with: pip install rich') from e

    console = Console()
    last_progress: PipelineProgress | None = None

    with Live(console=console, refresh_per_second=refresh_rate) as live:
        for progress in progress_stream:
            last_progress = progress
            live.update(_create_display_panel(progress, show_actions))

    if last_progress is None:
        raise RuntimeError('No progress updates received')

    return last_progress


async def display_progress_async(
    progress_stream: 'AsyncIterator[PipelineProgress]',
    *,
    show_actions: bool = True,
    refresh_rate: float = 4.0,
) -> 'PipelineProgress':
    """Display pipeline progress in the console using Rich (async version).

    Creates a live-updating display showing:
    - Overall pipeline status and progress bar
    - Current action being executed
    - Individual action statuses in a table

    Args:
        progress_stream: AsyncIterator yielding PipelineProgress updates.
        show_actions: If True, show individual action statuses.
        refresh_rate: Refreshes per second for the live display.

    Returns:
        Final PipelineProgress after completion.

    Example:
        >>> from synapse_sdk.plugins.pipelines.display import display_progress_async
        >>> run_id = await executor.submit_async(pipeline, params)
        >>> async for progress in executor.stream_progress_async(run_id):
        ...     # Process updates
        >>> final = await display_progress_async(executor.stream_progress_async(run_id))
    """
    try:
        from rich.console import Console
        from rich.live import Live
    except ImportError as e:
        raise ImportError('Rich library is required for progress display. Install it with: pip install rich') from e

    console = Console()
    last_progress: PipelineProgress | None = None

    with Live(console=console, refresh_per_second=refresh_rate) as live:
        async for progress in progress_stream:
            last_progress = progress
            live.update(_create_display_panel(progress, show_actions))

    if last_progress is None:
        raise RuntimeError('No progress updates received')

    return last_progress


def print_progress_summary(progress: 'PipelineProgress') -> None:
    """Print a summary of pipeline execution.

    Args:
        progress: Final pipeline progress to summarize.
    """
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        # Fallback to plain print
        print(f'Pipeline {progress.run_id}: {progress.status.value}')
        return

    console = Console()
    from synapse_sdk.plugins.pipelines.models import ActionStatus, RunStatus

    # Status emoji
    status_emoji = {
        RunStatus.COMPLETED: '[green]OK[/]',
        RunStatus.FAILED: '[red]FAILED[/]',
        RunStatus.CANCELLED: '[yellow]CANCELLED[/]',
        RunStatus.RUNNING: '[blue]RUNNING[/]',
        RunStatus.PENDING: '[dim]PENDING[/]',
    }

    console.print()
    console.print(f'[bold]Pipeline:[/] {progress.run_id}')
    console.print(f'[bold]Status:[/] {status_emoji.get(progress.status, progress.status.value)}')

    if progress.started_at:
        console.print(f'[bold]Started:[/] {progress.started_at.isoformat()}')
    if progress.completed_at:
        console.print(f'[bold]Completed:[/] {progress.completed_at.isoformat()}')
        if progress.started_at:
            duration = progress.completed_at - progress.started_at
            console.print(f'[bold]Duration:[/] {duration}')

    if progress.actions:
        console.print()
        table = Table(title='Actions', show_header=True)
        table.add_column('Action', style='cyan')
        table.add_column('Status')
        table.add_column('Duration')

        action_status_style = {
            ActionStatus.COMPLETED: '[green]COMPLETED[/]',
            ActionStatus.FAILED: '[red]FAILED[/]',
            ActionStatus.RUNNING: '[blue]RUNNING[/]',
            ActionStatus.PENDING: '[dim]PENDING[/]',
            ActionStatus.SKIPPED: '[yellow]SKIPPED[/]',
        }

        for action in progress.actions:
            duration = '-'
            if action.started_at and action.completed_at:
                duration = str(action.completed_at - action.started_at)
            elif action.started_at:
                duration = 'running...'

            table.add_row(
                action.name,
                action_status_style.get(action.status, str(action.status)),
                duration,
            )

        console.print(table)

    if progress.error:
        console.print()
        console.print(f'[red bold]Error:[/] {progress.error}')


__all__ = ['display_progress', 'display_progress_async', 'print_progress_summary']
