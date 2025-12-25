from typing import Tuple
import networkx as nx

from batem.graphs.plot.directed import DirectedGraphPlotter


class Way:

    def __init__(self, name: str, start_node: Tuple[float, float],
                 end_node: Tuple[float, float]):
        self.name = name
        self.start_node = start_node
        self.end_node = end_node


if __name__ == "__main__":

    # python batem/graphs/directed/main.py

    G = nx.DiGraph()

    # Define some nodes with lat/lon coordinates
    start_node = (45.6325153, 6.8693065)
    end_node = (45.6468097, 6.8618197)
    way_pdr = Way("Plan du Repos", start_node, end_node)

    # Add edges with names
    G.add_edge(start_node, end_node, weight=1.0, way=way_pdr)

    third_node = (45.6399027, 6.8673232)
    way_chamois_1 = Way("Chamois 1", end_node, third_node)
    G.add_edge(end_node, third_node, weight=1.0, way=way_chamois_1)
    way_chamois_2 = Way("Chamois 2", third_node, start_node)
    G.add_edge(third_node, start_node, weight=1.0, way=way_chamois_2)

    start_node_2 = (45.6293094, 6.8484057)
    end_node_2 = (45.6469019, 6.8612917)
    way_roches_noires = Way("Roches Noires", start_node_2, end_node_2)
    G.add_edge(start_node_2, end_node_2, weight=1.0, way=way_roches_noires)

    start_node_3 = (45.6260058, 6.8642884)
    end_node_3 = (45.6397464, 6.8601482)
    way_eucherts = Way("Eucherts", start_node_3, end_node_3)
    G.add_edge(start_node_3, end_node_3, weight=1.0, way=way_eucherts)

    another_node = (45.6442177, 6.8599488)
    way_tetras_1 = Way("Tetras 1", end_node_2, another_node)
    G.add_edge(end_node_2, another_node, weight=1.0, way=way_tetras_1)

    way_artificial = Way("Artificial Way", way_roches_noires.end_node,
                         way_pdr.end_node)
    G.add_edge(way_artificial.start_node, way_artificial.end_node,
               weight=1.0, way=way_artificial)
    way_artificial_2 = Way("Artificial Way 2", way_pdr.end_node,
                           way_roches_noires.end_node)
    G.add_edge(way_artificial_2.start_node, way_artificial_2.end_node,
               weight=1.0, way=way_artificial_2)

    way_artificial_3 = Way("Artificial Way 3", way_tetras_1.end_node,
                           way_roches_noires.start_node)
    G.add_edge(way_artificial_3.start_node, way_artificial_3.end_node,
               weight=1.0, way=way_artificial_3)

    # Add debug print
    print("Graph edges:")
    for edge in G.edges(data=True):
        print(f"Edge: {edge[0]} -> {edge[1]} with name: {edge[2]['way'].name}")

    print("Strong component count: ", len(
        list(nx.strongly_connected_components(G))))
    print("Weak component count: ", len(
        list(nx.weakly_connected_components(G))))

    DirectedGraphPlotter().plot(G, show_strong=True)
