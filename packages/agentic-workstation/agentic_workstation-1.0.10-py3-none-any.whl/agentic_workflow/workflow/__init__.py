"""
Workflow package loader module.

Provides functions for discovering and loading workflow packages from
manifests/workflows//.
"""

from ..generation.canonical_loader import (
    list_workflows,
    load_workflow,
    get_workflow_agents,
    get_workflow_artifacts,
    get_workflow_instructions,
    get_default_workflow,
    WorkflowPackage,
    WorkflowError,
)

from .resolver import (
    get_workflow_for_project,
    get_workflow_name_for_project,
    resolve_workflow,
)

__all__ = [
    # Loader
    "list_workflows",
    "load_workflow",
    "get_workflow_agents",
    "get_workflow_artifacts",
    "get_workflow_instructions",
    "get_default_workflow",
    "WorkflowPackage",
    "WorkflowError",
    # Resolver
    "get_workflow_for_project",
    "get_workflow_name_for_project",
    "resolve_workflow",
]
