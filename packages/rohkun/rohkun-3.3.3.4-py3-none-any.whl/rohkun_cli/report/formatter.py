"""
Report formatting and saving
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def format_report(analysis_results: Dict, project_path: Path) -> Dict:
    """
    Format analysis results into a report
    
    Args:
        analysis_results: Results from scanner
        project_path: Project root path
        
    Returns:
        Formatted report dict with all features
    """
    summary = analysis_results["summary"]
    endpoints = analysis_results.get("endpoints", [])
    api_calls = analysis_results.get("api_calls", [])
    connections = analysis_results.get("connections", [])
    
    # Calculate health indicators for AI/human understanding
    connection_rate = len(connections) / max(len(endpoints), 1) if endpoints else 0
    health_status = "healthy" if connection_rate >= 0.6 else "needs_attention" if connection_rate >= 0.3 else "critical"
    
    report = {
        "version": "2.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project": {
            "path": str(project_path),
            "name": project_path.name
        },
        "summary": summary,
        "endpoints": endpoints,
        "api_calls": api_calls,
        "connections": connections,
        "dependencies": analysis_results.get("dependencies", {
            "imports": [],
            "function_calls": [],
            "function_definitions": []
        }),
        "blast_radius": analysis_results.get("blast_radius", []),
        "high_impact_nodes": analysis_results.get("high_impact_nodes", []),
        "accuracy": analysis_results.get("accuracy", {}),
        "metadata": {
            "files_scanned": analysis_results.get("files_scanned", 0)
        },
        # Add semantic context for AI and human understanding
        "semantic_context": {
            "health_status": health_status,
            "health_description": _get_health_description(health_status, connection_rate),
            "connection_rate": connection_rate,
            "key_insights": _generate_key_insights(summary, endpoints, api_calls, connections),
            "field_descriptions": {
                "endpoints": "Backend API endpoints (routes) that accept HTTP requests",
                "api_calls": "Frontend/client code that makes HTTP requests to APIs",
                "connections": "Matched pairs showing which API calls connect to which endpoints",
                "blast_radius": "Impact analysis showing how many files/endpoints would be affected by changes",
                "high_impact_nodes": "Critical endpoints/files that have many dependencies"
            }
        }
    }
    
    # Add UI inspection data if present
    if "ui_inspection" in analysis_results:
        report["ui_inspection"] = analysis_results["ui_inspection"]
        
        # Add UI insights to semantic_context
        ui_summary = analysis_results["ui_inspection"].get("summary", {})
        if ui_summary.get("total_issues", 0) > 0:
            ui_insight = f"Found {ui_summary['total_issues']} UI issues across {ui_summary.get('total_files', 0)} HTML files"
            issues_by_type = ui_summary.get("issues_by_type", {})
            if issues_by_type:
                type_list = ", ".join([f"{count} {type.replace('_', ' ')}" for type, count in issues_by_type.items()])
                ui_insight += f" ({type_list})"
            report["semantic_context"]["key_insights"].append(ui_insight)
    
    return report


def _get_health_description(status: str, connection_rate: float) -> str:
    """Generate human-readable health description"""
    if status == "healthy":
        return f"Good integration: {connection_rate:.0%} of endpoints have matching API calls"
    elif status == "needs_attention":
        return f"Moderate integration: {connection_rate:.0%} of endpoints have matching API calls. Some endpoints may be unused or called from external clients."
    else:
        return f"Low integration: {connection_rate:.0%} of endpoints have matching API calls. Many endpoints may be unused, or API calls may be missing."


def _generate_key_insights(summary: Dict, endpoints: List, api_calls: List, connections: List) -> List[str]:
    """Generate actionable insights for humans and AI"""
    insights = []
    
    total_endpoints = summary.get("total_endpoints", 0)
    total_api_calls = summary.get("total_api_calls", 0)
    total_connections = summary.get("total_connections", 0)
    
    if total_endpoints > 0 and total_connections > 0:
        connection_rate = total_connections / total_endpoints
        if connection_rate >= 0.8:
            insights.append("Excellent frontend-backend integration detected")
        elif connection_rate >= 0.5:
            insights.append("Good integration, but some endpoints may be unused or called externally")
        else:
            insights.append("Low integration rate - consider reviewing unused endpoints or missing API calls")
    
    if total_endpoints == 0 and total_api_calls > 0:
        insights.append("API calls found but no endpoints detected - may be calling external APIs")
    
    if total_api_calls == 0 and total_endpoints > 0:
        insights.append("Endpoints found but no API calls detected - may be used by external clients or missing frontend code")
    
    high_impact = summary.get("high_impact_nodes", 0)
    if high_impact > 0:
        insights.append(f"{high_impact} high-impact nodes detected - changes to these would affect many files")
    
    return insights


def save_report(report: Dict, project_path: Path) -> Path:
    """
    Save report to .rohkun/reports/ directory in a numbered folder
    
    Structure: .rohkun/reports/1/report.json
               .rohkun/reports/2/report.json
               etc.
    
    Args:
        report: Report dict
        project_path: Project root path
        
    Returns:
        Path to saved report file
    """
    # Create reports directory
    reports_dir = project_path / ".rohkun" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Find next sequential folder number (always increment, don't fill gaps)
    existing_folders = set()
    for folder in reports_dir.iterdir():
        if folder.is_dir() and folder.name.isdigit():
            existing_folders.add(int(folder.name))
    
    # Use next number after the highest existing folder
    if existing_folders:
        folder_num = max(existing_folders) + 1
    else:
        folder_num = 1
    
    # Create numbered folder
    report_folder = reports_dir / str(folder_num)
    report_folder.mkdir(exist_ok=True)
    
    # Save report as report.json in the folder
    report_file = report_folder / "report.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report_file


def print_report_summary(report: Dict):
    """Print a human-readable summary of the report with all features"""
    summary = report["summary"]
    
    print("\n" + "="*60)
    print("ROHKUN ANALYSIS REPORT")
    print("="*60)
    print(f"\nProject: {report['project']['name']}")
    print(f"Generated: {report['generated_at']}")
    
    # Show HTML visualization link if available
    if 'visualization' in report:
        viz = report['visualization']
        html_path = viz.get('html_path', '')
        if html_path:
            print(f"\n📊 Interactive Graph: {html_path}")
            print(f"   (Open in browser to view interactive knowledge graph)")
    
    print(f"\nFiles Scanned: {report['metadata']['files_scanned']}")
    print(f"Endpoints Found: {summary['total_endpoints']}")
    print(f"API Calls Found: {summary['total_api_calls']}")
    print(f"Connections Found: {summary['total_connections']}")
    
    # Accuracy info
    accuracy = report.get('accuracy', {})
    if accuracy:
        print(f"\nEstimated Accuracy: {accuracy.get('estimated_accuracy', 'N/A')}")
        print(f"  High Confidence: {accuracy.get('high_confidence', 0)}")
        print(f"  Medium Confidence: {accuracy.get('medium_confidence', 0)}")
        print(f"  Low Confidence: {accuracy.get('low_confidence', 0)}")
    
    # High impact nodes
    high_impact = report.get('high_impact_nodes', [])
    if high_impact:
        print("\n" + "-"*60)
        print(f"HIGH IMPACT NODES ({len(high_impact)})")
        print("-"*60)
        print("These nodes have many dependents - changes would affect many files:")
        for node in high_impact[:5]:
            print(f"\n  {node['target']} ({node['severity'].upper()})")
            print(f"  {node['impact_description']}")
        if len(high_impact) > 5:
            print(f"\n  ... and {len(high_impact) - 5} more")
    
    # Connections with confidence
    if report['connections']:
        print("\n" + "-"*60)
        print("CONNECTIONS")
        print("-"*60)
        
        for i, conn in enumerate(report['connections'][:10], 1):  # Show first 10
            endpoint = conn['endpoint']
            api_call = conn['api_call']
            confidence = conn.get('confidence', 'unknown')
            confidence_score = conn.get('confidence_score', 0)
            
            # Color code by confidence
            conf_symbol = "●" if confidence == "high" else "◐" if confidence == "medium" else "○"
            
            confidence_desc = "very high" if confidence_score >= 90 else "high" if confidence_score >= 70 else "moderate" if confidence_score >= 50 else "low"
            print(f"\n{i}. {conf_symbol} {endpoint['method']} {endpoint['path']} ({confidence} confidence - {confidence_desc})")
            print(f"   Endpoint: {endpoint['file']}:{endpoint['line']}")
            print(f"   Called from: {api_call['file']}:{api_call['line']}")
            
            # Show confidence reasons if available
            reasons = conn.get('confidence_reasons', [])
            if reasons:
                print(f"   Reasons: {', '.join(reasons)}")
        
        if len(report['connections']) > 10:
            print(f"\n... and {len(report['connections']) - 10} more connections")
    
    # Blast radius summary
    blast_radius = report.get('blast_radius', [])
    if blast_radius:
        critical = sum(1 for b in blast_radius if b['severity'] == 'critical')
        high = sum(1 for b in blast_radius if b['severity'] == 'high')
        
        if critical or high:
            print("\n" + "-"*60)
            print("BLAST RADIUS SUMMARY")
            print("-"*60)
            if critical:
                print(f"  Critical Impact: {critical} nodes")
            if high:
                print(f"  High Impact: {high} nodes")
    
    print("\n" + "="*60 + "\n")
