"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

It is an instance of Model for the office H358

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
import time
import numpy
from core.statemodel import StateModel
from core.components import LayeredWallSide, SIDE_TYPES
from core.model import _CoreModelMaker
from core.data import DataProvider, Bindings
from batem.core.siggen import Merger, SignalBuilder
from core.solar import InvertedMask, RectangularMask, SolarSystem, SolarModel, Collector
from core.control import TemperatureController, ControlModel, ZoneTemperatureSetpointPort, ZoneHvacContinuousPowerPort, ControlledZoneManager

bindings = Bindings()
bindings.link_model_data('TZoutdoor', 'weather_temperature')
bindings.link_model_data('PZindoor', 'indoor:Pheat')
bindings.link_model_data('PCO2indoor', 'indoor:PCO2')
bindings.link_model_data('CCO2outdoor', 'outdoor:CCO2')

dp = DataProvider(latitude_north_deg=45.19160172269835, longitude_east_deg=5.717386779367178, starting_stringdate='1/1/2022', ending_stringdate='1/1/2023', bindings=bindings, location='Grenoble', number_of_levels=4)

dp.add_param('body_metabolism', 100, (50, 150, 10))
dp.add_param('body_PCO2', 7, (0, 25, 1))
dp.add_param('outdoor:CCO2', 400)
dp.add_param('indoor:volume', 250)

occupancy_sgen = SignalBuilder(dp.series('datetime'))
occupancy_sgen.build_daily((1, 2, 3, 4, 5), {0: 2, 8: 0, 12: 2, 14: 0, 17: 2})
occupancy_sgen.build_daily((6, 7), {0: 2})
occupancy: list[float] = occupancy_sgen()
dp.add_var('indoor:occupancy', occupancy)

window_mask = InvertedMask(RectangularMask((-90, 90), (0, 45)))
solar_model = SolarModel(dp.weather_data)
solar_system = SolarSystem(solar_model)
Collector(solar_system, 'main', surface_m2=2, exposure_deg=0, slope_deg=90, solar_factor=0.85, close_mask=window_mask)
solar_gains_with_mask: list[float] = solar_system.powers_W(gather_collectors=True)
dp.add_var('Psun_window', solar_gains_with_mask)

dp.add_parameterized('indoor:Pmetabolism', lambda k: dp('body_metabolism') * dp('indoor:occupancy', k), 100, 10)
dp.add_parameterized('indoor:Pheat', lambda k: dp('indoor:occupancy', k) * dp('body_metabolism') + dp('Psun_window', k), 100, 10)
dp.add_parameterized('indoor:PCO2', lambda k: dp('body_PCO2') * dp('indoor:occupancy', k), 7, 1)

print('Making signals for controls and set-points')

temperature_sgen = SignalBuilder(dp.series('datetime'))
temperature_sgen.build_daily([0, 1, 2, 3, 4], {0: 13, 7: 20, 18: 13})
temperature_sgen.build_daily([5, 6], {0: 20})
heating_period: list[float | None] = temperature_sgen.build_seasonal('16/11', '15/3')
cooling_period_temperature_sgen = SignalBuilder(dp.series('datetime'))
cooling_period_temperature_sgen.build_daily([0, 1, 2, 3, 4], {0: 20, 7: 24, 18: 29})
cooling_period_temperature_sgen.build_daily([5, 6], {0: 29})
cooling_period: list[float | None] = cooling_period_temperature_sgen.build_seasonal('15/6', '15/9')
temperature_sgen.merge(cooling_period_temperature_sgen())
dp.add_var('TZindoor_setpoint', temperature_sgen())

hvac_modes_sgen = SignalBuilder(dp.series('datetime'))
hvac_modes_sgen.merge(heating_period)
hvac_modes_sgen.merge(cooling_period, merger=Merger(lambda x, y: x - y, 'n'))
dp.add_var('mode', hvac_modes_sgen())

print('Make state models and put in cache')
start: float = time.time()
state_model_maker = _CoreModelMaker('indoor', data_provider=dp, periodic_depth_seconds=3600, state_model_order_max=5)

side: float = 10.
height: float = 2.5
wall_surface: float = 4 * side * height
windows_surface: float = wall_surface * 0.1
floor_surface: float = side**2
house_volume: float = floor_surface * height

wall: LayeredWallSide = state_model_maker.layered_wall_side('indoor', 'outdoor', SIDE_TYPES.WALL, wall_surface - windows_surface)
wall.layer('foam', 0.2)
wall.layer('concrete', 0.13)

roof: LayeredWallSide = state_model_maker.layered_wall_side('indoor', 'outdoor', SIDE_TYPES.ROOF, floor_surface)
roof.layer('foam', 0.2)
roof.layer('concrete', 0.13)

glazing: LayeredWallSide = state_model_maker.layered_wall_side('indoor', 'outdoor', SIDE_TYPES.GLAZING, windows_surface)
glazing.layer('glass', 4e-3)
glazing.layer('air', 12e-3)
glazing.layer('glass', 4e-3)

air_renewal_volume_per_hour = 1
state_model_maker.connect_airflow('outdoor', 'indoor', dp('indoor:volume') * air_renewal_volume_per_hour / 3600)
state_model_maker.zones_to_simulate('indoor')

nominal_state_model: StateModel = state_model_maker.make_k(0)

print('\nduration: %i secondes' % round(time.time() - start))

nominal_state_model: StateModel = state_model_maker.make_k(k=None)
print(nominal_state_model)


class DirectManager(ControlledZoneManager):

    def __init__(self, dp: DataProvider,  building_state_model_maker: _CoreModelMaker) -> None:
        super().__init__(dp, building_state_model_maker)

    def make_ports(self) -> None:
        self.temperature_setpoint_cport = ZoneTemperatureSetpointPort(dp, 'TZindoor_setpoint', mode_name='mode', mode_value_domains={1: (13, 19, 20, 21, 22, 23), 0: None, -1: (24, 25, 26, 28, 29, 32)})  # 'TZindoor',

        self.heater_cooler_control_cport = ZoneHvacContinuousPowerPort(dp, 'PZindoor_control', max_heating_power=3000, max_cooling_power=3000, hvac_mode='mode')

    def zone_temperature_controllers(self) -> dict[TemperatureController, float]:
        return {self.make_zone_temperature_controller('TZindoor', self.temperature_setpoint_cport, 'PZindoor', self.heater_cooler_control_cport): 0}

    def controls(self, k: int, X_k: numpy.matrix, current_output_dict: dict[str, float]) -> None:
        pass


manager = DirectManager(dp, state_model_maker)
control_model = ControlModel(state_model_maker, manager)
print(control_model)
control_model.simulate()
dp.plot()
