import os
from Objects import Node, Edge, InvalidNodeIDError, EdgeDoesNotExistError
import networkx as nx
import heapq
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
CORS(app)

def build():      #reads data from csv files, creates objects 
    G = nx.Graph()
    nodes = []
    edges = []

    base_path = os.path.dirname(__file__)
    nodes_path = os.path.join(base_path, "../csv/YU-nodes.csv")
    edges_path = os.path.join(base_path, "../csv/YU-edges.csv")

    with open(nodes_path, "r") as f:
        next(f)
        for line in f:
            object = line.split(",")
            new_node = Node(int(object[0]), float(object[1]), float(object[2]), object[3])
            nodes.append(new_node)
            G.add_node(int(object[0]), data=new_node)

    with open(edges_path, "r") as f:
        next(f)
        for line in f:
            object = line.split(",")
            new_edge = Edge(int(object[0]), int(object[1]), float(object[2]))
            edges.append(new_edge)
            G.add_edge(int(object[0]), int(object[1]), weight=float(object[2]))  

    return G, nodes, edges

def findNode(id):
    start = 0
    end = len(nodes)-1
    while (start <= end):
        mid = (start + end) // 2
        if nodes[mid].getID() == id:
            return nodes[mid]
        elif nodes[mid].getID() > id:
            end = mid - 1
        else:
            start = mid + 1
    raise InvalidNodeIDError(f"No such id {id} in nodes exists")

def findEdge(start, dest):
    for e in edges:
        if e.getStart() == start and e.getDest() == dest:
            return e
    raise EdgeDoesNotExistError(f"No edge with starting node {start.getID()} and destination node {dest.getID} exists")

def dijkstras(start):       #start node will be the IDs of the node
    previous = {n.getID(): None for n in nodes}
    visited = {n.getID(): False for n in nodes}
    distances = {n.getID(): float("inf") for n in nodes}
    distances[start] = 0
    priorityQueue = []
    heapq.heapify(priorityQueue)
    heapq.heappush(priorityQueue, (0, start))
    
    while priorityQueue:
        currentDistance, currentNode = heapq.heappop(priorityQueue)
    
        if currentDistance > distances[currentNode]:    #removes any "stale" elements 
            continue
        
        visited[currentNode] = True
        for neighbourNode, edge in graph[currentNode].items():
            weight = edge.get("weight")
            if visited[neighbourNode]: 
                continue
            newDistance = currentDistance + weight
            if newDistance < distances[neighbourNode]:
                distances[neighbourNode] = newDistance
                previous[neighbourNode] = currentNode
                heapq.heappush(priorityQueue, (newDistance, neighbourNode))
    
    return previous, distances

def getPath(start, end):
    previous, distances = dijkstras(start)
    nodePath = []
    totalDistance = distances[end]
    current = end
    while (current != None):    
        nodePath.append(current)    #nodes are appended in reverse order
        current = previous[current]

    nodePath = nodePath[::-1]       #reverses array (nodes are now in order from start to finish)

    return nodePath, totalDistance    #returns list of nodes and edges from start to finish as well as total distance

def getNearestNode(lat, lng):
    closestNode = None
    minDistance = float("inf")
    for n in nodes:
        d_squared = (n.getLng() - lng)**2 + (n.getLat() - lat)**2
        if d_squared < minDistance:
            minDistance = d_squared
            closestNode = n
    return closestNode

@app.route('/')
def index():
    print("Looking for templates in:", app.template_folder)
    print("Files found:", os.listdir(app.template_folder))
    return render_template('index.html')


@app.route('/nodes')
def get_nodes():
    return jsonify([
        {'id': n.getID(), 'lat': n.getLat(), 'lng': n.getLng(), 'name': n.getName()} for n in nodes
    ])

@app.route('/path')
def get_path():
    src = int(request.args.get('src'))
    dst = int(request.args.get('dst'))
    node_path, distance = getPath(src, dst)
    path_coords = [{'lat': findNode(n).getLat(), 'lng': findNode(n).getLng()} for n in node_path]
    return jsonify({'path': path_coords, 'distance': round(distance, 1)})

@app.route('/nearest')
def get_nearest():
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    n = getNearestNode(lat, lng)
    return jsonify({'id': n.getID(), 'lat': n.getLat(), 'lng': n.getLng(), 'name': n.getName()})


graph, nodes, edges = build()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port = port)
    
    #app.run(debug=True)
    
    