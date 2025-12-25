

from batem.reno.utils import TimeSpaceHandler
from timezonefinder import TimezoneFinder


WEATHER_VARIABLES = ["temperature_2m",
                     "relative_humidity_2m",
                     "apparent_temperature",
                     "dew_point_2m",
                     "precipitation",
                     "rain",
                     "showers",
                     "snowfall",
                     "snow_depth",
                     "surface_pressure",
                     "cloud_cover",
                     "cloud_cover_low",
                     "cloud_cover_mid",
                     "cloud_cover_high",
                     "wind_speed_10m",
                     "wind_direction_10m",
                     "wind_gusts_10m",
                     "soil_temperature_0cm",
                     "shortwave_radiation",
                     "direct_radiation",
                     "diffuse_radiation",
                     "direct_normal_irradiance",
                     "shortwave_radiation_instant",
                     "direct_radiation_instant",
                     "diffuse_radiation_instant",
                     "direct_normal_irradiance_instant",
                     "terrestrial_radiation_instant"]

OPEN_WEATHER_TO_NAMES_MAP = {'temperature_2m': 'temperature',
                             'dew_point_2m': 'dew_point_temperature',
                             'wind_speed_10m': 'wind_speed',
                             'wind_direction_10m': 'wind_direction_in_deg',
                             'apparent_temperature': 'feels_like',
                             'relative_humidity_2m': 'humidity',
                             'cloud_cover': 'cloudiness',
                             'surface_pressure': 'pressure'}


class WeatherData:

    def __init__(self, time_space_handler: TimeSpaceHandler):
        self.location = time_space_handler.location

        self.timezone = TimezoneFinder().timezone_at(
            lat=time_space_handler.latitude_north_deg,
            lng=time_space_handler.longitude_east_deg)

        self.variables_by_time: dict[float, dict[str, float]] = {}
        self.units_by_variable: dict[str, str] = {}
