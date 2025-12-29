"""Synapse SDK MCP Server.

This module provides an MCP (Model Context Protocol) server that enables
AI assistants to interact with Synapse infrastructure for plugin development,
execution, debugging, and deployment.

Usage:
    # Initialize config (uses existing ~/.synapse/credentials if available)
    synapse mcp init

    # Run via CLI
    synapse mcp serve

    # Or run directly
    python -m synapse_sdk.mcp

    # Cursor: Add to ~/.cursor/mcp.json:
    {
        "mcpServers": {
            "synapse": {
                "command": "uvx",
                "args": ["--from", "synapse-sdk[mcp]", "synapse", "mcp", "serve"]
            }
        }
    }

    # Claude Code:
    claude mcp add synapse -- uvx --from 'synapse-sdk[mcp]' synapse mcp serve

Configuration (~/.synapse/config.yaml):
    default_environment: profile_1

    environments:
      profile_1:
        backend_url: https://api.synapse.sh
        access_token: your-token
"""

from synapse_sdk.mcp.config import ConfigManager, EnvironmentConfig, get_config_manager
from synapse_sdk.mcp.server import mcp, serve

__all__ = [
    'mcp',
    'serve',
    'ConfigManager',
    'EnvironmentConfig',
    'get_config_manager',
]
