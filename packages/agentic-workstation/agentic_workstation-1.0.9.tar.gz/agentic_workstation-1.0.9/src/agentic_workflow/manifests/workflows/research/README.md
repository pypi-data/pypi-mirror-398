# Research Workflow

An evidence-based academic research pipeline from ideation to publication.

The Research Workflow guides users through the complete research lifecycle: formulating questions, surveying literature, designing methodology, collecting and analyzing data, drafting manuscripts, and preparing final submissions. Each agent enforces academic rigor with citation requirements and quality gates at critical transitions.

## Quick Start

```bash
# Initialize a new research project
python3 -m scripts.cli.workflow init my_research --workflow research --description "My research project"

# Start working
cd projects/my_research
./workflow activate R00
```

## Agents

### Core Pipeline (8 agents)

| ID | Name | Purpose |
|----|------|---------|
| R00 | Research Orchestrator | Project coordination and session management |
| R01 | Research Scoping & Discovery | Defines questions, maps literature landscape |
| R02 | Source Processing & Synthesis | Acquires sources, performs critical synthesis |
| R03 | Methodology & Execution | Designs methodology, manages data collection |
| R04 | Analysis & Interpretation | Analyzes data, interprets findings |
| R05 | Writing & Narrative | Constructs argument, drafts manuscript |
| R06 | References & Quality | Manages citations, ensures quality standards |
| R07 | Finalization | Polishes manuscript, prepares submission |

### On-Demand Specialists (4 agents)

| ID | Specialty | Called By |
|----|-----------|-----------|
| R-TEX | LaTeX typesetting and compilation | R05, R07 |
| R-VIZ | Charts, diagrams, visualizations | R04, R05, R07 |
| R-EDIT | Language editing, compliance checking | R05, R06, R07 |
| R-STAT | Advanced statistics, citation verification | R04, R06 |

## Stages

| Stage | Agents | Purpose |
|-------|--------|---------|
| IDEATION | R00, R01 | Define research questions and scope |
| DISCOVERY | R02 | Acquire and synthesize sources |
| METHODOLOGY | R03 | Design methodology, collect data |
| EXECUTION | R04 | Analyze data, interpret findings |
| WRITING | R05, R06 | Draft manuscript, manage citations |
| FINALIZATION | R07 | Polish and prepare for submission |

## Quality Gates

| Checkpoint | After | Gate Type | Criteria |
|------------|-------|-----------|----------|
| literature_review | R02 | Human | Literature synthesis complete, gaps identified |
| methodology_approval | R03 | Human | Methodology approved before data collection |
| submission_ready | R07 | Human | Manuscript ready for submission |

## Key Artifacts

### Planning Phase (R01)
- `research_proposal.md` — Research questions, scope, venues
- `hypothesis_register.md` — Testable hypotheses
- `literature_landscape.md` — Research themes, key authors
- `research_gap_analysis.md` — Gaps and opportunities

### Discovery Phase (R02)
- `source_library.md` — Organized source catalog
- `synthesis_matrix.md` — Cross-source comparison
- `evidence_inventory.md` — Claims with supporting evidence

### Methodology Phase (R03)
- `methodology_design.md` — Approach and justification
- `experiment_protocol.md` — Step-by-step procedures
- `data_dictionary.md` — Variable definitions

### Analysis Phase (R04)
- `analysis_results.md` — Statistical output
- `hypothesis_outcomes.md` — Which hypotheses supported
- `findings_summary.md` — Key findings

### Writing Phase (R05-R06)
- `argument_structure.md` — Logical flow
- `contribution_claims.md` — Research contributions
- `manuscript_draft.md` — Complete first draft
- `bibliography.bib` — BibTeX references
- `qa_report.md` — Quality assessment

### Finalization Phase (R07)
- `manuscript_final.md` — Publication-ready manuscript
- `cover_letter.md` — Submission cover letter
- `submission_checklist.md` — Pre-submission verification

## Output Structure

```
project/
├── artifacts/           # Agent workspaces
│   └── ARxx_agent_Rxx/
├── output/              # Research outputs
│   ├── manuscript/      # Final manuscript versions
│   │   ├── sections/    # Individual sections
│   │   ├── figures/     # Publication figures
│   │   └── tables/      # Publication tables
│   ├── data/
│   │   ├── raw/         # Raw collected data
│   │   └── processed/   # Analysis-ready data
│   ├── sources/         # Source papers
│   │   └── summaries/   # Per-source summaries
│   ├── analysis/        # Analysis outputs
│   │   └── scripts/     # R/Python scripts
│   ├── figures/         # Working figures
│   └── submission/      # Final submission package
└── package/             # Deliverables
```

## CLI Commands

```bash
./workflow status                # Show current state
./workflow activate R01          # Switch to agent
./workflow handoff --from R01 --to R02 --artifacts "research_proposal.md"
./workflow decision --title "Target venue" --rationale "IEEE format"
./workflow end                   # Complete session
```

## Evidence Standards

All claims in research artifacts must be:
- **Cited** — linked to a source in the bibliography
- **Traceable** — claim → evidence → source chain maintained
- **Verifiable** — sources can be checked

Citation format: Use BibTeX keys `[@AuthorYear]` or `\cite{AuthorYear}` during drafting.

## Customization

To customize this workflow:
1. Edit `manifests/workflows/research/workflow.yaml`
2. Regenerate agents: `python3 -m scripts.generation.generate_agents --workflow research`

### Common Customizations

- **Change stages:** Edit `stages` in workflow.yaml
- **Add agents:** Add to agents.yaml, instructions.yaml
- **Modify checkpoints:** Edit `checkpoints` in workflow.yaml
- **Update templates:** Edit files in `templates/prompts/`
