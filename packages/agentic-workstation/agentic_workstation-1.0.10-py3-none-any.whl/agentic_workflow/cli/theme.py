"""
Theme definitions for the Agentic Workflow OS CLI & TUI.

This module provides semantic color and style constants for consistent UI theming.
"""

from typing import Dict


class Theme:
    """Semantic theme constants for consistent UI styling."""

    # Primary colors
    PRIMARY = "bold cyan"
    SECONDARY = "bold blue"
    ACCENT = "bold yellow"

    # Status colors
    SUCCESS = "bold green"
    ERROR = "bold red"
    WARNING = "bold yellow"
    INFO = "bold blue"

    # Text styles
    HEADER = "bold white"
    SUBHEADER = "bold cyan"
    BODY = "white"
    DIM = "dim"
    BOLD = "bold"

    # Prompt styles
    PROMPT = "bold cyan"

    # UI elements
    BORDER = "blue"
    PANEL_BORDER = "cyan"
    TABLE_HEADER = "bold cyan"
    TABLE_ROW = "white"
    TABLE_TITLE = "bold blue"
    TABLE_BORDER = "blue"

    # Text semantics
    WARNING_TEXT = "yellow"
    INFO_TEXT = "cyan"
    ERROR_TEXT = "bold red"

    # Borders
    ERROR_BORDER = "red"
    WARNING_BORDER = "yellow"
    INFO_BORDER = BORDER

    # Syntax highlighting theme name
    SYNTAX_THEME = "monokai"

    # Special elements
    ASCII_ART = "bold cyan"
    FOOTER = "dim cyan"
    HINT = "dim white"

    # Dashboard semantic tokens
    DASHBOARD = {
        "project.border": "blue",
        "project.title": "bold blue",
        "project.key": "cyan",
        "session.border": "green",
        "session.title": "bold green",
        "session.key": "green",
        "activity.border": "magenta",
        "activity.title": "bold magenta",
        "activity.header": "bold magenta",
        "text.value": "yellow",
        "text.dim": "dim",
    }

    # Feedback semantic tokens
    FEEDBACK = {
        "success.text": SUCCESS,
        "success.border": BORDER,
        "error.text": ERROR,
        "error.border": "red",
        "info.text": INFO,
        "info.border": BORDER,
        "warning.text": WARNING,
        "warning.border": "yellow",
    }

    # Progress semantic tokens
    PROGRESS = {
        "spinner.color": "cyan",
        "spinner.name": "dots",
        "text.style": INFO,
    }

    # Header/context bar tokens
    HEADER_BAR = {
        "border": BORDER,
        "title": PRIMARY,
        "subtitle": SECONDARY,
        "accent": ACCENT,
    }

    # CLI-specific semantic tokens
    CLI = {
        # Display message tokens
        "display.success.icon": "✓",
        "display.success.color": "green",
        "display.error.icon": "✗",
        "display.error.color": "red",
        "display.warning.icon": "⚠",
        "display.warning.color": "yellow",
        "display.info.icon": "ℹ",
        "display.info.color": "blue",

        # Panel styling
        "panel.success.border": "green",
        "panel.error.border": "red",
        "panel.warning.border": "yellow",
        "panel.info.border": "blue",

        # Progress indicators
        "progress.spinner.color": "cyan",
        "progress.text.color": "cyan",

        # Input styling
        "input.prompt.color": "bold cyan",
        "input.hint.color": "dim white",
        "input.cancel.color": "red",

        # Table styling
        "table.header.color": "bold cyan",
        "table.border.color": "blue",
        "table.title.color": "bold blue",

        # Status panel styling
        "status.panel.border": "blue",
        "status.key.color": "cyan",
        "status.value.color": "magenta",

        # Project summary styling
        "summary.panel.border": "green",
        "summary.title.color": "bold green",
        "summary.workflow.color": "yellow",
        "summary.location.color": "white",
        "summary.directories.color": "white",
        "summary.steps.color": "white",

        # Panel and table styling
        "panel.title.color": "bold blue",
        "table.header": "bold cyan",
        "table.body": "white",

        # Help panel styling
        "help.command.color": "green",
        "help.description.color": "white",
    }

    @classmethod
    def get_rich_style(cls, name: str) -> str:
        """Get a rich style by name."""
        return getattr(cls, name.upper(), "white")

    @classmethod
    def get_color_map(cls) -> Dict[str, str]:
        """Get a mapping of semantic names to rich styles."""
        base_map = {
            "primary": cls.PRIMARY,
            "secondary": cls.SECONDARY,
            "accent": cls.ACCENT,
            "success": cls.SUCCESS,
            "error": cls.ERROR,
            "warning": cls.WARNING,
            "info": cls.INFO,
            "warning.text": cls.WARNING_TEXT,
            "info.text": cls.INFO_TEXT,
            "error.text": cls.ERROR_TEXT,
            "header": cls.HEADER,
            "subheader": cls.SUBHEADER,
            "body": cls.BODY,
            "dim": cls.DIM,
            "bold": cls.BOLD,
            "prompt": cls.PROMPT,
            "ascii_art": cls.ASCII_ART,
            "footer": cls.FOOTER,
            "hint": cls.HINT,
            "table.title": cls.TABLE_TITLE,
            "table.border": cls.TABLE_BORDER,
            "error.border": cls.ERROR_BORDER,
            "warning.border": cls.WARNING_BORDER,
            "info.border": cls.INFO_BORDER,
            "panel.border": cls.PANEL_BORDER,
            "syntax.theme": cls.SYNTAX_THEME,
        }

        # Add CLI theme tokens
        cli_map = {k.replace("display.", "").replace("cli.", ""): v for k, v in cls.CLI.items()}
        base_map.update(cli_map)

        return base_map

    @classmethod
    def dashboard_theme(cls) -> Dict[str, str]:
        """Return dashboard theme tokens."""
        return cls.DASHBOARD.copy()

    @classmethod
    def feedback_theme(cls) -> Dict[str, str]:
        """Return feedback theme tokens."""
        return cls.FEEDBACK.copy()

    @classmethod
    def progress_theme(cls) -> Dict[str, str]:
        """Return progress theme tokens."""
        return cls.PROGRESS.copy()

    @classmethod
    def header_theme(cls) -> Dict[str, str]:
        """Return header/context bar tokens."""
        return cls.HEADER_BAR.copy()
    
    @classmethod
    def cli_theme(cls) -> Dict[str, str]:
        """Return CLI-specific theme tokens."""
        return cls.CLI.copy()
    
__all__ = ["Theme"]