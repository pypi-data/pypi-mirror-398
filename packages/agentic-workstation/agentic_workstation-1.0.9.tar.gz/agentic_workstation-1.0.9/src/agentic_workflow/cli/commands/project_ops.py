"""
Project Operations Commands
Focus: Management and Status (List, Delete, Status).
"""
import click
from ..handlers.project_handlers import ProjectHandlers
from ..handlers.query_handlers import QueryHandlers
from ..utils import display_error

# Initialize Handlers
project_handlers = ProjectHandlers()
query_handlers = QueryHandlers()

@click.command(name='list')
@click.argument('name', required=False)
@click.option('--format', '-f', 'output_format', default='table', type=click.Choice(['table', 'json', 'yaml']))
def list_projects(name: str, output_format: str):
    """List all projects or show details for one."""
    try:
        project_handlers.handle_list(name=name, output_format=output_format)
    except Exception as e:
        display_error(f"List failed: {e}")

@click.command(name='delete')
@click.argument('project')
@click.option('--force', is_flag=True, help='Force deletion without confirmation')
def delete_project(project: str, force: bool):
    """Permanently delete a project."""
    if not force:
        if not click.confirm(f"Are you sure you want to delete '{project}'?"):
            return
            
    try:
        project_handlers.handle_delete(project=project, force=force)
    except Exception as e:
        display_error(f"Deletion failed: {e}")

@click.command(name='list-pending')
@click.pass_context
def list_pending(ctx: click.Context):
    """List pending handoffs for the current project."""
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    
    try:
        query_handlers.handle_list_pending(project=project_name)
    except Exception as e:
        display_error(f"List pending failed: {e}")

@click.command(name='list-blockers')
@click.pass_context
def list_blockers(ctx: click.Context):
    """List active blockers for the current project."""
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    
    try:
        query_handlers.handle_list_blockers(project=project_name)
    except Exception as e:
        display_error(f"List blockers failed: {e}")

@click.command()
@click.pass_context
def status(ctx: click.Context):
    """Show status (Context-Aware)."""
    # If inside a project, shows workflow state.
    # If outside, could show system health or error.
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    
    try:
        query_handlers.handle_status(project=project_name)
    except Exception as e:
        display_error(f"Status check failed: {e}")


__all__ = ["list_projects", "delete_project", "list_pending", "list_blockers", "status"]