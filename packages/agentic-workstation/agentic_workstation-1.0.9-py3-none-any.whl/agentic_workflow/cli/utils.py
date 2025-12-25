#!/usr/bin/env python3
"""Utility functions for Agentic Workflow CLI."""
# Re-export functions from their new locations for backward compatibility

# UI functions from cli.ui_utils
from .ui_utils import (
    setup_logging,
    format_output,
    confirm_action,
    show_progress,
    display_error,
    exit_with_error,
    display_success,
    display_warning,
    display_info,
    display_status_panel,
    display_help_panel,
    display_action_result,
    display_project_summary,
    shorten_path,
    format_file_list,
)

# Business logic functions from core.project
from ..core.project import (
    get_project_root,
    is_in_project,
    validate_project_name,
)

# Generation functions from generators.structure
# from ..generators.structure import (
#     create_project_structure,
#     generate_project_files,
#     generate_initial_artifacts,
#     render_template,
#     build_agent_context,
# )

# Canonical loading functions from generation.canonical_loader
# from ..generation.canonical_loader import (
#     load_workflow_manifest,
#     load_canonical_workflow_data,
# )

# Expose all imported functions
__all__ = [
    # UI functions
    "setup_logging",
    "format_output",
    "confirm_action",
    "show_progress",
    "display_error",
    "exit_with_error",
    "display_success",
    "display_warning",
    "display_info",
    "display_status_panel",
    "display_help_panel",
    "display_action_result",
    "display_project_summary",
    "shorten_path",
    "format_file_list",
# Business logic
    "get_project_root",
    "is_in_project",
    "validate_project_name",
    # Generation
    # "create_project_structure",
    # "generate_project_files",
    # "generate_initial_artifacts",
    # "render_template",
    # "build_agent_context",
    # Canonical loading
    # "load_workflow_manifest",
    # "load_canonical_workflow_data",
]