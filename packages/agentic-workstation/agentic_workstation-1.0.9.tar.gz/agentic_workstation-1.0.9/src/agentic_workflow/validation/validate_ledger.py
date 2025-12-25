#!/usr/bin/env python3
"""Simple validator for `extra` YAML produced by the dispatcher.

Reads YAML from stdin and validates required keys for the given --type.

Usage:
    echo "source: A01\ntarget: A02" | python3 -m scripts.validation.validate_ledger --type HANDOFF
"""
import sys
import argparse
from pathlib import Path
import yaml
from agentic_workflow.cli.utils import display_error

__all__ = ["validate_handoff", "validate_workflow_handoff", "validate_feedback", "validate_iteration"]


def validate_handoff(data):
    """Validate handoff data structure."""
    errors = []
    if not data.get('source'):
        errors.append('missing source')
    if not data.get('target'):
        errors.append('missing target')
    if not data.get('artifacts'):
        errors.append('missing artifacts')
    
    # Check workflow-aware validation if project info is available
    source = data.get('source')
    target = data.get('target')
    project = data.get('project')
    
    if source and target and project:
        workflow_errors = validate_workflow_handoff(project, source, target)
        errors.extend(workflow_errors)
    
    return errors


def validate_workflow_handoff(project_name: str, from_agent: str, to_agent: str, artifacts: list = None) -> list:
    """
    Validate that a handoff is allowed according to the workflow definition and governance rules.
    
    Args:
        project_name: Name of the project
        from_agent: Agent initiating the handoff
        to_agent: Agent receiving the handoff
        artifacts: List of artifact names being handed off
        
    Returns:
        List of validation error messages
    """
    errors = []
    artifacts = artifacts or []
    
    try:
        # Load configuration
        from agentic_workflow.core.config_service import ConfigurationService
        config_service = ConfigurationService()
        config = config_service.load_config()
        
        # Get project path
        if config.is_project_context and config.project:
            project_path = str(config.project.root_path)
        else:
            # Fallback: construct path
            from agentic_workflow.core.paths import get_projects_dir
            projects_dir = get_projects_dir(config.system)
            project_path = str(projects_dir / project_name)
        
        # Get workflow name from project config
        from agentic_workflow.core.project import get_project_workflow_name
        workflow_name = get_project_workflow_name(project_name)
        if not workflow_name:
            return ["workflow not specified in project config"]
            
        # Load workflow package
        from agentic_workflow.generation.canonical_loader import load_workflow
        wf = load_workflow(workflow_name)
        if not wf:
            return [f"workflow '{workflow_name}' not found"]
            
        # Find the source agent
        source_agent = wf.get_agent(from_agent)
        if not source_agent:
            errors.append(f"source agent '{from_agent}' not found in workflow '{workflow_name}'")
            return errors
            
        # Check if target agent exists
        target_agent = wf.get_agent(to_agent)
        if not target_agent:
            errors.append(f"target agent '{to_agent}' not found in workflow '{workflow_name}'")
            return errors
            
        # Run governance validation
        from agentic_workflow.core.governance import GovernanceEngine
        
        # Determine strictness level from project config
        strictness = 'strict' if (config.project and config.project.strict_mode) else 'moderate'
        
        # Prepare governance config
        governance_config = {
            'strictness': {'level': strictness}
        }
        
        engine = GovernanceEngine({'governance': governance_config})
        
        # Prepare data for governance validation
        data = {
            'from_agent': from_agent,
            'to_agent': to_agent,
            'artifacts': artifacts,
            'project_path': project_path,
            'project': {'name': project_name, 'workflow': workflow_name},
            'agent': {'id': from_agent}  # Source agent context
        }
        
        # Validate
        result = engine.validate('handoff', data, strictness)
        if not result.passed:
            for violation in result.violations:
                errors.append(f"Governance violation: {violation['error_message']}")
        
        return errors
        
    except Exception as e:
        return [f"validation error: {str(e)}"]


def validate_feedback(data):
    """Validate feedback data structure."""
    errors = []
    if not data.get('source'):
        errors.append('missing source')
    if not data.get('target'):
        errors.append('missing target')
    return errors


def validate_iteration(data):
    """Validate iteration data structure."""
    # iteration has loose requirements
    return []


def main():
    """Main entry point for ledger validation CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', required=True, help='Event type to validate')
    args = parser.parse_args()

    try:
        raw = sys.stdin.read()
        extra = yaml.safe_load(raw) or {}
    except Exception as e:
        display_error(f'Failed to parse YAML from stdin: {e}')
        sys.exit(2)

    etype = args.type.upper()
    errs = []
    if etype == 'HANDOFF':
        errs = validate_handoff(extra)
    elif etype == 'FEEDBACK':
        errs = validate_feedback(extra)
    elif etype == 'ITERATION':
        errs = validate_iteration(extra)
    elif etype == 'SESSION_ARCHIVE':
        errs = []
    else:
        display_error(f'Unknown type: {etype}')
        sys.exit(2)

    if errs:
        for e in errs:
            display_error(str(e))
        sys.exit(3)

    sys.exit(0)


if __name__ == '__main__':
    main()
