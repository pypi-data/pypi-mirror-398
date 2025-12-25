"""
Scheduler for energy community simulation.

This module provides the main simulation scheduler that coordinates the
interaction between community members, PV production, and the energy
manager. It handles the step-by-step execution of the simulation and
exports the results.
"""

import csv
from typing import Any
from batem.reno.community.creation import PVCommunityBuilder
from batem.reno.community.model import EnergyCommunity
from batem.reno.constants import MANAGER_TYPE
from batem.reno.pv.creation import WeatherDataBuilder
from batem.reno.simulation.manager.model import AdaptiveManager, BasicManager, ReactiveManager
from batem.reno.simulation.member.model import Member
from batem.reno.simulation.scenario import Scenario
from batem.reno.utils import FilePathBuilder, TimeSpaceHandler, parse_args


class Scheduler:
    """
    Main scheduler for energy community simulation.

    This class coordinates the simulation of an energy community,
    managing the interaction between community members, PV production,
    and the energy manager. It executes the simulation step by step
    and handles result export.

    Attributes:
        community: Energy community being simulated
        scenario: Simulation scenario configuration
        steps: Total number of simulation steps (hours)
        k: Current simulation step
        manager: Energy system manager
        members: List of community members
    """

    def __init__(self, community: EnergyCommunity, scenario: Scenario):
        """
        Initialize the scheduler.

        The number of steps is determined by the number of hours in the
        simulation period, defined by the time space handler of the
        community.

        Args:
            community: Energy community to simulate
            scenario: Simulation scenario configuration

        Example:
            >>> scheduler = Scheduler(community, scenario)
        """
        self.community = community
        self.scenario = scenario
        self.steps = len(self.community.time_space_handler.range_hourly)
        self.k = 0

        self._build_manager()
        self.members = self._build_members()

    def _build_manager(self):
        """
        Build the manager based on the scenario.
        """
        ts_handler = self.community.time_space_handler
        indication_interval = self.scenario.indication_interval
        if self.scenario.manager_type == MANAGER_TYPE.BASIC:
            self.manager = BasicManager(ts_handler, indication_interval)
        elif self.scenario.manager_type == MANAGER_TYPE.REACTIVE:
            self.manager = ReactiveManager(ts_handler, indication_interval)
        elif self.scenario.manager_type == MANAGER_TYPE.ADAPTIVE:
            self.manager = AdaptiveManager(ts_handler, indication_interval)
        else:
            raise ValueError(
                f"Invalid manager type: {self.scenario.manager_type}")

    def _build_members(self) -> list[Member]:
        """
        Create Member instances for all houses in the community.
        """
        members: list[Member] = []
        for house in self.community.houses:
            member = Member(
                self.community.time_space_handler,
                house)
            members.append(member)
        return members

    def run(self, write_results: bool = True, print_info: bool = True):
        """
        Run the complete simulation step by step.

        Each step represents one hour of simulation time. The simulation
        progresses through all steps, updating member states and
        generating recommendations. Results are exported to CSV and the
        scenario is saved to JSON at the end.

        Example:
            >>> scheduler.run()
        """
        ts_handler = self.community.time_space_handler
        for k in range(self.steps):
            timestamp = ts_handler.get_datetime_from_k(k)
            if print_info:
                print(f"Step {k} ({timestamp}) of {self.steps}")
            self._step(k)

        if write_results:
            self.to_csv()
            self.scenario.to_json()

    def _step(self, k: int):
        """
        Execute a single simulation step.

        For each step:
        1. Get recommendation from the manager
        2. Update each member's state based on the recommendation

        Args:
            k: Current simulation step index
        """
        recommendation = self.manager.step(
            k=k,
            members=self.members,
            pv=self.community.pv_plant)

        for member in self.members:
            member.step(k, recommendation)

        if isinstance(self.manager, ReactiveManager):
            extra_recommendation = self.manager.extra_step(
                k=k,
                members=self.members,
                pv=self.community.pv_plant)

            for member in self.members:
                member.extra_step(k, extra_recommendation)

    def to_csv(self):
        """
        Export simulation results to a CSV file.

        The CSV file contains the following columns:
        - timestamp: Simulation timestamp
        - exp_{house_id}: Expected consumption for each house
        - sim_{house_id}: Simulated consumption for each house
        - manager: Manager's recommendation
        - pv: PV production value

        The file is saved in the simulation results folder with a name
        based on the location and time range.
        """
        file_path = FilePathBuilder().get_simulation_results_path(
            self.community.time_space_handler,
            self.scenario.manager_type)

        header = ["timestamp"]
        for member in self.members:
            header.append(f"presence_{member.house.house_id}")
            header.append(f"exp_{member.house.house_id}")
            header.append(f"sim_{member.house.house_id}")

        header.append("manager")
        header.append("pv")

        with open(file_path, "w") as f:
            writer = csv.writer(f)

            writer.writerow(header)

            ts_handler = self.community.time_space_handler

            for k in range(self.steps):
                timestamp = ts_handler.get_datetime_from_k(k)

                result: dict[Any, Any] = {'timestamp': timestamp}

                for member in self.members:
                    h_id = member.house.house_id
                    result[f"presence_{h_id}"] = member.presence[timestamp]
                    result[f"exp_{h_id}"] = member.exp_consumption[timestamp]
                    result[f"sim_{h_id}"] = member.sim_consumption[timestamp]

                result["manager"] = (
                    self.manager.recommendations[timestamp].type.value)
                result["pv"] = (
                    self.community.pv_plant.power_production_hourly[timestamp])

                writer.writerow(result.values())


if __name__ == "__main__":

    # python batem/reno/simulation/scheduler/model.py --manager_type reactive

    args = parse_args()

    manager_type = MANAGER_TYPE(args.manager_type)
    print(f"Manager type: {manager_type}")

    time_space_handler = TimeSpaceHandler(
        location=args.location,
        start_date=args.start_date,
        end_date=args.end_date)

    exposure_deg = 0.0
    slope_deg = 152.0

    weather_data = WeatherDataBuilder().build(
        location=time_space_handler.location,
        latitude_north_deg=time_space_handler.latitude_north_deg,
        longitude_east_deg=time_space_handler.longitude_east_deg,
        from_datetime_string=time_space_handler.start_date,
        to_datetime_string=time_space_handler.end_date)

    community = PVCommunityBuilder(time_space_handler
                                   ).build(
        weather_data=weather_data,
        panel_peak_power_kW=args.peak_power_kW,
        number_of_panels=args.number_of_panels,
        exposure_deg=exposure_deg,
        slope_deg=slope_deg,
        regenerate_consumption=False,
        exclude_houses=[2000926, 2000927, 2000928])

    scenario = Scenario(
        location=args.location,
        start_date=args.start_date,
        end_date=args.end_date,
        house_ids=[house.house_id for house in community.houses],
        pv_number_of_panels=args.number_of_panels,
        pv_panel_height_m=community.pv_plant.panel_height_m,
        pv_panel_width_m=community.pv_plant.panel_width_m,
        pv_exposure_deg=exposure_deg,
        pv_slope_deg=slope_deg,
        pv_peak_power_kW=args.peak_power_kW,
        pv_mount_type=community.pv_plant.mount_type,
        indication_interval=[7, 22],
        manager_type=manager_type
    )

    Scheduler(community, scenario).run()
