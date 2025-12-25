# Implementation Workflow

Test-driven software implementation workflow with 6 core agents + 4 on-demand agents.

## Overview

The implementation workflow follows the **"Test-First, Trace-Always, Gate-Before-Go"** philosophy to transform planning artifacts into working, tested, documented code.

## Prerequisites

### Source Project

This workflow requires a completed **planning** project with all artifacts. The planning project must have:

- All core planning artifacts generated
- Implementation readiness report completed (A11)
- Transition handoff plan completed (A12)
- Feasibility and integration audits passed (A13)

### Project Linking

On initialization, artifacts from the planning project are copied to `input/`:

```bash
./workflow init my-app-impl --from ../my-app-planning
```

To refresh artifacts from planning:

```bash
./workflow refresh --from-planning
```

---

## Agents

### Core Pipeline Agents (6)

| ID | Role | Description |
|----|------|-------------|
| **I0** | Implementation Orchestrator | Session management, gating, coordination |
| **I1** | Scaffold & DevOps Architect | Project structure, CI/CD, infrastructure |
| **I2** | Backend & Data Engineer | API, business logic, data layer |
| **I3** | Frontend & UX Engineer | UI components, interactions, accessibility |
| **I4** | Quality & Validation Specialist | Testing, code review, observability |
| **I5** | Release & Integration Manager | Release packaging, changelog, deployment |

### On-Demand Agents (4)

| ID | Role | When to Invoke |
|----|------|----------------|
| **I-SEC** | Security Auditor | Security review at any stage |
| **I-DOC** | Documentation Specialist | Comprehensive documentation |
| **I-DS** | Data Steward | Complex migrations, PII handling |
| **I-PERF** | Performance Engineer | Performance analysis, optimization |

---

## Pipeline

```
┌─────────┐     ┌─────────┐     ┌─────────┬─────────┐     ┌─────────┐     ┌─────────┐
│   I0    │────▶│   I1    │────▶│   I2    │   I3    │────▶│   I4    │────▶│   I5    │
│  Orch   │     │Scaffold │     │ Backend │Frontend │     │ Quality │     │ Release │
└─────────┘     └────┬────┘     └────┬────┴────┬────┘     └────┬────┘     └────┬────┘
                     │               │         │               │               │
                     ▼               └────┬────┘               ▼               ▼
               [APPROVAL]                │                [APPROVAL]      [APPROVAL]
                                   [GATE: tests]
```

### Checkpoints

1. **After I1** (Human Approval): Validate project structure
2. **After I2/I3** (Gate): Unit tests must pass
3. **After I4** (Human Approval): Quality sign-off
4. **After I5** (Human Approval): Final release approval

---

## Workflow Stages

Each task progresses through 8 stages:

| Stage | Description |
|-------|-------------|
| **INTAKE** | Task received, context loaded |
| **SPEC** | Mini-spec created with REQ-ID trace |
| **APPROVED** | Human/gate approval granted |
| **TEST_WRITE** | Failing tests authored (TDD red) |
| **IMPLEMENT** | Code written (TDD green) |
| **INSTRUMENT** | Observability added |
| **VERIFY** | Tests pass, coverage met |
| **COMPLETE** | Ready for handoff |

---

## TDD Configuration

TDD is configurable per project:

```yaml
tdd:
  enforce: true          # Default
  skip_for:
    - documentation
    - configuration
  require_coverage: 80   # Minimum coverage %
```

### V-Model Micro-Cycle

```
ingest → spec_test → implement → instrument → log
```

---

## Gating

### Pre-Activation Check

Before any agent can be activated:

```bash
./workflow gate-check I2
```

Checks:
- `implementation_feasibility_gap_report.md` — no blockers
- `integration_consistency_audit.md` — no critical issues

### Blocker Handling

If blockers found:
1. `blocked=true` flag set
2. Agent activation halted
3. Resolve in source artifact
4. Clear flag and retry

---

## Artifact Tiers

Artifacts are loaded in tiers to manage context:

| Tier | When Loaded | Example |
|------|-------------|---------|
| **Core** | On agent activation | implementation_task_list.md |
| **Domain** | Based on task scope | business_logic_map.md |
| **Reference** | On demand | user_journeys.md |

---

## Input Artifacts (from Planning)

These artifacts are copied from the planning project:

| Category | Artifacts |
|----------|-----------|
| Requirements | requirements_spec.md, constraints_and_assumptions.md |
| Architecture | architecture_overview.md, system_design.md, data_flow_overview.md |
| API | api_specifications.md, integration_plan.md, communication_flows.md |
| Data | logical_data_model.md, data_strategy.md, data_governance_plan.md |
| Infrastructure | infrastructure_plan.md, cicd_pipeline_plan.md, deployment_model.md |
| Security | secure_design_recommendations.md |
| UX | conceptual_wireframes.md, interaction_flows.md, accessibility_compliance_plan.md |
| Testing | testing_strategy.md, test_architecture_plan.md |
| Business | business_logic_map.md |
| Handoff | implementation_task_list.md, implementation_handoff_plan.md |
| Gating | implementation_feasibility_gap_report.md, integration_consistency_audit.md |

---

## Implementation Artifacts (produced)

| Agent | Artifacts |
|-------|-----------|
| I1 | codebase_scaffold_map.md, cicd_config/, infrastructure/, SETUP.md |
| I2 | src/backend/, db/migrations/, tests/unit/backend/, api_realization_status.md |
| I3 | src/frontend/, tests/components/, tests/a11y/, ui_component_inventory.md |
| I4 | tests/e2e/, test_execution_register.md, coverage_report.md |
| I5 | CHANGELOG.md, release_notes.md, release/ |

---

## CLI Commands

### Core Commands

```bash
# Initialize implementation project from planning
./workflow init my-app-impl --from ../my-app-planning

# Refresh artifacts from planning
./workflow refresh --from-planning

# Check gating before agent activation
./workflow gate-check I2

# Activate an agent
./workflow activate I1

# Invoke on-demand agent
./workflow invoke I-SEC
./workflow invoke I-SEC --scope code
```

### Artifact Commands

```bash
# List artifacts by tier
./workflow artifact list --tier core
./workflow artifact list --tier domain

# Show artifact (auto-resolves)
./workflow artifact show requirements_spec.md
```

---

## Flags

Orthogonal flags that can be set at any stage:

| Flag | Type | Purpose |
|------|------|---------|
| blocked | boolean | Gating has blockers |
| blocker_reason | string | What's blocking |
| debt_items | list | Technical debt logged |
| retry_count | number | VERIFY retry attempts |

---

## File Structure

```
projects/my-app-impl/
├── input/                    # Copied from planning
│   ├── requirements_spec.md
│   ├── architecture_overview.md
│   └── ...
├── artifacts/                # Implementation outputs
│   ├── codebase_scaffold_map.md
│   ├── api_realization_status.md
│   └── ...
├── agent_files/              # Generated agent prompts
│   ├── I0_Implementation_Orchestrator.md
│   ├── I1_Scaffold_DevOps_Architect.md
│   └── ...
├── agent_log/                # Agent handoffs and decisions
├── src/                      # Source code
│   ├── backend/
│   └── frontend/
├── tests/                    # Test files
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── ...
├── db/                       # Database
│   └── migrations/
├── docs/                     # Documentation
├── release/                  # Release packages
├── implementation_index.md   # Project index
├── active_session.md         # Current session state
└── project.yaml              # Project configuration
```

---

## Governance

See `governance.md` for detailed rules on:
- TDD enforcement
- Traceability requirements
- Gating policies
- Stage definitions
- Documentation requirements
- Technical debt management

---

## Related Documents

- [Planning Workflow](../planning/README.md) — Source workflow
- [Workflow Schema](../../../docs/WORKFLOW_CREATION_SCHEMA.md) — Workflow creation reference
- [Workflow Development Guide](../../../docs/WORKFLOW_DEVELOPMENT_GUIDE.md) — Detailed guide

---

*This workflow is part of the agentic-workflow-os system.*
