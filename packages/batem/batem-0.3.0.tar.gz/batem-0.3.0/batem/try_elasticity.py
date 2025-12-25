from abc import ABC, abstractmethod
import math
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from msilib import CAB
from typing import Any
from batem.core.library import DIRECTIONS_SREF
from batem.core.solar import SolarModel, SolarSystem, Collector
from batem.core.weather import SiteWeatherData, SWDbuilder
from batem.core.control import OccupancyProfile


@dataclass
class SimulationData:
    # context
    latitude_north_deg: float
    longitude_east_deg: float
    year: int = 2023
    
    # weather
    outdoor_temperatures_deg: list[float]
    wind_speeds_m_s: list[float]
    cloudiness_percentage: list[float]
    precipitations_mm_per_hour: list[float]
    rains_mm_per_hour: list[float]
    snowfalls_mm_per_hour: list[float]
    pressures_hPa: list[float]
    humidities_percentage: list[float]
    wind_directions_deg: list[float]
    
    # occupancy
    occupancy_weekday_profile: dict[tuple[int, ...], dict[tuple[int, int], float]] = {(18, 7): 4}
    occupancy_weekend_profile: dict[tuple[int, ...], dict[tuple[int, int], float]] = {(0, 24): 4}
    average_occupancy_electric_gain_W: float = 100
    occupancies: list[float]
    presences: list[float]
    metabolic_gains: list[float]
    electricity_consumptions: list[float]
    permanent_electric_gain_W: float = 100
    electric_gain_per_occupant_W: float = 150
    
    # hvac
    average_occupancy_metabolic_gain_W: float = 100
    average_permanent_electric_gain_W: float = 100
    air_renewal_overheat_threshold_deg: float = 26
    heating_COP: float = 3
    cooling_COP: float = 3
    heating_setpoint_deg: float = 21
    cooling_setpoint_deg: float = 24
    winter_hvac_trigger_temperature_deg: float = 16
    summer_hvac_trigger_temperature_deg: float = 24
    hvac_hour_delay_for_trigger_h: int = 24
    # air_renewal_overheat_deg: float = 5
    extreme_discomfort_temperatures_deg: float = (16, 28)
    air_renewal_presence_vol_per_h: float = 1
    air_renewal_absence_vol_per_h: float = 0.1
    shutters_triggering_temperature_deg: float = 24
    ventilation_heat_recovery_efficiency: float = 0.8

    # geometry
    n_floors: int = 1
    shape_factor: float = 1
    total_floor_surface_m2: float = 100
    floor_height_m: float = 2.5
    south_glazing_ratio: float = 0.1
    east_glazing_ratio: float = 0.1
    west_glazing_ratio: float = 0.1
    north_glazing_ratio: float = 0.1
    passive_south_protection_angle_deg: float = 90
    ventilation_heat_recovery_efficiency: float = 0.8
    wall_surface_m2: float
    glazing_surface_m2: float
    inout_wall_composition: list[tuple[str, float]] = [('plaster', 13e-3), ('concrete', 14e-2), ('polystyrene', 15e-2)]
    inout_roof_composition: list[tuple[str, float]] = [('plaster', 13e-3), ('concrete', 14e-2), ('polystyrene', 30e-2)]
    inout_glazing_composition: list[tuple[str, float]] = [('glass', 4e-3), ('air', 12e-3), ('glass', 4e-3)]
    inout_ground_composition: list[tuple[str, float]] = [('concrete', 13e-2), ('gravels', 50e-2)]

    # production
    pv_efficiency: float = 0.40
    best_pv_exposure_deg: float
    best_pv_slope_deg: float
    pv_surface_m2: float
    PV_unit_production_W: list[float]
    PV_surface_production_W: list[float]
    
    # output data
    indoor_temperatures_deg: list[float]
    heating_needs_W: list[float]
    cooling_needs_W: list[float]
    hvac_needs_W: list[float]
    cooling_needs_W: list[float]
    max_heating_power_W: float
    max_cooling_power_W: float
    heating_needs_kWh: float
    cooling_needs_kWh: float
    hvac_needs_kWh: float


class Simulator(ABC):

    @abstractmethod
    def simulate(self, input_data: SimulationData) -> SimulationData:
        pass


# class Simulation(ABC):

#     def __init__(self, simulator: Simulator, simulation_data: SimulationData | list[SimulationData], max_workers: int | None = None, use_threads: bool = False) -> None:
#         if isinstance(simulation_data, SimulationData):
#             self.multiple_simulations = False
#             simulation_data: SimulationData = simulator.simulate(simulation_data.copy())
#             self.data = [SimulationData(simulation_data, output_data)]
#         else:
#             # Run simulations in parallel
#             # ProcessPoolExecutor (use_threads=False) runs on separate CPU cores for true parallelism
#             # ThreadPoolExecutor (use_threads=True) is limited by Python's GIL and won't use separate cores for CPU-bound tasks
#             self.multiple_simulations = True
#             executor_class = ThreadPoolExecutor if use_threads else ProcessPoolExecutor
#             with executor_class(max_workers=max_workers) as executor:
#                 # Submit all simulation tasks with indices to preserve order
#                 future_to_index = {executor.submit(simulator.simulate, inp_data): idx for idx, inp_data in enumerate(simulation_data)}
#                 # Collect results as they complete, storing by index
#                 results: dict[int, SimulationData] = {}
#                 for future in as_completed(future_to_index):
#                     idx = future_to_index[future]
#                     output_data = future.result()
#                     results[idx] = output_data
#                 # Build results list in the same order as input_data
#                 self.simulation_data: list[SimulationData] = [SimulationData(inp_data, results[idx]) for idx, inp_data in enumerate(simulation_data)]

    


class SimulationController:

    def __init__(self, simulation_data: SimulationData) -> None:
        swd_builder: SWDbuilder = SWDbuilder(location=simulation_data.location, latitude_north_deg=simulation_data.latitude_north_deg, longitude_east_deg=simulation_data.longitude_east_deg)
        site_weather_data: SiteWeatherData = swd_builder(from_stringdate=f'1/1/{simulation_data.year}', to_stringdate=f'31/12/{simulation_data.year}', albedo=simulation_data.albedo, pollution=simulation_data.pollution)
        solar_model: SolarModel = SolarModel(simulation_data.site_weather_data)
        simulation_data: SimulationData = self.initial_simulation_maker(simulation_data, site_weather_data, solar_model)
        simulation_data: SimulationData = self.parametric_simulation_maker(simulation_data)
        
        
    def initial_simulation_maker(self, simulation_data: SimulationData, site_weather_data: SiteWeatherData, solar_model: SolarModel) -> SimulationData:
        
        simulation_data.outdoor_temperatures_deg = site_weather_data.get('temperature')
        simulation_data.wind_speeds_m_s = site_weather_data.get('wind_speed_m_s')
        simulation_data.cloudiness_percentage = site_weather_data.get('cloudiness')
        simulation_data.precipitations_mm_per_hour = site_weather_data.get('precipitation')
        simulation_data.rains_mm_per_hour = site_weather_data.get('rain')
        simulation_data.snowfalls_mm_per_hour = site_weather_data.get('snowfall')
        simulation_data.pressures_hPa = site_weather_data.get('pressure')
        simulation_data.humidities_percentage = site_weather_data.get('humidity')
        simulation_data.wind_directions_deg = site_weather_data.get('wind_direction_in_deg')
        simulation_data.best_pv_exposure_deg, simulation_data.best_pv_slope_deg = solar_model.best_direction()
        simulation_data.occupancies = OccupancyProfile(simulation_data.occupancy_weekday_profile, simulation_data.occupancy_weekend_profile).signal(simulation_data.datetimes)
        simulation_data.presences = [int(occupancy > 0) for occupancy in simulation_data.occupancies]
        simulation_data.metabolic_gains = [occupancy * simulation_data.average_occupancy_metabolic_gain_W for occupancy in simulation_data.occupancies]
        simulation_data.electricity_consumptions = [simulation_data.average_permanent_electric_gain_W + occupancy * simulation_data.average_occupancy_electric_gain_W for occupancy in simulation_data.occupancies]
        return simulation_data
        
    def parametric_simulation_maker(self, simulation_data: SimulationData, n_floors: int=None, shape_factor: float=None, rotation_angle_deg: float=None, passive_south_protection_angle_deg: float=None, glazing_direction: (float, DIRECTIONS_SREF) = None, solar_protection_angle_deg: float=None, ventilation_heat_recovery_efficiency: float=None, heating_setpoint_deg: float=None, cooling_setpoint_deg: float=None, insulation_ratio_m: float=None) -> SimulationData:
        
        solar_pv_system: SolarSystem = SolarSystem(solar_model)
        Collector(solar_pv_system, 'PVplant', surface_m2=1, , slope_deg=180)
        
        total_floor_surface_m2: float = simulation_data.total_floor_surface_m2
        floor_surface_m2: float=total_floor_surface_m2 / n_floors

        side_areas: dict[DIRECTIONS_SREF, float]={DIRECTIONS_SREF.NORTH: L_NS * floor_height_m * n_floors, DIRECTIONS_SREF.SOUTH: L_NS *
            floor_height_m * n_floors, DIRECTIONS_SREF.EAST: L_EW * floor_height_m * n_floors, DIRECTIONS_SREF.WEST: L_EW * floor_height_m * n_floors}
        total_side_area: float=sum(side_areas.values())

        total_side_area_for_glazing: float=sum(side_areas.values())
        if total_side_area_for_glazing > 0:
            effective_glazing_ratio: float=total_glazing_area / total_side_area_for_glazing
        else:
            effective_glazing_ratio: float=default_glazing_ratio

        glazing_direction_ratios: dict[DIRECTIONS_SREF, float]={direction: side_areas[direction] * effective_glazing_ratio for direction in DIRECTIONS_SREF}
        
        self.unit_solar_gain_system = SolarSystem(self.solar_model)
        for direction in DIRECTIONS_SREF:
            Collector(self.unit_solar_gain_system, direction.name, exposure_deg=direction.value, slope_deg=SLOPES.VERTICAL.value, surface_m2=1, solar_factor=1)
        Collector(self.unit_solar_gain_system, 'HORIZONTAL_UP', exposure_deg=DIRECTIONS_SREF.SOUTH.value, slope_deg=SLOPES.HORIZONTAL_UP.value, surface_m2=1, solar_factor=1)
        self.set('unit_canonic_solar_powers_W', self.unit_solar_gain_system.powers_W(gather_collectors=False))
        self.unit_canonic_solar_powers_W: list[float] = self.unit_solar_gain_system.powers_W(gather_collectors=False)

        if simulation_data.modified_glazing_direction is not None and simulation_data.modified_glazing_direction in DIRECTIONS_SREF and simulation_data.modified_glazing_ratio is not None:
            modified_direction_area: float=side_areas[simulation_data.modified_glazing_direction] * simulation_data.modified_glazing_ratio
            directed_glazing_areas[simulation_data.modified_glazing_direction]=modified_direction_area

            remaining_glazing_area: float=total_glazing_area - modified_direction_area

            other_side_areas_sum: float=sum(side_areas[d] for d in DIRECTIONS_SREF if d != simulation_data.modified_glazing_direction)

            if other_side_areas_sum > 0 and remaining_glazing_area >= 0:
                for direction in DIRECTIONS_SREF:
                    if direction != simulation_data.modified_glazing_direction:
                        proportion: float=side_areas[direction] / other_side_areas_sum
                        directed_glazing_areas[direction]=remaining_glazing_area * proportion
            elif remaining_glazing_area < 0:
                for direction in DIRECTIONS_SREF:
                    if direction != simulation_data.modified_glazing_direction:
                        directed_glazing_areas[direction]=0.0

        total_glazing_area: float=sum(directed_glazing_areas.values())
        total_wall_area: float=total_side_area - total_glazing_area

        return total_wall_area, floor_surface_m2, total_glazing_area, directed_glazing_areas

    def simulation_finalizer(self, simulation_data: SimulationData) -> SimulationData:
        pass

    def simulate(self, simulator: Simulator, simulation_data: SimulationData | list[SimulationData], max_workers: int | None = None, use_threads: bool = False) -> None:
        if isinstance(simulation_data, SimulationData):
            self.multiple_simulations = False
            simulation_data: SimulationData = simulator.simulate(simulation_data.copy())
            self.data = [SimulationData(simulation_data, output_data)]
        else:
            # Run simulations in parallel
            # ProcessPoolExecutor (use_threads=False) runs on separate CPU cores for true parallelism
            # ThreadPoolExecutor (use_threads=True) is limited by Python's GIL and won't use separate cores for CPU-bound tasks
            self.multiple_simulations = True
            executor_class = ThreadPoolExecutor if use_threads else ProcessPoolExecutor
            with executor_class(max_workers=max_workers) as executor:
                # Submit all simulation tasks with indices to preserve order
                future_to_index = {executor.submit(simulator.simulate, inp_data): idx for idx, inp_data in enumerate(simulation_data)}
                # Collect results as they complete, storing by index
                results: dict[int, SimulationData] = {}
                for future in as_completed(future_to_index):
                    idx = future_to_index[future]
                    output_data = future.result()
                    results[idx] = output_data
                # Build results list in the same order as input_data
                self.simulation_data: list[SimulationData] = [SimulationData(inp_data, results[idx]) for idx, inp_data in enumerate(simulation_data)]  

    def parametric(self, name: str, values: list[float] | tuple[str, list[float]] = None) -> None | float:
        if values is None:
            return self.parametrics[name]
        else:
            self.parametrics[name] = sorted(values)
        if name not in self.parameters:
            self.parameter(name, values[0])
        self.parametrics[name] = sorted(values)

    def simulate(self, simulator: Simulator, parametric_data_name: str = None) -> SimulationData:
        nominal_input_data: SimulationData = self.reset()
        self.parametric_simulation_maker(nominal_input_data)
        if parametric_data_name is None:
            self.nominal_input_data: SimulationData = 
            return simulator.simulate(nominal_input_data)
        else:
            input_data_set: list[SimulationData] = []
            for value in self.parametrics[parametric_data_name]:
                input_data: Any = nominal_input_data.copy()
                input_data.param(parametric_data_name, value)
                self.parametric_simulation_maker(input_data)
                input_data_set.append(input_data)
            return Simulation(simulator, input_data_set)
        
    def __call__(self, data_name: str) -> float | list[float] | dict[str, float] | dict[str, list[float]]:
        if self.multiple_simulations:
            data_values = [data(data_name, parametric=True) for data in self.data]
            for i in range(1, len(data_values)):
                if data_values[i] != data_values[0]:
                    return data_values
            return data_values[0]
        else:
            data = self.data[0](data_name)
            return data


class Configuration:

    def __init__(self, latitude_north_deg: float, longitude_east_deg: float, year: int, albedo: float=0.1, pollution: float=0.1, total_floor_surface_m2: float=100, height_m: float=2.8, n_floors: int=1, shape_factor: float=1, default_glazing_ratio: float=0.1, modified_glazing_ratio: float=None, modified_glazing_direction: DIRECTIONS_SREF=None) -> None:
        self.latitude_north_deg=latitude_north_deg
        self.longitude_east_deg=longitude_east_deg
        self.year=year
        self.albedo=albedo
        self.pollution=pollution
        self.total_floor_surface_m2=total_floor_surface_m2
        self.height_m=height_m
        self.n_floors=n_floors
        self.shape_factor=shape_factor
        self.default_glazing_ratio=default_glazing_ratio
        self.modified_glazing_ratio=modified_glazing_ratio
        self.modified_glazing_direction=modified_glazing_direction


class SimulationData:

    def __init__(self, input_data: SimulationData, output_data: SimulationOutputData, parametric: str = None) -> None:
        self.input_data: SimulationData = input_data
        self.output_data: SimulationOutputData = output_data

    def __call__(self, data_name: str) -> float | list[float] | dict[str, float] | dict[str, list[float]]:
        if data_name in self.output_data:
            return self.output_data[data_name]
        else:
            raise ValueError(f"Data name {data_name} not found")

if __name__ == '__main__':
    result: float=house_elasticity(
        total_floor_surface_m2=100, height_m=2.5, n_floors=1, shape_factor=1,
        default_glazing_ratio=0.1)
    print("### Result:")
    print(f"Total wall area: {result[0]}")
    print(f"Floor area: {result[1]}")
    print(f"Total glazing area: {result[2]}")
    print(f"Directed glazing areas: {result[3]}")
    print(f"Sum of directed areas: {sum(result[3].values())}")
    print(f"Total side area: {result[0] + result[2]}")  # wall_area + glazing_area

    print('--------------------------------')
    result: float=house_elasticity(
        total_floor_surface_m2=100, height_m=2.5, n_floors=2, shape_factor=2,
        default_glazing_ratio=0.1, modified_glazing_ratio=0.2, modified_glazing_direction=DIRECTIONS_SREF.SOUTH
    )
    print("### Result:")
    print(f"Total wall area: {result[0]}")
    print(f"Floor area: {result[1]}")
    print(f"Total glazing area: {result[2]}")
    print(f"Directed glazing areas: {result[3]}")
    print(f"Sum of directed areas: {sum(result[3].values())}")
    print(f"Total side area: {result[0] + result[2]}")  # wall_area + glazing_area
