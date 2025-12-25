# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from __future__ import annotations
import matplotlib.pyplot as plt
import numpy
import math
from core.solar import HorizonMask, SolarModel, SolarSystem, Collector
from core.data import DataProvider, Bindings
from core.components import SIDE_TYPES, Composition
from core.model import _CoreModelMaker
from batem.core.siggen import SignalBuilder, Merger
from core.inhabitants import Preference
from core.control import ZoneTemperatureSetpointPort, TemperatureController, ControlModel, AirflowPort, ZoneHvacContinuousPowerPort, ControlledZoneManager
from core.library import properties
import time

print("linking model variables with recorded data...")
bindings = Bindings()
bindings('TZoutdoor', 'weather_temperature')
bindings('PZcabinet', 'cabinet:Pheat')
bindings('PCO2cabinet', 'cabinet:PCO2')
bindings('PCO2toilet', 'toilet:PCO2')
bindings('CCO2cabinet', 'cabinet_CO2_concentration')
bindings('cabinet-outdoor:z_window', 'window_opening')
bindings('cabinet:occupancy', 'occupancy')

print('Loading data...')
dp = DataProvider(location='Grenoble_Faure', latitude_north_deg=45.18851777751821, longitude_east_deg=5.733932073114256, starting_stringdate="1/1/2022", ending_stringdate="31/12/2022", bindings=bindings, albedo=0.2, pollution=0.1, number_of_levels=4)


print("Displaying data solar gain passing through window...")
surface_window = 3.07 * 2.29 + 3 * .80 * .60 + .73 * .6 + 2 * 1 * 1
direction_window = -7
solar_protection = 180  # no protection
solar_factor = 0.56

solar_model = SolarModel(dp.weather_data)
solar_system = SolarSystem(solar_model)
roof_building_mask = HorizonMask((-180, 90), (-98, 90), (-98, 20), (-88, 50), (45, 50), (45, 90), (180, 90))

side_window_mask = HorizonMask((-180, 50), (83, 50), (83, 20), (103, 20), (103, 90), (180, 90))
side_window_mask.plot()
plt.show()

Collector(solar_system, 'roof', surface_m2=surface_window, exposure_deg=direction_window, slope_deg=16, solar_factor=solar_factor, collector_mask=roof_building_mask)
Collector(solar_system, 'side', surface_m2=1*.6, exposure_deg=173, slope_deg=90, solar_factor=solar_factor, collector_mask=side_window_mask)
solar_gains_with_mask = solar_system.solar_gains_W(gather_collectors=True)
dp.add_var('Psun_window', solar_gains_with_mask)


# Dimensions
# surfaces
surface_fl0_office = 34
surface_fl0_bedroom = 11
surface_fl0_bathroom = 3
surface_fl0_storage = 3
surface_fl0_restroom = 1
surface_fl1_main = 55
surface_fl1_bedroom = 16
surface_fl1_bathroom = 5
surface_fl1_storage = 2
surface_fl2_bedroom = 12

roof_angle = 16 / 180 * math.pi
roof_fl1_main = (surface_fl0_restroom - surface_fl2_bedroom) / math.cos(roof_angle)
roof_fl1_bedroom = surface_fl1_bedroom / math.cos(roof_angle)
roof_fl1_bathroom = surface_fl1_bathroom / math.cos(roof_angle)
roof_fl1_storage = surface_fl1_storage / math.cos(roof_angle)
roof_fl2_bedroom = surface_fl2_bedroom / math.cos(roof_angle)


#########
insulation_thickness = 150e-3
surface_cabinet: float = 5.85*2.14
volume_cabinet: float = surface_cabinet*2.29
surface_toilet: float = 1.18*2.14
volume_toilet: float = surface_toilet*2.29
surface_cabinet_wall: float = (2 * 6000e-3 + 2440e-3) * 2590e-3 - surface_window

# data occupants
body_metabolism = 100
occupant_consumption = 200
occupancy_sgen = SignalBuilder(dp.series('datetime'))
weekdays: list[float] = occupancy_sgen.build_daily([0, 1, 2, 3, 4], {0: 0, 8: 3, 18: 0})  # 12: 0, 13: 3,
weekends: list[float] = occupancy_sgen.build_daily([5, 6], {0: 0})
occupancy: list[float] = occupancy_sgen()
dp.add_var('occupancy', occupancy)
presence: list[int] = [int(occupancy[k] > 0) for k in range(len(dp))]
dp.add_var('presence', presence)

dp.add_var('PZcabinet', [occupancy[k] * (body_metabolism + occupant_consumption) + dp('Psun_window', k) for k in dp.ks])
dp.add_param('PZtoilet', 0)

# Data heating and cooling
# winter_temperature_sgen = SignalGenerator(dp.series('datetime'))
# weekdays = winter_temperature_sgen.daily([0, 1, 2, 3, 4], {0: None, 7: 20, 19: None})
# heating_period = winter_temperature_sgen.seasonal('16/11', '15/3')
# summer_temperature_sgen = SignalGenerator(dp.series('datetime'))
# weekdays = summer_temperature_sgen.daily([0, 1, 2, 3, 4], {0: None, 7: 22, 19: None})
# cooling_period = summer_temperature_sgen.seasonal('16/3', '15/11', in_value=-1)

temperature_sgen = SignalBuilder(dp.series('datetime'), None)
temperature_sgen.build_daily([0, 1, 2, 3, 4], {0: None, 7: 20, 19: None}, merger=Merger(min, 'r'))
heating_period = temperature_sgen.build_seasonal('16/11', '15/3', 1, merger=Merger(max, 'b'))
temp_sgen = SignalBuilder(dp.series('datetime'), None)
temp_sgen.build_daily([0, 1, 2, 3, 4], {0: None, 7: 22, 19: None}, merger=Merger(min, 'r'))
cooling_period = temp_sgen.build_seasonal('16/3', '15/11', 1, merger=Merger(max, 'b'))
temperature_sgen.merge(temp_sgen(), merger=Merger(min, 'n'))
dp.add_var('TZcabinet_setpoint', temperature_sgen())
# hvac_temperature_sgen = SignalGenerator(dp.series('datetime'))
# hvac_temperature_sgen.seasonal(dm_start: str, dm_end: str, in_value: float = 1, out_value: float = None)
# , winter_temperature_sgen(), summer_temperature_sgen())
dp.add_var('TZcabinet_setpoint', temperature_sgen())

# hvac_modes = SignalGenerator(dp.series('datetime'), heating_period, cooling_period)
# hvac_modes.integerize()
hvac_modes_sgen = SignalBuilder(dp.series('datetime'))
hvac_modes_sgen.merge(heating_period, merger=Merger(max, 'l'))
hvac_modes_sgen.merge(cooling_period, merger=Merger(lambda x, y: x - y, 'n'))
dp.add_var('mode', hvac_modes_sgen())

# dp.add_var('mode', hvac_modes())

# Data ventilation and CO2
q_infiltration: float = volume_cabinet/3600
q_ventilation = 6 * volume_cabinet/3600
q_freecooling: float = 15 * volume_cabinet/3600
body_PCO2 = 7

dp.add_param('CCO2outdoor', 400)
dp.add_param('cabinet:volume', volume_cabinet)
dp.add_param('toilet:volume', volume_toilet)
dp.add_var('PCO2cabinet', [body_PCO2 * occupancy[k] for k in range(len(dp))])
dp.add_param('PCO2toilet', 0)
ventilation_sgen = SignalBuilder(dp.series('datetime'))
ventilation_sgen.build_daily([0, 1, 2, 3, 4], {0: 0, 7: 1, 10: 0})
ventilation_sgen.build_daily([5, 6], {0: 0})
ventilation: list[float] = ventilation_sgen()
dp.add_var('ventilation', ventilation)
dp.add_var('cabinet-outdoor:Q', [q_infiltration + ventilation[k]*q_ventilation for k in range(len(dp))])
dp.add_var('toilet-cabinet:Q', [q_infiltration + ventilation[k]*q_ventilation for k in range(len(dp))])

ventilation_cport = AirflowPort(dp, 'cabinet-outdoor:Q', 'mode', 'presence', {-2: (q_infiltration,), -1: (q_infiltration, q_freecooling), 0: (q_infiltration,), 1: (q_infiltration, q_ventilation, q_freecooling), 2: (q_infiltration,), 3: (q_infiltration, q_ventilation)})

properties.load('steel', 'thermal', 177)
properties.load('glass', 'thermal', 267)
properties.load('polystyrene', 'thermal', 145)
properties.load('wood', 'thermal', 240)
properties.load('plaster', 'thermal', 14)

state_model_maker = _CoreModelMaker('cabinet', 'toilet', data_provider=dp, periodic_depth_seconds=3600, state_model_order_max=5)

wall = SideFactory(state_model_maker, ('wood', 3e-3), ('polystyrene', insulation_thickness), ('steel', 5e-3), ('wood', 3e-3))
floor = SideFactory(state_model_maker, ('wood', 10e-3), ('polystyrene', insulation_thickness), ('steel', 5e-3))
ceiling = SideFactory(state_model_maker, ('wood', 3e-3), ('polystyrene', insulation_thickness), ('steel', 5e-3))
glazing = SideFactory(state_model_maker, ('glass', 4e-3), ('air', 10e-3), ('glass', 4e-3), ('air', 10e-3), ('glass', 4e-3))
internal_wall_composition = SideFactory(state_model_maker, ('wood', 9e-3), ('air', 20e-3), ('wood', 9e-3))

# Cabinet
state_model_maker.make_side(wall('cabinet', 'outdoor', SIDE_TYPES.WALL, surface_cabinet_wall))
state_model_maker.make_side(floor('cabinet', 'outdoor', SIDE_TYPES.FLOOR, surface_cabinet))
ceiling_composition.make_side(ceiling('cabinet', 'outdoor', SIDE_TYPES.CEILING, surface_cabinet))
glazing_composition.make_side(glazing('cabinet', 'outdoor', SIDE_TYPES.GLAZING, surface_window))
# Toilet
internal_wall_composition.make_side('cabinet', 'toilet', SIDE_TYPES.WALL, 2138e-3 * 2290e-3)
wall_composition.make_side('toilet', 'outdoor', SIDE_TYPES.WALL, (1315e-3 * 2 + 2138e-3) * 2290e-3)
floor_composition.make_side('toilet', 'outdoor', SIDE_TYPES.FLOOR, 2440e-3 * 1330e-3)
ceiling_composition.make_side('toilet', 'outdoor', SIDE_TYPES.CEILING, 2440e-3 * 1330e-3)

state_model_maker.zones_to_simulate('cabinet', 'toilet')
state_model_maker.connect_airflow('cabinet', 'outdoor', dp('cabinet-outdoor:Q'))  # nominal value
state_model_maker.connect_airflow('toilet', 'cabinet', dp('toilet-cabinet:Q'))  # nominal value
print(state_model_maker)

nominal_state_model = state_model_maker.make_k()
print(nominal_state_model)

start: float = time.time()
print('\nmodel simulation duration: %f secondes' % (time.time() - start))


class DirectManager(ControlledZoneManager):

    def __init__(self, dp: DataProvider, building_state_model_maker: _CoreModelMaker) -> None:
        super().__init__(dp, building_state_model_maker)

    def make_ports(self) -> None:
        self.airflow_cport = AirflowPort(dp, 'cabinet-outdoor:Q', 'mode', 'presence', {-2: (q_infiltration,), -1: (q_infiltration, q_freecooling), 0: (q_infiltration,), 1: (q_infiltration, q_ventilation, q_freecooling), 2: (q_infiltration,), 3: (q_infiltration, q_ventilation)})

        self.temperature_setpoint_cport = ZoneTemperatureSetpointPort(dp, 'TZcabinet_setpoint', 'TZcabinet', mode_name='mode', mode_value_domains={1: (13, 19, 20, 21, 22, 23), 0: None, -1: (24, 25, 26, 28, 29, 32)})

        self.mode_power_cport = ZoneHvacContinuousPowerPort(dp, 'PZcabinet_control', 'PZcabinet', max_heating_power=3000, max_cooling_power=3000, hvac_mode='mode', full_range=False)

    def zone_temperature_controllers(self) -> dict[TemperatureController, float]:
        return {self.make_zone_temperature_controller(self.temperature_setpoint_cport, self.mode_power_cport): 0}

    def controls(self, k: int, X_k: numpy.matrix, current_output_dict: dict[str, float]) -> None:
        Tin: float = current_output_dict['TZcabinet']
        Tout: float = self.dp('weather_temperature', k)
        if self.dp('presence', k) == 1:
            if 20 <= Tout <= 23 or self.dp('CCO2cabinet', k) > 3000:
                self.airflow_cport(k, q_freecooling)
            elif Tin > 23 and Tout < 20:
                self.airflow_cport(k, q_freecooling)


preference = Preference(preferred_temperatures=(19, 24), extreme_temperatures=(16, 29), preferred_CO2_concentration=(500, 1500), temperature_weight_wrt_CO2=0.5, power_weight_wrt_comfort=0.5, mode_cop={1: 2, -1: 2})

manager = DirectManager(dp, state_model_maker)
# manager = DayAheadManager(state_model_maker, dp, {ventilation_cport: 0}, preference)

control_model = ControlModel(state_model_maker, manager)
print(control_model)
control_model.simulate()

Pheater = dp.series('PZcabinet_control')
occupancy = dp.series('occupancy')
preference.print_assessment(dp.series('datetime'), PHVAC=Pheater, temperatures=dp.series('TZcabinet'), CO2_concentrations=dp.series('CCO2cabinet'), occupancies=dp.series('occupancy'), action_sets=(), modes=dp.series('mode'), list_extreme_hours=True)
electricity_needs = [abs(Pheater[k])/2 + occupancy[k] * occupant_consumption for k in dp.ks]
dp.add_var('electricity needs', electricity_needs)

exposure_in_deg = 0
slope_in_deg = 0
solar_factor = .2
surface = 7
solar_system = SolarSystem(solar_model)
solar_system.add_collector('PVpanel', surface_m2=surface, exposure_deg=exposure_in_deg, slope_deg=slope_in_deg, solar_factor=solar_factor)
global_productions_in_Wh, _ = solar_system.solar_gains_W()
print('PV production en kWh:', round(sum(global_productions_in_Wh) / 1000))
dp.add_var('productionPV', global_productions_in_Wh)

dp.plot()
