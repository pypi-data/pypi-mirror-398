"""
Frontend UI inspection using RenderTell engine
Captures UI snapshots and detects issues (overlaps, dead buttons, broken images, etc.)
"""
import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


def find_html_files(project_path: Path) -> List[Path]:
    """
    Find all HTML files in project
    
    Args:
        project_path: Project root directory
        
    Returns:
        List of HTML file paths (excluding node_modules, .git, dist, build)
    """
    html_files = []
    skip_dirs = {'node_modules', '.git', 'dist', 'build', '.next', '.nuxt', 'venv', '__pycache__', '.rohkun'}
    
    for html_file in project_path.rglob("*.html"):
        # Skip files in excluded directories
        parts = html_file.parts
        if any(skip_dir in parts for skip_dir in skip_dirs):
            continue
        html_files.append(html_file)
    
    return html_files


def get_rendertell_engine_path() -> Optional[Path]:
    """
    Get path to RenderTell engine
    
    Returns:
        Path to engine directory, or None if not found
    """
    # First, try bundled engine (for pip-installed package)
    current_file = Path(__file__).resolve()
    bundled_engine = current_file.parent / "rendertell_engine"
    
    if bundled_engine.exists() and (bundled_engine / "dist" / "index.js").exists():
        return bundled_engine
    
    # Fallback: Try to find RenderTell in development environment
    cli_dir = current_file.parent.parent.parent  # Go up from rohkun_cli -> cli-v2 -> Rohkun
    rendertell_path = cli_dir / "RenderTell" / "packages" / "engine"
    
    if rendertell_path.exists() and (rendertell_path / "dist" / "index.js").exists():
        return rendertell_path
    
    # Try alternative path (if RenderTell is at project root)
    alt_path = cli_dir.parent / "RenderTell" / "packages" / "engine"
    if alt_path.exists() and (alt_path / "dist" / "index.js").exists():
        return alt_path
    
    return None


def capture_ui_snapshot(html_path: Path, engine_path: Path) -> Optional[Dict[str, Any]]:
    """
    Capture UI snapshot using RenderTell engine via Node.js
    
    Args:
        html_path: Path to HTML file
        engine_path: Path to RenderTell engine directory
        
    Returns:
        Snapshot dict, or None if capture failed
    """
    try:
        # Convert Windows path to file:// URL format
        abs_path = html_path.resolve()
        file_url = f"file:///{str(abs_path).replace(chr(92), '/')}"
        
        # Node.js script to capture snapshot
        engine_js_path = (engine_path.resolve() / "dist" / "index.js")
        # Convert Windows path to forward slashes for Node.js require
        engine_js_path_str = str(engine_js_path).replace('\\', '/')
        
        node_script = f"""
const {{ captureSnapshot }} = require('{engine_js_path_str}');

captureSnapshot('{file_url}', {{
    performanceProfile: 'balanced',
    viewportOnly: true
}})
.then(snapshot => {{
    console.log(JSON.stringify(snapshot));
}})
.catch(error => {{
    console.error(JSON.stringify({{ error: error.message, stack: error.stack }}));
    process.exit(1);
}});
"""
        
        # Run Node.js
        result = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout per file
        )
        
        if result.returncode != 0:
            # Try to parse error from stderr or stdout
            error_output = result.stderr or result.stdout
            try:
                # Look for JSON error in output
                error_data = json.loads(error_output)
                print(f"⚠️  Failed to capture {html_path.name}: {error_data.get('error', 'Unknown error')}", file=sys.stderr)
            except:
                # Show first 200 chars of error
                error_preview = error_output[:200] if error_output else 'Unknown error'
                print(f"⚠️  Failed to capture {html_path.name}: {error_preview}", file=sys.stderr)
            return None
        
        # Parse snapshot JSON - filter out any non-JSON lines (like "Using system Chrome...")
        output = result.stdout.strip()
        if not output:
            print(f"⚠️  Empty output from RenderTell for {html_path.name}", file=sys.stderr)
            return None
        
        # Filter out non-JSON lines (e.g., "Using system Chrome: ...")
        lines = output.split('\n')
        json_lines = [line for line in lines if line.strip().startswith('{')]
        if not json_lines:
            print(f"⚠️  No JSON found in RenderTell output for {html_path.name}", file=sys.stderr)
            return None
        
        # Use the last line that starts with '{' (should be the full JSON)
        json_output = json_lines[-1]
        
        try:
            snapshot = json.loads(json_output)
            return snapshot
        except json.JSONDecodeError as e:
            # Debug: show first 500 chars of output
            print(f"⚠️  Invalid JSON from RenderTell for {html_path.name}: {e}", file=sys.stderr)
            print(f"   Output preview: {json_output[:500]}", file=sys.stderr)
            return None
        
    except subprocess.TimeoutExpired:
        print(f"⚠️  Timeout capturing {html_path.name} (took >30s)", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️  Invalid JSON from RenderTell for {html_path.name}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️  Error capturing {html_path.name}: {e}", file=sys.stderr)
        return None


def analyze_snapshot(snapshot: Dict[str, Any], file_path: str) -> List[Dict[str, Any]]:
    """
    Analyze snapshot and return list of issues
    
    Args:
        snapshot: Snapshot data from RenderTell
        file_path: Path to HTML file (for context)
        
    Returns:
        List of issue dicts with type, element, message, severity
    """
    issues = []
    elements = snapshot.get("elements", {})
    
    for element_id, element in elements.items():
        # Check for covered elements
        visibility = element.get("visibility", {})
        if visibility.get("isCovered"):
            covering_element = visibility.get("coveringElement", "unknown")
            issues.append({
                "type": "covered",
                "element": element_id,
                "message": f"Element {element_id} is covered by {covering_element}",
                "severity": "high",
                "file": file_path
            })
        
        # Check for dead buttons (no click handlers)
        tag = element.get("tag", "").upper()
        if tag == "BUTTON" or (tag == "A" and element.get("href")):
            event_listeners = element.get("eventListeners", [])
            has_click = any(
                listener.get("type") == "click" 
                for listener in event_listeners
            )
            if not has_click and tag == "BUTTON":
                issues.append({
                    "type": "dead_button",
                    "element": element_id,
                    "message": f"Button {element_id} has no click handler",
                    "severity": "medium",
                    "file": file_path
                })
        
        # Check for broken images
        if tag == "IMG":
            image_data = element.get("image", {})
            if image_data.get("broken"):
                src = image_data.get("src", "unknown")
                issues.append({
                    "type": "broken_image",
                    "element": element_id,
                    "message": f"Image {src} failed to load",
                    "severity": "medium",
                    "file": file_path
                })
        
        # Check for zero-size visible elements (might be layout issues)
        rect = element.get("rect", {})
        width = rect.get("width", 0)
        height = rect.get("height", 0)
        if width == 0 and height == 0 and visibility.get("isVisible"):
            issues.append({
                "type": "zero_size",
                "element": element_id,
                "message": f"Element {element_id} is visible but has zero size",
                "severity": "low",
                "file": file_path
            })
    
    return issues


def capture_frontend_snapshots(project_path: Path) -> Dict[str, Any]:
    """
    Capture UI snapshots for all HTML files in project
    
    Args:
        project_path: Project root directory
        
    Returns:
        Dict with snapshots, issues, and summary
    """
    # Check if RenderTell engine is available
    engine_path = get_rendertell_engine_path()
    if not engine_path:
        # Silently skip if RenderTell not found (optional feature)
        return {
            "snapshots": [],
            "issues": [],
            "summary": {
                "total_files": 0,
                "total_elements": 0,
                "total_issues": 0,
                "issues_by_type": {}
            },
            "enabled": False,
            "reason": "RenderTell engine not found"
        }
    
    # Check if Node.js is available
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return {
            "snapshots": [],
            "issues": [],
            "summary": {
                "total_files": 0,
                "total_elements": 0,
                "total_issues": 0,
                "issues_by_type": {}
            },
            "enabled": False,
            "reason": "Node.js not found"
        }
    
    # Find HTML files
    html_files = find_html_files(project_path)
    
    if not html_files:
        return {
            "snapshots": [],
            "issues": [],
            "summary": {
                "total_files": 0,
                "total_elements": 0,
                "total_issues": 0,
                "issues_by_type": {}
            },
            "enabled": True
        }
    
    # Capture snapshots
    snapshots = []
    all_issues = []
    
    for html_file in html_files:
        try:
            snapshot = capture_ui_snapshot(html_file, engine_path)
            if snapshot:
                issues = analyze_snapshot(snapshot, str(html_file.relative_to(project_path)))
                
                snapshots.append({
                    "file": str(html_file.relative_to(project_path)),
                    "url": f"file:///{str(html_file.resolve()).replace(chr(92), '/')}",
                    "timestamp": snapshot.get("meta", {}).get("timestamp"),
                    "elements": snapshot.get("elements", {}),
                    "issues": issues
                })
                all_issues.extend(issues)
        except Exception as e:
            print(f"⚠️  Error processing {html_file.name}: {e}", file=sys.stderr)
            continue
    
    # Calculate summary
    total_elements = sum(len(s.get("elements", {})) for s in snapshots)
    issues_by_type = {}
    for issue in all_issues:
        issue_type = issue.get("type", "unknown")
        issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1
    
    return {
        "snapshots": snapshots,
        "issues": all_issues,
        "summary": {
            "total_files": len(snapshots),
            "total_elements": total_elements,
            "total_issues": len(all_issues),
            "issues_by_type": issues_by_type
        },
        "enabled": True
    }

