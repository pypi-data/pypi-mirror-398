"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
from core.weather import SiteWeatherData, SWDbuilder
import matplotlib.pylab as plt
from pandas.plotting import register_matplotlib_converters


register_matplotlib_converters()
site_weather_data: SiteWeatherData = SWDbuilder(location='refuge_des_bans', from_requested_stringdate='1/01/2019', to_requested_stringdate='1/01/2020',
                                                            self.site_latitude_north_deg=44.8344080974042, longitude_east_deg=6.3612244173071915,  albedo=.1).site_weather_data

print(site_weather_data.from_stringdate, '>', site_weather_data.to_stringdate)
site_weather_data.day_degrees()
fig, ax = plt.subplots()
plt.plot(site_weather_data.series('datetime'),
         site_weather_data.series('temperature'))
ax.set_title('temperature')
ax.axis('tight')
fig, ax = plt.subplots()
plt.plot(site_weather_data.series('datetime'),
         site_weather_data.series('cloudiness'))
ax.set_title('cloudiness')
ax.axis('tight')
fig, ax = plt.subplots()
plt.plot(site_weather_data.series('stringdate'),
         site_weather_data.series('humidity'))
ax.set_title('humidity')
ax.axis('tight')
fig, ax = plt.subplots()
plt.plot(site_weather_data.series('stringdate'),
         site_weather_data.series('wind_speed'))
ax.set_title('wind_speed')
ax.axis('tight')

plt.show()
