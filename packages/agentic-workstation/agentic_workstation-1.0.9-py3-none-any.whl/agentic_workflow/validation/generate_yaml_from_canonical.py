#!/usr/bin/env python3
"""Generate a human-editable YAML file from canonical JSON manifests.

Usage:
  ./scripts/validation/generate_yaml_from_canonical.py  [--output PATH] [--no-derived]

Behavior:
- Reads canonical JSON from `manifests/_canonical//`.
- If `instructions.json` is missing/empty or contains a human-style `agents` mapping,
  transform that mapping into the canonical `{"instructions": [ ... ]}` shape
  using canonical agent ids (matched by role/title or slug).
- Writes a human-editable YAML to `manifests/workflows//canonical_generated.yaml`.
- By default includes derived cross-references under `_derived`; pass `--no-derived`
  to disable.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from agentic_workflow.cli.utils import display_success, display_error, display_warning

try:
    import yaml
except Exception:
    display_error("PyYAML is required. Install with: pip install pyyaml")
    raise

__all__ = ["transform_human_instructions"]


def find_repo_root():
    """Find the repository root by locating the manifests directory."""
    cur = os.getcwd()
    while True:
        if os.path.isdir(os.path.join(cur, 'manifests')):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    raise FileNotFoundError('Could not locate repository root (manifests/ not found)')


def load_json(path):
    """Load JSON data from a file path."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def make_slug(text: str) -> str:
    """Convert text to a slug format suitable for identifiers."""
    s = (text or '').strip().lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = '_'.join(s.split())
    return s or 'unknown'


# Note: derived/indexed views and instruction canonicalization removed by request.
# This script now focuses on emitting the canonical agents/artifacts/workflow
# into a human-editable YAML and normalizing artifact owner slugs to canonical IDs.


def transform_human_instructions(human_instr: dict, canonical_agents: list):
    """Transform human-readable instructions into canonical format."""
    lookup = {}
    for a in canonical_agents:
        role = (a.get('role') or '').strip().lower()
        slug = (a.get('slug') or '').strip().lower()
        if role:
            lookup[role] = a
        if slug:
            lookup[slug] = a

    instructions_list = []
    agents_section = human_instr.get('agents') or {}
    for key, entry in agents_section.items():
        title = (entry.get('title') or entry.get('role') or '').strip()
        canon = None
        if title:
            canon = lookup.get(title.lower())
        if not canon and title:
            t_low = title.lower()
            for a in canonical_agents:
                arole_low = (a.get('role') or '').lower()
                if not arole_low:
                    continue
                if t_low in arole_low or arole_low in t_low:
                    canon = a
                    break

        if not canon:
            try:
                n = int(key)
                for a in canonical_agents:
                    aid = a.get('id', '')
                    if aid.endswith(f"-{n:02d}") or aid.endswith(f"-{(n+1):02d}"):
                        canon = a
                        break
            except Exception:
                pass

        if canon:
            agent_id = canon.get('id')
            agent_slug = canon.get('slug')
        else:
            agent_slug = make_slug(title)
            agent_id = (agent_slug.upper()[:1] + '-' + agent_slug.replace('_', '')[:2])

        instr_obj = {
            'id': agent_id,
            'slug': agent_slug or make_slug(title),
            'role': entry.get('title') or entry.get('role') or '',
            'purpose': entry.get('purpose') or entry.get('description') or '',
        }
        for opt in ('responsibilities', 'ownership', 'workflow', 'boundaries', 'domain_rules'):
            if opt in entry:
                instr_obj[opt] = entry[opt]

        instructions_list.append(instr_obj)

    return {'instructions': instructions_list}


def main():
    """Main entry point for YAML generation CLI."""
    p = argparse.ArgumentParser(description='Generate YAML from canonical JSON manifests')
    p.add_argument('workflow', help='Workflow name (directory under manifests/_canonical)')
    p.add_argument('--output', '-o', help='Output YAML path')
    p.add_argument('--agent-id-format', choices=['canonical', 'padded'], default='padded', help='How to render agent IDs in output: "canonical" preserves IDs as-is, "padded" removes the hyphen (A-01 -> A01)')
    p.set_defaults()
    args = p.parse_args()

    root = find_repo_root()
    canonical_dir = os.path.join(root, 'manifests', '_canonical', args.workflow)
    if not os.path.isdir(canonical_dir):
        display_error(f'Canonical dir not found: {canonical_dir}')
        sys.exit(2)

    files = {
        'agents': os.path.join(canonical_dir, 'agents.json'),
        'artifacts': os.path.join(canonical_dir, 'artifacts.json'),
        'instructions': os.path.join(canonical_dir, 'instructions.json'),
        'workflow': os.path.join(canonical_dir, 'workflow.json'),
    }

    data = {}
    for key, path in files.items():
        if os.path.isfile(path):
            try:
                data[key] = load_json(path)
            except Exception as e:
                display_error(f'Error loading {path}: {e}')
                sys.exit(3)
        else:
            data[key] = {} if key != 'agents' else {}

    # Normalize common canonical shapes: unwrap {"agents": [...]} wrappers
    for plural in ('agents', 'artifacts'):
        val = data.get(plural)
        if isinstance(val, dict) and plural in val and isinstance(val[plural], list):
            data[plural] = val[plural]

    # Do not attempt to transform or include instructions in the generated YAML.
    data.pop('instructions', None)

    # Build maps and normalize artifact owners (map slugs to canonical agent IDs)
    agents_obj = data.get('agents') or []
    artifacts_obj = data.get('artifacts') or []
    agents_map = {}
    if isinstance(agents_obj, list):
        for a in agents_obj:
            aid = a.get('id') or a.get('agent_id') or a.get('name')
            if not aid:
                continue
            agents_map[aid] = a
    elif isinstance(agents_obj, dict):
        agents_map = agents_obj

    artifacts_map = {}
    if isinstance(artifacts_obj, list):
        for art in artifacts_obj:
            key = art.get('filename') or art.get('name') or art.get('id')
            if not key:
                continue
            artifacts_map[key] = art
    elif isinstance(artifacts_obj, dict):
        artifacts_map = artifacts_obj

    slug_to_id = {}
    for aid, aobj in agents_map.items():
        slug = (aobj.get('slug') or '').strip()
        if slug:
            slug_to_id[slug] = aid

    for key, art in artifacts_map.items():
        owner = art.get('owner')
        if owner and isinstance(owner, str) and not owner.startswith('A-'):
            owner_slug = owner.strip().lower()
            mapped = slug_to_id.get(owner_slug)
            if mapped:
                art['owner'] = mapped
            else:
                owner_slug2 = re.sub(r'[^a-z0-9_]', '', owner_slug)
                mapped = slug_to_id.get(owner_slug2)
                if mapped:
                    art['owner'] = mapped
                else:
                    display_warning(f'Could not map artifact owner "{owner}" for artifact "{key}"')

    # Optionally render agent IDs in a different presentation format for planning phase
    render_map = {}
    if args.agent_id_format == 'padded':
        # map A-01 -> A01
        for aid in list(agents_map.keys()):
            if isinstance(aid, str) and '-' in aid:
                rid = aid.replace('-', '')
                render_map[aid] = rid

        # apply rendering to agents list, artifact owners, and workflow pipeline/checkpoints
        rendered_agents = []
        for a in data.get('agents', []):
            a_copy = dict(a)
            aid = a_copy.get('id')
            if aid in render_map:
                a_copy['id'] = render_map[aid]
            rendered_agents.append(a_copy)
        data['agents'] = rendered_agents

        for k, art in list(artifacts_map.items()):
            owner = art.get('owner')
            if owner in render_map:
                art['owner'] = render_map[owner]

        wf = data.get('workflow') or {}
        if isinstance(wf, dict):
            pipeline = wf.get('pipeline', {})
            order = pipeline.get('order', [])
            if isinstance(order, list):
                pipeline['order'] = [render_map.get(x, x) for x in order]
            # checkpoints may refer to after_agent
            cps = wf.get('checkpoints') or []
            for cp in cps:
                if isinstance(cp, dict) and 'after_agent' in cp:
                    cp['after_agent'] = render_map.get(cp['after_agent'], cp['after_agent'])
            wf['checkpoints'] = cps
            data['workflow'] = wf

    # Output YAML
    out_path = os.path.join(root, 'manifests', 'workflows', args.workflow, 'canonical_generated.yaml') if not args.output else args.output
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    header = (
        f"# Generated from canonical JSON in: {os.path.join('manifests','_canonical',args.workflow)}\n"
        f"# Generated at: {datetime.utcnow().isoformat()}Z\n"
        "# This YAML is intended for human editing; canonical JSON is authoritative.\n"
        "# To persist changes back to canonical JSON, run your migration tooling.\n\n"
    )

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(header)
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

    display_success(f'Wrote YAML: {out_path}')


if __name__ == '__main__':
    main()
