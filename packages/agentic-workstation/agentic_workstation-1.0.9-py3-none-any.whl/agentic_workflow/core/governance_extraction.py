"""Extract governance rules from workflow manifests into internal config.

Translate workflow manifest governance sections into the normalized
governance configuration format consumed by the GovernanceEngine.
"""

import logging
from typing import Dict, List, Mapping, MutableMapping

from agentic_workflow.core.governance import (
    GOVERNANCE_LEVEL_STRICT,
    GOVERNANCE_LEVEL_MODERATE,
    GOVERNANCE_LEVEL_LENIENT,
)

logger = logging.getLogger(__name__)


__all__ = ["extract_governance_from_workflow"]


def extract_governance_from_workflow(workflow_data: Mapping[str, object]) -> MutableMapping[str, object]:
    """Convert a workflow manifest into a governance configuration mapping.

    Read the `workflow` and `config` sections from the provided manifest and
    produce a mapping containing `strictness` and `rules` suitable for the
    internal GovernanceEngine.

    Args:
        workflow_data: Parsed workflow manifest mapping.

    Returns:
        A mutable mapping representing governance configuration.
    """
    governance_config: MutableMapping[str, object] = {}
    workflow_info = workflow_data.get("workflow", {}) or {}
    workflow_governance = workflow_info.get("governance", {}) or {}

    # If no governance in manifest, return empty config but don't error
    if not workflow_governance:
        # We may still derive rules from enforcement settings below
        pass

    # 1. Extract strictness level
    enforcement_config = (workflow_info.get("config", {}) or {}).get("enforcement", {}) or {}
    mode = enforcement_config.get("mode", "moderate")

    level_mapping = {
        "strict": GOVERNANCE_LEVEL_STRICT,
        "moderate": GOVERNANCE_LEVEL_MODERATE,
        "lenient": GOVERNANCE_LEVEL_MODERATE,
    }
    governance_config["strictness"] = {"level": level_mapping.get(mode, GOVERNANCE_LEVEL_MODERATE)}

    # 2. Extract specific rule overrides
    rules: MutableMapping[str, object] = {}

    # Checkpoint gating rule
    checkpoint_gating = enforcement_config.get("checkpoint_gating", "moderate")
    if checkpoint_gating == "strict":
        rules["strict_checkpoint_gating"] = {
            "name": "Strict Checkpoint Gating",
            "description": "All checkpoints must be completed before proceeding",
            "context": "handoff",
            "level": "strict",
            "error_message": "Cannot proceed without completing required checkpoints",
            "fix_suggestion": "Complete all upstream checkpoints before handoff",
        }

    # Handoff gating rule
    handoff_gating = enforcement_config.get("handoff_gating", "moderate")
    if handoff_gating == "strict":
        rules["strict_handoff_gating"] = {
            "name": "Strict Handoff Gating",
            "description": "All handoffs must be properly logged",
            "context": "handoff",
            "level": "strict",
            "error_message": "Handoff must be properly logged before proceeding",
            "fix_suggestion": "Ensure handoff is logged in agent_log/exchange_log.md",
        }

    # Required artifacts rule (Derived from artifacts section)
    _extract_artifact_rules(workflow_data, rules)

    # Decision logging rule
    logging_config = (workflow_info.get("config", {}) or {}).get("logging", {}) or {}
    if logging_config.get("require_decision_log", False):
        rules["decision_logging_required"] = {
            "name": "Decision Logging Required",
            "description": "All decisions must be logged",
            "context": "decision",
            "level": "moderate",
            "error_message": "Decision must be logged",
            "fix_suggestion": "Log decision in agent_log/decision_log.md",
        }

    # Naming convention rule
    artifact_naming = workflow_governance.get("artifact_naming", {}) or {}
    if artifact_naming.get("enforce_snake_case", False):
        rules["snake_case_artifacts"] = {
            "name": "Snake Case Artifacts",
            "description": "All artifacts must follow snake_case naming",
            "context": "init",
            "level": "lenient",
            "error_message": "Artifact names must be in snake_case",
            "fix_suggestion": "Rename artifacts to follow snake_case convention",
        }

    governance_config["rules"] = rules
    return governance_config


def _extract_artifact_rules(workflow_data: Mapping[str, object], rules: MutableMapping[str, object]) -> None:
    """Populate `rules` with artifact-derived governance rules.

    This helper inspects the workflow manifest `artifacts` section and adds
    checks such as required artifact verification.

    Args:
        workflow_data: Parsed workflow manifest mapping.
        rules: Mutable mapping to be updated with artifact rules.
    """
    artifacts_data = workflow_data.get("artifacts", {}) or {}
    if isinstance(artifacts_data, list):
        artifacts = artifacts_data
    else:
        artifacts = artifacts_data.get("artifacts", []) if isinstance(artifacts_data, dict) else []

    required_artifacts = [art for art in artifacts if isinstance(art, dict) and art.get("required", False)]

    if required_artifacts:
        rules["required_artifacts_check"] = {
            "name": "Required Artifacts Check",
            "description": "All required artifacts must be present",
            "context": "end",
            "level": "moderate",
            "error_message": "Required artifacts are missing",
            "fix_suggestion": "Ensure all required artifacts are created before session end",
        }
