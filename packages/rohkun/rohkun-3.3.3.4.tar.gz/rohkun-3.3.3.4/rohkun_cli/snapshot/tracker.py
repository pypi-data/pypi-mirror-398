"""
Snapshot Tracker - Provides continuity across scans

This is what makes Rohkun valuable for AI:
1. Detects if we've scanned this project before (project hash)
2. Saves each scan as a snapshot
3. Computes diffs between snapshots
4. Tracks drift over time
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List


def generate_project_hash(project_path: Path) -> str:
    """
    Generate a unique hash for this project
    
    Uses project path + creation time to create stable identifier
    """
    # Use absolute path for consistency
    path_str = str(project_path.resolve())
    
    # Create hash
    hash_obj = hashlib.sha256(path_str.encode())
    hash_hex = hash_obj.hexdigest()[:6].upper()
    
    return f"RHKN-{hash_hex}"


class SnapshotTracker:
    """Tracks snapshots and provides continuity"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.rohkun_dir = project_path / ".rohkun"
        self.snapshots_dir = self.rohkun_dir / "snapshots"
        self.reports_dir = self.rohkun_dir / "reports"
        self.project_file = self.rohkun_dir / "project.json"
        self.snapshot_index_file = self.snapshots_dir / "snapshot_index.json"
        
        # Ensure directories exist
        self.rohkun_dir.mkdir(exist_ok=True)
        self.snapshots_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
    
    def get_or_create_project(self) -> Dict:
        """Get existing project or create new one"""
        if self.project_file.exists():
            with open(self.project_file, 'r') as f:
                return json.load(f)
        
        # Create new project
        project_hash = generate_project_hash(self.project_path)
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        project = {
            "project_hash": project_hash,
            "project_name": self.project_path.name,
            "created_at": timestamp,
            "first_snapshot": None,
            "last_snapshot": None,
            "total_snapshots": 0,
            "tracking_days": 0
        }
        
        with open(self.project_file, 'w') as f:
            json.dump(project, f, indent=2)
        
        return project
    
    def save_snapshot(self, analysis_results: Dict, report_filename: Optional[str] = None) -> Dict:
        """
        Save current analysis as a snapshot
        
        Args:
            analysis_results: Results from scanner
            report_filename: Optional report filename to link to this snapshot
        
        Returns snapshot metadata
        """
        project = self.get_or_create_project()
        
        # Load or create snapshot index
        if self.snapshot_index_file.exists():
            with open(self.snapshot_index_file, 'r') as f:
                index = json.load(f)
        else:
            index = {
                "project_hash": project["project_hash"],
                "snapshots": []
            }
        
        # Create snapshot
        timestamp = datetime.utcnow()
        snapshot_id = f"snapshot_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        snapshot = {
            "id": snapshot_id,
            "timestamp": timestamp.isoformat() + "Z",
            "sequence": len(index["snapshots"]) + 1,
            "endpoints": analysis_results['summary']['total_endpoints'],
            "api_calls": analysis_results['summary']['total_api_calls'],
            "connections": analysis_results['summary']['total_connections'],
            "files": analysis_results['files_scanned'],
            "drift": 0.0,  # Will be calculated if there's a previous snapshot
            "status": "baseline" if len(index["snapshots"]) == 0 else "healthy",
            "report_file": report_filename  # Link to report file
        }
        
        # Calculate drift if there's a previous snapshot
        if index["snapshots"]:
            previous = index["snapshots"][-1]
            snapshot["drift"] = self._calculate_drift(previous, snapshot)
            snapshot["compared_to"] = previous["id"]
            snapshot["compared_to_report"] = previous.get("report_file")  # Link to previous report
            
            # Update status based on drift
            if snapshot["drift"] < 0.2:
                snapshot["status"] = "healthy"
            elif snapshot["drift"] < 0.5:
                snapshot["status"] = "caution"
            else:
                snapshot["status"] = "high_drift"
        
        # Add to index
        index["snapshots"].append(snapshot)
        
        # Save index
        with open(self.snapshot_index_file, 'w') as f:
            json.dump(index, f, indent=2)
        
        # Update project
        project["last_snapshot"] = snapshot_id
        if project["first_snapshot"] is None:
            project["first_snapshot"] = snapshot_id
        project["total_snapshots"] = len(index["snapshots"])
        
        with open(self.project_file, 'w') as f:
            json.dump(project, f, indent=2)
        
        return snapshot
    
    def get_previous_snapshot(self) -> Optional[Dict]:
        """Get the previous snapshot for comparison"""
        if not self.snapshot_index_file.exists():
            return None
        
        with open(self.snapshot_index_file, 'r') as f:
            index = json.load(f)
        
        if len(index["snapshots"]) < 2:
            return None
        
        return index["snapshots"][-2]
    
    def get_previous_report_path(self) -> Optional[Path]:
        """Get the path to the previous snapshot's report file"""
        previous = self.get_previous_snapshot()
        if not previous or not previous.get("report_file"):
            return None
        
        report_identifier = previous["report_file"]
        
        # New format: folder number (e.g., "1", "2")
        if report_identifier.isdigit():
            report_path = self.reports_dir / report_identifier / "report.json"
        else:
            # Old format: filename (backward compatibility)
            report_path = self.reports_dir / report_identifier
        
        if report_path.exists():
            return report_path
        return None
    
    def _calculate_drift(self, previous: Dict, current: Dict) -> float:
        """
        Calculate drift score between snapshots
        
        Drift measures structural change:
        - 0.0-0.2: Low drift (healthy)
        - 0.2-0.5: Medium drift (review)
        - 0.5+: High drift (significant changes)
        """
        drift = 0.0
        
        # Endpoint changes
        endpoint_change = abs(current.get("endpoints", 0) - previous.get("endpoints", 0))
        drift += endpoint_change * 0.1
        
        # API call changes
        api_call_change = abs(current.get("api_calls", 0) - previous.get("api_calls", 0))
        drift += api_call_change * 0.1
        
        # Connection changes (handle old snapshots that might not have this)
        connection_change = abs(current.get("connections", 0) - previous.get("connections", 0))
        drift += connection_change * 0.15
        
        # File changes
        file_change_ratio = abs(current.get("files", 0) - previous.get("files", 0)) / max(previous.get("files", 1), 1)
        if file_change_ratio > 0.2:
            drift += file_change_ratio * 0.3
        
        return min(drift, 1.0)  # Cap at 1.0
    
    def get_snapshot_summary(self) -> Dict:
        """Get summary of all snapshots for display"""
        if not self.snapshot_index_file.exists():
            return {
                "total": 0,
                "first": None,
                "last": None,
                "drift_trend": "N/A"
            }
        
        with open(self.snapshot_index_file, 'r') as f:
            index = json.load(f)
        
        snapshots = index["snapshots"]
        
        if not snapshots:
            return {
                "total": 0,
                "first": None,
                "last": None,
                "drift_trend": "N/A"
            }
        
        # Calculate average drift
        recent_drifts = [s["drift"] for s in snapshots[-5:] if "drift" in s]
        avg_drift = sum(recent_drifts) / len(recent_drifts) if recent_drifts else 0.0
        
        if avg_drift < 0.2:
            drift_trend = "Stable"
        elif avg_drift < 0.5:
            drift_trend = "Moderate"
        else:
            drift_trend = "High"
        
        return {
            "total": len(snapshots),
            "first": snapshots[0],
            "last": snapshots[-1],
            "drift_trend": drift_trend,
            "avg_drift": avg_drift
        }
