"""Template engine for rendering Jinja2 templates."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from jinja2 import Environment, FileSystemLoader, ChoiceLoader, TemplateNotFound, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Environment = None
    FileSystemLoader = None
    ChoiceLoader = None
    TemplateNotFound = None
    select_autoescape = None

from agentic_workflow.core.exceptions import TemplateError
from .constants import TEMPLATES_DIR, WORKFLOWS_DIR


class TemplateEngine:
    """Infrastructure layer: Template loading and rendering.

    Responsibilities:
    - File system operations for template discovery
    - Jinja2 environment setup and configuration
    - Template rendering with error handling

    No knowledge of agents, workflows, or domain data.
    """

    def __init__(self, workflow: Optional[str] = None, workflow_root: Optional[Path] = None):
        """Initialize the template engine.

        Args:
            workflow: Workflow name for package-specific templates
            workflow_root: Custom workflow root path
        """
        if not JINJA2_AVAILABLE:
            raise ImportError(
                "Jinja2 is required for template rendering. "
                "Install with: pip install jinja2"
            )

        self.workflow = workflow
        self.workflow_root = workflow_root
        self._env = self._create_environment(workflow, workflow_root)

    def _create_environment(self, workflow: Optional[str] = None, workflow_root: Optional[Path] = None) -> Any:
        """Create Jinja2 environment with hierarchical loaders.

        Search order (highest to lowest priority):
        1. User Project: .agentic/templates/
        2. Workflow Package: manifests/workflows/{workflow}/templates/
        3. System Defaults: templates/ (via importlib.resources for packaging)
        """
        loaders = []
        searched_paths = []

        # 1. User Project Override (Highest Priority)
        try:
            from agentic_workflow.core.paths import find_project_root
            project_root = find_project_root()
            if project_root:
                user_templates = project_root / ".agentic" / "templates"
                if user_templates.exists():
                    loaders.append(FileSystemLoader(str(user_templates)))
                    searched_paths.append(str(user_templates))
        except ImportError:
            pass  # paths module should always be available

        # 2. Workflow Root Override
        if workflow_root and workflow_root.exists():
            loaders.append(FileSystemLoader(str(workflow_root)))
            searched_paths.append(str(workflow_root))

        # 3. Workflow Package Templates
        if workflow:
            wf_pkg_path = WORKFLOWS_DIR / workflow / "templates"
            if wf_pkg_path.exists():
                loaders.append(FileSystemLoader(str(wf_pkg_path)))
                searched_paths.append(str(wf_pkg_path))

        # 4. System Defaults (via importlib.resources for proper packaging support)
        try:
            from importlib import resources
            # Try package-relative path first (for installed packages)
            try:
                templates_path = resources.files('agentic_workflow') / 'templates'
                if templates_path.exists():
                    # Add _base subdirectory for base templates
                    base_templates = templates_path / "_base"
                    if base_templates.exists():
                        loaders.append(FileSystemLoader(str(base_templates)))
                        searched_paths.append(str(base_templates))
                    # Add main templates directory
                    loaders.append(FileSystemLoader(str(templates_path)))
                    searched_paths.append(str(templates_path))
            except (AttributeError, FileNotFoundError):
                # Fallback to filesystem path (for development)
                if TEMPLATES_DIR.exists():
                    # Add _base subdirectory for base templates
                    base_templates = TEMPLATES_DIR / "_base"
                    if base_templates.exists():
                        loaders.append(FileSystemLoader(str(base_templates)))
                        searched_paths.append(str(base_templates))
                    # Add main templates directory
                    loaders.append(FileSystemLoader(str(TEMPLATES_DIR)))
                    searched_paths.append(str(TEMPLATES_DIR))
        except ImportError:
            # Final fallback
            if TEMPLATES_DIR.exists():
                loaders.append(FileSystemLoader(str(TEMPLATES_DIR)))
                searched_paths.append(str(TEMPLATES_DIR))

        if not loaders:
            raise TemplateError(
                f"No template directories found. Searched paths: {searched_paths}",
                error_code="NO_TEMPLATE_DIRS"
            )

        # Store searched paths for error reporting
        self._searched_paths = searched_paths

        # Create environment
        env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Register custom filters
        self._register_filters(env)

        return env

    def _register_filters(self, env: Any) -> None:
        """Register custom Jinja2 filters for markdown formatting."""

        def md_list(items: List[str], prefix: str = "- ") -> str:
            """Format list as markdown bullet points."""
            if not items:
                return ""
            return "\n".join(f"{prefix}{item}" for item in items)

        def md_numbered_list(items: List[str]) -> str:
            """Format list as markdown numbered list."""
            if not items:
                return ""
            return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))

        def md_table(rows: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
            """Format list of dicts as markdown table."""
            if not rows:
                return ""
            if headers is None:
                headers = list(rows[0].keys())

            lines = []
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join("---" for _ in headers) + " |")

            for row in rows:
                values = [str(row.get(h, "")) for h in headers]
                lines.append("| " + " | ".join(values) + " |")

            return "\n".join(lines)

        def quote(text: str) -> str:
            """Wrap text in markdown quote."""
            if not text:
                return ""
            return "\n".join(f"> {line}" for line in text.split("\n"))

        def code(text: str, lang: str = "") -> str:
            """Wrap text in markdown code block."""
            return f"```{lang}\n{text}\n```"

        def slugify(text: str) -> str:
            """Convert text to URL-friendly slug."""
            text = text.lower()
            text = re.sub(r'[^\w\s-]', '', text)
            text = re.sub(r'[\s_]+', '-', text)
            return text.strip('-')

        def capitalize_first(text: str) -> str:
            """Capitalize first letter only."""
            if not text:
                return ""
            return text[0].upper() + text[1:]

        # Register all filters
        env.filters['md_list'] = md_list
        env.filters['md_numbered_list'] = md_numbered_list
        env.filters['md_table'] = md_table
        env.filters['quote'] = quote
        env.filters['code'] = code
        env.filters['slugify'] = slugify
        env.filters['capitalize_first'] = capitalize_first

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with context.

        Args:
            template_name: Template filename (e.g., 'agent_base.md.j2')
            context: Dictionary of template variables

        Returns:
            Rendered template string

        Raises:
            TemplateError: If template not found or rendering fails
        """
        try:
            template = self._env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound as e:
            raise TemplateError(
                f"Template '{template_name}' not found. Searched in: {self._searched_paths}",
                error_code="TEMPLATE_NOT_FOUND",
                context={"template": template_name, "searched_paths": self._searched_paths}
            ) from e
        except Exception as e:
            raise TemplateError(
                f"Template rendering failed for '{template_name}': {e}",
                error_code="TEMPLATE_RENDER_ERROR",
                context={"template": template_name}
            ) from e

    def render_string(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render a template string with context.

        Args:
            template_str: Template content as string
            context: Dictionary of template variables

        Returns:
            Rendered template string
        """
        try:
            template = self._env.from_string(template_str)
            return template.render(**context)
        except Exception as e:
            raise TemplateError(
                f"String template rendering failed: {e}",
                error_code="STRING_TEMPLATE_ERROR"
            ) from e

    def get_template_path(self, template_name: str) -> Optional[Path]:
        """Get the resolved path of a template.

        Args:
            template_name: Template filename

        Returns:
            Path to the resolved template, or None if not found
        """
        try:
            source, filename, _ = self._env.loader.get_source(self._env, template_name)
            return Path(filename) if filename else None
        except TemplateNotFound:
            return None

__all__ = ["TemplateEngine"]