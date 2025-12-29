"""
Knowledge Graph HTTP Server - Serves graph data as JSON API
Can be tested with curl
"""
import json
import http.server
import socketserver
import threading
import sys
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs
import time

from .api import (
    generate_api_graph_data,
    generate_dependency_graph_data,
    generate_comparison_data,
    load_report_from_file
)


class KnowledgeGraphRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for knowledge graph API endpoints"""
    
    def __init__(self, *args, reports_dir: Path = None, **kwargs):
        self.reports_dir = reports_dir or Path('.')
        super().__init__(*args, **kwargs)
    
    def _validate_report_name(self, report_name: str) -> bool:
        """
        Validate report name to prevent path traversal attacks
        
        Supports both old format (report_*.json) and new format (folder number)
        
        Args:
            report_name: Report filename or folder number to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not report_name:
            return False
        
        # Check for path traversal attempts
        if '..' in report_name or '/' in report_name or '\\' in report_name:
            return False
        
        # New format: folder number (e.g., "1", "2", "3")
        if report_name.isdigit():
            return True
        
        # Old format: report_*.json (backward compatibility)
        if report_name.startswith('report_') and report_name.endswith('.json'):
            # Check for any other suspicious characters
            if any(char in report_name for char in ['<', '>', '|', ':', '*', '?', '"']):
                return False
            return True
        
        return False
    
    def _get_report_path(self, report_name: Optional[str] = None) -> Optional[Path]:
        """
        Get report path, either specified or latest
        Supports both new format (folder numbers) and old format (report_*.json)
        Includes security validation
        
        Args:
            report_name: Optional report folder number (e.g., "1") or old format filename
            
        Returns:
            Path to report file, or None if not found/invalid
        """
        if report_name:
            # Validate report name first (security)
            if not self._validate_report_name(report_name):
                print(f"[KG-API] Invalid report name: {report_name}", file=sys.stderr, flush=True)
                return None
            
            # New format: folder number (e.g., "1", "2", "3")
            if report_name.isdigit():
                report_path = self.reports_dir / report_name / "report.json"
                
                # Check if folder exists
                folder_path = self.reports_dir / report_name
                if not folder_path.exists() or not folder_path.is_dir():
                    print(f"[KG-API] Report folder not found: {report_name}", file=sys.stderr, flush=True)
                    return None
            else:
                # Old format: report_*.json (backward compatibility)
                report_path = self.reports_dir / report_name
            
            # Additional security check: ensure path is still within reports_dir
            try:
                if not str(report_path.resolve()).startswith(str(self.reports_dir.resolve())):
                    print(f"[KG-API] Path traversal attempt detected: {report_name}", file=sys.stderr, flush=True)
                    return None
            except (OSError, ValueError) as e:
                print(f"[KG-API] Error resolving path for {report_name}: {e}", file=sys.stderr, flush=True)
                return None
            
            if not report_path.exists():
                print(f"[KG-API] Report file not found: {report_path}", file=sys.stderr, flush=True)
                return None
            
            return report_path
        else:
            # Get latest report - check new format first, then old format
            try:
                # New format: find highest numbered folder with valid report.json
                numbered_folders = []
                for folder in self.reports_dir.iterdir():
                    if folder.is_dir() and folder.name.isdigit():
                        report_file = folder / "report.json"
                        if report_file.exists():
                            numbered_folders.append((int(folder.name), report_file))
                
                if numbered_folders:
                    # Sort by folder number (descending) and return latest
                    numbered_folders.sort(key=lambda x: x[0], reverse=True)
                    return numbered_folders[0][1]
                
                # Fallback to old format (backward compatibility)
                reports = sorted(self.reports_dir.glob('report_*.json'),
                               key=lambda p: p.stat().st_mtime, reverse=True)
                return reports[0] if reports else None
            except (OSError, ValueError) as e:
                print(f"[KG-API] Error finding latest report: {e}", file=sys.stderr, flush=True)
                return None
    
    def do_GET(self):
        """Handle GET requests"""
        import sys
        print(f"[KG-API] GET {self.path}", file=sys.stderr, flush=True)
        
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        print(f"[KG-API] Path: {path}, Query: {query}", file=sys.stderr, flush=True)
        
        try:
            # API endpoints
            if path == '/api/graph/api-connections':
                print(f"[KG-API] Generating API connections graph", file=sys.stderr, flush=True)
                # GET /api/graph/api-connections?report=report_20250115_120000.json
                report_name = query.get('report', [None])[0]
                
                report_path = self._get_report_path(report_name)
                if not report_path:
                    if report_name:
                        self._send_error('Invalid report name or report not found', 400)
                    else:
                        self._send_error('No reports found', 404)
                        return
                
                print(f"[KG-API] Using report: {report_path}", file=sys.stderr, flush=True)
                print(f"[KG-API] Generating graph data...", file=sys.stderr, flush=True)
                data = generate_api_graph_data(report_path)
                print(f"[KG-API] Graph data generated: {len(data.get('nodes', []))} nodes, {len(data.get('edges', []))} edges", file=sys.stderr, flush=True)
                self._send_json(data)
            
            elif path == '/api/graph/dependencies':
                # GET /api/graph/dependencies?report=report_20250115_120000.json
                report_name = query.get('report', [None])[0]
                
                report_path = self._get_report_path(report_name)
                if not report_path:
                    if report_name:
                        self._send_error('Invalid report name or report not found', 400)
                    else:
                        self._send_error('No reports found', 404)
                        return
                
                data = generate_dependency_graph_data(report_path)
                self._send_json(data)
            
            elif path == '/api/graph/function-dependencies':
                # GET /api/graph/function-dependencies?report=report_20250115_120000.json
                print(f"[KG-API] Generating function dependencies graph", file=sys.stderr, flush=True)
                report_name = query.get('report', [None])[0]
                
                report_path = self._get_report_path(report_name)
                if not report_path:
                    if report_name:
                        self._send_error('Invalid report name or report not found', 400)
                    else:
                        self._send_error('No reports found', 404)
                        return
                
                print(f"[KG-API] Using report: {report_path}", file=sys.stderr, flush=True)
                print(f"[KG-API] Generating function dependency graph data...", file=sys.stderr, flush=True)
                from .api import generate_function_dependency_graph_data
                data = generate_function_dependency_graph_data(report_path)
                print(f"[KG-API] Function dependency graph data generated: {len(data.get('nodes', []))} nodes, {len(data.get('edges', []))} edges", file=sys.stderr, flush=True)
                self._send_json(data)
            
            elif path == '/api/graph/compare':
                # GET /api/graph/compare?current=report1.json&previous=report2.json
                current_name = query.get('current', [None])[0]
                previous_name = query.get('previous', [None])[0]
                
                if not current_name or not previous_name:
                    self._send_error('Missing current or previous report parameter', 400)
                    return
                
                current_path = self._get_report_path(current_name)
                previous_path = self._get_report_path(previous_name)
                
                if not current_path:
                    self._send_error('Invalid current report name or report not found', 400)
                    return
                
                if not previous_path:
                    self._send_error('Invalid previous report name or report not found', 400)
                    return
                
                data = generate_comparison_data(current_path, previous_path)
                self._send_json(data)
            
            elif path == '/api/reports/list':
                # GET /api/reports/list
                missing_folders = []  # Initialize outside try block
                try:
                    # New format: get reports from numbered folders in ascending order
                    # Track missing folders
                    numbered_folders = {}
                    for folder in self.reports_dir.iterdir():
                        if folder.is_dir() and folder.name.isdigit():
                            folder_num = int(folder.name)
                            report_file = folder / "report.json"
                            if report_file.exists():
                                numbered_folders[folder_num] = report_file
                    
                    # Determine range: from 1 to max folder number
                    if numbered_folders:
                        max_folder = max(numbered_folders.keys())
                        # Check for missing folders in sequence
                        for i in range(1, max_folder + 1):
                            if i not in numbered_folders:
                                missing_folders.append(i)
                        
                        # Sort by folder number (ascending order)
                        report_files = [numbered_folders[i] for i in sorted(numbered_folders.keys())]
                    else:
                        report_files = []
                    
                    # Fallback to old format (backward compatibility)
                    if not report_files:
                        report_files = sorted(self.reports_dir.glob('report_*.json'),
                               key=lambda p: p.stat().st_mtime, reverse=True)
                except (OSError, ValueError) as e:
                    print(f"[KG-API] Error listing reports: {e}", file=sys.stderr, flush=True)
                    self._send_error('Error listing reports', 500)
                    return
                
                report_list = []
                for report_path in report_files:
                    try:
                        report = load_report_from_file(report_path)
                        if report:
                            # Determine identifier: folder number for new format, filename for old
                            if report_path.parent.name.isdigit():
                                identifier = report_path.parent.name  # Folder number
                            else:
                                identifier = report_path.name  # Old format filename
                            
                            report_list.append({
                                'filename': identifier,  # Use folder number or filename
                                'generated_at': report.get('generated_at'),
                                'project_name': report.get('project', {}).get('name'),
                                'summary': report.get('summary', {})
                            })
                    except (FileNotFoundError, PermissionError) as e:
                        print(f"[KG-API] Warning: Failed to load report {report_path.name}: {e}", file=sys.stderr, flush=True)
                        continue
                    except json.JSONDecodeError as e:
                        print(f"[KG-API] Warning: Invalid JSON in report {report_path.name}: {e}", file=sys.stderr, flush=True)
                        continue
                    except Exception as e:
                        print(f"[KG-API] Warning: Unexpected error loading report {report_path.name}: {e}", file=sys.stderr, flush=True)
                        continue
                
                # Include missing folders info if using new format
                response = {
                    'reports': report_list
                }
                if missing_folders:
                    response['missing_folders'] = missing_folders
                    response['message'] = f'Note: Folders {missing_folders} are missing but expected in sequence'
                
                self._send_json(response)
            
            elif path == '/api/reports/latest':
                # GET /api/reports/latest
                try:
                    reports = sorted(self.reports_dir.glob('report_*.json'),
                                   key=lambda p: p.stat().st_mtime, reverse=True)
                except (OSError, ValueError) as e:
                    print(f"[KG-API] Error finding latest report: {e}", file=sys.stderr, flush=True)
                    self._send_error('Error finding latest report', 500)
                    return
                
                if not reports:
                    self._send_error('No reports found', 404)
                    return
                
                latest = reports[0]
                report = load_report_from_file(latest)
                if not report:
                    self._send_error('Failed to load latest report', 500)
                    return
                
                self._send_json({
                    'filename': latest.name,
                    'report': report
                })
            
            else:
                print(f"[KG-API] Unknown endpoint: {path}", file=sys.stderr, flush=True)
                self._send_error(f'Unknown endpoint: {path}', 404)
        
        except Exception as e:
            import traceback
            print(f"[KG-API] Error: {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            self._send_error(f'Server error: {str(e)}', 500)
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json(self, data: dict, status_code: int = 200):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        json_str = json.dumps(data, indent=2)
        self.wfile.write(json_str.encode('utf-8'))
    
    def _send_error(self, message: str, status_code: int = 400):
        """Send error response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        error_data = {'error': message}
        self.wfile.write(json.dumps(error_data).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def start_knowledge_graph_server(
    reports_dir: Path,
    port: int = 8002,
    open_browser: bool = False
) -> Tuple[threading.Thread, int]:
    """
    Start HTTP server for knowledge graph API
    
    Args:
        reports_dir: Directory containing JSON reports
        port: Port to run server on
        open_browser: Whether to open browser (not used for API)
        
    Returns:
        Tuple of (server_thread, actual_port)
    """
    # Find available port
    actual_port = port
    for attempt in range(10):
        try:
            handler = lambda *args, **kwargs: KnowledgeGraphRequestHandler(
                *args, reports_dir=reports_dir, **kwargs
            )
            httpd = socketserver.TCPServer(("", actual_port), handler, bind_and_activate=False)
            httpd.allow_reuse_address = True
            httpd.server_bind()
            httpd.server_activate()
            break
        except OSError:
            actual_port += 1
    else:
        raise RuntimeError(f"Could not find available port starting from {port}")
    
    # Start server in background thread
    def run_server():
        try:
            httpd.serve_forever()
        except Exception:
            pass
        finally:
            httpd.shutdown()
            httpd.server_close()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(0.5)
    
    return server_thread, actual_port

