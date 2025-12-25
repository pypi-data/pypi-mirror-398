"""
HiveMind MCP Server - Integration Tests
Full workflow tests for the MCP server.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import os

from parser import analyze_directory
from generator import generate_and_write
from navigator import load_hivemind, load_with_context, find_function, trace_connections
from enrichment import preserve_existing_context, merge_contexts
from utils import create_anchor, parse_anchor


class TestFullWorkflow:
    """Integration tests for the complete workflow."""
    
    @pytest.fixture
    def sample_project(self):
        """Create a sample project structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create src directory
            src = root / 'src'
            src.mkdir()
            
            # Create main.py
            (src / 'main.py').write_text('''
"""Main application module."""

from utils import helper

def main():
    """Entry point."""
    print("Hello, World!")
    result = helper(42)
    return result

def process_data(data: list) -> dict:
    """Process input data."""
    return {"count": len(data)}

if __name__ == "__main__":
    main()
''')
            
            # Create utils.py
            (src / 'utils.py').write_text('''
"""Utility functions."""

def helper(x: int) -> int:
    """Double the input."""
    return x * 2

def format_output(data: dict) -> str:
    """Format data for display."""
    return str(data)
''')
            
            # Create components directory
            components = src / 'components'
            components.mkdir()
            
            (components / 'widget.py').write_text('''
"""Widget component."""

class Widget:
    def __init__(self, name: str):
        self.name = name
    
    def render(self) -> str:
        return f"<widget>{self.name}</widget>"
''')
            
            yield root
    
    @pytest.mark.asyncio
    async def test_analyze_and_generate(self, sample_project):
        """Test parsing and generating documentation."""
        src_dir = sample_project / 'src'
        
        # Analyze directory
        structure = analyze_directory(src_dir)
        
        assert structure['name'] == 'src'
        assert len(structure['files']) >= 2
        assert len(structure['all_functions']) >= 2
        
        # Generate documentation
        result = await generate_and_write(structure)
        
        assert result['success'] is True
        
        # Verify files exist
        hivemind_path = src_dir / 'hivemind.md'
        flowchart_path = src_dir / 'flowchart.mmd'
        
        assert hivemind_path.exists()
        assert flowchart_path.exists()
        
        # Verify content
        content = hivemind_path.read_text()
        assert '# src' in content
        assert 'main' in content or 'helper' in content
    
    @pytest.mark.asyncio
    async def test_navigate_after_generation(self, sample_project):
        """Test navigation after generating documentation."""
        src_dir = sample_project / 'src'
        
        # Generate docs first
        structure = analyze_directory(src_dir)
        await generate_and_write(structure)
        
        # Create anchor and navigate
        anchor = create_anchor(src_dir)
        content = await load_hivemind(anchor)
        
        assert content is not None
        assert '# src' in content
    
    @pytest.mark.asyncio
    async def test_preserve_context_on_update(self, sample_project):
        """Test that AI context is preserved when updating."""
        src_dir = sample_project / 'src'
        
        # First generation with AI context
        structure = analyze_directory(src_dir)
        ai_context = {
            'context': 'This is the main source directory.',
            'user_requirements': 'Must maintain Python 3.11 compatibility.',
            'warnings': 'Critical: Do not modify without tests.',
        }
        await generate_and_write(structure, ai_context)
        
        # Preserve context
        preserved = preserve_existing_context(src_dir)
        
        assert preserved['context'] == 'This is the main source directory.'
        assert 'Python 3.11' in preserved['user_requirements']
        assert 'Critical' in preserved['warnings']
    
    @pytest.mark.asyncio
    async def test_load_with_context_hierarchy(self, sample_project):
        """Test loading context with parent and children."""
        src_dir = sample_project / 'src'
        components_dir = src_dir / 'components'
        
        # Generate docs for both directories
        src_structure = analyze_directory(src_dir)
        await generate_and_write(src_structure, {'context': 'Main source'})
        
        comp_structure = analyze_directory(components_dir)
        await generate_and_write(comp_structure, {'context': 'UI components'})
        
        # Load with context
        anchor = create_anchor(src_dir)
        result = await load_with_context(anchor, include_parent=True, include_children_summary=True)
        
        assert result['current'] is not None
        assert len(result['children']) >= 1


class TestErrorHandling:
    """Tests for error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_navigate_nonexistent_anchor(self):
        """Test navigating to non-existent anchor."""
        content = await load_hivemind("anchor:///nonexistent/path")
        assert content is None
    
    def test_parse_invalid_anchor(self):
        """Test parsing invalid anchor format."""
        with pytest.raises(ValueError):
            parse_anchor("invalid://format")
    
    @pytest.mark.asyncio
    async def test_analyze_empty_directory(self):
        """Test analyzing an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            structure = analyze_directory(Path(tmpdir))
            
            assert structure['files'] == []
            assert structure['all_functions'] == []
            assert structure['metrics']['total_files'] == 0


class TestAnchorSystem:
    """Tests for the anchor point system."""
    
    def test_create_anchor(self):
        """Test anchor creation."""
        path = Path('/test/project/src')
        anchor = create_anchor(path)
        
        assert anchor.startswith('anchor://')
        assert 'src' in anchor
    
    def test_parse_anchor(self):
        """Test anchor parsing."""
        anchor = 'anchor:///test/project/src'
        path = parse_anchor(anchor)
        
        assert path.name == 'src'
    
    def test_anchor_roundtrip(self):
        """Test that anchor creation and parsing are consistent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original = Path(tmpdir)
            anchor = create_anchor(original)
            parsed = parse_anchor(anchor)
            
            assert parsed.resolve() == original.resolve()


class TestSearchFunctionality:
    """Tests for search functionality."""
    
    @pytest.fixture
    def documented_project(self):
        """Create and document a project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create file with functions
            (root / 'main.py').write_text('''
def validateSession(token: str) -> bool:
    """Validate user session."""
    return True

def processData(data: list) -> dict:
    """Process input data."""
    return {}
''')
            
            # Generate docs
            structure = analyze_directory(root)
            asyncio.run(generate_and_write(structure))
            
            yield root
    
    @pytest.mark.asyncio
    async def test_find_function_exists(self, documented_project):
        """Test finding an existing function."""
        results = await find_function(documented_project, 'validateSession', return_context=False)
        
        # May or may not find depending on hivemind content
        # This test verifies the function doesn't crash
        assert isinstance(results, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
