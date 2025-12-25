# Manifests Directory

## Overview
The manifests directory contains canonical definitions for workflows, agents, artifacts, and schemas that define the structure and behavior of agent orchestration processes.

## Purpose
Provides the "blueprints" for different types of projects and workflows. Enables pluggable workflow systems where users can define custom agent chains and artifact requirements.

## Key Subdirectories
- `_canonical/`: Standard workflow definitions (planning, implementation, etc.)
- `_canonical_schemas/`: JSON schemas for validation
- `_schemas/`: Schema definitions for manifests
- `workflows/`: Workflow-specific configurations

## Functions
- **Workflow Definition**: Specify agent sequences and transitions
- **Agent Specification**: Define roles, responsibilities, and prompts
- **Artifact Schema**: Describe required deliverables and validation rules
- **Validation Rules**: Ensure workflow compliance and artifact quality

## Dependencies
- **Depends on**: Core validation module for schema checking
- **Used by**: Workflow loader, session manager, CLI commands
- **External**: JSON Schema library for validation

## Inputs/Outputs
- **Inputs**: Workflow design requirements, agent specifications
- **Outputs**: Loaded workflow objects, agent configurations, validation schemas

## Integration
Manifests are loaded at workflow initialization and cached for performance. They define the "contract" that projects must follow, ensuring consistent execution across different project types.