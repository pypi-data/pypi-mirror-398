# security_control_trace.md

Purpose: Trace threats to recommended security controls and implementing artifacts; support verification and residual risk analysis.

Schema Columns:
| threat_id | threat_description | control_id | control_description | implementing_artifacts | verification | status | residual_risk |
|-----------|--------------------|------------|---------------------|------------------------|--------------|--------|---------------|
| THREAT-001 | Unauthorized access via weak auth | CTRL-001 | Enforce strong auth & MFA | secure_design_recommendations.md, engineering_standards.md | auth penetration test | PLANNED | LOW |
| THREAT-002 | Data exfiltration via API enumeration | CTRL-002 | Rate limiting & anomaly detection | api_specifications.md, infrastructure_plan.md | dynamic security test | PLANNED | MEDIUM |
| THREAT-003 | Injection attacks (SQL/Command) | CTRL-003 | Parameterized queries & input validation | engineering_standards.md, system_design.md | static analysis + fuzz | PLANNED | LOW |
| THREAT-004 | Sensitive data at rest exposure | CTRL-004 | Encryption + key rotation | infrastructure_plan.md, storage_strategy.md | config audit | PLANNED | LOW |
| THREAT-005 | Insufficient logging for incidents | CTRL-005 | Security event logging & alerting | observability_strategy.md, sre_readiness_plan.md | log configuration review | PLANNED | MEDIUM |

Integrity Rules:
- Each threat mapped to ≥1 control.
- Each control mapped to ≥1 implementing artifact.
- Residual risk must be LOW/MEDIUM/HIGH with rationale documented (appendix if HIGH).

Status Values: PLANNED → IMPLEMENTED → VERIFIED.

Metrics:
- Control Coverage % = (# threats with ≥1 control) / (total threats) * 100.
- Verification Coverage % = (# controls with verification defined) / (total controls) * 100.

End of file.
