import osmnx as ox

coordinates = "42.303238, -83.065248"    

G = ox.graph_from_address(coordinates, dist=750, network_type="walk")

nodes, edges = ox.graph_to_gdfs(G)

nodes_df = nodes.reset_index()[["osmid", "y", "x"]].rename(columns={"y": "lat", "x": "lng"})
nodes_df["names"] = ""
namedNodes = {}

nodes_df["names"] = nodes_df["osmid"].map(namedNodes).fillna("")

edges_df = edges.reset_index()[["u", "v", "length"]]

nodes_df.to_csv("Windsor-nodes.csv", index=False)
edges_df.to_csv("Windsor-edges.csv", index=False)
