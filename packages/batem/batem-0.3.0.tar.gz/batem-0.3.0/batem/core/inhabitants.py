"""Occupant behavior and comfort assessment module for building energy analysis.

.. module:: batem.core.inhabitants

This module provides comprehensive tools for modeling occupant behavior, preferences,
and comfort assessment in building energy systems. It implements occupant preference
models that consider thermal comfort, air quality, energy costs, and behavioral
patterns to evaluate building performance from the occupant's perspective.

Classes
-------

.. autosummary::
   :toctree: generated/

   Contiguous
   Preference

Classes Description
-------------------

**Contiguous**
    Time series analysis for identifying contiguous periods of specific conditions.

**Preference**
    Comprehensive occupant preference model with comfort and cost assessment.

Key Features
------------

* Thermal comfort assessment with preferred and extreme temperature ranges
* Air quality evaluation using CO2 concentration thresholds
* Energy cost calculation with COP (Coefficient of Performance) considerations
* Occupant behavior modeling including configuration change frequency
* ICONE indicator for air quality confinement assessment
* Multi-objective optimization balancing comfort and energy costs
* Time series analysis for identifying problematic periods
* Comprehensive assessment reporting with detailed comfort metrics
* Support for different HVAC modes and their efficiency factors
* Integration with building energy simulation and control systems

The module is designed for building energy analysis, occupant comfort studies,
and building performance evaluation from the user's perspective.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""
import math
from collections.abc import Iterable
from datetime import datetime
from batem.core.timemg import datetime_to_stringdate
from batem.core.comfort import icone
import prettytable


class Contiguous:
    """Time series analysis for identifying and displaying contiguous periods of specific conditions.

    This class helps identify and analyze contiguous time periods where specific
    conditions occur (e.g., extreme temperatures, poor air quality). It provides
    methods to track time slots and generate formatted output showing the duration
    and timing of these periods.

    :param name: Name identifier for the contiguous period being tracked.
    :type name: str
    :param datetimes: List of datetime objects corresponding to the time series.
    :type datetimes: list[datetime]
    :ivar name: Name identifier for the contiguous period.
    :ivar datetimes: List of datetime objects for the time series.
    :ivar time_slots: List of time slot indices where conditions occur.
    """

    def __init__(self, name: str, datetimes: list[datetime]):
        """
        Initialize a Contiguous period tracker.

        :param name: Name identifier for the contiguous period being tracked.
        :type name: str
        :param datetimes: List of datetime objects corresponding to the time series.
        :type datetimes: list[datetime]
        """
        self.name: str = name
        self.datetimes: list[datetime] = datetimes
        self.time_slots: list[int] = list()

    def add(self, k: int) -> None:
        """Add a time slot index to the contiguous period.

        :param k: Time slot index to add.
        :type k: int
        """
        self.time_slots.append(k)

    def __str__(self) -> str:
        """Generate a string representation of contiguous periods.

        :return: Formatted string showing contiguous periods with their durations.
        :rtype: str
        """
        string: str = f"Period of {self.name}: "
        if len(self.time_slots) == 0:
            return string + "\nempty"
        k_start: int = self.time_slots[0]
        counter: int = 1
        for i in range(1, len(self.time_slots)):
            if self.time_slots[i] != k_start + counter:
                string += "\n%s (k=%i): %i hours, " % (datetime_to_stringdate(self.datetimes[k_start]), k_start, counter)
                counter = 1
                k_start = self.time_slots[i]
            else:
                counter += 1
        return string


class Preference:
    """Comprehensive occupant preference model for comfort and cost assessment.

    This class provides a complete model of occupant preferences that considers
    thermal comfort, air quality, energy costs, and behavioral patterns. It
    implements multi-objective optimization that balances comfort satisfaction
    with energy consumption costs, taking into account occupant behavior and
    system efficiency factors.

    :param preferred_temperatures: Target indoor temperature interval in degrees Celsius.
    :type preferred_temperatures: tuple[float, float]
    :param extreme_temperatures: Lower/upper bounds of tolerable temperatures in degrees Celsius.
    :type extreme_temperatures: tuple[float, float]
    :param preferred_CO2_concentration: Acceptable indoor CO₂ concentration range in ppm.
    :type preferred_CO2_concentration: tuple[float, float]
    :param temperature_weight_wrt_CO2: Weight of thermal comfort relative to air-quality comfort.
    :type temperature_weight_wrt_CO2: float
    :param power_weight_wrt_comfort: Weight of energy cost relative to combined comfort.
    :type power_weight_wrt_comfort: float
    :param sleeping_hours: Sequence of integer hours (0-23) that represent sleeping periods.
    :type sleeping_hours: Iterable[int] | None
    :param mode_cop: Mapping from HVAC mode identifiers to coefficient of performance values.
    :type mode_cop: dict[int, float]
    """

    def __init__(
        self,
        preferred_temperatures: tuple[float, float] = (20, 26),
        extreme_temperatures: tuple[float, float] = (16, 30),
        preferred_CO2_concentration: tuple[float, float] = (500, 1700),
        temperature_weight_wrt_CO2: float = 0.5,
        power_weight_wrt_comfort: float = 0.5,
        sleeping_hours: Iterable[int] | None = (23, 0, 1, 2, 3, 4, 5, 6),
        mode_cop: dict[int, float] = {},
        power_unit: str = 'Wh'
    ):
        """Initialise the preference model and configure comfort weights.

        :param preferred_temperatures: Target indoor temperature interval in degrees Celsius.
        :param extreme_temperatures: Lower/upper bounds of tolerable temperatures in degrees Celsius.
        :param preferred_CO2_concentration: Acceptable indoor CO₂ concentration range in ppm.
        :param temperature_weight_wrt_CO2: Weight of thermal comfort relative to air-quality comfort (``1`` means temperature only).
        :param power_weight_wrt_comfort: Weight of energy cost relative to combined comfort (``1`` means cost only).
        :param sleeping_hours: Sequence of integer hours (``0``–``23``) that represent sleeping periods. Thermal indicators ignore these slots while air-quality indicators still include them.
        :param mode_cop: Mapping from HVAC mode identifiers to coefficient of performance values used when translating power to energy cost.
        """
        self.preferred_temperatures = preferred_temperatures
        self.extreme_temperatures = extreme_temperatures
        self.preferred_CO2_concentration = preferred_CO2_concentration
        self.temperature_weight_wrt_CO2 = temperature_weight_wrt_CO2
        self.power_weight_wrt_comfort = power_weight_wrt_comfort
        self.mode_cop = mode_cop
        self.sleeping_hours: set[int] = {int(hour) % 24 for hour in sleeping_hours} if sleeping_hours is not None else set()
        self.power_unit: str = power_unit
        
    def change_dissatisfaction(self, occupancy: list[float], action_set: tuple[list[float]] | None = None) -> float:
        """Compute the ratio of the number of hours where occupants have to change their home configuration divided by the number of hours with presence.

        :param occupancy: A vector of occupancies indicating presence.
        :type occupancy: list[float]
        :param action_set: Different vectors of actions representing configuration changes.
        :type action_set: tuple[list[float]] | None, optional
        :return: The number of hours where occupants have to change their home configuration divided by the number of hours with presence.
        :rtype: float
        """
        number_of_changes = 0
        number_of_presences = 0
        previous_actions = [actions[0] for actions in action_set]
        for k in range(len(occupancy)):
            if occupancy[k] > 0:
                number_of_presences += 1
                for i in range(len(action_set)):
                    actions = action_set[i]
                    if actions[k] != previous_actions[i]:
                        number_of_changes += 1
                        previous_actions[i] = actions[k]
        return number_of_changes / number_of_presences if number_of_presences > 0 else 0

    def thermal_comfort_dissatisfaction(self, temperatures: list[float], occupancies: list[float], hours: Iterable[int] | None = None) -> float:
        """Compute the average thermal discomfort over occupied hours.

        :param temperatures: Hourly indoor air temperatures aligned with ``occupancies``.
        :param occupancies: Occupancy levels per hour (values ``> 0`` indicate presence).
        :param hours: Optional iterable of hour indices (``0``–``23``). When provided, entries whose hour
            is part of :attr:`sleeping_hours` are excluded from the calculation.
        :returns: Average thermal dissatisfaction score in the ``[0, +inf)`` range.
        """
        temps = list(temperatures) if isinstance(temperatures, Iterable) else [temperatures]
        occs = list(occupancies) if isinstance(occupancies, Iterable) else [occupancies]
        hrs = list(hours) if hours is not None else None
        if hrs is not None and len(hrs) != len(temps):
            raise ValueError("hours length must match temperatures length")
        if len(temps) != len(occs):
            raise ValueError("temperatures and occupancies must have the same length")

        considered_indices: list[int] = [
            i for i, occ in enumerate(occs)
            if occ and (hrs is None or hrs[i] not in self.sleeping_hours)
        ]
        if not considered_indices:
            return 0.0

        dissatisfaction = 0.0
        for i in considered_indices:
            temp = float(temps[i])
            if temp < self.preferred_temperatures[0]:
                dissatisfaction += (self.preferred_temperatures[0] - temp) / (self.preferred_temperatures[0] - self.extreme_temperatures[0])
            elif temp > self.preferred_temperatures[1]:
                dissatisfaction += (temp - self.preferred_temperatures[1]) / (self.extreme_temperatures[1] - self.preferred_temperatures[1])
        return dissatisfaction / len(considered_indices)

    def air_quality_dissatisfaction(self, CO2_concentrations: list[float], occupancies: list[float]) -> float:
        """Compute the average air-quality dissatisfaction considering occupied hours only.

        :param CO2_concentrations: Indoor CO₂ concentrations in ppm.
        :param occupancies: Occupancy levels per hour (values ``> 0`` indicate presence).
        :returns: Average dissatisfaction in the ``[0, +inf)`` range.
        """
        if type(CO2_concentrations) is not list:
            CO2_concentrations = [CO2_concentrations]
            occupancies = [occupancies]
        dissatisfaction = 0.0
        denom = (self.preferred_CO2_concentration[1] - self.preferred_CO2_concentration[0]) or 1.0
        n = 0
        for value, occupancy in zip(CO2_concentrations, occupancies):
            if occupancy:
                dissatisfaction += max(0.0, (float(value) - self.preferred_CO2_concentration[0]) / denom)
                n += 1
        return dissatisfaction / n if n else 0.0

    def comfort_dissatisfaction(self, temperatures: list[float], CO2_concentrations: list[float], occupancies: list[float], hours: list[int] = None) -> float:
        """Blend thermal and air-quality dissatisfaction into a single KPI.

        :param temperatures: Indoor temperature profile aligned with ``occupancies``.
        :param CO2_concentrations: Indoor CO₂ concentration profile.
        :param occupancies: Occupancy signal used to ignore vacant periods.
        :param hours: Optional hourly indices (``0``–``23``) to remove sleeping hours from the thermal term.
        :returns: Weighted comfort dissatisfaction value.
        """
        return (
            self.temperature_weight_wrt_CO2 * self.thermal_comfort_dissatisfaction(temperatures, occupancies, hours)
            + (1 - self.temperature_weight_wrt_CO2) * self.air_quality_dissatisfaction(CO2_concentrations, occupancies)
        )

    def daily_cost_euros(self, Pheat: list[float], modes: list[int] | None = None, kWh_price: float = 0.13, power_unit: str = 'Wh') -> float:
        """Compute the daily heating cost in euros.

        :param Pheat: List of heating power consumptions in watts.
        :type Pheat: list[float]
        :param modes: Optional list of HVAC mode identifiers for COP-aware cost calculation.
        :type modes: list[int] | None, optional
        :param kWh_price: Tariff per kWh in euros, defaults to 0.13.
        :type kWh_price: float, optional
        :return: Daily energy cost in euros.
        :rtype: float
        """
        needed_energy_Wh = 0.0
        for k in range(len(Pheat)):
            if modes is not None and modes[k] != 0 and modes[k] in self.mode_cop:
                needed_energy_Wh += float(abs(Pheat[k])) / float(self.mode_cop[modes[k]])
            else:  # consider a COP = 1
                needed_energy_Wh += float(abs(Pheat[k]))
            # else:
            #     cost_Wh = sum(Pheat)
        if power_unit == 'Wh':
            return float(24 * needed_energy_Wh / len(Pheat) / 1000 * float(kWh_price))
        elif power_unit == 'kWh':
            return float(24 * needed_energy_Wh / len(Pheat) * float(kWh_price))
        else:
            raise ValueError(f"Invalid power unit: {power_unit}")

    def icone(self, CO2_concentration: list[float], occupancy: list[float]) -> float:
        """Compute the ICONE indicator dealing with confinement regarding air quality.

        The ICONE (Indicateur de Confinement) is a metric that evaluates air quality
        confinement based on CO2 concentration levels during occupied periods.

        :param CO2_concentration: List of CO2 concentrations in ppm.
        :type CO2_concentration: list[float]
        :param occupancy: List of occupancies indicating presence.
        :type occupancy: list[float]
        :return: ICONE value between 0 and 5, where higher values indicate worse confinement.
        :rtype: float
        """
        n_presence = 0
        n1_medium_containment = 0
        n2_high_containment = 0
        for k in range(len(occupancy)):
            if occupancy[k] > 0:
                n_presence += 1
                if 1000 <= CO2_concentration[k] < 1700:
                    n1_medium_containment += 1
                elif CO2_concentration[k] >= 1700:
                    n2_high_containment += 1
        f1 = n1_medium_containment / n_presence if n_presence > 0 else 0
        f2 = n2_high_containment / n_presence if n_presence > 0 else 0
        return 8.3 * math.log10(1 + f1 + 3 * f2)

    def assess(self, Pheater: list[float], temperatures: list[float], CO2_concentrations: list[float], occupancies: tuple[list[float]], hours: list[int] | None = None, modes: list[float] | None = None, power_unit: str = 'Wh') -> float:
        """Evaluate the aggregated objective combining comfort and energy cost.

        :param Pheater: Thermal power time series supplied by the HVAC system in watts.
        :type Pheater: list[float]
        :param temperatures: Indoor temperature time series in degrees Celsius.
        :type temperatures: list[float]
        :param CO2_concentrations: Indoor CO₂ concentration time series in ppm.
        :type CO2_concentrations: list[float]
        :param occupancies: Occupancy profiles aligned with temperatures.
        :type occupancies: tuple[list[float]]
        :param hours: Optional hourly indices to pass to thermal_comfort_dissatisfaction.
        :type hours: list[int] | None, optional
        :param modes: HVAC operating modes used to determine the effective COP when computing energy cost.
        :type modes: list[float] | None, optional
        :return: Scalar objective value (lower is better).
        :rtype: float
        """
        return (
            self.daily_cost_euros(Pheater, modes, power_unit=power_unit) * self.power_weight_wrt_comfort
            + (1 - self.power_weight_wrt_comfort) * self.comfort_dissatisfaction(temperatures, CO2_concentrations, occupancies, hours)
        )

    def print_assessment(self, datetimes: list[datetime], PHVAC: list[float], temperatures: list[float], CO2_concentrations: list[float], occupancies: list[float], action_sets: tuple[list[float]] | None = None, modes: list[float] | None = None, list_extreme_hours: bool = False, power_unit: str = 'Wh') -> None:
        """Pretty-print comfort and cost indicators derived from a simulation run.

        :param datetimes: Time axis associated with the input time series.
        :type datetimes: list[datetime]
        :param PHVAC: HVAC power time series in watts.
        :type PHVAC: list[float]
        :param temperatures: Indoor temperature series in degrees Celsius.
        :type temperatures: list[float]
        :param CO2_concentrations: Indoor CO₂ concentration series in ppm.
        :type CO2_concentrations: list[float]
        :param occupancies: Occupancy signal used to detect presence.
        :type occupancies: list[float]
        :param action_sets: Optional tuple of action series used to evaluate configuration changes.
        :type action_sets: tuple[list[float]] | None, optional
        :param modes: Optional HVAC mode time series used for COP-aware energy cost.
        :type modes: list[float] | None, optional
        :param list_extreme_hours: When True, the function lists contiguous periods of extreme thermal conditions.
        :type list_extreme_hours: bool, optional
        """
        hours = [dt.hour for dt in datetimes]
        hour_quality_counters: dict[str, int] = {'extreme cold': 0, 'cold': 0, 'perfect': 0, 'warm': 0, 'extreme warm': 0}
        n_hours_with_presence = 0
        total_presence_hours = 0
        sleeping_presence_hours = 0
        sleeping_temperatures: list[float] = []
        sleeping_co2_concentrations: list[float] = []
        sleeping_hours_set = self.sleeping_hours
        extreme_cold_contiguous = Contiguous('Extreme cold', datetimes)
        extreme_warm_contiguous = Contiguous('Extreme warm', datetimes)

        for k, temperature in enumerate(temperatures):
            if occupancies[k] > 0:
                total_presence_hours += 1
                if hours[k] in sleeping_hours_set:
                    sleeping_presence_hours += 1
                    sleeping_temperatures.append(float(temperature))
                    sleeping_co2_concentrations.append(float(CO2_concentrations[k]))
                    continue
                n_hours_with_presence += 1
                if temperature < self.extreme_temperatures[0]:
                    hour_quality_counters['extreme cold'] += 1
                    extreme_cold_contiguous.add(k)
                elif temperature < self.preferred_temperatures[0]:
                    hour_quality_counters['cold'] += 1
                elif temperature > self.extreme_temperatures[1]:
                    hour_quality_counters['extreme warm'] += 1
                    extreme_warm_contiguous.add(k)
                elif temperature > self.preferred_temperatures[1]:
                    hour_quality_counters['warm'] += 1
                else:
                    hour_quality_counters['perfect'] += 1
        conversion = 1000 if power_unit == 'Wh' else 1
        print(f'\nThe assessed period covers {round(len(temperatures)/24)} days with a total HVAC energy of {int(round(sum([abs(P) / conversion for P in PHVAC])))}kWh (heating: {int(round(sum([P / conversion if P > 0 else 0 for P in PHVAC])))}kWh / cooling: {int(round(sum([-P / conversion if P < 0 else 0 for P in PHVAC])))}kWh):')
        print('- global objective: %s' % self.assess(PHVAC, temperatures, CO2_concentrations, occupancies, hours, modes, power_unit))
        print('- average thermal dissatisfaction: %.2f%%' % (self.thermal_comfort_dissatisfaction(temperatures, occupancies, hours) * 100))
        for hour_quality_counter in hour_quality_counters:
            ratio = (100 * hour_quality_counters[hour_quality_counter] / n_hours_with_presence) if n_hours_with_presence > 0 else 0.0
            print('- %% of %s hours: %.2f' % (hour_quality_counter, ratio))
        if sleeping_presence_hours > 0:
            avg_sleep_temp = sum(sleeping_temperatures) / len(sleeping_temperatures)
            avg_sleep_co2 = sum(sleeping_co2_concentrations) / len(sleeping_co2_concentrations)
            share_sleep = 100 * sleeping_presence_hours / total_presence_hours if total_presence_hours > 0 else 0.0
            print('- %% of sleeping hours: %.0f%% at average temperature %.1f°C and CO2 %.0fppm' % (share_sleep, avg_sleep_temp, avg_sleep_co2))
        else:
            print('- %% of sleeping hours: 0.00')
        print('- average CO2 dissatisfaction: %.2f%%' % (self.air_quality_dissatisfaction(CO2_concentrations, occupancies) * 100))
        print('- ICONE: %.2f' % (icone(CO2_concentrations, occupancies)))
        print('- average comfort dissatisfaction: %.2f%%' % (self.comfort_dissatisfaction(temperatures, CO2_concentrations, occupancies, hours) * 100))
        if action_sets is not None:
            print('- change dissatisfaction (number of changes / number of time slots with presence): %.2f%%' % (self.change_dissatisfaction(occupancies, action_sets) * 100))
        print('- heating cost: %.2f euros/day' % self.daily_cost_euros(PHVAC, modes, power_unit=power_unit))

        temperatures_when_presence = list()
        CO2_concentrations_when_presence = list()
        for i in range(len(occupancies)):
            if occupancies[i] > 0:
                if sleeping_hours_set and hours[i] in sleeping_hours_set:
                    continue
                temperatures_when_presence.append(temperatures[i])
                CO2_concentrations_when_presence.append(CO2_concentrations[i])
        if len(temperatures_when_presence) > 0:
            temperatures_when_presence.sort()
            CO2_concentrations_when_presence.sort()
            office_temperatures_estimated_presence_lowest = temperatures_when_presence[:math.ceil(len(temperatures_when_presence) * 0.1)]
            office_temperatures_estimated_presence_highest = temperatures_when_presence[math.floor(len(temperatures_when_presence) * 0.9):]
            office_co2_concentrations_estimated_presence_lowest = CO2_concentrations_when_presence[:math.ceil(len(CO2_concentrations_when_presence) * 0.1)]
            office_co2_concentrations_estimated_presence_highest = CO2_concentrations_when_presence[math.floor(len(CO2_concentrations_when_presence) * 0.9):]
            print('- average temperature during presence: %.1f' % (sum(temperatures_when_presence) / len(temperatures_when_presence)))
            print('- average 10%% lowest temperature during presence: %.1f' % (sum(office_temperatures_estimated_presence_lowest) / len(office_temperatures_estimated_presence_lowest)))
            print('- average 10%% highest temperature during presence: %.1f' % (sum(office_temperatures_estimated_presence_highest) / len(office_temperatures_estimated_presence_highest)))
            print('- average CO2 concentration during presence: %.0f' % (sum(CO2_concentrations_when_presence) / len(CO2_concentrations_when_presence)))
            print('- average 10%% lowest CO2 concentration during presence: %.0f' % (sum(office_co2_concentrations_estimated_presence_lowest) / len(office_co2_concentrations_estimated_presence_lowest)))
            print('- average 10%% highest CO2 concentration during presence: %.0f' %
                  (sum(office_co2_concentrations_estimated_presence_highest) / len(office_co2_concentrations_estimated_presence_highest)))
        if sleeping_temperatures:
            print('- average temperature during sleeping hours: %.1f' % (sum(sleeping_temperatures) / len(sleeping_temperatures)))
        if sleeping_co2_concentrations:
            print('- average CO2 concentration during sleeping hours: %.0f' % (sum(sleeping_co2_concentrations) / len(sleeping_co2_concentrations)))
        if list_extreme_hours:
            print('Contiguous periods:')
            print(extreme_cold_contiguous)
            print(extreme_warm_contiguous)

    def print_comfort(self, floor_data: list[dict]) -> None:
        """Print a compact summary of comfort data for multiple floors in a prettytable.
        
        :param floor_data: List of dictionaries, each containing floor comfort data with keys:
            - 'floor_name': str - Name of the floor (e.g., 'floor1')
            - 'datetimes': list[datetime] - Time axis
            - 'PHVAC': list[float] - HVAC power time series
            - 'temperatures': list[float] - Indoor temperature series
            - 'CO2_concentrations': list[float] - CO2 concentration series
            - 'occupancies': list[float] - Occupancy signal
            - 'modes': list[float] | None - Optional HVAC mode series
            - 'power_unit': str - Power unit ('Wh' or 'kWh'), defaults to 'Wh'
        :type floor_data: list[dict]
        """
        # Collect data for all floors
        floor_names: list[str] = []
        floor_metrics: list[dict] = []
        
        import numpy as np
        
        for floor_info in floor_data:
            floor_name = floor_info.get('floor_name', 'unknown')
            datetimes = floor_info['datetimes']
            PHVAC = floor_info['PHVAC']
            temperatures = floor_info['temperatures']
            CO2_concentrations = floor_info['CO2_concentrations']
            occupancies = floor_info['occupancies']
            modes = floor_info.get('modes', None)
            power_unit = floor_info.get('power_unit', 'Wh')
            
            hours = [dt.hour for dt in datetimes]
            hour_quality_counters: dict[str, int] = {'extreme cold': 0, 'cold': 0, 'perfect': 0, 'warm': 0, 'extreme warm': 0}
            n_hours_with_presence = 0
            sleeping_hours_set = self.sleeping_hours
            
            temperatures_when_presence: list[float] = []
            CO2_concentrations_when_presence: list[float] = []
            
            for k, temperature in enumerate(temperatures):
                if occupancies[k] > 0:
                    if sleeping_hours_set and hours[k] in sleeping_hours_set:
                        continue
                    n_hours_with_presence += 1
                    temperatures_when_presence.append(float(temperature))
                    CO2_concentrations_when_presence.append(float(CO2_concentrations[k]))
                    
                    if temperature < self.extreme_temperatures[0]:
                        hour_quality_counters['extreme cold'] += 1
                    elif temperature < self.preferred_temperatures[0]:
                        hour_quality_counters['cold'] += 1
                    elif temperature > self.extreme_temperatures[1]:
                        hour_quality_counters['extreme warm'] += 1
                    elif temperature > self.preferred_temperatures[1]:
                        hour_quality_counters['warm'] += 1
                    else:
                        hour_quality_counters['perfect'] += 1
            
            # Calculate metrics
            thermal_dis = self.thermal_comfort_dissatisfaction(temperatures, occupancies, hours) * 100
            co2_dis = self.air_quality_dissatisfaction(CO2_concentrations, occupancies) * 100
            comfort_dis = self.comfort_dissatisfaction(temperatures, CO2_concentrations, occupancies, hours) * 100
            
            perfect_pct = (100 * hour_quality_counters['perfect'] / n_hours_with_presence) if n_hours_with_presence > 0 else 0.0
            cold_pct = (100 * hour_quality_counters['cold'] / n_hours_with_presence) if n_hours_with_presence > 0 else 0.0
            warm_pct = (100 * hour_quality_counters['warm'] / n_hours_with_presence) if n_hours_with_presence > 0 else 0.0
            extreme_pct = (100 * (hour_quality_counters['extreme cold'] + hour_quality_counters['extreme warm']) / n_hours_with_presence) if n_hours_with_presence > 0 else 0.0
            
            icone_value = icone(CO2_concentrations, occupancies)
            # Convert PHVAC and modes to lists to ensure proper type handling
            PHVAC_list = list(PHVAC) if isinstance(PHVAC, (np.ndarray, np.generic)) else PHVAC
            if not isinstance(PHVAC_list, list):
                PHVAC_list = list(PHVAC_list)
            modes_list = None
            if modes is not None:
                modes_list = list(modes) if isinstance(modes, (np.ndarray, np.generic)) else modes
                if not isinstance(modes_list, list):
                    modes_list = list(modes_list)
            daily_cost = self.daily_cost_euros(PHVAC_list, modes_list, power_unit=power_unit)
            
            avg_temp = sum(temperatures_when_presence) / len(temperatures_when_presence) if temperatures_when_presence else 0.0
            avg_co2 = sum(CO2_concentrations_when_presence) / len(CO2_concentrations_when_presence) if CO2_concentrations_when_presence else 0.0
            
            floor_names.append(floor_name)
            floor_metrics.append({
                'thermal_dis': thermal_dis,
                'co2_dis': co2_dis,
                'comfort_dis': comfort_dis,
                'perfect_pct': perfect_pct,
                'cold_pct': cold_pct,
                'warm_pct': warm_pct,
                'extreme_pct': extreme_pct,
                'icone_value': icone_value,
                'daily_cost': daily_cost,
                'avg_temp': avg_temp,
                'avg_co2': avg_co2
            })
        
        # Create transposed table with metrics as rows and floors as columns
        table = prettytable.PrettyTable()
        table.field_names = ["Metric"] + floor_names
        
        # Add rows for each metric
        table.add_row(["Thermal Dis (%)"] + [f"{data['thermal_dis']:.1f}" for data in floor_metrics])
        table.add_row(["CO2 Dis (%)"] + [f"{data['co2_dis']:.1f}" for data in floor_metrics])
        table.add_row(["Comfort Dis (%)"] + [f"{data['comfort_dis']:.1f}" for data in floor_metrics])
        table.add_row([""] + [""] * len(floor_names))  # Empty row for spacing
        table.add_row(["Perfect (%)"] + [f"{data['perfect_pct']:.1f}" for data in floor_metrics])
        table.add_row(["Cold (%)"] + [f"{data['cold_pct']:.1f}" for data in floor_metrics])
        table.add_row(["Warm (%)"] + [f"{data['warm_pct']:.1f}" for data in floor_metrics])
        table.add_row(["Extreme (%)"] + [f"{data['extreme_pct']:.1f}" for data in floor_metrics])
        table.add_row([""] + [""] * len(floor_names))  # Empty row for spacing
        table.add_row(["ICONE"] + [f"{data['icone_value']:.2f}" for data in floor_metrics])
        table.add_row(["Cost (€/day)"] + [f"{data['daily_cost']:.2f}" for data in floor_metrics])
        table.add_row(["T avg (°C)"] + [f"{data['avg_temp']:.1f}" for data in floor_metrics])
        table.add_row(["CO2 avg (ppm)"] + [f"{int(round(data['avg_co2']))}" for data in floor_metrics])
        
        # Set alignment - left for metric column, right for all floor columns
        table.align["Metric"] = "l"
        for floor_name in floor_names:
            table.align[floor_name] = "r"
        
        print("\n" + "=" * 30)
        print("COMFORT ASSESSMENT SUMMARY")
        print("=" * 30)
        print(table)
        print("=" * 30 + "\n")

    def __str__(self) -> str:
        """Return a description of the defined preferences.

        :return: A descriptive string summarizing the preference configuration.
        :rtype: str
        """
        string = 'Preference:\ntemperature in %f<%f..%f>%f\n concentrationCO2 %f..%f\n' % (
            self.extreme_temperatures[0], self.preferred_temperatures[0], self.preferred_temperatures[1], self.extreme_temperatures[1], self.preferred_CO2_concentration[0], self.preferred_CO2_concentration[1])
        string += 'overall: %.3f * cost + %.3f disT + %.3f disCO2' % (self.power_weight_wrt_comfort, (1-self.power_weight_wrt_comfort) * self.temperature_weight_wrt_CO2, (1-self.power_weight_wrt_comfort) * (1-self.temperature_weight_wrt_CO2))
        return string
