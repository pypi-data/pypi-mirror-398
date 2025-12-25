#!/usr/bin/env python3
"""
Canonical JSON Loader & Workflow Object Model.

This is the Single Source of Truth for loading workflow definitions.
It handles:
1. Loading raw JSON/YAML manifests from the disk.
2. Validating existence of required files (workflow, agents, artifacts).
3. Hydrating the `WorkflowPackage` object used by the rest of the system.
"""

import json
import logging
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from importlib import resources

# Configure logging for this module
logger = logging.getLogger(__name__)

# Define custom exceptions here to avoid circular imports with core.exceptions
class CanonicalLoadError(Exception):
    """Raised when canonical loading fails (missing files, bad JSON)."""
    pass

class WorkflowError(Exception):
    """Raised when workflow validation or logic fails."""
    pass

__all__ = [
    "CanonicalLoadError",
    "WorkflowError",
    "WorkflowPackage",
    "load_canonical_workflow",
    "load_workflow",                # Alias for load_canonical_workflow(return_object=True)
    "list_canonical_workflows",
    "list_workflows",
    "get_workflow_agents",
    "get_workflow_artifacts",
    "get_workflow_instructions",
    "get_default_workflow",
    "get_agents_list",
    "get_artifacts_list", 
    "get_instructions_list",
    "get_workflow_metadata",
    "build_agent_lookup",
    "build_artifact_lookup",
    "build_instruction_lookup",
    "extract_files_from_produces_consumes"
]

# =============================================================================
# WORKFLOW OBJECT MODEL
# =============================================================================

@dataclass
class WorkflowPackage:
    """
    Represents a fully loaded and validated workflow package.
    Acts as the immutable configuration object for a workflow execution.
    """
    name: str
    version: str
    path: Path
    metadata: Dict[str, Any] = field(default_factory=dict)
    agents: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    instructions: Dict[str, Any] = field(default_factory=dict)
    governance: str = ""

    @property
    def display_name(self) -> str:
        """Get the human-readable display name for this workflow."""
        return self.metadata.get("display_name", self.name.title())

    @property
    def description(self) -> str:
        """Get the workflow description."""
        return self.metadata.get("description", "")

    @property
    def pipeline_order(self) -> List[str]:
        """Get the ordered list of agent IDs in the workflow pipeline."""
        return self.metadata.get("pipeline", {}).get("order", [])

    @property
    def checkpoints(self) -> List[Dict[str, Any]]:
        """Get the workflow checkpoints configuration."""
        return self.metadata.get("checkpoints", [])

    @property
    def display_config(self) -> Dict[str, Any]:
        """Raw display configuration dictionary."""
        return self.metadata.get("display", {})

    @property
    def agent_prefix(self) -> str:
        """Agent ID prefix (e.g., 'A', 'I'). Prefers display config."""
        return self.display_config.get("agent_prefix", self.metadata.get("prefix", "A"))

    @property
    def id_format(self) -> str:
        """ID format: 'padded' (A01) or 'simple' (I1)."""
        return self.display_config.get("id_format", self.metadata.get("agent_id_format", "padded"))

    def format_agent_id(self, agent_id: str) -> str:
        """
        Format an agent ID according to workflow display rules.
        Ex: '1' -> 'A01' (if padded/A), 'orch' -> 'A00'
        """
        aid = str(agent_id).upper()
        
        # 1. Handle Special Roles
        if aid in ('ORCH', 'ORCHESTRATOR', '0', '00'):
            # Default orchestrator ID if not set
            default_orch = f"{self.agent_prefix}-00" if self.id_format == 'padded' else f"{self.agent_prefix}0"
            return self.display_config.get('orch_id', default_orch)

        # 2. Handle On-Demand / Special Agents (e.g., 'SEC' -> 'A-SEC')
        if aid in ('SEC', 'DOC', 'DS', 'PERF'):
            return f"{self.agent_prefix}-{aid}"

        # 3. Handle Numeric IDs
        # Strip existing prefix if present to re-format correctly
        clean_id = aid.replace(self.agent_prefix, "").replace("-", "")
        if clean_id.isdigit():
            num = int(clean_id)
            num_str = str(num).zfill(2) if self.id_format == "padded" else str(num)
            separator = "-" if self.id_format == "padded" else ""
            return f"{self.agent_prefix}{separator}{num_str}"

        # 4. Fallback: Return as-is if it matches pattern, else prefix it
        if aid.startswith(self.agent_prefix):
            return aid
        
        return f"{self.agent_prefix}{aid}"

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Find agent definition by ID (robust lookup)."""
        target = str(agent_id).upper()
        
        # Try exact match first
        for agent in self.agents:
            if str(agent.get("id", "")).upper() == target:
                return agent
        
        # Try formatted match
        formatted = self.format_agent_id(target)
        for agent in self.agents:
            if str(agent.get("id", "")).upper() == formatted:
                return agent
                
        return None

# =============================================================================
# LOADING LOGIC
# =============================================================================

def get_canonical_dir() -> Path:
    """Get the canonical manifests directory."""
    try:
        # Try to use the standard core paths if available
        from ..core.paths import get_manifests_dir
        return get_manifests_dir() / "_canonical"
    except (ImportError, Exception):
        # Robust fallback for dev environments / tests
        from ..core.config_service import find_repo_root
        repo_root = find_repo_root()
        return repo_root / "manifests" / "_canonical"

def list_canonical_workflows() -> List[str]:
    """List available workflow names from the canonical directory."""
    canonical_dir = get_canonical_dir()
    if not canonical_dir.exists():
        logger.warning(f"Canonical directory not found: {canonical_dir}")
        return []
        
    workflows = []
    for d in canonical_dir.iterdir():
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith("."):
            workflows.append(d.name)
    return sorted(workflows)

def list_workflows() -> List[Dict[str, str]]:
    """
    List available workflow packages from canonical JSON.
    
    Returns:
        List of dicts with 'name', 'version', 'path', 'description' keys.
    
    Example:
        >>> workflows = list_workflows()
        >>> for wf in workflows:
        ...     print(f"{wf['name']} v{wf['version']}")
    """
    workflows_dir = get_canonical_dir()
    result = []
    
    # Get workflows from canonical directory
    for wf_name in list_canonical_workflows():
        manifests = load_canonical_workflow(wf_name)
        workflow_data = manifests.get("workflow", {})
        if workflow_data:
            wf_path = workflows_dir / wf_name
            result.append({
                "name": wf_name,
                "version": workflow_data.get("version", "0.0.0"),
                "path": str(wf_path),
                "description": workflow_data.get("description", ""),
                "enabled": True,
                "status": "stable",
            })
    
    return result

def _load_manifest_file(workflow_dir: Path, filename_base: str) -> Optional[Dict[str, Any]]:
    """Helper to load a JSON or YAML file."""
    extensions = [".json", ".yaml", ".yml"]
    
    for ext in extensions:
        file_path = workflow_dir / f"{filename_base}{ext}"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    if ext == ".json":
                        return json.load(f)
                    else:
                        return yaml.safe_load(f)
            except Exception as e:
                raise CanonicalLoadError(f"Failed to parse {file_path}: {e}")
    return None

def load_canonical_workflow(workflow: str, return_object: bool = False) -> Any:
    """
    Load all canonical files for a workflow.
    
    Args:
        workflow: Workflow name (e.g., "planning")
        return_object: If True, returns WorkflowPackage object. If False, returns raw dict.
    
    Returns:
        WorkflowPackage or Dict[str, Any]
    """
    canonical_dir = get_canonical_dir()
    wf_path = canonical_dir / workflow
    
    if not wf_path.exists():
        raise CanonicalLoadError(f"Workflow '{workflow}' not found at {wf_path}")

    # Load Components
    manifests = {
        "workflow": _load_manifest_file(wf_path, "workflow"),
        "agents": _load_manifest_file(wf_path, "agents"),
        "artifacts": _load_manifest_file(wf_path, "artifacts"),
        "instructions": _load_manifest_file(wf_path, "instructions"),
    }

    # Validate Essentials
    if not manifests["workflow"]:
        raise CanonicalLoadError(f"Missing workflow definition for '{workflow}'")
    
    # Defaults
    if not manifests["agents"]: manifests["agents"] = {"agents": []}
    if not manifests["artifacts"]: manifests["artifacts"] = {"artifacts": []}
    if not manifests["instructions"]: manifests["instructions"] = {"instructions": []}

    if not return_object:
        return manifests

    # Construct Object
    workflow_data = manifests.get("workflow", {})
    
    # Extract Lists safely
    agents_list = manifests.get("agents", {}).get("agents", [])
    artifacts_list = manifests.get("artifacts", {}).get("artifacts", [])
    
    # Handle Governance (JSON dict or string)
    gov_data = workflow_data.get("governance", {})
    governance_str = json.dumps(gov_data, indent=2) if isinstance(gov_data, dict) else str(gov_data)

    return WorkflowPackage(
        name=workflow_data.get("name", workflow),
        version=workflow_data.get("version", "0.0.0"),
        path=wf_path,
        metadata=workflow_data,
        agents=agents_list,
        artifacts=artifacts_list,
        instructions=manifests.get("instructions", {}),
        governance=governance_str
    )

def load_workflow(name: str) -> WorkflowPackage:
    """Alias for load_canonical_workflow(..., return_object=True)."""
    return load_canonical_workflow(name, return_object=True)

# =============================================================================
# CONVENIENCE ACCESSORS
# =============================================================================

def get_default_workflow() -> str:
    """Get the default workflow name."""
    return "planning"

def get_workflow_agents(name: str) -> List[Dict[str, Any]]:
    """Get agents for a workflow by name."""
    return load_workflow(name).agents

def get_workflow_artifacts(name: str) -> List[Dict[str, Any]]:
    """Get artifacts for a workflow by name."""
    return load_workflow(name).artifacts

def get_workflow_instructions(name: str) -> Dict[str, Any]:
    """Get instructions for a workflow by name."""
    return load_workflow(name).instructions

# =============================================================================
# DATA EXTRACTION HELPERS
# =============================================================================

def get_agents_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract agents list from canonical data.
    
    Args:
        data: Loaded canonical workflow data.
        
    Returns:
        List of agent definitions.
    """
    agents_data = data.get("agents", {})
    return agents_data.get("agents", [])


def get_artifacts_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract artifacts list from canonical data.
    
    Args:
        data: Loaded canonical workflow data.
        
    Returns:
        List of artifact definitions.
    """
    artifacts_data = data.get("artifacts", {})
    return artifacts_data.get("artifacts", [])


def get_instructions_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract instructions list from canonical data.
    
    Args:
        data: Loaded canonical workflow data.
        
    Returns:
        List of instruction definitions.
    """
    instructions_data = data.get("instructions", {})
    return instructions_data.get("instructions", [])


def get_workflow_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract workflow metadata from canonical data.
    
    Args:
        data: Loaded canonical workflow data.
        
    Returns:
        Workflow metadata dictionary.
    """
    return data.get("workflow", {})

# =============================================================================
# LOOKUP BUILDERS
# =============================================================================

def build_agent_lookup(agents: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build a lookup dict from agent ID to agent definition.
    
    Args:
        agents: List of agent definitions.
        
    Returns:
        Dict mapping agent ID to agent dict.
    """
    return {agent["id"]: agent for agent in agents if "id" in agent}


def build_artifact_lookup(artifacts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build a lookup dict from artifact ID to artifact definition.
    
    Args:
        artifacts: List of artifact definitions.
        
    Returns:
        Dict mapping artifact ID to artifact dict.
    """
    return {artifact["id"]: artifact for artifact in artifacts if "id" in artifact}


def build_instruction_lookup(instructions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build a lookup dict from instruction ID to instruction definition.
    
    Args:
        instructions: List of instruction definitions.
        
    Returns:
        Dict mapping instruction ID to instruction dict.
    """
    return {instruction["id"]: instruction for instruction in instructions if "id" in instruction}


def extract_files_from_produces_consumes(items: Any) -> List[str]:
    """Extract file paths from produces/consumes lists.
    
    Args:
        items: List of file paths or dicts with 'file' key.
        
    Returns:
        List of file paths as strings.
    """
    if not items:
        return []
    
    files = []
    for item in items:
        if isinstance(item, str):
            files.append(item)
        elif isinstance(item, dict) and "file" in item:
            files.append(item["file"])
    return files

if __name__ == "__main__":
    # Simple self-test
    logging.basicConfig(level=logging.INFO)
    try:
        wf = load_workflow("planning")
        print(f"Loaded Workflow: {wf.display_name} (v{wf.version})")
        print(f"Agents: {len(wf.agents)}")
    except Exception as e:
        print(f"Error loading workflow: {e}")