from typing import TYPE_CHECKING
import plotly.graph_objects as go


if TYPE_CHECKING:
    from batem.skiers.agents.skier_flow import SkierAgent


class IndividualSkierPlotter:
    """Analyzes and visualizes individual skier behavior."""

    def __init__(self, skiers: list['SkierAgent']):
        """Initialize with list of skier agents.

        Args:
            skiers: List of SkierAgent objects to analyze
        """
        self.skiers = skiers
        self._calculate_individual_stats()

    def _calculate_individual_stats(self) -> None:
        """Calculate statistics for each individual skier."""
        self.skier_stats = []

        for skier in self.skiers:
            # Calculate basic metrics
            total_skilifts = len(skier.trajectory)
            unique_skilifts = len(set(skier.trajectory))

            # Calculate wait times
            avg_wait_time = skier.total_wait_time / \
                total_skilifts if total_skilifts > 0 else 0

            # Store statistics
            self.skier_stats.append({
                'category': skier.skier_type.value,
                'preference': skier.preference.value,
                'total_skilifts': total_skilifts,
                'unique_skilifts': unique_skilifts,
                'avg_wait_time': avg_wait_time,
                'total_wait_time': skier.total_wait_time,
                'time_in_lift': skier.time_in_lift,
                'trajectory': skier.trajectory,
                'patience': skier.patience
            })

    def plot_skier_trajectory(self, skier_index: int) -> None:
        """Plot the trajectory of a specific skier.

        Args:
            skier_index: Index of the skier to plot
        """
        if not 0 <= skier_index < len(self.skier_stats):
            print(f"Invalid skier index. Must be between 0 and "
                  f"{len(self.skier_stats) - 1}")
            return

        skier = self.skier_stats[skier_index]

        # Create figure
        fig = go.Figure()

        # Add trajectory as a line with markers
        fig.add_trace(
            go.Scatter(
                x=list(range(len(skier['trajectory']))),
                y=skier['trajectory'],
                mode='lines+markers',
                name='Trajectory',
                line=dict(color='rgb(55, 83, 109)', width=2),
                marker=dict(size=8)
            )
        )

        # Update layout
        fig.update_layout(
            title=f'Skier Trajectory (Type: {skier["category"]}, '
            f'Preference: {skier["preference"]})',
            xaxis_title='Skilift Sequence',
            yaxis_title='Skilift Name',
            height=600,
            width=1000,
            showlegend=False
        )

        # Add hover template
        fig.update_traces(
            hovertemplate=(
                "Sequence: %{x}<br>"
                "Skilift: %{y}<br>"
                "<extra></extra>"
            )
        )

        fig.show()

    def plot_skier_metrics(self, top_n: int = 10) -> None:
        """Plot key metrics for top N skiers by total wait time.

        Args:
            top_n: Number of top skiers to plot
        """
        # Sort skiers by total wait time
        sorted_stats = sorted(
            self.skier_stats,
            key=lambda x: x['total_wait_time'],
            reverse=True
        )[:top_n]

        # Create figure with subplots
        fig = go.Figure()

        # Add total wait time bars
        fig.add_trace(
            go.Bar(
                x=[f"Skier {i+1}" for i in range(len(sorted_stats))],
                y=[s['total_wait_time'] for s in sorted_stats],
                name='Total Wait Time',
                marker_color='rgb(55, 83, 109)',
                text=[f"{s['total_wait_time']:.1f}m" for s in sorted_stats],
                textposition='auto'
            )
        )

        # Add time in lift as line
        fig.add_trace(
            go.Scatter(
                x=[f"Skier {i+1}" for i in range(len(sorted_stats))],
                y=[s['time_in_lift'] for s in sorted_stats],
                name='Time in Lift',
                yaxis='y2',
                mode='lines+markers',
                line=dict(color='rgb(26, 118, 255)', width=3),
                marker=dict(size=8)
            )
        )

        # Update layout
        fig.update_layout(
            title=f'Top {top_n} Skiers by Total Wait Time',
            xaxis_title='Skier',
            yaxis_title='Total Wait Time (minutes)',
            yaxis2=dict(
                title='Time in Lift (minutes)',
                overlaying='y',
                side='right'
            ),
            height=600,
            width=1000,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        # Add hover template
        fig.update_traces(
            hovertemplate=(
                "Skier: %{x}<br>"
                "Value: %{y:.1f} minutes<br>"
                "Type: %{customdata[0]}<br>"
                "Preference: %{customdata[1]}<br>"
                "Patience: %{customdata[2]:.2f}<br>"
                "<extra></extra>"
            ),
            customdata=[[s['category'], s['preference'], s['patience']]
                        for s in sorted_stats]
        )

        fig.show()

    def plot_category_comparison(self) -> None:
        """Plot comparison of metrics across skier types."""
        # Group stats by category
        category_stats = {}
        for stat in self.skier_stats:
            cat = stat['category']
            if cat not in category_stats:
                category_stats[cat] = []
            category_stats[cat].append(stat)

        # Calculate averages for each category
        categories = []
        avg_wait_times = []
        avg_time_in_lift = []
        avg_unique_skilifts = []

        for cat, stats in category_stats.items():
            categories.append(cat)
            avg_wait_times.append(
                sum(s['total_wait_time'] for s in stats) / len(stats)
            )
            avg_time_in_lift.append(
                sum(s['time_in_lift'] for s in stats) / len(stats)
            )
            avg_unique_skilifts.append(
                sum(s['unique_skilifts'] for s in stats) / len(stats)
            )

        # Create figure
        fig = go.Figure()

        # Add wait time bars
        fig.add_trace(
            go.Bar(
                x=categories,
                y=avg_wait_times,
                name='Avg Wait Time',
                marker_color='rgb(55, 83, 109)',
                text=[f"{t:.1f}m" for t in avg_wait_times],
                textposition='auto'
            )
        )

        # Add time in lift as line
        fig.add_trace(
            go.Scatter(
                x=categories,
                y=avg_time_in_lift,
                name='Avg Time in Lift',
                yaxis='y2',
                mode='lines+markers',
                line=dict(color='rgb(26, 118, 255)', width=3),
                marker=dict(size=8)
            )
        )

        # Add unique skilifts as line
        fig.add_trace(
            go.Scatter(
                x=categories,
                y=avg_unique_skilifts,
                name='Avg Unique Skilifts',
                yaxis='y3',
                mode='lines+markers',
                line=dict(color='rgb(255, 65, 54)', width=3),
                marker=dict(size=8)
            )
        )

        # Update layout
        fig.update_layout(
            title='Skier Type Comparison',
            xaxis_title='Skier Type',
            yaxis_title='Average Wait Time (minutes)',
            yaxis2=dict(
                title='Average Time in Lift (minutes)',
                overlaying='y',
                side='right'
            ),
            yaxis3=dict(
                title='Average Unique Skilifts',
                overlaying='y',
                side='right',
                anchor='free',
                position=1.0
            ),
            height=600,
            width=1000,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        # Add hover template
        fig.update_traces(
            hovertemplate=(
                "Type: %{x}<br>"
                "Value: %{y:.1f}<br>"
                "Skiers in Type: %{customdata}<br>"
                "<extra></extra>"
            ),
            customdata=[len(stats) for stats in category_stats.values()]
        )

        fig.show()

    def plot_skier_heatmap(self) -> None:
        """Plot a heatmap of skilift transitions."""
        # Create transition matrix
        skilifts = set()
        for stat in self.skier_stats:
            skilifts.update(stat['trajectory'])
        skilifts = sorted(list(skilifts))

        # Initialize transition matrix
        transitions = {s1: {s2: 0 for s2 in skilifts} for s1 in skilifts}

        # Count transitions
        for stat in self.skier_stats:
            trajectory = stat['trajectory']
            for i in range(len(trajectory) - 1):
                from_lift = trajectory[i]
                to_lift = trajectory[i + 1]
                transitions[from_lift][to_lift] += 1

        # Create heatmap
        fig = go.Figure()

        # Add heatmap
        fig.add_trace(
            go.Heatmap(
                z=[[transitions[s1][s2] for s2 in skilifts]
                    for s1 in skilifts],
                x=skilifts,
                y=skilifts,
                colorscale='Viridis',
                showscale=True
            )
        )

        # Update layout
        fig.update_layout(
            title='Skilift Transition Heatmap',
            xaxis_title='To Skilift',
            yaxis_title='From Skilift',
            height=800,
            width=1000
        )

        # Add hover template
        fig.update_traces(
            hovertemplate=(
                "From: %{y}<br>"
                "To: %{x}<br>"
                "Count: %{z}<br>"
                "<extra></extra>"
            )
        )

        fig.show()
