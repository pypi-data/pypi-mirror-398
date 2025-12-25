"""
Dashboard view for TUI project cockpit.

This module contains the dashboard view that displays project status
and session context in a cockpit-style interface.
"""

from typing import Dict, Any, List
from datetime import datetime
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns

from .base_views import BaseView

class DashboardView(BaseView):
    """Dashboard view for project cockpit interface."""

    def __init__(self, console, theme_map: dict):
        super().__init__(console, theme_map=theme_map)
        self.theme_map = theme_map

    def render(self, 
               project_name: str, 
               session_context: Dict[str, Any], 
               status: Dict[str, Any], 
               recent_activity: List[Dict[str, Any]] = None) -> None:
        """Render the dashboard with project info, session context, status, and recent activity."""
        
        # 1. Data Preparation (Normalization)
        project_data = {
            "Project": project_name,
            "Workflow": status.get('workflow') or 'Not set',
            "Description": status.get('description') or 'No description available'
        }

        session_data = {
            "Active Agent": session_context.get('active_agent') or 'No active agent',
            "Current Stage": status.get('stage') or 'Not started',
            "Last Action": session_context.get('last_action') or 'No recent activity'
        }

        # 2. Component Rendering (compact columns + stacked activity)
        top_columns = Columns(
            [
                self._create_info_panel("Project Information", project_data, "project"),
                self._create_info_panel("Session Status", session_data, "session")
            ],
            expand=True,
            equal=True,
            padding=(0, 1)
        )

        activity_panel = self._create_activity_panel(recent_activity or [])

        self.console.print(top_columns)
        self.console.print(activity_panel)

    def _create_info_panel(self, title: str, data: Dict[str, str], theme_prefix: str) -> Panel:
        """
        Generic helper to create Key-Value information panels.
        
        Args:
            title: Panel title text
            data: Dictionary of Label->Value pairs
            theme_prefix: Key prefix to look up in self.THEME (e.g., 'project')
        """
        content = Text()
        
        for key, value in data.items():
            # Apply semantic styling
            key_style = self.theme_map.get(f"{theme_prefix}.key", "bold")
            val_style = self.theme_map.get("text.value", "default")
            
            # Special handling for description/long text to be dim
            if key in ["Description", "Last Action"]:
                val_style = self.theme_map.get("text.dim", "dim")

            content.append(f"{key}: ", style=key_style)
            content.append(f"{value}\n", style=val_style)

        return Panel(
            content,
            title=title,
            border_style=self.theme_map.get(f'{theme_prefix}.border', 'blue'),
            padding=(0, 1)
        )

    def _create_activity_panel(self, activity: List[Dict[str, Any]]) -> Panel:
        """Create the recent activity panel with robust formatting."""
        table = Table(
            show_header=True, 
            header_style=self.theme_map.get("activity.header", "bold"),
            expand=True  # Ensure table fills the panel
        )
        
        # Define columns with explicit ratios/widths for responsiveness
        table.add_column("Time", style="dim", width=16, no_wrap=True)
        table.add_column("Type", width=10)
        table.add_column("Summary", style="white", ratio=1, overflow="fold") # Fold long text

        if not activity:
            # Handle empty state gracefully
            table.add_row("No recent activity", "-", "-")
        else:
            for item in activity:
                table.add_row(
                    self._format_timestamp(item.get('timestamp')),
                    item.get('type', 'unknown').title(),
                    item.get('summary', 'No summary')
                )

        return Panel(
            table,
            title="Recent Activity",
            border_style=self.theme_map.get("activity.border", "blue"),
            padding=(0, 1)
        )

    def _format_timestamp(self, ts_str: str) -> str:
        """Robustly parse and format timestamps."""
        if not ts_str:
            return ""
        try:
            # Parse ISO format (e.g., 2025-12-15T14:30:00.123456)
            dt = datetime.fromisoformat(ts_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            # Fallback for unexpected formats
            return ts_str[:16]


__all__ = ["DashboardView"]