#!/usr/bin/env python3
"""
Rohkun CLI v2 - Client-side code analysis tool

Usage:
    rohkun run [path]               # Run analysis (automatically compares with previous snapshot)
    rohkun config --api-key KEY     # Set API key
    rohkun --version                # Show version
"""
import sys
import argparse
from pathlib import Path
import time
from datetime import datetime

from . import __version__
from .config import Config
from .auth import authorize_scan, report_usage
from .analyzer import scan_project
from .report import format_report, save_report, print_report_summary
from .snapshot import SnapshotTracker
from .core import run_analysis
from .utils.display import (
    print_error, print_success, print_info, print_header,
    print_auth_error, print_scan_summary, print_warning
)
from .utils.file_utils import estimate_project_size


def show_setup_help():
    """Show platform-specific setup help when API key is missing"""
    import platform
    
    system = platform.system().lower()
    
    print_error("No API key found")
    print_info("")
    print_info("🚀 Quick Setup:")
    print_info("  1. Visit: https://rohkun.com/dashboard")
    print_info("  2. Create an API key")
    print_info("  3. Copy the complete setup command for your platform")
    print_info("  4. Run it in your terminal")
    print_info("")
    
    if system == "windows":
        print_info("💡 Windows users: Use PowerShell or Command Prompt")
        print_info("   If you get 'pip not found', install Python from python.org")
    elif system == "darwin":  # macOS
        print_info("💡 macOS users: Use Terminal")
        print_info("   If you get 'pip not found', try: brew install python3")
    elif system == "linux":
        print_info("💡 Linux users: Use your terminal")
        print_info("   If you get 'pip not found', try: sudo apt install python3-pip")
    
    print_info("")
    print_info("Or set manually:")
    print_info("  rohkun config --api-key YOUR_KEY")


def check_first_run(config):
    """Check if this is the user's first run and show welcome message"""
    first_run_file = config.rohkun_dir / ".first_run"
    
    if not first_run_file.exists():
        print_success("🎉 Welcome to Rohkun!")
        print_info("This is your first scan. We'll create a baseline snapshot of your project.")
        print_info("Future scans will show you what changed since this baseline.")
        print_info("")
        
        # Create first run marker
        config.ensure_directories()
        first_run_file.touch()
        return True
    
    return False


def cmd_scan(args):
    """Execute scan command"""
    project_path = Path(args.path).resolve()
    
    if not project_path.exists():
        print_error(f"Path does not exist: {project_path}")
        sys.exit(1)
    
    if not project_path.is_dir():
        print_error(f"Path is not a directory: {project_path}")
        sys.exit(1)
    
    print_header("🔍 Rohkun Code Analysis")
    
    # Estimate project size
    print_info("Estimating project size...")
    size_info = estimate_project_size(project_path)
    print_info(f"Found ~{size_info['file_count']} files ({size_info['size_mb']} MB)")
    
    # Authorization (required in production)
    # Load config
    config = Config(project_path)
    api_key = config.get_api_key()
    
    if not api_key:
        show_setup_help()
        sys.exit(1)
    
    # Authorize scan
    print_info("Checking authorization...")
    auth_result = authorize_scan(
        api_key=api_key,
        project_name=project_path.name,
        estimated_files=size_info['file_count']
    )
    
    if not auth_result.authorized:
        # Check if server sent custom display message
        if auth_result.cli_display:
            display = auth_result.cli_display
            
            # Print title
            if display.get("title"):
                if display.get("type") == "error":
                    print_error(display["title"])
                else:
                    print_info(display["title"])
            
            # Print message lines
            print()
            for line in display.get("lines", []):
                print(f"  {line}" if line else "")
            print()
        else:
            # Fallback to old error display
            print_auth_error(
                auth_result.reason,
                auth_result.message,
                auth_result.credits_remaining,
                auth_result.tier
            )
        
        sys.exit(1)
    
    print_success(f"Authorized! ({auth_result.credits_remaining} credits remaining)")
    
    # Check for first run
    is_first_run = check_first_run(config)
    
    # Run analysis using shared core function
    print_info("Analyzing project...")
    start_time = time.time()
    
    try:
        # Use shared core function
        result = run_analysis(
            project_path=project_path,
            api_key=api_key,
            skip_auth=False
        )
        
        if not result.success:
            print_error(result.error_message or result.error)
            if result.error_reason:
                print_info(f"Reason: {result.error_reason}")
            sys.exit(1)
        
        # Extract results for CLI display
        results = result.results
        report_file = result.report_path
        snapshot = result.snapshot
        project_info = {'project_hash': result.project_hash}
        duration = time.time() - start_time
        
        # Get snapshot summary for display
        tracker = SnapshotTracker(project_path)
        snapshot_summary = tracker.get_snapshot_summary()
        is_first_scan = snapshot_summary['total'] == 0
        
        if not is_first_scan:
            print_info(f"Continuing project: {project_info['project_hash']} (Scan #{snapshot_summary['total'] + 1})")
        
        # Generate CLI report text with project hash
        from .report import format_cli_report
        cli_report_text = format_cli_report(
            analysis_results=results,
            project_name=project_path.name,
            user_email="local@user",
            report_id=project_info['project_hash']
        )
        
        # Add snapshot info to report
        if not is_first_scan:
            snapshot_info = f"\n{'='*80}\n"
            snapshot_info += "CONTINUITY TRACKING\n"
            snapshot_info += f"{'='*80}\n"
            snapshot_info += f"Project: {project_info['project_hash']}\n"
            snapshot_info += f"Snapshot: #{snapshot['sequence']}\n"
            snapshot_info += f"Drift Score: {snapshot['drift']:.2f} ({snapshot['status']})\n"
            snapshot_info += f"Previous Scan: {snapshot.get('compared_to', 'N/A')}\n"
            snapshot_info += f"\nDrift Levels:\n"
            snapshot_info += f"  • 0.0-0.2: Low drift (healthy, focused changes)\n"
            snapshot_info += f"  • 0.2-0.5: Medium drift (review changes)\n"
            snapshot_info += f"  • 0.5+: High drift (significant refactor)\n"
            snapshot_info += f"\n"
            
            cli_report_text = cli_report_text.replace(
                "END OF REPORT",
                snapshot_info + "END OF REPORT"
            )
        
        # Save CLI report to file in the same numbered folder as report.json
        # Get the folder number from the report path
        report_folder = result.report_path.parent
        cli_report_file = report_folder / "report.txt"
        with open(cli_report_file, 'w') as f:
            f.write(cli_report_text)
        
        # Copy to clipboard
        try:
            import pyperclip
            pyperclip.copy(cli_report_text)
            clipboard_success = True
        except:
            clipboard_success = False
        
        # Calculate token savings
        tokens_saved = (results['summary']['total_endpoints'] + 
                       results['summary']['total_api_calls'] + 
                       results['summary']['total_connections']) * 100
        cost_savings = (tokens_saved / 1000) * 0.03
        
        # Print minimal summary
        print_header("✅ Analysis Complete")
        
        if result.credits_remaining is not None:
            print_success(f"Credits Remaining: {result.credits_remaining}")
        
        print_success(f"Token Savings: ~{tokens_saved:,} tokens (${cost_savings:.2f})")
        print_success(f"Report saved: {cli_report_file}")
        
        # Show HTML graph link (from AnalysisResult or report) - PRIMARY OUTPUT
        html_path_to_show = None
        if result.html_graph_path:
            html_path_to_show = result.html_graph_path
        elif result.report_path:
            # Fallback: read from report JSON
            import json
            try:
                with open(result.report_path, 'r') as f:
                    report_data = json.load(f)
                    if 'visualization' in report_data:
                        viz = report_data['visualization']
                        html_path = viz.get('html_path', '')
                        if html_path:
                            html_path_to_show = project_path / html_path
            except Exception:
                pass  # Silently fail if can't read report
        
        if html_path_to_show:
            # Convert to absolute path for file:// URL
            abs_html_path = html_path_to_show.resolve()
            # Create clickable file:// link (works in most modern terminals)
            file_url = f"file:///{str(abs_html_path).replace(chr(92), '/')}"  # Replace backslashes for URL
            # Use terminal hyperlink format (OSC 8 escape sequence) - works in modern terminals
            clickable_link = f"\033]8;;{file_url}\033\\{html_path_to_show}\033]8;;\033\\"
            print_success(f"📊 Interactive Graph: {clickable_link}")
            print_info("   → Click the link above to open in your browser (or double-click the file)")
        
        if clipboard_success:
            print_success("📋 Report copied to clipboard - paste anywhere!")
        else:
            print_warning("Could not copy to clipboard (install pyperclip)")
        
        print()
        print_info("Quick Summary:")
        print(f"  • Project: {project_info['project_hash']}")
        print(f"  • Snapshot: #{snapshot['sequence']}")
        if not is_first_scan:
            print(f"  • Drift: {snapshot['drift']:.2f} ({snapshot['status']})")
        print(f"  • Endpoints: {results['summary']['total_endpoints']}")
        print(f"  • API Calls: {results['summary']['total_api_calls']}")
        print(f"  • Connections: {results['summary']['total_connections']}")
        print(f"  • Files Scanned: {results['files_scanned']}")
        print(f"  • Duration: {duration:.2f}s")
        print()
        
        if args.verbose:
            print_info("Full report:")
            print(cli_report_text)
        
        # Always compare with previous report if available (default behavior)
        if not is_first_scan:
            from .report.comparison import load_report, compare_reports, print_comparison
            
            # Use snapshot tracker to get the correct previous report
            previous_report_path = tracker.get_previous_report_path()
            
            if previous_report_path and previous_report_path.exists():
                print_info(f"Comparing with previous snapshot...")
                previous_report = load_report(previous_report_path)
                if previous_report:
                    # Load current report for comparison
                    current_report = load_report(report_file)
                    if current_report:
                        comparison = compare_reports(current_report, previous_report)
                        print_comparison(comparison)
                    else:
                        print_info("Failed to load current report for comparison")
                else:
                    print_info("Failed to load previous report for comparison")
            else:
                print_info("No previous snapshot found for comparison")
        
    except Exception as e:
        print_error(f"Analysis failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        
        # Report failure
        if api_key and auth_result:
            if auth_result.request_id:
                report_usage(api_key, auth_result.request_id, success=False)
        sys.exit(1)


def cmd_config(args):
    """Execute config command"""
    project_path = Path.cwd()
    config = Config(project_path)
    
    if args.api_key:
        is_global = getattr(args, 'global_config', False)
        config.set_api_key(args.api_key, global_config=is_global)
        
        if is_global:
            print_success("API key saved to ~/.rohkun/config.json (global)")
            print_info("This key will be used for all projects")
        else:
            print_success("API key saved to .rohkun/config.json (project)")
            print_info("This key will only be used for this project")
        
        print_info("You can now run: rohkun run")
    else:
        # Show current config
        current_key = config.get_api_key()
        if current_key:
            masked_key = current_key[:8] + "..." + current_key[-4:]
            print_info(f"Current API key: {masked_key}")
        else:
            print_info("No API key configured")
            print_info("")
            print_info("Set API key in 3 ways:")
            print_info("  1. Global:  rohkun config --api-key YOUR_KEY --global")
            print_info("  2. Project: rohkun config --api-key YOUR_KEY")
            print_info("  3. Environment: export ROHKUN_API_KEY=YOUR_KEY")
            print_info("")
            print_info("Get your API key at: https://rohkun.com/dashboard")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Rohkun - Client-side code analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'Rohkun CLI v{__version__}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Run command (primary)
    run_parser = subparsers.add_parser('run', help='Run analysis on project')
    run_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to project directory (defaults to current directory if not specified)'
    )
    run_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    
    # Scan command (alias for backward compatibility)
    scan_parser = subparsers.add_parser('scan', help='Scan project for API connections (alias for "run")')
    scan_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to project directory (defaults to current directory if not specified)'
    )
    scan_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configure Rohkun CLI')
    config_parser.add_argument(
        '--api-key',
        help='Set API key'
    )
    config_parser.add_argument(
        '--global',
        action='store_true',
        dest='global_config',
        help='Save to global config (~/.rohkun/config.json) instead of project config'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command in ('run', 'scan'):
        cmd_scan(args)
    elif args.command == 'config':
        cmd_config(args)


if __name__ == '__main__':
    main()
