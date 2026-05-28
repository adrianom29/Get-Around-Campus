import os
from Objects import Node, Edge, InvalidNodeIDError, EdgeDoesNotExistError
import networkx as nx
import heapq
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
CORS(app)

CAMPUSES = {
    "YU": {
        "name": "York University",
        "center": [43.773361, -79.502361],
        "zoom": 16,
        "nodes": "../csv/YorkU-nodes.csv",
        "edges": "../csv/YorkU-edges.csv",
    },
    "UofT":{
        "name": "University of Toronto St. George",
        "center": [43.663381, -79.395807],
        "zoom": 16,
        "nodes": "../csv/UofT-nodes.csv",
        "edges": "../csv/UofT-edges.csv",
    },
    "TMU":{
        "name": "Toronto Metropolitan University",
        "center": [43.657583, -79.383001],
        "zoom": 16,
        "nodes": "../csv/TMU-nodes.csv",
        "edges": "../csv/TMU-edges.csv",
    },
    "UWO":{
        "name": "Western University",
        "center": [43.007141, -81.274985],
        "zoom": 16,
        "nodes": "../csv/UWO-nodes.csv",
        "edges": "../csv/UWO-edges.csv",
    },
    "McMaster":{
        "name": "McMaster University",
        "center": [43.262888, -79.918887],
        "zoom": 16,
        "nodes": "../csv/Mac-nodes.csv",
        "edges": "../csv/Mac-edges.csv",
    },
    "UWWLU":{
        "name": "University of Waterloo and Wilfred Laurier University",
        "center": [43.473147, -80.537368],
        "zoom": 16,
        "nodes": "../csv/UW-WLU-nodes.csv",
        "edges": "../csv/UW-WLU-edges.csv",
    },
    "UG":{
        "name": "University of Guelph",
        "center": [43.531960, -80.226169],
        "zoom": 16,
        "nodes": "../csv/UG-nodes.csv",
        "edges": "../csv/UG-edges.csv",
    },
    "QU":{
        "name": "Queen's University",
        "center": [44.225706, -76.495570],
        "zoom": 16,
        "nodes": "../csv/QU-nodes.csv",
        "edges": "../csv/QU-edges.csv",
    },
    "WindsorU":{#750
        "name": "University of Windsor",
        "center": [42.303238, -83.065248],
        "zoom": 16,
        "nodes": "../csv/Windsor-nodes.csv",
        "edges": "../csv/Windsor-edges.csv",
    },
}

_campus_data = {}   # campus_key -> {"graph": G, "nodes": [...], "edges": [...]}

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
    """Lazy-load and cache campus graph data."""
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
    raise InvalidNodeIDError(f"No node with id {id}")

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

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True)