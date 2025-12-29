"""Agent configuration management."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# Config file path
CONFIG_DIR = Path.home() / '.synapse'
CONFIG_FILE = CONFIG_DIR / 'config.json'


@dataclass
class AgentConfig:
    """Agent configuration."""

    id: int
    name: str | None = None
    url: str | None = None
    token: str | None = None


def _ensure_config_dir() -> None:
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_config() -> dict:
    """Load configuration from file."""
    _ensure_config_dir()
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return {}


def _save_config(config: dict) -> None:
    """Save configuration to file."""
    _ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    CONFIG_FILE.chmod(0o600)


def get_agent_config() -> AgentConfig | None:
    """Get current agent configuration.

    Returns:
        AgentConfig if configured, None otherwise.
    """
    config = _load_config()
    agent = config.get('agent')
    if not agent or 'id' not in agent:
        return None
    return AgentConfig(
        id=agent['id'],
        name=agent.get('name'),
        url=agent.get('url'),
        token=agent.get('token'),
    )


def set_agent_config(
    agent_id: int,
    *,
    name: str | None = None,
    url: str | None = None,
    token: str | None = None,
) -> None:
    """Set agent configuration.

    Args:
        agent_id: Agent ID.
        name: Agent name.
        url: Agent URL.
        token: Agent authentication token.
    """
    config = _load_config()
    config['agent'] = {'id': agent_id}
    if name:
        config['agent']['name'] = name
    if url:
        config['agent']['url'] = url
    if token:
        config['agent']['token'] = token
    _save_config(config)


def clear_agent_config() -> None:
    """Clear agent configuration."""
    config = _load_config()
    if 'agent' in config:
        del config['agent']
    _save_config(config)


__all__ = [
    'AgentConfig',
    'get_agent_config',
    'set_agent_config',
    'clear_agent_config',
]
