"""
Core analysis logic
Returns structured data instead of printing
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .config import Config
from .auth import authorize_scan, report_usage
from .analyzer import scan_project
from .report import format_report, save_report
from .snapshot import SnapshotTracker
# Knowledge graph uses standalone HTML (no server needed)
from .utils.file_utils import estimate_project_size


@dataclass
class AnalysisResult:
    """Structured result from analysis"""
    success: bool
    results: Optional[Dict[str, Any]] = None
    report_path: Optional[Path] = None
    html_graph_path: Optional[Path] = None  # Path to standalone HTML graph file
    snapshot: Optional[Dict[str, Any]] = None
    project_hash: Optional[str] = None
    visualization_url: Optional[str] = None
    knowledge_graph_url: Optional[str] = None
    credits_remaining: Optional[int] = None
    error: Optional[str] = None
    error_reason: Optional[str] = None
    error_message: Optional[str] = None


def run_analysis(
    project_path: Path,
    api_key: Optional[str] = None,
    skip_auth: bool = False
) -> AnalysisResult:
    """
    Core analysis function
    
    Args:
        project_path: Path to project directory
        api_key: Optional API key (if None, will try to load from config)
        skip_auth: Skip authorization check (for testing)
    
    Returns:
        AnalysisResult with structured data
    """
    project_path = project_path.resolve()
    
    # Validate path
    if not project_path.exists():
        return AnalysisResult(
            success=False,
            error="Path does not exist",
            error_message=f"Path does not exist: {project_path}"
        )
    
    if not project_path.is_dir():
        return AnalysisResult(
            success=False,
            error="Not a directory",
            error_message=f"Path is not a directory: {project_path}"
        )
    
    # Get API key
    if api_key is None:
        config = Config(project_path)
        api_key = config.get_api_key()
    
    # Authorization
    auth_result = None
    if not skip_auth:
        if not api_key:
            return AnalysisResult(
                success=False,
                error="No API key found",
                error_message="Set your API key with: rohkun config --api-key YOUR_KEY"
            )
        
        # Estimate size and authorize
        size_info = estimate_project_size(project_path)
        auth_result = authorize_scan(
            api_key=api_key,
            project_name=project_path.name,
            estimated_files=size_info['file_count']
        )
        
        if not auth_result.authorized:
            return AnalysisResult(
                success=False,
                error="Authorization failed",
                error_reason=auth_result.reason,
                error_message=auth_result.message,
                credits_remaining=auth_result.credits_remaining
            )
    
    # Run analysis
    try:
        # Initialize snapshot tracker
        tracker = SnapshotTracker(project_path)
        project_info = tracker.get_or_create_project()
        
        # Run scan
        results = scan_project(project_path)
        
        # Capture UI snapshots (NEW)
        try:
            from .frontend_inspector import capture_frontend_snapshots
            ui_snapshots = capture_frontend_snapshots(project_path)
            
            # Merge UI data into results
            results['ui_inspection'] = ui_snapshots
            
            # Add UI issues to summary (ensure summary exists)
            if 'summary' not in results:
                results['summary'] = {}
            ui_summary = ui_snapshots.get('summary', {})
            results['summary']['ui_issues'] = {
                'total': ui_summary.get('total_issues', 0),
                'high': len([i for i in ui_snapshots.get('issues', []) if i.get('severity') == 'high']),
                'medium': len([i for i in ui_snapshots.get('issues', []) if i.get('severity') == 'medium']),
                'low': len([i for i in ui_snapshots.get('issues', []) if i.get('severity') == 'low'])
            }
        except Exception as e:
            # UI inspection is optional, don't fail the whole analysis
            print(f"⚠️  UI inspection failed: {e}", file=sys.stderr)
            results['ui_inspection'] = {
                "snapshots": [],
                "issues": [],
                "summary": {"total_files": 0, "total_elements": 0, "total_issues": 0, "issues_by_type": {}},
                "enabled": False,
                "error": str(e)
            }
            if 'summary' not in results:
                results['summary'] = {}
            results['summary']['ui_issues'] = {'total': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        # Generate report
        report = format_report(results, project_path)
        report_file = save_report(report, project_path)
        
        # Generate HTML graph in same folder as report
        from .knowledge_graph.html_generator import generate_standalone_html
        html_file = generate_standalone_html(report_file)
        
        # Add HTML file path to report and save again
        report['visualization'] = {
            'html_path': str(html_file.relative_to(project_path)),
            'html_file': html_file.name,
            'folder': report_file.parent.name  # Folder number
        }
        
        # Update report file with HTML path
        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save snapshot - use folder number instead of filename
        report_folder = report_file.parent.name  # Get folder number (e.g., "1", "2")
        snapshot = tracker.save_snapshot(results, report_folder)
        
        # Report usage (fire-and-forget)
        if not skip_auth and api_key and auth_result and auth_result.request_id:
            report_usage(api_key, auth_result.request_id, success=True)
        
        return AnalysisResult(
            success=True,
            results=results,
            report_path=report_file,
            html_graph_path=html_file,  # Include HTML graph path (standalone, no server needed)
            snapshot=snapshot,
            project_hash=project_info['project_hash'],
            visualization_url=None,  # No server - use file:// URL
            knowledge_graph_url=None,  # No server - use file:// URL
            credits_remaining=auth_result.credits_remaining if auth_result else None
        )
        
    except Exception as e:
        # Report failure
        if not skip_auth and api_key and auth_result and auth_result.request_id:
            report_usage(api_key, auth_result.request_id, success=False)
        
        return AnalysisResult(
            success=False,
            error="Analysis failed",
            error_message=str(e)
        )

