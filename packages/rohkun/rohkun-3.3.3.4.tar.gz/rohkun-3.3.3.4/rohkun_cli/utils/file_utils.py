"""
File system utilities
"""
from pathlib import Path
from typing import List, Set
from ..config import EXCLUDED_DIRS, EXCLUDED_FILES, MAX_FILE_SIZE


def should_scan_file(file_path: Path) -> bool:
    """Check if file should be scanned"""
    # Check file extension
    if any(file_path.name.endswith(ext) for ext in EXCLUDED_FILES):
        return False
    
    # Check file size
    try:
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return False
    except:
        return False
    
    return True


def scan_directory(project_path: Path, excluded_dirs: Set[str] = None) -> List[Path]:
    """
    Recursively scan directory for code files
    
    Args:
        project_path: Root directory to scan
        excluded_dirs: Additional directories to exclude
        
    Returns:
        List of file paths to analyze
    """
    if excluded_dirs is None:
        excluded_dirs = EXCLUDED_DIRS
    else:
        excluded_dirs = EXCLUDED_DIRS | excluded_dirs
    
    files = []
    
    for item in project_path.rglob("*"):
        # Skip excluded directories
        if any(excluded in item.parts for excluded in excluded_dirs):
            continue
        
        # Only process files
        if not item.is_file():
            continue
        
        # Check if should scan
        if should_scan_file(item):
            files.append(item)
    
    return files


def read_file_safe(file_path: Path) -> str:
    """
    Safely read file content
    
    Returns:
        File content as string, or empty string if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except:
        return ""


def estimate_project_size(project_path: Path) -> dict:
    """
    Estimate project size for authorization
    
    Returns:
        Dict with file count and size estimates
    """
    files = scan_directory(project_path)
    
    total_size = 0
    for file in files:
        try:
            total_size += file.stat().st_size
        except:
            pass
    
    return {
        "file_count": len(files),
        "size_mb": round(total_size / (1024 * 1024), 2)
    }
