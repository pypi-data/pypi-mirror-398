"""
Display controllers for TUI.

This module contains controllers for displaying information.
"""

import sys
from pathlib import Path

from .base_controller import BaseController
from agentic_workflow import __version__


class SystemInfoController(BaseController):
    """Controller for system information display."""

    def execute(self, *args, **kwargs) -> None:
        """Execute system information display."""
        self.feedback.info("System Information")

        # Get real system information
        project_count = 0
        try:
            projects_data = self.app.project_handlers.list_projects_data()
            project_count = projects_data.get('count', 0)
        except Exception:
            project_count = 0

        # Count workflows
        workflow_count = 0
        try:
            workflows = self.app.workflow_handlers.list_workflows_data()
            workflow_count = len(workflows)
        except Exception:
            workflow_count = 0

        # Prepare data for the view
        system_data = {
            'version': __version__,
            'python_version': f"{sys.version.split()[0]}",
            'platform': sys.platform,
            'project_count': project_count,
            'workflow_count': workflow_count,
            'working_directory': str(Path.cwd())
        }

        # Use the new view to render system information
        from ..views import SystemInfoView
        view = SystemInfoView(console=self.console, theme_map=self.theme.get_color_map())
        view.render(system_data)

        self.input_handler.wait_for_user()


__all__ = ["SystemInfoController"]