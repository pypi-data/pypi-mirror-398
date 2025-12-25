#!/usr/bin/env python3
"""YAML writer with comments and formatting.

Writes denormalized data to human-readable YAML files with:
- Section headers and dividers
- Inline comments explaining fields
- Consistent formatting

Usage:
    from agentic_workflow.generation.yaml_writer import YamlWriter
    
    writer = YamlWriter()
    writer.write_workflow_yaml(data, output_path)
    writer.write_agents_yaml(agents, output_path)
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

try:
    import yaml
except ImportError:
    from agentic_workflow.cli.utils import display_error
    display_error("ERROR: pyyaml required. Install with: pip install pyyaml")
    sys.exit(1)

__all__ = ["YamlWriter", "write_all_yaml"]


class YamlWriter:
    """Writes YAML files with comments and consistent formatting."""
    
    def __init__(self, workflow_name: str = ""):
        """Initialize YAML writer.
        
        Args:
            workflow_name: Workflow name for header generation.
        """
        self.workflow_name = workflow_name
        self.generation_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def _header(self, title: str, source_files: List[str] = None) -> str:
        """Generate file header comment.
        
        Args:
            title: Section title.
            source_files: List of source JSON files.
            
        Returns:
            Header comment string.
        """
        lines = [
            "# " + "=" * 74,
            f"# {title.upper()}",
            f"# Generated: {self.generation_date}",
        ]
        
        if source_files:
            lines.append(f"# Source: {', '.join(source_files)}")
        
        lines.append(f"# Workflow: {self.workflow_name}")
        lines.append("#")
        lines.append("# NOTE: This file is GENERATED from canonical JSON files.")
        lines.append("#       Edit the source JSON in manifests/_canonical/ instead.")
        lines.append("# " + "=" * 74)
        lines.append("")
        
        return "\n".join(lines)
    
    def _section_divider(self, title: str, char: str = "-") -> str:
        """Generate section divider comment.
        
        Args:
            title: Section title.
            char: Divider character.
            
        Returns:
            Divider comment string.
        """
        return f"\n# {char * 3} {title} {char * (67 - len(title))}\n"
    
    def _agent_header(self, agent_id: str, role: str) -> str:
        """Generate agent section header.
        
        Args:
            agent_id: Agent ID.
            role: Agent role.
            
        Returns:
            Agent header comment string.
        """
        lines = [
            "",
            "  # " + "=" * 70,
            f"  # {agent_id}: {role}",
            "  # " + "=" * 70,
            "",  # Trailing newline before list item
        ]
        return "\n".join(lines)
    
    def _yaml_dump(self, data: Any, indent: int = 0) -> str:
        """Dump data to YAML string with custom formatting.
        
        Args:
            data: Data to serialize.
            indent: Base indentation level.
            
        Returns:
            YAML string.
        """
        # Use custom representer for clean output
        class CleanDumper(yaml.SafeDumper):
            pass
        
        # Represent None as empty
        def represent_none(dumper, data):
            return dumper.represent_scalar('tag:yaml.org,2002:null', '')
        
        CleanDumper.add_representer(type(None), represent_none)
        
        result = yaml.dump(
            data,
            Dumper=CleanDumper,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )
        
        # Add indentation if needed
        if indent > 0:
            prefix = "  " * indent
            result = "\n".join(prefix + line if line else line for line in result.split("\n"))
        
        return result
    
    def write_workflow_yaml(
        self, 
        workflow: Dict[str, Any], 
        output_path: Path
    ) -> None:
        """Write workflow.yaml with summary and structure.
        
        Args:
            workflow: Denormalized workflow data.
            output_path: Output file path.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            # Header
            f.write(self._header(
                f"{self.workflow_name} Workflow",
                ["workflow.json", "agents.json"]
            ))
            
            # Core metadata
            f.write("# --- Workflow Metadata ---\n")
            core_fields = {
                "name": workflow.get("name", ""),
                "workflow_id": workflow.get("workflow_id", ""),
                "display_name": workflow.get("display_name", ""),
                "version": workflow.get("version", ""),
                "description": workflow.get("description", ""),
            }
            f.write(self._yaml_dump(core_fields))
            
            # Agent summary
            f.write(self._section_divider("Agent Summary (derived)"))
            summary = workflow.get("agent_summary", {})
            f.write(self._yaml_dump({"agent_summary": summary}))
            
            # Pipeline
            f.write(self._section_divider("Pipeline Configuration"))
            pipeline = workflow.get("pipeline", {})
            f.write(self._yaml_dump({"pipeline": pipeline}))
            
            # Directories
            directories = workflow.get("directories", {})
            if directories:
                f.write(self._section_divider("Directory Structure"))
                f.write("# Used by scaffold scripts for project initialization\n")
                f.write(self._yaml_dump({"directories": directories}))
            
            # Checkpoints
            checkpoints = workflow.get("checkpoints", [])
            if checkpoints:
                f.write(self._section_divider("Checkpoints"))
                f.write(self._yaml_dump({"checkpoints": checkpoints}))
            
            # Stages (implementation workflow)
            stages = workflow.get("stages", [])
            if stages:
                f.write(self._section_divider("Stages"))
                f.write(self._yaml_dump({"stages": stages}))
            
            # Cycles
            cycles = workflow.get("cycles", {})
            if cycles:
                f.write(self._section_divider("Cycles"))
                f.write(self._yaml_dump({"cycles": cycles}))
            
            # Globals
            globals_data = workflow.get("globals", {})
            if globals_data:
                f.write(self._section_divider("Global Rules"))
                f.write(self._yaml_dump({"globals": globals_data}))
            
            # CLI
            cli = workflow.get("cli", {})
            if cli:
                f.write(self._section_divider("CLI Configuration"))
                f.write(self._yaml_dump({"cli": cli}))
            
            # Governance
            governance = workflow.get("governance", {})
            if governance:
                f.write(self._section_divider("Governance Rules"))
                f.write(self._yaml_dump({"governance": governance}))
    
    def write_agents_yaml(
        self, 
        agents: List[Dict[str, Any]], 
        output_path: Path
    ) -> None:
        """Write agents.yaml with enriched agent definitions.
        
        Args:
            agents: List of denormalized agents.
            output_path: Output file path.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            # Header
            f.write(self._header(
                f"Agents - {self.workflow_name} Workflow",
                ["agents.json", "artifacts.json", "instructions.json"]
            ))
            
            f.write("agents:\n")
            
            for agent in agents:
                # Agent header comment
                f.write(self._agent_header(agent["id"], agent.get("role", "")))
                
                # Core agent data
                agent_data = {
                    "id": agent["id"],
                    "slug": agent.get("slug", ""),
                    "role": agent.get("role", ""),
                    "agent_type": agent.get("agent_type", "core"),
                }
                
                # Add purpose if present
                if agent.get("purpose"):
                    agent_data["purpose"] = agent["purpose"]
                
                # Add key responsibilities
                if agent.get("key_responsibilities"):
                    agent_data["key_responsibilities"] = agent["key_responsibilities"]
                
                # Add produces (simplified for readability)
                produces = agent.get("produces", {})
                if produces:
                    agent_data["produces"] = self._simplify_produces(produces)
                
                # Add consumes (simplified for readability)
                consumes = agent.get("consumes", {})
                if consumes:
                    agent_data["consumes"] = self._simplify_consumes(consumes)
                
                # Add handoff
                handoff = agent.get("handoff", {})
                if handoff:
                    agent_data["handoff"] = handoff
                
                # Write agent block - use proper indentation
                # First dump the dict without list wrapper
                agent_yaml = yaml.dump(
                    agent_data,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    width=120,
                )
                # Add list item marker and indent each line
                lines = agent_yaml.split("\n")
                for i, line in enumerate(lines):
                    if i == 0:
                        f.write(f"  - {line}\n")
                    elif line.strip():
                        f.write(f"    {line}\n")
                f.write("\n")
    
    def _simplify_produces(self, produces: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Simplify produces structure for YAML output.
        
        Removes empty fields, keeps essential info.
        """
        result = {}
        for category, items in produces.items():
            simplified = []
            for item in items:
                entry = {"filename": item["filename"]}
                if item.get("description"):
                    entry["description"] = item["description"]
                if item.get("is_gating"):
                    entry["is_gating"] = True
                simplified.append(entry)
            if simplified:
                result[category] = simplified
        return result
    
    def _simplify_consumes(self, consumes: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Simplify consumes structure for YAML output."""
        result = {}
        for category, items in consumes.items():
            simplified = []
            for item in items:
                entry = {"filename": item["filename"]}
                if item.get("source"):
                    entry["source"] = item["source"]
                if not item.get("required", True):
                    entry["required"] = False
                simplified.append(entry)
            if simplified:
                result[category] = simplified
        return result
    
    def write_artifacts_yaml(
        self, 
        artifacts: List[Dict[str, Any]], 
        output_path: Path
    ) -> None:
        """Write artifacts.yaml with ownership and relationships.
        
        Args:
            artifacts: List of denormalized artifacts.
            output_path: Output file path.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            # Header
            f.write(self._header(
                f"Artifacts - {self.workflow_name} Workflow",
                ["artifacts.json", "agents.json"]
            ))
            
            # Group artifacts by category
            by_category: Dict[str, List[Dict]] = {}
            for art in artifacts:
                cat = art.get("category", "core")
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(art)
            
            f.write("artifacts:\n")
            
            # Write by category
            category_order = ["core", "domain", "reference", "gating", "log"]
            for cat in category_order:
                if cat not in by_category:
                    continue
                
                f.write(self._section_divider(f"{cat.upper()} Artifacts", "-"))
                
                for art in by_category[cat]:
                    art_data = {
                        "filename": art["filename"],
                        "owner": art["owner"],
                        "category": art["category"],
                    }
                    
                    if art.get("description"):
                        art_data["description"] = art["description"]
                    
                    if art.get("purpose"):
                        art_data["purpose"] = art["purpose"]
                    
                    if art.get("is_gating"):
                        art_data["is_gating"] = True
                    
                    if art.get("is_shared"):
                        art_data["is_shared"] = True
                    
                    consumed_by = art.get("consumed_by", [])
                    if consumed_by:
                        art_data["consumed_by"] = consumed_by
                    
                    # Write with proper list item formatting
                    f.write(f"  - filename: {art_data['filename']}\n")
                    f.write(f"    owner: {art_data['owner']}\n")
                    f.write(f"    category: {art_data['category']}\n")
                    
                    if art_data.get("description"):
                        f.write(f"    description: {art_data['description']}\n")
                    
                    if art_data.get("purpose"):
                        f.write(f"    purpose: {art_data['purpose']}\n")
                    
                    if art_data.get("is_gating"):
                        f.write(f"    is_gating: true\n")
                    
                    if art_data.get("is_shared"):
                        f.write(f"    is_shared: true\n")
                    
                    if consumed_by:
                        f.write(f"    consumed_by:\n")
                        for consumer in consumed_by:
                            f.write(f"    - {consumer}\n")
                    
                    f.write("\n")
            
            # Any uncategorized
            for cat, arts in by_category.items():
                if cat in category_order:
                    continue
                f.write(self._section_divider(f"{cat.upper()} Artifacts", "-"))
                for art in arts:
                    # Same logic as above...
                    f.write(f"  - filename: {art['filename']}\n")
                    f.write(f"    owner: {art['owner']}\n")
    
    def write_instructions_yaml(
        self, 
        instructions: List[Dict[str, Any]], 
        output_path: Path
    ) -> None:
        """Write instructions.yaml with full agent instructions.
        
        Args:
            instructions: List of denormalized instructions.
            output_path: Output file path.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            # Header
            f.write(self._header(
                f"Instructions - {self.workflow_name} Workflow",
                ["instructions.json", "agents.json", "workflow.json"]
            ))
            
            f.write("# This file contains complete agent instructions for prompt generation.\n")
            f.write("# Each agent has: purpose, responsibilities, workflow, boundaries, I/O.\n\n")
            
            f.write("instructions:\n")
            
            for instr in instructions:
                # Agent header
                f.write(self._agent_header(instr["id"], instr.get("role", "")))
                
                instr_data = {
                    "id": instr["id"],
                    "slug": instr.get("slug", ""),
                    "role": instr.get("role", ""),
                }
                
                if instr.get("purpose"):
                    instr_data["purpose"] = instr["purpose"]
                
                if instr.get("responsibilities"):
                    instr_data["responsibilities"] = instr["responsibilities"]
                
                if instr.get("workflow"):
                    instr_data["workflow"] = instr["workflow"]
                
                if instr.get("boundaries"):
                    instr_data["boundaries"] = instr["boundaries"]
                
                if instr.get("domain_rules"):
                    instr_data["domain_rules"] = instr["domain_rules"]
                
                # Add I/O for completeness
                produces = instr.get("produces", {})
                if produces:
                    instr_data["produces"] = self._simplify_produces(produces)
                
                consumes = instr.get("consumes", {})
                if consumes:
                    instr_data["consumes"] = self._simplify_consumes(consumes)
                
                if instr.get("handoff"):
                    instr_data["handoff"] = instr["handoff"]
                
                # Write with proper indentation (same approach as agents)
                instr_yaml = yaml.dump(
                    instr_data,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    width=120,
                )
                lines = instr_yaml.split("\n")
                for i, line in enumerate(lines):
                    if i == 0:
                        f.write(f"  - {line}\n")
                    elif line.strip():
                        f.write(f"    {line}\n")
                f.write("\n")


def write_all_yaml(
    denormalized_data: Dict[str, Any],
    output_dir: Path,
    workflow_name: str
) -> List[Path]:
    """Write all YAML files for a workflow.
    
    Args:
        denormalized_data: Output from denormalize_canonical().
        output_dir: Output directory.
        workflow_name: Workflow name.
        
    Returns:
        List of created file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    writer = YamlWriter(workflow_name)
    files_created = []
    
    # Write each file
    workflow_path = output_dir / "workflow.yaml"
    writer.write_workflow_yaml(denormalized_data["workflow"], workflow_path)
    files_created.append(workflow_path)
    
    agents_path = output_dir / "agents.yaml"
    writer.write_agents_yaml(denormalized_data["agents"], agents_path)
    files_created.append(agents_path)
    
    artifacts_path = output_dir / "artifacts.yaml"
    writer.write_artifacts_yaml(denormalized_data["artifacts"], artifacts_path)
    files_created.append(artifacts_path)
    
    instructions_path = output_dir / "instructions.yaml"
    writer.write_instructions_yaml(denormalized_data["instructions"], instructions_path)
    files_created.append(instructions_path)
    
    return files_created
