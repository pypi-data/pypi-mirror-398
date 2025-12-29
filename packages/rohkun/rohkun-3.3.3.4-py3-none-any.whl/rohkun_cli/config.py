"""
Configuration management for Rohkun CLI
"""
import os
from pathlib import Path
import json
from typing import Optional

# API Configuration
API_BASE_URL = os.getenv("ROHKUN_API_URL", "https://rohkun-api.onrender.com")
API_TIMEOUT = int(os.getenv("ROHKUN_API_TIMEOUT", "10"))  # seconds (configurable via env var)

# Local paths
ROHKUN_DIR = ".rohkun"
REPORTS_DIR = "reports"
CONFIG_FILE = "config.json"

# File scanning
EXCLUDED_DIRS = {
    "node_modules", ".git", ".venv", "venv", "__pycache__", 
    "dist", "build", ".next", ".nuxt", "target", "bin", "obj"
}

EXCLUDED_FILES = {
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe",
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot",
    ".min.js", ".min.css", ".map"
}

MAX_FILE_SIZE = 1024 * 1024  # 1MB


class Config:
    """CLI configuration manager"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.rohkun_dir = project_path / ROHKUN_DIR
        self.config_file = self.rohkun_dir / CONFIG_FILE
        self.reports_dir = self.rohkun_dir / REPORTS_DIR
        
    def ensure_directories(self):
        """Create .rohkun directories if they don't exist"""
        self.rohkun_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
    def load_config(self) -> dict:
        """Load configuration from .rohkun/config.json"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self, config: dict):
        """Save configuration to .rohkun/config.json"""
        self.ensure_directories()
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_api_key(self) -> Optional[str]:
        """
        Get API key from config or environment
        
        Priority:
        1. Environment variable (ROHKUN_API_KEY)
        2. Project config (.rohkun/config.json)
        3. Global config (~/.rohkun/config.json)
        """
        # 1. Check environment first
        api_key = os.getenv("ROHKUN_API_KEY")
        if api_key:
            return api_key
        
        # 2. Check project config
        if self.config_file.exists():
            config = self.load_config()
            api_key = config.get("api_key")
            if api_key:
                return api_key
        
        # 3. Check global config
        global_config_file = Path.home() / ".rohkun" / "config.json"
        if global_config_file.exists():
            try:
                with open(global_config_file, 'r') as f:
                    config = json.load(f)
                    api_key = config.get("api_key")
                    if api_key:
                        return api_key
            except:
                pass
        
        return None
    
    def set_api_key(self, api_key: str, global_config: bool = False):
        """
        Save API key to config
        
        Args:
            api_key: The API key to save
            global_config: If True, save to ~/.rohkun/config.json (global)
                          If False, save to .rohkun/config.json (project)
        """
        if global_config:
            # Save to global config
            global_config_dir = Path.home() / ".rohkun"
            global_config_dir.mkdir(exist_ok=True)
            global_config_file = global_config_dir / "config.json"
            
            config = {}
            if global_config_file.exists():
                try:
                    with open(global_config_file, 'r') as f:
                        config = json.load(f)
                except:
                    pass
            
            config["api_key"] = api_key
            with open(global_config_file, 'w') as f:
                json.dump(config, f, indent=2)
        else:
            # Save to project config
            config = self.load_config()
            config["api_key"] = api_key
            self.save_config(config)
