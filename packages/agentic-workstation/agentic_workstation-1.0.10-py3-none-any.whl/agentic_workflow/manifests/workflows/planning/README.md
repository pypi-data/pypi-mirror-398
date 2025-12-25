# Planning Workflow Package

> Software project planning workflow with 14 specialized agents.

## Overview

This workflow package provides a comprehensive planning pipeline for software projects, covering:

- **Requirements & Scope** (Agent 0-1)
- **Architecture & Design** (Agent 2)
- **Security & Compliance** (Agent 3)
- **Infrastructure & DevOps** (Agent 4)
- **Data Architecture** (Agent 5)
- **API & Integration** (Agent 6)
- **UX & Interaction** (Agent 7)
- **Developer Workflow** (Agent 8)
- **QA & Testing** (Agent 9)
- **Product Alignment** (Agent 10)
- **SRE & Reliability** (Agent 11)
- **Transition Readiness** (Agent 12)
- **Feasibility Audit** (Agent 13)

## Package Contents

| File | Purpose |
|------|---------|
| `workflow.yaml` | Workflow metadata, pipeline order, globals, checkpoints |
| `agents.yaml` | Agent definitions with produces/consumes contracts |
| `artifacts.yaml` | Artifact registry with ownership and descriptions |
| `instructions.yaml` | Per-agent domain instructions (lean format) |
| `governance.md` | Workflow-specific governance rules |

## Usage

```bash
# Initialize a project with this workflow
python3 -m scripts.cli.workflow init myproject --workflow planning --description "My planning project"

# Or use the default (planning is default)
python3 -m scripts.cli.workflow init myproject --description "My project"
```

## Pipeline Order

```
Orchestrator → A0 (Incubation) → A1 (Planning) → A2 (Architecture) →
A3 (Security) → A4 (Infra) → A5 (Data) → A6 (API) → A7 (UX) →
A8 (Dev Workflow) → A9 (QA) → A10 (Product) → A11 (SRE) →
A12 (Transition) → A13 (Audit) → Implementation Handoff
```

## Checkpoints

| After Agent | Type | Description |
|-------------|------|-------------|
| A2 (Architecture) | Human Approval | Architecture review before security |
| A12 (Transition) | Human Approval | Transition audit before final check |
| A13 (Audit) | Gate | All critical gaps addressed |

## Version History

- **1.0.0** (2025-11-29): Initial modular package structure
