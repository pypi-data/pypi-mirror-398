"""
HiveMind MCP Server
Main MCP server entry point that exposes tools to AI assistants.

Tools:
- document_current_work: Real-time documentation while building
- build_hive: Document existing codebase
- navigate_to: Load context from anchor point
- find_function: Search for function across codebase
- trace_usage: Find dependencies/dependents
- update_hivemind: Update docs when code changes
"""

import asyncio
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from config import SERVER_NAME, DEFAULT_EXCLUDE_PATTERNS
from parser import analyze_directory
from generator import generate_and_write, generate_hivemind, generate_flowchart, write_files
from enrichment import merge_contexts, preserve_existing_context, enrich_with_ai
from navigator import (
    load_hivemind,
    load_with_context,
    find_function,
    trace_connections,
    format_trace_result,
    get_navigation_context,
)
from utils import normalize_path, should_ignore


# Initialize MCP server
app = Server(SERVER_NAME)


# ============================================================================
# Tool Definitions
# ============================================================================

TOOLS = [
    Tool(
        name="document_current_work",
        description="Document code being built in real-time. AI calls this while actively creating code to preserve context and user requirements.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to directory being documented"
                },
                "context": {
                    "type": "string",
                    "description": "AI's explanation of what this code does (2-3 sentences)"
                },
                "user_requirements": {
                    "type": "string",
                    "description": "Specific user requirements, constraints, or preferences mentioned during development"
                },
                "warnings": {
                    "type": "string",
                    "description": "Important warnings, gotchas, or things to be careful about"
                },
                "next_steps": {
                    "type": "string",
                    "description": "Planned next steps, TODOs, or future enhancements"
                },
                "how_it_works": {
                    "type": "string",
                    "description": "Brief explanation of key patterns, algorithms, or logic"
                }
            },
            "required": ["path"]
        }
    ),
    Tool(
        name="build_hive",
        description="Generate documentation for entire existing codebase. Walks directory tree and creates hivemind.md and flowchart.mmd at each level.",
        inputSchema={
            "type": "object",
            "properties": {
                "root_path": {
                    "type": "string",
                    "description": "Root directory of codebase to document"
                },
                "exclude_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Glob patterns to exclude (e.g., node_modules/**, .git/**)",
                    "default": ["node_modules/**", ".next/**", ".git/**", "dist/**"]
                },
                "enrich_with_ai": {
                    "type": "boolean",
                    "description": "Whether to use AI API for context enrichment (slower but richer)",
                    "default": False
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum directory depth to process (-1 for unlimited)",
                    "default": -1
                }
            },
            "required": ["root_path"]
        }
    ),
    Tool(
        name="navigate_to",
        description="Load complete context for a specific directory using its anchor point. Returns the hivemind.md content plus optional parent/children summaries.",
        inputSchema={
            "type": "object",
            "properties": {
                "anchor": {
                    "type": "string",
                    "description": "Anchor point in format: anchor://path/to/directory"
                },
                "include_parent": {
                    "type": "boolean",
                    "description": "Include parent directory context for broader understanding",
                    "default": True
                },
                "include_children_summary": {
                    "type": "boolean",
                    "description": "Include brief summary of child directories",
                    "default": True
                }
            },
            "required": ["anchor"]
        }
    ),
    Tool(
        name="find_function",
        description="Search entire hive for a specific function by name. Returns all locations where the function is defined.",
        inputSchema={
            "type": "object",
            "properties": {
                "function_name": {
                    "type": "string",
                    "description": "Name of function to find"
                },
                "root_path": {
                    "type": "string",
                    "description": "Root directory to search from (defaults to current directory)"
                },
                "return_context": {
                    "type": "boolean",
                    "description": "Return full context (function signature, location, description) or just anchor points",
                    "default": False
                }
            },
            "required": ["function_name"]
        }
    ),
    Tool(
        name="trace_usage",
        description="Trace dependencies and dependents of a module. Shows what it uses (upstream) and what uses it (downstream).",
        inputSchema={
            "type": "object",
            "properties": {
                "anchor": {
                    "type": "string",
                    "description": "Anchor point to trace from"
                },
                "direction": {
                    "type": "string",
                    "enum": ["upstream", "downstream", "both"],
                    "description": "upstream=dependencies, downstream=dependents, both=full graph",
                    "default": "both"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "How many levels deep to trace",
                    "default": 2
                }
            },
            "required": ["anchor"]
        }
    ),
    Tool(
        name="update_hivemind",
        description="Update documentation when code changes. Re-extracts structure but preserves AI context from existing documentation.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path that changed"
                },
                "preserve_ai_context": {
                    "type": "boolean",
                    "description": "Keep existing AI-generated sections (recommended)",
                    "default": True
                }
            },
            "required": ["path"]
        }
    ),
    # =========================================================================
    # GUIDED HIVE BUILD TOOLS
    # These tools create a cooperative workflow where MCP guides the AI
    # to provide context for each directory in the codebase.
    # =========================================================================
    Tool(
        name="start_hive_build",
        description="""Start a GUIDED hive build process. This discovers all directories in the codebase and returns the FIRST directory for YOU (the AI) to document.

WORKFLOW:
1. You call start_hive_build with root_path
2. MCP returns the first directory with its structure (files, functions, imports)
3. YOU read the actual code files and understand what the directory does
4. YOU call continue_hive_build with your context (what it does, how it works, etc.)
5. MCP writes hivemind.md with both structure AND your context, then returns the NEXT directory
6. Repeat until all directories are documented

This makes YOU the source of intelligent documentation, not an external API.""",
        inputSchema={
            "type": "object",
            "properties": {
                "root_path": {
                    "type": "string",
                    "description": "Root directory of codebase to document"
                },
                "exclude_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Glob patterns to exclude",
                    "default": ["node_modules/**", ".next/**", ".git/**", "dist/**", "__pycache__/**", ".venv/**"]
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum directory depth (-1 for unlimited)",
                    "default": -1
                }
            },
            "required": ["root_path"]
        }
    ),
    Tool(
        name="continue_hive_build",
        description="""Continue the guided hive build by providing YOUR context for the current directory.

After receiving a directory from start_hive_build or a previous continue_hive_build:
1. Read the code files in that directory  
2. Understand what the code does
3. Call this tool with your context

MCP will:
1. Write hivemind.md with structure + YOUR context
2. Return the NEXT directory for you to document (or signal completion)

Keep calling this until MCP says the build is complete.""",
        inputSchema={
            "type": "object",
            "properties": {
                "context": {
                    "type": "string",
                    "description": "YOUR explanation of what this directory/code does (2-3 sentences)"
                },
                "how_it_works": {
                    "type": "string",
                    "description": "YOUR explanation of the key logic, patterns, or algorithms"
                },
                "user_requirements": {
                    "type": "string",
                    "description": "Any user requirements or constraints you're aware of"
                },
                "warnings": {
                    "type": "string",
                    "description": "Important warnings or gotchas you noticed"
                },
                "next_steps": {
                    "type": "string",
                    "description": "Suggested next steps or TODOs"
                }
            },
            "required": ["context"]
        }
    ),
    Tool(
        name="get_hive_status",
        description="Get the status of the current guided hive build. Shows progress and which directory is next.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
]

# ============================================================================
# Guided Hive Build State
# Stores the queue of directories and current progress
# ============================================================================
_hive_build_state = {
    'active': False,
    'root_path': None,
    'queue': [],           # List of directory paths to process
    'current_index': 0,    # Index of current directory being documented
    'current_structure': None,  # Parsed structure of current directory
    'completed': [],       # List of completed directory paths
    'stats': {
        'directories': 0,
        'files': 0,
        'functions': 0,
        'lines': 0,
    }
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return list of all available tools."""
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool invocations."""
    try:
        if name == "document_current_work":
            return await handle_document_current_work(arguments)
        elif name == "build_hive":
            return await handle_build_hive(arguments)
        elif name == "navigate_to":
            return await handle_navigate_to(arguments)
        elif name == "find_function":
            return await handle_find_function(arguments)
        elif name == "trace_usage":
            return await handle_trace_usage(arguments)
        elif name == "update_hivemind":
            return await handle_update_hivemind(arguments)
        # Guided Hive Build tools
        elif name == "start_hive_build":
            return await handle_start_hive_build(arguments)
        elif name == "continue_hive_build":
            return await handle_continue_hive_build(arguments)
        elif name == "get_hive_status":
            return await handle_get_hive_status(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


# ============================================================================
# Tool Handlers
# ============================================================================

async def handle_document_current_work(args: dict) -> list[TextContent]:
    """
    Handle document_current_work tool.
    
    Real-time documentation while building code.
    """
    path = args.get("path")
    if not path:
        return [TextContent(type="text", text="Error: 'path' is required")]
    
    dir_path = normalize_path(path)
    
    if not dir_path.exists():
        return [TextContent(type="text", text=f"Error: Directory does not exist: {dir_path}")]
    
    # Parse directory structure
    structure = analyze_directory(dir_path)
    
    # Create AI context from arguments
    ai_context = {
        'context': args.get('context', ''),
        'user_requirements': args.get('user_requirements', ''),
        'warnings': args.get('warnings', ''),
        'next_steps': args.get('next_steps', ''),
        'how_it_works': args.get('how_it_works', ''),
    }
    
    # Generate and write documentation
    result = await generate_and_write(structure, ai_context)
    
    # Build response
    if result.get('success'):
        messages = [
            f"Successfully documented {dir_path.name}",
            f"   - Parsed {structure['metrics']['total_files']} files ({structure['metrics']['total_lines']} lines)",
            f"   - Found {structure['metrics']['total_functions']} functions",
            f"   - Generated hivemind.md ({result['hivemind_lines']} lines)",
            f"   - Generated flowchart.mmd ({result['flowchart_lines']} lines)",
        ]
        return [TextContent(type="text", text='\n'.join(messages))]
    else:
        errors = '\n'.join(result.get('errors', ['Unknown error']))
        return [TextContent(type="text", text=f"Error documenting {dir_path.name}:\n{errors}")]


async def handle_build_hive(args: dict) -> list[TextContent]:
    """
    Handle build_hive tool.
    
    Document entire existing codebase.
    """
    root_path = args.get("root_path")
    if not root_path:
        return [TextContent(type="text", text="Error: 'root_path' is required")]
    
    root = normalize_path(root_path)
    
    if not root.exists():
        return [TextContent(type="text", text=f"Error: Directory does not exist: {root}")]
    
    exclude_patterns = set(args.get("exclude_patterns", DEFAULT_EXCLUDE_PATTERNS))
    use_ai = args.get("enrich_with_ai", False)
    max_depth = args.get("max_depth", -1)
    
    # Statistics
    stats = {
        'directories': 0,
        'files': 0,
        'functions': 0,
        'lines': 0,
        'errors': [],
    }
    
    messages = [f"🔍 Scanning {root}..."]
    
    # Walk directory tree
    def should_process(dir_path: Path, current_depth: int) -> bool:
        if max_depth >= 0 and current_depth > max_depth:
            return False
        if should_ignore(dir_path):
            return False
        # Check exclude patterns
        for pattern in exclude_patterns:
            if dir_path.match(pattern.rstrip('/**').rstrip('/*')):
                return False
        return True
    
    async def process_directory(dir_path: Path, depth: int = 0):
        if not should_process(dir_path, depth):
            return
        
        try:
            # Parse structure
            structure = analyze_directory(dir_path, root)
            
            # Optionally enrich with AI
            ai_context = {}
            if use_ai:
                ai_context = await enrich_with_ai(structure)
            
            # Generate and write
            result = await generate_and_write(structure, ai_context)
            
            if result.get('success'):
                stats['directories'] += 1
                stats['files'] += structure['metrics']['total_files']
                stats['functions'] += structure['metrics']['total_functions']
                stats['lines'] += structure['metrics']['total_lines']
            else:
                stats['errors'].extend(result.get('errors', []))
            
            # Process children
            for child in structure.get('children', []):
                child_path = Path(child)
                if child_path.is_dir():
                    await process_directory(child_path, depth + 1)
                    
        except Exception as e:
            stats['errors'].append(f"{dir_path}: {str(e)}")
    
    # Start processing
    await process_directory(root)
    
    # Build response
    messages.extend([
        f"Documentation complete!",
        f"",
        f"Summary:",
        f"   - Documented {stats['directories']} directories",
        f"   - Parsed {stats['files']} files",
        f"   - Found {stats['functions']} functions",
        f"   - Total lines: {stats['lines']}",
        f"   - Generated {stats['directories'] * 2} files (hivemind.md + flowchart.mmd)",
    ])
    
    if stats['errors']:
        messages.append(f"\nErrors ({len(stats['errors'])}):")
        for error in stats['errors'][:5]:
            messages.append(f"   - {error}")
        if len(stats['errors']) > 5:
            messages.append(f"   - ...and {len(stats['errors']) - 5} more")
    
    return [TextContent(type="text", text='\n'.join(messages))]


async def handle_navigate_to(args: dict) -> list[TextContent]:
    """
    Handle navigate_to tool.
    
    Load context from anchor point.
    """
    anchor = args.get("anchor")
    if not anchor:
        return [TextContent(type="text", text="Error: 'anchor' is required")]
    
    include_parent = args.get("include_parent", True)
    include_children = args.get("include_children_summary", True)
    
    result = await load_with_context(
        anchor,
        include_parent=include_parent,
        include_children_summary=include_children,
    )
    
    if result.get('error'):
        return [TextContent(type="text", text=f"Error: {result['error']}")]
    
    if not result.get('current'):
        return [TextContent(type="text", text=f"No documentation found at {anchor}. Run build_hive first.")]
    
    # Format response
    sections = []
    
    if result.get('parent') and include_parent:
        parent = result['parent']
        sections.append("=== PARENT CONTEXT ===")
        sections.append(f"# {parent['name']}")
        sections.append(parent.get('summary', '_No summary_'))
        sections.append("")
    
    sections.append("=== CURRENT CONTEXT ===")
    sections.append(result['current'])
    
    if result.get('children') and include_children:
        sections.append("")
        sections.append("=== CHILDREN ===")
        for child in result['children']:
            summary = child.get('summary', '_No summary_')[:80]
            sections.append(f"- **{child['name']}**: {summary}...")
    
    return [TextContent(type="text", text='\n'.join(sections))]


async def handle_find_function(args: dict) -> list[TextContent]:
    """
    Handle find_function tool.
    
    Search for function across codebase.
    """
    function_name = args.get("function_name")
    if not function_name:
        return [TextContent(type="text", text="Error: 'function_name' is required")]
    
    root_path = normalize_path(args.get("root_path", "."))
    return_context = args.get("return_context", False)
    
    results = await find_function(root_path, function_name, return_context)
    
    if not results:
        return [TextContent(type="text", text=f"No definitions found for '{function_name}'")]
    
    # Format response
    messages = [f"Found {len(results)} location(s) for '{function_name}':", ""]
    
    for i, result in enumerate(results, 1):
        anchor = result.get('anchor', 'Unknown')
        messages.append(f"{i}. {anchor}")
        
        if return_context:
            if result.get('signature'):
                messages.append(f"   `{result['signature']}`")
            if result.get('line'):
                messages.append(f"   - Line: {result['line']}")
        
        messages.append("")
    
    return [TextContent(type="text", text='\n'.join(messages))]


async def handle_trace_usage(args: dict) -> list[TextContent]:
    """
    Handle trace_usage tool.
    
    Trace dependencies and dependents.
    """
    anchor = args.get("anchor")
    if not anchor:
        return [TextContent(type="text", text="Error: 'anchor' is required")]
    
    direction = args.get("direction", "both")
    max_depth = args.get("max_depth", 2)
    
    result = await trace_connections(anchor, direction, max_depth)
    
    if result.get('error'):
        return [TextContent(type="text", text=f"Error: {result['error']}")]
    
    # Format response
    formatted = format_trace_result(result)
    
    messages = [
        f"Dependency trace for {anchor}",
        f"   Direction: {direction}, Max depth: {max_depth}",
        "",
        formatted,
    ]
    
    return [TextContent(type="text", text='\n'.join(messages))]


async def handle_update_hivemind(args: dict) -> list[TextContent]:
    """
    Handle update_hivemind tool.
    
    Update docs when code changes, preserving AI context.
    """
    path = args.get("path")
    if not path:
        return [TextContent(type="text", text="Error: 'path' is required")]
    
    dir_path = normalize_path(path)
    
    if not dir_path.exists():
        return [TextContent(type="text", text=f"Error: Directory does not exist: {dir_path}")]
    
    preserve = args.get("preserve_ai_context", True)
    
    # Optionally preserve existing AI context
    ai_context = {}
    if preserve:
        ai_context = preserve_existing_context(dir_path)
    
    # Re-parse directory
    structure = analyze_directory(dir_path)
    
    # Generate and write
    result = await generate_and_write(structure, ai_context)
    
    if result.get('success'):
        preserved_info = ""
        if preserve and any(ai_context.values()):
            preserved_sections = [k for k, v in ai_context.items() if v]
            preserved_info = f"\n   - Preserved AI context: {', '.join(preserved_sections)}"

        messages = [
            f"Updated documentation for {dir_path.name}",
            f"   - Parsed {structure['metrics']['total_files']} files",
            f"   - Found {structure['metrics']['total_functions']} functions",
            preserved_info,
        ]
        return [TextContent(type="text", text='\n'.join(messages))]
    else:
        errors = '\n'.join(result.get('errors', ['Unknown error']))
        return [TextContent(type="text", text=f"Error updating {dir_path.name}:\n{errors}")]


# ============================================================================
# Guided Hive Build Handlers
# ============================================================================

async def handle_start_hive_build(args: dict) -> list[TextContent]:
    """
    Start a guided hive build.
    
    Discovers all directories and returns the first one for the AI to document.
    """
    global _hive_build_state
    
    root_path = args.get("root_path")
    if not root_path:
        return [TextContent(type="text", text="Error: 'root_path' is required")]
    
    root = normalize_path(root_path)
    
    if not root.exists():
        return [TextContent(type="text", text=f"Error: Directory does not exist: {root}")]
    
    exclude_patterns = set(args.get("exclude_patterns", DEFAULT_EXCLUDE_PATTERNS))
    max_depth = args.get("max_depth", -1)
    
    # Discover all directories
    queue = []
    
    def discover(dir_path: Path, depth: int = 0):
        if max_depth >= 0 and depth > max_depth:
            return
        if should_ignore(dir_path):
            return
        for pattern in exclude_patterns:
            if dir_path.match(pattern.rstrip('/**').rstrip('/*')):
                return
        
        queue.append(str(dir_path))
        
        try:
            for child in dir_path.iterdir():
                if child.is_dir():
                    discover(child, depth + 1)
        except PermissionError:
            pass
    
    discover(root)
    
    if not queue:
        return [TextContent(type="text", text="No directories found to document.")]
    
    # Initialize state
    _hive_build_state = {
        'active': True,
        'root_path': str(root),
        'queue': queue,
        'current_index': 0,
        'current_structure': None,
        'completed': [],
        'stats': {'directories': 0, 'files': 0, 'functions': 0, 'lines': 0}
    }
    
    # Parse first directory
    first_dir = Path(queue[0])
    structure = analyze_directory(first_dir, root)
    _hive_build_state['current_structure'] = structure
    
    # Format the response - tell AI to read and provide context
    files_list = '\n'.join([f"   - {f['name']} ({f.get('lines', 0)} lines)" for f in structure.get('files', [])[:10]])
    funcs_list = '\n'.join([f"   - {f['name']}{f.get('params', '()')}" for f in structure.get('all_functions', [])[:10]])
    
    messages = [
        f"GUIDED HIVE BUILD STARTED",
        f"",
        f"Discovered {len(queue)} directories to document",
        f"",
        f"===============================================================",
        f"DIRECTORY 1/{len(queue)}: {first_dir.name}",
        f"   Path: {first_dir}",
        f"===============================================================",
        f"",
        f"Files ({len(structure.get('files', []))}):",
        files_list or "   (none)",
        f"",
        f"Functions ({len(structure.get('all_functions', []))}):",
        funcs_list or "   (none)",
        f"",
        f"===============================================================",
        f"YOUR TASK:",
        f"1. Read the code files in this directory",
        f"2. Understand what the code does",
        f"3. Call continue_hive_build with your context:",
        f"   - context: What this directory/code does (2-3 sentences)",
        f"   - how_it_works: Key patterns, algorithms, or logic",
        f"   - warnings: Any gotchas or issues you notice",
        f"   - next_steps: Suggested TODOs (optional)",
        f"===============================================================",
    ]
    
    return [TextContent(type="text", text='\n'.join(messages))]


async def handle_continue_hive_build(args: dict) -> list[TextContent]:
    """
    Continue guided hive build with AI-provided context.
    
    Writes hivemind.md for current directory, then returns next directory.
    """
    global _hive_build_state
    
    if not _hive_build_state.get('active'):
        return [TextContent(type="text", text="Error: No active hive build. Call start_hive_build first.")]
    
    context = args.get("context", "")
    if not context:
        return [TextContent(type="text", text="Error: 'context' is required. Explain what this directory does.")]
    
    # Get current state
    queue = _hive_build_state['queue']
    current_index = _hive_build_state['current_index']
    structure = _hive_build_state['current_structure']
    root = Path(_hive_build_state['root_path'])
    
    if current_index >= len(queue):
        return [TextContent(type="text", text="Build already complete! No more directories.")]
    
    current_dir = Path(queue[current_index])
    
    # Create AI context from arguments
    ai_context = {
        'context': context,
        'how_it_works': args.get('how_it_works', ''),
        'user_requirements': args.get('user_requirements', ''),
        'warnings': args.get('warnings', ''),
        'next_steps': args.get('next_steps', ''),
    }
    
    # Generate and write documentation
    result = await generate_and_write(structure, ai_context)
    
    # Update stats
    if result.get('success'):
        _hive_build_state['stats']['directories'] += 1
        _hive_build_state['stats']['files'] += structure['metrics']['total_files']
        _hive_build_state['stats']['functions'] += structure['metrics']['total_functions']
        _hive_build_state['stats']['lines'] += structure['metrics']['total_lines']
        _hive_build_state['completed'].append(str(current_dir))
    
    # Move to next directory
    _hive_build_state['current_index'] += 1
    next_index = _hive_build_state['current_index']
    
    # Check if we're done
    if next_index >= len(queue):
        _hive_build_state['active'] = False
        stats = _hive_build_state['stats']
        
        messages = [
            f"HIVE BUILD COMPLETE!",
            f"",
            f"Summary:",
            f"   - Documented {stats['directories']} directories",
            f"   - Parsed {stats['files']} files",
            f"   - Found {stats['functions']} functions",
            f"   - Total lines: {stats['lines']}",
            f"   - Generated {stats['directories'] * 2} files (hivemind.md + flowchart.mmd)",
            f"",
            f"All directories now have AI-enriched documentation!",
            f"",
            f"You can now use navigate_to, find_function, and trace_usage to explore.",
        ]
        return [TextContent(type="text", text='\n'.join(messages))]
    
    # Parse next directory
    next_dir = Path(queue[next_index])
    next_structure = analyze_directory(next_dir, root)
    _hive_build_state['current_structure'] = next_structure
    
    # Format response for next directory
    files_list = '\n'.join([f"   - {f['name']} ({f.get('lines', 0)} lines)" for f in next_structure.get('files', [])[:10]])
    funcs_list = '\n'.join([f"   - {f['name']}{f.get('params', '()')}" for f in next_structure.get('all_functions', [])[:10]])
    
    messages = [
        f"Documented: {current_dir.name}",
        f"",
        f"===============================================================",
        f"DIRECTORY {next_index + 1}/{len(queue)}: {next_dir.name}",
        f"   Path: {next_dir}",
        f"===============================================================",
        f"",
        f"Files ({len(next_structure.get('files', []))}):",
        files_list or "   (none)",
        f"",
        f"Functions ({len(next_structure.get('all_functions', []))}):",
        funcs_list or "   (none)",
        f"",
        f"===============================================================",
        f"YOUR TASK: Read the code, then call continue_hive_build",
        f"===============================================================",
    ]
    
    return [TextContent(type="text", text='\n'.join(messages))]


async def handle_get_hive_status(args: dict) -> list[TextContent]:
    """
    Get status of current guided hive build.
    """
    if not _hive_build_state.get('active'):
        return [TextContent(type="text", text="No active hive build. Call start_hive_build to begin.")]
    
    queue = _hive_build_state['queue']
    current_index = _hive_build_state['current_index']
    completed = _hive_build_state['completed']
    stats = _hive_build_state['stats']
    
    current_dir = queue[current_index] if current_index < len(queue) else "Complete"
    
    messages = [
        f"HIVE BUILD STATUS",
        f"",
        f"Progress: {current_index}/{len(queue)} directories",
        f"Current: {Path(current_dir).name if current_index < len(queue) else 'Done'}",
        f"",
        f"Stats so far:",
        f"   - Directories documented: {stats['directories']}",
        f"   - Files parsed: {stats['files']}",
        f"   - Functions found: {stats['functions']}",
        f"   - Lines processed: {stats['lines']}",
        f"",
        f"Remaining: {len(queue) - current_index} directories",
    ]
    
    return [TextContent(type="text", text='\n'.join(messages))]


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Start MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
