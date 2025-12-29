"""
Endpoint detection - find API endpoints in backend code using AST parsing
"""
import re
from pathlib import Path
from typing import List, Dict, Optional
import tree_sitter as ts
from tree_sitter import Language

# Try to import language parsers (optional - will fall back to regex if not available)
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

try:
    import tree_sitter_typescript as tstypescript
    TYPESCRIPT_LANGUAGE = Language(tstypescript.language_typescript())
except (ImportError, AttributeError, TypeError):
    TYPESCRIPT_LANGUAGE = None

try:
    import tree_sitter_go as tsgo
    GO_LANGUAGE = Language(tsgo.language())
except (ImportError, AttributeError, TypeError):
    GO_LANGUAGE = None

try:
    import tree_sitter_java as tsjava
    JAVA_LANGUAGE = Language(tsjava.language())
except (ImportError, AttributeError, TypeError):
    JAVA_LANGUAGE = None


def _get_language_parser(file_path: Path) -> Optional[tuple]:
    """Get tree-sitter parser for file based on extension"""
    ext = file_path.suffix.lower()
    
    language_map = {
        '.py': ('python', PYTHON_LANGUAGE),
        '.js': ('javascript', JAVASCRIPT_LANGUAGE),
        '.jsx': ('javascript', JAVASCRIPT_LANGUAGE),
        '.ts': ('typescript', TYPESCRIPT_LANGUAGE),
        '.tsx': ('typescript', TYPESCRIPT_LANGUAGE),
        '.go': ('go', GO_LANGUAGE),
        '.java': ('java', JAVA_LANGUAGE),
    }
    
    lang_info = language_map.get(ext)
    if lang_info and lang_info[1] is not None:
        parser = ts.Parser()
        parser.language = lang_info[1]
        return (lang_info[0], parser)
    
    return None


def _extract_string_literal(node) -> Optional[str]:
    """Extract string literal from AST node"""
    if node.type == 'string':
        # Remove quotes
        text = node.text.decode('utf-8')
        if text.startswith('"') and text.endswith('"'):
            return text[1:-1]
        elif text.startswith("'") and text.endswith("'"):
            return text[1:-1]
        elif text.startswith('"""') and text.endswith('"""'):
            return text[3:-3]
        elif text.startswith("'''") and text.endswith("'''"):
            return text[3:-3]
    elif node.type == 'concatenated_string':
        # Handle string concatenation
        parts = []
        for child in node.children:
            if child.type == 'string':
                part = _extract_string_literal(child)
                if part:
                    parts.append(part)
        return ''.join(parts) if parts else None
    return None


def _find_python_endpoints_ast(tree, content: bytes) -> List[Dict]:
    """Find Python endpoints using AST (Flask, FastAPI, Django)"""
    endpoints = []
    root = tree.root_node
    
    def process_decorator(decorator_node):
        """Process a decorator node to extract endpoint info"""
        # Decorator structure: decorator -> [@, call]
        if decorator_node.child_count >= 2:
            call_node = decorator_node.children[1]  # The call after @
            if call_node.type == 'call':
                # Check the callee (app.route, app.get, etc.)
                if call_node.child_count > 0:
                    callee = call_node.children[0]
                    
                    # Must be attribute (app.route, app.get, etc.)
                    if callee.type == 'attribute' and callee.child_count >= 3:
                        method_name = callee.children[2].text.decode('utf-8')
                        
                        # Flask: @app.route(...)
                        if method_name == 'route':
                            if call_node.child_count > 1:
                                args = call_node.children[1]  # argument_list
                                # Path is at args.children[1] (after the opening paren)
                                if args.child_count > 1:
                                    path_arg = args.children[1]
                                    path = _extract_string_literal(path_arg)
                                    
                                    if path:
                                        method = 'GET'  # Default
                                        # Check for methods parameter
                                        for i in range(2, args.child_count):
                                            arg = args.children[i]
                                            if arg.type == 'keyword_argument' and arg.child_count > 0:
                                                key_node = arg.children[0]
                                                if key_node.type == 'identifier' and key_node.text.decode('utf-8') == 'methods':
                                                    # Extract methods from list (at arg.children[2])
                                                    if arg.child_count > 2:
                                                        methods_list = arg.children[2]
                                                        if methods_list.type == 'list':
                                                            # Method string is usually at index 1 (after [)
                                                            for list_child in methods_list.children:
                                                                if list_child.type == 'string':
                                                                    method = _extract_string_literal(list_child)
                                                                    if method:
                                                                        method = method.upper()
                                                                        break
                                        
                                        line_num = decorator_node.start_point[0] + 1
                                        endpoints.append({
                                            "method": method,
                                            "path": path,
                                            "file": "",
                                            "line": line_num,
                                            "language": "python",
                                            "type": "endpoint",
                                            "framework": "flask"
                                        })
                        
                        # FastAPI: @app.get, @app.post, etc.
                        elif method_name in ['get', 'post', 'put', 'delete', 'patch']:
                            method = method_name.upper()
                            if call_node.child_count > 1:
                                args = call_node.children[1]  # argument_list
                                # Path is at args.children[1] (after the opening paren)
                                if args.child_count > 1:
                                    path_arg = args.children[1]
                                    path = _extract_string_literal(path_arg)
                                    
                                    if path:
                                        line_num = decorator_node.start_point[0] + 1
                                        endpoints.append({
                                            "method": method,
                                            "path": path,
                                            "file": "",
                                            "line": line_num,
                                            "language": "python",
                                            "type": "endpoint",
                                            "framework": "fastapi"
                                        })
    
    def traverse(node):
        # Handle standalone decorator nodes (Flask style)
        if node.type == 'decorator':
            process_decorator(node)
        
        # Handle decorated_definition nodes (FastAPI style)
        elif node.type == 'decorated_definition':
            # decorated_definition contains decorator(s) as children
            for child in node.children:
                if child.type == 'decorator':
                    process_decorator(child)
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return endpoints


def _find_javascript_endpoints_ast(tree, content: bytes) -> List[Dict]:
    """Find JavaScript/TypeScript endpoints using AST (Express, Next.js)"""
    endpoints = []
    root = tree.root_node
    content_str = content.decode('utf-8')
    seen = set()  # Track seen endpoints to avoid duplicates
    
    def traverse(node):
        # Express app.get/post/etc.
        if node.type == 'call_expression':
            if node.child_count >= 2:
                callee = node.children[0]
                if callee.type == 'member_expression':
                    # Check if it's app.get, router.post, etc.
                    # member_expression structure: [identifier (app), ., property_identifier (get)]
                    if callee.child_count >= 3:
                        obj_node = callee.children[0]
                        method_node = callee.children[2]  # property_identifier
                        
                        obj_text = obj_node.text.decode('utf-8') if obj_node.type == 'identifier' else ''
                        method_text = method_node.text.decode('utf-8') if method_node.type == 'property_identifier' else ''
                        
                        if obj_text in ['app', 'router', 'express'] and method_text in ['get', 'post', 'put', 'delete', 'patch']:
                            # Get path from arguments
                            # arguments structure: [(, string (path), ...]
                            if node.child_count > 1:
                                args = node.children[1]
                                if args.type == 'arguments' and args.child_count > 1:
                                    # Path is at index 1 (after opening paren)
                                    path_arg = args.children[1]
                                    path = _extract_string_literal(path_arg)
                                    
                                    if path:
                                        # Create unique key to avoid duplicates
                                        key = (method_text.upper(), path, node.start_point[0])
                                        if key not in seen:
                                            seen.add(key)
                                            line_num = node.start_point[0] + 1
                                            endpoints.append({
                                                "method": method_text.upper(),
                                                "path": path,
                                                "file": "",
                                                "line": line_num,
                                                "language": "javascript",
                                                "type": "endpoint",
                                                "framework": "express"
                                            })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return endpoints


def _find_go_endpoints_ast(tree, content: bytes) -> List[Dict]:
    """Find Go endpoints using AST"""
    endpoints = []
    root = tree.root_node
    content_str = content.decode('utf-8')
    
    def extract_go_string(node):
        """Extract string from Go interpreted_string_literal"""
        if node.type == 'interpreted_string_literal':
            # Look for interpreted_string_literal_content child
            for child in node.children:
                if child.type == 'interpreted_string_literal_content':
                    return child.text.decode('utf-8')
        return _extract_string_literal(node)
    
    def traverse(node):
        # Go router methods: router.Get, router.Post, etc.
        if node.type == 'call_expression':
            if node.child_count >= 2:
                callee = node.children[0]
                
                # Check for chained .Methods() call
                if callee.type == 'selector_expression' and callee.child_count > 0:
                    # This might be .Methods() chained after HandleFunc
                    # Check if the object is another call_expression
                    obj = callee.children[0]
                    method_name = callee.children[-1].text.decode('utf-8') if callee.child_count > 0 else ''
                    
                    if method_name == 'Methods' and obj.type == 'call_expression':
                        # This is .Methods() chained - extract method from args
                        args = node.children[1] if node.child_count > 1 else None
                        if args and args.type == 'argument_list' and args.child_count > 1:
                            method_arg = args.children[1]
                            method = extract_go_string(method_arg)
                            if method:
                                # Now get the path from the parent HandleFunc call
                                parent_args = obj.children[1] if obj.child_count > 1 else None
                                if parent_args and parent_args.type == 'argument_list' and parent_args.child_count > 1:
                                    path_arg = parent_args.children[1]
                                    path = extract_go_string(path_arg)
                                    if path:
                                        line_num = obj.start_point[0] + 1
                                        endpoints.append({
                                            "method": method.upper(),
                                            "path": path,
                                            "file": "",
                                            "line": line_num,
                                            "language": "go",
                                            "type": "endpoint",
                                            "framework": "gorilla/mux"
                                        })
                    
                    # Direct router methods: router.Get, router.Post, etc.
                    elif method_name in ['Get', 'Post', 'Put', 'Delete', 'Patch']:
                        # Get path from first argument
                        if node.child_count > 1:
                            args = node.children[1]
                            if args.type == 'argument_list' and args.child_count > 1:
                                path_arg = args.children[1]
                                path = extract_go_string(path_arg)
                                
                                if path:
                                    method = method_name.upper()
                                    line_num = node.start_point[0] + 1
                                    endpoints.append({
                                        "method": method,
                                        "path": path,
                                        "file": "",
                                        "line": line_num,
                                        "language": "go",
                                        "type": "endpoint",
                                        "framework": "net/http"
                                    })
                    
                    # HandleFunc without chained Methods
                    elif method_name == 'HandleFunc':
                        if node.child_count > 1:
                            args = node.children[1]
                            if args.type == 'argument_list' and args.child_count > 1:
                                path_arg = args.children[1]
                                path = extract_go_string(path_arg)
                                
                                if path:
                                    # Default to GET for HandleFunc without explicit method
                                    method = 'GET'
                                    line_num = node.start_point[0] + 1
                                    endpoints.append({
                                        "method": method,
                                        "path": path,
                                        "file": "",
                                        "line": line_num,
                                        "language": "go",
                                        "type": "endpoint",
                                        "framework": "net/http"
                                    })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return endpoints


def _find_java_endpoints_ast(tree, content: bytes) -> List[Dict]:
    """Find Java endpoints using AST (Spring Boot)"""
    endpoints = []
    root = tree.root_node
    content_str = content.decode('utf-8')
    
    # Track class-level @RequestMapping for path prefix
    class_path_prefix = ""
    
    def extract_java_string(node):
        """Extract string from Java string_literal"""
        if node.type == 'string_literal':
            # Look for string_fragment child
            for child in node.children:
                if child.type == 'string_fragment':
                    return child.text.decode('utf-8')
        return _extract_string_literal(node)
    
    def traverse(node):
        nonlocal class_path_prefix
        
        # Check for class-level @RequestMapping
        if node.type == 'class_declaration':
            # Look for @RequestMapping in modifiers
            for child in node.children:
                if child.type == 'modifiers':
                    for modifier in child.children:
                        if modifier.type == 'annotation':
                            if modifier.child_count >= 2:
                                name_node = modifier.children[1]
                                if name_node.type == 'identifier' and name_node.text.decode('utf-8') == 'RequestMapping':
                                    # Extract path from annotation_argument_list
                                    if modifier.child_count >= 3:
                                        args = modifier.children[2]
                                        if args.type == 'annotation_argument_list' and args.child_count > 1:
                                            path_arg = args.children[1]
                                            path = extract_java_string(path_arg)
                                            if path:
                                                class_path_prefix = path
        
        # Spring annotations: @GetMapping, @PostMapping, etc.
        if node.type == 'annotation':
            if node.child_count >= 2:
                name_node = node.children[1]
                if name_node.type == 'identifier':
                    annotation_name = name_node.text.decode('utf-8')
                    
                    method_map = {
                        'GetMapping': 'GET',
                        'PostMapping': 'POST',
                        'PutMapping': 'PUT',
                        'DeleteMapping': 'DELETE',
                        'PatchMapping': 'PATCH',
                    }
                    
                    if annotation_name in method_map:
                        method = method_map[annotation_name]
                        
                        # Extract path from annotation_argument_list
                        if node.child_count >= 3:
                            args = node.children[2]
                            if args.type == 'annotation_argument_list' and args.child_count > 1:
                                # Path is at index 1 (after opening paren)
                                path_arg = args.children[1]
                                path = extract_java_string(path_arg)
                                
                                if path:
                                    # Combine with class-level prefix if exists
                                    full_path = class_path_prefix + path if class_path_prefix else path
                                    line_num = node.start_point[0] + 1
                                    endpoints.append({
                                        "method": method,
                                        "path": full_path,
                                        "file": "",
                                        "line": line_num,
                                        "language": "java",
                                        "type": "endpoint",
                                        "framework": "spring"
                                    })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return endpoints


def _find_endpoints_regex_fallback(file_path: Path, content: str) -> List[Dict]:
    """Fallback to regex-based detection for unsupported languages or AST failures"""
    endpoints = []
    
    # Common endpoint patterns (regex fallback)
    ENDPOINT_PATTERNS = [
        # Python Flask @app.route
        (r'@app\.route\(["\']([^"\']+)["\'](?:.*?methods\s*=\s*\[["\']([^"\']+)["\'])?', 'python_flask_route'),
        
        # Python Flask/FastAPI method decorators
        (r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', 'python'),
        (r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', 'python'),
        
        # JavaScript/TypeScript Express
        (r'app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', 'javascript'),
        (r'router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', 'javascript'),
        
        # Go
        (r'(GET|POST|PUT|DELETE|PATCH)\(["\']([^"\']+)["\']', 'go'),
        
        # Java Spring
        (r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\(["\']([^"\']+)["\']', 'java'),
    ]
    
    for pattern, language in ENDPOINT_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            if language == 'python_flask_route':
                path = match.group(1)
                method = match.group(2) if match.group(2) else 'GET'
                method = method.upper()
            else:
                method = match.group(1).upper()
                path = match.group(2)
            
            line_num = content[:match.start()].count('\n') + 1
            
            endpoints.append({
                "method": method,
                "path": path,
                "file": str(file_path),
                "line": line_num,
                "language": language.replace('_flask_route', ''),
                "type": "endpoint"
            })
    
    return endpoints


def find_endpoints(file_path: Path, content: str) -> List[Dict]:
    """
    Find API endpoints in file content using AST parsing
    
    Strategy:
    1. Use AST parsing to extract what we can DETERMINISTICALLY understand
    2. Mark all results with confidence level:
       - 'confident': AST successfully parsed and extracted
       - 'uncertain': AST detected a pattern but couldn't fully parse it
       - 'unsupported': No AST parser available for this language
    
    Args:
        file_path: Path to file
        content: File content
        
    Returns:
        List of endpoint dictionaries with 'confidence' field
    """
    endpoints = []
    
    # Try AST parsing
    try:
        parser_info = _get_language_parser(file_path)
        if parser_info:
            language, parser = parser_info
            tree = parser.parse(bytes(content, 'utf-8'))
            
            if language == 'python':
                endpoints = _find_python_endpoints_ast(tree, bytes(content, 'utf-8'))
            elif language in ['javascript', 'typescript']:
                endpoints = _find_javascript_endpoints_ast(tree, bytes(content, 'utf-8'))
            elif language == 'go':
                endpoints = _find_go_endpoints_ast(tree, bytes(content, 'utf-8'))
            elif language == 'java':
                endpoints = _find_java_endpoints_ast(tree, bytes(content, 'utf-8'))
            
            # Mark all AST results as confident
            for endpoint in endpoints:
                endpoint['file'] = str(file_path)
                endpoint['confidence'] = 'confident'
                endpoint['detection_method'] = 'ast'
            
            # TODO: Add uncertain patterns detection
            # This would scan for patterns AST saw but couldn't fully parse
            # e.g., decorators without clear paths, dynamic route registration, etc.
            
            return endpoints
        else:
            # No AST parser available for this language
            return [{
                'file': str(file_path),
                'confidence': 'unsupported',
                'detection_method': 'none',
                'note': f'No AST parser available for {file_path.suffix}'
            }]
            
    except Exception as e:
        # AST parsing failed
        return [{
            'file': str(file_path),
            'confidence': 'error',
            'detection_method': 'none',
            'note': f'AST parsing failed: {str(e)}'
        }]
