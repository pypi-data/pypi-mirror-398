"""
Performance indicators for renewable energy systems.

This module provides functions to calculate key performance indicators (KPIs)
for renewable energy systems, particularly focusing on self-consumption and
self-sufficiency metrics.
"""

from datetime import datetime, timedelta
from dataclasses import dataclass

from batem.reno.simulation.recommendation import (
    Recommendation, RecommendationType)


def self_consumption(load_by_time: dict[datetime, float],
                     production_by_time: dict[datetime, float],
                     battery_power_by_time: dict[datetime, float] = {}
                     ) -> float:
    """
    Calculate the self-consumption ratio of a house.

    The self-consumption ratio represents the proportion of locally produced
    energy that is consumed on-site. It is calculated as the ratio between
    the energy consumed from local production and the total energy produced.

    Args:
        load_by_time: Dictionary mapping timestamps to load values (kWh)
        production_by_time: Dictionary mapping timestamps to production values
            (kWh)
        battery_power_by_time: Dictionary mapping
        timestamps to battery power values

    Returns:
        float: Self-consumption ratio between 0 and 1
    Example:
        >>> load = {datetime(2023, 1, 1, 12): 2.0}
        >>> prod = {datetime(2023, 1, 1, 12): 3.0}
        >>> self_consumption(load, prod)
        0.6666666666666666
    """

    if len(production_by_time) == 0:
        print("warning: production_by_time is empty")
        return 0

    self_consumption = 0
    total_production = sum(production_by_time.values())
    if total_production == 0:
        print("warning: total_production is 0")
        return 0

    for timestamp, load in load_by_time.items():
        battery_power = battery_power_by_time.get(timestamp, 0)
        production = production_by_time[timestamp]
        self_consumption += min(load - battery_power, production)

    return self_consumption / total_production


def self_sufficiency(load_by_time: dict[datetime, float],
                     production_by_time: dict[datetime, float],
                     battery_power_by_time: dict[datetime, float] = {}
                     ) -> float:
    """
    Calculate the self-sufficiency ratio of a house.

    The self-sufficiency ratio represents the proportion of energy demand
    that is met by local production. It is calculated as the ratio between
    the energy consumed from local production and the total energy demand.

    Args:
        load_by_time: Dictionary mapping timestamps to load values (kWh)
        production_by_time: Dictionary mapping timestamps to production values
            (kWh)
        battery_power_by_time: Dictionary mapping timestamps
        to battery power values (kWh)

    Returns:
        float: Self-sufficiency ratio between 0 and 1
    Example:
        >>> load = {datetime(2023, 1, 1, 12): 2.0}
        >>> prod = {datetime(2023, 1, 1, 12): 3.0}
        >>> self_sufficiency(load, prod)
        1.0
    """

    if len(production_by_time) == 0:
        print("warning: production_by_time is empty")
        return 0

    if len(load_by_time) == 0:
        print("warning: load_by_time is empty")
        return 0

    self_consumption = 0
    total_consumption = sum(load_by_time.values())
    if total_consumption == 0:
        print("warning: total_consumption is 0")
        return 0

    for timestamp, load in load_by_time.items():
        battery_power = battery_power_by_time.get(timestamp, 0)
        production = production_by_time[timestamp]
        self_consumption += min(load - battery_power, production)

    return self_consumption / total_consumption


def neeg(load_by_time: dict[datetime, float],
         production_by_time: dict[datetime, float],
         battery_power_by_time: dict[datetime, float] = {}) -> float:
    """
    Calculate net energy exchanged with the grid.

    Args:
        load_by_time: Dictionary mapping timestamps to load values (kWh)
        production_by_time: Dictionary mapping timestamps to production values
            (kWh)
        battery_power_by_time: Dictionary mapping timestamps to
        battery power values (kWh)
            (kWh)
    Returns:
        float: Net energy exchanged with the grid (kWh)
    """
    net_energy_exchanged = 0
    for timestamp, load in load_by_time.items():
        battery_power = battery_power_by_time.get(timestamp, 0)
        production = production_by_time[timestamp]
        net_energy_exchanged += abs(production - load + battery_power)
    return net_energy_exchanged


def demanded_contribution(
        recommendations_by_time: dict[datetime, Recommendation],
        recommendation_interval: list[int]) -> float:
    """
    Calculate the demanded contribution of a house.

    The demanded contribution is the ration between the number of
    recommendations different then None
    and the total number of recommendations,
    but only during the recommendation interval.
    """
    if len(recommendations_by_time) == 0:
        return 0

    ccr = 0
    valid_hours = 0
    for timestamp, recommendation in recommendations_by_time.items():
        if (timestamp.hour >= recommendation_interval[0] and
                timestamp.hour <= recommendation_interval[1]):
            valid_hours += 1
            if RecommendationType(recommendation) != RecommendationType.NONE:
                ccr += 1

    return ccr / valid_hours


def cost(consumption_by_time: dict[datetime, float],
         production_by_time: dict[datetime, float],
         tariff_per_extracted_kWh: float = 0.2,
         tariff_per_injected_kWh: float = 0.1,
         battery_power_by_time: dict[datetime, float] = {}) -> float:
    """
    Calculate the cost of energy for the respective period,
    considering a fixed tariff for extracted energy
    and a fixed tariff for injected energy.

    Args:
        consumption_by_time: Dictionary mapping timestamps
            to consumption values (kWh)
        production_by_time: Dictionary mapping timestamps
            to production values (kWh)
        tariff_per_extracted_kWh: Tariff for extracted energy (€/kWh)
        tariff_per_injected_kWh: Tariff for injected energy (€/kWh)

    Returns:
        float: Total cost in euros (negative values indicate profit)
    """

    total_cost = 0
    for timestamp, consumption in consumption_by_time.items():
        production = production_by_time[timestamp]
        battery_power = battery_power_by_time.get(timestamp, 0)

        if battery_power > 0:
            charge_energy = 0
            discharge_energy = battery_power
        else:
            charge_energy = - battery_power
            discharge_energy = 0

        if production > consumption:
            injected_energy = production - consumption - charge_energy
            total_cost -= injected_energy * tariff_per_injected_kWh
        else:
            extracted_energy = consumption - production - discharge_energy
            total_cost += extracted_energy * tariff_per_extracted_kWh
    return total_cost


def savings_per_day(exp_consumption_by_time: dict[datetime, float],
                    sim_consumption_by_time: dict[datetime, float],
                    exp_production_by_time: dict[datetime, float],
                    days_in_period: int = 365,
                    tariff_per_extracted_kWh: float = 0.2,
                    tariff_per_injected_kWh: float = 0.1) -> float:
    """
    Calculate the savings per day of a house,
    considering a fixed tariff for extracted energy
    and a fixed tariff for injected energy.

    Args:
        exp_consumption_by_time: Dictionary mapping timestamps
            to consumption values (kWh)
        sim_consumption_by_time: Dictionary mapping timestamps
            to consumption values (kWh)
        exp_production_by_time: Dictionary mapping timestamps
            to production values (kWh)
        days_in_period: Number of days in the period (default: 365)
        tariff_per_extracted_kWh: Tariff for extracted energy (€/kWh)
        tariff_per_injected_kWh: Tariff for injected energy (€/kWh)

    Returns:
        float: Daily savings in euros


    """
    if (len(exp_consumption_by_time) != len(sim_consumption_by_time) or
            len(exp_consumption_by_time) != len(exp_production_by_time)):
        msg = (
            "All input dictionaries must have the same length: "
            f"{len(exp_consumption_by_time)} != "
            f"{len(sim_consumption_by_time)} != "
            f"{len(exp_production_by_time)}"
        )
        raise ValueError(msg)

    if days_in_period == 0:
        raise ValueError("days_in_period cannot be 0")

    exp_cost = cost(exp_consumption_by_time, exp_production_by_time,
                    tariff_per_extracted_kWh, tariff_per_injected_kWh)
    sim_cost = cost(sim_consumption_by_time, exp_production_by_time,
                    tariff_per_extracted_kWh, tariff_per_injected_kWh)
    return (exp_cost - sim_cost) / days_in_period


def recommendations_per_day(
        recommendations_by_time: dict[datetime, RecommendationType],
        recommendation_interval: list[int] = [7, 22],
        days_in_period: int = 365) -> float:
    """
    Calculate the number of unique recommendation groups per day.

    Args:
        recommendations_by_time: Dictionary
        mapping timestamps to recommendations. Assumed to be sorted by
        timestamp.
        recommendation_interval: List of [start_hour, end_hour] for valid hours
        days_in_period: Number of days in the period (default: 365)

    Returns:
        float: Average number of unique recommendation groups per day
    """
    if len(recommendations_by_time) == 0:
        return 0

    recommendation_per_day_list = []
    current_day_groups = set()  # Track unique groups for current day
    current_recommendation = None
    group_start_time = None

    for timestamp, recommendation in recommendations_by_time.items():
        # Reset counters at the start of each day
        if timestamp.hour == 0:
            if current_day_groups:  # Add the last group if exists
                current_day_groups.add(
                    (current_recommendation, group_start_time))
            recommendation_per_day_list.append(len(current_day_groups))
            current_day_groups = set()
            current_recommendation = None
            group_start_time = None
            continue

        # Skip if outside recommendation interval
        if not (timestamp.hour >= recommendation_interval[0] and
                timestamp.hour <= recommendation_interval[1]):
            continue

        # Skip NONE recommendations
        current_recommendation = RecommendationType(recommendation)
        if current_recommendation == RecommendationType.NONE:
            continue

        # If this is the first recommendation of the day
        if group_start_time is None:
            group_start_time = timestamp
            current_recommendation = recommendation
            continue

        # Check if recommendation changed
        previous_timestamp = timestamp - timedelta(hours=1)
        previous_recommendation = recommendations_by_time[previous_timestamp]

        if previous_recommendation != current_recommendation:
            # Add the completed group
            current_day_groups.add((previous_recommendation, group_start_time))
            # Start new group
            group_start_time = timestamp
            current_recommendation = recommendation

    # Add the last group of the last day
    if current_recommendation is not None and group_start_time is not None:
        current_day_groups.add((current_recommendation, group_start_time))
        recommendation_per_day_list.append(len(current_day_groups))

    if len(recommendation_per_day_list) == 0:
        return 0

    return sum(recommendation_per_day_list) / len(recommendation_per_day_list)


def battery_protection(battery_soc_by_time: dict[datetime, float]) -> float:
    """
    Calculate the battery protection indicator as the ratio of the
    hours in which the battery soc is greater than 0.2
    and less than 0.8 relative to the total number of hours.
    """
    return sum(1 for soc in battery_soc_by_time.values()
               if soc > 0.2 and soc < 0.8) / len(battery_soc_by_time)


def avg_battery_variation(soc_by_time: dict[datetime, float],
                          ) -> float:
    """
    Calculate the average battery variation as the ratio of the
    battery soc.
    """
    return sum(soc_by_time.values()) / len(soc_by_time)


@dataclass
class BasicIndicators:
    neeg_value: float
    sc_value: float
    ss_value: float
    opex_cost_value: float


@dataclass
class BatteryIndicators:
    basic_indicators: BasicIndicators
    battery_protection_value: float
    battery_variation_value: float


if __name__ == "__main__":

    # python batem/reno/indicators.py

    recommendations_by_time = {
        datetime(2023, 1, 1, 6): RecommendationType.NONE,
        datetime(2023, 1, 1, 7): RecommendationType.DECREASE,
        datetime(2023, 1, 1, 8): RecommendationType.INCREASE,
        datetime(2023, 1, 1, 9): RecommendationType.DECREASE,
        datetime(2023, 1, 1, 10): RecommendationType.INCREASE,
        datetime(2023, 1, 1, 11): RecommendationType.NONE,
        datetime(2023, 1, 1, 12): RecommendationType.INCREASE,
        datetime(2023, 1, 1, 13): RecommendationType.NONE,
        datetime(2023, 1, 1, 14): RecommendationType.INCREASE,
        datetime(2023, 1, 1, 15): RecommendationType.INCREASE,
        datetime(2023, 1, 1, 16): RecommendationType.NONE,
        datetime(2023, 1, 1, 17): RecommendationType.INCREASE,
        datetime(2023, 1, 1, 18): RecommendationType.INCREASE,
        datetime(2023, 1, 1, 19): RecommendationType.NONE,
        datetime(2023, 1, 1, 20): RecommendationType.INCREASE,
        datetime(2023, 1, 1, 21): RecommendationType.NONE,
        datetime(2023, 1, 1, 22): RecommendationType.NONE,
        datetime(2023, 1, 1, 23): RecommendationType.NONE,
        datetime(2023, 1, 2, 0): RecommendationType.NONE,
    }
    print(recommendations_per_day(
        recommendations_by_time, [7, 22]))
