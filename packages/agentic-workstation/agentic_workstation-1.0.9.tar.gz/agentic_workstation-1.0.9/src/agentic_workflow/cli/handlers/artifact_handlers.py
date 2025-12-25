"""
Artifact handlers for TUI/CLI.

Provides filesystem-backed helpers for listing and reading artifacts
without embedding IO in controllers/views.
"""

from pathlib import Path
from typing import List, Tuple


class ArtifactHandlers:
    """Filesystem-backed artifact helpers."""

    def list_artifacts(self, artifacts_dir: Path) -> List[Tuple[Path, str]]:
        """Return a list of (full_path, relative_path) for artifacts."""
        artifacts: List[Tuple[Path, str]] = []
        if not artifacts_dir.exists():
            return artifacts

        for file_path in artifacts_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(artifacts_dir)
                artifacts.append((file_path, str(relative_path)))
        return artifacts

    def read_artifact(self, file_path: Path) -> str:
        """Read artifact content as text."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


__all__ = ["ArtifactHandlers"]