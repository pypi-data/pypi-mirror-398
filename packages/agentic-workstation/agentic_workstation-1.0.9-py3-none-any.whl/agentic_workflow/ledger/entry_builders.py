"""Entry builders for standardized markdown entries.

Generates properly formatted markdown entries with markers for:
- Handoffs, Feedback, Iterations (exchange_log)
- Sessions, Decisions, Assumptions, Blockers (context_log)
- Tasks, Local Decisions, Local Assumptions (agent context)
"""
import datetime
from datetime import timezone
from typing import Optional, List, Dict, Any, Tuple

__all__ = [
    "get_timestamp",
    "build_handoff_entry",
    "build_feedback_entry", 
    "build_iteration_entry",
    "build_session_entry",
    "build_decision_entry",
    "build_assumption_entry",
    "build_blocker_entry",
    "build_task_entry"
]


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_handoff_entry(entry_id: str, from_agent: str, to_agent: str, 
                        artifacts: Optional[List[str]] = None, notes: Optional[str] = None,
                        status: str = "pending") -> Tuple[str, Dict[str, Any]]:
    """Build a handoff entry for exchange_log.
    
    Returns:
        Tuple of (markdown_content, yaml_dict)
    """
    timestamp = get_timestamp()
    artifacts = artifacts or []
    artifacts_md = "\n".join([f"- `{a}`" for a in artifacts]) if artifacts else "- (none)"
    
    md = f"""### {entry_id} — {from_agent} → {to_agent}

| Field | Value |
|-------|-------|
| **Timestamp** | {timestamp} |
| **From Agent** | {from_agent} |
| **To Agent** | {to_agent} |
| **Status** | {'⏳ pending' if status == 'pending' else '✅ accepted'} |

**Artifacts Included:**
{artifacts_md}

**Handoff Notes:**
{notes or '(none provided)'}

**Acceptance Notes:**
(pending acceptance)"""

    yaml_entry = {
        'id': entry_id,
        'timestamp': timestamp,
        'from_agent': from_agent,
        'to_agent': to_agent,
        'status': status,
        'artifacts': artifacts,
        'notes': notes,
    }
    
    return md, yaml_entry


def build_feedback_entry(entry_id: str, reporter: str, target: str,
                         severity: str, summary: str,
                         status: str = "open") -> Tuple[str, Dict[str, Any]]:
    """Build a feedback entry for exchange_log.
    
    Returns:
        Tuple of (markdown_content, yaml_dict)
    """
    timestamp = get_timestamp()
    
    severity_emoji = {
        'low': '🟢 low',
        'medium': '🟡 medium', 
        'high': '🔴 high',
        'critical': '🚨 critical',
    }.get(severity.lower(), severity)
    
    status_emoji = {
        'open': '🔵 open',
        'resolved': '✅ resolved',
        'wontfix': '⚪ wontfix',
    }.get(status.lower(), status)
    
    md = f"""### {entry_id} — {summary[:40]}{'...' if len(summary) > 40 else ''}

| Field | Value |
|-------|-------|
| **Timestamp** | {timestamp} |
| **Reporter** | {reporter} |
| **Target** | {target} |
| **Severity** | {severity_emoji} |
| **Status** | {status_emoji} |

**Summary:**
{summary}

**Resolution:**
(pending)"""

    yaml_entry = {
        'id': entry_id,
        'timestamp': timestamp,
        'reporter': reporter,
        'target': target,
        'severity': severity,
        'status': status,
        'summary': summary,
    }
    
    return md, yaml_entry


def build_iteration_entry(entry_id: str, trigger: str, impacted_agents: Optional[List[str]],
                          version_bump: Optional[str] = None, description: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """Build an iteration entry for exchange_log.
    
    Returns:
        Tuple of (markdown_content, yaml_dict)
    """
    timestamp = get_timestamp()
    impacted = ", ".join(impacted_agents) if impacted_agents else "(none)"
    
    md = f"""### {entry_id} — {trigger[:30]}{'...' if len(trigger) > 30 else ''}

| Field | Value |
|-------|-------|
| **Timestamp** | {timestamp} |
| **Trigger** | {trigger} |
| **Impacted Agents** | {impacted} |
| **Version Bump** | {version_bump or '(none)'} |

**Description:**
{description or '(none provided)'}"""

    yaml_entry = {
        'id': entry_id,
        'timestamp': timestamp,
        'trigger': trigger,
        'impacted_agents': impacted_agents or [],
        'version_bump': version_bump,
        'description': description,
    }
    
    return md, yaml_entry


def build_session_entry(entry_id: str, agent_id: str, agent_role: str,
                        status: str = "active", summary: Optional[str] = None,
                        artifacts: Optional[List[str]] = None) -> Tuple[str, Dict[str, Any]]:
    """Build a session entry for context_log.
    
    Returns:
        Tuple of (markdown_content, yaml_dict)
    """
    timestamp = get_timestamp()
    
    status_emoji = {
        'active': '🔵 active',
        'completed': '✅ completed',
        'paused': '⏸️ paused',
    }.get(status.lower(), status)
    
    artifacts_md = "\n".join([f"- `{a}`" for a in (artifacts or [])]) if artifacts else "- (in progress)"
    
    md = f"""### {entry_id} — {agent_id} ({agent_role})

| Field | Value |
|-------|-------|
| **Timestamp** | {timestamp} |
| **Agent** | {agent_id} ({agent_role}) |
| **Duration** | {'ongoing' if status == 'active' else 'completed'} |
| **Status** | {status_emoji} |

**Summary:**
{summary or 'Session started.'}

**Artifacts Created:**
{artifacts_md}

**Key Outcomes:**
- (pending)"""

    yaml_entry = {
        'id': entry_id,
        'timestamp': timestamp,
        'agent_id': agent_id,
        'agent_role': agent_role,
        'status': status,
        'duration_minutes': None,
        'summary': summary,
        'artifacts': artifacts or [],
    }
    
    return md, yaml_entry


def build_decision_entry(entry_id: str, agent: str, title: str,
                         rationale: str, impacts: Optional[str] = None,
                         scope: str = "global") -> Tuple[str, Dict[str, Any]]:
    """Build a decision entry for context_log or agent context.
    
    Returns:
        Tuple of (markdown_content, yaml_dict)
    """
    timestamp = get_timestamp()
    
    md = f"""### {entry_id} — {title}

| Field | Value |
|-------|-------|
| **Timestamp** | {timestamp} |
| **Agent** | {agent} |
| **Scope** | {scope} |

**Decision:**
{title}

**Rationale:**
{rationale}

**Impacts:**
{impacts or '(none specified)'}"""

    yaml_entry = {
        'id': entry_id,
        'timestamp': timestamp,
        'agent': agent,
        'scope': scope,
        'title': title,
        'rationale': rationale,
        'impacts': impacts,
    }
    
    return md, yaml_entry


def build_assumption_entry(entry_id: str, agent: str, assumption: str,
                           rationale: Optional[str] = None, reversal_condition: Optional[str] = None,
                           status: str = "active") -> Tuple[str, Dict[str, Any]]:
    """Build an assumption entry for context_log or agent context.
    
    Returns:
        Tuple of (markdown_content, yaml_dict)
    """
    timestamp = get_timestamp()
    
    status_emoji = {
        'active': '⚪ active',
        'validated': '✅ validated',
        'invalidated': '❌ invalidated',
    }.get(status.lower(), status)
    
    md = f"""### {entry_id} — {assumption[:40]}{'...' if len(assumption) > 40 else ''}

| Field | Value |
|-------|-------|
| **Timestamp** | {timestamp} |
| **Agent** | {agent} |
| **Status** | {status_emoji} |

**Assumption:**
{assumption}

**Rationale:**
{rationale or '(none provided)'}

**Reversal Condition:**
{reversal_condition or '(none specified)'}"""

    yaml_entry = {
        'id': entry_id,
        'timestamp': timestamp,
        'agent': agent,
        'status': status,
        'assumption': assumption,
        'rationale': rationale,
        'reversal_condition': reversal_condition,
    }
    
    return md, yaml_entry


def build_blocker_entry(entry_id: str, reporter: str, title: str,
                        description: str, blocked_agents: Optional[List[str]] = None,
                        required_action: Optional[str] = None,
                        status: str = "pending") -> Tuple[str, Dict[str, Any]]:
    """Build a blocker entry for context_log.
    
    Returns:
        Tuple of (markdown_content, yaml_dict)
    """
    timestamp = get_timestamp()
    
    status_emoji = {
        'pending': '🟡 pending',
        'resolved': '✅ resolved',
        'escalated': '🔴 escalated',
    }.get(status.lower(), status)
    
    blocked = ", ".join(blocked_agents) if blocked_agents else "(none)"
    
    md = f"""### {entry_id} — {title}

| Field | Value |
|-------|-------|
| **Timestamp** | {timestamp} |
| **Reporter** | {reporter} |
| **Blocked Agents** | {blocked} |
| **Status** | {status_emoji} |

**Description:**
{description}

**Required Action:**
{required_action or '(none specified)'}

**Impact:**
{f'Agents {blocked} cannot proceed.' if blocked_agents else '(no agents blocked)'}"""

    yaml_entry = {
        'id': entry_id,
        'timestamp': timestamp,
        'reporter': reporter,
        'title': title,
        'description': description,
        'blocked_agents': blocked_agents or [],
        'required_action': required_action,
        'status': status,
    }
    
    return md, yaml_entry


def build_task_entry(entry_id: str, title: str, status: str = "active",
                     output: Optional[str] = None, notes: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """Build a task entry for agent context.
    
    Returns:
        Tuple of (markdown_content, yaml_dict)
    """
    timestamp = get_timestamp()
    
    checkbox = "[x]" if status in ("completed", "done") else "[ ]"
    
    md = f"""- {checkbox} **{entry_id}** — {title} ({timestamp})
  - Output: {output or '(pending)'}
  - Notes: {notes or '(none)'}"""

    yaml_entry = {
        'id': entry_id,
        'timestamp': timestamp,
        'title': title,
        'status': status,
        'output': output,
        'notes': notes,
    }
    
    return md, yaml_entry
