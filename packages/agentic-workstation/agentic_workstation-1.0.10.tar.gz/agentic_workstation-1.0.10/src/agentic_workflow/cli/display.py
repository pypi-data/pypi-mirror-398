#!/usr/bin/env python3
"""Display utility functions for Agentic Workflow CLI."""
import sys
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .theme import Theme
from .formatting import get_terminal_width


def display_error(message: str, console: Console) -> None:
    """Display an error message in a themed panel."""
    if not message or not isinstance(message, str):
        message = "An unknown error occurred"
    color_map = Theme.get_color_map()
    panel = Panel(
        f"[{color_map['error.color']}]{message}[/{color_map['error.color']}]",
        title=f"[{color_map['error.color']}]Error[/{color_map['error.color']}]",
        border_style=color_map['panel.error.border'],
        padding=(0, 1),
        width=min(get_terminal_width() - 4, 100)
    )
    console.print(panel)


def exit_with_error(message: str, console: Console, exit_code: int = 1) -> None:
    """Display an error message and exit the program."""
    display_error(message, console)
    sys.exit(exit_code)


def display_success(message: str, console: Console) -> None:
    """Display a success message."""
    if not message or not isinstance(message, str):
        message = "Operation completed successfully"
    color_map = Theme.get_color_map()
    console.print(f"[{color_map['success.color']}]✓[/{color_map['success.color']}] {message}")


def display_warning(message: str, console: Console) -> None:
    """Display a warning message."""
    if not message or not isinstance(message, str):
        message = "Warning"
    color_map = Theme.get_color_map()
    console.print(f"[{color_map['warning.color']}]⚠[/{color_map['warning.color']}] {message}")


def display_info(message: str, console: Console) -> None:
    """Display an info message."""
    if not message or not isinstance(message, str):
        return  # Don't display empty info messages
    color_map = Theme.get_color_map()
    console.print(f"[{color_map['info.color']}]ℹ[/{color_map['info.color']}] {message}")


def display_project_summary(project_name: str, workflow: str, directories: List[str], next_steps: List[str], console: Console) -> None:
    """Display project creation summary in a structured panel."""
    color_map = Theme.get_color_map()
    # Input validation and defaults
    project_name = project_name or "Unknown Project"
    workflow = workflow or "Default Workflow"
    directories = directories or []
    next_steps = next_steps or []
    
    # Create directories list
    dir_content = "\n".join(f"  • {d}" for d in directories) if directories else "  • No directories created"

    # Create next steps list
    steps_content = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(next_steps)) if next_steps else "  • No next steps defined"

    content = f"""[bold {color_map['summary.workflow.color']}]Workflow:[/bold {color_map['summary.workflow.color']}] {workflow}
[bold {color_map['summary.location.color']}]Location:[/bold {color_map['summary.location.color']}] projects/{project_name}

[bold {color_map['summary.directories.color']}]Created directories:[/bold {color_map['summary.directories.color']}]
{dir_content}

[bold {color_map['summary.steps.color']}]Next steps:[/bold {color_map['summary.steps.color']}]
{steps_content}"""

    panel = Panel(
        content,
        title=f"[bold {color_map['summary.title.color']}]🎉 Project Created[/bold {color_map['summary.title.color']}]",
        border_style=color_map['summary.panel.border'],
        padding=(1, 2),
        width=min(get_terminal_width() - 4, 120)
    )
    console.print(panel)


def display_action_result(action: str, success: bool,  console: Console, details: Optional[List[str]] = None, icon: Optional[str] = None) -> None:
    """Standardized action completion display with optional details."""
    if not action or not isinstance(action, str):
        action = "Unknown action"
    
    color_map = Theme.get_color_map()
    if icon is None:
        icon = "✓" if success else "✗"
    color = color_map['success.color'] if success else color_map['error.color']

    console.print(f"[{color}]{icon}[/{color}] {action}")
    if details and isinstance(details, list):
        for detail in details:
            if detail and isinstance(detail, str):
                console.print(f"[{color}]  └─[/{color}] {detail}")


def display_help_panel(title: str, commands: List[Dict[str, str]], console: Console) -> None:
    """Display help in a rich panel with formatted commands."""
    if not commands:
        return

    color_map = Theme.get_color_map()
    # Create table for commands
    table = Table(box=None, pad_edge=False)
    table.add_column("Command", style=color_map['help.command.color'], no_wrap=True, max_width=get_terminal_width() // 4)
    table.add_column("Description", style=color_map['help.description.color'], overflow="fold", max_width=get_terminal_width() // 2)

    for cmd in commands:
        table.add_row(cmd.get('command', ''), cmd.get('description', ''))

    panel = Panel(
        table,
        title=f"[bold {color_map['panel.title.color']}] {title} [/bold {color_map['panel.title.color']}]",
        border_style=color_map['panel.border'],
        padding=(1, 2),
        width=min(get_terminal_width() - 4, 100)  # Responsive width with max
    )
    console.print(panel)

def display_status_panel(project_name: str, status_data: Dict[str, Any], console: Console) -> None:
    """Display project status in a structured table panel."""
    color_map = Theme.get_color_map()
    table = Table(title=f"[bold {color_map['panel.title.color']}]Project Status: {project_name}[/bold {color_map['panel.title.color']}]")
    table.add_column("Property", style=color_map['table.header'], no_wrap=True)
    table.add_column("Value", style=color_map['table.body'], max_width=get_terminal_width() // 2)

    for key, value in status_data.items():
        formatted_key = key.replace('_', ' ').title()
        table.add_row(formatted_key, str(value))

    console.print(table)


