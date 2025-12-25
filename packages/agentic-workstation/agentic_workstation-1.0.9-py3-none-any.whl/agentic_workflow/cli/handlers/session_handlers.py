"""
Session command handlers for Agentic Workflow CLI.
Focus: Active lifecycle management (Init, Activate, End).
"""

from pathlib import Path
from typing import Optional, List
import logging

from agentic_workflow.core.exceptions import (
    ProjectNotFoundError, CLIExecutionError,
    handle_error, validate_required
)
from agentic_workflow.services import ProjectService, WorkflowService
from agentic_workflow.session.gate_checker import GateChecker
from ..utils import (
    display_success, display_project_summary, 
    display_action_result, display_info
)

logger = logging.getLogger(__name__)

class SessionHandlers:
    """Handlers for session lifecycle management."""

    def __init__(self, config=None):
        """Initialize the SessionHandlers with optional config."""
        self.config = config
        self.project_service = ProjectService(config)
        self.workflow_service = WorkflowService()

    def handle_init(
        self,
        project: str,
        workflow: Optional[str] = None,
        description: Optional[str] = None,
        force: bool = False
    ) -> None:
        """Handle project initialization (Starts the lifecycle)."""
        try:
            validate_required(project, "project", "init")
            workflow_type = workflow or 'planning'
            
            logger.info(f"Initializing project '{project}' with workflow '{workflow_type}'")

            # Initialize via Service Layer
            result = self.project_service.init_project(
                project_name=project,
                workflow_name=workflow_type,
                description=description,
                force=force
            )
            
            # UX: Determine first agent for "Next Steps" guidance
            first_agent = "A-01"
            try:
                manifest = self.workflow_service.get_workflow_manifest(workflow_type)
                pipeline = manifest.get('workflow', {}).get('pipeline', {}).get('order', [])
                if len(pipeline) > 1:
                    first_agent = pipeline[1]
            except Exception:
                pass

            next_steps = [
                f"cd \"{result.target_path}\"",
                "agentic status", 
                f"agentic activate {first_agent}"
            ]

            # Display Rich Summary using actual root inventory
            directories = self._summarize_root_entries(result.target_path)
            display_project_summary(project, workflow_type, directories, next_steps)
            display_success(f"Project '{project}' initialized successfully")

        except Exception as e:
            handle_error(e, "project initialization", {"project": project})

    def handle_activate(
        self,
        agent_id: str,
        project: Optional[str] = None
    ) -> None:
        """Handle agent activation."""
        try:
            validate_required(agent_id, "agent_id", "activate")
            
            # Auto-detect project if not provided
            if not project:
                if not self.config or not self.config.is_project_context:
                    # Fallback to CWD name if config isn't fully hydrated yet
                    project = Path.cwd().name
                else:
                    project = self.config.project.root_path.name

            logger.info(f"Activating agent '{agent_id}' in project '{project}'")

            if not self.project_service.project_exists(project):
                raise ProjectNotFoundError(f"Project '{project}' not found")

            # Check gates before activation
            gate_checker = GateChecker(self.config)
            gate_result = gate_checker.check_gate(project, agent_id)
            if not gate_result.passed:
                violation_messages = []
                for violation in gate_result.violations:
                    message = violation.get('message', 'Unknown violation')
                    violation_messages.append(message)
                if violation_messages:
                    raise CLIExecutionError(f"Cannot activate agent '{agent_id}': {'; '.join(violation_messages)}")
                else:
                    raise CLIExecutionError(f"Cannot activate agent '{agent_id}': Gate check failed")

            # Execute Activation
            result = self.project_service.activate_agent(project, agent_id)

            # Build status display
            status_lines = []
            if result.get('stage_advanced'):
                status_lines.append(f"Stage advanced: {result.get('previous_stage')} → {result.get('current_stage')}")
            status_lines.extend([
                f"Role: {result.get('role', 'Unknown')}", 
                f"Session ID: {result.get('session_id', 'N/A')}"
            ])
            
            display_action_result(
                f"Agent '{agent_id}' activated",
                True,
                status_lines
            )

        except Exception as e:
            handle_error(e, "agent activation", {"project": project, "agent_id": agent_id})

    def handle_end(
        self,
        project: Optional[str] = None
    ) -> None:
        """Handle session end."""
        try:
            if not project:
                project = Path.cwd().name

            logger.info(f"Ending session for project '{project}'")

            if not self.project_service.project_exists(project):
                raise ProjectNotFoundError(f"Project '{project}' not found")

            result = self.project_service.end_session(project)

            display_action_result(
                f"Session ended for project '{project}'",
                True,
                [f"Archived agents: {result.get('archived_agents', 0)}", 
                 f"Final status: {result.get('status', 'completed')}"]
            )

        except Exception as e:
            handle_error(e, "session end", {"project": project})

    def _summarize_root_entries(self, root_path: Path) -> List[str]:
        """Summarize top-level project entries for creation output."""
        entries: List[str] = []
        if not root_path or not Path(root_path).exists():
            return entries

        for item in Path(root_path).iterdir():
            if item.name.startswith('.'):
                continue
            if item.is_dir():
                count = sum(1 for _ in item.rglob('*'))
                entries.append(f"{item.name}/ ({count} items)")
            else:
                entries.append(f"{item.name} (file)")

        entries.sort()
        return entries


__all__ = ["SessionHandlers"]