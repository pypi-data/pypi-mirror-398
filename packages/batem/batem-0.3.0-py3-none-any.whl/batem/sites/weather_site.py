"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
import batem.core.weather
import batem.core.solar
import batem.core.timemg
import matplotlib.pylab as plt
from batem.core.data import DataProvider
# from pandas.plotting import register_matplotlib_converters
from datetime import datetime
from matplotlib.patches import Ellipse


def plot_rain_events(datetimes: list[datetime], precipitations: list[float], *axs):
    if len(axs) < 2:
        fig1, ax1 = plt.subplots()
        fig2, ax2 = plt.subplots()
    else:
        ax1, ax2 = axs
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

    month_accumulator, month_cumulated_precipitations = list(), list()
    current_month = datetimes[0].month
    week_accumulator, week_cumulated_precipitations = list(), list()
    current_week = datetimes[0].isocalendar().week

    for k, precipitation in enumerate(precipitations):
        month: int = datetimes[k].month
        if current_month != month or k == len(precipitations)-1:
            month_quantity = sum(month_accumulator)
            month_cumulated_precipitations.extend(
                [month_quantity for _ in range(len(month_accumulator))])
            month_accumulator: list[float] = [precipitation]
            current_month = month
        else:
            month_accumulator.append(precipitation)

        week: int = datetimes[k].isocalendar().week
        if current_week != week or k == len(precipitations)-1:
            week_quantity = sum(week_accumulator)
            week_cumulated_precipitations.extend(
                [week_quantity for _ in range(len(week_accumulator))])
            week_accumulator: list[float] = [precipitation]
            current_week = week
        else:
            week_accumulator.append(precipitation)

        stringdate: str = batem.core.timemg.datetime_to_stringdate(
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

    ax1.set(xlim=(0, max_duration), ylim=(0, max_quantity))
    for characteristics in rains_dict:
        ellipse = Ellipse(characteristics, width=rains_dict[characteristics],
                          height=rains_dict[characteristics], edgecolor='black', facecolor='orange')
        ax1.add_artist(ellipse)
        ellipse.set_alpha(0.5)
        plt.annotate(
            ','.join(rains_months_dict[characteristics]), characteristics)
    ax1.set_title('rain events (numbers stands for month# (%i raining days out of %i)' % (
        len(days_with_rain), len(days)))
    ax1.set_xlabel('duration in hours')
    ax1.set_ylabel('quantity in mm/h')

    ax2.stairs(month_cumulated_precipitations,
               datetimes, fill=True, color='cyan')
    ax2.stairs(week_cumulated_precipitations,
               datetimes, fill=True, color='pink')
    ax2.set_xlabel('times')
    ax2.set_ylabel('quantity in mm')


if __name__ == '__main__':
    # location = 'Cayenne'
    # year = 2023
    # latitude, longitude = 4.924435336591809, -52.31276008988111

    # location = 'Assouan'
    # year = 2023
    # latitude, longitude = 24.02769921861417, 32.87455490478971

    # location = 'Séville'
    # year = 2023
    # latitude, longitude = 37.39459541966303, -5.976329994207859

    # location = 'Grenoble_Grenette'
    # year = 2023
    # latitude, longitude = 45.190823325765166, 5.727264569512632

    # location = 'Dernau'
    # year = 2021
    # latitude, longitude = 50.533597125769006, 7.043932243115649

    # location = 'Montpellier_Comedie'
    # year = 2023
    # latitude, longitude = 43.60868701389951, 3.879524999715972

    # location = 'Paris_Vendome'
    # year = 2023
    # latitude, longitude = 43.60868701389951, 3.879524999715972

    # location: str = 'Grenoble'
    # year = 2022
    # latitude, longitude = 45.19154994547585, 5.722065312331381
    
    # location: str = 'Lyon'
    # year = 2022
    # latitude, longitude = 45.76223391279203, 4.836900125558293

    location: str = 'Rennes'
    year = 2024
    latitude, longitude = 48.114993728285654, -1.676572334072725

    # location: str = 'Carqueiranne'
    # year = 2023
    # latitude, longitude = 43.08933178200723, 6.072235955304281

    # location = 'Aigle'
    # year = 2023
    # latitude, longitude = 45.011352235478476, 6.324482739625443

    # location = 'Valmorel'
    # year = 2023
    # latitude, longitude = 45.46169400539397, 6.441806169545177

    # location = 'Tirana'
    # year = 2023
    # latitude, longitude = 41.32125784049168, 19.858985090315503

    # collector exposure: - 90 east, 90 west, 0 south, 180 north (clockwise with South as reference)
    exposure = 0
    slope = 0  # collector slope: 0 facing the sky, 90 facing the exposure
    surface = 1  # collector surface in m2
    solar_factor = 1

    from_stringdate = '1/01/%i' % year
    to_stringdate = '31/12/%i' % year
    dp = DataProvider(location=location, latitude_north_deg=latitude, longitude_east_deg=longitude,
                      starting_stringdate=from_stringdate, ending_stringdate=to_stringdate)

    solar_model = batem.core.solar.SolarModel(dp.weather_data)
    solar_system = batem.core.solar.SolarSystem(solar_model)
    batem.core.solar.Collector(solar_system, 'surface', surface_m2=surface,
                               exposure_deg=exposure, slope_deg=slope, solar_factor=solar_factor)
    solar_gains_in_Wh = solar_system.powers_W(gather_collectors=True)

    dp.add_var('horizontal irradiance Wh', solar_gains_in_Wh)
    print(dp.weather_data)
    print('production horizontal en kWh', sum(solar_gains_in_Wh)/1000)

    dp.save()

    dp.plot()
    plt.show()

    # fig, ax = plt.subplots()
    # plt.plot(site_weather_data.get('datetime'), site_weather_data.get('direct_radiation'), label='horizontal')  # total
    # plt.plot(site_weather_data.get('datetime'), site_weather_data.get('diffuse_radiation'), label='diffuse_radiation')  # diffuse
    # plt.plot(site_weather_data.get('datetime'), site_weather_data.get('direct_normal_irradiance'), label='perpendicular to the sun beams')  # direct
    # exposure = 0  # - 90 east, 90 west, 0 south, 180 north (clockwise with South as reference)
    # slope = 0  # 0 facing the sky, 90 facing the exposure
    # irradiances = solar_model.irradiances(exposure_deg=exposure, slope_deg=slope)  # mask=buildingenergy.solar.RectangularMask(minmax_azimuths_deg=(-90+exposure, 90+exposure), minmax_altitudes_deg=(-90+slope, 90+slope))

    # print('openmeteo: %f' % (sum(site_weather_data.get('direct_radiation'))/1000))
    # print('calculus: %f' % (sum(irradiances['total'])/1000))

    # plt.plot(site_weather_data.get('datetime'), irradiances['direct'], label='model_direct')  # direct
    # plt.plot(site_weather_data.get('datetime'), irradiances['diffuse'], label='model_diffuse')  # diffuse
    # plt.plot(site_weather_data.get('datetime'), irradiances['reflected'], label='model_reflected')
    # plt.plot(site_weather_data.get('datetime'), irradiances['total'], label='model_total')  # total
    # plt.plot(site_weather_data.get('datetime'), irradiances['normal'], label='model_normal')

    # ax.set_title('irradiances')
    # plt.legend()
    # ax.axis('tight')
    # fig, ax = plt.subplots()
    # plt.plot(site_weather_data.get('datetime'), solar_model.sun_altitudes_deg, label='altitude')
    # plt.plot(site_weather_data.get('datetime'), solar_model.sun_azimuths_deg, label='azimuth')
    # ax.set_title('angles')
    # plt.legend()
    # ax.axis('tight')

    # ax.set_title('snow depth')
    # plt.legend()
    # ax.axis('tight')
    # fig, ax = plt.subplots()
    # plt.plot(site_weather_data.get('datetime'), site_weather_data.get('snow_depth'), label='snow depth')
    # ax.set_title('time')
    # plt.legend()
    # ax.axis('tight')

    # datetimes: list[float] = site_weather_data.get('datetime')
    # precipitations: list[float] = site_weather_data.get('precipitation')
    # plot_rain_events(datetimes, precipitations)
    # plt.show()
