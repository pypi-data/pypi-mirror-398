# Test Suite Manifest

> Test coverage plan for {{project_name}}

## Metadata

| Field | Value |
|-------|-------|
| **Project** | {{project_name}} |
| **Created** | {{timestamp}} |
| **TDD Mode** | Active |
| **Coverage Target** | 80% minimum |

---

## Test Strategy

### Test Pyramid

```
        /\
       /  \  E2E Tests (5-10%)
      /----\
     /      \  Integration Tests (20-30%)
    /--------\
   /          \  Unit Tests (60-70%)
  /--------------\
```

---

## Test Categories

### Unit Tests

| Module | Test File | Coverage | Status |
|--------|-----------|----------|--------|
| ... | tests/unit/test_*.py | ...% | Not Started |

### Integration Tests

| Integration Point | Test File | Status |
|-------------------|-----------|--------|
| ... | tests/integration/test_*.py | Not Started |

### E2E Tests

| Scenario | Test File | Status |
|----------|-----------|--------|
| ... | tests/e2e/test_*.py | Not Started |

---

## Test-to-Requirement Traceability

| Requirement ID | Test IDs | Coverage Status |
|----------------|----------|-----------------|
| REQ-001 | TC-001, TC-002 | Pending |

---

## Test Data

### Test Fixtures

| Fixture | Purpose | Location |
|---------|---------|----------|
| ... | ... | tests/fixtures/ |

### Mock Services

| Service | Mock Location | Description |
|---------|---------------|-------------|
| ... | tests/mocks/ | ... |

---

## CI/CD Integration

### Test Commands

```bash
# Run all tests
pytest tests/ --cov=src --cov-report=html

# Run unit tests only
pytest tests/unit/ -v

# Run with TDD watch mode
ptw tests/ -- --last-failed
```

### Coverage Requirements

- Minimum line coverage: 80%
- Branch coverage: 70%
- No untested critical paths

---

## Notes

<!-- Test planning notes -->
