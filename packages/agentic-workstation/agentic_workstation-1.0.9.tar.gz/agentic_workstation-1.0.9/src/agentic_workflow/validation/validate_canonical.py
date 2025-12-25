#!/usr/bin/env python3
"""
Comprehensive validator for canonical JSON manifests.

Validates:
1. JSON Schema conformance (using jsonschema)
2. Cross-reference integrity between files
3. ID format compliance
4. Artifact ownership consistency
5. Pipeline order validity
6. Cycle references (instructions → workflow.cycles)
7. Cross-workflow artifact dependencies (from_workflow → input_from)
8. Stage-agent assignments

Usage:
  python3 scripts/validation/validate_canonical.py [--workflow planning]
  python3 scripts/validation/validate_canonical.py --all
  python3 scripts/validation/validate_canonical.py --check-cross-refs
"""
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, field

try:
    import jsonschema
except ImportError:
    jsonschema = None

from agentic_workflow.cli.utils import display_error, display_warning, display_info, display_success
from agentic_workflow.generation.canonical_loader import load_canonical_workflow, get_canonical_dir

# Resolve paths
ROOT = Path(__file__).resolve().parents[3]
CANONICAL_DIR = get_canonical_dir()
SCHEMAS_DIR = ROOT / "src" / "agentic_workflow" / "manifests" / "_canonical_schemas"

# ID patterns - aligned with schema: 1-2 uppercase letters, hyphen, 2-6 alphanumeric
AGENT_ID_PATTERN = re.compile(r"^[A-Z]{1,2}-[A-Z0-9]{2,6}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9_]+$")
FILENAME_PATTERN = re.compile(r"^[a-z0-9_/]+\.(md|yaml|json|bib)$")

__all__ = ["ValidationResult", "validate_workflow"]


@dataclass
class ValidationResult:
    """Holds validation results for a workflow."""
    workflow: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        """Return True if validation passed (no errors)."""
        return len(self.errors) == 0
    
    def add_error(self, msg: str):
        """Add an error message to the result."""
        self.errors.append(msg)
    
    def add_warning(self, msg: str):
        """Add a warning message to the result."""
        self.warnings.append(msg)
    
    def add_info(self, msg: str):
        """Add an info message to the result."""
        self.info.append(msg)
    
    def print_summary(self):
        """Print a summary of the validation results."""
        status = "PASSED" if self.passed else "FAILED"
        display_info(f"Workflow: {self.workflow} - {status}")
        
        if self.errors:
            display_error(f"Errors ({len(self.errors)}):")
            for e in self.errors:
                display_error(f"  - {e}")
        
        if self.warnings:
            display_warning(f"Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                display_warning(f"  - {w}")
        
        if self.info:
            display_info(f"Info ({len(self.info)}):")
            for i in self.info:
                display_info(f"  - {i}")


def load_json(path: Path) -> Optional[Dict]:
    """Load a JSON file, return None if not found."""
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_schema(data: Dict, schema_path: Path, result: ValidationResult, file_name: str):
    """Validate data against JSON schema."""
    if jsonschema is None:
        result.add_warning(f"jsonschema not installed, skipping schema validation for {file_name}")
        return
    
    if not schema_path.exists():
        result.add_warning(f"Schema not found: {schema_path}")
        return
    
    schema = load_json(schema_path)
    try:
        jsonschema.validate(instance=data, schema=schema)
        result.add_info(f"{file_name}: Schema validation passed")
    except jsonschema.ValidationError as e:
        result.add_error(f"{file_name}: Schema validation failed - {e.message}")


def validate_agent_ids(agents_data: Dict, result: ValidationResult) -> Set[str]:
    """Validate agent IDs and return set of valid IDs."""
    valid_ids = set()
    slugs_seen = set()
    
    for agent in agents_data.get("agents", []):
        agent_id = agent.get("id", "")
        slug = agent.get("slug", "")
        
        # Check ID format
        if not AGENT_ID_PATTERN.match(agent_id):
            result.add_error(f"agents.json: Invalid agent ID format '{agent_id}' - must match ^[A-Z]{{1,3}}-[A-Z0-9]{{2,}}$")
        else:
            valid_ids.add(agent_id)
        
        # Check slug format
        if not SLUG_PATTERN.match(slug):
            result.add_error(f"agents.json: Invalid slug format '{slug}' for agent {agent_id}")
        
        # Check slug uniqueness
        if slug in slugs_seen:
            result.add_error(f"agents.json: Duplicate slug '{slug}'")
        slugs_seen.add(slug)
    
    return valid_ids


def validate_artifact_filenames(artifacts_data: Dict, agent_ids: Set[str], result: ValidationResult) -> Set[str]:
    """Validate artifact filenames and ownership."""
    valid_filenames = set()
    filenames_seen = set()
    
    for artifact in artifacts_data.get("artifacts", []):
        filename = artifact.get("filename", "")
        owner = artifact.get("owner", "")
        
        # Check filename format (allow subdirectories)
        if filename and not FILENAME_PATTERN.match(filename):
            result.add_warning(f"artifacts.json: Filename '{filename}' may not follow convention")
        
        # Check for duplicates
        if filename in filenames_seen:
            result.add_error(f"artifacts.json: Duplicate filename '{filename}'")
        filenames_seen.add(filename)
        valid_filenames.add(filename)
        
        # Check owner exists in agents
        if owner and owner not in agent_ids:
            result.add_error(f"artifacts.json: Owner '{owner}' for '{filename}' not found in agents.json")
    
    return valid_filenames


def validate_instructions(instructions_data: Dict, agent_ids: Set[str], result: ValidationResult):
    """Validate instructions match agents."""
    instruction_ids = set()
    
    for instr in instructions_data.get("instructions", []):
        instr_id = instr.get("id", "")
        slug = instr.get("slug", "")
        
        # Check ID format
        if not AGENT_ID_PATTERN.match(instr_id):
            result.add_error(f"instructions.json: Invalid ID format '{instr_id}'")
        
        # Check slug format
        if not SLUG_PATTERN.match(slug):
            result.add_error(f"instructions.json: Invalid slug format '{slug}' for {instr_id}")
        
        # Check ID exists in agents
        if instr_id not in agent_ids:
            result.add_error(f"instructions.json: ID '{instr_id}' not found in agents.json")
        
        # Check for duplicate instruction IDs
        if instr_id in instruction_ids:
            result.add_error(f"instructions.json: Duplicate ID '{instr_id}'")
        instruction_ids.add(instr_id)
        
        # Check required fields
        if not instr.get("purpose"):
            result.add_warning(f"instructions.json: Missing 'purpose' for {instr_id}")
    
    # Check all agents have instructions
    missing = agent_ids - instruction_ids
    if missing:
        result.add_warning(f"instructions.json: Missing instructions for agents: {', '.join(sorted(missing))}")


def validate_produces_consumes(agents_data: Dict, artifact_filenames: Set[str], workflow_data: Optional[Dict], result: ValidationResult):
    """Validate all produces/consumes references exist in artifacts or input_from."""
    # Build set of valid cross-workflow artifacts from input_from
    input_from_artifacts: Dict[str, Set[str]] = {}
    if workflow_data:
        input_from = workflow_data.get("input_from", {})
        for wf_name, wf_config in input_from.items():
            if isinstance(wf_config, dict):
                artifacts = wf_config.get("artifacts", [])
            elif isinstance(wf_config, list):
                artifacts = wf_config
            else:
                artifacts = []
            input_from_artifacts[wf_name] = set(artifacts)
    
    for agent in agents_data.get("agents", []):
        agent_id = agent.get("id", "")
        
        # Extract all filenames from produces
        produces = agent.get("produces", {})
        if isinstance(produces, dict):
            for category, files in produces.items():
                if isinstance(files, list):
                    for f in files:
                        if f and f not in artifact_filenames:
                            result.add_error(f"agents.json: Agent {agent_id} produces '{f}' not in artifacts.json")
        elif isinstance(produces, list):
            for f in produces:
                if f and f not in artifact_filenames:
                    result.add_error(f"agents.json: Agent {agent_id} produces '{f}' not in artifacts.json")
        
        # Extract all filenames from consumes with cross-workflow support
        consumes = agent.get("consumes", {})
        if isinstance(consumes, dict):
            for category, files in consumes.items():
                if isinstance(files, list):
                    for item in files:
                        _validate_consume_item(item, agent_id, artifact_filenames, input_from_artifacts, result)
        elif isinstance(consumes, list):
            for item in consumes:
                _validate_consume_item(item, agent_id, artifact_filenames, input_from_artifacts, result)


def _validate_consume_item(item: Any, agent_id: str, artifact_filenames: Set[str], 
                           input_from_artifacts: Dict[str, Set[str]], result: ValidationResult):
    """Helper to validate a single consume item (string or object)."""
    if isinstance(item, str):
        # Simple string - must be in local artifacts
        if item and item not in artifact_filenames:
            result.add_warning(f"agents.json: Agent {agent_id} consumes '{item}' not in artifacts.json")
    elif isinstance(item, dict):
        filename = item.get("file", "")
        from_workflow = item.get("from_workflow")
        required = item.get("required", True)
        
        if from_workflow:
            # Cross-workflow artifact - must be in input_from
            if from_workflow not in input_from_artifacts:
                result.add_error(f"agents.json: Agent {agent_id} references from_workflow '{from_workflow}' not in input_from")
            elif filename not in input_from_artifacts.get(from_workflow, set()):
                result.add_error(f"agents.json: Agent {agent_id} consumes '{filename}' from workflow '{from_workflow}' not listed in input_from[{from_workflow}].artifacts")
        else:
            # Local artifact
            if filename and filename not in artifact_filenames:
                if required:
                    result.add_warning(f"agents.json: Agent {agent_id} consumes '{filename}' not in artifacts.json")
                # Optional artifacts missing is just info
                else:
                    result.add_info(f"agents.json: Agent {agent_id} optionally consumes '{filename}' (not in artifacts.json)")


def validate_input_from_artifacts(workflow_data: Dict, result: ValidationResult):
    """Validate that input_from artifacts can be used for workflow start."""
    if not workflow_data:
        return
    
    input_from = workflow_data.get("input_from", {})
    if not input_from:
        return
    
    for wf_name, wf_config in input_from.items():
        if isinstance(wf_config, dict):
            artifacts = wf_config.get("artifacts", [])
            if not artifacts:
                result.add_warning(f"workflow.json: input_from[{wf_name}] has no artifacts listed")
        elif isinstance(wf_config, list):
            if not wf_config:
                result.add_warning(f"workflow.json: input_from[{wf_name}] is empty list")
        else:
            result.add_warning(f"workflow.json: input_from[{wf_name}] has unexpected format")
    
    result.add_info(f"workflow.json: {len(input_from)} cross-workflow input source(s) defined")


def validate_cycle_references(instructions_data: Dict, workflow_data: Optional[Dict], result: ValidationResult):
    """Validate that cycle references in instructions match workflow.cycles definitions."""
    if not instructions_data or not workflow_data:
        return
    
    # Get defined cycles from workflow.json
    defined_cycles = set(workflow_data.get("cycles", {}).keys())
    
    for instr in instructions_data.get("instructions", []):
        instr_id = instr.get("id", "")
        workflow_section = instr.get("workflow", {})
        if not workflow_section:
            continue
        
        cycle = workflow_section.get("cycle")
        if cycle is None:
            continue
        
        if isinstance(cycle, str):
            # Reference to workflow.cycles - must exist
            if cycle not in defined_cycles:
                result.add_error(f"instructions.json: Agent {instr_id} references undefined cycle '{cycle}' (not in workflow.cycles)")
        elif isinstance(cycle, dict):
            # Inline cycle definition - validate structure
            if not cycle.get("name"):
                result.add_warning(f"instructions.json: Agent {instr_id} inline cycle missing 'name'")
            if not cycle.get("steps"):
                result.add_warning(f"instructions.json: Agent {instr_id} inline cycle missing 'steps'")
    
    if defined_cycles:
        result.add_info(f"workflow.json: {len(defined_cycles)} cycle(s) defined: {', '.join(sorted(defined_cycles))}")


def validate_stage_agents(workflow_data: Dict, agent_ids: Set[str], result: ValidationResult):
    """Validate that all agents in stages exist and are in pipeline."""
    if not workflow_data:
        return
    
    stages = workflow_data.get("stages", [])
    pipeline = workflow_data.get("pipeline", {})
    pipeline_order = set(pipeline.get("order", []))
    on_demand = set(pipeline.get("on_demand", []))
    all_pipeline_agents = pipeline_order | on_demand
    
    for stage in stages:
        stage_id = stage.get("id", "UNKNOWN")
        stage_agents = stage.get("agents", [])
        
        for agent_id in stage_agents:
            if agent_id not in agent_ids:
                result.add_error(f"workflow.json: Stage '{stage_id}' references unknown agent '{agent_id}'")
            elif agent_id not in all_pipeline_agents:
                result.add_warning(f"workflow.json: Stage '{stage_id}' agent '{agent_id}' not in pipeline.order or pipeline.on_demand")


def validate_deprecated_globals(workflow_data: Dict, result: ValidationResult):
    """Warn about deprecated globals usage."""
    if not workflow_data:
        return
    globals_section = workflow_data.get("globals", {})
    if "logging_policy" in globals_section:
        result.add_warning("workflow.json: globals.logging_policy is DEPRECATED - use config.logging")
    if "enforcement" in globals_section:
        result.add_warning("workflow.json: globals.enforcement is DEPRECATED - use config.enforcement")
    if "ui" in globals_section:
        result.add_warning("workflow.json: globals.ui is DEPRECATED - use display section")


def validate_on_demand_placement(workflow_data: Dict, result: ValidationResult):
    """Warn if on_demand agents are in metadata instead of pipeline."""
    if not workflow_data:
        return
    metadata = workflow_data.get("metadata", {})
    if "on_demand" in metadata:
        result.add_warning("workflow.json: metadata.on_demand should be moved to pipeline.on_demand")


def validate_artifact_templates(artifacts_data: Dict, result: ValidationResult):
    """Warn about null template values that should be removed."""
    if not artifacts_data:
        return
    for artifact in artifacts_data.get("artifacts", []):
        if "template" in artifact and artifact.get("template") is None:
            filename = artifact.get("filename", "?")
            result.add_warning(f"artifacts.json: '{filename}' has template: null - remove field instead")


def validate_config_section(workflow_data: Dict, result: ValidationResult):
    """Check that config section exists with required sub-sections."""
    if not workflow_data:
        return
    config = workflow_data.get("config")
    if not config:
        result.add_warning("workflow.json: Missing 'config' section - add enforcement and logging config")
        return
    if "enforcement" not in config:
        result.add_warning("workflow.json: config.enforcement missing")
    if "logging" not in config:
        result.add_warning("workflow.json: config.logging missing")


def validate_stage_completeness(workflow_data: Dict, agent_ids: Set[str], result: ValidationResult):
    """Ensure stages are defined and agents are assigned."""
    if not workflow_data:
        return
    stages = workflow_data.get("stages", [])
    pipeline_order = set(workflow_data.get("pipeline", {}).get("order", []))
    
    if not stages and pipeline_order:
        result.add_warning("workflow.json: No stages defined - consider adding explicit stage assignments")
        return
    
    assigned_agents = set()
    for stage in stages:
        assigned_agents.update(stage.get("agents", []))
    
    unassigned = pipeline_order - assigned_agents
    if unassigned:
        result.add_warning(f"workflow.json: Agents not in any stage: {', '.join(sorted(unassigned))}")


def validate_slug_consistency(agents_data: Dict, instructions_data: Optional[Dict], result: ValidationResult):
    """Validate that slugs match between agents.json and instructions.json."""
    if not instructions_data:
        return
    
    agent_slugs = {a.get("id"): a.get("slug") for a in agents_data.get("agents", [])}
    
    for instr in instructions_data.get("instructions", []):
        instr_id = instr.get("id", "")
        instr_slug = instr.get("slug", "")
        
        if instr_id in agent_slugs:
            expected_slug = agent_slugs[instr_id]
            if expected_slug and instr_slug and expected_slug != instr_slug:
                result.add_error(f"instructions.json: Agent {instr_id} slug '{instr_slug}' doesn't match agents.json slug '{expected_slug}'")


def validate_pipeline_order(workflow_data: Dict, agent_ids: Set[str], result: ValidationResult):
    """Validate pipeline order references valid agents."""
    if not workflow_data:
        return
    
    pipeline = workflow_data.get("pipeline", {})
    order = pipeline.get("order", [])
    
    for agent_id in order:
        if agent_id not in agent_ids:
            result.add_error(f"workflow.json: Pipeline order references unknown agent '{agent_id}'")


def detect_circular_dependencies(agents_data: Dict, result: ValidationResult):
    """Detect circular dependencies in produces/consumes graph."""
    # Build dependency graph: agent -> set of agents it depends on
    agent_produces: Dict[str, Set[str]] = {}
    artifact_producer: Dict[str, str] = {}
    
    def extract_files(items: Any) -> Set[str]:
        """Extract file names from produces/consumes structure."""
        files = set()
        if isinstance(items, dict):
            for category_files in items.values():
                if isinstance(category_files, list):
                    for item in category_files:
                        if isinstance(item, dict):
                            files.add(item.get("file", ""))
                        elif isinstance(item, str):
                            files.add(item)
        elif isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    files.add(item.get("file", ""))
                elif isinstance(item, str):
                    files.add(item)
        return files
    
    # First pass: map artifacts to their producers
    for agent in agents_data.get("agents", []):
        agent_id = agent.get("id", "")
        produces = agent.get("produces", {})
        
        produced_files = extract_files(produces)
        
        agent_produces[agent_id] = produced_files
        for f in produced_files:
            if f:
                artifact_producer[f] = agent_id
    
    # Second pass: build dependency graph
    dependencies: Dict[str, Set[str]] = {aid: set() for aid in agent_produces}
    
    for agent in agents_data.get("agents", []):
        agent_id = agent.get("id", "")
        consumes = agent.get("consumes", {})
        
        consumed_files = extract_files(consumes)
        
        for f in consumed_files:
            if f and f in artifact_producer:
                producer = artifact_producer[f]
                if producer != agent_id:
                    dependencies[agent_id].add(producer)
    
    # Detect cycles using DFS
    def has_cycle(node: str, visited: Set[str], rec_stack: Set[str], path: List[str]) -> Optional[List[str]]:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for dep in dependencies.get(node, set()):
            if dep not in visited:
                cycle = has_cycle(dep, visited, rec_stack, path)
                if cycle:
                    return cycle
            elif dep in rec_stack:
                # Found cycle
                cycle_start = path.index(dep)
                return path[cycle_start:] + [dep]
        
        path.pop()
        rec_stack.remove(node)
        return None
    
    visited: Set[str] = set()
    for agent_id in dependencies:
        if agent_id not in visited:
            cycle = has_cycle(agent_id, visited, set(), [])
            if cycle:
                result.add_error(f"Circular dependency detected: {' -> '.join(cycle)}")
                break


def validate_workflow(workflow_name: str) -> ValidationResult:
    """Run all validations for a workflow."""
    result = ValidationResult(workflow=workflow_name)
    
    try:
        # Load all files using canonical loader
        manifests = load_canonical_workflow(workflow_name)
        agents_data = manifests["agents"]
        artifacts_data = manifests["artifacts"]
        instructions_data = manifests["instructions"]
        workflow_data = manifests["workflow"]
    except Exception as e:
        result.add_error(f"Failed to load workflow manifests: {e}")
        return result
    
    # Schema validation
    validate_schema(agents_data, SCHEMAS_DIR / "agents.schema.json", result, "agents.json")
    if artifacts_data:
        validate_schema(artifacts_data, SCHEMAS_DIR / "artifacts.schema.json", result, "artifacts.json")
    if instructions_data:
        validate_schema(instructions_data, SCHEMAS_DIR / "instructions.schema.json", result, "instructions.json")
    if workflow_data:
        validate_schema(workflow_data, SCHEMAS_DIR / "workflow.schema.json", result, "workflow.json")
    
    # Cross-reference validation
    agent_ids = validate_agent_ids(agents_data, result)
    
    artifact_filenames = set()
    if artifacts_data:
        artifact_filenames = validate_artifact_filenames(artifacts_data, agent_ids, result)
    
    if instructions_data:
        validate_instructions(instructions_data, agent_ids, result)
    
    # Produces/consumes validation with cross-workflow support
    if artifact_filenames:
        validate_produces_consumes(agents_data, artifact_filenames, workflow_data, result)
    
    if workflow_data:
        validate_pipeline_order(workflow_data, agent_ids, result)
        # New: Stage-agent validation
        validate_stage_agents(workflow_data, agent_ids, result)
        # New: Input_from validation
        validate_input_from_artifacts(workflow_data, result)
        # Additional checks for migration
        validate_deprecated_globals(workflow_data, result)
        validate_on_demand_placement(workflow_data, result)
        validate_config_section(workflow_data, result)
        validate_stage_completeness(workflow_data, agent_ids, result)
    
    # New: Cycle reference validation
    if instructions_data and workflow_data:
        validate_cycle_references(instructions_data, workflow_data, result)
    
    # New: Slug consistency validation
    if instructions_data:
        validate_slug_consistency(agents_data, instructions_data, result)
    
    # Artifact checks
    if artifacts_data:
        validate_artifact_templates(artifacts_data, result)

    # Dependency cycle detection
    detect_circular_dependencies(agents_data, result)
    
    return result


def main():
    """Main entry point for canonical validation CLI."""
    import argparse
    parser = argparse.ArgumentParser(description="Validate canonical JSON manifests")
    parser.add_argument('--workflow', '-w', help='Specific workflow to validate')
    parser.add_argument('--all', '-a', action='store_true', help='Validate all workflows')
    parser.add_argument('--check-cross-refs', action='store_true', help='Only check cross-references')
    parser.add_argument('--quiet', '-q', action='store_true', help='Only show errors')
    args = parser.parse_args()
    
    if not CANONICAL_DIR.exists():
        display_error(f"Canonical directory not found: {CANONICAL_DIR}")
        sys.exit(1)
    
    workflows = []
    if args.workflow:
        workflows = [args.workflow]
    elif args.all:
        workflows = [d.name for d in CANONICAL_DIR.iterdir() if d.is_dir()]
    else:
        # Default to all
        workflows = [d.name for d in CANONICAL_DIR.iterdir() if d.is_dir()]
    
    if not workflows:
        display_info("No workflows found to validate")
        sys.exit(0)
    
    all_passed = True
    results = []
    
    for wf in workflows:
        result = validate_workflow(wf)
        results.append(result)
        if not result.passed:
            all_passed = False
    
    # Print results
    for result in results:
        if args.quiet and result.passed:
            continue
        result.print_summary()
    
    # Final summary
    display_info(f"VALIDATION SUMMARY: {len(results)} workflow(s) checked")
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    display_success(f"Passed: {passed}")
    display_info(f"Failed: {failed}")
    
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
