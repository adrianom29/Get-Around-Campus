import os
import subprocess
import hmac
import hashlib
import urllib.request
import urllib.error
from objects import Node, Edge
import networkx as nx
import heapq
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from config import CAMPUSES

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
CORS(app)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GITHUB_WEBHOOK_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET')
PA_API_TOKEN = os.environ.get('PA_API_TOKEN')
PA_USERNAME = os.environ.get('PA_USERNAME')
PA_DOMAIN = os.environ.get('PA_DOMAIN')

_campus_data = {}   # campus_key -> { "graph": G, "nodes": [...], "edges": [...]}

def build(campus_key):
    cfg = CAMPUSES[campus_key]
    G = nx.Graph()
    nodes, edges = [], []

    base_path = os.path.dirname(__file__)
    nodes_path = os.path.abspath(os.path.join(base_path, cfg["nodes"]))
    edges_path = os.path.abspath(os.path.join(base_path, cfg["edges"]))

    with open(nodes_path, "r") as f:
        next(f)
        for line in f:
            parts = line.split(",")
            name = parts[3].strip() if len(parts) > 3 else None
            n = Node(int(parts[0]), float(parts[1]), float(parts[2]), name)
            nodes.append(n)
            G.add_node(n.getID(), data=n)

    with open(edges_path, "r") as f:
        next(f)
        for line in f:
            parts = line.split(",")
            e = Edge(int(parts[0]), int(parts[1]), float(parts[2]))
            edges.append(e)
            G.add_edge(e.getStart(), e.getDest(), weight=e.getWeight())

    return G, nodes, edges

def get_campus(campus_key):
    if campus_key not in _campus_data:
        if campus_key not in CAMPUSES:
            return None
        G, nodes, edges = build(campus_key)
        _campus_data[campus_key] = {"graph": G, "nodes": nodes, "edges": edges}
    return _campus_data[campus_key]

def findNode(nodes, id):
    start, end = 0, len(nodes) - 1
    while start <= end:
        mid = (start + end) // 2
        if nodes[mid].getID() == id:
            return nodes[mid]
        elif nodes[mid].getID() > id:
            end = mid - 1
        else:
            start = mid + 1

def dijkstras(graph, nodes, start_id):
    previous = {n.getID(): None for n in nodes}
    visited = {n.getID(): False for n in nodes}
    distances = {n.getID(): float("inf") for n in nodes}
    distances[start_id] = 0
    pq = [(0, start_id)]
    heapq.heapify(pq)

    while pq:
        cur_dist, cur_node = heapq.heappop(pq)
        if cur_dist > distances[cur_node]:
            continue
        visited[cur_node] = True
        for neighbour, edge in graph[cur_node].items():
            if visited[neighbour]:
                continue
            new_dist = cur_dist + edge["weight"]
            if new_dist < distances[neighbour]:
                distances[neighbour] = new_dist
                previous[neighbour] = cur_node
                heapq.heappush(pq, (new_dist, neighbour))
    return previous, distances

def getPath(graph, nodes, start_id, end_id):
    previous, distances = dijkstras(graph, nodes, start_id)
    path, current = [], end_id
    while current is not None:
        path.append(current)
        current = previous[current]
    return path[::-1], distances[end_id]

def getNearestNode(nodes, lat, lng):
    return min(nodes, key=lambda n: (n.getLat()-lat)**2 + (n.getLng()-lng)**2)

def _asset_version(filename):
    path = os.path.join(app.static_folder, filename)
    try:
        return int(os.path.getmtime(path))
    except OSError:
        return 0

@app.route('/')
def index():
    return render_template('index.html',
                            app_js_version=_asset_version('app.js'),
                            style_css_version=_asset_version('style.css'))

@app.route('/campuses')
def list_campuses():
    return jsonify([
        {"key": k, "name": v["name"], "center": v["center"], "zoom": v["zoom"]}
        for k, v in CAMPUSES.items()
    ])

@app.route('/<campus>/nodes')
def get_nodes(campus):
    data = get_campus(campus)
    if not data:
        return jsonify({"error": "Unknown campus"}), 404
    return jsonify([
        {'id': n.getID(), 'lat': n.getLat(), 'lng': n.getLng(), 'name': n.getName()}
        for n in data["nodes"]
    ])

@app.route('/<campus>/named-nodes')
def get_named_nodes(campus):
    data = get_campus(campus)
    if not data:
        return jsonify({"error": "Unknown campus"}), 404
    return jsonify([
        {'id': n.getID(), 'lat': n.getLat(), 'lng': n.getLng(), 'name': n.getName()}
        for n in data["nodes"] if n.getName() and n.getName().strip()
    ])

@app.route('/<campus>/nearest')
def get_nearest(campus):
    data = get_campus(campus)
    if not data:
        return jsonify({"error": "Unknown campus"}), 404
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    n = getNearestNode(data["nodes"], lat, lng)
    return jsonify({'id': n.getID(), 'lat': n.getLat(), 'lng': n.getLng(), 'name': n.getName()})

@app.route('/<campus>/path')
def get_path(campus):
    data = get_campus(campus)
    if not data:
        return jsonify({"error": "Unknown campus"}), 404
    src = int(request.args.get('src'))
    dst = int(request.args.get('dst'))
    node_path, distance = getPath(data["graph"], data["nodes"], src, dst)
    coords = [{'lat': findNode(data["nodes"], n).getLat(),
               'lng': findNode(data["nodes"], n).getLng()} for n in node_path]
    return jsonify({'path': coords, 'distance': round(distance, 1)})

def _reload_webapp():
    if not (PA_API_TOKEN and PA_USERNAME and PA_DOMAIN):
        return False, "PA_API_TOKEN/PA_USERNAME/PA_DOMAIN not set"
    url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USERNAME}/webapps/{PA_DOMAIN}/reload/'
    req = urllib.request.Request(url, method='POST', headers={'Authorization': f'Token {PA_API_TOKEN}'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status == 200, resp.read().decode()
    except urllib.error.HTTPError as e:
        return False, e.read().decode()
    except urllib.error.URLError as e:
        return False, str(e)

@app.route('/webhook/deploy', methods=['POST'])
def deploy_webhook():
    if not GITHUB_WEBHOOK_SECRET:
        return jsonify({"error": "webhook not configured"}), 503

    signature = request.headers.get('X-Hub-Signature-256', '')
    expected = 'sha256=' + hmac.new(GITHUB_WEBHOOK_SECRET.encode(), request.data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return jsonify({"error": "invalid signature"}), 403

    if request.headers.get('X-GitHub-Event') != 'push':
        return jsonify({"status": "ignored"}), 200

    payload = request.get_json(silent=True) or {}
    if payload.get('ref') and payload['ref'] != 'refs/heads/main':
        return jsonify({"status": "ignored", "ref": payload.get('ref')}), 200

    pull = subprocess.run(['git', 'pull'], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
    reload_ok, reload_body = _reload_webapp()

    return jsonify({
        "git_pull": {"returncode": pull.returncode, "stdout": pull.stdout, "stderr": pull.stderr},
        "reload": {"ok": reload_ok, "body": reload_body},
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port = port)