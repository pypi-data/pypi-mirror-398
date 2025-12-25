"""Orchestrate project creation using workflow-driven generators.

Delegate to specialized generators to create configuration, directory
structure and runtime artifacts driven by a workflow package.
- Config generation: generators/config.py
- Structure generation: generators/structure.py
- Runtime generation: generators/runtime.py

"""

import logging
from pathlib import Path
from typing import TypedDict

from .config_service import ConfigurationService

# Import specialized generators
from agentic_workflow.generators.config import generate_project_config
# from agentic_workflow.generators.structure import (
#     create_project_directories,
# )
# from agentic_workflow.generators.runtime import (
#     generate_artifact_files,
#     generate_agent_files,
#     generate_workflow_script,
#     initialize_runtime_state
# )
from agentic_workflow.core.governance_extraction import extract_governance_from_workflow

# Setup logging
logger = logging.getLogger(__name__)


class CreateProjectResult(TypedDict):
    """Result of project creation operation."""
    status: str
    path: Path


__all__ = ["create_project_from_workflow"]


def create_project_from_workflow(workflow_type: str, project_name: str, target_path: Path, description: str = None) -> CreateProjectResult:
    """Create a new project at `target_path` using the named workflow type."""
    from ..core.config_service import ConfigurationService
    from ..generators.pipeline import InitPipeline

    config_service = ConfigurationService()
    config = config_service.load_config()

    pipeline = InitPipeline(config)
    pipeline.run(project_name, str(target_path), workflow_type, description=description)

    return {"status": "created", "path": target_path}


# Update the placeholder functions in config.py
def _update_config_placeholders():
    """Update placeholder functions in config.py with actual implementations."""
    # Import the config module
    from . import config as config_module

    # Replace placeholder functions with implementations from generators/core
    config_module.generate_project_config = generate_project_config
    config_module.extract_governance_from_workflow = extract_governance_from_workflow

    logger.info("Updated config.py placeholder functions with actual implementations")