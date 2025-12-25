"""Workflow resolution utilities.

This module provides high-level functions for resolving workflows
in the context of projects.

Usage:
    from workflow.resolver import get_workflow_for_project
    
    wf = get_workflow_for_project('myproject')
"""
from typing import Optional

__all__ = [
    "get_workflow_for_project",
    "get_workflow_name_for_project",
    "resolve_workflow"
]

from ..generation.canonical_loader import load_workflow, get_default_workflow, WorkflowPackage, WorkflowError

from agentic_workflow.core.project import load_project_meta, get_project_workflow_name


def get_workflow_for_project(project_name: str) -> WorkflowPackage:
    """Load the WorkflowPackage for a project.
    
    This is the recommended way to get a workflow for an existing project.
    It reads the project's project_config.json and loads the appropriate workflow.
    
    Args:
        project_name: Name of the project.
        
    Returns:
        WorkflowPackage instance for the project's workflow.
        
    Raises:
        WorkflowError: If project doesn't exist or workflow can't be loaded.
    """
    meta = load_project_meta(project_name)
    
    if meta is None:
        raise WorkflowError(f"Project not found or has no workflow metadata: {project_name}")
    
    workflow_name = meta.get('workflow')
    if not workflow_name:
        workflow_name = get_default_workflow()
    
    return load_workflow(workflow_name)


def get_workflow_name_for_project(project_name: str) -> Optional[str]:
    """Get the workflow name for a project without loading the full package.
    
    Args:
        project_name: Name of the project.
        
    Returns:
        Workflow name string, or None if project doesn't exist.
    """
    return get_project_workflow_name(project_name)


def resolve_workflow(project_name: Optional[str] = None, 
                     workflow_name: Optional[str] = None) -> WorkflowPackage:
    """Resolve a workflow from either project or workflow name.
    
    This is a flexible resolver that works in multiple contexts:
    - If project_name is given, load the project's workflow
    - If workflow_name is given, load that workflow directly
    - If neither, load the default workflow
    
    Args:
        project_name: Optional project name.
        workflow_name: Optional workflow name (overrides project's workflow).
        
    Returns:
        WorkflowPackage instance.
        
    Raises:
        WorkflowError: If workflow can't be loaded.
    """
    # Explicit workflow name takes precedence
    if workflow_name:
        return load_workflow(workflow_name)
    
    # Try project's workflow
    if project_name:
        return get_workflow_for_project(project_name)
    
    # Fall back to default
    return load_workflow(get_default_workflow())
