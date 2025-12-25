# TDD Cycle Log

> Test-Driven Development tracking for {{project_name}}

## Metadata

| Field | Value |
|-------|-------|
| **Project** | {{project_name}} |
| **Created** | {{timestamp}} |
| **Workflow** | Implementation |

---

## TDD Micro-Cycles

<!-- Each entry represents a RED → GREEN → REFACTOR cycle -->

### Format

```yaml
- cycle_id: TDD-001
  timestamp: YYYY-MM-DD HH:MM
  agent: I2
  test_file: tests/unit/test_example.py
  test_name: test_function_does_x
  red:
    status: FAIL
    assertion: "Expected X, got Y"
  green:
    status: PASS
    implementation: src/module.py::function_name
  refactor:
    changes: "Extracted helper, renamed variable"
    still_green: true
  story_id: US-001
```

---

## Cycles

<!-- Add TDD cycles below -->

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Cycles | 0 |
| Successful Cycles | 0 |
| Failed Refactors | 0 |
| Average Cycle Time | - |

---

## Violations

<!-- Any TDD violations (implementation without test) -->

| Timestamp | Agent | File | Description | Resolution |
|-----------|-------|------|-------------|------------|

---

## Notes

<!-- TDD session notes -->
