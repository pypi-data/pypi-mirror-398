"""Manage project metadata: load, save and query project-level metadata.

Provides canonical helpers for reading and updating project metadata used by
session and workflow code paths.
"""
from pathlib import Path
from typing import Dict, Optional, Any, TypedDict
import json
import re

from .paths import get_projects_dir
from .config_service import ConfigurationService

# Project config filename (JSON format)
PROJECT_CONFIG_FILE = "config.yaml"

__all__ = [
    "get_project_dir",
    "project_exists",
    "load_project_meta",
    "save_project_meta",
    "get_project_workflow_name",
    "get_project_stage",
    "update_project_meta",
    "get_project_root",
    "is_in_project",
    "validate_project_name",
]


class ProjectMeta(TypedDict, total=False):
    """TypedDict describing the shape of a project's metadata mapping."""
    workflow: Optional[str]
    workflow_type: Optional[str]
    current_stage: Optional[str]
    # free-form metadata bag for compatibility with legacy configs
    metadata: Dict[str, object]


def get_project_dir(project_name: str) -> Path:
    """Get absolute path to project directory.
    
    Args:
        project_name: Name of the project.
        
    Returns:
        Path to the project directory (may not exist).
    """
    return get_projects_dir() / project_name


def project_exists(project_name: str) -> bool:
    """Check if a project exists.
    
    Args:
        project_name: Name of the project.
        
    Returns:
        True if project directory exists and has project_config.json.
    """
    project_dir = get_project_dir(project_name)
    return project_dir.exists() and (project_dir / ".agentic" / PROJECT_CONFIG_FILE).exists()


def load_project_meta(project_name: str) -> Optional[ProjectMeta]:
    """Read the project's metadata mapping from the project's config file.

    Args:
        project_name: Name of the project.

    Returns:
        A `ProjectMeta` mapping when present, otherwise `None`.
    """
    project_dir = get_project_dir(project_name)
    config_file = project_dir / ".agentic" / PROJECT_CONFIG_FILE

    if not config_file.exists():
        return None

    import yaml
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def save_project_meta(project_name: str, data: ProjectMeta) -> None:
    """Write the provided project metadata mapping to the project's config file."""
    project_dir = get_project_dir(project_name)
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")
    
    config_file = project_dir / ".agentic" / PROJECT_CONFIG_FILE
    config_file.parent.mkdir(parents=True, exist_ok=True)
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)


def get_project_workflow_name(project_name: str) -> Optional[str]:
    """Return the configured workflow name for the given project, if any."""
    meta = load_project_meta(project_name)
    if meta is None:
        return None
    workflow = meta.get('workflow')
    if isinstance(workflow, str):
        return workflow
    # Handle legacy config where workflow is a dict or missing
    workflow_type = meta.get('workflow_type')
    if isinstance(workflow_type, str):
        return workflow_type
    return None


def get_project_stage(project_name: str) -> Optional[str]:
    """Get the current stage for a project (if workflow has stages).
    
    Args:
        project_name: Name of the project.
        
    Returns:
        Current stage name, or None if not applicable.
    """
    meta = load_project_meta(project_name)
    if meta is None:
        return None
    return meta.get('current_stage')


def update_project_meta(project_name: str, updates: Dict[str, object]) -> ProjectMeta:
    """Merge `updates` into project metadata and persist the result."""
    meta = load_project_meta(project_name)
    if meta is None:
        raise FileNotFoundError(f"Project not found: {project_name}")

    meta.update(updates)
    save_project_meta(project_name, meta)
    return meta


def get_project_root() -> Optional[Path]:
    """Find the project root directory by looking for project structure.
    
    Returns:
        Path to project root, or None if not in a project.
    """
    config_service = ConfigurationService()
    return config_service.find_project_root()


def is_in_project() -> bool:
    """Check if we're currently in a project directory.
    
    Returns:
        True if in a project directory.
    """
    return get_project_root() is not None


def validate_project_name(name: str) -> bool:
    """Validate a project name.
    
    Args:
        name: Project name to validate.
        
    Returns:
        True if name is valid (alphanumeric, underscore, hyphen only).
    """
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))
