"""Plugin templates for synapse plugin create."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def _get_templates_dir() -> Path:
    """Get the templates directory path.

    Uses importlib.resources for reliable access to package data,
    falling back to __file__ for editable installs.
    """
    try:
        # Try importlib.resources first (works with installed packages)
        package_files = files('synapse_sdk.plugins.templates')
        # For filesystem-based packages, this will have a real path
        # joinpath returns a Traversable that we can use
        base = package_files / 'base'
        # Check if config.yaml.j2 exists to verify path is valid
        if (base / 'config.yaml.j2').is_file():
            # Get the actual path - package_files should be a Path-like for installed packages
            return Path(str(package_files))
    except (TypeError, AttributeError, FileNotFoundError):
        pass

    # Fall back to __file__ for editable installs or if above fails
    return Path(__file__).parent


# Cache the result to avoid repeated calls
TEMPLATES_DIR = _get_templates_dir()


def get_template_dir(category: str | None = None) -> Path:
    """Get template directory for a category.

    Args:
        category: Plugin category. If None, returns base template directory.

    Returns:
        Path to template directory.
    """
    if category:
        return TEMPLATES_DIR / category
    return TEMPLATES_DIR / 'base'


__all__ = ['TEMPLATES_DIR', 'get_template_dir']
