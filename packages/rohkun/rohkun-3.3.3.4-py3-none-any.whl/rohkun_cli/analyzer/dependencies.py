"""
Dependency Scanner - Extract imports and function calls using AST
Deterministic dependency detection for blast radius analysis
"""
from pathlib import Path
from typing import List, Dict, Optional, Set
import tree_sitter as ts
from tree_sitter import Language

# Import language parsers
try:
    import tree_sitter_python as tspython
    PYTHON_LANGUAGE = Language(tspython.language())
except (ImportError, AttributeError, TypeError):
    PYTHON_LANGUAGE = None

try:
    import tree_sitter_javascript as tsjavascript
    JAVASCRIPT_LANGUAGE = Language(tsjavascript.language())
except (ImportError, AttributeError, TypeError):
    JAVASCRIPT_LANGUAGE = None


def _get_language_parser(file_path: Path) -> Optional[tuple]:
    """Get tree-sitter parser for file based on extension"""
    ext = file_path.suffix.lower()
    
    language_map = {
        '.py': ('python', PYTHON_LANGUAGE),
        '.js': ('javascript', JAVASCRIPT_LANGUAGE),
        '.jsx': ('javascript', JAVASCRIPT_LANGUAGE),
        '.ts': ('javascript', JAVASCRIPT_LANGUAGE),  # Use JS parser for TS
        '.tsx': ('javascript', JAVASCRIPT_LANGUAGE),
    }
    
    lang_info = language_map.get(ext)
    if lang_info and lang_info[1] is not None:
        parser = ts.Parser()
        parser.language = lang_info[1]
        return (lang_info[0], parser)
    
    return None


def find_imports(file_path: Path, content: str) -> List[Dict]:
    """
    Find import statements using AST
    Returns deterministic list of imports
    """
    imports = []
    
    try:
        parser_info = _get_language_parser(file_path)
        if not parser_info:
            return []
        
        language, parser = parser_info
        tree = parser.parse(bytes(content, 'utf-8'))
        
        if language == 'python':
            imports = _find_python_imports(tree, bytes(content, 'utf-8'))
        elif language == 'javascript':
            imports = _find_javascript_imports(tree, bytes(content, 'utf-8'))
        
        for imp in imports:
            imp['file'] = str(file_path)
            imp['confidence'] = 'confident'
            imp['detection_method'] = 'ast'
        
        return imports
        
    except Exception:
        return []


def _find_python_imports(tree, content: bytes) -> List[Dict]:
    """Find Python import statements"""
    imports = []
    root = tree.root_node
    
    def traverse(node):
        # import module
        if node.type == 'import_statement':
            line = node.start_point[0] + 1
            import_text = node.text.decode('utf-8')
            
            # Extract module names
            for child in node.children:
                if child.type == 'dotted_name':
                    module = child.text.decode('utf-8')
                    imports.append({
                        'type': 'import',
                        'module': module,
                        'imported_names': [module],
                        'line': line,
                        'code': import_text
                    })
        
        # from module import name
        elif node.type == 'import_from_statement':
            line = node.start_point[0] + 1
            import_text = node.text.decode('utf-8')
            
            module = None
            imported_names = []
            
            for child in node.children:
                if child.type == 'dotted_name':
                    module = child.text.decode('utf-8')
                elif child.type == 'import_prefix':
                    # Handle relative imports (from . import x)
                    module = child.text.decode('utf-8')
                elif child.type in ['aliased_import', 'dotted_name'] and module:
                    # Extract imported names
                    name = child.text.decode('utf-8').split(' as ')[0]
                    imported_names.append(name)
            
            if module:
                imports.append({
                    'type': 'import_from',
                    'module': module,
                    'imported_names': imported_names,
                    'line': line,
                    'code': import_text
                })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return imports


def _find_javascript_imports(tree, content: bytes) -> List[Dict]:
    """Find JavaScript/TypeScript import statements"""
    imports = []
    root = tree.root_node
    
    def traverse(node):
        # import x from 'module'
        if node.type == 'import_statement':
            line = node.start_point[0] + 1
            import_text = node.text.decode('utf-8')
            
            module = None
            imported_names = []
            
            for child in node.children:
                if child.type == 'string':
                    # Module path
                    module = child.text.decode('utf-8').strip('"').strip("'")
                elif child.type == 'import_clause':
                    # Extract imported names
                    for subchild in child.children:
                        if subchild.type == 'identifier':
                            imported_names.append(subchild.text.decode('utf-8'))
            
            if module:
                imports.append({
                    'type': 'import',
                    'module': module,
                    'imported_names': imported_names,
                    'line': line,
                    'code': import_text
                })
        
        # const x = require('module')
        elif node.type == 'variable_declaration':
            for child in node.children:
                if child.type == 'variable_declarator':
                    # Check if it's a require() call
                    for subchild in child.children:
                        if subchild.type == 'call_expression':
                            callee = subchild.children[0] if subchild.child_count > 0 else None
                            if callee and callee.type == 'identifier' and callee.text.decode('utf-8') == 'require':
                                # Extract module name
                                if subchild.child_count > 1:
                                    args = subchild.children[1]
                                    if args.type == 'arguments' and args.child_count > 1:
                                        module_arg = args.children[1]
                                        if module_arg.type == 'string':
                                            module = module_arg.text.decode('utf-8').strip('"').strip("'")
                                            line = node.start_point[0] + 1
                                            imports.append({
                                                'type': 'require',
                                                'module': module,
                                                'imported_names': [],
                                                'line': line,
                                                'code': node.text.decode('utf-8')[:80]
                                            })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return imports


def find_function_calls(file_path: Path, content: str) -> List[Dict]:
    """
    Find function calls using AST
    Returns deterministic list of function calls for dependency tracking
    """
    calls = []
    
    try:
        parser_info = _get_language_parser(file_path)
        if not parser_info:
            return []
        
        language, parser = parser_info
        tree = parser.parse(bytes(content, 'utf-8'))
        
        if language == 'python':
            calls = _find_python_function_calls(tree, bytes(content, 'utf-8'))
        elif language == 'javascript':
            calls = _find_javascript_function_calls(tree, bytes(content, 'utf-8'))
        
        for call in calls:
            call['file'] = str(file_path)
            call['confidence'] = 'confident'
            call['detection_method'] = 'ast'
        
        return calls
        
    except Exception:
        return []


def _find_python_function_calls(tree, content: bytes) -> List[Dict]:
    """Find Python function calls"""
    calls = []
    root = tree.root_node
    
    def traverse(node):
        if node.type == 'call':
            line = node.start_point[0] + 1
            callee = node.children[0] if node.child_count > 0 else None
            
            if callee:
                func_name = None
                
                if callee.type == 'identifier':
                    # Simple function call: func()
                    func_name = callee.text.decode('utf-8')
                elif callee.type == 'attribute':
                    # Method call: obj.method()
                    func_name = callee.text.decode('utf-8')
                
                if func_name:
                    calls.append({
                        'type': 'function_call',
                        'function': func_name,
                        'line': line,
                        'code': node.text.decode('utf-8')[:80]
                    })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return calls


def _find_javascript_function_calls(tree, content: bytes) -> List[Dict]:
    """Find JavaScript function calls"""
    calls = []
    root = tree.root_node
    
    def traverse(node):
        if node.type == 'call_expression':
            line = node.start_point[0] + 1
            callee = node.children[0] if node.child_count > 0 else None
            
            if callee:
                func_name = None
                
                if callee.type == 'identifier':
                    # Simple function call: func()
                    func_name = callee.text.decode('utf-8')
                elif callee.type == 'member_expression':
                    # Method call: obj.method()
                    func_name = callee.text.decode('utf-8')
                
                if func_name:
                    calls.append({
                        'type': 'function_call',
                        'function': func_name,
                        'line': line,
                        'code': node.text.decode('utf-8')[:80]
                    })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return calls


def find_function_definitions(file_path: Path, content: str) -> List[Dict]:
    """
    Find function definitions using AST
    Returns deterministic list of functions for dependency tracking
    """
    functions = []
    
    try:
        parser_info = _get_language_parser(file_path)
        if not parser_info:
            return []
        
        language, parser = parser_info
        tree = parser.parse(bytes(content, 'utf-8'))
        
        if language == 'python':
            functions = _find_python_functions(tree, bytes(content, 'utf-8'))
        elif language == 'javascript':
            functions = _find_javascript_functions(tree, bytes(content, 'utf-8'))
        
        for func in functions:
            func['file'] = str(file_path)
            func['confidence'] = 'confident'
            func['detection_method'] = 'ast'
        
        return functions
        
    except Exception:
        return []


def _find_python_functions(tree, content: bytes) -> List[Dict]:
    """Find Python function definitions"""
    functions = []
    root = tree.root_node
    
    def traverse(node):
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            params_node = node.child_by_field_name('parameters')
            
            if name_node:
                func_name = name_node.text.decode('utf-8')
                line = node.start_point[0] + 1
                
                # Check if async
                is_async = any(c.type == 'async' for c in node.children)
                
                functions.append({
                    'type': 'function',
                    'name': func_name,
                    'line': line,
                    'is_async': is_async,
                    'params': params_node.text.decode('utf-8') if params_node else '()'
                })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return functions


def _find_javascript_functions(tree, content: bytes) -> List[Dict]:
    """Find JavaScript function definitions"""
    functions = []
    root = tree.root_node
    
    def traverse(node):
        if node.type in ['function_declaration', 'function', 'arrow_function', 'method_definition']:
            line = node.start_point[0] + 1
            
            # Try to get function name
            func_name = None
            if node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    func_name = name_node.text.decode('utf-8')
            elif node.type == 'method_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    func_name = name_node.text.decode('utf-8')
            
            # Check if async
            is_async = any(c.type == 'async' for c in node.children)
            
            if func_name:
                functions.append({
                    'type': 'function',
                    'name': func_name,
                    'line': line,
                    'is_async': is_async
                })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return functions
