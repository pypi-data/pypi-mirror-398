"""
Knowledge Graph UI Server - Serves HTML visualization pages
Serves the UI files and proxies API requests
"""
import http.server
import socketserver
import threading
import sys
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse
import time

from .server import start_knowledge_graph_server as start_api_server


class KnowledgeGraphUIServer:
    """Serves UI HTML files and proxies to API server"""
    
    def __init__(self, ui_dir: Path, reports_dir: Path, api_port: int = 8002):
        self.ui_dir = ui_dir
        self.reports_dir = reports_dir
        self.api_port = api_port
        self.api_thread = None
    
    def start(self, port: int = 8003) -> Tuple[threading.Thread, int]:
        """
        Start UI server and API server
        
        Args:
            port: Port for UI server
            
        Returns:
            Tuple of (server_thread, actual_port)
        """
        # Start API server first
        self.api_thread, actual_api_port = start_api_server(self.reports_dir, port=self.api_port)
        self.api_port = actual_api_port
        
        # Create custom handler
        class UIRequestHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, ui_dir=None, api_port=None, **kwargs):
                self.ui_dir = ui_dir
                self.api_port = api_port
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                """Handle GET requests - serve static files or graph_v2.html"""
                parsed = urlparse(self.path)
                file_path = parsed.path.lstrip('/')
                
                # Check if it's a request for a static file (JS, CSS, etc.)
                if file_path and '.' in file_path and '/' not in file_path:
                    # Try to serve the requested file from ui_dir
                    requested_file = self.ui_dir / file_path
                    if requested_file.exists() and requested_file.is_file():
                        try:
                            # Determine content type
                            content_type = 'text/plain'
                            if file_path.endswith('.js'):
                                content_type = 'application/javascript'
                            elif file_path.endswith('.css'):
                                content_type = 'text/css'
                            elif file_path.endswith('.html'):
                                content_type = 'text/html'
                            elif file_path.endswith('.json'):
                                content_type = 'application/json'
                            
                            # Read and serve the file
                            with open(requested_file, 'rb') as f:
                                content = f.read()
                            
                            self.send_response(200)
                            self.send_header('Content-Type', content_type)
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.send_header('Content-Length', str(len(content)))
                            self.end_headers()
                            self.wfile.write(content)
                            return
                        except Exception as e:
                            print(f"[UI-Server] Error serving {file_path}: {e}", file=sys.stderr, flush=True)
                
                # For all other paths, serve graph_v2.html (SPA behavior)
                graph_v2_path = self.ui_dir / 'graph_v2.html'
                if graph_v2_path.exists():
                    try:
                        with open(graph_v2_path, 'rb') as f:
                            content = f.read()
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/html')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Content-Length', str(len(content)))
                        self.end_headers()
                        self.wfile.write(content)
                        return
                    except Exception as e:
                        print(f"[UI-Server] Error serving graph_v2.html: {e}", file=sys.stderr, flush=True)
                
                # Fallback to default handler
                super().do_GET()
            
            def end_headers(self):
                """Add CORS headers"""
                self.send_header('Access-Control-Allow-Origin', '*')
                super().end_headers()
            
            def log_message(self, format, *args):
                """Suppress default logging"""
                pass
        
        # Find available port
        actual_port = port
        for attempt in range(10):
            try:
                handler = lambda *args, **kwargs: UIRequestHandler(
                    *args, ui_dir=self.ui_dir, api_port=self.api_port, **kwargs
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
        
        time.sleep(0.5)
        
        return server_thread, actual_port


def start_knowledge_graph_ui(
    project_path: Path,
    ui_port: int = 8003,
    api_port: int = 8002
) -> Tuple[threading.Thread, int, int]:
    """
    Start both UI and API servers for knowledge graphs
    
    Args:
        project_path: Project root path
        ui_port: Port for UI server
        api_port: Port for API server
        
    Returns:
        Tuple of (ui_thread, ui_port, api_port)
    """
    ui_dir = Path(__file__).parent / 'ui'
    reports_dir = project_path / '.rohkun' / 'reports'
    
    server = KnowledgeGraphUIServer(ui_dir, reports_dir, api_port)
    ui_thread, actual_ui_port = server.start(ui_port)
    
    return ui_thread, actual_ui_port, server.api_port

