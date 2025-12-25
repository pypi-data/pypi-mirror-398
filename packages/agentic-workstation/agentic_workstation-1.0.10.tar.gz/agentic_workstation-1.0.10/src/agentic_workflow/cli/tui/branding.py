"""
Branding and ASCII art for Agentic Workflow OS TUI.

This module contains branding assets and ASCII art used throughout the TUI.
"""

from typing import Optional
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

from agentic_workflow.cli.theme import Theme


def get_agentic_ascii_art_colored(
    console: Optional[Console] = None,
    theme_map: Optional[dict] = None
) -> Text:
    """Return colored ASCII art for AGENTIC branding.

    Args:
        console: Rich console instance (optional)
        theme_map: Theme mapping (optional, uses Theme if not provided)

    Returns:
        Rich Text object with colored ASCII art
    """
    theme_map = theme_map or Theme.get_color_map()

    # Enhanced ASCII art with better proportions
    art_lines = [
        " █████╗   ██████╗  ███████╗ ███╗   ██╗ ████████╗ ██╗  ██████╗ ",
        "██╔══██╗ ██╔════╝  ██╔════╝ ████╗  ██║ ╚══██╔══╝ ██║ ██╔════╝ ",
        "███████║ ██║  ███╗ █████╗   ██╔██╗ ██║    ██║    ██║ ██║      ",
        "██╔══██║ ██║   ██║ ██╔══╝   ██║╚██╗██║    ██║    ██║ ██║      ",
        "██║  ██║ ╚██████╔╝ ███████╗ ██║ ╚████║    ██║    ██║ ╚██████╗ ",
        "╚═╝  ╚═╝  ╚═════╝  ╚══════╝ ╚═╝  ╚═══╝    ╚═╝    ╚═╝  ╚═════╝ "
    ]

    # Create a Text object with default styling
    text = Text()
    primary_color = theme_map.get("primary", "bold cyan")
    accent_color = theme_map.get("accent", "bold yellow")
    colors = [primary_color] * (len(art_lines) - 1) + [accent_color]

    for i, line in enumerate(art_lines):
        text.append(line + "\n", style=colors[i])

    return text


def display_context_header(
    context: Optional[str] = None,
    console: Optional[Console] = None,
    theme_map: Optional[dict] = None
) -> None:
    """Display AGENTIC header with optional context-specific hints.

    Args:
        context: Optional context ("Global" or "Project") for mode-specific hints
        console: Rich console instance (optional, creates new if not provided)
        theme_map: Theme mapping (optional, uses Theme if not provided)
    """
    console = console or Console()
    theme_map = theme_map or Theme.get_color_map()

    ascii_art = get_agentic_ascii_art_colored(console, theme_map)

    # Main title on border
    title = "Agentic Workflow OS Professional AI Development Orchestration"

    # Create panel with title on border
    panel = Panel(
        ascii_art,
        title=title,
        title_align="center",
        border_style=theme_map.get("primary", "cyan"),
        padding=(1, 2)
    )

    console.print(panel)

    # Add context hint below if provided
    if context:
        if context.lower() == "global":
            hint = "Global Configuration & Project Management"
        elif context.lower() == "project":
            hint = "Active Project Workflow & Agent Operations"
        else:
            hint = context

        console.print(f"[{theme_map.get('subheader', 'cyan')}]{hint.center(len(title))}[/{theme_map.get('subheader', 'cyan')}]")

    console.print()  # Add some spacing


__all__ = [
    "get_agentic_ascii_art_colored",
    "display_context_header",
]