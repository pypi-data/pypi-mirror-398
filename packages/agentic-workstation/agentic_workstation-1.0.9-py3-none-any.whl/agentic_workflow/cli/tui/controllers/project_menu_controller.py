"""
Project menu controller for TUI.

This module contains the controller for project context menu operations.
"""

from questionary import Choice

from .base_controller import BaseController
from ...ui_utils import get_agentic_ascii_art
from ..ui import InputResult
from ..views import DashboardView


class ProjectMenuController(BaseController):
    """Controller for project context menu operations."""

    def execute(self, *args, **kwargs) -> str:
        """Execute the project menu and return the selected action."""
        # Display AGENTIC ASCII art centered with tighter spacing
        self.console.print(get_agentic_ascii_art(), style=self.theme.ASCII_ART, justify="left")

        project_name = self.app.project_root.name if self.app.project_root else "Unknown"

        # Fetch latest status and session data via handlers
        try:
            dashboard_data = self.app.query_handlers.get_dashboard_data(project_name)
            status_result = dashboard_data.get('status', {})
            session_context = dashboard_data.get('session_context', {'active_agent': None, 'last_action': 'No recent activity'})
            recent_activity = dashboard_data.get('recent_activity', [])
        except Exception:
            status_result = {}
            session_context = {'active_agent': None, 'last_action': 'No recent activity'}
            recent_activity = []

        # Render dashboard with fresh data
        dashboard = DashboardView(console=self.console, theme_map=self.theme.dashboard_theme())
        dashboard.render(
            project_name=project_name,
            session_context=session_context,
            status=status_result,
            recent_activity=recent_activity
        )

        # Menu options
        choice = self.input_handler.get_selection(
            choices=[
                Choice(title="View Workflow Status", value="status"),
                Choice(title="Agent Operations", value="agents"),
                Choice(title="List Pending Handoffs", value="list-pending"),
                Choice(title="List Active Blockers", value="list-blockers"),
                Choice(title="Artifact Management", value="artifacts"),
                Choice(title="Project Navigation", value="navigate")
            ],
            message="Select an option:"
        )

        return choice

    def execute_workflow_status(self) -> None:
        """Execute workflow status display."""
        self.app.workflow_status_controller.execute()

    def execute_agent_operations(self) -> None:
        """Execute agent operations menu."""
        self.app.agent_operations_controller.run_menu()

    def execute_list_pending(self) -> None:
        """Execute list pending handoffs."""
        self.display_context_header("Pending Handoffs")
        
        project_name = self.app.project_root.name if self.app.project_root else "Unknown"
        try:
            self.app.query_handlers.handle_list_pending(project=project_name)
        except Exception as e:
            self.app.error_view.display_error_modal(str(e))
        
        self.input_handler.wait_for_user()

    def execute_list_blockers(self) -> None:
        """Execute list active blockers."""
        self.display_context_header("Active Blockers")
        
        project_name = self.app.project_root.name if self.app.project_root else "Unknown"
        try:
            self.app.query_handlers.handle_list_blockers(project=project_name)
        except Exception as e:
            self.app.error_view.display_error_modal(str(e))
        
        self.input_handler.wait_for_user()

    def execute_artifact_management(self) -> None:
        """Execute artifact management."""
        self.app.artifact_management_controller.execute()

    def execute_project_navigation(self) -> None:
        """Execute project navigation display."""
        # Assuming app has project_navigation_controller initialized
        if hasattr(self.app, 'project_navigation_controller'):
            self.app.project_navigation_controller.execute()
        else:
            self.feedback.error("Navigation controller not initialized.")
            self.input_handler.wait_for_user()

    def run_menu(self) -> str:
        """Run the complete project menu loop and return context change."""
        choice = self.execute()

        if choice is None or choice == InputResult.EXIT:
            return "global"  # Exit project context on cancel/ctrl+C
        elif choice == "status":
            self.execute_workflow_status()
        elif choice == "agents":
            self.execute_agent_operations()
        elif choice == "list-pending":
            self.execute_list_pending()
        elif choice == "list-blockers":
            self.execute_list_blockers()
        elif choice == "artifacts":
            self.execute_artifact_management()
        elif choice == "navigate":
            self.execute_project_navigation()

        return "project"  # Stay in project context


__all__ = ["ProjectMenuController"]