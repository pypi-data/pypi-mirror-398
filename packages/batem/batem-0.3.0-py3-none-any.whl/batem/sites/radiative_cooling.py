"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
import numpy
import matplotlib.pyplot as plt
from core.thermal import CAUSALITY, ThermalNetwork
from core.library import Properties, SLOPES
from core.data import DataProvider
from core.solar import SolarModel, SolarSystem, PVsystem, MOUNT_TYPE, Collector


# system parameters
properties = Properties()
properties.load('marble', 'thermal', 206)
wind_speed = 2.4
surface_m2: float = 1.7
cloud_emissivity = .96
ground_emissivity = .92
PV_emissivity: float = .5
PV_thickness: float = 5e-2
PV_efficiency: float = .2
location: str = 'Grenoble'
starting_stringdate, ending_stringdate = "1/7/2023", "1/10/2023"
latitude_north_deg, longitude_east_deg = 45.19154994547585, 5.722065312331381
wind_speed_is_m_per_sec = 2.4
T_year_average = 13
slab_material = 'marble'
slab_thickness: float = 50e-2
n_layers = 10

# create data for simulation
dp = DataProvider(location, latitude_north_deg, longitude_east_deg, starting_stringdate=starting_stringdate, ending_stringdate=ending_stringdate, albedo=.1, pollution=0.1)
T_average_celsius: float = sum(dp.series('weather_temperature'))/len(dp)
dp.add_param('T_underground', T_year_average)

solar_model = SolarModel(dp.weather_data)
sun_altitudes_deg: list[float] = solar_model.altitudes_deg
sun_azimuths_deg: list[float] = solar_model.azimuths_deg
solar_system = SolarSystem(solar_model)

dp.add_var('sun_azimuths_deg', sun_azimuths_deg)
dp.add_var('sun_altitudes_deg', sun_altitudes_deg)

# generate radiative power exchange with sky for PV cover and for ground
P_sky_pv_linear: list[float] = [Properties.P_sky_surface_linear(weather_temperature_celsius=dp('weather_temperature', k), cloudiness_percent=dp('weather_cloudiness', k), altitude_deg=sun_altitudes_deg[k], dewpoint_temperature_celsius=dp('weather_dew_point_2m', k), emissivity=PV_emissivity, average_temperature_celsius=T_average_celsius, surface=surface_m2) for k in range(len(dp))]
dp.add_var('P_sky_pv_linear', P_sky_pv_linear)

P_sky_ground_linear: list[float] = [Properties.P_sky_surface_linear(weather_temperature_celsius=dp('weather_temperature', k), cloudiness_percent=dp('weather_cloudiness', k), altitude_deg=sun_altitudes_deg[k], dewpoint_temperature_celsius=dp('weather_dew_point_2m', k), emissivity=ground_emissivity, average_temperature_celsius=T_average_celsius, surface=surface_m2) for k in range(len(dp))]
dp.add_var('P_sky_ground_linear', P_sky_ground_linear)

# generate data for simulation
Collector(solar_system, 'PVheat', exposure_deg=-30, slope_deg=0, solar_factor=1-PV_efficiency-PV_emissivity, surface_m2=surface_m2)

pv_system = PVsystem(solar_model, array_width_m=20, panel_height_m=1.7, pv_efficiency=PV_efficiency, number_of_cell_rows=10, temperature_coefficient=0.0035, surface_m2=surface_m2)
pv_production: list[float] = pv_system.electric_power_W(-30, 0, distance_between_arrays_m=1.8, mount_type=MOUNT_TYPE.FLAT)
print('Total PV production: %0.fkWh' % sum(pv_production))
dp.add_var('P_sun', solar_system.solar_gains_W(gather_collectors=True))
dp.add_var('pv_production_Wh', pv_production)

P_sun_pv_sky_linear = [dp('P_sun', k) + P_sky_pv_linear[k] for k in range(len(dp))]
dp.add_var('P_sun_pv_sky_linear', P_sun_pv_sky_linear)
R_sky_pv: float = 1/(properties.U_surface_radiation(PV_emissivity, T_average_celsius, surface_m2=surface_m2) + properties.U_outdoor_surface_convection(wind_speed_is_m_per_sec=wind_speed_is_m_per_sec, surface=surface_m2))
U_pv = Properties.U_surface_radiation(PV_emissivity, T_average_celsius, surface_m2=surface_m2)
U_ground = Properties.U_surface_radiation(ground_emissivity, T_average_celsius, surface_m2=surface_m2)
print('U_pv:', U_pv)
print('U_ground:', U_ground)

# make equivalent electrical circuit for COVERED
net_covered = ThermalNetwork()
net_covered.T('weather_temperature', CAUSALITY.IN)
net_covered.T('T_pv_up', CAUSALITY.OUT)
net_covered.HEAT('T_pv_up', 'P_sun_pv_sky_linear')
net_covered.T('T_pv_down', CAUSALITY.OUT)
net_covered.T('T_ground', CAUSALITY.OUT)
net_covered.T('T_underground', CAUSALITY.IN)
net_covered.R('weather_temperature', 'T_pv_up', val=R_sky_pv)
net_covered.R('T_pv_up', 'T_pv_down', val=properties.conduction_resistance('glass', PV_thickness, surface=surface_m2))
net_covered.R('T_pv_down', 'weather_temperature', val=properties.outdoor_surface_resistance('glass', SLOPES.HORIZONTAL_UP, average_temperature_celsius=T_average_celsius, wind_speed_is_m_per_sec=wind_speed_is_m_per_sec, surface=surface_m2))
net_covered.R('weather_temperature', 'T_ground', val=properties.outdoor_surface_resistance(slab_material, SLOPES.HORIZONTAL_UP, average_temperature_celsius=T_average_celsius, wind_speed_is_m_per_sec=wind_speed_is_m_per_sec, surface=surface_m2))
R_slab: float = properties.conduction_resistance(slab_material, slab_thickness, surface=surface_m2)
C_slab: float = properties.capacitance(slab_material, slab_thickness, surface=surface_m2)
net_covered.RCs(fromT='T_ground', toT='T_underground', n_layers=n_layers, Rtotal=R_slab, Ctotal=C_slab)
# net_covered.draw()
# plt.show()

# simulate system with PV coverage: COVERED
state_model_COVERED = net_covered.state_model()
print(state_model_COVERED)
state_model_COVERED.simulate(dp, suffix='COVERED')


dp.add_var('T_operative_COVERED', [((dp('T_ground_COVERED', i) + dp('T_pv_down_COVERED', i))/2 + dp('weather_temperature', i))/2 for i in range(len(dp))])
dp.add_var('P_sun_pv_sky_exact_COVERED', [Properties.P_sky_surface_exact(weather_temperature_celsius=dp('weather_temperature', k), cloudiness_percent=dp('weather_cloudiness', k), altitude_deg=dp('sun_altitudes_deg', k), dewpoint_temperature_celsius=dp('weather_dew_point_2m', k), emissivity=PV_emissivity, surface_temperature_celsius=dp('T_pv_up_COVERED', k), surface=surface_m2) for k in range(len(dp))])
dp.add_var('P', [1/R_sky_pv*(dp('T_pv_up_COVERED', k)-dp('weather_temperature', k)) for k in range(len(dp))])

# make equivalent electrical circuit for UNCOVERED
R_sky_ground: float = 1/(Properties.U_surface_radiation(emissivity=ground_emissivity, average_temperature_celsius=T_average_celsius, surface_m2=surface_m2) + Properties.U_outdoor_surface_convection(wind_speed_is_m_per_sec=wind_speed_is_m_per_sec, surface=surface_m2))

dp.add_var('P_sun_sky_ground_linear', [dp('P_sky_ground_linear', k) + dp('P_sun', k) for k in range(len(dp))])

net_uncovered = ThermalNetwork()
net_uncovered.T('weather_temperature', CAUSALITY.IN)
net_uncovered.T('T_ground', CAUSALITY.OUT)
net_uncovered.HEAT('T_ground', 'P_sun_sky_ground_linear')
net_uncovered.T('T_underground', CAUSALITY.IN)
net_uncovered.R('T_ground', 'weather_temperature', val=R_sky_ground)
net_uncovered.RCs(fromT='T_ground', toT='T_underground', n_layers=n_layers, Rtotal=R_slab, Ctotal=C_slab)

# simulate system without PV coverage: UNCOVERED
state_model_uncovered = net_uncovered.state_model()
print(state_model_uncovered)
state_model_uncovered.simulate(dp, suffix='UNCOVERED')

dp.add_var('T_operative_UNCOVERED', [(dp('T_ground_UNCOVERED', k) + dp('weather_temperature', k))/2 for k in range(len(dp))])
dp.add_var('P_sun_pv_sky_exact_UNCOVERED', [Properties.P_sky_surface_exact(weather_temperature_celsius=dp('weather_temperature', k), cloudiness_percent=dp('weather_cloudiness', k), altitude_deg=dp('sun_altitudes_deg', k), dewpoint_temperature_celsius=dp('weather_dew_point_2m', k), emissivity=ground_emissivity, surface_temperature_celsius=dp('T_ground_UNCOVERED', k), surface=surface_m2) for k in range(len(dp))])
dp.add_var('P_sun_sky_ground_linear', dp.series('P_sky_ground_linear'))

# simulate hybrid system with day/night removable PV coverage: HYBRID
simulated_outputs: dict[str, list[float]] = {variable_name: list() for variable_name in state_model_COVERED.output_names}
X = None
day_output_names: list[str] = state_model_COVERED.output_names
night_output_names: list[str] = state_model_uncovered.output_names
for k in range(len(dp)):
    current_day_input_values: dict[str, float] = {input_name: dp(input_name, k) for input_name in state_model_COVERED.input_names}
    current_night_input_values: dict[str, float] = {input_name: dp(input_name, k) for input_name in state_model_uncovered.input_names}
    if X is None:
        if dp('sun_altitudes_deg', k) > 0:
            X: numpy.matrix = state_model_COVERED.initialize(**current_day_input_values)
        else:
            X: numpy.matrix = state_model_uncovered.initialize(**current_day_input_values)
    state_model_COVERED.set_state(X)
    state_model_uncovered.set_state(X)

    for i, val in enumerate(state_model_COVERED.output(**current_day_input_values)):
        if dp('sun_altitudes_deg', k) > 0:
            simulated_outputs[day_output_names[i]].append(val)
        else:
            if day_output_names[i] in night_output_names:
                simulated_outputs[day_output_names[day_output_names.index(day_output_names[i])]].append(val)
            else:
                simulated_outputs[day_output_names[i]].append(val)
    if dp('sun_altitudes_deg', k) > 0:
        X = state_model_COVERED.step(**current_day_input_values)
    else:
        X = state_model_uncovered.step(**current_day_input_values)
for output_name in day_output_names:
    dp.add_var(output_name+'_HYBRID', simulated_outputs[output_name])

dp.add_var('T_operative_HYBRID', [(dp('T_ground_HYBRID', i) + dp('weather_temperature', i))/2 if dp('sun_altitudes_deg', i) <= 0 else (((dp('T_ground_HYBRID', i) + dp('T_pv_down_HYBRID', i))/2) + dp('weather_temperature',i))/2 for i in range(len(dp))])

dp.add_var('P_sun_pv_sky_exact_HYBRID', [Properties.P_sky_surface_exact(weather_temperature_celsius=dp('weather_temperature', k), cloudiness_percent=dp('weather_cloudiness', k), altitude_deg=dp('sun_altitudes_deg', k), dewpoint_temperature_celsius=dp('weather_dew_point_2m', k), emissivity=ground_emissivity, surface_temperature_celsius=dp('T_ground_HYBRID', k), surface=surface_m2) for k in range(len(dp))])

dp.plot()
