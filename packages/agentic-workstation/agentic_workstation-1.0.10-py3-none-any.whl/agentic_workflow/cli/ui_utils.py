#!/usr/bin/env python3
"""UI utility functions for Agentic Workflow CLI."""
import sys
from typing import Any, Dict, List, NoReturn, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import structlog
from contextlib import contextmanager
import json
import yaml
from .display import display_error, display_info


__all__ = [
    "setup_logging",
    "format_output",
    "show_progress",
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


def format_output(data: Any, format_type: str = "table", title: Optional[str] = None, console: Optional[Console] = None) -> None:
    """Format data for output in various formats."""
    if console is None:
        console = Console()
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
        display_error(f"Failed to format output: {e}", console)
        console.print(data)  # Fallback to raw output


@contextmanager
def show_progress(message: str, console: Optional[Console] = None):
    """Show a progress indicator as a context manager."""
    if console is None:
        console = Console()
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

