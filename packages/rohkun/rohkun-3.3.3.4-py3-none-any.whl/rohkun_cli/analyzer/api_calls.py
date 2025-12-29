"""
API call detection - find API calls in frontend/client code using AST parsing
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
    }
    
    lang_info = language_map.get(ext)
    if lang_info and lang_info[1] is not None:
        parser = ts.Parser()
        parser.language = lang_info[1]
        return (lang_info[0], parser)
    
    return None


def _extract_string_literal(node) -> Optional[str]:
    """
    Extract string literal or template literal from AST node
    Uses AST structure to extract strings deterministically
    """
    if node.type == 'string':
        # Check if it's an f-string by looking for interpolation children
        has_interpolation = any(child.type == 'interpolation' for child in node.children)
        
        if has_interpolation:
            # F-string: extract static parts and mark variables
            parts = []
            for child in node.children:
                if child.type == 'string_content':
                    # Static text part
                    parts.append(child.text.decode('utf-8'))
                elif child.type == 'interpolation':
                    # Variable part - extract variable name
                    var_name = None
                    for subchild in child.children:
                        if subchild.type == 'identifier':
                            var_name = subchild.text.decode('utf-8')
                            break
                    if var_name:
                        parts.append(f'{{{var_name}}}')
                    else:
                        parts.append('{...}')  # Complex expression
            return ''.join(parts) if parts else None
        else:
            # Regular string - remove quotes
            text = node.text.decode('utf-8')
            if text.startswith('"') and text.endswith('"'):
                return text[1:-1]
            elif text.startswith("'") and text.endswith("'"):
                return text[1:-1]
            elif text.startswith('"""') and text.endswith('"""'):
                return text[3:-3]
            elif text.startswith("'''") and text.endswith("'''"):
                return text[3:-3]
                
    elif node.type == 'template_string':
        # JavaScript template literals: extract static parts and mark variables
        parts = []
        for child in node.children:
            if child.type == 'string_fragment':
                # Static text part
                parts.append(child.text.decode('utf-8'))
            elif child.type == 'template_substitution':
                # Variable part - extract variable name
                var_name = None
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        var_name = subchild.text.decode('utf-8')
                        break
                if var_name:
                    parts.append(f'${{{var_name}}}')
                else:
                    parts.append('${...}')  # Complex expression
        return ''.join(parts) if parts else None
        
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


def _find_python_api_calls_ast(tree, content: bytes) -> List[Dict]:
    """Find Python API calls using AST (requests, httpx, aiohttp)"""
    api_calls = []
    root = tree.root_node
    content_str = content.decode('utf-8')
    
    def traverse(node):
        # requests.get, requests.post, etc.
        if node.type == 'call':
            if node.child_count > 0:
                callee = node.children[0]
                if callee.type == 'attribute':
                    # Check if it's requests.get, httpx.get, etc.
                    obj_text = callee.children[0].text.decode('utf-8') if callee.child_count > 0 else ''
                    method_text = callee.children[-1].text.decode('utf-8') if callee.child_count > 1 else ''
                    
                    if obj_text in ['requests', 'httpx', 'aiohttp', 'client'] and method_text in ['get', 'post', 'put', 'delete', 'patch']:
                        # Get URL from first argument
                        if node.child_count > 1:
                            args = node.children[1]
                            if args.type == 'argument_list' and args.child_count > 1:
                                # Skip opening paren at index 0, URL is at index 1
                                first_arg = args.children[1]
                                url = _extract_string_literal(first_arg)
                                
                                if url:
                                    line_num = node.start_point[0] + 1
                                    api_calls.append({
                                        "method": method_text.upper(),
                                        "url": url,
                                        "file": "",
                                        "line": line_num,
                                        "library": obj_text,
                                        "type": "api_call"
                                    })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return api_calls


def _find_javascript_api_calls_ast(tree, content: bytes) -> List[Dict]:
    """Find JavaScript/TypeScript API calls using AST (fetch, axios, etc.)"""
    api_calls = []
    root = tree.root_node
    content_str = content.decode('utf-8')
    
    def traverse(node):
        # fetch() calls
        if node.type == 'call_expression':
            if node.child_count > 0:
                callee = node.children[0]
                
                # fetch(url)
                if callee.type == 'identifier' and callee.text.decode('utf-8') == 'fetch':
                    if node.child_count > 1:
                        args = node.children[1]
                        if args.type == 'arguments' and args.child_count > 1:
                            # Skip opening paren at index 0, URL is at index 1
                            first_arg = args.children[1]
                            url = _extract_string_literal(first_arg)
                            
                            if url:
                                # Check for method in second argument (options object)
                                method = 'GET'  # Default
                                # Options object would be at index 3 (after comma at index 2)
                                if args.child_count > 3:
                                    options = args.children[3]
                                    if options.type == 'object':
                                        for prop in options.children:
                                            if prop.type == 'pair' and prop.child_count >= 3:
                                                key = prop.children[0].text.decode('utf-8')
                                                if 'method' in key.lower():
                                                    # Value is at index 2 (after colon at index 1)
                                                    method_val = _extract_string_literal(prop.children[2])
                                                    if method_val:
                                                        method = method_val.upper()
                                
                                line_num = node.start_point[0] + 1
                                api_calls.append({
                                    "method": method,
                                    "url": url,
                                    "file": "",
                                    "line": line_num,
                                    "library": "fetch",
                                    "type": "api_call"
                                })
                
                # axios.get, axios.post, etc.
                elif callee.type == 'member_expression':
                    obj_text = callee.children[0].text.decode('utf-8') if callee.child_count > 0 else ''
                    method_text = callee.children[-1].text.decode('utf-8') if callee.child_count > 1 else ''
                    
                    if obj_text in ['axios', 'http', 'request'] and method_text in ['get', 'post', 'put', 'delete', 'patch']:
                        # Get URL from first argument
                        if node.child_count > 1:
                            args = node.children[1]
                            if args.type == 'arguments' and args.child_count > 1:
                                # Skip opening paren at index 0, URL is at index 1
                                first_arg = args.children[1]
                                url = _extract_string_literal(first_arg)
                                
                                if url:
                                    line_num = node.start_point[0] + 1
                                    api_calls.append({
                                        "method": method_text.upper(),
                                        "url": url,
                                        "file": "",
                                        "line": line_num,
                                        "library": obj_text,
                                        "type": "api_call"
                                    })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return api_calls


def _find_go_api_calls_ast(tree, content: bytes) -> List[Dict]:
    """Find Go API calls using AST (http.Get, http.Post, etc.)"""
    api_calls = []
    root = tree.root_node
    content_str = content.decode('utf-8')
    
    def traverse(node):
        # http.Get, http.Post, etc.
        if node.type == 'call_expression':
            if node.child_count >= 2:
                callee = node.children[0]
                if callee.type == 'selector_expression':
                    # Check for http.Get, http.Post, etc.
                    obj_text = callee.children[0].text.decode('utf-8') if callee.child_count > 0 else ''
                    method_text = callee.children[-1].text.decode('utf-8') if callee.child_count > 1 else ''
                    
                    if obj_text == 'http' and method_text in ['Get', 'Post', 'Put', 'Delete']:
                        # Get URL from first argument
                        if node.child_count > 1:
                            args = node.children[1]
                            if args.type == 'argument_list' and args.child_count > 0:
                                first_arg = args.children[0]
                                url = _extract_string_literal(first_arg)
                                
                                if url:
                                    line_num = node.start_point[0] + 1
                                    api_calls.append({
                                        "method": method_text.upper(),
                                        "url": url,
                                        "file": "",
                                        "line": line_num,
                                        "library": "http",
                                        "type": "api_call"
                                    })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return api_calls


def _find_api_calls_regex_fallback(file_path: Path, content: str) -> List[Dict]:
    """Fallback to regex-based detection for unsupported languages or AST failures"""
    api_calls = []
    
    # Common API call patterns (regex fallback)
    API_CALL_PATTERNS = [
        # fetch()
        (r'fetch\(["\']([^"\']+)["\']', 'fetch'),
        
        # axios
        (r'axios\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', 'axios'),
        
        # requests (Python)
        (r'requests\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', 'requests'),
        
        # http.get/post (Go)
        (r'http\.(Get|Post|Put|Delete)\(["\']([^"\']+)["\']', 'http'),
    ]
    
    for pattern, library in API_CALL_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        
        for match in matches:
            if library == 'fetch':
                method = 'GET'  # Default for fetch
                url = match.group(1)
            else:
                method = match.group(1).upper()
                url = match.group(2)
            
            line_num = content[:match.start()].count('\n') + 1
            
            api_calls.append({
                "method": method,
                "url": url,
                "file": str(file_path),
                "line": line_num,
                "library": library,
                "type": "api_call"
            })
    
    return api_calls


def find_api_calls(file_path: Path, content: str) -> List[Dict]:
    """
    Find API calls in file content using AST parsing
    
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
        List of API call dictionaries with 'confidence' field
    """
    api_calls = []
    
    # Try AST parsing
    try:
        parser_info = _get_language_parser(file_path)
        if parser_info:
            language, parser = parser_info
            tree = parser.parse(bytes(content, 'utf-8'))
            
            # Get confident findings
            if language == 'python':
                confident = _find_python_api_calls_ast(tree, bytes(content, 'utf-8'))
                uncertain = _find_uncertain_python_api_calls(tree, bytes(content, 'utf-8'))
            elif language in ['javascript', 'typescript']:
                confident = _find_javascript_api_calls_ast(tree, bytes(content, 'utf-8'))
                uncertain = _find_uncertain_javascript_api_calls(tree, bytes(content, 'utf-8'))
            elif language == 'go':
                confident = _find_go_api_calls_ast(tree, bytes(content, 'utf-8'))
                uncertain = []  # TODO: implement for Go
            else:
                confident = []
                uncertain = []
            
            # Mark confident results
            for api_call in confident:
                api_call['file'] = str(file_path)
                api_call['confidence'] = 'confident'
                api_call['detection_method'] = 'ast'
            
            # Mark uncertain results
            for api_call in uncertain:
                api_call['file'] = str(file_path)
                api_call['confidence'] = 'uncertain'
                api_call['detection_method'] = 'ast'
            
            return confident + uncertain
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


def _find_uncertain_python_api_calls(tree, content: bytes) -> List[Dict]:
    """Detect Python API call patterns that use dynamic values"""
    uncertain = []
    root = tree.root_node
    
    def get_reason(node):
        """Get human-readable reason why this is uncertain"""
        if node.type == 'identifier':
            var_name = node.text.decode('utf-8')
            return f"Variable '{var_name}' value unknown (imported or computed)"
        elif node.type == 'call':
            func_text = node.children[0].text.decode('utf-8') if node.child_count > 0 else 'function'
            return f"Result of function call: {func_text}()"
        elif node.type == 'subscript':
            return "Dictionary/array access with variable key"
        elif node.type == 'binary_operator':
            return "String concatenation with variables"
        elif node.type == 'attribute':
            return "Attribute access (e.g., config.base_url)"
        else:
            return f"Dynamic value ({node.type})"
    
    def traverse(node):
        if node.type == 'call':
            callee = node.children[0] if node.child_count > 0 else None
            if callee and callee.type == 'attribute':
                obj_text = callee.children[0].text.decode('utf-8') if callee.child_count > 0 else ''
                method_text = callee.children[-1].text.decode('utf-8') if callee.child_count > 1 else ''
                
                if obj_text in ['requests', 'httpx', 'client'] and method_text in ['get', 'post', 'put', 'delete', 'patch']:
                    if node.child_count > 1:
                        args = node.children[1]
                        if args.type == 'argument_list' and args.child_count > 1:
                            url_arg = args.children[1]
                            
                            # If URL is not a string or f-string, it's uncertain
                            if url_arg.type not in ['string']:
                                uncertain.append({
                                    'type': 'api_call',
                                    'line': node.start_point[0] + 1,
                                    'column': node.start_point[1],
                                    'reason': get_reason(url_arg),
                                    'code': node.text.decode('utf-8')[:80],
                                    'library': obj_text,
                                    'method': method_text.upper()
                                })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return uncertain


def _find_uncertain_javascript_api_calls(tree, content: bytes) -> List[Dict]:
    """Detect JavaScript API call patterns that use dynamic values"""
    uncertain = []
    root = tree.root_node
    
    def get_reason(node):
        """Get human-readable reason why this is uncertain"""
        if node.type == 'identifier':
            var_name = node.text.decode('utf-8')
            return f"Variable '{var_name}' value unknown (imported or computed)"
        elif node.type == 'call_expression':
            func_text = node.children[0].text.decode('utf-8') if node.child_count > 0 else 'function'
            return f"Result of function call: {func_text}()"
        elif node.type == 'subscript_expression':
            return "Array/object access with variable key"
        elif node.type == 'binary_expression':
            return "String concatenation with variables"
        elif node.type == 'member_expression':
            return "Property access (e.g., config.baseUrl)"
        else:
            return f"Dynamic value ({node.type})"
    
    def traverse(node):
        # fetch() with non-literal URL
        if node.type == 'call_expression':
            callee = node.children[0] if node.child_count > 0 else None
            
            if callee and callee.type == 'identifier' and callee.text.decode('utf-8') == 'fetch':
                if node.child_count > 1:
                    args = node.children[1]
                    if args.type == 'arguments' and args.child_count > 1:
                        url_arg = args.children[1]
                        
                        if url_arg.type not in ['string', 'template_string']:
                            uncertain.append({
                                'type': 'api_call',
                                'line': node.start_point[0] + 1,
                                'column': node.start_point[1],
                                'reason': get_reason(url_arg),
                                'code': node.text.decode('utf-8')[:80],
                                'library': 'fetch',
                                'method': 'GET'
                            })
            
            # axios.get/post/etc with non-literal URL
            elif callee and callee.type == 'member_expression':
                obj_text = callee.children[0].text.decode('utf-8') if callee.child_count > 0 else ''
                method_text = callee.children[-1].text.decode('utf-8') if callee.child_count > 1 else ''
                
                if obj_text in ['axios', 'http'] and method_text in ['get', 'post', 'put', 'delete', 'patch']:
                    if node.child_count > 1:
                        args = node.children[1]
                        if args.type == 'arguments' and args.child_count > 1:
                            url_arg = args.children[1]
                            
                            if url_arg.type not in ['string', 'template_string']:
                                uncertain.append({
                                    'type': 'api_call',
                                    'line': node.start_point[0] + 1,
                                    'column': node.start_point[1],
                                    'reason': get_reason(url_arg),
                                    'code': node.text.decode('utf-8')[:80],
                                    'library': obj_text,
                                    'method': method_text.upper()
                                })
        
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return uncertain
