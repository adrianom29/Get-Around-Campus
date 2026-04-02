import osmnx as ox

place_name = "43.773343262098116, -79.50233968503798"      #center of York U campus

G = ox.graph_from_address(place_name, dist=1000, network_type="walk")

nodes, edges = ox.graph_to_gdfs(G)

nodes_df = nodes.reset_index()[["osmid", "y", "x"]].rename(columns={"y": "lat", "x": "lng"})
nodes_df["names"] = ""
namedNodes = {
    1966251295: "ACE - Accolade Building East",
    9951910778: "ACW - Accolade Building West",
    13249061579: "AO - Archives of Ontario",
    13270809927: "ATK - Atkinson",
    13237577162: "BC - Norman Bethune College",
    8119481538: "BCSS - Bennett Centre for Student Services", 
    13275989612: "BRG - Bergeron Centre for Engineering Excellence",
    8099328757: "BSB - Behavioural Science Building",
    9951910776: "BU - Burton Auditorium",
    11361006524: "CB - Chemistry Building",
    9981919377: "CC - Calumet College",
    11885254385: "CFA - The Joan & Martin Goldfarb Centre for Fine Arts",
    9951910763: "CFT - Centre for Film and Theatre / Joseph F. Green Studio Theatre",
    9951548959: "CLH - Curtis Lecture Halls",
    9951548949: "CSQ - Central Square",
    8185069870: "CUB - Central Utilities Building",
    7885367779: "DB - Victor Phillip Dahdaleh Building",
    7854384610: "ELC - Executive Learning Centre",
    9951910527: "FC - Founders College",
    8099328752: "FRQ - Farquharson Life Sciences",
    7854359430: "HC - Lorna R. Marsden Honour Court & Welcome Centre",
    1966261770: "HNE - Health, Nursing and Environmental Studies Building",
    8177968984: "K - Kinsmen Building",
    8153684523: "KT - Kaneff Tower",
    5729327315: "LAS - Lassonde Building",
    11361006533: "LSB - Life Sciences Building",
    8192369553: "LUM - Lumbers Building",
    10220206182: "MB - Rob and Cheryl McEwen Graduate Study & Research Building",
    1917568972: "MC - McLaughlin College",
    9951548924: "OSG - Ignat Kaneff Building (Osgoode Hall Law School)",
    8177968826: "PRB - Physical Resources Building",
    10187458862: "PSE - Petrie Science and Engineering Building / Petrie Observatory",
    8099166920: "R - Ross Building",
    13249100540: "SC - Stong College",
    9951548946: "SCL - 	Scott Library",
    7838027578: "SHR - Sherman Health Science Research Centre",
    1895622015: "SLH - Stedman Lecture Halls",
    10220206183: "SSB - Seymour Schulich Building",
    13240837597: "SSC Second Student Centre",
    1112358369: "STC - First Student Centre",
    10187464130: "STL - Steacie Science & Engineering Library",
    1917564586: "TC - Tennis Canada - Sobeys Stadium",
    8095126761: "TFC - Track & Field Centre",
    13239120876: "TM - Tait McKenzie Centre",
    8095157686: "VC - Vanier College",
    7831227012: "VH - Vari Hall",
    8095126668: "WC - Winters College",
    8095126629: "WOB - West Office Building",
    5757433926: "WSC - William Small Centre",
    13300320749: "YL - York Lanes",
    7832769376: "York University TTC Station",
    7024680949: "Pioneer Village TTC Station"
}

nodes_df["names"] = nodes_df["osmid"].map(namedNodes).fillna("")

edges_df = edges.reset_index()[["u", "v", "length"]]

nodes_df.to_csv("nodesNEW.csv", index=False)
edges_df.to_csv("edgesNEW.csv", index=False)
