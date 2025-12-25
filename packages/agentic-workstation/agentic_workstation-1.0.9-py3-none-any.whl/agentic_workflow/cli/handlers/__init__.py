"""
Request Handlers for Agentic Workflow.

This package contains the domain-specific handlers that bridge the CLI/TUI
interfaces with the core Service layer.

Architecture:
- GlobalHandlers: System-wide config and setup (No project context).
- ProjectHandlers: Static project CRUD (List, Delete).
- SessionHandlers: Active lifecycle (Init, Activate, End).
- QueryHandlers: Read-only state queries (Status, Check).
- EntryHandlers: Ledger data entry (Handoff, Decision).
- WorkflowHandlers: Advanced workflow logic (Gates, Stages).
"""

from .global_handlers import GlobalHandlers
from .project_handlers import ProjectHandlers
from .artifact_handlers import ArtifactHandlers
from .session_handlers import SessionHandlers
from .query_handlers import QueryHandlers
from .entry_handlers import EntryHandlers
from .workflow_handlers import WorkflowHandlers

__all__ = [
    "GlobalHandlers",
    "ProjectHandlers",
    "ArtifactHandlers",
    "SessionHandlers",
    "QueryHandlers",
    "EntryHandlers",
    "WorkflowHandlers",
]