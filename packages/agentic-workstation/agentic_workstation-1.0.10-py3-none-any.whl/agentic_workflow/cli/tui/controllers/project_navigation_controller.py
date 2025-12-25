"""
Navigation controllers for TUI.

This module contains controllers for navigation operations.
"""

from pathlib import Path
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .base_controller import BaseController


class ProjectNavigationController(BaseController):
    """Controller for project navigation display."""

    def execute(self, *args, **kwargs) -> None:
        """Execute project navigation display."""
        if not self.app.project_root:
            self.feedback.error("Not in a project directory.")
            self.input_handler.wait_for_user()
            return

        summary_panel = self._build_summary_panel()
        dir_panel = self._build_directory_panel()
        tips_panel = self._build_tips_panel()

        self.console.print(Group(summary_panel, dir_panel, tips_panel))
        self.input_handler.wait_for_user()

    def _build_summary_panel(self) -> Panel:
        """Compact project summary panel."""
        body = Text()
        body.append(f"Project: {self.app.project_root.name}\n", style=self.theme.get_color_map().get("bold", "bold"))
        body.append(f"Location: {self.app.project_root}")
        return Panel(body, title="Project Navigation", padding=(0, 1))

    def _build_directory_panel(self) -> Panel:
        """Compact directory overview table using handler-provided inventory."""
        inventory = self.app.query_handlers.get_project_inventory(self.app.project_root)
        entries = inventory.get("entries", [])

        table = Table(show_header=True, header_style=self.theme.get_color_map().get("table.header", "bold"), expand=True, box=None, pad_edge=False)
        table.add_column("Entry", style=self.theme.get_color_map().get("primary", "cyan"), no_wrap=True)
        table.add_column("Items", style=self.theme.get_color_map().get("accent", "magenta"), width=8, no_wrap=True)
        table.add_column("Type", style=self.theme.get_color_map().get("body", "white"), no_wrap=True)

        if not entries:
            table.add_row("(empty)", "-", "-")
        else:
            for entry in entries:
                name = entry.get("name", "?")
                count = str(entry.get("count", 0)) if entry.get("type") == "dir" else "-"
                entry_type = "dir" if entry.get("type") == "dir" else "file"
                table.add_row(name, count, entry_type)

        return Panel(table, title="Project Root", padding=(0, 1))

    def _build_tips_panel(self) -> Panel:
        """Helpful navigation tips."""
        tips = Text()
        tips.append("Use your file explorer or terminal to browse.\n", style=self.theme.get_color_map().get("bold", "bold"))
        tips.append("Tip: run `ls` or `tree` from the project root to inspect structure.")
        return Panel(tips, padding=(0, 1))

    def _count_entries(self, dir_path: Path) -> int:
        """Count directory entries (files and subdirectories)."""
        if not dir_path.exists():
            return 0
        return len(list(dir_path.rglob("*")))


__all__ = ["ProjectNavigationController"]