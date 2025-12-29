from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from synapse_sdk.plugins.discovery import PluginDiscovery
from synapse_sdk.plugins.executors.local import LocalExecutor
from synapse_sdk.plugins.executors.ray.job import RayJobExecutor
from synapse_sdk.plugins.executors.ray.task import RayActorExecutor

if TYPE_CHECKING:
    from synapse_sdk.plugins.action import BaseAction


def _discover_action(plugin_code: str, action: str) -> type[BaseAction] | Callable:
    """Discover action class from plugin code.

    Args:
        plugin_code: Either a module path ('my_plugins.yolov8') or
                     a filesystem path to config.yaml ('/path/to/plugin')
        action: Action name to load

    Returns:
        Action class or decorated function
    """
    path = Path(plugin_code)

    # Check if it's a filesystem path (config.yaml or directory)
    if path.exists() or (path.parent.exists() and path.suffix == '.yaml'):
        discovery = PluginDiscovery.from_path(path)
    else:
        # Treat as module path - import and introspect
        module = importlib.import_module(plugin_code)
        discovery = PluginDiscovery.from_module(module)

    return discovery.get_action_class(action)


def run_plugin(
    plugin_code: str,
    action: str,
    params: dict[str, Any] | None = None,
    *,
    mode: Literal['local', 'task', 'job'] = 'local',
    **executor_kwargs: Any,
) -> Any:
    """Run a plugin action.

    This is the main entry point for executing plugin actions. It handles
    plugin discovery, parameter validation, and execution delegation to
    the appropriate executor based on the mode.

    Args:
        plugin_code: Plugin identifier. Can be:
            - Module path: 'my_plugins.yolov8' (discovers via @action decorators or BaseAction classes)
            - Filesystem path: '/path/to/plugin' or '/path/to/config.yaml'
        action: Action name to execute (e.g., 'train', 'infer', 'export').
        params: Action parameters as a dictionary. Will be validated against
            the action's params schema if defined.
        mode: Execution mode:
            - 'local': Run in the current process (default, good for dev).
            - 'task': Run via Ray Actor pool (fast startup, <1s).
            - 'job': Run via Ray Job API (for heavy/long-running workloads).
        **executor_kwargs: Additional executor options:
            - action_cls: Optional explicit action class (skips discovery).
            - env: PluginEnvironment or dict for environment config.
            - job_id: Optional job identifier for tracking.

    Returns:
        For 'local' and 'task' modes: Action result (type depends on the action).
        For 'job' mode: Job ID string for tracking (async submission).

    Raises:
        ActionNotFoundError: If the action doesn't exist in the plugin.
        ValidationError: If params fail schema validation.
        ExecutionError: If action execution fails.

    Example:
        >>> from synapse_sdk.plugins.runner import run_plugin
        >>>
        >>> # Auto-discover from module path
        >>> result = run_plugin('my_plugins.yolov8', 'train', {'epochs': 10})
        >>>
        >>> # Auto-discover from config.yaml path
        >>> result = run_plugin('/path/to/plugin', 'train', {'epochs': 10})
        >>>
        >>> # Explicit action class (skips discovery)
        >>> result = run_plugin('yolov8', 'train', {'epochs': 10}, action_cls=TrainAction)
    """
    params = params or {}

    if mode == 'local':
        action_cls = executor_kwargs.pop('action_cls', None)
        if action_cls is None:
            action_cls = _discover_action(plugin_code, action)
        executor = LocalExecutor(**executor_kwargs)
        return executor.execute(action_cls, params)

    elif mode == 'task':
        action_cls = executor_kwargs.pop('action_cls', None)
        if action_cls is None:
            action_cls = _discover_action(plugin_code, action)
        executor = RayActorExecutor(**executor_kwargs)
        return executor.execute(action_cls, params)

    else:  # mode == 'job'
        executor = RayJobExecutor(**executor_kwargs)
        # Job mode is async - submit and return job_id
        return executor.submit(action, params)


__all__ = ['run_plugin']
