"""MCP Server configuration and environment management."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class EnvironmentConfig:
    """Configuration for a single environment."""

    name: str
    backend_url: str | None = None
    access_token: str | None = None
    tenant: str | None = None
    # Agent info is fetched from backend, but cached here after selection
    agent_id: int | None = None
    agent_name: str | None = None
    agent_url: str | None = None
    agent_token: str | None = None
    plugin_paths: list[str] = field(default_factory=list)

    def has_backend(self) -> bool:
        """Check if backend is configured."""
        return bool(self.backend_url and self.access_token)

    def has_agent(self) -> bool:
        """Check if agent is configured."""
        return bool(self.agent_url and self.agent_token)

    def to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """Convert to dictionary, optionally hiding secrets."""
        result = {
            'name': self.name,
            'backend_url': self.backend_url,
            'tenant': self.tenant,
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'agent_url': self.agent_url,
            'plugin_paths': self.plugin_paths,
            'has_backend': self.has_backend(),
            'has_agent': self.has_agent(),
        }
        if include_secrets:
            result['access_token'] = self.access_token
            result['agent_token'] = self.agent_token
        else:
            result['access_token'] = '***' if self.access_token else None
            result['agent_token'] = '***' if self.agent_token else None
        return result


class ConfigManager:
    """Manages MCP server configuration and environment switching."""

    DEFAULT_CONFIG_PATH = Path.home() / '.synapse' / 'config.yaml'

    def __init__(self, config_path: Path | str | None = None):
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self._environments: dict[str, EnvironmentConfig] = {}
        self._default_env: str | None = None
        self._active_env: str | None = None
        self._backend_client: Any = None
        self._agent_client: Any = None
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            self._log(f'Config file not found: {self.config_path}')
            return

        try:
            with open(self.config_path) as f:
                data = yaml.safe_load(f) or {}

            self._default_env = data.get('default_environment')

            for name, env_data in data.get('environments', {}).items():
                if env_data is None:
                    env_data = {}
                self._environments[name] = EnvironmentConfig(
                    name=name,
                    backend_url=env_data.get('backend_url'),
                    access_token=env_data.get('access_token'),
                    tenant=env_data.get('tenant'),
                    agent_id=env_data.get('agent_id'),
                    agent_name=env_data.get('agent_name'),
                    agent_url=env_data.get('agent_url'),
                    agent_token=env_data.get('agent_token'),
                    plugin_paths=env_data.get('plugin_paths', []),
                )

            # Set active environment to default
            if self._default_env and self._default_env in self._environments:
                self._active_env = self._default_env

            self._log(f'Loaded {len(self._environments)} environments from {self.config_path}')

        except Exception as e:
            self._log(f'Error loading config: {e}')

    def _save_config(self) -> None:
        """Save current configuration to YAML file."""
        data = {
            'default_environment': self._default_env,
            'environments': {},
        }

        for name, env in self._environments.items():
            env_data: dict[str, Any] = {}
            if env.backend_url:
                env_data['backend_url'] = env.backend_url
            if env.access_token:
                env_data['access_token'] = env.access_token
            if env.tenant:
                env_data['tenant'] = env.tenant
            if env.agent_id:
                env_data['agent_id'] = env.agent_id
            if env.agent_name:
                env_data['agent_name'] = env.agent_name
            if env.agent_url:
                env_data['agent_url'] = env.agent_url
            if env.agent_token:
                env_data['agent_token'] = env.agent_token
            if env.plugin_paths:
                env_data['plugin_paths'] = env.plugin_paths
            data['environments'][name] = env_data

        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        # Set restrictive permissions (owner read/write only)
        self.config_path.chmod(0o600)

    def _log(self, message: str) -> None:
        """Log to stderr (safe for MCP STDIO transport)."""
        print(f'[synapse-mcp] {message}', file=sys.stderr)

    def _clear_clients(self) -> None:
        """Clear cached client instances."""
        self._backend_client = None
        self._agent_client = None

    # Environment management

    def list_environments(self) -> list[str]:
        """List all configured environment names."""
        return list(self._environments.keys())

    def get_environment(self, name: str) -> EnvironmentConfig | None:
        """Get environment configuration by name."""
        return self._environments.get(name)

    def get_active_environment(self) -> EnvironmentConfig | None:
        """Get the currently active environment."""
        if self._active_env:
            return self._environments.get(self._active_env)
        return None

    def get_active_environment_name(self) -> str | None:
        """Get the name of the currently active environment."""
        return self._active_env

    def set_active_environment(self, name: str) -> bool:
        """Set the active environment by name."""
        if name not in self._environments:
            return False
        self._active_env = name
        self._clear_clients()
        self._log(f'Switched to environment: {name}')
        return True

    def add_environment(
        self,
        name: str,
        backend_url: str | None = None,
        access_token: str | None = None,
        tenant: str | None = None,
        plugin_paths: list[str] | None = None,
        set_as_default: bool = False,
    ) -> EnvironmentConfig:
        """Add or update an environment configuration.

        Note: Agent is configured separately via set_agent() after fetching from backend.
        """
        # Preserve existing agent config if updating
        existing = self._environments.get(name)
        env = EnvironmentConfig(
            name=name,
            backend_url=backend_url,
            access_token=access_token,
            tenant=tenant,
            agent_id=existing.agent_id if existing else None,
            agent_name=existing.agent_name if existing else None,
            agent_url=existing.agent_url if existing else None,
            agent_token=existing.agent_token if existing else None,
            plugin_paths=plugin_paths or [],
        )
        self._environments[name] = env

        if set_as_default or not self._default_env:
            self._default_env = name

        if not self._active_env:
            self._active_env = name

        self._save_config()
        self._log(f'Added environment: {name}')
        return env

    def set_agent(
        self,
        agent_id: int,
        agent_name: str | None = None,
        agent_url: str | None = None,
        agent_token: str | None = None,
    ) -> bool:
        """Set the agent for the active environment.

        Args:
            agent_id: Agent ID from backend
            agent_name: Agent name
            agent_url: Agent URL
            agent_token: Agent authentication token

        Returns:
            True if successful, False if no active environment
        """
        env = self.get_active_environment()
        if not env:
            return False

        env.agent_id = agent_id
        env.agent_name = agent_name
        env.agent_url = agent_url
        env.agent_token = agent_token
        self._clear_clients()
        self._save_config()
        self._log(f'Set agent {agent_id} ({agent_name}) for environment: {env.name}')
        return True

    def clear_agent(self) -> bool:
        """Clear the agent for the active environment."""
        env = self.get_active_environment()
        if not env:
            return False

        env.agent_id = None
        env.agent_name = None
        env.agent_url = None
        env.agent_token = None
        self._clear_clients()
        self._save_config()
        self._log(f'Cleared agent for environment: {env.name}')
        return True

    def remove_environment(self, name: str) -> bool:
        """Remove an environment configuration."""
        if name not in self._environments:
            return False

        del self._environments[name]

        if self._default_env == name:
            self._default_env = next(iter(self._environments), None)

        if self._active_env == name:
            self._active_env = self._default_env
            self._clear_clients()

        self._save_config()
        self._log(f'Removed environment: {name}')
        return True

    # Client access

    def get_backend_client(self):
        """Get BackendClient for the active environment."""
        env = self.get_active_environment()
        if not env or not env.has_backend():
            return None

        if self._backend_client is None:
            from synapse_sdk.clients.backend import BackendClient

            self._backend_client = BackendClient(
                base_url=env.backend_url,
                access_token=env.access_token,
                tenant=env.tenant,
            )

        return self._backend_client

    def get_agent_client(self):
        """Get AgentClient for the active environment."""
        env = self.get_active_environment()
        if not env or not env.has_agent():
            return None

        if self._agent_client is None:
            from synapse_sdk.clients import AgentClient

            self._agent_client = AgentClient(
                base_url=env.agent_url,
                agent_token=env.agent_token,
                tenant=env.tenant,
            )

        return self._agent_client

    # Status

    def get_status(self) -> dict[str, Any]:
        """Get current configuration status."""
        env = self.get_active_environment()
        return {
            'config_path': str(self.config_path),
            'config_exists': self.config_path.exists(),
            'environments': self.list_environments(),
            'default_environment': self._default_env,
            'active_environment': self._active_env,
            'active_env_details': env.to_dict() if env else None,
        }


# Global config manager instance
_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """Get the global ConfigManager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reset_config_manager() -> None:
    """Reset the global ConfigManager instance (for testing)."""
    global _config_manager
    _config_manager = None
