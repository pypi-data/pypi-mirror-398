
from dataclasses import dataclass
from datetime import datetime
import os
from batem.reno.constants import DATE_FORMAT
from batem.reno.house.creation import (
    HouseBuilder, HouseCreationExperiment, HouseFilePathBuilder)
from batem.reno.house.model import House
from plotly.graph_objects import Scatter, Figure

from batem.reno.plot.base import (
    AxesConfigurator, DataProcessor, FigureSaver, PlotConfig, PlotRenderer)
from batem.reno.pv.model import PVPlant
from batem.reno.utils import (
    TimeSpaceHandler
)


@dataclass
class AppliancesPlotterConfig(PlotConfig):
    """Configuration for appliances plotter."""
    experiment: HouseCreationExperiment
    has_production: bool
    time_space_handler: TimeSpaceHandler
    hourly: bool
    show: bool


@dataclass
class AppliancesData:
    """Data for appliances plotter."""
    house: House
    pv_plant: PVPlant | None = None


@dataclass
class ProcessedAppliancesData:
    """Data for house plotter."""
    appliance_names: list[str]
    consumptions_in_time: list[dict[datetime, float]]
    production: dict[datetime, float]


class AppliancesPlotterDataProcessor(DataProcessor):
    """Data processor for house plotter."""

    def process_data(self, data: AppliancesData,
                     config: AppliancesPlotterConfig
                     ) -> ProcessedAppliancesData:
        """Process the data for the appliances plotter."""

        processed_data = ProcessedAppliancesData(
            appliance_names=[],
            consumptions_in_time=[],
            production=(data.pv_plant.production.usage_hourly
                        if data.pv_plant is not None else {}))

        for appliance in data.house.appliances:
            load = appliance.consumption
            processed_data.appliance_names.append(appliance.name)

            if config.hourly:
                if not load.usage_hourly:
                    print("Warning: No hourly consumption data")
                    continue
                processed_data.consumptions_in_time.append(load.usage_hourly)
            else:
                processed_data.consumptions_in_time.append(load.usage_10min)

        return processed_data


class AppliancesAxesConfigurator(AxesConfigurator):
    """Axes configurator for appliances plotter."""

    def configure_axes(self, fig: Figure, config: AppliancesPlotterConfig):
        """Configure the axes for the appliances plotter."""
        # Update layout
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

    def create_figure(self, config: AppliancesPlotterConfig) -> Figure:
        """Create the figure for the appliances plotter."""
        # Create a single figure
        fig = Figure()  # type: ignore
        return fig


class AppliancePlotRenderer(PlotRenderer):
    """Renderer for appliances plotter."""

    def render_plot(self, fig: Figure, data: ProcessedAppliancesData,
                    config: AppliancesPlotterConfig):
        """Render the plot for the appliances plotter."""
        # Add a line for each appliance
        for appliance_name, consumption in zip(data.appliance_names,
                                               data.consumptions_in_time):
            fig.add_trace(
                Scatter(
                    x=list(consumption.keys()),
                    y=list(consumption.values()),
                    name=f"{appliance_name}",
                    mode='lines'
                )  # type: ignore
            )

        if config.has_production:
            x = list(data.production.keys())
            y = list(data.production.values())
            fig.add_trace(
                Scatter(x=x, y=y, mode='lines',
                        name="Production hourly",
                        )  # type: ignore
            )


class AppliancesFigureSaver(FigureSaver):
    """Figure saver for appliances plotter."""

    def save_figure(self, fig: Figure, config: AppliancesPlotterConfig):
        """Save the figure for the appliances plotter."""
        if config.show:
            fig.show()
        else:
            file_path = config.file_path
            fig.write_html(file_path, auto_open=True)


class HousePlotterFilePathBuilder:
    def __init__(self):
        self.house_path_builder = HouseFilePathBuilder()

    def build_plot_path(self,
                        house: House,
                        experiment: HouseCreationExperiment,
                        config: AppliancesPlotterConfig,
                        appliances: bool = False) -> str:
        """
        Set the file path for the plot.
        If appliances is True, the file path will be for the appliances plot.
        If appliances is False, the file path will be for the house plot.
        If hourly is True, the file path will be for the hourly plot.
        If hourly is False, the file path will be for the 10min plot.
        """
        folder = self.house_path_builder.get_experiment_folder(
            experiment)

        start_time_str = house.time_range.start_time.strftime(
            DATE_FORMAT) if house.time_range.start_time is not None else "_"
        end_time_str = house.time_range.end_time.strftime(
            DATE_FORMAT) if house.time_range.end_time is not None else "_"

        suffix = 'hourly' if config.hourly else '10min'
        prefix = 'appliances' if appliances else 'house'
        if config.has_production:
            prefix = f'{prefix}_with_production'
        file_name = (f"{prefix}_{house.house_id}_from_{start_time_str
                                                       }_to_"
                     f"{end_time_str}_{suffix}.html")
        path = os.path.join(folder, file_name)
        return path


@dataclass
class ProcessedHouseData:
    """Data for house plotter."""
    time: list[datetime]
    consumption: dict[datetime, float]
    production: dict[datetime, float]


class HousePlotterDataProcessor(DataProcessor):
    """Data processor for house plotter."""

    def process_data(self, data: AppliancesData,
                     config: AppliancesPlotterConfig
                     ) -> ProcessedHouseData:
        """Process the data for the house plotter."""
        load = data.house.consumption

        if config.hourly:
            if not load.usage_hourly:
                raise ValueError("No hourly consumption data")
            return ProcessedHouseData(
                time=list(load.usage_hourly.keys()),
                consumption=load.usage_hourly,
                production={})
        else:
            return ProcessedHouseData(
                time=list(load.usage_10min.keys()),
                consumption=load.usage_10min,
                production={})


class HousePlotterPlotRenderer(PlotRenderer):
    """Renderer for house plotter."""

    def render_plot(self, fig: Figure, data: ProcessedHouseData,
                    config: AppliancesPlotterConfig):
        """Render the plot for the house plotter."""
        label = "Consumption hourly" if config.hourly else "Consumption 10min"
        fig.add_trace(
            Scatter(x=list(data.consumption.keys()),
                    y=list(data.consumption.values()), mode='lines',
                    name=label,
                    )  # type: ignore
        )

        if config.has_production:
            fig.add_trace(
                Scatter(x=list(data.production.keys()),
                        y=list(data.production.values()), mode='lines',
                        name="Production hourly",
                        )  # type: ignore
            )


class HousePlotterAxesConfigurator(AxesConfigurator):
    """Axes configurator for house plotter."""

    def configure_axes(self, fig: Figure, config: AppliancesPlotterConfig):
        """Configure the axes for the house plotter."""
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Power [kW]")

    def create_figure(self, config: AppliancesPlotterConfig) -> Figure:
        """Create the figure for the house plotter."""
        fig = Figure()  # type: ignore
        return fig
