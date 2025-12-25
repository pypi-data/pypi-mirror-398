

from datetime import datetime
from dataclasses import dataclass
from batem.core import weather
from batem.core.solar import MOUNT_TYPES
from batem.core import solar


@dataclass
class ProductionData:
    """
    Container for production data.
    The production data is stored in hourly intervals.
    The data is stored in kW.
    """
    usage_hourly: dict[datetime, float]


class PVPlant:
    def __init__(self,
                 weather_data: weather.SiteWeatherData,
                 solar_model: solar.SolarModel,
                 exposure_deg: float = 0,
                 slope_deg: float = 160,
                 pv_efficiency: float = .2,
                 panel_width_m: float = 1,
                 panel_height_m: float = 1.7,
                 number_of_panels: int = 3,
                 peak_power_kW: float = 8,
                 PV_inverter_efficiency: float = 0.95,
                 temperature_coefficient: float = 0.0035,
                 distance_between_arrays_m: float = 1.7,
                 mount_type: MOUNT_TYPES = MOUNT_TYPES.FLAT):
        """
        The location is the location of the PV plant.
        The latitude and longitude are the latitude
        and longitude of the PV plant.
        The exposure is the angle between the South
        and the direction of the PV plant.
        I.e. 0° is South, -90° is West, 90° is East, 180° is North.
        The slope is the angle between the horizontal
        and the plane of the PV plant.
        I.e. 0° is horizontal, 90° is vertical.
        The PV efficiency is the efficiency of the PV panel.
        The panel width and height are the width and height of the PV panel.
        The number of panels per array is the number of panels in each array.
        The peak power is the peak power of the PV plant.
        The PV inverter efficiency is the efficiency of the PV inverter.
        The temperature coefficient is the temperature coefficient
        of the PV panel.
        The distance between arrays is the distance between
        the arrays of the PV plant.
        The mount type is the type of mount of the PV plant.
        The power production is the power production of the PV plant
        expressed in kWh.
        """

        self.weather_data = weather_data
        self.solar_model = solar_model
        self.exposure_deg = exposure_deg
        self.slope_deg = slope_deg
        self.pv_efficiency = pv_efficiency
        self.panel_width_m = panel_width_m
        self.panel_height_m = panel_height_m
        self.number_of_panels = number_of_panels
        self.peak_power_kW = peak_power_kW
        self.PV_inverter_efficiency = PV_inverter_efficiency
        self.temperature_coefficient = temperature_coefficient
        self.distance_between_arrays_m = distance_between_arrays_m
        self.mount_type = mount_type

        self.production: ProductionData
