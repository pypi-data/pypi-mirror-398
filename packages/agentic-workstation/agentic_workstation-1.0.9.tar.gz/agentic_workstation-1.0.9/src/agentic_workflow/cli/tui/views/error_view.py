"""
Error view for TUI.

This module contains views for displaying errors.
"""

from typing import Optional, Dict
from rich.console import Console
from rich.panel import Panel

from ..ui.input import InputHandler
from ..ui.theme import Theme


class ErrorView:
    """View for displaying error messages."""

    def __init__(self, console: Console, input_handler: InputHandler, theme_map: Optional[Dict[str, str]] = None):
        self.console = console
        self.input_handler = input_handler
        self.theme_map = theme_map or Theme.get_color_map()

    def display_error_modal(self, message: str, title: str = "Error", clear: bool = False) -> None:
        """Display an error modal and wait for user input."""
        if clear:
            self.console.clear()
        title_style = self.theme_map.get("error.text", "bold red")
        text_style = self.theme_map.get("error.text", "bold red")
        border_style = self.theme_map.get("error.border", self.theme_map.get("panel.border", "red"))
        error_panel = Panel(
            f"[{text_style}]{message}[/{text_style}]",
            title=f"[{title_style}]{title}[/{title_style}]",
            border_style=border_style,
            padding=(1, 2)
        )
        self.console.print(error_panel)
        self.input_handler.wait_for_user()


__all__ = ["ErrorView"]