import * as THREE from 'three';

// Scene setup
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0e27);

// Camera
const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);
camera.position.z = 4;

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.getElementById('canvas-container').appendChild(renderer.domElement);

// Globe parameters
const radius = 2;
const segments = 64;

// Create transparent globe
const globeGeometry = new THREE.SphereGeometry(radius, segments, segments);
const globeMaterial = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.1,
    wireframe: false,
    side: THREE.DoubleSide
});
const globe = new THREE.Mesh(globeGeometry, globeMaterial);
scene.add(globe);

// Create atmosphere glow
const atmosphereGeometry = new THREE.SphereGeometry(radius * 1.15, segments, segments);
const atmosphereMaterial = new THREE.ShaderMaterial({
    vertexShader: `
        varying vec3 vNormal;
        void main() {
            vNormal = normalize(normalMatrix * normal);
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `,
    fragmentShader: `
        varying vec3 vNormal;
        void main() {
            float intensity = pow(0.6 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
            gl_FragColor = vec4(0.3, 0.6, 1.0, 1.0) * intensity;
        }
    `,
    side: THREE.BackSide,
    blending: THREE.AdditiveBlending,
    transparent: true
});
const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
atmosphere.visible = false;
scene.add(atmosphere);

// Create inner glow
const glowGeometry = new THREE.SphereGeometry(radius * 1.05, segments, segments);
const glowMaterial = new THREE.ShaderMaterial({
    vertexShader: `
        varying vec3 vNormal;
        void main() {
            vNormal = normalize(normalMatrix * normal);
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `,
    fragmentShader: `
        varying vec3 vNormal;
        void main() {
            float intensity = pow(0.8 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 3.0);
            gl_FragColor = vec4(0.4, 1.0, 0.8, 1.0) * intensity;
        }
    `,
    side: THREE.FrontSide,
    blending: THREE.AdditiveBlending,
    transparent: true
});
const glow = new THREE.Mesh(glowGeometry, glowMaterial);
glow.visible = false;
scene.add(glow);

// Borders group
const bordersGroup = new THREE.Group();
scene.add(bordersGroup);

// Markers group
const markersGroup = new THREE.Group();
scene.add(markersGroup);

// Connections group
const connectionsGroup = new THREE.Group();
scene.add(connectionsGroup);

// Storage
const borderLines = [];
const markers = [];
const connections = [];
let countryData = new Map();
let selectedCountry = null;

// Border colors
const borderColors = [
    0xff6b6b, 0x4ecdc4, 0x45b7d1, 0xf9ca24, 0x6c5ce7,
    0xa29bfe, 0xfd79a8, 0xfdcb6e, 0xe17055, 0x00b894
];

// State
let state = {
    autoRotate: true,
    rotationSpeed: 0.001,
    showMarkers: false,
    showConnections: false,
    showGlow: false,
    showAtmosphere: false,
    zoom: 1,
    isDragging: false,
    previousMousePosition: { x: 0, y: 0 },
    mouseDownPosition: { x: 0, y: 0 }
};

// FPS counter
let lastTime = performance.now();
let frames = 0;
let fps = 0;

// Utility functions
function latLonToVector3(lat, lon, r) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    const x = -(r * Math.sin(phi) * Math.cos(theta));
    const z = r * Math.sin(phi) * Math.sin(theta);
    const y = r * Math.cos(phi);
    return new THREE.Vector3(x, y, z);
}

function normalizeCountryName(name) {
    if (!name) return '';
    return name.toString().toLowerCase().trim();
}

function getCountryColorIndex(countryName) {
    if (!countryName) return 0;
    const normalized = normalizeCountryName(countryName);
    let hash = 0;
    for (let i = 0; i < normalized.length; i++) {
        hash = normalized.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash) % borderColors.length;
}

function createBorderKey(points) {
    if (points.length < 2) return null;
    const first = points[0];
    const last = points[points.length - 1];
    const key = `${Math.round(first.x * 1000)},${Math.round(first.y * 1000)},${Math.round(first.z * 1000)}-${Math.round(last.x * 1000)},${Math.round(last.y * 1000)},${Math.round(last.z * 1000)}`;
    return key;
}

// Load country borders
async function loadCountryBorders() {
    try {
        const response = await fetch('https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson');
        const geoData = await response.json();
        
        const countryColorMap = new Map();
        const drawnBorders = new Map();
        
        function getCountryIdentifier(feature) {
            return feature.properties?.ISO_A3 || feature.properties?.ISO_A2 || 
                   feature.properties?.NAME || feature.properties?.name || 
                   feature.properties?.ADMIN || feature.id?.toString() || '';
        }
        
        // Collect country data
        geoData.features.forEach((feature) => {
            const countryId = getCountryIdentifier(feature);
            const normalized = normalizeCountryName(countryId);
            
            if (normalized && !countryColorMap.has(normalized)) {
                const colorIndex = getCountryColorIndex(normalized);
                countryColorMap.set(normalized, borderColors[colorIndex % borderColors.length]);
                
                // Store country data
                countryData.set(normalized, {
                    name: feature.properties?.NAME || feature.properties?.name || countryId,
                    code: feature.properties?.ISO_A3 || feature.properties?.ISO_A2 || '',
                    region: feature.properties?.REGION_UN || feature.properties?.SUBREGION || 'Unknown',
                    population: Math.floor(Math.random() * 100000000), // Mock data
                    gdp: Math.floor(Math.random() * 1000000000000) // Mock data
                });
            }
        });
        
        // Create borders
        geoData.features.forEach((feature) => {
            const geometryType = feature.geometry.type;
            const coordinates = feature.geometry.coordinates;
            const countryId = getCountryIdentifier(feature);
            const normalized = normalizeCountryName(countryId);
            const color = countryColorMap.get(normalized) || borderColors[0];
            
            const processRing = (ring) => {
                const points = ring.map(([lon, lat]) => 
                    latLonToVector3(lat, lon, radius * 1.002)
                );
                
                const borderKey = createBorderKey(points);
                const reverseKey = createBorderKey([...points].reverse());
                
                if (borderKey && (drawnBorders.has(borderKey) || drawnBorders.has(reverseKey))) {
                    return;
                }
                
                if (borderKey) {
                    drawnBorders.set(borderKey, true);
                }
                
                const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
                const lineMaterial = new THREE.LineBasicMaterial({
                    color: color,
                    linewidth: 1,
                    transparent: true,
                    opacity: 0.9,
                    depthTest: false,
                    depthWrite: false
                });
                const line = new THREE.Line(lineGeometry, lineMaterial);
                line.userData = { country: normalized, countryName: countryData.get(normalized)?.name };
                bordersGroup.add(line);
                
                borderLines.push({
                    line: line,
                    originalPoints: points,
                    baseColor: color,
                    baseOpacity: 0.9,
                    country: normalized
                });
            };
            
            if (geometryType === 'Polygon') {
                coordinates.forEach(ring => processRing(ring));
            } else if (geometryType === 'MultiPolygon') {
                coordinates.forEach(polygon => {
                    polygon.forEach(ring => processRing(ring));
                });
            }
        });
        
        document.getElementById('country-count').textContent = countryData.size;
        document.getElementById('loading').style.display = 'none';
    } catch (error) {
        console.error('Error loading country borders:', error);
        document.getElementById('loading').innerHTML = '<div class="spinner"></div><div>Error loading data. Please refresh.</div>';
    }
}

// Create marker
function createMarker(lat, lon, label, color = 0x64ffda) {
    const position = latLonToVector3(lat, lon, radius * 1.05);
    
    // Marker sphere
    const markerGeometry = new THREE.SphereGeometry(0.03, 16, 16);
    const markerMaterial = new THREE.MeshBasicMaterial({ color: color });
    const marker = new THREE.Mesh(markerGeometry, markerMaterial);
    marker.position.copy(position);
    
    // Glow effect
    const glowGeometry = new THREE.SphereGeometry(0.05, 16, 16);
    const glowMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.3
    });
    const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
    glowMesh.position.copy(position);
    
    marker.userData = { label: label, lat: lat, lon: lon };
    glowMesh.userData = { label: label, lat: lat, lon: lon };
    
    markersGroup.add(marker);
    markersGroup.add(glowMesh);
    
    markers.push({ marker, glow: glowMesh, label, lat, lon });
    
    updateMarkerCount();
    return marker;
}

// Create connection arc
function createConnection(lat1, lon1, lat2, lon2, color = 0xff6b6b) {
    const start = latLonToVector3(lat1, lon1, radius * 1.02);
    const end = latLonToVector3(lat2, lon2, radius * 1.02);
    
    const distance = start.distanceTo(end);
    const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
    mid.normalize().multiplyScalar(radius * 1.02 + distance * 0.3);
    
    const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
    const points = curve.getPoints(50);
    
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.6,
        linewidth: 2
    });
    
    const line = new THREE.Line(geometry, material);
    connectionsGroup.add(line);
    connections.push(line);
    
    return line;
}

// Add some sample markers and connections
function addSampleData() {
    // Major cities
    const cities = [
        { lat: 40.7128, lon: -74.0060, label: 'New York' },
        { lat: 51.5074, lon: -0.1278, label: 'London' },
        { lat: 35.6762, lon: 139.6503, label: 'Tokyo' },
        { lat: -33.8688, lon: 151.2093, label: 'Sydney' },
        { lat: 48.8566, lon: 2.3522, label: 'Paris' },
        { lat: 55.7558, lon: 37.6173, label: 'Moscow' }
    ];
    
    cities.forEach(city => {
        createMarker(city.lat, city.lon, city.label);
    });
    
    // Create connections between cities
    for (let i = 0; i < cities.length - 1; i++) {
        const city1 = cities[i];
        const city2 = cities[i + 1];
        createConnection(city1.lat, city1.lon, city2.lat, city2.lon);
    }
}

// Mouse interaction
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const tooltip = document.getElementById('tooltip');
const infoPanel = document.getElementById('info-panel');

function onMouseDown(event) {
    state.isDragging = true;
    state.previousMousePosition = { x: event.clientX, y: event.clientY };
    state.mouseDownPosition = { x: event.clientX, y: event.clientY };
}

function onMouseMove(event) {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
    
    if (state.isDragging) {
        const deltaX = event.clientX - state.previousMousePosition.x;
        const deltaY = event.clientY - state.previousMousePosition.y;
        
        globe.rotation.y += deltaX * 0.01;
        bordersGroup.rotation.y += deltaX * 0.01;
        markersGroup.rotation.y += deltaX * 0.01;
        connectionsGroup.rotation.y += deltaX * 0.01;
        atmosphere.rotation.y += deltaX * 0.01;
        glow.rotation.y += deltaX * 0.01;
        
        globe.rotation.x += deltaY * 0.01;
        bordersGroup.rotation.x += deltaY * 0.01;
        markersGroup.rotation.x += deltaY * 0.01;
        connectionsGroup.rotation.x += deltaY * 0.01;
        atmosphere.rotation.x += deltaY * 0.01;
        glow.rotation.x += deltaY * 0.01;
        
        state.previousMousePosition = { x: event.clientX, y: event.clientY };
        renderer.domElement.style.cursor = 'grabbing';
        return;
    }
    
    // Tooltip for markers
    raycaster.setFromCamera(mouse, camera);
    const markerIntersects = raycaster.intersectObjects(markersGroup.children);
    
    if (markerIntersects.length > 0) {
        const marker = markerIntersects[0].object;
        if (marker.userData.label) {
            tooltip.textContent = marker.userData.label;
            tooltip.style.display = 'block';
            tooltip.style.left = event.clientX + 10 + 'px';
            tooltip.style.top = event.clientY + 10 + 'px';
            renderer.domElement.style.cursor = 'pointer';
            return;
        }
    }
    
    // Tooltip for borders
    const borderIntersects = raycaster.intersectObjects(bordersGroup.children);
    if (borderIntersects.length > 0) {
        const border = borderIntersects[0].object;
        if (border.userData.countryName) {
            tooltip.textContent = border.userData.countryName;
            tooltip.style.display = 'block';
            tooltip.style.left = event.clientX + 10 + 'px';
            tooltip.style.top = event.clientY + 10 + 'px';
            renderer.domElement.style.cursor = 'pointer';
            return;
        }
    }
    
    const globeIntersects = raycaster.intersectObject(globe);
    if (globeIntersects.length > 0) {
        renderer.domElement.style.cursor = 'grab';
    } else {
        renderer.domElement.style.cursor = 'default';
    }
    
    tooltip.style.display = 'none';
}

function onMouseUp(event) {
    if (state.isDragging) {
        // Check if this was a click (minimal movement) or a drag
        const dragDistance = Math.sqrt(
            Math.pow(event.clientX - state.mouseDownPosition.x, 2) +
            Math.pow(event.clientY - state.mouseDownPosition.y, 2)
        );
        
        // If movement was less than 5 pixels, treat it as a click
        if (dragDistance < 5) {
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
            
            raycaster.setFromCamera(mouse, camera);
            
            // Check for marker clicks
            const markerIntersects = raycaster.intersectObjects(markersGroup.children);
            if (markerIntersects.length > 0) {
                const marker = markerIntersects[0].object;
                if (marker.userData.label) {
                    showInfo(marker.userData.label, `Lat: ${marker.userData.lat.toFixed(2)}, Lon: ${marker.userData.lon.toFixed(2)}`);
                    state.isDragging = false;
                    renderer.domElement.style.cursor = 'default';
                    return;
                }
            }
            
            // Check for border clicks - use world space raycasting
            const borderIntersects = raycaster.intersectObjects(bordersGroup.children, true);
            if (borderIntersects.length > 0) {
                const border = borderIntersects[0].object;
                if (border.userData.country) {
                    highlightCountry(border.userData.country);
                    const data = countryData.get(border.userData.country);
                    if (data) {
                        showCountryInfo(data);
                    }
                }
            }
        }
    }
    
    state.isDragging = false;
    renderer.domElement.style.cursor = 'default';
}

// UI Functions
function showInfo(title, content) {
    document.getElementById('country-name').textContent = title;
    document.getElementById('country-code').textContent = '';
    document.getElementById('country-region').textContent = '';
    document.getElementById('country-data').textContent = content;
    infoPanel.classList.add('visible');
}

function showCountryInfo(data) {
    document.getElementById('country-name').textContent = data.name;
    document.getElementById('country-code').textContent = `Code: ${data.code}`;
    document.getElementById('country-region').textContent = `Region: ${data.region}`;
    document.getElementById('country-data').textContent = 
        `Population: ${(data.population / 1000000).toFixed(1)}M | GDP: $${(data.gdp / 1000000000).toFixed(1)}B`;
    infoPanel.classList.add('visible');
}

function highlightCountry(countryId) {
    // Reset previous highlight
    borderLines.forEach(bl => {
        bl.line.material.opacity = bl.baseOpacity;
        bl.line.material.color.setHex(bl.baseColor);
    });
    
    // Highlight selected country
    borderLines.forEach(bl => {
        if (bl.country === countryId) {
            bl.line.material.opacity = 1.0;
            bl.line.material.color.setHex(0xffffff);
        }
    });
    
    selectedCountry = countryId;
}

function updateMarkerCount() {
    document.getElementById('marker-count').textContent = markers.length;
}

// Search functionality
function setupSearch() {
    const searchInput = document.getElementById('country-search');
    const searchResults = document.getElementById('search-results');
    
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        
        const matches = Array.from(countryData.entries())
            .filter(([key, data]) => 
                data.name.toLowerCase().includes(query) || 
                data.code.toLowerCase().includes(query)
            )
            .slice(0, 10);
        
        if (matches.length === 0) {
            searchResults.style.display = 'none';
            return;
        }
        
        searchResults.innerHTML = matches.map(([key, data]) => 
            `<div class="search-result-item" data-country="${key}">${data.name} (${data.code})</div>`
        ).join('');
        
        searchResults.style.display = 'block';
        
        // Add click handlers
        searchResults.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const countryId = item.dataset.country;
                highlightCountry(countryId);
                const data = countryData.get(countryId);
                if (data) {
                    showCountryInfo(data);
                }
                searchResults.style.display = 'none';
                searchInput.value = '';
            });
        });
    });
    
    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });
}

// Control panel setup
function setupControls() {
    const speedSlider = document.getElementById('rotation-speed');
    const speedValue = document.getElementById('speed-value');
    speedSlider.addEventListener('input', (e) => {
        const speed = parseFloat(e.target.value);
        state.rotationSpeed = speed * 0.001;
        speedValue.textContent = speed.toFixed(1) + 'x';
    });
    
    const zoomSlider = document.getElementById('zoom-level');
    const zoomValue = document.getElementById('zoom-value');
    zoomSlider.addEventListener('input', (e) => {
        const zoom = parseFloat(e.target.value);
        state.zoom = zoom;
        camera.position.z = 4 / zoom;
        zoomValue.textContent = zoom.toFixed(1) + 'x';
    });
    
    document.getElementById('toggle-rotation').addEventListener('click', (e) => {
        state.autoRotate = !state.autoRotate;
        e.target.classList.toggle('active');
    });
    
    document.getElementById('reset-view').addEventListener('click', () => {
        globe.rotation.set(0, 0, 0);
        bordersGroup.rotation.set(0, 0, 0);
        markersGroup.rotation.set(0, 0, 0);
        connectionsGroup.rotation.set(0, 0, 0);
        atmosphere.rotation.set(0, 0, 0);
        glow.rotation.set(0, 0, 0);
        camera.position.z = 4;
        state.zoom = 1;
        zoomSlider.value = 1;
        zoomValue.textContent = '1.0x';
    });
    
    document.getElementById('toggle-markers').addEventListener('click', (e) => {
        state.showMarkers = !state.showMarkers;
        markersGroup.visible = state.showMarkers;
        e.target.classList.toggle('active');
        if (state.showMarkers && markers.length === 0) {
            addSampleData();
        }
    });
    
    document.getElementById('toggle-connections').addEventListener('click', (e) => {
        state.showConnections = !state.showConnections;
        connectionsGroup.visible = state.showConnections;
        e.target.classList.toggle('active');
        if (state.showConnections && connections.length === 0 && markers.length > 0) {
            // Connections already created with markers
        }
    });
    
    document.getElementById('toggle-glow').addEventListener('click', (e) => {
        state.showGlow = !state.showGlow;
        glow.visible = state.showGlow;
        e.target.classList.toggle('active');
    });
    
    document.getElementById('toggle-atmosphere').addEventListener('click', (e) => {
        state.showAtmosphere = !state.showAtmosphere;
        atmosphere.visible = state.showAtmosphere;
        e.target.classList.toggle('active');
    });
    
    document.getElementById('add-marker').addEventListener('click', () => {
        const lat = (Math.random() - 0.5) * 160;
        const lon = (Math.random() - 0.5) * 360;
        const colors = [0x64ffda, 0xff6b6b, 0x4ecdc4, 0xf9ca24, 0x6c5ce7];
        const color = colors[Math.floor(Math.random() * colors.length)];
        createMarker(lat, lon, `Marker ${markers.length + 1}`, color);
        
        if (!state.showMarkers) {
            state.showMarkers = true;
            markersGroup.visible = true;
            document.getElementById('toggle-markers').classList.add('active');
        }
    });
    
    document.getElementById('close-info').addEventListener('click', () => {
        infoPanel.classList.remove('visible');
    });
}

// Event listeners
renderer.domElement.addEventListener('mousedown', onMouseDown);
renderer.domElement.addEventListener('mousemove', onMouseMove);
renderer.domElement.addEventListener('mouseup', onMouseUp);
renderer.domElement.addEventListener('mouseleave', onMouseUp);

// Border opacity update
function updateBorderOpacity() {
    const cameraDirection = new THREE.Vector3();
    camera.getWorldDirection(cameraDirection);
    cameraDirection.multiplyScalar(-1);
    
    borderLines.forEach((borderLine) => {
        const positions = borderLine.line.geometry.attributes.position;
        if (!positions || positions.count === 0) return;
        
        let midpoint = new THREE.Vector3();
        for (let i = 0; i < positions.count; i++) {
            const point = new THREE.Vector3();
            point.fromBufferAttribute(positions, i);
            borderLine.line.localToWorld(point);
            midpoint.add(point);
        }
        midpoint.divideScalar(positions.count);
        
        const directionToMidpoint = midpoint.clone().normalize();
        const dotProduct = directionToMidpoint.dot(cameraDirection);
        
        const dimOpacity = 0.2;
        const opacityRange = borderLine.baseOpacity - dimOpacity;
        const newOpacity = dimOpacity + (dotProduct + 1) / 2 * opacityRange;
        
        borderLine.line.material.opacity = Math.max(dimOpacity, Math.min(borderLine.baseOpacity, newOpacity));
    });
}

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    
    // FPS counter
    frames++;
    const currentTime = performance.now();
    if (currentTime >= lastTime + 1000) {
        fps = Math.round((frames * 1000) / (currentTime - lastTime));
        document.getElementById('fps').textContent = fps;
        frames = 0;
        lastTime = currentTime;
    }
    
    // Auto-rotate
    if (state.autoRotate && !state.isDragging) {
        globe.rotation.y += state.rotationSpeed;
        bordersGroup.rotation.y += state.rotationSpeed;
        markersGroup.rotation.y += state.rotationSpeed;
        connectionsGroup.rotation.y += state.rotationSpeed;
        atmosphere.rotation.y += state.rotationSpeed;
        glow.rotation.y += state.rotationSpeed;
    }
    
    // Animate marker glow
    markers.forEach((m, i) => {
        const time = Date.now() * 0.001;
        m.glow.material.opacity = 0.3 + Math.sin(time * 2 + i) * 0.2;
        m.glow.scale.setScalar(1 + Math.sin(time * 2 + i) * 0.2);
    });
    
    updateBorderOpacity();
    renderer.render(scene, camera);
}

// Window resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

// Initialize
loadCountryBorders();
setupControls();
setupSearch();
animate();
