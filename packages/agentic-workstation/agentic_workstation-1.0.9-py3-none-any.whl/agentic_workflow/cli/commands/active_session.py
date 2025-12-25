"""
Active Session Commands
Focus: The 'Doing' commands (Activate, Handoff, Decision, End).
"""
import click
from rich_click import RichCommand
from ..handlers.session_handlers import SessionHandlers
from ..handlers.entry_handlers import EntryHandlers
from ..utils import display_error
from agentic_workflow.services import LedgerService

# Initialize Handlers
session_handlers = SessionHandlers()
entry_handlers = EntryHandlers()

@click.command(cls=RichCommand)
@click.argument('agent_id')
@click.pass_context
def activate(ctx: click.Context, agent_id: str):
    """Activate an agent session."""
    # Context-aware config injection (if available)
    config = ctx.obj.get('config') if ctx.obj else None
    
    try:
        # Pass config implicitly if needed, but handler mainly uses kwargs
        if config:
            session_handlers.config = config
            
        session_handlers.handle_activate(agent_id=agent_id)
    except Exception as e:
        display_error(f"Activation failed: {e}")

@click.command(cls=RichCommand)
@click.option('--to', required=True, help='Target agent ID')
@click.option('--from', 'from_agent', help='Source agent ID (Auto-detected if active)')
@click.option('--artifacts', help='Comma-separated artifact names')
@click.option('--notes', help='Handoff notes')
@click.pass_context
def handoff(ctx: click.Context, to: str, from_agent: str, artifacts: str, notes: str):
    """Record a handoff to another agent."""
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    
    # Auto-detect 'from_agent' if not supplied
    if not from_agent and project_name:
        ledger_service = LedgerService()
        active_session = ledger_service.get_active_session(project_name)
        if active_session:
            from_agent = active_session.get('agent_id')
        else:
            raise click.UsageError(
                f"No active agent session found for project '{project_name}'. "
                "Please specify --from or activate an agent first."
            )

    try:
        entry_handlers.handle_handoff(
            project=project_name, # Passed explicitly from context
            from_agent=from_agent,
            to_agent=to,
            artifacts=artifacts,
            notes=notes
        )
    except Exception as e:
        display_error(f"Handoff failed: {e}")

@click.command(cls=RichCommand, help="Record a key project decision.")
@click.option('--title', required=True, help='Decision title')
@click.option('--rationale', required=True, help='Reasoning behind the decision')
@click.option('--agent', help='Agent ID making the decision')
@click.pass_context
def decision(ctx: click.Context, title: str, rationale: str, agent: str):
    """Record a key project decision with title, rationale, and optional agent ID."""
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None

    try:
        entry_handlers.handle_decision(
            project=project_name,
            title=title,
            rationale=rationale,
            agent=agent
        )
    except Exception as e:
        display_error(f"Decision recording failed: {e}")

@click.command(cls=RichCommand, name='end', help="Archive the current session and reset state.")
@click.pass_context
def end_session(ctx: click.Context):
    """End the current active session."""
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    
    try:
        session_handlers.handle_end(project=project_name)
    except Exception as e:
        display_error(f"Failed to end session: {e}")

@click.command(cls=RichCommand, name='check-handoff')
@click.argument('agent_id')
@click.pass_context
def check_handoff(ctx: click.Context, agent_id: str):
    """Check if a handoff exists for an agent."""
    from ..handlers.query_handlers import QueryHandlers
    query_handlers = QueryHandlers()
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    
    try:
        query_handlers.handle_check_handoff(project=project_name, agent_id=agent_id)
    except Exception as e:
        display_error(f"Handoff check failed: {e}")

@click.command(cls=RichCommand)
@click.option('--target', required=True, help='Feedback target')
@click.option('--severity', required=True, type=click.Choice(['low', 'medium', 'high', 'critical']), help='Severity level')
@click.option('--summary', required=True, help='Feedback summary')
@click.pass_context
def feedback(ctx: click.Context, target: str, severity: str, summary: str):
    """Record feedback for an agent or artifact."""
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    
    try:
        entry_handlers.handle_feedback(
            project=project_name,
            target=target,
            severity=severity,
            summary=summary
        )
    except Exception as e:
        display_error(f"Feedback recording failed: {e}")

@click.command(cls=RichCommand)
@click.option('--title', required=True, help='Blocker title')
@click.option('--description', required=True, help='Blocker description')
@click.option('--blocked-agents', help='Comma-separated list of blocked agent IDs')
@click.pass_context
def blocker(ctx: click.Context, title: str, description: str, blocked_agents: str):
    """Record a blocker that prevents progress."""
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    
    # Parse blocked_agents if provided
    blocked_agents_list = None
    if blocked_agents:
        blocked_agents_list = [agent.strip() for agent in blocked_agents.split(',')]
    
    try:
        entry_handlers.handle_blocker(
            project=project_name,
            title=title,
            description=description,
            blocked_agents=blocked_agents_list
        )
    except Exception as e:
        display_error(f"Blocker recording failed: {e}")

@click.command(cls=RichCommand)
@click.option('--trigger', required=True, help='What triggered the iteration')
@click.option('--impacted-agents', required=True, help='Comma-separated list of impacted agent IDs')
@click.option('--description', required=True, help='Iteration description')
@click.option('--version-bump', type=click.Choice(['patch', 'minor', 'major']), default='patch', help='Version bump type')
@click.pass_context
def iteration(ctx: click.Context, trigger: str, impacted_agents: str, description: str, version_bump: str):
    """Record an iteration in the development process."""
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    
    # Parse impacted_agents
    impacted_agents_list = [agent.strip() for agent in impacted_agents.split(',')]
    
    try:
        entry_handlers.handle_iteration(
            project=project_name,
            trigger=trigger,
            impacted_agents=impacted_agents_list,
            description=description,
            version_bump=version_bump
        )
    except Exception as e:
        display_error(f"Iteration recording failed: {e}")

@click.command(cls=RichCommand)
@click.option('--assumption', required=True, help='The assumption text')
@click.option('--rationale', required=True, help='Rationale for the assumption')
@click.pass_context
def assumption(ctx: click.Context, assumption: str, rationale: str):
    """Record an assumption that may affect the project."""
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    
    try:
        entry_handlers.handle_assumption(
            project=project_name,
            assumption=assumption,
            rationale=rationale
        )
    except Exception as e:
        display_error(f"Assumption recording failed: {e}")


__all__ = [
    "activate",
    "handoff", 
    "decision",
    "end_session",
    "check_handoff",
    "feedback",
    "blocker",
    "iteration",
    "assumption"
]