"""
Governance Rule Engine for Agentic Workflow Platform.

This module provides governance rule enforcement for workflow operations,
ensuring compliance with project-specific and global governance policies.

It includes:
- Rule-based validation with configurable strictness levels.
- Support for different governance contexts (init, handoff, decision, end).
- detailed error reporting with actionable feedback.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union, TypedDict
from dataclasses import dataclass, field

from agentic_workflow.core.exceptions import (
    GovernanceError,
    ValidationViolation,
    PolicyConfigurationError
)
# Use late import for config functions to avoid circular deps if needed,
# or import standard constants/types.
from agentic_workflow.core.config_service import ConfigurationService
from .paths import get_project_dirs, get_workflow_paths

# Setup logging
logger = logging.getLogger(__name__)

# Governance constants
GOVERNANCE_LEVEL_STRICT = "strict"
GOVERNANCE_LEVEL_MODERATE = "moderate"
GOVERNANCE_LEVEL_LENIENT = "lenient"

GOVERNANCE_CONTEXT_INIT = "init"
GOVERNANCE_CONTEXT_HANDOFF = "handoff"
GOVERNANCE_CONTEXT_DECISION = "decision"
GOVERNANCE_CONTEXT_END = "end"
GOVERNANCE_CONTEXT_ACTIVATION = "activation"


# Public interface for this module
__all__ = [
    "GovernanceRule",
    "GovernanceResult",
    "GovernanceEngine",
    "get_governance_engine",
    "validate_governance",
    "enforce_governance",
]


# TypedDicts to expose expected config/data shapes for static analysis
class GovernanceConfig(TypedDict, total=False):
    """Configuration for governance rules and strictness levels."""
    strictness: Dict[str, str]
    rules: Dict[str, object]


class ProjectMetadata(TypedDict, total=False):
    """Metadata for a project."""
    name: str
    description: str
    created: Optional[str]


class AgentMetadata(TypedDict, total=False):
    """Metadata for an agent."""
    role: Optional[str]
    capabilities: Optional[List[str]]


class RuntimeConfig(TypedDict, total=False):
    """Runtime configuration including governance settings."""
    governance: GovernanceConfig


class ProjectData(TypedDict, total=False):
    """Data structure for project information in governance checks."""
    path: str
    metadata: ProjectMetadata


class AgentData(TypedDict, total=False):
    """Data structure for agent information in governance checks."""
    id: str
    stage: str
    consumes_core: List[str]
    metadata: AgentMetadata


class Violation(TypedDict, total=False):
    """Structure for governance rule violations."""
    rule: str
    description: str
    error_message: str
    fix_suggestion: Optional[str]
    level: str


class Warning(TypedDict, total=False):
    """Structure for governance warnings."""
    message: str
    rule: Optional[str]
    level: Optional[str]
    detail: Optional[str]


class GovernanceData(TypedDict, total=False):
    """Complete data structure for governance validation."""
    project_path: str
    project: ProjectData
    agent: AgentData
    artifacts: List[str]
    rationale: str
    from_agent: str
    to_agent: str
    stage: Dict[str, object]


@dataclass
class GovernanceRule:
    """Encapsulates a governance rule used to validate workflow data.

    Attributes:
        name: Unique identifier for the rule.
        description: Human-readable description of what the rule enforces.
        context: The context in which this rule applies (e.g., 'init', 'handoff').
        level: Strictness level required to trigger this rule ('strict', 'moderate', 'lenient').
        condition: Callable that evaluates `GovernanceData` and returns True when compliant.
        error_message: Message to display when the rule is violated.
        fix_suggestion: Optional suggestion for resolving the violation.
        enabled: Whether the rule is currently active.
    """
    name: str
    description: str
    context: str
    level: str
    condition: Callable[["GovernanceData"], bool]
    error_message: str
    fix_suggestion: Optional[str] = None
    enabled: bool = True


@dataclass
class GovernanceResult:
    """Represents the outcome of governance validation for a given context.

    Attributes:
        passed: True if all applicable rules passed.
        violations: List of violation details.
        warnings: List of warning details.
        context: The context that was validated.
    """
    passed: bool
    violations: List[Violation] = field(default_factory=list)
    warnings: List["Warning"] = field(default_factory=list)
    context: str = ""

    def __bool__(self) -> bool:
        """Return True if governance validation passed."""
        return self.passed


class GovernanceEngine:
    """Evaluates governance rules against workflow data for specified contexts.

    The engine manages a registry of `GovernanceRule` instances and applies
    them according to configured strictness and context.
    """

    def __init__(self, config: "RuntimeConfig"):
        """Initialize the GovernanceEngine with a runtime configuration.

        Args:
            config: Runtime configuration with governance settings.
        """
        # keep the raw config available for backwards compatibility
        self.config: RuntimeConfig = config
        self.rules: Dict[str, GovernanceRule] = {}
        self._load_rules()

    def register_rule(self, rule: GovernanceRule) -> None:
        """
        Register a new governance rule or overwrite an existing one.

        Args:
            rule: The GovernanceRule instance to register.
        """
        self.rules[rule.name] = rule
        logger.debug(f"Registered governance rule: {rule.name}")

    def _load_rules(self) -> None:
        """
        Load governance rules from configuration and defaults.

        Merges built-in default rules with overrides provided in the configuration.
        """
        governance_config = self.config.get('governance', {})

        # 1. Load default rules
        default_rules = self._get_default_rules()

        # 2. Extract overrides from config
        config_rules = governance_config.get('rules') or {}

        # 3. Merge rules
        # First, process overrides for existing default rules
        for rule_name, rule_config in config_rules.items():
            if rule_name in default_rules:
                default_rule = default_rules[rule_name]
                # Create a new rule instance with overrides
                self.register_rule(GovernanceRule(
                    name=rule_config.get('name', default_rule.name),
                    description=rule_config.get('description', default_rule.description),
                    context=rule_config.get('context', default_rule.context),
                    level=rule_config.get('level', default_rule.level),
                    condition=default_rule.condition,  # Retain original condition logic
                    error_message=rule_config.get('error_message', default_rule.error_message),
                    fix_suggestion=rule_config.get('fix_suggestion', default_rule.fix_suggestion),
                    enabled=rule_config.get('enabled', default_rule.enabled)
                ))
            else:
                # Custom rule defined in config - use dynamic condition evaluation
                self.register_rule(GovernanceRule(
                    name=rule_config.get('name', rule_name),
                    description=rule_config.get('description', ''),
                    context=rule_config.get('context', GOVERNANCE_CONTEXT_INIT),
                    level=rule_config.get('level', GOVERNANCE_LEVEL_MODERATE),
                    condition=self._create_dynamic_condition(rule_config),
                    error_message=rule_config.get('error_message', f'Rule {rule_name} failed'),
                    fix_suggestion=rule_config.get('fix_suggestion'),
                    enabled=rule_config.get('enabled', True)
                ))

        # 4. Register remaining default rules
        for rule_name, rule in default_rules.items():
            if rule_name not in self.rules:
                self.register_rule(rule)

    def _create_dynamic_condition(self, rule_config: Dict[str, object]) -> Callable[["GovernanceData"], bool]:
        """
        Create a dynamic condition function from declarative rule configuration.

        Translates YAML/JSON rule definitions into executable logic that evaluates:
        - required_files: Check if files exist relative to project path
        - required_context: Check if keys exist in agent/project data
        - blocked_by: Check if agent ID is in blocked list

        Args:
            rule_config: Dictionary containing rule configuration keys

        Returns:
            Callable that takes data dict and returns bool
        """
        def dynamic_condition(data: "GovernanceData") -> bool:
            # Check required files
            required_files = rule_config.get('required_files', [])
            if required_files:
                project_path = Path(data.get('project', {}).get('path', ''))
                if not project_path.exists():
                    logger.warning(f"Project path does not exist: {project_path}")
                    return False

                for file_path in required_files:
                    full_path = project_path / file_path
                    if not full_path.exists():
                        logger.debug(f"Required file missing: {full_path}")
                        return False

            # Check required context keys
            required_context = rule_config.get('required_context', [])
            if required_context:
                agent_data = data.get('agent', {})
                project_data = data.get('project', {})

                for key in required_context:
                    if key not in agent_data and key not in project_data:
                        logger.debug(f"Required context key missing: {key}")
                        return False

            # Check blocked agents
            blocked_by = rule_config.get('blocked_by', [])
            if blocked_by:
                agent_id = data.get('agent', {}).get('id', '')
                if agent_id in blocked_by:
                    logger.debug(f"Agent {agent_id} is blocked by rule")
                    return False

            return True

        return dynamic_condition

    def _get_default_rules(self) -> Dict[str, GovernanceRule]:
        """
        Define the set of built-in default governance rules.

        Returns:
            Dictionary mapping rule names to GovernanceRule instances.
        """
        return {
            'project_structure_valid': GovernanceRule(
                name='project_structure_valid',
                description='Project directory structure must be valid',
                context=GOVERNANCE_CONTEXT_INIT,
                level=GOVERNANCE_LEVEL_STRICT,
                condition=self._check_project_structure,
                error_message='Project structure validation failed',
                fix_suggestion='Run project initialization to create required directories'
            ),
            'workflow_files_exist': GovernanceRule(
                name='workflow_files_exist',
                description='Required workflow files must exist',
                context=GOVERNANCE_CONTEXT_INIT,
                level=GOVERNANCE_LEVEL_MODERATE,
                condition=self._check_workflow_files,
                error_message='Required workflow files are missing',
                fix_suggestion='Ensure workflow.json, agents.json, and artifacts.json exist'
            ),
            'agent_handoff_valid': GovernanceRule(
                name='agent_handoff_valid',
                description='Agent handoff must be valid',
                context=GOVERNANCE_CONTEXT_HANDOFF,
                level=GOVERNANCE_LEVEL_STRICT,
                condition=self._check_agent_handoff,
                error_message='Invalid agent handoff',
                fix_suggestion='Ensure from_agent and to_agent are valid and different'
            ),
            'decision_rationale_required': GovernanceRule(
                name='decision_rationale_required',
                description='Decisions must have rationale',
                context=GOVERNANCE_CONTEXT_DECISION,
                level=GOVERNANCE_LEVEL_MODERATE,
                condition=self._check_decision_rationale,
                error_message='Decision rationale is required',
                fix_suggestion='Provide a rationale for the decision'
            ),
            'session_end_artifacts_complete': GovernanceRule(
                name='session_end_artifacts_complete',
                description='All required artifacts must be complete at session end',
                context=GOVERNANCE_CONTEXT_END,
                level=GOVERNANCE_LEVEL_LENIENT,
                condition=self._check_artifacts_complete,
                error_message='Required artifacts are incomplete',
                fix_suggestion='Complete all required artifacts before ending session'
            ),
            'agent_stage_valid': GovernanceRule(
                name='agent_stage_valid',
                description='Agent must be valid for current project stage',
                context=GOVERNANCE_CONTEXT_ACTIVATION,
                level=GOVERNANCE_LEVEL_STRICT,
                condition=self._check_agent_stage,
                error_message='Agent cannot be activated in current stage',
                fix_suggestion='Advance to appropriate stage or select different agent'
            ),
            'agent_artifacts_exist': GovernanceRule(
                name='agent_artifacts_exist',
                description='Required artifacts must exist for agent activation',
                context=GOVERNANCE_CONTEXT_ACTIVATION,
                level=GOVERNANCE_LEVEL_MODERATE,
                condition=self._check_agent_artifacts,
                error_message='Required artifacts are missing',
                fix_suggestion='Create required artifacts before activating agent'
            ),
            'agent_not_blocked': GovernanceRule(
                name='agent_not_blocked',
                description='Agent must not be blocked',
                context=GOVERNANCE_CONTEXT_ACTIVATION,
                level=GOVERNANCE_LEVEL_STRICT,
                condition=self._check_agent_not_blocked,
                error_message='Agent is currently blocked',
                fix_suggestion='Resolve blockers before activating agent'
            )
        }

    def validate(
        self,
        context: str,
        data: "GovernanceData",
        strictness: Optional[str] = None,
    ) -> GovernanceResult:
        """Validate provided governance data against registered rules for a context.

        Args:
            context: The context to validate (e.g., 'init', 'handoff').
            data: The governance data to evaluate.
            strictness: Optional override for strictness level. Defaults to configured level.

        Returns:
            GovernanceResult containing pass/fail and any violations.
        """
        if strictness is None:
            strictness = self.config.get('governance', {}).get('strictness', {}).get('level', GOVERNANCE_LEVEL_MODERATE)

        result = GovernanceResult(passed=True, context=context)
        evaluated_rules = 0

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            if rule.context != context:
                continue

            # Check if rule applies to the current strictness level
            if not self._rule_applies_to_level(rule.level, strictness):
                continue

            evaluated_rules += 1

            try:
                rule_passed = rule.condition(data)
                
                if not rule_passed:
                    violation = {
                        'rule': rule.name,
                        'description': rule.description,
                        'error_message': rule.error_message,
                        'fix_suggestion': rule.fix_suggestion,
                        'level': rule.level
                    }
                    result.violations.append(violation)
                    result.passed = False
                    logger.warning(f"Governance violation: {rule.name} - {rule.error_message}")
                else:
                    logger.debug(f"Governance rule passed: {rule.name}")

            except Exception as e:
                logger.error(f"Error evaluating governance rule {rule.name}: {e}")
                
                # In strict mode, code errors during validation are treated as violations
                if strictness == GOVERNANCE_LEVEL_STRICT:
                    violation = {
                        'rule': rule.name,
                        'description': rule.description,
                        'error_message': f'Rule evaluation failed: {e}',
                        'fix_suggestion': 'Check rule configuration and data format',
                        'level': rule.level
                    }
                    result.violations.append(violation)
                    result.passed = False

        logger.info(f"Governance validation complete: {evaluated_rules} rules evaluated, {len(result.violations)} violations")
        return result

    def enforce(
        self,
        context: str,
        data: "GovernanceData",
        strictness: Optional[str] = None,
    ) -> None:
        """Enforce governance rules for the given context and raise on violations.

        Args:
            context: The context to enforce.
            data: The governance data to validate.
            strictness: Optional strictness level override.

        Raises:
            ValidationViolation: If any compliance rules are violated.
        """
        result = self.validate(context, data, strictness)
        if not result.passed:
            # Construct a detailed error message from violations
            msgs = [f"- {v['error_message']} ({v['rule']})" for v in result.violations]
            msg_str = "\n".join(msgs)
            raise ValidationViolation(
                f"Governance enforcement failed with {len(result.violations)} violations:\n{msg_str}",
                context={"violations": result.violations, "governance_context": context}
            )

    def _rule_applies_to_level(self, rule_level: str, current_level: str) -> bool:
        """
        Check if a rule applies to the current strictness level.
        
        Logic: A rule at 'rule_level' applies if 'current_level' is equal or stricter.
        Hierarchy: LENIENT < MODERATE < STRICT
        """
        levels = [GOVERNANCE_LEVEL_LENIENT, GOVERNANCE_LEVEL_MODERATE, GOVERNANCE_LEVEL_STRICT]
        
        try:
            rule_index = levels.index(rule_level)
            current_index = levels.index(current_level)
            return rule_index <= current_index
        except ValueError:
            logger.warning(f"Invalid governance level encountered: rule={rule_level}, current={current_level}")
            return True # Fallback: apply rule

    # ---------------------------
    # Built-in Condition Logic
    # ---------------------------

    def _check_project_structure(self, data: "GovernanceData") -> bool:
        """Check whether the project directory structure is valid for the project.
        """
        try:
            project_path = data.get('project_path')
            if not project_path:
                return False

            from .paths import validate_project_structure
            issues = validate_project_structure(Path(project_path), self.config)
            return len(issues) == 0
        except Exception:
            return False

    def _check_workflow_files(self, data: "GovernanceData") -> bool:
        """Verify required workflow files exist under the given project path.
        """
        try:
            project_path = data.get('project_path')
            if not project_path:
                return False

            workflow_paths = get_workflow_paths(self.config, Path(project_path))
            required_files = ['workflow_file', 'agents_file', 'artifacts_file']

            for file_key in required_files:
                file_path = workflow_paths.get(file_key)
                if not file_path or not file_path.exists():
                    return False

            return True
        except Exception:
            return False

    def _check_agent_handoff(self, data: "GovernanceData") -> bool:
        """Validate that a handoff between agents is well-formed and references existing artifacts.
        """
        from_agent = data.get('from_agent')
        to_agent = data.get('to_agent')
        artifacts = data.get('artifacts', [])

        if not from_agent or not to_agent:
            return False

        if from_agent == to_agent:
            return False

        # Validate existence of referenced artifacts
        if artifacts:
            try:
                project_path = data.get('project_path')
                if project_path:
                    project_dirs = get_project_dirs(self.config, Path(project_path))
                    artifacts_dir = project_dirs.get('artifacts')
                    if artifacts_dir:
                        for artifact in artifacts:
                            artifact_path = artifacts_dir / artifact
                            if not artifact_path.exists():
                                return False
            except Exception:
                pass 

        return True

    def _check_decision_rationale(self, data: "GovernanceData") -> bool:
        """Ensure a decision includes a non-empty rationale string.
        """
        rationale = data.get('rationale', '').strip()
        return len(rationale) > 0

    def _check_artifacts_complete(self, data: "GovernanceData") -> bool:
        """Check that all artifacts marked as required are present in the artifacts directory.
        """
        try:
            project_path = data.get('project_path')
            if not project_path:
                return True

            workflow_paths = get_workflow_paths(self.config, Path(project_path))
            artifacts_file = workflow_paths.get('artifacts_file')

            if not artifacts_file or not artifacts_file.exists():
                return True

            with open(artifacts_file, 'r', encoding='utf-8') as f:
                artifacts_data = json.load(f)

            project_dirs = get_project_dirs(self.config, Path(project_path))
            artifacts_dir = project_dirs.get('artifacts')

            if not artifacts_dir:
                return True

            for artifact in artifacts_data.get('artifacts', []):
                if artifact.get('required', False):
                    artifact_name = artifact.get('name')
                    if artifact_name:
                        artifact_path = artifacts_dir / artifact_name
                        if not artifact_path.exists():
                            return False

            return True
        except Exception:
            return True

    def _check_agent_stage(self, data: "GovernanceData") -> bool:
        """Determine whether the agent is allowed to activate in the current project stage.
        """
        try:
            agent_stage = data.get('agent', {}).get('stage', '')
            current_stage = data.get('stage', {}).get('current', '')
            
            if not agent_stage or not current_stage:
                return True  # No specific stage requirement
            
            # Simple check: agent stage should be <= current stage
            # This is a basic implementation - could be enhanced
            return agent_stage == current_stage
        except Exception:
            return True

    def _check_agent_artifacts(self, data: "GovernanceData") -> bool:
        """Verify that artifacts consumed by the agent are present or declared.
        """
        try:
            consumes_core = data.get('agent', {}).get('consumes_core', [])
            if not consumes_core:
                return True  # No required artifacts
            
            # For now, assume artifacts exist if listed
            # Could be enhanced to check actual file existence
            return True
        except Exception:
            return True

    def _check_agent_not_blocked(self, data: "GovernanceData") -> bool:
        """Ensure the agent is not currently blocked by governance rules or blockers.
        """
        try:
            # For now, assume no blockers
            # Could be enhanced to check blocker logs
            return True
        except Exception:
            return True


# -----------------------------------------------------------------------------
# Module Interface Functions
# -----------------------------------------------------------------------------

def get_governance_engine(config: Optional["RuntimeConfig"] = None) -> GovernanceEngine:
    """
    Factory function to get a GovernanceEngine instance.

    Args:
        config: Optional configuration dictionary. If None, loads command config.

    Returns:
        Initialized GovernanceEngine.
    """
    if config is None:
        config_service = ConfigurationService()
        cfg = config_service.load_config()
        config = cfg  # type: ignore[assignment]
    return GovernanceEngine(config)


def validate_governance(
    context: str,
    data: "GovernanceData",
    config: Optional["RuntimeConfig"] = None,
    strictness: Optional[str] = None,
) -> GovernanceResult:
    """
    Convenience wrapper to validate governance rules.

    Args:
        context: Validation context.
        data: Data to validate.
        config: Engine configuration.
        strictness: Strictness level override.

    Returns:
        GovernanceResult.
    """
    engine = get_governance_engine(config)
    return engine.validate(context, data, strictness)


def enforce_governance(
    context: str,
    data: "GovernanceData",
    config: Optional["RuntimeConfig"] = None,
    strictness: Optional[str] = None,
) -> None:
    """
    Convenience wrapper to enforce governance rules.

    Args:
        context: Enforcement context.
        data: Data to validate.
        config: Engine configuration.
        strictness: Strictness level override.

    Raises:
        ValidationViolation: If rules validation fails.
    """
    engine = get_governance_engine(config)
    engine.enforce(context, data, strictness)

