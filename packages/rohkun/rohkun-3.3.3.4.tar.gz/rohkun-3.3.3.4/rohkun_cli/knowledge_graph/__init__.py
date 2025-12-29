"""
Knowledge Graph Visualization Module
Generates Obsidian-style network graphs for endpoint connections
Reads from existing JSON reports - no additional inputs needed
"""

from pathlib import Path
from typing import Optional

from .api import (
    KnowledgeGraphAPI,
    generate_api_graph_data,
    generate_dependency_graph_data,
    generate_comparison_data
)
from .server import start_knowledge_graph_server
from .html_generator import generate_standalone_html


def generate_graph(report_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Public entry point: generate a standalone knowledge-graph HTML from a report.

    Args:
        report_path: Path to a Rohkun report JSON file.
        output_path: Optional output HTML path. Defaults to <report_dir>/graph.html.

    Returns:
        Path to the generated HTML file.
    """
    return generate_standalone_html(report_path, output_path)

__all__ = [
    'KnowledgeGraphAPI',
    'generate_api_graph_data',
    'generate_dependency_graph_data',
    'generate_comparison_data',
    'start_knowledge_graph_server',
    'generate_standalone_html',
    'generate_graph'
]
