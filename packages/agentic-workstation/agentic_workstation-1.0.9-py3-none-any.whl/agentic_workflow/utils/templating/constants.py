"""Constants for the templating package."""
from pathlib import Path
import importlib.resources as resources

from agentic_workflow.core.paths import get_package_root

# Template file defaults
DEFAULT_AGENT_TEMPLATE = "_base/agent_base.md.j2"
DEFAULT_SESSION_TEMPLATE = "_base/session_base.md.j2"

# Directory paths
try:
    TEMPLATES_DIR = Path(resources.files("agentic_workflow.templates"))
except Exception:
    TEMPLATES_DIR = get_package_root() / "templates"

WORKFLOWS_DIR = get_package_root() / "manifests" / "workflows"

__all__ = ["DEFAULT_AGENT_TEMPLATE", "DEFAULT_SESSION_TEMPLATE", "TEMPLATES_DIR", "WORKFLOWS_DIR"]