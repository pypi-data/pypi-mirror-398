# technology_watchlist.md

Purpose: Monitor technology items for currency, deprecation, and replacement guidance to avoid usage of deprecated code, methods, or techniques.

Schema:
| item | category | current_status | deprecation_date | replacement | action_required | risk_to_plan | action_window_days | owner | review_cycle_days |
|------|----------|----------------|------------------|-------------|-----------------|-------------|--------------------|-------|-------------------|
| Python 3.10 | Language Runtime | ACTIVE | N/A | Python 3.11+ | Evaluate migration window | LOW  | 30 | Agent 8 | 90 |
| Library-X 1.x | Third-Party Lib | DEPRECATING | 2026-03-01 | Library-X 2.x | Plan upgrade path | MEDIUM | 30 | Agent 8 | 30 |
| LegacyAuth | Internal Module | DEPRECATED | 2025-09-01 | NewAuthService | Remove references | HIGH | 14 | Agent 3 | 14 |
| React Class Components | Frontend Pattern | DEPRECATING | N/A | Functional + Hooks | Refactor legacy UI | MEDIUM | 45 | Agent 7 | 60 |
| InsecureHashMD5 | Crypto Function | DEPRECATED | 2020-01-01 | SHA-256 | Audit & replace | HIGH | 7 | Agent 3 | 14 |

Status Values: ACTIVE | DEPRECATING | DEPRECATED | REPLACED.

Integrity Rules:
- Each DEPRECATING/DEPRECATED item must list a replacement and action_required.
- review_cycle_days ≤ 90; HIGH-RISK items ≤ 30.

Metrics:
- Deprecated Resolution Rate = (# DEPRECATED items with action_required completed) / (total DEPRECATED items) * 100.

Governance:
- Additions/removals require ADR if impacting multiple artifacts.
- Quarterly audit updates status transitions.
- Audit schedule now logged via `exchange_log.md` iteration or handoff events (context_log archived).

End of file.
