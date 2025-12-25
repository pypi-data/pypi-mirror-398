"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from batem.core.weather import SiteWeatherData, SWDbuilder
from batem.core.solar import SolarModel

# location = 'LaCoteSaintAndre'
# year = 2023
# latitude, longitude = 45.393775, 5.260494

# location: str = 'AutransMeaudre'
# year = 2023
# latitude, longitude = 45.175560185534195, 5.5427723689148065

# location = 'Assouan'
# year = 2023
# latitude, longitude = 24.02769921861417, 32.87455490478971

# location = 'Aigle'
# year = 2023
# latitude, longitude = 45.011352235478476, 6.324482739625443

# location = 'Pilatte'
# year = 2023
# latitude, longitude = 44.87038737113471, 6.331994116259443

# location = 'Columbia'
# year = 2023
# latitude, longitude = 10.434159, -73.277765

# location = 'Seville'
# year = 2023
# latitude, longitude = 37.39459541966303, -5.976329994207859

location: str = 'narbonne'
year = 2023
latitude_north_deg, longitude_east_deg = 43.185457207892796, 3.0031356684177566

site_weather_data: SiteWeatherData = SWDbuilder(location=location, latitude_north_deg=latitude_north_deg, longitude_east_deg=longitude_east_deg)(from_stringdate='1/01/%i' % year, to_stringdate='31/12/%i' % year, albedo=0.1)
solar_model = SolarModel(site_weather_data)
solar_model.try_export()
