"""
Inventory Report Formatter - Clean inventories, not connection guessing

Philosophy: We provide structured inventories of what exists.
We don't guess at connections (40% accurate).
We let AI/developers determine how things connect.
"""
from typing import Dict, List
from pathlib import Path
from datetime import datetime


def format_inventory_report(analysis_results: Dict, project_path: Path) -> Dict:
    """
    Format analysis results as clean inventories
    
    Returns structured report with:
    1. Backend Endpoints (what exists)
    2. Frontend API Calls (what's called)
    3. Library Abstractions (how they might connect)
    4. Blast Radius (impact analysis)
    5. AI Context Notes (how to use this data)
    """
    endpoints = analysis_results.get('endpoints', [])
    api_calls = analysis_results.get('api_calls', [])
    blast_radius = analysis_results.get('blast_radius', [])
    high_impact_nodes = analysis_results.get('high_impact_nodes', [])
    
    # Detect library abstractions
    libraries = detect_library_abstractions(endpoints, api_calls)
    
    # Calculate token savings
    total_items = len(endpoints) + len(api_calls)
    tokens_saved = total_items * 100  # Each item saves ~100 tokens
    cost_savings = (tokens_saved / 1000) * 0.03
    
    return {
        "version": "2.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project": {
            "path": str(project_path),
            "name": project_path.name
        },
        "token_savings": {
            "tokens_saved": tokens_saved,
            "cost_savings_usd": round(cost_savings, 2),
            "explanation": "Structured data that would require reading entire files"
        },
        "backend_endpoints": {
            "count": len(endpoints),
            "items": endpoints,
            "note": "These are the API endpoints detected in your backend code"
        },
        "frontend_api_calls": {
            "count": len(api_calls),
            "items": api_calls,
            "note": "These are the API calls detected in your frontend code"
        },
        "library_abstractions": libraries,
        "blast_radius": {
            "high_impact_nodes": high_impact_nodes,
            "all_results": blast_radius,
            "note": "Shows the impact of changing each endpoint - how many files/endpoints would be affected"
        },
        "ai_context": {
            "how_to_use": [
                "This report provides structured metadata about your API surface",
                "Use endpoint inventory to understand what your backend exposes",
                "Use API call inventory to understand what your frontend requests",
                "Library abstractions explain how they might connect",
                "All data includes file paths and line numbers for verification"
            ],
            "limitations": [
                "Dynamic routes computed at runtime are NOT detected",
                "External API calls may appear (this is expected)",
                "Library abstractions (Apollo, Socket.io) require manual verification",
                "Always verify important findings with runtime testing"
            ]
        },
        "metadata": {
            "files_scanned": analysis_results.get("files_scanned", 0)
        }
    }


def detect_library_abstractions(endpoints: List[Dict], api_calls: List[Dict]) -> Dict:
    """
    Detect library abstractions that might connect frontend to backend
    
    Returns dict explaining how libraries work, not guessing connections
    """
    abstractions = {}
    
    # Check for GraphQL
    graphql_endpoints = [e for e in endpoints if '/graphql' in e.get('path', '').lower()]
    graphql_calls = [c for c in api_calls if 'graphql' in c.get('url', '').lower() or c.get('library') == 'apollo']
    
    if graphql_endpoints or graphql_calls:
        abstractions['graphql'] = {
            "detected": True,
            "backend_endpoints": len(graphql_endpoints),
            "frontend_usage": len(graphql_calls),
            "explanation": "GraphQL uses a single endpoint (POST /graphql) for all operations. Frontend queries/mutations go through Apollo Client or similar. All useQuery/useMutation calls use this endpoint.",
            "note": "GraphQL connections are abstracted - you won't see individual REST endpoints"
        }
    
    # Check for WebSocket
    websocket_endpoints = [e for e in endpoints if 'socket' in e.get('path', '').lower() or 'ws' in e.get('path', '').lower()]
    
    if websocket_endpoints:
        abstractions['websocket'] = {
            "detected": True,
            "backend_endpoints": len(websocket_endpoints),
            "explanation": "WebSocket connections (Socket.io, ws) use persistent connections. Frontend socket.emit() calls go to these endpoints. Connection is implicit, not per-request.",
            "note": "WebSocket usage won't show as individual API calls"
        }
    
    # Check for tRPC
    trpc_endpoints = [e for e in endpoints if 'trpc' in e.get('path', '').lower()]
    
    if trpc_endpoints:
        abstractions['trpc'] = {
            "detected": True,
            "backend_endpoints": len(trpc_endpoints),
            "explanation": "tRPC uses type-safe RPC calls. Frontend calls look like function calls, not HTTP requests. All calls go through tRPC client.",
            "note": "tRPC connections are abstracted - you won't see fetch() calls"
        }
    
    return abstractions


def print_inventory_report(report: Dict):
    """Print human-readable inventory report"""
    print("\n" + "="*80)
    print("🚀 ROHKUN CODE INVENTORY")
    print("="*80)
    print(f"\nProject: {report['project']['name']}")
    print(f"Generated: {report['generated_at']}")
    
    # Token savings
    savings = report['token_savings']
    print(f"\n💰 Token Savings: ~{savings['tokens_saved']:,} tokens (${savings['cost_savings_usd']:.2f})")
    print(f"   {savings['explanation']}")
    
    # Backend endpoints
    print("\n" + "="*80)
    print("📡 BACKEND ENDPOINTS")
    print("="*80)
    backend = report['backend_endpoints']
    print(f"\n{backend['note']}")
    print(f"Total: {backend['count']}")
    print()
    
    for i, ep in enumerate(backend['items'][:15], 1):
        method = ep.get('method', 'GET')
        path = ep.get('path', 'unknown')
        file_path = ep.get('file', 'unknown')
        line = ep.get('line', '?')
        confidence = ep.get('confidence', 'high').upper()
        
        print(f"{i:2d}. {method:6s} {path:40s} [{confidence}]")
        print(f"    {file_path}:{line}")
    
    if backend['count'] > 15:
        print(f"\n... and {backend['count'] - 15} more endpoints")
    
    # Frontend API calls
    print("\n" + "="*80)
    print("🌐 FRONTEND API CALLS")
    print("="*80)
    frontend = report['frontend_api_calls']
    print(f"\n{frontend['note']}")
    print(f"Total: {frontend['count']}")
    print()
    
    for i, call in enumerate(frontend['items'][:15], 1):
        method = call.get('method', 'GET')
        url = call.get('url', 'unknown')
        file_path = call.get('file', 'unknown')
        line = call.get('line', '?')
        library = call.get('library', 'unknown')
        confidence = call.get('confidence', 'high').upper()
        
        print(f"{i:2d}. {method:6s} {url:40s} [{confidence}]")
        print(f"    {file_path}:{line} (via {library})")
    
    if frontend['count'] > 15:
        print(f"\n... and {frontend['count'] - 15} more API calls")
    
    # Library abstractions
    if report['library_abstractions']:
        print("\n" + "="*80)
        print("🔌 LIBRARY ABSTRACTIONS DETECTED")
        print("="*80)
        print("\nThese libraries abstract the connection between frontend and backend:")
        print()
        
        for lib_name, lib_info in report['library_abstractions'].items():
            print(f"• {lib_name.upper()}")
            print(f"  {lib_info['explanation']}")
            print(f"  Note: {lib_info['note']}")
            print()
    
    # Blast Radius
    blast_radius_data = report.get('blast_radius', {})
    high_impact = blast_radius_data.get('high_impact_nodes', [])
    
    if high_impact:
        print("\n" + "="*80)
        print("💥 BLAST RADIUS - HIGH IMPACT CHANGES")
        print("="*80)
        print(f"\n{blast_radius_data.get('note', 'Impact analysis of code changes')}")
        print(f"Total high-impact nodes: {len(high_impact)}")
        print()
        
        for i, node in enumerate(high_impact[:10], 1):
            severity = node.get('severity', 'unknown').upper()
            target = node.get('target', 'unknown')
            total_deps = node.get('total_dependents', 0)
            description = node.get('impact_description', '')
            
            # Color code severity
            severity_icon = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }.get(severity, '⚪')
            
            print(f"{i:2d}. {severity_icon} [{severity}] {target}")
            print(f"    {description}")
            print(f"    Total dependents: {total_deps}")
            print()
        
        if len(high_impact) > 10:
            print(f"... and {len(high_impact) - 10} more high-impact nodes")
        
        print("\nSeverity Levels:")
        print("  🔴 CRITICAL: Very high impact - many dependents or widespread effect")
        print("  🟠 HIGH: Significant impact - multiple dependents or moderate spread")
        print("  🟡 MEDIUM: Moderate impact - some dependents or limited spread")
        print("  🟢 LOW: Minimal impact - few or no dependents")
    
    # AI Context
    print("="*80)
    print("🤖 HOW TO USE THIS REPORT")
    print("="*80)
    context = report['ai_context']
    
    print("\nWhat you can do:")
    for item in context['how_to_use']:
        print(f"  • {item}")
    
    print("\nLimitations:")
    for item in context['limitations']:
        print(f"  ⚠️  {item}")
    
    print("\n" + "="*80)
    print("END OF REPORT")
    print("="*80 + "\n")
