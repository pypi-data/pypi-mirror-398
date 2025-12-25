

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import sqrt
import os
import random


from batem.reno.experiment import Experiment
from batem.reno.house.creation import HouseFilePathBuilder
from batem.reno.house.model import House, TimeRange
from batem.reno.indicators.models import (
    BasicIndicators,
    BatteryIndicators, avg_battery_variation,
    battery_protection, cost, neeg,
    self_consumption, self_sufficiency
)
from batem.reno.pv.creation import PVPlantFilePathBuilder
from batem.reno.pv.model import PVPlant
from batem.reno.utils import FilePathBuilder


@dataclass
class BatteryConfig:
    """
    The config is the battery configuration.
    The capacity_kWh is the capacity of the battery in kWh.
    The max_discharge_power_kW is the maximum discharge power for a time step
    of the battery in kW.
    The max_charge_power_kW is the maximum charge power for a time step
    of the battery in kW.
    The round_trip_efficiency is the efficiency of the battery.
    """
    capacity_kWh: float
    max_discharge_power_kW: float
    max_charge_power_kW: float
    round_trip_efficiency: float


class Command(Enum):
    charge = 2
    discharge = 0
    do_nothing = 1


@dataclass
class BatteryState:
    """
    The state of the battery at a given time step.

    The timestamp is the current time step.
    The soc is the state of charge of the battery.
    The power is the power of the battery in kW.
    The command is the command of the battery (charge, discharge, do_nothing).
    """
    timestamp: datetime
    soc: float
    power: float
    command: Command


class Season(Enum):
    winter = "winter"
    spring = "spring"
    summer = "summer"
    autumn = "autumn"


class Strategy(ABC):

    def __init__(self, config: BatteryConfig):
        self._config = config
        self.name = self.__class__.__name__

    @abstractmethod
    def apply(self,
              hour: int,
              season: Season,
              consumption_kW: float,
              production_kW: float
              ) -> tuple[Command, float]:
        """
        Applies a strategy to determine what command and how much power to
        extract or inject into the battery.

        Args:
            hour: The hour of the day
            season: The season
            consumption_kW: The consumption power in kW
            production_kW: The production power in kW

        Returns:
        tuple[Command, float]: The command and the power to
        extract or inject into the battery

        Example:
            >>> command, power = battery._apply_strategy(10, Season.winter,
            20, 30)
            >>> print(command, power)
            >>> Command.charge, 10
        """
        pass


class NaiveStrategy(Strategy):
    def __init__(self, config: BatteryConfig):
        super().__init__(config)
        self.name = "NaiveStrategy"

    def apply(self, hour: int, season: Season,
              consumption_kW: float,
              production_kW: float
              ) -> tuple[Command, float]:

        required_power = consumption_kW - production_kW

        if required_power > 0:
            # if consumption is greater than production,
            # then we need to draw positive power from the battery
            return (Command.discharge, required_power)
        elif required_power < 0:
            # if consumption is less than production,
            # then we need to charge negative power into the battery
            return (Command.charge, required_power)
        else:
            return Command.do_nothing, 0


class PeriodIdentifier:
    def __init__(self):
        pass

    def is_night(self, hour: int) -> bool:
        return hour >= 0 and hour <= 8

    def is_day(self, hour: int) -> bool:
        return hour >= 8 and hour <= 16


class InactiveNightStrategy(Strategy):
    def __init__(self, config: BatteryConfig):
        super().__init__(config)
        self.name = "InactiveNightStrategy"
        self._naive_strategy = NaiveStrategy(config)
        self._period_identifier = PeriodIdentifier()

    def apply(self, hour: int, season: Season,
              consumption_kW: float,
              production_kW: float
              ) -> tuple[Command, float]:

        if self._period_identifier.is_night(hour):
            return Command.do_nothing, 0
        else:
            return self._naive_strategy.apply(hour,
                                              season,
                                              consumption_kW,
                                              production_kW)


class PeriodsStrategy(Strategy):
    def __init__(self, config: BatteryConfig):
        super().__init__(config)
        self.name = "PeriodsStrategy"
        self._inactive_strategy = InactiveNightStrategy(config)
        self._period_identifier = PeriodIdentifier()

    def apply(self, hour: int, season: Season,
              consumption_kW: float,
              production_kW: float
              ) -> tuple[Command, float]:

        if self._period_identifier.is_night(hour):
            return self._inactive_strategy.apply(hour,
                                                 season,
                                                 consumption_kW,
                                                 production_kW)
        else:
            if self._period_identifier.is_day(hour):
                if production_kW > consumption_kW:
                    # if production is greater than consumption,
                    # then we charge the battery with half of the surplus
                    # and the other half we inject into the grid
                    surplus = production_kW - consumption_kW
                    # we keep the negative sign
                    # to follow the convention
                    return (Command.charge, (-1) * surplus/2)
                else:
                    # if consumption is greater than production,
                    # then we discharge the battery and try to cover
                    # the deficit
                    # if the battery is not enough to cover the deficit,
                    # then we extract the remaining deficit from the grid
                    deficit = consumption_kW - production_kW
                    return (Command.discharge, deficit)
            else:
                # if we are in the 3rd period of the day, don't use the battery
                # TODO: consider a different solution
                return Command.do_nothing, 0


class SeasonsStrategy(Strategy):
    def __init__(self, config: BatteryConfig):
        super().__init__(config)
        self.name = "SeasonsStrategy"
        self._naive_strategy = NaiveStrategy(config)

    def apply(self, hour: int, season: Season,
              consumption_kW: float,
              production_kW: float
              ) -> tuple[Command, float]:

        if season == Season.winter or season == Season.spring:
            return self._naive_strategy.apply(hour,
                                              season,
                                              consumption_kW,
                                              production_kW)
        else:
            return self._calculate_seasonal_command_and_power(
                consumption_kW,
                production_kW)

    def _calculate_seasonal_command_and_power(
        self,
        consumption_kW: float,
        production_kW: float
    ) -> tuple[Command, float]:
        if production_kW > consumption_kW:
            # if production is greater than consumption,
            # then we charge the battery with 70% of the surplus
            # and the other 30% we inject into the grid
            surplus = production_kW - consumption_kW
            # we keep the negative sign
            # to follow the convention
            return (Command.charge, (-1) * 0.3 * surplus)
        else:
            # if consumption is greater than production,
            # then we discharge the battery and try to cover
            # the deficit
            # if the battery is not enough to cover the deficit,
            # then we extract the remaining deficit from the grid
            deficit = consumption_kW - production_kW
            return (Command.discharge, deficit)


class BPINaiveStrategy(Strategy):
    def __init__(self, config: BatteryConfig):
        super().__init__(config)
        self.name = "BPINaiveStrategy"
        self._naive_strategy = NaiveStrategy(config)

    def apply(self, hour: int, season: Season,
              consumption_kW: float,
              production_kW: float
              ) -> tuple[Command, float]:

        if production_kW > 1.2 * consumption_kW:
            return self._naive_strategy.apply(hour,
                                              season,
                                              consumption_kW,
                                              production_kW)
        elif production_kW < 0.8 * consumption_kW:
            return self._naive_strategy.apply(hour,
                                              season,
                                              consumption_kW,
                                              production_kW)
        else:
            return Command.do_nothing, 0


@dataclass
class Case:
    battery_state: BatteryState
    command: Command
    load: float
    production: float
    indicators_until_now: BatteryIndicators


class Phases(Enum):
    learning = "learning"
    case_based_reasoning = "case_based_reasoning"


class CaseBasedReasoningStrategy(Strategy):
    def __init__(self, config: BatteryConfig, phase: Phases):
        super().__init__(config)
        self.name = "CaseBasedReasoningStrategy"
        self._phase = phase
        self._other_strategies = [NaiveStrategy(config),
                                  InactiveNightStrategy(config),
                                  PeriodsStrategy(config),
                                  SeasonsStrategy(config)]
        self._cases: list[Case] = []
        self._current_soc = 0.8  # Default initial SOC

    def update_current_soc(self, soc: float):
        """Update the current SOC for case similarity calculations."""
        self._current_soc = soc

    def apply(self, hour: int, season: Season,
              consumption_kW: float,
              production_kW: float
              ) -> tuple[Command, float]:
        if self._phase == Phases.learning:
            # in the learning phase, we randomly choose a strategy
            # to apply
            random_strategy = random.choice(self._other_strategies)
            return random_strategy.apply(hour, season, consumption_kW,
                                         production_kW)
        else:
            closest_cases_indeces = self._get_top_10_closest_cases_indeces(
                hour, season, consumption_kW, production_kW)

            # Get the cases following right after the closest cases
            # Note: We need to get the NEXT cases, not the same ones
            following_cases = []
            for index in closest_cases_indeces:
                if index + 1 < len(self._cases):
                    following_cases.append(self._cases[index + 1])

            if not following_cases:
                # Fallback to naive strategy if no following cases available
                return NaiveStrategy(self._config).apply(
                    hour, season, consumption_kW, production_kW)

            command_and_score = [(following_case.command,
                                  self._composite_score(self._cases[closest_case_index], following_case))
                                 for following_case, closest_case_index
                                 in zip(following_cases, closest_cases_indeces)]

            # print("Current soc, load and production: ",
            #      self._current_soc, consumption_kW, production_kW)
            # print("Most similar cases: ", closest_cases_indeces)
            # print("Following cases: ", following_cases)
            # print("Command and score: ", command_and_score)

            # We choose the command that maximizes the composite score
            command, score = max(command_and_score, key=lambda x: x[1])
            required_power = consumption_kW - production_kW
            return command, required_power

    def _composite_score(self, current_case: Case, following_case: Case) -> float:
        """
        Calculate the composite score of a case.
        Higher score means better performance.
        """
        next_indicators = following_case.indicators_until_now
        current_indicators = current_case.indicators_until_now

        if next_indicators.basic_indicators.neeg_value < current_indicators.basic_indicators.neeg_value:
            neeg_change = 1
        else:
            neeg_change = 0

        if next_indicators.battery_protection_value > current_indicators.battery_protection_value:
            battery_protection_change = 1
        else:
            battery_protection_change = 0

        # Define weights (sum should = 1.0)
        w_battery = 0      # Battery protection weight
        w_neeg = 1         # NEEG weight (lower is better)

        return (w_neeg * neeg_change + w_battery * battery_protection_change)

    def _get_top_10_closest_cases_indeces(
            self, hour: int, season: Season,
            consumption_kW: float, production_kW: float) -> list[int]:
        """
        Get the top 10 closest cases to the current state.
        """

        # Calculate the distance for each case and sort them
        cases_with_distance = []
        for case in self._cases:
            distance = self._calculate_distance(
                case, hour, season, consumption_kW, production_kW,
                self._current_soc)
            cases_with_distance.append((distance, case))
        # Sort by distance
        cases_with_distance.sort(key=lambda x: x[0])
        # Get the top 10 closest cases
        closest_cases = [case for _, case in cases_with_distance[:10]]
        closest_cases_indeces = [self._cases.index(
            case) for case in closest_cases]
        return closest_cases_indeces

    def _calculate_distance(self, case: Case, hour: int, season: Season,
                            consumption_now_kW: float, production_kW: float,
                            current_soc: float) -> float:
        """
        Calculate the weighted Euclidean distance between a case and the
        current state, using hour, season, consumption (load),
        production, and soc.
        Uses normalized weights to account for different scales.
        """
        # Normalize SOC difference (SOC is 0-1 range)
        soc_diff = abs(case.battery_state.soc - current_soc)

        # Normalize production difference (assuming max production ~5kW)
        production_diff = abs(case.production - production_kW) / 5.0

        # Normalize consumption difference (assuming max consumption ~3kW)
        consumption_diff = abs(case.load - consumption_now_kW) / 3.0

        # Hour difference (0-23 range, normalize to 0-1)
        hour_diff = abs(case.battery_state.timestamp.hour - hour) / 24.0

        # Season difference (binary: same season = 0, different season = 1)
        case_season = self._get_season_from_month(
            case.battery_state.timestamp.month)
        season_diff = 0 if case_season == season else 1

        # Weighted Euclidean distance with time factors
        return sqrt(soc_diff**2 + production_diff**2 + consumption_diff**2 +
                    (hour_diff * 0.1)**2 + (season_diff * 0.2)**2)

    def _get_season_from_month(self, month: int) -> Season:
        """Get season from month number."""
        if month >= 1 and month <= 3:
            return Season.winter
        elif month >= 4 and month <= 6:
            return Season.spring
        elif month >= 7 and month <= 9:
            return Season.summer
        else:
            return Season.autumn


class Battery:

    def __init__(self, experiment: 'BatterySimulationExperiment',
                 strategy: Strategy, config: BatteryConfig,
                 init_soc: float = 0.8):
        """
        The config is the battery configuration.
        The init_soc is the initial state of charge of the battery.
        We initialize the soc with the initial soc
        The time step is one hour and is kept in variable k
        """
        self._state = BatteryState(
            timestamp=datetime.now(),
            soc=init_soc,
            power=0.0,
            command=Command.do_nothing)
        self._power_calculator = BatteryPowerCalculator(self)
        self._state_history: list[BatteryState] = []
        self._k = 0
        self.config = config
        self._strategy = strategy

        # We assume that the charge efficiency is equal
        # to the discharge efficiency
        self.charge_efficiency = sqrt(config.round_trip_efficiency)
        self.discharge_efficiency = sqrt(
            config.round_trip_efficiency)

    def step(self, timestamp: datetime,
             consumption_kW: float, production_kW: float):
        """
        Execute a single step of the battery, meaning that we
        apply the strategy to determine the command and the power
        to assign to the battery, and then we update the state of the battery.

        Args:
            timestamp: The timestamp of the step
            consumption_kW: The consumption power in kW
            production_kW: The production power in kW
        """

        self._k += 1

        season = self._get_season(timestamp)

        command, power = self._strategy.apply(
            hour=timestamp.hour,
            season=season,
            consumption_kW=consumption_kW,
            production_kW=production_kW)

        battery_power = self._power_calculator.get_battery_power(
            command, power)

        new_soc = self._state.soc - (battery_power/self.config.capacity_kWh)

        self._state = BatteryState(
            timestamp=timestamp,
            soc=new_soc,
            power=battery_power,
            command=command)

        self._state_history.append(self._state)

    def _get_season(self, timestamp: datetime) -> Season:
        """
        Get the season of the timestamp.
        """
        if timestamp.month >= 1 and timestamp.month <= 3:
            return Season.winter
        elif timestamp.month >= 4 and timestamp.month <= 6:
            return Season.spring
        elif timestamp.month >= 7 and timestamp.month <= 9:
            return Season.summer
        else:
            return Season.autumn

    def get_current_soc(self) -> float:
        """
        Get the current state of charge of the battery.
        """
        return self._state.soc

    def get_battery_power_by_time(self) -> dict[datetime, float]:
        """
        Get the battery power by time.
        """
        return {state.timestamp: state.power for state in self._state_history}

    def get_battery_soc_by_time(self) -> dict[datetime, float]:
        """
        Get the battery soc by time.
        """
        return {state.timestamp: state.soc for state in self._state_history}


class BatteryPowerCalculator:

    def __init__(self, battery: Battery) -> None:
        self._battery = battery

    def get_battery_power(self, command: Command, assigned_power_kW: float):
        """
        Get the battery power after taking into account:
        - the efficiency
        - the max power that the battery can handle
        - the max capacity of the battery
        - the state of charge of the battery

        Args:
            command: The command to apply
            assigned_power_kW: The power to assign to the battery

        Returns:
            The battery power expressed in kW
        """

        if command == Command.charge:
            if self._battery.get_current_soc() >= 0.95:
                return 0
            return self._calculate_charge_power(assigned_power_kW)
        elif command == Command.discharge:
            if self._battery.get_current_soc() <= 0.05:
                return 0
            return self._calculate_discharge_power(assigned_power_kW)
        else:
            return 0

    def _calculate_charge_power(self, assigned_power_kW: float) -> float:
        """
        Calculate the charge power after taking into account the efficiency
        and the max power that the battery can handle.
        """
        # Determine how much power we can actually charge
        # into the battery after taking into account the efficiency
        # and consideering the total capacity of the battery
        power_after_efficiency = (assigned_power_kW *
                                  self._battery.charge_efficiency)
        max_admissible_power = ((1 - self._battery.get_current_soc())
                                * self._battery.config.capacity_kWh
                                * self._battery.charge_efficiency)

        # Determine how much power we can actually charge
        # into the battery after considering the max power
        # that the battery can handle
        limited_power = max(power_after_efficiency,
                            -1 * max_admissible_power,
                            -1 * self._battery.config.max_charge_power_kW)
        return limited_power

    def _calculate_discharge_power(self, assigned_power_kW: float) -> float:
        """
        Calculate the discharge power after taking into account the efficiency
        and the max power that the battery can handle.
        """
        # Determine how much power we can actually discharge
        # from the battery after taking into account the efficiency
        # and consideering the total capacity of the battery
        power_after_efficiency = (assigned_power_kW /
                                  self._battery.discharge_efficiency)

        remaining_capacity = (
            self._battery.get_current_soc()
            * self._battery.config.capacity_kWh
            / self._battery.discharge_efficiency)

        # Determine how much power we can actually discharge
        # from the battery after considering the max power
        # that the battery can handle
        limited_power = min(power_after_efficiency,
                            remaining_capacity,
                            self._battery.config.max_discharge_power_kW)
        return limited_power


@dataclass
class BatterySimulationResult:
    """
    This represents the result of the battery simulation.

    The battery is the battery model.
    The house is the house model.
    The pv_plant is the pv plant model.
    The initial_indicators are the indicators before the simulation.
    The final_indicators are the indicators after the simulation.
    """
    battery: Battery
    house: House
    pv_plant: PVPlant
    initial_indicators: BasicIndicators
    final_indicators: BatteryIndicators


class BatterySimulationExperiment(Experiment):
    """
    This represents the experiment of the battery simulation.
    """

    def __init__(self, name: str,
                 battery_config: BatteryConfig,
                 house: House,
                 pv_plant: PVPlant):
        super().__init__(name)
        self.battery_capacity_kWh = battery_config.capacity_kWh
        self.house = house
        self.pv_plant = pv_plant


class BatteryFilePathBuilder:
    """
    This class builds the paths to the battery simulation results.
    """

    def __init__(self):
        self.file_path_builder = FilePathBuilder()
        self.house_path_builder = HouseFilePathBuilder()
        self.pv_plant_path_builder = PVPlantFilePathBuilder()

    def get_cases_path(self, experiment: BatterySimulationExperiment) -> str:
        """
        Get the path to the cases file.
        """
        folder = self.file_path_builder.get_experiment_folder(experiment)
        file_name = f"cases_{experiment.name}.csv"
        return os.path.join(folder, file_name)


class CaseRepository:
    def __init__(self,
                 experiment: BatterySimulationExperiment,
                 house: House,
                 pv_plant: PVPlant):
        self._experiment = experiment
        self._house = house
        self._pv_plant = pv_plant
        self._case_builder = CaseBuilder()

    def export_cases(self, battery: 'Battery'):
        """
        Export the cases to a CSV file.
        """
        import csv

        cases = self._case_builder.build_cases_from_sim(
            battery=battery,
            house=self._house,
            pv_plant=self._pv_plant)

        if not cases:
            raise ValueError("No cases to export.")

        file_path = BatteryFilePathBuilder().get_cases_path(self._experiment)

        fieldnames = [
            "timestamp",
            "command",
            "battery_power",
            "soc",
            "load",
            "production",
            "neeg_value",
            "sc_value",
            "ss_value",
            "opex_cost_value",
            "battery_protection_value",
            "battery_variation_value"
        ]

        with open(file_path, mode="w", newline="", encoding="utf-8"
                  ) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for case in cases:
                indicators = case.indicators_until_now
                battery = case.indicators_until_now.battery_protection_value
                writer.writerow({
                    "timestamp": case.battery_state.timestamp.isoformat(),
                    "command": case.battery_state.command.name,
                    "battery_power": case.battery_state.power,
                    "load": case.load,
                    "production": case.production,
                    "soc": case.battery_state.soc,
                    "neeg_value": indicators.basic_indicators.neeg_value,
                    "sc_value": indicators.basic_indicators.sc_value,
                    "ss_value": indicators.basic_indicators.ss_value,
                    "opex_cost_value": indicators.basic_indicators.opex_cost_value,
                    "battery_protection_value": battery,
                    "battery_variation_value": indicators.battery_variation_value
                })

    def load_cases(self) -> list[Case]:
        """
        Load the cases from a CSV file.
        """
        import csv
        cases = []
        file_path = BatteryFilePathBuilder().get_cases_path(self._experiment)
        with open(file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                case = Case(
                    battery_state=BatteryState(
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        command=Command[row["command"]],
                        power=float(row["battery_power"]),
                        soc=float(row["soc"])),
                    command=Command[row["command"]],
                    load=float(row["load"]),
                    production=float(row["production"]),
                    indicators_until_now=BatteryIndicators(
                        BasicIndicators(
                            neeg_value=float(row["neeg_value"]),
                            sc_value=float(row["sc_value"]),
                            ss_value=float(row["ss_value"]),
                            opex_cost_value=float(row["opex_cost_value"])),
                        battery_protection_value=float(
                            row["battery_protection_value"]),
                        battery_variation_value=float(
                            row["battery_variation_value"]))
                )
                cases.append(case)
        return cases


class CaseBuilder:
    def __init__(self):
        pass

    def build_cases_from_sim(self,
                             battery: Battery,
                             house: House,
                             pv_plant: PVPlant) -> list[Case]:
        cases = []
        if not house.consumption.usage_hourly:
            raise ValueError("Load by time is not set")
        load_in_time = house.consumption.usage_hourly
        production_in_time = pv_plant.production.usage_hourly
        battery_power_in_time = battery.get_battery_power_by_time()
        battery_soc_in_time = battery.get_battery_soc_by_time()

        for i, state in enumerate(battery._state_history):
            indicators = self._calculate_indicators_until_current_timestamp(
                time_range=house.time_range,
                current_time=state.timestamp,
                load_in_time=load_in_time,
                production_in_time=production_in_time,
                battery_power_in_time=battery_power_in_time,
                battery_soc_in_time=battery_soc_in_time)

            load = load_in_time[state.timestamp]
            production = production_in_time[state.timestamp]
            case = Case(state, state.command, load, production, indicators)
            cases.append(case)
        return cases

    def _calculate_indicators_until_current_timestamp(
            self,
            time_range: TimeRange,
            current_time: datetime,
            load_in_time: dict[datetime, float],
            production_in_time: dict[datetime, float],
            battery_power_in_time: dict[datetime, float],
            battery_soc_in_time: dict[datetime, float]):
        """
        Calculate the indicators until the current timestamp.
        """

        if (not load_in_time
            or not production_in_time
                or not battery_power_in_time
                or not battery_soc_in_time):
            return BatteryIndicators(
                BasicIndicators(neeg_value=0,
                                sc_value=0,
                                ss_value=0,
                                opex_cost_value=0),
                battery_protection_value=0,
                battery_variation_value=0)

        start_time = time_range.start_time

        (load_up_to_time,
         production_up_to_time,
         battery_power_up_to_time,
         battery_soc_up_to_time) = \
            self._determine_power_until_current_timestamp(
                start_time=start_time,
                current_time=current_time,
                load_in_time=load_in_time,
                production_in_time=production_in_time,
                battery_power_in_time=battery_power_in_time,
                battery_soc_in_time=battery_soc_in_time)

        sc = self_consumption(load_up_to_time,
                              production_up_to_time,
                              battery_power_up_to_time)
        ss = self_sufficiency(load_up_to_time,
                              production_up_to_time,
                              battery_power_up_to_time)
        battery_protection_value = battery_protection(battery_soc_up_to_time)
        neeg_value = neeg(load_up_to_time,
                          production_up_to_time,
                          battery_power_up_to_time)
        opex_cost_value = cost(load_up_to_time,
                               production_up_to_time,
                               battery_power_by_time=battery_power_up_to_time)
        battery_variation_value = avg_battery_variation(battery_soc_up_to_time)

        return BatteryIndicators(
            BasicIndicators(neeg_value=neeg_value,
                            sc_value=sc,
                            ss_value=ss,
                            opex_cost_value=opex_cost_value),
            battery_protection_value=battery_protection_value,
            battery_variation_value=battery_variation_value)

    def _determine_power_until_current_timestamp(
            self,
            start_time: datetime,
            current_time: datetime,
            load_in_time: dict[datetime, float],
            production_in_time: dict[datetime, float],
            battery_power_in_time: dict[datetime, float],
            battery_soc_in_time: dict[datetime, float]
    ) -> tuple[dict[datetime, float],
               dict[datetime, float],
               dict[datetime, float],
               dict[datetime, float]]:
        """
        Determine the power until the current timestamp.
        """
        load_up_to_time = {time: load_in_time[time]
                           for time in load_in_time.keys()
                           if time >= start_time
                           and time <= current_time}
        production_up_to_time = {time: production_in_time[time]
                                 for time in production_in_time.keys()
                                 if time in load_in_time
                                 and time >= start_time
                                 and time <= current_time}
        battery_power_up_to_time = {
            time: battery_power_in_time[time]
            for time in battery_power_in_time.keys()
            if time in load_in_time and time <= current_time}
        battery_soc_up_to_time = {
            time: battery_soc_in_time[time]
            for time in battery_soc_in_time.keys()
            if time in load_in_time and time <= current_time}

        return (load_up_to_time,
                production_up_to_time,
                battery_power_up_to_time,
                battery_soc_up_to_time)
