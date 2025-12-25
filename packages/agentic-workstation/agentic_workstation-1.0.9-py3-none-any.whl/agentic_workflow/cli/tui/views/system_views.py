"""
System information view components.

This module contains view classes for displaying system status
and configuration information.
"""

import sys
from pathlib import Path
from typing import Dict, Any
from rich.table import Table

from .base_views import BaseView


class SystemInfoView(BaseView):
    """View for displaying system information."""

    def render(self, data: Dict[str, Any]) -> None:
        """Render system information in a table format."""
        # System info table
        info_table = Table()
        info_table.add_column("Property", style=self.theme_map.get("primary", "cyan"), no_wrap=True)
        info_table.add_column("Value", style=self.theme_map.get("accent", "yellow"))

        info_table.add_row("Version", data.get('version', 'unknown'))
        info_table.add_row("Python Version", data.get('python_version', f"{sys.version.split()[0]}"))
        info_table.add_row("Platform", data.get('platform', sys.platform))
        info_table.add_row("Projects", str(data.get('project_count', 0)))
        info_table.add_row("Workflow Types", str(data.get('workflow_count', 0)))
        info_table.add_row("Working Directory", str(data.get('working_directory', Path.cwd())))

        self.console.print(info_table)


__all__ = ["SystemInfoView"]