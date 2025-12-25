"""Manage active session state and agent context switching for a project.

Manages the active session state, agent context switching, and project status updates.
"""

import datetime
import re
import yaml
import logging
from pathlib import Path
from typing import Tuple, Dict, Optional, Any, TypedDict

from ..core.project import load_project_meta
from ..core.exceptions import AgentNotFoundError, ProjectNotFoundError, WorkflowError
from ..generation.canonical_loader import load_workflow
from ..session import session_frontmatter as sf

from agentic_workflow.core.paths import AGENT_FILES_DIR

# Public API
__all__ = ["SessionManager"]


class FrontMatter(TypedDict, total=False):
    """Typed mapping for agent markdown frontmatter (title, role, description).

    The `metadata` field holds arbitrary, optional metadata extracted from
    the agent file frontmatter.
    """
    title: Optional[str]
    agent_role: Optional[str]
    description: Optional[str]
    metadata: Dict[str, object]


logger = logging.getLogger(__name__)

try:
    from ..utils.templating import TemplateEngine, ContextResolver
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    TemplateEngine = None
    ContextResolver = None



class SessionManager:
    """Manage agent sessions, load agent content, and update session state."""

    def __init__(self, project_dir: Path):
        """Initialize the SessionManager for `project_dir` and validate the project exists."""
        self.project_dir = project_dir
        if not self.project_dir.exists():
            raise ProjectNotFoundError(f"Project directory not found: {self.project_dir}")
        self.project_name = self.project_dir.name

    def get_workflow_name(self) -> str:
        """Retrieve the workflow name for the current project from metadata."""
        meta = load_project_meta(self.project_name)
        if meta and 'workflow' in meta:
            return meta['workflow']
        # Fallback: check config.yaml directly if meta load fails (though load_project_meta should handle this)
        return 'planning'

    def activate_agent(self, agent_id: str) -> None:
        """Activate an agent session and update session and project state."""
        workflow_name = self.get_workflow_name()
        logger.info(f"Activating Agent {agent_id} in {self.project_name} ({workflow_name})...")

        # 1. Load Workflow Package (The Source of Truth)
        try:
            wf = load_workflow(workflow_name)
        except WorkflowError as e:
            raise ProjectNotFoundError(f"Could not load workflow '{workflow_name}': {e}")

        # 2. Normalize ID using Workflow Rules
        # The workflow package knows if it should be 'A-01', 'A01', or 'I-1'
        agent_id_formatted = wf.format_agent_id(agent_id)
        
        # 3. Find Agent Definition
        agent_def = wf.get_agent(agent_id_formatted)
        if not agent_def:
            raise AgentNotFoundError(f"Agent '{agent_id}' (normalized: {agent_id_formatted}) not defined in workflow '{workflow_name}'")

        # 4. Load Content Deterministically
        content, filename = self._load_agent_file(agent_def, wf)
        logger.info(f"Loaded agent from {filename}")

        # 5. Parse Frontmatter (for title/role)
        frontmatter, _ = self._parse_agent_content(content)
        agent_role = frontmatter.get('agent_role', agent_def.get('role', 'Unknown'))
        
        # 6. Update Session File
        self._update_active_session_file(agent_id_formatted, workflow_name)

        # 7. Update Project Index
        agent_display = f"{agent_id_formatted} ({agent_role})"
        self._update_project_index(agent_display)
        
        logger.info(f"Activation complete: {agent_display}")

    def _load_agent_file(self, agent_def: Dict[str, Any], wf: Any) -> Tuple[str, str]:
        """Load the agent markdown file for the given agent definition and return its content and filename."""
        # Reconstruct filename logic to match what InitPipeline/Structure created
        # Standard: {ID}_{Role}.md (sanitized)
        agent_id = agent_def.get('id')
        role = agent_def.get('role', agent_def.get('slug', 'agent'))
        
        # We need to match the filename generation logic from generate_agents.py
        # Assuming simple sanitation here or looking for partial match if strict name is unknown
        
        # 1. Try exact standard name first
        filename = f"{agent_id}_{role}.md"
        # Sanitize filename (basic)
        filename = filename.replace(" ", "_").replace("/", "-")
        
        target_file = self.project_dir / 'agent_files' / filename
        
        if target_file.exists():
            return target_file.read_text(encoding='utf-8'), target_file.name

        # 2. Try without dash (legacy format)
        alt_filename = f"{agent_id.replace('-', '')}_{role}.md".replace(" ", "_").replace("/", "-")
        alt_file = self.project_dir / 'agent_files' / alt_filename
        if alt_file.exists():
            return alt_file.read_text(encoding='utf-8'), alt_file.name

        # 3. Fallback: Search by ID prefix if exact name doesn't match
        # (Handles cases where role name might have different spacing/sanitization)
        search_dir = self.project_dir / 'agent_files'
        if search_dir.exists():
            for f in search_dir.glob("*.md"):
                if f.name.startswith(f"{agent_id}_") or f.name.startswith(f"{agent_id.replace('-', '')}_"):
                    return f.read_text(encoding='utf-8'), f.name

        raise AgentNotFoundError(
            f"Agent file for '{agent_id}' not found in {search_dir}. "
            f"Expected '{filename}' or '{alt_filename}' or '{agent_id}_*.md'"
        )

    def _parse_agent_content(self, content: str) -> Tuple["FrontMatter", str]:
        """Parse YAML frontmatter from an agent markdown file and return the frontmatter and body."""
        fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        frontmatter: FrontMatter = yaml.safe_load(fm_match.group(1)) if fm_match else {}
        body_match = re.search(r"\n---\n(.*)", content, re.DOTALL)
        body = body_match.group(1).strip() if body_match else content
        return frontmatter, body

    def _update_active_session_file(self, agent_id: str, workflow_name: str) -> None:
        """Render the active session template and write the session file to disk."""
        session_path = self.project_dir / "agent_context" / "active_session.md"
        session_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not JINJA2_AVAILABLE:
             raise ImportError("Jinja2 is required for session rendering")
             
        engine = TemplateEngine(workflow=workflow_name)
        resolver = ContextResolver()
        context = resolver.get_session_context(
            workflow=workflow_name,
            agent_id=agent_id,
            project_name=self.project_name,
            timestamp=datetime.datetime.now().isoformat()
        )
        content = engine.render("_base/session_base.md.j2", context)
        session_path.write_text(content, encoding='utf-8')


    def _update_project_index(self, agent_role: str) -> None:
        """Update the project's `project_index.md` with the current active agent and timestamp."""
        index_path = self.project_dir / "project_index.md"
        if not index_path.exists():
            logger.warning("project_index.md not found, skipping status update")
            return
            
        try:
            content = index_path.read_text(encoding='utf-8')
            
            # Update Active Agent line
            # Pattern matches "**Active Agent:** <anything up to newline>"
            if "**Active Agent:**" in content:
                content = re.sub(
                    r"\*\*Active Agent:\*\*.*", 
                    f"**Active Agent:** {agent_role}", 
                    content
                )
            
            # Update Last Action line
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if "**Last Action:**" in content:
                content = re.sub(
                    r"\*\*Last Action:\*\*.*", 
                    f"**Last Action:** Session started ({timestamp})", 
                    content
                )
            
            index_path.write_text(content, encoding='utf-8')
            
        except Exception as e:
            logger.error(f"Failed to update project index: {e}")