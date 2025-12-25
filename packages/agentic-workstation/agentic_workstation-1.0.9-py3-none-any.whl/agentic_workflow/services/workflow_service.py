"""
Workflow service for Agentic Workflow Platform.

This service handles workflow-related operations like loading,
validation, and management.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from ..core.exceptions import (
    WorkflowError, WorkflowNotFoundError, WorkflowValidationError,
    validate_required
)
from ..core.config_service import ConfigurationService
from ..generation.canonical_loader import load_workflow, list_workflows, WorkflowPackage

logger = logging.getLogger(__name__)

__all__ = ["WorkflowService"]


class WorkflowService:
    """Service for workflow operations."""

    def __init__(self):
        """Initialize the WorkflowService with configuration."""
        config_service = ConfigurationService()
        self.config = config_service.load_config()

    def list_workflows(self) -> List[str]:
        """
        List all available workflows.

        Returns:
            List of workflow names
        """
        try:
            return list_workflows()
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            raise WorkflowError(f"Workflow listing failed: {e}", cause=e)

    def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        """
        Get information about a specific workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            Dictionary with workflow information

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
        """
        validate_required(workflow_name, "workflow_name", "get_workflow_info")

        try:
            workflow_package = load_workflow(workflow_name)

            return {
                'name': workflow_name,
                'display_name': workflow_package.display_name,
                'description': workflow_package.description,
                'version': workflow_package.version,
                'agent_count': len(workflow_package.agents),
                'agents': [agent.get('id', '') for agent in workflow_package.agents if isinstance(agent, dict)]
            }

        except FileNotFoundError:
            raise WorkflowNotFoundError(f"Workflow '{workflow_name}' not found")
        except Exception as e:
            logger.error(f"Failed to get workflow info for '{workflow_name}': {e}")
            raise WorkflowError(f"Workflow info retrieval failed: {e}", cause=e)

    def validate_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """
        Validate a workflow configuration.

        Args:
            workflow_name: Name of the workflow

        Returns:
            Dictionary with validation results

        Raises:
            WorkflowValidationError: If validation fails
        """
        validate_required(workflow_name, "workflow_name", "validate_workflow")

        try:
            # Use existing validation logic
            from ..validation.validate_canonical import validate_workflow
            result = validate_workflow(workflow_name)

            if not result.is_valid:
                raise WorkflowValidationError(
                    f"Workflow '{workflow_name}' validation failed: {result.errors}",
                    context={'workflow_name': workflow_name, 'errors': result.errors}
                )

            return {
                'workflow_name': workflow_name,
                'is_valid': True,
                'errors': [],
                'warnings': result.warnings
            }

        except WorkflowValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to validate workflow '{workflow_name}': {e}")
            raise WorkflowValidationError(f"Workflow validation failed: {e}", cause=e)

    def get_workflow_manifest(self, workflow_name: str) -> Dict[str, Any]:
        """
        Get the complete workflow manifest.

        Args:
            workflow_name: Name of the workflow

        Returns:
            Complete workflow manifest data

        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
        """
        validate_required(workflow_name, "workflow_name", "get_workflow_manifest")

        try:
            workflow_package = load_workflow(workflow_name)
            return {
                'workflow': workflow_package.metadata,
                'agents': workflow_package.agents,
                'artifacts': workflow_package.artifacts,
                'instructions': workflow_package.instructions
            }
        except FileNotFoundError:
            raise WorkflowNotFoundError(f"Workflow '{workflow_name}' not found")
        except Exception as e:
            logger.error(f"Failed to load workflow manifest '{workflow_name}': {e}")
            raise WorkflowError(f"Workflow manifest loading failed: {e}", cause=e)
