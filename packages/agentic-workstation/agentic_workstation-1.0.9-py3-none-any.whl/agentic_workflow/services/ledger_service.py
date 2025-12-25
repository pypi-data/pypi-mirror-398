"""
Ledger service for Agentic Workflow Platform.

This service handles ledger operations like handoffs, decisions, etc.
"""

from typing import Dict, Any, Optional, List
import logging

from ..ledger.entry_reader import get_project_summary, get_active_session, get_handoffs, get_pending_handoffs, get_decisions, get_active_blockers
from ..ledger.entry_writer import write_handoff, write_decision, write_feedback, write_blocker, write_iteration, write_assumption

logger = logging.getLogger(__name__)

__all__ = ["LedgerService"]


class LedgerService:
    """Service for ledger operations."""

    def __init__(self):
        """Initialize the LedgerService."""
        pass

    def record_handoff(self, project_name: str, from_agent: str, to_agent: str,
                      artifacts: Optional[List[str]] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """Record an agent handoff."""
        try:
            entry_id, md_path = write_handoff(
                project_name=project_name,
                from_agent=from_agent,
                to_agent=to_agent,
                artifacts=artifacts,
                notes=notes
            )
            return {
                'entry_id': entry_id,
                'md_path': md_path,
                'status': 'recorded'
            }
        except Exception as e:
            logger.error(f"Failed to record handoff: {e}")
            raise

    def record_decision(self, project_name: str, title: str, rationale: str,
                       agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Record a decision."""
        try:
            entry_id, md_path = write_decision(
                project_name=project_name,
                agent=agent_id,
                title=title,
                rationale=rationale
            )
            return {
                'entry_id': entry_id,
                'md_path': md_path,
                'status': 'recorded'
            }
        except Exception as e:
            logger.error(f"Failed to record decision: {e}")
            raise

    def record_feedback(self, project_name: str, reporter: str, target: str,
                       severity: str, summary: str, status: str = 'open') -> Dict[str, Any]:
        """Record feedback."""
        try:
            entry_id, md_path = write_feedback(
                project_name=project_name,
                reporter=reporter,
                target=target,
                severity=severity,
                summary=summary,
                status=status
            )
            return {
                'entry_id': entry_id,
                'md_path': md_path,
                'status': 'recorded'
            }
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")
            raise

    def record_blocker(self, project_name: str, reporter: str, title: str,
                      description: str, blocked_agents: Optional[List[str]] = None,
                      status: str = 'pending') -> Dict[str, Any]:
        """Record a blocker."""
        try:
            entry_id, md_path = write_blocker(
                project_name=project_name,
                reporter=reporter,
                title=title,
                description=description,
                blocked_agents=blocked_agents,
                status=status
            )
            return {
                'entry_id': entry_id,
                'md_path': md_path,
                'status': 'recorded'
            }
        except Exception as e:
            logger.error(f"Failed to record blocker: {e}")
            raise

    def record_iteration(self, project_name: str, trigger: str,
                        impacted_agents: List[str], description: str,
                        version_bump: str = 'patch') -> Dict[str, Any]:
        """Record an iteration."""
        try:
            entry_id, md_path = write_iteration(
                project_name=project_name,
                trigger=trigger,
                impacted_agents=impacted_agents,
                version_bump=version_bump,
                description=description
            )
            return {
                'entry_id': entry_id,
                'md_path': md_path,
                'status': 'recorded'
            }
        except Exception as e:
            logger.error(f"Failed to record iteration: {e}")
            raise

    def record_assumption(self, project_name: str, agent_id: str,
                         assumption: str, rationale: str,
                         status: str = 'active') -> Dict[str, Any]:
        """Record an assumption."""
        try:
            entry_id, md_path = write_assumption(
                project_name=project_name,
                agent=agent_id,
                assumption=assumption,
                rationale=rationale,
                status=status
            )
            return {
                'entry_id': entry_id,
                'md_path': md_path,
                'status': 'recorded'
            }
        except Exception as e:
            logger.error(f"Failed to record assumption: {e}")
            raise

    def get_status(self, project_name: str) -> Dict[str, Any]:
        """Get project status."""
        try:
            # Get project summary from logs
            summary = get_project_summary(project_name)
            
            # Check for active session
            active_session = get_active_session(project_name)
            active_agents = 1 if active_session else 0
            
            # Get total handoffs (completed ones)
            all_handoffs = get_handoffs(project_name)
            completed_handoffs = len([h for h in all_handoffs if h.get('status') == 'completed'])
            
            # Determine last activity
            last_activity = "No recent activity"
            if active_session:
                last_activity = f"Agent {active_session.get('agent_id', 'Unknown')} active"
            elif all_handoffs:
                last_handoff = all_handoffs[-1]  # Most recent
                last_activity = f"Last handoff: {last_handoff.get('from_agent', '?')} → {last_handoff.get('to_agent', '?')}"
            
            return {
                "active_agents": active_agents,
                "completed_handoffs": completed_handoffs,
                "open_blockers": summary.get('active_blockers', 0),
                "last_activity": last_activity
            }
        except Exception as e:
            logger.error(f"Failed to get status for project '{project_name}': {e}")
            # Return basic status on error
            return {
                "active_agents": 0,
                "completed_handoffs": 0,
                "open_blockers": 0,
                "last_activity": "Status unavailable"
            }

    def get_latest_handoff(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get the most recent handoff for a project."""
        try:
            handoffs = get_handoffs(project_name, limit=1)
            return handoffs[0] if handoffs else None
        except Exception as e:
            logger.error(f"Failed to get latest handoff for project '{project_name}': {e}")
            return None

    def get_pending_handoffs(self, project_name: str, to_agent: str = None) -> List[Dict[str, Any]]:
        """Get pending handoffs for a project, optionally filtered by target agent."""
        try:
            return get_pending_handoffs(project_name, to_agent)
        except Exception as e:
            logger.error(f"Failed to get pending handoffs for project '{project_name}': {e}")
            return []

    def get_active_blockers(self, project_name: str, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active blockers for a project, optionally filtered by agent."""
        try:
            return get_active_blockers(project_name, agent_id)
        except Exception as e:
            logger.error(f"Failed to get active blockers for project '{project_name}': {e}")
            return []

    def get_active_session(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get the active session for a project."""
        try:
            return get_active_session(project_name)
        except Exception as e:
            logger.error(f"Failed to get active session for project '{project_name}': {e}")
            return None

    def get_recent_activity(self, project_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent activity (handoffs and decisions) for a project.
        
        Args:
            project_name: Name of the project
            limit: Maximum number of activities to return
            
        Returns:
            List of recent activities sorted by timestamp (descending)
        """
        try:
            # Get recent handoffs and decisions
            handoffs = get_handoffs(project_name)
            decisions = get_decisions(project_name)
            
            # Add type field and prepare for merging
            activities = []
            
            for handoff in handoffs:
                activities.append({
                    'type': 'handoff',
                    'timestamp': handoff.get('timestamp', ''),
                    'summary': f"{handoff.get('from_agent', '?')} → {handoff.get('to_agent', '?')}",
                    'details': handoff
                })
            
            for decision in decisions:
                activities.append({
                    'type': 'decision',
                    'timestamp': decision.get('timestamp', ''),
                    'summary': decision.get('title', 'Untitled Decision'),
                    'details': decision
                })
            
            # Sort by timestamp descending (most recent first)
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Return top limit items
            return activities[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent activity for project '{project_name}': {e}")
            return []