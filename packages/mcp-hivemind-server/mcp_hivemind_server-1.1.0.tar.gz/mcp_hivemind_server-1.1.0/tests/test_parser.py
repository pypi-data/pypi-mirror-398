"""
HiveMind MCP Server - Parser Tests
Unit tests for code structure extraction.
"""

import pytest
from pathlib import Path
import tempfile
import os

from parser import CodeParser, analyze_directory, FunctionInfo, ImportInfo


class TestCodeParser:
    """Tests for the CodeParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CodeParser()
    
    def test_parser_initialization(self):
        """Test that parser initializes correctly."""
        assert self.parser is not None
        # Check if parsers are available (depends on tree-sitter installation)
        assert isinstance(self.parser.parsers, dict)
    
    def test_parse_python_file(self):
        """Test parsing a Python file."""
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        f.write('''
def hello_world():
    """Say hello."""
    print("Hello, World!")

async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    return {}

class MyClass:
    def __init__(self):
        pass
    
    def method(self, arg: int) -> str:
        return str(arg)
''')
        f.close()  # Close before parsing (Windows compatibility)
            
        try:
            result = self.parser.parse_file(Path(f.name))
            
            assert 'functions' in result
            assert 'imports' in result
            assert 'classes' in result
            assert 'file_info' in result
            
            # Check functions were found
            func_names = [func['name'] for func in result['functions']]
            assert 'hello_world' in func_names or 'fetch_data' in func_names
            
        finally:
            os.unlink(f.name)
    
    def test_parse_typescript_file(self):
        """Test parsing a TypeScript file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write('''
import { useState } from 'react';
import axios from 'axios';

export function calculateSum(a: number, b: number): number {
    return a + b;
}

export const fetchUser = async (id: string): Promise<User> => {
    const response = await axios.get(`/users/${id}`);
    return response.data;
};

interface User {
    id: string;
    name: string;
}

export default class UserService {
    private apiUrl: string;
    
    constructor(url: string) {
        this.apiUrl = url;
    }
    
    async getUser(id: string): Promise<User> {
        return fetchUser(id);
    }
}
''')
            f.flush()
            
            try:
                result = self.parser.parse_file(Path(f.name))
                
                assert 'functions' in result
                assert 'imports' in result
                assert 'exports' in result
                
                # Check imports were found
                import_modules = [imp['module'] for imp in result['imports']]
                assert 'react' in import_modules or 'axios' in import_modules
                
            finally:
                os.unlink(f.name)
    
    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('')
            f.flush()
            
            try:
                result = self.parser.parse_file(Path(f.name))
                
                assert result['functions'] == []
                assert result['imports'] == []
                
            finally:
                os.unlink(f.name)
    
    def test_parse_unsupported_extension(self):
        """Test parsing file with unsupported extension."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write('some content')
            f.flush()
            
            try:
                result = self.parser.parse_file(Path(f.name))
                
                # Should return empty result without error
                assert result['functions'] == []
                
            finally:
                os.unlink(f.name)


class TestAnalyzeDirectory:
    """Tests for the analyze_directory function."""
    
    def test_analyze_simple_directory(self):
        """Test analyzing a simple directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple Python file
            py_file = Path(tmpdir) / 'main.py'
            py_file.write_text('''
def main():
    print("Hello")

def helper(x: int) -> int:
    return x * 2
''')
            
            result = analyze_directory(Path(tmpdir))
            
            assert result['name'] == Path(tmpdir).name
            assert result['path'] == str(Path(tmpdir).resolve())
            assert len(result['files']) >= 1
            assert result['metrics']['total_files'] >= 1
    
    def test_analyze_directory_with_children(self):
        """Test analyzing directory with subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create subdirectory
            subdir = Path(tmpdir) / 'submodule'
            subdir.mkdir()
            
            # Create file in subdir
            (subdir / 'module.py').write_text('def func(): pass')
            
            result = analyze_directory(Path(tmpdir))
            
            assert len(result['children']) >= 1
            assert str(subdir) in result['children']
    
    def test_analyze_ignores_node_modules(self):
        """Test that node_modules is ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create node_modules
            node_modules = Path(tmpdir) / 'node_modules'
            node_modules.mkdir()
            (node_modules / 'package.json').write_text('{}')
            
            result = analyze_directory(Path(tmpdir))
            
            # node_modules should not be in children
            for child in result['children']:
                assert 'node_modules' not in child


class TestDataClasses:
    """Tests for data classes."""
    
    def test_function_info_to_dict(self):
        """Test FunctionInfo conversion to dict."""
        func = FunctionInfo(
            name='testFunc',
            params='(a: int, b: str)',
            return_type='bool',
            start_line=10,
            end_line=20,
            is_async=True,
            exported=True,
            complexity=5,
        )
        
        d = func.to_dict()
        
        assert d['name'] == 'testFunc'
        assert d['params'] == '(a: int, b: str)'
        assert d['return_type'] == 'bool'
        assert d['async'] is True
        assert d['exported'] is True
        assert d['complexity'] == 5
    
    def test_import_info_to_dict(self):
        """Test ImportInfo conversion to dict."""
        imp = ImportInfo(
            module='react',
            imports=['useState', 'useEffect'],
            is_default=False,
            is_namespace=False,
        )
        
        d = imp.to_dict()
        
        assert d['module'] == 'react'
        assert 'useState' in d['imports']
        assert d['is_default'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
