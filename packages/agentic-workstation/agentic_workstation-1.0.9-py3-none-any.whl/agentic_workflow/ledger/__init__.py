"""Ledger and logging operations module.

This module contains scripts for managing logs and ledgers:
- log_entry: CLI for appending log entries
- log_write: Core log writing logic
- handoff_notify: Notify handoffs between agents
- check_handoff: Verify handoff entries exist
"""

from .log_write import write_log

__all__ = ['write_log']
