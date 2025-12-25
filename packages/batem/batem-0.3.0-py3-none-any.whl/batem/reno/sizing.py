
from batem.core import weather
from batem.reno.community.creation import CommunityHousesBuilder
from batem.reno.community.model import EnergyCommunity
from batem.reno.constants import MANAGER_TYPE
from batem.reno.indicators import neeg
from batem.reno.pv.creation import PVPlantBuilder, WeatherDataBuilder
from batem.reno.simulation.scenario import Scenario
from batem.reno.simulation.scheduler.model import Scheduler
from batem.reno.utils import TimeSpaceHandler, parse_args
from scipy.optimize import differential_evolution

MANAGER_MAP = {
    0: MANAGER_TYPE.BASIC,
    1: MANAGER_TYPE.REACTIVE,
    2: MANAGER_TYPE.ADAPTIVE,
}


class Simulation:

    def __init__(self, time_space_handler: TimeSpaceHandler):
        self.time_space_handler = time_space_handler

    def run(self, manager: MANAGER_TYPE,
            weather_data: weather.SiteWeatherData,
            community: EnergyCommunity,
            number_of_panels: int,
            peak_power_kW: float,
            print_info: bool = True):

        exposure_deg = 0.0
        slope_deg = 152.0

        community.pv_plant = PVPlantBuilder().build(
            weather_data=weather_data,
            exposure_deg=exposure_deg,
            slope_deg=slope_deg,
            peak_power_kW=peak_power_kW,
            number_of_panels=number_of_panels,
            panel_height_m=1.7,
            panel_width_m=1)

        scenario = Scenario(
            location=self.time_space_handler.location,
            start_date=self.time_space_handler.start_date,
            end_date=self.time_space_handler.end_date,
            house_ids=[house.house_id for house in community.houses],
            pv_number_of_panels=number_of_panels,
            pv_panel_height_m=community.pv_plant.panel_height_m,
            pv_panel_width_m=community.pv_plant.panel_width_m,
            pv_exposure_deg=exposure_deg,
            pv_slope_deg=slope_deg,
            pv_peak_power_kW=peak_power_kW,
            pv_mount_type=community.pv_plant.mount_type,
            indication_interval=[7, 22],
            manager_type=manager
        )

        scheduler = Scheduler(community, scenario)
        scheduler.run(write_results=False, print_info=print_info)

        result = self._get_neeg(scheduler)
        scenario.delete_results(self.time_space_handler, manager)
        return result

    def _get_neeg(self, scheduler: Scheduler) -> float:

        members = scheduler.members
        time_range = self.time_space_handler.range_hourly

        sim_consumption = [sum(member.sim_consumption[datetime]
                               for member in members)
                           for datetime in time_range]

        pv_production = scheduler.community.pv_plant.production.usage_hourly

        load_by_time = {datetime: sim_consumption[i]
                        for i, datetime in enumerate(time_range)}

        return neeg(load_by_time, pv_production)


class SizingStrategy:
    def __init__(self, time_space_handler: TimeSpaceHandler):
        self.time_space_handler = time_space_handler

    def run(self):
        community = CommunityHousesBuilder(self.time_space_handler
                                           ).build(
            regenerate_consumption=False,
            exclude_houses=[2000926, 2000927, 2000928])

        weather_data = WeatherDataBuilder().build(
            location=self.time_space_handler.location,
            latitude_north_deg=self.time_space_handler.latitude_north_deg,
            longitude_east_deg=self.time_space_handler.longitude_east_deg,
            from_datetime_string=self.time_space_handler.start_date,
            to_datetime_string=self.time_space_handler.end_date)

        initial_neeg = Simulation(self.time_space_handler).run(
            MANAGER_TYPE.BASIC,
            weather_data,
            community,
            30,
            0.455,
            print_info=False)

        print(f"Initial NEEG: {initial_neeg:.3f}")

        bounds = [(1, 100), (0.1, 1.0), (0, 2)]  # (panels, power, manager)

        result = differential_evolution(
            self.objective_function,
            args=(self.time_space_handler, weather_data, community),
            bounds=bounds,
            workers=10,
            maxiter=10,
            popsize=30,
            disp=True,
            polish=True
        )

        optimal_panels = int(result.x[0])
        optimal_power = result.x[1]

        print(f"Optimal number of panels: {optimal_panels}")
        print(f"Optimal peak power: {optimal_power:.3f} kW")
        print(f"Optimal manager: {MANAGER_MAP[int(result.x[2])]}")
        print(f"Best NEEG: {result.fun:.3f}")

    @staticmethod
    def objective_function(x, time_space_handler: TimeSpaceHandler,
                           weather_data: weather.SiteWeatherData,
                           community: EnergyCommunity):
        number_of_panels = int(x[0])
        peak_power_kW = x[1]
        manager_type = int(x[2])

        manager = MANAGER_MAP[manager_type]

        if number_of_panels < 1 or peak_power_kW < 0.1:
            return float('inf')

        neeg_value = Simulation(time_space_handler).run(
            manager,
            weather_data,
            community,
            number_of_panels,
            peak_power_kW,
            print_info=False)

        return neeg_value


if __name__ == "__main__":

    # python batem/reno/sizing.py

    args = parse_args()

    SizingStrategy(TimeSpaceHandler(
        location=args.location,
        start_date=args.start_date,
        end_date=args.end_date)).run()
