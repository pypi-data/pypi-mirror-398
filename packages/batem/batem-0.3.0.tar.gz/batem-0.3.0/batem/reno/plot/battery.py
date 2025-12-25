from dataclasses import dataclass
from typing import Any
import matplotlib.pyplot as plt
from batem.reno.plot.base import (
    AxesConfigurator, DataProcessor, FigureSaver, PlotConfig, PlotRenderer)
from batem.reno.battery.model import BatterySimulationResult, BatteryState
from plotly.graph_objects import Scatter


@dataclass
class BatteryPlotConfig(PlotConfig):
    """Configuration for battery plot."""


class BatteryDataProcessor(DataProcessor):
    """Data processor for battery plot."""

    def process_data(self, data: BatterySimulationResult,
                     config: BatteryPlotConfig) -> Any:
        """Process the data for the battery plot."""
        return {
            "production": data.pv_plant.production.usage_hourly,
            "consumption": data.house.consumption.usage_hourly,
            "battery_state_history": data.battery._state_history,
            "initial_indicators": data.initial_indicators,
            "final_indicators": data.final_indicators,
        }


class BatteryAxesConfigurator(AxesConfigurator):
    """Axes configurator for battery plot."""

    def configure_axes(self, fig: Any, config: BatteryPlotConfig):
        """Configure the axes for the battery plot."""
        fig[0].suptitle("Battery Simulation Results")

        axes = fig[1]
        ax1, ax2 = axes

        # Configure first subplot (production vs consumption)
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Power (kW)")
        ax1.set_title("Production vs Consumption")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Configure second subplot (battery SOC)
        ax2.set_xlabel("Time")
        ax2.set_ylabel("State of Charge (SOC)")
        ax2.set_title("Battery State of Charge")
        ax2.grid(True, alpha=0.3)

    def create_figure(self, config: BatteryPlotConfig) -> Any:
        """Create the figure for the battery plot."""
        fig = plt.subplots(nrows=2, ncols=1, figsize=config.size)
        return fig


class BatteryRenderer(PlotRenderer):
    """Renderer for battery plot."""

    def render_plot(self, fig: Any, data: Any, config: BatteryPlotConfig):
        """Render the plot for the battery."""
        production = data["production"]
        consumption = data["consumption"]
        battery_state_history: list[BatteryState] = (
            data["battery_state_history"])

        axes = fig[1]
        ax1, ax2 = axes

        # Extract datetime keys and values for time series plotting

        time_keys = sorted(consumption.keys())
        production_values = [production[t] for t in time_keys]
        consumption_values = [consumption[t] for t in time_keys]
        battery_power_values = [state.power for state in battery_state_history]

        ax1.plot(time_keys, production_values, label='Production')
        ax1.plot(time_keys, consumption_values, label='Consumption')
        ax1.plot(time_keys, battery_power_values, label='Battery Power')

        # Battery history is a list of SOC values
        soc_values = [state.soc for state in battery_state_history]

        command_values = [
            state.command.value for state in battery_state_history]
        ax2.plot(time_keys, soc_values, label='Battery SOC', color='orange')
        ax2.plot(time_keys, command_values,
                 label='Battery Command', color='red')

        self._add_indicators_annotation(data, ax1)

    def _add_indicators_annotation(self, data: Any, ax1: Any):
        initial_indicators = data["initial_indicators"]
        final_indicators = data["final_indicators"]
        # Add indicators text box
        indicators_text = (
            "Initial Indicators:\n"
            f"NEEG: {initial_indicators.neeg_value:.3f}\n"
            f"SC: {initial_indicators.sc_value:.3f}\n"
            f"SS: {initial_indicators.ss_value:.3f}\n"
            f"OPEX: {initial_indicators.opex_cost_value:.3f}\n\n"
            "Final Indicators:\n"
            f"NEEG: {final_indicators.basic_indicators.neeg_value:.3f}\n"
            f"SC: {final_indicators.basic_indicators.sc_value:.3f}\n"
            f"SS: {final_indicators.basic_indicators.ss_value:.3f}\n"
            f"OPEX: {final_indicators.basic_indicators.opex_cost_value:.3f}\n"
            f"Battery Protection: {final_indicators.battery_protection_value:.2f}\n"
            f"Battery Variation: {final_indicators.battery_variation_value:.2f}"
        )

        # Add text box to the first subplot
        ax1.text(0.02, 0.98, indicators_text, transform=ax1.transAxes,
                 fontsize=8, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))


class BatteryFigureSaver(FigureSaver):
    """Figure saver for battery plot."""

    def save_figure(self, fig: Any, config: BatteryPlotConfig):
        """Save the figure for the battery."""
        file_path = config.file_path
        if config.as_png:
            fig[0].savefig(file_path, format='png',
                           dpi=500, bbox_inches='tight')
        else:
            fig[0].savefig(file_path, format='pdf', bbox_inches='tight')


class InteractiveAxesConfigurator(AxesConfigurator):
    """Interactive axes configurator for battery plot."""

    def configure_axes(self, fig: Any, config: BatteryPlotConfig):
        """Configure the axes for the battery plot."""
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Power [kW]",
            height=800,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            )
        )

    def create_figure(self, config: BatteryPlotConfig) -> Any:
        """Create the figure for the battery plot."""
        from plotly.subplots import make_subplots
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True)
        return fig


class InteractiveRenderer(PlotRenderer):
    """Interactive renderer for battery plot."""

    def render_plot(self, fig: Any, data: Any, config: BatteryPlotConfig):
        """Render the plot for the battery."""
        production = data["production"]
        consumption = data["consumption"]
        battery_state_history = data["battery_state_history"]

        time = sorted(consumption.keys())
        consumption_values = [consumption[t] for t in time]
        production_values = [production[t] for t in time]
        battery_power_values = [state.power for state in battery_state_history]
        grid_power_values = [
            consumption[t] - production[t] - battery_power_values[i]
            for i, t in enumerate(time)]

        names = ["Consumption", "Production", "Battery Power", "Grid Power"]

        for power_series, name in zip(
                [consumption_values,
                 production_values,
                 battery_power_values,
                 grid_power_values], names):
            fig.add_trace(
                Scatter(
                    x=time,
                    y=power_series,
                    name=name,
                    mode='lines'
                ),  # type: ignore
                row=1,
                col=1
            )

        command_values = [
            state.command.value for state in battery_state_history]
        fig.add_trace(
            Scatter(
                x=time,
                y=command_values,
                name="Battery Command",
                mode='lines'
            ),  # type: ignore
            row=2,
            col=1
        )

        soc_values = [state.soc for state in battery_state_history]
        fig.add_trace(
            Scatter(
                x=time,
                y=soc_values,
                name="Battery SOC",
                mode='lines'
            ),  # type: ignore
            row=3,
            col=1
        )
        self._add_indicators_annotation(fig, data)

    def _add_indicators_annotation(self, fig: Any, data: Any):
        initial_indicators = data["initial_indicators"]
        final_indicators = data["final_indicators"]
        # Add indicators annotation
        indicators_text = (
            "<b>Initial Indicators:</b><br>"
            f"NEEG: {initial_indicators.neeg_value:.3f}<br>"
            f"SC: {initial_indicators.sc_value:.3f}<br>"
            f"SS: {initial_indicators.ss_value:.3f}<br>"
            f"OPEX: {initial_indicators.opex_cost_value:.3f}<br><br>"
            "<b>Final Indicators:</b><br>"
            f"NEEG: {final_indicators.basic_indicators.neeg_value:.3f}<br>"
            f"SC: {final_indicators.basic_indicators.sc_value:.3f}<br>"
            f"SS: {final_indicators.basic_indicators.ss_value:.3f}<br>"
            f"OPEX: {final_indicators.basic_indicators.opex_cost_value:.3f}<br>"
            f"Battery Protection: {final_indicators.battery_protection_value:.2f}<br>"
            f"Battery Variation: {final_indicators.battery_variation_value:.2f}"
        )

        fig.add_annotation(
            text=indicators_text,
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            xanchor="left", yanchor="top",
            showarrow=False,
            font=dict(size=10),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1
        )


class InteractiveFigureSaver(FigureSaver):
    """Interactive figure saver for battery plot."""

    def save_figure(self, fig: Any, config: BatteryPlotConfig):
        """Save the figure for the battery."""
        file_path = config.file_path
        fig.write_html(file_path, auto_open=True)
