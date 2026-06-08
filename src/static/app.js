//const API = 'http://127.0.0.1:5000';
//const API = 'https://get-around-campus.onrender.com';
const API = 'https://get-around-campus.fly.dev';
let currentCampus = null;
let namedNodes = [];
let startNode = null, endNode = null, pathLayer = null, clickCount = 0;

const map = L.map('map').setView([43.773361, -79.502361], 16);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© Contributors of OpenStreetMap'
}).addTo(map);
    
const startMarker = L.circleMarker([0,0], {radius:8, color:'#E24B4A', fillColor:'#E24B4A', fillOpacity:1});
const endMarker   = L.circleMarker([0,0], {radius:8, color:'#1D9E75', fillColor:'#1D9E75', fillOpacity:1});

async function loadCampuses() {
    const res = await fetch(`${API}/campuses`);
    const campuses = await res.json();
    const sel = document.getElementById('campus-select');
    sel.innerHTML = campuses.map(c =>
        `<option value="${c.key}">${c.name}</option>`
    ).join('');
    await switchCampus(campuses[0].key);
}

async function switchCampus(key) {
    currentCampus = key;
    clearPath();

    const res = await fetch(`${API}/campuses`);
    const campuses = await res.json();
    const campus = campuses.find(c => c.key === key);
    if (campus) map.setView(campus.center, campus.zoom);

    const nr = await fetch(`${API}/${key}/named-nodes`);
    namedNodes = await nr.json();

    document.getElementById('search').value = '';
    document.getElementById('suggestions').style.display = 'none';
}

map.on('click', async (e) => {
    if (!currentCampus) return;
    const {lat, lng} = e.latlng;
    const res = await fetch(`${API}/${currentCampus}/nearest?lat=${lat}&lng=${lng}`); 
    const node = await res.json();
    const info = node.name?.trim() || `${lat.toFixed(5)}, ${lng.toFixed(5)}`; //${node.id};
    drawNode(node, info);
});

function drawNode(node, info) {
    if (clickCount % 2 === 0) {
        if (pathLayer) clearPath();
        startNode = node;
        startMarker.setLatLng([node.lat, node.lng]).addTo(map);
        document.getElementById('start-label').textContent = `Start: ${info}`;
    } else {
        if (pathLayer) { clearPath(); drawNode(node, info); return; }
        endNode = node;
        endMarker.setLatLng([node.lat, node.lng]).addTo(map);
        document.getElementById('end-label').textContent = `End: ${info}`;
    }
    clickCount++;
}

async function findPath() {
    if (!startNode || !endNode || !currentCampus) return;
    const res = await fetch(`${API}/${currentCampus}/path?src=${startNode.id}&dst=${endNode.id}`);
    const data = await res.json();
    if (pathLayer) map.removeLayer(pathLayer);
    const coords = data.path.map(p => [p.lat, p.lng]);
    pathLayer = L.polyline(coords, {color:'#1D9E75', weight:5, opacity:0.85}).addTo(map);
    map.fitBounds(pathLayer.getBounds(), {padding:[40,40]});
    document.getElementById('result').textContent = `Distance: ${data.distance} m`;
}

function clearPath() {
    if (pathLayer) { map.removeLayer(pathLayer); pathLayer = null; }
    if (map.hasLayer(startMarker)) map.removeLayer(startMarker);
    if (map.hasLayer(endMarker))   map.removeLayer(endMarker);
    startNode = endNode = null;
    clickCount = 0;
    document.getElementById('start-label').textContent = 'Start: —';
    document.getElementById('end-label').textContent   = 'End: —';
    document.getElementById('result').textContent      = '';
}

function searchBuildings(query) {
    const box = document.getElementById('suggestions');
    if (!query) { box.style.display = 'none'; return; }
    const matches = namedNodes.filter(n => n.name.toLowerCase().includes(query.toLowerCase()));
    if (!matches.length) { box.style.display = 'none'; return; }
    box.innerHTML = matches.map(n =>
        `<div class="suggestion" onclick="selectBuilding(${n.id})">${n.name}</div>`
    ).join('');
    box.style.display = 'block';
}

function selectBuilding(id) {
    const node = namedNodes.find(n => n.id === id);
    document.getElementById('suggestions').style.display = 'none';
    document.getElementById('search').value = node.name;
    drawNode(node, node.name);
    map.setView([node.lat, node.lng], 18);
}

function swapStartAndEnd() {
    if (!startNode || !endNode) return;
    const tempNode = endNode;
    const tempText = document.getElementById('end-label').textContent.slice(5);
    endNode = startNode;
    endMarker.setLatLng([startNode.lat, startNode.lng]);
    document.getElementById('end-label').textContent = `End: ${document.getElementById('start-label').textContent.slice(7)}`;
    startNode = tempNode;
    startMarker.setLatLng([tempNode.lat, tempNode.lng]);
    document.getElementById('start-label').textContent = `Start: ${tempText}`;
}

loadCampuses();