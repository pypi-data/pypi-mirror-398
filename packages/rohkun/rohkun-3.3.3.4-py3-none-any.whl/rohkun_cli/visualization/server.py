"""
Local HTTP Server for Visualization
"""
import http.server
import socketserver
import threading
import webbrowser
from pathlib import Path
from typing import Optional, Tuple
import time


class VisualizationHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for serving visualization files"""
    
    def __init__(self, *args, directory: Path = None, **kwargs):
        self.directory = directory
        super().__init__(*args, **kwargs)
    
    def translate_path(self, path):
        """Override to serve from custom directory"""
        if self.directory:
            # Remove leading slash
            path = path.lstrip('/')
            if path == '' or path == '/':
                path = 'index.html'
            
            # Serve from visualization directory
            full_path = self.directory / path
            if full_path.exists():
                return str(full_path)
        
        return super().translate_path(path)
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass  # Don't log every request


def start_visualization_server(
    visualization_dir: Path,
    port: int = 8000,
    open_browser: bool = True,
    auto_close_after: Optional[int] = None
) -> Tuple[threading.Thread, int]:
    """
    Start a local HTTP server to serve the visualization
    
    Args:
        visualization_dir: Directory containing visualization files
        port: Port to run server on (default: 8000)
        open_browser: Whether to automatically open browser
        auto_close_after: Auto-close server after N seconds (None = don't auto-close)
        
    Returns:
        Tuple of (server_thread, actual_port)
    """
    # Try to find an available port
    actual_port = port
    for attempt in range(10):
        try:
            handler = lambda *args, **kwargs: VisualizationHTTPRequestHandler(
                *args, directory=visualization_dir, **kwargs
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
    
    # Wait a moment for server to start
    time.sleep(0.5)
    
    # Open browser if requested
    if open_browser:
        url = f"http://localhost:{actual_port}"
        try:
            webbrowser.open(url)
        except Exception:
            pass  # Browser opening is optional
    
    # Auto-close if requested
    if auto_close_after:
        def auto_close():
            time.sleep(auto_close_after)
            httpd.shutdown()
        
        close_thread = threading.Thread(target=auto_close, daemon=True)
        close_thread.start()
    
    return server_thread, actual_port

