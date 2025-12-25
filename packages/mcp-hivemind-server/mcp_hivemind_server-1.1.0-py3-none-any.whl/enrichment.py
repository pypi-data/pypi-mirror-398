"""
HiveMind MCP Server - Enrichment
Handle AI context integration and optional AI enrichment.
"""

import re
from pathlib import Path
from typing import Dict, Optional, Any, List

from config import HIVEMIND_FILENAME


def merge_contexts(
    structure: Dict[str, Any],
    ai_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Merge dry logic structure with AI context.
    
    Args:
        structure: Parsed structure dictionary from parser
        ai_context: Optional AI-provided context dictionary
        
    Returns:
        Combined context dictionary
    """
    ai_context = ai_context or {}
    
    return {
        'context': ai_context.get('context', ''),
        'user_requirements': ai_context.get('user_requirements', ''),
        'warnings': ai_context.get('warnings', ''),
        'next_steps': ai_context.get('next_steps', ''),
        'how_it_works': ai_context.get('how_it_works', ''),
    }


def preserve_existing_context(dir_path: Path) -> Dict[str, Any]:
    """
    Extract AI context sections from existing hivemind.md.
    
    This allows updates to preserve user-provided context while
    regenerating the structural (dry logic) sections.
    
    Args:
        dir_path: Path to directory containing hivemind.md
        
    Returns:
        Dictionary with preserved AI context sections
    """
    hivemind_path = dir_path / HIVEMIND_FILENAME
    
    context = {
        'context': '',
        'user_requirements': '',
        'warnings': '',
        'next_steps': '',
        'how_it_works': '',
    }
    
    if not hivemind_path.exists():
        return context
    
    try:
        content = hivemind_path.read_text(encoding='utf-8', errors='ignore')
        
        # Split at the separator line
        parts = content.split('---')
        if len(parts) < 2:
            return context
        
        ai_section = parts[0]
        
        # Extract each section
        context['context'] = _extract_section(ai_section, '## 🎯 What This Does')
        context['user_requirements'] = _extract_section(ai_section, '## 👤 User Requirements')
        context['warnings'] = _extract_section(ai_section, '## ⚠️ Important Notes')
        context['next_steps'] = _extract_section(ai_section, '## 🔮 Next Steps')
        context['how_it_works'] = _extract_section(ai_section, '## 💡 How It Works')
        
    except Exception:
        pass
    
    return context


def _extract_section(content: str, header: str) -> str:
    """
    Extract content between a header and the next header.
    
    Args:
        content: Full markdown content
        header: Header to look for
        
    Returns:
        Content of the section (empty string if not found)
    """
    lines = content.split('\n')
    result = []
    in_section = False
    
    for line in lines:
        if line.strip().startswith(header):
            in_section = True
            continue
        elif line.strip().startswith('## ') and in_section:
            break
        elif in_section:
            result.append(line)
    
    # Clean up: remove leading/trailing empty lines
    text = '\n'.join(result).strip()
    return text


def create_ai_enrichment_prompt(structure: Dict[str, Any]) -> str:
    """
    Create a prompt for AI enrichment of documentation.
    
    This prompt can be sent to an AI API to generate context.
    
    Args:
        structure: Parsed structure dictionary
        
    Returns:
        Prompt string for AI enrichment
    """
    files = structure.get('files', [])
    functions = structure.get('all_functions', [])
    imports = structure.get('all_imports', [])
    classes = structure.get('all_classes', [])
    
    # Format file list
    file_list = '\n'.join([f"- {f.get('name')} ({f.get('lines', 0)} lines)" for f in files])
    
    # Format function signatures
    func_list = '\n'.join([
        f"- {f.get('name')}{f.get('params', '()')}: {f.get('return_type', 'void')}"
        for f in functions[:20]  # Limit to 20 functions
    ])
    if len(functions) > 20:
        func_list += f"\n- ...and {len(functions) - 20} more functions"
    
    # Format imports
    import_list = '\n'.join([
        f"- {i.get('module')}"
        for i in imports[:15]
    ])
    
    # Format classes
    class_list = '\n'.join([
        f"- {c.get('name')}" + (f" extends {c.get('extends')}" if c.get('extends') else "")
        for c in classes
    ])
    
    prompt = f"""Analyze this code directory and provide brief documentation.

Directory: {structure.get('name', 'Unknown')}
Path: {structure.get('path', 'Unknown')}

Files:
{file_list or 'None'}

Functions:
{func_list or 'None'}

Classes:
{class_list or 'None'}

Imports:
{import_list or 'None'}

Provide documentation in this EXACT format:

WHAT_THIS_DOES:
[2-3 sentences explaining the primary purpose and role of this directory in the codebase]

HOW_IT_WORKS:
[1 paragraph explaining the key patterns, algorithms, or logic used]

Keep it concise and technical. Focus on the "what" and "how", not the obvious.
"""
    
    return prompt


def parse_ai_enrichment_response(response: str) -> Dict[str, Any]:
    """
    Parse AI enrichment response into context dictionary.
    
    Args:
        response: AI response text
        
    Returns:
        Context dictionary with extracted sections
    """
    context = {
        'context': '',
        'how_it_works': '',
    }
    
    lines = response.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped.startswith('WHAT_THIS_DOES:'):
            if current_section:
                context[current_section] = '\n'.join(current_content).strip()
            current_section = 'context'
            current_content = []
        elif line_stripped.startswith('HOW_IT_WORKS:'):
            if current_section:
                context[current_section] = '\n'.join(current_content).strip()
            current_section = 'how_it_works'
            current_content = []
        elif current_section:
            current_content.append(line)
    
    # Don't forget the last section
    if current_section and current_content:
        context[current_section] = '\n'.join(current_content).strip()
    
    return context


async def enrich_with_ai(
    structure: Dict[str, Any],
    api_key: Optional[str] = None,
    model: str = "claude-3-haiku-20240307"
) -> Dict[str, Any]:
    """
    Call AI API to generate context enrichment.
    
    This is an optional feature that requires an Anthropic API key.
    
    Args:
        structure: Parsed structure dictionary
        api_key: Anthropic API key (optional, uses env var if not provided)
        model: Model to use for enrichment
        
    Returns:
        AI-generated context dictionary
    """
    import os
    
    api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        return {
            'context': '',
            'how_it_works': '',
            'error': 'No API key provided. Set ANTHROPIC_API_KEY environment variable.',
        }
    
    try:
        import httpx
        
        prompt = create_ai_enrichment_prompt(structure)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': api_key,
                    'content-type': 'application/json',
                    'anthropic-version': '2023-06-01',
                },
                json={
                    'model': model,
                    'max_tokens': 500,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ]
                },
                timeout=30.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('content', [{}])[0].get('text', '')
                return parse_ai_enrichment_response(ai_response)
            else:
                return {
                    'context': '',
                    'how_it_works': '',
                    'error': f'API error: {response.status_code}',
                }
                
    except ImportError:
        return {
            'context': '',
            'how_it_works': '',
            'error': 'httpx not installed. Run: pip install httpx',
        }
    except Exception as e:
        return {
            'context': '',
            'how_it_works': '',
            'error': str(e),
        }


def format_ai_context_for_display(ai_context: Dict[str, Any]) -> str:
    """
    Format AI context for human-readable display.
    
    Args:
        ai_context: Context dictionary
        
    Returns:
        Formatted string
    """
    sections = []
    
    if ai_context.get('context'):
        sections.append(f"**What This Does**: {ai_context['context']}")
    
    if ai_context.get('user_requirements'):
        sections.append(f"**User Requirements**: {ai_context['user_requirements']}")
    
    if ai_context.get('warnings'):
        sections.append(f"**Warnings**: {ai_context['warnings']}")
    
    if ai_context.get('next_steps'):
        sections.append(f"**Next Steps**: {ai_context['next_steps']}")
    
    if ai_context.get('how_it_works'):
        sections.append(f"**How It Works**: {ai_context['how_it_works']}")
    
    return '\n\n'.join(sections) if sections else '_No AI context provided_'
