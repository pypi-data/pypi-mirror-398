"""
Workflow controllers for TUI.

This module contains controllers for workflow-related operations.
"""

from .base_controller import BaseController


class WorkflowStatusController(BaseController):
    """Controller for workflow status display."""

    def execute(self, *args, **kwargs) -> None:
        """Execute workflow status display."""
        self.feedback.info("Workflow Status")

        try:
            if not self.app.project_root:
                self.feedback.warning("Not in a project context.")
                return

            project_name = self.app.project_root.name
            status_data = self.app.project_handlers.get_project_status_data(project_name)

            from ..views import ProjectStatusView
            view = ProjectStatusView(console=self.console, theme_map=self.theme.get_color_map())
            view.render(status_data)

        except Exception as e:
            self.feedback.error(f"Failed to get workflow status: {e}")

        self.input_handler.wait_for_user()


__all__ = ["WorkflowStatusController"]
