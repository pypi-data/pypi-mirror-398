"""
HiveMind MCP Server - Parser
Code structure extraction using tree-sitter for TypeScript, JavaScript, and Python.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field

try:
    import tree_sitter_languages
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from config import (
    PARSEABLE_EXTENSIONS,
    INCLUDEABLE_EXTENSIONS,
    IGNORE_PATTERNS,
    TS_JS_FUNCTION_NODES,
    TS_JS_IMPORT_NODES,
    TS_JS_EXPORT_NODES,
    TS_JS_CLASS_NODES,
    TS_TYPE_NODES,
    PY_FUNCTION_NODES,
    PY_IMPORT_NODES,
    PY_CLASS_NODES,
    get_complexity_label,
)
from utils import should_ignore, get_file_info, normalize_path


@dataclass
class FunctionInfo:
    """Information about a function definition."""
    name: str
    params: str
    return_type: str
    start_line: int
    end_line: int
    is_async: bool = False
    exported: bool = False
    complexity: int = 1
    docstring: Optional[str] = None
    file_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'params': self.params,
            'return_type': self.return_type,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'async': self.is_async,
            'exported': self.exported,
            'complexity': self.complexity,
            'complexity_label': get_complexity_label(self.complexity),
            'docstring': self.docstring,
            'file_path': self.file_path,
        }


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: str
    imports: List[str] = field(default_factory=list)
    is_default: bool = False
    is_namespace: bool = False
    alias: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'module': self.module,
            'imports': self.imports,
            'is_default': self.is_default,
            'is_namespace': self.is_namespace,
            'alias': self.alias,
        }


@dataclass
class ExportInfo:
    """Information about an export statement."""
    name: str
    export_type: str  # 'function', 'class', 'const', 'type', 'interface', 'default'
    is_default: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.export_type,
            'is_default': self.is_default,
        }


@dataclass
class ClassInfo:
    """Information about a class definition."""
    name: str
    start_line: int
    end_line: int
    methods: List[FunctionInfo] = field(default_factory=list)
    exported: bool = False
    extends: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'methods': [m.to_dict() for m in self.methods],
            'exported': self.exported,
            'extends': self.extends,
        }


@dataclass
class TypeInfo:
    """Information about a type/interface definition."""
    name: str
    kind: str  # 'interface' or 'type'
    start_line: int
    end_line: int
    exported: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'kind': self.kind,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'exported': self.exported,
        }


class CodeParser:
    """
    Parse code files using tree-sitter to extract structural information.
    """
    
    def __init__(self):
        """Initialize the parser with tree-sitter languages."""
        self.parsers: Dict[str, Any] = {}
        self._init_parsers()
    
    def _init_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        if not TREE_SITTER_AVAILABLE:
            return
            
        language_map = {
            'typescript': 'typescript',
            'tsx': 'tsx',
            'javascript': 'javascript',
            'python': 'python',
        }
        
        for lang_key, lang_name in language_map.items():
            try:
                self.parsers[lang_key] = tree_sitter_languages.get_parser(lang_name)
            except Exception:
                pass  # Language not available
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a single file and extract structural information.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            Dictionary containing extracted information
        """
        result = {
            'functions': [],
            'imports': [],
            'exports': [],
            'classes': [],
            'types': [],
            'file_info': get_file_info(file_path),
        }
        
        ext = file_path.suffix.lower()
        if ext not in PARSEABLE_EXTENSIONS:
            return result
        
        lang = PARSEABLE_EXTENSIONS[ext]
        if lang not in self.parsers:
            # Fallback to regex-based parsing
            return self._parse_with_regex(file_path, lang)
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            tree = self.parsers[lang].parse(bytes(content, 'utf-8'))
            
            if lang in ('typescript', 'tsx', 'javascript'):
                self._extract_ts_js(tree.root_node, content, result, str(file_path))
            elif lang == 'python':
                self._extract_python(tree.root_node, content, result, str(file_path))
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _extract_ts_js(self, node: Any, content: str, result: Dict, file_path: str):
        """Extract information from TypeScript/JavaScript AST."""
        lines = content.split('\n')
        
        def get_text(n) -> str:
            return content[n.start_byte:n.end_byte]
        
        def walk(n, exported: bool = False):
            node_type = n.type
            
            # Check for export
            is_exported = exported or node_type == 'export_statement'
            
            # Functions
            if node_type in TS_JS_FUNCTION_NODES:
                func = self._parse_ts_js_function(n, get_text, is_exported, file_path)
                if func:
                    result['functions'].append(func.to_dict())
            
            # Imports
            elif node_type == 'import_statement':
                imp = self._parse_ts_js_import(n, get_text)
                if imp:
                    result['imports'].append(imp.to_dict())
            
            # Exports
            elif node_type == 'export_statement':
                exp = self._parse_ts_js_export(n, get_text)
                if exp:
                    result['exports'].extend([e.to_dict() for e in exp])
            
            # Classes
            elif node_type in TS_JS_CLASS_NODES:
                cls = self._parse_ts_js_class(n, get_text, is_exported, file_path)
                if cls:
                    result['classes'].append(cls.to_dict())
            
            # Types/Interfaces
            elif node_type in TS_TYPE_NODES:
                type_info = self._parse_ts_type(n, get_text, is_exported)
                if type_info:
                    result['types'].append(type_info.to_dict())
            
            # Recurse into children
            for child in n.children:
                walk(child, is_exported if node_type == 'export_statement' else False)
        
        walk(node)
    
    def _parse_ts_js_function(self, node: Any, get_text, exported: bool, file_path: str) -> Optional[FunctionInfo]:
        """Parse a TypeScript/JavaScript function node."""
        try:
            name = ""
            params = ""
            return_type = "void"
            is_async = False
            
            for child in node.children:
                if child.type == 'identifier':
                    name = get_text(child)
                elif child.type == 'formal_parameters':
                    params = get_text(child)
                elif child.type == 'type_annotation':
                    return_type = get_text(child).lstrip(': ')
                elif child.type == 'async':
                    is_async = True
            
            # For arrow functions, check parent for variable name
            if not name and node.type == 'arrow_function':
                parent = node.parent
                if parent and parent.type == 'variable_declarator':
                    for child in parent.children:
                        if child.type == 'identifier':
                            name = get_text(child)
                            break
            
            if not name:
                return None
            
            # Calculate complexity (simplified: count branches)
            complexity = 1
            def count_branches(n):
                nonlocal complexity
                if n.type in ('if_statement', 'conditional_expression', 'switch_case'):
                    complexity += 1
                elif n.type in ('for_statement', 'while_statement', 'do_statement', 'for_in_statement'):
                    complexity += 1
                for child in n.children:
                    count_branches(child)
            count_branches(node)
            
            return FunctionInfo(
                name=name,
                params=params,
                return_type=return_type,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                is_async=is_async,
                exported=exported,
                complexity=complexity,
                file_path=file_path,
            )
        except Exception:
            return None
    
    def _parse_ts_js_import(self, node: Any, get_text) -> Optional[ImportInfo]:
        """Parse a TypeScript/JavaScript import statement."""
        try:
            module = ""
            imports = []
            is_default = False
            is_namespace = False
            
            for child in node.children:
                if child.type == 'string':
                    module = get_text(child).strip('"\'')
                elif child.type == 'import_clause':
                    for ic_child in child.children:
                        if ic_child.type == 'identifier':
                            imports.append(get_text(ic_child))
                            is_default = True
                        elif ic_child.type == 'named_imports':
                            for ni_child in ic_child.children:
                                if ni_child.type == 'import_specifier':
                                    for spec_child in ni_child.children:
                                        if spec_child.type == 'identifier':
                                            imports.append(get_text(spec_child))
                                            break
                        elif ic_child.type == 'namespace_import':
                            is_namespace = True
                            for ns_child in ic_child.children:
                                if ns_child.type == 'identifier':
                                    imports.append(get_text(ns_child))
            
            if module:
                return ImportInfo(
                    module=module,
                    imports=imports,
                    is_default=is_default,
                    is_namespace=is_namespace,
                )
            return None
        except Exception:
            return None
    
    def _parse_ts_js_export(self, node: Any, get_text) -> List[ExportInfo]:
        """Parse a TypeScript/JavaScript export statement."""
        exports = []
        try:
            is_default = False
            
            for child in node.children:
                if child.type == 'default':
                    is_default = True
                elif child.type == 'function_declaration':
                    for fc in child.children:
                        if fc.type == 'identifier':
                            exports.append(ExportInfo(
                                name=get_text(fc),
                                export_type='function',
                                is_default=is_default,
                            ))
                            break
                elif child.type == 'class_declaration':
                    for cc in child.children:
                        if cc.type == 'identifier':
                            exports.append(ExportInfo(
                                name=get_text(cc),
                                export_type='class',
                                is_default=is_default,
                            ))
                            break
                elif child.type == 'lexical_declaration':
                    for lc in child.children:
                        if lc.type == 'variable_declarator':
                            for vc in lc.children:
                                if vc.type == 'identifier':
                                    exports.append(ExportInfo(
                                        name=get_text(vc),
                                        export_type='const',
                                        is_default=is_default,
                                    ))
                                    break
                elif child.type == 'identifier':
                    exports.append(ExportInfo(
                        name=get_text(child),
                        export_type='default' if is_default else 'named',
                        is_default=is_default,
                    ))
        except Exception:
            pass
        return exports
    
    def _parse_ts_js_class(self, node: Any, get_text, exported: bool, file_path: str) -> Optional[ClassInfo]:
        """Parse a TypeScript/JavaScript class."""
        try:
            name = ""
            extends = None
            methods = []
            
            for child in node.children:
                if child.type == 'identifier':
                    name = get_text(child)
                elif child.type == 'class_heritage':
                    for hc in child.children:
                        if hc.type == 'extends_clause':
                            for ec in hc.children:
                                if ec.type == 'identifier':
                                    extends = get_text(ec)
                elif child.type == 'class_body':
                    for bc in child.children:
                        if bc.type == 'method_definition':
                            func = self._parse_ts_js_function(bc, get_text, True, file_path)
                            if func:
                                methods.append(func)
            
            if name:
                return ClassInfo(
                    name=name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    methods=methods,
                    exported=exported,
                    extends=extends,
                )
            return None
        except Exception:
            return None
    
    def _parse_ts_type(self, node: Any, get_text, exported: bool) -> Optional[TypeInfo]:
        """Parse a TypeScript type or interface."""
        try:
            name = ""
            kind = "interface" if node.type == 'interface_declaration' else "type"
            
            for child in node.children:
                if child.type == 'identifier' or child.type == 'type_identifier':
                    name = get_text(child)
                    break
            
            if name:
                return TypeInfo(
                    name=name,
                    kind=kind,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    exported=exported,
                )
            return None
        except Exception:
            return None
    
    def _extract_python(self, node: Any, content: str, result: Dict, file_path: str):
        """Extract information from Python AST."""
        def get_text(n) -> str:
            return content[n.start_byte:n.end_byte]
        
        def walk(n, in_class: bool = False):
            node_type = n.type
            
            # Functions
            if node_type in PY_FUNCTION_NODES:
                func = self._parse_python_function(n, get_text, file_path)
                if func:
                    result['functions'].append(func.to_dict())
            
            # Imports
            elif node_type in PY_IMPORT_NODES:
                imps = self._parse_python_import(n, get_text)
                for imp in imps:
                    result['imports'].append(imp.to_dict())
            
            # Classes
            elif node_type == 'class_definition':
                cls = self._parse_python_class(n, get_text, file_path)
                if cls:
                    result['classes'].append(cls.to_dict())
                return  # Don't recurse into class body separately
            
            # Recurse
            for child in n.children:
                walk(child, in_class)
        
        walk(node)
    
    def _parse_python_function(self, node: Any, get_text, file_path: str) -> Optional[FunctionInfo]:
        """Parse a Python function definition."""
        try:
            name = ""
            params = ""
            return_type = "None"
            is_async = node.type == 'async_function_definition'
            docstring = None
            
            for child in node.children:
                if child.type == 'identifier':
                    name = get_text(child)
                elif child.type == 'parameters':
                    params = get_text(child)
                elif child.type == 'type':
                    return_type = get_text(child)
                elif child.type == 'block':
                    # Check first statement for docstring
                    for bc in child.children:
                        if bc.type == 'expression_statement':
                            for ec in bc.children:
                                if ec.type == 'string':
                                    docstring = get_text(ec).strip('"\' ')
                                    break
                            break
            
            if not name or name.startswith('_'):
                # Skip private functions for now
                pass
            
            # Calculate complexity
            complexity = 1
            def count_branches(n):
                nonlocal complexity
                if n.type in ('if_statement', 'conditional_expression', 'elif_clause'):
                    complexity += 1
                elif n.type in ('for_statement', 'while_statement', 'with_statement'):
                    complexity += 1
                elif n.type == 'except_clause':
                    complexity += 1
                for child in n.children:
                    count_branches(child)
            count_branches(node)
            
            return FunctionInfo(
                name=name,
                params=params,
                return_type=return_type,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                is_async=is_async,
                exported=not name.startswith('_'),
                complexity=complexity,
                docstring=docstring,
                file_path=file_path,
            )
        except Exception:
            return None
    
    def _parse_python_import(self, node: Any, get_text) -> List[ImportInfo]:
        """Parse Python import statements."""
        imports = []
        try:
            if node.type == 'import_statement':
                # import module or import module as alias
                for child in node.children:
                    if child.type == 'dotted_name':
                        imports.append(ImportInfo(
                            module=get_text(child),
                            imports=[get_text(child).split('.')[-1]],
                            is_namespace=True,
                        ))
                    elif child.type == 'aliased_import':
                        module = ""
                        alias = ""
                        for ac in child.children:
                            if ac.type == 'dotted_name':
                                module = get_text(ac)
                            elif ac.type == 'identifier':
                                alias = get_text(ac)
                        if module:
                            imports.append(ImportInfo(
                                module=module,
                                imports=[alias] if alias else [module.split('.')[-1]],
                                alias=alias,
                                is_namespace=True,
                            ))
            
            elif node.type == 'import_from_statement':
                # from module import name
                module = ""
                names = []
                for child in node.children:
                    if child.type == 'dotted_name' or child.type == 'relative_import':
                        module = get_text(child)
                    elif child.type == 'identifier':
                        names.append(get_text(child))
                    elif child.type == 'aliased_import':
                        for ac in child.children:
                            if ac.type == 'identifier':
                                names.append(get_text(ac))
                                break
                    elif child.type == 'wildcard_import':
                        names.append('*')
                
                if module:
                    imports.append(ImportInfo(
                        module=module,
                        imports=names,
                        is_default=len(names) == 1 and names[0] != '*',
                    ))
        except Exception:
            pass
        return imports
    
    def _parse_python_class(self, node: Any, get_text, file_path: str) -> Optional[ClassInfo]:
        """Parse a Python class definition."""
        try:
            name = ""
            extends = None
            methods = []
            
            for child in node.children:
                if child.type == 'identifier':
                    name = get_text(child)
                elif child.type == 'argument_list':
                    # Base classes
                    for ac in child.children:
                        if ac.type == 'identifier':
                            extends = get_text(ac)
                            break
                elif child.type == 'block':
                    for bc in child.children:
                        if bc.type in PY_FUNCTION_NODES:
                            func = self._parse_python_function(bc, get_text, file_path)
                            if func:
                                methods.append(func)
            
            if name:
                return ClassInfo(
                    name=name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    methods=methods,
                    exported=not name.startswith('_'),
                    extends=extends,
                )
            return None
        except Exception:
            return None
    
    def _parse_with_regex(self, file_path: Path, lang: str) -> Dict[str, Any]:
        """Fallback regex-based parsing when tree-sitter is not available."""
        import re
        
        result = {
            'functions': [],
            'imports': [],
            'exports': [],
            'classes': [],
            'types': [],
            'file_info': get_file_info(file_path),
        }
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            if lang == 'python':
                # Python function pattern
                func_pattern = r'^(async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:'
                import_pattern = r'^(?:from\s+([\w.]+)\s+)?import\s+(.+)$'
                class_pattern = r'^class\s+(\w+)(?:\(([^)]*)\))?:'
                
                for i, line in enumerate(lines):
                    # Functions
                    match = re.match(func_pattern, line.strip())
                    if match:
                        result['functions'].append({
                            'name': match.group(2),
                            'params': f"({match.group(3)})",
                            'return_type': match.group(4) or 'None',
                            'start_line': i + 1,
                            'end_line': i + 1,
                            'async': bool(match.group(1)),
                            'exported': not match.group(2).startswith('_'),
                            'complexity': 1,
                            'file_path': str(file_path),
                        })
                    
                    # Imports
                    match = re.match(import_pattern, line.strip())
                    if match:
                        module = match.group(1) or match.group(2).split(',')[0].strip()
                        names = [n.strip() for n in match.group(2).split(',')]
                        result['imports'].append({
                            'module': module,
                            'imports': names if match.group(1) else [module],
                            'is_default': False,
                            'is_namespace': not match.group(1),
                        })
                    
                    # Classes
                    match = re.match(class_pattern, line.strip())
                    if match:
                        result['classes'].append({
                            'name': match.group(1),
                            'start_line': i + 1,
                            'end_line': i + 1,
                            'methods': [],
                            'exported': not match.group(1).startswith('_'),
                            'extends': match.group(2),
                        })
            
            elif lang in ('typescript', 'javascript', 'tsx'):
                # JS/TS patterns
                func_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)'
                arrow_pattern = r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>'
                import_pattern = r"import\s+(?:{([^}]+)}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]"
                export_pattern = r'export\s+(?:default\s+)?(?:const|let|var|function|class)\s+(\w+)'
                
                for i, line in enumerate(lines):
                    # Functions
                    match = re.search(func_pattern, line)
                    if match:
                        result['functions'].append({
                            'name': match.group(1),
                            'params': f"({match.group(2)})",
                            'return_type': 'void',
                            'start_line': i + 1,
                            'end_line': i + 1,
                            'async': 'async' in line,
                            'exported': 'export' in line,
                            'complexity': 1,
                            'file_path': str(file_path),
                        })
                    
                    # Arrow functions
                    match = re.search(arrow_pattern, line)
                    if match:
                        result['functions'].append({
                            'name': match.group(1),
                            'params': '()',
                            'return_type': 'void',
                            'start_line': i + 1,
                            'end_line': i + 1,
                            'async': 'async' in line,
                            'exported': 'export' in line,
                            'complexity': 1,
                            'file_path': str(file_path),
                        })
                    
                    # Imports
                    match = re.search(import_pattern, line)
                    if match:
                        names = match.group(1) or match.group(2)
                        if names:
                            result['imports'].append({
                                'module': match.group(3),
                                'imports': [n.strip() for n in names.split(',')] if match.group(1) else [names],
                                'is_default': bool(match.group(2)),
                                'is_namespace': False,
                            })
                    
                    # Exports
                    match = re.search(export_pattern, line)
                    if match:
                        result['exports'].append({
                            'name': match.group(1),
                            'type': 'named',
                            'is_default': 'default' in line,
                        })
        except Exception as e:
            result['error'] = str(e)
        
        return result


def analyze_directory(dir_path: Path, root_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Analyze all code files in a directory (non-recursive for that level).
    
    Args:
        dir_path: Path to directory to analyze
        root_path: Optional root path for relative anchor generation
        
    Returns:
        Comprehensive structure dictionary
    """
    dir_path = normalize_path(str(dir_path))
    if root_path is None:
        root_path = dir_path
    
    parser = CodeParser()
    
    structure = {
        'path': str(dir_path),
        'name': dir_path.name,
        'files': [],
        'all_functions': [],
        'all_imports': [],
        'all_exports': [],
        'all_classes': [],
        'all_types': [],
        'children': [],
        'parent': str(dir_path.parent) if dir_path != root_path else None,
        'metrics': {
            'total_lines': 0,
            'total_files': 0,
            'total_functions': 0,
            'avg_complexity': 0.0,
        },
        'connections': {
            'uses': [],
            'used_by': [],
        },
    }
    
    try:
        # List files and directories
        for item in dir_path.iterdir():
            if should_ignore(item):
                continue
            
            if item.is_dir():
                structure['children'].append(str(item))
            
            elif item.is_file() and item.suffix.lower() in INCLUDEABLE_EXTENSIONS:
                # Parse the file
                parsed = parser.parse_file(item)
                
                structure['files'].append(parsed.get('file_info', {'name': item.name}))
                structure['all_functions'].extend(parsed.get('functions', []))
                structure['all_imports'].extend(parsed.get('imports', []))
                structure['all_exports'].extend(parsed.get('exports', []))
                structure['all_classes'].extend(parsed.get('classes', []))
                structure['all_types'].extend(parsed.get('types', []))
        
        # Calculate metrics
        total_lines = sum(f.get('lines', 0) for f in structure['files'])
        total_functions = len(structure['all_functions'])
        complexities = [f.get('complexity', 1) for f in structure['all_functions']]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 1.0
        
        structure['metrics'] = {
            'total_lines': total_lines,
            'total_files': len(structure['files']),
            'total_functions': total_functions,
            'total_classes': len(structure['all_classes']),
            'total_types': len(structure['all_types']),
            'avg_complexity': round(avg_complexity, 2),
            'complexity_label': get_complexity_label(int(avg_complexity)),
        }
        
        # Analyze connections based on imports
        structure['connections'] = _analyze_connections(structure, root_path)
        
    except Exception as e:
        structure['error'] = str(e)
    
    return structure


def _analyze_connections(structure: Dict, root_path: Path) -> Dict[str, List[str]]:
    """
    Analyze import statements to build connection graph.
    
    Args:
        structure: Parsed structure dictionary
        root_path: Root path for anchor generation
        
    Returns:
        Dictionary with 'uses' and 'used_by' lists
    """
    uses = set()
    
    for imp in structure.get('all_imports', []):
        module = imp.get('module', '')
        
        # Skip external packages
        if not module.startswith('.') and not module.startswith('@/'):
            uses.add(module)
            continue
        
        # Normalize relative imports
        if module.startswith('.'):
            # Convert relative path to absolute
            current = Path(structure['path'])
            parts = module.split('/')
            for part in parts:
                if part == '.':
                    continue
                elif part == '..':
                    current = current.parent
                else:
                    current = current / part
            uses.add(str(current))
        elif module.startswith('@/'):
            # Project-relative import
            uses.add(str(root_path / module[2:]))
    
    return {
        'uses': list(uses),
        'used_by': [],  # Will be populated during full codebase scan
    }
