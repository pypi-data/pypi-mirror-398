import networkx as nx


def connectivity_analysis(graph: nx.DiGraph):
    """
    Analyze the connectivity of a directed graph.
    """
    # Analyze connectivity from the existing code
    print("Strongly connected components:")
    strong_components = list(nx.strongly_connected_components(graph))
    for i, component in enumerate(strong_components):
        print(f"Component {i+1}: {len(component)} nodes")

    print(f"\nStrong component count: {len(strong_components)}")

    print("\nWeakly connected components:")
    weak_components = list(nx.weakly_connected_components(graph))
    for i, component in enumerate(weak_components):
        print(f"Component {i+1}: {len(component)} nodes")

    print(f"\nWeak component count: {len(weak_components)}")


def street_map_analysis(graph: nx.Graph):
    """
    Analyze the street map graph.
    """
    # Analyze the street network
    print("\nStreet Network Analysis:")
    print(f"Number of intersections: {graph.number_of_nodes()}")
    print(f"Number of roads: {graph.number_of_edges()}")
    print("\nRoads in the network:")
    for (start, end, data) in graph.edges(data=True):
        print(f"{data['road_name']}: {start} to {end} ({data['length']}m)")


def graph_properties(graph: nx.DiGraph):
    """
    Analyze the graph properties.
    """
    print(f"Number of nodes: {graph.number_of_nodes()}")
    print(f"Number of edges: {graph.number_of_edges()}")

    for node in graph.nodes():
        print(f"Node: {node}")
        print(f"In-degree of {node}: {graph.in_degree(node)}")
        print(f"Out-degree of {node}: {graph.out_degree(node)}")

    # Print all edges with their way names
    print("\nGraph edges with ski slope names:")
    for edge in graph.edges(data=True):
        way_name = edge[2]['way']
        print(f"Edge: {edge[0]} -> {edge[1]} (Way: {way_name})")


def centrality_measures(graph: nx.DiGraph):
    """
    Compute the degree and betweenness centrality of the graph.
    """
    # Centrality measures
    degree_centrality = nx.degree_centrality(graph)
    betweenness_centrality = nx.betweenness_centrality(graph)

    print(f"\nDegree centrality: {degree_centrality}")
    print(f"Betweenness centrality: {betweenness_centrality}")

    # Find the most central node
    # most_central_node = max(
    #    degree_centrality, key=degree_centrality.get)  # type: ignore
   # print(f"\nMost central node (degree): {most_central_node}")

    # for way in graph.edges(data=True):
    #    if way[0] == most_central_node:
    #        print(f"Way: {way[2]['way']}")
