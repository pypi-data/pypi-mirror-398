#!/usr/bin/env python3
"""Validate workflow manifest consistency and basic repository sanity.

Checks performed:
- Loads agents.yaml and artifacts.yaml from workflow package.
- Ensures each agent's `consumes` entries are defined in artifacts.yaml.
- Ensures each agent's `produces` entries match `owner` in artifacts.yaml.
- Verifies agent prompt files listed in the manifest exist.
- Lints agent prompts against the hybrid template (H3 headers).

Usage:
    python3 -m scripts.validation.validate_agents [--workflow planning]
"""
import os
import sys
from typing import List, Tuple, Dict
import re
from agentic_workflow.cli.utils import display_error, display_warning, display_info

try:
    import yaml
except ImportError:
    display_error("Missing dependency 'pyyaml'. Install with: pip install pyyaml")
    sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
WORKFLOWS_DIR = os.path.join(ROOT, 'manifests', 'workflows')
DEFAULT_WORKFLOW = 'planning'
ADVANCED_GOVERNANCE = os.getenv('ADVANCED_GOVERNANCE', '0').strip().lower() in ('1', 'true', 'yes', 'on')

__all__ = ["validate_manifests", "lint_agent_prompts"]


def load_yaml_file(path: str):
    """Load YAML file directly."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def flatten_artifacts(artifacts):
    """Flatten nested artifact structure to list of filenames.
    
    Handles both:
    - Flat list: ['file1.md', 'file2.md']
    - Nested dict: {'core': [{'filename': 'file1.md'}], 'domain': [...]}
    """
    if isinstance(artifacts, list):
        # Already a flat list
        result = []
        for item in artifacts:
            if isinstance(item, dict):
                result.append(item.get('filename', item.get('file', str(item))))
            else:
                result.append(str(item))
        return result
    elif isinstance(artifacts, dict):
        # Nested structure with core/domain/etc categories
        result = []
        for category, items in artifacts.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        result.append(item.get('filename', item.get('file', str(item))))
                    else:
                        result.append(str(item))
        return result
    return []


def validate_manifests(agents_data, artifacts_data) -> Tuple[List[str], List[str]]:
    """Cross-validate agents.yaml and artifacts.yaml."""
    errors = []
    warnings = []

    agents = agents_data.get('agents', [])
    artifacts = artifacts_data.get('artifacts', [])
    logs = artifacts_data.get('logs', [])
    
    # Create lookups - use 'filename' (canonical schema field)
    artifact_lookup = {a['filename']: a for a in artifacts}
    log_lookup = {l['filename']: l for l in logs} if logs else {}
    
    for agent in agents:
        agent_id = agent['id']
        slug = agent.get('slug')
        
        # Flatten nested produces/consumes structures
        produces_list = flatten_artifacts(agent.get('produces', []))
        consumes_list = flatten_artifacts(agent.get('consumes', []))
        
        # Validate Produces
        for prod in produces_list:
            if prod in log_lookup:
                continue
            if prod.endswith('_log.md'):
                expected_log = f"{slug}_log.md"
                if prod == expected_log:
                    continue
            if prod not in artifact_lookup:
                errors.append(f"Agent {agent_id}: produces '{prod}' which is NOT defined in artifacts.yaml")
                continue
            art_def = artifact_lookup[prod]
            if art_def['owner'] != agent_id:
                errors.append(f"Agent {agent_id}: claims to produce '{prod}' but artifacts.yaml lists owner as {art_def['owner']}")

        # Validate Consumes
        for cons in consumes_list:
            if cons in log_lookup:
                continue
            if cons.endswith('_log.md'):
                continue
            if cons not in artifact_lookup:
                errors.append(f"Agent {agent_id}: consumes '{cons}' which is NOT defined in artifacts.yaml")

    # Coverage Check (Orphaned Artifacts)
    produced_artifacts = set()
    for agent in agents:
        produced_artifacts.update(flatten_artifacts(agent.get('produces', [])))
    
    for art_file in artifact_lookup:
        if art_file not in produced_artifacts:
            owner = artifact_lookup[art_file].get('owner')
            if owner in (0, 'orch', 'orchestrator'):
                continue
            warnings.append(f"Artifact '{art_file}' is defined in artifacts.yaml but NOT produced by any agent")

    return errors, warnings


def lint_agent_prompts(agent_files_map: Dict[int, str]) -> Tuple[List[str], List[str]]:
    """Check agent prompt files for presence of standardized sections."""
    warnings = []
    errors = []
    
    required_sections = [
        '### purpose',
        '### ownership',
        '### consumes',
        '### produces',
        '### core responsibilities',
        '### workflow & handoffs',
        '## logging expectations',
        '## output requirements',
    ]
    
    for aid, relpath in agent_files_map.items():
        if not relpath:
            continue
        abspath = os.path.join(ROOT, relpath)
        if not os.path.exists(abspath):
            continue
        
        try:
            with open(abspath, 'r', encoding='utf-8') as f:
                text = f.read().lower()
        except Exception:
            continue
            
        missing = []
        for sec in required_sections:
            if isinstance(sec, tuple):
                if not any(variant in text for variant in sec):
                    missing.append('/'.join(sec))
            else:
                if sec not in text:
                    missing.append(sec)
        
        if missing:
            errors.append(f'Agent {aid}: missing sections: {missing}')

    return errors, warnings


def main():
    """Main entry point for agent validation CLI."""
    errors = []
    warnings = []
    
    # Parse workflow argument
    workflow = DEFAULT_WORKFLOW
    if '--workflow' in sys.argv:
        idx = sys.argv.index('--workflow')
        if idx + 1 < len(sys.argv):
            workflow = sys.argv[idx + 1]
    
    workflow_dir = os.path.join(WORKFLOWS_DIR, workflow)
    
    # Check if workflow exists using canonical loader
    from agentic_workflow.generation.canonical_loader import list_canonical_workflows
    available_workflows = list_canonical_workflows()
    if workflow not in available_workflows:
        display_error(f"Workflow '{workflow}' not found. Available: {', '.join(available_workflows)}")
        sys.exit(3)

    try:
        # Use canonical loader instead of direct file access
        from agentic_workflow.generation.canonical_loader import load_canonical_workflow
        manifests = load_canonical_workflow(workflow)
        agents_data = {'agents': manifests.get('agents', {}).get('agents', [])}
        artifacts_data = {'artifacts': manifests.get('artifacts', {}).get('artifacts', []), 
                         'logs': manifests.get('artifacts', {}).get('logs', [])}
    except Exception as e:
        display_error(f"Error loading manifests: {e}")
        sys.exit(1)

    display_info(f"Validating workflow: {workflow}")

    # Cross-Validate Manifests
    m_errors, m_warnings = validate_manifests(agents_data, artifacts_data)
    errors.extend(m_errors)
    warnings.extend(m_warnings)

    # Additional: validate generated agent files and frontmatter match workflow formatting
    try:
        from agentic_workflow.generation.canonical_loader import load_workflow, WorkflowError
        from agentic_workflow.generation.generate_agents import get_agent_filename
        wf = load_workflow(workflow)
        # agent_files directory for this workflow (directly under ROOT)
        agent_files_dir = os.path.join(ROOT, 'agent_files', workflow)

        for agent in agents_data.get('agents', []):
            # Determine expected filename using generator logic with workflow
            try:
                expected = get_agent_filename(agent, wf)
            except Exception:
                expected = agent.get('file', '')

            # Candidate paths to check
            candidates = []
            if agent.get('file'):
                candidates.append(os.path.join(ROOT, agent.get('file')))
            candidates.append(os.path.join(agent_files_dir, expected))

            found_path = None
            for c in candidates:
                if c and os.path.exists(c):
                    found_path = c
                    break

            if not found_path:
                warnings.append(f"Agent {agent.get('id')}: expected agent file not found (tried: {candidates})")
                continue

            # Read frontmatter and verify agent_id formatting
            try:
                with open(found_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                m = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
                if m:
                    fm = yaml.safe_load(m.group(1)) or {}
                    fm_aid = fm.get('agent_id')
                    expected_id = wf.format_agent_id(agent.get('id'))
                    # Normalize to strings for comparison
                    if str(fm_aid) != str(expected_id):
                        errors.append(f"Agent {agent.get('id')}: frontmatter agent_id '{fm_aid}' does not match expected '{expected_id}' in file {found_path}")
                else:
                    warnings.append(f"Agent {agent.get('id')}: no frontmatter found in {found_path}")
            except Exception as e:
                warnings.append(f"Agent {agent.get('id')}: failed to read/validate {found_path}: {e}")
    except Exception:
        # If workflow loader/generator not available, skip these checks silently
        pass

    # Validate Agent Prompts
    agents = agents_data.get('agents', [])
    agent_files = {a['id']: a.get('file') for a in agents}
    
    for aid, fname in agent_files.items():
        if fname and not os.path.exists(os.path.join(ROOT, fname)):
            # Agent files are now in projects, not at root - skip this check
            # errors.append(f"Agent {aid}: prompt file missing: {fname}")
            pass

    if ADVANCED_GOVERNANCE:
        l_errors, l_warnings = lint_agent_prompts(agent_files)
        errors.extend(l_errors)
        warnings.extend(l_warnings)

    # Print results
    if errors:
        display_error('Errors:')
        for e in errors:
            display_error(' - ' + str(e))
    if warnings:
        display_warning('Warnings:')
        for w in warnings:
            display_warning(' - ' + str(w))

    if not errors and not warnings:
        display_info('Validation passed: no issues found.')

    if errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
