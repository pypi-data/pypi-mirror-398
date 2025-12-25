"""Perform file and directory I/O operations used across the application.

Provide safe, cross-platform helpers for creating directories and reading
or writing text files with UTF-8 encoding. These functions are intentionally
small and deterministic to improve static analysis.
"""

from pathlib import Path
from typing import Union
import os

__all__ = [
    "create_directory",
    "ensure_parent_dir",
    "write_file",
    "read_file",
    "make_executable",
]


def create_directory(path: Union[str, Path]) -> Path:
    """Create a directory and its parents if they do not exist.

    Ensures the returned path exists and is a directory. Uses `Path.mkdir`
    with `parents=True` and `exist_ok=True` for idempotent behavior.

    Args:
        path: Directory path to create.

    Returns:
        Path: The directory path that now exists on disk.
    """
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent_dir(file_path: Union[str, Path]) -> Path:
    """Create the parent directory for `file_path` if it does not exist.

    This prevents file write errors by ensuring parent directories exist
    before any write operations.

    Args:
        file_path: Path to a target file.

    Returns:
        Path: The original file path as a `Path` object.
    """
    file_path = Path(file_path)
    parent = file_path.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    return file_path


def write_file(file_path: Union[str, Path], content: str, overwrite: bool = True) -> bool:
    """Write UTF-8 text to `file_path`, creating parents as needed.

    Args:
        file_path: Destination file path.
        content: Text content to write (assumed UTF-8).
        overwrite: If False, do not overwrite an existing file.

    Returns:
        bool: True if the file was written, False if skipped due to `overwrite=False`.
    """
    file_path = Path(file_path)
    if not overwrite and file_path.exists():
        return False
    ensure_parent_dir(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def read_file(file_path: Union[str, Path]) -> str:
    """Read and return the UTF-8 text contents of `file_path`.

    Args:
        file_path: Path to the file to read.

    Returns:
        str: File contents as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def make_executable(file_path: Union[str, Path]) -> None:
    """Set executable permission bits on a file (POSIX).

    Adds user/group/other execute bits to the file mode. On non-POSIX
    systems this is a best-effort no-op.

    Args:
        file_path: Path to the file to modify.
    """
    import stat
    file_path = Path(file_path)
    try:
        current = file_path.stat().st_mode
        file_path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        # Ignore permission changes on unsupported file systems
        pass
