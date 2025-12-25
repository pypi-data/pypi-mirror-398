"""
Layout management for the Agentic Workflow OS TUI.

This module provides consistent screen rendering with headers, bodies, and footers.
"""

from typing import Any
from contextlib import contextmanager
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.columns import Columns
from rich.align import Align
from rich.live import Live

from .theme import Theme


class LayoutManager:
    """Manages consistent screen layout rendering."""

    def __init__(self, console: Console = None, theme_map: Any = None):
        """Initialize the layout manager."""
        self.console = console or Console()
        self.theme_map = theme_map or Theme.get_color_map()

    def render_screen(
        self,
        body_content: Any,
        title: str = "Agentic Workflow OS",
        subtitle: str = "",
        footer_text: str = "Use arrow keys to navigate • Enter to select • Ctrl+C to cancel",
        clear: bool = False,
    ) -> None:
        """Render a complete screen with header, body, and footer.

        Args:
            body_content: The main content to render (Rich renderable)
            title: Main title for the header
            subtitle: Subtitle for the header
            footer_text: Text to display in the footer
            clear: Whether to clear the console before rendering
        """
        # Clear the console only when explicitly requested
        if clear:
            self.console.clear()

        # Create header
        header_text = Text(title, style=self.theme_map.get("header", Theme.HEADER))
        if subtitle:
            header_text.append(f"\n{subtitle}", style=self.theme_map.get("subheader", Theme.SUBHEADER))

        header_panel = Panel.fit(
            Align.center(header_text),
            border_style=self.theme_map.get("panel.border", Theme.BORDER),
            title="🎯",
            title_align="left"
        )

        footer_panel = None
        if footer_text:
            footer_panel = Panel.fit(
                Text(footer_text, style=self.theme_map.get("footer", Theme.FOOTER)),
                border_style=self.theme_map.get("panel.border", Theme.BORDER)
            )

        # Render components with tighter vertical spacing
        self.console.print(header_panel)

        if hasattr(body_content, '__rich_console__'):
            self.console.print(body_content)
        else:
            self.console.print(str(body_content))

        if footer_panel:
            self.console.print(footer_panel)

    def render_header_only(
        self,
        title: str = "Agentic Workflow OS",
        subtitle: str = "",
        clear: bool = True,
    ) -> None:
        """Render just the header (for screens that handle their own body)."""
        if clear:
            self.console.clear()

        header_text = Text(title, style=self.theme_map.get("header", Theme.HEADER))
        if subtitle:
            header_text.append(f"\n{subtitle}", style=self.theme_map.get("subheader", Theme.SUBHEADER))

        header_panel = Panel.fit(
            Align.center(header_text),
            border_style=self.theme_map.get("panel.border", Theme.BORDER),
            title="🎯",
            title_align="left"
        )

        self.console.print(header_panel)
        self.console.print()

    def render_body_only(self, content: Any) -> None:
        """Render just the body content (for screens with custom headers)."""
        if hasattr(content, '__rich_console__'):
            self.console.print(content)
        else:
            self.console.print(str(content))

    def render_footer_only(
        self,
        footer_text: str = "Use arrow keys to navigate • Enter to select • Ctrl+C to cancel"
    ) -> None:
        """Render just the footer."""
        footer_panel = Panel.fit(
            Text(footer_text, style=self.theme_map.get("footer", Theme.FOOTER)),
            border_style=self.theme_map.get("panel.border", Theme.BORDER)
        )
        self.console.print()
        self.console.print(footer_panel)

    def render_status(self, message: Any, *, style_key: str = "info.text", border_key: str = "panel.border", clear: bool = False) -> None:
        """Render a status/footer area to avoid panel stacking."""
        if clear:
            self.console.clear()

        if isinstance(message, Panel):
            panel = message
        else:
            text_style = self.theme_map.get(style_key, Theme.INFO)
            border_style = self.theme_map.get(border_key, self.theme_map.get("panel.border", Theme.BORDER))
            panel = Panel(Text(str(message), style=text_style), border_style=border_style, padding=(0, 1))

        self.console.print(panel)

    @contextmanager
    def live_status(self, message: Any = "", *, style_key: str = "info.text", border_key: str = "panel.border", refresh_per_second: int = 4):
        """Opt-in persistent status/footer using Live to reduce scrollback."""
        text_style = self.theme_map.get(style_key, Theme.INFO)
        border_style = self.theme_map.get(border_key, self.theme_map.get("panel.border", Theme.BORDER))
        panel = Panel(Text(str(message), style=text_style), border_style=border_style, padding=(0, 1))
        with Live(panel, console=self.console, refresh_per_second=refresh_per_second, transient=True) as live:
            yield live


__all__ = ["LayoutManager"]