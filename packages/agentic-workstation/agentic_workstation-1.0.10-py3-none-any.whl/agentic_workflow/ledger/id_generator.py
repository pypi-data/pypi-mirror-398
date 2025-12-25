"""ID generation utilities for log entries.

Auto-generates sequential IDs based on existing entries in YAML ledgers.
Supports: HANDOFF (HO-xxx), FEEDBACK (FB-xxx), ITERATION (ITER-xxx),
SESSION (SESS-xxx), DECISION (DEC-xxx), ASSUMPTION (ASSUMP-xxx), BLOCKER (BLK-xxx)
"""
import re
from pathlib import Path
import yaml

__all__ = [
    "ID_PREFIXES",
    "get_next_id",
    "get_next_id_from_md", 
    "generate_entry_id",
    "generate_context_entry_id"
]

# ID prefixes by type
ID_PREFIXES = {
    'HANDOFF': 'HO',
    'FEEDBACK': 'FB',
    'ITERATION': 'ITER',
    'SESSION': 'SESS',
    'DECISION': 'DEC',
    'ASSUMPTION': 'ASSUMP',
    'BLOCKER': 'BLK',
    'TASK': 'T',
    'QUESTION': 'Q',
}


def _extract_numeric_id(id_string: str, prefix: str) -> int:
    """Extract the numeric portion from an ID string like 'HO-005' -> 5."""
    if not id_string:
        return 0
    pattern = rf'{prefix}-?(\d+)'
    match = re.search(pattern, id_string, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


def get_next_id(yaml_path: Path, entry_type: str) -> str:
    """Get the next sequential ID for an entry type by reading the YAML ledger.
    
    Args:
        yaml_path: Path to the YAML ledger file
        entry_type: Type of entry (HANDOFF, FEEDBACK, etc.)
        
    Returns:
        Next ID string like 'HO-001', 'FB-002', etc.
    """
    prefix = ID_PREFIXES.get(entry_type.upper(), entry_type[:3].upper())
    
    if not yaml_path.exists():
        return f"{prefix}-001"
    
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
    except Exception:
        return f"{prefix}-001"
    
    if not data:
        return f"{prefix}-001"
    
    # Handle both list format and dict format
    max_num = 0
    
    if isinstance(data, list):
        # List of entries (old format or exchange_log entries)
        for entry in data:
            if not isinstance(entry, dict):
                continue
            # Check various ID field names
            for id_field in ['handoff_id', 'ticket_id', 'iteration_id', 'id', 'ref_id']:
                id_val = entry.get(id_field, '')
                if id_val and prefix in str(id_val).upper():
                    num = _extract_numeric_id(str(id_val), prefix)
                    max_num = max(max_num, num)
    
    elif isinstance(data, dict):
        # Dict format with sections (new format)
        # Check known section keys
        section_keys = {
            'HO': 'handoffs',
            'FB': 'feedback',
            'ITER': 'iterations',
            'SESS': 'sessions',
            'DEC': 'decisions',
            'ASSUMP': 'assumptions',
            'BLK': 'blockers',
        }
        
        section_key = section_keys.get(prefix, entry_type.lower() + 's')
        entries = data.get(section_key, [])
        
        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                id_val = entry.get('id', '')
                if id_val:
                    num = _extract_numeric_id(str(id_val), prefix)
                    max_num = max(max_num, num)
    
    next_num = max_num + 1
    return f"{prefix}-{next_num:03d}"


def get_next_id_from_md(md_path: Path, entry_type: str) -> str:
    """Fallback: Get next ID by scanning markdown for existing entry markers.
    
    Scans for patterns like 
    """
    prefix = ID_PREFIXES.get(entry_type.upper(), entry_type[:3].upper())
    
    if not md_path.exists():
        return f"{prefix}-001"
    
    try:
        content = md_path.read_text()
    except Exception:
        return f"{prefix}-001"
    
    # Find all entry markers with this prefix
    pattern = rf'ENTRY:{entry_type.upper()}:{prefix}-(\d+):START'
    matches = re.findall(pattern, content, re.IGNORECASE)
    
    if not matches:
        return f"{prefix}-001"
    
    max_num = max(int(m) for m in matches)
    return f"{prefix}-{max_num + 1:03d}"


def generate_entry_id(project_dir: Path, log_file: str, entry_type: str) -> str:
    """Generate the next entry ID for a given log file and entry type.
    
    Tries YAML first, falls back to MD scanning.
    
    Args:
        project_dir: Project directory path
        log_file: Log file name (e.g., 'exchange_log.md' or 'context_log.md')
        entry_type: Entry type (HANDOFF, FEEDBACK, SESSION, DECISION, etc.)
        
    Returns:
        Next ID string like 'HO-001', 'SESS-003', etc.
    """
    # Normalize log_file path
    if 'agent_log' in log_file:
        base_path = project_dir / log_file
    else:
        base_path = project_dir / 'agent_log' / log_file
    
    yaml_path = base_path.with_suffix('.yaml')
    md_path = base_path if base_path.suffix == '.md' else base_path.with_suffix('.md')
    
    # Try YAML first (more reliable)
    if yaml_path.exists():
        return get_next_id(yaml_path, entry_type)
    
    # Fall back to MD scanning
    return get_next_id_from_md(md_path, entry_type)


def generate_context_entry_id(context_path: Path, entry_type: str) -> str:
    """Generate next ID for agent context file entries.
    
    These are local IDs (e.g., DEC-L-001 for local decisions).
    Scans the context file directly.
    """
    prefix = ID_PREFIXES.get(entry_type.upper(), entry_type[:3].upper())
    local_prefix = f"{prefix}-L"
    
    if not context_path.exists():
        return f"{local_prefix}-001"
    
    try:
        content = context_path.read_text()
    except Exception:
        return f"{local_prefix}-001"
    
    # Find local entry markers
    pattern = rf'ENTRY:{entry_type.upper()}:{local_prefix}-(\d+):START'
    matches = re.findall(pattern, content, re.IGNORECASE)
    
    if not matches:
        return f"{local_prefix}-001"
    
    max_num = max(int(m) for m in matches)
    return f"{local_prefix}-{max_num + 1:03d}"
