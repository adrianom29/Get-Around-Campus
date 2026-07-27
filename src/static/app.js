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
const userMarker = L.circleMarker([0,0], {radius:7, color:'#ffffff', weight:2, fillColor:'#4285F4', fillOpacity:1});

function getUserLocation() {
    return new Promise(resolve => {
        if (!navigator.geolocation) { resolve(null); return; }
        const timer = setTimeout(() => resolve(null), 10000);
        navigator.geolocation.getCurrentPosition(
            pos => { clearTimeout(timer); resolve({lat: pos.coords.latitude, lng: pos.coords.longitude}); },
            () => { clearTimeout(timer); resolve(null); },
            {timeout: 8000}
        );
    });
}

function nearestCampusKey(campuses, loc) {
    return campuses.reduce((best, c) => {
        const d = (c.center[0]-loc.lat)**2 + (c.center[1]-loc.lng)**2;
        return d < best.d ? {key: c.key, d} : best;
    }, {key: campuses[0].key, d: Infinity}).key;
}

function trackUserLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.watchPosition(
        pos => {
            const {latitude: lat, longitude: lng} = pos.coords;
            userMarker.setLatLng([lat, lng]);
            if (!map.hasLayer(userMarker)) userMarker.addTo(map);
        },
        () => {},
        {enableHighAccuracy: true, maximumAge: 5000}
    );
}

async function loadCampuses() {
    const res = await fetch(`${API}/campuses`);
    const campuses = await res.json();
    const sel = document.getElementById('campus-select');
    sel.innerHTML = campuses.map(c =>
        `<option value="${c.key}">${c.name}</option>`
    ).join('');

    const userLoc = await getUserLocation();
    const initialKey = userLoc ? nearestCampusKey(campuses, userLoc) : campuses[0].key;
    sel.value = initialKey;
    await switchCampus(initialKey);

    if (userLoc) {
        userMarker.setLatLng([userLoc.lat, userLoc.lng]).addTo(map);
    }
    trackUserLocation();
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
    const rows = [];
    if (!query && slot === 'start' && map.hasLayer(userMarker)) {
        rows.push(`<div class="suggestion" onclick="selectUserLocation()">Your location</div>`);
    }
    if (query) {
        const matches = namedNodes.filter(n => n.name.toLowerCase().includes(query.toLowerCase()));
        rows.push(...matches.map(n => `<div class="suggestion" onclick="selectBuilding(${n.id}, '${slot}')">${n.name}</div>`));
    }
    if (!rows.length) { box.style.display = 'none'; return; }
    box.innerHTML = rows.join('');
    box.style.display = 'block';
}

function selectBuilding(id, slot) {
    if (pathLayer) return;
    const node = namedNodes.find(n => n.id === id);
    document.getElementById(`suggestions-${slot}`).style.display = 'none';
    drawNode(node, node.name, slot);
    map.setView([node.lat, node.lng], 18);
}

async function selectUserLocation() {
    if (pathLayer || !currentCampus || !map.hasLayer(userMarker)) return;
    document.getElementById('suggestions-start').style.display = 'none';
    const {lat, lng} = userMarker.getLatLng();
    const res = await fetch(`${API}/${currentCampus}/nearest?lat=${lat}&lng=${lng}`);
    const node = await res.json();
    drawNode(node, 'Your location', 'start');
}


loadCampuses();