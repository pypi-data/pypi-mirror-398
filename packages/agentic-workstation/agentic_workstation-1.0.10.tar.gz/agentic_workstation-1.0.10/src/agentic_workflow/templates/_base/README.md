# Template Base Directory

> Canonical block definitions and template contracts for the agent workflow system.

**Version:** 1.0  
**Created:** 2025-12-05  
**Status:** Active

---

## 1. Canonical Block Set

Templates are composed of **blocks** — logical sections that can be required or optional.

| Block | Required | Description |
|-------|----------|-------------|
| `frontmatter` | ✅ | YAML metadata block with agent/project context and CLI commands |
| `quickref` | ✅ | Layer 1 quick reference — essential context visible without scrolling |
| `body` | ✅ | Main content (agent instructions, workflow steps, responsibilities) |
| `handoff` | ✅ | Next agent info, required artifacts/logs, pre-handoff checklist |
| `checklist` | ⚪ | Session start/end checklists (driven by `logging_policy`) |
| `checkpoint_warning` | ⚪ | Displayed when checkpoint follows this agent |
| `governance_footer` | ⚪ | Governance rules, bypass policies, domain constraints |

### Block Markers

Blocks are delimited by Jinja2 block tags:

```jinja2
{% block frontmatter %}
---
agent_id: {{ agent_id }}
...
---
{% endblock %}

{% block quickref %}
## Quick Reference
...
{% endblock %}
```

---

## 2. Required Frontmatter Keys

All agent templates **must** include these frontmatter keys:

### Universal (All Templates)

| Key | Type | Description |
|-----|------|-------------|
| `agent_id` | string | Agent identifier (e.g., `A-02`, `P-01`) |
| `workflow_name` | string | Workflow type (`planning`, `implementation`, etc.) |
| `project_name` | string | Current project name |

### Agent Templates

| Key | Type | Description |
|-----|------|-------------|
| `agent_role` | string | Human-readable role title |
| `agent_type` | string | `core`, `support`, or `on-demand` |
| `stage` | string | Workflow stage ID |

### Session Templates

| Key | Type | Description |
|-----|------|-------------|
| `context_file` | string | Path to context index file |
| `cli_commands` | array | Ready-to-use CLI commands |
| `checkpoint_pending` | boolean | Whether checkpoint follows current agent |

---

## 3. Block Contracts by Template Type

### Agent Prompt (`agent_base.md.j2`)

| Block | Required | Notes |
|-------|----------|-------|
| `frontmatter` | ✅ | Must include agent keys |
| `quickref` | ✅ | Agent summary, artifact tables |
| `body` | ✅ | Instructions, workflow steps, boundaries |
| `handoff` | ✅ | Next agent(s), checklist |
| `checkpoint_warning` | ⚪ | Only if checkpoint follows |
| `governance_footer` | ⚪ | Domain rules, constraints |

### Orchestrator Prompt (`orchestrator_base.md.j2`)

| Block | Required | Notes |
|-------|----------|-------|
| `frontmatter` | ✅ | Must include workflow metadata |
| `quickref` | ✅ | Pipeline overview, agent table |
| `body` | ✅ | Orchestration instructions |
| `pipeline` | ✅ | Visual pipeline with checkpoints |
| `governance_footer` | ⚪ | Workflow-level rules |

### Session Template (`session_base.md.j2`)

| Block | Required | Notes |
|-------|----------|-------|
| `frontmatter` | ✅ | CLI commands, context path |
| `quickref` | ✅ | Base rules, protocol |
| `checklist` | ✅ | Start/end session items |
| `body` | ✅ | Session instructions |
| `checkpoint_warning` | ⚪ | If checkpoint after current agent |

### Context Index (`context_index_base.md.j2`)

| Block | Required | Notes |
|-------|----------|-------|
| `frontmatter` | ✅ | Agent context metadata |
| `body` | ✅ | Context sections |
| `artifact_tracking` | ✅ | Artifact status table |

---

## 4. Template Inheritance

Templates use Jinja2 `{% extends %}` for inheritance:

```
templates/
├── _base/
│   ├── workflow_base.md.j2    ← Layer 1: Common to all workflows
│   ├── agent_base.md.j2       ← Layer 2: All agents
│   ├── orchestrator_base.md.j2
│   └── session_base.md.j2
├── _roles/
│   ├── analyst/
│   │   └── agent_body.md.j2   ← Layer 3: Role-specific
│   ├── engineer/
│   └── auditor/
└── planning/                   ← Layer 4: Workflow-specific override
    └── agent_body.md.j2
```

**Inheritance Chain Example:**

```
planning/agent_body.md.j2
    └── extends _roles/analyst/agent_body.md.j2
        └── extends _base/agent_base.md.j2
            └── extends _base/workflow_base.md.j2
```

---

## 5. Partial Includes

Reusable sections live in `_partials/`:

| Partial | Purpose |
|---------|---------|
| `frontmatter_helpers.j2` | Macros for frontmatter generation |
| `handoff_section.j2` | Handoff display with checklist |
| `checkpoint_warning.j2` | Checkpoint gating warning |
| `governance_footer.j2` | Governance rules footer |
| `artifact_table.j2` | Tiered artifact tables (core/domain/log) |
| `cli_commands.j2` | CLI command rendering |

**Usage:**

```jinja2
{% include '_partials/handoff_section.j2' %}
```

---

## 6. Validation Rules

Templates are validated by `scripts/validation/validate_templates.py`:

| Rule | Severity | Description |
|------|----------|-------------|
| `required-blocks` | ERROR | All required blocks must be present |
| `no-raw-placeholders` | ERROR | No `{{` or `}}` in rendered output |
| `frontmatter-schema` | ERROR | Frontmatter keys must match schema |
| `block-order` | WARN | Blocks should follow canonical order |
| `no-empty-blocks` | WARN | Blocks should have content |

---

## 7. File Naming Convention

| Pattern | Description | Example |
|---------|-------------|---------|
| `*_base.md.j2` | Base templates for inheritance | `agent_base.md.j2` |
| `*.md.j2` | Jinja2 templates | `agent_body.md.j2` |
| `*.j2` | Partial templates (no markdown) | `handoff_section.j2` |
| `*.md.tpl` | Legacy mustache templates (deprecated) | `agent_body.md.tpl` |

---

## 8. Migration Notes

### From `.tpl` to `.j2`

Old mustache-style templates use `{{placeholder}}`. New Jinja2 templates use `{{ variable }}`.

**Migration steps:**
1. Create new `.j2` template with Jinja2 syntax
2. Test rendering with smoke tests
3. Update generator to use new template
4. Archive old `.tpl` file

---

*Last updated: 2025-12-05*
