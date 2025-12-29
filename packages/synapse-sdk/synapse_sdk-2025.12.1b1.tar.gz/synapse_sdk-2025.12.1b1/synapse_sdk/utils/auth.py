"""Authentication utilities for SDK."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient

# Environment variable names
ENV_SYNAPSE_HOST = 'SYNAPSE_HOST'
ENV_SYNAPSE_ACCESS_TOKEN = 'SYNAPSE_ACCESS_TOKEN'

# Default host
DEFAULT_HOST = 'https://api.synapse.sh'

# Credentials file path
CREDENTIALS_FILE = Path.home() / '.synapse' / 'credentials'


def load_credentials() -> tuple[str | None, str | None]:
    """Load credentials from environment or credentials file.

    Priority:
    1. Environment variables (SYNAPSE_HOST, SYNAPSE_ACCESS_TOKEN)
    2. Credentials file (~/.synapse/credentials)

    Returns:
        Tuple of (host, token). Either may be None if not found.
    """
    host = os.environ.get(ENV_SYNAPSE_HOST)
    token = os.environ.get(ENV_SYNAPSE_ACCESS_TOKEN)

    # Fall back to credentials file
    if not token and CREDENTIALS_FILE.exists():
        for line in CREDENTIALS_FILE.read_text().splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if key == ENV_SYNAPSE_HOST and not host:
                    host = value
                elif key == ENV_SYNAPSE_ACCESS_TOKEN and not token:
                    token = value

    return host, token


def create_backend_client() -> BackendClient | None:
    """Create a BackendClient from environment/credentials if available.

    Returns:
        BackendClient if credentials are available, None otherwise.
    """
    host, token = load_credentials()

    if not token:
        return None

    from synapse_sdk.clients.backend import BackendClient

    return BackendClient(base_url=host or DEFAULT_HOST, access_token=token)


__all__ = [
    'ENV_SYNAPSE_HOST',
    'ENV_SYNAPSE_ACCESS_TOKEN',
    'DEFAULT_HOST',
    'CREDENTIALS_FILE',
    'load_credentials',
    'create_backend_client',
]
