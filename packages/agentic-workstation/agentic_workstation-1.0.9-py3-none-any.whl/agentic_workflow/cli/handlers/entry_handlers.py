"""
Entry command handlers for Agentic Workflow CLI.

This module contains handlers for entry-related commands like handoff, decision, etc.
Extracted from the monolithic workflow.py for better maintainability.

Design Decision: Handlers accept keyword arguments directly instead of argparse.Namespace.
This allows the handlers to be used both from CLI (via Click) and programmatically (from services).
"""

from typing import Optional, List
import logging
from pathlib import Path

from agentic_workflow.core.exceptions import CLIExecutionError, handle_error, validate_required
from agentic_workflow.services import LedgerService
from ..utils import display_action_result, display_success

logger = logging.getLogger(__name__)


class EntryHandlers:
    """Handlers for entry-related CLI commands.
    
    All handler methods accept keyword arguments directly for clean integration
    with Click commands. No argparse.Namespace conversion required.
    """

    def __init__(self):
        """Initialize the EntryHandlers with required services."""
        self.ledger_service = LedgerService()

    def handle_handoff(
        self,
        project: str,
        from_agent: str,
        to_agent: str,
        artifacts: Optional[str] = None,
        notes: Optional[str] = None
    ) -> None:
        """
        Handle agent handoff command.

        Args:
            project: Project name (required)
            from_agent: Source agent ID (required)
            to_agent: Target agent ID (required)
            artifacts: Comma-separated artifact list
            notes: Handoff notes

        Raises:
            CLIExecutionError: If handoff fails
        """
        try:
            validate_required(project, "project", "handoff")
            validate_required(from_agent, "from_agent", "handoff")
            validate_required(to_agent, "to_agent", "handoff")

            artifact_list = None
            if artifacts:
                artifact_list = [art.strip() for art in artifacts.split(',')]

            # Validate handoff against workflow rules
            from agentic_workflow.validation.validate_ledger import validate_workflow_handoff
            workflow_errors = validate_workflow_handoff(project, from_agent, to_agent, artifact_list)
            if workflow_errors:
                error_msg = f"Workflow validation failed: {'; '.join(workflow_errors)}"
                raise CLIExecutionError(error_msg)

            logger.info(f"Recording handoff in project '{project}': {from_agent} -> {to_agent}")

            result = self.ledger_service.record_handoff(
                project_name=project,
                from_agent=from_agent,
                to_agent=to_agent,
                artifacts=artifact_list,
                notes=notes
            )

            display_action_result(
                action=f"Handoff recorded: {from_agent} -> {to_agent}",
                success=True,
                details=[f"Artifacts: {', '.join(artifact_list)}"] if artifact_list else None
            )

        except Exception as e:
            handle_error(e, "agent handoff", {
                "project": project,
                "from_agent": from_agent,
                "to_agent": to_agent
            })

    def handle_decision(
        self,
        project: Optional[str],
        title: str,
        rationale: str,
        agent: Optional[str] = None
    ) -> None:
        """
        Handle decision recording command.

        Args:
            project: Project name (optional, auto-detected in project context)
            title: Decision title (required)
            rationale: Decision rationale (required)
            agent: Agent ID (optional)

        Raises:
            CLIExecutionError: If decision recording fails
        """
        try:
            # Auto-detect project if not provided
            if not project:
                from agentic_workflow.core.config_service import ConfigurationService
                config_service = ConfigurationService()
                config = config_service.load_config()
                if not config.is_project_context:
                    raise CLIExecutionError("No project specified and not in project context")
                project = Path.cwd().name  # Use current directory name

            validate_required(title, "title", "decision")
            validate_required(rationale, "rationale", "decision")

            logger.info(f"Recording decision in project '{project}': {title}")

            result = self.ledger_service.record_decision(
                project_name=project,
                title=title,
                rationale=rationale,
                agent_id=agent
            )

            display_action_result(
                action=f"Decision recorded: {title}",
                success=True,
                details=[f"Agent: {agent}"] if agent else None
            )

        except Exception as e:
            handle_error(e, "decision recording", {"project": project, "title": title})

    def handle_feedback(
        self,
        project: str,
        target: str,
        severity: str,
        summary: str
    ) -> None:
        """
        Handle feedback recording command.

        Args:
            project: Project name (required)
            target: Feedback target (required)
            severity: Severity level (required)
            summary: Feedback summary (required)

        Raises:
            CLIExecutionError: If feedback recording fails
        """
        try:
            validate_required(project, "project", "feedback")
            validate_required(target, "target", "feedback")
            validate_required(severity, "severity", "feedback")
            validate_required(summary, "summary", "feedback")

            # Get active agent as reporter
            active_session = self.ledger_service.get_active_session(project)
            if not active_session:
                raise CLIExecutionError("No active agent session found. Please activate an agent first.")
            reporter = active_session.get('agent_id')

            # Record feedback
            result = self.ledger_service.record_feedback(
                project_name=project,
                reporter=reporter,
                target=target,
                severity=severity,
                summary=summary
            )
            display_success(f"Feedback recorded for {target} (ID: {result['entry_id']})")

        except Exception as e:
            handle_error(e, "feedback recording", {"project": project, "target": target})

    def handle_iteration(
        self,
        project: str,
        trigger: str,
        impacted_agents: List[str],
        description: str,
        version_bump: str = 'patch'
    ) -> None:
        """
        Handle iteration recording command.

        Args:
            project: Project name (required)
            trigger: Iteration trigger (required)
            impacted_agents: List of impacted agent IDs (required)
            description: Iteration description (required)
            version_bump: Version bump type (optional, default 'patch')

        Raises:
            CLIExecutionError: If iteration recording fails
        """
        try:
            validate_required(project, "project", "iteration")
            validate_required(trigger, "trigger", "iteration")
            validate_required(impacted_agents, "impacted_agents", "iteration")
            validate_required(description, "description", "iteration")

            # Record iteration
            result = self.ledger_service.record_iteration(
                project_name=project,
                trigger=trigger,
                impacted_agents=impacted_agents,
                description=description,
                version_bump=version_bump
            )
            display_success(f"Iteration recorded: {trigger} (ID: {result['entry_id']})")

        except Exception as e:
            handle_error(e, "iteration recording", {"project": project, "trigger": trigger})

    def handle_session(
        self,
        project: str,
        agent: str
    ) -> None:
        """
        Handle session context command.

        Args:
            project: Project name (required)
            agent: Agent ID (required)

        Raises:
            CLIExecutionError: If session recording fails
        """
        try:
            validate_required(project, "project", "session")
            validate_required(agent, "agent", "session")

            # Placeholder - implement session logic
            logger.info(f"Recording session context for {agent} in project '{project}'")
            display_success(f"Session context recorded for {agent}")

        except Exception as e:
            handle_error(e, "session recording", {"project": project, "agent": agent})

    def handle_assumption(
        self,
        project: str,
        assumption: str,
        rationale: str
    ) -> None:
        """
        Handle assumption recording command.

        Args:
            project: Project name (required)
            assumption: Assumption text (required)
            rationale: Rationale for the assumption (required)

        Raises:
            CLIExecutionError: If assumption recording fails
        """
        try:
            validate_required(project, "project", "assumption")
            validate_required(assumption, "assumption", "assumption")
            validate_required(rationale, "rationale", "assumption")

            # Get active agent
            active_session = self.ledger_service.get_active_session(project)
            if not active_session:
                raise CLIExecutionError("No active agent session found. Please activate an agent first.")
            agent_id = active_session.get('agent_id')

            # Record assumption
            result = self.ledger_service.record_assumption(
                project_name=project,
                agent_id=agent_id,
                assumption=assumption,
                rationale=rationale
            )
            display_success(f"Assumption recorded (ID: {result['entry_id']})")

        except Exception as e:
            handle_error(e, "assumption recording", {"project": project})

    def handle_blocker(
        self,
        project: str,
        title: str,
        description: str,
        blocked_agents: Optional[List[str]] = None
    ) -> None:
        """
        Handle blocker recording command.

        Args:
            project: Project name (required)
            title: Blocker title (required)
            description: Blocker description (required)
            blocked_agents: List of blocked agent IDs (optional)

        Raises:
            CLIExecutionError: If blocker recording fails
        """
        try:
            validate_required(project, "project", "blocker")
            validate_required(title, "title", "blocker")
            validate_required(description, "description", "blocker")

            # Get active agent as reporter
            active_session = self.ledger_service.get_active_session(project)
            if not active_session:
                raise CLIExecutionError("No active agent session found. Please activate an agent first.")
            reporter = active_session.get('agent_id')

            # Record blocker
            result = self.ledger_service.record_blocker(
                project_name=project,
                reporter=reporter,
                title=title,
                description=description,
                blocked_agents=blocked_agents
            )
            display_success(f"Blocker recorded: {title} (ID: {result['entry_id']})")

        except Exception as e:
            handle_error(e, "blocker recording", {"project": project, "title": title})


__all__ = ["EntryHandlers"]
