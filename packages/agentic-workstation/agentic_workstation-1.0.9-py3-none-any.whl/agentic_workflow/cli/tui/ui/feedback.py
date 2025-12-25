"""Feedback presenter for TUI.

Provides TUI-native success/error/info/warning feedback using the shared console.
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .theme import Theme


class FeedbackPresenter:
    """Renders lightweight feedback panels without disrupting layout."""

    def __init__(self, console: Console, layout=None, theme_map=None):
        self.console = console
        self.layout = layout
        self.theme_map = theme_map or Theme.feedback_theme()

    def success(self, message: str) -> None:
        self._print(message, key_prefix="success")

    def error(self, message: str) -> None:
        self._print(message, key_prefix="error")

    def info(self, message: str) -> None:
        if not message:
            return
        self._print(message, key_prefix="info")

    def warning(self, message: str) -> None:
        self._print(message, key_prefix="warning")

    def _print(self, message: str, key_prefix: str) -> None:
        text_style = self.theme_map.get(f"{key_prefix}.text", Theme.INFO)
        border_style = self.theme_map.get(f"{key_prefix}.border", Theme.BORDER)
        panel = Panel(Text(message, style=text_style), border_style=border_style, padding=(0, 1))
        if self.layout:
            self.layout.render_status(panel)
        else:
            self.console.print(panel)


__all__ = ["FeedbackPresenter"]