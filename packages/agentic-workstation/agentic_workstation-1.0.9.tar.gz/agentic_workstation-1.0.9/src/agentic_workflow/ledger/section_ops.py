"""Marker-based section operations for log and context files.

Provides utilities for:
- Reading specific sections by marker
- Inserting entries at the top of sections (reverse chronological)
- Updating YAML sidecars alongside markdown
"""
import re
import datetime
from datetime import timezone
from pathlib import Path
from typing import Dict, Any, List
import yaml

__all__ = [
    "read_section",
    "read_entry", 
    "insert_entry_to_section",
    "update_metadata",
    "get_timestamp",
    "ensure_yaml_sidecar",
    "append_to_yaml_sidecar",
    "read_yaml_section",
    "find_entry_in_yaml"
]


def read_section(file_path: Path, section_name: str) -> str:
    """Read content between SECTION markers.
    
    Args:
        file_path: Path to the markdown file
        section_name: Section name (e.g., 'HANDOFFS', 'DECISIONS')
        
    Returns:
        Content between markers (excluding markers), or empty string if not found
    """
    if not file_path.exists():
        return ""
    
    content = file_path.read_text()
    pattern = rf'\n(.*?)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    return ""


def read_entry(file_path: Path, entry_type: str, entry_id: str) -> str:
    """Read a specific entry by its markers.
    
    Args:
        file_path: Path to the markdown file
        entry_type: Entry type (HANDOFF, DECISION, etc.)
        entry_id: Entry ID (HO-001, DEC-003, etc.)
        
    Returns:
        Entry content (excluding markers), or empty string if not found
    """
    if not file_path.exists():
        return ""
    
    content = file_path.read_text()
    pattern = rf'\n(.*?)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    return ""


def insert_entry_to_section(file_path: Path, section_name: str, entry_type: str, 
                            entry_id: str, entry_content: str) -> bool:
    """Insert a new entry at the TOP of a section (reverse chronological order).
    
    Args:
        file_path: Path to the markdown file
        section_name: Section name (e.g., 'HANDOFFS')
        entry_type: Entry type for markers (e.g., 'HANDOFF')
        entry_id: Entry ID (e.g., 'HO-001')
        entry_content: The markdown content for the entry (without markers)
        
    Returns:
        True if successful, False otherwise
    """
    # Create file with basic section structure if it doesn't exist
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Create a basic log file with the required section
        basic_content = f"""# Log File

> Created: {get_timestamp()}

---
<!-- SECTION:{section_name}:START -->
## {section_name.title()}
<!-- (Newest entries at top) -->
<!-- SECTION:{section_name}:END -->

"""
        file_path.write_text(basic_content)
    
    content = file_path.read_text()
    
    # Build the full entry with markers
    entry_block = f"""
{entry_content}


"""
    
    # Find the section and insert after the START marker and any comment (with any suffix)
    # Matches:  OR 
    pattern = rf'(\n(?:##[^\n]*\n)?(?:\n)?]*\) -->\n)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        # Insert after the section start and comment
        insert_pos = match.end()
        new_content = content[:insert_pos] + "\n" + entry_block + content[insert_pos:]
        file_path.write_text(new_content)
        return True
    
    # Fallback: find section start and insert after header
    pattern_simple = rf'(\n)'
    match_simple = re.search(pattern_simple, content, re.IGNORECASE)
    
    if match_simple:
        insert_pos = match_simple.end()
        rest = content[insert_pos:]
        
        # Skip header line (## ...)
        if rest.startswith('##'):
            next_line = rest.find('\n')
            if next_line != -1:
                insert_pos += next_line + 1
                rest = content[insert_pos:]
        
        # Skip empty lines
        while rest.startswith('\n'):
            insert_pos += 1
            rest = content[insert_pos:]
        
        # Skip comment line if present
        if rest.startswith('<!-- '):
            next_line = rest.find('\n')
            if next_line != -1:
                insert_pos += next_line + 1
        
        new_content = content[:insert_pos] + "\n" + entry_block + content[insert_pos:]
        file_path.write_text(new_content)
        return True
    
    return False


def update_metadata(file_path: Path, updates: Dict[str, Any]) -> bool:
    """Update values in the METADATA section.
    
    Args:
        file_path: Path to the markdown file
        updates: Dict of key-value pairs to update (e.g., {'last_updated': '...'})
        
    Returns:
        True if successful
    """
    if not file_path.exists():
        return False
    
    content = file_path.read_text()
    
    for key, value in updates.items():
        # Try to update existing key
        pattern = rf'^({key}:\s*).*$'
        replacement = rf'\1{value}'
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            content = new_content
    
    file_path.write_text(content)
    return True


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_yaml_sidecar(md_path: Path) -> Path:
    """Ensure YAML sidecar exists for a markdown file.
    
    Creates empty structure if missing.
    
    Returns:
        Path to the YAML file
    """
    yaml_path = md_path.with_suffix('.yaml')
    
    if not yaml_path.exists():
        # Determine structure based on filename
        if 'exchange_log' in str(md_path):
            initial_data = {
                'project': md_path.parent.parent.name,
                'created': get_timestamp(),
                'last_updated': get_timestamp(),
                'handoffs': [],
                'feedback': [],
                'iterations': [],
                'archives': [],
            }
        elif 'context_log' in str(md_path):
            initial_data = {
                'project': md_path.parent.parent.name,
                'created': get_timestamp(),
                'last_updated': get_timestamp(),
                'sessions': [],
                'decisions': [],
                'assumptions': [],
                'blockers': [],
                'archives': [],
            }
        else:
            initial_data = {
                'created': get_timestamp(),
                'last_updated': get_timestamp(),
                'entries': [],
            }
        
        with open(yaml_path, 'w') as f:
            yaml.safe_dump(initial_data, f, sort_keys=False)
    
    return yaml_path


def append_to_yaml_sidecar(yaml_path: Path, section: str, entry: Dict[str, Any]) -> bool:
    """Append an entry to a section in the YAML sidecar.
    
    Entries are prepended (newest first) to match markdown order.
    
    Args:
        yaml_path: Path to the YAML file
        section: Section key (e.g., 'handoffs', 'decisions')
        entry: Dict entry to add
        
    Returns:
        True if successful
    """
    if not yaml_path.exists():
        yaml_path = ensure_yaml_sidecar(yaml_path.with_suffix('.md'))
    
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        data = {}
    
    # Ensure section exists
    if section not in data:
        data[section] = []
    
    # Prepend new entry (newest first)
    data[section].insert(0, entry)
    data['last_updated'] = get_timestamp()
    
    with open(yaml_path, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False)
    
    return True


def read_yaml_section(yaml_path: Path, section: str) -> List[Dict[str, Any]]:
    """Read all entries from a YAML section.
    
    Args:
        yaml_path: Path to the YAML file
        section: Section key (e.g., 'handoffs')
        
    Returns:
        List of entries, or empty list
    """
    if not yaml_path.exists():
        return []
    
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return []
    
    return data.get(section, [])


def find_entry_in_yaml(yaml_path: Path, section: str, entry_id: str) -> Dict[str, Any]:
    """Find a specific entry by ID in a YAML section.
    
    Args:
        yaml_path: Path to the YAML file
        section: Section key
        entry_id: Entry ID to find
        
    Returns:
        Entry dict if found, else empty dict
    """
    entries = read_yaml_section(yaml_path, section)
    
    for entry in entries:
        if entry.get('id') == entry_id:
            return entry
    
    return {}
