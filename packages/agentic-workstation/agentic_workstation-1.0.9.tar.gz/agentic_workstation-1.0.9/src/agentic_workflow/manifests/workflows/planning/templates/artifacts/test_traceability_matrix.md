# test_traceability_matrix.md

Purpose: Optional specialized matrix separating testing focus from broader requirement traceability; links requirements to concrete test case identifiers and test types.

Schema Columns:
| requirement_id | test_case_id | test_type | coverage_goal | automation | owner | status |
|----------------|--------------|-----------|---------------|-----------|-------|--------|
| REQ-001 | TC-UNIT-001 | unit | 100% branch | YES | Agent 9 | PLANNED |
| REQ-001 | TC-INTEG-010 | integration | critical paths | YES | Agent 9 | PLANNED |
| REQ-001 | TC-CONTRACT-005 | contract | all fields validated | YES | Agent 9 | PLANNED |
| REQ-002 | TC-PERF-020 | performance | p95 latency <= target | YES | Agent 9 | PLANNED |
| REQ-004 | TC-RESIL-002 | resilience | graceful failover | PARTIAL | Agent 9 | PLANNED |
| REQ-005 | TC-ACCESS-003 | accessibility | form usable via keyboard | YES | Agent 9 | PLANNED |

Integrity Rules:
- Each HIGH risk requirement must have ≥ unit + integration + one specialized test (contract/performance/resilience/security).
- test_case_id unique across matrix.
- automation field: YES | PARTIAL | NO.

Metrics:
- Automated Test Ratio = (# rows automation=YES) / (total rows) * 100.
- High Risk Requirement Full Coverage % = (# HIGH requirements meeting integrity rule) / (total HIGH requirements) * 100.

Status: PLANNED → IMPLEMENTED → VERIFIED.

Maintenance:
- Synchronize with `test_coverage_model.md` changes.
- Update coverage_goal detail as implementation clarifies scope.

End of file.
