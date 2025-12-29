// Knowledge Graph JavaScript - Designer Handoff

let network = null;
let nodes = null;
let edges = null;
let physicsEnabled = true;
let labelsEnabled = true;
let graphData = null;

// Initialize with data
function init(data) {
    graphData = data;
    const container = document.getElementById('network-container');
    
    // Update info panel
    document.getElementById('project-name').textContent = data.summary?.project_name || 'Unknown Project';
    document.getElementById('node-count').textContent = data.summary?.total_nodes || data.nodes?.length || 0;
    document.getElementById('edge-count').textContent = data.summary?.total_edges || data.edges?.length || 0;
    document.getElementById('high-impact-count').textContent = data.summary?.high_impact || 0;
    
    // Create nodes and edges datasets
    nodes = new vis.DataSet(data.nodes || []);
    edges = new vis.DataSet(data.edges || []);
    
    // Network options
    const options = {
        nodes: {
            shape: 'dot',
            font: {
                color: '#ffffff',
                size: 14,
                face: 'JetBrains Mono'
            },
            borderWidth: 2,
            shadow: {
                enabled: true,
                color: 'rgba(124, 58, 237, 0.5)',
                size: 10,
                x: 0,
                y: 0
            },
            scaling: {
                min: 10,
                max: 60
            }
        },
        edges: {
            arrows: {
                to: {
                    enabled: true,
                    scaleFactor: 0.8
                }
            },
            font: {
                color: '#a1a1a1',
                size: 11,
                face: 'JetBrains Mono'
            },
            shadow: {
                enabled: true,
                color: 'rgba(124, 58, 237, 0.3)',
                size: 5
            }
        },
        physics: {
            enabled: physicsEnabled,
            stabilization: {
                enabled: true,
                iterations: 200
            },
            barnesHut: {
                gravitationalConstant: -2000,
                centralGravity: 0.1,
                springLength: 150,
                springConstant: 0.04,
                damping: 0.09
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 100,
            zoomView: true,
            dragView: true
        },
        layout: {
            improvedLayout: true
        }
    };
    
    // Create network
    const networkData = { nodes: nodes, edges: edges };
    network = new vis.Network(container, networkData, options);
    
    // Event handlers
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = nodes.get(nodeId);
            showNodeInfo(node);
        } else {
            hideNodeInfo();
        }
    });
    
    network.on('hoverNode', function(params) {
        container.style.cursor = 'pointer';
    });
    
    network.on('blurNode', function(params) {
        container.style.cursor = 'default';
    });
    
    // Search functionality
    const searchInput = document.getElementById('search-input');
    let searchTimeout = null;
    
    searchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
            const query = e.target.value.toLowerCase();
            if (query === '') {
                nodes.update(graphData.nodes || []);
            } else {
                const filtered = (graphData.nodes || []).filter(node => {
                    return (node.label || '').toLowerCase().includes(query) ||
                           (node.path || '').toLowerCase().includes(query) ||
                           (node.method || '').toLowerCase().includes(query);
                });
                nodes.update(filtered);
            }
        }, 300);
    });
}

function showNodeInfo(node) {
    const infoDiv = document.getElementById('node-info');
    const method = node.method || 'UNKNOWN';
    const path = node.path || 'unknown';
    const file = node.file || 'unknown';
    const line = node.line || '?';
    const connections = node.connections || 0;
    
    infoDiv.innerHTML = `
        <h3>${node.label || `${method} ${path}`}</h3>
        <p><strong>Method:</strong> ${method}</p>
        <p><strong>Path:</strong> ${path}</p>
        <p><strong>File:</strong> ${file}</p>
        <p><strong>Line:</strong> ${line}</p>
        <p><strong>Connections:</strong> ${connections}</p>
    `;
    infoDiv.classList.add('visible');
}

function hideNodeInfo() {
    document.getElementById('node-info').classList.remove('visible');
}

function resetView() {
    if (network) {
        network.fit({
            animation: {
                duration: 1000,
                easingFunction: 'easeInOutQuad'
            }
        });
    }
}

function togglePhysics() {
    if (network) {
        physicsEnabled = !physicsEnabled;
        network.setOptions({ physics: { enabled: physicsEnabled } });
        document.getElementById('physics-btn').textContent = `Physics: ${physicsEnabled ? 'ON' : 'OFF'}`;
    }
}

function toggleLabels() {
    if (nodes && graphData) {
        labelsEnabled = !labelsEnabled;
        const update = (graphData.nodes || []).map(node => ({
            ...node,
            font: { ...(node.font || {}), size: labelsEnabled ? 14 : 0 }
        }));
        nodes.update(update);
        document.getElementById('labels-btn').textContent = `Labels: ${labelsEnabled ? 'ON' : 'OFF'}`;
        document.getElementById('labels-btn').classList.toggle('active', labelsEnabled);
    }
}

function exportScreenshot() {
    showToast('Generating screenshot...');
    
    html2canvas(document.getElementById('network-container'), {
        backgroundColor: '#030303',
        scale: 2,
        useCORS: true
    }).then(canvas => {
        const link = document.createElement('a');
        link.download = `rohkun-knowledge-graph-${Date.now()}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
        showToast('Screenshot saved!');
    });
}

function copyLink() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        showToast('Link copied to clipboard!');
    });
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('visible');
    setTimeout(() => {
        toast.classList.remove('visible');
    }, 3000);
}

// Handle window resize
window.addEventListener('resize', function() {
    if (network) {
        network.redraw();
    }
});














