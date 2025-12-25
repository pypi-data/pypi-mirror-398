
from dataclasses import dataclass
from datetime import datetime
import os
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from typing import Any, override
from batem.core.library import DIRECTIONS_SREF, SLOPES
from batem.core.solar import EXTRA_DIRECTIONS, SolarModel
from batem.core.weather import SiteWeatherData
from batem.core.weather import SWDbuilder
from batem.reno.plot.base import (
    AxesConfigurator, DataProcessor, FigureSaver,
    PlotConfig, PlotRenderer, Plotter)
from batem.reno.utils import FilePathBuilder, TimeSpaceHandler


@dataclass
class AnglePlotConfig(PlotConfig):
    """Configuration for angle plot."""
    selected_day: datetime | None = None


class AngleDataProcessor(DataProcessor):

    def process_data(self, data: SolarModel, config: AnglePlotConfig
                     ) -> tuple[list[datetime], list[float], list[float]]:

        times = data.datetimes
        altitudes = data.altitudes_deg
        azimuths = data.azimuths_deg

        if config.selected_day is not None:
            # Find indices in the original arrays that match the selected day
            indices = [i for i, t in enumerate(times)
                       if t.day == config.selected_day.day
                       and t.month == config.selected_day.month
                       and t.year == config.selected_day.year]

            # Filter all arrays using the same indices
            times = [times[i] for i in indices]
            altitudes = [altitudes[i] for i in indices]
            azimuths = [azimuths[i] for i in indices]

        return times, altitudes, azimuths


class AngleAxesConfigurator(AxesConfigurator):

    def configure_axes(self, fig: Any, config: AnglePlotConfig):

        if config.selected_day is not None:
            fig[0].suptitle("Angle plot for " +
                            config.selected_day.strftime("%Y-%m-%d"))
        else:
            fig[0].suptitle("Angle plots")

        ax1, ax2 = fig[1]
        ax1.set_ylabel('Altitude (deg)')
        ax1.set_xlabel('Time')
        ax1.legend()
        ax1.grid()

        ax2.set_ylabel('Azimuth (deg)')
        ax2.set_xlabel('Time')
        ax2.set_ylim(-180, 180)
        ax2.legend()
        ax2.grid()

    def create_figure(self, config: AnglePlotConfig) -> Any:
        fig = plt.subplots(nrows=2, ncols=1, figsize=config.size)
        return fig


class AngleRenderer(PlotRenderer):

    def render_plot(self, fig: Any,
                    data: tuple[list[datetime], list[float], list[float]]):
        # Plot altitude and azimuth on separate subplots
        times, altitudes, azimuths = data
        # fig is a tuple (figure, axes)
        axes = fig[1]
        ax1, ax2 = axes

        ax1.plot(times, altitudes, label='Altitude (deg)')

        ax2.plot(times, azimuths, label='Azimuth (deg)', color='orange')


class AngleFigureSaver(FigureSaver):

    def save_figure(self, fig: Figure, config: AnglePlotConfig):
        file_path = config.file_path
        if config.as_png:
            fig.savefig(file_path, format='png', dpi=500, bbox_inches='tight')
        else:
            fig.savefig(file_path, format='pdf', bbox_inches='tight')


@dataclass
class CardinalIrradiancePlotConfig(PlotConfig):
    """Configuration for cardinal irradiance plot."""
    direction: SLOPES | DIRECTIONS_SREF


class CardinalIrradianceDataProcessor(DataProcessor):
    def process_data(self, data: Any, config: CardinalIrradiancePlotConfig):
        return data


class CardinalIrradianceRenderer(PlotRenderer):
    def render_plot(self, fig: Any, data: Any):
        axes = fig[1]
        axes.plot(data)


class CardinalIrradianceAxesConfigurator(AxesConfigurator):
    def configure_axes(self, fig: Any, config: CardinalIrradiancePlotConfig):
        fig[0].suptitle(config.direction.name)
        fig[1].set_xlabel('Time')
        fig[1].set_ylabel('Irradiance (W/m²)')
        fig[1].grid()
        fig[1].set_ylim(0, 1000)

    def create_figure(self, config: CardinalIrradiancePlotConfig) -> Any:
        fig = plt.subplots(nrows=1, ncols=1, figsize=config.size)
        return fig


class CardinalIrradianceFigureSaver(FigureSaver):
    def save_figure(self, fig: Figure, config: CardinalIrradiancePlotConfig):
        file_path = config.file_path
        fig.savefig(file_path, format='png', dpi=500, bbox_inches='tight')


def build_solar_model(location: str):
    time_space_handler = TimeSpaceHandler(location=location,
                                          start_date="01/01/2021",
                                          end_date="31/12/2021")
    weather_data_builder = SWDbuilder(
        location=location,
        latitude_north_deg=time_space_handler.latitude_north_deg,
        longitude_east_deg=time_space_handler.longitude_east_deg
    )
    weather_data = weather_data_builder(
        from_stringdate=time_space_handler.start_date,
        to_stringdate=time_space_handler.end_date
    )
    solar_model = SolarModel(weather_data)
    return solar_model


@dataclass
class WeatherPlotConfig(PlotConfig):
    """Configuration for weather plot."""
    variables: list[str]
    irradiance_variables: list[str]


class WeatherDataProcessor(DataProcessor):

    @override
    def process_data(self, data: Any, config: WeatherPlotConfig):
        return data


class WeatherRenderer(PlotRenderer):
    def render_plot(self, fig: Any, data: SiteWeatherData,
                    config: WeatherPlotConfig):
        axes = fig[1]
        for i in range(5):
            subplot_axes = axes[i]
            for variable in config.variables:
                weather_variables_in_time = data.get(variable)
                subplot_axes.plot(weather_variables_in_time)
                subplot_axes.set_ylabel(variable)
            for variable in config.irradiance_variables:
                irradiance_variables_in_time = data.get(variable)
                subplot_axes.plot(irradiance_variables_in_time)


class WeatherAxesConfigurator(AxesConfigurator):
    def configure_axes(self, fig: Any, config: WeatherPlotConfig):
        fig[0].suptitle(config.variables + config.irradiance_variables)
        axes = fig[1]
        axes.set_xlabel('Time')
        axes.set_ylabel('Value')
        axes.grid()

    def create_figure(self, config: WeatherPlotConfig) -> Any:
        fig = plt.subplots(nrows=5, ncols=1, figsize=config.size)
        return fig


class WeatherFigureSaver(FigureSaver):
    def save_figure(self, fig: Figure, config: WeatherPlotConfig):
        file_path = config.file_path
        fig.savefig(file_path, format='png', dpi=500, bbox_inches='tight')


def plot_angles(location: str):

    solar_model = build_solar_model(location)

    folder = FilePathBuilder().get_simulation_plots_folder()
    name = 'angle_plot'
    name_with_location = name + '_' + location
    file_path = os.path.join(folder, name_with_location + '.png')

    plotter = Plotter(AnglePlotConfig(as_png=True,
                                      file_path=file_path,
                                      size=(10, 8),
                                      selected_day=None),
                      data_processor=AngleDataProcessor(),
                      renderer=AngleRenderer(),
                      axes_configurator=AngleAxesConfigurator(),
                      figure_saver=AngleFigureSaver())
    plotter.plot(solar_model)


def plot_angles_one_day(location: str, day: datetime):

    solar_model = build_solar_model(location)

    folder = FilePathBuilder().get_simulation_plots_folder()
    name = 'angle_plot'
    name_with_location = name + '_' + location
    name_with_day = name_with_location + '_day_' + day.strftime("%Y-%m-%d")
    file_path = os.path.join(folder, name_with_day + '.png')

    plotter = Plotter(AnglePlotConfig(as_png=True,
                                      file_path=file_path,
                                      size=(10, 8),
                                      selected_day=day),
                      data_processor=AngleDataProcessor(),
                      renderer=AngleRenderer(),
                      axes_configurator=AngleAxesConfigurator(),
                      figure_saver=AngleFigureSaver())
    plotter.plot(solar_model)


def plot_heliodon(location: str):

    solar_model = build_solar_model(location)
    axes = solar_model.plot_heliodon(year=2021)
    fig = axes.get_figure()

    folder = FilePathBuilder().get_simulation_plots_folder()
    name = 'heliodon_plot'
    name_with_location = name + '_' + location
    file_path = os.path.join(folder, name_with_location + '.png')

    if fig is not None and isinstance(fig, Figure):
        fig.savefig(file_path, format='png', dpi=500, bbox_inches='tight')
    else:
        raise ValueError("No figure found")


def plot_cardinal_irradiances(location: str):
    solar_model = build_solar_model(location)

    irradiances_W = solar_model.cardinal_irradiances_W

    folder = FilePathBuilder().get_simulation_plots_folder()
    name = 'cardinal_irradiances_plot'
    name_with_location = name + '_' + location
    for direction in list(irradiances_W.keys()):

        name_with_direction = name_with_location + '_' + direction.name
        file_path = os.path.join(folder, name_with_direction + '.png')

        Plotter(CardinalIrradiancePlotConfig(as_png=True,
                                             file_path=file_path,
                                             size=(10, 5),
                                             direction=direction),
                data_processor=CardinalIrradianceDataProcessor(),
                renderer=CardinalIrradianceRenderer(),
                axes_configurator=CardinalIrradianceAxesConfigurator(),
                figure_saver=CardinalIrradianceFigureSaver()).plot(
                    irradiances_W[direction])

    best_exposure, best_slope = solar_model.best_angles()

    print("For location: ", location, " best exposure: ",
          best_exposure, " best slope: ", best_slope)
    name_with_location = name + '_' + location
    name_with_direction = name_with_location + '_best_angles'
    file_path = os.path.join(folder, name_with_direction + '.png')
    irradiances_W[EXTRA_DIRECTIONS.BEST] = solar_model.irradiances_W(
        best_exposure, best_slope)  # type: ignore
    Plotter(CardinalIrradiancePlotConfig(
        as_png=True,
        file_path=file_path,
        size=(10, 5),
        direction=EXTRA_DIRECTIONS.BEST),  # type: ignore
        data_processor=CardinalIrradianceDataProcessor(),
        renderer=CardinalIrradianceRenderer(),
        axes_configurator=CardinalIrradianceAxesConfigurator(),
        figure_saver=CardinalIrradianceFigureSaver()).plot(
        irradiances_W[EXTRA_DIRECTIONS.BEST])  # type: ignore


def plot_weather(location: str):
    solar_model = build_solar_model(location)

    folder = FilePathBuilder().get_simulation_plots_folder()
    name = 'weather_plot'
    name_with_location = name + '_' + location
    file_path = os.path.join(folder, name_with_location + '.png')

    Plotter(WeatherPlotConfig(as_png=True,
                              file_path=file_path,
                              size=(10, 5),
                              variables=[
                                  'cloudiness', 'temperature'],
                              irradiance_variables=['rhi', 'ghi', 'dhi']),
            data_processor=WeatherDataProcessor(),
            renderer=WeatherRenderer(),
            axes_configurator=WeatherAxesConfigurator(),
            figure_saver=WeatherFigureSaver()).plot(solar_model)


if __name__ == "__main__":

    # python -m batem.reno.plot.weather

    for location in ["Bucharest"]:

        # plot_cardinal_irradiances(location=location)
        plot_weather(location=location)

        exit()

        plot_heliodon(location=location)

        plot_angles(location=location)

        plot_angles_one_day(location=location,
                            day=datetime(year=2021, month=7, day=3))

        plot_angles_one_day(location=location,
                            day=datetime(year=2021, month=1, day=3))
