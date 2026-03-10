import os
from Objects import Node, Edge, InvalidNodeIDError, EdgeDoesNotExistError
import networkx as nx
import heapq
import math
import time
import matplotlib.pyplot as plt

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
            new_node = Node(int(object[0]), float(object[1]), float(object[2]))
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
    edgePath = []
    for i in range(len(nodePath) -1):
        edgePath.append(findEdge(nodePath[i], nodePath[i+1]))

    return nodePath, edgePath, totalDistance    #returns list of nodes and edges from start to finish as well as total distance

def getNearestNode(y, x):       #y = latitude, x = longitude
    closestNode = None
    minDistance = float("inf")
    for n in nodes:
        d_squared = (n.getX() - x)**2 + (n.getY() - y)**2
        if d_squared < minDistance:
            minDistance = d_squared
            closestNode = n
    return closestNode

import sys
print(sys.executable)

start_time = time.perf_counter()
graph, nodes, edges = build()

#tests: 
n = getNearestNode(4.767657, -79.509253)
print(f"{n.getY()}, {n.getX()}")

pnode, pedge, distances = getPath(35485240, 10845513120)
print(len(pnode))
print(len(pedge))

try:
    n = findNode(13402070430)
    print(f"{n.getY()}, {n.getX()}")
except InvalidNodeIDError as e:
    print(e)

print(findNode(edges[3].getStart()).getX())

end_time = time.perf_counter()
print(end_time - start_time)

latitudes = [n.getY() for n in nodes]
longitudes = [n.getX() for n in nodes]

for e in edges:
    xValues = [findNode(e.getStart()).getX(), findNode(e.getDest()).getX()]
    yValues = [findNode(e.getStart()).getY(), findNode(e.getDest()).getY()]
    plt.plot(xValues, yValues, linewidth=0.2)

plt.scatter(longitudes, latitudes, s=2)
plt.xlabel("X")
plt.ylabel("Y")
plt.title("Graph nodes")

plt.show()

