"""
Project scanner - orchestrates the analysis
"""
from pathlib import Path
from typing import Dict, List
from ..utils.file_utils import scan_directory, read_file_safe
from .endpoints import find_endpoints
from .api_calls import find_api_calls
from .matcher import match_connections
from .confidence import calculate_connection_confidence, calculate_accuracy_boundaries
from .blast_radius import BlastRadiusCalculator
from .dependencies import find_imports, find_function_calls, find_function_definitions


def _deduplicate_findings(findings: List[Dict]) -> List[Dict]:
    """
    Deduplicate findings by (method, path/url, file, line)
    """
    seen = set()
    unique = []
    for finding in findings:
        key = (
            finding.get('method'),
            finding.get('path') or finding.get('url'),
            finding.get('file'),
            finding.get('line')
        )
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return unique


def scan_project(project_path: Path) -> Dict:
    """
    Scan project and analyze code
    
    Args:
        project_path: Root directory of project
        
    Returns:
        Dict with analysis results including blast radius and confidence scores
    """
    # Get all files to scan
    files = scan_directory(project_path)
    
    # Analyze files
    all_endpoints = []
    all_api_calls = []
    all_imports = []
    all_function_calls = []
    all_function_defs = []
    
    for file_path in files:
        content = read_file_safe(file_path)
        if not content:
            continue
        
        # Find endpoints in this file
        endpoints = find_endpoints(file_path, content)
        # Filter out unsupported entries (files that couldn't be parsed)
        # Only include entries that have required fields (method and path)
        valid_endpoints = [
            ep for ep in endpoints 
            if ep.get('confidence') != 'unsupported' 
            and ep.get('method') 
            and ep.get('path')
        ]
        all_endpoints.extend(valid_endpoints)
        
        # Find API calls in this file
        api_calls = find_api_calls(file_path, content)
        # Filter out unsupported entries (files that couldn't be parsed)
        # Only include entries that have required fields (method and url)
        valid_api_calls = [
            call for call in api_calls 
            if call.get('confidence') != 'unsupported' 
            and call.get('method') 
            and call.get('url')
        ]
        all_api_calls.extend(valid_api_calls)
        
        # Find dependencies (imports, function calls, function definitions)
        imports = find_imports(file_path, content)
        all_imports.extend(imports)
        
        function_calls = find_function_calls(file_path, content)
        all_function_calls.extend(function_calls)
        
        function_defs = find_function_definitions(file_path, content)
        all_function_defs.extend(function_defs)
    
    # Deduplicate findings
    all_endpoints = _deduplicate_findings(all_endpoints)
    all_api_calls = _deduplicate_findings(all_api_calls)
    
    # Match connections
    connections = match_connections(all_endpoints, all_api_calls)
    
    # Add confidence scores to connections
    for conn in connections:
        confidence_data = calculate_connection_confidence(conn['endpoint'], conn['api_call'])
        conn['confidence'] = confidence_data['confidence']
        conn['confidence_reasons'] = confidence_data['reasons']
    
    # Calculate confidence distribution
    confidence_dist = calculate_accuracy_boundaries(connections)
    
    # Build blast radius analysis with enhanced dependency tracking
    blast_radius_calc = BlastRadiusCalculator()
    blast_radius_calc.build_from_analysis(all_endpoints, all_api_calls, connections)
    
    # Add function definitions to blast radius
    for func_def in all_function_defs:
        # Skip if missing required fields
        if 'file' not in func_def or 'name' not in func_def or 'line' not in func_def:
            continue
            
        identifier = f"func:{func_def['file']}:{func_def['name']}"
        blast_radius_calc.add_node(
            identifier=identifier,
            node_type="function",
            file_path=func_def['file'],
            line_number=func_def['line']
        )
    
    # Add function call dependencies
    for func_call in all_function_calls:
        # Skip if missing required fields
        if 'file' not in func_call or 'function' not in func_call:
            continue
            
        caller_id = f"file:{func_call['file']}"
        callee_id = f"func:{func_call['function']}"
        blast_radius_calc.add_call(caller_id, callee_id)
    
    # Calculate blast radius for all endpoints
    blast_radius_results = []
    for endpoint in all_endpoints:
        # Skip if missing required fields
        if 'method' not in endpoint or 'path' not in endpoint:
            continue
            
        identifier = f"{endpoint['method']}:{endpoint['path']}"
        result = blast_radius_calc.calculate_blast_radius(identifier)
        if result:
            blast_radius_results.append({
                "target": result.target,
                "target_type": result.target_type,
                "target_file": result.target_file,
                "target_line": result.target_line,
                "direct_dependents": result.direct_dependents,
                "total_dependents": result.total_dependents,
                "affected_files": list(result.affected_files),
                "affected_endpoints": list(result.affected_endpoints),
                "severity": result.severity,
                "impact_description": result.impact_description
            })
    
    # Find high-impact nodes
    high_impact = blast_radius_calc.get_high_impact_nodes(min_severity="high")
    
    return {
        "files_scanned": len(files),
        "endpoints": all_endpoints,
        "api_calls": all_api_calls,
        "connections": connections,
        "dependencies": {
            "imports": all_imports,
            "function_calls": all_function_calls,
            "function_definitions": all_function_defs
        },
        "blast_radius": blast_radius_results,
        "high_impact_nodes": [
            {
                "target": r.target,
                "severity": r.severity,
                "total_dependents": r.total_dependents,
                "impact_description": r.impact_description
            }
            for r in high_impact[:10]  # Top 10
        ],
        "confidence_distribution": confidence_dist,
        "summary": {
            "total_endpoints": len(all_endpoints),
            "total_api_calls": len(all_api_calls),
            "total_connections": len(connections),
            "total_imports": len(all_imports),
            "total_function_calls": len(all_function_calls),
            "total_function_definitions": len(all_function_defs),
            "certain_connections": confidence_dist.get('certain', 0),
            "high_confidence_connections": confidence_dist.get('high', 0),
            "medium_confidence_connections": confidence_dist.get('medium', 0),
            "low_confidence_connections": confidence_dist.get('low', 0),
            "high_impact_nodes": len(high_impact)
        }
    }
