"""
Global command handlers for Agentic Workflow CLI.
Focus: System configuration and global info.
"""

from typing import Optional
import logging

from agentic_workflow.core.exceptions import AgenticWorkflowError
from ..utils import display_info, display_error, display_help_panel

logger = logging.getLogger(__name__)

class GlobalHandlers:
    """Handlers for global CLI commands."""

    def handle_list_workflows(self) -> None:
        """List available workflow types."""
        from agentic_workflow.services import WorkflowService
        workflow_service = WorkflowService()
        
        try:
            workflows = workflow_service.list_workflows()
            if not workflows:
                display_info("No workflows found")
                return

            commands = []
            for workflow in workflows:
                try:
                    info = workflow_service.get_workflow_info(workflow['name'])
                    desc = f"{info.get('description', 'No description')}\n(Agents: {info.get('agent_count', 0)}, v{info.get('version', 'unknown')})"
                    commands.append({'command': workflow['name'], 'description': desc})
                except Exception:
                    commands.append({'command': workflow['name'], 'description': "Error loading info"})

            display_help_panel("Available Workflows", commands)

        except Exception as e:
            display_error(f"Failed to list workflows: {e}")

    def handle_config(self, edit: bool = False) -> None:
        """Show or edit global configuration."""
        from agentic_workflow.core.config_service import ConfigurationService
        config_service = ConfigurationService()
        config_path = config_service._get_global_config_path()

        if edit:
            import subprocess
            from agentic_workflow.core.schema import SystemConfig
            # Hack: Instantiate default to get editor command if file doesn't exist? 
            # Better to load what exists or default.
            try:
                # Simple logic for now
                editor = "code" 
                subprocess.run([editor, str(config_path)])
            except Exception as e:
                display_error(f"Failed to open editor: {e}")
        else:
            if config_path.exists():
                with open(config_path) as f:
                    content = f.read()
                display_info(f"Global config at: {config_path}")
                display_info(content)
            else:
                display_info("No global config found. Run 'agentic init' inside a folder to set it up.")


__all__ = ["GlobalHandlers"]