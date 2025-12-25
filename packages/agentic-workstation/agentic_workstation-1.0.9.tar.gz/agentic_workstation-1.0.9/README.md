# Agentic Workflow OS

> **Structured Architectural Scaffolding for AI Development**

[![Version](https://img.shields.io/badge/version-1.0.9-blue.svg)](https://github.com/sujith-eag/agentic_workflow)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Agentic Workflow OS** is a development platform that orchestrates Multi-Agent Systems to plan, architect, and implement complex software projects. Unlike "Chat with Code" tools that rely on messy, unstructured conversation history, this system enforces a **Context-First** philosophy. It treats Agent Context as a file-system state machine, ensuring that your AI Engineer knows exactly what your AI Architect decided.

---

## ⚡ Why Use This?

Most AI coding tools suffer from **Context Drift**. After 20 messages, the AI forgets the architectural constraints you set in message #1.

AI for projects and work is like a rocket: it gives a quick boost of velocity if you have direction, but soon everyone realizes it's only a first-stage booster that stops midway once context is off. The velocity drops, and to carry forward and build production-grade applications needs a 2nd and 3rd stage booster with precision guidance to reach and stay in orbit. **This project is that 2nd and 3rd stage.**

**Agentic Workflow OS solves this by:**
1.  **Strict Role Separation:** Agents have clearly defined roles with explicit boundaries - architects handle specifications, engineers handle implementation, with enforced separation to prevent scope creep.
2.  **Artifact-Driven Handoffs:** Agents cannot proceed until they receive specific, validated artifacts from predecessors, ensuring dependencies are met before progression.
3.  **Programmatic Agent Interaction:** Agents operate in environments with terminal access, using CLI tools to search project state, log decisions, record handoffs, and progress through workflow stages - enabling structured, auditable AI collaboration without conversational drift.

The system operates on a **Stateless Core / Stateful Edge** model.

---

## 🚀 Quick Start

### Environment Setup
Create and activate a Python virtual environment:
```bash
# Create virtual environment
python3 -m venv myproject-env

# Activate the environment
source myproject-env/bin/activate  

# On Windows: 
source myproject-env\Scripts\activate
```

### Installation

**Option A: Pip (Recommended)**
```bash
pip install agentic-workstation

# First run will launch an interactive setup wizard
agentic --help
```

> **First-Time Setup**: On first run, Agentic Workflow OS will launch an interactive setup wizard to configure your workspace and preferences. This creates `~/.config/agentic/config.yaml` with your settings.

**Option B: From Source (Development)**
```bash
git clone https://github.com/sujith-eag/agentic_workflow.git
cd agentic_workflow
pip install -e .
```

### Uninstallation

**Option A: Pip**
```bash
pip uninstall agentic-workstation
```

**Option B: Docker**
```bash
# Remove the Docker image
docker rmi agentic-workstation

# Remove any running containers (if any)
docker rm $(docker ps -aq --filter ancestor=agentic-workstation)
```

## CLI & TUI Usage

For detailed CLI documentation, see [CLI_REFERENCE.md](CLI_REFERENCE.md). For interactive usage, use the Text User Interface (TUI) with `agentic`.

### Available Commands

The CLI uses a **context-aware design** - commands available depend on whether you're in a project directory or not.

#### Global Commands (from repository root)
- `agentic init <name> --workflow <type> --description "desc"` - Initialize new project with workflow
- `agentic list` - List all projects or show details for one
- `agentic delete <name>` - Permanently delete a project
- `agentic workflows` - List available workflow definitions
- `agentic config` - View or edit global configuration
- `agentic` - Launch TUI in global mode

#### Project Commands (from within project directory)
- `agentic status` - Show project status and workflow state
- `agentic activate <agent_id>` - Activate specific agent session
- `agentic handoff --to <agent_id> --artifacts "files"` - Record agent handoff with artifacts
- `agentic decision --title "Title" --rationale "Reason"` - Record project decision
- `agentic end` - End current workflow session
- `agentic feedback --target <agent_id> --severity <level> --summary "Summary"` - Record feedback for an agent or artifact
- `agentic blocker --title "Title" --description "Desc" --blocked-agents "ids"` - Record a blocker that prevents progress
- `agentic iteration --trigger "Trigger" --impacted-agents "ids" --description "Desc"` - Record an iteration in the development process
- `agentic assumption --assumption "Assumption" --rationale "Rationale"` - Record an assumption that may affect the project
- `agentic list-pending` - List pending handoffs for the current project
- `agentic list-blockers` - List active blockers for the current project

---

## 🏗️ Creating & Running a Project

### 1. Initialize a Project
Navigate to your empty folder and initialize a project.

```bash
# From repository root (global context)
agentic init MySaaS --workflow planning --description "My SaaS application project"
```

*Available workflows: `planning`, `implementation`, `research`, `workflow-creation`*

### 2. Agent Workflow Orchestration

Agents operate in environments with terminal access, using CLI commands to orchestrate structured workflows:

1.  **Navigate to Project:** `cd projects/MySaaS`

2.  **Session Activation:** User or Agents run `agentic activate A-01` to start their session and receive context.

3.  **Context Processing:** Agents access the generated `active_session.md` file containing their role, instructions, and project state.

4.  **Artifact Generation:** Agents produce required deliverables and save them to specified artifact paths.

5.  **Handoff Execution:** Agents execute handoff commands to progress the workflow:
    ```bash
    agentic handoff --to A-02 --artifacts "artifacts/project_brief.md,artifacts/requirements.md"
    ```
    *The system validates artifact existence and workflow rules before allowing progression. The from agent is automatically inferred from the active session.*

6.  **State Management:** Agents can log decisions, record blockers, and query project status using CLI commands throughout the process.

### 3. Review Status

View the decision tree and current state.

```bash
agentic status
```

---

## 📦 Workflows

The system supports pluggable **Workflow Manifests** with four main workflow types.

### 1. Planning (15 agents: A-00 to A-14)
*   **Goal:** Turn a 1-sentence idea into a full Tech Spec.
*   **Key Agents:**
    *   `A-00 Orchestrator & Project Controller`
    *   `A-01 Project Guide & Idea Incubation`
    *   `A-02 Planning & Requirements Analyst`
    *   `A-03 Architecture & Technical Design Analyst`
    *   `A-04 Security & Compliance Scrutineer`
    *   `A-05 Infrastructure & DevOps Planning Architect`
    *   `A-06 Data Architecture & Storage Planning Specialist`
    *   `A-07 API & Integration Planning Specialist`
    *   `A-08 UX & Interaction Planning Specialist`
    *   `A-09 Developer Workflow & Engineering Standards Planner`

### 2. Implementation (10 agents: I-00 to I-05 + specialists)
*   **Goal:** Turn specs into production code.
*   **Key Agents:**
    *   `I-00 Implementation Orchestrator`
    *   `I-01 Scaffold & DevOps Architect`
    *   `I-02 Backend & Data Engineer`
    *   `I-03 Frontend & UX Engineer`
    *   `I-04 Quality & Validation Specialist`
    *   `I-05 Release & Integration Manager`
    *   `I-DOC Documentation Sprint Agent`
    *   `I-DS Data Store Implementation Specialist`
    *   `I-PERF Performance Optimization Agent`
    *   `I-SEC Security Hardening Auditor`

### 3. Research (12 agents)
*   **Goal:** Conduct thorough research, analysis, and reporting.
*   **Use Cases:** Literature review, data analysis, academic research, market research.

### 4. Workflow-Creation (9 agents)
*   **Goal:** Create and customize new workflow packages.
*   **Use Cases:** Meta-workflow development, process automation.

### Custom Workflows
You can create your own workflows by placing a manifest in:
- Project: `./.agentic/workflows/my-custom-flow/workflow.json`
- User global: `~/.config/agentic/workflows/my-custom-flow/workflow.json`
- System: Bundled in package (not recommended for custom)

Workflow manifests include `workflow.json`, `agents.json`, `artifacts.json`, etc.

---

## 🛠️ CLI Commands

### Global Commands (from repository root)
```bash
# List available workflows
agentic workflows

# Initialize new project
agentic init MyProject --workflow planning --description "My project description"

# Launch TUI (Terminal User Interface)
agentic

# Show CLI help
agentic --help
```

### Project Commands (from within project directory)
```bash
# Navigate to project
cd projects/MyProject

# Show current project status
agentic status

# Activate an agent session
agentic activate A-01

# Record handoff between agents (from agent inferred from active session)
agentic handoff --to A-02 --artifacts "requirements.md,architecture.md"

# Record project decision
agentic decision --title "Technology Stack Selection" --rationale "React + Node.js chosen for full-stack consistency"

# End workflow session
agentic end
```

## ⚙️ Configuration & Setup

### Automatic Setup
On first run, Agentic Workflow OS automatically launches an interactive setup wizard that configures:
- **Default workspace** (where projects are stored)
- **Editor command** (for opening files)
- **UI preferences** and logging levels

### Configuration Files

**Global Config** (`~/.config/agentic/config.yaml`):
```yaml
default_workspace: "~/AgenticProjects"
editor_command: "code"
tui_enabled: true
check_updates: true
log_level: "INFO"
```

**Project Config** (`.agentic/config.yaml` in each project):
```yaml
workflow: planning
strict_mode: true
excluded_paths:
  - "node_modules"
  - ".git"
custom_overrides:
  governance:
    require_reviews: true
```

### Manual Configuration
If you prefer to set up configuration manually or modify existing settings:

1. **Create global config directory:**
   ```bash
   mkdir -p ~/.config/agentic
   ```

2. **Create config file:**
   ```bash
   cat > ~/.config/agentic/config.yaml << 'EOF'
   default_workspace: "~/AgenticProjects"
   editor_command: "code"
   tui_enabled: true
   check_updates: true
   log_level: "INFO"
   EOF
   ```

3. **Create workspace directory:**
   ```bash
   mkdir -p ~/AgenticProjects
   ```

### Re-running Setup
To re-run the setup wizard or modify configuration:
```bash
# Remove config to trigger setup again
rm ~/.config/agentic/config.yaml
agentic
```

---

## 🛠️ Development

This project is built with Python 3.10+.

*   **Core:** `src/agentic_workflow`
*   **Manifests:** `src/agentic_workflow/manifests` (Canonical Definitions)
*   **Templates:** `src/agentic_workflow/templates` (Jinja2 templates)
*   **Build:** `pyproject.toml` (Hatchling)
*   **Tests:** Not included in deployment

**License:** MIT
