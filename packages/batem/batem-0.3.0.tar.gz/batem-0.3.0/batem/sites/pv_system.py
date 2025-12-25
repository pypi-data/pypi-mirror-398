# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from __future__ import annotations

import numpy
import time
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from matplotlib import cm
import core
import batem.core.timemg
import core.solar
import core.weather
# %matplotlib inline


def main():
    peak_power_kW: float = 15
    panel_height_m: float = 1.7  # in m
    PV_inverter_efficiency: float = 0.95
    temperature_coefficient: float = 0.0035
    array_width_m: float = 8  # in m

    open_weather_map_json_reader = core.weather.SWDbuilder(location='Akkar_El_Atiqa', from_requested_stringdate='1/01/2023', to_requested_stringdate='31/12/2023',
                                                                       albedo=0.1, pollution=0.1, self.site_latitude_north_deg=34.54607406260623, longitude_east_deg=36.24159305617472)
    site_weather_data = open_weather_map_json_reader.site_weather_data
    solar_model = core.solar.SolarModel(site_weather_data)

    pv_system: core.solar.PVsystem = core.solar.PVsystem(
        # peak_power_kW=peak_power,
        solar_model,  array_width_m=8, panel_height_m=1.7, pv_efficiency=.24, temperature_coefficient=0.0035, surface_m2=8*1.7)

    datetimes = numpy.array(pv_system.datetimes)
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True)

    exposure_in_deg = 0  # 0° means directed to the South, 90° to the West,...
    slope_in_deg = 35  # in degrees: 0 = face the sky, 90° = face to the south
    distance_between_arrays_in_m = 2

    productions_in_kWh: list[float] = pv_system.solar_gains_kW(
        exposure_in_deg, slope_in_deg, distance_between_arrays_in_m, core.solar.MOUNT_TYPE.FLAT)
    pv_system_productions_in_kWh = numpy.array(productions_in_kWh)
    fig.add_trace(go.Scatter(x=datetimes, y=pv_system_productions_in_kWh,
                  name='flat mount PV production in kWh', line_shape='hv'), row=1, col=1)
    pv_system.print_month_hour_productions(
        exposure_in_deg, slope_in_deg, distance_between_arrays_in_m, core.solar.MOUNT_TYPE.FLAT)
    fig.show()
    quit()

    PV_efficiency: float = peak_power_kW * PV_inverter_efficiency
    pv_system: core.solar.PVsystem = core.solar.PVsystem(solar_model, peak_power_kW=peak_power_kW, array_width_m=array_width_m,
                                                         panel_height_m=panel_height_m, pv_efficiency=PV_efficiency, temperature_coefficient=temperature_coefficient)

    datetimes = numpy.array(pv_system.datetimes)
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True)

    productions_in_kWh: list[float] = pv_system.solar_gains_kW(
        exposure_in_deg, slope_in_deg, distance_between_arrays_in_m, core.solar.MOUNT_TYPE.FLAT)
    pv_system_productions_in_kWh = numpy.array(productions_in_kWh)
    fig.add_trace(go.Scatter(x=datetimes, y=pv_system_productions_in_kWh,
                  name='flat mount PV production in kWh', line_shape='hv'), row=1, col=1)
    pv_system.print_month_hour_productions(
        exposure_in_deg, slope_in_deg, distance_between_arrays_in_m, core.solar.MOUNT_TYPE.FLAT)

    # productions_in_kWh: list[float] = pv_system.productions_in_kWh(exposure_in_deg, slope_in_deg, distance_between_arrays_in_m, buildingenergy.solar.MOUNT_TYPE.SAW)
    pv_system_productions_in_kWh = numpy.array(productions_in_kWh)
    fig.add_trace(go.Scatter(x=datetimes, y=pv_system_productions_in_kWh,
                  name='saw mount PV production in kWh', line_shape='hv'), row=1, col=1)
    pv_system.print_month_hour_productions(
        exposure_in_deg, slope_in_deg, distance_between_arrays_in_m, core.solar.MOUNT_TYPE.SAW)

    productions_in_kWh: list[float] = pv_system.solar_gains_kW(
        exposure_in_deg, slope_in_deg, distance_between_arrays_in_m, core.solar.MOUNT_TYPE.FLAT)
    pv_system_productions_in_kWh = numpy.array(productions_in_kWh)
    fig.add_trace(go.Scatter(x=datetimes, y=pv_system_productions_in_kWh,
                  name='arrow mount PV production in kWh', line_shape='hv'), row=1, col=1)
    pv_system.print_month_hour_productions(
        exposure_in_deg, slope_in_deg, distance_between_arrays_in_m, core.solar.MOUNT_TYPE.FLAT)

    fig.update_layout(title="exposure: %f°, slope: %f°, distance: %f" % (exposure_in_deg, slope_in_deg,
                      distance_between_arrays_in_m), xaxis_title="date & tim (each hour)", yaxis_title="PV electricity production in kWh")
    fig.show()

    print(pv_system)

    mount_type = core.solar.MOUNT_TYPE.FLAT
    distances_between_arrays_in_m: list[float] = [
        i/100 for i in (170, 175, 180)]
    panel_slopes_in_deg: list[float] = [i for i in range(0, 90, 5)]
    exposure_in_deg = 0

    t0 = time.time()
    productions_in_kWh, productions_in_kWh_per_pv_surf = core.solar.pv_productions_distances_slopes(
        pv_system, exposure_in_deg, panel_slopes_in_deg, distances_between_arrays_in_m, mount_type)
    print('pv_productions_distances_slopes:', (time.time() - t0)/60, 'min')

    X, Y = numpy.meshgrid(panel_slopes_in_deg, distances_between_arrays_in_m)
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    ax.plot_surface(X, Y, productions_in_kWh, cmap=cm.coolwarm,
                    linewidth=0, antialiased=False)
    ax.set_xlabel('panel slope (deg)')
    ax.set_ylabel('distance between panels (m)')
    ax.set_zlabel('production (kWh)')
    ax.set_title('exposure: %f°, mount type: %s' %
                 (exposure_in_deg, mount_type))

    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    ax.plot_surface(X, Y, productions_in_kWh_per_pv_surf,
                    cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_xlabel('panel slope (deg)')
    ax.set_ylabel('distance between panels (m)')
    ax.set_zlabel('production per m2 of PV (kWh/m2)')
    ax.set_title('exposure: %f°, mount type: %s' %
                 (exposure_in_deg, mount_type))

    exposures_in_deg: list[float] = list(range(-90, 90, 5))
    slopes_in_deg: list[float] = list(range(0, 90, 5))
    distance_between_arrays_in_m: float = 1.2
    mount_type: core.solar.MOUNT_TYPE = core.solar.MOUNT_TYPE.FLAT

    t0 = time.time()
    pv_productions_kWh, productions_kWh_per_pv_surf = core.solar.pv_productions_angles(
        pv_system, exposures_in_deg, slopes_in_deg, distance_between_arrays_in_m, mount_type)
    print('pv_productions_distances_slopes:', (time.time() - t0)/60, 'min')

    X, Y = numpy.meshgrid(exposures_in_deg, slopes_in_deg)
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    ax.plot_surface(X, Y, numpy.array(pv_productions_kWh),
                    cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_xlabel('exposure (deg)')
    ax.set_ylabel('slope (deg)')
    ax.set_zlabel('production (kWh)')
    ax.set_title('distance: %fm, mount type: %s' %
                 (distance_between_arrays_in_m, mount_type))


if __name__ == '__main__':
    main()
    plt.show()
    # python3.11 -m cProfile -o nathan.prof nathan_pv_system.py
    # snakeviz nathan.prof
    #
    # pip3.11 install line_profiler
    # python3.11 -m kernprof -l -v nathan.py
