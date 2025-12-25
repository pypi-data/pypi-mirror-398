"""
Base action classes for the Command Pattern implementation.

This module defines the abstract base class for all actions in the TUI.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAction(ABC):
    """Abstract base class for all actions in the TUI."""

    def __init__(self, app):
        """Initialize the action with the TUI app instance."""
        self.app = app
        self.name = self.__class__.__name__.replace('Action', '').lower()
        self.description = self.get_description()

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Get the display name for this action."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get the description for this action."""
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the action with the given context.

        Args:
            context: Dictionary containing execution context (project_name, etc.)

        Returns:
            Any result from the action execution
        """
        pass


__all__ = ["BaseAction"]