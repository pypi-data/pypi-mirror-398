# Templates Directory

## Overview
The templates directory contains Jinja2 templates used to generate project structures, agent prompts, documentation, and other artifacts dynamically.

## Purpose
Enables code generation and content templating to create consistent, customized outputs based on workflow requirements and project parameters.

## Key Subdirectories
- `_base/`: Base templates for common structures
- `_partials/`: Reusable template components
- `artifacts/`: Templates for agent deliverables
- `docs/`: Documentation templates
- `logs/`: Log file templates
- `prompts/`: Agent prompt templates

## Functions
- **Project Generation**: Create initial project directory structures
- **Agent Prompts**: Generate role-specific instructions and context
- **Documentation**: Produce consistent docs and guides
- **Artifact Templates**: Provide starting points for deliverables

## Dependencies
- **Depends on**: Jinja2 templating engine
- **Used by**: Project generation service, workflow initialization
- **Inputs**: Template variables from manifests and user input

## Inputs/Outputs
- **Inputs**: Template variables (project name, workflow type, agent details)
- **Outputs**: Rendered files (markdown, JSON, code, etc.)

## Integration
Templates are rendered during project creation and agent activation. They ensure consistency across projects while allowing customization through variable substitution.