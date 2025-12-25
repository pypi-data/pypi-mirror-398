#!/usr/bin/env python3
"""
Main CLI entry point for Agentic Workflow OS.
Role: Context Router. Directs commands to specific operations modules.
"""
import sys
import click
from rich.console import Console
from rich_click import RichGroup

from agentic_workflow import __version__
from agentic_workflow.core.config_service import ConfigurationService
from agentic_workflow.core.schema import RuntimeConfig
from agentic_workflow.core.exceptions import AgenticWorkflowError
from agentic_workflow.cli.utils import display_error, setup_logging

# Import New Command Modules (Phase 2)
from agentic_workflow.cli.commands import global_ops
from agentic_workflow.cli.commands import project_ops
from agentic_workflow.cli.commands import active_session

console = Console()

class ContextAwareGroup(RichGroup):
    """
    Smart Command Router.
    Dynamically exposes commands based on whether the user is inside a project.
    """

    def list_commands(self, ctx: click.Context) -> list[str]:
        """Return available commands based on current context."""
        config = self._get_config(ctx)

        if config.is_project_context:
            # Inside a project: Active Workflow Focus
            return ['status', 'activate', 'handoff', 'decision', 'end', 'feedback', 'blocker', 'iteration', 'assumption', 'list-pending', 'list-blockers']
        else:
            # Global Root: System & Management Focus
            return ['init', 'list', 'delete', 'config', 'workflows']

    def get_command(self, ctx: click.Context, cmd_name: str):
        """Map command string to actual function implementation."""
        config = self._get_config(ctx)

        # 1. Project Context Routing
        if config.is_project_context:
            mapping = {
                'status': project_ops.status,
                'activate': active_session.activate,
                'handoff': active_session.handoff,
                'decision': active_session.decision,
                'end': active_session.end_session,  # Alias 'end' -> 'end_session'
                'check-handoff': active_session.check_handoff,
                'feedback': active_session.feedback,
                'blocker': active_session.blocker,
                'iteration': active_session.iteration,
                'assumption': active_session.assumption,
                'list-pending': project_ops.list_pending,
                'list-blockers': project_ops.list_blockers,
            }
            return mapping.get(cmd_name)

        # 2. Global Context Routing
        else:
            mapping = {
                'init': global_ops.init,
                'list': project_ops.list_projects,    # Alias 'list' -> 'list_projects'
                'delete': project_ops.delete_project, # Alias 'delete' -> 'delete_project'
                'config': global_ops.config,
                'workflows': global_ops.list_workflows # Alias 'workflows' -> 'list_workflows'
            }
            return mapping.get(cmd_name)

    def _get_config(self, ctx: click.Context):
        """Helper to ensure config is loaded only once."""
        if not ctx.obj or 'config' not in ctx.obj:
            service = ConfigurationService()
            # Determine context silently to avoid noise during tab-completion
            config = service.load_config(verbose=False)
            if not ctx.obj: ctx.obj = {}
            ctx.obj['config'] = config
        return ctx.obj['config']


def show_version(ctx, param, value):
    """Callback to display styled version."""
    if value:
        from rich.panel import Panel
        console.print(Panel(f"[bold cyan]Agentic Workflow OS v{__version__}[/]", border_style="blue"))
        ctx.exit()


@click.group(cls=ContextAwareGroup, invoke_without_command=True)
@click.option('--version', is_flag=True, callback=show_version, expose_value=False, help='Show version')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--force', '-f', is_flag=True, help='Force operations (bypass safety checks)')
@click.pass_context
def cli(ctx: click.Context, verbose: bool, force: bool):
    """
    Agentic Workflow OS — Context-Aware Orchestration Engine.
    
    The available commands change based on your directory.
    Run 'agentic init' to start a new project.
    """
    ctx.ensure_object(dict)
    
    # 1. Load Config (Hydration)
    service = ConfigurationService()
    # Force flag overrides runtime strictness
    config = service.load_config(verbose=verbose, force=force)
    
    # 2. Setup Logging
    setup_logging(verbose=verbose, log_level=config.system.log_level.value)
    
    # 3. Store in Context
    ctx.obj['config'] = config
    ctx.obj['console'] = console

    # 4. TUI Fallback (If no subcommand)
    if ctx.invoked_subcommand is None:
        run_tui_mode(config)


def run_tui_mode(config: RuntimeConfig):
    """Launch the interactive Text User Interface."""
    try:
        from .tui.main import TUIApp
        app = TUIApp(config)
        app.run()
    except Exception as e:
        # Fallback error handling if TUI crashes hard
        console.print_exception()
        sys.exit(1)


# Static Registration (Required for click help generation to work mostly correctly)
# We register them, but ContextAwareGroup hides/shows them dynamically.
cli.add_command(global_ops.init)
cli.add_command(global_ops.config)
cli.add_command(active_session.activate)
cli.add_command(project_ops.status)

if __name__ == "__main__":
    try:
        cli()
    except AgenticWorkflowError as e:
        display_error(str(e))
        sys.exit(1)
    except Exception as e:
        display_error(f"Unexpected system error: {e}")
        sys.exit(1)


__all__ = ["cli"]