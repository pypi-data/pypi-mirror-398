# ux_log.md

Purpose: Domain-specific ledger for UX planning decisions, assumptions, gaps, risks, and structured intake summaries across personas, IA, journeys, flows, and wireframes.

Entry Format (pipe-delimited):
`timestamp | entry_type | id_refs | summary | status`

Entry Types:
- UX-INTAKE: Initial/updated UX intake summaries.
- UX-DEC: Decision entries (navigation restructure, persona addition) using UX-DEC-###.
- UX-QUESTION: Clarifying questions awaiting response.
- UX-GAP: Missing input blocking UX specificity (e.g., data shape unknown).
- UX-ASSUMP: Provisional UX assumption substituting a gap.
- UX-RISK: Usability/accessibility risk (link RISK-### or accessibility criteria).

ID Patterns:
- Decisions: UX-DEC-001, UX-DEC-002, ...
- Assumptions optional granular: UX-ASSUMP-001 or grouped by entry_type.

Usage Rules:
- Each UX-DEC must reference affected artifacts (information_architecture.md, user_journeys.md, etc.).
- Promote UX-ASSUMP to UX-DEC once validated.
- Escalate persistent UX-GAP after 2 cycles; consider ADR if structural.

Governance:
- Cross-link REQ IDs for journeys and flows via `api_endpoints` or accessibility criteria in `traceability_matrix.md`.
- Major navigation/persona structural changes → ADR plus UX-DEC record.
- Append-only; do not rewrite historical entries.

Initial Entry Placeholder:
`2025-11-22T00:00:00Z | UX-INTAKE | (none) | Initialized ux_log.md per ADR introducing API & UX domain logs | active`
