"""Utility modules for agentic-workflow-os."""

from pathlib import Path


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


__all__ = ["ensure_directory"]
