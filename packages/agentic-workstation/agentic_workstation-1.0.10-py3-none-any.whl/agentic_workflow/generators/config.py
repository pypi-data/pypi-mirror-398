"""
Configuration generator for project creation.

CRITICAL COMPONENT: This module is essential for project initialization.
It handles the logical generation of the project configuration dictionary,
merging app defaults with workflow-specific settings and governance rules.

Used by: core/project_generation.py for creating .agentic/config.yaml
"""

__all__ = ["generate_project_config"]

import logging
from datetime import datetime
from typing import Dict, Any

from agentic_workflow.core.governance import GOVERNANCE_LEVEL_STRICT, GOVERNANCE_LEVEL_MODERATE

logger = logging.getLogger(__name__)

def generate_project_config(workflow_type: str, project_name: str, app_config: Dict[str, Any], workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate project configuration from workflow data

    Design Decision: Create a complete project config by combining workflow data with app config defaults
    """
    # Lazy import to avoid circular dependency
    from agentic_workflow.core.governance_extraction import extract_governance_from_workflow

    project_config = {
        'name': project_name,
        'workflow': workflow_type,
        'version': '1.0.0',
        'description': f'Project generated from {workflow_type} workflow',
        'created_at': datetime.now().isoformat(),
    }

    # Extract workflow metadata
    workflow_info = workflow_data.get('workflow', {})
    if 'description' in workflow_info:
        project_config['description'] = workflow_info['description'].split('\n')[0]  # First line only

    if 'version' in workflow_info:
        project_config['version'] = workflow_info['version']

    # Extract directory structure from workflow
    workflow_dirs = workflow_info.get('directories', {})
    directories = {}

    # Map workflow directories to project config format
    dir_mapping = {
        'agent_files': 'agent_files',
        'agent_context': 'agent_context',
        'agent_log': 'agent_log',
        'artifacts': 'artifacts',
        'docs': 'docs',
        'input': 'input',
        'package': 'package'
    }

    for config_key, workflow_key in dir_mapping.items():
        if workflow_key in workflow_dirs:
            directories[config_key] = workflow_dirs[workflow_key]

    if directories:
        project_config['directories'] = directories

    # Extract workflow file paths
    workflow_config = {}
    if 'workflow_specific' in workflow_info.get('governance', {}):
        workflow_config['governance_file'] = workflow_info['governance']['workflow_specific']

    # Set standard workflow file paths
    workflow_config.update({
        'workflow_file': 'workflow.json',
        'agents_file': 'agents.json',
        'artifacts_file': 'artifacts.json',
        'instructions_file': 'instructions.json'
    })

    project_config['workflow_config'] = workflow_config

    # Extract governance configuration
    governance_config = extract_governance_from_workflow(workflow_data)
    if governance_config:
        project_config['governance'] = governance_config

    # Extract agent configurations
    agents_data = workflow_data.get('agents', {})
    if isinstance(agents_data, list):
        agents = agents_data
    else:
        agents = agents_data.get('agents', [])
    if agents:
        agent_configs = {}
        for agent in agents:
            agent_id = agent['id']
            agent_configs[agent_id] = {
                'name': agent.get('role', agent['slug']),
                'description': agent.get('description', ''),
                'enabled': True,  # Default to enabled
                'max_iterations': 10,  # Default value
                'timeout_minutes': 30,  # Default value
                'required_artifacts': [
                    art['filename'] for art in agent.get('produces', {}).get('core', [])
                    if isinstance(art, dict) and art.get('required', False)
                ]
            }
        project_config['agents'] = agent_configs

    # Set script paths (will be resolved dynamically)
    project_config['scripts'] = {
        'workflow_cli': 'scripts/workflow',
        'project_cli': f'projects/{project_name}/workflow'
    }

    logger.info(f"Generated project config for {project_name} using {workflow_type} workflow")
    return project_config
