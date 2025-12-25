"""
Type definitions for the TUI module.
"""

from enum import Enum


class ContextState(Enum):
    """Enumeration for TUI context states."""
    GLOBAL = "global"
    PROJECT = "project"