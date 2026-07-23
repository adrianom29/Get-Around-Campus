//const API = 'http://127.0.0.1:5000';

const API = 'https://AdrianoM29.pythonanywhere.com';
let currentCampus = null;
let namedNodes = [];
let startNode = null, endNode = null, pathLayer = null;

const map = L.map('map').setView([43.773361, -79.502361], 16);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© Contributors of OpenStreetMap'
}).addTo(map);

const startMarker   = L.circleMarker([0,0], {radius:8, color:'#1D9E75', fillColor:'#1D9E75', fillOpacity:1});    

const finishIcon = L.icon({
    iconUrl:      '/static/images/finish.png',
    iconSize:     [30, 30], // size of the icon
    iconAnchor:   [2, 25], // bottom tip of the flag pole, so it points at the node
});
const endMarker = L.marker([0,0], {icon: finishIcon});

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

}

map.on('click', async (e) => {
    if (!currentCampus || pathLayer) return;
    const {lat, lng} = e.latlng;
    const res = await fetch(`${API}/${currentCampus}/nearest?lat=${lat}&lng=${lng}`);
    const node = await res.json();
    const info = node.name?.trim() || `${lat.toFixed(5)}, ${lng.toFixed(5)}`; //${node.id};
    const slot = (startNode && !endNode) ? 'end' : 'start';
    drawNode(node, info, slot);
});

function drawNode(node, info, slot) {
    if (pathLayer) return;
    if (slot === 'start') {
        startNode = node;
        startMarker.setLatLng([node.lat, node.lng]).addTo(map);
        document.getElementById('start-label').textContent = `Start:`;
        document.getElementById('search-start').value = info;
    } else {
        endNode = node;
        endMarker.setLatLng([node.lat, node.lng]).addTo(map);
        document.getElementById('end-label').textContent = `End:`;
        document.getElementById('search-end').value = info;
    }
}

async function findPath() {
    if (!startNode || !endNode || !currentCampus) return;
    const res = await fetch(`${API}/${currentCampus}/path?src=${startNode.id}&dst=${endNode.id}`);
    const data = await res.json();
    if (pathLayer) map.removeLayer(pathLayer);
    const coords = data.path.map(p => [p.lat, p.lng]);
    pathLayer = L.polyline(coords, {color:'#2db2f0', weight:5, opacity:0.85}).addTo(map);
    map.fitBounds(pathLayer.getBounds(), {padding:[40,40]});
    document.getElementById('distance').textContent = `Distance: ${data.distance} m`;
    const time = Math.round(data.distance / 80);
    document.getElementById('time').textContent = `Time: ${time} mins`;
    startMarker.bringToFront();
    endMarker.bringToFront();
}

function clearPath() {
    if (pathLayer) { map.removeLayer(pathLayer); pathLayer = null; }
    if (map.hasLayer(startMarker)) map.removeLayer(startMarker);
    if (map.hasLayer(endMarker))   map.removeLayer(endMarker);
    startNode = endNode = null;
    document.getElementById('start-label').textContent = 'Start:';
    document.getElementById('end-label').textContent   = 'End:';
    document.getElementById('search-start').value = '';
    document.getElementById('search-end').value = '';
    document.getElementById('suggestions-start').style.display = 'none';
    document.getElementById('suggestions-end').style.display = 'none';
    document.getElementById('distance').textContent = '';
    document.getElementById('time').textContent = '';
}

function searchBuildings(query, slot) {
    const box = document.getElementById(`suggestions-${slot}`);
    if (!query) { box.style.display = 'none'; return; }
    const matches = namedNodes.filter(n => n.name.toLowerCase().includes(query.toLowerCase()));
    if (!matches.length) { box.style.display = 'none'; return; }
    box.innerHTML = matches.map(n =>
        `<div class="suggestion" onclick="selectBuilding(${n.id}, '${slot}')">${n.name}</div>`
    ).join('');
    box.style.display = 'block';
}

function selectBuilding(id, slot) {
    if (pathLayer) return;
    const node = namedNodes.find(n => n.id === id);
    document.getElementById(`suggestions-${slot}`).style.display = 'none';
    drawNode(node, node.name, slot);
    map.setView([node.lat, node.lng], 18);
}

function swapStartAndEnd() {
    if (!startNode || !endNode || pathLayer) return;
    const tempNode = endNode;
    const tempText = document.getElementById('end-label').textContent.slice(5);
    const startText = document.getElementById('start-label').textContent.slice(7);
    endNode = startNode;
    endMarker.setLatLng([startNode.lat, startNode.lng]);
    document.getElementById('end-label').textContent = `End: ${startText}`;
    document.getElementById('search-end').value = startText;
    startNode = tempNode;
    startMarker.setLatLng([tempNode.lat, tempNode.lng]);
    document.getElementById('start-label').textContent = `Start: ${tempText}`;
    document.getElementById('search-start').value = tempText;
}

loadCampuses();