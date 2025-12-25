#!/usr/bin/env python3
"""Simple session validator for dispatcher actions.

Usage:
    python3 -m scripts.validation.validate_session --project  --action  [--agent ] [--artifact ] [--id ]
"""
import argparse
import sys
from pathlib import Path
import yaml

from agentic_workflow.cli.utils import display_error, display_success

from agentic_workflow.cli.utils import display_error, display_success, display_info

__all__ = ["validate_init", "validate_activate", "validate_populate", "validate_end", "validate_update_index", "validate_check_handoff"]


def fail(msg):
    """Exit with error message."""
    display_error(f"ERROR: {msg}")
    sys.exit(1)


def check_project_exists(proj):
    """Check if project directory exists."""
    from agentic_workflow.core.project import get_project_dir
    p = Path(get_project_dir(proj))
    if not p.exists():
        fail(f"project not found: {p}")
    return p


def validate_init(args):
    """Validate project initialization."""
    from agentic_workflow.core.project import get_project_dir
    p = Path(get_project_dir(args.project))
    if not p.exists():
        fail(f"after init, project directory missing: {p}")
    # basic structure
    for sub in ("artifacts", "agent_context", "agent_log"):
        if not (p / sub).exists():
            fail(f"missing subdir: {p/ sub}")
    display_success("init validation passed")


def validate_activate(args):
    """Validate agent activation."""
    p = check_project_exists(args.project)
    active = p / "agent_context" / "active_session.md"
    if not active.exists():
        fail(f"active_session.md missing after activate: {active}")
    display_success("activate validation passed")


def validate_populate(args):
    """Validate agent file population."""
    from agentic_workflow.core.paths import get_agent_files_dir
    af = Path(get_agent_files_dir())
    if not af.exists() or not any(af.glob("A*_*")):
        fail("agent_files not populated")
    display_success("populate validation passed")


def validate_end(args):
    """Validate session end."""
    p = check_project_exists(args.project)
    ctx = p / "agent_log" / "context_log.md"
    if not ctx.exists():
        fail(f"context_log.md missing after end: {ctx}")
    display_success("end validation passed")


def validate_update_index(args):
    """Validate index update."""
    if not args.artifact:
        fail("--artifact required for update-index validation")
    a = Path(args.artifact)
    if not a.exists():
        fail(f"artifact path does not exist: {a}")
    display_success("update-index validation passed")


def validate_check_handoff(args):
    """Validate handoff check."""
    p = check_project_exists(args.project)
    ledger = p / "agent_log" / "exchange_log.yaml"
    if not ledger.exists():
        fail(f"ledger not found: {ledger}")
    try:
        data = yaml.safe_load(ledger.read_text()) or []
    except Exception as e:
        fail(f"failed to parse ledger yaml: {e}")
    hid = args.id
    if not hid:
        fail("--id required for check-handoff validation")
    matches = [e for e in data if isinstance(e, dict) and (e.get('handoff_id')==hid or e.get('id')==hid or e.get('type')==hid)]
    if not matches:
        fail(f"no handoff matching {hid} in {ledger}")
    display_success(f"check-handoff found {len(matches)} matching entry(ies)")


def main():
    """Main entry point for session validation CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--agent")
    parser.add_argument("--artifact")
    parser.add_argument("--id")
    args = parser.parse_args()

    action = args.action
    if action == 'init':
        validate_init(args)
    elif action == 'activate':
        validate_activate(args)
    elif action == 'populate':
        validate_populate(args)
    elif action == 'end':
        validate_end(args)
    elif action == 'update-index':
        validate_update_index(args)
    elif action == 'check-handoff':
        validate_check_handoff(args)
    else:
        display_info(f"No validation rule for action: {action}")
        sys.exit(0)


if __name__ == '__main__':
    main()
