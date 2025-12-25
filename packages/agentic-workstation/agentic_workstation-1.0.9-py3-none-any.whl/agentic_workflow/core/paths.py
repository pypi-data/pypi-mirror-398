import sys
from pathlib import Path
from typing import Optional, List, Callable, Dict, Any, Union, TypedDict
from importlib import resources
from dataclasses import dataclass
import os
import logging

__all__ = [
    # Package Paths (where code lives)
    "get_package_root",
    "get_manifests_dir",
    "get_templates_dir", 
    "get_schemas_dir",
    
    # Project Paths (where user data lives)
    "get_projects_dir",
    "get_agent_files_dir",
    "get_workflow_search_paths",
    
    # Root Finding
    "find_repo_root",
    "find_project_root",
    
    # Path Resolution
    "ResolvedPath",
    "resolve_path",
    "resolve_config_paths",
    "get_project_dirs",
    "get_workflow_paths",
    "ensure_project_dirs_exist",
    "validate_project_structure",
    "get_script_paths",
    "get_agent_file_path",
    "get_artifact_path",
    "get_log_path",
    "get_context_path",
    
    # Backward Compatibility
    "PROJECTS_DIR",
    "AGENT_FILES_DIR",
]


def get_package_root() -> Path:
    """Resolve the package root Path using importlib.resources or a fallback.

    The function prefers `importlib.resources.files` but falls back to a
    repository-relative package path when resources are unavailable.
    """
    try:
        # Check if resources are available
        p = resources.files("agentic_workflow")
        return Path(p)
    except Exception:
         # Fallback to dev mode path
         return Path(__file__).resolve().parent.parent

def get_manifests_dir() -> Path:
    """Return the package `manifests` directory Path inside the package root."""
    return get_package_root() / "manifests"

def get_templates_dir() -> Path:
    """Return the package `templates` directory Path from package resources or fallback."""
    try:
        return Path(resources.files("agentic_workflow.templates"))
    except Exception:
        return get_package_root() / "templates"

def get_schemas_dir() -> Path:
    """Return the package `schemas` directory Path inside the package root."""
    return get_package_root() / "schemas"

def find_repo_root(start_path: Optional[Path] = None) -> Path:
    """
    Find the repository root by looking for common indicators

    Design Decision: Look for .git directory, src/ directory, or config/ directory
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Walk up the directory tree
    for path in [current] + list(current.parents):
        if (path / '.git').is_dir() or \
           (path / 'src').is_dir() or \
           (path / 'config').is_dir():
            return path

    # Fallback to current directory
    return start_path

def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the project root by looking for .agentic/ directory or project_index.md
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    while current != current.parent:
        if (current / ".agentic").is_dir() or (current / "project_index.md").exists():
            return current
        current = current.parent
    return None

def get_projects_dir() -> Path:
    """Resolve the projects directory as the parent of the repository root Path."""
    repo_root = find_repo_root()
    return repo_root.parent

def get_agent_files_dir() -> Path:
    """Resolve the global `agent_files` directory Path for the current repo."""
    repo_root = find_repo_root()
    return repo_root / "agent_files"

def get_workflow_search_paths(project_root: Optional[Path] = None) -> List[Path]:
    """Build an ordered list of Paths to search for workflows (project, user, system).

    Order of returned paths:
    1. Project-local workflows (``<project_root>/.agentic/workflows``)
    2. User workflows under XDG or platformdirs
    3. Bundled system workflows inside package manifests
    """
    paths = []
    
    # 1. Project
    if project_root is None:
        try:
             project_root = find_project_root()
        except (ImportError, Exception):
             pass
             
    if project_root:
        paths.append(project_root / ".agentic" / "workflows")
        
    # 2. User
    # Use ConfigurationService logic or platformdirs
    # We can try to import the config service helper or replicate
    import os
    try:
        import platformdirs
        user_data = Path(platformdirs.user_data_dir("agentic-workflow", "agentic")) / "workflows"
        paths.append(user_data)
    except ImportError:
        # Fallback
        xdg_data = os.environ.get('XDG_DATA_HOME')
        if xdg_data:
             paths.append(Path(xdg_data) / "agentic" / "workflows")
        else:
             paths.append(Path.home() / ".local" / "share" / "agentic" / "workflows")

    # 3. System (Bundled)
    try:
        # We need the 'workflows' dir inside manifests
        # get_manifests_dir returns manifests/ or manifests/_canonical
        # Our bundled workflows are in manifests/workflows
        # Let's use resources again to be safe
        p = resources.files("agentic_workflow.manifests")
        paths.append(Path(p) / "workflows")
    except Exception:
         # Fallback
         paths.append(get_package_root() / "manifests" / "workflows")
         
    return paths


# Path resolution constants and types
PATH_TYPE_ABSOLUTE = "absolute"
PATH_TYPE_RELATIVE_PROJECT = "relative_project"
PATH_TYPE_RELATIVE_REPO = "relative_repo"
PATH_TYPE_RELATIVE_CURRENT = "relative_current"

@dataclass
class ResolvedPath:
    """Represent a resolved `Path` with metadata for config-driven resolution.

    The dataclass exposes the resolved absolute `path`, the original input
    string, the `path_type` detected, the `base_path` used for resolution,
    and boolean flags describing existence and file/directory status.
    """
    path: Path
    original_path: str
    path_type: str
    base_path: Path
    exists: bool
    is_file: bool
    is_dir: bool

    def __str__(self) -> str:
        """Return the string form of the resolved Path for logging or display."""
        return str(self.path)

    def __fspath__(self) -> str:
        """Return the filesystem path string for consumption by I/O APIs."""
        return str(self.path)

class PathResolutionError(Exception):
    """Raised when path resolution fails during config or path handling."""
    pass

def _expand_env_vars_in_path(path_str: str) -> str:
    """Expand environment variables in a path string to their values."""
    return os.path.expandvars(path_str)

def _detect_path_type(path_str: str) -> str:
    """Detect whether a path string is absolute or repo/project/current relative.

    Design Decision: Use prefixes to indicate path type:
    - Absolute paths start with / or drive letter (Windows)
    - ${REPO_ROOT}/... for repo-relative paths
    - ${PROJECT_ROOT}/... for project-relative paths
    - Everything else is relative to current directory
    """
    path_str = path_str.strip()

    # Check for absolute paths
    if Path(path_str).is_absolute():
        return PATH_TYPE_ABSOLUTE

    # Check for special prefixes
    if path_str.startswith("${REPO_ROOT}/") or path_str.startswith("${REPO_ROOT}\\"):
        return PATH_TYPE_RELATIVE_REPO
    elif path_str.startswith("${PROJECT_ROOT}/") or path_str.startswith("${PROJECT_ROOT}\\"):
        return PATH_TYPE_RELATIVE_PROJECT

    # Default to relative to current directory
    return PATH_TYPE_RELATIVE_CURRENT

def _get_base_path(path_type: str, project_path: Optional[Path] = None, repo_path: Optional[Path] = None) -> Path:
    """Return the base `Path` used to resolve a path of the given type."""
    if path_type == PATH_TYPE_ABSOLUTE:
        return Path("/")
    elif path_type == PATH_TYPE_RELATIVE_REPO:
        return repo_path or find_repo_root()
    elif path_type == PATH_TYPE_RELATIVE_PROJECT:
        return project_path or find_project_root()
    elif path_type == PATH_TYPE_RELATIVE_CURRENT:
        return Path.cwd()
    else:
        raise PathResolutionError(f"Unknown path type: {path_type}")

def resolve_path(path_str: str, project_path: Optional[Path] = None, repo_path: Optional[Path] = None) -> ResolvedPath:
    """Resolve a path string into a `ResolvedPath` using project/repo context.

    Supports absolute paths, user expansion (~), and special prefixes 
    `${REPO_ROOT}` and `${PROJECT_ROOT}`.
    """
    if not path_str or not path_str.strip():
        raise PathResolutionError("Empty path string provided")

    # 1. Expand environment variables ($VAR)
    expanded_path = _expand_env_vars_in_path(path_str)
    
    # 2. Expand User Tilde (~) - Critical fix for path consistency
    if "~" in expanded_path:
        expanded_path = os.path.expanduser(expanded_path)
        
    original_path = path_str

    # Detect path type
    path_type = _detect_path_type(expanded_path)

    # Get base path
    base_path = _get_base_path(path_type, project_path, repo_path)

    # Remove prefix if present
    if path_type == PATH_TYPE_RELATIVE_REPO:
        clean_path = expanded_path.replace("${REPO_ROOT}", "").lstrip("/\\")
    elif path_type == PATH_TYPE_RELATIVE_PROJECT:
        clean_path = expanded_path.replace("${PROJECT_ROOT}", "").lstrip("/\\")
    else:
        clean_path = expanded_path

    # Resolve the path
    if path_type == PATH_TYPE_ABSOLUTE:
        resolved_path = Path(clean_path)
    else:
        resolved_path = base_path / clean_path

    # Resolve any remaining relative components (and symlinks)
    try:
        resolved_path = resolved_path.resolve()
    except Exception:
        # If file doesn't exist, resolve() on Windows might behave differently 
        # or strict=True defaults. We mostly want normalization here.
        resolved_path = Path(os.path.abspath(resolved_path))

    # Check if path exists and get metadata
    exists = resolved_path.exists()
    is_file = resolved_path.is_file() if exists else False
    is_dir = resolved_path.is_dir() if exists else False

    logger = logging.getLogger(__name__)
    logger.debug(f"Resolved path '{original_path}' -> '{resolved_path}' (type: {path_type}, exists: {exists})")

    return ResolvedPath(
        path=resolved_path,
        original_path=original_path,
        path_type=path_type,
        base_path=base_path,
        exists=exists,
        is_file=is_file,
        is_dir=is_dir
    )

class ConfigMapping(TypedDict, total=False):
    """Typed mapping describing path-related configuration sections.

    - `directories`: mapping of logical directory names to relative/absolute paths
    - `workflow`: mapping of workflow-related filenames to paths
    - `scripts`: mapping of named script entries to path strings
    """
    directories: Dict[str, str]
    workflow: Dict[str, str]
    scripts: Dict[str, str]

def resolve_config_paths(config: ConfigMapping, project_path: Optional[Path] = None, repo_path: Optional[Path] = None) -> Dict[str, ResolvedPath]:
    """Recursively resolve path-like strings in `config` and return ResolvedPath map.

    Walks the provided configuration mapping and resolves any string that looks
    like a filesystem path into a `ResolvedPath`. The returned mapping keys
    are dotted keys describing the original location (e.g. ``config.directories.agent_files``).
    """
    resolved_paths = {}

    def _resolve_value(key_path: str, value: Any) -> Any:
        if isinstance(value, str):
            # Check if it looks like a path (contains / or \)
            if "/" in value or "\\" in value:
                try:
                    resolved = resolve_path(value, project_path, repo_path)
                    resolved_paths[key_path] = resolved
                    return str(resolved.path)
                except PathResolutionError as e:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to resolve path '{value}' for '{key_path}': {e}")
                    return value
        elif isinstance(value, dict):
            return {k: _resolve_value(f"{key_path}.{k}", v) for k, v in value.items()}
        elif isinstance(value, list):
            return [_resolve_value(f"{key_path}[{i}]", item) for i, item in enumerate(value)]
        return value

    # Resolve paths in config
    resolved_config = _resolve_value("config", config)

    return resolved_paths

def get_project_dirs(config: ConfigMapping, project_path: Path) -> Dict[str, Path]:
    """Return a mapping of canonical project directory names to absolute Paths.

    Uses `config['directories']` when present and falls back to sensible
    defaults under the provided `project_path`.
    """
    dirs_config = config.get('directories', {})

    # Default directory structure
    default_dirs = {
        'agent_files': 'agent_files',
        'agent_context': 'agent_context',
        'agent_log': 'agent_log',
        'artifacts': 'artifacts',
        'docs': 'docs',
        'input': 'input',
        'package': 'package',
        'scripts': 'scripts'
    }

    # Override with config values
    project_dirs = {}
    for dir_name, default_path in default_dirs.items():
        config_path = dirs_config.get(dir_name, default_path)
        try:
            resolved = resolve_path(config_path, project_path=project_path)
            project_dirs[dir_name] = resolved.path
        except PathResolutionError as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to resolve {dir_name} directory '{config_path}': {e}")
            # Fallback to default relative to project
            project_dirs[dir_name] = project_path / default_path

    return project_dirs

def get_workflow_paths(config: ConfigMapping, project_path: Path) -> Dict[str, Path]:
    """Return canonical workflow-related file Paths resolved relative to `project_path`.

    Ensures workflow file names are treated as project-relative when not
    explicitly absolute or prefixed with `${REPO_ROOT}`/`${PROJECT_ROOT}`.
    """
    workflow_config = config.get('workflow', {})

    # Default workflow paths
    default_paths = {
        'workflow_file': 'workflow.json',
        'agents_file': 'agents.json',
        'artifacts_file': 'artifacts.json',
        'instructions_file': 'instructions.json',
        'governance_file': 'governance.md'
    }

    workflow_paths = {}
    for file_name, default_path in default_paths.items():
        config_path = workflow_config.get(file_name, default_path)
        try:
            # For workflow files, treat relative paths as project-relative by default
            if not config_path.startswith(("${REPO_ROOT}", "${PROJECT_ROOT}", "/")) and not Path(config_path).is_absolute():
                config_path = f"${{PROJECT_ROOT}}/{config_path}"
            resolved = resolve_path(config_path, project_path=project_path)
            workflow_paths[file_name] = resolved.path
        except PathResolutionError as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to resolve {file_name} '{config_path}': {e}")
            # Fallback to default relative to project
            workflow_paths[file_name] = project_path / default_path

    return workflow_paths

def ensure_project_dirs_exist(project_dirs: Dict[str, Path]) -> None:
    """Create any missing project directories from the provided mapping."""
    for dir_name, dir_path in project_dirs.items():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger = logging.getLogger(__name__)
            logger.debug(f"Ensured directory exists: {dir_path}")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create directory {dir_name}: {dir_path} - {e}")

def validate_project_structure(project_path: Path, config: ConfigMapping) -> List[str]:
    """Validate project directories and required workflow files, returning a list of issues."""
    issues: List[str] = []

    # Get expected directories
    project_dirs = get_project_dirs(config, project_path)

    # Check directories exist
    for dir_name, dir_path in project_dirs.items():
        if not dir_path.exists():
            issues.append(f"Missing directory: {dir_path}")
        elif not dir_path.is_dir():
            issues.append(f"Path exists but is not a directory: {dir_path}")

    # Get expected workflow files
    workflow_paths = get_workflow_paths(config, project_path)

    # Check workflow files exist (some may be optional)
    required_files = ['workflow_file', 'agents_file']
    for file_name in required_files:
        file_path = workflow_paths[file_name]
        if not file_path.exists():
            issues.append(f"Missing required file: {file_path}")

    return issues

def get_script_paths(config: ConfigMapping, repo_path: Optional[Path] = None) -> Dict[str, Path]:
    """Return resolved Paths for named CLI scripts declared in `config['scripts']`.

    If `repo_path` is omitted the repository root is located using the
    configuration service helper.
    """
    scripts_config = config.get('scripts', {})

    if repo_path is None:
        repo_path = find_repo_root()

    # Default script paths
    default_scripts = {
        'workflow_cli': 'scripts/workflow',
        'project_cli': 'projects/{project_name}/workflow',
        'validation_script': 'scripts/validation/validate_session.py'
    }

    script_paths = {}
    for script_name, default_path in default_scripts.items():
        config_path = scripts_config.get(script_name, default_path)
        try:
            resolved = resolve_path(config_path, repo_path=repo_path)
            script_paths[script_name] = resolved.path
        except PathResolutionError as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to resolve {script_name} script '{config_path}': {e}")
            # Fallback to default relative to repo
            script_paths[script_name] = repo_path / default_path

    return script_paths

# Utility functions for common path operations
def get_agent_file_path(project_dirs: Dict[str, Path], agent_id: str, file_type: str = 'md') -> Path:
    """Return the Path to an agent file inside the project's `agent_files` dir."""
    return project_dirs['agent_files'] / f"{agent_id}.{file_type}"

def get_artifact_path(project_dirs: Dict[str, Path], artifact_name: str) -> Path:
    """Return the Path to an artifact inside the project's `artifacts` dir."""
    return project_dirs['artifacts'] / artifact_name

def get_log_path(project_dirs: Dict[str, Path], log_type: str, timestamp: Optional[str] = None) -> Path:
    """Return the Path to a log file inside the project's `agent_log` directory."""
    if timestamp:
        return project_dirs['agent_log'] / f"{log_type}_{timestamp}.log"
    else:
        return project_dirs['agent_log'] / f"{log_type}.log"

def get_context_path(project_dirs: Dict[str, Path], context_type: str) -> Path:
    """Return the Path for a context JSON file inside `agent_context`."""
    return project_dirs['agent_context'] / f"{context_type}.json"


# Lazy-evaluated Path wrapper to avoid executing filesystem resolution at import time
class _LazyPath:
    """Lazily compute and proxy a `pathlib.Path` value on first access.

    This preserves backward-compatible module level symbols like
    `PROJECTS_DIR` while preventing filesystem/path-resolution from
    running at import time (which breaks the "No Ghost Logic" rule).
    """

    def __init__(self, factory: Callable[[], Path]):
        """Store a zero-argument `factory` that returns a `Path` when invoked."""
        self._factory = factory
        self._value: Optional[Path] = None

    def _ensure(self) -> None:
        """Compute and cache the backed `Path` value on first access."""
        if self._value is None:
            self._value = self._factory()

    def __getattr__(self, name):
        """Proxy attribute access to the resolved `Path` after ensuring it exists."""
        self._ensure()
        return getattr(self._value, name)

    def __fspath__(self) -> str:
        """Return the filesystem path string of the resolved Path."""
        self._ensure()
        return self._value.__fspath__()

    def __str__(self) -> str:
        """Return the string form of the resolved Path for display/logging."""
        self._ensure()
        return str(self._value)

    def __repr__(self) -> str:
        """Return a compact representation helpful for debugging the lazy wrapper."""
        return f"_LazyPath({self._factory.__name__}) -> {repr(self._value)}"

    def __truediv__(self, key):
        """Support division operator to compose paths (delegates to resolved Path)."""
        self._ensure()
        return self._value / key


# For backward compatibility: expose lazy-evaluated module symbols that act like Paths
PROJECTS_DIR = _LazyPath(get_projects_dir)
AGENT_FILES_DIR = _LazyPath(get_agent_files_dir)
