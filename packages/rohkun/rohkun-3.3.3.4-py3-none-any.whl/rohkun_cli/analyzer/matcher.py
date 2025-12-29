"""
Connection matcher - match API calls to endpoints
"""
from typing import List, Dict
import re


def normalize_path(path: str) -> str:
    """Normalize API path for matching"""
    # Remove query parameters
    path = path.split('?')[0]
    
    # Remove trailing slash
    path = path.rstrip('/')
    
    # Remove leading slash if present
    if path.startswith('/'):
        path = path[1:]
    
    return path


def paths_match(endpoint_path: str, call_url: str) -> bool:
    """
    Check if endpoint path matches API call URL
    
    Handles:
    - Exact matches
    - Path parameters (:id, {id}, <id>, ${id})
    - Template variables (${API_URL}, ${BASE_URL}, etc.)
    - Partial URL matches
    """
    # Normalize both paths
    endpoint = normalize_path(endpoint_path)
    call = normalize_path(call_url)
    
    # Remove template variables from call URL (${API_URL}, ${BASE_URL}, {BASE_URL}, etc.)
    # Match ${ANYTHING}/ or {ANYTHING}/ at the start
    call = re.sub(r'^\$\{[^}]+\}/', '', call)  # ${VAR}/
    call = re.sub(r'^\{[^}]+\}/', '', call)    # {VAR}/
    
    # Extract path from full URL if present
    if '://' in call:
        # Extract path from URL
        parts = call.split('://', 1)[1].split('/', 1)
        if len(parts) > 1:
            call = parts[1]
        else:
            return False
    
    # Exact match
    if endpoint == call:
        return True
    
    # Convert path parameters to regex
    # Flask: <int:id>, <id>
    # Express: :id
    # Template: ${id}
    # All become: [^/]+
    endpoint_pattern = endpoint
    endpoint_pattern = re.sub(r'<[^>]+>', r'[^/]+', endpoint_pattern)  # Flask <int:id>
    endpoint_pattern = re.sub(r':[^/]+', r'[^/]+', endpoint_pattern)    # Express :id
    endpoint_pattern = re.sub(r'\{[^}]+\}', r'[^/]+', endpoint_pattern) # {id}
    
    call_pattern = call
    call_pattern = re.sub(r'\$\{[^}]+\}', r'[^/]+', call_pattern)  # ${userId}
    call_pattern = re.sub(r'\{[^}]+\}', r'[^/]+', call_pattern)    # {userId}
    
    # Try regex match both ways
    if re.fullmatch(endpoint_pattern, call):
        return True
    if re.fullmatch(call_pattern, endpoint):
        return True
    
    return False


def match_connections(endpoints: List[Dict], api_calls: List[Dict]) -> List[Dict]:
    """
    Match API calls to endpoints
    
    Args:
        endpoints: List of endpoint dicts
        api_calls: List of API call dicts
        
    Returns:
        List of connection dicts
    """
    connections = []
    
    for call in api_calls:
        # Skip if call doesn't have required fields
        if "method" not in call or "url" not in call:
            continue
            
        for endpoint in endpoints:
            # Skip if endpoint doesn't have required fields
            if "method" not in endpoint or "path" not in endpoint:
                continue
                
            # Check if methods match
            if call["method"] != endpoint["method"]:
                continue
            
            # Check if paths match
            if paths_match(endpoint["path"], call["url"]):
                connections.append({
                    "endpoint": endpoint,
                    "api_call": call,
                    "confidence": "high",
                    "match_type": "path_and_method"
                })
    
    return connections
