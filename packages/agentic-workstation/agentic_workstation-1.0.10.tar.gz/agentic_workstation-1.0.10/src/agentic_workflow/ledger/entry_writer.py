"""Unified entry writer using the new standardized format.

High-level API for writing entries to exchange_log and context_log.
Auto-generates IDs and manages both MD and YAML files.
"""
from pathlib import Path
from typing import Optional, List, Union

__all__ = [
    "write_handoff",
    "write_feedback", 
    "write_iteration",
    "write_session",
    "write_decision",
    "write_assumption",
    "write_blocker"
]

from agentic_workflow.ledger.id_generator import generate_entry_id
from agentic_workflow.ledger.section_ops import (
    insert_entry_to_section, 
    update_metadata, 
    ensure_yaml_sidecar,
    append_to_yaml_sidecar,
    get_timestamp
)
from agentic_workflow.ledger.entry_builders import (
    build_handoff_entry,
    build_feedback_entry,
    build_iteration_entry,
    build_session_entry,
    build_decision_entry,
    build_assumption_entry,
    build_blocker_entry,
)
from agentic_workflow.core.paths import PROJECTS_DIR


def _resolve_project_dir(project_name: str, project_root: Optional[Union[str, Path]] = None) -> Path:
    """Resolve project directory with optional override and ensure log folders exist."""
    base_dir = Path(project_root) if project_root else PROJECTS_DIR / project_name
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "agent_log").mkdir(parents=True, exist_ok=True)
    return base_dir


def _get_log_paths(project_dir: Path, log_type: str):
    """Get MD and YAML paths for a log type."""
    if log_type == "exchange":
        md_path = project_dir / "agent_log" / "exchange_log.md"
    elif log_type == "context":
        md_path = project_dir / "agent_log" / "context_log.md"
    else:
        raise ValueError(f"Unknown log type: {log_type}")
    
    yaml_path = md_path.with_suffix('.yaml')
    return md_path, yaml_path


def write_handoff(project_name: str, from_agent: str, to_agent: str,
                  artifacts: Optional[List[str]] = None, notes: Optional[str] = None,
                  status: str = "pending", project_root: Optional[Union[str, Path]] = None) -> tuple[str, str]:
    """Write a handoff entry to exchange_log.
    
    Returns:
        Tuple of (entry_id, md_path)
    """
    project_dir = _resolve_project_dir(project_name, project_root)
    
    md_path, yaml_path = _get_log_paths(project_dir, "exchange")
    
    # Generate ID
    entry_id = generate_entry_id(project_dir, "exchange_log.md", "HANDOFF")
    
    # Build entry
    md_content, yaml_entry = build_handoff_entry(
        entry_id, from_agent, to_agent, artifacts, notes, status
    )
    
    # Insert to MD
    success = insert_entry_to_section(md_path, "HANDOFFS", "HANDOFF", entry_id, md_content)
    if not success:
        raise RuntimeError(f"Failed to insert handoff to {md_path}")
    
    # Update YAML
    ensure_yaml_sidecar(md_path)
    append_to_yaml_sidecar(yaml_path, "handoffs", yaml_entry)
    update_metadata(md_path, {'last_updated': get_timestamp()})
    
    return entry_id, str(md_path)


def write_feedback(project_name: str, reporter: str, target: str,
                   severity: str, summary: str,
                   status: str = "open", project_root: Optional[Union[str, Path]] = None) -> tuple[str, str]:
    """Write a feedback entry to exchange_log.
    
    Returns:
        Tuple of (entry_id, md_path)
    """
    project_dir = _resolve_project_dir(project_name, project_root)
    
    md_path, yaml_path = _get_log_paths(project_dir, "exchange")
    
    entry_id = generate_entry_id(project_dir, "exchange_log.md", "FEEDBACK")
    md_content, yaml_entry = build_feedback_entry(
        entry_id, reporter, target, severity, summary, status
    )
    
    success = insert_entry_to_section(md_path, "FEEDBACK", "FEEDBACK", entry_id, md_content)
    if not success:
        raise RuntimeError(f"Failed to insert feedback to {md_path}")
    
    ensure_yaml_sidecar(md_path)
    append_to_yaml_sidecar(yaml_path, "feedback", yaml_entry)
    update_metadata(md_path, {'last_updated': get_timestamp()})
    
    return entry_id, str(md_path)


def write_iteration(project_name: str, trigger: str, impacted_agents: Optional[List[str]],
                    version_bump: Optional[str] = None, description: Optional[str] = None,
                    project_root: Optional[Union[str, Path]] = None) -> tuple[str, str]:
    """Write an iteration entry to exchange_log.
    
    Returns:
        Tuple of (entry_id, md_path)
    """
    project_dir = _resolve_project_dir(project_name, project_root)
    
    md_path, yaml_path = _get_log_paths(project_dir, "exchange")
    
    entry_id = generate_entry_id(project_dir, "exchange_log.md", "ITERATION")
    md_content, yaml_entry = build_iteration_entry(
        entry_id, trigger, impacted_agents, version_bump, description
    )
    
    success = insert_entry_to_section(md_path, "ITERATIONS", "ITERATION", entry_id, md_content)
    if not success:
        raise RuntimeError(f"Failed to insert iteration to {md_path}")
    
    ensure_yaml_sidecar(md_path)
    append_to_yaml_sidecar(yaml_path, "iterations", yaml_entry)
    update_metadata(md_path, {'last_updated': get_timestamp()})
    
    return entry_id, str(md_path)


def write_session(project_name: str, agent_id: str, agent_role: str,
                  status: str = "active", summary: Optional[str] = None,
                  artifacts: Optional[List[str]] = None,
                  project_root: Optional[Union[str, Path]] = None) -> tuple[str, str]:
    """Write a session entry to context_log.
    
    Returns:
        Tuple of (entry_id, md_path)
    """
    project_dir = _resolve_project_dir(project_name, project_root)
    
    md_path, yaml_path = _get_log_paths(project_dir, "context")
    
    entry_id = generate_entry_id(project_dir, "context_log.md", "SESSION")
    md_content, yaml_entry = build_session_entry(
        entry_id, agent_id, agent_role, status, summary, artifacts
    )
    
    success = insert_entry_to_section(md_path, "SESSIONS", "SESSION", entry_id, md_content)
    if not success:
        raise RuntimeError(f"Failed to insert session to {md_path}")
    
    ensure_yaml_sidecar(md_path)
    append_to_yaml_sidecar(yaml_path, "sessions", yaml_entry)
    update_metadata(md_path, {'last_updated': get_timestamp()})
    
    return entry_id, str(md_path)


def write_decision(project_name: str, agent: str, title: str,
                   rationale: str, impacts: Optional[str] = None,
                   scope: str = "global", project_root: Optional[Union[str, Path]] = None) -> tuple[str, str]:
    """Write a decision entry to context_log.
    
    Returns:
        Tuple of (entry_id, md_path)
    """
    project_dir = _resolve_project_dir(project_name, project_root)
    
    md_path, yaml_path = _get_log_paths(project_dir, "context")
    
    entry_id = generate_entry_id(project_dir, "context_log.md", "DECISION")
    md_content, yaml_entry = build_decision_entry(
        entry_id, agent, title, rationale, impacts, scope
    )
    
    success = insert_entry_to_section(md_path, "DECISIONS", "DECISION", entry_id, md_content)
    if not success:
        raise RuntimeError(f"Failed to insert decision to {md_path}")
    
    ensure_yaml_sidecar(md_path)
    append_to_yaml_sidecar(yaml_path, "decisions", yaml_entry)
    update_metadata(md_path, {'last_updated': get_timestamp()})
    
    return entry_id, str(md_path)


def write_assumption(project_name: str, agent: str, assumption: str,
                     rationale: Optional[str] = None, reversal_condition: Optional[str] = None,
                     status: str = "active", project_root: Optional[Union[str, Path]] = None) -> tuple[str, str]:
    """Write an assumption entry to context_log.
    
    Returns:
        Tuple of (entry_id, md_path)
    """
    project_dir = _resolve_project_dir(project_name, project_root)
    
    md_path, yaml_path = _get_log_paths(project_dir, "context")
    
    entry_id = generate_entry_id(project_dir, "context_log.md", "ASSUMPTION")
    md_content, yaml_entry = build_assumption_entry(
        entry_id, agent, assumption, rationale, reversal_condition, status
    )
    
    success = insert_entry_to_section(md_path, "ASSUMPTIONS", "ASSUMPTION", entry_id, md_content)
    if not success:
        raise RuntimeError(f"Failed to insert assumption to {md_path}")
    
    ensure_yaml_sidecar(md_path)
    append_to_yaml_sidecar(yaml_path, "assumptions", yaml_entry)
    update_metadata(md_path, {'last_updated': get_timestamp()})
    
    return entry_id, str(md_path)


def write_blocker(project_name: str, reporter: str, title: str,
                  description: str, blocked_agents: Optional[List[str]] = None,
                  required_action: Optional[str] = None,
                  status: str = "pending", project_root: Optional[Union[str, Path]] = None) -> tuple[str, str]:
    """Write a blocker entry to context_log.
    
    Returns:
        Tuple of (entry_id, md_path)
    """
    project_dir = _resolve_project_dir(project_name, project_root)
    
    md_path, yaml_path = _get_log_paths(project_dir, "context")
    
    entry_id = generate_entry_id(project_dir, "context_log.md", "BLOCKER")
    md_content, yaml_entry = build_blocker_entry(
        entry_id, reporter, title, description, blocked_agents, required_action, status
    )
    
    success = insert_entry_to_section(md_path, "BLOCKERS", "BLOCKER", entry_id, md_content)
    if not success:
        raise RuntimeError(f"Failed to insert blocker to {md_path}")
    
    ensure_yaml_sidecar(md_path)
    append_to_yaml_sidecar(yaml_path, "blockers", yaml_entry)
    update_metadata(md_path, {'last_updated': get_timestamp()})
    
    return entry_id, str(md_path)
