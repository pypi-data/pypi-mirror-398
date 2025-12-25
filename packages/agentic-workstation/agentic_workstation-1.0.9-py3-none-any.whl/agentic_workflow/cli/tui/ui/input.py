"""
Input handling for the Agentic Workflow OS TUI.

This module provides consistent input handling with proper exit logic.
"""

from enum import Enum
from typing import List, Optional, Union
import questionary
from questionary import Choice
from rich.console import Console

from .theme import Theme


class InputResult(Enum):
    """Sentinel values for input results."""
    EXIT = "exit"
    CONTINUE = "continue"


class InputHandler:
    """Handles user input with consistent styling and exit logic."""

    def __init__(self, console: Console = None):
        """Initialize the input handler."""
        self.console = console or Console()

    def get_selection(
        self,
        choices: List[Choice],
        message: str = "Select an option:"
    ) -> Union[str, InputResult]:
        """Get a selection from the user.

        Args:
            choices: List of Choice objects
            message: Prompt message

        Returns:
            Selected value or InputResult.EXIT on cancellation
        """
        # Add exit option if not present
        has_exit = any(choice.value in ['exit', 'cancel', 'back'] for choice in choices)
        if not has_exit:
            choices = choices + [Choice(title="Cancel / Exit", value="cancel")]

        try:
            result = questionary.select(
                message,
                choices=choices,
                instruction="",
                qmark="",
                use_shortcuts=False,
                pointer="▶ "
            ).unsafe_ask()

            if result in ['exit', 'cancel', 'back']:
                return InputResult.EXIT

            return result

        except KeyboardInterrupt:
            return InputResult.EXIT
        except Exception as e:
            from rich.text import Text
            self.console.print(Text(f"Input error: {e}", style=Theme.ERROR))
            return InputResult.EXIT

    def get_text(
        self,
        message: str = "Enter text:",
        default: str = "",
        validate: Optional[callable] = None
    ) -> Union[str, InputResult]:
        """Get text input from the user.

        Args:
            message: Prompt message
            default: Default value
            validate: Validation function

        Returns:
            Input text or InputResult.EXIT on cancellation
        """
        try:
            result = questionary.text(
                message,
                default=default,
                validate=validate
            ).unsafe_ask()

            return result

        except KeyboardInterrupt:
            return InputResult.EXIT
        except Exception as e:
            from rich.text import Text
            self.console.print(Text(f"Input error: {e}", style=Theme.ERROR))
            return InputResult.EXIT

    def wait_for_user(self, message: Optional[str] = "Press Enter to continue...", *, show_message: bool = True) -> InputResult:
        """Wait for user to press Enter with exit sentinel support.

        Returns:
            InputResult.CONTINUE on enter, InputResult.EXIT on cancellation.
        """
        try:
            if show_message and message:
                from rich.text import Text
                self.console.print(Text(message, style=Theme.INFO_TEXT))
            self.console.input("")
            return InputResult.CONTINUE
        except KeyboardInterrupt:
            return InputResult.EXIT

    def get_confirmation(
        self,
        message: str = "Are you sure?",
        default: bool = False
    ) -> Union[bool, InputResult]:
        """Get a confirmation from the user.

        Args:
            message: Confirmation message
            default: Default value

        Returns:
            True/False or InputResult.EXIT on cancellation
        """
        try:
            return questionary.confirm(
                message,
                default=default
            ).unsafe_ask()

        except KeyboardInterrupt:
            return InputResult.EXIT
        except Exception as e:
            from rich.text import Text
            self.console.print(Text(f"Input error: {e}", style=Theme.ERROR))
            return InputResult.EXIT


__all__ = ["InputHandler", "InputResult"]