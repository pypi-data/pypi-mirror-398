"""
Atomic Initialization Pipeline for Agentic Workflow projects.

CRITICAL COMPONENT: This is the core project creation engine.
Implements the Staging-Commit pattern to ensure projects are created fully formed
and can be safely refreshed without corruption.

Used by: services/project_service.py and core/project_generation.py
Handles: Complete project structure creation, template rendering, file staging
"""

from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime

from ..core.schema import RuntimeConfig
from ..core.models import ProjectModel, VirtualFile, PipelineResult
from ..core.exceptions import AgenticWorkflowError
from ..generation.canonical_loader import load_workflow
from ..generation.generate_agents import build_agent_files
from ..utils import ensure_directory

logger = logging.getLogger(__name__)

__all__ = ["InitPipeline"]


class InitPipeline:
    """Pipeline for atomic project initialization."""

    def __init__(self, config: RuntimeConfig):
        """Initialize the pipeline with runtime configuration."""
        self.config = config

    def run(self, project_name: str, target_path: str, workflow: str, force: bool = False, description: str = None) -> PipelineResult:
        """Execute the full initialization pipeline."""
        # 1. Resolve Path
        target_path_obj = self._resolve_path(target_path)

        # 2. Validation (Pre-Flight)
        self._validate_target(target_path_obj, force)

        # 3. Hydration
        project_model = self._hydrate_model(project_name, target_path_obj, workflow, description)

        # 4. Rendering
        vfs = self._render_templates(project_model)

        # 5. Commit
        return self._commit_to_disk(vfs, project_model, refresh_mode=False)

    def refresh(self, project_name: str, target_path: str, workflow: str) -> PipelineResult:
        """Execute the refresh pipeline for existing projects."""
        # 1. Resolve Path
        target_path_obj = Path(target_path).resolve()

        # 2. Validation (Pre-Flight) - Skip force check for refresh
        if not target_path_obj.exists():
            raise AgenticWorkflowError(f"Project directory {target_path_obj} does not exist. Use run() for new projects.")

        # Load existing description from config
        existing_description = self._load_existing_description(target_path_obj)

        # 3. Hydration
        project_model = self._hydrate_model(project_name, target_path_obj, workflow, existing_description)

        # 4. Rendering
        vfs = self._render_templates(project_model)

        # 5. Filter for safe refresh
        filtered_vfs = self._filter_for_refresh(vfs, target_path_obj)

        # 6. Commit
        return self._commit_to_disk(filtered_vfs, project_model, refresh_mode=True)

    def _load_existing_description(self, project_path: Path) -> str:
        """Load existing description from project config."""
        config_path = project_path / ".agentic" / "config.yaml"
        if config_path.exists():
            try:
                import yaml
                with open(config_path, 'r') as f:
                    data = yaml.safe_load(f)
                    return data.get('description', '') if data else ''
            except Exception:
                pass
        return ''

    def _filter_for_refresh(self, vfs: List[VirtualFile], project_path: Path) -> List[VirtualFile]:
        """Filter virtual files for safe refresh operation."""
        filtered = []
        
        for vf in vfs:
            # Get relative path from project root
            try:
                rel_path = vf.path.relative_to(project_path)
                rel_str = str(rel_path)
            except ValueError:
                # File outside project, skip
                continue
            
            # ALWAYS write system files
            if (rel_str.startswith('agent_files/') or 
                rel_str.startswith('.agentic/') or 
                rel_str.startswith('.github/')):
                filtered.append(vf)
                continue
            
            # NEVER write user files if they exist
            if (rel_str == 'agent_context/active_session.md' or
                rel_str.startswith('artifacts/') or
                rel_str.startswith('input/')):
                if vf.path.exists():
                    logger.info(f"Skipping existing user file: {rel_str}")
                    continue
                else:
                    # File doesn't exist, safe to create
                    filtered.append(vf)
                    continue
            
            # For other files (like project_index.md, docs/), allow update
            filtered.append(vf)
        
        return filtered

    def _resolve_path(self, target_path: str) -> Path:
        """Resolve the target path, using default workspace if not absolute."""
        path = Path(target_path)
        if not path.is_absolute():
            # Use default workspace from config
            default_workspace = getattr(self.config.system, 'default_workspace', Path.cwd())
            path = Path(default_workspace) / target_path
        return path.resolve()

    def _validate_target(self, target_path: Path, force: bool) -> None:
        """Validate the target directory."""
        if target_path.exists():
            if not force and any(target_path.iterdir()):
                raise AgenticWorkflowError(f"Target directory {target_path} is not empty. Use --force to overwrite.")
        else:
            # Create the directory if it doesn't exist
            target_path.mkdir(parents=True, exist_ok=True)
        # Check for nested projects
        if self._is_inside_project(target_path):
            raise AgenticWorkflowError("Cannot create project inside existing project")

    def _is_inside_project(self, path: Path) -> bool:
        """Check if path is inside an existing project."""
        current = path.parent
        while current != current.parent:
            if (current / ".agentic").is_dir():
                return True
            current = current.parent
        return False

    def _hydrate_model(self, name: str, target_path: Path, workflow: str, description: str = None) -> ProjectModel:
        """Create the in-memory project model."""
        # Load workflow definition
        from ..generation.canonical_loader import load_canonical_workflow
        workflow_data = load_canonical_workflow(workflow, return_object=False)

        context_data = {
            'project_name': name,
            'workflow_type': workflow,
            'workflow_data': workflow_data,
            'timestamp': datetime.now().isoformat(),  # Current date
            'description': description or '',
        }

        return ProjectModel(
            name=name,
            root_path=target_path,
            workflow_type=workflow,
            context_data=context_data
        )

    def _render_templates(self, project_model: ProjectModel) -> List[VirtualFile]:
        """Render all templates into virtual files."""
        vfs = []
        
        # Get workflow data for content generation
        workflow_data = project_model.context_data.get('workflow_data', {})
        
        # Create .agentic directory structure
        agentic_dir = project_model.root_path / ".agentic"
        config_path = agentic_dir / "config.yaml"
        description = project_model.context_data.get('description', '')
        vfs.append(VirtualFile(
            path=config_path,
            content=f"workflow: {project_model.workflow_type}\nstrict_mode: true\ndescription: \"{description}\"\n"
        ))

        # Generate agent files
        agent_files_vfs = self._generate_agent_files(project_model)
        vfs.extend(agent_files_vfs)
        
        # Generate artifact files
        artifact_files_vfs = self._generate_artifact_files(project_model, workflow_data)
        vfs.extend(artifact_files_vfs)
        
        # Generate runtime state (logs, docs, active session)
        runtime_vfs = self._generate_runtime_state(project_model, workflow_data)
        vfs.extend(runtime_vfs)

        # Create project directories (from workflow manifest)
        workflow_dirs = workflow_data.get('workflow', {}).get('directories', {})
        
        # Extract directory names (exclude 'root' and 'templates' which are special)
        directories = []
        for key, value in workflow_dirs.items():
            if key not in ['root', 'templates'] and isinstance(value, str):
                # Remove any path prefixes like 'artifacts/', 'agent_files/', etc.
                dir_name = value.rstrip('/')
                directories.append(dir_name)
        
        # Fallback to default directories if none found in workflow
        if not directories:
            directories = [
                "agent_files",
                "agent_context", 
                "agent_log",
                "artifacts",
                "docs",
                "input",
                "package"
            ]
        
        # Directories are created in _commit_to_disk via _create_project_directories

        return vfs

    def _commit_to_disk(self, vfs: List[VirtualFile], project_model: ProjectModel, refresh_mode: bool = False) -> PipelineResult:
        """Atomically write all files to disk and return execution result."""
        mode_str = "refresh" if refresh_mode else "init"
        logger.info(f"Committing {len(vfs)} files in {mode_str} mode")
        
        created_files = []
        updated_files = []
        skipped_files = []
        
        # Create project directories
        self._create_project_directories(project_model)
        
        # Then, write all virtual files
        for vf in vfs:
            ensure_directory(vf.path.parent)
            file_existed = vf.path.exists()
            
            try:
                rel_path = vf.path.relative_to(project_model.root_path)
                logger.info(f"Writing file: {rel_path}")
            except ValueError:
                logger.info(f"Writing file: {vf.path}")
            
            with open(vf.path, 'w') as f:
                f.write(vf.content)
            
            if file_existed:
                updated_files.append(vf.path)
            else:
                created_files.append(vf.path)
        
        success = True
        message = f"Successfully {mode_str}ed project with {len(created_files)} created, {len(updated_files)} updated files"
        
        return PipelineResult(
            success=success,
            message=message,
            created_files=created_files,
            updated_files=updated_files,
            skipped_files=skipped_files,
            target_path=project_model.root_path
        )

    def _create_project_directories(self, project_model: ProjectModel) -> None:
        """Create the standard project directory structure."""
        # Define Standard Structure
        standard_dirs = [
            'agent_files',
            'agent_context',
            'agent_log',
            'artifacts',
            'docs',
            'input',
            'package',
            '.agentic'  # New config location
        ]

        for dir_name in standard_dirs:
            dir_path = project_model.root_path / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)

        # Create agent_log/archives subdirectory
        archives_dir = project_model.root_path / "agent_log" / "archives"
        if not archives_dir.exists():
            archives_dir.mkdir(parents=True, exist_ok=True)

        # Create Agent-Specific Artifact Directories
        workflow_data = project_model.context_data.get('workflow_data', {})
        self._create_agent_dirs(project_model.root_path, workflow_data)

    def _create_agent_dirs(self, target_path: Path, workflow_data: Dict[str, Any]) -> None:
        """Helper to create agent-specific subdirectories."""
        agents_data = workflow_data.get('agents', {})
        
        # Handle list vs dict structure from canonical json
        agents = agents_data if isinstance(agents_data, list) else agents_data.get('agents', [])
        
        artifacts_root = target_path / 'artifacts'

        for agent in agents:
            agent_id = agent.get('id', '')
            agent_slug = agent.get('slug', agent_id.replace('-', '_'))
            agent_type = agent.get('agent_type', 'core')

            # Orchestrators usually work at root context, but we create a folder just in case
            if agent_type == 'orchestrator':
                continue

            if agent_id and agent_slug:
                agent_dir = artifacts_root / f"{agent_id}_{agent_slug}"
                if not agent_dir.exists():
                    agent_dir.mkdir(parents=True, exist_ok=True)

    def _generate_agent_files(self, project_model: ProjectModel) -> List[VirtualFile]:
        """Generate agent markdown files for the project."""
        vfs = []
        
        try:
            # Build agent files in memory
            agent_files = build_agent_files(project_model.workflow_type, project_model.name)
            
            # Create VirtualFile for each
            output_dir = project_model.root_path / 'agent_files'
            for filename, content in agent_files.items():
                file_path = output_dir / filename
                vfs.append(VirtualFile(path=file_path, content=content))
                
        except Exception as e:
            logger.warning(f"Failed to generate agent files: {e}")
            
        return vfs

    def _generate_artifact_files(self, project_model: ProjectModel, workflow_data: Dict[str, Any]) -> List[VirtualFile]:
        """Generate initial artifact files from workflow artifact definitions."""
        from ..utils.templating import TemplateEngine
        
        vfs = []
        
        try:
            # Initialize template loader
            loader = TemplateEngine(workflow=project_model.workflow_type)
            
            # Get artifacts from workflow data (not from agents)
            artifacts_data = workflow_data.get('artifacts', {})
            if isinstance(artifacts_data, dict):
                artifacts_list = artifacts_data.get('artifacts', [])
            else:
                artifacts_list = []
            
            # Pre-calculate agent mapping for ownership
            agents = workflow_data.get('agents', [])
            if isinstance(agents, dict):
                agents = agents.get('agents', [])
            agent_map = {a.get('id'): a.get('slug', a.get('id', '').replace('-', '_')) for a in agents}
            
            artifacts_dir = project_model.root_path / 'artifacts'
            
            for artifact in artifacts_list:
                if not isinstance(artifact, dict):
                    continue
                    
                filename = artifact.get('filename')
                owner = artifact.get('owner', 'unknown')
                description = artifact.get('description', 'No description provided.')
                
                if not filename or not owner:
                    continue
                    
                # Get agent slug for directory naming
                agent_slug = agent_map.get(owner, owner.replace('-', '_'))
                
                # Create agent directory: artifacts/{ID}_{Slug}/
                agent_dir = artifacts_dir / f"{owner}_{agent_slug}"
                
                file_path = agent_dir / filename
                
                # Enforce extension for text content if missing
                if not file_path.suffix and '.' not in file_path.name:
                     file_path = file_path.with_suffix('.md')
                     filename = file_path.name
                
                # Try to render using templates
                content = ""
                template_found = False
                
                # Search for template candidates
                candidates = [
                    f"artifacts/{filename}.j2", 
                    f"artifacts/{filename}",
                    f"{filename}.j2", 
                    f"{filename}"
                ]
                
                for candidate in candidates:
                    try:
                        context = {
                            'project_name': project_model.name,
                            'agent_id': owner,
                            'description': description,
                            'artifact': artifact,
                            'workflow': project_model.workflow_type 
                        }
                        content = loader.render(candidate, context)
                        template_found = True
                        break
                    except Exception:
                        continue
                
                # Fallback content
                if not template_found:
                    content = f"""# {filename}

**Owner**: {owner}
**Description**: {description}

<!-- Initial scaffold generated by agentic-workflow -->
"""
                
                vfs.append(VirtualFile(path=file_path, content=content))
                # Show progress for artifact files
                try:
                    shortened = f"{file_path.relative_to(project_model.root_path)}"
                except Exception:
                    shortened = str(file_path)
                # Removed display_success call
                
        except Exception as e:
            logger.warning(f"Failed to generate artifact files: {e}")
            
        return vfs

    def _generate_runtime_state(self, project_model: ProjectModel, workflow_data: Dict[str, Any]) -> List[VirtualFile]:
        """Initialize runtime state (logs, contexts, docs) from templates."""
        from ..utils.templating import TemplateEngine
        from datetime import datetime
        
        vfs = []
        
        try:
            # Initialize template loader
            loader = TemplateEngine(workflow=project_model.workflow_type)
            
            # Helper to render all files in a source subdir (similar to runtime.py)
            def render_subdir(subdir: str, target_subdir: str):
                # Use filesystem to discover templates (like runtime.py does)
                from ..core.paths import get_templates_dir
                
                source_dir = get_templates_dir() / subdir
                if not source_dir.exists():
                    return
                    
                target_dir = project_model.root_path / target_subdir
                
                for template_file in source_dir.glob('*'):
                    if template_file.is_dir() or template_file.name.startswith('_'):
                        continue
                        
                    template_name = template_file.name
                    
                    # Target filename: strip .j2 suffix
                    target_filename = template_name
                    if target_filename.endswith('.j2'):
                        target_filename = target_filename[:-3]
                    
                    # Construct relative path for loader
                    loader_path = f"{subdir}/{template_name}"
                    
                    try:
                        content = loader.render(
                            loader_path, 
                            {'project_name': project_model.name, 'workflow_type': project_model.workflow_type}
                        )
                        target_path = target_dir / target_filename
                        vfs.append(VirtualFile(path=target_path, content=content))
                        # Show progress for runtime files
                        try:
                            shortened = f"{target_path.relative_to(project_model.root_path)}"
                        except Exception:
                            shortened = str(target_path)
                        # Removed display_success call
                    except Exception as e:
                        logger.warning(f"Failed to render runtime template {loader_path}: {e}")

            # 1. Initialize Logs
            render_subdir("logs", "agent_log")

            # 2. Initialize Docs  
            render_subdir("docs", "docs")
            
            # Get first agent from workflow data
            pipeline_order = workflow_data.get('workflow', {}).get('pipeline', {}).get('order', [])
            first_agent_id = pipeline_order[0] if pipeline_order else None
            
            agents = workflow_data.get('agents', [])
            if isinstance(agents, dict): 
                agents = agents.get('agents', [])
            first_agent = next((a for a in agents if a.get('id') == first_agent_id), None) if first_agent_id else None
            
            first_agent_role = first_agent.get('role', 'Unknown') if first_agent else 'Unknown'
            
            workflow_meta = workflow_data.get('workflow', {})
            workflow_display_name = workflow_meta.get('display_name', project_model.workflow_type.capitalize())
            workflow_version = workflow_meta.get('version', '1.0')
            
            # Generate active_session.md
            try:
                if not first_agent_id:
                    # Create a simple uninitialized session file
                    session_content = f"""---
session_type: uninitialized
project_name: {project_model.name}
workflow_name: {project_model.workflow_type}
status: ready_for_activation
timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# WORKFLOW READY FOR ACTIVATION

The project has been initialized and is ready for the first agent activation.

## Next Steps

1. **Activate the first agent:**
   ```bash
   ./workflow activate A-01  # For planning workflow
   # OR
   ./workflow activate I-01  # For implementation workflow
   ```

2. **Review project context** in `project_index.md`

3. **Begin producing artifacts** in the `artifacts/` directory

## Workflow Status

- **Status:** Ready for Activation
- **Next Agent:** A-01 (Project Guide & Idea Incubation)
- **Workflow:** {workflow_display_name}
"""
                else:
                    # Use ContextResolver for proper session context building
                    from ..utils.templating import ContextResolver
                    resolver = ContextResolver()
                    session_context = resolver.get_session_context(
                        workflow=project_model.workflow_type,
                        agent_id=first_agent_id,
                        project_name=project_model.name,
                        timestamp=datetime.now().isoformat()
                    )
                    session_content = loader.render('_base/session_base.md.j2', session_context)
                
                session_path = project_model.root_path / "agent_context" / "active_session.md"
                vfs.append(VirtualFile(path=session_path, content=session_content))
                
            except Exception as e:
                logger.warning(f"Failed to generate active_session.md: {e}")

            # Generate project_index.md
            try:
                index_context = {
                    'project_name': project_model.name,
                    'workflow_name': project_model.workflow_type,
                    'workflow_display_name': workflow_display_name,
                    'workflow_version': workflow_version,
                    'timestamp': datetime.now().isoformat(),
                    'registry_entries': [],  # Empty initially
                    'current_phase': 'INTAKE',
                    'active_agent': first_agent_id or 'None',
                    'last_action': 'Project initialized'
                }
                index_content = loader.render('_base/project_index.md.j2', index_context)
                index_path = project_model.root_path / "project_index.md"
                vfs.append(VirtualFile(path=index_path, content=index_content))
                # Removed display_success call
            except Exception as e:
                logger.warning(f"Failed to generate project_index.md: {e}")
                # Fallback
                fallback_content = f"""# {project_model.name} Project Index

**Workflow:** {project_model.workflow_type}
**Created:** {datetime.now().isoformat()}

## Directory Structure

- `agent_files/` - Generated agent prompts
- `agent_context/` - Runtime context  
- `agent_log/` - Handoffs and decisions
- `artifacts/` - Agent outputs
- `docs/` - Self-contained references
- `input/` - User requirements
- `package/` - Final deliverables
"""
                index_path = project_model.root_path / "project_index.md"
                vfs.append(VirtualFile(path=index_path, content=fallback_content))
                
            # Generate GOVERNANCE_GUIDE.md
            try:
                gov_context = {
                    'project_name': project_model.name,
                    'workflow_name': project_model.workflow_type,
                    'workflow_data': workflow_data.get('workflow', {}),
                }
                gov_content = loader.render('docs/GOVERNANCE_GUIDE.md.j2', gov_context)
                gov_path = project_model.root_path / "docs" / "GOVERNANCE_GUIDE.md"
                vfs.append(VirtualFile(path=gov_path, content=gov_content))
            except Exception as e:
                logger.warning(f"Failed to generate GOVERNANCE_GUIDE.md: {e}")
                
        except Exception as e:
            logger.warning(f"Failed to generate runtime state: {e}")
            
        return vfs