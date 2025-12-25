# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from batem.core.weather import SWDbuilder
from batem.core.solar import SolarModel, SolarSystem, Collector

location: str = 'Tirana'
latitude_north_deg = 41.330815
longitude_east_deg = 19.819229
weather_year: int = 2023
albedo = 0.1

site_weather_data = SWDbuilder(location=location, latitude_north_deg=latitude_north_deg, longitude_east_deg=longitude_east_deg)(from_stringdate='1/01/%i' % weather_year, to_stringdate='1/01/%i' % (weather_year+1), albedo=albedo, pollution=0.1)

window_solar_mask = None
# window_solar_mask = buildingenergy.solar.RectangularMask((-86, 60), (20, 68))

solar_model = SolarModel(site_weather_data)
solar_system = SolarSystem(solar_model)
Collector(solar_system, 'south', exposure_deg=0, slope_deg=90, surface_m2=1, solar_factor=1)
Collector(solar_system, 'east', exposure_deg=-90, slope_deg=90, surface_m2=1, solar_factor=1)
Collector(solar_system, 'west', exposure_deg=90, slope_deg=90, surface_m2=1, solar_factor=1)
Collector(solar_system, 'north', exposure_deg=180, slope_deg=90, surface_m2=1, solar_factor=1)
Collector(solar_system, 'horizontal', exposure_deg=0, slope_deg=180, surface_m2=1, solar_factor=1)

solar_system.day_degrees_solar_gain_xls('dju20-26', heat_temperature_reference=20, cool_temperature_reference=26)
