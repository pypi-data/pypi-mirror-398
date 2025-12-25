"""
Workflow action classes for the Command Pattern implementation.

This module contains concrete action classes for agent operations.
"""

from typing import Any, Dict
from questionary import Choice

from .base_action import BaseAction
from ..ui import InputResult


class ActivateAgentAction(BaseAction):
    """Action for activating an agent."""

    @property
    def display_name(self) -> str:
        return "Activate Agent"

    def get_description(self) -> str:
        return "Activate an agent for the current workflow session"

    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the activate agent action."""
        project_name = context.get('project_name', 'Unknown')

        agent_id = self.app.input_handler.get_text("Enter agent ID to activate:")
        if agent_id == InputResult.EXIT or not agent_id:
            return None

        try:
            with self.app.progress.spinner(f"Activating agent {agent_id}..."):
                self.app.session_handlers.handle_activate(
                    project=project_name,
                    agent_id=agent_id
                )
            self.app.feedback.success(f"Agent {agent_id} activated successfully!")
            return True
        except Exception as e:
            self.app.error_view.display_error_modal(str(e))
            return False


class HandoffAction(BaseAction):
    """Action for recording agent handoffs."""

    @property
    def display_name(self) -> str:
        return "Record Agent Handoff"

    def get_description(self) -> str:
        return "Record a handoff between agents with artifacts and notes"

    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the handoff action."""
        project_name = context.get('project_name', 'Unknown')

        # Prefetch active agent via handler
        active_agent = "Unknown"
        try:
            session_data = self.app.query_handlers.get_active_session(project_name)
            if session_data and session_data.get('agent_id'):
                active_agent = session_data['agent_id']
        except Exception:
            pass  # Keep default if fetch fails

        # Pre-fill from_agent with active agent
        from_agent = self.app.input_handler.get_text("From agent ID:", default=active_agent)
        if from_agent == InputResult.EXIT:
            return None

        to_agent = self.app.input_handler.get_text(
            "To agent ID:",
            validate=lambda x: len(x.strip()) > 0 or "To agent ID is required"
        )
        if to_agent == InputResult.EXIT:
            return None

        artifacts = self.app.input_handler.get_text("Artifacts (comma-separated, optional):")
        if artifacts == InputResult.EXIT:
            return None

        notes = self.app.input_handler.get_text("Handoff notes (optional):")
        if notes == InputResult.EXIT:
            return None

        if from_agent and to_agent:
            try:
                with self.app.progress.spinner("Recording agent handoff..."):
                    self.app.entry_handlers.handle_handoff(
                        project=project_name,
                        from_agent=from_agent,
                        to_agent=to_agent,
                        artifacts=artifacts if artifacts else None,
                        notes=notes if notes else None
                    )
                self.app.feedback.success("Handoff recorded successfully!")
                return True
            except Exception as e:
                self.app.error_view.display_error_modal(str(e))
                return False
        return None


class DecisionAction(BaseAction):
    """Action for recording decisions."""

    @property
    def display_name(self) -> str:
        return "Record Decision"

    def get_description(self) -> str:
        return "Record a decision with rationale"

    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the decision action."""
        project_name = context.get('project_name', 'Unknown')

        title = self.app.input_handler.get_text(
            "Decision title:",
            validate=lambda x: len(x.strip()) > 0 or "Decision title is required"
        )
        if title == InputResult.EXIT:
            return None

        rationale = self.app.input_handler.get_text(
            "Decision rationale:",
            validate=lambda x: len(x.strip()) > 0 or "Decision rationale is required"
        )
        if rationale == InputResult.EXIT:
            return None

        agent = self.app.input_handler.get_text("Agent ID (optional):")
        if agent == InputResult.EXIT:
            return None

        if title and rationale:
            try:
                with self.app.progress.spinner("Recording decision..."):
                    self.app.entry_handlers.handle_decision(
                        project=project_name,
                        title=title,
                        rationale=rationale,
                        agent=agent if agent else None
                    )
                self.app.feedback.success("Decision recorded successfully!")
                return True
            except Exception as e:
                self.app.error_view.display_error_modal(str(e))
                return False
        return None


class FeedbackAction(BaseAction):
    """Action for recording feedback."""

    @property
    def display_name(self) -> str:
        return "Record Feedback"

    def get_description(self) -> str:
        return "Record feedback on agents or artifacts"

    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the feedback action."""
        project_name = context.get('project_name', 'Unknown')

        target = self.app.input_handler.get_text("Feedback target (agent or artifact):")
        if target == InputResult.EXIT or not target:
            return None

        severity = self.app.input_handler.get_selection(
            choices=[
                Choice(title="Low", value="low"),
                Choice(title="Medium", value="medium"),
                Choice(title="High", value="high")
            ],
            message="Severity:"
        )
        if severity == InputResult.EXIT:
            return None

        summary = self.app.input_handler.get_text("Feedback summary:")
        if summary == InputResult.EXIT or not summary:
            return None

        if target and severity and summary:
            try:
                with self.app.progress.spinner("Recording feedback..."):
                    self.app.entry_handlers.handle_feedback(
                        project=project_name,
                        target=target,
                        severity=severity,
                        summary=summary
                    )
                self.app.feedback.success("Feedback recorded successfully!")
                return True
            except Exception as e:
                self.app.error_view.display_error_modal(str(e))
                return False
        return None


class BlockerAction(BaseAction):
    """Action for recording blockers."""

    @property
    def display_name(self) -> str:
        return "Record Blocker"

    def get_description(self) -> str:
        return "Record workflow blockers and affected agents"

    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the blocker action."""
        project_name = context.get('project_name', 'Unknown')

        title = self.app.input_handler.get_text("Blocker title:")
        if title == self.app.input_handler.InputResult.EXIT or not title:
            return None

        description = self.app.input_handler.get_text("Blocker description:")
        if description == self.app.input_handler.InputResult.EXIT or not description:
            return None

        blocked_agents = self.app.input_handler.get_text("Blocked agents (comma-separated, optional):")
        if blocked_agents == self.app.input_handler.InputResult.EXIT:
            return None

        if title and description:
            try:
                with self.app.progress.spinner("Recording blocker..."):
                    self.app.entry_handlers.handle_blocker(
                        project=project_name,
                        title=title,
                        description=description,
                        blocked_agents=blocked_agents.split(',') if blocked_agents else None
                    )
                self.app.feedback.success("Blocker recorded successfully!")
                return True
            except Exception as e:
                self.app.error_view.display_error_modal(str(e))
                return False
        return None


class IterationAction(BaseAction):
    """Action for recording iterations."""

    @property
    def display_name(self) -> str:
        return "Record Iteration"

    def get_description(self) -> str:
        return "Record workflow iterations and version changes"

    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the iteration action."""
        project_name = context.get('project_name', 'Unknown')

        trigger = self.app.input_handler.get_text("What triggered this iteration:")
        if trigger == self.app.input_handler.InputResult.EXIT or not trigger:
            return None

        impacted_agents = self.app.input_handler.get_text("Impacted agents (comma-separated):")
        if impacted_agents == self.app.input_handler.InputResult.EXIT or not impacted_agents:
            return None

        description = self.app.input_handler.get_text("Iteration description:")
        if description == self.app.input_handler.InputResult.EXIT or not description:
            return None

        version_bump = self.app.input_handler.get_selection(
            choices=[
                Choice(title="Patch", value="patch"),
                Choice(title="Minor", value="minor"),
                Choice(title="Major", value="major")
            ],
            message="Version bump:"
        )
        if version_bump == self.app.input_handler.InputResult.EXIT:
            return None

        if trigger and impacted_agents and description and version_bump:
            try:
                with self.app.progress.spinner("Recording iteration..."):
                    self.app.entry_handlers.handle_iteration(
                        project=project_name,
                        trigger=trigger,
                        impacted_agents=impacted_agents.split(','),
                        description=description,
                        version_bump=version_bump
                    )
                self.app.feedback.success("Iteration recorded successfully!")
                return True
            except Exception as e:
                self.app.error_view.display_error_modal(str(e))
                return False
        return None


class AssumptionAction(BaseAction):
    """Action for recording assumptions."""

    @property
    def display_name(self) -> str:
        return "Record Assumption"

    def get_description(self) -> str:
        return "Record workflow assumptions and their rationale"

    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the assumption action."""
        project_name = context.get('project_name', 'Unknown')

        assumption = self.app.input_handler.get_text("Assumption:")
        if assumption == self.app.input_handler.InputResult.EXIT or not assumption:
            return None

        rationale = self.app.input_handler.get_text("Rationale:")
        if rationale == self.app.input_handler.InputResult.EXIT or not rationale:
            return None

        if assumption and rationale:
            try:
                with self.app.progress.spinner("Recording assumption..."):
                    self.app.entry_handlers.handle_assumption(
                        project=project_name,
                        assumption=assumption,
                        rationale=rationale
                    )
                self.app.feedback.success("Assumption recorded successfully!")
                return True
            except Exception as e:
                self.app.error_view.display_error_modal(str(e))
                return False
        return None


class EndWorkflowAction(BaseAction):
    """Action for ending the workflow."""

    @property
    def display_name(self) -> str:
        return "End Workflow"

    def get_description(self) -> str:
        return "End the current workflow session"

    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the end workflow action."""
        project_name = context.get('project_name', 'Unknown')

        confirm = self.app.input_handler.get_confirmation("Are you sure you want to end the workflow?", default=False)
        if confirm == self.app.input_handler.InputResult.EXIT:
            return None

        if confirm:
            try:
                with self.app.progress.spinner("Ending workflow session..."):
                    self.app.session_handlers.handle_end(project=project_name)
                self.app.feedback.success("Workflow ended successfully!")
                return True
            except Exception as e:
                self.app.error_view.display_error_modal(str(e))
                return False
        return None


__all__ = [
    "ActivateAgentAction",
    "HandoffAction",
    "DecisionAction",
    "FeedbackAction",
    "BlockerAction",
    "IterationAction",
    "AssumptionAction",
    "EndWorkflowAction",
]