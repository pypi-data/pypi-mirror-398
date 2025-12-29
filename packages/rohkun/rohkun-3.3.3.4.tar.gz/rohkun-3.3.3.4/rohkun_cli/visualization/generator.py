"""
Visualization Generator - Creates interactive 3D network graph HTML
"""
import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


def generate_visualization(report: Dict, project_path: Path) -> Path:
    """
    Generate interactive 3D visualization HTML file
    
    Args:
        report: Report dictionary with endpoints, api_calls, connections
        project_path: Project root path
        
    Returns:
        Path to generated HTML file
    """
    # Create visualization directory
    viz_dir = project_path / ".rohkun" / "visualization"
    viz_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate graph data
    graph_data = build_graph_data(report)
    
    # Generate HTML
    html_content = generate_html(graph_data, report)
    
    # Save HTML file
    html_file = viz_dir / "index.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Save graph data as JSON for the HTML to load
    data_file = viz_dir / "graph_data.json"
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)
    
    return html_file


def build_graph_data(report: Dict) -> Dict:
    """
    Build graph data structure from report
    
    Returns:
        Dict with nodes and links for visualization
    """
    endpoints = report.get('endpoints', [])
    api_calls = report.get('api_calls', [])
    connections = report.get('connections', [])
    high_impact_nodes = report.get('high_impact_nodes', [])
    
    # Build node map
    nodes = {}
    node_id_counter = 0
    
    # Add endpoint nodes
    for endpoint in endpoints:
        node_id = f"endpoint_{node_id_counter}"
        node_id_counter += 1
        
        method = endpoint.get('method', 'GET')
        path = endpoint.get('path', 'unknown')
        file_path = endpoint.get('file', 'unknown')
        
        # Create unique key for this endpoint
        endpoint_key = f"{method}:{path}"
        
        if endpoint_key not in nodes:
            nodes[endpoint_key] = {
                'id': node_id,
                'label': f"{method} {path}",
                'type': 'endpoint',
                'method': method,
                'path': path,
                'file': file_path,
                'line': endpoint.get('line', 0),
                'confidence': endpoint.get('confidence', 'medium'),
                'size': 1.0,
                'connections': 0
            }
    
    # Add API call nodes
    for api_call in api_calls:
        node_id = f"api_call_{node_id_counter}"
        node_id_counter += 1
        
        method = api_call.get('method', 'GET')
        url = api_call.get('url', 'unknown')
        file_path = api_call.get('file', 'unknown')
        
        # Create unique key
        call_key = f"call:{file_path}:{api_call.get('line', 0)}"
        
        if call_key not in nodes:
            nodes[call_key] = {
                'id': node_id,
                'label': f"{method} {url[:50]}",
                'type': 'api_call',
                'method': method,
                'url': url,
                'file': file_path,
                'line': api_call.get('line', 0),
                'confidence': api_call.get('confidence', 'medium'),
                'size': 0.8,
                'connections': 0
            }
    
    # Build links from connections
    links = []
    link_set = set()  # To avoid duplicates
    
    for conn in connections:
        endpoint = conn.get('endpoint', {})
        api_call = conn.get('api_call', {})
        
        endpoint_key = f"{endpoint.get('method', 'GET')}:{endpoint.get('path', 'unknown')}"
        call_key = f"call:{api_call.get('file', 'unknown')}:{api_call.get('line', 0)}"
        
        if endpoint_key in nodes and call_key in nodes:
            link_key = (nodes[endpoint_key]['id'], nodes[call_key]['id'])
            
            if link_key not in link_set:
                link_set.add(link_key)
                links.append({
                    'source': nodes[endpoint_key]['id'],
                    'target': nodes[call_key]['id'],
                    'confidence': conn.get('confidence', 'medium'),
                    'confidence_score': conn.get('confidence_score', 50)
                })
                
                # Update connection counts
                nodes[endpoint_key]['connections'] += 1
                nodes[call_key]['connections'] += 1
    
    # Update node sizes based on connections (high impact nodes are bigger)
    max_connections = max((n['connections'] for n in nodes.values()), default=1)
    
    for node_key, node in nodes.items():
        # Base size on connection count
        if max_connections > 0:
            node['size'] = 0.5 + (node['connections'] / max_connections) * 1.5
        
        # Check if it's a high impact node
        for impact_node in high_impact_nodes:
            target = impact_node.get('target', '')
            if target in node['label'] or target in node.get('path', ''):
                node['size'] *= 1.5  # Make high impact nodes bigger
                node['high_impact'] = True
                break
    
    # Convert to lists
    nodes_list = list(nodes.values())
    
    return {
        'nodes': nodes_list,
        'links': links,
        'summary': {
            'total_nodes': len(nodes_list),
            'total_links': len(links),
            'endpoints': len([n for n in nodes_list if n['type'] == 'endpoint']),
            'api_calls': len([n for n in nodes_list if n['type'] == 'api_call'])
        }
    }


def generate_html(graph_data: Dict, report: Dict) -> str:
    """
    Generate the HTML content with Three.js 3D visualization
    """
    project_name = report.get('project', {}).get('name', 'Unknown Project')
    summary = report.get('summary', {})
    
    # Escape JSON for embedding
    graph_data_json = json.dumps(graph_data).replace('</script>', '<\\/script>')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rohkun Visualization - {project_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            background: #030303;
            color: #ffffff;
            overflow: hidden;
            height: 100vh;
        }}
        
        #canvas-container {{
            width: 100%;
            height: 100vh;
            position: relative;
        }}
        
        #info-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(5, 5, 5, 0.95);
            border: 1px solid #7c3aed;
            border-radius: 8px;
            padding: 20px;
            max-width: 350px;
            z-index: 100;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 30px rgba(124, 58, 237, 0.3);
        }}
        
        #info-panel h1 {{
            font-size: 18px;
            margin-bottom: 12px;
            color: #7c3aed;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        #info-panel .stat {{
            margin: 8px 0;
            font-size: 13px;
            color: #a1a1a1;
        }}
        
        #info-panel .stat strong {{
            color: #ffffff;
        }}
        
        #controls {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(5, 5, 5, 0.95);
            border: 1px solid #7c3aed;
            border-radius: 8px;
            padding: 15px 25px;
            z-index: 100;
            backdrop-filter: blur(10px);
            display: flex;
            gap: 15px;
            align-items: center;
        }}
        
        #controls button {{
            background: transparent;
            border: 1px solid #7c3aed;
            color: #7c3aed;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            transition: all 0.2s;
        }}
        
        #controls button:hover {{
            background: #7c3aed;
            color: #ffffff;
            box-shadow: 0 0 15px rgba(124, 58, 237, 0.5);
        }}
        
        #legend {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(5, 5, 5, 0.95);
            border: 1px solid #7c3aed;
            border-radius: 8px;
            padding: 15px;
            z-index: 100;
            backdrop-filter: blur(10px);
            font-size: 12px;
        }}
        
        #legend h3 {{
            color: #7c3aed;
            margin-bottom: 10px;
            font-size: 13px;
            text-transform: uppercase;
        }}
        
        #legend .legend-item {{
            display: flex;
            align-items: center;
            margin: 8px 0;
            gap: 10px;
        }}
        
        #legend .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }}
        
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            z-index: 1000;
        }}
        
        .spinner {{
            width: 50px;
            height: 50px;
            border: 4px solid rgba(124, 58, 237, 0.3);
            border-top-color: #7c3aed;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        #node-info {{
            position: absolute;
            bottom: 80px;
            left: 20px;
            background: rgba(5, 5, 5, 0.95);
            border: 1px solid #7c3aed;
            border-radius: 8px;
            padding: 15px;
            max-width: 350px;
            z-index: 100;
            backdrop-filter: blur(10px);
            display: none;
        }}
        
        #node-info.visible {{
            display: block;
        }}
        
        #node-info h3 {{
            color: #7c3aed;
            margin-bottom: 10px;
            font-size: 14px;
        }}
        
        #node-info p {{
            font-size: 12px;
            color: #a1a1a1;
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div id="canvas-container">
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div>Loading visualization...</div>
        </div>
    </div>
    
    <div id="info-panel">
        <h1>🚀 Rohkun</h1>
        <div class="stat"><strong>Project:</strong> {project_name}</div>
        <div class="stat"><strong>Nodes:</strong> <span id="node-count">{graph_data['summary']['total_nodes']}</span></div>
        <div class="stat"><strong>Connections:</strong> <span id="link-count">{graph_data['summary']['total_links']}</span></div>
        <div class="stat"><strong>Endpoints:</strong> {graph_data['summary']['endpoints']}</div>
        <div class="stat"><strong>API Calls:</strong> {graph_data['summary']['api_calls']}</div>
    </div>
    
    <div id="legend">
        <h3>Legend</h3>
        <div class="legend-item">
            <div class="legend-color" style="background: #7c3aed;"></div>
            <span>Endpoints</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #00ff41;"></div>
            <span>API Calls</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ff3333;"></div>
            <span>High Impact</span>
        </div>
    </div>
    
    <div id="controls">
        <button onclick="resetCamera()">Reset View</button>
        <button onclick="toggleAnimation()">Toggle Animation</button>
        <button onclick="exportScreenshot()">📸 Screenshot</button>
    </div>
    
    <div id="node-info"></div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        // Graph data
        const graphData = {graph_data_json};
        
        // Scene setup
        let scene, camera, renderer, controls;
        let nodes = [];
        let links = [];
        let animationEnabled = true;
        let selectedNode = null;
        
        // Initialize
        function init() {{
            // Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x030303);
            
            // Camera
            camera = new THREE.PerspectiveCamera(
                75,
                window.innerWidth / window.innerHeight,
                0.1,
                10000
            );
            camera.position.z = 100;
            camera.position.y = 50;
            camera.position.x = 50;
            
            // Renderer
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            document.getElementById('canvas-container').appendChild(renderer.domElement);
            
            // Lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            
            const pointLight1 = new THREE.PointLight(0x7c3aed, 1, 1000);
            pointLight1.position.set(50, 50, 50);
            scene.add(pointLight1);
            
            const pointLight2 = new THREE.PointLight(0x00ff41, 0.8, 1000);
            pointLight2.position.set(-50, -50, 50);
            scene.add(pointLight2);
            
            // Build graph
            buildGraph();
            
            // Mouse controls (simple orbit)
            let mouseDown = false;
            let mouseX = 0;
            let mouseY = 0;
            
            renderer.domElement.addEventListener('mousedown', (e) => {{
                mouseDown = true;
                mouseX = e.clientX;
                mouseY = e.clientY;
            }});
            
            renderer.domElement.addEventListener('mouseup', () => {{
                mouseDown = false;
            }});
            
            renderer.domElement.addEventListener('mousemove', (e) => {{
                if (mouseDown) {{
                    const deltaX = e.clientX - mouseX;
                    const deltaY = e.clientY - mouseY;
                    
                    // Rotate camera around origin
                    const spherical = new THREE.Spherical();
                    spherical.setFromVector3(camera.position);
                    spherical.theta -= deltaX * 0.01;
                    spherical.phi += deltaY * 0.01;
                    spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi));
                    
                    camera.position.setFromSpherical(spherical);
                    camera.lookAt(0, 0, 0);
                    
                    mouseX = e.clientX;
                    mouseY = e.clientY;
                }}
            }});
            
            // Zoom with wheel
            renderer.domElement.addEventListener('wheel', (e) => {{
                const distance = camera.position.length();
                const newDistance = distance + e.deltaY * 0.1;
                if (newDistance > 10 && newDistance < 500) {{
                    camera.position.normalize().multiplyScalar(newDistance);
                }}
            }});
            
            // Hide loading
            document.getElementById('loading').style.display = 'none';
            
            // Start animation
            animate();
        }}
        
        function buildGraph() {{
            // Calculate layout (force-directed simulation)
            const nodeMap = {{}};
            graphData.nodes.forEach((node, i) => {{
                // Initial random position
                const angle = (i / graphData.nodes.length) * Math.PI * 2;
                const radius = 30 + Math.random() * 20;
                nodeMap[node.id] = {{
                    ...node,
                    x: Math.cos(angle) * radius,
                    y: Math.sin(angle) * radius * 0.5,
                    z: (Math.random() - 0.5) * 30,
                    vx: 0,
                    vy: 0,
                    vz: 0
                }};
            }});
            
            // Simple force-directed layout
            for (let iter = 0; iter < 100; iter++) {{
                graphData.links.forEach(link => {{
                    const source = nodeMap[link.source];
                    const target = nodeMap[link.target];
                    
                    if (!source || !target) return;
                    
                    const dx = target.x - source.x;
                    const dy = target.y - source.y;
                    const dz = target.z - source.z;
                    const distance = Math.sqrt(dx*dx + dy*dy + dz*dz) || 1;
                    
                    const force = (distance - 15) * 0.01;
                    
                    source.vx += (dx / distance) * force;
                    source.vy += (dy / distance) * force;
                    source.vz += (dz / distance) * force;
                    target.vx -= (dx / distance) * force;
                    target.vy -= (dy / distance) * force;
                    target.vz -= (dz / distance) * force;
                }});
                
                // Apply velocity with damping
                Object.values(nodeMap).forEach(node => {{
                    node.x += node.vx;
                    node.y += node.vy;
                    node.z += node.vz;
                    node.vx *= 0.9;
                    node.vy *= 0.9;
                    node.vz *= 0.9;
                }});
            }}
            
            // Create node meshes
            graphData.nodes.forEach(nodeData => {{
                const node = nodeMap[nodeData.id];
                if (!node) return;
                
                // Color based on type
                let color = 0x7c3aed; // Purple for endpoints
                if (nodeData.type === 'api_call') {{
                    color = 0x00ff41; // Green for API calls
                }}
                if (nodeData.high_impact) {{
                    color = 0xff3333; // Red for high impact
                }}
                
                // Create sphere
                const geometry = new THREE.SphereGeometry(nodeData.size * 2, 16, 16);
                const material = new THREE.MeshPhongMaterial({{
                    color: color,
                    emissive: color,
                    emissiveIntensity: 0.3,
                    transparent: true,
                    opacity: 0.9
                }});
                
                const mesh = new THREE.Mesh(geometry, material);
                mesh.position.set(node.x, node.y, node.z);
                mesh.userData = nodeData;
                
                // Add glow effect
                const glowGeometry = new THREE.SphereGeometry(nodeData.size * 2.5, 16, 16);
                const glowMaterial = new THREE.MeshBasicMaterial({{
                    color: color,
                    transparent: true,
                    opacity: 0.2
                }});
                const glow = new THREE.Mesh(glowGeometry, glowMaterial);
                mesh.add(glow);
                
                scene.add(mesh);
                nodes.push(mesh);
            }});
            
            // Create links
            graphData.links.forEach(linkData => {{
                const sourceNode = nodeMap[linkData.source];
                const targetNode = nodeMap[linkData.target];
                
                if (!sourceNode || !targetNode) return;
                
                const geometry = new THREE.BufferGeometry().setFromPoints([
                    new THREE.Vector3(sourceNode.x, sourceNode.y, sourceNode.z),
                    new THREE.Vector3(targetNode.x, targetNode.y, targetNode.z)
                ]);
                
                const opacity = linkData.confidence_score / 100;
                const material = new THREE.LineBasicMaterial({{
                    color: 0x7c3aed,
                    transparent: true,
                    opacity: opacity * 0.5
                }});
                
                const line = new THREE.Line(geometry, material);
                scene.add(line);
                links.push(line);
            }});
        }}
        
        function animate() {{
            requestAnimationFrame(animate);
            
            if (animationEnabled) {{
                // Rotate nodes slightly
                nodes.forEach((node, i) => {{
                    node.rotation.x += 0.001;
                    node.rotation.y += 0.002;
                }});
            }}
            
            renderer.render(scene, camera);
        }}
        
        function resetCamera() {{
            camera.position.set(50, 50, 100);
            camera.lookAt(0, 0, 0);
        }}
        
        function toggleAnimation() {{
            animationEnabled = !animationEnabled;
        }}
        
        function exportScreenshot() {{
            const link = document.createElement('a');
            link.download = 'rohkun-visualization.png';
            link.href = renderer.domElement.toDataURL();
            link.click();
        }}
        
        // Handle window resize
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
        
        // Initialize on load
        window.addEventListener('load', init);
    </script>
</body>
</html>"""


















