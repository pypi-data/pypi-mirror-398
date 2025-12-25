"""
HiveMind MCP Server - Configuration
Constants and configuration options for the MCP server.
"""

from pathlib import Path
from typing import Dict, List, Set

# ============================================================================
# MCP Server Configuration
# ============================================================================

SERVER_NAME = "hive-mind"
SERVER_VERSION = "1.0.0"

# ============================================================================
# Ignore Patterns
# ============================================================================

IGNORE_PATTERNS: Set[str] = {
    'node_modules',
    '.next',
    '.git',
    'dist',
    'build',
    '__pycache__',
    '.venv',
    'venv',
    'coverage',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    'eggs',
    '*.egg-info',
    '.eggs',
    'htmlcov',
    '.hypothesis',
    '.nox',
}

# Default glob patterns to exclude
DEFAULT_EXCLUDE_PATTERNS: List[str] = [
    'node_modules/**',
    '.next/**',
    '.git/**',
    'dist/**',
    'build/**',
    '__pycache__/**',
    '.venv/**',
    'venv/**',
    'coverage/**',
]

# ============================================================================
# File Extensions and Language Mapping
# ============================================================================

PARSEABLE_EXTENSIONS: Dict[str, str] = {
    '.ts': 'typescript',
    '.tsx': 'tsx',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.py': 'python',
    '.mjs': 'javascript',
    '.cjs': 'javascript',
}

# Extensions to include in file listings (even if not parsed)
INCLUDEABLE_EXTENSIONS: Set[str] = {
    '.ts', '.tsx', '.js', '.jsx', '.py',
    '.json', '.yaml', '.yml',
    '.md', '.mdx',
    '.css', '.scss', '.less',
    '.html', '.vue', '.svelte',
}

# ============================================================================
# Documentation Files
# ============================================================================

HIVEMIND_FILENAME = 'hivemind.md'
FLOWCHART_FILENAME = 'flowchart.mmd'

# ============================================================================
# Anchor Point Configuration
# ============================================================================

ANCHOR_PREFIX = 'anchor://'

# ============================================================================
# Complexity Thresholds
# ============================================================================

COMPLEXITY_LOW = 5
COMPLEXITY_MEDIUM = 10
COMPLEXITY_HIGH = 20

def get_complexity_label(score: int) -> str:
    """Convert complexity score to human-readable label."""
    if score <= COMPLEXITY_LOW:
        return "Low"
    elif score <= COMPLEXITY_MEDIUM:
        return "Medium"
    else:
        return "High"

# ============================================================================
# Tree-sitter Node Types
# ============================================================================

# TypeScript/JavaScript function-like nodes
TS_JS_FUNCTION_NODES = {
    'function_declaration',
    'arrow_function',
    'function_expression',
    'method_definition',
    'generator_function_declaration',
}

# TypeScript/JavaScript import/export nodes
TS_JS_IMPORT_NODES = {
    'import_statement',
    'import_clause',
}

TS_JS_EXPORT_NODES = {
    'export_statement',
    'export_clause',
}

# Python function-like nodes
PY_FUNCTION_NODES = {
    'function_definition',
    'async_function_definition',
}

# Python import nodes
PY_IMPORT_NODES = {
    'import_statement',
    'import_from_statement',
}

# Class definition nodes
TS_JS_CLASS_NODES = {
    'class_declaration',
    'class_expression',
}

PY_CLASS_NODES = {
    'class_definition',
}

# Type definition nodes (TypeScript)
TS_TYPE_NODES = {
    'interface_declaration',
    'type_alias_declaration',
}
