import pandas as pd
import plotly.graph_objects as go
from collections import Counter, defaultdict
from typing import TYPE_CHECKING

from batem.skiers.skier import SkierData

if TYPE_CHECKING:
    from batem.skiers.agents.skier_flow import SkierAgent


class SkierStayingTimePlotter:

    def __init__(self, skiers: list[SkierData]):
        self.skiers = skiers

    def plot(self, use_skier_category: bool = False) -> None:
        # Convert staying times to hours for better readability
        data = []
        for skier in self.skiers:
            starting_time = skier.trajectory[0].time
            ending_time = skier.trajectory[-1].time
            staying_time_hours = (
                ending_time - starting_time).total_seconds() / 3600

            if use_skier_category:
                data.append({
                    'category': skier.category,
                    'staying_time_hours': staying_time_hours
                })
            else:
                data.append({
                    'category': skier.skipass_category,
                    'staying_time_hours': staying_time_hours
                })

        df = pd.DataFrame(data)

        # Calculate statistics for each category
        stats = df.groupby('category').agg({
            'staying_time_hours': ['mean', 'median', 'count']
        }).round(2)
        stats.columns = ['avg_hours', 'median_hours', 'skier_count']
        stats = stats.reset_index()

        # Create figure with secondary y-axis
        fig = go.Figure()

        # Add average staying time bars
        fig.add_trace(
            go.Bar(
                x=stats['category'],
                y=stats['avg_hours'],
                name='Average Staying Time',
                marker_color='rgb(55, 83, 109)',
                text=stats['avg_hours'].round(1),
                textposition='auto',
            )
        )

        # Add skier count as line
        fig.add_trace(
            go.Scatter(
                x=stats['category'],
                y=stats['skier_count'],
                name='Number of Skiers',
                yaxis='y2',
                mode='lines+markers',
                line=dict(color='rgb(26, 118, 255)', width=3),
                marker=dict(size=8)
            )
        )

        # Update layout
        fig.update_layout(
            title='Skier Staying Time Analysis by Category',
            xaxis=dict(
                title='Category',
                tickangle=45
            ),
            yaxis=dict(
                title='Average Staying Time (hours)',
            ),
            yaxis2=dict(
                title='Number of Skiers',
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
            hovertemplate="<br>".join([
                "Category: %{x}",
                "Average Time: %{y:.1f} hours",
                "Number of Skiers: %{customdata[0]}",
                "<extra></extra>"
            ]),
            customdata=stats[['skier_count']].values
        )

        fig.show()


class SkierStayingTimeStatisticsPlotter:

    def __init__(self, skiers: list[SkierData]):
        self.skiers = skiers

    def plot(self) -> None:
        # Calculate staying times in hours
        staying_times = []
        for skier in self.skiers:
            starting_time = skier.trajectory[0].time
            ending_time = skier.trajectory[-1].time
            staying_time_hours = (
                ending_time - starting_time).total_seconds() / 3600
            staying_times.append(staying_time_hours)

        # Create figure with subplots
        fig = go.Figure()

        # Add histogram of staying times
        fig.add_trace(
            go.Histogram(
                x=staying_times,
                name='Staying Time Distribution',
                nbinsx=30,
                marker_color='rgb(55, 83, 109)',
                opacity=0.75
            )
        )

        # Update layout
        fig.update_layout(
            title='Distribution of Skier Staying Times',
            xaxis_title='Staying Time (hours)',
            yaxis_title='Number of Skiers',
            showlegend=False,
            height=600,
            width=1000,
            bargap=0.1
        )

        # Add hover template
        fig.update_traces(
            hovertemplate="<br>".join([
                "Time Range: %{x:.1f} hours",
                "Number of Skiers: %{y}",
                "<extra></extra>"
            ])
        )

        fig.show()


class SkiliftUsagePlotter:

    def __init__(self, skiers: list[SkierData]):
        self.skiers = skiers
        self._calculate_usage_stats()

    def _calculate_usage_stats(self) -> None:
        """Calculate usage statistics for all skilifts."""
        self.skilift_counts = Counter()
        self.skilift_times = {}
        self.total_uses = 0
        self.skilift_sequences = defaultdict(
            list)  # For analyzing common paths
        self.skilift_wait_times = defaultdict(list)  # For analyzing wait times

        for skier in self.skiers:
            prev_time = None
            prev_skilift = None

            for interaction in skier.trajectory:
                skilift = interaction.skilift
                current_time = interaction.time

                self.skilift_counts[skilift] += 1
                self.total_uses += 1

                if skilift not in self.skilift_times:
                    self.skilift_times[skilift] = []
                self.skilift_times[skilift].append(current_time)

                # Track sequences of skilifts
                if prev_skilift:
                    self.skilift_sequences[prev_skilift].append(skilift)

                # Calculate wait times between skilifts
                if prev_time:
                    # in minutes
                    wait_time = (current_time - prev_time).total_seconds() / 60
                    self.skilift_wait_times[prev_skilift].append(wait_time)

                prev_time = current_time
                prev_skilift = skilift

    def plot_most_used(self, top_n: int = 15) -> None:
        """Plot the top N most used skilifts."""
        # Get top N most used skilifts
        top_skilifts = self.skilift_counts.most_common(top_n)
        skilift_names = [lift for lift, _ in top_skilifts]
        usage_counts = [count for _, count in top_skilifts]
        usage_percentages = [count/self.total_uses *
                             100 for count in usage_counts]

        # Create figure
        fig = go.Figure()

        # Add horizontal bar chart
        fig.add_trace(
            go.Bar(
                y=skilift_names,
                x=usage_counts,
                orientation='h',
                marker_color='rgb(55, 83, 109)',
                text=[f"{count:,} ({pct:.1f}%)" for count, pct in
                      zip(usage_counts, usage_percentages)],
                textposition='auto',
            )
        )

        # Update layout
        fig.update_layout(
            title=f'Top {top_n} Most Used Skilifts',
            xaxis_title='Number of Uses',
            yaxis_title='Skilift Name',
            height=max(400, len(skilift_names) * 25),
            width=1000,
            showlegend=False,
            bargap=0.2
        )

        # Add hover template
        fig.update_traces(
            hovertemplate="<br>".join([
                "Skilift: %{y}",
                "Number of Uses: %{x:,}",
                "Percentage: %{customdata:.1f}%",
                "<extra></extra>"
            ]),
            customdata=usage_percentages
        )

        fig.show()

    def plot_usage_by_hour(self, skilift_name: str) -> None:
        """Plot the usage pattern of a specific skilift by hour."""
        if skilift_name not in self.skilift_times:
            print(f"Skilift {skilift_name} not found in the data")
            return

        # Count usage by hour
        hour_counts = Counter()
        for time in self.skilift_times[skilift_name]:
            hour_counts[time.hour] += 1

        # Prepare data
        hours = list(range(24))
        counts = [hour_counts[hour] for hour in hours]

        # Create figure
        fig = go.Figure()

        # Add bar chart
        fig.add_trace(
            go.Bar(
                x=hours,
                y=counts,
                marker_color='rgb(55, 83, 109)',
                text=counts,
                textposition='auto',
            )
        )

        # Update layout
        fig.update_layout(
            title=f'Usage Pattern of {skilift_name} by Hour',
            xaxis_title='Hour of Day',
            yaxis_title='Number of Uses',
            height=500,
            width=1000,
            showlegend=False,
            bargap=0.2,
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=1
            )
        )

        # Add hover template
        fig.update_traces(
            hovertemplate="<br>".join([
                "Hour: %{x}:00",
                "Number of Uses: %{y}",
                "<extra></extra>"
            ])
        )

        fig.show()

    def plot_common_paths(self, skilift_name: str, top_n: int = 5) -> None:
        """Plot the most common paths taken after using a specific skilift."""
        if skilift_name not in self.skilift_sequences:
            print(f"Skilift {skilift_name} not found in the data")
            return

        # Count next skilift frequencies
        next_skilift_counts = Counter(self.skilift_sequences[skilift_name])
        top_next_skilifts = next_skilift_counts.most_common(top_n)

        next_skilift_names = [lift for lift, _ in top_next_skilifts]
        frequencies = [count for _, count in top_next_skilifts]
        percentages = [count/len(self.skilift_sequences[skilift_name])*100
                       for count in frequencies]

        # Create figure
        fig = go.Figure()

        # Add horizontal bar chart
        fig.add_trace(
            go.Bar(
                y=next_skilift_names,
                x=frequencies,
                orientation='h',
                marker_color='rgb(55, 83, 109)',
                text=[f"{count:,} ({pct:.1f}%)" for count, pct in
                      zip(frequencies, percentages)],
                textposition='auto',
            )
        )

        # Update layout
        fig.update_layout(
            title=f'Most Common Next Skilifts After {skilift_name}',
            xaxis_title='Number of Skiers',
            yaxis_title='Next Skilift',
            height=max(400, len(next_skilift_names) * 25),
            width=1000,
            showlegend=False,
            bargap=0.2
        )

        fig.show()


class SkierTrajectoryPlotter:

    def __init__(self, skiers: list[SkierData]):
        self.skiers = skiers
        self._calculate_trajectories()

    def _calculate_trajectories(self) -> None:
        """Calculate common trajectories from each starting point."""
        self.starting_points = Counter()
        self.trajectories = defaultdict(list)

        for skier in self.skiers:
            if not skier.trajectory:
                continue

            # Get starting skilift
            start_skilift = skier.trajectory[0].skilift
            self.starting_points[start_skilift] += 1

            # Get sequence of skilifts
            sequence = [
                interaction.skilift for interaction in skier.trajectory]
            self.trajectories[start_skilift].append(sequence)

    def plot_common_trajectories(self, start_skilift: str) -> None:
        """Plot the most common trajectories starting from a specific skilift.

        Args:
            start_skilift: The starting skilift to analyze
        """
        if start_skilift not in self.trajectories:
            print(f"No trajectories found starting from {start_skilift}")
            return

        # Count trajectory frequencies
        trajectory_counts = Counter()
        for trajectory in self.trajectories[start_skilift]:
            trajectory_counts[tuple(trajectory)] += 1

        # Get top trajectories
        top_trajectories = trajectory_counts.most_common(10)

        # Prepare data for visualization
        trajectory_names = []
        frequencies = []
        percentages = []
        total_trajectories = len(self.trajectories[start_skilift])

        for trajectory, count in top_trajectories:
            # Format trajectory as string with arrows
            trajectory_str = ' → '.join(trajectory)
            trajectory_names.append(trajectory_str)
            frequencies.append(count)
            percentages.append(count/total_trajectories*100)

        # Create figure
        fig = go.Figure()

        # Add horizontal bar chart
        fig.add_trace(
            go.Bar(
                y=trajectory_names,
                x=frequencies,
                orientation='h',
                marker_color='rgb(55, 83, 109)',
                text=[f"{count:,} ({pct:.1f}%)" for count, pct in
                      zip(frequencies, percentages)],
                textposition='auto',
            )
        )

        # Update layout
        fig.update_layout(
            title=f'Most Common Trajectories Starting from {start_skilift}',
            xaxis_title='Number of Skiers',
            yaxis_title='Trajectory',
            height=max(400, len(trajectory_names) * 25),
            width=1000,
            showlegend=False,
            bargap=0.2
        )

        # Add hover template
        fig.update_traces(
            hovertemplate="<br>".join([
                "Trajectory: %{y}",
                "Number of Skiers: %{x:,}",
                "Percentage: %{customdata:.1f}%",
                "<extra></extra>"
            ]),
            customdata=percentages
        )

        fig.show()

    def plot_starting_points(self, top_n: int = 15) -> None:
        """Plot the most common starting points for skier trajectories."""
        # Get top N starting points
        top_starts = self.starting_points.most_common(top_n)
        start_names = [lift for lift, _ in top_starts]
        frequencies = [count for _, count in top_starts]
        percentages = [count/sum(self.starting_points.values())*100
                       for count in frequencies]

        # Create figure
        fig = go.Figure()

        # Add horizontal bar chart
        fig.add_trace(
            go.Bar(
                y=start_names,
                x=frequencies,
                orientation='h',
                marker_color='rgb(55, 83, 109)',
                text=[f"{count:,} ({pct:.1f}%)" for count, pct in
                      zip(frequencies, percentages)],
                textposition='auto',
            )
        )

        # Update layout
        fig.update_layout(
            title=f'Top {top_n} Most Common Starting Points',
            xaxis_title='Number of Skiers',
            yaxis_title='Starting Skilift',
            height=max(400, len(start_names) * 25),
            width=1000,
            showlegend=False,
            bargap=0.2
        )

        # Add hover template
        fig.update_traces(
            hovertemplate="<br>".join([
                "Starting Point: %{y}",
                "Number of Skiers: %{x:,}",
                "Percentage: %{customdata:.1f}%",
                "<extra></extra>"
            ]),
            customdata=percentages
        )

        fig.show()


class SimulationStatePlotter:
    """Visualizes the state of the simulation over time."""

    def __init__(self, simulation_history: list[dict]):
        """Initialize with simulation history data.

        Args:
            simulation_history: List of state dictionaries recorded during 
                              simulation
        """
        self.history = simulation_history

    def plot_queue_lengths(self) -> None:
        """Plot queue lengths for all skilifts over time."""
        # Extract timestamps and queue data
        timestamps = [state['timestamp'] for state in self.history]
        skilift_names = list(self.history[0]['skilift_states'].keys())

        # Create figure
        fig = go.Figure()

        # Add line for each skilift
        for skilift in skilift_names:
            queue_lengths = [
                state['skilift_states'][skilift]['queue']
                for state in self.history
            ]
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=queue_lengths,
                    name=skilift,
                    mode='lines',
                    hovertemplate=(
                        "Time: %{x}<br>"
                        "Queue Length: %{y}<br>"
                        "<extra></extra>"
                    )
                )
            )

        # Update layout
        fig.update_layout(
            title='Skilift Queue Lengths Over Time',
            xaxis_title='Time',
            yaxis_title='Queue Length',
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

        fig.show()

    def plot_wait_times(self) -> None:
        """Plot wait times for all skilifts over time."""
        # Extract timestamps and wait time data
        timestamps = [state['timestamp'] for state in self.history]
        skilift_names = list(self.history[0]['skilift_states'].keys())

        # Create figure
        fig = go.Figure()

        # Add line for each skilift
        for skilift in skilift_names:
            wait_times = [
                state['skilift_states'][skilift]['wait_time']
                for state in self.history
            ]
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=wait_times,
                    name=skilift,
                    mode='lines',
                    hovertemplate=(
                        "Time: %{x}<br>"
                        "Wait Time: %{y:.1f} minutes<br>"
                        "<extra></extra>"
                    )
                )
            )

        # Update layout
        fig.update_layout(
            title='Skilift Wait Times Over Time',
            xaxis_title='Time',
            yaxis_title='Wait Time (minutes)',
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

        fig.show()

    def plot_active_skiers(self) -> None:
        """Plot number of active skiers over time."""
        # Extract timestamps and active skier counts
        timestamps = [state['timestamp'] for state in self.history]
        active_skiers = [state['active_skiers'] for state in self.history]

        # Create figure
        fig = go.Figure()

        # Add line for active skiers
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=active_skiers,
                name='Active Skiers',
                mode='lines',
                line=dict(color='rgb(55, 83, 109)', width=3),
                hovertemplate=(
                    "Time: %{x}<br>"
                    "Active Skiers: %{y}<br>"
                    "<extra></extra>"
                )
            )
        )

        # Update layout
        fig.update_layout(
            title='Number of Active Skiers Over Time',
            xaxis_title='Time',
            yaxis_title='Number of Active Skiers',
            height=600,
            width=1000,
            showlegend=False
        )

        fig.show()

    def plot_all_metrics(self) -> None:
        """Plot all key metrics in a single figure with subplots."""
        # Extract timestamps and data
        timestamps = [state['timestamp'] for state in self.history]
        skilift_names = list(self.history[0]['skilift_states'].keys())

        # Create figure with subplots
        fig = go.Figure()

        # Add queue lengths
        for skilift in skilift_names:
            queue_lengths = [
                state['skilift_states'][skilift]['queue']
                for state in self.history
            ]
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=queue_lengths,
                    name=f"{skilift} Queue",
                    mode='lines',
                    hovertemplate=(
                        "Time: %{x}<br>"
                        "Queue Length: %{y}<br>"
                        "<extra></extra>"
                    )
                )
            )

        # Add wait times
        for skilift in skilift_names:
            wait_times = [
                state['skilift_states'][skilift]['wait_time']
                for state in self.history
            ]
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=wait_times,
                    name=f"{skilift} Wait Time",
                    mode='lines',
                    line=dict(dash='dash'),
                    hovertemplate=(
                        "Time: %{x}<br>"
                        "Wait Time: %{y:.1f} minutes<br>"
                        "<extra></extra>"
                    )
                )
            )

        # Add active skiers
        active_skiers = [state['active_skiers'] for state in self.history]
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=active_skiers,
                name='Active Skiers',
                mode='lines',
                line=dict(color='rgb(55, 83, 109)', width=3),
                hovertemplate=(
                    "Time: %{x}<br>"
                    "Active Skiers: %{y}<br>"
                    "<extra></extra>"
                )
            )
        )

        # Update layout
        fig.update_layout(
            title='Simulation State Over Time',
            xaxis_title='Time',
            yaxis_title='Value',
            height=800,
            width=1200,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        fig.show()

    def plot_fill_rates(self) -> None:
        """Plot the fill rate (utilization) of each skilift over time.

        Fill rate is calculated as the number of skiers currently in the lift
        divided by the lift's capacity.
        """
        # Extract timestamps and queue data
        timestamps = [state['timestamp'] for state in self.history]
        skilift_names = list(self.history[0]['skilift_states'].keys())

        # Create figure
        fig = go.Figure()

        # Add line for each skilift
        for skilift in skilift_names:
            # Calculate fill rate as skiers_in_lift/capacity
            skiers_in_lift = [
                state['skilift_states'][skilift]['skiers_in_lift']
                for state in self.history
            ]
            capacity = self.history[0]['skilift_states'][skilift]['capacity']
            fill_rates = [s / capacity for s in skiers_in_lift]

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=fill_rates,
                    name=skilift,
                    mode='lines',
                    hovertemplate=(
                        "Time: %{x}<br>"
                        "Fill Rate: %{y:.1%}<br>"
                        "Skiers in Lift: %{customdata[0]}/{customdata[1]}<br>"
                        "<extra></extra>"
                    ),
                    customdata=list(zip(skiers_in_lift,
                                        [capacity] * len(skiers_in_lift)))
                )
            )

        # Update layout
        fig.update_layout(
            title='Skilift Fill Rates Over Time',
            xaxis_title='Time',
            yaxis_title='Fill Rate',
            height=600,
            width=1000,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            yaxis=dict(
                tickformat='.0%',  # Format y-axis as percentages
                range=[0, 1]  # Set y-axis range from 0 to 100%
            )
        )

        fig.show()
