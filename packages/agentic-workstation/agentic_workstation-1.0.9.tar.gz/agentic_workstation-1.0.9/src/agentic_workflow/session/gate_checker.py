#!/usr/bin/env python3
"""Gate checker for agent activation using Governance Engine.

This module provides pre-activation validation by delegating to the
GovernanceEngine for rule-based checks.
"""

from typing import Dict, Any, Optional

from ..core.schema import RuntimeConfig
from ..core.governance import GovernanceEngine, GovernanceResult
from ..core.project import load_project_meta
from ..core.paths import find_project_root
from ..generation.canonical_loader import load_workflow

__all__ = ["GateChecker"]


class GateChecker:
    """Gate checker for agent activation using Governance Engine."""

    def __init__(self, config: RuntimeConfig):
        """Initialize the gate checker with configuration."""
        self.config = config
        # Convert RuntimeConfig to dict for GovernanceEngine
        config_dict = config.model_dump() if hasattr(config, 'model_dump') else config.__dict__
        self.governance_engine = GovernanceEngine(config_dict)

    def check_gate(self, project_name: str, agent_id: Optional[str]) -> GovernanceResult:
        """Check if agent activation is allowed.
        
        Args:
            project_name: Name of the project
            agent_id: Agent ID to check, or None for project-level check
            
        Returns:
            GovernanceResult with pass/fail status and reasons
        """
        # Gather context data
        project_data = self._gather_project_context(project_name)
        agent_data = self._gather_agent_context(project_name, agent_id)
        stage_data = self._gather_stage_context(project_name)
        
        # Build payload for governance engine
        payload = {
            "project": project_data,
            "agent": agent_data,
            "stage": stage_data
        }
        
        # Delegate to governance engine
        return self.governance_engine.validate("activation", payload)

    def _gather_project_context(self, project_name: str) -> Dict[str, Any]:
        """Gather project-level context data."""
        project_meta = load_project_meta(project_name) or {}
        project_path = find_project_root()
        
        return {
            "name": project_name,
            "path": str(project_path) if project_path else "",
            "workflow": project_meta.get("workflow", "planning"),
            "current_stage": project_meta.get("current_stage", "INTAKE"),
            "strict_mode": project_meta.get("strict_mode", True)
        }

    def _gather_agent_context(self, project_name: str, agent_id: Optional[str]) -> Dict[str, Any]:
        """Gather agent-specific context data."""
        project_meta = load_project_meta(project_name) or {}
        workflow_name = project_meta.get("workflow", "planning")
        
        if agent_id is None:
            agent = {}
        else:
            try:
                workflow_data = load_workflow(workflow_name)
                agents = workflow_data.get("agents", [])
                agent = next((a for a in agents if a.get("id") == agent_id), {})
            except Exception:
                agent = {}
        
        return {
            "id": agent_id,
            "role": agent.get("role", ""),
            "type": agent.get("type", "core"),
            "stage": agent.get("stage", ""),
            "consumes_core": agent.get("consumes_core", []),
            "produces": agent.get("produces", [])
        }

    def _gather_stage_context(self, project_name: str) -> Dict[str, Any]:
        """Gather current stage context data."""
        project_meta = load_project_meta(project_name) or {}
        workflow_name = project_meta.get("workflow", "planning")
        current_stage = project_meta.get("current_stage", "INTAKE")
        
        try:
            workflow_data = load_workflow(workflow_name)
            stages = workflow_data.get("stages", [])
            stage = next((s for s in stages if s.get("id") == current_stage), {})
        except Exception:
            stage = {}
        
        return {
            "current": current_stage,
            "description": stage.get("description", ""),
            "agents": stage.get("agents", [])
        }
