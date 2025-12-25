"""Core log writing logic for the ledger system.

Provides write_log() function for appending structured entries to both
human-readable Markdown and machine-parseable YAML ledgers.
"""
import datetime
import sys
from datetime import timezone
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

__all__ = ["write_log"]

from agentic_workflow.core.paths import PROJECTS_DIR


def _resolve_paths(project_dir: Path, log_file: str):
    """Normalize log_file path to be inside agent_log/."""
    if "agent_log" in log_file:
        md_path = project_dir / log_file
    else:
        md_path = project_dir / "agent_log" / log_file

    # YAML ledger path mirrors the md filename but with .yaml extension
    yaml_path = md_path.with_suffix('.yaml')
    return md_path, yaml_path


def _get_active_agent(project_dir: Path):
    """Extract active agent name from project_index.md."""
    index_path = project_dir / "project_index.md"
    agent_name = "Unknown"
    if index_path.exists():
        with open(index_path, "r") as f:
            for line in f:
                if "**Active Agent:**" in line:
                    agent_name = line.split("**Active Agent:**", 1)[1].strip()
                    break
    return agent_name


def write_log(project_name: str, log_file: str, entry_type: str, ref_id: str, summary: str, status: str, extra: Optional[Dict[str, Any]] = None):
    """Write a structured log entry to both MD and YAML ledgers.
    
    Args:
        project_name: Name of the project
        log_file: Log file name (e.g., 'exchange_log.md')
        entry_type: Type of entry (HANDOFF, FEEDBACK, ITERATION, etc.)
        ref_id: Reference ID for the entry
        summary: Summary text
        status: Status string
        extra: Optional dict with additional metadata
        
    Returns:
        Tuple of (md_path, yaml_path) as strings
    """
    project_dir = PROJECTS_DIR / project_name
    if not project_dir.exists():
        raise FileNotFoundError(f"Project {project_name} not found")

    md_path, yaml_path = _resolve_paths(project_dir, log_file)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    # Use timezone-aware UTC timestamps
    timestamp = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    agent_name = _get_active_agent(project_dir)
    
    # Helper to safely get from extra dict
    def _extra_get(extra_dict, primary, default=None):
        if not extra_dict:
            return default
        return extra_dict.get(primary, default)

    # Format MD row based on entry_type
    if entry_type == "HANDOFF":
        from_agent = _extra_get(extra, "source", "Unknown")
        to_agent = _extra_get(extra, "target", "Unknown")
        artifacts = _extra_get(extra, "artifacts", []) or []
        artifacts_joined = ", ".join(artifacts)
        row = f"| {ref_id} | {timestamp} | {from_agent} | {to_agent} | {artifacts_joined} | {status} |"
    elif entry_type == "FEEDBACK":
        reporter = _extra_get(extra, "source", agent_name)
        target = _extra_get(extra, "target", "Unknown")
        severity = _extra_get(extra, "severity", "UNKNOWN")
        row = f"| {ref_id} | {timestamp} | {reporter} | {target} | {severity} | {summary} | {status} |"
    elif entry_type == "ITERATION":
        trigger = _extra_get(extra, "trigger", "manual")
        impacted = _extra_get(extra, "impact_agents", []) or []
        impacted_joined = ", ".join(impacted)
        version = _extra_get(extra, "version_bump", "")
        row = f"| {ref_id} | {timestamp} | {trigger} | {impacted_joined} | {version} |"
    else:
        row = f"| {timestamp} | {agent_name} | {entry_type} | {ref_id} | {summary} | {status} |"
    
    # Insert the row into the correct section of the MD file
    section_markers = {
        "HANDOFF": "## 1. Handoff Log",
        "FEEDBACK": "## 2. Feedback Tickets",
        "ITERATION": "## 3. Iteration Cycles",
    }

    if md_path.exists():
        md_text = md_path.read_text()
        marker = section_markers.get(entry_type)
        if marker and marker in md_text:
            start = md_text.find(marker)
            next_sec = md_text.find('\n## ', start + 1)
            insert_pos = next_sec if next_sec != -1 else len(md_text)
            new_md = md_text[:insert_pos].rstrip() + "\n" + row + "\n" + md_text[insert_pos:]
            md_path.write_text(new_md)
        else:
            with open(md_path, "a") as f:
                f.write(row + "\n")
    else:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        with open(md_path, "w") as f:
            f.write(row + "\n")

    # Append to YAML ledger
    ledger = []
    if yaml_path.exists():
        try:
            with open(yaml_path, "r") as yf:
                ledger = yaml.safe_load(yf) or []
        except Exception:
            ledger = []

    # Build ledger entry based on type
    if entry_type == "HANDOFF":
        handoff_entry = {
            "type": "HANDOFF",
            "timestamp": timestamp,
            "handoff_id": ref_id,
            "source": _extra_get(extra, "source", None),
            "target": _extra_get(extra, "target", None),
            "artifacts": _extra_get(extra, "artifacts", []),
            "severity": _extra_get(extra, "severity", None),
            "priority": _extra_get(extra, "priority", None),
            "summary": summary,
            "status": status,
        }
        ledger.append(handoff_entry)
    elif entry_type == "FEEDBACK":
        feedback_entry = {
            "type": "FEEDBACK",
            "timestamp": timestamp,
            "ticket_id": ref_id,
            "source": _extra_get(extra, "source", agent_name),
            "target": _extra_get(extra, "target", None),
            "artifacts": _extra_get(extra, "artifacts", []),
            "severity": _extra_get(extra, "severity", None),
            "summary": summary,
            "status": status,
        }
        ledger.append(feedback_entry)
    elif entry_type == "ITERATION":
        iteration_entry = {
            "type": "ITERATION",
            "timestamp": timestamp,
            "iteration_id": ref_id,
            "trigger_event": _extra_get(extra, "trigger", None),
            "impacted_agents": _extra_get(extra, "impact_agents", []),
            "version_bump": _extra_get(extra, "version_bump", None),
            "artifacts": _extra_get(extra, "artifacts", []),
            "summary": summary,
            "status": status,
        }
        ledger.append(iteration_entry)
    else:
        entry = {
            "timestamp": timestamp,
            "agent": agent_name,
            "type": entry_type,
            "ref_id": ref_id,
            "summary": summary,
            "status": status,
        }
        ledger.append(entry)

    with open(yaml_path, "w") as yf:
        yaml.safe_dump(ledger, yf, sort_keys=False)

    # Rebuild a clean MD view from the YAML ledger
    # Skip rebuild for context_log.md since it contains freeform session archives
    if "context_log" not in str(md_path):
        try:
            _rebuild_md_from_ledger(yaml_path, md_path)
        except Exception:
            pass

    return str(md_path), str(yaml_path)


def _rebuild_md_from_ledger(yaml_path: Path, md_path: Path):
    """Rewrite the MD file with canonical tables generated from the YAML ledger."""
    data = []
    if yaml_path.exists():
        try:
            data = yaml.safe_load(yaml_path.read_text()) or []
        except Exception:
            data = []

    normalized = [e for e in data if isinstance(e, dict)]

    handoffs = [e for e in normalized if e.get("type") == "HANDOFF"]
    feedbacks = [e for e in normalized if e.get("type") == "FEEDBACK"]
    iterations = [e for e in normalized if e.get("type") == "ITERATION"]
    others = [e for e in normalized if e.get("type") not in ("HANDOFF", "FEEDBACK", "ITERATION")]

    lines = []
    lines.append(f"# Exchange Log: {md_path.parents[1].name}\n")
    lines.append("Purpose: Canonical record of inter-agent handoffs, feedback tickets, and iteration cycles.")
    lines.append("Governance: This file is the \"Gating Source of Truth\". Agents must check here for upstream HANDOFFs before starting work.\n")

    # Handoff table
    lines.append("## 1. Handoff Log")
    lines.append("| handoff_id | timestamp | from_agent | to_agent | artifacts_included | status |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for h in handoffs:
        raw_artifacts = h.get("artifacts") or []
        artifacts_list = [str(a).replace('\\n', '').strip() for a in raw_artifacts]
        artifacts = ", ".join(artifacts_list)
        hid = h.get('handoff_id') or h.get('ref_id') or ''
        source = h.get('source') or h.get('from') or ''
        target = h.get('target') or h.get('to') or ''
        lines.append(f"| {hid} | {h.get('timestamp')} | {source} | {target} | {artifacts} | {h.get('status')} |")

    # Feedback table
    lines.append("\n## 2. Feedback Tickets")
    lines.append("| ticket_id | timestamp | reporter_agent | target_agent | severity | summary | status |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for f in feedbacks:
        reporter = f.get('source') or f.get('reporter') or ''
        target = f.get('target') or ''
        lines.append(f"| {f.get('ticket_id')} | {f.get('timestamp')} | {reporter} | {target} | {f.get('severity')} | {f.get('summary')} | {f.get('status')} |")

    # Iteration table
    lines.append("\n## 3. Iteration Cycles")
    lines.append("| iteration_id | timestamp | trigger_event | impacted_agents | version_bump |")
    lines.append("| :--- | :--- | :--- | :--- | :--- |")
    for it in iterations:
        impacted = ", ".join(it.get('impacted_agents') or [])
        lines.append(f"| {it.get('iteration_id')} | {it.get('timestamp')} | {it.get('trigger_event')} | {impacted} | {it.get('version_bump')} |")

    # Other entries (generic)
    if others:
        lines.append("\n## Other Entries")
        for o in others:
            lines.append(f"- {o}")

    md_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    # Simple CLI for manual use
    from agentic_workflow.cli.utils import display_error, display_success, display_info
    if len(sys.argv) < 7:
        display_info("Usage: python3 -m scripts.ledger.log_write")
        sys.exit(1)
    _, project_name, log_file, entry_type, ref_id, summary, status = sys.argv[:7]
    md, yml = write_log(project_name, log_file, entry_type, ref_id, summary, status)
    display_success(f"Logged to {md} and ledger {yml}")
