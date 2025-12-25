"""
Base controller classes for TUI menu navigation.

This module contains base controller functionality shared across
different menu controller implementations.
"""

from abc import ABC, abstractmethod
from typing import Any

from rich.panel import Panel
from rich.text import Text
from ..ui import LayoutManager, InputHandler, Theme


class BaseController(ABC):
    """Base class for menu controllers."""

    def __init__(self, app):
        """Initialize the base controller with the TUI app instance."""
        self.app = app
        self.console = app.console
        self.layout = app.layout
        self.input_handler = app.input_handler
        self.theme = app.theme
        self.feedback = app.feedback

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the controller's main logic."""
        pass

    def display_context_header(self, title: str) -> None:
        """Display a persistent context header with project and agent info."""
        header_theme = self.theme.header_theme()
        # Get project name
        project_name = "No Project"
        if self.app.project_root:
            project_name = self.app.project_root.name

        # Get active agent
        active_agent = "No Active Agent"
        try:
            if project_name != "No Project":
                session_data = self.app.query_handlers.get_active_session(project_name)
                if session_data and session_data.get('agent_id'):
                    active_agent = session_data['agent_id']
        except Exception:
            pass

        # Create header content
        header_text = Text()
        header_text.append("Agentic OS", style=header_theme.get("title", Theme.SECONDARY))
        header_text.append(" :: ", style=header_theme.get("accent", Theme.DIM))
        header_text.append(f"[Project: {project_name}]", style=header_theme.get("title", Theme.PRIMARY))
        header_text.append(" ", style=header_theme.get("accent", Theme.DIM))
        header_text.append(f"[Agent: {active_agent}]", style=header_theme.get("subtitle", Theme.SUCCESS))
        header_text.append(" :: ", style=header_theme.get("accent", Theme.DIM))
        header_text.append(title, style=header_theme.get("accent", Theme.ACCENT))

        # Create and display header panel
        header_panel = Panel(
            header_text,
            border_style=header_theme.get("border", Theme.BORDER),
            padding=(0, 1)
        )

        # Render header without an extra footer to avoid repeated navigation hints
        self.console.print(header_panel)
        self.console.print()

    def handle_exit(self) -> None:
        """Handle clean application exit."""
        from rich.text import Text
        self.console.print(Text("Goodbye!", style=Theme.SUCCESS))
        import sys
        sys.exit(0)

    def handle_error(self, error: Exception, operation: str) -> None:
        """Handle controller errors consistently."""
        self.feedback.error(f"Failed to {operation}: {error}")

    def handle_success(self, message: str) -> None:
        """Handle controller success consistently."""
        self.feedback.success(message)


__all__ = ["BaseController"]