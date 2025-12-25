import os
from batem.reno.community.creation import PVCommunityBuilder
from batem.reno.community.model import EnergyCommunity
from plotly.graph_objects import Figure, Scatter

from batem.reno.utils import FilePathBuilder, TimeSpaceHandler, parse_args


class CommunityPlotter:
    def __init__(self):
        pass

    def plot(self, community: EnergyCommunity, show: bool = False):

        fig = Figure()  # type: ignore

        # Add a line for each appliance
        for house in community.houses:
            time = community.time_space_handler.range_hourly
            consumption = tuple(house.total_consumption_hourly.values())
            label = f"house {house.house_id}"

            fig.add_trace(
                Scatter(
                    x=time,
                    y=consumption,
                    name=label,
                    mode='lines'
                )  # type: ignore
            )

        time = community.time_space_handler.range_hourly
        consumption = tuple(community.total_consumption.values())
        label = "community"

        fig.add_trace(
            Scatter(
                x=time,
                y=consumption,
                name="community",
                mode='lines'
            )  # type: ignore
        )

        production = list(community.pv_plant.power_production_hourly.values())
        fig.add_trace(
            Scatter(
                x=time,
                y=production,
                name="pv",
                mode='lines'
            )  # type: ignore
        )
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Power [kW]",
            height=800,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99)
        )

        if show:
            fig.show()
        else:
            path = CommunityPlotBuilder().set_file_path(community)
            fig.write_html(path, auto_open=True)


class CommunityPlotBuilder:
    def __init__(self):
        pass

    def set_file_path(self, community: EnergyCommunity) -> str:
        name = "community"
        name = f"{name}_{community.time_space_handler.location}"
        name = f"{name}_from_{community.time_space_handler.start_time}_"
        name = f"{name}_to_{community.time_space_handler.end_time}"
        name = f"{name}.html"
        folder = FilePathBuilder().get_plots_folder()
        file_path = os.path.join(folder, name)
        return file_path


if __name__ == "__main__":
    # python batem/reno/plot/community.py

    args = parse_args()

    time_space_handler = TimeSpaceHandler(
        location=args.location,
        start_date=args.start_date,
        end_date=args.end_date)

    community = PVCommunityBuilder(time_space_handler
                                   ).build(
        panel_peak_power_kW=8,
        number_of_panels=1,
        panel_height_m=1,
        panel_width_m=1,
        exposure_deg=0.0,
        slope_deg=152.0)

    CommunityPlotter().plot(community)
