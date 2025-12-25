"""
Wizard controllers for TUI.

This module contains controllers for guided workflows and wizards.
"""

from questionary import Choice

from .base_controller import BaseController
from ..ui import InputResult


class ProjectWizardController(BaseController):
    """Controller for project creation wizard."""

    def execute(self, *args, **kwargs) -> bool:
        """Execute the project creation wizard.
        
        Returns:
            True if project was created successfully, False if cancelled
        """
        # Clear screen and show wizard header
        self.layout.render_screen(
            "",
            title="Project Creation Wizard",
            subtitle="Create a new Agentic Workflow project",
            footer_text="",
            # clear=True
        )
        
        # Project name
        name = self.input_handler.get_text("Project name:")
        if name == InputResult.EXIT or not name:
            return False

        # Workflow type - get real workflow types
        try:
            workflow_type = self._select_workflow_type()
            if workflow_type == InputResult.EXIT or not workflow_type:
                return False
        except Exception as e:
            from rich.text import Text
            self.layout.render_screen(
                body_content=Text(f"Failed to load workflows: {e}", style=self.theme.ERROR),
                title="Error",
                footer_text="Press Enter to continue...",
                clear=True
            )
            return False

        # Description
        description = self.input_handler.get_text("Project description:")
        if description == InputResult.EXIT:
            return False

        # Confirm
        confirm = self.input_handler.get_confirmation(f"Create project '{name}' with {workflow_type} workflow?")
        if confirm == InputResult.EXIT:
            return False

        if confirm:
            try:
                # Use session handlers for proper atomic pipeline initialization
                with self.app.progress.spinner(f"Creating project '{name}'...", use_spinner=False):
                    self.app.session_handlers.handle_init(
                        project=name,
                        workflow=workflow_type,
                        description=description,
                        force=False
                    )
                
                # Show success message
                from rich.text import Text
                success_body = Text(
                    f"✓ Project '{name}' created successfully!\n\nYou can now navigate to the project directory and start working.",
                    style=self.theme.SUCCESS
                )
                self.layout.render_screen(
                    body_content=success_body,
                    title="Project Created",
                    footer_text="Press Enter to continue...",
                    clear=True
                )
                self.input_handler.wait_for_user(show_message=False)
                return True
            except Exception as e:
                from rich.text import Text
                self.layout.render_screen(
                    body_content=Text(f"Failed to create project: {e}", style=self.theme.ERROR),
                    title="Error",
                    footer_text="Press Enter to continue...",
                    clear=True
                )
                return False
        else:
            from rich.text import Text
            self.layout.render_screen(
                body_content=Text("Project creation cancelled.", style=self.theme.WARNING),
                title="Cancelled",
                footer_text="Press Enter to continue...",
                clear=True
            )
            return False

    def _select_workflow_type(self) -> str:
        """Select workflow type with dynamic loading."""
        try:
            workflows = self.app.workflow_handlers.list_workflows_data()
            workflow_choices = []
            for workflow in workflows:
                desc = f"{workflow.get('description', 'No description')[:60]}..."
                workflow_choices.append(
                    Choice(title=f"{workflow.get('name')} - {desc}", value=workflow.get('name'))
                )
        except Exception as e:
            from agentic_workflow.core.exceptions import AgenticWorkflowError
            raise AgenticWorkflowError("No workflows found. System may be corrupt.") from e

        return self.input_handler.get_selection(
            choices=workflow_choices,
            message="Select workflow type:"
        )


__all__ = ["ProjectWizardController"]