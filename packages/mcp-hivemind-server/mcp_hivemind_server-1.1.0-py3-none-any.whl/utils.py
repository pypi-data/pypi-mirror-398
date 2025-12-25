"""
HiveMind MCP Server - Utilities
Helper functions for path manipulation, formatting, and common operations.
"""

import re
from pathlib import Path
from typing import List, Optional, Any
from datetime import datetime

from config import ANCHOR_PREFIX, IGNORE_PATTERNS


def sanitize_filename(name: str) -> str:
    """
    Clean filename for use in Mermaid IDs.
    Removes special characters and replaces spaces/dots with underscores.
    
    Args:
        name: Original filename or identifier
        
    Returns:
        Sanitized string safe for Mermaid node IDs
    """
    # Remove file extension if present
    name = Path(name).stem if '.' in name else name
    # Replace special characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Ensure it starts with a letter (Mermaid requirement)
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'n_' + sanitized
    return sanitized or 'unnamed'


def normalize_path(path: str) -> Path:
    """
    Normalize file path to absolute Path object.
    
    Args:
        path: Relative or absolute path string
        
    Returns:
        Normalized absolute Path object
    """
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve()


def parse_anchor(anchor: str) -> Path:
    """
    Convert anchor string to file path.
    
    Args:
        anchor: Anchor in format "anchor://path/to/directory"
        
    Returns:
        Path object pointing to the directory
        
    Raises:
        ValueError: If anchor format is invalid
    """
    if not anchor.startswith(ANCHOR_PREFIX):
        raise ValueError(f"Invalid anchor format. Expected '{ANCHOR_PREFIX}...'")
    
    path_str = anchor[len(ANCHOR_PREFIX):]
    return normalize_path(path_str)


def create_anchor(path: Path, root: Optional[Path] = None) -> str:
    """
    Create anchor string from path.
    
    Args:
        path: Path to create anchor for
        root: Optional root path to make anchor relative to
        
    Returns:
        Anchor string in format "anchor://path/to/directory"
    """
    if root:
        try:
            relative = path.relative_to(root)
            return f"{ANCHOR_PREFIX}{relative.as_posix()}"
        except ValueError:
            pass
    return f"{ANCHOR_PREFIX}{path.as_posix()}"


def format_list(items: List[Any], prefix: str = "- ") -> str:
    """
    Format list items for markdown.
    
    Args:
        items: List of items to format
        prefix: Prefix for each line (default "- ")
        
    Returns:
        Formatted markdown list string
    """
    if not items:
        return "_None_"
    return '\n'.join(f"{prefix}{item}" for item in items)


def format_code_block(code: str, language: str = "") -> str:
    """
    Format code as markdown code block.
    
    Args:
        code: Code content
        language: Language for syntax highlighting
        
    Returns:
        Formatted code block string
    """
    return f"```{language}\n{code}\n```"


def get_relative_path(from_path: Path, to_path: Path) -> str:
    """
    Get relative path from one path to another.
    
    Args:
        from_path: Starting path
        to_path: Target path
        
    Returns:
        Relative path string
    """
    try:
        # Find common ancestor
        from_parts = from_path.resolve().parts
        to_parts = to_path.resolve().parts
        
        # Find where paths diverge
        common_length = 0
        for i, (f, t) in enumerate(zip(from_parts, to_parts)):
            if f != t:
                break
            common_length = i + 1
        
        # Build relative path
        ups = len(from_parts) - common_length
        downs = to_parts[common_length:]
        
        if ups == 0 and not downs:
            return '.'
        
        parts = ['..'] * ups + list(downs)
        return '/'.join(parts)
    except Exception:
        return str(to_path)


def should_ignore(path: Path) -> bool:
    """
    Check if path should be ignored.
    
    Args:
        path: Path to check
        
    Returns:
        True if path should be ignored
    """
    for pattern in IGNORE_PATTERNS:
        if pattern in path.parts:
            return True
        # Check for glob patterns
        if '*' in pattern:
            if path.match(pattern):
                return True
    return False


def calculate_complexity(node_count: int, branch_count: int = 0, loop_count: int = 0) -> int:
    """
    Calculate simplified cyclomatic complexity.
    
    Cyclomatic complexity = E - N + 2P where:
    - E = edges
    - N = nodes  
    - P = connected components (usually 1)
    
    Simplified: 1 + number of decision points (branches, loops)
    
    Args:
        node_count: Number of nodes/statements
        branch_count: Number of if/switch/ternary
        loop_count: Number of for/while/do-while
        
    Returns:
        Complexity score
    """
    return 1 + branch_count + loop_count


def get_file_info(file_path: Path) -> dict:
    """
    Get basic file information.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dict with name, path, lines, size, modified
    """
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = len(content.splitlines())
        size = file_path.stat().st_size
        modified = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        return {
            'name': file_path.name,
            'path': str(file_path),
            'lines': lines,
            'size': size,
            'modified': modified.isoformat(),
        }
    except Exception as e:
        return {
            'name': file_path.name,
            'path': str(file_path),
            'lines': 0,
            'size': 0,
            'error': str(e),
        }


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 KB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != 'B' else f"{size_bytes} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def extract_first_paragraph(markdown: str) -> str:
    """
    Extract the first paragraph from markdown content.
    Useful for generating summaries.
    
    Args:
        markdown: Markdown content
        
    Returns:
        First paragraph text
    """
    lines = markdown.strip().split('\n')
    paragraph = []
    started = False
    
    for line in lines:
        # Skip headers and empty lines at start
        if not started:
            if line.startswith('#') or not line.strip():
                continue
            started = True
        
        # End at empty line or new header
        if started:
            if not line.strip() or line.startswith('#'):
                break
            paragraph.append(line.strip())
    
    return ' '.join(paragraph)
