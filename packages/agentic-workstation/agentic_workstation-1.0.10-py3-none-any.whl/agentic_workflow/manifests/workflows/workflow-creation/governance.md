# Workflow Creation Governance

## Overview

This workflow guides users through creating new workflow packages for the
agentic-workflow-os system. It follows a waterfall model where each phase
completes fully before the next begins.

## Stages

| Stage | Agents | Purpose |
|-------|--------|---------|
| DISCOVERY | W00, W01, W02 | Understand domain and create skeleton |
| DEFINITION | W03, W04, W05 | Define agents, artifacts, instructions |
| GENERATION | W06 | Create templates for agent generation |
| VALIDATION | W07, W08 | Test and document the workflow |

## Quality Gates

### Gate 1: Domain Analysis Review (After W01)

**Purpose:** Ensure the domain is well understood before proceeding.

**Criteria:**
- [ ] Workflow purpose is clear and specific
- [ ] All phases identified with inputs/outputs
- [ ] Quality gates defined with criteria
- [ ] Key constraints documented

### Gate 2: Definition Review (After W04)

**Purpose:** Validate agent and artifact definitions before writing instructions.

**Criteria:**
- [ ] All agents have produces/consumes defined
- [ ] All artifacts mapped to agents
- [ ] Ownership is clear (one producer per artifact)
- [ ] Filenames are consistent

### Gate 3: Workflow Verified (After W07)

**Purpose:** Confirm the workflow works before documentation.

**Criteria:**
- [ ] All validators pass
- [ ] Agent generation produces correct output
- [ ] CLI commands work
- [ ] No critical issues remain

## Critical Format Rules

These rules MUST be followed or the workflow will not function:

### agents.yaml Format

```yaml
# CORRECT
produces:
  - filename.md
consumes:
  - other_file.md

# WRONG - do not use
artifacts:
  - artifact_id: "ART-001"
```

### instructions.yaml Format

```yaml
# CORRECT
agents:
  W01:
    purpose: |
      ...

# WRONG - do not use
instructions:
  W01:
    purpose: |
      ...
```

### Template Syntax

```markdown
# CORRECT - mustache style, no spaces
{{variable}}

# WRONG - Jinja2 style with spaces
{{ variable }}
```

## Artifact Flow

```
W01 produces → domain_notes.md, phase_list.md, gate_definitions.md
                     ↓
W02 consumes → domain_notes.md, phase_list.md, gate_definitions.md
W02 produces → workflow_yaml_draft.md, structure_checklist.md
                     ↓
W03 consumes → domain_notes.md, phase_list.md
W03 produces → agents_yaml_draft.md, handoff_flow.md
                     ↓
W04 consumes → agents_yaml_draft.md, handoff_flow.md
W04 produces → artifacts_yaml_draft.md, artifact_ownership_map.md
                     ↓
W05 consumes → agents_yaml_draft.md, artifacts_yaml_draft.md, domain_notes.md
W05 produces → instructions_yaml_draft.md, governance_md_draft.md
                     ↓
W06 consumes → instructions_yaml_draft.md, agents_yaml_draft.md
W06 produces → agent_header_tpl.md, agent_body_tpl.md, template_test_output.md
                     ↓
W07 consumes → (all drafts)
W07 produces → validation_report.md, test_results.md
                     ↓
W08 consumes → validation_report.md, domain_notes.md, agents_yaml_draft.md
W08 produces → workflow_readme.md, final_checklist.md, commit_message.md
```

## Decision Authority

| Decision Type | Authority |
|---------------|-----------|
| Workflow name and structure | Human (W01) |
| Agent boundaries | Human (W03) |
| Gate locations | Human (W01) |
| Template customization | Agent (W06) |
| Issue severity | Agent (W07) |
| Final approval | Human (W08) |

## Reference Documents

During workflow creation, agents should reference:

- `docs/workflow_creation/` — Detailed phase guides
- `manifests/workflows/planning/` — Example workflow
- `manifests/workflows/research/` — Another example
- `manifests/workflows/_schema.yaml` — Package schema

## Estimated Timeline

| Phase | Agent | Time |
|-------|-------|------|
| Discovery | W01 | 30-60 min |
| Structure | W02 | 15-30 min |
| Agents | W03 | 45-90 min |
| Artifacts | W04 | 30-60 min |
| Instructions | W05 | 60-120 min |
| Templates | W06 | 45-90 min |
| Testing | W07 | 30-60 min |
| Documentation | W08 | 30-45 min |
| **Total** | | **4-8 hours** |
