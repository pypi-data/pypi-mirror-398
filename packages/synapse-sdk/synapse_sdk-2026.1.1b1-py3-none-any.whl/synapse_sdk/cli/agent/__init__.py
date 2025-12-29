"""Agent CLI commands."""

from synapse_sdk.cli.agent.config import (
    AgentConfig,
    clear_agent_config,
    get_agent_config,
    set_agent_config,
)
from synapse_sdk.cli.agent.select import (
    check_agent_connection,
    fetch_agents,
    select_agent_interactive,
)

__all__ = [
    # Config
    'AgentConfig',
    'get_agent_config',
    'set_agent_config',
    'clear_agent_config',
    # Selection
    'fetch_agents',
    'select_agent_interactive',
    'check_agent_connection',
]
