import os
import plotly.graph_objects as go
from batem.reno.constants import DATE_FORMAT
from batem.reno.pv.creation import PVPlantBuilder, WeatherDataBuilder
from batem.reno.pv.model import PVPlant

from batem.reno.utils import (
    FilePathBuilder,
    TimeSpaceHandler,
    parse_args
)


class PVPlotter:

    def __init__(self):
        pass

    def plot_production(self, pv_plant: PVPlant, best_angles: bool = False):

        time = list(pv_plant.power_production_hourly.keys())
        production = tuple(pv_plant.power_production_hourly.values())
        title = "Total Production"

        if best_angles:
            title = f"{title} - Best Angles"

        fig = go.Figure()  # type: ignore
        fig.add_trace(
            go.Scatter(x=time,
                       y=production,
                       mode='lines',
                       name="Production",
                       )  # type: ignore
        )

        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Power [kW]")

        file_path = PVPlotBuilder().set_file_path(pv_plant, best_angles)
        fig.write_html(file_path, auto_open=True)


class PVPlotBuilder:
    def __init__(self):
        pass

    def set_file_path(self,
                      pv_plant: PVPlant,
                      best_angles: bool = False) -> str:
        """
        Set the file path for the plot.
        """
        start_time_str = list(pv_plant.power_production_hourly.keys())[
            0].strftime(DATE_FORMAT)
        end_time_str = list(pv_plant.power_production_hourly.keys())[
            -1].strftime(DATE_FORMAT)
        folder = FilePathBuilder().get_plots_folder()
        name = "pv_plant"
        name = f"{name}_{pv_plant.weather_data.location}"
        name = f"{name}_from_{start_time_str}_to_{end_time_str}"
        if best_angles:
            name = f"{name}_best_angles"
        name = f"{name}.html"

        file_path = os.path.join(folder, name)
        return file_path


if __name__ == "__main__":
    # python batem/reno/plot/pv.py --location Grenoble
    args = parse_args()

    time_space_handler = TimeSpaceHandler(location=args.location,
                                          start_date="01/01/2021",
                                          end_date="31/12/2021")

    peak_power = 8
    number_of_panels = 1

    weather_data = WeatherDataBuilder().build(
        location=time_space_handler.location,
        latitude_north_deg=time_space_handler.latitude_north_deg,
        longitude_east_deg=time_space_handler.longitude_east_deg,
        from_datetime_string=time_space_handler.start_date,
        to_datetime_string=time_space_handler.end_date)

    pv_plant = PVPlantBuilder().build(
        time_space_handler=time_space_handler,
        weather_data=weather_data,
        peak_power_kW=peak_power,
        number_of_panels=number_of_panels,
        exposure_deg=0,
        slope_deg=160)

    PVPlotter().plot_production(pv_plant)

    best_exposure, best_slope = pv_plant.solar_model.best_angles()
    print(f'Best exposure: {best_exposure}°, best slope: {best_slope}°')

    best_pv_plant = PVPlantBuilder().build(
        time_space_handler=time_space_handler,
        weather_data=weather_data,
        exposure_deg=float(best_exposure),
        slope_deg=float(best_slope),
        peak_power_kW=peak_power,
        number_of_panels=number_of_panels)

    PVPlotter().plot_production(best_pv_plant, best_angles=True)
