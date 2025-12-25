#!/usr/bin/env python3
"""Planning project sync for implementation workflow.

This module syncs artifacts from a linked planning project to the
implementation project's input/planning_artifacts directory.

Usage:
    from session.sync_planning import sync_from_planning
    
    result = sync_from_planning('myproject', dry_run=False)
"""
import sys
import shutil
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from agentic_workflow.core.project import load_project_meta, save_project_meta
from agentic_workflow.core.paths import PROJECTS_DIR

logger = logging.getLogger(__name__)


__all__ = ["sync_from_planning"]


def get_input_artifacts(workflow_name: str) -> List[Dict]:
    """Get list of input artifacts from workflow configuration."""
    from ..generation.canonical_loader import load_workflow
    wf = load_workflow(workflow_name)
    # Assume wf.artifacts contains input artifacts
    return wf.artifacts


def file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file."""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def find_artifact_source(
    planning_project_dir: Path,
    artifact_id: str
) -> Optional[Path]:
    """Find the source file for an artifact in planning project.
    
    Searches common locations:
    - package/
    - artifacts/
    - agent_context/
    """
    search_locations = [
        planning_project_dir / "package",
        planning_project_dir / "artifacts",
        planning_project_dir / "agent_context",
    ]
    
    # Also search subdirectories
    for loc in search_locations:
        if not loc.exists():
            continue
        
        # Direct match
        direct = loc / f"{artifact_id}.md"
        if direct.exists():
            return direct
        
        # Search subdirectories
        for subdir in loc.iterdir():
            if subdir.is_dir():
                match = subdir / f"{artifact_id}.md"
                if match.exists():
                    return match
    
    return None


def sync_from_planning(
    project_name: str,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Sync artifacts from linked planning project.
    
    Args:
        project_name: Name of the implementation project
        dry_run: If True, preview without making changes
        
    Returns:
        Dict with:
        - success: bool
        - planning_project: str - Name of planning project
        - file_count: int - Number of files synced
        - changed_files: List[str] - Files that changed
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
    
    # Check if this is an implementation workflow
    if workflow_name != 'implementation':
        return {
            'success': False,
            'error': f"Sync only applies to implementation workflow (current: {workflow_name})"
        }
    
    # Get linked planning project
    linked_project = project_wf.get('linked_planning_project')
    if not linked_project:
        return {
            'success': False,
            'error': "No linked planning project configured in project_config.json"
        }
    
    planning_project_dir = PROJECTS_DIR / linked_project
    if not planning_project_dir.exists():
        return {
            'success': False,
            'error': f"Linked planning project '{linked_project}' not found"
        }
    
    # Get input artifacts list
    input_artifacts = get_input_artifacts(workflow_name)
    if not input_artifacts:
        return {
            'success': True,
            'planning_project': linked_project,
            'file_count': 0,
            'changed_files': [],
            'message': "No input artifacts defined in workflow"
        }
    
    # Create target directory
    target_dir = project_dir / "input" / "planning_artifacts"
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
    
    # Sync each artifact
    synced_files = []
    changed_files = []
    
    for artifact in input_artifacts:
        artifact_id = artifact.get('id')
        if not artifact_id:
            continue
        
        # Find source
        source_path = find_artifact_source(planning_project_dir, artifact_id)
        if not source_path:
            logger.warning(f"Artifact '{artifact_id}' not found in planning project")
            continue
        
        target_path = target_dir / f"{artifact_id}.md"
        
        # Check if file changed
        is_changed = False
        if target_path.exists():
            if file_hash(source_path) != file_hash(target_path):
                is_changed = True
        else:
            is_changed = True
        
        if is_changed:
            changed_files.append(artifact_id)
        
        if not dry_run:
            shutil.copy2(source_path, target_path)
            synced_files.append(artifact_id)
        else:
            synced_files.append(artifact_id)
    
    # Update sync timestamp
    if not dry_run:
        project_wf['last_planning_sync'] = datetime.now().isoformat()
        save_project_meta(project_name, project_wf)
    
    return {
        'success': True,
        'planning_project': linked_project,
        'file_count': len(synced_files),
        'synced_files': synced_files,
        'changed_files': changed_files,
        'dry_run': dry_run
    }
