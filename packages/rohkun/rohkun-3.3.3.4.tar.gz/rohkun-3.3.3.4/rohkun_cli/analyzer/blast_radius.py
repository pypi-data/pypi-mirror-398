"""
Blast Radius Calculator - Calculate impact of code changes

Tracks dependencies and calculates what would be affected by changes.
"""
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class DependencyNode:
    """Node in dependency graph"""
    identifier: str
    node_type: str  # "function", "class", "endpoint", "file"
    file_path: str
    line_number: int
    
    # What this depends on
    calls: Set[str] = field(default_factory=set)
    imports: Set[str] = field(default_factory=set)
    
    # What depends on this
    called_by: Set[str] = field(default_factory=set)
    imported_by: Set[str] = field(default_factory=set)
    
    # Endpoint info
    is_endpoint: bool = False
    endpoint_path: Optional[str] = None
    endpoint_method: Optional[str] = None


@dataclass
class BlastRadiusResult:
    """Result of blast radius calculation"""
    target: str
    target_type: str
    target_file: str
    target_line: int
    
    # Impact metrics
    direct_dependents: int
    total_dependents: int
    affected_files: Set[str]
    affected_endpoints: Set[str]
    
    # Severity
    severity: str  # "low", "medium", "high", "critical"
    impact_description: str


class BlastRadiusCalculator:
    """Calculate blast radius for code changes"""
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.file_to_nodes: Dict[str, Set[str]] = defaultdict(set)
    
    def add_node(self, identifier: str, node_type: str, file_path: str, 
                 line_number: int, is_endpoint: bool = False,
                 endpoint_path: str = None, endpoint_method: str = None):
        """Add a node to the dependency graph"""
        if identifier not in self.nodes:
            self.nodes[identifier] = DependencyNode(
                identifier=identifier,
                node_type=node_type,
                file_path=file_path,
                line_number=line_number,
                is_endpoint=is_endpoint,
                endpoint_path=endpoint_path,
                endpoint_method=endpoint_method
            )
        
        self.file_to_nodes[file_path].add(identifier)
        return self.nodes[identifier]
    
    def add_call(self, caller: str, callee: str):
        """Add a function call dependency"""
        if caller in self.nodes:
            self.nodes[caller].calls.add(callee)
        
        if callee not in self.nodes:
            # Create placeholder
            self.nodes[callee] = DependencyNode(
                identifier=callee,
                node_type="function",
                file_path="unknown",
                line_number=0
            )
        
        self.nodes[callee].called_by.add(caller)
    
    def build_from_analysis(self, endpoints: List[Dict], api_calls: List[Dict], 
                           connections: List[Dict]):
        """Build dependency graph from analysis results"""
        # Add endpoints
        for endpoint in endpoints:
            # Skip if missing required fields
            if 'method' not in endpoint or 'path' not in endpoint:
                continue
            if 'file' not in endpoint or 'line' not in endpoint:
                continue
                
            identifier = f"{endpoint['method']}:{endpoint['path']}"
            self.add_node(
                identifier=identifier,
                node_type="endpoint",
                file_path=endpoint['file'],
                line_number=endpoint['line'],
                is_endpoint=True,
                endpoint_path=endpoint['path'],
                endpoint_method=endpoint['method']
            )
        
        # Add API calls
        for call in api_calls:
            # Skip if missing required fields
            if 'file' not in call or 'line' not in call:
                continue
                
            identifier = f"call:{call['file']}:{call['line']}"
            self.add_node(
                identifier=identifier,
                node_type="api_call",
                file_path=call['file'],
                line_number=call['line']
            )
        
        # Add connections as dependencies
        for conn in connections:
            endpoint = conn.get('endpoint', {})
            api_call = conn.get('api_call', {})
            
            # Skip if missing required fields
            if 'method' not in endpoint or 'path' not in endpoint:
                continue
            if 'file' not in api_call or 'line' not in api_call:
                continue
            
            endpoint_id = f"{endpoint['method']}:{endpoint['path']}"
            call_id = f"call:{api_call['file']}:{api_call['line']}"
            
            self.add_call(call_id, endpoint_id)
    
    def calculate_blast_radius(self, identifier: str, max_depth: int = 10) -> Optional[BlastRadiusResult]:
        """Calculate blast radius for a node"""
        if identifier not in self.nodes:
            return None
        
        node = self.nodes[identifier]
        
        # Get all dependents recursively
        all_dependents = self._get_dependents(identifier, max_depth)
        direct_dependents = node.called_by | node.imported_by
        
        # Categorize impact
        affected_files = set()
        affected_endpoints = set()
        
        for dep_id in all_dependents:
            if dep_id in self.nodes:
                dep_node = self.nodes[dep_id]
                affected_files.add(dep_node.file_path)
                if dep_node.is_endpoint:
                    affected_endpoints.add(dep_id)
        
        # Calculate severity
        # Use direct_dependents as a key metric since it represents immediate impact
        severity = self._calculate_severity(
            len(direct_dependents),  # direct dependents (immediate impact)
            len(all_dependents),     # total dependents (recursive impact)
            len(affected_files),     # affected files
            len(affected_endpoints)  # affected endpoints
        )
        
        # Generate description
        description = self._generate_description(
            identifier, node.node_type, len(direct_dependents),
            len(all_dependents), len(affected_files), len(affected_endpoints)
        )
        
        return BlastRadiusResult(
            target=identifier,
            target_type=node.node_type,
            target_file=node.file_path,
            target_line=node.line_number,
            direct_dependents=len(direct_dependents),
            total_dependents=len(all_dependents),
            affected_files=affected_files,
            affected_endpoints=affected_endpoints,
            severity=severity,
            impact_description=description
        )
    
    def _get_dependents(self, identifier: str, max_depth: int) -> Set[str]:
        """Get all dependents recursively"""
        dependents = set()
        visited = set()
        
        def collect(node_id: str, depth: int):
            if depth > max_depth or node_id in visited or node_id not in self.nodes:
                return
            
            visited.add(node_id)
            node = self.nodes[node_id]
            
            for dep in node.called_by | node.imported_by:
                dependents.add(dep)
                collect(dep, depth + 1)
        
        collect(identifier, 0)
        return dependents
    
    def _calculate_severity(self, direct: int, total: int, files: int, endpoints: int) -> str:
        """
        Calculate severity level
        
        Thresholds optimized for typical coding workflows:
        - More sensitive to catch impactful changes early
        - Better suited for small/medium projects
        - Flags meaningful dependencies (3-4 dependents) as high impact
        - Considers direct dependents as key metric for immediate impact
        """
        # Critical: Very high impact - many direct dependents or widespread effect
        if endpoints >= 6 or files >= 12 or total >= 25 or direct >= 8:
            return "critical"
        # High: Significant impact - 3+ direct dependents or moderate spread
        if endpoints >= 3 or files >= 4 or total >= 8 or direct >= 5:
            return "high"
        # Medium: Moderate impact - 2+ direct dependents or some spread
        if endpoints >= 2 or files >= 2 or total >= 4 or direct >= 3:
            return "medium"
        return "low"
    
    def _generate_description(self, identifier: str, node_type: str, 
                            direct: int, total: int, files: int, endpoints: int) -> str:
        """Generate impact description"""
        parts = []
        if endpoints > 0:
            parts.append(f"{endpoints} endpoint{'s' if endpoints != 1 else ''}")
        if files > 0:
            parts.append(f"{files} file{'s' if files != 1 else ''}")
        
        if not parts:
            return f"Changing {node_type} '{identifier}' has no detected dependents."
        
        impact = ", ".join(parts)
        return f"Changing {node_type} '{identifier}' affects {impact} ({direct} direct, {total} total dependents)."
    
    def get_high_impact_nodes(self, min_severity: str = "high") -> List[BlastRadiusResult]:
        """Find all high-impact nodes"""
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_level = severity_order.get(min_severity, 0)
        
        results = []
        for identifier in self.nodes:
            result = self.calculate_blast_radius(identifier)
            if result and severity_order.get(result.severity, 0) >= min_level:
                results.append(result)
        
        results.sort(key=lambda x: x.total_dependents, reverse=True)
        return results
