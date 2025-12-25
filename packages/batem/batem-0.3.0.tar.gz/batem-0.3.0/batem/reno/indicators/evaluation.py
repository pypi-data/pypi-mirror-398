from typing import TYPE_CHECKING, Optional
from batem.reno.house.model import House
from batem.reno.pv.model import PVPlant

from batem.reno.indicators.models import (
    BatteryIndicators, avg_battery_variation, battery_protection, neeg,
    self_consumption, self_sufficiency,
    cost, BasicIndicators)

if TYPE_CHECKING:
    from batem.reno.battery.model import Battery


def calculate_basic_indicators(house: House, pv_plant: PVPlant,
                               battery: Optional['Battery'] = None
                               ) -> BasicIndicators:
    if not house.consumption.usage_hourly:
        raise ValueError("Consumption is not set")
    if not pv_plant.production.usage_hourly:
        raise ValueError("Production is not set")

    battery_power_by_time = (
        battery.get_battery_power_by_time() if battery else {})
    consumption_by_time = house.consumption.usage_hourly
    production_by_time = pv_plant.production.usage_hourly

    neeg_value = neeg(
        consumption_by_time,
        production_by_time,
        battery_power_by_time=battery_power_by_time)
    sc_value = self_consumption(
        consumption_by_time,
        production_by_time,
        battery_power_by_time=battery_power_by_time)
    ss_value = self_sufficiency(consumption_by_time,
                                production_by_time,
                                battery_power_by_time=battery_power_by_time)
    opex_cost_value = cost(consumption_by_time,
                           production_by_time,
                           battery_power_by_time=battery_power_by_time)

    return BasicIndicators(neeg_value, sc_value, ss_value, opex_cost_value)


def calculate_battery_indicators(house: House, pv_plant: PVPlant,
                                 battery: 'Battery'
                                 ) -> BatteryIndicators:
    basic_indicators = calculate_basic_indicators(house, pv_plant, battery)
    battery_protection_value = battery_protection(
        battery.get_battery_soc_by_time())
    battery_variation_value = avg_battery_variation(
        battery.get_battery_soc_by_time(),
    )
    battery_indicators = BatteryIndicators(
        basic_indicators=basic_indicators,
        battery_protection_value=battery_protection_value,
        battery_variation_value=battery_variation_value)

    return battery_indicators


class Printer:
    def __init__(self, indicators: BasicIndicators):
        self.indicators = indicators

    def print(self, prefix: str = ""):
        """
        Print the indicators with a prefix
        to indicate the source of the indicators.

        Args:
            prefix: Prefix to print before the indicators
        """
        print(f"{prefix}NEEG: {self.indicators.neeg_value:.3f}")
        print(f"{prefix}SC: {self.indicators.sc_value:.3f}")
        print(f"{prefix}SS: {self.indicators.ss_value:.3f}")
        print(f"{prefix}OPEX Cost: {self.indicators.opex_cost_value:.3f}")


class BatteryPrinter:
    def __init__(self, indicators: BatteryIndicators):
        self.indicators = indicators
        self._printer = Printer(indicators.basic_indicators)

    def print(self, prefix: str = ""):
        """
        Print the indicators with a prefix
        to indicate the source of the indicators.
        """
        self._printer.print(prefix)
        bpi_value = self.indicators.battery_protection_value
        avg_variation_value = self.indicators.battery_variation_value
        print(f"{prefix}Battery Protection: {bpi_value:.3f}")
        print(f"{prefix}Battery Variation: {avg_variation_value:.3f}")
