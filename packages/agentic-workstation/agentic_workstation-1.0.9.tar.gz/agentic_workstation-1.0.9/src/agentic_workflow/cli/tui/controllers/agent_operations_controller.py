"""
Agent operations controller for TUI.

This module contains the controller for agent operations menu.
"""

from questionary import Choice

from .base_controller import BaseController
from ..actions import (
    ActivateAgentAction,
    HandoffAction,
    DecisionAction,
    FeedbackAction,
    BlockerAction,
    IterationAction,
    AssumptionAction,
    EndWorkflowAction,
)
from ..ui import InputResult


class AgentOperationsController(BaseController):
    """Controller for agent operations menu."""

    def __init__(self, app):
        """Initialize the agent operations controller."""
        super().__init__(app)
        # Register actions using the Command Pattern
        self.actions = {
            'activate': ActivateAgentAction(self.app),
            'handoff': HandoffAction(self.app),
            'decision': DecisionAction(self.app),
            'feedback': FeedbackAction(self.app),
            'blocker': BlockerAction(self.app),
            'iteration': IterationAction(self.app),
            'assumption': AssumptionAction(self.app),
            'end': EndWorkflowAction(self.app),
        }

    def execute(self, *args, **kwargs) -> None:
        """Execute the agent operations menu."""
        self.run_menu()

    def run_menu(self) -> None:
        """Run the agent operations menu."""
        self.display_context_header("Agent Operations")
        project_name = self.app.project_root.name if self.app.project_root else "Unknown"

        # FIXED: Use the dictionary KEY as the value to ensure lookup succeeds
        choices = [
            Choice(title=action.display_name, value=key)
            for key, action in self.actions.items()
        ]

        # Agent operations menu
        choice = self.input_handler.get_selection(
            choices=choices,
            message="Select agent operation:"
        )

        if choice == InputResult.EXIT or choice is None:
            return  # Cancelled

        # Dispatch
        if choice in self.actions:
            context = {'project_name': project_name}
            self.actions[choice].execute(context)
            # Give the user a chance to read results before returning
            self.input_handler.wait_for_user()


__all__ = ["AgentOperationsController"]