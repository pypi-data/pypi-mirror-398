# Workflow Creation Workflow

A meta-workflow that guides users through creating new workflow packages for the agentic-workflow-os system.

## Overview

This workflow provides structured guidance for:
- Analyzing domain requirements
- Defining workflow structure
- Designing agent sequences
- Specifying artifacts
- Writing instructions
- Creating templates
- Testing and validation
- Documentation

## Agents

| ID | Name | Purpose |
|----|------|---------|
| W00 | Workflow Guide | Entry point, helps define domain and goals |
| W01 | Domain Analyst | Analyzes domain, produces structured notes |
| W02 | Structure Architect | Defines workflow.yaml structure |
| W03 | Agent Designer | Creates agents.yaml with sequences |
| W04 | Artifact Mapper | Defines artifacts.yaml registry |
| W05 | Instructions Author | Writes instructions.yaml |
| W06 | Template Builder | Creates workflow-specific templates |
| W07 | Testing Specialist | Validates workflow package |
| W08 | Documentation Writer | Creates README and updates registry |

## Stages

1. **ANALYSIS** (W00, W01)
   - Gather domain requirements
   - Analyze agent needs
   - Human checkpoint: Approve domain analysis

2. **DESIGN** (W02, W03)
   - Define workflow structure
   - Design agent sequences
   - Human checkpoint: Approve agent design

3. **IMPLEMENTATION** (W04, W05, W06)
   - Create artifact registry
   - Write agent instructions
   - Build templates

4. **VALIDATION** (W07, W08)
   - Test workflow generation
   - Create documentation
   - Human checkpoint: Final approval

## Artifacts

### System
- `session_context.md` — Session tracking
- `handoff_log.md` — Agent transitions
- `decision_log.md` — Design decisions

### Phase Outputs
- `domain_notes.md` — Domain analysis
- `workflow.yaml` — Workflow structure
- `agents.yaml` — Agent definitions
- `artifacts.yaml` — Artifact registry
- `instructions.yaml` — Per-agent instructions
- `governance.md` — Governance rules
- `templates/` — Workflow templates
- `test_results.md` — Validation report
- `README.md` — Workflow documentation

## Usage

```bash
# Initialize a workflow-creation project
python3 -m scripts.cli.workflow init my_new_workflow --workflow workflow-creation --description "Creating a new workflow"

# Start with the guide
cd projects/my_new_workflow
./workflow activate W00

# Follow the agent sequence
./workflow handoff --from W00 --to W01 --artifacts "input/requirements.md"
```

## Critical Format Rules

When creating workflow files:

1. **agents.yaml** — Use `produces: [file.md]` not artifact_id references
2. **instructions.yaml** — Root key must be `agents:` not `instructions:`
3. **Templates** — Use Jinja2 `{{ variable }}` (whitespace-friendly) and prefer `.j2` templates

See `docs/workflow_creation/` for detailed guidance.

## Example Output

After completing this workflow, you'll have:

```
manifests/workflows/<your-workflow>/
├── workflow.yaml      # Metadata, stages, checkpoints
├── agents.yaml        # Agent definitions
├── artifacts.yaml     # Artifact registry
├── instructions.yaml  # Per-agent instructions
├── governance.md      # Governance rules
├── README.md          # Documentation
└── templates/
   └── prompts/
      ├── agent_header.md.j2
      └── agent_body.md.j2  (or use global `_base/agent_base.md.j2`)
```

## See Also

- [Workflow Creation Guide](../../../docs/workflow_creation/00_INDEX.md)
- [Schema Reference](../../../docs/WORKFLOW_CREATION_SCHEMA.md)
- [Planning Workflow](../planning/) — Example workflow
- [Research Workflow](../research/) — Another example
