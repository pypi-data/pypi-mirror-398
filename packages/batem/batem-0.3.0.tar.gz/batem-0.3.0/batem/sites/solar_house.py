"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
import matplotlib.pyplot as plt
from scipy.constants import Stefan_Boltzmann
import numpy
from core.thermal import CAUSALITY, ThermalNetwork
from core.library import Properties, SLOPES
from core.data import DataProvider
from core.solar import SolarModel, SolarSystem, Collector, RADIATION_TYPE
from core.components import Composition

properties = Properties()
properties.load('marble', 'thermal', 206)
wind_speed = 2.4
covered_surface: float = 10 * 10
window_surface = 1 * 2
wall_surface = 10 * 2.5 - window_surface
glass_solar_factor = .8
location: str = 'Grenoble'
starting_stringdate, ending_stringdate = "1/1/2023", "31/12/2023"
latitude_north_deg, longitude_east_deg = 45.19154994547585, 5.722065312331381
wind_speed_is_m_per_sec = 2.4
T_year_average = 13
slab_material = 'concrete'
slab_thickness: float = 30e-2
n_layers = 1


def simulate(dp: DataProvider, reflectance: float, suffix: str):
    wall_absorption_out = reflectance - 1
    print('wall_absorption_out:', wall_absorption_out)
    
    T_average: float = sum(dp.series('weather_temperature'))/len(dp)
    dp.add_param('T_underground', T_average)

    solar_model = SolarModel(dp.weather_data)
    windows_solar_system = SolarSystem(solar_model)
    Collector(windows_solar_system, 'window_south', exposure_deg=0, slope_deg=90, surface_m2=window_surface, solar_factor=glass_solar_factor)
    Collector(windows_solar_system, 'window_east', exposure_deg=90, slope_deg=90, surface_m2=window_surface, solar_factor=glass_solar_factor)
    Collector(windows_solar_system, 'window_west', exposure_deg=-90, slope_deg=90, surface_m2=window_surface, solar_factor=glass_solar_factor)
    Collector(windows_solar_system, 'window_north', exposure_deg=180, slope_deg=90, surface_m2=window_surface, solar_factor=glass_solar_factor)
    windows_gains: dict[str, dict[RADIATION_TYPE, list[float]]] | dict[RADIATION_TYPE, list[float]] = windows_solar_system.solar_gains_W(RADIATION_TYPE.TOTAL, gather_collectors=True)
    dp.add_var('P_windows', windows_gains)

    walls_solar_system = SolarSystem(solar_model)
    Collector(walls_solar_system, 'roof', exposure_deg=0, slope_deg=0, surface_m2=covered_surface, solar_factor=wall_absorption_out)
    Collector(walls_solar_system, 'wall_south', exposure_deg=0, slope_deg=90, surface_m2=wall_surface, solar_factor=wall_absorption_out)
    Collector(walls_solar_system, 'wall_east', exposure_deg=-90, slope_deg=90, surface_m2=wall_surface, solar_factor=wall_absorption_out)
    Collector(walls_solar_system, 'wall_west', exposure_deg=90, slope_deg=90, surface_m2=wall_surface, solar_factor=wall_absorption_out)
    Collector(walls_solar_system, 'wall_north', exposure_deg=180, slope_deg=90, surface_m2=wall_surface, solar_factor=wall_absorption_out)
    walls_gains: dict[str, dict[RADIATION_TYPE, list[float]]] | dict[RADIATION_TYPE, list[float]] = walls_solar_system.solar_gains_W(RADIATION_TYPE.TOTAL)

    dp.add_var('P_wall_south', walls_gains['wall_south'])
    dp.add_var('P_wall_east', walls_gains['wall_east'])
    dp.add_var('P_wall_west', walls_gains['wall_west'])
    dp.add_var('P_wall_north', walls_gains['wall_north'])
    dp.add_var('P_roof', walls_gains['roof'])

    tnet = ThermalNetwork()
    tnet.T('weather_temperature', CAUSALITY.IN)
    tnet.T('T_in', CAUSALITY.OUT)
    tnet.HEAT('T_in', 'P_windows')
    tnet.T('T_wall_south_out')
    tnet.HEAT('T_wall_south_out', 'P_wall_south')
    tnet.T('T_wall_east_out')
    tnet.HEAT('T_wall_east_out', 'P_wall_east')
    tnet.T('T_wall_west_out')
    tnet.HEAT('T_wall_west_out', 'P_wall_west')
    tnet.T('T_wall_north_out')
    tnet.HEAT('T_wall_north_out', 'P_wall_north')
    tnet.T('T_roof_out', CAUSALITY.OUT)
    tnet.HEAT('T_roof_out', 'P_roof')
    tnet.T('T_ground')
    tnet.T('T_underground', CAUSALITY.IN)
    
    insulation_thickness = 5e-2

    R_slab: float = properties.conduction_resistance(slab_material, slab_thickness, surface=covered_surface)
    C_slab: float = properties.capacitance(slab_material, slab_thickness, surface=covered_surface)
    tnet.RCs(fromT='T_ground', toT='T_underground', n_layers=n_layers, Rtotal=R_slab, Ctotal=C_slab)
    tnet.R('T_in', 'T_ground', val=properties.indoor_surface_resistance(slab_material, SLOPES.HORIZONTAL_UP, surface=covered_surface))

    compo_windows = Composition(first_layer_indoor=True, last_layer_indoor=False, position='vertical')
    compo_windows.layer('glass', 4e-3)
    compo_windows.layer('air', 12e-3)
    compo_windows.layer('glass', 4e-3)
    tnet.R('weather_temperature', 'T_in', val=compo_windows.R / (window_surface * 4))

    compo_walls = Composition(first_layer_indoor=True, last_layer_indoor=None, position='vertical')
    compo_walls.layer('plaster', 13e-3)
    compo_walls.layer('glass_foam', insulation_thickness)
    compo_walls.layer('concrete', 10e-2)

    tnet.R('T_in', 'T_wall_south_out', compo_walls.R / wall_surface)
    tnet.R('T_wall_south_out', 'weather_temperature', val=properties.outdoor_surface_resistance('concrete', SLOPES.VERTICAL, average_temperature_celsius=T_average, wind_speed_is_m_per_sec=wind_speed_is_m_per_sec, surface=wall_surface))

    tnet.R('T_in', 'T_wall_east_out', val=compo_walls.R / wall_surface)
    tnet.R('T_wall_east_out', 'weather_temperature', val=properties.outdoor_surface_resistance('concrete', SLOPES.VERTICAL, average_temperature_celsius=T_average, wind_speed_is_m_per_sec=wind_speed_is_m_per_sec, surface=wall_surface))

    tnet.R('T_in', 'T_wall_west_out', val=compo_walls.R / wall_surface)
    tnet.R('T_wall_west_out', 'weather_temperature', val=properties.outdoor_surface_resistance('concrete', SLOPES.VERTICAL, average_temperature_celsius=T_average, wind_speed_is_m_per_sec=wind_speed_is_m_per_sec, surface=wall_surface))

    tnet.R('T_in', 'T_wall_north_out', val=compo_walls.R / wall_surface)
    tnet.R('T_wall_north_out', 'weather_temperature', val=properties.outdoor_surface_resistance('concrete', SLOPES.VERTICAL, average_temperature_celsius=T_average, wind_speed_is_m_per_sec=wind_speed_is_m_per_sec, surface=wall_surface))

    compo_roof = Composition(first_layer_indoor=True, last_layer_indoor=None, position='horizontal')
    compo_roof.layer('plaster', 13e-3)
    compo_roof.layer('glass foam', insulation_thickness)
    compo_roof.layer('concrete', 10e-2)
    tnet.R('T_roof_out', 'T_in', val=compo_walls.R / covered_surface)
    tnet.R('weather_temperature', 'T_roof_out', val=properties.outdoor_surface_resistance('concrete', SLOPES.HORIZONTAL_UP, average_temperature_celsius=T_average, wind_speed_is_m_per_sec=wind_speed_is_m_per_sec, surface=covered_surface))
    # tnet.draw()
    # plt.show()

    state_model = tnet.state_model()
    print(state_model)
    state_model.simulate(dp, suffix=suffix)
    if suffix is None:
        return dp.series('T_in')
    else:
        return dp.series('T_in_' + suffix)


dp1 = DataProvider(location, latitude_north_deg, longitude_east_deg, starting_stringdate=starting_stringdate, ending_stringdate=ending_stringdate, albedo=.1, pollution=0.1)
suffix = 'black'
simulate(dp1, reflectance=0.04, suffix=suffix)

dp2 = dp1.excerpt()
suffix = 'white'
T_in_2 = simulate(dp2, reflectance=0.8, suffix=suffix)
dp1.add_var('T_in_'+suffix, T_in_2)
dp1.plot()
