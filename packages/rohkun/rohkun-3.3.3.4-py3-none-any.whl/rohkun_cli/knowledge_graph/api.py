"""
Knowledge Graph API - Data layer for graph visualizations
Generates graph data from JSON reports
No UI code here - just data transformation
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict
from datetime import datetime

# Node sizing constants
MIN_NODE_SIZE = 10
MAX_NODE_SIZE = 60
BASE_ENDPOINT_SIZE = 15
CONNECTION_SIZE_MULTIPLIER = 3
BASE_FILE_SIZE = 20
ENDPOINT_SIZE_MULTIPLIER = 2
FUNCTION_SIZE_MULTIPLIER = 1

# API call node sizing
BASE_API_CALL_SIZE = 12

# Confidence score thresholds for edge styling
CONFIDENCE_HIGH = 95
CONFIDENCE_MEDIUM_HIGH = 70
CONFIDENCE_MEDIUM = 50
DEFAULT_CONFIDENCE_SCORE = 50


class KnowledgeGraphAPI:
    """
    API for generating graph data from reports
    All methods return pure data structures (no HTML/UI)
    """
    
    def __init__(self, report: Dict):
        """
        Initialize with a report
        
        Args:
            report: Report dictionary from JSON file
        """
        self.report = report
        self.endpoints = report.get('endpoints', [])
        self.api_calls = report.get('api_calls', [])
        self.connections = report.get('connections', [])
        self.dependencies = report.get('dependencies', {})
        self.blast_radius = report.get('blast_radius', [])
        self.high_impact_nodes = report.get('high_impact_nodes', [])
    
    def get_api_connections_graph(self) -> Dict:
        """
        Generate API connections graph (functions)
        Nodes: Functions that define endpoints + functions that call APIs
        Edges: Function calls between them
        
        Returns:
            Dict with nodes and edges for vis.js Network
        """
        nodes = {}
        edges = []
        node_id_counter = 0
        
        # v2.0 Cyber-Professional color scheme
        method_colors = {
            'GET': '#3b82f6',      # blue-500 - Safe, read operations
            'POST': '#00FF94',     # Neon Mint - Create operations
            'PUT': '#FFE600',      # Electric Yellow - Update operations
            'DELETE': '#FF003C',   # Cyberpunk Red - Destructive operations
            'PATCH': '#00F0FF',    # Neon Cyan - Partial updates
            'OPTIONS': '#6b7280',  # gray-500 - Metadata operations
            'HEAD': '#6b7280',     # gray-500 - Metadata operations
            'UNKNOWN': '#4b5563'   # gray-600 - Unknown methods
        }
        
        # Track function nodes (endpoint functions)
        endpoint_functions = {}  # function_name -> node_id
        
        # Build endpoint function nodes
        for endpoint in self.endpoints:
            method = (endpoint.get('method') or 'UNKNOWN').upper()
            path = endpoint.get('path') or 'unknown'
            file_path = endpoint.get('file') or 'unknown'
            line = endpoint.get('line') or 0
            
            # Extract function name from file/line context
            # For now, use endpoint path as identifier
            func_key = f"{method}:{path}"
            
            if func_key not in endpoint_functions:
                node_id = f"endpoint_func_{node_id_counter}"
                node_id_counter += 1
                
                # Count connections to this endpoint (will check for actual edges later)
                connection_count = sum(
                    1 for conn in self.connections
                    if conn.get('endpoint', {}).get('method') == method
                    and conn.get('endpoint', {}).get('path') == path
                )
                
                # Check if high impact
                is_high_impact = any(
                    impact.get('target', '') in path or
                    impact.get('target', '') == func_key
                    for impact in self.high_impact_nodes
                )
                
                color = method_colors.get(method, method_colors['UNKNOWN'])
                if is_high_impact:
                    color = '#BC13FE'  # Hot Pink - High impact nodes
                # Orphaned check happens AFTER edges are built
                
                size = BASE_ENDPOINT_SIZE + (connection_count * CONNECTION_SIZE_MULTIPLIER)
                size = max(MIN_NODE_SIZE, min(size, MAX_NODE_SIZE))
                
                endpoint_functions[func_key] = node_id
                nodes[node_id] = {
                    'id': node_id,
                    'label': f"{method} {path}",
                    'title': f"Endpoint Function\n{method} {path}\nFile: {file_path}\nLine: {line}\nConnections: {connection_count}",
                    'type': 'endpoint_function',
                    'method': method,
                    'path': path,
                    'file': file_path,
                    'line': line,
                    'value': size,
                    'size': size,
                    'color': {
                        'background': color,
                        'border': color,
                        'highlight': {'background': color, 'border': '#ffffff'}
                    },
                    'font': {'color': '#ffffff', 'size': 13, 'face': 'JetBrains Mono'},
                    'borderWidth': 2,
                    'connections': connection_count,
                    'high_impact': is_high_impact
                }
        
        # Build API call function nodes
        api_call_functions = {}  # function_key -> node_id
        
        for api_call in self.api_calls:
            method = (api_call.get('method') or 'UNKNOWN').upper()
            url = api_call.get('url') or 'unknown'
            file_path = api_call.get('file') or 'unknown'
            line = api_call.get('line') or 0
            
            # Use file:line as function identifier (since we don't have function names yet)
            func_key = f"api_call:{file_path}:{line}"
            
            if func_key not in api_call_functions:
                node_id = f"api_call_func_{node_id_counter}"
                node_id_counter += 1
                
                color = method_colors.get(method, method_colors['UNKNOWN'])
                size = BASE_API_CALL_SIZE
                # Orphaned check happens AFTER edges are built
                
                api_call_functions[func_key] = node_id
                nodes[node_id] = {
                    'id': node_id,
                    'label': f"{method} {url[:30]}...",
                    'title': f"API Call Function\n{method} {url}\nFile: {file_path}\nLine: {line}",
                    'type': 'api_call_function',
                    'method': method,
                    'url': url,
                    'file': file_path,
                    'line': line,
                    'value': size,
                    'size': size,
                    'color': {
                        'background': color,
                        'border': color,
                        'highlight': {'background': color, 'border': '#ffffff'}
                    },
                    'font': {'color': '#ffffff', 'size': 12, 'face': 'JetBrains Mono'},
                    'borderWidth': 2,
                    'connections': 0
                }
        
        # Build edges from connections
        edge_set = set()
        
        for conn in self.connections:
            endpoint = conn.get('endpoint', {})
            api_call = conn.get('api_call', {})
            
            endpoint_key = f"{endpoint.get('method', 'GET')}:{endpoint.get('path', 'unknown')}"
            api_call_key = f"api_call:{api_call.get('file', 'unknown')}:{api_call.get('line', 0)}"
            
            if endpoint_key in endpoint_functions and api_call_key in api_call_functions:
                # Arrow direction: API Call → Endpoint (API call is used by endpoint)
                # This means: endpoint depends on/uses the API call
                api_call_id = api_call_functions[api_call_key]
                endpoint_id = endpoint_functions[endpoint_key]
                
                edge_key = (api_call_id, endpoint_id)
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    
                    confidence_score = conn.get('confidence_score', DEFAULT_CONFIDENCE_SCORE)
                    
                    # v2.0 Neon edge colors based on confidence
                    if confidence_score >= CONFIDENCE_HIGH:
                        edge_color = '#00FF94'  # Neon Mint - high confidence
                        opacity = 0.8
                    elif confidence_score >= CONFIDENCE_MEDIUM_HIGH:
                        edge_color = '#7c3aed'  # purple - medium-high
                        opacity = 0.6
                    elif confidence_score >= CONFIDENCE_MEDIUM:
                        edge_color = '#8b5cf6'  # purple light - medium
                        opacity = 0.4
                    else:
                        edge_color = '#333333'  # Dark gray - low
                        opacity = 0.3
                    
                    edges.append({
                        'from': api_call_id,  # API call is the source
                        'to': endpoint_id,    # Endpoint is the target (endpoint uses API call)
                        'label': api_call.get('method', 'GET'),
                        'arrows': 'to',
                        'color': {
                            'color': edge_color,
                            'opacity': opacity,
                            'highlight': '#ffffff'
                        },
                        'width': max(1, int(confidence_score / 50)),
                        'smooth': {'type': 'continuous', 'roundness': 0.5},
                        'confidence': conn.get('confidence', 'medium'),
                        'confidence_score': confidence_score
                    })
        
        # Deterministic orphan detection - only mark as orphaned if CERTAIN
        # A node is orphaned ONLY if:
        # 1. It has NO edges connected (deterministic check)
        # 2. AND it's not high-impact
        # 3. AND we've reviewed all connections (edges are fully built)
        connected_node_ids = set()
        for edge in edges:
            connected_node_ids.add(edge['from'])
            connected_node_ids.add(edge['to'])
        
        # Also check if node has any potential connections in the connections array
        # (even if they didn't result in edges due to low confidence)
        nodes_with_potential_connections = set()
        for conn in self.connections:
            endpoint = conn.get('endpoint', {})
            api_call = conn.get('api_call', {})
            
            endpoint_key = f"{endpoint.get('method', 'GET')}:{endpoint.get('path', 'unknown')}"
            api_call_key = f"api_call:{api_call.get('file', 'unknown')}:{api_call.get('line', 0)}"
            
            # Check if this connection exists in our nodes (even if edge wasn't created)
            if endpoint_key in endpoint_functions:
                nodes_with_potential_connections.add(endpoint_functions[endpoint_key])
            if api_call_key in api_call_functions:
                nodes_with_potential_connections.add(api_call_functions[api_call_key])
        
        # Mark orphaned nodes (nodes with NO edges AND no potential connections)
        orphaned_count = 0
        for node_id, node in nodes.items():
            has_edges = node_id in connected_node_ids
            has_potential = node_id in nodes_with_potential_connections
            
            # Only mark as orphaned if CERTAIN: no edges AND no potential connections
            if not has_edges and not has_potential:
                if not node.get('high_impact', False):  # Don't override high impact
                    node['color'] = {
                        'background': '#374151',  # gray-700 - Orphaned
                        'border': '#374151',
                        'highlight': {'background': '#374151', 'border': '#ffffff'}
                    }
                    orphaned_count += 1
        
        return {
            'nodes': list(nodes.values()),
            'edges': edges,
            'summary': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'endpoint_functions': len([n for n in nodes.values() if n['type'] == 'endpoint_function']),
                'api_call_functions': len([n for n in nodes.values() if n['type'] == 'api_call_function']),
                'high_impact': len([n for n in nodes.values() if n.get('high_impact', False)]),
                'orphaned': orphaned_count
            }
        }
    
    def get_function_dependency_graph(self) -> Dict:
        """
        Generate function-level dependency graph based on actual function calls
        Nodes: All functions (defined functions)
        Edges: Function calls (which function calls which)
        
        Returns:
            Dict with nodes and edges for vis.js Network
        """
        nodes = {}
        edges = []
        node_id_counter = 0
        
        # Color scheme for functions
        FUNCTION_COLOR = '#7c3aed'  # purple - Regular functions
        IMPORTED_COLOR = '#00F0FF'  # Neon Cyan - Imported functions
        CALLER_COLOR = '#FFE600'    # Electric Yellow - Functions that call others
        ORPHAN_COLOR = '#374151'    # gray-700 - Orphaned functions
        HIGH_IMPACT_COLOR = '#BC13FE'  # Hot Pink - High impact
        
        function_calls = self.dependencies.get('function_calls', [])
        function_defs = self.dependencies.get('function_definitions', [])
        imports = self.dependencies.get('imports', [])
        
        # Track all functions by file:line or file:name
        function_nodes = {}  # function_key -> node_id
        
        # 1. Create nodes for all defined functions
        for func_def in function_defs:
            func_name = func_def.get('name', 'unknown')
            file_path = func_def.get('file', 'unknown')
            line = func_def.get('line', 0)
            
            func_key = f"{file_path}:{func_name}"
            
            if func_key not in function_nodes:
                node_id = f"func_{node_id_counter}"
                node_id_counter += 1
                
                # Check if high impact
                is_high_impact = any(
                    impact.get('target_file', '') == file_path
                    for impact in self.high_impact_nodes
                )
                
                color = HIGH_IMPACT_COLOR if is_high_impact else FUNCTION_COLOR
                size = BASE_FILE_SIZE
                
                function_nodes[func_key] = node_id
                nodes[node_id] = {
                    'id': node_id,
                    'label': func_name,
                    'title': f"Function: {func_name}\nFile: {Path(file_path).name}\nLine: {line}",
                    'type': 'function',
                    'name': func_name,
                    'file': file_path,
                    'line': line,
                    'value': size,
                    'size': size,
                    'color': {
                        'background': color,
                        'border': color,
                        'highlight': {'background': color, 'border': '#ffffff'}
                    },
                    'font': {'color': '#ffffff', 'size': 13, 'face': 'JetBrains Mono'},
                    'borderWidth': 2,
                    'high_impact': is_high_impact
                }
        
        # 2. Create nodes for called functions (that might not be defined in scanned files)
        for func_call in function_calls:
            # Support both 'function' and 'callee' field names
            func_name = func_call.get('function') or func_call.get('callee') or None
            file_path = func_call.get('file', 'unknown')
            line = func_call.get('line', 0)
            
            # Skip if function name is missing, empty, or 'unknown'
            if not func_name or func_name == 'unknown' or func_name.strip() == '':
                continue
            
            # Create a node for the called function if it doesn't exist
            # Use just the function name as key for external/library functions
            func_key = f"call:{func_name}"
            
            if func_key not in function_nodes:
                # Check if this is a defined function in our codebase
                matching_def = None
                callee_file = func_call.get('callee_file', 'unknown')
                
                # First try to match by name and file (if callee_file is provided)
                if callee_file != 'unknown':
                    for func_def in function_defs:
                        if func_def.get('name') == func_name and func_def.get('file') == callee_file:
                            matching_def = func_def
                            break
                
                # If not found, try to match by name only
                if not matching_def:
                    for func_def in function_defs:
                        if func_def.get('name') == func_name:
                            matching_def = func_def
                            break
                
                if matching_def:
                    # This function IS defined - use the existing node from step 1
                    # Don't create a new node, just map the func_key to the existing node
                    existing_key = f"{matching_def.get('file')}:{matching_def.get('name')}"
                    if existing_key in function_nodes:
                        function_nodes[func_key] = function_nodes[existing_key]
                else:
                    # External/library function - not found in our codebase
                    node_id = f"func_{node_id_counter}"
                    node_id_counter += 1
                    
                    color = IMPORTED_COLOR
                    size = BASE_API_CALL_SIZE
                    
                    function_nodes[func_key] = node_id
                    nodes[node_id] = {
                        'id': node_id,
                        'label': func_name,
                        'title': f"Called Function: {func_name}\n(External/Library)" + (f"\nFile: {callee_file}" if callee_file != 'unknown' else ""),
                        'type': 'external_function',
                        'name': func_name,
                        'file': callee_file if callee_file != 'unknown' else None,
                        'file_path': callee_file if callee_file != 'unknown' else None,
                        'value': size,
                        'size': size,
                        'color': {
                            'background': color,
                            'border': color,
                            'highlight': {'background': color, 'border': '#ffffff'}
                        },
                        'font': {'color': '#ffffff', 'size': 12, 'face': 'JetBrains Mono'},
                        'borderWidth': 2
                    }
        
        # 3. Create edges from function calls
        edge_set = set()
        
        for func_call in function_calls:
            caller_file = func_call.get('file', 'unknown')
            caller_line = func_call.get('line', 0)
            # Support both 'function' and 'callee' field names
            callee_name = func_call.get('function') or func_call.get('callee') or None
            
            # Skip if callee name is missing, empty, or 'unknown'
            if not callee_name or callee_name == 'unknown' or callee_name.strip() == '':
                continue
            
            # Find the caller function (the function that contains this call)
            # Support both 'caller' field and finding by file/line
            caller_func = None
            caller_name = func_call.get('caller')
            if caller_name:
                # Use explicit caller field if available
                for func_def in function_defs:
                    if func_def.get('name') == caller_name and func_def.get('file') == caller_file:
                        caller_func = func_def
                        break
            else:
                # Fallback: find caller by file and line
                for func_def in function_defs:
                    if func_def.get('file') == caller_file:
                        # Check if the call is within this function's scope
                        # (simplified: just check if call is after function definition)
                        if func_def.get('line', 0) <= caller_line:
                            caller_func = func_def
            
            if caller_func:
                caller_key = f"{caller_func.get('file')}:{caller_func.get('name')}"
                
                # Find the callee function
                callee_key = None
                callee_file = func_call.get('callee_file')
                if callee_file:
                    # Try to find by name and file
                    for func_def in function_defs:
                        if func_def.get('name') == callee_name and func_def.get('file') == callee_file:
                            callee_key = f"{func_def.get('file')}:{func_def.get('name')}"
                            break
                
                if not callee_key:
                    # Try to find by name only
                    for func_def in function_defs:
                        if func_def.get('name') == callee_name:
                            callee_key = f"{func_def.get('file')}:{func_def.get('name')}"
                            break
                
                if not callee_key:
                    # External function
                    callee_key = f"call:{callee_name}"
                
                if caller_key in function_nodes and callee_key in function_nodes:
                    caller_id = function_nodes[caller_key]
                    callee_id = function_nodes[callee_key]
                    
                    edge_key = (caller_id, callee_id)
                    if edge_key not in edge_set:
                        edge_set.add(edge_key)
                        
                        edges.append({
                            'from': caller_id,
                            'to': callee_id,
                            'label': 'calls',
                            'arrows': 'to',
                            'color': {
                                'color': '#7c3aed',  # purple
                                'opacity': 0.6,
                                'highlight': '#ffffff'
                            },
                            'width': 2,
                            'smooth': {'type': 'continuous', 'roundness': 0.5}
                        })
        
        # 4. Update colors for caller functions
        caller_ids = set(edge['from'] for edge in edges)
        for node_id in caller_ids:
            if node_id in nodes and not nodes[node_id].get('high_impact', False):
                nodes[node_id]['color'] = {
                    'background': CALLER_COLOR,
                    'border': CALLER_COLOR,
                    'highlight': {'background': CALLER_COLOR, 'border': '#ffffff'}
                }
        
        # 5. Mark orphaned nodes
        connected_node_ids = set()
        for edge in edges:
            connected_node_ids.add(edge['from'])
            connected_node_ids.add(edge['to'])
        
        orphaned_count = 0
        for node_id, node in nodes.items():
            if node_id not in connected_node_ids:
                if not node.get('high_impact', False):
                    node['color'] = {
                        'background': ORPHAN_COLOR,
                        'border': ORPHAN_COLOR,
                        'highlight': {'background': ORPHAN_COLOR, 'border': '#ffffff'}
                    }
                    orphaned_count += 1
        
        return {
            'nodes': list(nodes.values()),
            'edges': edges,
            'summary': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'defined_functions': len([n for n in nodes.values() if n['type'] == 'function']),
                'external_functions': len([n for n in nodes.values() if n['type'] == 'external_function']),
                'high_impact': len([n for n in nodes.values() if n.get('high_impact', False)]),
                'orphaned': orphaned_count
            }
        }
    
    def get_dependency_graph(self) -> Dict:
        """
        Generate dependency graph (files)
        Nodes: Files
        Edges: Import/dependency relationships
        
        Returns:
            Dict with nodes and edges for vis.js Network
        """
        nodes = {}
        edges = []
        node_id_counter = 0
        
        imports = self.dependencies.get('imports', [])
        function_calls = self.dependencies.get('function_calls', [])
        function_defs = self.dependencies.get('function_definitions', [])
        
        # Collect all unique files
        all_files = set()
        
        # From endpoints
        for endpoint in self.endpoints:
            file_path = endpoint.get('file')
            if file_path:
                all_files.add(file_path)
        
        # From API calls
        for api_call in self.api_calls:
            file_path = api_call.get('file')
            if file_path:
                all_files.add(file_path)
        
        # From imports
        for imp in imports:
            file_path = imp.get('file')
            if file_path:
                all_files.add(file_path)
            imported = imp.get('imported')
            if imported:
                # Try to resolve imported module to file
                # For now, just track the import
                pass
        
        # From function definitions
        for func_def in function_defs:
            file_path = func_def.get('file')
            if file_path:
                all_files.add(file_path)
        
        # Create file nodes
        file_to_node_id = {}
        
        # Strict Exclusion Policy: Only allow code files in the graph
        # Exclude docs, config, data, etc.
        ALLOWED_EXTENSIONS = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.rb', '.php', '.cs', '.rs', '.c', '.cpp', 
            '.html', '.css', '.scss', '.sql', '.sh', '.bat'
        }
        
        for file_path in all_files:
            # Skip excluded extensions
            ext = Path(file_path).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue
                
            node_id = f"file_{node_id_counter}"
            node_id_counter += 1
            file_to_node_id[file_path] = node_id
            
            # Count dependencies (how many files import this)
            import_count = sum(1 for imp in imports if imp.get('imported') and file_path in str(imp.get('imported', '')))
            
            # Check if high impact (from blast radius)
            is_high_impact = any(
                br.get('target_file') == file_path or
                file_path in br.get('affected_files', [])
                for br in self.blast_radius
            )
            
            # Get file extension for color coding
            ext = Path(file_path).suffix.lower()
            color = self._get_file_color(ext)
            
            # Size based on number of endpoints/functions in file
            endpoint_count = sum(1 for ep in self.endpoints if ep.get('file') == file_path)
            func_count = sum(1 for f in function_defs if f.get('file') == file_path)
            
            if is_high_impact:
                color = '#BC13FE'  # Hot Pink - High impact files
            # Orphaned check happens AFTER edges are built
            
            size = BASE_FILE_SIZE + (endpoint_count * ENDPOINT_SIZE_MULTIPLIER) + (func_count * FUNCTION_SIZE_MULTIPLIER)
            size = max(MIN_NODE_SIZE, min(size, MAX_NODE_SIZE))
            
            nodes[node_id] = {
                'id': node_id,
                'label': Path(file_path).name,
                'title': f"File: {file_path}\nEndpoints: {endpoint_count}\nFunctions: {func_count}\nImports: {import_count}",
                'type': 'file',
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'extension': ext,
                'value': size,
                'size': size,
                'color': {
                    'background': color,
                    'border': color,
                    'highlight': {'background': color, 'border': '#ffffff'}
                },
                'font': {'color': '#ffffff', 'size': 13, 'face': 'JetBrains Mono'},
                'borderWidth': 2,
                'endpoint_count': endpoint_count,
                'function_count': func_count,
                'import_count': import_count,
                'high_impact': is_high_impact
            }
        
        # Build edges from imports
        edge_set = set()
        
        # Common library names to exclude (these are external packages, not project files)
        # This is a basic list - could be expanded or made configurable
        EXCLUDED_LIBRARIES = {
            'flask', 'jsonify', 'request', 'json', 'os', 'sys', 'pathlib', 'typing',
            'collections', 'datetime', 're', 'math', 'random', 'time', 'uuid',
            'requests', 'urllib', 'http', 'socket', 'threading', 'multiprocessing',
            'asyncio', 'aiohttp', 'fastapi', 'django', 'sqlalchemy', 'pandas', 'numpy',
            'react', 'vue', 'angular', 'express', 'axios', 'fetch', 'lodash', 'jquery',
            'fs', 'path', 'util', 'events', 'stream', 'buffer', 'crypto', 'http', 'https',
            'net', 'dns', 'url', 'querystring', 'zlib', 'readline', 'child_process'
        }
        
        for imp in imports:
            source_file = imp.get('file')
            imported = imp.get('imported')
            
            if not source_file or not imported:
                continue
            
            # Skip if this is a known library (not a project file)
            # Check if imported name is a known library
            imported_lower = imported.lower().split('.')[0]  # Get base module name
            if imported_lower in EXCLUDED_LIBRARIES:
                continue
            
            # Try to find target file (simplified - would need module resolution)
            # Only create edges for actual project files, not libraries
            target_file = None
            for file_path in all_files:
                # More strict matching: imported name must match the file stem exactly
                # or be a clear substring match (not just any substring)
                file_stem = Path(file_path).stem.lower()
                imported_base = imported_lower
                
                # Exact match or the imported name is the file stem
                if file_stem == imported_base:
                    target_file = file_path
                    break
                # Or if it's a relative import (starts with .) and matches
                elif imported.startswith('.') and file_stem == imported_base.lstrip('.'):
                    target_file = file_path
                    break
            
            if target_file and source_file in file_to_node_id and target_file in file_to_node_id:
                source_id = file_to_node_id[source_file]
                target_id = file_to_node_id[target_file]
                
                edge_key = (source_id, target_id)
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    
                    edges.append({
                        'from': source_id,
                        'to': target_id,
                        'label': 'imports',
                        'arrows': 'to',
                        'color': {
                            'color': '#7c3aed',  # purple - Import relationships
                            'opacity': 0.5,
                            'highlight': '#ffffff'
                        },
                        'width': 1,
                        'smooth': {'type': 'continuous', 'roundness': 0.3},
                        'dashes': False,
                        'type': 'import'
                    })
        
        # Also create edges for files that have endpoints calling APIs in other files
        for conn in self.connections:
            endpoint_file = conn.get('endpoint', {}).get('file')
            api_call_file = conn.get('api_call', {}).get('file')
            
            if endpoint_file and api_call_file and endpoint_file != api_call_file:
                if endpoint_file in file_to_node_id and api_call_file in file_to_node_id:
                    source_id = file_to_node_id[endpoint_file]
                    target_id = file_to_node_id[api_call_file]
                    
                    edge_key = (source_id, target_id)
                    if edge_key not in edge_set:
                        edge_set.add(edge_key)
                        
                        edges.append({
                            'from': source_id,
                            'to': target_id,
                            'label': 'calls',
                            'arrows': 'to',
                            'color': {
                                'color': '#7c3aed',  # purple - API call relationships
                                'opacity': 0.5,
                                'highlight': '#ffffff'
                            },
                            'width': 1,
                            'smooth': {'type': 'continuous', 'roundness': 0.5},
                            'dashes': True,
                            'type': 'api_call'
                        })
        
        # Deterministic orphan detection for files - only mark if CERTAIN
        connected_node_ids = set()
        for edge in edges:
            connected_node_ids.add(edge['from'])
            connected_node_ids.add(edge['to'])
        
        # Check if file has any potential dependencies (even if edge wasn't created)
        files_with_potential_deps = set()
        for imp in imports:
            source_file = imp.get('file')
            imported = imp.get('imported')
            if source_file and source_file in file_to_node_id:
                files_with_potential_deps.add(file_to_node_id[source_file])
        
        # Also check connections
        for conn in self.connections:
            endpoint_file = conn.get('endpoint', {}).get('file')
            api_call_file = conn.get('api_call', {}).get('file')
            if endpoint_file and endpoint_file in file_to_node_id:
                files_with_potential_deps.add(file_to_node_id[endpoint_file])
            if api_call_file and api_call_file in file_to_node_id:
                files_with_potential_deps.add(file_to_node_id[api_call_file])
        
        # Mark orphaned files (files with NO edges AND no potential dependencies)
        # STRICT MODE: Only mark supported code files as orphaned. Others are just "Unknown/Standalone"
        orphaned_count = 0
        supported_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.rb', '.php', '.cs', '.rs', '.c', '.cpp'}
        
        for node_id, node in nodes.items():
            has_edges = node_id in connected_node_ids
            has_potential = node_id in files_with_potential_deps
            
            # Only mark as orphaned if CERTAIN: no edges AND no potential dependencies
            if not has_edges and not has_potential:
                ext = node.get('extension', '').lower()
                
                # If it's a supported code file, we expect connections. Absence means ORPHANED.
                if ext in supported_extensions:
                    if not node.get('high_impact', False):  # Don't override high impact
                        node['color'] = {
                            'background': '#374151',  # gray-700 - Orphaned
                            'border': '#374151',
                            'highlight': {'background': '#374151', 'border': '#ffffff'}
                        }
                        node['is_orphaned'] = True # Mark explicit flag
                        orphaned_count += 1
                else:
                    # For non-code files (config, json, yaml, etc.), we don't assert they are orphaned.
                    # They might be used dynamically. Leave them as "Unknown/Other" (default color).
                    node['is_orphaned'] = False
        
        return {
            'nodes': list(nodes.values()),
            'edges': edges,
            'summary': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'files': len(nodes),
                'high_impact': len([n for n in nodes.values() if n.get('high_impact', False)]),
                'orphaned': orphaned_count
            }
        }
    
    def get_snapshot_comparison(self, previous_report: Dict) -> Dict:
        """
        Compare current report with previous report
        Returns diff data for visualization
        
        Args:
            previous_report: Previous report dictionary
            
        Returns:
            Dict with added/removed/changed items
        """
        from ..report.comparison import compare_reports
        
        comparison = compare_reports(self.report, previous_report)
        
        # Extract node IDs for highlighting
        added_endpoint_keys = set(comparison.get('added_endpoints', []))
        removed_endpoint_keys = set(comparison.get('removed_endpoints', []))
        added_connection_keys = set(comparison.get('added_connections', []))
        removed_connection_keys = set(comparison.get('removed_connections', []))
        
        return {
            'comparison': comparison,
            'added_endpoints': list(added_endpoint_keys),
            'removed_endpoints': list(removed_endpoint_keys),
            'added_connections': list(added_connection_keys),
            'removed_connections': list(removed_connection_keys),
            'metric_changes': comparison.get('metric_changes', {}),
            'blast_radius_changes': comparison.get('blast_radius_changes', {})
        }
    
    def _get_file_color(self, extension: str) -> str:
        """Get color for file based on extension - v2.0 Neon colors"""
        color_map = {
            '.py': '#00F0FF',      # Neon Cyan - Python
            '.js': '#F59E0B',      # Amber - JavaScript (softer, more professional than yellow)
            '.ts': '#3178c6',      # TypeScript blue
            '.jsx': '#61dafb',     # React cyan
            '.tsx': '#3178c6',     # TypeScript blue
            '.go': '#00add8',      # Go cyan
            '.java': '#ed8b00',    # Java orange
            '.rb': '#cc342d',      # Ruby red
            '.php': '#777bb4',     # PHP purple
            '.cs': '#239120',      # C# green
            '.rs': '#ce422b',      # Rust red
            '.c': '#00599c',       # C blue
            '.cpp': '#00599c',     # C++ blue
        }
        return color_map.get(extension, '#6b7280')  # gray-500 for unknown


def load_report_from_file(report_path: Path) -> Optional[Dict]:
    """
    Load report JSON from file
    
    Args:
        report_path: Path to JSON report file
        
    Returns:
        Report dictionary or None if loading fails
    """
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[KG-API] Report file not found: {report_path}", file=sys.stderr, flush=True)
        return None
    except PermissionError:
        print(f"[KG-API] Permission denied reading report: {report_path}", file=sys.stderr, flush=True)
        return None
    except json.JSONDecodeError as e:
        print(f"[KG-API] Invalid JSON in report {report_path}: {e}", file=sys.stderr, flush=True)
        return None
    except Exception as e:
        print(f"[KG-API] Unexpected error loading report {report_path}: {e}", file=sys.stderr, flush=True)
        return None


def generate_api_graph_data(report_path: Path) -> Dict:
    """
    Generate API connections graph data from report file
    
    Args:
        report_path: Path to JSON report file
        
    Returns:
        Graph data dict
    """
    report = load_report_from_file(report_path)
    if not report:
        return {'error': 'Failed to load report'}
    
    api = KnowledgeGraphAPI(report)
    return api.get_api_connections_graph()


def generate_dependency_graph_data(report_path: Path) -> Dict:
    """
    Generate dependency graph data from report file (file-level)
    
    Args:
        report_path: Path to JSON report file
        
    Returns:
        Graph data dict
    """
    report = load_report_from_file(report_path)
    if not report:
        return {'error': 'Failed to load report'}
    
    api = KnowledgeGraphAPI(report)
    return api.get_dependency_graph()


def generate_function_dependency_graph_data(report_path: Path) -> Dict:
    """
    Generate function-level dependency graph data from report file
    
    Args:
        report_path: Path to JSON report file
        
    Returns:
        Graph data dict
    """
    report = load_report_from_file(report_path)
    if not report:
        return {'error': 'Failed to load report'}
    
    api = KnowledgeGraphAPI(report)
    return api.get_function_dependency_graph()


def generate_comparison_data(current_report_path: Path, previous_report_path: Path) -> Dict:
    """
    Generate comparison data between two reports
    
    Args:
        current_report_path: Path to current report
        previous_report_path: Path to previous report
        
    Returns:
        Comparison data dict
    """
    current_report = load_report_from_file(current_report_path)
    previous_report = load_report_from_file(previous_report_path)
    
    if not current_report or not previous_report:
        return {'error': 'Failed to load reports'}
    
    api = KnowledgeGraphAPI(current_report)
    return api.get_snapshot_comparison(previous_report)

