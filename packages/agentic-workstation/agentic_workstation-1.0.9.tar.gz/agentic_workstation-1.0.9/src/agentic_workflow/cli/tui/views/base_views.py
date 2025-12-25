"""
Base view class for data presentation.

This module contains the base view functionality shared across
different view implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from rich.console import Console

from ..ui import Theme

__all__ = ["BaseView"]


class BaseView(ABC):
    """Base class for view components."""

    def __init__(self, console: Console, theme_map: Optional[Dict[str, str]] = None):
        """Initialize the base view with an injected console instance."""
        self.console = console
        self.theme_map = theme_map or Theme.get_color_map()

    @abstractmethod
    def render(self, data: Any) -> None:
        """Render data to the console."""
        pass