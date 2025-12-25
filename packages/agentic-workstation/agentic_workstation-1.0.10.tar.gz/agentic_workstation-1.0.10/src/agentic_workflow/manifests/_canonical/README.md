# Canonical Data — Source of Truth

**Location:** `manifests/_canonical/`  
**Purpose:** Authoritative JSON data for all workflow definitions

---

## This is THE Source of Truth

All workflow data originates here. The YAML files in `manifests/workflows/` are **generated** from this canonical data and should **never be edited directly**.

```
┌──────────────────────────────────────────────────────────────┐
│               CANONICAL JSON (Edit Here)                     │
│               manifests/_canonical/<workflow>/               │
├──────────────────────────────────────────────────────────────┤
│  workflow.json   → Metadata, pipeline, stages, checkpoints  │
│  agents.json     → Agent IDs, roles, I/O contracts          │
│  artifacts.json  → Artifact registry with ownership         │
│  instructions.json → Behavioral guidance, workflow steps    │
└──────────────────────────────────────────────────────────────┘
                              │
                     validate (JSON Schema)
                              │
                     cross-reference check
                              │
                     generate (with comments)
                              ▼
┌──────────────────────────────────────────────────────────────┐
│              DERIVED YAML (Do Not Edit)                      │
│              manifests/workflows/<workflow>/                 │
└──────────────────────────────────────────────────────────────┘
```

---

### config (new)

The `config` section on `workflow.json` centralizes enforcement, logging, validation and bypass defaults. Example:

```json
"config": {
  "enforcement": {"mode": "strict","checkpoint_gating": "strict","handoff_gating": "strict"},
  "logging": {"require_session_log": true,"require_decision_log": true},
  "validation": {"run_validation_commands": true, "timeout_seconds": 30},
  "bypass": {"require_reason": true, "log_bypasses": true}
}
```

## Workflow Inventory

| Workflow | Agents | Purpose |
|----------|--------|---------|
| `planning` | 15 (A-00 to A-14) | Software project planning |
| `implementation` | 10 (6 core + 4 on-demand) | TDD-based development |
| `research` | 12 (8 core + 4 on-demand) | Academic research pipeline |
| `workflow-creation` | — | Meta-workflow for creating new workflows |

---

## File Relationships

```
workflow.json
    │
    ├── pipeline.order ────────► agents.json (agent IDs)
    ├── checkpoints[].owner ───► agents.json (agent IDs)
    ├── stages[].agents ───────► agents.json (agent IDs)
    └── input_from ────────────► (cross-workflow artifacts)

agents.json
    │
    ├── produces.* ────────────► artifacts.json (filenames)
    └── consumes.* ────────────► artifacts.json (filenames)
                                 OR input_from (cross-workflow)

artifacts.json
    │
    └── owner ─────────────────► agents.json (agent IDs)

instructions.json
    │
    ├── id ────────────────────► agents.json (must match)
    ├── slug ──────────────────► agents.json (must match)
    ├── handoff.next[].id ─────► agents.json (agent IDs)
    └── workflow.cycle ────────► workflow.json (cycles)
```

---

## Quick Reference: Required Fields

### workflow.json

```json
{
  "name": "workflow_id",           // Required
  "display_name": "Human Name",    // Required
  "pipeline": {                    // Required
    "order": ["A-00", "A-01"]      // Required: agent execution order
  }
}
```

### agents.json

```json
{
  "agents": [
    {
      "id": "A-00",                // Required: ^[A-Z]{1,2}-[A-Z0-9]{2,6}$
      "slug": "orchestrator",      // Required: ^[a-z0-9_]+$
      "role": "Orchestrator"       // Required: human-readable name
    }
  ]
}
```

### artifacts.json

```json
{
  "artifacts": [
    {
      "filename": "output.md",     // Required: file path
      "owner": "A-00",             // Required: valid agent ID
      "description": "...",        // Required: what it is
      "category": "core"           // Required: core|domain|reference|gating|log
    }
  ]
}
```

### instructions.json

```json
{
  "instructions": [
    {
      "id": "A-00",                // Required: must match agents.json
      "slug": "orchestrator",      // Required: must match agents.json
      "purpose": "..."             // Required: what agent achieves
    }
  ]
}
```

---

## Editing Patterns

### Pattern 1: Add New Agent

```bash
# 1. Edit agents.json - add agent definition
# 2. Edit artifacts.json - add produced artifacts
# 3. Edit instructions.json - add behavioral instructions
# 4. Edit workflow.json - add to pipeline.order
# 5. Validate
python3 -m scripts.validation.validate_canonical --workflow planning
```

### Pattern 2: Add Cross-Workflow Dependency

```bash
# In target workflow's workflow.json:
"input_from": {
  "source_workflow": {
    "artifacts": ["needed_file.md"]
  }
}

# In target workflow's agents.json:
"consumes": {
  "core": [
    {"file": "needed_file.md", "from_workflow": "source_workflow"}
  ]
}
```

### Pattern 3: Add Optional Consume

```json
"consumes": {
  "core": [
    "required_file.md",
    {"file": "optional_file.md", "required": false}
  ]
}
```

### Pattern 4: Define Reusable Cycle

```json
// workflow.json
"cycles": {
  "tdd": {
    "name": "TDD Micro-Cycle",
    "steps": ["ingest", "spec_test", "implement", "instrument", "log"]
  }
}

// instructions.json
{
  "id": "I-02",
  "workflow": {
    "cycle": "tdd"  // Reference by name
  }
}
```

---

## Validation Commands

```bash
# Validate single workflow
python3 -m scripts.validation.validate_canonical --workflow planning

# Validate all workflows
python3 -m scripts.validation.validate_canonical --all

# Quiet mode (errors only)
python3 -m scripts.validation.validate_canonical --all --quiet
```

---

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Invalid agent ID format` | ID doesn't match `^[A-Z]{1,2}-[A-Z0-9]{2,6}$` | Use format like `A-01`, `I-SEC` |
| `Owner not found in agents.json` | Artifact references nonexistent agent | Check agent ID spelling |
| `Produces 'X' not in artifacts.json` | Agent claims to produce unregistered artifact | Add artifact to `artifacts.json` |
| `Duplicate slug` | Two agents have same slug | Use unique slugs |
| `ID not found in agents.json` | Instruction references nonexistent agent | Add agent to `agents.json` |
| `Slug mismatch` | Instruction slug ≠ agent slug | Make slugs identical |

---

## Schema Locations

| Schema | Validates |
|--------|-----------|
| `_canonical_schemas/workflow.schema.json` | `*/workflow.json` |
| `_canonical_schemas/agents.schema.json` | `*/agents.json` |
| `_canonical_schemas/artifacts.schema.json` | `*/artifacts.json` |
| `_canonical_schemas/instructions.schema.json` | `*/instructions.json` |

---

## Migration Status

| Workflow | Status | Notes |
|----------|--------|-------|
| planning | ✅ Complete | 15 agents, 60+ artifacts |
| implementation | ✅ Complete | TDD workflow with cycles |
| research | ✅ Complete | Academic pipeline |
| workflow-creation | ✅ Complete | Meta-workflow |

---

## Related Files

- `../MANIFEST_README.md` — Complete manifests guide
- `CANONICAL_SCHEMA_SPECIFICATION.md` — Schema design document
- `CURRENT_SCHEMA_STATUS.md` — Migration status snapshot
