"""
Pydantic models for Agentic Workflow configuration.

This module defines the type-safe configuration schemas for the cascading
configuration system. All configurations are validated using Pydantic V2.
"""

from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal, TypedDict
from enum import Enum


class LogLevel(str, Enum):
    """Enumerate supported logging levels used across the system."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# Public API
__all__ = [
    "LogLevel",
    "SystemConfig",
    "ProjectConfig",
    "WorkflowRules",
    "RuntimeConfig",
]


# TypedDicts for nested workflow structures to expose schema shapes
class StageSpec(TypedDict, total=False):
    """Typed shape describing a workflow stage (id, name, description, metadata)."""
    id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    metadata: Optional[Dict[str, object]]


class GateSpec(TypedDict, total=False):
    """Typed shape describing a workflow gate with condition and transitions."""
    name: Optional[str]
    condition: Optional[Dict[str, object]]
    on_pass: Optional[List[str]]
    on_fail: Optional[List[str]]


class GovernanceSpec(TypedDict, total=False):
    """Typed mapping for governance rules and strictness levels for a workflow."""
    rules: Optional[Dict[str, object]]
    strictness: Optional[Dict[str, str]]


class SystemConfig(BaseModel):
    """Represent global system configuration stored in the user's config file.

    Resides in `~/.config/agentic/config.yaml` and contains workspace and UX settings.
    """
    # Core Workspace Settings
    default_workspace: Path = Field(
        default=Path("~/AgenticProjects"),
        description="Default root directory for all new projects"
    )
    # User Experience
    editor_command: str = Field(
        default="code",
        description="Command to open files/artifacts (e.g., 'code', 'vim', 'nano')"
    )
    tui_enabled: bool = Field(
        default=True,
        description="Enable interactive TUI features by default"
    )
    check_updates: bool = Field(
        default=True,
        description="Check for package updates on startup"
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Default logging level"
    )

    @field_validator("default_workspace")
    @classmethod
    def validate_workspace_path(cls, v) -> Path:
        """Expand ~ in path and return as Path"""
        if isinstance(v, str):
            return Path(v).expanduser()
        return v.expanduser()


class ProjectConfig(BaseModel):
    """Describe project-specific configuration stored under the project's `.agentic` directory.

    Includes workflow selection, root path, and project-level overrides.
    """
    workflow: str = Field(
        description="Name of the active workflow type"
    )
    root_path: Path = Field(
        description="Absolute path to the project root"
    )
    strict_mode: bool = Field(
        default=True,
        description="Enforce strict governance rules"
    )
    description: str = Field(
        default="",
        description="Project description"
    )
    excluded_paths: List[str] = Field(
        default_factory=list,
        description="Paths to exclude from processing"
    )
    custom_overrides: Dict[str, object] = Field(
        default_factory=dict,
        description="Workflow-specific overrides"
    )
    


class WorkflowRules(BaseModel):
    """Model the immutable workflow rules loaded from a workflow package's `workflow.json`.

    Exposes stages, gate definitions, required artifacts and governance metadata.
    """
    stages: List[StageSpec] = Field(default_factory=list)
    gates: Dict[str, GateSpec] = Field(default_factory=dict)
    required_artifacts: List[str] = Field(default_factory=list)
    governance: GovernanceSpec = Field(default_factory=dict)


class RuntimeConfig(BaseModel):
    """Represent the final merged runtime configuration used by the engine.

    Combines `SystemConfig`, `ProjectConfig`, and `WorkflowRules` into a single object.
    """
    system: SystemConfig = Field(default_factory=SystemConfig)
    project: Optional[ProjectConfig] = None
    workflow_rules: WorkflowRules = Field(default_factory=WorkflowRules)
    verbose: bool = Field(default=False, description="Runtime verbosity flag")
    force: bool = Field(default=False, description="Force operations")
    @property
    def is_project_context(self) -> bool:
        """Check if we're in a project context"""
        return self.project is not None