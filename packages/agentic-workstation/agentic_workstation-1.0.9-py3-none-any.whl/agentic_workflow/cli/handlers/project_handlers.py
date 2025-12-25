"""
Project command handlers for Agentic Workflow CLI.
Focus: Static project management (List, Delete).
"""

from typing import Optional, Dict, Any
import logging

from ...core.exceptions import (
    ProjectError, ProjectNotFoundError, 
    handle_error, validate_required
)
from agentic_workflow.services import ProjectService
from ..utils import display_action_result, display_info, display_warning, shorten_path

logger = logging.getLogger(__name__)

class ProjectHandlers:
    """Handlers for static project management."""

    def __init__(self):
        """Initialize the ProjectHandlers with required services."""
        self.project_service = ProjectService()

    # --- TUI-friendly helpers (data only, no display) ---
    def list_projects_data(self) -> Dict[str, Any]:
        """Return raw project listing data without rendering."""
        return self.project_service.list_projects()

    def get_project_status_data(self, project_name: str) -> Dict[str, Any]:
        """Return raw project status data without rendering."""
        return self.project_service.get_project_status(project_name)

    def handle_list(
        self,
        name: Optional[str] = None,
        output_format: str = 'table'
    ) -> None:
        """Handle project listing command."""
        try:
            logger.info("Listing projects" if not name else f"Showing project '{name}'")

            if name:
                # Show specific project details
                result = self.project_service.get_project_status(name)
                if result['status'] == 'found':
                    if result.get('config'):
                        self._format_project_output(result['config'], output_format, f"Project: {name}")
                    else:
                        display_warning(f"Project '{name}' found but no configuration available")
                        display_info(f"Location: {shorten_path(result.get('path', 'unknown'))}")
                else:
                    raise ProjectNotFoundError(f"Project '{name}' not found")
            else:
                # List all projects
                result = self.project_service.list_projects()
                if result['count'] > 0:
                    self._format_projects_list(result['projects'], output_format)
                else:
                    display_info("No projects found")

        except Exception as e:
            handle_error(e, "project listing", {"project_name": name})

    def handle_delete(
        self,
        project: str,
        force: bool = False
    ) -> None:
        """Handle project deletion (Renamed from remove for consistency)."""
        try:
            validate_required(project, "project", "delete")
            logger.info(f"Deleting project '{project}'")

            # Check existence first
            if not self.project_service.project_exists(project):
                raise ProjectNotFoundError(f"Project '{project}' not found")

            # Execute deletion
            result = self.project_service.remove_project(project, force)

            display_action_result(
                action=f"Project '{project}' deleted successfully",
                success=True,
                details=[f"Location: {result.get('path', 'unknown')}"]
            )

        except Exception as e:
            handle_error(e, "project deletion", {"project": project})

    def _format_project_output(self, project_data: Dict[str, Any], output_format: str, title: str) -> None:
        """Format project data for output."""
        if output_format == 'json':
            import json
            display_info(json.dumps(project_data, indent=2))
        elif output_format == 'yaml':
            import yaml
            display_info(yaml.dump(project_data, default_flow_style=False))
        else:  # table
            display_info(f"\n{title}")
            display_info("=" * len(title))
            for key, value in project_data.items():
                if isinstance(value, dict):
                    display_info(f"{key}:")
                    for sub_key, sub_value in value.items():
                        display_info(f"  {sub_key}: {sub_value}")
                else:
                    display_info(f"{key}: {value}")
            display_info("")

    def _format_projects_list(self, projects: list, output_format: str) -> None:
        """Format projects list for output."""
        if output_format == 'json':
            import json
            display_info(json.dumps(projects, indent=2))
        elif output_format == 'yaml':
            import yaml
            display_info(yaml.dump(projects, default_flow_style=False))
        else:
            display_info("\nAvailable Projects")
            display_info("=" * 18)
            for project in projects:
                display_info(f"Name: {project['name']}")
                display_info(f"  Workflow: {project['workflow']}")
                display_info(f"  Description: {project['description']}")
                display_info("")


__all__ = ["ProjectHandlers"]