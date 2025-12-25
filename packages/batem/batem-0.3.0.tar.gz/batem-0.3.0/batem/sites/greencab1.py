# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from batem.core.components import LayeredWallSide
from batem.core.data import DataProvider, Bindings
from batem.core.solar import SolarModel, SolarSystem, Collector
from batem.core.model import ModelMaker
from batem.core.control import SignalGenerator, Simulation, TemperatureController, TemperatureSetpointPort, HVACcontinuousModePort, OccupancyProfile, HeatingPeriod, CoolingPeriod
from batem.core.inhabitants import Preference
from batem.core.library import SIDE_TYPES

# #### greencab v1.0 ####
# #### DESIGN PARAMETERS ####

surface_window = 1.8 * 1.9
direction_window = -90
solar_protection = 90  # no protection
solar_factor = 0.56
cabinet_length = 5.77
cabinet_width = 2.21
cabinet_height = 2.29
body_metabolism = 100
occupant_consumption = 200
body_PCO2 = 7

surface_cabinet: float = cabinet_length*cabinet_width
volume_cabinet: float = surface_cabinet*cabinet_height
surface_cabinet_wall: float = 2 * (cabinet_length + cabinet_width) * cabinet_height - surface_window
q_infiltration: float = volume_cabinet / 3600

# #### DATA PROVIDER ####
bindings: Bindings = Bindings()
bindings.link_model_data('TZ:outdoor', 'weather_temperature')

dp: DataProvider = DataProvider(location='Saint-Julien-en-Saint-Alban', latitude_north_deg=44.71407488275519, longitude_east_deg=4.633318302898348, starting_stringdate='1/1/2022', ending_stringdate='31/10/2022', bindings=bindings, albedo=0.1, pollution=0.1, number_of_levels=4)

# #### SOLAR MODEL ####
solar_system: SolarSystem = SolarSystem(SolarModel(dp.weather_data))
Collector(solar_system, 'main', surface_m2=surface_window, exposure_deg=direction_window, slope_deg=90, solar_factor=solar_factor)
solar_gains_with_mask: list[float] = solar_system.powers_W(gather_collectors=True)
dp.add_var('Psun_window:cabinet', solar_gains_with_mask)

# #### SIGNAL GENERATION ####
siggen: SignalGenerator = SignalGenerator(dp, OccupancyProfile(weekday_profile={0: 0, 7: 1, 8: 3, 19: 0}, weekend_profile={0: 0}))
siggen.add_hvac_period(HeatingPeriod('16/11', '15/3', weekday_profile={0: None, 7: 19, 20: None}, weekend_profile={0: None, }))
siggen.add_hvac_period(CoolingPeriod('16/3', '15/11', weekday_profile={0: None, 7: 24, 20: None}, weekend_profile={0: None, }))
siggen.generate('cabinet')

occupancy_cabinet: list[float | None] = dp.series('OCCUPANCY:cabinet')
dp.add_var('PCO2:cabinet', siggen.filter(occupancy_cabinet, lambda x: x * body_PCO2 if x is not None else 0))
dp.add_param('CCO2:outdoor', 400)
dp.add_param('Q:cabinet-outdoor', q_infiltration)

# Create the ModelMaker - pass zones as keyword arguments (volume=number for simulated, None for boundary)
model_maker: ModelMaker = ModelMaker(data_provider=dp, periodic_depth_seconds=3600, state_model_order_max=None, cabinet=volume_cabinet, outdoor=None)

# Build the thermal model BEFORE accessing the model
wall: LayeredWallSide = model_maker.layered_wall_side('cabinet', 'outdoor', SIDE_TYPES.WALL, surface_cabinet_wall)
wall.layer('plaster', 13e-3)
wall.layer('steel', 5e-3)
wall.layer('wood', 3e-3)

floor: LayeredWallSide = model_maker.layered_wall_side('cabinet', 'outdoor', SIDE_TYPES.FLOOR, surface_cabinet)
floor.layer('wood', 10e-3)
floor.layer('steel', 5e-3)

ceiling: LayeredWallSide = model_maker.layered_wall_side('cabinet', 'outdoor', SIDE_TYPES.CEILING, surface_cabinet)
ceiling.layer('plaster', 13e-3)
ceiling.layer('steel', 5e-3)

glazing: LayeredWallSide = model_maker.layered_wall_side('cabinet', 'outdoor', SIDE_TYPES.GLAZING, surface_window)
glazing.layer('glass', 4e-3)
glazing.layer('air', 10e-3)
glazing.layer('glass', 4e-3)
glazing.layer('air', 10e-3)
glazing.layer('glass', 4e-3)

dp.add_var('GAIN:cabinet', [occupancy_cabinet[k] * (body_metabolism + occupant_consumption) + solar_gains_with_mask[k] for k in dp.ks])


# Add airflow connection between cabinet and outdoor for ventilation/infiltration
model_maker.connect_airflow('cabinet', 'outdoor', dp('Q:cabinet-outdoor'))

# Force rebuild of the nominal model now that all walls are defined
model_maker.state_models_cache.clear()  # Clear cache
_ = model_maker.nominal  # Rebuild nominal model with complete thermal structure

print("Model input names:", model_maker.inputs)
print("Model output names:", model_maker.outputs)

# Initialize control ports
hvac_port: HVACcontinuousModePort = HVACcontinuousModePort(data_provider=dp, zone_name='cabinet', max_heating_power=2000, max_cooling_power=2000)
temperature_setpoint_port: TemperatureSetpointPort = TemperatureSetpointPort(data_provider=dp, zone_name='cabinet', heating_levels=[13, 19, 20, 21, 22, 23], cooling_levels=[24, 25, 26, 28, 29, 32])
temperature_controller: TemperatureController = TemperatureController(hvac_heat_port=hvac_port, temperature_setpoint_port=temperature_setpoint_port, model_maker=model_maker)

simulation: Simulation = Simulation(model_maker)
simulation.add_control_port(hvac_port)
simulation.add_temperature_controller(zone_name='cabinet', temperature_controller=temperature_controller)
simulation.run(suffix='sim')

# #### PRINT THE SIMULATION RESULTS ####
preference: Preference = Preference(preferred_temperatures=(19, 24), extreme_temperatures=(16, 29), preferred_CO2_concentration=(500, 1500), temperature_weight_wrt_CO2=0.5, power_weight_wrt_comfort=0.5, mode_cop={1: 2, -1: 2})

print(simulation)
print(simulation.control_ports)
preference.print_assessment(dp.datetimes, dp.series('PHVAC:cabinet#sim'), dp.series('TZ:cabinet#sim'), dp.series('CCO2:cabinet#sim'), dp.series('OCCUPANCY:cabinet'))
dp.plot()
