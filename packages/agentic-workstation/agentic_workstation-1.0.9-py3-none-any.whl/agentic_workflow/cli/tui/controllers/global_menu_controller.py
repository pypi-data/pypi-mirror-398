"""
Global menu controller for TUI.

This module contains the controller for global context menu operations.
"""

from questionary import Choice

from .base_controller import BaseController
from ...ui_utils import get_agentic_ascii_art
from ..ui import InputResult, Theme


class GlobalMenuController(BaseController):
    """Controller for global context menu operations."""

    def execute(self, *args, **kwargs) -> str:
        """Execute the global menu and return the selected action."""
        # Create menu content; layout will clear
        ascii_art = get_agentic_ascii_art()

        from rich.text import Text

        # Style the ASCII art
        styled_ascii_art = Text(ascii_art.strip(), style=self.theme.get_color_map().get("ascii_art", "cyan"))

        # Use layout manager to render
        self.layout.render_screen(
            styled_ascii_art,
            title="Agentic Workflow OS - Global Mode",
            subtitle="Project Management & Creation",
            footer_text="",
            clear=False
        )

        # Menu options
        choice = self.input_handler.get_selection(
            choices=[
                Choice(title="Create New Project", value="create"),
                Choice(title="List Existing Projects", value="list"),
                Choice(title="Manage Existing Project", value="manage"),
                Choice(title="System Information", value="info")
            ],
            message="Select an option:"
        )

        return choice

    def execute_create_project(self) -> bool:
        """Execute project creation wizard.
        
        Returns:
            True if project was created, False otherwise
        """
        return self.app.project_wizard_controller.execute()

    def execute_list_projects(self) -> None:
        """Execute project listing."""
        self.app._list_projects()

    def execute_manage_project(self) -> None:
        """Execute project management menu."""
        self.app.project_management_controller.execute()

    def execute_system_info(self) -> None:
        """Execute system information display."""
        self.app.system_info_controller.execute()

    def run_menu(self) -> None:
        """Run the complete global menu loop."""
        while True:
            result = self.execute()

            if result == InputResult.EXIT:
                self.handle_exit()
                break
            elif result == "create":
                if self.execute_create_project():
                    # Project was created successfully, exit the TUI
                    self.handle_exit()
                    break
            elif result == "list":
                self.execute_list_projects()
            elif result == "manage":
                self.execute_manage_project()
            elif result == "info":
                self.execute_system_info()
            # Continue the loop for any other case


__all__ = ["GlobalMenuController"]