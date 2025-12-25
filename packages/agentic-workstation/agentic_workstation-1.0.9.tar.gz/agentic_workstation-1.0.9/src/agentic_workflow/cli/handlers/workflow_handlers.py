"""
Workflow command handlers for Agentic Workflow CLI.
Focus: Advanced workflow manipulation (Stages, Gates).
"""

import logging
from ...core.exceptions import CLIExecutionError, handle_error, validate_required
from ...session.stage_manager import set_stage
from ...session.gate_checker import GateChecker
from ..utils import display_action_result, display_success, display_error

logger = logging.getLogger(__name__)

class WorkflowHandlers:
    """Handlers for advanced workflow operations."""

    def __init__(self, config=None):
        """Initialize the WorkflowHandlers with optional config."""
        self.config = config
        from agentic_workflow.services import WorkflowService
        self.workflow_service = WorkflowService()

    # --- TUI-friendly helpers (data only, no display) ---
    def list_workflows_data(self) -> list:
        """Return workflow metadata for selection dialogs."""
        workflows = self.workflow_service.list_workflows()
        enriched = []
        for workflow in workflows:
            try:
                info = self.workflow_service.get_workflow_info(workflow["name"])
                description = info.get("description", "No description")
            except Exception:
                description = "No description"
            enriched.append({"name": workflow.get("name"), "description": description})
        return enriched

    def handle_set_stage(
        self,
        project: str,
        stage: str
    ) -> None:
        """Force set the workflow stage (Admin override)."""
        try:
            validate_required(project, "project", "set_stage")
            validate_required(stage, "stage", "set_stage")

            result = set_stage(project, stage)
            
            if result['success']:
                display_success(f"Stage changed: {result.get('previous', 'None')} → {result['current']}")
            else:
                display_error(f"Failed to set stage: {result['error']}")

        except Exception as e:
            handle_error(e, "stage setting", {"project": project, "stage": stage})

    def handle_gate_check(
        self,
        project: str
    ) -> None:
        """Manually trigger a gate check."""
        try:
            validate_required(project, "project", "gate_check")
            
            # Instantiate GateChecker
            gate_checker = GateChecker(self.config)
            
            # Check gate for project (agent_id=None for generic check)
            result = gate_checker.check_gate(project, None)
            
            if result.passed:
                display_success(f"Gate check passed for project '{project}'")
            else:
                # Display violations
                violation_messages = []
                for violation in result.violations:
                    message = violation.get('message', 'Unknown violation')
                    violation_messages.append(message)
                if violation_messages:
                    display_error(f"Gate check failed for project '{project}': {'; '.join(violation_messages)}")
                else:
                    display_error(f"Gate check failed for project '{project}': Unknown reasons")
                    
        except Exception as e:
            handle_error(e, "gate check", {"project": project})


__all__ = ["WorkflowHandlers"]