#!/usr/bin/env python3
"""Generate agent files from workflow packages using Jinja2 templates.

This module provides functions to generate agent prompt files from workflow packages
using Jinja2 templates and canonical JSON data.

Functions:
- build_agent_files(): Build agent files in memory (returns dict)
- generate_agents(): Generate agent files to disk
- generate_agents_for_project(): Generate agent files for a specific project
"""
import json
import sys
from pathlib import Path
from typing import Dict, Optional, Any

__all__ = ["build_agent_files", "generate_agents", "generate_agents_for_project"]

from agentic_workflow.generation.canonical_loader import load_workflow, WorkflowError
from agentic_workflow.workflow.resolver import get_default_workflow
from agentic_workflow.utils.templating import TemplateEngine, ContextResolver
from agentic_workflow.core.paths import find_repo_root
from pathlib import Path as _Path


def get_agent_filename(agent: dict, wf) -> str:
    """Generate filename for an agent.
    
    Uses workflow.format_agent_id() to get consistent ID formatting.
    
    Args:
        agent: Agent definition dict
        wf: WorkflowPackage instance
        
    Returns:
        Filename string (e.g., "A01_Requirements Analyst.md")
    """
    agent_id = agent.get('id')
    role = agent.get('role', agent.get('slug', 'agent'))
    
    # Use workflow's ID formatter for consistent naming
    formatted_id = wf.format_agent_id(agent_id)
    
    return f"{formatted_id}_{role}.md"


def build_agent_files(workflow_name: str, project_name: str) -> Dict[str, str]:
    """Build agent files in memory without writing to disk.
    
    Args:
        workflow_name: Name of workflow package (e.g., 'planning')
        project_name: Project name for context
        
    Returns:
        Dict[str, str]: Mapping of filename to content
        
    Raises:
        WorkflowError: If workflow loading fails
    """
    wf = load_workflow(workflow_name)
    
    # Initialize templating components
    engine = TemplateEngine(workflow=workflow_name)
    resolver = ContextResolver()
    
    agent_files = {}
    for agent in wf.agents:
        agent_id = agent.get('id')
        
        # Render using new templating API
        context = resolver.get_agent_context(workflow_name, agent_id, project_name)
        content = engine.render("_base/agent_base.md.j2", context)
        
        # Generate filename
        filename = get_agent_filename(agent, wf)
        
        agent_files[filename] = content
    
    return agent_files


def generate_agents(
    workflow_name: str,
    output_dir: Optional[Path] = None,
    agent_filter: Optional[str] = None,
    project_name: str = "project",
    dry_run: bool = False
) -> Dict[str, Any]:
    """Generate agent files using Jinja2 template engine.
    
    Uses the global agent_base.md.j2 template with context from canonical JSON.
    
    Args:
        workflow_name: Name of workflow package (e.g., 'planning')
        output_dir: Output directory (default: agent_files//)
        agent_filter: Optional agent ID to filter to single agent
        project_name: Project name for context
        dry_run: If True, return content without writing
        
    Returns:
        Dict with 'success', 'generated_files', 'error' keys
    """
    try:
        # Build all agent files in memory
        all_agent_files = build_agent_files(workflow_name, project_name)
    except WorkflowError as e:
        return {"success": False, "error": str(e)}
    
    # Set default output directory
    if output_dir is None:
        output_dir = find_repo_root() / 'agent_files' / workflow_name
    
    # Filter agents if requested
    if agent_filter:
        # Load workflow to get agent list for filtering
        try:
            wf = load_workflow(workflow_name)
        except WorkflowError as e:
            return {"success": False, "error": str(e)}
        
        target = str(agent_filter).upper()
        # Use workflow's formatting helper to normalize the requested agent id
        try:
            target_id = wf.format_agent_id(target)
        except Exception:
            target_id = target

        # Get filtered agent list
        filtered_agents = [a for a in wf.agents if str(wf.format_agent_id(a.get('id', ''))).upper() == target_id.upper()]
        if not filtered_agents:
            return {"success": False, "error": f"Agent {agent_filter} not found in workflow {workflow_name}"}
        
        # Filter the files
        filtered_files = {}
        for agent in filtered_agents:
            filename = get_agent_filename(agent, wf)
            if filename in all_agent_files:
                filtered_files[filename] = all_agent_files[filename]
        
        agent_files = filtered_files
    else:
        agent_files = all_agent_files
    
    generated_files = []
    for filename, content in agent_files.items():
        if dry_run:
            generated_files.append({"filename": filename, "content": content})
        else:
            full_path = Path(output_dir) / filename
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            generated_files.append({"filename": filename, "path": str(full_path)})
            
    return {"success": True, "generated_files": generated_files}


def generate_agents_for_project(
    project_name: str,
    agent_filter: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Generate agent files for a project using its workflow.
    
    Reads workflow from project's project_config.json metadata file.
    Outputs to projects//agent_files/
    
    Args:
        project_name: Project name
        agent_filter: Optional agent ID to filter
        dry_run: If True, return content without writing
        
    Returns:
        Dict with 'success', 'generated_files', 'error' keys
    """
    project_dir = find_repo_root() / 'projects' / project_name
    
    if not project_dir.exists():
        return {"success": False, "error": f"Project {project_name} not found"}
    
    # Read project workflow from project_config.json
    meta_path = project_dir / 'project_config.json'
    if meta_path.exists():
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        workflow_name = meta.get('workflow', get_default_workflow())
    else:
        workflow_name = get_default_workflow()
    
    output_dir = project_dir / 'agent_files'
    
    return generate_agents(workflow_name, output_dir, agent_filter, project_name, dry_run)
