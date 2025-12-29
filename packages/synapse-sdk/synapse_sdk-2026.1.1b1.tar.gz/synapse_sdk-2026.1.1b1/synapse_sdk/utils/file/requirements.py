"""Requirements file parsing utilities."""

from __future__ import annotations

from pathlib import Path


def read_requirements(path: str | Path) -> list[str] | None:
    """Parse requirements.txt file.

    Reads a requirements.txt file and returns a list of requirement strings,
    filtering out empty lines and comments.

    Args:
        path: Path to requirements.txt file

    Returns:
        List of requirement strings, or None if file doesn't exist.
        Returns None if file exists but contains no valid requirements.
    """
    path = Path(path)
    if not path.exists():
        return None

    requirements = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                requirements.append(line)

    return requirements if requirements else None


__all__ = ['read_requirements']
