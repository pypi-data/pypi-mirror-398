#!/usr/bin/env python3
"""Generate denormalized YAML files from canonical JSON.

Main orchestrator script for Phase 2 of workflow generation pipeline.
Loads canonical JSON, denormalizes data, writes YAML with comments.

Usage:
    # Generate for specific workflow
    python3 -m agentic_workflow.generation.generate_workflow_yaml --workflow planning
    
    # Generate for all workflows
    python3 -m agentic_workflow.generation.generate_workflow_yaml --all
    
    # Dry run (show what would be generated)
    python3 -m agentic_workflow.generation.generate_workflow_yaml --workflow planning --dry-run
    
    # Generate with verbose output
    python3 -m agentic_workflow.generation.generate_workflow_yaml --workflow planning --verbose
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agentic_workflow.generation.canonical_loader import (
    list_canonical_workflows,
    load_canonical_workflow,
    get_agents_list,
    get_artifacts_list,
    get_instructions_list,
    get_workflow_metadata,
    CanonicalLoadError,
)
from agentic_workflow.generation.denormalizer import (
    Denormalizer,
    denormalize_canonical,
)
from agentic_workflow.generation.yaml_writer import write_all_yaml

from agentic_workflow.cli.utils import display_info, display_error, display_success

# Output directory
WORKFLOWS_DIR = Path(__file__).resolve().parents[2] / "manifests" / "workflows"
ROOT = Path(__file__).resolve().parents[2]

__all__ = ["GenerationReport", "generate_workflow"]


class GenerationReport:
    """Tracks generation progress and creates summary report."""
    
    def __init__(self):
        """Initialize the GenerationReport with empty tracking lists."""
        self.start_time = datetime.now()
        self.workflows_processed: List[str] = []
        self.files_created: List[Path] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.assumptions: List[str] = []
    
    def add_workflow(self, workflow_id: str):
        """Record a processed workflow."""
        self.workflows_processed.append(workflow_id)
    
    def add_file(self, path: Path):
        """Record a created file."""
        self.files_created.append(path)
    
    def add_error(self, msg: str):
        """Record an error."""
        self.errors.append(msg)
    
    def add_warning(self, msg: str):
        """Record a warning."""
        self.warnings.append(msg)
    
    def add_assumption(self, msg: str):
        """Record an assumption made during generation."""
        self.assumptions.append(msg)
    
    def summary(self) -> str:
        """Generate summary report."""
        elapsed = datetime.now() - self.start_time
        
        lines = [
            "",
            "=" * 76,
            "YAML GENERATION REPORT",
            "=" * 76,
            f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {elapsed.total_seconds():.2f}s",
            "",
            "--- CHANGES MADE ---",
            f"Workflows processed: {len(self.workflows_processed)}",
        ]
        
        for wf in self.workflows_processed:
            lines.append(f"  - {wf}")
        
        lines.append(f"\nFiles created: {len(self.files_created)}")
        for f in self.files_created:
            lines.append(f"  - {f.relative_to(ROOT)}")
        
        if self.assumptions:
            lines.append("\n--- ASSUMPTIONS ---")
            for a in self.assumptions:
                lines.append(f"  • {a}")
        
        if self.warnings:
            lines.append("\n--- WARNINGS ---")
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        
        if self.errors:
            lines.append("\n--- ERRORS ---")
            for e in self.errors:
                lines.append(f"  ✗ {e}")
        
        lines.append("\n--- NEXT STEPS ---")
        lines.append("  1. Review generated YAML files in manifests/workflows/")
        lines.append("  2. Validate YAML structure with: python3 -m scripts.validation.validate_yaml")
        lines.append("  3. Test agent generation with: python3 -m scripts.generation.generate_agents")
        
        lines.append("")
        lines.append("=" * 76)
        
        return "\n".join(lines)


def generate_workflow(
    workflow_id: str,
    report: GenerationReport,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Generate YAML files for a single workflow.
    
    Args:
        workflow_id: Workflow identifier (e.g., 'planning').
        report: Report object to track progress.
        dry_run: If True, don't write files.
        verbose: If True, print detailed progress.
        
    Returns:
        True if successful, False otherwise.
    """
    display_info(f"Processing: {workflow_id}")

    # Load canonical JSON
    display_info("Loading canonical JSON files...")
    try:
        canonical = load_canonical_workflow(workflow_id)
        if verbose:
            agents = get_agents_list(canonical)
            artifacts = get_artifacts_list(canonical)
            instructions = get_instructions_list(canonical)
            display_info(f"  - agents.json: {len(agents)} agents")
            display_info(f"  - artifacts.json: {len(artifacts)} artifacts")
            display_info("  - workflow.json: loaded")
            display_info(f"  - instructions.json: {len(instructions)} entries")
    except CanonicalLoadError as e:
        report.add_error(f"{workflow_id}: Failed to load JSON: {e}")
        display_error(f"Failed to load JSON: {e}")
        return False
    except Exception as e:
        report.add_error(f"{workflow_id}: Unexpected error: {e}")
        display_error(f"Unexpected error: {e}")
        return False
    
    # Denormalize data
    display_info("Denormalizing data...")
    try:
        denormalized = denormalize_canonical(canonical)
        if verbose:
            display_info(f"  - Summary fields: {len(denormalized['workflow'])}")
            display_info(f"  - Enriched agents: {len(denormalized['agents'])}")
            display_info(f"  - Enriched artifacts: {len(denormalized['artifacts'])}")
    except Exception as e:
        report.add_error(f"{workflow_id}: Failed to denormalize: {e}")
        display_error(f"Failed to denormalize: {e}")
        return False
    
    # Prepare output directory
    output_dir = WORKFLOWS_DIR / workflow_id
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track assumptions
    report.add_assumption(f"{workflow_id}: Agent I/O merged from agents.json + artifacts.json")
    report.add_assumption(f"{workflow_id}: Instructions merged from instructions.json")
    report.add_assumption(f"{workflow_id}: artifact categories derived from category field")
    
    # Prepare data structure for YAML writer
    yaml_data = denormalized
    
    if dry_run:
        display_info(f"DRY RUN: Would write to {output_dir}")
        display_info("  - workflow.yaml")
        display_info("  - agents.yaml")
        display_info("  - artifacts.yaml")
        display_info("  - instructions.yaml")
        report.add_workflow(workflow_id)
        return True
    
    # Write YAML files
    display_info(f"Writing YAML files to {output_dir}/")
    try:
        # Get workflow display name
        workflow_meta = get_workflow_metadata(canonical)
        display_name = workflow_meta.get("display_name", workflow_id.title())
        
        files = write_all_yaml(yaml_data, output_dir, display_name)
        for f in files:
            report.add_file(f)
        for f in files:
            display_success(f"  Written: {f}")
    except Exception as e:
        report.add_error(f"{workflow_id}: Failed to write YAML: {e}")
        display_error(f"Failed to write YAML: {e}")
        return False
    
    report.add_workflow(workflow_id)
    display_success(f"Completed: {workflow_id}")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate denormalized YAML from canonical JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --workflow planning
  %(prog)s --all
  %(prog)s --workflow implementation --dry-run
  %(prog)s --all --verbose
        """,
    )
    
    parser.add_argument(
        "--workflow", "-w",
        type=str,
        help="Workflow ID to generate (e.g., 'planning', 'implementation')",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Generate for all available workflows",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be generated without writing files",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed progress information",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available workflows and exit",
    )
    
    args = parser.parse_args()
    
    # List workflows
    available = list_canonical_workflows()
    
    if args.list:
        display_info("Available workflows in manifests/_canonical/:")
        for w in available:
            display_info(f"  - {w}")
        sys.exit(0)
    
    # Validate arguments
    if not args.workflow and not args.all:
        parser.error("Must specify --workflow or --all")
    
    if args.workflow and args.all:
        parser.error("Cannot specify both --workflow and --all")
    
    if args.workflow and args.workflow not in available:
        display_error(f"Unknown workflow '{args.workflow}'")
        display_info(f"Available: {', '.join(available)}")
        sys.exit(1)
    
    # Determine which workflows to process
    workflows = available if args.all else [args.workflow]
    
    display_info("YAML GENERATION FROM CANONICAL JSON")
    display_info(f"Mode: {'DRY RUN' if args.dry_run else 'WRITE'}")
    display_info(f"Workflows: {', '.join(workflows)}")
    display_info(f"Output: {WORKFLOWS_DIR}/")
    
    # Process workflows
    report = GenerationReport()
    success = True
    
    for workflow_id in workflows:
        result = generate_workflow(
            workflow_id,
            report,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        if not result:
            success = False
    
    # Print report
    display_info(report.summary())
    
    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
