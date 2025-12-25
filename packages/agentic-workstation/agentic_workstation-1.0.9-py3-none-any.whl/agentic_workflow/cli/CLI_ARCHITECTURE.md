# Agentic Workflow OS: CLI Architecture Reference

**Version:** 2.0 (Release Candidate)
**Status:** Stable / Governance Enforced
**Scope:** Command Line Interface, Context Routing, and Request Handlers.

## 1. Architectural Overview

The CLI serves as the primary interface for the Agentic Workflow OS, operating as a **"Smart Binary"** that dynamically adapts its behavior based on the execution context. It implements a strict **Unidirectional Data Flow** pattern, ensuring separation between user interaction, business logic, and data persistence.

### The Layered Model

```mermaid
graph TD
    User[User Terminal] --> Main[main.py (Router)]
    Main --> Commands[Command Modules (Click)]
    Commands --> Handlers[Request Handlers (Bridge)]
    Handlers --> Governance[Governance Engine (Gates)]
    Governance --> Services[Core Services (Business Logic)]
    Services --> Ledger[Ledger I/O (Persistence)]
````

1.  **Router (`main.py`):** The entry point detector. It identifies the directory context (Global vs. Project) and modifies the `ContextAwareGroup` to expose relevant commands.
2.  **Commands (`cli/commands/`):** Pure `click` definitions responsible for argument parsing and UI rendering via `rich`. These modules contain **ZERO** business logic.
3.  **Handlers (`handlers/`):** The application bridge. They orchestrate Service calls, handle exceptions, and route data to the logic layer.
4.  **Governance (`core/governance.py`):** An interceptor layer that enforces rules (Strict/Moderate) before allowing state-changing operations.
5.  **Services:** The core engine components (`ProjectService`, `LedgerService`) managing the domain logic.

-----

## 2\. Context-Aware Routing (`main.py`)

The `agentic` binary utilizes a custom command group to filter functionality based on location.

| Context | Condition | Available Command Set |
| :--- | :--- | :--- |
| **Global Mode** | User is **NOT** inside a project directory. | System initialization, project management (`list`, `delete`), global configuration. |
| **Project Mode** | User **IS** inside a `projects/<name>` directory. | Workflow execution (`activate`, `handoff`), entry recording (`blocker`, `feedback`), and status queries. |

**Command Aliasing Strategy**
To enhance usability, internal function names are mapped to intuitive CLI verbs:

  * `list_projects` → `list`
  * `delete_project` → `delete`
  * `end_session` → `end`
  * `list_pending_handoffs` → `list-pending`
  * `list_active_blockers` → `list-blockers`

-----

## 3\. Command Modules Reference

The command interface is segmented into three logical modules within `cli/commands/`.

### A. `global_ops.py` (System & Setup)

*Context: Global Mode Only*

| Command | Arguments | Handler Mapping | Description |
| :--- | :--- | :--- | :--- |
| **`init`** | `<name> --workflow` | `SessionHandlers.handle_init` | Scaffolds a new project structure and initializes the atomic pipeline. |
| **`workflows`** | None | `GlobalHandlers.handle_list_workflows` | Lists installed workflow definitions and versions. |
| **`config`** | `--edit` | `GlobalHandlers.handle_config` | View or edit the system-wide configuration. |

### B. `project_ops.py` (Management & Query)

*Context: Shared (Global/Project)*

| Command | Arguments | Handler Mapping | Description |
| :--- | :--- | :--- | :--- |
| **`list`** | `[name]` | `ProjectHandlers.handle_list` | Lists all projects (Global) or project details. |
| **`delete`** | `<name>` | `ProjectHandlers.handle_delete` | Permanently removes a project and its artifacts. |
| **`status`** | None | `QueryHandlers.handle_status` | **Smart Status:** Aggregates active agents, blockers, and handoffs. |
| **`list-pending`** | None | `QueryHandlers.handle_list_pending` | Tables all pending handoffs waiting for action. |
| **`list-blockers`** | None | `QueryHandlers.handle_list_blockers` | Tables all active blockers impeding the workflow. |

### C. `active_session.py` (The Workflow Loop)

*Context: Project Mode Only*

| Command | Arguments | Handler Mapping | Description |
| :--- | :--- | :--- | :--- |
| **`activate`** | `<agent_id>` | `SessionHandlers.handle_activate` | **Gated:** Activates an agent session if governance rules pass. |
| **`handoff`** | `--to <agent>` | `EntryHandlers.handle_handoff` | Records a formal handoff. Auto-detects source agent. |
| **`decision`** | `--title <t>` | `EntryHandlers.handle_decision` | Logs an architectural decision record (ADR). |
| **`blocker`** | `--title <t>` | `EntryHandlers.handle_blocker` | Raises a blocking issue attached to the active session. |
| **`feedback`** | `--target <t>` | `EntryHandlers.handle_feedback` | Records structured feedback for agents or artifacts. |
| **`iteration`** | `--trigger <t>` | `EntryHandlers.handle_iteration` | Logs a workflow iteration or version bump. |
| **`assumption`** | `--text <t>` | `EntryHandlers.handle_assumption` | Records explicitly stated project assumptions. |
| **`end`** | None | `SessionHandlers.handle_end` | Archives the session, clears active state, and saves logs. |

-----

## 4\. Handler Architecture (`handlers/`)

Handlers act as the specialized bridge between the Interface (CLI/TUI) and the Core Services. They enforce the "Zero Data Loss" policy by ensuring all calls result in Ledger persistence.

### `SessionHandlers`

**Responsibility:** Lifecycle Management & Governance

  * `handle_init`: Bootstraps the project via `InitPipeline`.
  * `handle_activate`: **Crucial.** Invokes `GateChecker` to enforce strictness rules before allowing activation. Raises `CLIExecutionError` on violation.
  * `handle_end`: Triggers archival and cleanup routines.

### `EntryHandlers`

**Responsibility:** Ledger Write Operations

  * `handle_handoff`, `handle_decision`, `handle_blocker`, `handle_feedback`, `handle_iteration`, `handle_assumption`.
  * **Design Note:** All handlers in this module communicate with `LedgerService` to append immutable records to `exchange_log.md` or `context_log.md`.

### `ProjectHandlers`

**Responsibility:** Filesystem & Configuration

  * `handle_list`: Metadata retrieval.
  * `handle_delete`: Safe filesystem removal.

### `QueryHandlers`

**Responsibility:** Read-Only State Aggregation

  * `handle_status`: Fetches and formats the "Cockpit" view data.
  * `handle_check_handoff`: Verifies ledger state for specific transitions.
  * `handle_list_pending`: Filters ledger for pending handoff items.
  * `handle_list_blockers`: Filters ledger for active blocking items.

-----

## 5\. Developer Guide: Adding a New Command

To maintain architectural integrity, follow this **3-Step Pattern** when extending the CLI.

### Step 1: Create the Logic (Handler)

Implement the business logic in the appropriate `handlers/` module. Always use the Service layer.

```python
# handlers/query_handlers.py
def handle_list_new_thing(self, project):
    data = self.ledger_service.get_new_things(project)
    format_output(data, "table")
```

### Step 2: Create the Interface (Command)

Define the Click command in the appropriate `cli/commands/` module. Use `rich_click` for consistent styling.

```python
# cli/commands/project_ops.py
@click.command(cls=RichCommand, name='list-new')
@click.pass_context
def list_new(ctx):
    # Context extraction logic...
    query_handlers.handle_list_new_thing(project)
```

### Step 3: Register the Route (Main)

Update the `ContextAwareGroup` mapping in `cli/main.py` to expose the command in the correct context.

```python
# cli/main.py
if config.is_project_context:
    mapping = {
        # ... existing ...
        'list-new': project_ops.list_new,
    }
```

-----

## 6\. Troubleshooting

### "Governance Failed" Error

  * **Context:** Occurs during `activate` or `handoff`.
  * **Cause:** The `GateChecker` has identified a violation (e.g., missing artifact, no prerequisite handoff) while the project is in Strict Mode.
  * **Fix:** Resolve the missing requirement or switch to Moderate Mode in `.agentic/config.yaml`.

### "Command not found"

  * **Context:** Typing `activate` in the root directory.
  * **Cause:** Context-aware routing hides commands that are invalid for the current location.
  * **Fix:** Navigate into a valid project directory (`cd projects/my-project`).

### "No Active Session" Error

  * **Context:** Running `blocker` or `feedback`.
  * **Cause:** These commands require an active agent context to attach the data to.
  * **Fix:** Run `agentic activate <agent_id>` first.

<!-- end list -->

```
```