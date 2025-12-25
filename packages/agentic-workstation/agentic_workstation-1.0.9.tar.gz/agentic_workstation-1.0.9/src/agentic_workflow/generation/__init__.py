"""Generation module.

This module contains scripts for generating content:
- canonical_loader: Load canonical JSON workflow files
- denormalizer: Denormalize canonical data for YAML generation
- yaml_writer: Write formatted YAML with comments
- generate_workflow_yaml: Main orchestrator for YAML generation
- generate_agents: Generate agent files from workflow packages
"""
from agentic_workflow.generation.canonical_loader import (
    load_canonical_workflow,
    list_canonical_workflows,
    get_agents_list,
    get_artifacts_list,
    get_instructions_list,
    get_workflow_metadata,
    CanonicalLoadError,
)
from agentic_workflow.generation.denormalizer import (
    Denormalizer,
    denormalize_canonical,
)
from agentic_workflow.generation.yaml_writer import (
    YamlWriter,
    write_all_yaml,
)

__all__ = [
    # Canonical loader
    'load_canonical_workflow',
    'list_canonical_workflows',
    'get_agents_list',
    'get_artifacts_list',
    'get_instructions_list',
    'get_workflow_metadata',
    'CanonicalLoadError',
    # Denormalizer
    'Denormalizer',
    'denormalize_canonical',
    # YAML writer
    'YamlWriter',
    'write_all_yaml',
]
