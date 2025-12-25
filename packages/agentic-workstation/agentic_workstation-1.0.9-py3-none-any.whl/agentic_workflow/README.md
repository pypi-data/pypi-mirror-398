# Scripts Package

Modular Python scripts for the multi-agent workflow system.

**Version:** 4.0.0  
**Last verified:** 2025-11-29

> **This document is the SINGLE SOURCE OF TRUTH for CLI API documentation.**  
> Generated project documentation references this file.

---

## CLI Reference

### Root Wrapper (convenience)

There is a repository-level wrapper script named `agent` placed at the repo root.
It execs the repository virtualenv Python (if present at `.venv/` or `venv/`) and
invokes the `scripts.cli.workflow` module, forwarding arguments. This provides a
convenient shorthand when you are operating from the repo root:

```bash
# From repo root (make executable first: `chmod +x ./agent`)
./agent init my_project --workflow planning
./agent list-workflows --json
```

The wrapper prefers an existing `.venv` or `venv` in the repo; if none is
found it falls back to the current Python interpreter.

### Two Ways to Use the CLI

#### 1. From Project Directory (Recommended)

Each project has a local `./workflow` wrapper that auto-detects the project context:

```bash
cd projects/my_project
./workflow status
./workflow activate A01
agentic handoff --to A02 --artifacts "spec.md"
```

#### 2. From Repository Root

Use the Python module with explicit project argument:

```bash
python3 -m scripts.cli.workflow init my_project --workflow planning --description "My project"
python3 -m scripts.cli.workflow refresh my_project
python3 -m scripts.cli.workflow list-workflows
python3 -m scripts.cli.workflow list-workflows --json
```

---

## Command Reference

### Project Management

| Command | From Project Dir | From Repo Root |
|---------|------------------|----------------|
| Initialize | N/A | `python3 -m scripts.cli.workflow init <project> --workflow planning --description "Project description"` |
| Refresh | N/A | `python3 -m scripts.cli.workflow refresh <project>` |
| List Workflows | N/A | `python3 -m scripts.cli.workflow list-workflows [--json]` |

### Session Lifecycle

| Command | From Project Dir | From Repo Root |
|---------|------------------|----------------|
| Status | `./workflow status` | `python3 -m scripts.cli.workflow status <project>` |
| Activate | `./workflow activate <agent_id>` | `python3 -m scripts.cli.workflow activate <project> <agent_id>` |
| End | `./workflow end` | `python3 -m scripts.cli.workflow end <project>` |

Agent ID formats accepted: `A01`, `A1`, `01`, `1`

### Exchange Log Entries

| Command | Syntax (from project dir) |
|---------|---------------------------|
| Feedback | `./workflow feedback --target <id> --severity <level> --summary <text>` |
| Iteration | `./workflow iteration --trigger <text> --agents <csv> [--version <bump>]` |

### Context Log Entries

| Command | Syntax (from project dir) |
|---------|---------------------------|
| Session | `./workflow session --agent <id> --role <name> [--summary <text>]` |
| Decision | `./workflow decision --title <text> --rationale <text> [--agent <id>]` |
| Assumption | `./workflow assumption --text <text> [--rationale <text>] [--reversal <cond>]` |
| Blocker | `./workflow blocker --title <text> --description <text> [--blocked <csv>]` |

### Query Commands

| Command | Syntax (from project dir) |
|---------|---------------------------|
| Check Handoff | `./workflow check-handoff <id>` |
| List Pending | `./workflow list-pending [--agent <id>]` |
| List Blockers | `./workflow list-blockers [--agent <id>]` |

---

## Directory Structure

```
scripts/
├── __init__.py              # Package root (v4.0.0)
├── cli/                     # CLI entry points
│   ├── workflow.py          # Python CLI implementation
│   └── workflow.sh          # Legacy shell wrapper
├── core/                    # Core shared modules (NEW)
│   ├── paths.py             # Centralized path constants
│   ├── project.py           # Project metadata operations
│   └── io.py                # File I/O utilities
├── generators/              # Content generators (NEW)
│   ├── docs.py              # CLI_REFERENCE, AGENT_PIPELINE, etc.
│   ├── index.py             # project_index.md generation
│   └── session.py           # active_session.md generation
├── session/                 # Session management
│   ├── session_frontmatter.py  # Frontmatter parsing
│   ├── init_project.py      # Project initialization
│   ├── refresh_project.py   # Project refresh (regenerate files)
│   ├── activate_agent.py    # Agent session activation
│   ├── end_session.py       # Session termination
│   ├── stage_manager.py     # Workflow stage transitions
│   ├── gate_checker.py      # Pre-activation gate checks
│   ├── invoke_agent.py      # On-demand agent invocation
│   └── sync_planning.py     # Planning→Implementation sync
├── ledger/                  # Log and handoff tracking
│   ├── id_generator.py      # Auto-generate entry IDs
│   ├── section_ops.py       # Marker-based section operations
│   ├── entry_builders.py    # Build formatted entries
│   ├── entry_writer.py      # High-level write API
│   ├── entry_reader.py      # Query and filter entries
│   └── log_write.py         # Log writing utilities
├── validation/              # Validators
│   ├── validate_session.py  # Session state validation
│   ├── validate_ledger.py   # Ledger YAML validation
│   └── validate_agents.py   # Agent manifest validation
├── generation/              # Agent file generation
│   └── generate_agents.py   # Generate agent prompts from workflow
├── utils/                   # Shared utilities
│   └── template_loader.py   # Template loading with workflow overrides
├── workflow/                # Workflow package utilities
│   ├── __init__.py          # WorkflowPackage class
│   └── resolver.py          # High-level workflow resolution
└── _deprecated/             # Archived legacy scripts
```

---

## Auto-Generated Entry IDs

Entry IDs are sequential based on existing entries in YAML sidecars:

| Type | Format | Example |
|------|--------|---------|
| Handoffs | `HO-###` | `HO-001`, `HO-002` |
| Feedback | `FB-###` | `FB-001`, `FB-002` |
| Iterations | `ITER-###` | `ITER-001`, `ITER-002` |
| Sessions | `SESS-###` | `SESS-001`, `SESS-002` |
| Decisions | `DEC-###` | `DEC-001`, `DEC-002` |
| Assumptions | `ASSUMP-###` | `ASSUMP-001`, `ASSUMP-002` |
| Blockers | `BLK-###` | `BLK-001`, `BLK-002` |

---

## YAML Sidecars

All log files have companion `.yaml` files for machine-readable queries:

```
agent_log/
├── exchange_log.md       # Human-readable markdown
├── exchange_log.yaml     # Structured YAML for scripts
├── context_log.md
└── context_log.yaml
```

---

## Template System

Templates use Jinja2-style `{{placeholder}}` syntax with workflow-specific overrides:

### Template Hierarchy

1. **Workflow-specific first:** `manifests/workflows/<type>/templates/<path>`
2. **Global fallback:** `templates/<path>`

### Usage

```python
from agentic_workflow.utils.jinja_loader import (
    render_agent, render_session, build_agent_context
)

# Render an agent file
agent_content = render_agent('planning', 'A-01', 'my_project')

# Render a session file  
session_content = render_session('planning', 'A-01', 'my_project')

# Build context for custom rendering
context = build_agent_context('planning', 'A-01', 'my_project')
```

---

## Python API

### Core Modules

```python
from agentic_workflow.core.paths import get_projects_dir, get_agent_files_dir
from agentic_workflow.core.config_service import ConfigurationService

# Get configuration
config = ConfigurationService().load_config()
projects_dir = get_projects_dir()
agent_files_dir = get_agent_files_dir()
```


### Workflow Resolution

```python
from agentic_workflow.workflow.loader import load_workflow, WorkflowPackage

# Load workflow by name
wf = load_workflow("planning")
print(wf.name, wf.version)  # "Planning", "1.0.0"
print(wf.agent_prefix)      # "A" for planning, "I" for implementation
```

### Entry Writing

```python
from agentic_workflow.ledger.entry_writer import write_handoff, write_decision

# Write handoff (returns entry_id, path)
entry_id, path = write_handoff("my_project", "A01", "A02", artifacts=["spec.md"])

# Write decision
entry_id, path = write_decision("my_project", "A01", "Use PostgreSQL", "ACID compliance")
```

### Entry Querying

```python
from agentic_workflow.ledger.entry_reader import get_pending_handoffs, get_project_summary

pending = get_pending_handoffs("my_project", to_agent="A02")
summary = get_project_summary("my_project")
```

---

## Validation

Run validators from repo root:

```bash
# Session state validation
python3 -m agentic_workflow.validation.validate_session projects/<project>

# Ledger YAML structure
python3 -m agentic_workflow.validation.validate_ledger projects/<project>

# Agent manifest consistency
python3 -m agentic_workflow.validation.validate_agents
```

---

## Example Workflow

```bash
# 1. Initialize project with planning workflow
python3 -m scripts.cli.workflow init my_project --workflow planning --description "My project"

# 2. Work from project directory
cd projects/my_project

# 3. Check status
./workflow status

# 4. Activate first agent
./workflow activate A01

# 5. Log decisions and assumptions
./workflow decision --title "Microservices" --rationale "Scalability needs"
./workflow assumption --text "MVP is English-only" --reversal "i18n requirement"

# 6. Handoff to next agent
./workflow handoff --from A01 --to A02 --artifacts "requirements.md,constraints.md"

# 7. Activate next agent
./workflow activate A02

# ... continue through pipeline ...

# 8. End session
./workflow end
```

---

## Exit Codes

- `0` — Success
- `1` — Error (validation, file not found, etc.)

## Dependencies

```bash
pip install pyyaml jinja2
```

---

## References

- **Workflow Packages:** `manifests/workflows/`
- **Template System:** `templates/README.md`
- **Project Structure:** `projects/README.md`
