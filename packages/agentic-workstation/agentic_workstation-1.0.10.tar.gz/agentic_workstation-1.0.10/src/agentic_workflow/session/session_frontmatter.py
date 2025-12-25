"""Helper utilities for building, merging, and rendering session YAML frontmatter.

Centralizes the logic so multiple scripts don't duplicate YAML handling.
"""
from pathlib import Path
import datetime
import yaml
import re

try:
    from agentic_workflow.utils.templating import TemplateEngine, ContextResolver
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    TemplateEngine = None
    ContextResolver = None

__all__ = [
    "merge_frontmatter",
    "render_frontmatter_yaml", 
    "load_frontmatter_from_text",
    "build_orchestrator_session_from_template",
]


def merge_frontmatter(session_fm: dict, agent_fm: dict, project_name: str = None) -> dict:
    """Merge agent frontmatter into session frontmatter with simplified keys.

    Produces a lean frontmatter with 8 essential fields:
    - project, agent_id, agent_slug, agent_role
    - context_file, consumes, produces, last_activated

    Returns the merged dict (does not write files).
    """
    session = dict(session_fm or {})
    agent = dict(agent_fm or {})

    # Determine project name from session or parameter
    proj = project_name or session.get('project', '')

    id_val = agent.get('agent_id')
    if id_val is None:
        id_str = ""
    else:
        id_str = str(id_val).zfill(2)

    # Agent role can come from multiple fields: agent_role, title, or existing session
    agent_role = agent.get('agent_role') or agent.get('title') or session.get('agent_role')
    slug = agent.get('agent_slug') or agent.get('slug') or (agent_role or '').lower().replace(' ', '_').replace('&', 'and') or f"agent_{id_str}"
    
    consumes = agent.get('consumes', session.get('consumes', []))
    produces = agent.get('produces', session.get('produces', []))
    
    # Compute context_file dynamically from slug
    context_file = agent.get('context_file')
    if not context_file and slug:
        context_file = f"agent_context/{slug}_context_index.md"
    elif not context_file:
        context_file = session.get('context_file', 'agent_context/orchestrator_context_index.md')

    # Simplified frontmatter - 8 essential fields
    return {
        'project': proj,
        'agent_id': id_str or session.get('agent_id', '00'),
        'agent_slug': slug,
        'agent_role': agent_role,
        'context_file': context_file,
        'consumes': consumes,
        'produces': produces,
        'last_activated': datetime.datetime.now().isoformat(),
    }


def render_frontmatter_yaml(fm: dict) -> str:
    """Return a YAML string block with leading/trailing '---' markers."""
    fm_yaml = yaml.dump(fm, sort_keys=False, default_flow_style=False, width=1000)
    return f"---\n{fm_yaml}---\n"


def load_frontmatter_from_text(text: str) -> dict:
    """Parse YAML frontmatter from text if present, else return {}."""
    import re

    fm_match = re.search(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if fm_match:
        try:
            return yaml.safe_load(fm_match.group(1)) or {}
        except Exception:
            return {}
    return {}


def build_orchestrator_session_from_template(workflow: str, project_name: str, agent_id: str = None, timestamp: str = "", extra_subs: dict | None = None, fm_extra: dict | None = None) -> str:
    """Build orchestrator session content from Jinja2 templates.
    
    Renders the complete session document including frontmatter and content layers
    for the orchestrator agent using workflow-specific templates.
    
    Args:
        workflow: Workflow name (e.g., 'planning', 'implementation')
        project_name: Name of the project
        agent_id: Agent identifier (e.g., 'A-00', 'I-00'). If None, uses first agent from workflow pipeline
        timestamp: Session timestamp (ISO format)
        extra_subs: Additional template substitutions
        fm_extra: Extra frontmatter fields
        
    Returns:
        Rendered session content as string with frontmatter and markdown content
    """
    if not JINJA2_AVAILABLE:
        raise ImportError("Jinja2 is required. Please install with: pip install jinja2")

    # If agent_id is not provided, get first agent from workflow pipeline order
    if agent_id is None:
        from agentic_workflow.generation.canonical_loader import load_canonical_workflow
        workflow_data = load_canonical_workflow(workflow, return_object=False)
        pipeline_order = workflow_data.get('workflow', {}).get('pipeline', {}).get('order', [])
        agent_id = pipeline_order[0] if pipeline_order else 'A-00'

    engine = TemplateEngine(workflow=workflow)
    resolver = ContextResolver()
    context = resolver.get_session_context(
        workflow=workflow,
        agent_id=agent_id,
        project_name=project_name,
        timestamp=timestamp,
        extra_subs=extra_subs
    )
    return engine.render("session_base.md.j2", context)


def ensure_context_file(project_dir: Path, context_file: str, agent_data: dict, templates_dir: Path = None) -> bool:
    """Ensure the agent's context file exists. Creates from template if missing.
    
    IMPORTANT: Does NOT overwrite existing context files to preserve agent state.
    
    Args:
        project_dir: Path to the project directory
        context_file: Relative path like 'agent_context/planning_context_index.md'
        agent_data: Dict with agent_id, agent_role, produces, etc.
        templates_dir: Optional path to templates directory
        
    Returns:
        True if file was created, False if it already existed
    """
    from agentic_workflow.core.paths import get_templates_dir
    
    context_path = project_dir / context_file
    
    # CRITICAL: Do not overwrite existing context files
    if context_path.exists():
        return False
    
    # Ensure parent directory exists
    context_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use ConfigurationService to get template paths
    if templates_dir is None:
        templates_dir = get_templates_dir()
    
    # Try to render using TemplateEngine with established context building
    try:
        # Get workflow from agent_data or project context
        workflow = agent_data.get('workflow', 'planning')  # Default fallback
        
        # Use ContextResolver for proper context building
        resolver = ContextResolver()
        agent_id = agent_data.get('agent_id', agent_data.get('active_agent_id', 'A-00'))
        
        # Build context using established patterns
        context = resolver.get_agent_context(
            workflow=workflow,
            agent_id=agent_id,
            project_name=agent_data.get('project', project_dir.name)
        )
        
        # Add additional context fields for context file
        now = datetime.datetime.now().isoformat()
        context.update({
            'created_at': now,
            'last_updated': now,
            'status': 'Initialized',
            'iteration': '1',
            'context_file': context_file,
            'log_file': agent_data.get('log_file', 'agent_log/exchange_log.md'),
        })
        
        # Try to render using TemplateEngine
        engine = TemplateEngine(workflow=workflow)
        content = engine.render("agent_context_index.md.j2", context)
        
    except Exception as e:
        # Fallback to minimal template if TemplateEngine fails
        print(f"Warning: TemplateEngine failed for context file, using fallback: {e}")
        
        # Get agent info using established patterns where possible
        agent_id = agent_data.get('agent_id', agent_data.get('active_agent_id', 'A-00'))
        agent_role = agent_data.get('agent_role', agent_data.get('active_agent', 'Unknown'))
        produces = agent_data.get('produces', [])
        now = datetime.datetime.now().isoformat()
        
        # Build artifact rows from produces
        artifact_rows = []
        for artifact in produces:
            if isinstance(artifact, str):
                name = artifact.split('/')[-1]  # Get filename
                artifact_rows.append(f"| `{name}` | Not Started | - |")
        
        if not artifact_rows:
            artifact_rows.append("| (none defined) | - | - |")
        
        # Use established context building for artifact directory
        artifact_dir = f"artifacts/{agent_id.replace('-', '')}_*" if '-' in agent_id else f"artifacts/{agent_id}_*"
        
        if produces:
            for p in produces:
                if isinstance(p, dict) and p.get('filename'):
                    artifact_dir = f"artifacts/{p['filename']}"
                    break
                elif isinstance(p, str) and p.startswith('artifacts/'):
                    parts = p.split('/')
                    if len(parts) >= 2:
                        artifact_dir = f"artifacts/{parts[1]}"
                        break
        
        # Minimal fallback template
        content = f"""# Agent Context: {agent_role}

> **Agent ID:** {agent_id}  
> **Created:** {now}

## Session Progress

### Active Tasks
- [ ] Review upstream artifacts
- [ ] Analyze inputs from `consumes`
- [ ] Draft primary outputs

## Artifact Tracker

| Artifact | Status | Notes |
|----------|--------|-------|
{chr(10).join(artifact_rows)}

## Notes & Scratchpad

- Agent activated at {now}
"""
    
    context_path.write_text(content)
    
    # Create YAML sidecar for the context file
    yaml_path = context_path.with_suffix('.yaml')
    if not yaml_path.exists():
        yaml_data = {
            'agent_id': agent_id,
            'agent_role': agent_role,
            'project': agent_data.get('project', project_dir.name),
            'created': now,
            'last_updated': now,
            'status': 'Initialized',
            'iteration': 1,
            'tasks': {
                'active': [],
                'completed': [],
                'blocked': [],
            },
            'artifacts': [],
            'decisions_local': [],
            'assumptions_local': [],
            'questions': [],
        }
        with open(yaml_path, 'w') as f:
            yaml.safe_dump(yaml_data, f, sort_keys=False)
    
    return True