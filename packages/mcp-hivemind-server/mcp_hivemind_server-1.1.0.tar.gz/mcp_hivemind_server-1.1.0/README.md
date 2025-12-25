# Hive Mind MCP Server

**Intelligent documentation system for codebases that creates living documentation as you build.**

Hive Mind is an MCP (Model Context Protocol) server that automatically generates `hivemind.md` and `flowchart.mmd` at every directory level, creating a navigable spider-web of documentation that:

- Works in **real-time** as code is built
- Can **retroactively** document existing codebases
- Preserves **user requirements** and architectural decisions
- Enables **AI navigation** via anchor points
- Works with any context window size (8k to 200k tokens)

## Installation

### Quick Start (Recommended)

You can run the server directly using `uvx` (no installation required):

```json
{
  "mcpServers": {
    "hive-mind": {
      "command": "uvx",
      "args": ["mcp-hivemind-server"]
    }
  }
}
```

### Install via pip

```bash
pip install mcp-hivemind-server
```

### Install from Source (Development)

```bash
# Clone the repository
git clone https://github.com/Jahanzaib-Kaleem/hive-mind-mcp.git
cd hive-mind-mcp

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Requirements

- Python 3.11 or higher
- Dependencies: `mcp`, `tree-sitter`, `tree-sitter-languages`, `aiofiles`, `pyyaml`

## Configuration

### For Antigravity / Claude Desktop

Edit your MCP configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Linux**: `~/.config/claude/claude_desktop_config.json`

**Option 1: Using `uvx` (Easiest)**
```json
{
  "mcpServers": {
    "hive-mind": {
      "command": "uvx",
      "args": ["mcp-hivemind-server"]
    }
  }
}
```

**Option 2: Using pip installation**
```json
{
  "mcpServers": {
    "hive-mind": {
      "command": "hive-mind",
      "args": []
    }
  }
}
```

**Option 3: Using Source Code**
```json
{
  "mcpServers": {
    "hive-mind": {
      "command": "python",
      "args": ["C:/path/to/hive-mind-mcp/server.py"]
    }
  }
}
```

### For Cursor

1. Open Cursor Settings
2. Navigate to **Features → MCP Servers**
3. Add new server:
   - **Name**: `hive-mind`
   - **Type**: `stdio`
   - **Command**: `uvx`
   - **Args**: `mcp-hivemind-server`

## Usage

### Real-time Documentation

While coding, ask your AI assistant:

> "Document this code as we build it"

The AI will call `document_current_work` to capture:
- Code structure (functions, imports, exports)
- User requirements and constraints
- Warnings and gotchas
- Next steps and TODOs
- How the code works

### Retroactive Documentation

For existing codebases, ask:

> "Document my entire codebase with hive-mind"

The AI will call `build_hive` to:
- Walk the entire directory tree
- Parse all code files
- Generate documentation at each level
- Create connection graphs

### Guided Hive Build (Recommended)

For **AI-enriched** documentation where YOU provide the context:

> "Start a guided hive build on my codebase"

**How it works:**
1. MCP discovers all directories
2. For each directory, MCP shows you the structure (files, functions)
3. **YOU read the actual code** and understand what it does
4. YOU call `continue_hive_build` with your explanation
5. MCP writes `hivemind.md` with both structure AND your context
6. Repeat until all directories are documented

This creates documentation with **intelligent context from the AI** (you!), not just dry parsing.

### Navigation

Ask AI to navigate your codebase:

> "Show me the auth system context"  
> "Find the validateSession function"  
> "Trace what uses the database module"

## Tools

### Core Tools
| Tool | Description |
|------|-------------|
| `document_current_work` | Real-time documentation while building code |
| `build_hive` | Auto-document entire codebase (structure only) |
| `navigate_to` | Load context from anchor point |
| `find_function` | Search for function across codebase |
| `trace_usage` | Find dependencies and dependents |
| `update_hivemind` | Update docs when code changes |

### Guided Build Tools
| Tool | Description |
|------|-------------|
| `start_hive_build` | Start guided build, returns first directory for YOU to document |
| `continue_hive_build` | Submit YOUR context, get next directory |
| `get_hive_status` | Check progress of guided build |

## Generated Files

### hivemind.md

Each directory gets a `hivemind.md` file containing:

**AI Context Sections** (above the line):
- What This Does - Purpose and role
- User Requirements - Constraints and preferences
- Important Notes - Warnings and gotchas
- Next Steps - TODOs and planned work
- How It Works - Key patterns and logic

**Dry Logic Sections** (below the line):
- Files at This Level
- Functions Defined
- Dependencies
- Exports
- Connections
- Navigation
- Metrics

### flowchart.mmd

Mermaid diagram showing:
- Current directory (purple center node)
- Parent directory (gray)
- Child directories (green)
- Upstream dependencies (orange)
- Downstream dependents (cyan)

## Anchor Points

Navigate using anchor points in format: `anchor://path/to/directory`

Example:
```
anchor://project/src/components/auth
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_parser.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Project Structure

```
hive-mind-mcp/
├── server.py              # Main MCP server entry point
├── parser.py              # Code structure extraction (tree-sitter)
├── generator.py           # Markdown/Mermaid generation
├── enrichment.py          # AI context integration
├── navigator.py           # Anchor point navigation
├── config.py              # Configuration constants
├── utils.py               # Helper functions
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── .gitignore
└── tests/
    ├── test_parser.py
    ├── test_generator.py
    └── test_integration.py
```

## Supported Languages

- TypeScript (`.ts`, `.tsx`)
- JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`)
- Python (`.py`)

## Optional AI Enrichment

Set `ANTHROPIC_API_KEY` environment variable to enable automatic AI-generated context:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

Then use `build_hive` with `enrich_with_ai: true`.

## License

MIT
