from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any


class PluginEnvironment:
    """Environment configuration for plugin execution.

    Auto-loads from:
    1. os.environ (lowest priority)
    2. Config file if provided (highest priority)

    Example:
        >>> env = PluginEnvironment.from_environ()
        >>> env.get_str('API_KEY')
        >>> env.get_int('BATCH_SIZE', default=32)
        >>> env.get_bool('DEBUG', default=False)
    """

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = data or {}

    @classmethod
    def from_environ(cls, prefix: str = '') -> PluginEnvironment:
        """Load from os.environ, optionally filtering by prefix."""
        data = {}
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            clean_key = key[len(prefix) :] if prefix else key
            data[clean_key] = value
        return cls(data)

    @classmethod
    def from_file(cls, path: str | Path) -> PluginEnvironment:
        """Load from TOML config file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f'Config file not found: {path}')
        with path.open('rb') as f:
            data = tomllib.load(f)
        return cls(data)

    @classmethod
    def merge(cls, *envs: PluginEnvironment) -> PluginEnvironment:
        """Merge multiple environments (later overrides earlier)."""
        merged: dict[str, Any] = {}
        for env in envs:
            merged.update(env._data)
        return cls(merged)

    def get(self, key: str, default: Any = None) -> Any:
        """Get raw value."""
        return self._data.get(key, default)

    def get_str(self, key: str, default: str | None = None) -> str | None:
        """Get string value."""
        val = self._data.get(key)
        if val is None:
            return default
        return str(val)

    def get_int(self, key: str, default: int | None = None) -> int | None:
        """Get integer value."""
        val = self._data.get(key)
        if val is None:
            return default
        return int(val)

    def get_float(self, key: str, default: float | None = None) -> float | None:
        """Get float value."""
        val = self._data.get(key)
        if val is None:
            return default
        return float(val)

    def get_bool(self, key: str, default: bool | None = None) -> bool | None:
        """Get boolean value (handles string 'true'/'false')."""
        val = self._data.get(key)
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ('true', '1', 'yes')
        return bool(val)

    def get_list(self, key: str, default: list | None = None) -> list | None:
        """Get list value (splits comma-separated strings)."""
        val = self._data.get(key)
        if val is None:
            return default
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            return [s.strip() for s in val.split(',') if s.strip()]
        return default

    def to_dict(self) -> dict[str, Any]:
        """Export as dictionary."""
        return dict(self._data)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]


__all__ = ['PluginEnvironment']
