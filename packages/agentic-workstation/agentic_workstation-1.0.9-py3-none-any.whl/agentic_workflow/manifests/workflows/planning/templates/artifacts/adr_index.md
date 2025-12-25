# adr_index.md

Purpose: Consolidated ADR inventory with impact index linking decisions to affected artifacts and subsequent supersessions.

Schema:
| adr_file | title | date | status | impacted_artifacts | supersedes | superseded_by | revision_ref | traceability_impacts |
|----------|-------|------|--------|--------------------|------------|---------------|--------------|----------------------|
| 2025-11-20-standardize-artifacts.md | Standardize Agent Artifacts and Canonical Manifest | 2025-11-20 | Accepted | AGENT_MANIFEST.md, all agent_files/* | None | None | 1.0.0 | REQ-001 |
| 2025-11-21-add-project-guide-agent.md | Introduce Pre-Pipeline Project Guide (Agent 0) | 2025-11-21 | Accepted | AGENT_MANIFEST.md, agent_files/A0_Project Guide & Idea Incubation.md | None | None | 1.0.0 | REQ-002 |
| 2025-11-22-add-agent-13-implementation-feasibility-auditor.md | Add Implementation Feasibility & Integration Integrity Auditor (Agent 13) | 2025-11-22 | Accepted | AGENT_MANIFEST.md, agent_files/A13_Implementation Feasibility & Integration Integrity Auditor.md | None | None | 1.0.0 | REQ-003 |

Impact Index Summary:
- Manifest Governance (2025-11-20): Establishes canonical artifact naming; impacts validation logic and all downstream prompt consistency.
- Agent 0 Introduction (2025-11-21): Adds optional ideation precursor; impacts Agent 1 optional inputs; requires validator dynamic ID handling.
- Agent 13 Addition (2025-11-22): Introduces feasibility & integration integrity audit layer; adds new artifacts (gap report, integration audit, logic review, deprecation matrix, scrutiny log) improving pre-implementation risk detection.

Metrics:
- ADR Acceptance Rate = (# Accepted ADRs) / (Total ADRs) * 100.
- Pending Impact Resolution Count = (# Proposed ADRs affecting validation/manifest not yet accepted).

Integrity Rules:
- Each ADR entry must include status and at least one impacted_artifact.
- supersedes and superseded_by use ADR filename or None.
- Proposed ADRs cannot list superseded_by.
- revision_ref indicates ADR file version; traceability_impacts lists REQ IDs directly influenced.

Maintenance:
- Update status when ADR moves from Proposed → Accepted → (optionally) Superseded.
- Append new rows; never modify historical accepted row content except for superseded_by updates.

End of file.
