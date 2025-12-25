"""
Interactive Setup Wizard for Agentic Workflow OS.
Triggers on first run to populate ~/.config/agentic/config.yaml.
"""
import os
import sys
from pathlib import Path
from typing import Optional
import yaml
from questionary import Choice
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Import the schema to ensure we save valid data
from agentic_workflow.core.schema import SystemConfig
from agentic_workflow.core.exceptions import ConfigError

# Import UI utilities
from .branding import display_context_header
from agentic_workflow.cli.theme import Theme
from .ui import InputHandler, InputResult, FeedbackPresenter

console: Optional[Console] = None

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "agentic"


def run_setup_wizard(
    console_override: Optional[Console] = None,
    input_handler: Optional[InputHandler] = None,
    feedback: Optional[FeedbackPresenter] = None,
    layout=None,
) -> None:
    """Launch the first-run configuration wizard.

    When invoked from the TUI, pass the shared `console`, `input_handler`, and `feedback`
    to avoid creating a new module-level Console. When invoked from CLI/bootstrap without
    a TUI context, the wizard will fall back to a local Console instance.
    """
    global console
    console = console_override or console or Console()
    theme = Theme
    input_handler = input_handler or InputHandler(console, feedback)
    feedback = feedback or FeedbackPresenter(console, theme_map=theme.feedback_theme())
    # For testing: auto-setup with defaults
    if os.environ.get('AGENTIC_AUTO_SETUP'):
        config_data = {
            "default_workspace": "~/AgenticProjects",
            "editor_command": "code",
            "tui_enabled": True,
            "check_updates": True,
            "log_level": "INFO"
        }
        _save_config(config_data, feedback)
        _ensure_workspace_exists(Path(config_data['default_workspace']).expanduser(), feedback)
        feedback.success("Auto-setup complete!")
        return

    console.clear()

    # Display AGENTIC header
    display_context_header("Global", console, theme_map=theme.get_color_map())
    console.print(Text(f"Press Ctrl+C or choose Cancel / Exit at any prompt to abort setup.\n", style=theme.DIM))

    # 1. Welcome UI
    welcome = Text("Welcome to Agentic Workflow OS\n", style=theme.HEADER)
    welcome.append("Let's set up your environment.", style=theme.DIM)
    console.print(Panel(welcome, border_style=theme.BORDER, title="First-Run Setup"))

    try:
        # 2. Workspace Selection
        default_ws = "~/AgenticProjects"
        # Use explicit Choice objects instead of dictionaries
        # This prevents internal mismatch errors in questionary validation
        choices = [
            Choice(title=f"Default ({default_ws})", value=default_ws),
            Choice(title="Current Directory", value=str(Path.cwd())),
            Choice(title="Custom Path...", value="custom")
        ]

        # Validate default is in choices (Check against Choice.value)
        valid_values = [c.value for c in choices]
        
        if default_ws not in valid_values:
            default_ws = None 

        ws_choice = input_handler.get_selection(
            choices=choices,
            message="Where should we store your projects?"
        )

        if ws_choice == InputResult.EXIT or ws_choice is None:
            feedback.warning("Setup cancelled.")
            return

        if ws_choice == "custom":
            workspace_path = input_handler.get_text("Path:", default=default_ws)
            if workspace_path == InputResult.EXIT or workspace_path is None:
                feedback.warning("Setup cancelled.")
                return
        else:
            workspace_path = ws_choice

        # 3. Editor Selection
        editor_choice = input_handler.get_selection(
            choices=[
                Choice(title="VS Code (code)", value="code"),
                Choice(title="Vim (vim)", value="vim"),
                Choice(title="Nano (nano)", value="nano"),
                Choice(title="Custom...", value="custom")
            ],
            message="Which editor do you use?"
        )

        if editor_choice == InputResult.EXIT or editor_choice is None:
            feedback.warning("Setup cancelled.")
            return

        if editor_choice == "custom":
            editor_cmd = input_handler.get_text("Enter command (e.g., 'subl', 'notepad'):")
            if editor_cmd == InputResult.EXIT or editor_cmd is None:
                feedback.warning("Setup cancelled.")
                return
        else:
            editor_cmd = editor_choice

        # 4. Save & Exit
        config_data = {
            "default_workspace": workspace_path,
            "editor_command": editor_cmd,
            "tui_enabled": True,
            "check_updates": True,
            "log_level": "INFO"
        }

        console.print()
        console.print("Configuration Summary:", style=theme.BOLD)
        console.print(f"  • Projects Location: {config_data['default_workspace']}", style=theme.INFO_TEXT)
        console.print(f"  • Default Editor:    {config_data['editor_command']}", style=theme.INFO_TEXT)
        console.print()

        confirm = input_handler.get_confirmation("Save configuration and continue?", default=True)
        if confirm == InputResult.EXIT:
            feedback.warning("Setup cancelled.")
            return

        if confirm:
            _save_config(config_data, feedback)
            _ensure_workspace_exists(Path(workspace_path), feedback)

            feedback.success("Setup complete!")
            console.print("Launching application...\n")
            # Logic flow returns to main.py here to continue execution
        else:
            feedback.warning("Setup cancelled. Exiting.")
            sys.exit(0)

    except KeyboardInterrupt:
        feedback.warning("Setup interrupted.")
        sys.exit(1)
    except Exception as e:
        feedback.error(f"Setup failed: {e}")
        sys.exit(1)


def _save_config(data: dict, feedback: FeedbackPresenter) -> None:
    """Serialize config to YAML with validation."""
    try:
        # Validate against schema before saving
        valid_config = SystemConfig(**data)
        
        # Ensure config dir exists
        DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config_file = DEFAULT_CONFIG_DIR / "config.yaml"
        
        # Convert to dict and ensure paths are strings
        config_dict = valid_config.model_dump()
        config_dict['default_workspace'] = str(config_dict['default_workspace'])
        config_dict['log_level'] = config_dict['log_level'].value if hasattr(config_dict['log_level'], 'value') else config_dict['log_level']
        
        with open(config_file, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)
            
    except Exception as e:
        feedback.error(f"Error saving configuration: {e}")
        raise ConfigError(f"Failed to save configuration: {e}")


def _ensure_workspace_exists(path: Path, feedback: FeedbackPresenter) -> None:
    """Create the workspace directory if it doesn't exist"""
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            feedback.info(f"Created workspace directory: {path}")
    except Exception as e:
        feedback.warning(f"Could not create workspace directory: {e}")


__all__ = ["run_setup_wizard"]