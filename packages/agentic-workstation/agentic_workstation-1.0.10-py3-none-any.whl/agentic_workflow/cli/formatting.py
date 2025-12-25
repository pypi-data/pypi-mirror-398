#!/usr/bin/env python3
"""Formatting utility functions for Agentic Workflow CLI."""
from typing import List, Optional
from pathlib import Path
import shutil


__all__ = ["get_terminal_width", "shorten_path", "format_file_list"]


def get_terminal_width() -> int:
    """Get the current terminal width, with fallback."""
    try:
        return shutil.get_terminal_size().columns
    except (OSError, AttributeError):
        return 80  # Default fallback width

def shorten_path(
    path: str,
    max_length: int = 60,
    project_root: Optional[Path] = None,
    cwd: Optional[Path] = None
) -> str:
    """Shorten paths for display readability.

    Args:
        path: The path to shorten
        max_length: Maximum length for the shortened path
        project_root: Project root path for relative shortening (optional)
        cwd: Current working directory for relative shortening (optional)

    Returns:
        Shortened path string
    """
    if not path or not isinstance(path, str):
        return str(path) if path else ""

    try:
        path_obj = Path(path)
        path_str = str(path)

        if len(path_str) <= max_length:
            return path_str

        # Try relative to project root if provided
        if project_root:
            try:
                rel_path = path_obj.relative_to(project_root)
                rel_str = str(rel_path)
                if len(rel_str) < len(path_str):
                    return rel_str
            except ValueError:
                pass  # Path not relative to project root

        # Try relative to current directory if provided
        if cwd:
            try:
                rel_path = path_obj.relative_to(cwd)
                rel_str = str(rel_path)
                if len(rel_str) < len(path_str):
                    return f"./{rel_str}"
            except ValueError:
                pass  # Path not relative to cwd

        # Fallback: truncate with ellipsis
        if max_length > 3:
            return f"...{path_str[-max_length+3:]}"
        else:
            return path_str[:max_length]

    except Exception:
        # If anything fails, return the original path truncated
        return str(path)[:max_length] if len(str(path)) > max_length else str(path)


def format_file_list(files: List[str], prefix: str = "✓ Generated:", max_line_length: Optional[int] = None) -> List[str]:
    """Format a list of files with proper line breaking.

    Args:
        files: List of file paths to format
        prefix: Prefix string to add before each file
        max_line_length: Maximum line length before breaking. If None, uses terminal width.

    Returns:
        List of formatted strings ready for display
    """
    if not files or not isinstance(files, list):
        return []

    if max_line_length is None:
        max_line_length = get_terminal_width() - 10  # Leave some margin

    if not isinstance(prefix, str):
        prefix = "✓"

    formatted_lines = []

    for file_path in files:
        if not file_path or not isinstance(file_path, str):
            continue

        short_path = shorten_path(file_path)
        line = f"{prefix} {short_path}"

        if len(line) <= max_line_length:
            formatted_lines.append(line)
        else:
            # Break long lines
            formatted_lines.append(f"{prefix}")
            formatted_lines.append(f"  {short_path}")

    return formatted_lines