import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
from typing import Dict, Any

import pytz
import requests
from batem.reno.utils import TimeSpaceHandler
from batem.weather.model import OPEN_WEATHER_TO_NAMES_MAP, WEATHER_VARIABLES, WeatherData
from batem.weather.utils import WeatherFilePathBuilder
from batem.core.timemg import epochtimems_to_datetime, stringdate_to_epochtimems


@dataclass
class WeatherDataConfig:
    """Configuration for weather data retrieval."""
    server_url: str = 'https://archive-api.open-meteo.com/v1/archive'
    start_date: str = '1/1/1980'
    date_format: str = '%d/%m/%Y'
    api_date_format: str = '%Y-%m-%d'
    timeout: int = 300


class WeatherDataBuilder:
    """Builder class for retrieving and processing weather data."""

    def __init__(self):
        """Initialize the weather data builder.

        Args:
            config: Optional configuration for weather data retrieval.
        """
        pass

    def build(self, ts_handler: TimeSpaceHandler) -> WeatherData:
        """Build weather data for the specified location.

        Args:
            ts_handler: TimeSpaceHandler object

        Returns:
            Dictionary containing the weather data

        Raises:
            FileNotFoundError: If weather file cannot be found or created
            ValueError: If API returns an error
        """
        print(f"Building weather data for {ts_handler.location} at "
              f"{ts_handler.latitude_north_deg}°N, "
              f"{ts_handler.longitude_east_deg}°E")

        try:
            data = self._load_data(ts_handler.location)
        except FileNotFoundError:
            self.build_json_data(ts_handler)
            data = self._load_data(ts_handler.location)

        self._check_time_range(data, ts_handler)

        weather_obj = WeatherData(ts_handler)

        weather_variables_values, weather_variables_units = self._process_weather_variables(
            data, ts_handler)

        weather_obj.variables_by_time = weather_variables_values
        weather_obj.units_by_variable = weather_variables_units

        return weather_obj

    def _load_data(self, location: str) -> Dict[str, Any]:
        """Load weather data from JSON file.

        Args:
            location: Name of the location

        Returns:
            Dictionary containing the weather data

        Raises:
            FileNotFoundError: If weather file cannot be found
        """
        path = WeatherFilePathBuilder().get_weather_json_file_path(location)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Weather file for {location} not found")

        with open(path) as json_file:
            return json.load(json_file)

    def build_json_data(self, ts_handler: TimeSpaceHandler) -> None:
        """Build and save weather data from OpenMeteo API.

        Args:
            ts_handler: TimeSpaceHandler object

        Raises:
            ValueError: If API returns an error
        """

        tz = pytz.timezone('UTC')
        # Calculate date range
        end_date = (datetime.now(tz=tz) + timedelta(days=-7)
                    ).strftime(WeatherDataConfig.date_format)

        start_date = datetime.strptime(
            WeatherDataConfig.start_date,
            WeatherDataConfig.date_format
        ).replace(tzinfo=tz).strftime(WeatherDataConfig.api_date_format)

        end_date = datetime.strptime(
            end_date,
            WeatherDataConfig.date_format
        ).replace(tzinfo=tz).strftime(WeatherDataConfig.api_date_format)

        # Fetch data from API
        response = requests.get(
            WeatherDataConfig.server_url,
            params={
                "latitude": ts_handler.latitude_north_deg,
                "longitude": ts_handler.longitude_east_deg,
                "start_date": start_date,
                "end_date": end_date,
                "hourly": WEATHER_VARIABLES
            },
            headers={'Accept': 'application/json'},
            timeout=WeatherDataConfig.timeout,
            stream=True
        )
        data = response.json()

        if 'error' in data:
            raise ValueError(f"API Error: {data['reason']}")

        # Clean up missing data
        self._clean_missing_data(data)

        # Convert time format
        self._convert_time_format(data)

        # Save data
        path = WeatherFilePathBuilder().get_weather_json_file_path(
            ts_handler.location)
        with open(path, 'w') as json_file:
            json.dump(data, json_file)
        print(f"Weather data extracted from OpenMeteo API saved to {path}")

    def _clean_missing_data(self, data: Dict[str, Any]) -> None:
        """Remove trailing missing data points.

        Args:
            data: Weather data dictionary
        """
        number_to_remove = 0
        for k in range(len(data['hourly']['time'])-1, -1, -1):
            if data['hourly']['temperature_2m'][k] is None:
                number_to_remove += 1
            else:
                break

        for v in data['hourly']:
            for _ in range(number_to_remove):
                data['hourly'][v].pop(-1)

    def _convert_time_format(self, data: Dict[str, Any]) -> None:
        """Convert time format to epoch milliseconds.

        Args:
            data: Weather data dictionary
            timezone: Timezone string for conversion
        """
        data['hourly']['epochtimems'] = [
            stringdate_to_epochtimems(
                time_str,
                date_format='%Y-%m-%dT%H:%M',
                timezone_str='UTC'
            )
            for time_str in data['hourly']['time']
        ]
        del data['hourly']['time']

    def _check_time_range(self, data: Dict[str, Any],
                          ts_handler: TimeSpaceHandler):
        """Check if the time range is valid.

        Args:
            data: Weather data dictionary
            ts_handler: TimeSpaceHandler object
        """

        recorded_from_epochtimems: int = data['hourly']['epochtimems'][0]
        recorded_to_epochtimems: int = data['hourly']['epochtimems'][-1]

        if (ts_handler.start_epochtimems is not None and
                recorded_from_epochtimems > ts_handler.start_epochtimems):
            message = (
                f"Beware: earliest requested date older than the recorded one"
                f"Recorded from: {recorded_from_epochtimems}"
                f"Requested from: {ts_handler.start_epochtimems}"
            )
            print(message, file=sys.stderr)
        if (ts_handler.end_epochtimems is not None and
                recorded_to_epochtimems < ts_handler.end_epochtimems):
            message = (
                f"Beware: latest requested date more recent than the recorded one"
                f"Recorded to: {recorded_to_epochtimems}"
                f"Requested to: {ts_handler.end_epochtimems}"
            )
            print(message, file=sys.stderr)

    def _process_weather_variables(
        self,
        weather_records: dict[str, Any],
        ts_handler: TimeSpaceHandler
    ) -> tuple[dict[float, dict[str, float]], dict[str, str]]:
        """Process weather variables from OpenMeteo records into time-indexed dict.

        Args:
            weather_records: Raw weather data from OpenMeteo

        Returns:
            Tuple of (time-indexed weather data, units)
        """
        # Initialize time-indexed dictionary for weather data
        weather_data: dict[datetime, dict[str, float]] = {}
        weather_units: dict[str, str] = {}

        openmeteo_epochtimems = weather_records['hourly']['epochtimems']
        openmeteo_variable_names = [
            name for name in weather_records['hourly'].keys()
            if name != 'epochtimems'
        ]

        for k in range(len(openmeteo_epochtimems)):

            if openmeteo_epochtimems[k] < ts_handler.start_epochtimems:
                continue
            if openmeteo_epochtimems[k] > ts_handler.end_epochtimems:
                break

            # Handle first data point
            current_time = epochtimems_to_datetime(
                openmeteo_epochtimems[k],
                timezone_str='UTC'
            )

            if not weather_data:
                self._process_first_data_point(
                    k, current_time, openmeteo_variable_names,
                    weather_records,
                    weather_data, weather_units
                )
            else:
                self._process_subsequent_data_point(
                    k, current_time, openmeteo_epochtimems,
                    openmeteo_variable_names, weather_records,
                    weather_data
                )

        return weather_data, weather_units

    def _process_first_data_point(
        self,
        index: int,
        timestamp: datetime,
        openmeteo_variable_names: list[str],
        weather_records: dict[str, Any],
        weather_data: dict[datetime, dict[str, float]],
        weather_units: dict[str, str]
    ) -> None:
        """Process the first data point in the time series."""
        weather_data[timestamp] = {}

        for var_name in openmeteo_variable_names:
            weather_var_name = OPEN_WEATHER_TO_NAMES_MAP.get(
                var_name, var_name)
            weather_units[weather_var_name] = (
                weather_records['hourly'][var_name]
            )
            weather_data[timestamp][weather_var_name] = (
                weather_records['hourly'][var_name][index]
            )

    def _process_subsequent_data_point(
        self,
        index: int,
        current_time: datetime,
        openmeteo_epochtimems: list[float],
        openmeteo_variable_names: list[str],
        weather_records: dict[str, Any],
        weather_data: dict[float, dict[str, float]]
    ) -> None:
        """Process subsequent data points, handling time shifts."""
        delta_ms = current_time - epochtimems_to_datetime(
            openmeteo_epochtimems[index-1],
            timezone_str='UTC'
        )

        if delta_ms == 2 * 3600 * 1000:  # Autumn time shift
            # Add interpolated point for time shift
            shift_time = openmeteo_epochtimems[index-1] + 3600 * 1000
            self._add_weather_point(
                index-1, shift_time, openmeteo_variable_names,
                weather_records, weather_data
            )

        if delta_ms > timedelta(seconds=0):
            self._add_weather_point(
                index-1, current_time, openmeteo_variable_names,
                weather_records, weather_data
            )

    def _add_weather_point(
        self,
        index: int,
        timestamp: datetime,
        openmeteo_variable_names: list[str],
        weather_records: dict[str, Any],
        weather_data: dict[datetime, dict[str, float]]
    ) -> None:
        """Add a single weather data point to the time-indexed dictionary."""
        weather_data[timestamp] = {}
        for var_name in openmeteo_variable_names:
            weather_var_name = OPEN_WEATHER_TO_NAMES_MAP.get(
                var_name, var_name)
            weather_data[timestamp][weather_var_name] = (
                weather_records['hourly'][var_name][index]
            )


if __name__ == "__main__":

    # python batem/weather/creation.py

    location = 'Grenoble'

    from_date = '1/1/2023'
    to_date = '31/12/2023'
    ts_handler = TimeSpaceHandler(location, from_date, to_date)

    weather_data = WeatherDataBuilder().build(ts_handler)
