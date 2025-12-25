"""
Query command handlers for Agentic Workflow CLI.

This module contains handlers for query-related commands like status, check-handoff, etc.
Extracted from the monolithic workflow.py for better maintainability.

Design Decision: Handlers accept keyword arguments directly instead of argparse.Namespace.
This allows the handlers to be used both from CLI (via Click) and programmatically (from services).
Focus: Read-only status and state queries.
"""

from typing import Optional, List, TypedDict
from typing import Literal
import logging
from pathlib import Path

from agentic_workflow.core.exceptions import handle_error, validate_required
from agentic_workflow.services import LedgerService, ProjectService
from ..utils import (
    display_action_result,
    display_error,
    display_info,
    display_status_panel,
    display_warning,
    shorten_path,
)
from ..ui_utils import format_output

logger = logging.getLogger(__name__)

__all__ = ["QueryHandlers"]


class InventoryEntry(TypedDict):
    """Describe a single project root entry for UI inventory rendering."""
    name: str
    type: Literal["dir", "file"]
    count: int


class ProjectInventory(TypedDict):
    """Collection of project root entries formatted for UI consumption."""
    entries: List[InventoryEntry]


class QueryHandlers:
    """Handlers for query-related CLI commands."""

    def __init__(self):
        """Initialize the QueryHandlers with required services."""
        self.ledger_service = LedgerService()
        self.project_service = ProjectService()

    # --- TUI-friendly helpers (data only, no display) ---
    def get_active_session(self, project: str) -> dict:
        """Return active session data for a project without rendering."""
        return self.ledger_service.get_active_session(project) or {}

    def get_dashboard_data(self, project: str) -> dict:
        """Collect dashboard-ready data (status, session, activity)."""
        status_result = {}
        session_context = {"active_agent": None, "last_action": "No recent activity"}
        recent_activity = []

        status_data = self.project_service.get_project_status(project)
        if status_data.get("status") == "found":
            status_result = status_data.get("config", {})

        session_data = self.ledger_service.get_active_session(project) or {}
        session_context = {
            "active_agent": session_data.get("agent_id"),
            "last_action": session_data.get("last_action", "No recent activity"),
        }

        recent_activity = self.ledger_service.get_recent_activity(project, limit=5) or []

        return {
            "status": status_result,
            "session_context": session_context,
            "recent_activity": recent_activity,
        }

    def get_project_inventory(self, project_path: Path, include_hidden: bool = False) -> ProjectInventory:
        """Return project root inventory for UI rendering with dirs first and counts included."""
        entries: List[InventoryEntry] = []
        if not project_path or not Path(project_path).exists():
            return {"entries": entries}

        for item in Path(project_path).iterdir():
            if not include_hidden and item.name.startswith('.'):
                continue

            if item.is_dir():
                count = sum(1 for _ in item.rglob('*'))
                entries.append({"name": f"{item.name}/", "type": "dir", "count": count})
            else:
                entries.append({"name": item.name, "type": "file", "count": 0})

        entries.sort(key=lambda e: (0 if e["type"] == "dir" else 1, e["name"].lower()))
        return {"entries": entries}

    def handle_status(
        self,
        project: Optional[str] = None
    ) -> None:
        """
        Handle smart status command.
        
        Logic:
        1. If project arg provided -> Show that project's status.
        2. If in project context -> Show current project's status.
        3. If global context -> Show 'Not in project' or System Health (future).
        """
        try:
            # 1. Determine Project
            if not project:
                # We can use ProjectService to detect context safely
                status_check = self.project_service.get_project_status()
                if status_check['status'] == 'found':
                    project = status_check['name']
                else:
                    display_error("Not in a project directory")
                    display_info(f"Current location: {shorten_path(str(Path.cwd()))}")
                    display_info("Use 'agentic init <name>' to create a new project")
                    return

            logger.info(f"Getting status for project '{project}'")

            # 2. Get Ledger Status (The "Active" state)
            ledger_status = self.ledger_service.get_status(project)
            
            # 3. Get Config Status (The "Static" state)
            config_status = self.project_service.get_project_status(project)

            # Combine or prioritize (Displaying Ledger Status in the panel)
            display_status_panel(project, ledger_status)
            
            # Optionally show warnings from config status
            if config_status.get('status') == 'found' and not config_status.get('config'):
                 display_info("[Warning] Project configuration file is missing/invalid.")

        except Exception as e:
            handle_error(e, "status retrieval", {"project": project})

    def handle_check_handoff(
        self,
        project: str,
        agent_id: str
    ) -> None:
        """Check if a handoff exists for an agent."""
        try:
            validate_required(project, "project", "check_handoff")
            validate_required(agent_id, "agent_id", "check_handoff")
            
            # Query for pending handoffs to this agent
            pending_handoffs = self.ledger_service.get_pending_handoffs(project, agent_id)
            
            if pending_handoffs:
                # Get the most recent handoff
                latest_handoff = pending_handoffs[0]  # Assuming sorted by recency
                from_agent = latest_handoff.get('from_agent', 'Unknown')
                display_action_result(
                    action=f"Handoff available from {from_agent}",
                    success=True,
                    details=[f"Target: {agent_id}", f"Status: {latest_handoff.get('status', 'pending')}"]
                )
            else:
                display_warning(f"No pending handoff found for {agent_id}")
            
        except Exception as e:
            handle_error(e, "handoff check", {"project": project, "agent_id": agent_id})
    
    def handle_list_pending(
        self,
        project: str
    ) -> None:
        """
        Handle list pending handoffs command.

        Args:
            project: Project name (required)

        Raises:
            CLIExecutionError: If listing fails
        """
        try:
            validate_required(project, "project", "list_pending")

            # Get pending handoffs
            pending_handoffs = self.ledger_service.get_pending_handoffs(project)
            
            if pending_handoffs:
                format_output(pending_handoffs, format_type='table', title=f"Pending Handoffs in '{project}'")
            else:
                display_info("No pending handoffs.")

        except Exception as e:
            handle_error(e, "pending handoffs listing", {"project": project})

    def handle_list_blockers(
        self,
        project: str
    ) -> None:
        """
        Handle list blockers command.

        Args:
            project: Project name (required)

        Raises:
            CLIExecutionError: If listing fails
        """
        try:
            validate_required(project, "project", "list_blockers")

            # Get active blockers
            active_blockers = self.ledger_service.get_active_blockers(project)
            
            if active_blockers:
                format_output(active_blockers, format_type='table', title=f"Active Blockers in '{project}'")
            else:
                display_info("No active blockers.")

        except Exception as e:
            handle_error(e, "blockers listing", {"project": project})


__all__ = ["QueryHandlers"]
