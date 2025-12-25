"""
Text User Interface for Agentic Workflow OS
Provides interactive menus and guided workflows for better UX.
"""

from pathlib import Path
import sys
from typing import Optional, Dict, Any
from dataclasses import dataclass

from rich.console import Console

from ..handlers import (
    ProjectHandlers,
    WorkflowHandlers,
    SessionHandlers,
    EntryHandlers,
    QueryHandlers,
    ArtifactHandlers,
)
from .ui import LayoutManager, InputHandler, Theme, FeedbackPresenter, ProgressPresenter
from agentic_workflow.core.exceptions import AgenticWorkflowError
from agentic_workflow import __version__


@dataclass
class TUIContext:
    """Shared UI dependencies for the TUI runtime."""

    console: Console
    layout: LayoutManager
    input_handler: InputHandler
    theme: Any
    feedback: FeedbackPresenter
    progress: ProgressPresenter


class TUIApp:
    """Main TUI Application Class"""

    def __init__(self, config=None):
        """Initialize the TUI application with configuration."""
        self.config = config
        self.current_context = "project" if config and config.is_project_context else "global"
        self.project_root = config.project.root_path if config and config.project else None
        self.console = Console()
        self.layout = LayoutManager(self.console, theme_map=Theme.get_color_map())
        self.input_handler = InputHandler(self.console)
        self.theme = Theme
        self.feedback = FeedbackPresenter(self.console, layout=self.layout, theme_map=self.theme.feedback_theme())
        self.progress = ProgressPresenter(self.console, layout=self.layout, theme_map=self.theme.progress_theme())
        self.context = TUIContext(
            console=self.console,
            layout=self.layout,
            input_handler=self.input_handler,
            theme=self.theme,
            feedback=self.feedback,
            progress=self.progress,
        )
        # Note: session_context removed - controllers now fetch fresh data from handlers
        self.project_handlers = ProjectHandlers()
        self.workflow_handlers = WorkflowHandlers()
        self.session_handlers = SessionHandlers(config)
        self.entry_handlers = EntryHandlers()
        self.query_handlers = QueryHandlers()
        self.artifact_handlers = ArtifactHandlers()
        
        # Initialize controllers
        from .controllers import (
            GlobalMenuController, 
            ProjectMenuController,
            ProjectWizardController,
            ProjectManagementController,
            SystemInfoController,
            WorkflowStatusController,
            ProjectNavigationController,
            AgentOperationsController,
            ArtifactManagementController
        )
        self.global_menu_controller = GlobalMenuController(self)
        self.project_menu_controller = ProjectMenuController(self)
        self.project_wizard_controller = ProjectWizardController(self)
        self.project_management_controller = ProjectManagementController(self)
        self.system_info_controller = SystemInfoController(self)
        self.workflow_status_controller = WorkflowStatusController(self)
        self.project_navigation_controller = ProjectNavigationController(self)
        self.agent_operations_controller = AgentOperationsController(self)
        self.artifact_management_controller = ArtifactManagementController(self)

        # Initialize views
        from .views import ErrorView
        self.error_view = ErrorView(console=self.console, input_handler=self.input_handler, theme_map=self.theme.get_color_map())

    def run(self):
        """Main TUI loop"""
        try:
            if self.current_context == "global":
                # Global menu handles its own loop and exits when done
                self.global_menu_controller.run_menu()
                return  # Exit after global menu completes
            else:
                # Project menu loop
                while True:
                    new_context = self.project_menu_controller.run_menu()
                    if new_context == "global":
                        self.current_context = "global"
                        self.project_root = None
                        break  # Go back to global
        except KeyboardInterrupt:
            self.feedback.info("Goodbye!")
            return  # Exit gracefully
        except SystemExit:
            # Handle SystemExit from menu cancellation
            return
        except AgenticWorkflowError as e:
            # Business Logic Errors (Governance, Config, etc.)
            self.error_view.display_error_modal(str(e), title="Operation Failed")
            # Return to main menu
            return
        except Exception as e:
            # Unexpected crashes
            self.error_view.display_error_modal(f"An unexpected error occurred:\n{str(e)}", title="Critical Error")
            raise
            sys.exit(1)

    def _list_projects(self):
        """List existing projects"""
        self.feedback.info("Existing Projects")
        self.feedback.info("")

        try:
            result = self.project_handlers.list_projects_data()

            # Use the new view to render the project list
            from .views import ProjectListView
            view = ProjectListView(console=self.console, theme_map=self.theme.get_color_map())
            view.render(result)

        except Exception as e:
            self.feedback.error(f"Failed to list projects: {e}")

        self.input_handler.wait_for_user()


def main():
    """TUI entry point"""
    app = TUIApp()
    app.run()


if __name__ == "__main__":
    main()


__all__ = ["TUIApp", "TUIContext", "main"]
