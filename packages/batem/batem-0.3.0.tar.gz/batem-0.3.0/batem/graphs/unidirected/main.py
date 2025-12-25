import networkx as nx

from batem.graphs.plot.unidirected import UnidirectedGraphPlotter


if __name__ == "__main__":

    # python batem/graphs/unidirected/main.py

    G = nx.Graph()
    G.add_edge(1, 2)
    G.add_edge(1, 3)
    G.add_edge(2, 3)
    G.add_edge(2, 4)
    G.add_edge(3, 4)
    G.add_edge(3, 5)
    G.add_edge(4, 5)

    UnidirectedGraphPlotter().plot(G)
