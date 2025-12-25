"""Progress utilities for the TUI.

Provides spinner-based progress contexts using the shared console.
"""

from contextlib import contextmanager
from typing import Iterator
from rich.console import Console

from .theme import Theme


class ProgressPresenter:
    """Spinner-based progress helper bound to a console."""

    def __init__(self, console: Console, layout=None, theme_map=None):
        self.console = console
        self.layout = layout
        self.theme_map = theme_map or Theme.progress_theme()

    @contextmanager
    def spinner(self, message: str, *, use_spinner: bool = True) -> Iterator[None]:
        """Render a progress indicator for TUI tasks; disable live redraws when stdout is chatty."""
        color = self.theme_map.get("spinner.color", "cyan")
        spinner_name = self.theme_map.get("spinner.name", "dots")
        text_style = self.theme_map.get("text.style", Theme.INFO)

        # Always show a status panel so users see the message even without a spinner
        if self.layout:
            self.layout.render_status(message, style_key="info.text", border_key="panel.border", clear=False)

        if not use_spinner:
            # Non-live mode to avoid interleaving with stdout prints
            yield
            return

        with self.console.status(f"[{color}]{message}[/{color}]", spinner=spinner_name, spinner_style=text_style):
            yield


__all__ = ["ProgressPresenter"]