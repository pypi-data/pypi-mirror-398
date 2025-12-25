"""
HiveMind MCP Server - Navigator
Navigate the spider-web of documentation using anchor points.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from config import HIVEMIND_FILENAME, ANCHOR_PREFIX
from utils import parse_anchor, create_anchor, normalize_path, extract_first_paragraph


async def load_hivemind(anchor: str) -> Optional[str]:
    """
    Load hivemind.md content from an anchor point.
    
    Args:
        anchor: Anchor string in format "anchor://path/to/directory"
        
    Returns:
        Content of hivemind.md or None if not found
    """
    try:
        dir_path = parse_anchor(anchor)
        hivemind_path = dir_path / HIVEMIND_FILENAME
        
        if not hivemind_path.exists():
            return None
        
        return hivemind_path.read_text(encoding='utf-8', errors='ignore')
        
    except Exception:
        return None


async def load_with_context(
    anchor: str,
    include_parent: bool = True,
    include_children_summary: bool = True,
) -> Dict[str, Any]:
    """
    Load target hivemind with optional parent and children context.
    
    Args:
        anchor: Target anchor point
        include_parent: Include parent directory context
        include_children_summary: Include summaries of child directories
        
    Returns:
        Dictionary with current, parent, and children content
    """
    result = {
        'current': None,
        'parent': None,
        'children': [],
        'anchor': anchor,
    }
    
    try:
        dir_path = parse_anchor(anchor)
        
        # Load current hivemind
        current_path = dir_path / HIVEMIND_FILENAME
        if current_path.exists():
            result['current'] = current_path.read_text(encoding='utf-8', errors='ignore')
        
        # Load parent hivemind
        if include_parent:
            parent_path = dir_path.parent / HIVEMIND_FILENAME
            if parent_path.exists():
                content = parent_path.read_text(encoding='utf-8', errors='ignore')
                # Extract just the header and What This Does section
                result['parent'] = {
                    'anchor': create_anchor(dir_path.parent),
                    'name': dir_path.parent.name,
                    'summary': extract_first_paragraph(content),
                }
        
        # Load children summaries
        if include_children_summary:
            for child in dir_path.iterdir():
                if child.is_dir():
                    child_hivemind = child / HIVEMIND_FILENAME
                    if child_hivemind.exists():
                        content = child_hivemind.read_text(encoding='utf-8', errors='ignore')
                        result['children'].append({
                            'anchor': create_anchor(child),
                            'name': child.name,
                            'summary': extract_first_paragraph(content),
                        })
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


async def search_hive(
    root_path: Path,
    query: str,
    search_type: str = 'function'
) -> List[Dict[str, Any]]:
    """
    Search all hivemind.md files for a query.
    
    Args:
        root_path: Root directory to start search from
        query: Search query (function name, module name, etc.)
        search_type: Type of search ('function', 'import', 'export', 'text')
        
    Returns:
        List of matching results with anchor points and context
    """
    results = []
    root_path = normalize_path(str(root_path))
    query_lower = query.lower()
    
    def search_in_file(hivemind_path: Path):
        try:
            content = hivemind_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            matches = []
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                
                # Check if query appears in line
                if query_lower in line_lower:
                    # Determine match type based on context
                    match_type = 'text'
                    
                    if search_type == 'function' and ('###' in line and '`' in line):
                        match_type = 'function'
                    elif search_type == 'import' and 'dependencies' in lines[max(0, i-5):i]:
                        match_type = 'import'
                    elif search_type == 'export' and 'exports' in lines[max(0, i-5):i]:
                        match_type = 'export'
                    
                    if search_type == 'text' or match_type == search_type:
                        matches.append({
                            'line': i + 1,
                            'content': line.strip(),
                            'type': match_type,
                        })
            
            if matches:
                dir_path = hivemind_path.parent
                results.append({
                    'anchor': create_anchor(dir_path),
                    'path': str(dir_path),
                    'name': dir_path.name,
                    'matches': matches,
                })
                
        except Exception:
            pass
    
    # Walk all directories
    for root, dirs, files in os.walk(root_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
            'node_modules', '.next', 'dist', 'build', '__pycache__', '.venv', 'venv'
        }]
        
        if HIVEMIND_FILENAME in files:
            search_in_file(Path(root) / HIVEMIND_FILENAME)
    
    return results


async def find_function(
    root_path: Path,
    function_name: str,
    return_context: bool = False,
) -> List[Dict[str, Any]]:
    """
    Find all definitions of a function by name.
    
    Args:
        root_path: Root directory to search from
        function_name: Name of function to find
        return_context: Include full context (signature, location, etc.)
        
    Returns:
        List of locations where function is defined
    """
    results = await search_hive(root_path, function_name, search_type='function')
    
    if not return_context:
        # Return just anchor points
        return [{'anchor': r['anchor'], 'name': r['name']} for r in results]
    
    # Extract more context for each match
    enriched_results = []
    
    for result in results:
        for match in result.get('matches', []):
            if 'function' in match.get('type', ''):
                enriched_results.append({
                    'anchor': result['anchor'],
                    'name': result['name'],
                    'signature': match.get('content', ''),
                    'line': match.get('line', 0),
                })
    
    return enriched_results


async def _scan_for_external_usage(target: str, root_path: Path) -> List[str]:
    """
    Scan codebase for usage of an external library.
    
    Args:
        target: Target anchor or module name
        root_path: Root directory to search
        
    Returns:
        List of anchors that use the target
    """
    found = []
    
    # Strip anchor prefix to get raw module name if needed
    clean_target = target
    if target.startswith('anchor://'):
        clean_target = target.split('anchor://')[-1]
    
    # We look for "anchor://target" in dependencies
    search_term = f"anchor://{clean_target}"
    
    try:
        for root, dirs, files in os.walk(str(root_path)):
            # Ignore standard junk directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                'node_modules', '.next', 'dist', 'build', '__pycache__', '.venv', 'venv'
            }]
            
            if HIVEMIND_FILENAME in files:
                path = Path(root) / HIVEMIND_FILENAME
                try:
                    content = path.read_text(encoding='utf-8', errors='ignore')
                    
                    if search_term not in content:
                        continue
                        
                    # Verify it's in the Upstream section
                    in_upstream = False
                    for line in content.split('\n'):
                        if 'Uses (Upstream)' in line:
                            in_upstream = True
                        elif 'Used By (Downstream)' in line or (line.startswith('## ') and in_upstream):
                            in_upstream = False
                        
                        if in_upstream and search_term in line:
                            found.append(create_anchor(Path(root)))
                            break
                            
                except Exception:
                    pass
    except Exception:
        pass
        
    return found


async def trace_connections(
    anchor: str,
    direction: str = 'both',
    max_depth: int = 2,
    root_path: Optional[Path] = None,
    include_external: bool = False,
) -> Dict[str, Any]:
    """
    Trace dependencies and dependents of a module.
    
    Args:
        anchor: Starting anchor point
        direction: 'upstream' (dependencies), 'downstream' (dependents), or 'both'
        max_depth: Maximum depth to trace
        root_path: Optional root path for searching
        include_external: Include external npm packages in results
        
    Returns:
        Dependency tree structure
    """
    result = {
        'anchor': anchor,
        'upstream': [],    # Things this module imports
        'downstream': [],  # Things that import this module
        'external': [],    # External packages (when include_external is True)
        'depth': 0,
    }
    
    try:
        dir_path = parse_anchor(anchor)
        hivemind_path = dir_path / HIVEMIND_FILENAME
        
        if not hivemind_path.exists():
            # If explicit hivemind missing, try scanning for external usage
            if root_path:
                external_usage = await _scan_for_external_usage(anchor, root_path)
                if external_usage:
                    result['downstream'] = external_usage
                    # Continue to recursive tracing below...
                else:
                    result['error'] = f"No hivemind.md found at {anchor} and no usage found in scan."
                    return result
            else:
                result['error'] = f"No hivemind.md found at {anchor}"
                return result
        
        content = hivemind_path.read_text(encoding='utf-8', errors='ignore')
        
        # Parse Dependencies section for external packages
        if include_external:
            in_dependencies = False
            in_external = False
            for line in content.split('\n'):
                line_stripped = line.strip()
                if '## Dependencies' in line:
                    in_dependencies = True
                elif line_stripped.startswith('## ') and in_dependencies:
                    in_dependencies = False
                elif '### External' in line and in_dependencies:
                    in_external = True
                elif '### Internal' in line and in_dependencies:
                    in_external = False
                elif in_external and line_stripped.startswith('- `'):
                    # Extract package name: - `@aws-sdk/client-s3` - ...
                    import re
                    match = re.search(r'`([^`]+)`', line_stripped)
                    if match:
                        pkg_name = match.group(1)
                        result['external'].append(pkg_name)
        
        # Parse Connections section
        in_connections = False
        in_upstream = False
        in_downstream = False
        
        for line in content.split('\n'):
            line_stripped = line.strip()
            
            if '## Connections' in line:
                in_connections = True
            elif line_stripped.startswith('## ') and in_connections:
                break
            elif 'Uses (Upstream)' in line or ('Uses' in line and in_connections):
                in_upstream = True
                in_downstream = False
            elif 'Used By (Downstream)' in line or ('Used By' in line and in_connections):
                in_downstream = True
                in_upstream = False
            elif in_connections and line_stripped.startswith('- '):
                # Extract anchor from line
                if '`anchor://' in line:
                    import re
                    match = re.search(r'`(anchor://[^`]+)`', line)
                    if match:
                        dep_anchor = match.group(1)
                        if in_upstream and direction in ('upstream', 'both'):
                            result['upstream'].append(dep_anchor)
                        elif in_downstream and direction in ('downstream', 'both'):
                            result['downstream'].append(dep_anchor)
        
        # Recursive tracing (if depth allows)
        if max_depth > 1:
            # Trace upstream
            if direction in ('upstream', 'both'):
                traced_upstream = []
                for dep in result['upstream'][:5]:  # Limit to prevent explosion
                    try:
                        child_trace = await trace_connections(
                            dep,
                            direction='upstream',
                            max_depth=max_depth - 1,
                            root_path=root_path,
                        )
                        traced_upstream.append(child_trace)
                    except Exception:
                        traced_upstream.append({'anchor': dep, 'error': 'Failed to trace'})
                result['upstream_trace'] = traced_upstream
            
            # Trace downstream
            if direction in ('downstream', 'both'):
                traced_downstream = []
                for dep in result['downstream'][:5]:  # Limit to prevent explosion
                    try:
                        child_trace = await trace_connections(
                            dep,
                            direction='downstream',
                            max_depth=max_depth - 1,
                            root_path=root_path,
                        )
                        traced_downstream.append(child_trace)
                    except Exception:
                        traced_downstream.append({'anchor': dep, 'error': 'Failed to trace'})
                result['downstream_trace'] = traced_downstream
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def format_trace_result(trace: Dict[str, Any], indent: int = 0) -> str:
    """
    Format trace result as readable text.
    
    Args:
        trace: Trace result dictionary
        indent: Indentation level
        
    Returns:
        Formatted string
    """
    prefix = "  " * indent
    lines = []
    
    anchor = trace.get('anchor', 'Unknown')
    lines.append(f"{prefix}📍 {anchor}")
    
    # Upstream
    upstream = trace.get('upstream', [])
    if upstream:
        lines.append(f"{prefix}  ⬆️ Uses ({len(upstream)}):")
        for dep in upstream:
            lines.append(f"{prefix}    - {dep}")
    
    # Upstream trace
    upstream_trace = trace.get('upstream_trace', [])
    if upstream_trace:
        for child in upstream_trace:
            lines.append(format_trace_result(child, indent + 2))
    
    # Downstream
    downstream = trace.get('downstream', [])
    if downstream:
        lines.append(f"{prefix}  ⬇️ Used By ({len(downstream)}):")
        for dep in downstream:
            lines.append(f"{prefix}    - {dep}")
    
    # Downstream trace
    downstream_trace = trace.get('downstream_trace', [])
    if downstream_trace:
        for child in downstream_trace:
            lines.append(format_trace_result(child, indent + 2))
    
    # External packages
    external = trace.get('external', [])
    if external:
        lines.append(f"{prefix}  📦 External Packages ({len(external)}):")
        for pkg in external:
            lines.append(f"{prefix}    - {pkg}")
    
    return '\n'.join(lines)


async def get_navigation_context(
    anchor: str,
    context_size: str = 'medium'
) -> str:
    """
    Get navigation context for AI to understand location in codebase.
    
    Args:
        anchor: Current anchor point
        context_size: 'small', 'medium', or 'large'
        
    Returns:
        Formatted context string
    """
    result = await load_with_context(
        anchor,
        include_parent=(context_size != 'small'),
        include_children_summary=(context_size != 'small'),
    )
    
    sections = []
    
    # Current context
    if result.get('current'):
        sections.append("=== CURRENT CONTEXT ===")
        if context_size == 'small':
            # Just the header and first section
            lines = result['current'].split('\n')
            sections.append('\n'.join(lines[:30]))
        elif context_size == 'medium':
            # Everything above the separator
            parts = result['current'].split('---')
            sections.append(parts[0] if parts else result['current'])
        else:
            # Full content
            sections.append(result['current'])
    
    # Parent context
    if result.get('parent'):
        sections.append("\n=== PARENT CONTEXT ===")
        parent = result['parent']
        sections.append(f"# {parent['name']}")
        sections.append(parent.get('summary', ''))
    
    # Children
    if result.get('children'):
        sections.append("\n=== CHILDREN ===")
        for child in result['children']:
            sections.append(f"- **{child['name']}**: {child.get('summary', '')[:100]}...")
    
    return '\n'.join(sections)
