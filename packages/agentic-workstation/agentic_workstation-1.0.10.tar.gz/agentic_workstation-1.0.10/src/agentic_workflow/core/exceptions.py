"""Define the canonical exception hierarchy and error utilities for Agentic Workflow.

This module centralizes exception types, structured error context, and
safe helper functions used across the platform to ensure consistent error
reporting and structured logs that the architecture mapper can statically
analyze.
"""

from typing import Dict, Optional, List, Callable, TypedDict, TypeVar
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# Typed structure for error/context payloads so public signatures avoid `Any`/`dict`.
class ErrorContext(TypedDict, total=False):
    """Represent structured error context fields for logging and diagnostics.

    Fields should be string-serializable to simplify static analysis.
    """
    operation: str
    error_type: str
    path: str
    value_name: str
    value: str


# Generic result type for safe_operation to avoid `Any` in public signatures.
T = TypeVar("T")

__all__ = [
    # Base Exception
    "AgenticWorkflowError",
    "AgenticError",
    
    # Configuration Errors
    "ConfigError",
    "ConfigNotFoundError", 
    "ConfigValidationError",
    "ConfigMergeError",
    
    # Project Errors
    "ProjectError",
    "ProjectNotFoundError",
    "ProjectAlreadyExistsError",
    "ProjectValidationError",
    
    # Workflow Errors
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowValidationError",
    "WorkflowExecutionError",
    
    # Agent Errors
    "AgentError",
    "AgentNotFoundError",
    "AgentValidationError",
    
    # CLI Errors
    "CLIError",
    "CLIValidationError",
    "CLIExecutionError",
    
    # Validation Errors
    "ValidationError",
    "SchemaValidationError",
    
    # File System Errors
    "FileSystemError",
    "FileNotFoundError",
    "FilePermissionError",
    "DirectoryError",
    
    # Ledger Errors
    "LedgerError",
    "LedgerValidationError",
    "LedgerCorruptionError",
    
    # Generation Errors
    "GenerationError",
    "TemplateError",
    "TemplateNotFoundError",
    
    # Service Errors
    "ServiceError",
    "ServiceUnavailableError",
    "ServiceTimeoutError",
    
    # Handler Errors
    "HandlerError",
    "SessionError",
    "ArtifactError",
    
    # Governance Errors
    "GovernanceError",
    "ValidationViolation",
    "PolicyConfigurationError",
    "ManifestError",
    
    # Utility Functions
    "handle_error",
    "validate_required",
    "validate_path_exists",
    "validate_file_readable",
    "safe_operation",
]


class AgenticWorkflowError(Exception):
    """Wrap an error message with a machine-readable code and structured context for logging.

    Use this base for all domain-specific exceptions so callers can reliably
    extract `error_code` and `context` for structured logs and maps.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional["ErrorContext"] = None,
        cause: Optional[Exception] = None,
    ):
        """Initialize the exception with `message`, optional `error_code`, and `context`.

        The `context` must be string-serializable and is stored as an `ErrorContext`.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        # Keep a typed, string-serializable context for static mapping
        self.context: "ErrorContext" = context or {}
        self.cause = cause

    # Exit code to use when this exception should translate to a process exit
    exit_code = 1

    def __str__(self) -> str:
        """Return a single-line, human-readable representation suitable for logs."""
        parts = [f"[{self.error_code}] {self.message}"]
        if self.context:
            parts.append(f"Context: {self.context}")
        if self.cause:
            parts.append(f"Cause: {self.cause}")
        return " | ".join(parts)

    def to_dict(self) -> Dict[str, str]:
        """Serialize the exception into a flat mapping of strings for logs.

        This method ensures stable, flat structures suitable for static analysis
        and structured logging systems.
        """
        result: Dict[str, str] = {
            "error_code": str(self.error_code),
            "error_message": str(self.message),
            "exception_type": self.__class__.__name__,
        }
        for k, v in self.context.items():
            try:
                result[k] = str(v)
            except Exception:
                result[k] = "<unstringifiable>"

        if self.cause:
            result["cause"] = str(self.cause)

        return result


# Configuration Errors
class ConfigError(AgenticWorkflowError):
    """Represent configuration-related errors during configuration load/merge."""
    exit_code = 10


class ConfigNotFoundError(ConfigError):
    """Indicate that a required configuration file was not found."""
    pass


class ConfigValidationError(ConfigError):
    """Indicate configuration validation failed with details in `context`."""
    pass


class ConfigMergeError(ConfigError):
    """Indicate an error occurred while merging layered configurations."""
    pass


# Project Errors
class ProjectError(AgenticWorkflowError):
    """Represent project-related errors such as missing or invalid projects."""
    pass


class ProjectNotFoundError(ProjectError):
    """Indicate the requested project could not be located on disk."""
    exit_code = 13


class ProjectAlreadyExistsError(ProjectError):
    """Indicate a project creation failed because the target already exists."""
    pass


class ProjectValidationError(ProjectError):
    """Indicate that project metadata or structure failed validation checks."""
    pass


# Workflow Errors
class WorkflowError(AgenticWorkflowError):
    """Represent workflow-related errors such as parse or missing workflow files."""
    pass


class WorkflowNotFoundError(WorkflowError):
    """Indicate the requested workflow package could not be found."""
    exit_code = 11


class WorkflowValidationError(WorkflowError):
    """Indicate the workflow manifest failed validation rules."""
    pass


class WorkflowExecutionError(WorkflowError):
    """Indicate an error occurred while executing a workflow pipeline."""
    pass


# Agent Errors
class AgentError(AgenticWorkflowError):
    """Represent agent-specific errors such as missing agent definitions."""
    pass


class AgentNotFoundError(AgentError):
    """Indicate that an agent identifier could not be resolved to a definition."""
    exit_code = 12


class AgentValidationError(AgentError):
    """Indicate that an agent definition failed validation checks."""
    pass


# CLI Errors
class CLIError(AgenticWorkflowError):
    """Represent CLI-related errors such as invalid input or command failures."""
    pass


class CLIValidationError(CLIError):
    """Indicate CLI input validation failed for the invoked command."""
    pass


class CLIExecutionError(CLIError):
    """Indicate an error occurred while executing a CLI command."""
    pass


# Validation Errors
class ValidationError(AgenticWorkflowError):
    """Represent general validation errors across the platform."""
    pass


class SchemaValidationError(ValidationError):
    """Indicate a Pydantic or schema validation failure with details in context."""
    pass


# File System Errors
class FileSystemError(AgenticWorkflowError):
    """Represent file system related errors such as missing files or permissions."""
    pass


class FileNotFoundError(FileSystemError):
    """Indicate a required filesystem path was not found."""
    pass


class FilePermissionError(FileSystemError):
    """Indicate a permission error when accessing a filesystem resource."""
    pass


class DirectoryError(FileSystemError):
    """Indicate errors performing directory operations (create/remove)."""
    pass


# Ledger Errors
class LedgerError(AgenticWorkflowError):
    """Represent ledger subsystem errors related to persistent state."""
    pass


class LedgerValidationError(LedgerError):
    """Indicate ledger integrity or validation issues."""
    pass


class LedgerCorruptionError(LedgerError):
    """Indicate detected ledger corruption requiring administrative action."""
    pass


# Generation Errors
class GenerationError(AgenticWorkflowError):
    """Represent errors encountered during project or artifact generation."""
    pass


class TemplateError(GenerationError):
    """Indicate template processing or rendering errors."""
    pass


class TemplateNotFoundError(TemplateError):
    """Indicate a requested template file could not be located."""
    pass


# Service Errors
class ServiceError(AgenticWorkflowError):
    """Represent transient or permanent service-layer failures."""
    pass


class ServiceUnavailableError(ServiceError):
    """Indicate the downstream service is currently unavailable."""
    pass


class ServiceTimeoutError(ServiceError):
    """Indicate a timeout occurred while calling a downstream service."""
    pass


class HandlerError(AgenticWorkflowError):
    """Represent errors occurring inside CLI handlers or command wiring."""
    pass


class SessionError(AgenticWorkflowError):
    """Indicate errors managing agent sessions or session state."""
    pass


class ArtifactError(AgenticWorkflowError):
    """Represent errors during artifact creation, lookup, or validation."""
    pass


class GovernanceError(AgenticWorkflowError):
    """Base exception for governance policy or validation errors."""
    pass


class ValidationViolation(GovernanceError):
    """Indicate a specific governance rule has been violated."""
    pass


class PolicyConfigurationError(GovernanceError):
    """Indicate governance policy definitions are invalid or malformed."""
    pass


class ManifestError(AgenticWorkflowError):
    """Represent errors parsing or validating workflow manifests."""
    exit_code = 14


# Backwards-compatible alias for older code using `AgenticError`
AgenticError = AgenticWorkflowError


def handle_error(
    error: Exception,
    operation: str,
    context: Optional[ErrorContext] = None,
    log_level: str = "error",
    reraise: bool = True,
) -> None:
    """Log an exception with structured context and optionally re-raise it.

    Normalizes context into a flat stringified mapping and emits a single
    structured log record. This function intentionally returns `None` and
    does not modify program control flow unless `reraise` is True.
    """
    # Normalize context into stringified flat mapping to simplify logging.
    full_context: ErrorContext = {"operation": operation, "error_type": type(error).__name__}
    if context:
        for k, v in context.items():
            try:
                full_context[k] = str(v)
            except Exception:
                full_context[k] = "<unstringifiable>"

    if isinstance(error, AgenticWorkflowError):
        log_data = error.to_dict()
        # Merge context fields
        log_data.update({k: str(v) for k, v in full_context.items()})
    else:
        log_data = {
            "operation": full_context.get("operation", ""),
            "error_type": full_context.get("error_type", ""),
            "error_message": str(error),
        }
        log_data.update({k: str(v) for k, v in full_context.items()})

    # Log the error using stable, flat data suitable for structured loggers
    log_func = getattr(logger, log_level.lower(), logger.error)
    log_func(f"Error in {operation}: {error}", extra=log_data)

    if reraise:
        raise error


def validate_required(
    value: object,
    name: str,
    operation: str,
    context: Optional[ErrorContext] = None,
) -> None:
    """Ensure a required value is present and not an empty string/collection.

    Raises a `ValidationError` with stringified `ErrorContext` when the
    precondition is not met.
    """
    ctx: ErrorContext = {"operation": operation, "value_name": name}
    if context:
        for k, v in context.items():
            ctx[k] = str(v)

    if value is None:
        raise ValidationError(
            f"Required value '{name}' is None",
            error_code="REQUIRED_VALUE_MISSING",
            context=ctx,
        )

    if isinstance(value, str) and not value.strip():
        raise ValidationError(
            f"Required value '{name}' is empty",
            error_code="REQUIRED_VALUE_EMPTY",
            context=ctx,
        )

    if isinstance(value, (list, tuple, set)) and len(value) == 0:
        raise ValidationError(
            f"Required value '{name}' is empty",
            error_code="REQUIRED_VALUE_EMPTY",
            context=ctx,
        )


def validate_path_exists(path: Path, operation: str) -> None:
    """Check that `path` exists and raise `FileNotFoundError` when missing.

    The raised exception contains a minimal `ErrorContext` that maps to
    `operation` and `path`, suitable for static analysis.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Path does not exist: {path}",
            error_code="PATH_NOT_FOUND",
            context={"operation": operation, "path": str(path)},
        )


def validate_file_readable(path: Path, operation: str) -> None:
    """Verify that `path` exists, is a file, and is readable.

    Raises `FileSystemError` or `FilePermissionError` with a minimal
    `ErrorContext` when checks fail.
    """
    validate_path_exists(path, operation)

    if not path.is_file():
        raise FileSystemError(
            f"Path is not a file: {path}",
            error_code="NOT_A_FILE",
            context={"operation": operation, "path": str(path)},
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            f.read(1)  # Try to read one character to verify readability
    except (PermissionError, OSError) as e:
        raise FilePermissionError(
            f"File is not readable: {path}",
            error_code="FILE_NOT_READABLE",
            context={"operation": operation, "path": str(path)},
            cause=e,
        )


def safe_operation(
    operation_func: Callable[[], T],
    operation_name: str,
    context: Optional[ErrorContext] = None,
    fallback_value: Optional[T] = None,
    log_level: str = "error",
) -> Optional[T]:
    """Run `operation_func` and return a typed fallback on error.

    This utility captures exceptions, emits a structured log via
    `handle_error`, and returns `fallback_value` instead of raising.
    """
    try:
        return operation_func()
    except Exception as e:
        handle_error(
            e,
            operation_name,
            context=context,
            log_level=log_level,
            reraise=False,
        )
        return fallback_value
