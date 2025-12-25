# nfa_coverage_matrix.md

Purpose: Centralized mapping of non-functional attributes (NFAs) to responsible planning artifacts, quantitative/qualitative metrics, targets, verification methods, and ownership.

Schema Columns:
| nfa_attribute | description | responsible_artifacts | metric | target | verification_method | owner | status |
|---------------|-------------|-----------------------|--------|--------|---------------------|-------|--------|
| Performance | Response time constraints | requirements_spec.md, testing_strategy.md | latency_p95_ms | 250 | performance test suite CI | Agent 8 / 9 | PLANNED |
| Scalability | Ability to handle growth | system_design.md, infrastructure_plan.md | max_rps_supported | 5k | load test + capacity_model | Agent 2 / 11 | PLANNED |
| Reliability | Availability & fault tolerance | resilience_architecture_plan.md, sre_readiness_plan.md | availability_percent | 99.9 | synthetic uptime monitor | Agent 11 | PLANNED |
| Security | Protection of assets | security_threat_assessment.md, secure_design_recommendations.md | critical_vuln_count | 0 | periodic security scan | Agent 3 | PLANNED |
| Compliance | Regulatory adherence | compliance_requirements.md | control_coverage_percent | 100 | control checklist audit | Agent 3 | PLANNED |
| Accessibility | Inclusive access | accessibility_compliance_plan.md | wcag_aa_criteria_passed | 95% | accessibility test & manual review | Agent 7 | PLANNED |
| Usability | User task efficiency | information_architecture.md, interaction_flows.md | task_success_rate | 90% | UX prototype study | Agent 7 | PLANNED |
| Observability | System introspection | observability_strategy.md, sre_readiness_plan.md | telemetry_gap_percent | <5% | instrumentation coverage audit | Agent 11 | PLANNED |
| Cost | Resource usage optimization | cloud_cost_projection.md | monthly_cost_estimate | <$X baseline | cost dashboard review | Agent 4 | PLANNED |
| Maintainability | Ease of updates | engineering_standards.md, development_workflow.md | refactor_cycle_days | <7 | code review metrics | Agent 8 | PLANNED |

Integrity Rules:
- Each NFA must list ≥1 responsible artifact.
- Metrics must be measurable or have defined qualitative proxy.
- Targets must be explicit; use placeholders if pending.
- Status progression: PLANNED → BASELINED → TRACKING → ACHIEVED.

Coverage Metrics:
- NFA Coverage % = (# NFAs with metric + verification_method) / (total NFAs) * 100.

Maintenance:
- Update status as baselines established.
- Adjust targets only via ADR if material change.

End of file.
