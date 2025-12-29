"""
Confidence Scoring - Calculate confidence levels for connections

Determines how confident we are about endpoint-to-API-call connections.
"""
from typing import Dict, List


def calculate_connection_confidence(endpoint: Dict, api_call: Dict) -> Dict:
    """
    Calculate confidence level for a connection
    
    Returns dict with:
    - confidence: "certain", "high", "medium", "low"
    - reasons: List of reasons for the level
    
    Philosophy: We are deterministic, not probabilistic.
    We provide clear categories, not percentages.
    """
    reasons = []
    matches = []
    
    # Check method match
    method_match = endpoint['method'] == api_call['method']
    if method_match:
        matches.append("method")
        reasons.append("HTTP method matches")
    
    # Check path similarity
    endpoint_path = normalize_path(endpoint['path'])
    call_url = normalize_path(api_call['url'])
    
    if paths_match_exactly(endpoint_path, call_url):
        matches.append("path_exact")
        reasons.append("Path matches exactly")
    elif paths_match_with_params(endpoint_path, call_url):
        matches.append("path_params")
        reasons.append("Path matches with parameters")
    elif paths_partially_match(endpoint_path, call_url):
        matches.append("path_partial")
        reasons.append("Path partially matches")
    
    # Check file relationships
    if are_in_same_project(endpoint['file'], api_call['file']):
        matches.append("same_project")
        reasons.append("Files in same project")
    
    if are_files_related(endpoint['file'], api_call['file']):
        matches.append("related_files")
        reasons.append("Files are related")
    
    # Determine confidence level (deterministic rules)
    if "method" in matches and "path_exact" in matches:
        confidence = "certain"  # Exact match on both method and path
    elif "method" in matches and "path_params" in matches:
        confidence = "high"  # Method + path with params
    elif "method" in matches and "path_partial" in matches:
        confidence = "medium"  # Method + partial path
    elif "method" in matches or "path_exact" in matches:
        confidence = "medium"  # Either method or exact path
    else:
        confidence = "low"  # Weak match
    
    return {
        "confidence": confidence,
        "reasons": reasons
    }


def normalize_path(path: str) -> str:
    """Normalize path for comparison"""
    # Remove query params
    path = path.split('?')[0]
    # Remove trailing slash
    path = path.rstrip('/')
    # Remove leading slash
    if path.startswith('/'):
        path = path[1:]
    return path.lower()


def paths_match_exactly(endpoint_path: str, call_url: str) -> bool:
    """Check if paths match exactly"""
    return endpoint_path == call_url


def paths_match_with_params(endpoint_path: str, call_url: str) -> bool:
    """Check if paths match with parameters"""
    import re
    
    # Convert path params to regex
    # :id, {id}, <id> -> [^/]+
    pattern = re.sub(r'[:{<][^>}:]+[>}:]?', r'[^/]+', endpoint_path)
    
    try:
        return bool(re.fullmatch(pattern, call_url))
    except:
        return False


def paths_partially_match(endpoint_path: str, call_url: str) -> bool:
    """Check if paths partially match"""
    endpoint_parts = endpoint_path.split('/')
    call_parts = call_url.split('/')
    
    # Check if at least 50% of parts match
    if len(endpoint_parts) == 0:
        return False
    
    matches = sum(1 for e, c in zip(endpoint_parts, call_parts) if e == c)
    return matches / len(endpoint_parts) >= 0.5


def are_in_same_project(file1: str, file2: str) -> bool:
    """Check if files are in the same project"""
    # Simple heuristic: share common root directory
    from pathlib import Path
    
    try:
        path1 = Path(file1)
        path2 = Path(file2)
        
        # Get first 2 parts of path
        parts1 = path1.parts[:2] if len(path1.parts) >= 2 else path1.parts
        parts2 = path2.parts[:2] if len(path2.parts) >= 2 else path2.parts
        
        return parts1 == parts2
    except:
        return False


def are_files_related(file1: str, file2: str) -> bool:
    """Check if files are related (e.g., frontend/backend, client/server)"""
    from pathlib import Path
    
    try:
        path1 = Path(file1)
        path2 = Path(file2)
        
        # Check if in related directories
        related_pairs = [
            ('frontend', 'backend'),
            ('client', 'server'),
            ('ui', 'api'),
            ('web', 'api'),
            ('app', 'server')
        ]
        
        for dir1, dir2 in related_pairs:
            if (dir1 in path1.parts and dir2 in path2.parts) or \
               (dir2 in path1.parts and dir1 in path2.parts):
                return True
        
        return False
    except:
        return False


def calculate_accuracy_boundaries(connections: List[Dict]) -> Dict:
    """
    Calculate confidence distribution for the analysis
    
    Returns confidence distribution (deterministic, no percentages)
    
    Philosophy: We are deterministic, not probabilistic.
    We count detections by confidence level, not estimate accuracy.
    """
    if not connections:
        return {
            "total_connections": 0,
            "certain": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
    
    certain = sum(1 for c in connections if c.get('confidence') == 'certain')
    high = sum(1 for c in connections if c.get('confidence') == 'high')
    medium = sum(1 for c in connections if c.get('confidence') == 'medium')
    low = sum(1 for c in connections if c.get('confidence') == 'low')
    
    return {
        "total_connections": len(connections),
        "certain": certain,
        "high": high,
        "medium": medium,
        "low": low
    }
