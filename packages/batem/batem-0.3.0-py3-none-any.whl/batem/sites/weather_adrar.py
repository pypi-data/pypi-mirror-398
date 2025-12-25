"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
from batem.core.weather import SWDbuilder
from batem.core.solar import CANONICAL_RADIATIONS, SolarModel
from batem.core.timemg import datetime_to_stringdate
from batem.core.data import DataProvider, DataProviderBuilder
import matplotlib.pylab as plt
from matplotlib.patches import Ellipse
from datetime import datetime


def plot_rain_events(datetimes: list[datetime], precipitations: list[float], ax=None):
    if ax is None:
        fig, ax = plt.subplots()
    days_with_rain: list[str] = list()
    days: list[str] = list()
    rains_dict: dict[tuple[float, float], int] = dict()
    rains_months_dict: dict[tuple[float, float], list[str]] = dict()
    rain_duration: int = 0
    max_duration = 0
    rain_quantity: float = 0
    max_quantity = 0
    threshold = 0.1
    was_raining = False
    for k, precipitation in enumerate(precipitations):
        stringdate = core.timemg.datetime_to_stringdate(
            datetimes[k]).split(' ')[0]
        if stringdate not in days:
            days.append(stringdate)
        if was_raining and precipitation > 0:  # ongoing rain event
            rain_duration += 1
            rain_quantity += precipitation
            if stringdate not in days_with_rain:
                days_with_rain.append(stringdate)
        elif was_raining and precipitation == 0:  # end of rain event
            characteristics: tuple[int, int] = (
                rain_duration, round(10*rain_quantity/rain_duration)/10)
            max_duration: int = max(max_duration, characteristics[0])
            max_quantity: int = max(max_quantity, characteristics[1])
            month = datetimes[k].month
            if characteristics in rains_dict:
                rains_dict[characteristics] += 1
                if str(month) not in rains_months_dict[characteristics]:
                    rains_months_dict[characteristics].append(str(month))
            else:
                rains_dict[characteristics] = 1
                rains_months_dict[characteristics] = [str(month)]
            was_raining = False
            rain_duration = 0
            rain_quantity = 0
        elif not was_raining and precipitation > threshold:  # beginning of rain event
            if stringdate not in days_with_rain:
                days_with_rain.append(stringdate)
            rain_duration = 1
            rain_quantity = precipitation
            was_raining = True

    ax.set(xlim=(0, max_duration), ylim=(0, max_quantity))
    for characteristics in rains_dict:
        ellipse = Ellipse(characteristics, width=rains_dict[characteristics],
                          height=rains_dict[characteristics], edgecolor='black', facecolor='orange')
        ax.add_artist(ellipse)
        ellipse.set_alpha(0.5)
        plt.annotate(
            ','.join(rains_months_dict[characteristics]), characteristics)
    ax.set_title('rain events (numbers stands for month# (%i raining days out of %i)' % (
        len(days_with_rain), len(days)))
    ax.set_xlabel('duration in hours')
    ax.set_ylabel('quantity in mm')


dp = DataProvider(location='adrar', latitude_north_deg=27.887364438572845, longitude_east_deg=-
                  0.27127041325827334, starting_stringdate='1/01/2014', ending_stringdate='1/01/2015')
# dp = DataProvider(location='grenoble', latitude_north_deg=45.19154994547585, longitude_east_deg=5.722065312331381, starting_stringdate='1/01/2014', ending_stringdate='1/01/2015')

site_weather_data = dp.weather_data
print(site_weather_data)

solar_model = SolarModel(site_weather_data)
solar_model.plot_heliodon(2014)
# plt.show()

irradiances_facing_sky = solar_model.irradiance_W(exposure_deg=0, slope_deg=0)
irradiances_south = solar_model.irradiance_W(exposure_deg=0, slope_deg=90)
irradiances_west = solar_model.irradiance_W(exposure_deg=90, slope_deg=90)
irradiances_east = solar_model.irradiance_W(exposure_deg=-90, slope_deg=90)
irradiances_north = solar_model.irradiance_W(exposure_deg=180, slope_deg=90)
irradiances_best = solar_model.irradiance_W(exposure_deg=0, slope_deg=45)
irradiances_oppbest = solar_model.irradiance_W(exposure_deg=180, slope_deg=45)

print('DNI: %gkWh' % (sum(solar_model.dni)/1000))
print('DHI: %gkWh' % (sum(solar_model.dhi)/1000))
print('RHI: %gkWh' % (sum(solar_model.rhi)/1000))
print('GHI: %gkWh' % (sum(solar_model.ghi)/1000))
print('TSI: %gkWh' % (sum(solar_model.tsi)/1000))

print('openmeteo (direct facing sky): %gkWh' %
      (sum(site_weather_data.get('direct_radiation'))/1000))
print('calculus (total facing sky): %gkWh ' %
      (sum(irradiances_facing_sky[RADIATION_TYPE.TOTAL])/1000))
print('calculus (total facing south): %gkWh ' %
      (sum(irradiances_south[CANONICAL_RADIATIONS.TOTAL])/1000))
print('calculus (total facing east): %gkWh ' %
      (sum(irradiances_east[RADIATION_TYPE.TOTAL])/1000))
print('calculus (total facing west): %gkWh ' %
      (sum(irradiances_west[RADIATION_TYPE.TOTAL])/1000))
print('calculus (total facing north): %gkWh ' %
      (sum(irradiances_north[CANONICAL_RADIATIONS.TOTAL])/1000))

dp.add_var('dni', solar_model.dni)
dp.add_var('dhi', solar_model.dhi)
dp.add_var('rhi', solar_model.rhi)
dp.add_var('ghi', solar_model.ghi)
dp.add_var('tsi', solar_model.tsi)

dp.add_var('model direct facing sky',
                         irradiances_facing_sky[RADIATION_TYPE.DIRECT])
dp.add_var('model diffuse facing sky',
                         irradiances_facing_sky[CANONICAL_RADIATIONS.DIFFUSE])
dp.add_var('model reflected facing sky',
                         irradiances_facing_sky[CANONICAL_RADIATIONS.REFLECTED])
dp.add_var('model total facing sky',
                         irradiances_facing_sky[CANONICAL_RADIATIONS.TOTAL])
dp.add_var('model normal facing sky',
                         irradiances_facing_sky[CANONICAL_RADIATIONS.NORMAL])

dp.add_var(
    'model total south', irradiances_south[RADIATION_TYPE.TOTAL])
dp.add_var(
    'model total east', irradiances_east[CANONICAL_RADIATIONS.TOTAL])
dp.add_var(
    'model total west', irradiances_west[CANONICAL_RADIATIONS.TOTAL])
dp.add_var(
    'model total north', irradiances_north[CANONICAL_RADIATIONS.TOTAL])
dp.add_var(
    'model total best', irradiances_best[CANONICAL_RADIATIONS.TOTAL])
dp.add_var('model total oppbest',
                         irradiances_oppbest[CANONICAL_RADIATIONS.TOTAL])

dp.plot()
