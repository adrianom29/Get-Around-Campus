import osmnx as ox

place_name = "43°46'24.1\"N 79°30'08.5\"W"      #center of York U campus

G = ox.graph_from_address(place_name, dist=1000, network_type="walk")

nodes, edges = ox.graph_to_gdfs(G)

nodes_df = nodes.reset_index()[["osmid", "y", "x"]]
edges_df = edges.reset_index()[["u", "v", "length"]]

nodes_df.to_csv("nodesNEW.csv", index=False)
edges_df.to_csv("edgesNEW.csv", index=False)
