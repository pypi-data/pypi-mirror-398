import networkx as nx
import plotly.graph_objects as go
from typing import Dict, Tuple


class DirectedGraphPlotter:

    def __init__(self):
        self.component_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]

    def _get_components(self, graph: nx.DiGraph) -> Tuple[Dict, Dict]:
        """Extract weakly and strongly connected components."""
        weak_components = list(nx.weakly_connected_components(graph))
        strong_components = list(nx.strongly_connected_components(graph))

        # Create mapping of nodes to their component IDs
        weak_component_map = {}
        for i, component in enumerate(weak_components):
            for node in component:
                weak_component_map[node] = i

        strong_component_map = {}
        for i, component in enumerate(strong_components):
            for node in component:
                strong_component_map[node] = i

        return weak_component_map, strong_component_map

    def plot(self, graph: nx.DiGraph, show_strong: bool = True,
             show: bool = False):
        # Get component mappings
        weak_component_map, strong_component_map = self._get_components(graph)

        # Create edge trace
        edge_x = []
        edge_y = []
        edge_text = []
        mid_x = []
        mid_y = []
        mid_text = []

        for edge in graph.edges(data=True):
            lat0, lon0 = edge[0]
            lat1, lon1 = edge[1]
            name = edge[2]["way"]
            # Add the edge line with None to break the line
            edge_x.extend([lon0, lon1, None])
            edge_y.extend([lat0, lat1, None])
            # Calculate midpoint for text
            mid_x.append((lon0 + lon1) / 2)
            mid_y.append((lat0 + lat1) / 2)
            mid_text.append(name)

        # Line trace for edges
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='text',
            hovertext=edge_text,
            mode='lines+markers',
            name='edges',
            marker=dict(
                symbol='arrow',
                size=20,
                angleref='previous'
            )
        )

        # Text trace for edge labels
        text_trace = go.Scatter(
            x=mid_x, y=mid_y,
            mode='text',
            text=mid_text,
            textposition='middle center',
            name='edge_labels'
        )

        # Node traces for components
        node_traces = []

        # First add strong components (they're more important)
        for component_id in set(strong_component_map.values()):
            node_x = []
            node_y = []
            node_text = []

            for node in graph.nodes():
                if strong_component_map[node] == component_id:
                    lat, lon = node
                    node_x.append(lon)
                    node_y.append(lat)
                    node_text.append(
                        f"Node: ({lat:.4f}, {lon:.4f})\n"
                        f"Strong Component: {component_id + 1}\n"
                        f"Weak Component: {weak_component_map[node] + 1}"
                    )

            if node_x:  # Only add trace if there are nodes in this component
                if show_strong:
                    color = self.component_colors[component_id % len(
                        self.component_colors)]
                    node_traces.append(go.Scatter(
                        x=node_x, y=node_y,
                        mode='markers',
                        name=f'Strong Component {component_id + 1}',
                        marker=dict(
                            size=15,  # Larger size for strong components
                            color=color,
                            symbol='circle',
                            line=dict(width=2, color='black')
                        ),
                        text=node_text,
                        hoverinfo='text'
                    ))
                else:
                    color = self.component_colors[weak_component_map[node] % len(
                        self.component_colors)]
                    node_traces.append(go.Scatter(
                        x=node_x, y=node_y,
                        mode='markers',
                        marker=dict(
                            size=15,  # Larger size for strong components
                            color=color,
                            symbol='circle',
                            line=dict(width=2, color='black')
                        ),
                        text=node_text,
                        hoverinfo='text'
                    ))

        # Create the figure with proper geographic layout
        fig = go.Figure()
        fig.add_trace(edge_trace)
        fig.add_trace(text_trace)
        for trace in node_traces:
            fig.add_trace(trace)

        fig.update_layout(
            title='Directed Graph with Connected Components',
            showlegend=True if show_strong else False,
            xaxis=dict(
                title='Longitude',
                range=[min(x for x in edge_x if x is not None) - 0.01,
                       max(x for x in edge_x if x is not None) + 0.01]
            ),
            yaxis=dict(
                title='Latitude',
                range=[min(y for y in edge_y if y is not None) - 0.01,
                       max(y for y in edge_y if y is not None) + 0.01]
            )
        )

        if show:
            fig.show()
        else:
            fig.write_html("batem/graphs/results/digraph.html", auto_open=True)
