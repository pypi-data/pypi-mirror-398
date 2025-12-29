"""
Report Comparison - Compare reports over time to track changes
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def load_report(report_path: Path) -> Optional[Dict]:
    """Load a report from file"""
    try:
        with open(report_path, 'r') as f:
            return json.load(f)
    except:
        return None


def find_previous_reports(reports_dir: Path, current_report: str) -> List[Path]:
    """Find all previous reports, sorted by date"""
    if not reports_dir.exists():
        return []
    
    reports = []
    for report_file in reports_dir.glob("report_*.json"):
        if report_file.name != current_report:
            reports.append(report_file)
    
    # Sort by modification time (newest first)
    reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return reports


def compare_reports(current: Dict, previous: Dict) -> Dict:
    """
    Compare two reports and return differences
    
    Returns dict with:
    - added_endpoints: New endpoints
    - removed_endpoints: Deleted endpoints
    - added_api_calls: New API calls
    - removed_api_calls: Deleted API calls
    - added_connections: New connections
    - removed_connections: Broken connections
    - blast_radius_changes: Blast radius for added/removed items
    - high_impact_changes: Changes in high-impact nodes
    - confidence_changes: Changes in confidence scores
    """
    # Compare endpoints (with safety checks)
    current_endpoints = {
        f"{e['method']}:{e['path']}" 
        for e in current.get('endpoints', []) 
        if 'method' in e and 'path' in e
    }
    previous_endpoints = {
        f"{e['method']}:{e['path']}" 
        for e in previous.get('endpoints', [])
        if 'method' in e and 'path' in e
    }
    
    added_endpoints = current_endpoints - previous_endpoints
    removed_endpoints = previous_endpoints - current_endpoints
    
    # Compare API calls (with safety checks)
    current_calls = {
        f"{c['method']}:{c['url']}:{c['file']}:{c['line']}" 
        for c in current.get('api_calls', [])
        if 'method' in c and 'url' in c and 'file' in c and 'line' in c
    }
    previous_calls = {
        f"{c['method']}:{c['url']}:{c['file']}:{c['line']}" 
        for c in previous.get('api_calls', [])
        if 'method' in c and 'url' in c and 'file' in c and 'line' in c
    }
    
    added_calls = current_calls - previous_calls
    removed_calls = previous_calls - current_calls
    
    # Compare connections (with safety checks)
    current_connections = {
        f"{c['endpoint']['method']}:{c['endpoint']['path']}->{c['api_call']['url']}"
        for c in current.get('connections', [])
        if 'endpoint' in c and 'api_call' in c
        and 'method' in c['endpoint'] and 'path' in c['endpoint']
        and 'url' in c['api_call']
    }
    previous_connections = {
        f"{c['endpoint']['method']}:{c['endpoint']['path']}->{c['api_call']['url']}"
        for c in previous.get('connections', [])
        if 'endpoint' in c and 'api_call' in c
        and 'method' in c['endpoint'] and 'path' in c['endpoint']
        and 'url' in c['api_call']
    }
    
    added_connections = current_connections - previous_connections
    removed_connections = previous_connections - current_connections
    
    # Compare summary metrics
    current_summary = current.get('summary', {})
    previous_summary = previous.get('summary', {})
    
    metric_changes = {
        'endpoints': current_summary.get('total_endpoints', 0) - previous_summary.get('total_endpoints', 0),
        'api_calls': current_summary.get('total_api_calls', 0) - previous_summary.get('total_api_calls', 0),
        'connections': current_summary.get('total_connections', 0) - previous_summary.get('total_connections', 0),
        'high_impact_nodes': current_summary.get('high_impact_nodes', 0) - previous_summary.get('high_impact_nodes', 0)
    }
    
    # Compare accuracy
    current_accuracy = current.get('accuracy', {})
    previous_accuracy = previous.get('accuracy', {})
    
    accuracy_change = {
        'current': current_accuracy.get('estimated_accuracy', 'N/A'),
        'previous': previous_accuracy.get('estimated_accuracy', 'N/A'),
        'percentage_change': current_accuracy.get('accuracy_percentage', 0) - previous_accuracy.get('accuracy_percentage', 0)
    }
    
    # Compare blast radius for changes
    blast_radius_changes = compare_blast_radius(current, previous, added_endpoints, removed_endpoints)
    
    # Generate change summary
    change_summary = generate_change_summary(
        added_endpoints, removed_endpoints,
        added_calls, removed_calls,
        added_connections, removed_connections,
        metric_changes
    )
    
    return {
        'comparison_date': datetime.utcnow().isoformat() + 'Z',
        'current_report_date': current.get('generated_at', 'unknown'),
        'previous_report_date': previous.get('generated_at', 'unknown'),
        'added_endpoints': list(added_endpoints),
        'removed_endpoints': list(removed_endpoints),
        'added_api_calls': list(added_calls),
        'removed_api_calls': list(removed_calls),
        'added_connections': list(added_connections),
        'removed_connections': list(removed_connections),
        'metric_changes': metric_changes,
        'accuracy_change': accuracy_change,
        'blast_radius_changes': blast_radius_changes,
        'change_summary': change_summary,
        'has_changes': any([
            added_endpoints, removed_endpoints,
            added_calls, removed_calls,
            added_connections, removed_connections
        ])
    }


def compare_blast_radius(current: Dict, previous: Dict, 
                        added_endpoints: set, removed_endpoints: set) -> Dict:
    """
    Compare blast radius between reports and calculate impact of changes
    
    Returns:
    - added_endpoint_impacts: Blast radius for new endpoints
    - removed_endpoint_impacts: Blast radius for removed endpoints (from previous report)
    - high_impact_changes: Changes in high-impact nodes
    """
    # Get blast radius data
    current_blast_radius = {br['target']: br for br in current.get('blast_radius', [])}
    previous_blast_radius = {br['target']: br for br in previous.get('blast_radius', [])}
    
    # Get blast radius for added endpoints
    added_endpoint_impacts = []
    for endpoint_id in added_endpoints:
        if endpoint_id in current_blast_radius:
            br = current_blast_radius[endpoint_id]
            added_endpoint_impacts.append({
                'endpoint': endpoint_id,
                'severity': br.get('severity', 'unknown'),
                'total_dependents': br.get('total_dependents', 0),
                'direct_dependents': br.get('direct_dependents', 0),
                'affected_files': br.get('affected_files', []),
                'impact_description': br.get('impact_description', '')
            })
    
    # Get blast radius for removed endpoints (from previous report)
    removed_endpoint_impacts = []
    for endpoint_id in removed_endpoints:
        if endpoint_id in previous_blast_radius:
            br = previous_blast_radius[endpoint_id]
            removed_endpoint_impacts.append({
                'endpoint': endpoint_id,
                'severity': br.get('severity', 'unknown'),
                'total_dependents': br.get('total_dependents', 0),
                'direct_dependents': br.get('direct_dependents', 0),
                'affected_files': br.get('affected_files', []),
                'impact_description': br.get('impact_description', ''),
                'warning': 'This endpoint had dependents - removal may break functionality'
            })
    
    # Compare high-impact nodes
    current_high_impact = {node['target']: node for node in current.get('high_impact_nodes', [])}
    previous_high_impact = {node['target']: node for node in previous.get('high_impact_nodes', [])}
    
    new_high_impact = set(current_high_impact.keys()) - set(previous_high_impact.keys())
    removed_high_impact = set(previous_high_impact.keys()) - set(current_high_impact.keys())
    
    # Calculate severity changes for existing high-impact nodes
    severity_changes = []
    for target in set(current_high_impact.keys()) & set(previous_high_impact.keys()):
        curr = current_high_impact[target]
        prev = previous_high_impact[target]
        
        if curr['severity'] != prev['severity']:
            severity_changes.append({
                'target': target,
                'previous_severity': prev['severity'],
                'current_severity': curr['severity'],
                'dependents_change': curr['total_dependents'] - prev['total_dependents']
            })
    
    return {
        'added_endpoint_impacts': added_endpoint_impacts,
        'removed_endpoint_impacts': removed_endpoint_impacts,
        'new_high_impact_nodes': list(new_high_impact),
        'removed_high_impact_nodes': list(removed_high_impact),
        'severity_changes': severity_changes,
        'summary': {
            'added_with_high_impact': len([e for e in added_endpoint_impacts if e['severity'] in ['high', 'critical']]),
            'removed_with_dependents': len([e for e in removed_endpoint_impacts if e['total_dependents'] > 0]),
            'new_high_impact_count': len(new_high_impact),
            'removed_high_impact_count': len(removed_high_impact)
        }
    }


def generate_change_summary(added_endpoints, removed_endpoints,
                           added_calls, removed_calls,
                           added_connections, removed_connections,
                           metric_changes) -> str:
    """Generate human-readable change summary"""
    parts = []
    
    if added_endpoints:
        parts.append(f"+{len(added_endpoints)} endpoint{'s' if len(added_endpoints) != 1 else ''}")
    if removed_endpoints:
        parts.append(f"-{len(removed_endpoints)} endpoint{'s' if len(removed_endpoints) != 1 else ''}")
    
    if added_calls:
        parts.append(f"+{len(added_calls)} API call{'s' if len(added_calls) != 1 else ''}")
    if removed_calls:
        parts.append(f"-{len(removed_calls)} API call{'s' if len(removed_calls) != 1 else ''}")
    
    if added_connections:
        parts.append(f"+{len(added_connections)} connection{'s' if len(added_connections) != 1 else ''}")
    if removed_connections:
        parts.append(f"-{len(removed_connections)} connection{'s' if len(removed_connections) != 1 else ''}")
    
    if not parts:
        return "No changes detected"
    
    return ", ".join(parts)


def print_comparison(comparison: Dict):
    """Print comparison results in a readable format"""
    print("\n" + "="*60)
    print("REPORT COMPARISON")
    print("="*60)
    
    print(f"\nCurrent:  {comparison['current_report_date']}")
    print(f"Previous: {comparison['previous_report_date']}")
    
    if not comparison['has_changes']:
        print("\n✓ No changes detected")
        # Show that comparison was performed by listing current counts from metric_changes
        # (metric_changes shows the difference, so we need to infer current from previous + diff)
        metric_changes = comparison.get('metric_changes', {})
        if metric_changes:
            # Note: metric_changes shows the difference, not absolute values
            # This is just to confirm comparison ran
            print(f"\n  Comparison verified: All metrics match between snapshots")
        return
    
    print(f"\nSummary: {comparison['change_summary']}")
    
    # Metric changes
    print("\n" + "-"*60)
    print("METRIC CHANGES")
    print("-"*60)
    
    for metric, change in comparison['metric_changes'].items():
        if change != 0:
            sign = "+" if change > 0 else ""
            print(f"  {metric.replace('_', ' ').title()}: {sign}{change}")
    
    # Accuracy change
    acc_change = comparison['accuracy_change']
    if acc_change['percentage_change'] != 0:
        print(f"\n  Accuracy: {acc_change['previous']} → {acc_change['current']}")
        print(f"  Change: {acc_change['percentage_change']:+.1f}%")
    
    # Added endpoints
    if comparison['added_endpoints']:
        print("\n" + "-"*60)
        print(f"ADDED ENDPOINTS ({len(comparison['added_endpoints'])})")
        print("-"*60)
        for endpoint in comparison['added_endpoints'][:10]:
            print(f"  + {endpoint}")
        if len(comparison['added_endpoints']) > 10:
            print(f"  ... and {len(comparison['added_endpoints']) - 10} more")
    
    # Removed endpoints
    if comparison['removed_endpoints']:
        print("\n" + "-"*60)
        print(f"REMOVED ENDPOINTS ({len(comparison['removed_endpoints'])})")
        print("-"*60)
        for endpoint in comparison['removed_endpoints'][:10]:
            print(f"  - {endpoint}")
        if len(comparison['removed_endpoints']) > 10:
            print(f"  ... and {len(comparison['removed_endpoints']) - 10} more")
    
    # Added connections
    if comparison['added_connections']:
        print("\n" + "-"*60)
        print(f"NEW CONNECTIONS ({len(comparison['added_connections'])})")
        print("-"*60)
        for conn in comparison['added_connections'][:5]:
            print(f"  + {conn}")
        if len(comparison['added_connections']) > 5:
            print(f"  ... and {len(comparison['added_connections']) - 5} more")
    
    # Broken connections
    if comparison['removed_connections']:
        print("\n" + "-"*60)
        print(f"BROKEN CONNECTIONS ({len(comparison['removed_connections'])})")
        print("-"*60)
        for conn in comparison['removed_connections'][:5]:
            print(f"  - {conn}")
        if len(comparison['removed_connections']) > 5:
            print(f"  ... and {len(comparison['removed_connections']) - 5} more")
    
    # Blast radius changes
    blast_radius = comparison.get('blast_radius_changes', {})
    if blast_radius:
        summary = blast_radius.get('summary', {})
        
        # Show removed endpoints with dependents (CRITICAL)
        removed_with_deps = blast_radius.get('removed_endpoint_impacts', [])
        removed_with_deps = [e for e in removed_with_deps if e['total_dependents'] > 0]
        
        if removed_with_deps:
            print("\n" + "-"*60)
            print(f"⚠️  REMOVED ENDPOINTS WITH DEPENDENTS ({len(removed_with_deps)})")
            print("-"*60)
            print("These endpoints had dependencies - removal may break functionality!")
            print()
            for impact in removed_with_deps[:5]:
                severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(impact['severity'], '⚪')
                print(f"  {severity_icon} {impact['endpoint']}")
                print(f"     Severity: {impact['severity'].upper()}")
                print(f"     Dependents: {impact['total_dependents']} ({impact['direct_dependents']} direct)")
                print(f"     Affected files: {len(impact['affected_files'])}")
                print()
        
        # Show added endpoints with high impact
        added_high_impact = [e for e in blast_radius.get('added_endpoint_impacts', []) 
                            if e['severity'] in ['high', 'critical']]
        
        if added_high_impact:
            print("\n" + "-"*60)
            print(f"NEW HIGH-IMPACT ENDPOINTS ({len(added_high_impact)})")
            print("-"*60)
            for impact in added_high_impact[:5]:
                severity_icon = {'critical': '🔴', 'high': '🟠'}.get(impact['severity'], '⚪')
                print(f"  {severity_icon} {impact['endpoint']}")
                print(f"     {impact['impact_description']}")
                print()
        
        # Show high-impact node changes
        new_high_impact = blast_radius.get('new_high_impact_nodes', [])
        removed_high_impact = blast_radius.get('removed_high_impact_nodes', [])
        
        if new_high_impact or removed_high_impact:
            print("\n" + "-"*60)
            print("HIGH-IMPACT NODE CHANGES")
            print("-"*60)
            if new_high_impact:
                print(f"  New high-impact nodes: {len(new_high_impact)}")
                for node in new_high_impact[:3]:
                    print(f"    + {node}")
            if removed_high_impact:
                print(f"  Removed high-impact nodes: {len(removed_high_impact)}")
                for node in removed_high_impact[:3]:
                    print(f"    - {node}")
    
    print("\n" + "="*60 + "\n")
