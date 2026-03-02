import os
from Objects import Node, Edge, InvalidNodeIDError
import networkx as nx
import heapq

def build_graph():      #reads data from csv files, creates objects 
    G = nx.Graph()
    nodes = []
    edges = []

    base_path = os.path.dirname(__file__)
    nodes_path = os.path.join(base_path, "../csv/YU-nodes.csv")
    edges_path = os.path.join(base_path, "../csv/YU-edges.csv")

    with open(nodes_path, "r") as f:
        next(f)
        for line in f:
            object = line.strip().split(",")
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

def getShortestPath(start, end):
    previous, distances = dijkstras(start)
    path = []
    totalDistance = distances[end]
    current = end
    while (current != None):
        path.append(current)
        current = previous[current]
    return path[::-1], totalDistance    #returns list of nodes in order of path from start node to end node


graph, nodes, edges = build_graph()

path, distances = getShortestPath(35485240, 10845513120)
print(path)


#try:
#    n = findNode(13402070430)
#    print(f"{n.getY()}, {n.getX()}")

#except InvalidNodeIDError as e:
#    print(e)
