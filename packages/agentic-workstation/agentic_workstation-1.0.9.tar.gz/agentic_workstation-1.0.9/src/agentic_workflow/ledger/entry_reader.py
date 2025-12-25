"""Log reader utilities for querying entries.

Provides functions to read and filter entries from exchange_log and context_log.
Uses YAML sidecars for structured queries, with MD fallback.
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml

__all__ = [
    "get_handoffs",
    "get_handoff_by_id",
    "get_pending_handoffs",
    "get_feedback",
    "get_open_feedback",
    "get_iterations",
    "get_sessions",
    "get_active_session",
    "get_decisions",
    "get_assumptions",
    "get_active_assumptions",
    "get_blockers",
    "get_active_blockers",
    "get_project_summary",
    "get_agent_context_summary"
]

from agentic_workflow.ledger.section_ops import (
    read_section,
    read_entry,
    read_yaml_section,
    find_entry_in_yaml,
)
from agentic_workflow.core.paths import PROJECTS_DIR


def _get_projects_dir():
    """Get the actual projects directory from config."""
    try:
        from agentic_workflow.core.config_service import ConfigurationService
        config = ConfigurationService().load_config()
        return config.system.default_workspace
    except:
        # Fallback
        return PROJECTS_DIR


def _get_yaml_path(project_dir: Path, log_type: str) -> Path:
    """Get YAML path for a log type."""
    if log_type == "exchange":
        return project_dir / "agent_log" / "exchange_log.yaml"
    elif log_type == "context":
        return project_dir / "agent_log" / "context_log.yaml"
    else:
        raise ValueError(f"Unknown log type: {log_type}")


def _get_md_path(project_dir: Path, log_type: str) -> Path:
    """Get MD path for a log type."""
    if log_type == "exchange":
        return project_dir / "agent_log" / "exchange_log.md"
    elif log_type == "context":
        return project_dir / "agent_log" / "context_log.md"
    else:
        raise ValueError(f"Unknown log type: {log_type}")


# === Exchange Log Queries ===

def get_handoffs(project_name: str, status: Optional[str] = None, 
                 from_agent: Optional[str] = None, to_agent: Optional[str] = None,
                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get handoff entries from exchange_log.
    
    Args:
        project_name: Project name
        status: Filter by status ('pending', 'accepted')
        from_agent: Filter by source agent
        to_agent: Filter by target agent
        limit: Max entries to return
        
    Returns:
        List of handoff dicts
    """
    projects_dir = _get_projects_dir()
    project_dir = projects_dir / project_name
    yaml_path = _get_yaml_path(project_dir, "exchange")
    
    entries = read_yaml_section(yaml_path, "handoffs")
    
    # Apply filters
    if status:
        entries = [e for e in entries if e.get('status') == status]
    if from_agent:
        entries = [e for e in entries if e.get('from_agent') == from_agent]
    if to_agent:
        entries = [e for e in entries if e.get('to_agent') == to_agent]
    
    if limit:
        entries = entries[:limit]
    
    return entries


def get_handoff_by_id(project_name: str, handoff_id: str) -> Dict[str, Any]:
    """Get a specific handoff by ID."""
    projects_dir = _get_projects_dir()
    project_dir = projects_dir / project_name
    yaml_path = _get_yaml_path(project_dir, "exchange")
    return find_entry_in_yaml(yaml_path, "handoffs", handoff_id)


def get_pending_handoffs(project_name: str, to_agent: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get pending handoffs, optionally filtered by target agent."""
    return get_handoffs(project_name, status="pending", to_agent=to_agent)


def get_feedback(project_name: str, status: Optional[str] = None,
                 target: Optional[str] = None, severity: Optional[str] = None,
                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get feedback entries from exchange_log."""
    projects_dir = _get_projects_dir()
    project_dir = projects_dir / project_name
    yaml_path = _get_yaml_path(project_dir, "exchange")
    
    entries = read_yaml_section(yaml_path, "feedback")
    
    if status:
        entries = [e for e in entries if e.get('status') == status]
    if target:
        entries = [e for e in entries if e.get('target') == target]
    if severity:
        entries = [e for e in entries if e.get('severity') == severity]
    
    if limit:
        entries = entries[:limit]
    
    return entries


def get_open_feedback(project_name: str, target: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get open feedback tickets."""
    return get_feedback(project_name, status="open", target=target)


def get_iterations(project_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get iteration entries from exchange_log."""
    projects_dir = _get_projects_dir()
    project_dir = projects_dir / project_name
    yaml_path = _get_yaml_path(project_dir, "exchange")
    
    entries = read_yaml_section(yaml_path, "iterations")
    
    if limit:
        entries = entries[:limit]
    
    return entries


# === Context Log Queries ===

def get_sessions(project_name: str, agent_id: Optional[str] = None,
                 status: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get session entries from context_log."""
    projects_dir = _get_projects_dir()
    project_dir = projects_dir / project_name
    yaml_path = _get_yaml_path(project_dir, "context")
    
    entries = read_yaml_section(yaml_path, "sessions")
    
    if agent_id:
        entries = [e for e in entries if e.get('agent_id') == agent_id]
    if status:
        entries = [e for e in entries if e.get('status') == status]
    
    if limit:
        entries = entries[:limit]
    
    return entries


def get_active_session(project_name: str) -> Dict[str, Any]:
    """Get the current active session from active_session.md frontmatter."""
    projects_dir = _get_projects_dir()
    project_dir = projects_dir / project_name
    active_session_path = project_dir / "agent_context" / "active_session.md"
    
    if not active_session_path.exists():
        return {}
    
    content = active_session_path.read_text()
    
    # Parse frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1])
                if fm:
                    # Use simplified field names
                    agent_id = fm.get('agent_id', '')
                    agent_role = fm.get('agent_role', '')
                    if agent_id and agent_role:
                        return {
                            'agent_id': agent_id,
                            'agent_role': agent_role,
                            'status': 'active',
                        }
            except yaml.YAMLError:
                pass
    
    return {}


def get_decisions(project_name: str, agent: Optional[str] = None,
                  scope: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get decision entries from context_log."""
    projects_dir = _get_projects_dir()
    project_dir = projects_dir / project_name
    yaml_path = _get_yaml_path(project_dir, "context")
    
    entries = read_yaml_section(yaml_path, "decisions")
    
    if agent:
        entries = [e for e in entries if e.get('agent') == agent]
    if scope:
        entries = [e for e in entries if e.get('scope') == scope]
    
    if limit:
        entries = entries[:limit]
    
    return entries


def get_assumptions(project_name: str, agent: Optional[str] = None,
                    status: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get assumption entries from context_log."""
    projects_dir = _get_projects_dir()
    project_dir = projects_dir / project_name
    yaml_path = _get_yaml_path(project_dir, "context")
    
    entries = read_yaml_section(yaml_path, "assumptions")
    
    if agent:
        entries = [e for e in entries if e.get('agent') == agent]
    if status:
        entries = [e for e in entries if e.get('status') == status]
    
    if limit:
        entries = entries[:limit]
    
    return entries


def get_active_assumptions(project_name: str) -> List[Dict[str, Any]]:
    """Get all active assumptions."""
    return get_assumptions(project_name, status="active")


def get_blockers(project_name: str, status: Optional[str] = None,
                 blocked_agent: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get blocker entries from context_log."""
    projects_dir = _get_projects_dir()
    project_dir = projects_dir / project_name
    yaml_path = _get_yaml_path(project_dir, "context")
    
    entries = read_yaml_section(yaml_path, "blockers")
    
    if status:
        entries = [e for e in entries if e.get('status') == status]
    if blocked_agent:
        entries = [e for e in entries 
                   if blocked_agent in (e.get('blocked_agents') or [])]
    
    if limit:
        entries = entries[:limit]
    
    return entries


def get_active_blockers(project_name: str, agent: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get pending blockers."""
    return get_blockers(project_name, status="pending", blocked_agent=agent)


# === Summary Functions ===

def get_project_summary(project_name: str) -> Dict[str, Any]:
    """Get a summary of the project state from logs."""
    return {
        'pending_handoffs': len(get_pending_handoffs(project_name)),
        'open_feedback': len(get_open_feedback(project_name)),
        'active_session': get_active_session(project_name),
        'total_decisions': len(get_decisions(project_name)),
        'active_assumptions': len(get_active_assumptions(project_name)),
        'active_blockers': len(get_active_blockers(project_name)),
        'total_iterations': len(get_iterations(project_name)),
    }


def get_agent_context_summary(project_name: str, agent_id: str) -> Dict[str, Any]:
    """Get context relevant to a specific agent."""
    return {
        'pending_handoffs_to_me': get_pending_handoffs(project_name, to_agent=agent_id),
        'open_feedback_for_me': get_open_feedback(project_name, target=agent_id),
        'blockers_affecting_me': get_active_blockers(project_name, agent=agent_id),
        'my_sessions': get_sessions(project_name, agent_id=agent_id, limit=3),
        'my_decisions': get_decisions(project_name, agent=agent_id),
    }
