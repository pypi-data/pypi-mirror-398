"""Context resolver for building template contexts from workflow data."""

from typing import Any, Dict, List, Optional


class ContextResolver:
    """Domain layer: Context building for workflow templates.

    Responsibilities:
    - Loading WorkflowPackage objects
    - Extracting agent/session data
    - Resolving artifact relationships
    - Building template contexts

    No knowledge of file systems or Jinja2.
    """

    def get_agent_context(self, workflow: str, agent_id: str, project_name: str = "project") -> Dict[str, Any]:
        """Build complete context for an agent template.

        Args:
            workflow: Workflow name
            agent_id: Agent identifier
            project_name: Project name for context

        Returns:
            Complete context dictionary for template rendering

        Raises:
            ValueError: If agent not found or data malformed
        """
        from agentic_workflow.generation.canonical_loader import load_workflow, WorkflowError

        # Load workflow package (structured object)
        try:
            wf = load_workflow(workflow)
        except WorkflowError as e:
            raise ValueError(f"Failed to load workflow '{workflow}': {e}") from e

        # Find agent data
        agent = None
        for a in wf.agents:
            if str(a.get('id', '')).upper() == str(agent_id).upper():
                agent = a
                break

        if not agent:
            raise ValueError(f"Agent {agent_id} not found in workflow '{workflow}'")

        # Use the canonical agent ID from the data
        canonical_agent_id = agent.get('id', agent_id)

        # Find agent instructions
        agent_instr = {}
        for instr in wf.instructions.get('instructions', []):
            if str(instr.get('id', '')).upper() == str(canonical_agent_id).upper():
                agent_instr = instr
                break

        # Build artifact lookup
        artifact_lookup = {a['filename']: a for a in wf.artifacts}

        # Resolve produces/consumes
        def resolve_artifacts(artifact_refs: Dict[str, List]) -> Dict[str, List[Dict]]:
            """Resolve artifact filenames to full artifact data."""
            result = {}
            for category, items in artifact_refs.items():
                resolved = []
                for item in items:
                    if isinstance(item, str):
                        fn = item
                    elif isinstance(item, dict):
                        fn = item.get('file') or item.get('filename', '')
                    else:
                        continue

                    artifact = artifact_lookup.get(fn, {'filename': fn, 'description': ''})
                    resolved.append(artifact)
                result[category] = resolved
            return result

        produces = resolve_artifacts(agent.get('produces', {}))
        consumes = resolve_artifacts(agent.get('consumes', {}))

        # Find stage and checkpoint
        stage = None
        for s in wf.metadata.get('stages', []):
            agents_list = [str(x).upper() for x in s.get('agents', [])]
            if str(canonical_agent_id).upper() in agents_list:
                stage = s
                break

        checkpoint = None
        for cp in wf.metadata.get('checkpoints', []):
            if str(cp.get('after_agent', '')).upper() == str(canonical_agent_id).upper():
                checkpoint = cp
                break

        # Build context with FIXED agent_type field
        context = {
            # Project info
            'project_name': project_name,
            'workflow_name': workflow,
            'workflow_display_name': wf.display_name,

            # Agent info
            'agent_id': canonical_agent_id,
            'agent_role': agent.get('role', ''),
            'agent_type': agent.get('agent_type', 'core'),  # FIXED: was 'type'
            'agent_slug': agent.get('slug', ''),

            # Instructions
            'purpose': agent_instr.get('purpose', ''),
            'responsibilities': agent_instr.get('responsibilities', []),
            'workflow': agent_instr.get('workflow', {}),
            'boundaries': agent_instr.get('boundaries', {}),
            'handoff': agent_instr.get('handoff', {}),
            'domain_rules': agent_instr.get('domain_rules', []),

            # Artifacts
            'produces': produces,
            'consumes': consumes,

            # Workflow context
            'stage': stage,
            'checkpoint': checkpoint,

            # Governance
            'governance': {
                'base_rules': wf.metadata.get('governance', {}).get('base_rules', []),
                'workflow_rules': wf.metadata.get('globals', [])
            },
            'enforcement': wf.metadata.get('config', {}).get('enforcement', {}),
            'logging_policy': wf.metadata.get('logging_policy', {}),

            # Computed fields
            'next_agent_id': (
                agent_instr.get('handoff', {}).get('next', [{}])[0].get('id')
                if agent_instr.get('handoff', {}).get('next')
                else None
            ),
            'required_artifacts': agent_instr.get('handoff', {}).get('required_artifacts', []),
        }

        return context

    def get_session_context(self, workflow: str, agent_id: str, project_name: str = "project",
                           timestamp: str = "", extra_subs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build context for a session template.

        Args:
            workflow: Workflow name
            agent_id: Agent identifier
            project_name: Project name
            timestamp: Session start timestamp
            extra_subs: Additional context variables

        Returns:
            Context dictionary for session template rendering
        """
        context = self.get_agent_context(workflow, agent_id, project_name)

        # Add session-specific fields
        context['timestamp'] = timestamp or ""
        context['context_file'] = f"agent_context/{workflow}_context_index.md"

        # Add live runtime data from ledger
        from agentic_workflow.ledger.entry_reader import get_handoffs, get_decisions
        
        # Get latest handoff
        handoffs = get_handoffs(project_name, limit=1)
        if handoffs:
            handoff = handoffs[0]
            context['handoff_note'] = handoff.get('notes', '')
            context['previous_agent'] = handoff.get('from_agent', '')
        else:
            context['handoff_note'] = ''
            context['previous_agent'] = ''
        
        # Get recent decisions (limit 5)
        decisions = get_decisions(project_name, limit=5)
        context['recent_decisions'] = decisions

        # Merge extra substitutions
        if extra_subs:
            context.update(extra_subs)

        return context

__all__ = ["ContextResolver"]