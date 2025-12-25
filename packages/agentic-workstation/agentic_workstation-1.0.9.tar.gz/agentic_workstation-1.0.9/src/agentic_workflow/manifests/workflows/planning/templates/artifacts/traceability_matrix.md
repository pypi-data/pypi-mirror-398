# traceability_matrix.md

Purpose: Provide a structured, machine-parseable mapping of requirements through architectural realization, API surface, data model entities, test coverage, and reliability metrics (SLO references), enabling completeness and impact analysis.

Schema Definition:
Columns: requirement_id | requirement_type | requirement_description | architecture_components | api_endpoints | data_entities | test_case_ids | nfa_attributes | risk_ids | slo_metrics | status | security_controls | accessibility_criteria | version | last_writer_agent | iteration_cycle

Field Conventions:
- requirement_id: Stable unique key (e.g., REQ-001). Immutable.
- requirement_type: FUNCTIONAL | NON_FUNCTIONAL.
- architecture_components: Comma-separated canonical component names from `system_design.md`.
- api_endpoints: Comma-separated endpoint identifiers from `api_specifications.md` (format: METHOD /path).
- data_entities: Comma-separated entity names from `logical_data_model.md`.
- test_case_ids: Placeholder references (e.g., TC-001) to be instantiated in test plans.
- nfa_attributes: Performance | Security | Reliability | Scalability | Accessibility | Usability | Compliance | Observability | Cost.
- risk_ids: References into `risk_register.md` (e.g., RISK-004) if requirement introduces risk.
- slo_metrics: Comma-separated SLO names (e.g., latency_p95, availability_99_9) from `sre_readiness_plan.md`.
- status: PLANNED | IMPLEMENTED | VERIFIED (planning phase uses PLANNED).

Integrity Rules:
- Every functional requirement MUST map to ≥1 architecture_component and ≥1 test_case_id.
- Every non-functional requirement MUST map to ≥1 nfa_attribute and ≥1 slo_metric (if reliability/performance).
- No orphan architecture_component (must appear in ≥1 row).
- No orphan api_endpoint for functional requirements that imply interaction.
- Risk-bearing requirements must list risk_ids with mitigation path.

Matrix (Initial Empty Skeleton):

| requirement_id | requirement_type | requirement_description | architecture_components | api_endpoints | data_entities | test_case_ids | nfa_attributes | risk_ids | slo_metrics | status | security_controls | accessibility_criteria | version | last_writer_agent | iteration_cycle |
|----------------|------------------|-------------------------|-------------------------|---------------|---------------|---------------|----------------|----------|------------|--------|------------------|------------------------|---------|-------------------|-----------------|
| REQ-001        | FUNCTIONAL       | <define>                | <component>             | GET /example  | <entity>      | TC-001        |                |          | latency_p95| PLANNED| CTRL-001          | WCAG-2.1-AA?           | 1.0.0   | 1                 | BASE            |
| REQ-002        | NON_FUNCTIONAL   | <define> (e.g. latency) | <component>             |               |               | TC-002        | Performance    | RISK-001 | latency_p95| PLANNED| CTRL-002          |                        | 1.0.0   | 2                 | BASE            |
| REQ-003        | FUNCTIONAL       | <define>                | <component>             | POST /item    | <entity>      | TC-003        | Security       | RISK-002 | availability_99_9 | PLANNED| CTRL-003      |                        | 1.0.0   | 2                 | BASE            |

Maintenance Workflow:
1. Agent 1 assigns requirement_id and baseline description.
2. Agent 2 populates architecture_components.
3. Agent 6 enriches api_endpoints.
4. Agent 5 supplies data_entities.
5. Agent 9 allocates test_case_ids placeholders.
6. Agent 11 adds slo_metrics for reliability-impacting requirements.
7. Risk register integration: security/data/infrastructure risks appended as risk_ids.

Validation Targets (for `validate_agents.py` extension):
- Detect missing mandatory mappings.
- Produce coverage ratios per dimension.
- Output JSON view for dashboards (`traceability_matrix.json`).

Coverage Metrics Formulas:
- Functional Requirement Architecture Coverage % = (functional requirements with ≥1 architecture_component) / (total functional requirements) * 100.
- Requirement Test Coverage % = (requirements with ≥1 test_case_id) / (total requirements) * 100.
- NFR SLO Coverage % = (non-functional requirements mapped to ≥1 slo_metric) / (total non-functional requirements) * 100.

Change Control:
- Additions: append new rows preserving ordering by requirement_id.
- Modifications: update only mapped fields; never alter requirement_id.
- Deletions: require ADR and explicit cascade review of dependent artifacts.

JSON Sidecar Recommendation:
- Provide parallel `traceability_matrix.json` for automation ingestion; structure: array of objects keyed by field names.

End of file.
