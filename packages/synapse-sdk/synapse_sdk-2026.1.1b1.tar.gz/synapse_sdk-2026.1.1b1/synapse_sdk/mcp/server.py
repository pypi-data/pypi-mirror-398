"""MCP Server for Synapse SDK.

This module provides the FastMCP server instance and registers all tools,
resources, and prompts for interacting with Synapse infrastructure.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise ImportError('MCP dependencies not installed. Install with: pip install synapse-sdk[mcp]')

from synapse_sdk.mcp.config import get_config_manager

if TYPE_CHECKING:
    from synapse_sdk.mcp.config import ConfigManager

# Create the MCP server instance
mcp = FastMCP(
    name='synapse',
    instructions='Synapse SDK MCP Server - Manage plugins, executions, and deployments',
)


def _log(message: str) -> None:
    """Log to stderr (safe for MCP STDIO transport)."""
    print(f'[synapse-mcp] {message}', file=sys.stderr)


def _get_config() -> ConfigManager:
    """Get the config manager instance."""
    return get_config_manager()


# =============================================================================
# Environment Tools
# =============================================================================


@mcp.tool()
def switch_environment(name: str) -> dict:
    """Switch to a different environment (e.g., prod, test, demo, local).

    Args:
        name: The environment name to switch to

    Returns:
        Status of the switch operation with environment details
    """
    config = _get_config()

    if name not in config.list_environments():
        return {
            'success': False,
            'error': f'Environment "{name}" not found',
            'available_environments': config.list_environments(),
        }

    config.set_active_environment(name)
    env = config.get_active_environment()

    return {
        'success': True,
        'message': f'Switched to environment: {name}',
        'environment': env.to_dict() if env else None,
    }


@mcp.tool()
def list_environments() -> dict:
    """List all configured environments.

    Returns:
        List of environment names and their configuration status
    """
    config = _get_config()
    environments = []

    for name in config.list_environments():
        env = config.get_environment(name)
        if env:
            environments.append(env.to_dict())

    return {
        'environments': environments,
        'active_environment': config.get_active_environment_name(),
        'config_path': str(config.config_path),
    }


@mcp.tool()
def get_current_environment() -> dict:
    """Get the currently active environment and its connection status.

    Returns:
        Current environment details including backend/agent availability
    """
    config = _get_config()
    env = config.get_active_environment()

    if not env:
        return {
            'active': False,
            'message': 'No environment is currently active. Use switch_environment() to select one.',
            'available_environments': config.list_environments(),
        }

    # Test connections
    backend_status = 'not_configured'
    agent_status = 'not_configured'

    if env.has_backend():
        try:
            client = config.get_backend_client()
            if client:
                backend_status = 'connected'
        except Exception as e:
            backend_status = f'error: {e}'

    if env.has_agent():
        try:
            client = config.get_agent_client()
            if client:
                agent_status = 'connected'
        except Exception as e:
            agent_status = f'error: {e}'

    return {
        'active': True,
        'environment': env.to_dict(),
        'backend_status': backend_status,
        'agent_status': agent_status,
    }


@mcp.tool()
def add_environment(
    name: str,
    backend_url: str | None = None,
    access_token: str | None = None,
    tenant: str | None = None,
    set_as_default: bool = False,
) -> dict:
    """Add or update an environment configuration.

    After adding, use list_agents() to see available agents,
    then select_agent() to configure the agent for this environment.

    Args:
        name: Environment name (e.g., 'prod', 'test', 'demo')
        backend_url: Synapse backend API URL
        access_token: Your API access token
        tenant: Tenant identifier
        set_as_default: Whether to set this as the default environment

    Returns:
        The created/updated environment configuration
    """
    config = _get_config()

    env = config.add_environment(
        name=name,
        backend_url=backend_url,
        access_token=access_token,
        tenant=tenant,
        set_as_default=set_as_default,
    )

    return {
        'success': True,
        'message': f'Environment "{name}" added/updated. Use list_agents() and select_agent() to configure an agent.',
        'environment': env.to_dict(),
    }


@mcp.tool()
def list_agents() -> dict:
    """List available agents from the backend.

    Fetches agents from the current environment's backend.
    Use select_agent() to choose one for execution.

    Returns:
        List of available agents with their IDs, names, URLs, and status
    """
    config = _get_config()
    client = config.get_backend_client()

    if not client:
        return {
            'success': False,
            'error': 'No backend configured. Use add_environment() first with backend_url and access_token.',
        }

    try:
        agents = client.list_agents()
        agent_list = []
        for agent in agents:
            agent_list.append({
                'id': agent.id,
                'name': agent.name,
                'url': agent.url,
                'status': agent.status,
                'is_connected': agent.is_connected,
            })

        env = config.get_active_environment()
        return {
            'success': True,
            'agents': agent_list,
            'current_agent_id': env.agent_id if env else None,
            'hint': 'Use select_agent(agent_id) to select an agent for execution.',
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def select_agent(agent_id: int) -> dict:
    """Select an agent for the current environment.

    Fetches the agent details from the backend and saves
    the agent URL and token for the current environment.

    Args:
        agent_id: The agent ID from list_agents()

    Returns:
        The selected agent configuration
    """
    config = _get_config()
    client = config.get_backend_client()

    if not client:
        return {
            'success': False,
            'error': 'No backend configured. Use add_environment() first.',
        }

    try:
        agents = client.list_agents()
        selected = None
        for agent in agents:
            if agent.id == agent_id:
                selected = agent
                break

        if not selected:
            return {
                'success': False,
                'error': f'Agent {agent_id} not found.',
                'available_ids': [a.id for a in agents],
            }

        # Save to config
        config.set_agent(
            agent_id=selected.id,
            agent_name=selected.name,
            agent_url=selected.url,
            agent_token=selected.token,
        )

        return {
            'success': True,
            'message': f'Agent "{selected.name}" selected for current environment.',
            'agent': {
                'id': selected.id,
                'name': selected.name,
                'url': selected.url,
                'status': selected.status,
            },
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def clear_agent() -> dict:
    """Clear the agent configuration for the current environment.

    Returns:
        Status of the operation
    """
    config = _get_config()

    if config.clear_agent():
        return {'success': True, 'message': 'Agent cleared for current environment.'}
    else:
        return {'success': False, 'error': 'No active environment.'}


# =============================================================================
# Plugin Tools
# =============================================================================


@mcp.tool()
def list_plugin_releases(limit: int = 20, offset: int = 0) -> dict:
    """List published plugin releases from the current environment.

    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip

    Returns:
        List of plugin releases
    """
    config = _get_config()
    client = config.get_agent_client()

    if not client:
        return {
            'success': False,
            'error': 'No agent configured for current environment. Use switch_environment() first.',
        }

    try:
        releases, total = client.list_plugin_releases(
            params={'limit': limit, 'offset': offset},
            list_all=False,
        )
        return {
            'success': True,
            'releases': releases,
            'total': total,
            'limit': limit,
            'offset': offset,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def get_plugin_release(lookup: str) -> dict:
    """Get details of a specific plugin release.

    Args:
        lookup: Plugin release ID or 'code:version' string

    Returns:
        Plugin release details
    """
    config = _get_config()
    client = config.get_agent_client()

    if not client:
        return {
            'success': False,
            'error': 'No agent configured for current environment.',
        }

    try:
        release = client.get_plugin_release(lookup)
        return {'success': True, 'release': release}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def discover_local_plugin(path: str) -> dict:
    """Discover actions in a local plugin directory.

    Args:
        path: Path to the plugin directory

    Returns:
        Plugin configuration and list of available actions
    """
    from pathlib import Path

    from synapse_sdk.plugins.discovery import PluginDiscovery

    plugin_path = Path(path).expanduser().resolve()

    if not plugin_path.exists():
        return {'success': False, 'error': f'Path not found: {plugin_path}'}

    try:
        discovery = PluginDiscovery.from_path(plugin_path)
        actions = discovery.list_actions()

        action_details = []
        for action_name in actions:
            try:
                action_config = discovery.get_action_config(action_name)
                action_details.append({
                    'name': action_name,
                    'description': action_config.description,
                    'method': action_config.method.value if action_config.method else None,
                })
            except Exception:
                action_details.append({'name': action_name})

        return {
            'success': True,
            'path': str(plugin_path),
            'plugin_config': discovery.to_config_dict(include_ui_schemas=False),
            'actions': action_details,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def get_action_config(path: str, action: str) -> dict:
    """Get detailed configuration and parameter schema for a plugin action.

    Args:
        path: Path to the plugin directory
        action: Name of the action

    Returns:
        Action configuration including parameter schema
    """
    from pathlib import Path

    from synapse_sdk.plugins.discovery import PluginDiscovery

    plugin_path = Path(path).expanduser().resolve()

    if not plugin_path.exists():
        return {'success': False, 'error': f'Path not found: {plugin_path}'}

    try:
        discovery = PluginDiscovery.from_path(plugin_path)

        if not discovery.has_action(action):
            return {
                'success': False,
                'error': f'Action "{action}" not found',
                'available_actions': discovery.list_actions(),
            }

        action_config = discovery.get_action_config(action)
        params_model = discovery.get_action_params_model(action)
        result_model = discovery.get_action_result_model(action)

        params_schema = None
        if params_model:
            params_schema = params_model.model_json_schema()

        result_schema = None
        if result_model:
            result_schema = result_model.model_json_schema()

        return {
            'success': True,
            'action': action,
            'config': {
                'name': action_config.name,
                'description': action_config.description,
                'entrypoint': action_config.entrypoint,
                'method': action_config.method.value if action_config.method else None,
            },
            'params_schema': params_schema,
            'result_schema': result_schema,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def validate_plugin_config(path: str) -> dict:
    """Validate a plugin's config.yaml file.

    Args:
        path: Path to the plugin directory

    Returns:
        Validation result with any errors or warnings
    """
    from pathlib import Path

    import yaml

    from synapse_sdk.plugins.discovery import PluginDiscovery

    plugin_path = Path(path).expanduser().resolve()
    config_file = plugin_path / 'config.yaml'

    if not plugin_path.exists():
        return {'success': False, 'error': f'Path not found: {plugin_path}'}

    if not config_file.exists():
        return {'success': False, 'error': f'config.yaml not found at: {config_file}'}

    errors = []
    warnings = []

    # Check YAML syntax
    try:
        with open(config_file) as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return {'success': False, 'valid': False, 'errors': [f'YAML syntax error: {e}']}

    # Check required fields
    if not raw_config:
        errors.append('config.yaml is empty')
    else:
        if 'code' not in raw_config:
            errors.append("Missing required field: 'code'")
        if 'name' not in raw_config:
            warnings.append("Missing recommended field: 'name'")
        if 'version' not in raw_config:
            warnings.append("Missing recommended field: 'version'")
        if 'actions' not in raw_config or not raw_config.get('actions'):
            errors.append('No actions defined')

    # Try to load as a full plugin
    try:
        discovery = PluginDiscovery.from_path(plugin_path)
        actions = discovery.list_actions()

        # Validate each action
        for action_name in actions:
            try:
                discovery.get_action_config(action_name)
            except Exception as e:
                errors.append(f"Action '{action_name}' config error: {e}")

            try:
                discovery.get_action_params_model(action_name)
            except Exception as e:
                warnings.append(f"Action '{action_name}' params model warning: {e}")

    except Exception as e:
        errors.append(f'Plugin discovery failed: {e}')

    return {
        'success': True,
        'valid': len(errors) == 0,
        'path': str(plugin_path),
        'errors': errors,
        'warnings': warnings,
        'config': raw_config,
    }


@mcp.tool()
def publish_plugin(path: str, version: str | None = None) -> dict:
    """Publish a local plugin to the registry.

    Args:
        path: Path to the plugin directory
        version: Version string (overrides config.yaml version if provided)

    Returns:
        Published plugin release details
    """
    from pathlib import Path

    from synapse_sdk.plugins.discovery import PluginDiscovery

    config = _get_config()
    client = config.get_agent_client()

    if not client:
        return {
            'success': False,
            'error': 'No agent configured for current environment.',
        }

    plugin_path = Path(path).expanduser().resolve()
    if not plugin_path.exists():
        return {'success': False, 'error': f'Path not found: {plugin_path}'}

    # Validate first
    validation = validate_plugin_config(str(plugin_path))
    if not validation.get('valid', False):
        return {
            'success': False,
            'error': 'Plugin validation failed',
            'validation_errors': validation.get('errors', []),
        }

    try:
        discovery = PluginDiscovery.from_path(plugin_path)
        plugin_config = discovery.config

        # Use provided version or fall back to config
        publish_version = version or plugin_config.version
        if not publish_version:
            return {
                'success': False,
                'error': 'No version specified. Provide version parameter or set in config.yaml',
            }

        result = client.publish_plugin_release(
            plugin_path=str(plugin_path),
            version=publish_version,
        )

        return {
            'success': True,
            'message': f'Plugin "{plugin_config.code}" version {publish_version} published',
            'release': result,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# =============================================================================
# Execution Tools
# =============================================================================


@mcp.tool()
def run_plugin(plugin: str, action: str, params: dict | None = None) -> dict:
    """Run a published plugin action via the agent.

    Args:
        plugin: Plugin code or 'code:version' string
        action: Action name to execute
        params: Parameters to pass to the action

    Returns:
        Execution result or job ID for async execution
    """
    config = _get_config()
    client = config.get_agent_client()

    if not client:
        return {
            'success': False,
            'error': 'No agent configured for current environment.',
        }

    try:
        result = client.run_plugin_release(
            lookup=plugin,
            action=action,
            params=params or {},
        )
        return {'success': True, 'result': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def run_debug_plugin(
    path: str,
    action: str,
    params: dict | None = None,
) -> dict:
    """Run a local plugin for debugging via the agent.

    This uploads the plugin code temporarily and runs it on the agent.

    Args:
        path: Path to the local plugin directory
        action: Action name to execute
        params: Parameters to pass to the action

    Returns:
        Execution result
    """
    from pathlib import Path

    config = _get_config()
    client = config.get_agent_client()

    if not client:
        return {
            'success': False,
            'error': 'No agent configured for current environment.',
        }

    plugin_path = Path(path).expanduser().resolve()
    if not plugin_path.exists():
        return {'success': False, 'error': f'Path not found: {plugin_path}'}

    try:
        result = client.run_debug_plugin_release(
            action=action,
            params=params or {},
            plugin_path=str(plugin_path),
        )
        return {'success': True, 'result': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def run_local_plugin(
    path: str,
    action: str,
    params: dict | None = None,
    mode: str = 'local',
) -> dict:
    """Run a local plugin directly (without agent).

    Args:
        path: Path to the local plugin directory
        action: Action name to execute
        params: Parameters to pass to the action
        mode: Execution mode - 'local' (in-process), 'task' (Ray Actor), or 'job' (Ray Job)

    Returns:
        Execution result
    """
    from pathlib import Path

    from synapse_sdk.plugins.runner import run_plugin as sdk_run_plugin

    plugin_path = Path(path).expanduser().resolve()
    if not plugin_path.exists():
        return {'success': False, 'error': f'Path not found: {plugin_path}'}

    if mode not in ('local', 'task', 'job'):
        return {'success': False, 'error': f'Invalid mode: {mode}. Use local, task, or job.'}

    try:
        result = sdk_run_plugin(
            plugin_code=str(plugin_path),
            action=action,
            params=params or {},
            mode=mode,
        )
        return {'success': True, 'result': result, 'mode': mode}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# =============================================================================
# Jobs & Logs Tools
# =============================================================================


@mcp.tool()
def list_jobs(limit: int = 20, status: str | None = None) -> dict:
    """List jobs from the current environment.

    Args:
        limit: Maximum number of jobs to return
        status: Filter by status (e.g., 'RUNNING', 'SUCCEEDED', 'FAILED', 'STOPPED', 'PENDING')

    Returns:
        List of jobs
    """
    config = _get_config()
    client = config.get_backend_client()

    if not client:
        return {
            'success': False,
            'error': 'No backend configured for current environment.',
        }

    env = config.get_active_environment()
    if not env or not env.agent_id:
        return {
            'success': False,
            'error': 'No agent selected. Use list_agents() and select_agent() first.',
        }

    try:
        params = {'limit': limit, 'agent': env.agent_id}
        if status:
            params['status'] = status.lower()

        result = client.list_jobs(params=params)

        # Backend returns paginated response
        jobs = result.get('results', []) if isinstance(result, dict) else result

        return {'success': True, 'jobs': jobs, 'count': len(jobs)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def get_job(job_id: str) -> dict:
    """Get details of a specific job.

    Args:
        job_id: The job ID (integer or UUID string)

    Returns:
        Job details including status, timestamps, and metadata
    """
    config = _get_config()
    client = config.get_backend_client()

    if not client:
        return {
            'success': False,
            'error': 'No backend configured for current environment.',
        }

    try:
        job = client.get_job(job_id)
        return {'success': True, 'job': job}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def get_job_logs(job_id: str, lines: int = 100) -> dict:
    """Get logs from a job.

    Args:
        job_id: The job ID (integer or UUID string)
        lines: Number of log lines to return (tail)

    Returns:
        Job logs
    """
    config = _get_config()
    client = config.get_backend_client()

    if not client:
        return {
            'success': False,
            'error': 'No backend configured for current environment.',
        }

    try:
        result = client.list_job_console_logs(job_id)

        # Extract log entries from response
        log_entries = result.get('results', []) if isinstance(result, dict) else result

        # Format logs as text
        log_lines = []
        for entry in log_entries:
            if isinstance(entry, dict):
                message = entry.get('message', entry.get('log', str(entry)))
                log_lines.append(message)
            else:
                log_lines.append(str(entry))

        # Return last N lines
        if len(log_lines) > lines:
            log_lines = log_lines[-lines:]

        logs = '\n'.join(log_lines)
        return {'success': True, 'logs': logs, 'job_id': job_id}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def stop_job(job_id: str) -> dict:
    """Stop a running job.

    Args:
        job_id: The job ID (integer or UUID string) to stop

    Returns:
        Stop operation result
    """
    config = _get_config()
    client = config.get_backend_client()

    if not client:
        return {
            'success': False,
            'error': 'No backend configured for current environment.',
        }

    try:
        # Update job status to stopped
        result = client.update_job(int(job_id), {'status': 'stopped'})
        return {'success': True, 'result': result, 'job_id': job_id}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# =============================================================================
# Deployment Tools
# =============================================================================


@mcp.tool()
def list_serve_applications() -> dict:
    """List deployed Ray Serve applications.

    Returns:
        List of serve applications
    """
    config = _get_config()
    client = config.get_backend_client()

    if not client:
        return {
            'success': False,
            'error': 'No backend configured for current environment.',
        }

    try:
        result = client.list_serve_applications()

        # Backend returns paginated response
        applications = result.get('results', []) if isinstance(result, dict) else result

        return {'success': True, 'applications': applications}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def get_serve_application(name: str) -> dict:
    """Get details of a Ray Serve application.

    Args:
        name: Application name

    Returns:
        Application details
    """
    config = _get_config()
    client = config.get_agent_client()

    if not client:
        return {
            'success': False,
            'error': 'No agent configured for current environment.',
        }

    try:
        application = client.get_serve_application(name)
        return {'success': True, 'application': application}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def delete_serve_application(name: str) -> dict:
    """Delete a Ray Serve application.

    Args:
        name: Application name to delete

    Returns:
        Deletion result
    """
    config = _get_config()
    client = config.get_agent_client()

    if not client:
        return {
            'success': False,
            'error': 'No agent configured for current environment.',
        }

    try:
        client.delete_serve_application(name)
        return {'success': True, 'message': f'Application "{name}" deleted'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# =============================================================================
# Model Tools
# =============================================================================


@mcp.tool()
def list_models(limit: int = 20, offset: int = 0) -> dict:
    """List available models from the current environment.

    Args:
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of models
    """
    config = _get_config()
    client = config.get_backend_client()

    if not client:
        return {
            'success': False,
            'error': 'No backend configured for current environment.',
        }

    try:
        result = client.list_models(params={'limit': limit, 'offset': offset})
        return {'success': True, 'models': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@mcp.tool()
def get_model(model_id: int) -> dict:
    """Get details of a specific model.

    Args:
        model_id: The model ID

    Returns:
        Model details
    """
    config = _get_config()
    client = config.get_backend_client()

    if not client:
        return {
            'success': False,
            'error': 'No backend configured for current environment.',
        }

    try:
        model = client.get_model(model_id)
        return {'success': True, 'model': model}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# =============================================================================
# MCP Resources
# =============================================================================


@mcp.resource('synapse://config')
def resource_config() -> str:
    """Current Synapse configuration (sanitized, no tokens)."""
    import json

    config = _get_config()
    env_list = []

    for name in config.list_environments():
        env = config.get_environment(name)
        if env:
            env_list.append({
                'name': name,
                'backend_url': env.backend_url,
                'agent_url': env.agent_url,
                'tenant': env.tenant,
                'has_access_token': bool(env.access_token),
                'has_agent_token': bool(env.agent_token),
                'plugin_paths': env.plugin_paths,
            })

    return json.dumps(
        {
            'config_path': str(config.config_path),
            'default_environment': config._default_environment,
            'active_environment': config.get_active_environment_name(),
            'environments': env_list,
        },
        indent=2,
    )


@mcp.resource('synapse://environments')
def resource_environments() -> str:
    """List of all configured environments."""
    import json

    config = _get_config()
    environments = []

    for name in config.list_environments():
        env = config.get_environment(name)
        if env:
            environments.append(env.to_dict())

    return json.dumps(
        {
            'environments': environments,
            'active': config.get_active_environment_name(),
        },
        indent=2,
    )


@mcp.resource('synapse://plugin/{path}/config')
def resource_plugin_config(path: str) -> str:
    """Plugin config.yaml content."""
    from pathlib import Path

    import yaml

    plugin_path = Path(path).expanduser().resolve()
    config_file = plugin_path / 'config.yaml'

    if not config_file.exists():
        return f'Error: config.yaml not found at {config_file}'

    with open(config_file) as f:
        return yaml.safe_dump(yaml.safe_load(f), default_flow_style=False)


@mcp.resource('synapse://plugin/{path}/actions')
def resource_plugin_actions(path: str) -> str:
    """List of actions in a plugin."""
    import json
    from pathlib import Path

    from synapse_sdk.plugins.discovery import PluginDiscovery

    plugin_path = Path(path).expanduser().resolve()

    if not plugin_path.exists():
        return f'Error: Path not found: {plugin_path}'

    try:
        discovery = PluginDiscovery.from_path(plugin_path)
        actions = []

        for action_name in discovery.list_actions():
            try:
                action_config = discovery.get_action_config(action_name)
                actions.append({
                    'name': action_name,
                    'description': action_config.description,
                    'method': action_config.method.value if action_config.method else None,
                    'entrypoint': action_config.entrypoint,
                })
            except Exception:
                actions.append({'name': action_name})

        return json.dumps({'plugin': str(plugin_path), 'actions': actions}, indent=2)
    except Exception as e:
        return f'Error: {e}'


@mcp.resource('synapse://plugin/{path}/action/{action}/schema')
def resource_action_schema(path: str, action: str) -> str:
    """Action parameter JSON schema."""
    import json
    from pathlib import Path

    from synapse_sdk.plugins.discovery import PluginDiscovery

    plugin_path = Path(path).expanduser().resolve()

    if not plugin_path.exists():
        return f'Error: Path not found: {plugin_path}'

    try:
        discovery = PluginDiscovery.from_path(plugin_path)

        if not discovery.has_action(action):
            return f'Error: Action "{action}" not found. Available: {discovery.list_actions()}'

        params_model = discovery.get_action_params_model(action)
        result_model = discovery.get_action_result_model(action)

        schema = {
            'action': action,
            'params_schema': params_model.model_json_schema() if params_model else None,
            'result_schema': result_model.model_json_schema() if result_model else None,
        }

        return json.dumps(schema, indent=2)
    except Exception as e:
        return f'Error: {e}'


# =============================================================================
# MCP Prompts
# =============================================================================


@mcp.prompt()
def debug_plugin(plugin_path: str, action: str = '') -> str:
    """Guide through debugging a local plugin.

    Args:
        plugin_path: Path to the local plugin directory
        action: Optional action name to focus on
    """
    prompt = f"""You are helping debug a local Synapse plugin.

Plugin Path: {plugin_path}

Steps to debug:

1. First, discover the plugin to see available actions:
   Use the `discover_local_plugin` tool with path="{plugin_path}"

2. Validate the plugin configuration:
   Use the `validate_plugin_config` tool with path="{plugin_path}"

3. If there are validation errors, help fix them by examining the config.yaml

4. To test an action locally (without remote agent):
   Use the `run_local_plugin` tool with path="{plugin_path}", action="<action_name>", params={{...}}, mode="local"

5. To test via the remote agent (for debugging in prod-like environment):
   Use the `run_debug_plugin` tool with path="{plugin_path}", action="<action_name>", params={{...}}

6. Check job logs if execution fails:
   Use `list_jobs` to find recent jobs, then `get_job_logs` for details
"""

    if action:
        prompt += f"""
Focus on action: {action}

Get the action schema:
   Use the `get_action_config` tool with path="{plugin_path}", action="{action}"
"""

    return prompt


@mcp.prompt()
def publish_plugin_workflow(plugin_path: str, version: str = '') -> str:
    """Guide through publishing a plugin to the registry.

    Args:
        plugin_path: Path to the local plugin directory
        version: Version to publish (optional)
    """
    version_note = f'Version to publish: {version}' if version else 'Version: (will use config.yaml version)'

    return f"""You are helping publish a Synapse plugin to the registry.

Plugin Path: {plugin_path}
{version_note}

Pre-publish checklist:

1. Validate the plugin configuration:
   Use `validate_plugin_config` with path="{plugin_path}"
   - Ensure no errors (warnings are okay)
   - Verify 'code', 'version', and 'actions' are properly defined

2. Test the plugin locally:
   Use `run_local_plugin` with path="{plugin_path}" and test each action

3. Verify the current environment:
   Use `get_current_environment` to confirm you're publishing to the right registry

4. Publish the plugin:
   Use `publish_plugin` with path="{plugin_path}"{f', version="{version}"' if version else ''}

5. Verify the publication:
   Use `get_plugin_release` with the plugin code:version to confirm

Post-publish:
- The plugin is now available in the registry
- Others can run it using `run_plugin` with the plugin code
"""


@mcp.prompt()
def diagnose_job(job_id: str) -> str:
    """Help diagnose a failed or problematic job.

    Args:
        job_id: The job ID to diagnose
    """
    return f"""You are helping diagnose a Synapse job.

Job ID: {job_id}

Diagnostic steps:

1. Get job details:
   Use `get_job` with job_id="{job_id}"
   - Check status: PENDING, RUNNING, SUCCEEDED, FAILED, STOPPED
   - Note the plugin/action that was run
   - Check start/end times

2. Get job logs:
   Use `get_job_logs` with job_id="{job_id}", lines=200
   - Look for error messages, stack traces
   - Check for timeout issues
   - Look for resource constraints (OOM, CPU limits)

3. If the job is stuck RUNNING:
   - Check if it's actually making progress in logs
   - Consider using `stop_job` if it's hung

4. Common issues to check:
   - Plugin code errors (stack traces in logs)
   - Configuration errors (missing params, wrong types)
   - Resource limits (memory, CPU, GPU)
   - Network issues (can't reach external services)
   - Timeout (job took too long)

5. If you need to re-run with fixes:
   - For published plugins: use `run_plugin`
   - For local plugins: use `run_local_plugin` or `run_debug_plugin`
"""


@mcp.prompt()
def setup_environment(env_name: str = 'prod') -> str:
    """Guide through setting up a new Synapse environment.

    Args:
        env_name: Name for the new environment (default: prod)
    """
    return f"""You are helping set up a new Synapse environment.

Environment Name: {env_name}

Setup steps:

1. First, check existing environments:
   Use `list_environments` to see what's already configured

2. Gather the required information:
   - Backend URL: The Synapse API server URL (e.g., https://api.synapse.example.com)
   - Access Token: Your API access token
   - Tenant: Your tenant identifier (optional)

3. Add the environment:
   Use `add_environment` with:
   - name="{env_name}"
   - backend_url="<your_backend_url>"
   - access_token="<your_access_token>"
   - tenant="<your_tenant>" (if applicable)
   - set_as_default=True (if this should be the default)

4. Switch to the new environment:
   Use `switch_environment` with name="{env_name}"

5. Configure the agent (fetched from backend):
   - Use `list_agents` to see available agents
   - Use `select_agent(agent_id)` to choose one

6. Verify the connection:
   Use `get_current_environment` to check backend/agent status

7. Test basic functionality:
   - Use `list_plugin_releases` to verify backend connection
   - Use `list_jobs` to verify agent connection

Configuration file location: ~/.synapse/config.yaml
"""


# =============================================================================
# Server Entry Point
# =============================================================================


def serve() -> None:
    """Run the MCP server."""
    _log('Starting Synapse MCP server...')
    config = _get_config()
    _log(f'Config path: {config.config_path}')
    _log(f'Environments: {config.list_environments()}')
    _log(f'Active environment: {config.get_active_environment_name()}')
    mcp.run()


if __name__ == '__main__':
    serve()
