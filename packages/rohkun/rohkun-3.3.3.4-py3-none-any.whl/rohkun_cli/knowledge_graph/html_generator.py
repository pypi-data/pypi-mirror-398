"""
Generate standalone HTML file with embedded graph data
Reference Implementation: Pre-calculated 2D layout acts as the anchor for 3D animation.
"""
import json
import re
from pathlib import Path
from typing import Dict, Optional

from .api import KnowledgeGraphAPI


def generate_standalone_html(
    report_path: Path,
    output_path: Optional[Path] = None,
    graph_type: str = 'api'
) -> Path:
    """
    Generate standalone HTML file with embedded graph data and 3D intro
    """
    # Load report
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # Generate ALL graph types
    api = KnowledgeGraphAPI(report)
    api_graph_data = api.get_api_connections_graph()
    dependency_graph_data = api.get_dependency_graph()
    function_dependency_graph_data = api.get_function_dependency_graph()
    
    # Read the base HTML template
    ui_dir = Path(__file__).parent / 'ui'
    html_template_path = ui_dir / 'graph_v2.html'
    
    with open(html_template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Embed ALL graph types in the HTML
    embedded_data = {
        'api': {
            'nodes': api_graph_data.get('nodes', []),
            'edges': api_graph_data.get('edges', []),
            'summary': api_graph_data.get('summary', {})
        },
        'dependencies': {
            'nodes': dependency_graph_data.get('nodes', []),
            'edges': dependency_graph_data.get('edges', []),
            'summary': dependency_graph_data.get('summary', {})
        },
        'function_dependencies': {
            'nodes': function_dependency_graph_data.get('nodes', []),
            'edges': function_dependency_graph_data.get('edges', []),
            'summary': function_dependency_graph_data.get('summary', {})
        },
        'report': report
    }
    
    # Embed source code content for dependency nodes (Files)
    # We try to read the file content from disk if available
    project_path_str = report.get('project', {}).get('path', '')
    if project_path_str:
        try:
            project_path = Path(project_path_str)
            dep_nodes = embedded_data['dependencies']['nodes']
            for node in dep_nodes:
                file_id = node.get('id', '')
                if not file_id: continue
                
                # Try to find the file
                # 1. As relative to project path
                full_path = project_path / file_id
                
                # 2. Check if file_id is absolute or relative to CWD (fallback)
                if not full_path.exists():
                    full_path = Path(file_id)
                
                if full_path.exists() and full_path.is_file():
                    try:
                        # Limit size to avoid massive HTML files (e.g. 100KB limit per file)
                        if full_path.stat().st_size < 100 * 1024: 
                            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                                node['content'] = f.read()
                        else:
                            node['content'] = f"# File too large to embed ({full_path.stat().st_size} bytes)"
                    except Exception as e:
                        node['content'] = f"# Error reading file: {str(e)}"
        except Exception as e:
            print(f"Warning: Failed to embed source code: {e}")

    # Escape the JSON for embedding
    embedded_json = json.dumps(embedded_data, indent=2)
    embedded_data_script = f"""
    <script id="embedded-graph-data" type="application/json">
{embedded_json}
    </script>
    """
    
    # Inject 3D intro enhancements
    html_content = inject_3d_intro(html_content)
    
    # UPDATE LEGENDS to match Deterministic Logic
    # We replace the hardcoded legends in the template with updated ones
    
    new_api_legend = (
        '\n'
        '        const apiLegend = [\n'
        "            {color: '#3b82f6', label: 'GET', desc: 'Retrieves data from the server. Safe and idempotent.'},\n"
        "            {color: '#00FF94', label: 'POST', desc: 'Submits data to be processed. Creates new resources.'},\n"
        "            {color: '#FFE600', label: 'PUT', desc: 'Updates a resource or creates it if missing. Idempotent.'},\n"
        "            {color: '#00F0FF', label: 'PATCH', desc: 'Partially updates a resource.'},\n"
        "            {color: '#FF003C', label: 'DELETE', desc: 'Removes a resource.'},\n"
        "            {color: '#BC13FE', label: 'HIGH IMPACT', desc: 'Critical API endpoints with high connectivity or central importance.'},\n"
        "            {color: '#374151', label: 'UNUSED', desc: 'Endpoints that are defined but have no detected internal calls.'},\n"
        "            {color: '#6b7280', label: 'UNKNOWN', desc: 'Method type could not be determined statically.'}\n"
        '        ];\n'
        '    '
    )
    
    new_func_dep_legend = (
        '\n'
        '        const funcDepLegend = [\n'
        "            {color: '#7c3aed', label: 'FUNCTION', desc: 'A function definition found in the codebase.'},\n"
        "            {color: '#FFE600', label: 'CALLER', desc: 'A function that actively calls other functions.'},\n"
        "            {color: '#00F0FF', label: 'EXTERNAL', desc: 'External library function or system API call.'},\n"
        "            {color: '#BC13FE', label: 'HIGH IMPACT', desc: 'Core functions that are heavily used across the project.'},\n"
        "            {color: '#374151', label: 'UNUSED', desc: 'Functions that are never called internally.'},\n"
        "            {color: '#6b7280', label: 'UNKNOWN', desc: 'Function type could not be determined.'}\n"
        '        ];\n'
        '    '
    )
    
    new_dep_legend = (
        '\n'
        '        const depLegend = [\n'
        "            {color: '#00F0FF', label: 'PYTHON', desc: 'Python source file (.py).'},\n"
        "            {color: '#FFE600', label: 'JAVASCRIPT', desc: 'JavaScript source file (.js).'},\n"
        "            {color: '#3178c6', label: 'TYPESCRIPT', desc: 'TypeScript source file (.ts).'},\n"
        "            {color: '#BC13FE', label: 'HIGH IMPACT', desc: 'Central modules imported by many other files. \"Traffic Hubs\".'},\n"
        "            {color: '#374151', label: 'STANDALONE', desc: 'Files with no detected imports or incoming dependencies. \"Islands\".'},\n"
        "            {color: '#6b7280', label: 'UNKNOWN/OTHER', desc: 'Files with unmapped extensions or ambiguous types.'}\n"
        '        ];\n'
        '    '
    )
    
    # Regex replacement to be robust against spacing
    html_content = re.sub(r'const apiLegend = \[.*?\];', new_api_legend, html_content, flags=re.DOTALL)
    html_content = re.sub(r'const funcDepLegend = \[.*?\];', new_func_dep_legend, html_content, flags=re.DOTALL)
    html_content = re.sub(r'const depLegend = \[.*?\];', new_dep_legend, html_content, flags=re.DOTALL)
    
    # Insert the embedded data script right before the main script tag
    script_start = html_content.find('<script>')
    if script_start == -1:
        script_start = html_content.find('<script ')
    
    if script_start != -1:
        html_content = (
            html_content[:script_start] + 
            embedded_data_script + '\n    ' +
            html_content[script_start:]
        )
    else:
        html_content = html_content.replace('</body>', embedded_data_script + '\n</body>')
    
    # Determine output path
    if output_path is None:
        output_path = report_path.parent / "graph.html"
    
    # Write the standalone HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path


def inject_3d_intro(html_content: str) -> str:
    """
    Inject 3D intro view code into the HTML template
        Uses the Reference Implementation logic: Calculate 2D Layout (for Z-axis positions) -> Animate 3D towards it -> Lock Z-axis for interaction.
    """
    # 1. Add Three.js library
    three_js_script = '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>'
    if 'three.js' not in html_content.lower():
        html_content = html_content.replace(
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>',
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>\n    ' + three_js_script
        )
    
    # 2. Add 3D CSS styles - HUD / Dock System
    css_3d = """
        /* --- HUD SYSTEM --- */
        #canvas-3d {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 1;
            background: #000;
        }
        
        /* Right-side Detail Drawer */
        #info-panel {
            position: fixed;
            top: 0; right: 0;
            left: auto !important; /* CRITICAL: Unset legacy 'left' positioning */
            width: 350px; /* Reduced width */
            height: 100%;
            background: rgba(12, 12, 16, 0.95);
            border-left: 1px solid #333;
            box-shadow: -10px 0 40px rgba(0,0,0,0.5);
            transform: translateX(100%); /* Start HIDDEN (off-screen right) */
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            z-index: 1000;
            overflow-y: auto;
            padding: 24px;
            backdrop-filter: blur(20px);
            display: block !important;
        }
        
        #info-panel.active {
            transform: translateX(0); /* Slide in when active */
        }
        
        #info-panel h2 {
            margin-top: 0;
            font-size: 24px;
            font-weight: 300;
            color: #fff;
            border-bottom: 1px solid #333;
            padding-bottom: 16px;
            margin-bottom: 16px;
            letter-spacing: -0.5px;
        }
        
        .panel-section {
            margin-bottom: 24px;
        }
        
        .panel-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #666;
            margin-bottom: 8px;
            display: block;
        }
        
        /* Bottom Control Dock */
        .control-dock {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 8px;
            background: rgba(20, 20, 25, 0.8);
            padding: 8px 12px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 900;
            transition: transform 0.2s ease, background 0.2s;
        }
        
        .control-dock:hover {
            background: rgba(30, 30, 35, 0.95);
            transform: translateX(-50%) translateY(-2px);
        }
        
        .dock-btn {
            background: transparent;
            border: none;
            color: #888;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            font-size: 10px;
            font-family: 'Inter', system-ui, sans-serif;
            font-weight: 500;
            transition: all 0.2s;
            min-width: 64px;
        }
        
        .dock-btn:hover {
            color: #fff;
            background: rgba(255,255,255,0.05);
        }
        
        .dock-btn.active {
            color: #4488ff;
            background: rgba(68, 136, 255, 0.1);
        }
        
        .dock-icon {
            font-size: 18px;
            margin-bottom: 2px;
        }
        
        /* Close Button inside Panel */
        .panel-close-btn {
            position: absolute;
            top: 24px;
            right: 24px;
            background: transparent;
            border: none;
            color: #666;
            cursor: pointer;
            font-size: 24px;
            line-height: 1;
            padding: 4px;
            transition: color 0.2s;
        }
        .panel-close-btn:hover {
            color: #fff;
        }
        
        /* Hide old elements */
        #panel-toggle, #btn-cam, #btn-lens, #btn-snapshot, #btn-reset { display: none !important; }
        .floating-controls { display: none !important; }
        
        /* KILL CLUTTER - Hide all legacy panels */
        #diff-panel, #diff-story-panel, #diff-summary { display: none !important; }
        #filter-menu, #search-box, #legend, #console-log { display: none !important; }
        /* Hide checkbox lists if they are free-floating */
        .filter-context { display: none !important; }
    """
    
    style_end = html_content.find('</style>')
    if style_end != -1:
        html_content = html_content[:style_end] + css_3d + '\n    ' + html_content[style_end:]
    
    # 3. Add 3D canvas container with HUD
    canvas_3d_html = """
    <!-- 3D Intro Canvas -->
    <div id="canvas-3d"></div>
    
    <!-- HUD Control Dock -->
    <div class="control-dock">
        <button class="dock-btn" onclick="exportScreenshot()" title="Take Screenshot">
            <span class="dock-icon">📸</span>
            <span>SNAP</span>
        </button>
    </div>
    """
    if '<div id="canvas-3d">' not in html_content:
        # 3D-only mode: network-container not needed, but keep it hidden if it exists in template
        network_container_pos = html_content.find('<div id="network-container">')
        if network_container_pos != -1:
            html_content = html_content[:network_container_pos] + canvas_3d_html + html_content[network_container_pos:]
            # Hide 2D network container (3D-only mode)
            html_content = html_content.replace(
                '<div id="network-container">',
                '<div id="network-container" style="display: none; opacity: 0;">'
            )
    
    # 4. Add 3D JavaScript code - REFERENCE IMPLEMENTATION LOGIC
    # Load 3D visualization code from external file
    try:
        ui_dir = Path(__file__).parent / 'ui'
        js_3d_path = ui_dir / "visualizer_3d.js"
        with open(js_3d_path, "r", encoding="utf-8") as f:
            js_3d = f.read()
    except Exception as e:
        print(f"Warning: Could not load 3D visualization code: {e}")
        js_3d = "// 3D visualization code not loaded"
    
    init_console_pos = html_content.find('// Initialize console')
    if init_console_pos != -1 and '// 3D ENGINE VARIABLES' not in html_content: 
        html_content = html_content[:init_console_pos] + js_3d + '\n        ' + html_content[init_console_pos:]
    
    # 5. Overwrite Load Handler - 3D ONLY (no 2D network)
    marker = "window.addEventListener('load', function() {"
    new_load_logic = (
        "\n"
        "            updateLegend(apiLegend);\n"
        "            \n"
        "            // 3D-only mode: Initialize 3D view directly (no 2D network)\n"
        "            if (typeof THREE !== 'undefined') {\n"
        "                console.log('[INIT] Starting 3D-only mode...');\n"
        "                init3DView();\n"
        "            } else {\n"
        "                console.error('[INIT] THREE.js not available!');\n"
        "            }\n"
        "            \n"
        "            setTimeout(() => initEdgeAnimationSystem(), 5000);\n"
        "            \n"
        "            "
    )
    
    if marker in html_content:
        start_idx = html_content.find(marker) + len(marker)
        end_idx = html_content.find("// Initialize edge animation system", start_idx)
        if start_idx != -1 and end_idx != -1 and (end_idx - start_idx) < 1000:
            html_content = html_content[:start_idx] + new_load_logic + html_content[end_idx:]
    
    # 6. Inject UI Buttons for 3D View - DEPRECATED (Moved to Dock)
    # We remove the original snapshot button as it's now in the dock
    snapshot_btn = '<button onclick="exportScreenshot()">📸 SNAPSHOT</button>'
    if snapshot_btn in html_content:
        html_content = html_content.replace(snapshot_btn, '')
    
    # 6.5. Replace exportScreenshot function to capture 3D canvas properly
    screenshot_function_start = "function exportScreenshot() {"
    if screenshot_function_start in html_content:
        # Find the function and replace it
        start_idx = html_content.find(screenshot_function_start)
        # Find the end of the function (next function or closing brace)
        end_markers = [
            "\n        function ",
            "\n        function\t",
            "\n    function ",
            "\n    function\t"
        ]
        end_idx = len(html_content)
        for marker in end_markers:
            next_func = html_content.find(marker, start_idx + 50)
            if next_func != -1 and next_func < end_idx:
                end_idx = next_func
        
        # If we didn't find another function, look for the closing brace pattern
        if end_idx == len(html_content):
            # Count braces to find function end
            brace_count = 0
            in_function = False
            for i in range(start_idx, len(html_content)):
                if html_content[i] == '{':
                    brace_count += 1
                    in_function = True
                elif html_content[i] == '}':
                    brace_count -= 1
                    if in_function and brace_count == 0:
                        end_idx = i + 1
                        break
        
        # Replace with fixed function
        new_screenshot_function = """function exportScreenshot() {
            try {
                // Check if 3D renderer exists
                if (typeof renderer3d !== 'undefined' && renderer3d && renderer3d.domElement) {
                    // Capture Three.js canvas directly
                    const canvas = renderer3d.domElement;
                    const dataURL = canvas.toDataURL('image/png');
                    
                    // Create download link
                    const link = document.createElement('a');
                    link.download = `rohkun-3d-graph-${Date.now()}.png`;
                    link.href = dataURL;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    // Show success message
                    if (typeof showToast === 'function') {
                        showToast('SNAPSHOT SAVED!');
                    }
                    if (typeof addLogEntry === 'function') {
                        addLogEntry('Screenshot exported successfully');
                    }
                } else {
                    // Fallback: try html2canvas on canvas-3d container
                    if (typeof html2canvas !== 'undefined') {
                        const container = document.getElementById('canvas-3d');
                        if (container) {
                            html2canvas(container, {
                                backgroundColor: '#050505',
                                scale: 2,
                                useCORS: true,
                                logging: false,
                                allowTaint: true
                            }).then(canvas => {
                                const link = document.createElement('a');
                                link.download = `rohkun-3d-graph-${Date.now()}.png`;
                                link.href = canvas.toDataURL('image/png');
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                                
                                if (typeof showToast === 'function') {
                                    showToast('SNAPSHOT SAVED!');
                                }
                            }).catch(error => {
                                console.error('Screenshot failed:', error);
                                if (typeof showToast === 'function') {
                                    showToast('SNAPSHOT FAILED');
                                }
                            });
                        } else {
                            alert('Canvas not found');
                        }
                    } else {
                        alert('Screenshot functionality not available');
                    }
                }
            } catch (error) {
                console.error('Screenshot error:', error);
                if (typeof showToast === 'function') {
                    showToast('SNAPSHOT FAILED: ' + error.message);
                }
            }
        }"""
        
        html_content = html_content[:start_idx] + new_screenshot_function + html_content[end_idx:]
        
    # 7. Replace Old Info Panel with New Context Drawer
    # Robust removal of old panel by finding specific markers
    start_marker = '<div id="info-panel">'
    start_idx = html_content.find(start_marker)
    
    new_drawer_html = """
    <!-- Context Drawer (Slide-out) -->
    <div id="info-panel">
        <button class="panel-close-btn" onclick="toggleInfoPanel()">×</button>
        <div id="drawer-content">
            <div style="display:flex; align-items:center; justify-content:center; height:100%; color:#666;">
                Select a node to view details
            </div>
        </div>
    </div>
    """

    if start_idx != -1:
        # The template has a specific close button at the end of the panel div
        end_marker = '<button class="panel-close-btn" onclick="toggleInfoPanel()">×</button>\n    </div>'
        end_idx = html_content.find(end_marker, start_idx)
        
        if end_idx != -1:
             full_end_idx = end_idx + len(end_marker)
             html_content = html_content[:start_idx] + new_drawer_html + html_content[full_end_idx:]
        else:
             # Fallback to regex if exact marker missing (safety net)
             html_content = re.sub(r'<div id="info-panel">.*?</div>', new_drawer_html, html_content, flags=re.DOTALL)
             
    # Also hide/remove the old toggle button
    html_content = html_content.replace('<div id="panel-toggle" onclick="toggleInfoPanel()">i</div>', '')
    
    # Remove old controls container to avoid clutter at bottom
    # Look for specific control button to identify block start/end if regex fails
    if '<div id="controls">' in html_content:
        html_content = re.sub(r'<div id="controls">.*?</div>', '', html_content, flags=re.DOTALL)
            
    return html_content
