# Agentic Workflow OS CLI & TUI Reference

**Version:** 1.0.9
**Generated:** December 15, 2025
**Source:** Code Review Analysis & CLI Implementation

## Overview

The Agentic Workflow OS provides both command-line (CLI) and text user interface (TUI) access to multi-agent workflow orchestration. The CLI uses a **context-aware design** where available commands depend on whether you're in a project directory or not. The TUI provides interactive, menu-driven workflow management with guided wizards and context-aware operations.

## Global Options

All commands support these global options:

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | | Show version and exit |
| `--verbose` | `-v` | Enable verbose output |
| `--force` | `-f` | Force operations |
| `--help` | | Show help message |

## Command Groups

### Context-Aware CLI Design

The CLI automatically detects context and shows different commands:

#### Global Context Commands (from repository root)
Available when **outside** project directories for system-wide operations.

| Command | Arguments | Options | Description |
|---------|-----------|---------|-------------|
| `init` | `name` | `--workflow`, `--description` | Initialize new project with workflow |
| `list` | None | None | List all projects or show details for one |
| `delete` | `name` | None | Permanently delete a project |
| `config` | None | None | View or edit global configuration |
| `workflows` | None | None | List available workflow definitions |
| (no subcommand) | None | None | Launch TUI in global mode |

#### Project Context Commands (from within project directory)
Available when **inside** project directories for workflow operations.

| Command | Arguments | Options | Description |
|---------|-----------|---------|-------------|
| `status` | None | None | Show project status and workflow state |
| `activate` | `agent_id` | None | Activate specific agent session |
| `handoff` | None | `--to`, `--artifacts`, `--from` | Record agent handoff with artifacts (from agent inferred from active session) |
| `decision` | None | `--title`, `--rationale` | Record project decision |
| `end` | None | None | End current workflow session |
| `feedback` | None | `--target`, `--severity`, `--summary` | Record feedback for an agent or artifact |
| `blocker` | None | `--title`, `--description`, `--blocked-agents` | Record a blocker that prevents progress |
| `iteration` | None | `--trigger`, `--impacted-agents`, `--description` | Record an iteration in the development process |
| `assumption` | None | `--assumption`, `--rationale` | Record an assumption that may affect the project |
| `list-pending` | None | None | List pending handoffs for the current project |
| `list-blockers` | None | None | List active blockers for the current project |

## Usage Examples

### CLI Usage

### Global Context (Repository Root)

```bash
# Initialize a new project
agentic init my_project --workflow planning --description "My new project"

# List all projects
agentic list

# Delete a project
agentic delete my_project

# List available workflows
agentic workflows

# Show configuration
agentic config

# Launch TUI (global mode)
agentic
```

### Project Context (Inside Project Directory)

```bash
# Navigate to project
cd projects/my_project

# Show project status
agentic status

# Activate an agent
agentic activate A-01

# Record handoff between agents (from agent inferred from active session)
agentic handoff --to A-02 --artifacts "requirements.md,architecture.md"

# Record project decision
agentic decision --title "Technology Stack Selection" --rationale "React + Node.js chosen"

# Record feedback
agentic feedback --target "A-02" --severity low --summary "Good work on requirements"

# Record a blocker
agentic blocker --title "API dependency missing" --description "External API not available" --blocked-agents "I-01,I-02"

# Record an iteration
agentic iteration --trigger "API design review" --impacted-agents "A-03,I-01" --description "Updated API endpoints based on feedback"

# Record an assumption
agentic assumption --assumption "API will be available by Q1" --rationale "Vendor confirmed timeline"

# List pending handoffs
agentic list-pending

# List active blockers
agentic list-blockers

# End workflow session
agentic end
```

**Note:** `--artifacts` values are relative to the project's `artifacts/` directory (for example, `A-02_planning/requirements_spec.md`).

### TUI Usage

```bash
# Launch interactive Text User Interface (auto-detects context)
agentic  # From repository root (global mode)

# From within project directory (project mode)
cd projects/my_project
agentic

# From source/development
python3 -m agentic_workflow.cli.main
```

### Advanced Usage

```bash
# Enable verbose logging
agentic --verbose status

# Force operations (use with caution)
agentic --force init my_project --workflow planning

# Record blocker with multiple blocked agents
agentic blocker --title "Database migration required" \
  --description "Legacy data needs migration before deployment" \
  --blocked-agents "I-02,I-03,I-05"

# Record iteration with detailed description
agentic iteration --trigger "Security audit findings" \
  --impacted-agents "A-04,I-04,I-06" \
  --description "Implementing security recommendations from audit"

# List operations with verbose output
agentic --verbose list-blockers
agentic --verbose list-pending
```

## CLI vs TUI

### Command Line Interface (CLI)
- **Best for**: Scripting, automation, CI/CD pipelines
- **Features**: Structured output formats (JSON, YAML, CSV), API mode, scripting integration
- **Usage**: Direct commands with options and arguments
- **Context**: Manual context management

### Text User Interface (TUI)
- **Best for**: Interactive workflow management, learning the system, guided operations
- **Features**: Menu-driven interface, context-aware menus, guided wizards, real-time data display
- **Usage**: `agentic` (no subcommand needed - auto-detects context)
- **Context**: Automatic detection (global vs project mode)

### When to Use Each

| Use Case | Recommended Interface | Reason |
|----------|----------------------|---------|
| **Scripting/Automation** | CLI | Structured output, API mode |
| **First-time setup** | TUI (`agentic`) | Guided wizards, help text |
| **CI/CD pipelines** | CLI | Non-interactive, predictable |
| **Interactive exploration** | TUI (`agentic`) | Menus, real-time feedback |
| **Batch operations** | CLI | Command composition, loops |
| **Learning the system** | TUI (`agentic`) | Context-aware guidance |

## Error Handling

The CLI provides comprehensive error handling with user-friendly messages:

- **Validation Errors**: Clear messages for invalid inputs
- **File System Errors**: Helpful guidance for permission/path issues
- **Network Errors**: Retry logic with informative messages
- **Configuration Errors**: Suggestions for fixing config issues

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Command not found
- `3`: Validation error
- `4`: File system error

## Configuration

The CLI uses YAML configuration files. Default locations:

1. Project-specific: `projects/<project>/.agentic/config.yaml`
2. Global config: `~/.config/agentic/config.yaml`

Example configuration:

```yaml
# Global config (~/.config/agentic/config.yaml)
default_workspace: "~/AgenticProjects"
editor_command: "code"
tui_enabled: true
check_updates: true
log_level: "INFO"

# Project config (projects/my_project/.agentic/config.yaml)
workflow: planning
strict_mode: true
excluded_paths:
  - "node_modules"
  - ".git"
```

## Troubleshooting

### Common Issues

1. **Command not found**: Ensure `agentic` is in your PATH after installation
2. **Permission denied**: Check file permissions in project directory
3. **Workflow not found**: Verify workflow name with `agentic workflows`
4. **Wrong context**: Make sure you're in the right directory (repo root for global commands, project directory for workflow commands)
5. **Agent ID format**: Use correct format like `A-01`, `I-02` (not `A01`, `I02`)
6. **No active session**: Entry commands (feedback, blocker, iteration, assumption) require an active agent session - use `agentic activate <agent_id>` first
7. **Blocker not showing**: Blockers are filtered by "pending" status - ensure blockers are recorded with correct status

### Context Issues

- **"Command not available in this context"**: You're trying to use project commands from repo root, or global commands from project directory
- **Solution**: Check your current directory and use `agentic --help` to see available commands

### Entry Command Issues

- **"No active agent session found"**: You must activate an agent before recording feedback, blockers, iterations, or assumptions
- **"Validation error"**: Check required fields for each command (e.g., blocker needs title and description)
- **"Blocker not listed"**: Ensure the blocker was recorded with "pending" status and you're in the correct project directory

### Context Issues

- **"Command not available in this context"**: You're trying to use project commands from repo root, or global commands from project directory
- **Solution**: Check your current directory and use `agentic --help` to see available commands

### Getting Help

```bash
# Show general help (shows available commands based on context)
agentic --help

# Show help for specific commands
agentic init --help
agentic activate --help
agentic handoff --help
agentic feedback --help
agentic blocker --help
agentic iteration --help
agentic assumption --help
agentic list-blockers --help
```

### Context Detection

The CLI automatically detects your context:

- **Global Context**: When you're in the repository root or outside project directories
- **Project Context**: When you're inside a `projects/<project_name>/` directory

Available commands change based on context. Use `agentic --help` to see what's available in your current location.

---

*This documentation covers both CLI and TUI interfaces for the Agentic Workflow OS. Last updated: December 21, 2025*
