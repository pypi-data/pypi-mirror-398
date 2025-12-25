# api_log.md

Purpose: Domain-specific ledger for API & integration planning decisions, gaps, assumptions, risks, and intake summaries.

Entry Format (pipe-delimited):
`timestamp | entry_type | id_refs | summary | status`

Entry Types:
- API-INTAKE: Initial or subsequent structured intake summaries.
- API-DEC: Decision entries using ID pattern API-DEC-###.
- API-QUESTION: Clarification questions awaiting response.
- API-GAP: Missing required input blocking specificity.
- API-ASSUMP: Provisional assumption substituting a gap.
- API-RISK: Reliability, performance, or integration risk flagged (link RISK-###).

ID Patterns:
- Decisions: API-DEC-001, API-DEC-002, ...
- Assumptions (optional granular): API-ASSUMP-001, or grouped under API-ASSUMP entry_type.

Usage Rules:
- Each API-DEC must reference affected conceptual endpoints or integration boundaries.
- Replace API-ASSUMP with API-DEC once clarified.
- Escalate unresolved API-GAP after 2 cycles to ADR consideration.

Governance:
- Cross-link relevant REQ IDs via `api_endpoints` in `traceability_matrix.md`.
- Major protocol/versioning shifts → ADR plus API-DEC entry summarizing rationale.
- Keep chronological ordering; do not edit historical rows—append corrections.

Initial Entry Placeholder:
`2025-11-22T00:00:00Z | API-INTAKE | (none) | Initialized api_log.md per ADR introducing API & UX domain logs | active`
