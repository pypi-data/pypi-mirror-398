"""Weather data management and Open-Meteo API integration module for building energy analysis.

.. module:: batem.core.weather

This module provides comprehensive tools for weather data management, retrieval,
and processing in building energy analysis systems. It includes Open-Meteo API
integration, elevation data retrieval, weather data building, and site weather
data processing capabilities for building energy analysis workflows.

Classes
-------

.. autosummary::
   :toctree: generated/

   ElevationRetriever
   SWDbuilder
   SiteWeatherData

Classes Description
-------------------

**ElevationRetriever**
    Elevation data retrieval and caching from web APIs.

**SWDbuilder**
    Historical weather data download and management from Open-Meteo API.

**SiteWeatherData**
    Weather time series data storage and processing for building energy analysis.

Key Features
------------

* Open-Meteo API integration for historical weather data retrieval
* Elevation data retrieval and caching for geographic coordinates
* Weather data building and management with automatic file caching
* Site weather data processing and time series management
* Atmospheric parameter calculations (humidity, temperature, pressure)
* Weather variable naming conversion and standardization
* Temperature distribution analysis and visualization
* Integration with building energy data providers and measurement systems
* Support for various weather data formats and API endpoints
* Geographic coordinate handling and timezone management

The module is designed for building energy analysis, weather data processing,
and comprehensive weather management in research and practice.

.. note::
    This module requires internet connectivity for downloading weather data from
    Open-Meteo API and elevation data from web services.

Author: stephane.ploix@grenoble-inp.fr

License: GNU General Public License v3.0
"""
from __future__ import annotations
import math
import json
import requests
from scipy.constants import Stefan_Boltzmann
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import copy
import os
from datetime import datetime
try:
    from geopy.geocoders import Nominatim
    HAS_GEOPY = True
except ImportError:
    HAS_GEOPY = False
    # Fallback for when geopy is not available
    class Nominatim:
        def __init__(self, *args, **kwargs):
            raise ImportError("geopy is required for get_location_from_city_name(). Please install it with: pip install geopy")

        def geocode(self, *args, **kwargs):
            raise ImportError("geopy is required for get_location_from_city_name(). Please install it with: pip install geopy")
from math import exp, cos, pi
from batem.core.timemg import REGULAR_DATE_FORMAT, REGULAR_DATETIME_FORMAT, epochtimems_to_datetime, epochtimems_to_stringdate, stringdate_to_epochtimems, TimezoneFinder, local_timezone
from batem.core.utils import FilePathChecker, TimeSeriesPlotter, FilePathBuilder
from typing import Any


DEFAULT_FROM_TO_NAMING: dict[str, str] = {
    "apparent_temperature": "feels_like",
    "cloud_cover_high": "cloudiness_high",
    "cloud_cover_low": "cloudiness_low",
    "cloud_cover_mid": "cloudiness_mid",
    "cloud_cover": "cloudiness",
    "dew_point_2m": "dew_point_temperature",
    "diffuse_radiation": "OM_dhi",  # _instant
    "direct_normal_irradiance": "OM_dni_v",  # _instant
    "direct_radiation": "OM_dni_h",  # _instant
    "precipitation": "precipitation",
    "rain": "rain",
    "relative_humidity_2m": "humidity",
    "shortwave_radiation": "OM_ghi",  # _instant
    "showers": "showers",
    "snow_depth": "snow_depth",
    "snowfall": "snowfall",
    "soil_temperature_0_to_7cm": None,  # Changed from soil_temperature_0cm to soil_temperature_0_to_7cm (correct Open-Meteo API name)
    "soil_temperature_7_to_28cm": None,
    "soil_temperature_28_to_100cm": None,
    "soil_temperature_100_to_255cm": None,
    "soil_moisture_0_to_7cm": None,
    "soil_moisture_7_to_28cm": None,
    "soil_moisture_28_to_100cm": None,
    "soil_moisture_100_to_255cm": None,
    "surface_pressure": "pressure",
    "temperature_2m": "temperature",
    "terrestrial_radiation_instant": "OM_tsi",
    "weather_code": None,  # Changed from weathercode to weather_code (correct Open-Meteo API name)
    "wind_direction_10m": "wind_direction_in_deg",
    "wind_gusts_10m": "wind_gusts_km_h",
    "wind_speed_10m": "wind_speed_km_h"
}


def convert_from_to_naming(deleted_variables: list[str] = []) -> dict[str, str]:
    """Convert weather variable naming with optional variable deletion.

    This function creates a copy of the default weather variable naming mapping
    and optionally removes specified variables by setting their values to None.

    :param deleted_variables: List of variable names to remove from the mapping
    :type deleted_variables: list[str]
    :return: Modified weather variable naming dictionary
    :rtype: dict[str, str]
    """
    _from_to_naming = DEFAULT_FROM_TO_NAMING.copy()
    for variable in deleted_variables:
        if variable in _from_to_naming:
            _from_to_naming[variable] = None
    return _from_to_naming


def absolute_humidity_kg_per_m3(temperature_deg: float, relative_humidity_percent: float) -> float:
    """Calculate absolute humidity in kg water per m³ of air.

    :param temperature_deg: Air temperature in degrees Celsius
    :type temperature_deg: float
    :param relative_humidity_percent: Relative humidity as a percentage (0-100)
    :type relative_humidity_percent: float
    :return: Absolute humidity in kg water per m³ of air
    :rtype: float
    """
    Rv_J_per_kg_K = 461.5  # J/kg.K
    saturation_vapour_pressure_Pa: float = 611.213 * exp(17.5043 * temperature_deg / (temperature_deg + 241.2))  # empirical formula of Magnus-Tetens
    partial_vapour_pressure_Pa: float = saturation_vapour_pressure_Pa * relative_humidity_percent / 100
    return partial_vapour_pressure_Pa / (Rv_J_per_kg_K * (temperature_deg + 273.15))


def absolute_humidity_kg_per_kg(temperature_deg: float, relative_humidity_percent: float, atmospheric_pressures_hPa: float = 1013.25) -> float:
    """Calculate absolute humidity in kg water per kg of dry air.

    :param temperature_deg: Air temperature in degrees Celsius
    :type temperature_deg: float
    :param relative_humidity_percent: Relative humidity as a percentage (0-100)
    :type relative_humidity_percent: float
    :param atmospheric_pressures_hPa: Atmospheric pressure in hPa
    :type atmospheric_pressures_hPa: float
    :return: Absolute humidity in kg water per kg of dry air
    :rtype: float
    """
    Rs_J_per_kg_K = 287.06
    density_kg_per_m3 = (atmospheric_pressures_hPa * 100 - 2.30617*relative_humidity_percent*exp(17.5043*temperature_deg/(241.2+temperature_deg))) / Rs_J_per_kg_K / (temperature_deg + 273.15)
    return absolute_humidity_kg_per_m3(temperature_deg, relative_humidity_percent) / density_kg_per_m3


def relative_humidity_percent(temperature_deg: float, absolute_humidity_kg_per_m3: float) -> float:
    """Calculate relative humidity percentage from absolute humidity.

    :param temperature_deg: Air temperature in degrees Celsius
    :type temperature_deg: float
    :param absolute_humidity_kg_per_m3: Absolute humidity in kg water per m³ of air
    :type absolute_humidity_kg_per_m3: float
    :return: Relative humidity as a percentage (0-100)
    :rtype: float
    """
    Rv_J_per_kg_K = 461.5  # J/kg.K
    saturation_vapour_pressure_Pa: float = 611.213 * exp(17.5043 * temperature_deg / (temperature_deg + 241.2))  # empirical formula of Magnus-Tetens
    partial_vapour_pressure_Pa: float = absolute_humidity_kg_per_m3 * Rv_J_per_kg_K * (temperature_deg + 273.15)
    return 100 * partial_vapour_pressure_Pa / saturation_vapour_pressure_Pa


def saturation_vapor_pressure_pa(T_air_C: float) -> float:
    """Saturation vapor pressure over liquid water in Pa (Buck 1981)."""
    es: float = 611.21 * math.exp((18.678 - T_air_C / 234.5) * (T_air_C / (257.14 + T_air_C)))
    return float(es)


def humidity_ratio(T_air_C: float, relative_humidity_coef: float, p_atm: float = 101325) -> float:
    """Humidity ratio (kg_w / kg_da) for air at dry-bulb T_c (°C) and RH (0–1)."""
    RATIO_W = 0.62198          # kg_w/kg_da (molecular weight ratio for humidity ratio)
    relative_humidity_coef: float = max(0.0, min(1.0, relative_humidity_coef))
    es: float = saturation_vapor_pressure_pa(T_air_C)
    e: float = relative_humidity_coef * es
    e: float = min(e, 0.99 * p_atm)
    Y: Any = RATIO_W * e / (p_atm - e)
    return float(Y)


def compute_hc_out(wind_speed_m_s: float) -> float:
    """Convective coefficient at water surface (air side)."""
    return 5.8 + 4.1 * wind_speed_m_s


def compute_sky_emissivity(T_air_C: float, cloud_cover_coef: float) -> float:
    """Compute sky emissivity based on air temperature and cloud cover."""
    T_air_K: float = T_air_C + 273.15
    epsilon_clear: float = 9.37e-6 * T_air_K**2
    epsilon_sky: float = epsilon_clear + (1 - epsilon_clear) * cloud_cover_coef**2
    return float(epsilon_sky)


class ElevationRetriever:
    """Retrieves and caches site elevation data from web APIs.

    This class provides elevation data retrieval for geographic coordinates with
    automatic caching to avoid repeated API calls.
    """

    def __init__(self) -> None:
        """Initialize the ElevationRetriever with cache file path."""
        self.json_db_name: str = FilePathBuilder().get_localizations_file_path()

        if not os.path.isfile(self.json_db_name):
            self.data = dict()
        else:
            self.data = json.load(open(self.json_db_name))

    def get(self, longitude_east_deg: float = None, latitude_north_deg: float = None) -> float:
        """Get elevation for given coordinates with caching.

        :param longitude_east_deg: Longitude in degrees east
        :type longitude_east_deg: float
        :param latitude_north_deg: Latitude in degrees north
        :type latitude_north_deg: float
        :return: Elevation in meters above sea level
        :rtype: float
        """
        if longitude_east_deg is None or latitude_north_deg is None:
            longitude_east_deg = self.longitude_east_deg
            latitude_north_deg = self.latitude_north_deg
        coordinate: str = '(%s,%s)' % (longitude_east_deg, latitude_north_deg)
        if coordinate not in self.data:
            elevation = 200
            try:
                elevation = ElevationRetriever._webapi_elevation_meter(longitude_east_deg, latitude_north_deg)
            except Exception:
                elevation = float(input('Enter manually the elevation:'))
            self.data[coordinate] = elevation
            with open(self.json_db_name, 'w') as json_file:
                json.dump(self.data, json_file)
        else:
            elevation: float = self.data[coordinate]
        return elevation

    @staticmethod
    def _webapi_elevation_meter(longitude_east_deg: float, latitude_north_deg: float) -> float:
        """Retrieve elevation from Open-Elevation API.

        :param longitude_east_deg: Longitude in degrees east
        :type longitude_east_deg: float
        :param latitude_north_deg: Latitude in degrees north
        :type latitude_north_deg: float
        :return: Elevation in meters above sea level
        :rtype: float
        """
        url = 'https://api.open-elevation.com/api/v1/lookup'
        params: dict[str, float] = {"locations": [{"latitude": latitude_north_deg, "longitude": longitude_east_deg}]}
        response = requests.post(url, json=params)
        try:
            response.raise_for_status()
            for info in response:
                print(info, response)

            data = response.json()
            elevations = [result['elevation'] for result in data['results']]
            return elevations[0]
        except requests.HTTPError as error:
            print(
                "The elevation server does not respond: "
                "horizon mask has to be set manually.", error)
            elevation_m = int(input('Elevation in m: '))
            return elevation_m


def get_location_from_city_name(city_name: str, country_name: str = "France") -> tuple[float, float]:
    if not HAS_GEOPY:
        raise ImportError("geopy is required for get_location_from_city_name(). Please install it with: pip install geopy")
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(city_name)
    if location:
        print("location for", city_name, "is: Latitude:", location.latitude, ", Longitude:", location.longitude)
        return city_name+'_'+country_name, location.latitude, location.longitude
    else:
        raise ValueError("City " + city_name + " not found")


def get_site_weather_data(city_name: str, country_name: str = "France", load_from_year: int = None, period_of_interest: tuple[str, str] | tuple[int, int] = None) -> SiteWeatherData:
    last_year = datetime.now().year - 1
    if period_of_interest is None:
        period_of_interest = ('01/01/%i' % last_year, '31/12/%i' % last_year)
    elif type(period_of_interest) is tuple and type(period_of_interest[0]) is int and type(period_of_interest[1]) is int:
        period_of_interest = ('01/01/%i' % period_of_interest[0], '31/12/%i' % period_of_interest[1])
    elif type(period_of_interest) is tuple and type(period_of_interest[0]) is str and type(period_of_interest[1]) is str:
        pass
    else:
        raise ValueError(f"Period of interest must be a tuple of strings or a tuple of integers but not {type(period_of_interest)} with values {period_of_interest}")
    
    if load_from_year is None:
        load_from_year = 1980
    elif load_from_year != 1980:
        city_name = city_name + '_' + str(load_from_year)
    location, latitude, longitude = get_location_from_city_name(city_name, country_name)
    swd_builder: SWDbuilder = SWDbuilder(location=location, latitude_north_deg=latitude, longitude_east_deg=longitude, initial_year=load_from_year, end_year=int(period_of_interest[1].split('/')[-1]))
    return swd_builder(from_stringdate=period_of_interest[0], to_stringdate=period_of_interest[1])


class SWDbuilder:
    """Downloads and manages historical weather data from Open-Meteo API.

    This class handles the download, caching, and management of historical weather data
    for specific geographic locations.
    """

    def __init__(self, location: str, latitude_north_deg: float, longitude_east_deg: float, initial_year: int = 1980, end_year: int = None) -> None:
        """Initialize a SiteWeatherDataBuilder for a specific location.

        :param location: Location name identifier
        :type location: str
        :param latitude_north_deg: Site latitude in degrees north
        :type latitude_north_deg: float
        :param longitude_east_deg: Site longitude in degrees east
        :type longitude_east_deg: float
        """
        if ',' in location:
            city_name, country_name = location.split(',')
        else:
            city_name = location
            country_name = 'France'
        self.city_name: str = city_name
        self.country_name: str = country_name
        self.location: str = location
        self.site_latitude_north_deg: float = latitude_north_deg
        self.site_longitude_east_deg: float = longitude_east_deg
        self.initial_year: int = initial_year
        if end_year is None:
            # Smart end year calculation based on current date
            current_date = datetime.now()
            current_year = current_date.year
            current_week = current_date.isocalendar().week
            if current_week > 1:
                end_year = current_year - 1  # Previous year
            else:
                end_year = current_year - 2  # Year before previous
        self.end_year: int = end_year
        json_file_path: str = FilePathBuilder().get_weather_file_path(location)
        if not FilePathChecker().is_file_exists(json_file_path):
            print(f"Weather file {json_file_path} not found, creating it")
            SWDbuilder._make_weather_json_file(json_file_path, latitude_north_deg, longitude_east_deg, self.initial_year, self.end_year)
        else:
            # Check if existing weather file needs updating with more recent data
            with open(json_file_path) as json_file:
                records: dict[str, Any] = json.load(json_file)
                last_epochtimems = int(records['epochtimems'][-1])
                last_date = epochtimems_to_stringdate(last_epochtimems, date_format=REGULAR_DATE_FORMAT, timezone_str=records.get('timezone', 'UTC'))
                last_year = int(last_date.split('/')[-1])  # Extract year from date string
                
                # Use the same smart date range calculation as in make_weather_json_file
                current_date = datetime.now()
                current_year = current_date.year
                current_week = current_date.isocalendar().week
                
                # Calculate expected end year using same logic
                if current_week > 1:
                    expected_end_year = current_year - 1  # Previous year
                else:
                    expected_end_year = current_year - 2  # Year before previous
                
                # If the data is older than expected, update it
                if last_year < expected_end_year:
                    print(f"Weather file {json_file_path} is outdated (last data: {last_year}, expected: {expected_end_year}). Updating...")
                    SWDbuilder._make_weather_json_file(json_file_path, latitude_north_deg, longitude_east_deg, self.initial_year, self.end_year)

        with open(json_file_path) as json_file:
            records: dict[str, Any] = json.load(json_file)
            self.weather_latitude_north_deg, self.weather_longitude_east_deg = records['latitude'], records['longitude']
            self.site_elevation_m: float = records['elevation']
            self.timezone_str: str = records['timezone']
            # Optimize data conversion using NumPy for better performance
            self.epochtimes_ms: list[int] = records['epochtimems']
            # Use NumPy for faster data conversion and better memory efficiency
            self.variables_values: dict[str, np.ndarray] = {}
            for k in records['hourly'].keys():
                data = records['hourly'][k]
                # Convert to NumPy array with NaN for None values
                self.variables_values[k] = np.array([float(v) if v is not None else np.nan for v in data], dtype=np.float32)
            self.variables_units: dict[str, str] = records['hourly_units']
            self.variable_names: list[str] = list(records['hourly'].keys())
            # self.variable_names.remove('epochtimems')
            self.first_epochtimems, self.last_epochtimems = int(records['epochtimems'][0]), int(records['epochtimems'][-1])
            print(f"First recorded date: {epochtimems_to_stringdate(self.first_epochtimems, date_format=REGULAR_DATETIME_FORMAT, timezone_str=self.timezone_str)}, Last recorded date: {epochtimems_to_stringdate(self.last_epochtimems, date_format=REGULAR_DATETIME_FORMAT, timezone_str=self.timezone_str)}")

    @staticmethod
    def _make_weather_json_file(json_file_path: str, site_latitude_north_deg: float, site_longitude_east_deg: float, start_year: int, end_year: int) -> None:
        """Create weather data JSON file by downloading from multiple weather sources.

        This method attempts to download historical weather data from multiple
        weather data sources (Open-Meteo ERA5, Forecast, etc.) and saves the
        data to a JSON file for caching and future use. Downloads data in 10-year
        chunks to balance efficiency with server load.

        :param json_file_path: Path where the weather data JSON file will be saved
        :type json_file_path: str
        :param site_latitude_north_deg: Site latitude in degrees north
        :type site_latitude_north_deg: float
        :param site_longitude_east_deg: Site longitude in degrees east
        :type site_longitude_east_deg: float
        :raises ValueError: If all weather data sources fail to provide data
        """
        # Try multiple weather data sources
        weather_sources = [
            {
                'name': 'Open-Meteo ERA5 Archive',
                # 'https://archive-api.open-meteo.com/v1/archive?latitude=52.52&longitude=13.41&start_date=2025-08-29&end_date=2025-09-12&hourly=temperature_2m,wind_speed_10m'
                'url': 'https://archive-api.open-meteo.com/v1/archive',
                'description': 'Historical weather data'
            },
            # {
            #     'name': 'Open-Meteo Forecast',
            #     'url': 'https://api.open-meteo.com/v1/forecast',
            #     'description': 'Weather forecast data (limited historical range)'
            # }
        ]
        
        # Use the end_year parameter as provided
        # Check if the requested end_year might not be available yet
        current_date = datetime.now()
        current_year = current_date.year
        if end_year >= current_year:
            print(f"Warning: Requested end_year ({end_year}) is current or future year. Data may not be fully available yet.")
        elif end_year == current_year - 1:
            current_week = current_date.isocalendar().week
            if current_week <= 1:
                print(f"Warning: Requested end_year ({end_year}) is very recent. Data may not be fully available yet.")
            
        print(f"Current date: {current_date.strftime('%Y-%m-%d')}")
        print(f"Downloading weather data from {start_year} to {end_year}")
        
        number_of_years = 10
        
        # Try each weather source
        for source in weather_sources:
            print(f"Trying weather source: {source['name']} ({source['description']})")
            
            # Try with the requested end_year first
            # If it fails with a 500 error (likely date not available), try progressively earlier years
            fallback_end_year = end_year
            max_fallback_attempts = 3  # Try up to 3 years earlier
            fallback_attempt = 0
            
            while fallback_attempt <= max_fallback_attempts:
                try:
                    SWDbuilder._download_weather_data_by_chunk(
                        source['url'],
                        site_latitude_north_deg,
                        site_longitude_east_deg,
                        start_year,
                        fallback_end_year,
                        json_file_path,
                        number_of_years
                    )
                    print(f"Successfully downloaded weather data from {source['name']}")
                    if fallback_end_year < end_year:
                        print(f"Note: Downloaded data up to {fallback_end_year} instead of requested {end_year} (data not yet available)")
                    return
                except ValueError as e:
                    error_msg = str(e).lower()
                    # Check if it's a 500 error or date-related error
                    if (("500" in error_msg or "something went wrong" in error_msg or
                         "date" in error_msg or "not available" in error_msg) and
                        fallback_attempt < max_fallback_attempts):
                        fallback_attempt += 1
                        fallback_end_year = end_year - fallback_attempt
                        print(f"Requested end_year ({end_year if fallback_attempt == 1 else fallback_end_year + 1}) not available. Trying {fallback_end_year} instead...")
                        continue
                    else:
                        # Re-raise if it's not a date availability issue or we've exhausted fallback attempts
                        raise
            
            # If we get here, all fallback attempts failed
            raise ValueError(f"Failed to download weather data even after trying years {end_year} down to {fallback_end_year}")

        # If all sources fail, raise an error
        raise ValueError("All weather data sources failed. Please check your internet connection and try again later.")

    @staticmethod
    def _download_weather_data(server_url: str, site_latitude_north_deg: float, site_longitude_east_deg: float,
                               from_openmeteo_string_date: str, to_openmeteo_string_date: str, json_file_path: str) -> None:
        """Download weather data from a specific server and save to JSON file.

        This method downloads historical weather data from a specified weather
        server API and saves the data to a JSON file with comprehensive error
        handling and retry mechanisms. Supports gzip compression for improved
        bandwidth efficiency and automatic decompression.

        :param server_url: URL of the weather data server API
        :type server_url: str
        :param site_latitude_north_deg: Site latitude in degrees north
        :type site_latitude_north_deg: float
        :param site_longitude_east_deg: Site longitude in degrees east
        :type site_longitude_east_deg: float
        :param from_openmeteo_string_date: Start date for weather data in YYYY-MM-DD format
        :type from_openmeteo_string_date: str
        :param to_openmeteo_string_date: End date for weather data in YYYY-MM-DD format
        :type to_openmeteo_string_date: str
        :param json_file_path: Path where the downloaded data will be saved
        :type json_file_path: str
        :raises ValueError: If the download fails after all retry attempts
        """
        print(f'Downloading data from {from_openmeteo_string_date} to {to_openmeteo_string_date}')

        # Build the request parameters with all variables from DEFAULT_FROM_TO_NAMING
        # Filter out variables that are not available in archive API
        # These variables return 500 errors when requested from Open-Meteo archive API
        excluded_variables = {
            # Soil temperature and moisture variables (not available in archive API)
            "soil_temperature_0_to_7cm",
            "soil_temperature_7_to_28cm",
            "soil_temperature_28_to_100cm",
            "soil_temperature_100_to_255cm",
            "soil_moisture_0_to_7cm",
            "soil_moisture_7_to_28cm",
            "soil_moisture_28_to_100cm",
            "soil_moisture_100_to_255cm",
            # Other variables not available in archive API
            "apparent_temperature",
            "cloud_cover_high",
            "cloud_cover_low",
            "cloud_cover_mid",
            "diffuse_radiation",
            "direct_normal_irradiance",
            "direct_radiation",
            "shortwave_radiation",
            "snow_depth",
        }
        
        # Get all variables, excluding those not available in archive API
        # Note: weather_code is included and works correctly
        all_variables = [var for var in DEFAULT_FROM_TO_NAMING.keys() if var not in excluded_variables]
        
        params = {
            "latitude": str(site_latitude_north_deg),
            "longitude": str(site_longitude_east_deg),
            "start_date": from_openmeteo_string_date,
            "end_date": to_openmeteo_string_date,
            "hourly": all_variables
        }

        # Check if the date range is too large (more than 2 years)
        
        try:
            start_date = datetime.strptime(from_openmeteo_string_date, '%Y-%m-%d')
            end_date = datetime.strptime(to_openmeteo_string_date, '%Y-%m-%d')
            days_diff = (end_date - start_date).days

            if days_diff > 365 * 2:  # More than 2 years
                print(f"Warning: Requesting {days_diff} days of data, which might be too large.")
                print("Consider reducing the date range or the system will try to download in chunks.")
        except Exception:
            pass  # If date parsing fails, continue with the original request

        print(f"Request URL: {server_url}")
        print(f"Request parameters: {params}")

        # Add retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries}")

                response: requests.Response = requests.get(
                    server_url,
                    params=params,
                    headers={
                        'Accept': 'application/json',
                        'Accept-Encoding': 'gzip, deflate, br'  # Support multiple compression formats
                    },
                    timeout=300,  # 5 minutes timeout for large requests
                    stream=True)

                print(f"Response status code: {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                
                # Check if response is compressed and log performance benefits
                content_encoding = response.headers.get('content-encoding', '')
                content_length = response.headers.get('content-length', 'unknown')
                if content_encoding:
                    print(f"Response is compressed with: {content_encoding} (Content-Length: {content_length} bytes)")
                    # Note: requests automatically decompresses gzip/deflate responses
                    print("Response will be automatically decompressed by requests library")
                else:
                    print(f"Response is not compressed (Content-Length: {content_length} bytes)")

                # Check if the response is successful
                if response.status_code != 200:
                    # Try to get error reason from response
                    error_reason = "Unknown server error"
                    try:
                        error_data = response.json()
                        if 'reason' in error_data:
                            error_reason = error_data['reason']
                    except Exception:
                        error_reason = response.text[:200] if response.text else "Unknown error"
                    
                    print(f"Server returned error status: {response.status_code}")
                    # Check if error is related to date availability
                    error_lower = error_reason.lower()
                    if any(keyword in error_lower for keyword in ['date', 'not available', 'out of range', 'latest']):
                        print("Note: The requested end date might not be available yet in the archive.")
                        print("Consider using an earlier end_year (e.g., current_year - 1 or current_year - 2)")
                    if attempt < max_retries - 1:
                        print("Retrying in 60 seconds...")
                        import time
                        time.sleep(60)
                        continue
                    raise ValueError(error_reason)

                # Check if response has content
                if not response.text.strip():
                    print("Server returned empty response")
                    if attempt < max_retries - 1:
                        print("Retrying in 60 seconds...")
                        import time
                        time.sleep(60)
                        continue
                    raise ValueError("Server returned empty response")

                # Try to parse JSON
                try:
                    data = response.json()
                except requests.exceptions.JSONDecodeError as e:
                    print(f"Failed to parse JSON response: {e}")
                    print(f"Response content (first 500 chars): {response.text[:500]}")
                    print(f"Response content type: {response.headers.get('content-type', 'unknown')}")
                    if attempt < max_retries - 1:
                        print("Retrying in 60 seconds...")
                        import time
                        time.sleep(60)
                        continue
                    raise ValueError(f"Server returned invalid JSON: {response.text[:200]}")

                if 'error' in data:
                    error_reason = data.get('reason', 'Unknown server error')
                    print(f"Server returned error: {error_reason}")
                    # Check if error is related to date availability
                    error_lower = error_reason.lower()
                    if any(keyword in error_lower for keyword in ['date', 'not available', 'out of range', 'latest']):
                        print("Note: The requested end date might not be available yet in the archive.")
                        print("Consider using an earlier end_year (e.g., current_year - 1 or current_year - 2)")
                    if attempt < max_retries - 1:
                        print("Retrying in 60 seconds...")
                        import time
                        time.sleep(60)
                        continue
                    raise ValueError(error_reason)

                # Success! Break out of retry loop
                break

            except requests.exceptions.Timeout as e:
                print(f"Request timeout occurred: {e}")
                print("The server took too long to respond. This might be due to large data requests.")
                if attempt < max_retries - 1:
                    print("Retrying in 60 seconds...")
                    import time
                    time.sleep(60)
                    continue
                raise ValueError(f"Request timeout after {max_retries} attempts: {e}")
            except requests.exceptions.RequestException as e:
                print(f"Network error occurred: {e}")
                if attempt < max_retries - 1:
                    print("Retrying in 60 seconds...")
                    import time
                    time.sleep(60)
                    continue
                raise ValueError(f"Failed to connect to weather server: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")
                if attempt < max_retries - 1:
                    print("Retrying in 60 seconds...")
                    import time
                    time.sleep(60)
                    continue
                raise

        # Add metadata to the data
        data['site_latitude'] = site_latitude_north_deg
        data['site_longitude'] = site_longitude_east_deg
        data['timezone'] = TimezoneFinder().timezone_at(lat=site_latitude_north_deg, lng=site_longitude_east_deg)
        data['elevation'] = ElevationRetriever().get(site_latitude_north_deg, site_longitude_east_deg)

        number_of_data_to_removed = 0
        for k in range(len(data['hourly']['time'])-1, -1, -1):
            if data['hourly']['temperature_2m'][k] is None:
                number_of_data_to_removed += 1
            else:
                break

        for variable in data['hourly']:
            for i in range(number_of_data_to_removed):
                data['hourly'][variable].pop(-1)

        epochtimes_ms: list[int] = [stringdate_to_epochtimems(openmeteo_stringtime, date_format='%Y-%m-%dT%H:%M', timezone_str=data['timezone']) for openmeteo_stringtime in data['hourly']['time']]
        data['epochtimems'] = epochtimes_ms

        del data['hourly']['time']
        del data['hourly_units']['time']

        with open(json_file_path, 'w') as json_file:
            json.dump(data, json_file)
            print(f"Weather file {json_file_path} created")

    @staticmethod
    def _download_weather_data_by_chunk(server_url: str, site_latitude_north_deg: float, site_longitude_east_deg: float,
                                        start_year: int, end_year: int, json_file_path: str, number_of_years: int = 10) -> None:
        """Download weather data decade by decade (10-year chunks) from a specific server and save to JSON file.

        This method downloads historical weather data in 10-year chunks to balance efficiency
        with server load. It combines all decade data into a single JSON file.

        :param server_url: URL of the weather data server API
        :type server_url: str
        :param site_latitude_north_deg: Site latitude in degrees north
        :type site_latitude_north_deg: float
        :param site_longitude_east_deg: Site longitude in degrees east
        :type site_longitude_east_deg: float
        :param start_year: Starting year for data download
        :type start_year: int
        :param end_year: Ending year for data download
        :type end_year: int
        :param json_file_path: Path where the downloaded data will be saved
        :type json_file_path: str
        :raises ValueError: If the download fails after all retry attempts
        """
        print(f'Downloading data from {start_year} to {end_year} in {number_of_years}-year chunks')
        
        # Initialize combined data structure
        combined_data = None
        all_epochtimes_ms = []
        
        # Download data decade by decade (10-year chunks, fallback to 5-year chunks if timeout)
        current_year = start_year
        decade_count = 0
        chunk_size = number_of_years  # Start with 10-year chunks
        
        while current_year <= end_year:
            decade_count += 1
            # Calculate the end year for this chunk
            chunk_end_year = min(current_year + chunk_size - 1, end_year)
            
            print(f"Downloading data for chunk {decade_count}: {current_year}-{chunk_end_year}...")
            
            # Define date range for this chunk
            from_openmeteo_string_date = f"{current_year}-01-01"
            to_openmeteo_string_date = f"{chunk_end_year}-12-31"
            
            # Create temporary file for this decade's data
            temp_json_file = f"{json_file_path}.temp_decade_{decade_count}"
            
            try:
                # Download data for this decade
                SWDbuilder._download_weather_data(
                    server_url,
                    site_latitude_north_deg,
                    site_longitude_east_deg,
                    from_openmeteo_string_date,
                    to_openmeteo_string_date,
                    temp_json_file
                )
                
                # Load the temporary data
                with open(temp_json_file, 'r') as f:
                    decade_data = json.load(f)
                
                # Initialize combined_data with first decade's metadata
                if combined_data is None:
                    combined_data = {
                        'latitude': decade_data['latitude'],
                        'longitude': decade_data['longitude'],
                        'elevation': decade_data['elevation'],
                        'timezone': decade_data['timezone'],
                        'hourly': {},
                        'hourly_units': decade_data['hourly_units'],
                        'site_latitude': decade_data['site_latitude'],
                        'site_longitude': decade_data['site_longitude']
                    }
                    
                    # Initialize hourly data structure
                    for variable in decade_data['hourly']:
                        combined_data['hourly'][variable] = []
                
                # Append this decade's data to combined data
                for variable in decade_data['hourly']:
                    combined_data['hourly'][variable].extend(decade_data['hourly'][variable])
                
                # Append epoch times
                all_epochtimes_ms.extend(decade_data['epochtimems'])
                
                # Clean up temporary file
                import os
                os.remove(temp_json_file)
                
                print(f"Successfully downloaded and merged data for chunk {decade_count} ({current_year}-{chunk_end_year})")
                
                # Add a delay between requests to be respectful to the server
                import time
                time.sleep(30)  # 30-second delay between decade requests
                
            except Exception as e:
                print(f"Failed to download data for chunk {decade_count} ({current_year}-{chunk_end_year}): {e}")
                
                # If timeout error and chunk size is 10, try reducing to 5-year chunks
                if "timeout" in str(e).lower() and chunk_size == 10:
                    print("Timeout detected. Reducing chunk size from 10 years to 5 years for remaining requests.")
                    chunk_size = 5
                    # Don't advance current_year, retry this chunk with smaller size
                    continue
                
                # Clean up temporary file if it exists
                import os
                if os.path.exists(temp_json_file):
                    os.remove(temp_json_file)
                # Continue to next chunk
                current_year = chunk_end_year + 1
                continue
            
            # Move to next chunk
            current_year = chunk_end_year + 1
        
        # Check if we got any data
        if combined_data is None or not all_epochtimes_ms:
            raise ValueError("No weather data was successfully downloaded")
        
        # Add combined epoch times
        combined_data['epochtimems'] = all_epochtimes_ms
        
        # Save the combined data
        with open(json_file_path, 'w') as json_file:
            json.dump(combined_data, json_file)
            print(f"Combined weather file {json_file_path} created with {len(all_epochtimes_ms)} data points from {decade_count} chunks")

    # @staticmethod
    # def build(from_requested_stringdate: str = None, to_requested_stringdate: str = None, albedo: float = 0.1, pollution: float = 0.1, from_to_naming: dict[str, str] = DEFAULT_FROM_TO_NAMING) -> SiteWeatherData:
    #     """
    #     Static method to build SiteWeatherData.

    #     Args:
    #         location: Location name
    #         latitude_north_deg: Latitude in degrees north
    #         longitude_east_deg: Longitude in degrees east
    #         from_requested_stringdate: Start date string
    #         to_requested_stringdate: End date string
    #         albedo: Albedo value
    #         pollution: Pollution value
    #         from_to_naming: Variable naming mapping

    #     Returns:
    #         SiteWeatherData object
    #     """
    #     builder = SWDbuilder(location, latitude_north_deg, longitude_east_deg)
    #     return builder(from_requested_stringdate, to_requested_stringdate, albedo, pollution, from_to_naming)

    def __call__(self, from_stringdate: str = None, to_stringdate: str = None, albedo: float = 0.1, pollution: float = 0.1, from_to_naming: dict[str, str] = DEFAULT_FROM_TO_NAMING) -> SiteWeatherData:
        """Create SiteWeatherData instance for specified date range and parameters.

        This method creates a SiteWeatherData instance by extracting weather data
        for the specified date range and applying the given parameters for albedo,
        pollution, and variable naming.

        :param from_stringdate: Start date for weather data extraction (optional)
        :type from_stringdate: str, optional
        :param to_stringdate: End date for weather data extraction (optional)
        :type to_stringdate: str, optional
        :param albedo: Surface albedo value for radiative calculations
        :type albedo: float
        :param pollution: Pollution factor for atmospheric calculations
        :type pollution: float
        :param from_to_naming: Variable naming mapping dictionary
        :type from_to_naming: dict[str, str]
        :return: SiteWeatherData instance with extracted weather data
        :rtype: SiteWeatherData
        :raises ValueError: If requested date range is outside available data range
        """
        if from_stringdate is not None:
            from_requested_epochtimems: int = stringdate_to_epochtimems(from_stringdate + ' 0:00:00', date_format=REGULAR_DATETIME_FORMAT, timezone_str=local_timezone())
            if from_requested_epochtimems < self.first_epochtimems:
                raise ValueError(f"Initial requested date {from_stringdate} is lower than the earliest recorded date {epochtimems_to_stringdate(self.first_epochtimems, date_format=REGULAR_DATETIME_FORMAT, timezone_str=local_timezone())}")
        else:
            from_requested_epochtimems = self.first_epochtimems

        if to_stringdate is not None:
            to_requested_epochtimems: int = stringdate_to_epochtimems(to_stringdate + ' 23:00:00', date_format=REGULAR_DATETIME_FORMAT, timezone_str=local_timezone())
            if to_requested_epochtimems > self.last_epochtimems:
                raise ValueError(f"Final requested date {to_stringdate} is greater than the latest recorded date {epochtimems_to_stringdate(self.last_epochtimems, date_format=REGULAR_DATETIME_FORMAT, timezone_str=local_timezone())}")
        else:
            to_requested_epochtimems = self.last_epochtimems

        print(f"Weather data from: {epochtimems_to_stringdate(from_requested_epochtimems, date_format=REGULAR_DATETIME_FORMAT, timezone_str=local_timezone())} to {epochtimems_to_stringdate(to_requested_epochtimems, date_format=REGULAR_DATETIME_FORMAT, timezone_str=local_timezone())}")

        indices = list()
        for i, epochtimems in enumerate(self.epochtimes_ms):
            if from_requested_epochtimems <= epochtimems <= to_requested_epochtimems:
                indices.append(i)
        requested_epochtimes_ms: list[int] = [self.epochtimes_ms[i] for i in indices]
        requested_variable_values: dict[str, list[float]] = dict()
        requested_variable_units: dict[str, str] = dict()

        # Only process variables that we actually have in our downloaded data
        for original_variable_name, requested_variable_name in from_to_naming.items():
            if requested_variable_name is not None and original_variable_name in self.variables_values:
                requested_variable_values[requested_variable_name] = [(self.variables_values[original_variable_name])[i] for i in indices]
                requested_variable_units[requested_variable_name] = self.variables_units[original_variable_name]

        site_weather_data = SiteWeatherData(
            location=self.location,
            site_latitude_north_deg=self.site_latitude_north_deg,
            site_longitude_east_deg=self.site_longitude_east_deg,
            weather_latitude_north_deg=self.weather_latitude_north_deg,
            weather_longitude_east_deg=self.weather_longitude_east_deg,
            epochtimes_ms=requested_epochtimes_ms,
            variable_values=requested_variable_values,
            variable_units=requested_variable_units,
            albedo=albedo,
            pollution=pollution,
            elevation=self.site_elevation_m,
            timezone_str=self.timezone_str
            )

        # for original_var_name, requested_var_name in from_to_naming.items():
        #     if requested_var_name is not None and requested_var_name in requested_variable_values:
        #         site_weather_data.add_variable(requested_var_name, self.variables_units[original_var_name], requested_variable_values[requested_var_name])

        # Add derived variables only if the required source variables exist
        site_weather_data.add_variable('absolute_humidity', 'kg water/kg air', site_weather_data.absolute_humidity_kg_per_kg())
        site_weather_data.add_variable('precipitation_mass', 'kg/m2/s', [p/1000/60 for p in site_weather_data.get('precipitation')])
        
        # Only add snowfall_mass if snowfall data is available
        if 'snowfall' in site_weather_data.variable_names:
            site_weather_data.add_variable('snowfall_mass', 'kg/m2/s', [p/1000/60 for p in site_weather_data.get('snowfall')])
        
        site_weather_data.add_variable('wind_speed_m_s', 'm/s', [p/3.6 for p in site_weather_data.get('wind_speed_km_h')])
        
        # Only add wind_gusts_m_s if wind_gusts_km_h data is available
        if 'wind_gusts_km_h' in site_weather_data.variable_names:
            site_weather_data.add_variable('wind_gusts_m_s', 'm/s', [p/3.6 for p in site_weather_data.get('wind_gusts_km_h')])
        
        # Only add longwave_radiation_sky if dew_point_temperature is available
        if 'dew_point_temperature' in site_weather_data.variable_names:
            site_weather_data.add_variable('longwave_radiation_sky', 'W/m2', site_weather_data.long_wave_radiation_sky())
        site_weather_data.origin = "https://open-meteo.com"

        return site_weather_data

    def __str__(self) -> str:
        """Return string representation of the SWDbuilder instance.

        :return: Formatted string with location, coordinates, data range, and available variables
        :rtype: str
        """
        string = f"Weather data builder for {self.location}\n"
        string += f"Site coordinates: lat={self.site_latitude_north_deg}, lon={self.site_longitude_east_deg}\n"
        string += f"Weather coordinates: lat={self.weather_latitude_north_deg}, lon={self.weather_longitude_east_deg}\n"
        string += f"Data range: {epochtimems_to_stringdate(self.first_epochtimems, date_format='%d/%m/%Y', timezone_str=self.timezone_str)} to {epochtimems_to_stringdate(self.last_epochtimems, date_format='%d/%m/%Y', timezone_str=self.timezone_str)}\n"
        string += f"Available variables: {', '.join(self.variable_names)}\n"
        return string


class SiteWeatherData:
    """Stores and processes weather time series data for building energy analysis.

    This class encapsulates all weather-related data for a specific site, including
    location information, atmospheric parameters, and time series weather data.
    """

    def __init__(self, location: str,
                 site_latitude_north_deg: float,
                 site_longitude_east_deg: float,
                 weather_latitude_north_deg: float,
                 weather_longitude_east_deg: float,
                 epochtimes_ms: list[int],
                 variable_values: dict[str, list[float]],
                 variable_units: dict[str, str],
                 albedo: float,
                 pollution: float,
                 elevation: float = None,
                 timezone_str: str = None) -> None:
        """Initialize a SiteWeatherData instance.

        :param location: Site location name
        :type location: str
        :param site_latitude_north_deg: Site latitude in degrees north
        :type site_latitude_north_deg: float
        :param site_longitude_east_deg: Site longitude in degrees east
        :type site_longitude_east_deg: float
        :param weather_latitude_north_deg: Weather station latitude
        :type weather_latitude_north_deg: float
        :param weather_longitude_east_deg: Weather station longitude
        :type weather_longitude_east_deg: float
        :param epochtimes_ms: List of epoch times in milliseconds
        :type epochtimes_ms: list[int]
        :param variable_values: Weather variable data
        :type variable_values: dict[str, list[float]]
        :param variable_units: Weather variable units
        :type variable_units: dict[str, str]
        :param albedo: Ground albedo coefficient (0-1)
        :type albedo: float
        :param pollution: Atmospheric pollution coefficient (AOD)
        :type pollution: float
        :param elevation: Site elevation in meters
        :type elevation: float
        :param timezone_str: Site timezone string
        :type timezone_str: str
        """
        self.origin: str = 'https://open-meteo.com'
        self.location: str = location
        self.site_latitude_north_deg: float = site_latitude_north_deg
        self.site_longitude_east_deg: float = site_longitude_east_deg
        self.weather_latitude_north_deg: float = weather_latitude_north_deg
        self.weather_longitude_east_deg: float = weather_longitude_east_deg
        self._epochtimes_ms: list[int] = epochtimes_ms
        self.variable_units = variable_units
        self.albedo: float = albedo
        self.elevation: float = elevation
        self.site_elevation_m: float = elevation
        # pollution is relative to Aerosol Optical Depth (AOD, sometimes called Aerosol Optical Thickness), which is provided by AERONET stations or satellite retrieval, at 380 nm and 500 nm (e.g. satellite retrieval of AOD at 500 nm is available at https://neo.sci.gsfc.nasa.gov/view.php?datasetId=AERONET_AOD_500_Dark_Target_Deep_Blue_Combined_Daily_5km_V3). It represents how much solar radiation at 380nm and 500nm wavelengths is attenuated (scattered + absorbed) as it passes through the atmosphere. Here, an average AOD 380nm and 500nm is used: it's named pollution.
        # AOD = 0.0 → perfectly clear (no aerosol extinction).
        # AOD = 0.1–0.2 → very clear atmosphere.
        # AOD = 0.3–0.5 → hazy conditions.
        # AOD > 1 → heavy pollution or dust storm.
        self.pollution: float = pollution
        self.timezone_str: str = timezone_str

        self._epochtimes_ms: list[int] = epochtimes_ms
        # Optimize datetime conversions - only convert when needed (lazy loading)
        self._datetimes: list[datetime] = None
        self._stringdates: list[str] = None

        self._variable_name_data: dict[str, list[float]] = variable_values
        self.variable_units: dict[str, str] = variable_units

        # Cache for expensive calculations
        self._calculation_cache = {}

    def __contains__(self, variable_name: str) -> bool:
        """Check if a variable name exists in the weather data.

        :param variable_name: Name of the variable to check
        :type variable_name: str
        :return: True if the variable exists, False otherwise
        :rtype: bool
        """
        return variable_name in self._variable_name_data

    @property
    def datetimes(self) -> list[datetime]:
        """Get list of datetime objects for weather data timestamps.

        :return: List of datetime objects corresponding to weather data timestamps
        :rtype: list[datetime]
        """
        if self._datetimes is None:
            # Lazy loading - only convert when accessed
            self._datetimes = [epochtimems_to_datetime(epochtime_ms, timezone_str=self.timezone_str) for epochtime_ms in self._epochtimes_ms]
        return self._datetimes

    @property
    def stringdates(self) -> list[str]:
        """Get list of string date representations for weather data timestamps.

        :return: List of string date representations corresponding to weather data timestamps
        :rtype: list[str]
        """
        if self._stringdates is None:
            # Lazy loading - only convert when accessed
            self._stringdates = [epochtimems_to_stringdate(epochtime_ms, timezone_str=local_timezone()) for epochtime_ms in self._epochtimes_ms]
        return self._stringdates

    @property
    def epochtimes_ms(self) -> list[int]:
        """Get list of epoch times in milliseconds for weather data timestamps.

        :return: List of epoch times in milliseconds corresponding to weather data timestamps
        :rtype: list[int]
        """
        return self._epochtimes_ms

    @property
    def from_stringdate(self) -> str:
        """Get the start date of the weather data as a string.

        :return: Start date of the weather data as a string
        :rtype: str
        """
        return self.stringdates[0]

    @property
    def to_stringdate(self) -> str:
        """Get the end date of the weather data as a string.

        :return: End date of the weather data as a string
        :rtype: str
        """
        return self.stringdates[-1]

    @property
    def from_epochtimems(self) -> int:
        """Get the start epoch time in milliseconds of the weather data.

        :return: Start epoch time in milliseconds of the weather data
        :rtype: int
        """
        return self._epochtimes_ms[0]

    @property
    def to_epochtimems(self) -> int:
        """Get the end epoch time in milliseconds of the weather data.

        :return: End epoch time in milliseconds of the weather data
        :rtype: int
        """
        return self._epochtimes_ms[-1]

    @property
    def from_datetime(self) -> datetime:
        """Get the start datetime of the weather data.

        :return: Start datetime of the weather data
        :rtype: datetime
        """
        return self.datetimes[0]

    @property
    def to_datetime(self) -> datetime:
        """Get the end datetime of the weather data.

        :return: End datetime of the weather data
        :rtype: datetime
        """
        return self.datetimes[-1]

    @property
    def variable_names(self) -> list[str]:
        """Get list of available weather variable names.

        :return: List of available weather variable names
        :rtype: list[str]
        """
        return self._variable_name_data.keys()

    def __len__(self) -> int:
        """Get the number of weather data points.

        :return: Number of weather data points
        :rtype: int
        """
        return len(self._epochtimes_ms)

    def __str__(self) -> str:
        """Return string representation of the SiteWeatherData instance.

        :return: Formatted string with location, coordinates, data range, and available variables
        :rtype: str
        """
        string: str = "site is %s (lat:%f,lon:%f) " % (
            self.location, self.site_latitude_north_deg, self.site_longitude_east_deg)
        if self._epochtimes_ms is not None:
            string += "with data from %s to %s\nweather variables are:\n" % (epochtimems_to_stringdate(
                self._epochtimes_ms[0]), epochtimems_to_stringdate(self._epochtimes_ms[-1]))
        else:
            string += "without data loaded yet\nweather variables are:\n"
        for v in self._variable_name_data:
            string += '- %s (%s)\n' % (v, self.variable_units[v])
        return string

    def units(self, variable_name: str = None):
        """Return the unit of a variable.

        :param variable_name: file_name of the variable
        :type variable_name: str
        :return: unit of this variable
        :rtype: str
        """
        if variable_name is None:
            return self.variable_units
        return self.variable_units[variable_name]

    def add_variable(self, variable_name: str, variable_unit: str, values: list[float | datetime]):
        """Add a new weather variable to the dataset.

        This method adds a new weather variable with its unit and values to the
        weather dataset, with automatic data type optimization for numerical data.

        :param variable_name: Name of the variable to add
        :type variable_name: str
        :param variable_unit: Unit of the variable
        :type variable_unit: str
        :param values: List of values for the variable
        :type values: list[float | datetime]
        """
        if variable_name not in self._variable_name_data and variable_name != 'datetime' and variable_name != 'epochtimems' and variable_name != 'stringdate':
            self.variable_units[variable_name] = variable_unit
            # Convert to NumPy array for better performance if it's numerical data
            if isinstance(values, list) and len(values) > 0 and isinstance(values[0], (int, float)):
                self._variable_name_data[variable_name] = np.array(values, dtype=np.float32)
            else:
                self._variable_name_data[variable_name] = values
            # Clear cache when data changes
            self._calculation_cache.clear()
            print(f"Added variable {variable_name} with unit {variable_unit}")

    def series(self, variable_name: str = None) -> list[float] | dict[str, list[float]]:
        """Get weather variable series data.

        This method returns weather variable data either for a specific variable
        or for all available variables in the dataset.

        :param variable_name: Name of the variable to retrieve (optional)
        :type variable_name: str, optional
        :return: Variable data as list or dictionary of all variables
        :rtype: list[float] | dict[str, list[float]]
        """
        if variable_name is not None:
            return self.get(variable_name)
        else:
            variable_values = dict()
            for variable_name in self.variable_names:
                if variable_name not in ('datetime', 'epochtimems', 'stringdate'):
                    variable_values[variable_name] = self.get(variable_name)
            return variable_values

    def __call__(self, variable_name: str) -> list[float | datetime.datetime]:
        """Call the instance to get weather variable data.

        :param variable_name: Name of the variable to retrieve
        :type variable_name: str
        :return: Variable data as list of values
        :rtype: list[float | datetime.datetime]
        """
        return self.get(variable_name)

    def clone(self) -> 'SiteWeatherData':
        """Create a deep copy of the SiteWeatherData instance.

        :return: Deep copy of the SiteWeatherData instance
        :rtype: SiteWeatherData
        """
        return copy.deepcopy(self)

    def get(self, variable_name: str) -> list[float | datetime.datetime]:
        """Return the data collection related to one variable.

        :param variable_name: variable file_name
        :type variable_name: str
        :return: list of float or str values corresponding to common dates for the specified variable
        :rtype: list[float or str]
        """
        if variable_name in self._variable_name_data:
            # Convert NumPy arrays back to lists for compatibility
            data = self._variable_name_data[variable_name]
            if isinstance(data, np.ndarray):
                return data.tolist()
            return data
        else:
            print(self)
            raise ValueError('Unknown variable: %s' % variable_name)

    def long_wave_radiation_sky(self) -> np.ndarray:
        """Compute the long wave radiation from the sky.

        :return: array of long wave radiation from the sky in W/m2
        :rtype: np.ndarray
        """
        # Check cache first
        cache_key = 'long_wave_radiation_sky'
        if cache_key in self._calculation_cache:
            return self._calculation_cache[cache_key]

        # Vectorized calculation using NumPy for much better performance
        dew_point_temperatures_deg = np.array(self.get('dew_point_temperature'), dtype=np.float32)
        ground_temperatures_deg = np.array(self.get('temperature'), dtype=np.float32)
        cloudiness_percent = np.array(self.get('cloudiness'), dtype=np.float32)

        # Vectorized calculations
        ground_temperatures_K = ground_temperatures_deg + 273.15

        # Calculate clear sky temperature using Swinbank model
        T_clear_K = 0.0552 * (ground_temperatures_K ** 1.5)

        # Calculate emissivities
        dew_point_norm = dew_point_temperatures_deg / 100.0
        eps_clear = 0.711 + 0.56 * dew_point_norm + 0.73 * (dew_point_norm ** 2)

        # Calculate emissive powers (both in W/m²)
        E_clear_W_per_m2 = eps_clear * Stefan_Boltzmann * (T_clear_K ** 4)
        E_cloud_W_m2 = 0.96 * Stefan_Boltzmann * ((ground_temperatures_K - 5) ** 4)

        # Vectorized final calculation (composite sky emissive power)
        cloudiness_factor = cloudiness_percent / 100.0
        _long_wave_radiation_sky_W_per_m2 = (1 - cloudiness_factor) * E_clear_W_per_m2 + cloudiness_factor * E_cloud_W_m2

        # Cache the result
        self._calculation_cache[cache_key] = _long_wave_radiation_sky_W_per_m2
        return -_long_wave_radiation_sky_W_per_m2

    def surface_out_radiative_exchange(self, slope_deg: float, surface_temperature_deg: list[float], ground_temperature_deg: list[float], surface_m2: float = 1) -> tuple[np.ndarray, np.ndarray]:
        """Calculate surface radiative exchange with sky and ground.

        This method calculates the radiative exchange between a surface and the
        sky/ground environment, considering surface slope, temperatures, and
        atmospheric conditions.

        :param slope_deg: Surface slope angle in degrees
        :type slope_deg: float
        :param surface_temperature_deg: Surface temperature values in degrees Celsius
        :type surface_temperature_deg: list[float]
        :param ground_temperature_deg: Ground temperature values in degrees Celsius
        :type ground_temperature_deg: list[float]
        :param surface_m2: Surface area in square meters
        :type surface_m2: float
        :return: Tuple of (sky radiative exchange, ground radiative exchange) in W/m2
        :rtype: tuple[np.ndarray, np.ndarray]
        """
        # Vectorized calculation for better performance
        dew_point_temperatures_deg = np.array(self.get('dew_point_temperature'), dtype=np.float32)
        outdoor_temperatures_deg = np.array(self.get('temperature'), dtype=np.float32)
        cloudiness_percent = np.array(self.get('cloudiness'), dtype=np.float32)
        surface_temperature_deg = np.array(surface_temperature_deg, dtype=np.float32)
        ground_temperature_deg = np.array(ground_temperature_deg, dtype=np.float32)

        beta_rad = (slope_deg - 180) / 180 * pi

        # Vectorized calculations
        wall_emissivity_W_per_m2 = 0.96 * Stefan_Boltzmann * ((surface_temperature_deg + 273.15) ** 4)
        ground_irradiance_W_per_m2 = 0.96 * Stefan_Boltzmann * ((ground_temperature_deg + 273.15) ** 4)

        # Calculate clear sky temperature using Swinbank model
        outdoor_temperatures_K = outdoor_temperatures_deg + 273.15
        T_clear_K = 0.0552 * (outdoor_temperatures_K ** 1.5)

        # Calculate emissivities
        dew_point_norm = dew_point_temperatures_deg / 100.0
        eps_clear = 0.711 + 0.56 * dew_point_norm + 0.73 * (dew_point_norm ** 2)

        # Calculate emissive powers (both in W/m²)
        clear_sky_irradiance_W_per_m2 = eps_clear * Stefan_Boltzmann * (T_clear_K ** 4)
        cloud_irradiance_W_per_m2 = 0.96 * Stefan_Boltzmann * ((outdoor_temperatures_K - 5) ** 4)

        # Composite sky emissive power
        cloudiness_factor = cloudiness_percent / 100.0
        sky_irradiance_W_per_m2 = (1 - cloudiness_factor) * clear_sky_irradiance_W_per_m2 + cloudiness_factor * cloud_irradiance_W_per_m2

        # Vectorized final calculations
        cos_beta = cos(beta_rad)
        phis_surface_ground_W_per_m2 = (wall_emissivity_W_per_m2 - ground_irradiance_W_per_m2) * (1 - cos_beta) / 2 * surface_m2
        phis_surface_sky_W_per_m2 = (wall_emissivity_W_per_m2 - sky_irradiance_W_per_m2) * (1 + cos_beta) / 2 * surface_m2

        return phis_surface_sky_W_per_m2, phis_surface_ground_W_per_m2

    def absolute_humidity_kg_per_kg(self) -> np.ndarray:
        """Calculate absolute humidity in kg water per kg of dry air for all time points.

        This method calculates the absolute humidity for all time points in the
        weather dataset using temperature, relative humidity, and atmospheric pressure.

        :return: Array of absolute humidity values in kg water per kg of dry air
        :rtype: np.ndarray
        """
        Rs_J_per_kg_K = 287.06
        # Vectorized calculation for better performance
        temperatures_deg = np.array(self.get('temperature'), dtype=np.float32)
        relative_humidities_percent = np.array(self.get('humidity'), dtype=np.float32)
        atmospheric_pressures_hPa = np.array(self.get('pressure'), dtype=np.float32)

        # Vectorized calculations
        temp_kelvin = temperatures_deg + 273.15
        exp_term = np.exp(17.5043 * temperatures_deg / (241.2 + temperatures_deg))
        density_kg_per_m3 = (atmospheric_pressures_hPa * 100 - 2.30617 * relative_humidities_percent * exp_term) / (Rs_J_per_kg_K * temp_kelvin)

        # Calculate absolute humidity using vectorized operations
        abs_humidity_kg_per_m3 = np.array([absolute_humidity_kg_per_m3(t, rh) for t, rh in zip(temperatures_deg, relative_humidities_percent)], dtype=np.float32)
        _absolute_humidities_kg_per_kg = abs_humidity_kg_per_m3 / density_kg_per_m3

        return _absolute_humidities_kg_per_kg

    def day_degrees(self, temperature_reference=18, heat=True):
        """Compute heating or cooling day degrees and print in terminal the sum of day degrees per month.

        :param temperature_reference: reference temperature (default is 18°C)
        :param heat: True if heating, False if cooling
        :return: list of day dates as string, list of day average, min and max outdoor temperature and day degrees per day
        :rtype: [list[str], list[float], list[float], list[float], list[float]]
        """
        datetimes: list[datetime] = self.datetimes
        stringdates: list[str] = self.stringdates
        temperatures: list[float] = self.get('temperature')
        dd_months: list[int] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        month_names: list[str] = ['January', 'February', 'March', 'April', 'May',
                                  'June', 'July', 'August', 'September', 'October', 'November', 'December']
        day_stringdate_days = list()
        average_temperature_days = list()
        min_temperature_days = list()
        max_temperature_days = list()
        day_degrees = list()
        day_temperature = list()
        current_day = datetimes[0].day
        for k in range(len(datetimes)):
            if current_day == datetimes[k].day:
                day_temperature.append(temperatures[k])
            else:
                day_stringdate_days.append(stringdates[k-1].split(' ')[0])
                average_day_temperature: float = sum(
                    day_temperature)/len(day_temperature)
                average_temperature_days.append(average_day_temperature)
                min_temperature_days.append(min(day_temperature))
                max_temperature_days.append(max(day_temperature))
                hdd = 0
                if heat:
                    if average_day_temperature < temperature_reference:
                        hdd = temperature_reference - average_day_temperature
                elif not heat:
                    if average_day_temperature > temperature_reference:
                        hdd = average_day_temperature - temperature_reference
                day_degrees.append(hdd)
                dd_months[datetimes[k].month-1] += hdd
                day_temperature = list()
            current_day = datetimes[k].day
        for i in range(len(dd_months)):
            print('day degrees', month_names[i], ': ', dd_months[i])
        return day_stringdate_days, average_temperature_days, min_temperature_days, max_temperature_days, day_degrees

    def data_datetimes_names(self) -> tuple[dict[str, list[float]], list[datetime], dict]:
        return self._variable_name_data, self.datetimes, self.variable_units

    def plot(self, variable_names: list[str] = None, all: bool = False, plot_type: str = 'timeplot', averager: str = '- hour', threshold: float = 0.7): 
        if variable_names is not None:
            if isinstance(variable_names, str):
                variable_names = [variable_names]
            variable_values: dict[str, list[float]] = {v: self.get(v) for v in variable_names}
        else:
            variable_values = self._variable_name_data
        TimeSeriesPlotter(variable_values, self.datetimes, self.variable_units, all=all, plot_type=plot_type, averager=averager, title='Weather Data %s' % self.location, threshold=threshold)


def temperature_distribution(datetimes: list[datetime.datetime], Toutdoors_C: list[float], reference_temperature_C: float = None) -> None:
    """Generate and visualize the distribution of outdoor temperatures.

    :param datetimes: List of datetime objects corresponding to temperature measurements
    :type datetimes: list[datetime.datetime]
    :param Toutdoors_C: List of outdoor temperatures in degrees Celsius
    :type Toutdoors_C: list[float]
    :param reference_temperature_C: Reference temperature line to display
    :type reference_temperature_C: float
    :return: None
    :rtype: None
    """

    # Convert to numpy array for easier analysis
    temperatures = np.array(Toutdoors_C)
    min_max_datetimes = np.array([datetimes[0], datetimes[-1]])

    # Calculate statistics
    mean_temp = np.mean(temperatures)
    std_temp = np.std(temperatures)
    min_temp = np.min(temperatures)
    max_temp = np.max(temperatures)

    # Create distribution plots
    fig = make_subplots(rows=2, cols=2, specs=[[{"secondary_y": False}, {"secondary_y": False}], [{"secondary_y": False}, {"secondary_y": False}]])

    # 1. Time series
    fig.add_trace(go.Scatter(x=datetimes, y=Toutdoors_C, mode='lines', name='Outdoor Temperature', line=dict(color='blue', width=1)), row=1, col=1)
    if reference_temperature_C is not None:
        fig.add_trace(go.Scatter(x=min_max_datetimes, y=[reference_temperature_C, reference_temperature_C], mode='lines', name='Reference Temperature', line=dict(color='red', width=2, dash='dash')), row=1, col=1)

    # 2. Distribution (histogram)
    fig.add_trace(go.Histogram(x=Toutdoors_C, nbinsx=50, name='Temperature Distribution', marker_color='lightblue', opacity=0.7), row=1, col=2)
    if reference_temperature_C is not None:
        fig.add_trace(go.Scatter(x=min_max_datetimes, y=[reference_temperature_C, reference_temperature_C], mode='lines', name='Reference Temperature', line=dict(color='red', width=2, dash='dash')), row=1, col=2)
        hist, bin_edges = np.histogram(Toutdoors_C, bins=50)
        y_min = 0
        y_max = np.max(hist)
        fig.add_trace(go.Scatter(x=[reference_temperature_C, reference_temperature_C], y=[y_min, y_max], mode='lines', name='Reference Temperature', line=dict(color='red', width=2, dash='dash')), row=1, col=2)

    # 3. Monthly box plot
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for month in range(1, 13):
        month_temps = [temp for temp, dt in zip(Toutdoors_C, datetimes) if dt.month == month]
        if month_temps:
            fig.add_trace(go.Box(y=month_temps, name=month_names[month-1], boxpoints='outliers', jitter=0.3, pointpos=-1.8), row=2, col=1)
    if reference_temperature_C is not None:
        fig.add_trace(go.Scatter(x=month_names, y=[reference_temperature_C] * 12, mode='lines', name='Reference Temperature', line=dict(color='red', width=2, dash='dash')), row=2, col=1)

    # 4. Temperature histogram with normal distribution overlay
    fig.add_trace(go.Histogram(x=Toutdoors_C, nbinsx=30, name='Temperature Histogram', marker_color='lightgreen', opacity=0.7), row=2, col=2)
    if reference_temperature_C is not None:
        hist, bin_edges = np.histogram(Toutdoors_C, bins=30)
        y_min = 0
        y_max = max(hist)
        fig.add_trace(go.Scatter(x=[reference_temperature_C, reference_temperature_C], y=[y_min, y_max], mode='lines', name='Reference Temperature', line=dict(color='red', width=2, dash='dash')), row=2, col=2)
    x_norm = np.linspace(min_temp, max_temp, 100)
    y_norm = len(temperatures) * (max_temp - min_temp) / 30 * (1 / (std_temp * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_norm - mean_temp) / std_temp) ** 2)
    fig.add_trace(
        go.Scatter(x=x_norm, y=y_norm, mode='lines', name='Normal Distribution', line=dict(color='red', width=2)),
        row=2, col=2
    )

    # Update layout
    fig.update_layout(
        title="Outdoor Temperature Distribution Analysis",
        height=800,
        showlegend=True
    )

    # Update axes labels
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
    fig.update_xaxes(title_text="Temperature (°C)", row=1, col=2)
    fig.update_yaxes(title_text="Frequency", row=1, col=2)
    fig.update_xaxes(title_text="Month", row=2, col=1)
    fig.update_yaxes(title_text="Temperature (°C)", row=2, col=1)
    fig.update_xaxes(title_text="Temperature (°C)", row=2, col=2)
    fig.update_yaxes(title_text="Frequency", row=2, col=2)

    # Use non-interactive backend to avoid Tkinter crashes on macOS
    try:
        # Try to show in browser if possible
        fig.show()
    except Exception:
        # Fallback: save to HTML file instead
        fig.write_html("temperature_distribution.html")
        print("Plot saved to temperature_distribution.html")
