"""Define Pydantic models used for project generation and pipeline results.

Models: `VirtualFile`, `ProjectModel`, and `PipelineResult` expose explicit
fields so the architecture mapper can statically extract data schemas.
"""

from pydantic import BaseModel
from pathlib import Path
from typing import Dict, List, TypedDict, Any


# Public exports from this module
__all__ = ["VirtualFile", "ProjectModel", "PipelineResult"]


class TemplateContext(TypedDict, total=False):
    """Mapping of template variable names to serializable string values.

    This TypedDict is intentionally permissive (total=False) to represent
    common template rendering contexts while avoiding `Any` or raw `dict`.
    """
    # Common simple types used in templates
    str_value: str


class VirtualFile(BaseModel):
    """Represent a file to be created during project initialization."""
    path: Path
    content: str
    is_template: bool = True


class ProjectModel(BaseModel):
    """Model the project state prior to commit used by generators."""
    name: str
    root_path: Path
    workflow_type: str
    context_data: Dict[str, Any]  # Data for template rendering


class PipelineResult(BaseModel):
    """Return result metadata from pipeline execution for UI consumption."""
    success: bool
    message: str
    created_files: List[Path]
    updated_files: List[Path]
    skipped_files: List[Path]
    target_path: Path