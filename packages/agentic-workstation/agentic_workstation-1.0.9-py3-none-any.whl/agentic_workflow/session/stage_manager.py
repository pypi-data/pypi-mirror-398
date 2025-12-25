#!/usr/bin/env python3
"""Stage manager for implementation workflow.

This module manages workflow stage transitions for implementation projects.

Usage:
    from session.stage_manager import set_stage, get_stage
    
    # Get current stage
    stage = get_stage('myproject')
    
    # Set new stage
    result = set_stage('myproject', 'TEST_WRITE')
"""
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from agentic_workflow.generation.canonical_loader import load_workflow

# Use core modules instead of duplicated code
from agentic_workflow.core.project import load_project_meta, save_project_meta
from agentic_workflow.core.paths import get_manifests_dir, PROJECTS_DIR

logger = logging.getLogger(__name__)

__all__ = ["get_stage", "set_stage", "get_workflow_stages", "validate_transition"]


def load_workflow_config(workflow_name: str) -> Optional[Dict]:
    """Load workflow configuration from canonical JSON."""
    try:
        wf = load_workflow(workflow_name)
        return wf.metadata
    except Exception:
        return None


def get_workflow_stages(workflow_name: str) -> List[str]:
    """Get list of valid stages for a workflow."""
    config = load_workflow_config(workflow_name)
    if not config:
        return []
    
    stages = config.get('stages', [])
    return [s.get('id') for s in stages if s.get('id')]


def get_stage(project_name: str) -> Optional[str]:
    """Get current stage of a project.
    
    Args:
        project_name: Name of the project
        
    Returns:
        Current stage name or None if not found
    """
    project_wf = load_project_meta(project_name)
    if not project_wf:
        return None
    
    return project_wf.get('current_stage')


def validate_stage_transition(
    workflow_name: str,
    current_stage: str,
    target_stage: str
) -> Dict[str, Any]:
    """Validate if a stage transition is allowed.
    
    Args:
        workflow_name: Name of the workflow
        current_stage: Current stage
        target_stage: Target stage
        
    Returns:
        Dict with:
        - valid: bool
        - message: str - Reason if invalid
    """
    config = load_workflow_config(workflow_name)
    if not config:
        return {'valid': False, 'message': 'Workflow config not found'}
    
    stages = config.get('stages', [])
    stage_ids = [s.get('id') for s in stages]
    
    # Check target stage exists
    if target_stage not in stage_ids:
        return {
            'valid': False,
            'message': f"Unknown stage: {target_stage}. Valid: {', '.join(stage_ids)}"
        }
    
    # Check current stage exists
    if current_stage and current_stage not in stage_ids:
        # Current stage unknown - allow any transition
        return {'valid': True, 'message': 'Current stage unknown, allowing transition'}
    
    # Check ordering if strict_order is enabled OR if we're in governance mode
    gating = config.get('gating', {})
    enforcement = config.get('config', {}).get('enforcement', {})
    
    # Enable stage ordering validation if strict_order is true OR enforcement mode is strict
    enforce_ordering = gating.get('strict_order', False) or enforcement.get('mode') == 'strict'
    
    if enforce_ordering and current_stage:
        current_idx = stage_ids.index(current_stage)
        target_idx = stage_ids.index(target_stage)
        
        # Only allow forward progression (or same)
        if target_idx < current_idx:
            return {
                'valid': False,
                'message': f"Cannot move backward from {current_stage} to {target_stage}"
            }
        
        # Check for skipping (only allow adjacent stages or explicit permission)
        allow_skip = gating.get('allow_skip', False)
        if not allow_skip and target_idx > current_idx + 1:
            return {
                'valid': False,
                'message': f"Cannot skip stages. Next allowed: {stage_ids[current_idx + 1]}"
            }
    
    return {'valid': True, 'message': 'Transition allowed'}


def log_stage_transition(
    project_name: str,
    previous: str,
    target: str
) -> None:
    """Log stage transition to context_log."""
    project_dir = PROJECTS_DIR / project_name
    context_log = project_dir / "agent_log" / "context_log.md"
    
    if not context_log.exists():
        return
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    entry = f"""
---

### STAGE TRANSITION

- **timestamp:** {now}
- **type:** stage-transition
- **from:** {previous or 'NONE'}
- **to:** {target}

"""
    
    with open(context_log, 'a') as f:
        f.write(entry)


def set_stage(
    project_name: str,
    stage: str,
    force: bool = False
) -> Dict[str, Any]:
    """Set the current workflow stage.
    
    Args:
        project_name: Name of the project
        stage: Target stage name
        force: If True, skip validation
        
    Returns:
        Dict with:
        - success: bool
        - previous: str - Previous stage
        - error: str - Error message if failed
    """
    project_dir = PROJECTS_DIR / project_name
    
    # Check project exists
    if not project_dir.exists():
        return {
            'success': False,
            'error': f"Project '{project_name}' not found"
        }
    
    # Load project workflow info
    project_wf = load_project_meta(project_name)
    if not project_wf:
        return {
            'success': False,
            'error': "Project workflow metadata not found (project_config.json)"
        }
    
    workflow_name = project_wf.get('workflow', 'planning')
    current_stage = project_wf.get('current_stage')
    
    # Validate transition
    if not force:
        validation = validate_stage_transition(workflow_name, current_stage, stage)
        if not validation['valid']:
            return {
                'success': False,
                'error': validation['message']
            }
    
    # Update stage
    project_wf['current_stage'] = stage
    project_wf['stage_updated_at'] = datetime.now().isoformat()
    
    # Track stage history
    if 'stage_history' not in project_wf:
        project_wf['stage_history'] = []
    
    project_wf['stage_history'].append({
        'stage': stage,
        'timestamp': datetime.now().isoformat()
    })
    
    # Save
    save_project_meta(project_name, project_wf)
    
    # Log transition
    try:
        log_stage_transition(project_name, current_stage, stage)
    except Exception as e:
        logger.warning(f"Could not log stage transition: {e}")
    
    return {
        'success': True,
        'previous': current_stage,
        'current': stage
    }


def list_stages(project_name: str) -> Dict[str, Any]:
    """List all stages and current position.
    
    Args:
        project_name: Name of the project
        
    Returns:
        Dict with:
        - stages: List[Dict] - All stages with current marker
        - current: str - Current stage
        - workflow: str - Workflow name
    """
    project_wf = load_project_meta(project_name)
    if not project_wf:
        return {
            'error': "Project workflow metadata not found"
        }
    
    workflow_name = project_wf.get('workflow', 'planning')
    current_stage = project_wf.get('current_stage')
    
    config = load_workflow_config(workflow_name)
    if not config:
        return {
            'error': f"Workflow config '{workflow_name}' not found"
        }
    
    stages = config.get('stages', [])
    result_stages = []
    
    for s in stages:
        stage_id = s.get('id')
        result_stages.append({
            'id': stage_id,
            'name': s.get('name', stage_id),
            'current': stage_id == current_stage,
            'description': s.get('description', '')
        })
    
    return {
        'stages': result_stages,
        'current': current_stage,
        'workflow': workflow_name
    }


def validate_transition(project_name: str, target_stage: str) -> Dict[str, Any]:
    """Validate if a project can transition to a target stage.
    
    This method checks exit gates and stage transition rules for the project.
    
    Args:
        project_name: Name of the project
        target_stage: Target stage to validate transition to
        
    Returns:
        Dict with:
        - valid: bool
        - message: str - Reason if invalid
        - current_stage: str - Current stage of the project
        - workflow: str - Workflow name
    """
    # Load project metadata
    project_wf = load_project_meta(project_name)
    if not project_wf:
        return {
            'valid': False,
            'message': f"Project '{project_name}' metadata not found",
            'current_stage': None,
            'workflow': None
        }
    
    workflow_name = project_wf.get('workflow', 'planning')
    current_stage = project_wf.get('current_stage', 'INTAKE')
    
    # Use existing validation logic
    validation = validate_stage_transition(workflow_name, current_stage, target_stage)
    
    return {
        'valid': validation['valid'],
        'message': validation['message'],
        'current_stage': current_stage,
        'workflow': workflow_name
    }
