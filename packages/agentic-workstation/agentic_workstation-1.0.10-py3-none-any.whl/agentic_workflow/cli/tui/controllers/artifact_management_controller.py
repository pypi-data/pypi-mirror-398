"""
Artifact management controller for TUI.

This module contains the controller for artifact management menu.
"""

from pathlib import Path
from questionary import Choice

from .base_controller import BaseController
from ..ui import InputResult
from ..views import ArtifactContentView


class ArtifactManagementController(BaseController):
    """Controller for artifact management menu."""

    def execute(self, *args, **kwargs) -> None:
        """Execute the artifact management."""
        self.run_menu()

    def run_menu(self) -> None:
        """Run the artifact management menu."""
        self.feedback.info("Artifact Management")

        project_root = self.app.project_root
        if not project_root:
            self.feedback.error("Not in a project directory.")
            self.input_handler.wait_for_user()
            return

        artifacts_dir = Path(project_root) / "artifacts"
        if not artifacts_dir.exists():
            self.feedback.warning("No artifacts directory found in this project.")
            self.input_handler.wait_for_user()
            return

        artifacts = self.app.artifact_handlers.list_artifacts(artifacts_dir)
        if not artifacts:
            self.feedback.info("No artifacts found in the artifacts directory.")
            self.input_handler.wait_for_user()
            return

        artifact_choices = [
            Choice(title=str(relative_path), value=(full_path, relative_path))
            for full_path, relative_path in artifacts
        ]

        selected = self.input_handler.get_selection(
            choices=artifact_choices,
            message="Select an artifact to view:"
        )

        if selected == InputResult.EXIT or selected is None:
            return

        full_path, relative_path = selected
        try:
            with self.app.progress.spinner(f"Opening {relative_path}"):
                content = self.app.artifact_handlers.read_artifact(full_path)

            view = ArtifactContentView(console=self.console, theme_map=self.theme.get_color_map())
            view.render(full_path, relative_path, content)
            self.input_handler.wait_for_user("Press Enter to return to artifacts...")
        except Exception as e:
            self.feedback.error(f"Failed to read artifact: {e}")


__all__ = ["ArtifactManagementController"]