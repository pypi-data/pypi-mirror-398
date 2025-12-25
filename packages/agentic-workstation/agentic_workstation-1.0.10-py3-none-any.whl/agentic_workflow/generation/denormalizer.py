#!/usr/bin/env python3
"""Denormalization logic for canonical workflow data.

Merges and enriches data from separate JSON files into consolidated views
suitable for YAML generation and human readability.

Key transformations:
- Agents: Enrich produces/consumes with artifact metadata
- Artifacts: Derive consumed_by from agents' consumes
- Instructions: Add produces/consumes for completeness

Usage:
    from agentic_workflow.generation.denormalizer import Denormalizer
    
    dn = Denormalizer(canonical_data)
    enriched_agents = dn.denormalize_agents()
    enriched_artifacts = dn.denormalize_artifacts()
"""

from typing import Any, Dict, List, Optional, Set
from .canonical_loader import (
    get_agents_list,
    get_artifacts_list,
    get_instructions_list,
    get_workflow_metadata,
    build_agent_lookup,
    build_artifact_lookup,
    build_instruction_lookup,
    extract_files_from_produces_consumes,
)

__all__ = ["Denormalizer", "denormalize_canonical"]


class Denormalizer:
    """Denormalizes canonical workflow data for human-readable output."""
    
    def __init__(self, canonical_data: Dict[str, Any]):
        """Initialize with loaded canonical workflow data.
        
        Args:
            canonical_data: Dict from load_canonical_workflow().
        """
        self.data = canonical_data
        self.workflow = get_workflow_metadata(canonical_data)
        self.agents = get_agents_list(canonical_data)
        self.artifacts = get_artifacts_list(canonical_data)
        self.instructions = get_instructions_list(canonical_data)
        
        # Build lookup dicts
        self.agent_lookup = build_agent_lookup(self.agents)
        self.artifact_lookup = build_artifact_lookup(self.artifacts)
        self.instruction_lookup = build_instruction_lookup(self.instructions)
        
        # Derive reverse relationships
        self._consumed_by = self._compute_consumed_by()
        self._produced_by = self._compute_produced_by()
    
    def _compute_consumed_by(self) -> Dict[str, List[str]]:
        """Compute which agents consume each artifact.
        
        Returns:
            Dict mapping filename to list of consumer agent IDs.
        """
        consumed_by: Dict[str, List[str]] = {}
        
        for agent in self.agents:
            agent_id = agent.get("id", "")
            consumes = agent.get("consumes", {})
            files = extract_files_from_produces_consumes(consumes)
            
            for filename in files:
                if filename not in consumed_by:
                    consumed_by[filename] = []
                if agent_id not in consumed_by[filename]:
                    consumed_by[filename].append(agent_id)
        
        return consumed_by
    
    def _compute_produced_by(self) -> Dict[str, str]:
        """Compute which agent produces each artifact.
        
        Returns:
            Dict mapping filename to producer agent ID.
        """
        produced_by: Dict[str, str] = {}
        
        for agent in self.agents:
            agent_id = agent.get("id", "")
            produces = agent.get("produces", {})
            files = extract_files_from_produces_consumes(produces)
            
            for filename in files:
                produced_by[filename] = agent_id
        
        return produced_by
    
    def get_artifact_metadata(self, filename: str) -> Dict[str, Any]:
        """Get enriched metadata for an artifact.
        
        Args:
            filename: Artifact filename.
            
        Returns:
            Dict with description, purpose, is_gating, template, etc.
        """
        artifact = self.artifact_lookup.get(filename, {})
        return {
            "description": artifact.get("description", ""),
            "purpose": artifact.get("purpose", ""),
            "category": artifact.get("category", "core"),
            "is_gating": artifact.get("is_gating", False),
            "is_shared": artifact.get("is_shared", False),
            "required": artifact.get("required", True),
            "template": artifact.get("template", ""),
            "type": artifact.get("type", "file"),
        }
    
    def get_instruction_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get key instruction fields for an agent.
        
        Args:
            agent_id: Agent ID.
            
        Returns:
            Dict with purpose, key_responsibilities (top 5), handoff.
        """
        instr = self.instruction_lookup.get(agent_id, {})
        
        responsibilities = instr.get("responsibilities", [])
        key_responsibilities = responsibilities[:5] if responsibilities else []
        
        return {
            "purpose": instr.get("purpose", ""),
            "key_responsibilities": key_responsibilities,
            "handoff": instr.get("handoff", {}),
            "boundaries": instr.get("boundaries", {}),
        }
    
    def enrich_produces_item(self, filename: str, category: str = "core") -> Dict[str, Any]:
        """Enrich a single produces item with artifact metadata.
        
        Args:
            filename: Artifact filename.
            category: Category from produces structure.
            
        Returns:
            Enriched item dict.
        """
        meta = self.get_artifact_metadata(filename)
        return {
            "filename": filename,
            "category": category,
            "description": meta["description"],
            "purpose": meta["purpose"],
            "is_gating": meta["is_gating"],
            "template": meta["template"],
        }
    
    def enrich_consumes_item(
        self, 
        item: Any, 
        category: str = "core"
    ) -> Dict[str, Any]:
        """Enrich a single consumes item with metadata.
        
        Args:
            item: Either a filename string or dict with {file, required}.
            category: Category from consumes structure.
            
        Returns:
            Enriched item dict.
        """
        if isinstance(item, dict):
            filename = item.get("filename") or item.get("file", "")
            required = item.get("required", True)
        else:
            filename = str(item)
            required = True
        
        meta = self.get_artifact_metadata(filename)
        source = self._produced_by.get(filename, "")
        
        return {
            "filename": filename,
            "category": category,
            "required": required,
            "source": source,
            "description": meta["description"],
        }
    
    def denormalize_produces(self, produces: Any) -> Dict[str, List[Dict[str, Any]]]:
        """Denormalize produces structure with artifact metadata.
        
        Args:
            produces: Original produces from agent.
            
        Returns:
            Categorized dict with enriched items.
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        
        if isinstance(produces, dict):
            for category, items in produces.items():
                if isinstance(items, list):
                    result[category] = []
                    for item in items:
                        # Extract filename from dict (prefer 'filename' over 'file' for canonical schema)
                        if isinstance(item, dict):
                            filename = item.get("filename") or item.get("file", "")
                        else:
                            filename = item
                        if filename:
                            result[category].append(self.enrich_produces_item(filename, category))
        elif isinstance(produces, list):
            result["core"] = [self.enrich_produces_item(f, "core") for f in produces]
        
        return result
    
    def denormalize_consumes(self, consumes: Any) -> Dict[str, List[Dict[str, Any]]]:
        """Denormalize consumes structure with artifact metadata.
        
        Args:
            consumes: Original consumes from agent.
            
        Returns:
            Categorized dict with enriched items.
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        
        if isinstance(consumes, dict):
            for category, items in consumes.items():
                if isinstance(items, list):
                    result[category] = []
                    for item in items:
                        result[category].append(self.enrich_consumes_item(item, category))
        elif isinstance(consumes, list):
            result["core"] = [self.enrich_consumes_item(item, "core") for item in consumes]
        
        return result
    
    def denormalize_agent(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """Denormalize a single agent with enriched data.
        
        Args:
            agent: Original agent definition.
            
        Returns:
            Enriched agent dict.
        """
        agent_id = agent.get("id", "")
        instr_summary = self.get_instruction_summary(agent_id)
        
        return {
            "id": agent_id,
            "slug": agent.get("slug", ""),
            "role": agent.get("role", ""),
            "agent_type": agent.get("agent_type", "core"),
            "description": agent.get("description", ""),
            
            # From instructions
            "purpose": instr_summary["purpose"],
            "key_responsibilities": instr_summary["key_responsibilities"],
            
            # Enriched I/O
            "produces": self.denormalize_produces(agent.get("produces", {})),
            "consumes": self.denormalize_consumes(agent.get("consumes", {})),
            
            # Handoff
            "handoff": instr_summary["handoff"],
        }
    
    def denormalize_agents(self) -> List[Dict[str, Any]]:
        """Denormalize all agents with enriched data.
        
        Returns:
            List of enriched agent dicts.
        """
        return [self.denormalize_agent(agent) for agent in self.agents]
    
    def denormalize_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """Denormalize a single artifact with derived relationships.
        
        Args:
            artifact: Original artifact definition.
            
        Returns:
            Enriched artifact dict.
        """
        filename = artifact.get("filename", "")
        
        return {
            "filename": filename,
            "owner": artifact.get("owner", ""),
            "category": artifact.get("category", "core"),
            "description": artifact.get("description", ""),
            "purpose": artifact.get("purpose", ""),
            "type": artifact.get("type", "file"),
            "is_gating": artifact.get("is_gating", False),
            "is_shared": artifact.get("is_shared", False),
            "required": artifact.get("required", True),
            "template": artifact.get("template", ""),
            
            # Derived relationships
            "consumed_by": self._consumed_by.get(filename, []),
        }
    
    def denormalize_artifacts(self) -> List[Dict[str, Any]]:
        """Denormalize all artifacts with derived relationships.
        
        Returns:
            List of enriched artifact dicts.
        """
        return [self.denormalize_artifact(art) for art in self.artifacts]
    
    def denormalize_instruction(self, instr: Dict[str, Any]) -> Dict[str, Any]:
        """Denormalize a single instruction with agent I/O.
        
        Args:
            instr: Original instruction definition.
            
        Returns:
            Enriched instruction dict with produces/consumes.
        """
        agent_id = instr.get("id", "")
        agent = self.agent_lookup.get(agent_id, {})
        
        return {
            "id": agent_id,
            "slug": instr.get("slug", ""),
            "role": instr.get("role", agent.get("role", "")),
            
            # Full instruction content
            "purpose": instr.get("purpose", ""),
            "responsibilities": instr.get("responsibilities", []),
            "workflow": instr.get("workflow", {}),
            "boundaries": instr.get("boundaries", {}),
            "handoff": instr.get("handoff", {}),
            "domain_rules": instr.get("domain_rules", []),
            
            # Duplicated I/O from agents (for prompt completeness)
            "produces": self.denormalize_produces(agent.get("produces", {})),
            "consumes": self.denormalize_consumes(agent.get("consumes", {})),
        }
    
    def denormalize_instructions(self) -> List[Dict[str, Any]]:
        """Denormalize all instructions with agent I/O.
        
        Returns:
            List of enriched instruction dicts.
        """
        return [self.denormalize_instruction(instr) for instr in self.instructions]
    
    def compute_workflow_summary(self) -> Dict[str, Any]:
        """Compute workflow summary statistics.
        
        Returns:
            Dict with agent counts, pipeline, etc.
        """
        agent_types = {}
        for agent in self.agents:
            atype = agent.get("agent_type", "core")
            agent_types[atype] = agent_types.get(atype, 0) + 1
        
        pipeline = self.workflow.get("pipeline", {})
        
        return {
            "total_agents": len(self.agents),
            "total_artifacts": len(self.artifacts),
            "agent_counts": agent_types,
            "pipeline_order": pipeline.get("order", []),
            "parallel_groups": pipeline.get("parallel_groups", []),
            "checkpoints": self.workflow.get("checkpoints", []),
        }
    
    def denormalize_workflow(self) -> Dict[str, Any]:
        """Denormalize workflow with summary statistics.
        
        Returns:
            Enriched workflow dict.
        """
        summary = self.compute_workflow_summary()
        
        # Merge with original workflow data
        result = dict(self.workflow)
        result["agent_summary"] = summary
        
        return result


# --- Convenience functions ---

def denormalize_canonical(canonical_data: Dict[str, Any]) -> Dict[str, Any]:
    """Denormalize all canonical data in one call.
    
    Args:
        canonical_data: Dict from load_canonical_workflow().
        
    Returns:
        Dict with denormalized workflow, agents, artifacts, instructions.
    """
    dn = Denormalizer(canonical_data)
    
    return {
        "workflow": dn.denormalize_workflow(),
        "agents": dn.denormalize_agents(),
        "artifacts": dn.denormalize_artifacts(),
        "instructions": dn.denormalize_instructions(),
    }
