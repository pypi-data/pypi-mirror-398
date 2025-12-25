"""
Utility functions and classes for the reno package.

This module provides various utilities for:
- Command line argument parsing
- Geographic location handling
- Time and space management
- File path management for data and results
"""

import argparse
from datetime import datetime, timezone
import os

import pandas as pd

from batem.core.timemg import stringdate_to_datetime, stringdate_to_epochtimems
from batem.reno.constants import MANAGER_TYPE
from batem.reno.experiment import Experiment


def parse_args():
    """
    Parse command line arguments for the simulation.

    Returns:
        argparse.Namespace: Parsed command line arguments containing:
            - location: Simulation location (default: "Grenoble")
            - start_date: Start date in DD/MM/YYYY format
                (default: "01/3/1998")
            - end_date: End date in DD/MM/YYYY format
                (default: "01/3/1999")

    Example:
        >>> args = parse_args()
        >>> print(f"Running simulation for {args.location}")
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--location", type=str,
                        required=False, default="Bucharest")
    parser.add_argument("--start_date", type=str,
                        required=False, default="01/2/1998")
    parser.add_argument("--end_date", type=str,
                        required=False, default="01/2/1999")
    parser.add_argument("--number_of_panels", type=int,
                        required=False, default=44)
    parser.add_argument("--peak_power_kW", type=float,
                        required=False, default=0.346)
    parser.add_argument("--manager_type", type=str,
                        required=False, default="reactive")
    return parser.parse_args()


def get_lat_lon_from_location(location: str) -> tuple[float, float]:
    """
    Get the latitude and longitude coordinates for a supported location.

    Args:
        location: Name of the location (currently supports "Grenoble" and
            "Bucharest")

    Returns:
        tuple[float, float]: (latitude, longitude) in decimal degrees

    Raises:
        ValueError: If the location is not supported

    Example:
        >>> lat, lon = get_lat_lon_from_location("Grenoble")
        >>> print(f"Latitude: {lat}, Longitude: {lon}")
    """
    if location == "Grenoble":
        return 45.19154994547585, 5.722065312331381
    elif location == "Bucharest":
        return 44.426827, 26.103731
    elif location == "Cayenne":
        return 4.924435336591809, -52.31276008988111
    elif location == "Paris":
        return 48.856614, 2.352222
    else:
        raise ValueError(f"Location {location} not supported")


class TimeSpaceHandler:
    """
    Handler for time and space related operations in the simulation.

    This class manages time ranges, geographic coordinates, and provides
    utilities for time-based operations in the simulation.

    Attributes:
        location: Name of the simulation location
        latitude_north_deg: Latitude in decimal degrees
        longitude_east_deg: Longitude in decimal degrees
        start_date: Start date string in DD/MM/YYYY format
        end_date: End date string in DD/MM/YYYY format
        start_time: Start datetime in UTC
        end_time: End datetime in UTC
        range_hourly: List of hourly datetimes in UTC
    """

    def __init__(self, location: str, start_date: str, end_date: str):
        """
        Initialize the TimeSpaceHandler.

        Args:
            location: Name of the simulation location
            start_date: Start date in DD/MM/YYYY format
            end_date: End date in DD/MM/YYYY format
        """
        self.location: str = location

        latitude_north_deg, longitude_east_deg = get_lat_lon_from_location(
            location)
        self.latitude_north_deg = latitude_north_deg
        self.longitude_east_deg = longitude_east_deg

        self.start_date: str = start_date
        self.end_date: str = end_date

        self.start_time_str: str = f"{start_date} 00:00:00"
        self.end_time_str: str = f"{end_date} 00:00:00"

        self.start_time: datetime = stringdate_to_datetime(
            self.start_time_str, timezone_str="UTC")  # type: ignore
        self.end_time: datetime = stringdate_to_datetime(
            self.end_time_str, timezone_str="UTC")  # type: ignore

        self.start_epochtimems: int = stringdate_to_epochtimems(
            self.start_time_str, date_format='%d/%m/%Y %H:%M:%S',
            timezone_str="UTC")
        self.end_epochtimems: int = stringdate_to_epochtimems(
            self.end_time_str, date_format='%d/%m/%Y %H:%M:%S',
            timezone_str="UTC")

        self._set_time_range()

    def _set_time_range(self):
        """
        Set the time range based on the start and end time.

        Creates an hourly range of datetimes, removing the DST transition
        hour to match consumption and production data. All times are
        converted to UTC.
        """
        # Create hourly range directly
        hourly_dates = pd.date_range(
            self.start_time, self.end_time, freq="h", inclusive="both"
        )

        # Convert to naive datetimes and remove DST transition hour
        self.range_hourly: list[datetime] = [
            dt.replace(tzinfo=None) for dt in hourly_dates
            if not (dt.month == 3 and dt.day >= 25 and dt.day <= 31
                    and dt.hour == 3 and dt.weekday() == 6)
        ]

        # Convert to UTC to match the consumption and production data
        self.range_hourly = [dt.replace(tzinfo=timezone.utc)
                             for dt in self.range_hourly]

    def get_k_from_datetime(self, datetime: datetime) -> int:
        """
        Get the index k for a given datetime in the hourly range.

        Args:
            datetime: The datetime to find the index for

        Returns:
            int: Index of the datetime in the hourly range

        Raises:
            ValueError: If the datetime is not in the range
        """
        return self.range_hourly.index(datetime)

    def get_datetime_from_k(self, k: int) -> datetime:
        """
        Get the datetime at index k in the hourly range.

        Args:
            k: Index in the hourly range

        Returns:
            datetime: The datetime at index k

        Raises:
            IndexError: If k is out of range
        """
        return self.range_hourly[k]


class FilePathBuilder:
    """
    Builder for file paths used in the simulation.

    This class provides methods to generate consistent file paths for
    various data files, results, and plots used in the simulation.
    """

    def __init__(self):
        """Initialize the FilePathBuilder."""
        pass

    def get_irise_db_path(self) -> str:
        """
        Get the path to the IRISE database.

        Returns:
            str: Path to the IRISE database file
        """
        return os.path.join("data", "irise38.sqlite3")

    def get_trimmed_house_consumption_path(
            self, house_id: int,
            time_space_handler: TimeSpaceHandler,
            hourly: bool = False) -> str:
        """
        Get the path to the trimmed house consumption data.

        Args:
            house_id: ID of the house
            time_space_handler: TimeSpaceHandler instance for time range
            hourly: Whether to use hourly data (default: False)

        Returns:
            str: Path to the trimmed consumption data file
        """
        start_time = time_space_handler.start_date.replace("/", "_")
        end_time = time_space_handler.end_date.replace("/", "_")
        if hourly:
            file_name = f"{house_id}_consumption_hourly_trimmed_{start_time}_"
            file_name = f"{file_name}_{end_time}.csv"
        else:
            file_name = f"{house_id}_consumption_trimmed_{start_time}_"
            file_name = f"{file_name}_{end_time}.csv"
        return os.path.join("batem", "reno", "csv_data", file_name)

    def get_plots_folder(self) -> str:
        """
        Get the path to the plots folder, creating it if it doesn't exist.

        Returns:
            str: Path to the plots folder
        """
        folder_name = "plots"
        path = os.path.join("batem", "reno", folder_name)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def get_community_valid_houses_path(
            self, time_space_handler: TimeSpaceHandler) -> str:
        """
        Get the path to the community valid houses file.

        Args:
            time_space_handler: TimeSpaceHandler instance for time range

        Returns:
            str: Path to the valid houses JSON file
        """
        file_name = (f"community_valid_houses_{time_space_handler.location}_"
                     f"{time_space_handler.start_date.replace('/', '_')}_"
                     f"{time_space_handler.end_date.replace('/', '_')}.json")
        return os.path.join("batem", "reno", "community", file_name)

    def get_experiments_folder(self) -> str:
        """
        Get the path to the simulation results folder, creating it if it
        doesn't exist.

        Returns:
            str: Path to the results folder
        """
        folder_name = "experiments"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        return folder_name

    def get_experiment_folder(self, experiment: Experiment) -> str:
        """
        Get the path to the experiment folder.

        """
        folder = self.get_experiments_folder()
        folder_name = os.path.join(folder, experiment.name)
        os.makedirs(folder_name, exist_ok=True)
        return folder_name

    def get_simulation_results_path(self,
                                    time_space_handler: TimeSpaceHandler,
                                    manager_type: MANAGER_TYPE
                                    ) -> str:
        """
        Get the path to the simulation results file.

        Args:
            time_space_handler: TimeSpaceHandler instance for time range

        Returns:
            str: Path to the results CSV file
        """
        folder = self.get_simulation_results_folder()
        start_date = time_space_handler.start_date.replace("/", "_")
        end_date = time_space_handler.end_date.replace("/", "_")
        manager_type_str = manager_type.value
        file_name = (f"results_{time_space_handler.location}_{start_date}_"
                     f"{end_date}_{manager_type_str}.csv")
        return os.path.join(folder, file_name)

    def get_simulation_plots_folder(self) -> str:
        """
        Get the path to the simulation plots folder, creating it if it
        doesn't exist.

        Returns:
            str: Path to the simulation plots folder
        """
        simulations_folder = self.get_simulation_results_folder()
        folder_name = "plots"
        path = os.path.join(simulations_folder, folder_name)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def get_scenario_path(self, time_space_handler: TimeSpaceHandler,
                          manager_type: MANAGER_TYPE,
                          number_of_panels: int, peak_power_kW: float) -> str:
        """
        Get the path to the scenario file.

        Args:
            time_space_handler: TimeSpaceHandler instance for time range
            number_of_panels: Number of panels
            peak_power_kW: Peak power of the PV plant

        Returns:
            str: Path to the scenario file
        """
        file_name = "scenario"
        start_date = time_space_handler.start_date.replace("/", "_")
        end_date = time_space_handler.end_date.replace("/", "_")
        manager_type_str = manager_type.value
        file_name = (f"{file_name}_"
                     f"{time_space_handler.location}_{start_date}_"
                     f"{end_date}_"
                     f"{manager_type_str}_"
                     f"number_of_panels_{number_of_panels}_"
                     f"peak_power_kW_{peak_power_kW}.json")
        folder = self.get_simulation_results_folder()
        return os.path.join(folder, file_name)
