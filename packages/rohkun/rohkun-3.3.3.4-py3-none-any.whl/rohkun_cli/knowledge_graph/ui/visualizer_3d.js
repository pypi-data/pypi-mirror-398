// --- GRAPH DATA TRANSLATOR ---
// Unified translator: converts any graph type (API, dependencies, function_dependencies)
// into a normalized format of just nodes (balls) and edges (lines)
// The renderer only ever sees this normalized format
window.GraphDataTranslator = {
    // Cache for embedded data and translated results
    _cache: {
        allData: null,
        parsed: false,
        translated: {}  // Cache translated results per graph type
    },
    
    // Parse embedded data once
    _parseEmbeddedData: function() {
        if (this._cache.parsed) {
            return this._cache.allData;
        }
        
        const embeddedScript = document.getElementById('embedded-graph-data');
        if (embeddedScript && embeddedScript.textContent) {
            try {
                this._cache.allData = JSON.parse(embeddedScript.textContent);
                this._cache.parsed = true;
                console.log('[TRANSLATOR] Parsed embedded graph data');
            } catch (e) {
                console.error('[TRANSLATOR] Failed to parse embedded data:', e);
                return null;
            }
        }
        return this._cache.allData;
    },
    
    // Translate any graph type to normalized format: { nodes: [], edges: [] }
    // Results are cached per graph type to avoid repeated translation
    translate: function(graphType, forceRefresh = false) {
        // Return cached result if available and not forcing refresh
        if (!forceRefresh && this._cache.translated[graphType]) {
            return this._cache.translated[graphType];
        }
        
        const allData = this._parseEmbeddedData();
        if (!allData) {
            console.error('[TRANSLATOR] No embedded data available');
            return { nodes: [], edges: [] };
        }
        
        // Map graph type to data key
        let dataKey = graphType;
        // NOTE: The UI Labels map as follows:
        // "FILES" button -> switchGraph('files') -> Maps to 'dependencies' (File Imports) -> Uses Code Metropolis (City)
        // "FUNCTIONS" button -> switchGraph('functions') -> Maps to 'function_dependencies' (Function Calls) -> Uses Spheres/Blobs
        // "APIs" button -> switchGraph('api') -> Maps to 'api' (Endpoints) -> Uses Spheres/Blobs
        
        if (graphType === 'files' || graphType === 'dependency') {
            // Support both old 'dependency' and new 'files' for backward compatibility
            dataKey = 'dependencies';
        } else if (graphType === 'functions' || graphType === 'function_dependency') {
            // Support both old 'function_dependency' and new 'functions' for backward compatibility
            dataKey = 'function_dependencies';
        }
        
        // Get the graph data for this type
        const graphData = allData[dataKey] || allData.api || { nodes: [], edges: [] };
        
        // Normalize: ensure nodes and edges are arrays
        const normalized = {
            nodes: Array.isArray(graphData.nodes) ? graphData.nodes : [],
            edges: Array.isArray(graphData.edges) ? graphData.edges : [],
            summary: graphData.summary || {},
            report: allData.report || {}
        };
        
        // Cache the result
        this._cache.translated[graphType] = normalized;
        
        // Only log on first translation or when forcing refresh
        if (forceRefresh || !this._cache.translated[graphType + '_logged']) {
            console.log(`[TRANSLATOR] ${graphType} -> ${dataKey}: ${normalized.nodes.length} balls, ${normalized.edges.length} lines`);
            this._cache.translated[graphType + '_logged'] = true;
        }
        
        return normalized;
    },
    
    // Clear cache for a specific graph type (useful when switching)
    clearCache: function(graphType) {
        if (graphType) {
            delete this._cache.translated[graphType];
            delete this._cache.translated[graphType + '_logged'];
        } else {
            // Clear all caches
            this._cache.translated = {};
        }
    }
};

// --- 3D ENGINE VARIABLES ---
let scene3d, camera3d, renderer3d;
let nodes3d = [];
let edgeLines3d;
let transitionTo2DStarted = false;
let final2DPositions = new Map(); // Stores the destination X,Y
let finalCameraDistance3D = 200;  // Calculated based on bounds
let orthoCam, perspectiveCam;     // Store camera references

// Toggle Camera Mode (Global)
window.toggleCameraMode = function() {
    if (window.currentGraphType !== 'dependency') return; // Only for City View
    
    const btn = document.getElementById('btn-cam');
    
    if (camera3d.isOrthographicCamera) {
        // Switch to Perspective
        const pos = camera3d.position.clone();
        camera3d = perspectiveCam;
        camera3d.position.copy(pos);
        camera3d.lookAt(0,0,0);
        console.log('[CAMERA] Switched to Perspective');
        if(btn) btn.textContent = '🎥 CAM: PERSP';
    } else {
        // Switch to Orthographic
        const pos = camera3d.position.clone();
        camera3d = orthoCam;
        camera3d.position.copy(pos);
        camera3d.lookAt(0,0,0);
        camera3d.zoom = 1.0; 
        camera3d.updateProjectionMatrix();
        console.log('[CAMERA] Switched to Orthographic (Blueprint)');
        if(btn) btn.textContent = '📐 CAM: ORTHO';
    }
};

// Keyboard Shortcut 'B'
window.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() === 'b') {
        window.toggleCameraMode();
    }
});
function updateGridMouse(cam) {
    if (window.gridMesh && cam && renderer3d && renderer3d.domElement) {
        // Default to center if mouse not moved yet
        if (window.mouseX === 0 && window.mouseY === 0) return;
        
        const rect = renderer3d.domElement.getBoundingClientRect();
        const mx = ((window.mouseX - rect.left) / rect.width) * 2 - 1;
        const my = -((window.mouseY - rect.top) / rect.height) * 2 + 1;
        
        const ray = new THREE.Raycaster();
        ray.setFromCamera(new THREE.Vector2(mx, my), cam);
        
        const planeZ = new THREE.Plane(new THREE.Vector3(0, 0, 1), 20); // Z = -20
        const target = new THREE.Vector3();
        ray.ray.intersectPlane(planeZ, target);
        
        if (target) {
            window.gridMesh.material.uniforms.uMouse.value.copy(target);
        }
    }
}

// --- CITY LAYOUT ENGINE ---
// Ground-up rebuild for "Code Metropolis"
const CityLayout = {
    config: {
        unitSize: 20,       // Base building footprint
        padding: 15,        // Increased padding between buildings (was 10) for better label spacing
        street: 50,         // Increased street width between districts (was 40) for better separation
        districtPadding: 25 // Increased padding inside district walls (was 20) for better spacing
    },

    // Main: Returns Map<id, {x,y,...}>
    layout: function(nodes, edges) {
        console.log('[CITY] 🏗️ Building Code Metropolis...');
        
        // Separate connected and unconnected files
        const connectedNodeIds = new Set();
        if (edges && edges.length > 0) {
            edges.forEach(e => {
                connectedNodeIds.add(e.from);
                connectedNodeIds.add(e.to);
            });
        }
        
        // Mark files as connected/unconnected but keep them together in tree structure
        nodes.forEach(node => {
            node.isConnected = connectedNodeIds.has(node.id);
        });
        
        const connectedCount = nodes.filter(n => n.isConnected).length;
        const unconnectedCount = nodes.filter(n => !n.isConnected).length;
        console.log(`[CITY] Connected files: ${connectedCount}, Unconnected files: ${unconnectedCount}`);
        
        // Build single tree structure preserving directory hierarchy
        const tree = this.buildTree(nodes);
        console.log('[CITY] Tree constructed. Root children:', tree.children.length);
        
        // Calculate sizes (bottom-up)
        this.calculateSizes(tree);
        console.log(`[CITY] Root Size: ${tree.w.toFixed(0)}x${tree.h.toFixed(0)}`);
        
        // Calculate positions (top-down) - organize by tree structure
        // Center the city at 0,0
        this.calculatePositions(tree, -tree.w/2, -tree.h/2);
        
        // Flatten to node map
        const nodeMap = new Map();
        this.flatten(tree, nodeMap);
        
        // Collect districts for visualization
        window.cityDistricts = [];
        this.collectDistricts(tree, window.cityDistricts);
        
        // Now apply separation: shift connected and unconnected files within their tree positions
        // This maintains tree structure but visually separates the two groups
        // Much larger separation - "punch 1" to the left, "punch 2" to the right
        const separationGap = 400; // Increased from 150 - much more space between groups
        
        // Find the center X of all nodes
        let minX = Infinity, maxX = -Infinity;
        nodeMap.forEach(n => {
            minX = Math.min(minX, n.x);
            maxX = Math.max(maxX, n.x);
        });
        const centerX = (minX + maxX) / 2;
        
        // Shift nodes: connected to left, unconnected to right
        // But maintain their relative positions within the tree
        nodeMap.forEach((n, nodeId) => {
            const node = nodes.find(nd => nd.id === nodeId);
            if (node && node.isConnected) {
                // Shift connected files significantly to the left (punch 1)
                n.x = n.x - separationGap / 2;
            } else {
                // Shift unconnected files significantly to the right (punch 2)
                n.x = n.x + separationGap / 2;
            }
        });
        
        return nodeMap;
    },

    buildTree: function(nodes) {
        const root = { path: 'root', children: [], files: [], type: 'root' };
        const map = { '': root };
        
        nodes.forEach(node => {
            const path = node.file_path || node.id;
            // Remove filename
            const parts = path.split('/');
            parts.pop(); 
            const dirPath = parts.join('/');
            
            // Ensure dir exists
            if (!map[dirPath]) {
                // Walk up and create
                const subParts = dirPath.split('/');
                let curr = '';
                let parent = root;
                subParts.forEach((p, i) => {
                    curr = i === 0 ? p : `${curr}/${p}`;
                    if (!map[curr]) {
                        const newDir = { path: curr, name: p, children: [], files: [], type: 'dir' };
                        map[curr] = newDir;
                        parent.children.push(newDir);
                    }
                    parent = map[curr];
                });
            }
            map[dirPath].files.push(node);
        });
        return root;
    },

    calculateSizes: function(node) {
        // 1. Size of Files Block (Grid)
        if (node.files.length > 0) {
            const count = node.files.length;
            const cols = Math.ceil(Math.sqrt(count));
            const rows = Math.ceil(count / cols);
            const u = this.config.unitSize + this.config.padding;
            
            node.filesBlock = {
                w: cols * u + this.config.districtPadding * 2,
                h: rows * u + this.config.districtPadding * 2,
                cols: cols
            };
        } else {
            node.filesBlock = { w: 0, h: 0 };
        }

        // 2. Recurse Children
        node.children.forEach(c => this.calculateSizes(c));
        
        // 3. Pack Children + FilesBlock using Shelf/Bin Packing
        // Items to pack:
        const items = [];
        if (node.filesBlock.w > 0) items.push({ ...node.filesBlock, type: 'files' });
        node.children.forEach(c => items.push({ ...c, type: 'dir' })); // c already has w/h
        
        // Sort by height (desc)
        items.sort((a, b) => b.h - a.h);
        
        let currentX = 0;
        let currentY = 0;
        let rowHeight = 0;
        let maxW = 0;
        
        // Target aspect ratio 1:1 roughly
        // Heuristic: Max width = sqrt(total_area)
        const totalArea = items.reduce((sum, i) => sum + i.w * i.h, 0);
        const targetW = Math.max(node.filesBlock.w, Math.sqrt(totalArea) * 1.2); 
        
        items.forEach(item => {
            if (currentX + item.w > targetW && currentX > 0) {
                // New Row
                currentX = 0;
                currentY += rowHeight + this.config.street;
                rowHeight = 0;
            }
            
            item.relX = currentX;
            item.relY = currentY;
            
            currentX += item.w + this.config.street;
            rowHeight = Math.max(rowHeight, item.h);
            maxW = Math.max(maxW, currentX);
        });
        
        node.w = Math.max(this.config.street, maxW); // Ensure non-zero
        node.h = currentY + rowHeight;
        // Store items back to node for positioning
        node.packedItems = items;
    },

    calculatePositions: function(node, absX, absY) {
        node.x = absX;
        node.y = absY;
        
        if (node.packedItems) {
            node.packedItems.forEach(item => {
                const myX = absX + item.relX;
                const myY = absY + item.relY;
                
                if (item.type === 'files') {
                    // Position individual files
                    // Grid layout
                    const u = this.config.unitSize + this.config.padding;
                    const startX = myX + this.config.districtPadding;
                    const startY = myY + this.config.districtPadding;
                    
                    node.files.forEach((f, i) => {
                        const col = i % item.cols;
                        const row = Math.floor(i / item.cols);
                        f.x = startX + col * u;
                        f.y = startY + row * u;
                    });
                } else if (item.type === 'dir') {
                    // Recurse - find the original child node object
                    // item is a copy or reference? It's a reference because we pushed 'c'
                    this.calculatePositions(item, myX, myY);
                }
            });
        }
    },

    flatten: function(node, map) {
        node.files.forEach(f => {
            map.set(f.id, {
                id: f.id,
                x: f.x,
                y: f.y,
                vx: 0, vy: 0,
                w: this.config.unitSize,
                h: this.config.unitSize
            });
        });
        node.children.forEach(c => this.flatten(c, map));
    },
    
    collectDistricts: function(node, list) {
        // Add this directory as a district
        if (node.path !== 'root') {
            list.push({
                path: node.path,
                name: node.name,
                x: node.x,
                y: node.y,
                w: node.w,
                h: node.h,
                depth: node.path.split('/').length,
                fileCount: node.files.length
            });
        }
        node.children.forEach(c => this.collectDistricts(c, list));
    }
};

// --- 1. PRE-CALCULATION (THE REFERENCE LOGIC) ---
// We calculate the 2D layout *before* showing the 3D scene
// This ensures a proper non-symmetric layout that the animation will transition to
function calculateReferenceLayout() {
    console.log('[LAYOUT] Calculating 2D positions via translator...');
    const nodeMap = new Map();
    
    // Use translator to get normalized data (translator -> renderer path)
    const graphData = window.GraphDataTranslator.translate(window.currentGraphType || 'api');
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];
    console.log(`[LAYOUT] Graph data: ${nodes.length} balls, ${edges.length} lines`);
    
    // === CITY LAYOUT (FILES) ===
    if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
         console.log('[LAYOUT] Running City Grid Layout...');
         return CityLayout.layout(nodes, edges);
    }

    // === FORCE-DIRECTED LAYOUT (APIs & FUNCTIONS) ===
    // Both APIs and Functions use the same blob/sphere force-directed layout
    // Separate connected nodes (center) from unconnected nodes (edges)
    
    // 1. Identify which nodes are connected (have edges)
    const connectedNodeIds = new Set();
    edges.forEach(e => {
        connectedNodeIds.add(e.from);
        connectedNodeIds.add(e.to);
    });
    
    const connectedNodes = [];
    const unconnectedNodes = [];
    nodes.forEach(n => {
        if (connectedNodeIds.has(n.id)) {
            connectedNodes.push(n);
        } else {
            unconnectedNodes.push(n);
        }
    });
    
    console.log(`[LAYOUT] Connected nodes: ${connectedNodes.length}, Unconnected nodes: ${unconnectedNodes.length}`);
    
    // 2. Initialize positions: connected in center, unconnected on edges
    // Increased spacing to prevent label overlap and better separation
    const centerSpread = 100;  // Increased from 60 - more space for connected nodes
    const edgeSpread = 250;    // Increased from 150 - much further separation for unconnected nodes
    const separationGap = 80;  // Minimum gap between connected and unconnected groups
    
    // Place connected nodes in center with better spacing
    connectedNodes.forEach((n, i) => {
        const seed = (i * 137.508) % 1; // Golden angle for better distribution
        const angle = seed * Math.PI * 2;
        // Use more of the center spread for better spacing
        const radius = (Math.random() * 0.4 + 0.1) * centerSpread; // 10-50% of center spread
        nodeMap.set(n.id, {
            id: n.id,
            x: Math.cos(angle) * radius + (Math.random() - 0.5) * 15, // Slightly more jitter
            y: Math.sin(angle) * radius + (Math.random() - 0.5) * 15,
            vx: 0, vy: 0,
            isConnected: true
        });
    });
    
    // Place unconnected nodes on edges/corners - much further away
    unconnectedNodes.forEach((n, i) => {
        // Distribute around the perimeter (corners and edges)
        const cornerCount = 4; // 4 corners
        const edgeCount = unconnectedNodes.length;
        const position = i % (cornerCount + 4); // 4 corners + 4 edge midpoints
        
        let x, y;
        // Ensure minimum distance from center (centerSpread + separationGap)
        const minRadius = centerSpread + separationGap;
        
        if (position < cornerCount) {
            // Place on corners - further out
            const corner = position;
            const cornerAngles = [Math.PI * 0.25, Math.PI * 0.75, Math.PI * 1.25, Math.PI * 1.75];
            const angle = cornerAngles[corner];
            const radius = Math.max(minRadius, edgeSpread * (0.8 + Math.random() * 0.2)); // 80-100% of edge spread
            x = Math.cos(angle) * radius;
            y = Math.sin(angle) * radius;
        } else {
            // Place on edge midpoints - further out
            const edge = position - cornerCount;
            const edgeAngles = [0, Math.PI * 0.5, Math.PI, Math.PI * 1.5];
            const angle = edgeAngles[edge % 4];
            const radius = Math.max(minRadius, edgeSpread * (0.7 + Math.random() * 0.3)); // 70-100% of edge spread
            x = Math.cos(angle) * radius;
            y = Math.sin(angle) * radius;
        }
        
        nodeMap.set(n.id, {
            id: n.id,
            x: x + (Math.random() - 0.5) * 20, // More jitter for better spacing
            y: y + (Math.random() - 0.5) * 20,
            vx: 0, vy: 0,
            isConnected: false
        });
    });
    
    const spread = Math.max(centerSpread, edgeSpread);
    
    // Physics Simulation with improved parameters
    // k is the ideal distance between nodes - increased for better label spacing
    const k = Math.sqrt((spread * spread * 2) / nodes.length) * 1.5; // Increased by 50% for better spacing
    const iterations = 300; // Increased iterations for better convergence
    
    // Cooling factor for simulated annealing effect
    let temperature = 1.0;
    const coolingRate = 0.95;
    
    for(let i=0; i<iterations; i++) {
        // Update temperature (simulated annealing)
        temperature *= coolingRate;
        
        // Central Gravity (different for connected vs unconnected)
        nodeMap.forEach(n => {
            if (n.isConnected) {
                // Strong gravity for connected nodes - keep them in center
                n.vx -= n.x * 0.02 * temperature;
                n.vy -= n.y * 0.02 * temperature;
            } else {
                // Weak/negative gravity for unconnected nodes - push to edges
                const dist = Math.sqrt(n.x * n.x + n.y * n.y);
                const targetDist = edgeSpread * 0.9; // Target distance from center
                if (dist < targetDist) {
                    // Push outward if too close to center
                    const pushForce = (targetDist - dist) / targetDist * 0.01 * temperature;
                    n.vx += (n.x / dist || 0) * pushForce;
                    n.vy += (n.y / dist || 0) * pushForce;
                } else {
                    // Light gravity to prevent infinite scattering
                    n.vx -= n.x * 0.003 * temperature;
                    n.vy -= n.y * 0.003 * temperature;
                }
            }
        });
        
        // Repulsion (Coulomb force - nodes repel each other)
        nodeMap.forEach(n1 => {
            let fx = 0, fy = 0;
            nodeMap.forEach(n2 => {
                if(n1.id === n2.id) return;
                const dx = n1.x - n2.x;
                const dy = n1.y - n2.y;
                const dist = Math.sqrt(dx*dx + dy*dy) || 0.1;
                // Repulsion force: k^2 / dist^2 (stronger repulsion)
                const force = (k * k) / (dist * dist);
                fx += (dx / dist) * force;
                fy += (dy / dist) * force;
            });
            n1.vx += fx * temperature;
            n1.vy += fy * temperature;
        });
        
        // Attraction (Spring force - edges pull nodes together)
        edges.forEach(e => {
            const n1 = nodeMap.get(e.from);
            const n2 = nodeMap.get(e.to);
            if(!n1 || !n2) return;
            const dx = n1.x - n2.x;
            const dy = n1.y - n2.y;
            const dist = Math.sqrt(dx*dx + dy*dy) || 0.1;
            // Attraction force: (dist - k) / k (spring-like)
            const force = (dist - k) / k;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            n1.vx -= fx * temperature;
            n1.vy -= fy * temperature;
            n2.vx += fx * temperature;
            n2.vy += fy * temperature;
        });
        
        // Update positions with adaptive damping
        const damping = 0.7 + (1 - temperature) * 0.2; // Increase damping as we cool
        nodeMap.forEach(n => {
            // Cap velocity to prevent explosions
            const maxVel = 10;
            const velMag = Math.sqrt(n.vx * n.vx + n.vy * n.vy);
            if (velMag > maxVel) {
                n.vx = (n.vx / velMag) * maxVel;
                n.vy = (n.vy / velMag) * maxVel;
            }
            
            n.x += n.vx * 0.1;
            n.y += n.vy * 0.1;
            n.vx *= damping;
            n.vy *= damping;
        });
    }
    
    // CRITICAL: Scale down if graph is too large (keep it visible)
    // Reference graphs are typically within ±200 units
    let maxDist = 0;
    nodeMap.forEach(n => {
        const dist = Math.sqrt(n.x * n.x + n.y * n.y);
        maxDist = Math.max(maxDist, dist);
    });
    
    if (maxDist > 200) {
        const scaleFactor = 200 / maxDist;
        console.log(`[LAYOUT] Scaling down by ${scaleFactor.toFixed(2)} (maxDist was ${maxDist.toFixed(1)})`);
        nodeMap.forEach(n => {
            n.x *= scaleFactor;
            n.y *= scaleFactor;
        });
    }
    
    // Calculate bounds for camera
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    nodeMap.forEach(n => {
        minX = Math.min(minX, n.x);
        maxX = Math.max(maxX, n.x);
        minY = Math.min(minY, n.y);
        maxY = Math.max(maxY, n.y);
    });
    
    const width = maxX - minX;
    const height = maxY - minY;
    const maxDim = Math.max(width, height, 100);
    
    // Calculate camera distance to fit graph
    const fovRad = (50 * Math.PI) / 180;
    finalCameraDistance3D = (maxDim * 1.2) / (2 * Math.tan(fovRad / 2));
    
    console.log(`[LAYOUT] Bounds: X[${minX.toFixed(1)}, ${maxX.toFixed(1)}] Y[${minY.toFixed(1)}, ${maxY.toFixed(1)}]`);
    console.log(`[LAYOUT] Max dimension: ${maxDim.toFixed(1)}, Camera distance: ${finalCameraDistance3D.toFixed(1)}`);
    console.log(`[LAYOUT] 2D positions calculated for ${nodeMap.size} balls`);
    
    return nodeMap;
}

// === TREE/HIERARCHICAL LAYOUT FOR FUNCTIONS ===
// If A depends on B, then B is the root (top) and A is the dependent (below)
// This creates a normal tree: root at top, dependents below
function calculateTreeLayout(nodes, edges) {
    console.log('[TREE] Calculating hierarchical tree layout...');
    const nodeMap = new Map();
    const nodeLookup = new Map(nodes.map(n => [n.id, n]));
    
    // Build adjacency lists: who depends on whom
    // If edge is from: A, to: B, then A depends on B (B is dependency, A is dependent)
    const dependents = new Map(); // dependency -> [dependents]
    const dependencies = new Map(); // dependent -> [dependencies]
    const inDegree = new Map(); // node -> how many dependencies it has
    
    nodes.forEach(n => {
        dependents.set(n.id, []);
        dependencies.set(n.id, []);
        inDegree.set(n.id, 0);
    });
    
    edges.forEach(edge => {
        const dependent = edge.from; // A depends on B
        const dependency = edge.to;   // B is the dependency
        
        if (!dependents.has(dependency)) dependents.set(dependency, []);
        if (!dependencies.has(dependent)) dependencies.set(dependent, []);
        
        dependents.get(dependency).push(dependent);
        dependencies.get(dependent).push(dependency);
        inDegree.set(dependent, (inDegree.get(dependent) || 0) + 1);
    });
    
    // Find root nodes (nodes with no dependencies - inDegree = 0)
    const roots = [];
    inDegree.forEach((degree, nodeId) => {
        if (degree === 0) {
            roots.push(nodeId);
        }
    });
    
    // If no clear roots, pick nodes with most dependents (most important)
    if (roots.length === 0) {
        console.log('[TREE] No clear root nodes, selecting nodes with most dependents...');
        const dependentsCount = Array.from(dependents.entries())
            .map(([id, deps]) => [id, deps.length])
            .sort((a, b) => b[1] - a[1]);
        
        // Take top 3 as roots
        roots.push(...dependentsCount.slice(0, Math.min(3, dependentsCount.length)).map(([id]) => id));
    }
    
    console.log(`[TREE] Found ${roots.length} root(s):`, roots);
    
    // Tree layout parameters
    const levelHeight = 120; // Vertical spacing between levels
    const nodeSpacing = 80;  // Horizontal spacing between siblings
    const rootY = -200;      // Start roots at top (negative Y = up)
    
    // Assign levels using BFS from roots
    const level = new Map();
    const visited = new Set();
    const queue = [];
    
    // Initialize roots at level 0
    roots.forEach(rootId => {
        level.set(rootId, 0);
        visited.add(rootId);
        queue.push(rootId);
    });
    
    // BFS to assign levels
    while (queue.length > 0) {
        const current = queue.shift();
        const currentLevel = level.get(current);
        
        // Process dependents (children in tree)
        const children = dependents.get(current) || [];
        children.forEach(child => {
            if (!visited.has(child)) {
                level.set(child, currentLevel + 1);
                visited.add(child);
                queue.push(child);
            } else {
                // Already visited - might be in a cycle, assign to deeper level
                const existingLevel = level.get(child);
                if (existingLevel <= currentLevel) {
                    level.set(child, currentLevel + 1);
                }
            }
        });
    }
    
    // Assign levels to unvisited nodes (orphans or cycles)
    nodes.forEach(n => {
        if (!level.has(n.id)) {
            // Find max level of dependencies, or assign to max level + 1
            const depLevels = (dependencies.get(n.id) || []).map(depId => level.get(depId) || 0);
            const maxDepLevel = depLevels.length > 0 ? Math.max(...depLevels) : -1;
            level.set(n.id, maxDepLevel + 1);
        }
    });
    
    // Group nodes by level
    const nodesByLevel = new Map();
    level.forEach((lvl, nodeId) => {
        if (!nodesByLevel.has(lvl)) {
            nodesByLevel.set(lvl, []);
        }
        nodesByLevel.get(lvl).push(nodeId);
    });
    
    console.log(`[TREE] Levels:`, Array.from(nodesByLevel.keys()).sort((a, b) => a - b).map(l => `${l}: ${nodesByLevel.get(l).length} nodes`));
    
    // Position nodes: level determines Y, siblings spread horizontally
    const maxLevel = Math.max(...Array.from(level.values()));
    
    nodesByLevel.forEach((nodeIds, lvl) => {
        const y = rootY + (lvl * levelHeight);
        const count = nodeIds.length;
        const totalWidth = (count - 1) * nodeSpacing;
        const startX = -totalWidth / 2;
        
        nodeIds.forEach((nodeId, idx) => {
            const x = startX + (idx * nodeSpacing);
            
            // Add small random offset to break perfect alignment
            const jitterX = (Math.random() - 0.5) * 10;
            const jitterY = (Math.random() - 0.5) * 5;
            
            nodeMap.set(nodeId, {
                id: nodeId,
                x: x + jitterX,
                y: y + jitterY,
                level: lvl,
                vx: 0,
                vy: 0
            });
        });
    });
    
    // Calculate bounds for camera
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    nodeMap.forEach(n => {
        minX = Math.min(minX, n.x);
        maxX = Math.max(maxX, n.x);
        minY = Math.min(minY, n.y);
        maxY = Math.max(maxY, n.y);
    });
    
    const width = maxX - minX;
    const height = maxY - minY;
    const maxDim = Math.max(width, height, 100);
    
    // Calculate camera distance
    const fovRad = (50 * Math.PI) / 180;
    finalCameraDistance3D = (maxDim * 1.2) / (2 * Math.tan(fovRad / 2));
    
    console.log(`[TREE] Bounds: X[${minX.toFixed(1)}, ${maxX.toFixed(1)}] Y[${minY.toFixed(1)}, ${maxY.toFixed(1)}]`);
    console.log(`[TREE] Max dimension: ${maxDim.toFixed(1)}, Camera distance: ${finalCameraDistance3D.toFixed(1)}`);
    console.log(`[TREE] Tree layout calculated for ${nodeMap.size} nodes`);
    
    return nodeMap;
}

// --- 2. 3D ENGINE (THREE.JS) ---
function init3DView() {
    console.log('[3D] ========================================');
    console.log('[3D] Initializing 3D renderer (translator -> renderer)');
    console.log('[3D] ========================================');
    const container = document.getElementById('canvas-3d');
    if (!container) {
        console.error('[3D] FATAL: canvas-3d container not found!');
        return;
    }
    console.log('[3D] Container found:', container);
    
    container.style.display = 'block';
    container.style.opacity = '1';
    console.log('[3D] Container display set to block, opacity to 1');
    
    // Inject Reset Button
    if (!document.getElementById('btn-reset')) {
        const camBtn = document.getElementById('btn-cam');
        if (camBtn && camBtn.parentNode) {
            const resetBtn = document.createElement('button');
            resetBtn.id = 'btn-reset';
            resetBtn.textContent = '↺ RESET';
            resetBtn.onclick = window.resetView;
            // Insert before camera button
            camBtn.parentNode.insertBefore(resetBtn, camBtn); 
        }
    }
    
    // Scene
    scene3d = new THREE.Scene();
    // Subtle Fog for Depth Perception (consultant request)
    if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
        // City view: Minimal fog (depth perception without obscuring)
        scene3d.fog = new THREE.Fog(0x000000, 400, 1200);
    } else {
        // Space view: Dramatic fog
        scene3d.fog = new THREE.Fog(0x000000, 200, 900);
    } 
    
    // Camera
    const aspect = window.innerWidth / window.innerHeight;
    
    // Standard Perspective Camera for Space/Galaxy Views
    const perspectiveCam = new THREE.PerspectiveCamera(50, aspect, 0.1, 4000);
    
    // Orthographic Camera for City View (Isometric - SimCity style)
    // Frustum size = view size in world units
    const frustumSize = 300; 
    orthoCam = new THREE.OrthographicCamera(
        frustumSize * aspect / -2, 
        frustumSize * aspect / 2, 
        frustumSize / 2, 
        frustumSize / -2, 
        1, 
        2000
    );
    
    // Default to Perspective
    camera3d = perspectiveCam; 
    camera3d.position.set(0, 0, 50);
    camera3d.lookAt(0,0,0);
    
    // Renderer
    renderer3d = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer3d.setSize(window.innerWidth, window.innerHeight);
    renderer3d.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer3d.domElement);
    
    // Lighting (Boosted for visibility)
    const ambientLight = new THREE.AmbientLight(0x222244, 0.8); // Increased from 0.3
    scene3d.add(ambientLight);
    
    // Nebula Lights (Background ambiance) - Color scheme separation
    if (window.currentGraphType === 'functions' || window.currentGraphType === 'function_dependency') {
        // Functions: Warm ambient lighting (orange/red)
        const nebula1 = new THREE.PointLight(0xFF6B35, 1.2, 400);
        nebula1.position.set(100, 50, -100);
        scene3d.add(nebula1);
        
        const nebula2 = new THREE.PointLight(0xFF8C42, 1.0, 400);
        nebula2.position.set(-100, -50, 100);
        scene3d.add(nebula2);
    } else if (window.currentGraphType === 'api') {
        // APIs: Cool ambient lighting (blue/cyan)
        const nebula1 = new THREE.PointLight(0x3b82f6, 1.2, 400);
        nebula1.position.set(100, 50, -100);
        scene3d.add(nebula1);
        
        const nebula2 = new THREE.PointLight(0x60A5FA, 1.0, 400);
        nebula2.position.set(-100, -50, 100);
        scene3d.add(nebula2);
    } else {
        // Files: Default purple/cyan
        const nebula1 = new THREE.PointLight(0x7c3aed, 1.2, 400);
        nebula1.position.set(100, 50, -100);
        scene3d.add(nebula1);
        
        const nebula2 = new THREE.PointLight(0x00ff94, 1.0, 400);
        nebula2.position.set(-100, -50, 100);
        scene3d.add(nebula2);
    }
    
    // Key Light (Directional - for Low Poly definition)
    const keyLight = new THREE.DirectionalLight(0xffffff, 0.8);
    keyLight.position.set(50, 100, 50);
    scene3d.add(keyLight);
    
    // Rim Light (Backlight - to define silhouettes)
    const rimLight = new THREE.DirectionalLight(0xffffff, 0.6);
    rimLight.position.set(-50, 50, -100);
    scene3d.add(rimLight);
    
    // Calculate the Layout FIRST
    console.log('[3D] Calling calculateReferenceLayout...');
    final2DPositions = calculateReferenceLayout();
    console.log('[3D] Layout calculated, positions stored:', final2DPositions.size);
    
    // SETUP CAMERA BASED ON GRAPH TYPE
    if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
        // Switch to Orthographic for 2D City View (No perspective BS)
        camera3d = orthoCam;
        console.log('[3D] Using Orthographic Camera for 2D City View');
        
        // --- SET INITIAL VIEW ---
        // Zoom out to fit whole city
        const zoom = 0.5; // Adjust based on city size
        camera3d.zoom = zoom;
        camera3d.position.set(0, 0, 500); // Directly overhead
        camera3d.lookAt(0, 0, 0);
        camera3d.updateProjectionMatrix();
        
    } else {
        camera3d = perspectiveCam;
        console.log('[3D] Using Perspective Camera for Graph View');
    }
    
    // No 2D network needed - staying in 3D for interaction
    
    // Use translator to get normalized data (translator -> renderer path)
    const graphData = window.GraphDataTranslator.translate(window.currentGraphType || 'api');
    console.log(`[3D] Graph data via translator: ${graphData.nodes.length} nodes, ${graphData.edges.length} edges`);
    console.log('[3D] Creating 3D nodes (balls) and edges (lines)...');
    
    // UPDATE UI STATS (Fix "LOADING..." issue)
    if (graphData.report && graphData.report.project) {
        const projName = graphData.report.project.name || 'Unknown Project';
        const projEl = document.getElementById('project-name');
        if (projEl) projEl.textContent = projName;
    }
    
    // Add Close Button to Panel if not present
    const infoPanel = document.getElementById('info-panel');
    if (infoPanel && !infoPanel.querySelector('.panel-close-btn')) {
        const closeBtn = document.createElement('button');
        closeBtn.className = 'panel-close-btn';
        closeBtn.innerHTML = '×';
        closeBtn.onclick = window.toggleInfoPanel;
        infoPanel.appendChild(closeBtn);
    }
    
    if (graphData.summary) {
        const nodeCountEl = document.getElementById('node-count');
        if (nodeCountEl) nodeCountEl.textContent = graphData.nodes.length;
        
        const edgeCountEl = document.getElementById('edge-count');
        if (edgeCountEl) edgeCountEl.textContent = graphData.edges.length;
        
        const impactEl = document.getElementById('high-impact-count');
        if (impactEl) impactEl.textContent = graphData.summary.high_impact || 0;
        
        const orphanEl = document.getElementById('orphaned-count');
        if (orphanEl) orphanEl.textContent = graphData.summary.orphaned || 0;
    }
    
    // --- 3D GRID BACKGROUND (Shader) ---
    const gridVertexShader = `
        varying vec3 vWorldPos;
        void main() {
            vWorldPos = (modelMatrix * vec4(position, 1.0)).xyz;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `;

    const gridFragmentShader = `
        varying vec3 vWorldPos;
        uniform vec3 uColor;
        uniform vec3 uHighlight;
        uniform vec3 uMouse;
        uniform float uRadius;
        uniform float uGridSize;
        uniform float uThickness;
        uniform float uCameraDistance;
        uniform float uBaseOpacity;

        void main() {
            vec2 pos = vWorldPos.xy;
            // Grid Lines
            vec2 grid = abs(fract(pos / uGridSize - 0.5) - 0.5) / fwidth(pos / uGridSize);
            float line = min(grid.x, grid.y);
            float alpha = 1.0 - smoothstep(0.0, uThickness, line);
            
            // Mouse Spotlight
            float dist = distance(pos, uMouse.xy);
            float spot = 1.0 - smoothstep(0.0, uRadius, dist);
            
            // Mix Colors
            vec3 finalColor = mix(uColor, uHighlight, spot * 0.8); 
            
            // Distance Fade (Fog-like)
            float fade = 1.0 - smoothstep(0.0, 1500.0, length(pos));
            
            // Adaptive opacity based on camera distance (zoom level)
            // When zoomed out (far camera), reduce opacity significantly
            // Camera distance typically ranges from ~50 (zoomed in) to ~500+ (zoomed out)
            float distanceOpacity = 1.0 - smoothstep(100.0, 400.0, uCameraDistance);
            distanceOpacity = max(distanceOpacity, 0.15); // Minimum 15% opacity even when very zoomed out
            
            if (alpha < 0.1 && spot < 0.1) discard;
            
            // Reduced base opacity from 0.6 to 0.3, then multiplied by distance factor
            gl_FragColor = vec4(finalColor, (alpha + spot * 0.2) * fade * uBaseOpacity * distanceOpacity);
        }
    `;

    const gridUniforms = {
        uColor: { value: new THREE.Color(0x334155) }, // Slate-600 (brighter)
        uHighlight: { value: new THREE.Color(0x7c3aed) }, 
        uMouse: { value: new THREE.Vector3(9999, 9999, 0) }, // Start off-screen
        uRadius: { value: 50.0 }, // Much smaller spotlight (was 200.0)
        uGridSize: { value: 5.0 }, // Ultra-fine grid (5x smaller)
        uThickness: { value: 1.0 },
        uCameraDistance: { value: 100.0 }, // Camera distance for adaptive opacity
        uBaseOpacity: { value: 0.3 } // Reduced base opacity from 0.6 to 0.3
    };
    
    const gridMat = new THREE.ShaderMaterial({
        vertexShader: gridVertexShader,
        fragmentShader: gridFragmentShader,
        uniforms: gridUniforms,
        transparent: true,
        depthWrite: false,
        side: THREE.DoubleSide
    });
    
    const gridGeo = new THREE.PlaneGeometry(4000, 4000);
    const gridMesh = new THREE.Mesh(gridGeo, gridMat);
    gridMesh.position.z = -25; // Background Plane (Furthest back)
    scene3d.add(gridMesh);
    window.gridMesh = gridMesh;

    // Create 3D Nodes based on 2D destinations + Random Z
    let nodeCount = 0;
    graphData.nodes.forEach(node => {
        nodeCount++;
        const dest = final2DPositions.get(node.id) || {x:0, y:0};
        
        // COLOR SCHEME SEPARATION: Cool palette for APIs, Warm palette for Functions
        let colorHex = 0x7c3aed; // Default purple (API)
        
        // Custom Color Logic based on Graph Type
        if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
            colorHex = 0x00F0FF; // Neon Cyan for FILES (default)
        } else if (window.currentGraphType === 'functions' || window.currentGraphType === 'function_dependency') {
            // FUNCTIONS: Warm palette (reds, oranges, yellows)
            colorHex = 0xFF4500; // Orange Red for FUNCTIONS (default - warmer than pure red)
        } else {
            // API: Cool palette (blues, cyans, purples)
            colorHex = 0x3b82f6; // Blue-500 for API (default - cooler than purple)
        }

        // High impact overrides everything
        if (node.high_impact) {
            if (window.currentGraphType === 'functions' || window.currentGraphType === 'function_dependency') {
                colorHex = 0xFF6B35; // Warm orange-red for high impact functions
            } else {
                colorHex = 0xBC13FE; // Hot pink for high impact APIs
            }
        } else if (node.color && node.color.background) {
            // Parse color from node data
            const bgColor = node.color.background;
            if (bgColor.startsWith('#')) {
                const parsedColor = parseInt(bgColor.substring(1), 16);
                
                // Apply color scheme filter based on graph type
                if (window.currentGraphType === 'functions' || window.currentGraphType === 'function_dependency') {
                    // Functions: Shift colors toward warm palette
                    // Convert to RGB, shift toward warm, convert back
                    const r = (parsedColor >> 16) & 0xFF;
                    const g = (parsedColor >> 8) & 0xFF;
                    const b = parsedColor & 0xFF;
                    
                    // Boost red/orange, reduce blue
                    const warmR = Math.min(255, r + 30);
                    const warmG = Math.max(0, Math.min(255, g - 10));
                    const warmB = Math.max(0, b - 40);
                    
                    colorHex = (warmR << 16) | (warmG << 8) | warmB;
                } else if (window.currentGraphType === 'api') {
                    // APIs: Shift colors toward cool palette
                    const r = (parsedColor >> 16) & 0xFF;
                    const g = (parsedColor >> 8) & 0xFF;
                    const b = parsedColor & 0xFF;
                    
                    // Boost blue/cyan, reduce red
                    const coolR = Math.max(0, r - 30);
                    const coolG = Math.min(255, g + 20);
                    const coolB = Math.min(255, b + 40);
                    
                    colorHex = (coolR << 16) | (coolG << 8) | coolB;
                } else {
                    colorHex = parsedColor; // Files: keep original
                }
            }
        }
        
        // Get node size (matching reference: node.size * 0.3)
        const nodeSize = (node.size || 20) * 0.3;
        if (nodeCount <= 3) {
            console.log(`[3D] Node ${nodeCount}: size=${node.size}, sphere radius=${nodeSize.toFixed(2)}`);
        }
        
        // Geometry and Material based on graph type
        let geo;
        let mat;
        let isGlass = false;
        
        if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
            // FILES: Code Metropolis (City Grid)
            
            // Metric 1: Functional Complexity -> HEIGHT
            // Industry Standard: Polynomial Scaling (Square Root)
            // Preserves variance better than Log, but controls outliers better than Linear.
            const complexity = (node.function_count || 0) + (node.endpoint_count || 0);
            // Base height 5, plus sqrt scaling. Cap at 200.
            // FORCE 2D: Flatten buildings (minimal height)
            const height = 2; 
            
            // Metric 2: Connectivity/Impact -> FOOTPRINT (Width/Depth)
            // Uses node.size which is calculated from import counts in API
            // Or fallback to import_count directly
            const baseSize = Math.max(15, (node.size || 20) * 0.6);
            
            // Box Geometry (Skyscraper) -> FLATTENED to tile
            // Width/Depth = Footprint based on Impact/Connectivity
            geo = new THREE.BoxGeometry(baseSize, baseSize, height);
            geo.translate(0, 0, height / 2); // Pivot at bottom
            
            // "Data Glass" Material -> FLAT 2D MATERIAL
            // Color: Use File Type Color (Cyan for Python, etc.)
            
            // 1. Base Color from Node (File Type)
            let baseColor = new THREE.Color(colorHex);
            
            // 2. No Heat Overlay for 2D (simpler look)
            mat = new THREE.MeshBasicMaterial({
                color: baseColor,
                transparent: true,
                opacity: 0.8,
                side: THREE.DoubleSide
            });
            
            // GOD BUILDING ALERT (Red Beacon) -> REMOVED FOR 2D FLAT VIEW
            // Or keep as a ring on the ground?
            // Let's remove for "pure 2D" request to keep it clean.
            if (complexity > 150) {
                 // Add simple ring on ground to indicate importance
                const ringGeo = new THREE.RingGeometry(baseSize * 0.8, baseSize, 32);
                const ringMat = new THREE.MeshBasicMaterial({ color: 0xff0000, side: THREE.DoubleSide });
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.position.set(0, 0, 1); // Just above building
                window.tempBeacon = ring;
            }
            
            // Building Contours
            const edges = new THREE.EdgesGeometry(geo);
            const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.5 }));
            
            // STORE FOR LATER ADDITION
            window.tempLine = line;

            // Store height for label positioning (flat)
            window.tempHeight = height;
            
        } else {
            // API & FUNCTIONS: Low Poly Sphere (Icosahedron detail 0) - Blob/sphere layout
            geo = new THREE.IcosahedronGeometry(nodeSize, 0);
            mat = new THREE.MeshStandardMaterial({ 
                color: colorHex, 
                emissive: colorHex,
                emissiveIntensity: 0.4, // Add glow
                flatShading: true,
                metalness: 0.2,
                roughness: 0.4
            });
        }
        
        const mesh = new THREE.Mesh(geo, mat);
        
        // Attach temp line if exists (Files View)
        if (window.tempLine) {
            mesh.add(window.tempLine);
            window.tempLine = null;
        }
        
        // Attach temp beacon if exists (God Building)
        if (window.tempBeacon) {
            mesh.add(window.tempBeacon);
            window.tempBeacon = null;
        }
        
        // Add random initial rotation (Upright, random Yaw)
        if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
            // City Mode: Upright buildings (no random tumble)
            mesh.rotation.x = 0;
            mesh.rotation.y = 0; 
            mesh.rotation.z = 0; 
        } else {
            // Space Mode: Random tumbling
            mesh.rotation.x = 0; 
            mesh.rotation.y = Math.random() * Math.PI;
        }
        
        // Assign random rotation speed - Sims Style (Single Axis)
        mesh.userData.rotSpeedX = 0;
        // Disable rotation for FILES (Code Metropolis)
        if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
            mesh.userData.rotSpeedY = 0;
        } else {
            mesh.userData.rotSpeedY = 0.05; // Faster spin for API/Functions
        }
        
        // Add Wireframe for Glass Towers
        if (isGlass) {
            const edges = new THREE.EdgesGeometry(geo);
            const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.3 }));
            mesh.add(line);
        }
        
        // Glow Sprite
        const canvas = document.createElement('canvas');
        canvas.width = 32; canvas.height = 32;
        const context = canvas.getContext('2d');
        const gradient = context.createRadialGradient(16, 16, 0, 16, 16, 16);
        gradient.addColorStop(0, 'rgba(255,255,255,1)');
        gradient.addColorStop(0.2, 'rgba(255,255,255,0.5)');
        gradient.addColorStop(0.5, 'rgba(255,255,255,0.1)');
        gradient.addColorStop(1, 'rgba(0,0,0,0)');
        context.fillStyle = gradient;
        context.fillRect(0, 0, 32, 32);
        
        const texture = new THREE.CanvasTexture(canvas);
        const spriteMat = new THREE.SpriteMaterial({ 
            map: texture, 
            color: colorHex, 
            transparent: true, 
            blending: THREE.AdditiveBlending,
            depthWrite: false // FIX: Prevents "square cutout" artifacts
        });
        const sprite = new THREE.Sprite(spriteMat);
        // Glow size matching reference: node.size * 2
        sprite.scale.set((node.size || 20) * 2, (node.size || 20) * 2, 1);
        mesh.add(sprite);
        
        // Text Label (hidden initially, shown after animation)
        // Measure text first to determine canvas size
        const labelText = node.label || node.id;
        const fontSize = 16; // Reduced from 32 to 16 - much smaller font
        const fontFamily = '"Roboto Mono", "Consolas", "Courier New", monospace';
        const font = `400 ${fontSize}px ${fontFamily}`;
        
        // Create temporary context to measure text
        const tempCanvas = document.createElement('canvas');
        const tempContext = tempCanvas.getContext('2d');
        tempContext.font = font;
        const textMetrics = tempContext.measureText(labelText);
        const textWidth = textMetrics.width;
        
        // Calculate canvas dimensions with padding
        const padding = 20; // Reduced padding
        const maxWidth = 300; // Reduced max width
        const canvasWidth = Math.min(Math.ceil(textWidth) + padding, maxWidth);
        const canvasHeight = 64; // Reduced height
        
        // Truncate text if it exceeds max width
        let displayText = labelText;
        if (textWidth > maxWidth - padding) {
            // Find where to truncate
            const maxTextWidth = maxWidth - padding - 60; // Leave room for "..."
            let truncated = '';
            for (let i = 0; i < labelText.length; i++) {
                const testText = labelText.substring(0, i) + '...';
                tempContext.font = font;
                const testWidth = tempContext.measureText(testText).width;
                if (testWidth > maxTextWidth) {
                    truncated = labelText.substring(0, Math.max(0, i - 1)) + '...';
                    break;
                }
            }
            displayText = truncated || labelText;
        }
        
        // Create actual label canvas - HIGH RESOLUTION for crisp text
        const dpr = window.devicePixelRatio || 2; // Use device pixel ratio for retina displays
        const labelCanvas = document.createElement('canvas');
        const labelContext = labelCanvas.getContext('2d');
        labelCanvas.width = canvasWidth * dpr; // High res
        labelCanvas.height = canvasHeight * dpr; // High res
        labelCanvas.style.width = canvasWidth + 'px';
        labelCanvas.style.height = canvasHeight + 'px';
        
        // Scale context for high DPI
        labelContext.scale(dpr, dpr);
        
        // Draw label with proper font size (already scaled by dpr)
        labelContext.font = font;
        labelContext.fillStyle = 'rgba(255, 255, 255, 0.95)';
        labelContext.textAlign = 'center';
        labelContext.textBaseline = 'middle';
        labelContext.shadowColor = 'rgba(0, 0, 0, 1.0)';
        labelContext.shadowBlur = 2;
        labelContext.shadowOffsetX = 0;
        labelContext.shadowOffsetY = 0;
        
        // Enable text rendering hints for better quality
        labelContext.textRenderingOptimization = 'optimizeQuality';
        labelContext.imageSmoothingEnabled = true;
        labelContext.imageSmoothingQuality = 'high';
        
        labelContext.fillText(displayText, canvasWidth / 2, canvasHeight / 2);
        
        const labelTexture = new THREE.CanvasTexture(labelCanvas);
        labelTexture.minFilter = THREE.LinearFilter; // Better filtering
        labelTexture.magFilter = THREE.LinearFilter;
        labelTexture.generateMipmaps = false; // Disable mipmaps for text clarity
        
        const labelMaterial = new THREE.SpriteMaterial({ 
            map: labelTexture, 
            transparent: true,
            opacity: 0, // Start hidden
            depthWrite: false 
        });
        const labelSprite = new THREE.Sprite(labelMaterial);
        
        // Dynamic Label Scaling - maintain aspect ratio properly
        const labelScale = camera3d.isOrthographicCamera ? 20 : 15; // Reduced from 60/40 to 20/15
        const aspectRatio = canvasWidth / canvasHeight;
        // Scale maintaining aspect ratio - width and height should match canvas proportions
        labelSprite.scale.set(labelScale * aspectRatio, labelScale, 1);
        
        // Store original text for tooltip/hover
        labelSprite.userData.originalText = labelText;
        labelSprite.userData.displayText = displayText;
        
        // Position Label - FIXED BELOW NODE at predetermined distance
        // Label is part of the node entity - moves with node automatically (child of mesh)
        const labelDistance = 8; // Fixed distance below node
        const labelY = -nodeSize - labelDistance; // Negative Y = below node
        labelSprite.position.set(0, labelY, 0); // Fixed position relative to node
        mesh.add(labelSprite); // Label is child of node - moves with it automatically
        
        // Set Initial 3D Position
        let zDepth = (Math.random() - 0.5) * 300;
        if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
            zDepth = 0; // Grounded on Grid for City
        }
        mesh.position.set(dest.x, dest.y, zDepth);
        
        // Store meta for animation (KEEP labelSprite reference!)
        mesh.userData = {
            id: node.id,
            destX: dest.x,
            destY: dest.y,
            origZ: zDepth,
            labelSprite: labelSprite, // Store reference for later
            rotSpeedX: mesh.userData.rotSpeedX,
            rotSpeedY: mesh.userData.rotSpeedY
        };
        
        scene3d.add(mesh);
        nodes3d.push(mesh);
    });
    
    // RENDER DISTRICTS (City Mode)
    if ((window.currentGraphType === 'files' || window.currentGraphType === 'dependency') && window.cityDistricts) {
         console.log(`[CITY] Rendering ${window.cityDistricts.length} districts...`);
         const districtGroup = new THREE.Group();
         
         window.cityDistricts.forEach(d => {
             // 1. Base Plane (Sidewalk)
             const geo = new THREE.PlaneGeometry(d.w - 2, d.h - 2); // Shrink slightly for gaps
             // Darker, more solid color for ground
             const depthColor = new THREE.Color().setHSL(0.6, 0.3, 0.1); 
             const mat = new THREE.MeshBasicMaterial({ 
                 color: depthColor, 
                 transparent: true, 
                 opacity: 0.5, // More visible (was 0.3)
                 side: THREE.DoubleSide,
                 depthWrite: false
             });
             const mesh = new THREE.Mesh(geo, mat);
             // Center of district is d.x + d.w/2 ... wait. 
             // CityLayout returns x,y as top-left? 
             // Yes: "currentX = x... item.x = currentX"
             // And "item.w" is width.
             // Three.js PlaneGeometry is centered at 0,0.
             // So we need to position it at center of the rect.
             
             mesh.position.set(d.x + d.w/2, d.y + d.h/2, -22); // Behind buildings (Z=-22)
             districtGroup.add(mesh);
             
             // 2. Border Line (Neon curbs)
             const edges = new THREE.EdgesGeometry(geo);
             const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ 
                color: 0x4488ff, 
                transparent: true, 
                opacity: 0.6 // Much brighter (was 0.2)
             }));
             line.position.copy(mesh.position);
             districtGroup.add(line);
             
             // 3. Text Label (Floating above district)
             // Adaptive sizing: Always show but scale for top levels
             if (d.depth <= 2) { 
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = 512; canvas.height = 128;
                ctx.fillStyle = 'rgba(0,0,0,0)'; // Transparent
                ctx.fillRect(0,0,512,128);
                
                // Cleaner district label
                ctx.font = '600 48px "Segoe UI", "Roboto", sans-serif'; 
                ctx.fillStyle = '#4488ff';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
                ctx.shadowBlur = 6;
                
                const count = d.fileCount || 0;
                const labelText = count > 0 ? `${d.name.toUpperCase()} (${count})` : d.name.toUpperCase();
                ctx.fillText(labelText, 256, 64);
                
                const tex = new THREE.CanvasTexture(canvas);
                const labelMat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.6 });
                const label = new THREE.Sprite(labelMat);
                
                const labelScale = Math.min(d.w * 0.8, 150); 
                label.scale.set(labelScale, labelScale * 0.25, 1);
                label.position.set(d.x + d.w/2, d.y + d.h/2, -22 + 5); // Floating slightly
                districtGroup.add(label);
             }
         });
         scene3d.add(districtGroup);
         window.districtGroup3d = districtGroup;
    }
    
    // Edge Lines with Arrows - Color scheme separation
    let edgeColor = 0xffffff; // Default white
    let edgeOpacity = 0.15;
    
    if (window.currentGraphType === 'functions' || window.currentGraphType === 'function_dependency') {
        // Functions: Warm edge colors (orange/red tint)
        edgeColor = 0xFF8C42; // Warm orange
        edgeOpacity = 0.25; // Slightly more visible
    } else if (window.currentGraphType === 'api') {
        // APIs: Cool edge colors (blue/cyan tint)
        edgeColor = 0x60A5FA; // Cool blue
        edgeOpacity = 0.2;
    }
    
    const lineMat = new THREE.LineBasicMaterial({ 
        color: edgeColor, 
        transparent: true, 
        opacity: edgeOpacity 
    });
    const edgeGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(graphData.edges.length * 6);
    edgeGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    edgeLines3d = new THREE.LineSegments(edgeGeo, lineMat);
    scene3d.add(edgeLines3d);
    
    // Create arrow cones for each edge to show direction
    const arrowGroup = new THREE.Group();
    // Reduced arrow size: radius 1, height 3 (was 2, 6)
    const arrowGeometry = new THREE.ConeGeometry(1, 3, 8);
    
    // Arrow colors match edge colors
    let arrowColor = 0x00ff94; // Default mint green
    if (window.currentGraphType === 'function_dependency') {
        arrowColor = 0xFF6B35; // Warm orange-red for functions
    } else if (window.currentGraphType === 'api') {
        arrowColor = 0x3b82f6; // Cool blue for APIs
    }
    
    const arrowMaterial = new THREE.MeshBasicMaterial({ color: arrowColor, transparent: true, opacity: 0.8 });
    
    graphData.edges.forEach(edge => {
        const arrow = new THREE.Mesh(arrowGeometry, arrowMaterial);
        arrow.userData = { from: edge.from, to: edge.to };
        // Start invisible and scaled down
        arrow.scale.set(0, 0, 0);
        arrowGroup.add(arrow);
    });
    scene3d.add(arrowGroup);
    window.arrowGroup3d = arrowGroup; // Store for updates
    
    // MINIMAP REMOVED
    
    // Start Animation Loop
    console.log('[3D] Starting animation loop...');
    let time = 0;
    let frameCount = 0;
    function animate() {
        if (transitionTo2DStarted) {
            console.log('[3D] Animation stopped - transition started');
            return;
        }
        window.currentAnimationFrameId = requestAnimationFrame(animate);
        time += 16;
        frameCount++;
        
        const DURATION = 2000; // Reduced from 4s to 2s
        
        if (frameCount === 1) {
            console.log('[3D] First frame rendered');
        }
        if (frameCount % 60 === 0) {
            console.log(`[3D] Animation running... time: ${time}ms / ${DURATION}ms`);
        }
        
        if (time >= DURATION) {
            transitionTo2DStarted = true;
            console.log(`[3D] Animation complete at ${time}ms, transitioning to interactive...`);
            transitionToInteractive();
            return;
        }
        
        const progress = time / DURATION;
        const ease = 1 - Math.pow(1 - progress, 3); // Smooth ease out
        
        // ROTATION: Active from T=0 (Sims Style)
        nodes3d.forEach(node => {
             if (node.userData.rotSpeedY) {
                 node.rotation.y += node.userData.rotSpeedY;
             }
             // Ring Animation
             node.children.forEach(child => {
                 if (child.type === 'Group') {
                     child.children.forEach(gc => {
                         if (gc.userData.isRing) {
                             gc.rotation.z += gc.userData.rotSpeed;
                         }
                     });
                 }
             });
        });
        
        // Calculate final camera distance (do this once)
        if (!window.finalCameraDistanceCalculated) {
            window.finalCameraDistanceCalculated = true;
            console.log(`[3D] Using calculated camera distance: ${finalCameraDistance3D.toFixed(1)}`);
        }
        
        const centerNode = nodes3d[0];
        if (!centerNode) return;
        
        const centerU = centerNode.userData;
        const finalDistance = finalCameraDistance3D;
        
        // === UNIFIED CAMERA & NODE MOTION ===
        
        if (window.currentGraphType === 'dependency') {
            // --- 2D CITY ANIMATION (Flat Pan) ---
            // No fly-in, just simple pan to center
            
            // Calculate bounding box center
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            nodes3d.forEach(n => {
                 minX = Math.min(minX, n.userData.destX);
                 maxX = Math.max(maxX, n.userData.destX);
                 minY = Math.min(minY, n.userData.destY);
                 maxY = Math.max(maxY, n.userData.destY);
            });
            const centerX = (minX + maxX) / 2;
            const centerY = (minY + maxY) / 2;
            
            camera3d.position.x = centerX * ease; // Simple pan from 0 to center
            camera3d.position.y = centerY * ease;
            camera3d.position.z = 500; // Locked height
            camera3d.lookAt(camera3d.position.x, camera3d.position.y, 0);
            
            // Nodes: Grounded
            nodes3d.forEach((mesh) => {
                const u = mesh.userData;
                mesh.position.set(u.destX, u.destY, 0); 
            });
            
        } else {
            // --- STANDARD GALAXY ZOOM (API/FUNC) ---
            // Start: Inside center node
            const startCamX = centerU.destX;
            const startCamY = centerU.destY;
            const startCamZ = centerU.origZ + 20;
            
            camera3d.position.x = startCamX + (0 - startCamX) * ease;
            camera3d.position.y = startCamY + (0 - startCamY) * ease;
            camera3d.position.z = startCamZ + (finalDistance - startCamZ) * ease;
            camera3d.lookAt(0, 0, 0);
            
            // Orbit Motion
            const orbitAmount = 1 - ease; 
            const angle = time * 0.001 * orbitAmount;
            
            nodes3d.forEach((mesh, idx) => {
                const u = mesh.userData;
                if (idx === 0) {
                    mesh.position.set(u.destX, u.destY, u.origZ * (1 - ease));
                } else {
                    const relX = u.destX - centerU.destX;
                    const relY = u.destY - centerU.destY;
                    const relZ = u.origZ - centerU.origZ;
                    
                    const cosA = Math.cos(angle);
                    const sinA = Math.sin(angle);
                    const rotX = relX * cosA - relZ * sinA;
                    const rotZ = relX * sinA + relZ * cosA;
                    
                    const orbitalX = centerU.destX + rotX;
                    const orbitalY = centerU.destY + relY;
                    const orbitalZ = centerU.origZ + rotZ;
                    
                    mesh.position.x = orbitalX + (u.destX - orbitalX) * ease;
                    mesh.position.y = orbitalY + (u.destY - orbitalY) * ease;
                    mesh.position.z = orbitalZ * (1 - ease);
                }
            });
        }
        
        // Update edges and arrows - use translator (translator -> renderer path)
        // Note: edgeData is cached in updateCachedEdgeData, but we use translator for consistency
        const edgeData = window.cachedEdgeData || [];
        const posAttr = edgeLines3d.geometry.attributes.position;
        const nodeLookup = new Map(nodes3d.map(n => [n.userData.id, n]));
        let idx = 0;
        edgeData.forEach(e => {
            const n1 = nodeLookup.get(e.from);
            const n2 = nodeLookup.get(e.to);
            if (n1 && n2) {
                posAttr.setXYZ(idx++, n1.position.x, n1.position.y, n1.position.z);
                posAttr.setXYZ(idx++, n2.position.x, n2.position.y, n2.position.z);
            }
        });
        posAttr.needsUpdate = true;
        edgeLines3d.geometry.setDrawRange(0, idx);
        
        // Update arrow positions and orientations
        // ANIMATION: "launched from the origin to the thing they're sending stuff to"
        if (window.arrowGroup3d) {
            window.arrowGroup3d.children.forEach(arrow => {
                const n1 = nodeLookup.get(arrow.userData.from);
                const n2 = nodeLookup.get(arrow.userData.to);
                if (n1 && n2) {
                    // Calculate direction vector
                    const direction = new THREE.Vector3()
                        .subVectors(n2.position, n1.position)
                        .normalize();
                    
                    // Calculate total distance
                    const totalDistance = n1.position.distanceTo(n2.position);
                    
                    // Target position (near target node)
                    // Place it 8 units before the target node (adjusted for smaller nodes)
                    const targetOffset = 8;
                    const targetPos = new THREE.Vector3(
                        n2.position.x - direction.x * targetOffset,
                        n2.position.y - direction.y * targetOffset,
                        n2.position.z - direction.z * targetOffset
                    );
                    
                    // Start position (at source node)
                    const startPos = n1.position.clone();
                    
                    // ANIMATION LOGIC:
                    // 1. Delay arrow appearance slightly (start after 20% progress)
                    // 2. Move from source to target
                    // 3. Scale up from 0 to 1
                    
                    let arrowProgress = (progress - 0.2) / 0.8; // 0 to 1 over the last 80%
                    if (arrowProgress < 0) arrowProgress = 0;
                    
                    // Smooth easing for arrow
                    const arrowEase = 1 - Math.pow(1 - arrowProgress, 2);
                    
                    // Interpolate position: Move from Source -> Target
                    const currentPos = new THREE.Vector3().lerpVectors(startPos, targetPos, arrowEase);
                    
                    arrow.position.copy(currentPos);
                    
                    // Orient arrow to point from n1 to n2
                    arrow.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
                    
                    // Scale up as it travels (pop effect)
                    const scale = Math.min(arrowEase * 1.5, 1); // Overshoot slightly then settle? No, just 0->1
                    arrow.scale.set(scale, scale, scale);
                    
                    // Fade in
                    arrow.material.opacity = Math.min(arrowEase * 2, 0.8);
                }
            });
        }
        
        // Update Grid Mouse Effect (Persistent)
        updateGridMouse(camera3d);
        
        // Update grid opacity based on camera distance (zoom level)
        if (window.gridMesh && window.gridMesh.material && window.gridMesh.material.uniforms) {
            const cameraDistance = camera3d.position.length();
            window.gridMesh.material.uniforms.uCameraDistance.value = cameraDistance;
        }
        
        renderer3d.render(scene3d, camera3d);
    }
    
    console.log('[3D] Calling animate() to start loop...');
    animate();
    
    window.addEventListener('resize', () => {
        if (renderer3d) {
            const aspect = window.innerWidth / window.innerHeight;
            renderer3d.setSize(window.innerWidth, window.innerHeight);
            
            // Update active camera
            if (camera3d.isOrthographicCamera) {
                const frustumSize = 300;
                camera3d.left = -frustumSize * aspect / 2;
                camera3d.right = frustumSize * aspect / 2;
                camera3d.top = frustumSize / 2;
                camera3d.bottom = -frustumSize / 2;
            } else {
                camera3d.aspect = aspect;
            }
            camera3d.updateProjectionMatrix();
        }
    });
}

// --- 3. TRANSITION TO INTERACTIVE 3D (NO 2D SWAP) ---
function transitionToInteractive() {
    console.log('[3D] Animation complete, enabling interaction...');
    
    // Pop out labels with a nice fade-in effect
    nodes3d.forEach((mesh, idx) => {
        if (mesh.userData.labelSprite) {
            setTimeout(() => {
                // Fade in label over 300ms
                const startTime = Date.now();
                const fadeIn = () => {
                    const elapsed = Date.now() - startTime;
                    const progress = Math.min(elapsed / 300, 1);
                    mesh.userData.labelSprite.material.opacity = progress;
                    if (progress < 1) {
                        requestAnimationFrame(fadeIn);
                    }
                };
                fadeIn();
            }, idx * 50); // Stagger labels for nice effect
        }
    });
    
    // Enable pointer events on 3D canvas
    const canvas3dContainer = document.getElementById('canvas-3d');
    if (!canvas3dContainer) {
        console.error('[3D] Cannot find canvas-3d container for interaction!');
        return;
    }
    
    canvas3dContainer.classList.add('interactive');
    canvas3dContainer.style.pointerEvents = 'auto';
    console.log('[3D] Pointer events enabled on canvas container');
    console.log('[3D] Container style:', window.getComputedStyle(canvas3dContainer).pointerEvents);
    console.log('[3D] Container z-index:', window.getComputedStyle(canvas3dContainer).zIndex);
    
    // Get the actual canvas element from the renderer
    const canvas = renderer3d.domElement;
    console.log('[3D] Canvas element:', canvas);
    console.log('[3D] Canvas parent:', canvas.parentElement);
    console.log('[3D] Canvas style:', window.getComputedStyle(canvas).pointerEvents);
    
    // Test if canvas is clickable
    canvas.style.cursor = 'grab';
    console.log('[3D] Set cursor to grab');
    
    // Add orbit controls for interaction + node dragging
    let isDragging = false;
    let isDraggingNode = false;
    let selectedNode = null;
    let previousMousePosition = { x: 0, y: 0 };
    
    // Raycaster for node selection
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    
    function getIntersectedNode(clientX, clientY) {
        // Convert mouse position to normalized device coordinates (-1 to +1)
        const rect = canvas.getBoundingClientRect();
        mouse.x = ((clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((clientY - rect.top) / rect.height) * 2 + 1;
        
        // Update raycaster
        raycaster.setFromCamera(mouse, camera3d);
        
        // Check intersections with nodes
        const intersects = raycaster.intersectObjects(nodes3d);
        return intersects.length > 0 ? intersects[0].object : null;
    }
    
    // Mouse down logic for dragging
    canvas.addEventListener('mousedown', (e) => {
        e.preventDefault(); // Prevent default selection
        
        // Get intersected node
        const node = getIntersectedNode(e.clientX, e.clientY);
        
        if (node) {
            // Start dragging node
            isDraggingNode = true;
            selectedNode = node;
            canvas.style.cursor = 'grabbing';
            console.log('[3D] Started dragging node:', node.userData.id);
        } else {
            // Start panning camera
            isDragging = true;
            canvas.style.cursor = 'move';
            console.log('[3D] Started panning camera');
        }
        
        previousMousePosition = { x: e.clientX, y: e.clientY };
    });

    // Mouse up logic to handle clicks vs drags
    canvas.addEventListener('mouseup', (e) => {
        const deltaX = Math.abs(e.clientX - previousMousePosition.x);
        const deltaY = Math.abs(e.clientY - previousMousePosition.y);
        const moveThreshold = 5; // pixels
        
        // Stop dragging
        isDragging = false;
        isDraggingNode = false;
        selectedNode = null;
        canvas.style.cursor = 'grab';
        
        // Check if it was a click (minimal movement)
        if (deltaX < moveThreshold && deltaY < moveThreshold) {
            const node = getIntersectedNode(e.clientX, e.clientY);
            if (node) {
                console.log('[3D] Node clicked:', node.userData.id);
                
                // Get full node data from translator
                const graphData = window.GraphDataTranslator.translate(window.currentGraphType || 'api', false);
                const fullNodeData = graphData.nodes.find(n => n.id === node.userData.id);
                
                if (fullNodeData && typeof showNodeInfo === 'function') {
                    showNodeInfo(fullNodeData);
                } else {
                    console.warn('[3D] Could not find full data for node:', node.userData.id);
                }
            }
        }
    });
    
    // Double Click for Code Overlay
    canvas.addEventListener('dblclick', (e) => {
        const node = getIntersectedNode(e.clientX, e.clientY);
        if (node) {
            console.log('[3D] Node double clicked:', node.userData.id);
            const modal = document.getElementById('code-overlay');
            if (modal) {
                // Get full data
                const graphData = window.GraphDataTranslator.translate(window.currentGraphType || 'api', false);
                const data = graphData.nodes.find(n => n.id === node.userData.id);
                
                if (data) {
                    document.getElementById('code-title').textContent = data.label || data.id;
                    
                    let metaHTML = '';
                    if (data.method) metaHTML += `<span style="margin-right:15px">METHOD: ${data.method}</span>`;
                    if (data.function_count !== undefined) metaHTML += `<span style="margin-right:15px">FUNCS: ${data.function_count}</span>`;
                    if (data.import_count !== undefined) metaHTML += `<span>IMPORTS: ${data.import_count}</span>`;
                    document.getElementById('code-meta').innerHTML = metaHTML;
                    
                    // Populate Code Content
                    const codeEl = document.getElementById('code-content');
                    if (data.content) {
                        codeEl.textContent = data.content;
                    } else {
                        codeEl.textContent = "# Source code not available (File not found or not embedded)";
                    }
                    
                    modal.classList.add('active');
                }
            }
        }
    });
    
    canvas.addEventListener('mousemove', (e) => {
        const deltaX = e.clientX - previousMousePosition.x;
        const deltaY = e.clientY - previousMousePosition.y;
        
        if (isDraggingNode && selectedNode) {
            // ... (Node dragging code remains same) ...
            // Raycast to find where mouse intersects the Z=0 plane
            const rect = canvas.getBoundingClientRect();
            mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
            
            raycaster.setFromCamera(mouse, camera3d);
            
            // Create a plane at Z=0 (where all nodes are)
            const plane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
            const intersectPoint = new THREE.Vector3();
            
            // Find where ray intersects the Z=0 plane
            raycaster.ray.intersectPlane(plane, intersectPoint);
            
            if (intersectPoint) {
                // Move node to intersection point (keeping Z=0)
                selectedNode.position.x = intersectPoint.x;
                selectedNode.position.y = intersectPoint.y;
                selectedNode.position.z = 0; // Keep at Z=0
                
                // Update userData
                selectedNode.userData.destX = intersectPoint.x;
                selectedNode.userData.destY = intersectPoint.y;
            }
        } else if (isDragging) {
            // Pan camera - move in XY plane
            
            if (camera3d.isOrthographicCamera) {
                 // ORTHOGRAPHIC PANNING (2D)
                 // In Ortho mode, zoom affects how much world space corresponds to screen pixels
                 // camera3d.zoom is the scale factor. 
                 // Higher zoom = smaller world area = slower movement needed?
                 // Actually, moving 1 pixel on screen = 1/zoom units in world
                 
                 const panSpeed = 1 / camera3d.zoom;
                 
                 camera3d.position.x -= deltaX * panSpeed;
                 camera3d.position.y += deltaY * panSpeed;
                 
            } else {
                 // PERSPECTIVE PANNING (3D)
                // Calculate pan speed based on distance from plane
                const distance = camera3d.position.z;
                const panSpeed = distance * 0.001; // Scale with distance
                
                camera3d.position.x -= deltaX * panSpeed;
                camera3d.position.y += deltaY * panSpeed;
            }
        }
        
        previousMousePosition = { x: e.clientX, y: e.clientY };
    });
    
    canvas.addEventListener('mouseup', () => {
        isDragging = false;
        isDraggingNode = false;
        selectedNode = null;
        canvas.style.cursor = 'grab';
        console.log('[3D] Mouse up - dragging stopped');
    });
    
    canvas.addEventListener('mouseleave', () => {
        isDragging = false;
        isDraggingNode = false;
        selectedNode = null;
        console.log('[3D] Mouse left canvas');
    });
    
    // Create Tooltip Element
    const tooltip = document.createElement('div');
    tooltip.id = 'tooltip-3d';
    tooltip.style.position = 'absolute';
    tooltip.style.pointerEvents = 'none';
    tooltip.style.display = 'none';
    tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
    tooltip.style.color = '#fff';
    tooltip.style.padding = '12px';
    tooltip.style.borderRadius = '6px';
    tooltip.style.border = '1px solid #4488ff';
    tooltip.style.fontFamily = 'monospace';
    tooltip.style.fontSize = '12px';
    tooltip.style.zIndex = '100';
    tooltip.style.maxWidth = '300px';
    tooltip.style.boxShadow = '0 4px 20px rgba(0,0,0,0.5)';
    document.body.appendChild(tooltip);

    // Hover effect - change cursor when over a node
    // Global hover state
    let hoveredNode = null;
    
    canvas.addEventListener('mousemove', (e) => {
        // Tooltip positioning
        if (hoveredNode) {
            tooltip.style.left = (e.clientX + 15) + 'px';
            tooltip.style.top = (e.clientY + 15) + 'px';
        }
    
        if (!isDragging && !isDraggingNode) {
            const node = getIntersectedNode(e.clientX, e.clientY);
            canvas.style.cursor = node ? 'pointer' : 'grab';
            
            // Handle Hover Interactions
            if (node !== hoveredNode) {
                // Unhover old
                if (hoveredNode) {
                     hoveredNode.scale.set(1, 1, 1);
                     tooltip.style.display = 'none';
                }
                
                hoveredNode = node;
                
                // Hover new
                if (hoveredNode) {
                     // Show Tooltip
                     tooltip.style.display = 'block';
                     const id = hoveredNode.userData.id;
                     
                     // Fetch data
                     const graphData = window.GraphDataTranslator.translate(window.currentGraphType || 'api', false);
                     const data = graphData.nodes.find(n => n.id === id);
                     
                     if (data) {
                         let html = `<strong style="font-size:14px; color:#4488ff">${data.label || data.id}</strong><br/>`;
                         html += `<div style="margin-top:5px; border-top:1px solid #333; padding-top:5px">`;
                         
                        // Custom fields based on type
                        if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
                             const complexity = (data.function_count || 0) + (data.endpoint_count || 0);
                             
                             // RISK ASSESSMENT
                             let risk = 'LOW';
                             let riskColor = '#00ff00';
                             if (complexity > 50) { risk = 'MEDIUM'; riskColor = '#ffff00'; }
                             if (complexity > 150) { risk = 'HIGH'; riskColor = '#ff0000'; }
                             
                             html += `<div style="margin-top:8px; padding-top:8px; border-top:1px solid #333;">`;
                             html += `<strong>RISK:</strong> <span style="color:${riskColor}">${risk}</span><br/>`;
                             html += `Complexity: ${complexity.toFixed(0)}<br/>`;
                             
                             // ACTIONABLE SUGGESTIONS
                             if (complexity > 100) {
                                 const filename = data.id.split('/').pop();
                                 const coreName = filename.replace(/\.[^/.]+$/, "_core$&");
                                 const utilsName = filename.replace(/\.[^/.]+$/, "_utils$&");
                                 html += `<em style="color:#888; display:block; margin-top:5px">💡 Split into:</em>`;
                                 html += `<span style="color:#4488ff; display:block; margin-left:10px">• ${coreName}</span>`;
                                 html += `<span style="color:#4488ff; display:block; margin-left:10px">• ${utilsName}</span>`;
                             }
                             
                             if ((data.import_count === 0) && (data.incoming_edges === 0)) { // Check orphans
                                 html += `<em style="color:#ff8800; display:block; margin-top:5px">⚠️ Unused file - consider removing</em>`;
                             }
                             
                             html += `</div>`;
                         } else if (window.currentGraphType === 'api' || window.currentGraphType === 'functions' || window.currentGraphType === 'function_dependency') {
                             // API or Functions view - show method, path/url, and file
                             const method = (data.method || 'UNKNOWN').toUpperCase();
                             const path = data.path || data.url || 'unknown';
                             const file = data.file || data.file_path || 'unknown';
                             const line = data.line || '?';
                             
                             // Extract just filename from full path for cleaner display
                             const fileName = file !== 'unknown' ? file.split(/[/\\]/).pop() : 'unknown';
                             
                             html += `<div style="margin-top:5px;">`;
                             html += `<strong>Method:</strong> ${method}<br/>`;
                             html += `<strong>Path:</strong> ${path.length > 30 ? path.substring(0, 27) + '...' : path}<br/>`;
                             html += `<strong>File:</strong> ${fileName}<br/>`;
                             if (line !== '?' && line !== 0) {
                                 html += `<strong>Line:</strong> ${line}<br/>`;
                             }
                             html += `</div>`;
                         } else {
                             // Generic
                             html += `Type: ${data.type || 'Unknown'}`;
                             // Try to show file if available
                             const file = data.file || data.file_path;
                             if (file) {
                                 const fileName = file.split(/[/\\]/).pop();
                                 html += `<br/><strong>File:</strong> ${fileName}`;
                             }
                         }
                         
                         html += `</div>`;
                         tooltip.innerHTML = html;
                     } else {
                         tooltip.innerHTML = `<strong>${id}</strong>`;
                     }
                }
            }
        }
    });
    
    canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        
        if (camera3d.isOrthographicCamera) {
            // ORTHOGRAPHIC ZOOM (2D)
            // Change zoom property directly
            const zoomSpeed = 0.001;
            camera3d.zoom -= e.deltaY * zoomSpeed;
            camera3d.zoom = Math.max(0.1, Math.min(camera3d.zoom, 5)); // Clamp zoom
            camera3d.updateProjectionMatrix();
            console.log('[3D] Ortho Zoom:', camera3d.zoom.toFixed(2));
        } else {
            // PERSPECTIVE ZOOM (3D)
            // Zoom by moving camera Z
            const zoomSpeed = 0.5;
            camera3d.position.z += e.deltaY * zoomSpeed;
            camera3d.position.z = Math.max(100, Math.min(camera3d.position.z, 2000));
            console.log('[3D] Persp Zoom:', camera3d.position.z.toFixed(1));
        }
    }, { passive: false });
    
    // Continue rendering for interaction with physics
    function renderInteractive() {
        window.currentRenderFrameId = requestAnimationFrame(renderInteractive);
        
        // Update Grid Mouse Effect (Persistent)
        updateGridMouse(camera3d);
        
        // Update grid opacity based on camera distance (zoom level)
        if (window.gridMesh && window.gridMesh.material && window.gridMesh.material.uniforms) {
            const cameraDistance = camera3d.position.length();
            window.gridMesh.material.uniforms.uCameraDistance.value = cameraDistance;
        }
        
        // Get current edge data directly from translator (no caching - simple approach)
        const graphData = window.GraphDataTranslator.translate(window.currentGraphType || 'api');
        const edgeData = graphData.edges || [];
        
        // Physics simulation (only for nodes not being dragged)
        const k = 80; // Spring constant (reduced)
        const damping = 0.9; // Higher damping to slow things down
        const repulsionStrength = 0.5; // Much weaker repulsion
        const attractionStrength = 0.3; // Weaker attraction
        
        nodes3d.forEach(node => {
            // Skip physics for the node being dragged
            if (node === selectedNode) return;
            
            // DISABLE PHYSICS FOR FILES (Code Metropolis)
            // Cities don't move!
            if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
                 return; 
            }
            
            // ROTATION: Sims Style - Single Axis (Y)
            if (node.userData.rotSpeedY) {
                node.rotation.y += node.userData.rotSpeedY;
                // No X/Z rotation for Sims style
            }
            
            // Initialize velocity if not exists
            if (!node.userData.vx) node.userData.vx = 0;
            if (!node.userData.vy) node.userData.vy = 0;
            
            let fx = 0, fy = 0;
            
            // BOBBING: Sims Style (Disable for City Buildings)
            if (window.currentGraphType !== 'dependency') {
                const time = Date.now() * 0.002;
                const phase = node.userData.id.length || 0; 
                const bobForce = Math.cos(time + phase) * 0.5; 
                fy += bobForce;
            }
            
            // CENTRAL GRAVITY: Pull everything to center to prevent scattering
            // This fixes the "1-to-1 connection drift" issue
            const gravity = 0.01;
            fx -= node.position.x * gravity;
            fy -= node.position.y * gravity;
            
            // Repulsion from all other nodes (much weaker)
            nodes3d.forEach(other => {
                if (node === other) return;
                
                const dx = node.position.x - other.position.x;
                const dy = node.position.y - other.position.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
                
                // Gentle repulsion
                const force = (k * k) / (dist * dist);
                fx += (dx / dist) * force * repulsionStrength;
                fy += (dy / dist) * force * repulsionStrength;
            });
            
            // Attraction along edges (spring force)
            edgeData.forEach(edge => {
                let other = null;
                if (edge.from === node.userData.id) {
                    other = nodes3d.find(n => n.userData.id === edge.to);
                } else if (edge.to === node.userData.id) {
                    other = nodes3d.find(n => n.userData.id === edge.from);
                }
                
                if (other) {
                    const dx = node.position.x - other.position.x;
                    const dy = node.position.y - other.position.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
                    
                    // Spring force (Hooke's law) - weaker
                    const force = (dist * dist) / k;
                    fx -= (dx / dist) * force * attractionStrength;
                    fy -= (dy / dist) * force * attractionStrength;
                }
            });
            
            // Cap maximum force to prevent explosions
            const maxForce = 50;
            const forceMag = Math.sqrt(fx * fx + fy * fy);
            if (forceMag > maxForce) {
                fx = (fx / forceMag) * maxForce;
                fy = (fy / forceMag) * maxForce;
            }
            
            // Update velocity with much smaller timestep
            node.userData.vx += fx * 0.001;
            node.userData.vy += fy * 0.001;
            
            // Apply damping
            node.userData.vx *= damping;
            node.userData.vy *= damping;
            
            // Cap maximum velocity
            const maxVel = 2;
            const velMag = Math.sqrt(node.userData.vx * node.userData.vx + node.userData.vy * node.userData.vy);
            if (velMag > maxVel) {
                node.userData.vx = (node.userData.vx / velMag) * maxVel;
                node.userData.vy = (node.userData.vy / velMag) * maxVel;
            }
            
            // Update position
            node.position.x += node.userData.vx;
            node.position.y += node.userData.vy;
            
            // Update userData
            node.userData.destX = node.position.x;
            node.userData.destY = node.position.y;
        });
        
        // LABELS ARE FIXED BELOW NODES - No physics, just maintain fixed position
        // Labels stay at fixed distance below their nodes, no repulsion needed
        
        // ANIMATE BEACONS (Pulsing)
        if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
            const time = Date.now() * 0.005;
            nodes3d.forEach(node => {
                // Find children that are beacons
                node.children.forEach(child => {
                    if (child.userData && child.userData.isBeacon) {
                        const scale = 1 + Math.sin(time + child.userData.phase) * 0.3;
                        child.scale.set(scale, scale, scale);
                        child.material.opacity = 0.5 + Math.sin(time + child.userData.phase) * 0.5;
                    }
                });
                
                // HOVER BREATHING (Micro-interaction)
                if (node === hoveredNode) {
                     const breath = 1.0 + Math.sin(time * 2) * 0.05; // +/- 5% scale
                     node.scale.set(breath, breath, breath);
                } else {
                     // Reset scale smoothly? or just snap back
                     if (node.scale.x !== 1 && !node.userData.isAnimating) {
                         node.scale.set(1, 1, 1);
                     }
                }
            });
        }
        
        // Update edges and arrows every frame
        const posAttr = edgeLines3d.geometry.attributes.position;
        const nodeLookup = new Map(nodes3d.map(n => [n.userData.id, n]));
        
        let idx = 0;
        edgeData.forEach(e => {
            const n1 = nodeLookup.get(e.from);
            const n2 = nodeLookup.get(e.to);
            if (n1 && n2) {
                posAttr.setXYZ(idx++, n1.position.x, n1.position.y, n1.position.z);
                posAttr.setXYZ(idx++, n2.position.x, n2.position.y, n2.position.z);
            }
        });
        posAttr.needsUpdate = true;
        edgeLines3d.geometry.setDrawRange(0, idx);
        
        // Update arrow positions and orientations
        if (window.arrowGroup3d) {
            window.arrowGroup3d.children.forEach(arrow => {
                const n1 = nodeLookup.get(arrow.userData.from);
                const n2 = nodeLookup.get(arrow.userData.to);
                if (n1 && n2) {
                    // Calculate direction vector
                    const direction = new THREE.Vector3()
                        .subVectors(n2.position, n1.position)
                        .normalize();
                    
                    // Position arrow near the END (target node)
                    const arrowDistance = 10;
                    arrow.position.set(
                        n2.position.x - direction.x * arrowDistance,
                        n2.position.y - direction.y * arrowDistance,
                        n2.position.z - direction.z * arrowDistance
                    );
                    
                    // Orient arrow to point from n1 to n2
                    arrow.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
                }
            });
        }
        
        renderer3d.render(scene3d, camera3d);
        
        // Minimap render REMOVED
    }
    // Start the interactive render loop
    renderInteractive();
    
    console.log('[3D] Interactive mode enabled - drag to pan, scroll to zoom');
}

// --- GRAPH SWITCHING FUNCTION ---
// Simple approach: destroy old graph completely, create new one from scratch
// No caching, no reuse - just destroy and rebuild
// This function is called when user clicks API/DEPENDENCIES/FILES buttons
// It uses the translator to get the correct graph data for that type and renders it
window.currentGraphType = 'api';
window.currentAnimationFrameId = null; // Track animation loop to stop it
window.currentRenderFrameId = null; // Track render loop to stop it
window.isSwitching = false; // Flag to prevent multiple simultaneous switches

function switchGraph3D(graphType) {
    console.log(`[SWITCH] Button clicked: Switching to ${graphType}`);
    console.log(`[SWITCH] Getting data from translator for type: ${graphType}`);
    
    if (graphType === window.currentGraphType) {
        console.log(`[SWITCH] Already showing ${graphType} - skipping`);
        return;
    }
    
    // Prevent multiple simultaneous switches
    if (window.isSwitching) {
        console.log(`[SWITCH] Already switching, ignoring duplicate call`);
        return;
    }
    window.isSwitching = true;
    
    const oldGraphType = window.currentGraphType; // Capture old type for revert

    
    // Stop ALL running animation loops immediately
    if (window.currentAnimationFrameId !== null) {
        cancelAnimationFrame(window.currentAnimationFrameId);
        window.currentAnimationFrameId = null;
        console.log('[SWITCH] Stopped animation loop');
    }
    
    if (window.currentRenderFrameId !== null) {
        cancelAnimationFrame(window.currentRenderFrameId);
        window.currentRenderFrameId = null;
        console.log('[SWITCH] Stopped render loop');
    }
    
    // Stop transition flag to prevent animation from continuing
    if (typeof transitionTo2DStarted !== 'undefined') {
        transitionTo2DStarted = true; // Stop any ongoing animation
    }
    
    // Update current graph type
    window.currentGraphType = graphType;
    
    // Clear translator cache to force fresh translation
    if (window.GraphDataTranslator) {
        window.GraphDataTranslator.clearCache();
    }
    
    // Completely destroy old 3D scene and all resources
    console.log('[SWITCH] Destroying old 3D scene...');
    if (scene3d) {
        // Remove all nodes and dispose resources
        const nodeCount = nodes3d.length;
        nodes3d.forEach((node, idx) => {
            if (node.userData && node.userData.labelSprite) {
                scene3d.remove(node.userData.labelSprite);
                if (node.userData.labelSprite.material) {
                    node.userData.labelSprite.material.dispose();
                }
            }
            if (node.geometry) node.geometry.dispose();
            if (node.material) {
                if (Array.isArray(node.material)) {
                    node.material.forEach(mat => mat.dispose());
                } else {
                    node.material.dispose();
                }
            }
            scene3d.remove(node);
        });
        nodes3d = [];
        console.log(`[SWITCH] Removed ${nodeCount} nodes`);
        
        // Remove edge lines
        if (edgeLines3d) {
            if (edgeLines3d.geometry) edgeLines3d.geometry.dispose();
            if (edgeLines3d.material) edgeLines3d.material.dispose();
            scene3d.remove(edgeLines3d);
            edgeLines3d = null;
            console.log('[SWITCH] Removed edge lines');
        }
        
        // Remove arrows
        if (window.arrowGroup3d) {
            const arrowCount = window.arrowGroup3d.children.length;
            window.arrowGroup3d.children.forEach(arrow => {
                if (arrow.geometry) arrow.geometry.dispose();
                if (arrow.material) arrow.material.dispose();
            });
            scene3d.remove(window.arrowGroup3d);
            window.arrowGroup3d = null;
            console.log(`[SWITCH] Removed ${arrowCount} arrows`);
        }
        
        // Remove Districts
        if (window.districtGroup3d) {
            const dCount = window.districtGroup3d.children.length;
            window.districtGroup3d.children.forEach(child => {
                if (child.geometry) child.geometry.dispose();
                if (child.material) {
                    if (Array.isArray(child.material)) child.material.forEach(m => m.dispose());
                    else child.material.dispose();
                }
            });
            scene3d.remove(window.districtGroup3d);
            window.districtGroup3d = null;
            console.log(`[SWITCH] Removed ${dCount} district elements`);
        }
    }
    
    // Cleanup Minimap REMOVED

    // Dispose renderer and clear canvas - MUST be done before creating new one
    if (typeof renderer3d !== 'undefined' && renderer3d) {
        const container = document.getElementById('canvas-3d');
        if (container && renderer3d.domElement && renderer3d.domElement.parentNode === container) {
            container.removeChild(renderer3d.domElement);
            console.log('[SWITCH] Removed renderer canvas from DOM');
        }
        renderer3d.dispose();
        renderer3d = null;
        console.log('[SWITCH] Disposed renderer');
    }
    
    // Clear scene completely
    if (typeof scene3d !== 'undefined' && scene3d) {
        while(scene3d.children.length > 0) {
            const child = scene3d.children[0];
            scene3d.remove(child);
            // Dispose geometries and materials
            if (child.geometry) child.geometry.dispose();
            if (child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach(mat => mat.dispose());
                } else {
                    child.material.dispose();
                }
            }
        }
        scene3d = null;
        console.log('[SWITCH] Cleared scene completely');
    }
    
    // Reset all 3D variables to ensure clean state
    nodes3d = [];
    edgeLines3d = null;
    window.arrowGroup3d = null;
    window.districtGroup3d = null;
    final2DPositions = new Map();
    transitionTo2DStarted = false;
    
    // CRITICAL: Set currentGraphType BEFORE calling init3DView
    // init3DView() uses window.currentGraphType to get data from translator
    window.currentGraphType = graphType;
    
    // Toggle Filter Context UI
    document.querySelectorAll('.filter-context').forEach(el => el.style.display = 'none');
    const filterId = (graphType === 'functions' || graphType === 'function_dependency') ? 'filter-context-functions' : `filter-context-${graphType}`;
    const filterContext = document.getElementById(filterId);
    if (filterContext) filterContext.style.display = 'block';
    
    // GRID VISIBILITY: Hide grid in City View (Disorienting in Ortho)
    if (window.gridMesh) {
        window.gridMesh.visible = (graphType !== 'dependency');
    }
    
    // Update UI Button visibility
    const camBtn = document.getElementById('btn-cam');
    const lensBtn = document.getElementById('btn-lens');
    
    if (camBtn) {
        camBtn.style.display = (graphType === 'files' || graphType === 'dependency') ? 'inline-block' : 'none';
        if (camera3d.isOrthographicCamera) {
            camBtn.textContent = '📐 CAM: ORTHO';
        } else {
            camBtn.textContent = '🎥 CAM: PERSP';
        }
    }
    
    if (lensBtn) {
        lensBtn.style.display = (graphType === 'files' || graphType === 'dependency') ? 'inline-block' : 'none';
    }
    
    console.log(`[SWITCH] Set window.currentGraphType to: ${graphType}`);
    
    // Verify translator has data for this type
    const testData = window.GraphDataTranslator.translate(graphType, true);
    console.log(`[SWITCH] Translator test: ${testData.nodes.length} balls, ${testData.edges.length} lines for ${graphType}`);
    
    if (testData.nodes.length === 0) {
        console.warn(`[SWITCH] No data available for ${graphType}`);
        
        // Show user-friendly message based on graph type
        let message = '';
        if (graphType === 'functions' || graphType === 'function_dependency') {
            message = 'No function data available. This view requires function calls and definitions to be detected in your codebase.';
        } else if (graphType === 'files' || graphType === 'dependency') {
            message = 'No file data available. This view requires import statements to be detected.';
        } else {
            message = `No ${graphType} data available in this report.`;
        }
        
        if (typeof showToast === 'function') {
            showToast(message);
        } else {
            alert(message);
        }
        window.currentGraphType = oldGraphType; // Revert type
        window.isSwitching = false;
        return;
    }
    
    // Create completely new 3D graph from scratch
    // init3DView() will use window.currentGraphType to get the correct data
    console.log(`[SWITCH] Calling init3DView() for ${graphType}...`);
    init3DView();
    
    // UPDATE STATS
    updateGraphStats();
    
    // Reset switching flag
    window.isSwitching = false;
    console.log('[SWITCH] Switch complete');
}

function updateGraphStats() {
    const graphData = window.GraphDataTranslator.translate(window.currentGraphType, false);
    
    // Project name
    if (graphData.report && graphData.report.project) {
        const projName = graphData.report.project.name || 'Unknown Project';
        const projEl = document.getElementById('project-name');
        if (projEl) projEl.textContent = projName;
    }
    
    // Node/Edge counts
    const nodeEl = document.getElementById('node-count');
    const edgeEl = document.getElementById('edge-count');
    if (nodeEl) nodeEl.textContent = graphData.nodes.length;
    if (edgeEl) edgeEl.textContent = graphData.edges.length;
    
    // High impact / Orphans
    const impactEl = document.getElementById('high-impact-count');
    const orphanEl = document.getElementById('orphaned-count');
    if (impactEl) impactEl.textContent = graphData.summary.high_impact || 0;
    if (orphanEl) orphanEl.textContent = graphData.summary.orphaned || 0;
}

window.resetView = function() {
    console.log('[3D] Resetting view...');
    if (window.currentGraphType === 'files' || window.currentGraphType === 'dependency') {
        // City View
        const dist = 200;
        // Use Orthographic or Perspective depending on current state? 
        // User didn't ask to switch camera mode, just reset position.
        // But init3DView sets it to dist, -dist, dist.
        camera3d.position.set(dist, -dist, dist);
        camera3d.lookAt(0,0,0);
        camera3d.zoom = 1;
        camera3d.updateProjectionMatrix();
    } else {
        // Galaxy View
        camera3d.position.set(0, 0, 1000); // Standard distance
        camera3d.lookAt(0, 0, 0);
        camera3d.zoom = 1;
        camera3d.updateProjectionMatrix();
    }
};

// Toggle Info Panel
window.toggleInfoPanel = function() {
    const panel = document.getElementById('info-panel');
    const toggle = document.getElementById('panel-toggle');
    
    if (panel && toggle) {
        panel.classList.toggle('hidden');
        if (panel.classList.contains('hidden')) {
            toggle.classList.add('visible');
        } else {
            toggle.classList.remove('visible');
        }
    }
};

// --- UI FUNCTIONS ---
window.toggleReportModal = function(e) {
    if (e && e.target !== e.currentTarget && e.target.id !== 'nav-report') return; 
    const modal = document.getElementById('report-modal');
    if (modal) {
        modal.classList.toggle('active');
        if (modal.classList.contains('active')) {
            // Populate JSON
            const report = window.embeddedGraphData ? window.embeddedGraphData.report : { error: 'No report data' };
            const jsonElem = document.getElementById('report-json');
            if (jsonElem) jsonElem.textContent = JSON.stringify(report, null, 2);
        }
    }
};

window.copyReport = function() {
    const jsonElem = document.getElementById('report-json');
    if (jsonElem) {
        navigator.clipboard.writeText(jsonElem.textContent).then(() => alert('Report copied to clipboard!'));
    }
};

window.closeCodeOverlay = function(e) {
    if (e && e.target !== e.currentTarget && !e.target.classList.contains('close-btn')) return;
    const modal = document.getElementById('code-overlay');
    if (modal) modal.classList.remove('active');
};

window.toggleFilterMenu = function() {
    const menu = document.getElementById('filter-menu');
    if (menu) menu.classList.toggle('active');
};

window.filterNodes = function(query) {
    // 3D Node Filtering
    query = query.toLowerCase();
    if (!window.nodes3d) return;
    
    window.nodes3d.forEach(node => {
        const id = (node.userData.id || '').toLowerCase();
        const visible = id.includes(query);
        node.visible = visible;
        // Also hide label/sprite if exists
        if (node.userData.labelSprite) node.userData.labelSprite.visible = visible;
    });
};

// Mouse Grid Effect
window.mouseX = 0; window.mouseY = 0;
document.addEventListener('mousemove', (e) => {
    window.mouseX = e.clientX;
    window.mouseY = e.clientY;
    document.body.style.setProperty('--mouse-x', e.clientX + 'px');
    document.body.style.setProperty('--mouse-y', e.clientY + 'px');
});

window.updateFilters = function(category, value) {
   // Toggle filter state
   if (!window.activeFilters[category]) window.activeFilters[category] = new Set();
   const set = window.activeFilters[category];
   if (set.has(value)) set.delete(value);
   else set.add(value);
   
   console.log('Active Filters:', window.activeFilters);
   // Trigger visibility update (implementation pending complexity)
   // For now, we just track state.
};

// --- LENS MODE TOGGLE ---
window.lensMode = 'default'; // default, debt, ownership, danger

window.toggleLensMode = function() {
    if (window.currentGraphType !== 'dependency') return;
    
    const modes = ['default', 'debt', 'ownership', 'danger'];
    let idx = modes.indexOf(window.lensMode);
    window.lensMode = modes[(idx + 1) % modes.length];
    
    console.log(`[LENS] Switched to ${window.lensMode}`);
    
    const btn = document.getElementById('btn-lens');
    if(btn) btn.textContent = `🔍 LENS: ${window.lensMode.toUpperCase()}`;
    
    // Re-apply colors to all nodes
    if(window.nodes3d) {
         window.nodes3d.forEach(node => {
              const data = window.GraphDataTranslator.translate('dependency', false).nodes.find(n => n.id === node.userData.id);
              if(data) {
                   // Logic for different lenses
                   let color = new THREE.Color(0x00F0FF); // Default
                   
                   if (window.lensMode === 'default') {
                       // Original logic: Type based
                       // We need to re-parse the hex color from somewhere? 
                       // Ideally store original color in userData
                       // For now, simplistic fallback:
                       if (data.id.endsWith('.py')) color.setHex(0x00F0FF);
                       else if (data.id.endsWith('.js')) color.setHex(0xFFE600);
                       else color.setHex(0x6b7280);
                   } else if (window.lensMode === 'debt') {
                       // Complexity Gradient (Green -> Red)
                       const complexity = (data.function_count || 0) + (data.endpoint_count || 0);
                       // Map 0-100 to Green-Red
                       const t = Math.min(1, complexity / 100);
                       color.setHSL(0.33 * (1 - t), 1.0, 0.5); 
                   } else if (window.lensMode === 'ownership') {
                       // Random color per "owner" (mocked)
                       // Hash the ID to pick a color?
                       const hash = data.id.length * 123; 
                       color.setHSL((hash % 360) / 360, 0.8, 0.5);
                   } else if (window.lensMode === 'danger') {
                       // High Complexity + Low Tests (Mocked)
                       // If complex, turn RED. Else Grey.
                       const complexity = (data.function_count || 0);
                       if (complexity > 50) color.setHex(0xFF0000); // DANGER
                       else color.setHex(0x333333); // Safe
                   }
                   
                   // Apply color to material
                   if(node.material) {
                       node.material.color = color;
                       node.material.emissive = color;
                       // Emissive intensity might need adjustment too
                   }
              }
         });
    }
};

// Make switchGraph3D available globally so button clicks can call it
// This avoids naming conflicts with the template's switchGraph function
window.switchGraph3D = switchGraph3D;

