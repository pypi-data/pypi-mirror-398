"""
Project view components for displaying project-related data.

This module contains view classes for rendering project lists,
project status, and other project-related information.
"""

from typing import Dict, Any, List
from rich.table import Table

from .base_views import BaseView


class ProjectListView(BaseView):
    """View for displaying lists of projects."""

    def render(self, data: Dict[str, Any]) -> None:
        """Render project list in a table format."""
        projects = data.get('projects', [])

        if not projects:
            warning_style = self.theme_map.get("warning.text", "yellow")
            self.console.print(f"[{warning_style}]No projects found.[/{warning_style}]")
            return

        # Format projects in a nice table
        table = Table(
            title="Projects",
            title_style=self.theme_map.get("table.title", "bold blue"),
            border_style=self.theme_map.get("table.border", "blue"),
        )
        table.add_column("Project Name", style=self.theme_map.get("primary", "cyan"), no_wrap=True)
        table.add_column("Workflow", style=self.theme_map.get("success", "green"))
        table.add_column("Description", style=self.theme_map.get("accent", "yellow"))

        for project in projects:
            table.add_row(
                project['name'],
                project['workflow'],
                project['description'] or "(no description)"
            )

        self.console.print(table)


class ProjectStatusView(BaseView):
    """View for displaying individual project status."""

    def render(self, data: Dict[str, Any]) -> None:
        """Render project status in a table format."""
        config = data.get('config')

        if not config:
            warning_style = self.theme_map.get("warning.text", "yellow")
            info_style = self.theme_map.get("info.text", "cyan")
            location = data.get('path', 'unknown')
            self.console.print(f"[{warning_style}]⚠ Project found but no configuration available[/]")
            self.console.print(f"[{info_style}]ℹ Location: {location}[/{info_style}]")
            return

        # Format project status in a nice table
        table = Table(
            title="Project Status",
            title_style=self.theme_map.get("table.title", "bold blue"),
            border_style=self.theme_map.get("table.border", "blue"),
        )
        table.add_column("Property", style=self.theme_map.get("primary", "cyan"), no_wrap=True)
        table.add_column("Value", style=self.theme_map.get("accent", "yellow"))

        # Add basic project info
        table.add_row("Project Name", config.get('name', data.get('project_name', 'unknown')))
        table.add_row("Workflow", config.get('workflow', 'unknown'))
        table.add_row("Description", config.get('description', ''))
        table.add_row("Location", str(data.get('path', 'unknown')))

        # Add workflow status if available
        if 'workflow_status' in config:
            workflow_status = config['workflow_status']
            table.add_row("Current Stage", workflow_status.get('stage', 'unknown'))
            table.add_row("Active Agent", workflow_status.get('active_agent', 'none'))

        self.console.print(table)


class ProjectSummaryView(BaseView):
    """View for displaying project creation summaries."""

    def render(self, data: Dict[str, Any]) -> None:
        """Render project summary with directories and next steps."""
        project_name = data.get('project_name', 'unknown')
        workflow_type = data.get('workflow_type', 'unknown')
        directories = data.get('directories', [])
        next_steps = data.get('next_steps', [])

        # Header
        self.console.print(f"\n[bold green]Project '{project_name}' created successfully![/bold green]")
        self.console.print(f"[dim]Workflow: {workflow_type}[/dim]\n")

        # Directories section
        if directories:
            self.console.print("[bold cyan]Project Structure:[/bold cyan]")
            for directory in directories:
                self.console.print(f"  • {directory}/")
            self.console.print()

        # Next steps section
        if next_steps:
            self.console.print("[bold cyan]Next Steps:[/bold cyan]")
            for step in next_steps:
                self.console.print(f"  {step}")
            self.console.print()


__all__ = ["ProjectListView", "ProjectStatusView", "ProjectSummaryView"]