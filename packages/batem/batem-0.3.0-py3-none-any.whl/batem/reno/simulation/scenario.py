"""
Scenario management for renewable energy simulations.

This module provides classes for managing simulation scenarios, including
PV system configurations and simulation parameters. It handles the
serialization and deserialization of scenarios to/from JSON files.
"""

import json
import os
from batem.core import solar
from batem.reno.constants import MANAGER_TYPE
from batem.reno.utils import (FilePathBuilder, TimeSpaceHandler,
                              parse_args)


class Scenario:
    """
    Represents a simulation scenario with PV system configuration.

    This class encapsulates all parameters needed for a renewable energy
    simulation, including location, time range, house IDs, and PV system
    specifications.

    Attributes:
        location: Name of the simulation location
        start_date: Start date in DD/MM/YYYY format
        end_date: End date in DD/MM/YYYY format
        house_ids: List of house IDs to include in simulation
        pv_number_of_panels: Number of PV panels in the system
        pv_panel_height_m: Height of each PV panel in meters
        pv_panel_width_m: Width of each PV panel in meters
        pv_exposure_deg: Panel exposure angle in degrees
        pv_slope_deg: Panel slope angle in degrees
        pv_peak_power_kW: Peak power output of the PV system in kW
        pv_mount_type: Type of PV panel mounting (from solar.MOUNT_TYPES)
        indication_interval: Interval of the day when indications are valid
    """

    def __init__(self,
                 location: str,
                 start_date: str,
                 end_date: str,
                 house_ids: list[int],
                 pv_number_of_panels: int,
                 pv_panel_height_m: float,
                 pv_panel_width_m: float,
                 pv_exposure_deg: float,
                 pv_slope_deg: float,
                 pv_peak_power_kW: float,
                 manager_type: MANAGER_TYPE,
                 pv_mount_type: solar.MOUNT_TYPES,
                 indication_interval: list[int] = [7, 22]):
        """
        Initialize a new simulation scenario.

        Args:
            location: Name of the simulation location
            start_date: Start date in DD/MM/YYYY format
            end_date: End date in DD/MM/YYYY format
            house_ids: List of house IDs to include in simulation
            pv_number_of_panels: Number of PV panels in the system
            pv_panel_height_m: Height of each PV panel in meters
            pv_panel_width_m: Width of each PV panel in meters
            pv_exposure_deg: Panel exposure angle in degrees
            pv_slope_deg: Panel slope angle in degrees
            pv_peak_power_kW: Peak power output of the PV system in kW
            manager_type: Type of manager to use
            pv_mount_type: Type of PV panel mounting
            indication_interval: Interval of the day when indications are valid

        Example:
            >>> scenario = Scenario(
            ...     location="Grenoble",
            ...     start_date="01/01/2023",
            ...     end_date="01/02/2023",
            ...     house_ids=[1, 2, 3],
            ...     pv_number_of_panels=10,
            ...     pv_panel_height_m=1.7,
            ...     pv_panel_width_m=1.0,
            ...     pv_exposure_deg=180.0,
            ...     pv_slope_deg=30.0,
            ...     pv_peak_power_kW=3.0,
            ...     pv_mount_type=solar.MOUNT_TYPES.FLAT,
            ...     manager_type=MANAGER_TYPE.BASIC,
            ...     indication_interval=[8, 18]
        """
        self.location = location
        self.start_date = start_date
        self.end_date = end_date
        self.house_ids = house_ids
        self.pv_number_of_panels = pv_number_of_panels
        self.pv_panel_height_m = pv_panel_height_m
        self.pv_panel_width_m = pv_panel_width_m
        self.pv_exposure_deg = pv_exposure_deg
        self.pv_slope_deg = pv_slope_deg
        self.pv_peak_power_kW = pv_peak_power_kW
        self.pv_mount_type = pv_mount_type
        self.indication_interval = indication_interval
        self.manager_type = manager_type

    def to_json(self):
        """
        Save the scenario configuration to a JSON file.

        The file is saved in the simulation results folder with a name
        based on the location and time range.

        Example:
            >>> scenario.to_json()
        """
        data = {k: v for k, v in self.__dict__.items()
                if k not in ['pv_mount_type', 'manager_type']}
        data['pv_mount_type'] = self.pv_mount_type.value
        data['manager_type'] = self.manager_type.value
        time_space_handler = TimeSpaceHandler(
            location=self.location,
            start_date=self.start_date,
            end_date=self.end_date)
        file_path = FilePathBuilder().get_scenario_path(
            time_space_handler,
            self.manager_type,
            self.pv_number_of_panels,
            self.pv_peak_power_kW)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def delete_results(self, time_space_handler: TimeSpaceHandler,
                       manager_type: MANAGER_TYPE):
        """
        Delete the results of the scenario.
        """
        file_path = FilePathBuilder().get_simulation_results_path(
            time_space_handler,
            manager_type)
        if os.path.exists(file_path):
            os.remove(file_path)

        scenario_path = FilePathBuilder().get_scenario_path(
            time_space_handler,
            manager_type,
            self.pv_number_of_panels,
            self.pv_peak_power_kW)
        if os.path.exists(scenario_path):
            os.remove(scenario_path)


class ScenarioBuilder:
    """
    Builder for creating Scenario instances from JSON files.

    This class provides methods to load and create Scenario instances
    from previously saved JSON configuration files.
    """

    def __init__(self):
        """Initialize the ScenarioBuilder."""
        pass

    def build(self, json_path: str) -> Scenario:
        """
        Build a Scenario instance from a JSON file.

        Args:
            json_path: Path to the JSON configuration file

        Returns:
            Scenario: Created Scenario instance

        Example:
            >>> builder = ScenarioBuilder()
            >>> scenario = builder.build("scenario.json")
        """
        with open(json_path, 'r') as f:
            data = json.load(f)

            return Scenario(**data)


if __name__ == "__main__":
    # python batem/reno/simulation/scenario.py

    args = parse_args()

    time_space_handler = TimeSpaceHandler(
        location=args.location,
        start_date=args.start_date,
        end_date=args.end_date)

    scenario = Scenario(
        location=args.location,
        start_date=args.start_date,
        end_date=args.end_date,
        house_ids=[],
        pv_number_of_panels=1,
        pv_panel_height_m=1,
        pv_panel_width_m=1,
        pv_exposure_deg=0.0,
        pv_slope_deg=152.0,
        pv_peak_power_kW=8,
        pv_mount_type=solar.MOUNT_TYPES.FLAT,
        manager_type=MANAGER_TYPE.BASIC)

    scenario.to_json()

    scenario_builder = ScenarioBuilder()
    scenario = scenario_builder.build(
        FilePathBuilder().get_scenario_path(
            time_space_handler,
            scenario.manager_type,
            scenario.pv_number_of_panels,
            scenario.pv_peak_power_kW))
    for attr in scenario.__dict__:
        print(attr, scenario.__dict__[attr])
