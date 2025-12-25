"""Core utilities for agentic-workflow-os.

This module provides foundational utilities used across all scripts:
- paths: Path resolution functions
- project: Project metadata operations
- io: File I/O helpers
- config: Configuration management system
- governance: Governance rule engine
- exceptions: Comprehensive error handling

These are workflow-agnostic and can be imported by any module.
"""
from .exceptions import (
    AgenticWorkflowError,
    ConfigError, ConfigNotFoundError, ConfigValidationError, ConfigMergeError,
    ProjectError, ProjectNotFoundError, ProjectAlreadyExistsError, ProjectValidationError,
    WorkflowError, WorkflowNotFoundError, WorkflowValidationError, WorkflowExecutionError,
    AgentError, AgentNotFoundError, AgentValidationError,
    CLIError, CLIValidationError, CLIExecutionError,
    ValidationError, SchemaValidationError,
    FileSystemError, FileNotFoundError, FilePermissionError, DirectoryError,
    LedgerError, LedgerValidationError, LedgerCorruptionError,
    GenerationError, TemplateError, TemplateNotFoundError,
    ServiceError, ServiceUnavailableError, ServiceTimeoutError,
    handle_error, validate_required, validate_path_exists, validate_file_readable, safe_operation
)
from .paths import (
    get_package_root,
    get_manifests_dir,
    get_templates_dir,
    get_schemas_dir,
    get_projects_dir,
)
from .project import (
    load_project_meta,
    save_project_meta,
    get_project_workflow_name,
    get_project_dir,
    project_exists,
)
from .io import (
    create_directory,
    write_file,
    ensure_parent_dir,
)
# from .config import (
#     get_config_for_command,
#     load_app_config,
#     load_project_config,
#     merge_configs,
#     validate_config,
#     save_project_config,
#     ConfigError,
#     ConfigNotFoundError,
#     ConfigValidationError,
#     ConfigMergeError,
#     ValidationResult,
# )
from .paths import (
    resolve_path,
    resolve_config_paths,
    get_project_dirs,
    get_workflow_paths,
    get_script_paths,
    ensure_project_dirs_exist,
    validate_project_structure,
    ResolvedPath,
    PathResolutionError,
    find_repo_root,
    find_project_root,
)

__all__ = [
    # Paths
    'REPO_ROOT',
    'SCRIPTS_ROOT', 
    'PROJECTS_DIR',
    'WORKFLOWS_DIR',
    'TEMPLATES_DIR',
    'MANIFESTS_DIR',
    # Project
    'load_project_meta',
    'save_project_meta',
    'get_project_workflow_name',
    'get_project_dir',
    'project_exists',
    # I/O
    'create_directory',
    'write_file',
    'ensure_parent_dir',
    # Config
    'get_config_for_command',
    'load_app_config',
    'load_project_config',
    'merge_configs',
    'validate_config',
    'save_project_config',
    'ConfigError',
    'ConfigNotFoundError',
    'ConfigValidationError',
    'ConfigMergeError',
    'ValidationResult',
    # Path Resolution
    'resolve_path',
    'resolve_config_paths',
    'get_project_dirs',
    'get_workflow_paths',
    'get_script_paths',
    'ensure_project_dirs_exist',
    'validate_project_structure',
    'ResolvedPath',
    'PathResolutionError',
    'find_repo_root',
    'find_project_root',
    # Governance
    'get_governance_engine',
    'validate_governance',
    'enforce_governance',
    'GovernanceError',
    'GovernanceResult',
]
