"""
Project service for Agentic Workflow Platform.

This service handles project-related operations like initialization,
activation, and management.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Use tomllib for TOML files (Python 3.11+), fallback to tomli for older versions
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from ..core.exceptions import (
    ProjectError, ProjectNotFoundError,
    validate_required
)
from ..core.config_service import ConfigurationService
from ..core.models import PipelineResult
from ..session.gate_checker import GateChecker
from ..generators.pipeline import InitPipeline
from ..utils.templating import TemplateEngine
from ..ledger.entry_builders import get_timestamp
from ..core.io import write_file, read_file

logger = logging.getLogger(__name__)

__all__ = ["ProjectService"]


class ProjectService:
    """Manages project lifecycle operations including initialization, activation, and management."""

    def __init__(self, config=None):
        """Initialize the ProjectService with configuration and gate checker."""
        if config:
            self.config = config
        else:
            self.config_service = ConfigurationService()
            self.config = self.config_service.load_config()
        
        self.gate_checker = GateChecker(self.config)

    def init_project(
        self,
        project_name: str,
        workflow_name: Optional[str] = None,
        description: Optional[str] = None,
        force: bool = False
    ) -> PipelineResult:
        """
        Initialize a new project.

        Args:
            project_name: Name of the project to create
            workflow_name: Workflow type (default: from registry)
            description: Project description
            force: Overwrite existing project if True

        Returns:
            PipelineResult with initialization results

        Raises:
            ProjectError: If initialization fails
        """
        validate_required(project_name, "project_name", "init_project")

        # Check if project already exists
        if self.project_exists(project_name) and not force:
            raise ProjectError(
                f"Project '{project_name}' already exists. Use force=True to overwrite.",
                error_code="PROJECT_EXISTS",
                context={"project": project_name}
            )

        # Resolve target path
        target_path = self.config.system.default_workspace / project_name

        # Initialize project using pipeline
        pipeline = InitPipeline(self.config)
        if description is not None:
            result = pipeline.run(project_name, str(target_path), workflow_name or "planning", force=force, description=description)
        else:
            result = pipeline.run(project_name, str(target_path), workflow_name or "planning", force=force)

        # Update project index with current state (populates artifact registry)
        if result.success:
            try:
                self.update_project_index(project_name)
            except Exception as e:
                logger.warning(f"Failed to update project index after initialization: {e}")

        return result

    def project_exists(self, project_name: str) -> bool:
        """
        Check if a project exists.

        Args:
            project_name: Name of the project

        Returns:
            True if project exists, False otherwise
        """
        validate_required(project_name, "project_name", "project_exists")

        from ..core.paths import find_repo_root
        repo_root = find_repo_root()
        # Use the default workspace from system config
        projects_dir = self.config.system.default_workspace
        project_path = projects_dir / project_name
        return project_path.exists() and project_path.is_dir()

    def refresh_project(self, project_name: str) -> PipelineResult:
        """
        Refresh an existing project.

        Args:
            project_name: Name of the project

        Returns:
            PipelineResult with refresh results

        Raises:
            ProjectError: If refresh fails
        """
        validate_required(project_name, "project_name", "refresh_project")

        if not self.project_exists(project_name):
            raise ProjectNotFoundError(f"Project '{project_name}' not found")

        # Determine project_path
        projects_dir = Path(self.config.system.default_workspace)
        project_path = projects_dir / project_name

        # Retrieve workflow name from project config
        config_data = self._load_project_config(project_path / '.agentic' / 'config')
        workflow_name = config_data.get('workflow', 'unknown')
        if workflow_name == 'unknown':
            raise ProjectError(f"Could not determine workflow for project '{project_name}'")

        # Execute refresh
        pipeline = InitPipeline(self.config)
        result = pipeline.refresh(project_name, project_path, workflow_name)

        return result

    def _get_agent_stage(self, project_name: str, agent_id: str) -> Optional[str]:
        """Get the stage an agent belongs to."""
        try:
            project_meta = self._load_project_config(Path(self.config.system.default_workspace) / project_name / '.agentic' / 'config')
            workflow_name = project_meta.get('workflow', 'planning')
            
            from ..generation.canonical_loader import load_workflow
            workflow_data = load_workflow(workflow_name)
            agents = workflow_data.agents
            agent = next((a for a in agents if a.get("id") == agent_id), {})
            stage = agent.get("stage")
            if stage:
                return stage
            # If no stage in agent, look in stages metadata
            stages = workflow_data.metadata.get('stages', [])
            for stage_info in stages:
                if agent_id in stage_info.get('agents', []):
                    return stage_info.get('id')
            return ""
        except Exception:
            return ""

    def _get_current_stage(self, project_name: str) -> str:
        """Get the current stage of a project."""
        project_meta = self._load_project_config(Path(self.config.system.default_workspace) / project_name / '.agentic' / 'config')
        current_stage = project_meta.get('current_stage')
        
        if current_stage:
            return current_stage
        
        # Default to first stage of the workflow
        workflow_name = project_meta.get('workflow', 'planning')
        try:
            from ..generation.canonical_loader import load_workflow
            wf = load_workflow(workflow_name)
            stages = wf.metadata.get('stages', [])
            if stages:
                return stages[0].get('id', 'INTAKE')
        except Exception:
            pass
        
        return 'INTAKE'

    def activate_agent(self, project_name: str, agent_id: str) -> Dict[str, Any]:
        """
        Activate an agent in a project.

        Args:
            project_name: Name of the project
            agent_id: ID of the agent to activate

        Returns:
            Dictionary with activation results

        Raises:
            ProjectError: If activation fails
        """
        validate_required(project_name, "project_name", "activate_agent")
        validate_required(agent_id, "agent_id", "activate_agent")

        if not self.project_exists(project_name):
            raise ProjectNotFoundError(f"Project '{project_name}' not found")

        # Get agent definition for role
        project_meta = self._load_project_config(Path(self.config.system.default_workspace) / project_name / '.agentic' / 'config')
        workflow_name = project_meta.get('workflow', 'planning')
        from ..generation.canonical_loader import load_workflow
        wf = load_workflow(workflow_name)
        agent_id_formatted = wf.format_agent_id(agent_id)
        agent_def = wf.get_agent(agent_id_formatted)
        role = agent_def.get('role', 'Unknown') if agent_def else 'Unknown'

        # Check if agent belongs to different stage and auto-advance if needed
        agent_stage = self._get_agent_stage(project_name, agent_id)
        current_stage = self._get_current_stage(project_name)
        
        stage_advanced = False
        if agent_stage and agent_stage != current_stage:
            # Validate stage transition before auto-advancing
            from ..session.stage_manager import validate_transition
            validation_result = validate_transition(project_name, agent_stage)
            
            if not validation_result['valid']:
                if self.config.project.strict_mode:
                    from ..core.exceptions import GovernanceError
                    raise GovernanceError(
                        f"Cannot auto-advance to stage '{agent_stage}' from '{current_stage}': {validation_result['message']}. "
                        f"Complete current stage requirements before activating agent {agent_id}."
                    )
                else:
                    logger.warning(f"Stage transition validation failed, proceeding in lenient mode: {validation_result['message']}")
            
            # Auto-advance to agent's stage (use force only in lenient mode if validation failed)
            from ..session.stage_manager import set_stage
            force_mode = not validation_result['valid'] and not self.config.project.strict_mode
            stage_result = set_stage(project_name, agent_stage, force=force_mode)
            if stage_result.get('success'):
                logger.info(f"Auto-advanced stage from {current_stage} to {agent_stage} for agent {agent_id}")
                stage_advanced = True
            else:
                logger.warning(f"Failed to auto-advance stage: {stage_result.get('error')}")

        from ..core.paths import find_repo_root
        repo_root = find_repo_root()
        projects_dir = repo_root / self.config.system.default_workspace
        project_path = projects_dir / project_name

        if not project_path.exists():
             raise ProjectNotFoundError(f"Project directory '{project_name}' not found at {project_path}")

        from ..core.session_manager import SessionManager
        try:
            manager = SessionManager(project_path)
            manager.activate_agent(agent_id)
            
            # Update project index with new state
            self.update_project_index(project_name)
            
        except Exception as e:
            raise ProjectError(f"Activation failed: {e}", cause=e)

        return {
            'project_name': project_name,
            'agent_id': agent_id,
            'role': role,
            'session_id': agent_id_formatted,
            'status': 'activated',
            'stage_advanced': stage_advanced,
            'previous_stage': current_stage if stage_advanced else None,
            'current_stage': agent_stage if stage_advanced else current_stage
        }

    def update_project_index(self, project_name: str) -> Dict[str, Any]:
        """
        Update the project_index.md file with current project state.

        Args:
            project_name: Name of the project

        Returns:
            Dictionary with update results

        Raises:
            ProjectError: If update fails
        """
        validate_required(project_name, "project_name", "update_project_index")

        if not self.project_exists(project_name):
            raise ProjectNotFoundError(f"Project '{project_name}' not found")

        try:
            # Get project path
            from ..core.paths import find_repo_root
            repo_root = find_repo_root()
            projects_dir = repo_root / self.config.system.default_workspace
            project_path = projects_dir / project_name

            # Load project config
            project_meta = self._load_project_config(project_path / '.agentic' / 'config')
            workflow_name = project_meta.get('workflow', 'planning')

            # Load workflow data
            from ..generation.canonical_loader import load_workflow
            wf = load_workflow(workflow_name)

            # Get current state
            current_phase = self._get_current_stage(project_name)
            active_agent = self._get_active_agent(project_name)
            last_action = self._get_last_action(project_name)

            # Get workflow metadata
            workflow_display_name = wf.display_name
            workflow_version = wf.version

            # Build artifact registry
            registry_entries = self._build_artifact_registry(project_path, wf)

            # Build context for template
            context = {
                'project_name': project_name,
                'workflow_name': workflow_name,
                'workflow_display_name': workflow_display_name,
                'workflow_version': workflow_version,
                'timestamp': get_timestamp(),
                'registry_entries': registry_entries,
                'current_phase': current_phase,
                'active_agent': active_agent,
                'last_action': last_action
            }

            # Render template
            from ..utils.templating import TemplateEngine
            loader = TemplateEngine(workflow=workflow_name)
            content = loader.render('_base/project_index.md.j2', context)

            # Write updated file
            index_path = project_path / 'project_index.md'
            write_file(index_path, content)

            return {
                'project_name': project_name,
                'status': 'updated',
                'index_path': str(index_path),
                'current_phase': current_phase,
                'active_agent': active_agent,
                'last_action': last_action
            }

        except Exception as e:
            logger.error(f"Failed to update project index for '{project_name}': {e}")
            raise ProjectError(f"Failed to update project index: {e}", cause=e)

    def _build_artifact_registry(self, project_path: Path, workflow_package) -> list:
        """
        Build the artifact registry from the project's artifacts directory.

        Args:
            project_path: Path to the project directory
            workflow_package: WorkflowPackage with agent information

        Returns:
            List of registry entries with name, owner, and description
        """
        registry_entries = []
        artifacts_dir = project_path / 'artifacts'

        if not artifacts_dir.exists():
            return registry_entries

        # Build agent lookup for role information
        agent_lookup = {}
        if hasattr(workflow_package, 'agents') and workflow_package.agents:
            for agent in workflow_package.agents:
                agent_id = agent.get('id', '')
                if agent_id:
                    agent_lookup[agent_id] = {
                        'role': agent.get('role', 'Unknown'),
                        'slug': agent.get('slug', 'unknown')
                    }

        # Scan artifact directories
        for agent_dir in artifacts_dir.iterdir():
            if not agent_dir.is_dir():
                continue

            # Extract agent ID from directory name (e.g., "A-01_incubation" -> "A-01")
            agent_id = agent_dir.name.split('_')[0] if '_' in agent_dir.name else agent_dir.name

            # Get agent info
            agent_info = agent_lookup.get(agent_id, {'role': f'Agent {agent_id}', 'slug': 'unknown'})
            agent_role = agent_info['role']

            # Scan files in this agent's directory (recursively)
            for file_path in agent_dir.rglob('*.md'):
                if file_path.is_file():
                    # Create human-readable name from filename
                    filename = file_path.name
                    name = filename.replace('.md', '').replace('_', ' ').title()

                    # Create description based on agent and file
                    description = f"Created by {agent_role}"

                    registry_entries.append({
                        'name': name,
                        'owner': agent_role,
                        'description': description
                    })

        # Sort by owner (agent role) for consistent ordering
        registry_entries.sort(key=lambda x: x['owner'])

        return registry_entries

    def _get_active_agent(self, project_name: str) -> str:
        """Get the currently active agent for a project."""
        try:
            from ..core.paths import find_repo_root
            repo_root = find_repo_root()
            projects_dir = repo_root / self.config.system.default_workspace
            project_path = projects_dir / project_name

            # Read active session to get current agent
            session_path = project_path / 'agent_context' / 'active_session.md'
            if session_path.exists():
                content = read_file(session_path)
                # Extract agent_id from frontmatter
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('agent_id:'):
                        return line.split(':', 1)[1].strip()
            return 'None'
        except Exception:
            return 'Unknown'

    def _get_last_action(self, project_name: str) -> str:
        """Get the last action performed in the project."""
        try:
            from ..core.paths import find_repo_root
            repo_root = find_repo_root()
            projects_dir = repo_root / self.config.system.default_workspace
            project_path = projects_dir / project_name

            # Check exchange log for recent handoffs
            exchange_log = project_path / 'agent_log' / 'exchange_log.md'
            if exchange_log.exists():
                content = read_file(exchange_log)
                # Look for the most recent handoff
                if 'HO-' in content:
                    return 'Agent handoff completed'

            # Check context log for recent decisions
            context_log = project_path / 'agent_log' / 'context_log.md'
            if context_log.exists():
                content = read_file(context_log)
                if 'DEC-' in content:
                    return 'Decision logged'

            return 'Agent activated'
        except Exception:
            return 'Unknown'

    def end_session(self, project_name: str) -> Dict[str, Any]:
        """
        End the current session for a project.

        Args:
            project_name: Name of the project

        Returns:
            Dictionary with session end results

        Raises:
            ProjectError: If session end fails
        """
        validate_required(project_name, "project_name", "end_session")

        if not self.project_exists(project_name):
            raise ProjectNotFoundError(f"Project '{project_name}' not found")

        # Determine project_path
        projects_dir = Path(self.config.system.default_workspace)
        project_path = projects_dir / project_name

        # Retrieve workflow name from project config
        config_data = self._load_project_config(project_path / '.agentic' / 'config')
        workflow_name = config_data.get('workflow', 'unknown')
        if workflow_name == 'unknown':
            raise ProjectError(f"Could not determine workflow for project '{project_name}'")

        # Locate active_session.md
        active_session_path = project_path / 'agent_context' / 'active_session.md'

        # Archive current content
        try:
            current_content = read_file(active_session_path)
            timestamp = get_timestamp()
            archive_dir = project_path / 'agent_log' / 'archives'
            archive_dir.mkdir(parents=True, exist_ok=True)
            archive_path = archive_dir / f'session_{timestamp}.md'
            write_file(archive_path, current_content)
        except FileNotFoundError:
            logger.warning(f"No active session file found for project '{project_name}', skipping archive")
            archive_path = None

        # Reset active_session.md
        loader = TemplateEngine(workflow=workflow_name)
        
        # Load workflow to get enforcement config
        from ..generation.canonical_loader import load_workflow
        try:
            wf = load_workflow(workflow_name)
            enforcement = wf.metadata.get('config', {}).get('enforcement', {})
        except Exception as e:
            logger.warning(f"Failed to load workflow '{workflow_name}' for enforcement config: {e}")
            enforcement = {}
        
        context = {
            "project_name": project_name, 
            "status": "ready",
            "enforcement": enforcement
        }
        fresh_content = loader.render('_base/session_base.md.j2', context)
        write_file(active_session_path, fresh_content)

        return {'status': 'ended', 'archived_to': str(archive_path) if archive_path else None}

    def _load_project_config(self, config_path: Path) -> Dict[str, Any]:
        """
        Load project config from config file.
        
        Args:
            config_path: Path to config file (without extension)
            
        Returns:
            Config data dict, or empty dict if file not found
        """
        # Use ConfigurationService to load project config properly
        try:
            project_config = ConfigurationService()
            config = project_config.load_config(context_path=config_path.parent.parent)
            return config.project.model_dump() if config.project else {}
        except Exception as e:
            logger.warning(f"Failed to load project config via ConfigurationService: {e}")
            return {}
    
    def list_projects(self) -> Dict[str, Any]:
        """
        List all available projects with their metadata.

        Returns:
            Dictionary containing project list and metadata

        Raises:
            ProjectError: If listing fails
        """
        try:
            logger.info("Listing all projects")

            projects_dir = Path(self.config.system.default_workspace)
            projects = []

            if not projects_dir.exists():
                return {
                    'projects': [],
                    'count': 0,
                    'message': 'No projects directory found'
                }

            for item in projects_dir.iterdir():
                if item.is_dir():
                    config_data = self._load_project_config(item / '.agentic' / 'config')
                    
                    if config_data:
                        projects.append({
                            'name': item.name,
                            'workflow': config_data.get('workflow', 'unknown'),
                            'description': config_data.get('description', ''),
                            'created': config_data.get('created', 'unknown'),
                            'version': config_data.get('version', 'unknown')
                        })
                    else:
                        # No config file found, but directory exists
                        projects.append({
                            'name': item.name,
                            'workflow': 'unknown',
                            'description': '',  # Blank for consistency with projects that have config but no description field
                            'created': 'unknown',
                            'version': 'unknown'
                        })

            return {
                'projects': projects,
                'count': len(projects),
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            raise ProjectError(f"Failed to list projects: {e}", cause=e)

    def remove_project(self, project_name: str, force: bool = False) -> Dict[str, Any]:
        """
        Remove a project safely.

        Args:
            project_name: Name of the project to remove
            force: Whether to skip confirmation prompts

        Returns:
            Dictionary with removal results

        Raises:
            ProjectError: If removal fails
        """
        validate_required(project_name, "project_name", "remove_project")

        try:
            logger.info(f"Removing project '{project_name}'")

            if not self.project_exists(project_name):
                raise ProjectNotFoundError(f"Project '{project_name}' not found")

            projects_dir = Path(self.config.system.default_workspace)
            project_path = projects_dir / project_name

            # Remove project directory
            import shutil
            shutil.rmtree(project_path)

            logger.info(f"Successfully removed project '{project_name}'")
            return {
                'project_name': project_name,
                'status': 'removed',
                'path': str(project_path)
            }

        except Exception as e:
            logger.error(f"Failed to remove project '{project_name}': {e}")
            raise ProjectError(
                f"Failed to remove project '{project_name}': {e}",
                context={'project_name': project_name},
                cause=e
            )

    def get_project_status(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive project status.

        Args:
            project_name: Specific project name, or None for current project

        Returns:
            Dictionary with project status information

        Raises:
            ProjectError: If status retrieval fails
        """
        try:
            if project_name:
                # Get specific project status
                logger.info(f"Getting status for project '{project_name}'")

                if not self.project_exists(project_name):
                    raise ProjectNotFoundError(f"Project '{project_name}' not found")

                projects_dir = Path(self.config.system.default_workspace)
                project_data = self._load_project_config(projects_dir / project_name / '.agentic' / 'config')

                if project_data:
                    return {
                        'project_name': project_name,
                        'status': 'found',
                        'config': project_data,
                        'path': str(projects_dir / project_name)
                    }
                else:
                    return {
                        'project_name': project_name,
                        'status': 'found',
                        'config': None,
                        'message': 'No configuration file found',
                        'path': str(projects_dir / project_name)
                    }
            else:
                # Get current project status (from current directory)
                from ..core.paths import find_project_root

                project_root = find_project_root()
                if not project_root:
                    return {
                        'status': 'not_in_project',
                        'message': 'Not in a project directory'
                    }

                config_data = self._load_project_config(project_root / '.agentic' / 'config')
                if config_data:
                    return {
                        'project_name': config_data.get('name', 'unknown'),
                        'status': 'current',
                        'config': config_data,
                        'path': str(project_root)
                    }
                else:
                    return {
                        'status': 'current',
                        'config': None,
                        'message': 'No configuration file found',
                        'path': str(project_root)
                    }

        except Exception as e:
            logger.error(f"Failed to get project status: {e}")
            raise ProjectError(f"Failed to get project status: {e}", cause=e)
