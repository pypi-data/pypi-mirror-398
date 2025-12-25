```markdown
---
artifact_name: <artifact_file_name.md>
owner_agent: Agent <N>
upstream_inputs:
	- project_overview.md
	- requirements_spec.md
downstream_outputs:
	- <downstream_artifact.md>
version: 1.0.0
status: DRAFT # Allowed: DRAFT | REVIEW | APPROVED | VERSIONED | SUPERSEDED
review_cycle_days: 90
governance:
	traceability_updates: false # true if artifact modifies requirement mappings
	adr_required_on_change: false # true if structural changes demand ADR
	last_writer_agent: <agent_id>
	iteration_cycle: BASE
audit_links:
	exchange_log_ref: "" # Handoff ID enabling this work
	feasibility_gap_refs: [] # list IFIA-GAP-### IDs impacting this artifact
	integration_mismatch_refs: [] # list mismatch IDs from integration_consistency_audit.md
	logic_coverage_impacts: [] # REQ IDs affected per logic_completeness_review.md
	deprecation_risk_refs: [] # items from deprecation_risk_matrix.md

# `<Human Title for Artifact>`

Purpose: One-line description of what this artifact captures.

Required Inputs:
- `project_overview.md` (example)
- `requirements_spec.md`

Outputs:
- List any downstream artifacts this file enables.

Ownership:
- Primary: <team/person>
- Contributes: <team/person>

Summary:
A short executive summary of the artifact and its intended consumers.

Contents:
- Background / Context
- Assumptions & Constraints
- Key Decisions (link to ADRs)
- Detailed content (models, diagrams, lists)
- Actionable next steps

Traceability & Audit References:
- Relevant `traceability_matrix.md` REQ rows (list REQ-IDs)
- Non-functional mappings (`nfa_coverage_matrix.md` rows)
- Accessibility criteria (from `accessibility_compliance_plan.md` if applicable)
- Feasibility gaps affecting this artifact (IFIA-GAP IDs)
- Integration mismatches resolved (integration_consistency_audit.md references)
- Logic coverage impacts (logic_completeness_review.md)
- Deprecation risks (deprecation_risk_matrix.md) with mitigation status

Open Risks:
- List risks with references to `risk_register.md` (if applicable)

Review Status:
- Current status with date and reviewer(s)

Example usage notes:
- Where to store diagrams
- Recommended filename conventions

---

Appendix:
- Timestamp: YYYY-MM-DD
- Author: @owner
- Version: 1.0.0
- Last Writer Agent: <agent_id>
- Iteration Cycle: BASE
- Feasibility Audit Pass: <TRUE|FALSE|N/A>
- Outstanding Blocker Gaps: <count>

```