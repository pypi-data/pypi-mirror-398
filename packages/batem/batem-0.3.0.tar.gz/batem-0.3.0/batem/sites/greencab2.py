# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from typing import Any
from batem.core.data import DataProvider, Bindings
from batem.core.control import HeatingPeriod, CoolingPeriod, OccupancyProfile, SignalGenerator, TemperatureController, Simulation, WEEKDAYS, TemperatureSetpointPort, HVACcontinuousModePort
from batem.core.solar import SolarModel, SolarSystem, Collector
from batem.core.model import ModelMaker
from batem.core.components import Side
from batem.core.inhabitants import Preference
from batem.core.library import SIDE_TYPES, DIRECTIONS_SREF, SLOPES
from batem.core.statemodel import StateModel


# #### DESIGN PARAMETERS ####

# human actors
body_metabolism = 100
occupant_consumption = 200
body_PCO2 = 7

# Window
surface_window: float = 2.2 * 0.9
exposure_window = DIRECTIONS_SREF.NORTH.value
slope_window = SLOPES.VERTICAL.value
solar_protection = 90  # Notice that 90°C ->no protection
solar_factor: float = 0.56

# Physics
insulation_thickness = 150e-3
container_height = 2.29
container_width = 2.44
container_length = 6
toilet_length = 1.18
container_floor_surface: float = container_length * container_width
cabinet_volume: float = container_floor_surface * container_height
toilet_surface: float = toilet_length * container_width
toilet_volume: float = toilet_surface * container_height
cabinet_surface_wall: float = (2 * container_length + container_width) * container_height - surface_window

# ventilation
q_infiltration: float = cabinet_volume/3600
q_ventilation: float = 1 * cabinet_volume/3600
q_freecooling: float = 2 * cabinet_volume/3600


# #### DATA PROVIDER AND SIGNALS ####
starting_stringdate = "1/1/2023"
ending_stringdate = "31/12/2023"
location = 'Saint-Julien-en-Saint-Alban'
latitude_north_deg: float = 44.71407488275519
longitude_east_deg: float = 4.633318302898348

bindings: Bindings = Bindings()
bindings('TZ:outdoor', 'weather_temperature')

dp: DataProvider = DataProvider(location=location, latitude_north_deg=latitude_north_deg, longitude_east_deg=longitude_east_deg, starting_stringdate=starting_stringdate, ending_stringdate=ending_stringdate, bindings=bindings, albedo=0.1, pollution=0.1, number_of_levels=4)

solar_model: SolarModel = SolarModel(dp.weather_data)
dp.solar_model = solar_model
solar_system: SolarSystem = SolarSystem(solar_model)
Collector(solar_system, 'main', surface_m2=surface_window, exposure_deg=exposure_window, slope_deg=slope_window, solar_factor=solar_factor)
solar_gains_with_mask: list[float] = solar_system.powers_W(gather_collectors=True)
dp.add_var('Psun_window:cabinet', solar_gains_with_mask)

siggen: SignalGenerator = SignalGenerator(dp, OccupancyProfile(weekday_profile={0: 0, 7: 1, 8: 3, 18: 0}, weekend_profile={0: 0},))
siggen.add_hvac_period(HeatingPeriod('16/11', '16/3', weekday_profile={0: None, 7: 19, 20: None}, weekend_profile={0: None, }))
siggen.add_hvac_period(CoolingPeriod('16/3', '16/11', weekday_profile={0: None, 7: 24, 20: None}, weekend_profile={0: None, }))
siggen.generate('cabinet')

occupancy: list[float | None] = dp.series('OCCUPANCY:cabinet')
dp.add_var('PCO2:cabinet', (siggen.filter(occupancy, lambda x: x * body_PCO2 if x is not None else 0)))
presence: list[int] = [int(occupancy[k] > 0) for k in range(len(dp))]

dp.add_var('GAIN:cabinet', [occupancy[k] * (body_metabolism + occupant_consumption) + solar_gains_with_mask[k] for k in dp.ks])
dp.add_param('GAIN:toilet', 0)
dp.add_param('PCO2:toilet', 0)

dp.add_param('CCO2:outdoor', 400)

ventilation: list[float] = siggen.build_daily([WEEKDAYS.MONDAY, WEEKDAYS.TUESDAY, WEEKDAYS.WEDNESDAY, WEEKDAYS.THURSDAY, WEEKDAYS.FRIDAY], {0: 0, 7: 1, 18: 0})
dp.add_var('ventilation', ventilation)
dp.add_var('Q:cabinet-outdoor', [q_infiltration + presence[k]*q_ventilation if occupancy[k] is not None else q_infiltration for k in range(len(dp))])
dp.add_var('Q:toilet-outdoor', [q_infiltration + ventilation[k]*q_ventilation if ventilation[k] is not None else q_infiltration for k in range(len(dp))])
# Add airflow from cabinet to toilet (e.g., through door cracks or when door is opened)
q_cabinet_toilet: float = cabinet_volume / 3600  # Airflow equal to infiltration rate
dp.add_var('Q:cabinet-toilet', [q_cabinet_toilet * presence[k] if presence[k] > 0 else 0.0 for k in range(len(dp))])


# #### STATE MODEL MAKER AND TEMPERATURE CONTROLLERS ####
model_maker = ModelMaker(data_provider=dp, periodic_depth_seconds=3600, state_model_order_max=None, cabinet=cabinet_volume, toilet=toilet_volume, outdoor=None)

wall = Side(('wood', 3e-3), ('polystyrene', insulation_thickness), ('steel', 5e-3), ('wood', 3e-3))
floor = Side(('wood', 10e-3), ('polystyrene', insulation_thickness), ('steel', 5e-3))
ceiling = Side(('wood', 3e-3), ('polystyrene', insulation_thickness), ('steel', 5e-3))
glazing = Side(('glass', 4e-3), ('air', 10e-3), ('glass', 4e-3), ('air', 10e-3), ('glass', 4e-3))
internal = Side(('wood', 9e-3), ('air', 20e-3), ('wood', 9e-3))

# Cabinet
model_maker.make_side(wall('cabinet', 'outdoor', SIDE_TYPES.WALL, cabinet_surface_wall))
model_maker.make_side(floor('cabinet', 'outdoor', SIDE_TYPES.FLOOR, container_floor_surface))
model_maker.make_side(ceiling('cabinet', 'outdoor', SIDE_TYPES.CEILING, container_floor_surface))
model_maker.make_side(glazing('cabinet', 'outdoor', SIDE_TYPES.GLAZING, surface_window))

# Toilet
model_maker.make_side(internal('cabinet', 'toilet', SIDE_TYPES.WALL, container_width * container_height))
model_maker.make_side(wall('toilet', 'outdoor', SIDE_TYPES.WALL, (toilet_length * 2 + container_width) * container_height))
model_maker.make_side(floor('toilet', 'outdoor', SIDE_TYPES.FLOOR, container_width * toilet_length))
model_maker.make_side(ceiling('toilet', 'outdoor', SIDE_TYPES.CEILING, container_width * toilet_length))

model_maker.zones_to_simulate({'cabinet': cabinet_volume, 'toilet': toilet_volume})
model_maker.connect_airflow('cabinet', 'outdoor')  # nominal value
model_maker.connect_airflow('toilet', 'outdoor')  # nominal value
model_maker.connect_airflow('cabinet', 'toilet', nominal_value=q_cabinet_toilet)  # Airflow from cabinet to toilet (variable Q:cabinet-toilet)

# Update the fingerprint with the airflows (ensures model rebuilds when airflows change)
# model_maker.dp.add_data_names_in_fingerprint(*[airflow.name for airflow in model_maker.airflows])
# model_maker.state_models_cache.clear()  # Clear any cached models
nominal_state_model: StateModel = model_maker.nominal


# #### CONTROL PORTS ####
hvac_port: HVACcontinuousModePort = HVACcontinuousModePort(data_provider=dp, zone_name='cabinet', max_heating_power=3000, max_cooling_power=3000)
temperature_setpoint_port: TemperatureSetpointPort = TemperatureSetpointPort(data_provider=dp, zone_name='cabinet', heating_levels=[13, 19, 20, 21, 22, 23], cooling_levels=[24, 25, 26, 28, 29, 32])
temperature_controller: TemperatureController = TemperatureController(hvac_heat_port=hvac_port, temperature_setpoint_port=temperature_setpoint_port, model_maker=model_maker)
# dp.add_var('MODE:cabinet', [2 if _ != 0 else 0 for _ in range(len(dp))], force=True)
simulation: Simulation = Simulation(model_maker)
simulation.add_temperature_controller(zone_name='cabinet', temperature_controller=temperature_controller)

simulation.run(suffix='sim')

# #### PRINT THE SIMULATION RESULTS ####
preference = Preference(preferred_temperatures=(19, 24), extreme_temperatures=(16, 29), preferred_CO2_concentration=(500, 1500), temperature_weight_wrt_CO2=0.5, power_weight_wrt_comfort=0.5, mode_cop={1: 2, -1: 2})

print(simulation)
print(simulation.control_ports)
preference.print_assessment(dp.datetimes, dp.series('PHVAC:cabinet#sim'), dp.series('TZ:cabinet#sim'), dp.series('CCO2:cabinet#sim'), dp.series('OCCUPANCY:cabinet'))
dp.plot()
Phvac: list[float] = dp.series('PHVAC:cabinet#sim')
electricity_needs: list[float | Any] = [abs(Phvac[k])/2 + occupancy[k] * occupant_consumption for k in dp.ks]
dp.add_var('PELEC:cabinet#sim', electricity_needs)

exposure_in_deg = 0
slope_in_deg = 180
solar_factor: float = .2
surface = 7
solar_system: SolarSystem = SolarSystem(dp.solar_model)
Collector(solar_system, 'PVpanel', surface_m2=surface, exposure_deg=exposure_in_deg, slope_deg=slope_in_deg, solar_factor=solar_factor)
global_productions_in_Wh = solar_system.powers_W(gather_collectors=True)
print('PV production in kWh:', round(sum(global_productions_in_Wh) / 1000))
dp.add_var('productionPV', global_productions_in_Wh)
dp.plot()
