"""
HiveMind MCP Server - Generator Tests
Unit tests for markdown and Mermaid generation.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile

from generator import generate_hivemind, generate_flowchart, write_files, generate_and_write


class TestGenerateHivemind:
    """Tests for hivemind.md generation."""
    
    @pytest.fixture
    def sample_structure(self):
        """Sample structure dictionary for testing."""
        return {
            'path': '/test/project/src',
            'name': 'src',
            'files': [
                {'name': 'index.ts', 'path': '/test/project/src/index.ts', 'lines': 100, 'size': 2500},
                {'name': 'utils.ts', 'path': '/test/project/src/utils.ts', 'lines': 50, 'size': 1200},
            ],
            'all_functions': [
                {
                    'name': 'main',
                    'params': '()',
                    'return_type': 'void',
                    'start_line': 10,
                    'end_line': 50,
                    'async': False,
                    'exported': True,
                    'complexity': 3,
                    'complexity_label': 'Low',
                    'file_path': '/test/project/src/index.ts',
                },
                {
                    'name': 'fetchData',
                    'params': '(url: string)',
                    'return_type': 'Promise<Data>',
                    'start_line': 60,
                    'end_line': 80,
                    'async': True,
                    'exported': True,
                    'complexity': 5,
                    'complexity_label': 'Low',
                    'file_path': '/test/project/src/index.ts',
                },
            ],
            'all_imports': [
                {'module': 'react', 'imports': ['useState', 'useEffect'], 'is_default': False, 'is_namespace': False},
                {'module': './utils', 'imports': ['helper'], 'is_default': False, 'is_namespace': False},
            ],
            'all_exports': [
                {'name': 'main', 'type': 'function', 'is_default': False},
                {'name': 'fetchData', 'type': 'function', 'is_default': False},
            ],
            'all_classes': [],
            'all_types': [],
            'children': ['/test/project/src/components', '/test/project/src/utils'],
            'parent': '/test/project',
            'metrics': {
                'total_lines': 150,
                'total_files': 2,
                'total_functions': 2,
                'total_classes': 0,
                'total_types': 0,
                'avg_complexity': 4.0,
                'complexity_label': 'Low',
            },
            'connections': {
                'uses': ['/test/project/lib'],
                'used_by': ['/test/project/app'],
            },
        }
    
    @pytest.mark.asyncio
    async def test_generate_hivemind_basic(self, sample_structure):
        """Test basic hivemind generation."""
        content = await generate_hivemind(sample_structure)
        
        assert '# src' in content
        assert '## 📁 Files at This Level' in content
        assert '## ⚙️ Functions Defined' in content
        assert '## 📦 Dependencies' in content
        assert '## 📊 Metrics' in content
    
    @pytest.mark.asyncio
    async def test_generate_hivemind_with_ai_context(self, sample_structure):
        """Test hivemind generation with AI context."""
        ai_context = {
            'context': 'This is the main source directory containing core application logic.',
            'user_requirements': 'Must support TypeScript strict mode.',
            'warnings': 'Do not modify without running tests.',
            'next_steps': 'Add unit tests for all functions.',
            'how_it_works': 'Uses React hooks for state management.',
        }
        
        content = await generate_hivemind(sample_structure, ai_context)
        
        assert '## 🎯 What This Does' in content
        assert 'main source directory' in content
        assert '## 👤 User Requirements' in content
        assert 'TypeScript strict mode' in content
        assert '## ⚠️ Important Notes' in content
        assert '## 🔮 Next Steps' in content
        assert '## 💡 How It Works' in content
    
    @pytest.mark.asyncio
    async def test_generate_hivemind_includes_separator(self, sample_structure):
        """Test that separator exists between AI and dry logic sections."""
        ai_context = {'context': 'Test context'}
        content = await generate_hivemind(sample_structure, ai_context)
        
        assert '---' in content
    
    @pytest.mark.asyncio
    async def test_generate_hivemind_functions_formatted(self, sample_structure):
        """Test that functions are properly formatted."""
        content = await generate_hivemind(sample_structure)
        
        assert '`main()' in content
        assert '`fetchData(url: string)' in content
        assert 'Async' in content
        assert 'Exported' in content


class TestGenerateFlowchart:
    """Tests for Mermaid flowchart generation."""
    
    @pytest.fixture
    def sample_structure(self):
        return {
            'path': '/test/project/src',
            'name': 'src',
            'parent': '/test/project',
            'children': ['/test/project/src/components'],
            'connections': {
                'uses': ['/test/project/lib'],
                'used_by': ['/test/project/app'],
            },
        }
    
    @pytest.mark.asyncio
    async def test_generate_flowchart_basic(self, sample_structure):
        """Test basic flowchart generation."""
        content = await generate_flowchart(sample_structure)
        
        assert 'graph TD' in content
        assert 'src' in content
    
    @pytest.mark.asyncio
    async def test_generate_flowchart_has_styling(self, sample_structure):
        """Test that flowchart includes styling."""
        content = await generate_flowchart(sample_structure)
        
        assert 'classDef currentNode' in content
        assert 'classDef parentNode' in content
        assert 'classDef childNode' in content
    
    @pytest.mark.asyncio
    async def test_generate_flowchart_includes_parent(self, sample_structure):
        """Test that parent is included in flowchart."""
        content = await generate_flowchart(sample_structure)
        
        assert 'Parent link' in content or 'project' in content


class TestWriteFiles:
    """Tests for file writing functions."""
    
    @pytest.mark.asyncio
    async def test_write_files_creates_files(self):
        """Test that write_files creates both files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await write_files(
                Path(tmpdir),
                "# Test Hivemind\n\nContent here.",
                "graph TD\n    A --> B",
            )
            
            assert result['success'] is True
            assert len(result['files_written']) == 2
            
            hivemind_path = Path(tmpdir) / 'hivemind.md'
            flowchart_path = Path(tmpdir) / 'flowchart.mmd'
            
            assert hivemind_path.exists()
            assert flowchart_path.exists()
    
    @pytest.mark.asyncio
    async def test_write_files_creates_directory(self):
        """Test that write_files creates directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / 'new' / 'nested' / 'dir'
            
            result = await write_files(
                new_dir,
                "# Test",
                "graph TD",
            )
            
            assert result['success'] is True
            assert new_dir.exists()


class TestGenerateAndWrite:
    """Tests for the combined generate_and_write function."""
    
    @pytest.mark.asyncio
    async def test_generate_and_write_integration(self):
        """Test full generation and writing workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            structure = {
                'path': tmpdir,
                'name': Path(tmpdir).name,
                'files': [{'name': 'test.py', 'lines': 10}],
                'all_functions': [],
                'all_imports': [],
                'all_exports': [],
                'all_classes': [],
                'all_types': [],
                'children': [],
                'parent': None,
                'metrics': {
                    'total_lines': 10,
                    'total_files': 1,
                    'total_functions': 0,
                    'total_classes': 0,
                    'total_types': 0,
                    'avg_complexity': 1.0,
                    'complexity_label': 'Low',
                },
                'connections': {'uses': [], 'used_by': []},
            }
            
            result = await generate_and_write(structure)
            
            assert result['success'] is True
            assert result['hivemind_lines'] > 0
            assert result['flowchart_lines'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
