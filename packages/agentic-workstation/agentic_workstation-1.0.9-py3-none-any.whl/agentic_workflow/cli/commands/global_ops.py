"""
Global Operations Commands
Focus: Bootstrap and System Config (Init, Config, Workflows).
"""
import click
from ..handlers.session_handlers import SessionHandlers
from ..handlers.global_handlers import GlobalHandlers
from ..utils import display_error

session_handlers = SessionHandlers()
global_handlers = GlobalHandlers()

@click.command()
@click.argument('project')
@click.option('--workflow', '-w', default='planning', help='Workflow type (default: planning)')
@click.option('--description', '-d', help='Short description of the project')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing project')
def init(project: str, workflow: str, description: str, force: bool):
    """Initialize a new Agentic Project."""
    try:
        # Init belongs to SessionHandlers because it starts the lifecycle
        session_handlers.handle_init(
            project=project,
            workflow=workflow,
            description=description,
            force=force
        )
    except Exception as e:
        display_error(f"Initialization failed: {e}")

@click.command(name='workflows')
def list_workflows():
    """List available workflow definitions."""
    try:
        global_handlers.handle_list_workflows()
    except Exception as e:
        display_error(f"Failed to list workflows: {e}")

@click.command()
@click.option('--edit', '-e', is_flag=True, help='Open config in default editor')
def config(edit: bool):
    """View or edit global configuration."""
    try:
        global_handlers.handle_config(edit=edit)
    except Exception as e:
        display_error(f"Config operation failed: {e}")


__all__ = ["init", "list_workflows", "config"]