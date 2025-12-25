#!/usr/bin/env python3
"""UI utility functions for Agentic Workflow CLI."""
import sys
from typing import Any, Dict, List, NoReturn, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import structlog
from contextlib import contextmanager
import json
import yaml
import shutil
from pathlib import Path
import questionary
from questionary import Choice

console = Console()

__all__ = [
    "setup_logging",
    "format_output",
    "confirm_action",
    "show_progress",
    "display_error",
    "exit_with_error",
    "display_success",
    "display_warning",
    "display_info",
    "display_status_panel",
    "display_help_panel",
    "display_action_result",
    "display_project_summary",
    "shorten_path",
    "format_file_list",
    "get_agentic_ascii_art",
    "get_terminal_width",
    "styled_text_input",
    "styled_select",
    "styled_confirm",
]


def setup_logging(verbose: bool = False, log_level: str = "INFO") -> None:
    """Setup structured logging."""
    import logging
    from structlog import WriteLoggerFactory
    from structlog.processors import JSONRenderer

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if verbose:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.processors.KeyValueRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=WriteLoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def format_output(data: Any, format_type: str = "table", title: Optional[str] = None) -> None:
    """Format data for output in various formats."""
    try:
        if format_type == "json":
            console.print_json(json.dumps(data, indent=2, default=str))
        elif format_type == "yaml":
            console.print(yaml.dump(data, default_flow_style=False))
        elif format_type == "table":
            if isinstance(data, list) and data:
                table = Table(title=title)
                # Get headers from first item, with validation
                if isinstance(data[0], dict) and data[0]:
                    headers = list(data[0].keys())
                else:
                    headers = ["Value"]
                
                for header in headers:
                    table.add_column(header, style="cyan")

                for item in data:
                    if isinstance(item, dict):
                        row = [str(item.get(h, "")) for h in headers]
                    else:
                        row = [str(item)]
                    table.add_row(*row)
                console.print(table)
            elif isinstance(data, dict):
                table = Table(title=title)
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="green")
                for key, value in data.items():
                    table.add_row(key, str(value))
                console.print(table)
            else:
                console.print(data)
        else:
            console.print(data)
    except Exception as e:
        display_error(f"Failed to format output: {e}")
        console.print(data)  # Fallback to raw output


def confirm_action(message: str, default: bool = False) -> bool:
    """Get user confirmation for an action."""
    return click.confirm(message, default=default)


@contextmanager
def show_progress(message: str):
    """Show a progress indicator as a context manager."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn(f"[bold green]{message}"),
        console=console,
    )
    with progress:
        task = progress.add_task("", total=None)
        try:
            yield
        finally:
            progress.update(task, completed=100)


def display_error(message: str) -> None:
    """Display an error message."""
    if not message or not isinstance(message, str):
        message = "An unknown error occurred"
    console.print(f"[red]Error:[/red] {message}")


def exit_with_error(message: str, exit_code: int = 1) -> NoReturn:
    """Display an error message and exit the program."""
    display_error(message)
    sys.exit(exit_code)


def display_success(message: str) -> None:
    """Display a success message."""
    if not message or not isinstance(message, str):
        message = "Operation completed successfully"
    console.print(f"[green]✓[/green] {message}")


def display_warning(message: str) -> None:
    """Display a warning message."""
    if not message or not isinstance(message, str):
        message = "Warning"
    console.print(f"[yellow]⚠[/yellow] {message}")


def display_info(message: str) -> None:
    """Display an info message."""
    if not message or not isinstance(message, str):
        return  # Don't display empty info messages
    console.print(f"[blue]ℹ[/blue] {message}")


def get_terminal_width() -> int:
    """Get the current terminal width, with fallback."""
    try:
        return shutil.get_terminal_size().columns
    except (OSError, AttributeError):
        return 80  # Default fallback width


def styled_text_input(message: str, default: str = "", validate: Optional[callable] = None) -> Optional[str]:
    """Styled text input with better UX and exit handling.
    
    Args:
        message: The prompt message
        default: Default value
        validate: Optional validation function
        
    Returns:
        User input string, or None if cancelled
    """
    try:
        # Create a styled prompt with instructions
        styled_message = f"[bold cyan]{message}[/bold cyan]"
        if default:
            styled_message += f" [dim](default: {default})[/dim]"
        styled_message += "\n[dim]Press Ctrl+C to cancel[/dim]"
        
        result = questionary.text(
            styled_message,
            default=default,
            validate=validate
        ).unsafe_ask()
        
        return result
    except KeyboardInterrupt:
        # Re-raise KeyboardInterrupt so it can be caught by the main loop
        raise


def styled_select(choices: List[Choice], message: str = "Select an option:") -> Optional[str]:
    """Styled select with better UX and consistent exit handling.
    
    Args:
        choices: List of Choice objects
        message: The prompt message
        
    Returns:
        Selected value, or None if cancelled
    """
    # Add exit option if not present
    has_exit = any(choice.value in ['exit', 'cancel', 'back'] for choice in choices)
    if not has_exit:
        choices = choices + [Choice(title="[red]Cancel/Exit[/red]", value="cancel")]
    
    styled_message = f"[bold cyan]{message}[/bold cyan]\n[dim]Use arrow keys to navigate, Enter to select, Ctrl+C to cancel[/dim]"
    
    try:
        result = questionary.select(
            styled_message,
            choices=choices,
            use_shortcuts=False,  # Disable shortcuts to avoid confusion
            pointer="▶ "
        ).unsafe_ask()
        
        if result in ['exit', 'cancel', 'back']:
            display_info("Cancelled.")
            return None
            
        return result
    except KeyboardInterrupt:
        # Re-raise KeyboardInterrupt so it can be caught by the main loop
        raise
    except Exception as e:
        display_error(f"Input error: {e}")
        return None


def styled_confirm(message: str, default: bool = False) -> bool:
    """Styled confirmation prompt with better UX.
    
    Args:
        message: The confirmation message
        default: Default value
        
    Returns:
        True/False, False if cancelled
    """
    try:
        styled_message = f"[bold yellow]{message}[/bold yellow]"
        if default:
            styled_message += " [dim](Y/n)[/dim]"
        else:
            styled_message += " [dim](y/N)[/dim]"
        styled_message += "\n[dim]Press Enter for default, or type 'y'/'n'[/dim]"
        
        return questionary.confirm(styled_message, default=default).unsafe_ask()
    except KeyboardInterrupt:
        # Re-raise KeyboardInterrupt so it can be caught by the main loop
        raise


def display_status_panel(project_name: str, status_data: Dict[str, Any]) -> None:
    """Display project status in a structured table panel."""
    table = Table(title=f"[bold blue]Project Status: {project_name}[/bold blue]")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta", max_width=get_terminal_width() // 2)

    for key, value in status_data.items():
        formatted_key = key.replace('_', ' ').title()
        table.add_row(formatted_key, str(value))

    console.print(table)


def display_help_panel(title: str, commands: List[Dict[str, str]]) -> None:
    """Display help in a rich panel with formatted commands."""
    if not commands:
        return

    # Create table for commands
    table = Table(box=None, pad_edge=False)
    table.add_column("Command", style="green", no_wrap=True, max_width=get_terminal_width() // 4)
    table.add_column("Description", style="white", overflow="fold", max_width=get_terminal_width() // 2)

    for cmd in commands:
        table.add_row(cmd.get('command', ''), cmd.get('description', ''))

    panel = Panel(
        table,
        title=f"[bold blue]{title}[/bold blue]",
        border_style="blue",
        padding=(1, 2),
        width=min(get_terminal_width() - 4, 100)  # Responsive width with max
    )
    console.print(panel)


def display_action_result(action: str, success: bool, details: Optional[List[str]] = None, icon: Optional[str] = None) -> None:
    """Standardized action completion display with optional details."""
    if not action or not isinstance(action, str):
        action = "Unknown action"
    
    if icon is None:
        icon = "✓" if success else "✗"
    color = "green" if success else "red"

    console.print(f"[{color}]{icon}[/{color}] {action}")
    if details and isinstance(details, list):
        for detail in details:
            if detail and isinstance(detail, str):
                console.print(f"[{color}]  └─[/{color}] {detail}")


def display_project_summary(project_name: str, workflow: str, directories: List[str], next_steps: List[str]) -> None:
    """Display project creation summary in a structured panel."""
    # Input validation and defaults
    project_name = project_name or "Unknown Project"
    workflow = workflow or "Default Workflow"
    directories = directories or []
    next_steps = next_steps or []
    
    # Create directories list
    dir_content = "\n".join(f"  • {d}" for d in directories) if directories else "  • No directories created"

    # Create next steps list
    steps_content = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(next_steps)) if next_steps else "  • No next steps defined"

    content = f"""[bold white]Workflow:[/bold white] {workflow}
[bold white]Location:[/bold white] projects/{project_name}

[bold white]Created directories:[/bold white]
{dir_content}

[bold white]Next steps:[/bold white]
{steps_content}"""

    panel = Panel(
        content,
        title="[bold green]🎉 Project Created[/bold green]",
        border_style="green",
        padding=(1, 2),
        width=min(get_terminal_width() - 4, 120)
    )
    console.print(panel)


def shorten_path(path: str, max_length: int = 60) -> str:
    """Shorten paths for display readability."""
    
    if not path or not isinstance(path, str):
        return str(path) if path else ""
    
    try:
        path_obj = Path(path)
        path_str = str(path)

        if len(path_str) <= max_length:
            return path_str

        # Try relative to project root
        try:
            from ..core.config_service import ConfigurationService
            config_service = ConfigurationService()
            project_root = config_service.find_project_root()
            if project_root:
                rel_path = path_obj.relative_to(project_root)
                rel_str = str(rel_path)
                if len(rel_str) < len(path_str):
                    return rel_str
        except (ImportError, AttributeError, ValueError):
            pass  # Config service not available or path not relative

        # Try relative to current directory
        try:
            rel_path = path_obj.relative_to(Path.cwd())
            rel_str = str(rel_path)
            if len(rel_str) < len(path_str):
                return f"./{rel_str}"
        except ValueError:
            pass  # Path not relative to cwd

        # Fallback: truncate with ellipsis
        if max_length > 3:
            return f"...{path_str[-max_length+3:]}"
        else:
            return path_str[:max_length]
            
    except Exception:
        # If anything fails, return the original path truncated
        return str(path)[:max_length] if len(str(path)) > max_length else str(path)


def format_file_list(files: List[str], prefix: str = "✓ Generated:", max_line_length: Optional[int] = None) -> List[str]:
    """Format a list of files with proper line breaking.
    
    Args:
        files: List of file paths to format
        prefix: Prefix string to add before each file
        max_line_length: Maximum line length before breaking. If None, uses terminal width.
    
    Returns:
        List of formatted strings ready for display
    """
    # Input validation
    if not files or not isinstance(files, list):
        return []
    
    if max_line_length is None:
        max_line_length = get_terminal_width() - 10  # Leave some margin
    
    if not isinstance(prefix, str):
        prefix = "✓"
    
    formatted_lines = []
    
    for file_path in files:
        # Validate each file path
        if not file_path or not isinstance(file_path, str):
            continue
            
        short_path = shorten_path(file_path)
        line = f"{prefix} {short_path}"

        if len(line) <= max_line_length:
            formatted_lines.append(line)
        else:
            # Break long lines
            formatted_lines.append(f"{prefix}")
            formatted_lines.append(f"  {short_path}")
    
    return formatted_lines


def get_agentic_ascii_art() -> str:
    """Return ASCII art for AGENTIC branding."""
    return """
 █████╗  ██████╗ ███████╗███╗   ██╗████████╗██╗ ██████╗
██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██║██╔════╝
███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ██║██║
██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ██║██║
██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ██║╚██████╗
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝ ╚═════╝
"""