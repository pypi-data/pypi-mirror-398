"""
HiveMind MCP Server - Generator
Generate hivemind.md and flowchart.mmd from structure and AI context.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiofiles
import asyncio
import shutil

from config import HIVEMIND_FILENAME, FLOWCHART_FILENAME, SVG_FILENAME, get_complexity_label
from utils import (
    sanitize_filename,
    create_anchor,
    format_list,
    format_code_block,
    get_relative_path,
    truncate_string,
)


async def generate_hivemind(
    structure: Dict[str, Any],
    ai_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate hivemind.md content from structure and AI context.
    
    Args:
        structure: Parsed structure dictionary from parser.analyze_directory()
        ai_context: Optional AI-provided context dictionary
        
    Returns:
        Formatted markdown string
    """
    ai_context = ai_context or {}
    sections = []
    
    # Header
    dir_name = structure.get('name', 'Unknown')
    sections.append(f"# {dir_name}")
    sections.append("")
    
    # ============================================================
    # AI Context Sections (above the line)
    # ============================================================
    
    # 🎯 What This Does
    if ai_context.get('context'):
        sections.append("## What This Does")
        sections.append(ai_context['context'])
        sections.append("")
    
    # 👤 User Requirements
    if ai_context.get('user_requirements'):
        sections.append("## User Requirements")
        sections.append(ai_context['user_requirements'])
        sections.append("")
    
    # ⚠️ Important Notes
    if ai_context.get('warnings'):
        sections.append("## Important Notes")
        sections.append(ai_context['warnings'])
        sections.append("")
    
    # 🔮 Next Steps
    if ai_context.get('next_steps'):
        sections.append("## Next Steps")
        sections.append(ai_context['next_steps'])
        sections.append("")
    
    # 💡 How It Works
    if ai_context.get('how_it_works'):
        sections.append("## How It Works")
        sections.append(ai_context['how_it_works'])
        sections.append("")
    
    # ============================================================
    # Separator
    # ============================================================
    sections.append("---")
    sections.append("")
    
    # ============================================================
    # Dry Logic Sections (below the line)
    # ============================================================
    
    # 📁 Files at This Level
    files = structure.get('files', [])
    if files:
        sections.append("## Files at This Level")
        for f in files:
            name = f.get('name', 'unknown')
            lines = f.get('lines', 0)
            sections.append(f"- `{name}` ({lines} lines)")
        sections.append("")
    
    # ⚙️ Functions Defined
    functions = structure.get('all_functions', [])
    if functions:
        sections.append("## Functions Defined")
        sections.append("")
        
        for func in functions:
            name = func.get('name', 'unknown')
            params = func.get('params', '()')
            return_type = func.get('return_type', 'void')
            
            # Function signature
            sections.append(f"### `{name}{params}: {return_type}`")
            
            # Details
            file_name = Path(func.get('file_path', '')).name if func.get('file_path') else 'unknown'
            start = func.get('start_line', 0)
            end = func.get('end_line', 0)
            sections.append(f"- **Location**: {file_name}:{start}-{end}")
            sections.append(f"- **Async**: {'Yes' if func.get('async') else 'No'}")
            sections.append(f"- **Exported**: {'Yes' if func.get('exported') else 'No'}")
            sections.append(f"- **Complexity**: {func.get('complexity_label', 'Low')}")
            
            if func.get('docstring'):
                sections.append(f"- **Description**: {truncate_string(func['docstring'], 100)}")
            
            sections.append("")
    
    # 📦 Dependencies
    imports = structure.get('all_imports', [])
    if imports:
        sections.append("## Dependencies")
        sections.append("")
        
        external = []
        internal = []
        
        for imp in imports:
            module = imp.get('module', '')
            names = ', '.join(imp.get('imports', []))
            
            if module.startswith('.') or module.startswith('@/') or module.startswith('~/'):
                internal.append(f"- `{module}` - {names or 'namespace'}")
            else:
                external.append(f"- `{module}` - {names or 'namespace'}")
        
        if external:
            sections.append("### External")
            sections.extend(external)
            sections.append("")
        
        if internal:
            sections.append("### Internal")
            sections.extend(internal)
            sections.append("")
    
    # 📤 Exports
    exports = structure.get('all_exports', [])
    if exports:
        sections.append("## Exports")
        sections.append("")
        
        export_lines = []
        for exp in exports:
            name = exp.get('name', '')
            exp_type = exp.get('type', 'named')
            is_default = exp.get('is_default', False)
            
            if is_default:
                export_lines.append(f"export default {name}")
            else:
                export_lines.append(f"export {exp_type} {name}")
        
        if export_lines:
            sections.append(format_code_block('\n'.join(export_lines), 'typescript'))
            sections.append("")
    
    # Classes
    classes = structure.get('all_classes', [])
    if classes:
        sections.append("## Classes")
        sections.append("")
        
        for cls in classes:
            name = cls.get('name', 'Unknown')
            extends = cls.get('extends')
            sections.append(f"### `{name}`" + (f" extends `{extends}`" if extends else ""))
            sections.append(f"- **Lines**: {cls.get('start_line', 0)}-{cls.get('end_line', 0)}")
            sections.append(f"- **Exported**: {'Yes' if cls.get('exported') else 'No'}")
            
            methods = cls.get('methods', [])
            if methods:
                sections.append(f"- **Methods**: {len(methods)}")
                for m in methods[:5]:  # Limit to 5 methods shown
                    sections.append(f"  - `{m.get('name', '')}()`")
                if len(methods) > 5:
                    sections.append(f"  - _...and {len(methods) - 5} more_")
            sections.append("")
    
    # Types (TypeScript)
    types = structure.get('all_types', [])
    if types:
        sections.append("## Types & Interfaces")
        sections.append("")
        
        for t in types:
            kind = t.get('kind', 'type')
            name = t.get('name', 'Unknown')
            sections.append(f"- `{kind} {name}` (line {t.get('start_line', 0)})")
        sections.append("")
    
    # 🔗 Connections
    connections = structure.get('connections', {})
    uses = connections.get('uses', [])
    used_by = connections.get('used_by', [])
    
    if uses or used_by:
        sections.append("## Connections")
        sections.append("")
        
        if used_by:
            sections.append("### Used By (Downstream)")
            for dep in used_by:
                anchor = create_anchor(Path(dep))
                sections.append(f"- `{anchor}`")
            sections.append("")
        
        if uses:
            sections.append("### Uses (Upstream)")
            for dep in uses:
                anchor = create_anchor(Path(dep))
                sections.append(f"- `{anchor}`")
            sections.append("")
    
    # Navigation
    sections.append("## Navigation")
    sections.append("")
    
    current_path = Path(structure.get('path', ''))
    parent = structure.get('parent')
    children = structure.get('children', [])
    
    # Parent link
    if parent:
        parent_path = Path(parent)
        rel_path = get_relative_path(current_path, parent_path)
        anchor = create_anchor(parent_path)
        sections.append(f"- **Parent**: [{parent_path.name}]({rel_path}/hivemind.md) `{anchor}`")
    
    # Children links
    if children:
        sections.append("- **Children**:")
        for child in children:
            child_path = Path(child)
            rel_path = get_relative_path(current_path, child_path)
            anchor = create_anchor(child_path)
            sections.append(f"  - [{child_path.name}]({rel_path}/hivemind.md) `{anchor}`")
    
    # Current anchor
    current_anchor = create_anchor(current_path)
    sections.append(f"- **Anchor**: `{current_anchor}`")
    sections.append("")
    
    # 📊 Metrics
    metrics = structure.get('metrics', {})
    sections.append("## Metrics")
    sections.append("")
    sections.append(f"- **Total Lines**: {metrics.get('total_lines', 0)}")
    sections.append(f"- **Total Files**: {metrics.get('total_files', 0)}")
    sections.append(f"- **Functions**: {metrics.get('total_functions', 0)}")
    sections.append(f"- **Classes**: {metrics.get('total_classes', 0)}")
    sections.append(f"- **Types**: {metrics.get('total_types', 0)}")
    sections.append(f"- **Avg Complexity**: {metrics.get('complexity_label', 'Low')} ({metrics.get('avg_complexity', 1.0)})")
    sections.append(f"- **Last Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    sections.append("")
    
    return '\n'.join(sections)


async def generate_flowchart(structure: Dict[str, Any]) -> str:
    """
    Generate Mermaid flowchart from structure.
    
    Args:
        structure: Parsed structure dictionary
        
    Returns:
        Mermaid diagram string
    """
    lines = []
    lines.append("graph TD")
    lines.append("")
    
    # Defaults for styling
    lines.append("    %% Styling for visual clarity")
    lines.append("    classDef currentNode fill:#4f46e5,stroke:#333,stroke-width:3px,color:#fff")
    lines.append("    classDef parentNode fill:#64748b,stroke:#333,stroke-width:2px,color:#fff")
    lines.append("    classDef childNode fill:#10b981,stroke:#333,stroke-width:2px,color:#fff")
    lines.append("    classDef upstreamNode fill:#f59e0b,stroke:#333,stroke-width:2px,color:#fff")
    lines.append("    classDef downstreamNode fill:#06b6d4,stroke:#333,stroke-width:2px,color:#fff")
    lines.append("")

    # Current directory as central node
    current_name = structure.get('name', 'current')
    current_id = sanitize_filename(current_name)
    lines.append(f"    %% Current directory as central node")
    lines.append(f"    {current_id}[{current_name}]")
    lines.append("")
    
    # Parent link
    parent = structure.get('parent')
    if parent:
        parent_name = Path(parent).name
        parent_id = sanitize_filename(f"parent_{parent_name}")
        lines.append(f"    %% Parent link")
        lines.append(f"    {parent_id}[{parent_name}] --> {current_id}")
        lines.append("")
    
    # Children links
    children = structure.get('children', [])
    if children:
        lines.append(f"    %% Children")
        for child in children:
            child_name = Path(child).name
            child_id = sanitize_filename(f"child_{child_name}")
            lines.append(f"    {current_id} --> {child_id}[{child_name}]")
        lines.append("")
    
    # Upstream dependencies (things this imports)
    connections = structure.get('connections', {})
    uses = connections.get('uses', [])
    if uses:
        lines.append(f"    %% Upstream dependencies (things this imports)")
        for i, dep in enumerate(uses[:5]):  # Limit to 5
            dep_name = Path(dep).name
            dep_id = sanitize_filename(f"dep_{dep_name}_{i}")
            lines.append(f"    {dep_id}[{dep_name}] --> {current_id}")
        lines.append("")
    
    # Downstream usage (things that import this)
    used_by = connections.get('used_by', [])
    if used_by:
        lines.append(f"    %% Downstream usage (things that import this)")
        for i, dep in enumerate(used_by[:5]):  # Limit to 5
            dep_name = Path(dep).name
            dep_id = sanitize_filename(f"user_{dep_name}_{i}")
            lines.append(f"    {current_id} --> {dep_id}[{dep_name}]")
        lines.append("")
    
    # Styling (already defined at top)
    
    # Apply styles
    lines.append(f"    class {current_id} currentNode")
    
    if parent:
        parent_name = Path(parent).name
        parent_id = sanitize_filename(f"parent_{parent_name}")
        lines.append(f"    class {parent_id} parentNode")
    
    if children:
        child_ids = [sanitize_filename(f"child_{Path(c).name}") for c in children]
        lines.append(f"    class {','.join(child_ids)} childNode")
    
    if uses:
        dep_ids = [sanitize_filename(f"dep_{Path(d).name}_{i}") for i, d in enumerate(uses[:5])]
        lines.append(f"    class {','.join(dep_ids)} upstreamNode")
    
    if used_by:
        user_ids = [sanitize_filename(f"user_{Path(d).name}_{i}") for i, d in enumerate(used_by[:5])]
        lines.append(f"    class {','.join(user_ids)} downstreamNode")
    
    return '\n'.join(lines)


async def generate_svg(mmd_path: Path, svg_path: Path, timeout: int = 30) -> Optional[str]:
    """
    Generate SVG from MMD file using mermaid-cli.
    
    Args:
        mmd_path: Path to input .mmd file
        svg_path: Path to output .svg file
        
    Returns:
        Error message if failed, None if success
    """
    # Check if mmdc is available
    mmdc_cmd = shutil.which("mmdc")
    if not mmdc_cmd:
        return "MMDC_NOT_INSTALLED: Mermaid CLI (mmdc) not installed. Advised to install for proper experience: npm install -g @mermaid-js/mermaid-cli"
    
    cmd = [
        mmdc_cmd,
        "-i", str(mmd_path),
        "-o", str(svg_path),
        "-t", "dark",
        "-b", "transparent"
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            return f"SVG generation timed out after {timeout}s"
        
        if process.returncode != 0:
            return f"Mermaid CLI failed: {stderr.decode()}"
            
        return None
        
    except Exception as e:
        return f"Error generating SVG: {str(e)}"


async def write_files(
    dir_path: Path,
    hivemind_content: str,
    flowchart_content: str,
) -> Dict[str, Any]:
    """
    Write hivemind.md, hivemind.mmd, and hivemind.svg to directory.
    
    Args:
        dir_path: Directory to write files to
        hivemind_content: Content for hivemind.md
        flowchart_content: Content for hivemind.mmd
        
    Returns:
        Dictionary with write status and file paths
    """
    result = {
        'success': True,
        'files_written': [],
        'errors': [],
    }
    
    # Ensure directory exists
    dir_path = Path(dir_path)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        result['success'] = False
        result['errors'].append(f"Failed to create directory: {e}")
        return result
    
    # Write hivemind.md
    hivemind_path = dir_path / HIVEMIND_FILENAME
    try:
        async with aiofiles.open(hivemind_path, 'w', encoding='utf-8') as f:
            await f.write(hivemind_content)
        result['files_written'].append(str(hivemind_path))
    except Exception as e:
        result['success'] = False
        result['errors'].append(f"Failed to write {HIVEMIND_FILENAME}: {e}")
    
    # Write hivemind.mmd
    flowchart_path = dir_path / FLOWCHART_FILENAME
    try:
        async with aiofiles.open(flowchart_path, 'w', encoding='utf-8') as f:
            await f.write(flowchart_content)
        result['files_written'].append(str(flowchart_path))
    except Exception as e:
        result['success'] = False
        result['errors'].append(f"Failed to write {FLOWCHART_FILENAME}: {e}")
    
    # Generate hivemind.svg
    if result.get('success'):
        svg_path = dir_path / SVG_FILENAME
        error = await generate_svg(flowchart_path, svg_path) # Original uses flowchart_path
        
        if error:
            # Don't fail the whole build for SVG generation errors, but log it
            result['errors'].append(f"SVG Generation warning: {error}")
        elif svg_path.exists():
            result['files_written'].append(str(svg_path))
    
    return result


async def generate_and_write(
    structure: Dict[str, Any],
    ai_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate documentation and write to directory.
    
    Convenience function that combines generation and writing.
    
    Args:
        structure: Parsed structure dictionary
        ai_context: Optional AI context
        
    Returns:
        Result dictionary with status and details
    """
    dir_path = Path(structure.get('path', '.'))
    
    # Generate content
    hivemind_content = await generate_hivemind(structure, ai_context)
    flowchart_content = await generate_flowchart(structure)
    
    # Write files
    result = await write_files(dir_path, hivemind_content, flowchart_content)
    
    # Add summary
    result['directory'] = str(dir_path)
    result['hivemind_lines'] = len(hivemind_content.split('\n'))
    result['flowchart_lines'] = len(flowchart_content.split('\n'))
    
    return result
