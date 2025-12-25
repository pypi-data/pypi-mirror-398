import networkx as nx
import plotly.graph_objects as go


class UnidirectedGraphPlotter:

    def __init__(self):
        pass

    def plot(self, graph: nx.Graph, use_map_coordinates: bool = False,
             show: bool = False):

        if use_map_coordinates:
            # Use node coordinates directly as they are lat/lon
            pos = {node: (node[1], node[0]) for node in graph.nodes()}
        else:
            # Get node positions using spring layout
            pos = nx.spring_layout(graph)

        # Create edge trace
        edge_x = []
        edge_y = []
        for edge in graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')  # type: ignore

        # Create node trace
        node_x = []
        node_y = []
        for node in graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=list(graph.nodes()),
            textposition="top center"
        )  # type: ignore

        # Create the figure
        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
            title='Unidirected Graph',  # type: ignore
            showlegend=False)  # type: ignore
        )  # type: ignore

        if use_map_coordinates:
            # Update layout for map view
            fig.update_layout(
                mapbox=dict(
                    style="open-street-map",
                    center=dict(lat=sum(y for y in node_y)/len(node_y),
                                lon=sum(x for x in node_x)/len(node_x)),
                    zoom=12
                ),
                margin=dict(l=0, r=0, t=0, b=0)
            )

        if show:
            fig.show()
        else:
            fig.write_html("batem/graphs/results/graph.html", auto_open=True)
