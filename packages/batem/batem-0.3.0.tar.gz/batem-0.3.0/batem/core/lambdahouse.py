"""Lambda House parametric building energy analysis and simulation module.

.. module:: batem.core.lambdahouse

This module provides a comprehensive parametric building energy analysis system
for evaluating building performance across multiple design configurations. It
implements a "lambda house" concept that allows systematic exploration of
building parameters, energy systems, and performance metrics through automated
simulation and analysis workflows.

Classes
-------

.. autosummary::
   :toctree: generated/

   ParametricData
   LambdaParametricData
   ReportGenerator
   Analyzes
   Simulator

Classes Description
-------------------

**ParametricData**
    Base class for parametric configuration management.

**LambdaParametricData**
    Specialized parametric data for building energy analysis.

**ReportGenerator**
    Automated report generation with visualizations and analysis.

**Analyzes**
    Comprehensive analysis suite for building performance evaluation.

**Simulator**
    Building energy simulation engine with thermal and solar calculations.

Key Features
------------

* Parametric building design with configurable geometry, materials, and systems
* Automated building energy simulation with thermal and solar calculations
* Comprehensive climate analysis including heating/cooling period detection
* Solar energy system modeling with photovoltaic and thermal collectors
* Building thermal analysis with composition-based heat transfer calculations
* Energy performance indicators including autonomy and self-consumption
* Automated report generation with charts, tables, and analysis summaries
* Multi-parameter sensitivity analysis and optimization support
* Integration with weather data and climate analysis tools
* Visualization capabilities for building performance and energy flows

The module is designed for building energy analysis, parametric design studies,
and comprehensive building performance evaluation in research and practice.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""
from matplotlib.colorbar import Colorbar
import math
import copy
import numpy
import hashlib
import prettytable
import sys
import os
import os.path
import shutil
from warnings import warn
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import matplotlib.image as mplimg
try:
    from psychrochart import PsychroChart
    HAS_PSYCHROCHART = True
except ImportError:
    HAS_PSYCHROCHART = False
    # Fallback for when psychrochart is not available

    class PsychroChart:
        @staticmethod
        def create():
            return None

from matplotlib.colors import LinearSegmentedColormap
from typing import Any, Self
from datetime import datetime
from matplotlib import cm
from matplotlib.ticker import PercentFormatter
from windrose import WindAxes, WindroseAxes
from batem.core.weather import SiteWeatherData, SWDbuilder
try:
    from batem.core.solar import SolarModel, Collector, PVplant, MOUNT_TYPES, SolarSystem, RectangularMask, InvertedMask
    HAS_SOLAR = True
except ImportError:
    HAS_SOLAR = False
    # Fallback for when solar module is not available

    class SolarModel:
        def __init__(self, *args, **kwargs):
            pass

    class Collector:
        def __init__(self, *args, **kwargs):
            pass

    class PVplant:
        def __init__(self, *args, **kwargs):
            pass

    class SolarSystem:
        def __init__(self, *args, **kwargs):
            pass

    class RectangularMask:
        def __init__(self, *args, **kwargs):
            pass

    class InvertedMask:
        def __init__(self, *args, **kwargs):
            pass

    MOUNT_TYPES = {}
from batem.core.components import Composition
from batem.core.library import DIRECTIONS_SREF, SLOPES, Setup
from batem.core.timemg import datetime_to_stringdate
from batem.core.comfort import OutdoorTemperatureIndices
from batem.core.utils import Averager
from batem.ecommunity.indicators import year_autonomy, NEEG_percent, self_consumption, self_sufficiency


class ParametricData:
    """Base class for parametric configuration management in building energy analysis.

    This class provides a flexible framework for managing parametric configurations
    in building energy analysis. It supports parameter definition, value assignment,
    and configuration management with signature generation for tracking parameter
    changes and enabling reproducible simulations.
    """

    @staticmethod
    def setup(*references: tuple[str]):
        """Access project configuration values through :class:`batem.core.library.Setup`."""
        return Setup.data(*references)

    def __init__(self) -> None:
        """Initialize a parametric data object.

        Creates an empty parametric data container with default section 'site'.
        All parameters, given data, functions, and results are organized into sections.
        """
        self._sections: dict[str, list[str]] = {}
        self._current_section: str = 'site'
        self._selected_parametric: str | None = None
        self._current_parametric_data: dict[str, float] = {}
        self._nominal_parametric_data: dict[str, float] = {}
        self._parametric_possible_values: dict[str, tuple[str, list[float]]] = {}
        self._given_data: dict[str, list[str]] = {}
        self._functions: dict[str, callable] = {}
        self._resulting_data: dict[str, float] = {}

    @property
    def signature(self) -> int:
        """Generate a signature representing the current parameter values.

        The signature is computed as a hash of all nominal parameter values,
        enabling comparison and caching of parametric configurations.

        :return: A hash code representing the current parameter configuration.
        :rtype: int
        """
        _signature: str = ''
        for v in self._nominal_parametric_data:
            _signature += str(self(v))
        return int.from_bytes(hashlib.sha256(_signature.encode()).digest()[:8], 'big')

    def parametric(self, name: str | None = None) -> list[str] | list[float]:
        """Get parametric parameter names or possible values for a parameter.

        :param name: Parameter name to get possible values for. If None, returns all parametric parameter names.
        :type name: str | None, optional
        :return: If name is None, returns keys of all parametric parameters. Otherwise, returns list of possible values.
        :rtype: list[float] | dict.keys
        """
        if name is None:
            return self._parametric_possible_values.keys()
        return self._parametric_possible_values[name]

    def select(self, name: str) -> None:
        """Select a parametric parameter for iteration.

        :param name: Name of the parametric parameter to select.
        :type name: str
        :raises ValueError: Raised if the parametric parameter is not found.
        """
        if name in self._parametric_possible_values:
            self._selected_parametric = name
        else:
            raise ValueError(f"parametric {name} not found")

    def section(self, name: str) -> bool:
        """Set the current section for organizing parameters.

        :param name: Name of the section to activate.
        :type name: str
        """
        self._current_section = name
        if name not in self._sections:
            self._sections[name] = list()
            return True
        else:
            return False

    def sections(self) -> list[str]:
        """Get list of all section names.

        :return: List of section names.
        :rtype: list[str]
        """
        return list(self._sections.keys())

    def set(self, name: str, data: Any, *data_value_domain: list[float]) -> None:
        """Set a parameter value or define a parametric parameter.

        If data_value_domain is provided, creates a parametric parameter with
        the given value domain. Otherwise, sets a given data value or updates
        an existing parametric parameter.

        :param name: Parameter name.
        :type name: str
        :param data: Parameter value to set.
        :type data: Any
        :param data_value_domain: Optional list of possible values for parametric parameters.
        :type data_value_domain: list[float], optional
        :raises ValueError: Raised if attempting to redefine given data.
        """
        if len(data_value_domain) > 0:
            self._set_parametric(name, data, list(data_value_domain))
        elif name in self._parametric_possible_values:
            self._current_parametric_data[name] = data
        else:
            self._set_given_data(name, data)

    def _set_parametric(self, name: str, data: Any, value_domain: list[float]) -> None:
        """Set a parametric parameter with its value domain."""
        if name in self._nominal_parametric_data:
            warn(f'warning: redefinition of value domain for parametric {name}')
        
        if data not in value_domain:
            value_domain.append(data)
        
        self._parametric_possible_values[name] = sorted(value_domain)
        
        if name not in self._nominal_parametric_data:
            self._nominal_parametric_data[name] = data
            self._current_parametric_data[name] = data
            self._ensure_section_exists()
            self._sections[self._current_section].append(name)

    def _set_given_data(self, name: str, data: Any) -> None:
        """Set a given (non-parametric) data value."""
        if name in self._given_data:
            raise ValueError(f"given data {name} cannot be redefined")
        
        self._given_data[name] = data
        self._ensure_section_exists()
        self._sections[self._current_section].append(name)

    def _ensure_section_exists(self) -> None:
        """Ensure the current section exists in the sections dictionary."""
        if self._current_section not in self._sections:
            self._sections[self._current_section] = []

    def deduce(self, name: str, a_function: callable) -> None:
        """Define a computed parameter using a function.

        The function will be called when the parameter is accessed via __call__.
        The function should take the ParametricData instance as its only argument.

        :param name: Name of the computed parameter.
        :type name: str
        :param a_function: Function that computes the parameter value from the configuration.
        :type a_function: callable
        :raises ValueError: Raised if a function with the same name already exists.
        """
        if name not in self._functions:
            self._functions[name] = a_function
            self._sections[self._current_section].append(name)
        else:
            raise ValueError(f"function {name} already exists")

    def result(self, name: str, data: Any) -> None:
        """Store a simulation result in the configuration.

        :param name: Name of the result parameter.
        :type name: str
        :param data: Result data to store.
        :type data: Any
        """
        self._resulting_data[name] = data
        self._sections[self._current_section].append(name)

    def __eq__(self, other_configuration: "ParametricData") -> bool:
        return self.signature == other_configuration.signature

    def __call__(self, name: str, nominal: bool = False) -> float | list[float]:
        """Get a parameter value by name.

        Retrieves the value of a parameter, computed parameter, given data,
        or result. Supports automatic unit conversion for _kW and _kWh suffixes.

        :param name: Parameter name to retrieve.
        :type name: str
        :param nominal: If True, returns nominal value for parametric parameters. Defaults to False.
        :type nominal: bool, optional
        :return: Parameter value. May be a float or list depending on the parameter type.
        :rtype: float | list[float]
        :raises ValueError: Raised if the parameter name is not found.
        """
        # Handle unit conversions first
        if name.endswith('_kW'):
            return self._convert_kW_to_W(name)
        if name.endswith('_kWh'):
            return self._convert_kWh_to_W(name)
        
        # Lookup in order: functions, parametric, given, results
        if name in self._functions:
            return self._functions[name](self)
        if name in self._nominal_parametric_data:
            return self._get_parametric_value(name, nominal)
        if name in self._given_data:
            return self._given_data[name]
        if name in self._resulting_data:
            return self._resulting_data[name]
        
        raise ValueError(f"data {name} not found")

    def _get_parametric_value(self, name: str, nominal: bool) -> float:
        """Get parametric value, either current or nominal."""
        if not nominal and name in self._current_parametric_data:
            return self._current_parametric_data[name]
        return self._nominal_parametric_data[name]

    def _convert_kW_to_W(self, name: str) -> list[float]:
        """Convert power from kW to W."""
        alternate_name = name[:-3] + '_W'
        value_W = self(alternate_name)
        return [val / 1000 for val in value_W]

    def _convert_kWh_to_W(self, name: str) -> float:
        """Convert energy from kWh to Wh."""
        alternate_name = name[:-4] + '_W'
        value_W = self(alternate_name)
        return sum(value_W) / 1000

    def __contains__(self, name) -> bool:
        return name in self._nominal_parametric_data or name in self._functions or name in self._given_data or name in self._resulting_data

    def copy(self) -> "Self":
        """Clone a configuration, including the temporary parameters.

        Creates a deep copy of the parametric data configuration with all
        parameters, functions, and results preserved.

        :return: A cloned configuration instance.
        :rtype: Self
        """
        # This method should be overridden in subclasses that need specific copying logic
        # For base ParametricData, create a shallow copy and deep copy the data structures
        new_instance = self.__class__.__new__(self.__class__)
        new_instance._sections = copy.deepcopy(self._sections)
        new_instance._current_section = self._current_section
        new_instance._selected_parametric = self._selected_parametric
        new_instance._nominal_parametric_data = copy.deepcopy(self._nominal_parametric_data)
        new_instance._current_parametric_data = copy.deepcopy(self._current_parametric_data)
        new_instance._parametric_possible_values = copy.deepcopy(self._parametric_possible_values)
        new_instance._given_data = copy.deepcopy(self._given_data)
        new_instance._functions = copy.deepcopy(self._functions)
        new_instance._resulting_data = copy.deepcopy(self._resulting_data)
        return new_instance

    def reset(self, parametric: str | None = None) -> None:
        """Restore the nominal value for a parameter or all parameters.

        Clears all result data and optionally resets a specific parametric
        parameter to its nominal value. If parametric is None, resets all
        parametric parameters.

        :param parametric: Name of the parametric parameter to reset. If None, resets all parameters.
        :type parametric: str | None, optional
        """
        self._resulting_data.clear()
        if parametric is None:
            self._current_parametric_data.clear()
        else:
            if parametric in self._current_parametric_data:
                self._current_parametric_data.pop(parametric)

    def __iter__(self) -> "Self":
        """Make it possible to iterate over the parametric values of the selected parameter.

        Initializes iteration over the value domain of the last selected
        parametric parameter using the select() method.

        :return: Self for iteration.
        :rtype: Self
        """
        self.n = 0
        return self

    def __next__(self) -> "Any":
        """Get the next parametric value in the iteration.

        Iterates through the value domain of the selected parametric parameter.
        Once the last value is reached, the parameter is reset to its nominal
        value and StopIteration is raised.

        :raises StopIteration: Raised when the last value in the domain is reached.
        :return: The next parametric value in the domain.
        :rtype: Any
        """
        value_domain = self._parametric_possible_values[self._selected_parametric]
        if self.n >= len(value_domain):
            self.reset(self._selected_parametric)
            raise StopIteration
        
        value = value_domain[self.n]
        self._current_parametric_data[self._selected_parametric] = value
        self.n += 1
        return value

    def __data_type(self, name: str) -> str:
        if name in self._given_data:
            return 'given'
        elif name in self._parametric_possible_values:
            return 'parametric'
        elif name in self._functions:
            return 'function'
        elif name in self._resulting_data:
            return 'result'
        else:
            raise ValueError(f"data {name} not found")

    def __given_str(self, name: str) -> str:
        return '- given "%s" = ' % (name) + self.__str_shortener(self._given_data[name])

    def __parametric_str(self, name: str) -> str:
        return '- parametric "%s" = ' % (name) + self.__str_shortener(self(name)) + '[nominal: ' + str(self._nominal_parametric_data[name]) + '] in {' + ', '.join([str(v) for v in self._parametric_possible_values[name]]) + '}'

    def __result_str(self, name: str) -> str:
        return '- result "%s" = ' % (name) + self.__str_shortener(self._resulting_data[name])

    def __function_str(self, name: str) -> str:
        return '- function "%s" = ' % (name) + self.__str_shortener(self._functions[name](self))

    def __str_shortener(self, data: "Any", max_length: int = 100) -> str:
        """Format data for display, removing numpy types and improving readability.
        
        :param data: Data to format.
        :type data: Any
        :param max_length: Maximum string length before truncation, defaults to 100.
        :type max_length: int, optional
        :return: Formatted string representation.
        :rtype: str
        """
        data = self._convert_numpy_types(data)
        string = self._format_value(data)
        
        if len(string) > max_length:
            return string[:max_length] + '...'
        return string

    def _convert_numpy_types(self, data: Any) -> Any:
        """Convert numpy types to native Python types."""
        if isinstance(data, numpy.ndarray):
            return data.item() if data.size == 1 else data.tolist()
        if hasattr(data, 'item') and hasattr(data, 'shape') and data.shape == ():
            return data.item()
        if isinstance(data, (list, tuple)):
            return type(data)(self._convert_numpy_item(item) for item in data)
        if isinstance(data, (numpy.integer, numpy.floating)):
            return float(data) if isinstance(data, numpy.floating) else int(data)
        return data

    def _convert_numpy_item(self, item: Any) -> Any:
        """Convert a single numpy item to Python type."""
        if isinstance(item, numpy.ndarray):
            return item.item() if item.size == 1 else item.tolist()
        if hasattr(item, 'item') and hasattr(item, 'shape') and item.shape == ():
            return item.item()
        if isinstance(item, (numpy.integer, numpy.floating)):
            return float(item) if isinstance(item, numpy.floating) else int(item)
        return item

    def _format_value(self, data: Any) -> str:
        """Format a value as a string."""
        if isinstance(data, float):
            return self._format_float(data)
        if isinstance(data, (list, tuple)):
            return self._format_sequence(data)
        return str(data)

    def _format_float(self, value: float) -> str:
        """Format a float value."""
        if not math.isfinite(value):
            return str(value)
        if value == int(value):
            return str(int(value))
        return f"{value:.6g}".rstrip('0').rstrip('.')

    def _format_sequence(self, data: list | tuple) -> str:
        """Format a list or tuple."""
        if len(data) <= 10:
            items = [self._format_float(item) if isinstance(item, float) else str(item) for item in data]
            brackets = ('[', ']') if isinstance(data, list) else ('(', ')')
            return brackets[0] + ', '.join(items) + brackets[1]
        
        # For long sequences, show first and last few items
        start_items = [str(item) for item in data[:3]]
        end_items = [str(item) for item in data[-3:]]
        brackets = ('[', ']') if isinstance(data, list) else ('(', ')')
        return brackets[0] + ', '.join(start_items) + ', ..., ' + ', '.join(end_items) + brackets[1]

    def __str__(self) -> str:
        string: str = ''
        for section_name in self._sections:
            string += '######### Section %s #########\n' % section_name
            for data_name in self._sections[section_name]:
                try:
                    data_type = self.__data_type(data_name)
                    if data_type == 'given':
                        string += self.__given_str(data_name) + '\n'
                    elif data_type == 'parametric':
                        string += self.__parametric_str(data_name) + '\n'
                    elif data_type == 'result':
                        string += self.__result_str(data_name) + '\n'
                    elif data_type == 'function':
                        string += self.__function_str(data_name) + '\n'
                except ValueError:
                    # Skip data names that are in sections but not in any data dictionary
                    # This can happen if results haven't been computed yet or were cleared
                    continue
        return string


# set the plotting preferences
plot_size: tuple[int, int] = (int(ParametricData.setup('sizes', 'width')), int(ParametricData.setup('sizes', 'height')))


class LambdaParametricData(ParametricData):
    """Specialized parametric data class for lambda house building energy analysis.

    This class extends ParametricData to provide building-specific parameter
    management for the lambda house concept. It integrates weather data, solar
    modeling, and building geometry parameters to enable comprehensive building
    energy analysis and parametric design studies.

    The lambda house is a standardized reference building (100 m², single floor,
    square) used for comparative energy analysis across different locations and
    design configurations. This class initializes all default parameters including
    building geometry, HVAC settings, window configurations, and occupant profiles.

    :param swd_builder: Weather data builder or existing SiteWeatherData instance.
    :type swd_builder: SWDbuilder | SiteWeatherData
    :param year: Year for the analysis period.
    :type year: int
    :param albedo: Ground albedo coefficient in the [0, 1] range, defaults to 0.1.
    :type albedo: float, optional
    :param pollution: Atmospheric pollution factor for solar attenuation, defaults to 0.1.
    :type pollution: float, optional
    :ivar site_weather_data: Weather data for the analysis year.
    :ivar full_site_weather_data: Complete historical weather data.
    :ivar solar_model: Solar radiation model for the site.
    :ivar datetimes: List of datetime objects for the analysis period.
    :ivar PV_plant: Photovoltaic plant model with optimal orientation.
    :ivar occupancy: Occupancy profile time series.
    """

    def __init__(self, swd_builder: SWDbuilder | SiteWeatherData, year: int, albedo: float = 0.1, pollution: float = 0.1) -> None:
        """Initialize lambda house parametric data with weather and building parameters.

        :param swd_builder: Weather data builder or existing SiteWeatherData instance.
        :type swd_builder: SWDbuilder | SiteWeatherData
        :param year: Year for the analysis period.
        :type year: int
        :param albedo: Ground albedo coefficient in the [0, 1] range, defaults to 0.1.
        :type albedo: float, optional
        :param pollution: Atmospheric pollution factor for solar attenuation, defaults to 0.1.
        :type pollution: float, optional
        """
        super().__init__()
        self._initialize_weather_data(swd_builder, year, albedo, pollution)
        self._initialize_site_parameters(year)
        self._initialize_house_parameters()
        self._initialize_hvac_parameters()
        self._initialize_pv_parameters()
        self._initialize_inhabitant_parameters()
        self._initialize_weather_analysis()
        self._initialize_solar_system()
        self._initialize_occupancy()

    def _initialize_weather_data(self, swd_builder: SWDbuilder | SiteWeatherData, year: int, albedo: float, pollution: float) -> None:
        """Initialize weather data and solar model."""
        if isinstance(swd_builder, SWDbuilder):
            self.full_site_weather_data: SiteWeatherData = swd_builder(albedo=albedo, pollution=pollution)
            self.site_weather_data: SiteWeatherData = swd_builder(from_stringdate=f'1/1/{year}', to_stringdate=f'31/12/{year}', albedo=albedo, pollution=pollution)
        else:
            self.full_site_weather_data: SiteWeatherData = swd_builder
            self.site_weather_data: SiteWeatherData = swd_builder

        self.solar_model: SolarModel = SolarModel(self.site_weather_data)
        self.datetimes: list[datetime] = self.site_weather_data.datetimes

    def _initialize_site_parameters(self, year: int) -> None:
        """Initialize site-related parameters from weather data."""
        weather_mappings = {
            'cloudiness_percentage': 'cloudiness',
            'precipitations_mm_per_hour': 'precipitation',
            'rains_mm_per_hour': 'rain',
            'snowfalls_mm_per_hour': 'snowfall',
            'outdoor_temperatures_deg': 'temperature',
            'pressures_hPa': 'pressure',
            'humidities_percentage': 'humidity',
            'wind_directions_deg': 'wind_direction_in_deg',
            'wind_speeds_m_s': 'wind_speed_m_s',
        }
        
        for param_name, weather_key in weather_mappings.items():
            self.set(param_name, self.site_weather_data.get(weather_key))
        
        self.set('absolute_humidity_kg_kg', self.site_weather_data.absolute_humidity_kg_per_kg())
        self.set('winter_hvac_trigger_temperature_deg', 16)
        self.set('summer_hvac_trigger_temperature_deg', 25)
        self.set('year', year)

    def _initialize_house_parameters(self) -> None:
        """Initialize house geometry and building parameters."""
        self.section('house')
        self.set('total_living_surface_m2', 100)
        self.set('floor_height_m', 2.5)
        self.set('shape_factor', 1, .25, .5, .75, 1, 1.25, 1.5, 1.75, 2, 3)
        self.set('number_of_floors', 1, 2, 3)
        self.set('glass_composition_in_out', [('glass', 4e-3), ('air', 6e-3), ('glass', 4e-3)])
        self.set('thickness_m', 10e-2, 0, 2e-2, 5e-2, 10e-2, 15e-2, 20e-2, 25e-2, 30e-2)

        self._setup_house_compositions()
        self._setup_glazing_parameters()
        self._setup_glazing_surfaces()
        self.set('south_solar_protection_angle_deg', 0, 15, 30, 35, 40, 45)

    def _setup_house_compositions(self) -> None:
        """Set up building composition parameters."""
        self.deduce('floor_surface_m2', lambda c: c('total_living_surface_m2') / c('number_of_floors'))
        self.deduce('wall_composition_in_out', lambda c: [('concrete', 14e-2), ('plaster', 15e-3), ('polystyrene', c('thickness_m'))])
        self.deduce('roof_composition_in_out', lambda c: [('plaster', 30e-3), ('polystyrene', c('thickness_m')), ('concrete', 13e-2)])
        self.deduce('ground_composition_in_out', lambda c: [('concrete', 13e-2), ('polystyrene', c('thickness_m')), ('gravels', 20e-2)])
        self.deduce('air_volume_m3', lambda c: c('total_living_surface_m2') * c('floor_height_m'))
        self.deduce('building_height_m', lambda c: c('number_of_floors') * c('floor_height_m'))

    def _setup_glazing_parameters(self) -> None:
        """Set up glazing ratio parameters."""
        self.set('solar_factor', 0.56)
        self.set('offset_exposure_deg', 0, -45, -30, -15, 0, 15, 30, 45)
        for direction in ['north', 'south', 'east', 'west']:
            self.set(f'glazing_ratio_{direction}', .1, 0.05, .2, .4, .6, .8)

    def _setup_glazing_surfaces(self) -> None:
        """Set up glazing surface calculations."""
        # Wall surface calculation
        self.deduce('wall_surface_m2', lambda c: c('floor_height_m') * (
            math.sqrt(c('shape_factor') * c('total_living_surface_m2') * c('number_of_floors')) * 
            (2 - c('glazing_ratio_north') - c('glazing_ratio_south')) + 
            math.sqrt(c('total_living_surface_m2') * c('number_of_floors') / c('shape_factor')) * 
            (2 - c('glazing_ratio_east') - c('glazing_ratio_west'))
        ))
        
        # Individual glazing surfaces
        def ns_length(c):
            return math.sqrt(c('shape_factor') * c('total_living_surface_m2') * c('number_of_floors'))

        def ew_length(c):
            return math.sqrt(c('total_living_surface_m2') * c('number_of_floors') / c('shape_factor'))

        self.deduce('glazing_surface_north_m2', lambda c: ns_length(c) * c('floor_height_m') * c('glazing_ratio_north'))
        self.deduce('glazing_surface_south_m2', lambda c: ns_length(c) * c('floor_height_m') * c('glazing_ratio_south'))
        self.deduce('glazing_surface_east_m2', lambda c: ew_length(c) * c('floor_height_m') * c('glazing_ratio_east'))
        self.deduce('glazing_surface_west_m2', lambda c: ew_length(c) * c('floor_height_m') * c('glazing_ratio_west'))

        # Total glazing surface
        self.deduce('glazing_surface_m2', lambda c: c('floor_height_m') * (
            ns_length(c) * (c('glazing_ratio_north') + c('glazing_ratio_south')) +
            ew_length(c) * (c('glazing_ratio_east') + c('glazing_ratio_west'))
        ))

    def _initialize_hvac_parameters(self) -> None:
        """Initialize HVAC system parameters."""
        self.section('HVAC')
        self.set('heating_setpoint_deg', 21, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 27)
        self.set('delta_temperature_absence_mode_deg', 3, 0, 1, 2, 3, 4)
        self.set('cooling_setpoint_deg', 24, 23, 24, 25, 27, 28, 29)
        self.set('hvac_hour_delay_for_trigger_h', 24)
        self.set('hvac_COP', 3)
        self.set('final_to_primary_energy_coefficient', 2.54)
        self.set('air_renewal_presence_vol_per_h', 3, .5, 1, 3, 5)
        self.set('air_renewal_absence_vol_per_h', 1)
        self.set('ventilation_heat_recovery_efficiency', 0.6, 0, .25, .5, .75, .9)

    def _initialize_pv_parameters(self) -> None:
        """Initialize photovoltaic system parameters."""
        self.section('PV')
        self.set('PV_efficiency', 0.20)
        best_exposure_deg, best_slope_deg = self.solar_model.best_direction()
        self.set('best_exposure_deg', best_exposure_deg)
        self.set('best_slope_deg', best_slope_deg)

    def _initialize_inhabitant_parameters(self) -> None:
        """Initialize occupant-related parameters."""
        self.section('inhabitants')
        self.set('occupancy_schema', {(1, 2, 3, 4, 5): {(18, 7): 4}, (6, 7): {(0, 24): 4}})
        self.set('average_occupancy_electric_gain_w', 50)
        self.set('average_occupancy_metabolic_gain_w', 100)
        self.set('average_permanent_electric_gain_w', 200)

    def _initialize_weather_analysis(self) -> None:
        """Initialize weather analysis and HVAC period calculations."""
        self.section('weather')
        self.set('datetimes', self.site_weather_data.datetimes)
        self.set('average_wind_speed_m_s', sum(self('wind_speeds_m_s')) / len(self))
        self.set('average_outdoor_temperature_deg', sum(self.site_weather_data.get('temperature')) / len(self))
        self.set('smooth_outdoor_temperatures_for_hvac_periods_deg', Averager(self.site_weather_data.get('temperature')).inertia_filter())

        self._calculate_heating_period()
        self._calculate_cooling_period()

    def _calculate_heating_period(self) -> None:
        """Calculate heating period indices and duration."""
        smooth_temps = numpy.array(self('smooth_outdoor_temperatures_for_hvac_periods_deg'))
        trigger_temp = self('winter_hvac_trigger_temperature_deg')
        no_heating_period = numpy.nonzero(smooth_temps > trigger_temp)[0]
        
        duration_h, indices = self._calculate_period_indices(no_heating_period, self('hvac_hour_delay_for_trigger_h'))
        
        self.set('heating_period_indices', indices)
        self.set('heating_period_duration_h', duration_h)
        self.heating_period_indices: tuple[int, int] = self('heating_period_indices')
        self.heating_period_duration_h: float = self('heating_period_duration_h')

    def _calculate_cooling_period(self) -> None:
        """Calculate cooling period indices and duration."""
        smooth_temps = numpy.array(self('smooth_outdoor_temperatures_for_hvac_periods_deg'))
        trigger_temp = self('summer_hvac_trigger_temperature_deg')
        no_cooling_period = numpy.nonzero(smooth_temps > trigger_temp)[0]
        
        delay_h = self('hvac_hour_delay_for_trigger_h')
        if len(no_cooling_period) > delay_h:
            duration_h, indices = self._calculate_period_indices(no_cooling_period, delay_h)
        else:
            duration_h, indices = 0, (0, 0)
        
        self.set('cooling_period_indices', indices)
        self.set('cooling_period_duration_h', duration_h)
        self.cooling_period_indices: tuple[int, int] = self('cooling_period_indices')
        self.cooling_period_duration_h: float = self('cooling_period_duration_h')

    def _calculate_period_indices(self, no_period_indices: numpy.ndarray, delay_h: int) -> tuple[int, tuple]:
        """Calculate period duration and indices from non-period indices.
        
        Returns duration in hours and indices tuple. Only periods >= 7 days (168 hours) are considered.
        """
        MIN_PERIOD_HOURS = 168
        
        if len(no_period_indices) == 0 or len(self) - delay_h - len(no_period_indices) <= 0:
            return 0, (0, 0)
        
        i_end = no_period_indices[0]
        i_start = no_period_indices[-1]
        
        if i_start.item() < i_end.item():
            duration = i_end.item() - i_start.item()
            if duration >= MIN_PERIOD_HOURS:
                return duration, (i_start.item(), i_end.item())
        else:
            duration = i_end.item() + (len(self) - i_start.item())
            if duration >= MIN_PERIOD_HOURS:
                return duration, (0, i_end.item(), i_start.item(), len(self))
        
        return 0, (0, 0)

    def _initialize_solar_system(self) -> None:
        """Initialize unit solar gain system for canonical calculations."""
        self.unit_solar_gain_system = SolarSystem(self.solar_model)
        for direction in DIRECTIONS_SREF:
            Collector(self.unit_solar_gain_system, direction.name, exposure_deg=direction.value, slope_deg=SLOPES.VERTICAL.value, surface_m2=1, solar_factor=1)
        Collector(self.unit_solar_gain_system, 'HORIZONTAL_UP', exposure_deg=DIRECTIONS_SREF.SOUTH.value, slope_deg=SLOPES.HORIZONTAL_UP.value, surface_m2=1, solar_factor=1)
        self.set('unit_canonic_solar_powers_W', self.unit_solar_gain_system.powers_W(gather_collectors=False))
        self.unit_canonic_solar_powers_W: list[float] = self.unit_solar_gain_system.powers_W(gather_collectors=False)

    def _initialize_occupancy(self) -> None:
        """Initialize occupancy profile from schema."""
        occupancy_schema = self('occupancy_schema')
        occupancy = []
        
        for a_datetime in self('datetimes'):
            day_of_week = a_datetime.isoweekday()
            hour_in_day = a_datetime.hour
            occupancy_value = 0
            
            for days in occupancy_schema:
                if day_of_week in days:
                    for period in occupancy_schema[days]:
                        start_hour, end_hour = period
                        if start_hour <= hour_in_day <= end_hour or (start_hour > end_hour and (hour_in_day >= start_hour or hour_in_day <= end_hour)):
                            occupancy_value = occupancy_schema[days][period]
                            break
                    if occupancy_value > 0:
                        break
            
            occupancy.append(occupancy_value)
        
        self.set('occupancy', occupancy)
        self.occupancy: list[float] = self('occupancy')

    def copy(self) -> "Self":
        """Clone a lambda house configuration, including weather data.

        Creates a deep copy of the lambda house configuration with all
        parameters, functions, results, and weather data preserved.

        :return: A cloned configuration instance.
        :rtype: Self
        """
        site_weather_data: SiteWeatherData = self('site_weather_data')
        swd_builder = SWDbuilder(site_weather_data.location, site_weather_data.site_latitude_north_deg, site_weather_data.site_longitude_east_deg)
        year = self('year')
        lbd_copy = LambdaParametricData(swd_builder, year, site_weather_data.albedo, site_weather_data.pollution)
        
        # Copy all parametric data from parent class
        lbd_copy._current_section = self._current_section
        lbd_copy._selected_parametric = self._selected_parametric
        lbd_copy._nominal_parametric_data = copy.deepcopy(self._nominal_parametric_data)
        lbd_copy._current_parametric_data = copy.deepcopy(self._current_parametric_data)
        lbd_copy._parametric_possible_values = copy.deepcopy(self._parametric_possible_values)
        lbd_copy._functions = copy.deepcopy(self._functions)
        lbd_copy._resulting_data = copy.deepcopy(self._resulting_data)
        
        return lbd_copy

    def __len__(self) -> int:
        """Get the number of time samples in the analysis period.

        :return: Number of hourly time samples.
        :rtype: int
        """
        return len(self.datetimes)

    def __str__(self) -> str:
        """Generate string representation of the lambda house configuration.

        :return: Formatted string with all parameters and number of samples.
        :rtype: str
        """
        string = str(super().__str__())
        string += f'{self.__class__.__name__} with {len(self)} samples\n'
        return string


def sort_values(datetimes: list[datetime], values: list[float]) -> tuple[list[float], list[float]]:
    """Sort the time series defined by datetimes and values according to values in descending order.

    :param datetimes: Times corresponding to values.
    :type datetimes: list[datetime]
    :param values: Values to be sorted.
    :type values: list[float]
    :return: Tuple of (sorted month numbers, sorted values) in descending order.
    :rtype: tuple[list[float], list[float]]
    """
    values_array = numpy.array(values)
    months_array = numpy.array([datetimes[i].timetuple().tm_yday/30.41666667 + 1 for i in range(len(datetimes))])
    indices = (-values_array).argsort()
    sorted_values_array = values_array[indices]
    sorted_months_array = months_array[indices]
    return sorted_months_array.tolist(), sorted_values_array.tolist()


def to_markdown_table(pretty_table: prettytable.PrettyTable) -> str:
    """Convert a PrettyTable object to a markdown table string.

    :param pretty_table: A PrettyTable object to convert.
    :type pretty_table: prettytable.PrettyTable
    :return: A string that adheres to GitHub markdown table rules.
    :rtype: str
    :note: Any customization beyond int and float style may have unexpected effects.
    """
    _join = pretty_table.junction_char
    if _join != "|":
        pretty_table.junction_char = "|"
    
    table_lines = pretty_table.get_string().split("\n")
    # Skip the first line (top border) and last line (bottom border)
    markdown_lines: list[str] = []
    
    for i, row in enumerate(table_lines[1:-1]):
        # Remove leading and trailing pipe characters
        cleaned_row = row.strip()
        if cleaned_row.startswith("|") and cleaned_row.endswith("|"):
            cleaned_row = cleaned_row[1:-1].strip()
        
        # Check if this is the separator row (second row, index 1 in table_lines)
        # The separator row typically contains only dashes and plus signs
        if i == 1 and all(c in "-+| " for c in cleaned_row):  # This is the separator row
            # Check alignment for each column and adjust separator
            num_columns = len(pretty_table.field_names)
            separator_parts = []
            for j in range(num_columns):
                # Check column alignment and set appropriate separator
                field_name = pretty_table.field_names[j]
                alignment = pretty_table.align.get(field_name, 'l')
                if alignment == 'r':
                    separator_parts.append("---:")  # Right-aligned
                elif alignment == 'l':
                    separator_parts.append(":---")  # Left-aligned
                else:
                    separator_parts.append(":---:")  # Center-aligned (default)
            cleaned_row = "|".join(separator_parts)
        
        markdown_lines.append("|" + cleaned_row + "|")
    
    pretty_table.junction_char = _join
    return "\n".join(markdown_lines)


class ReportGenerator:
    """Automated report generation system for building energy analysis results.

    This class provides comprehensive report generation capabilities for building
    energy analysis results. It supports both on-screen display and file output
    with markdown formatting, figure generation, and structured analysis reporting.
    """
    def __init__(self, location: str, year: int, on_screen: bool = True) -> None:
        """Initialize the report generator.

        :param location: Location name for the analysis site.
        :type location: str
        :param year: Year for the analysis period.
        :type year: int
        :param on_screen: Whether to display output on screen or save to file, defaults to True.
        :type on_screen: bool, optional
        """
        self.on_screen: bool = on_screen
        self.original_stdout = sys.stdout

        self.figure_counter: int = 0
        if not on_screen:
            results_folder: str = LambdaParametricData.setup('folders', 'results')
            if not os.path.exists(results_folder):
                os.mkdir(results_folder)
            self.mmd_filename: str = LambdaParametricData.setup('folders', 'results') + location + "_" + str(year) + ".md"
            self.pdf_filename: str = LambdaParametricData.setup('folders', 'results') + location + "_" + str(year) + ".pdf"
            if os.path.exists(self.mmd_filename):
                os.remove(self.mmd_filename)
            if os.path.exists(self.pdf_filename):
                os.remove(self.pdf_filename)
            figures_folder: str = LambdaParametricData.setup('folders', 'results') + LambdaParametricData.setup('folders', 'figures')
            if os.path.exists(figures_folder):
                shutil.rmtree(figures_folder, ignore_errors=True)
            os.mkdir(figures_folder)
            sys.stdout = open(self.mmd_filename, 'w')
            # Add YAML metadata header for PDF font size
            print('---')
            print('documentclass: extarticle')
            print('fontsize: 14pt')
            print('geometry: margin=0.5in')
            print('linestretch: 0.85')
            print('---')
            print()

        self.add_text(f'# Analysis of the site "{location}" for the year {year} <a name="site"></a>')
        self.add_text('## The $\\lambda$-house principle <a name="principle"></a>')
        self.add_image("lambda.png")

        self.add_text("Pre-design stage is characterized by a known location for the construction but little ideas about the building to design. Nevertheless, this is during this stage that main directions are taken. Because engineers do not have enough data to setup simulations, they use to intervene a little during this stage. However, very impacting decisions like whether it is interesting or not to set large windows for each facade use to be taken, or what is the direction for the building? Or, for a given floor surface, is it more interesting to design a single floor building or a multiple floor one? Moreover, many local phenomena make sense only for a complete building: knowing solar radiation, knowing the albedo, knowing the cloudiness of the site, knowing the solar masks,etc... cannot be appreciated without considering a complete building.")

        self.add_text("The idea of the $\\lambda$-house is to locate a known standard house and to analyze its behavior regarding energy in order to point out the impact of possible choices on energy performances: helping to make decisions for a specific location comparatively to other known locations. By default, the $\\lambda$ house is a $100m^2$ single floor square house equipped with an invertible heat pump and a dual flow ventilation system.")
        self.add_text("The model includes occupant adaptive behaviors to preserve thermal comfort: if the free indoor temperature exceeds 26°C, inhabitants react by closing shutters to reduce solar gains and prevent overheating.")
        self.add_text("See the end of the report for the list of parameters characterizing the so-called $\\lambda$-house (\"maison témoin\" in French). When a more specific house is needed, it means that the engineer has more data and can setup a simulation. The lambda house is no longer needed.")

        self.add_text("Three minimum requirements for setting up a lambda-house at a specific location has to be specified:")
        self.add_text("- a name that is used to save the results and to name the weather file")
        self.add_text('- the location of the house in terms of decimal latitude north and longitude east angles, that can be found on Google Maps for instance by right clicking on the map, or on Open Street Map')
        self.add_text("- the year for the analysis")
        self.add_text("The $\\lambda$-house code will download the weather data from 1980 from [open-meteo](https://open-meteo.com), the far solar masks made by surrounding landscape, the elevation of the defined location")
        self.figure_counter = 1

    def close(self, parameters_description: str, pdf: bool = True, latex_template: str | None = None, features: bool = True) -> None:
        """Close the report and save it to file.

        :param parameters_description: Description of lambda house parameters to include at the end of the report.
        :type parameters_description: str
        :param pdf: Whether to generate a PDF version of the report, defaults to True.
        :type pdf: bool, optional
        :param latex_template: Optional path to a custom LaTeX template file for PDF generation, defaults to None.
        :type latex_template: str | None, optional
        :note: PDF generation requires pypandoc to be installed.
        """
        # Add parameters section at the end of the report
        if features:
            self.add_text('\n\n\n\n\n\n\n\n')
            self.add_text('_______________________________________________________________________')
            self.add_text('\n')
            self.add_text('## Features of the $\\lambda$-house <a name="features"></a>')
            self.add_text("The parameters below describe the house context. Although it is not the $\\lambda$-house philosophy, which be the same anywhere for comparison purpose, its parameters can be modified to better match a given context.")

            self.add_text('For each parameter, a list of values defined in "parametric" can be specified. They are used for parametric studies.')
            for data_description in parameters_description.split('\n'):
                self.add_text(data_description)
        
        # Always flush and close the markdown file before PDF conversion
        # This ensures all content is written to disk before pypandoc reads it
        if not self.on_screen:
            sys.stdout.flush()
            sys.stdout.close()
            sys.stdout = self.original_stdout

        if pdf:
            try:  # Convert Markdown to PDF with resource path specified
                import pypandoc
                base_dir = os.path.dirname(os.path.abspath(self.mmd_filename))
                print(f"PDF generation: {self.pdf_filename}", file=sys.stderr)
                # Use LaTeX options to maximize content per page:
                # - Small margins (0.5in on all sides)
                # - Font size (14pt = 1.5x of original 9pt, using extarticle class for larger sizes)
                # - Tighter line spacing (0.85)
                # - Reduce spacing around figures and sections
                # Note: extarticle class is needed for font sizes > 12pt (standard article only supports 10pt, 11pt, 12pt)
                
                # Create a temporary LaTeX header file to force font size
                import tempfile
                header_file = tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False)
                header_file.write('\\usepackage{extsizes}\n')
                header_file.write('\\renewcommand{\\normalsize}{\\fontsize{14pt}{17pt}\\selectfont}\n')
                header_file.write('\\renewcommand{\\small}{\\fontsize{12pt}{14pt}\\selectfont}\n')
                header_file.write('\\renewcommand{\\footnotesize}{\\fontsize{10pt}{12pt}\\selectfont}\n')
                header_file.write('\\renewcommand{\\scriptsize}{\\fontsize{8pt}{10pt}\\selectfont}\n')
                header_file.write('\\renewcommand{\\tiny}{\\fontsize{7pt}{8pt}\\selectfont}\n')
                header_file.write('\\renewcommand{\\large}{\\fontsize{16pt}{19pt}\\selectfont}\n')
                header_file.write('\\renewcommand{\\Large}{\\fontsize{18pt}{22pt}\\selectfont}\n')
                header_file.write('\\renewcommand{\\LARGE}{\\fontsize{20pt}{24pt}\\selectfont}\n')
                header_file.write('\\renewcommand{\\huge}{\\fontsize{22pt}{26pt}\\selectfont}\n')
                header_file.write('\\renewcommand{\\Huge}{\\fontsize{24pt}{28pt}\\selectfont}\n')
                header_file.close()
                
                extra_args = [
                    '--resource-path', base_dir,
                    '--variable', 'geometry=margin=0.5in',
                    '--variable', 'linestretch=0.85',
                    '--variable', 'documentclass=extarticle',  # extarticle supports larger font sizes (8pt-20pt)
                    '--variable', 'fontsize=14pt',  # Explicitly set font size
                    '--variable', 'documentclass-options=14pt,a4paper',  # Font size: 14pt (1.5x of original 9pt)
                    '--variable', 'toc-depth=3',
                    '--variable', 'secnumdepth=3',
                    '--include-in-header', header_file.name  # Include custom font size commands
                ]
                # Add custom template if provided
                if latex_template and os.path.exists(latex_template):
                    extra_args.extend(['--template', latex_template])
                output: str = pypandoc.convert_file(self.mmd_filename, 'pdf', outputfile=self.pdf_filename, extra_args=extra_args)
                assert output == "", "Error during conversion"
                # Clean up temporary header file
                try:
                    os.unlink(header_file.name)
                except Exception:
                    pass  # Ignore errors when cleaning up
            except Exception as e:
                print(f"PDF file cannot be created because pypandoc is not installed: {e}")
                # Clean up temporary header file on error
                try:
                    if 'header_file' in locals():
                        os.unlink(header_file.name)
                except Exception:
                    pass  # Ignore errors when cleaning up

    def add_image(self, file_name: str) -> None:
        """Add an image to the report.

        :param file_name: Name of the image file to include.
        :type file_name: str
        """
        if not self.on_screen:
            self.add_text("![](../figs/%s)" % file_name)
        else:
            image = mplimg.imread('./figs/%s' % file_name)
            plt.imshow(image)
            plt.show()

    def add_text(self, text: str, on_screen_only: bool = False, on_mmd_only: bool = False) -> None:
        """Add a text line to the report.

        :param text: Text to be added to the report.
        :type text: str
        :param on_screen_only: If True, only display on screen (not saved to file), defaults to False.
        :type on_screen_only: bool, optional
        :param on_mmd_only: If True, only save to markdown file (not displayed), defaults to False.
        :type on_mmd_only: bool, optional
        """
        if not self.on_screen and (not on_mmd_only and not on_screen_only):
            print(str(text) + '\n')
            if not self.on_screen and not str(text).startswith('!'):
                print(str(text) + '\n', file=sys.stderr)
        else:
            print(str(text) + '\n')

    def add_pretty_table(self, pretty_table: prettytable.PrettyTable, on_screen_only: bool = False, on_mmd_only: bool = False) -> None:
        """Add a PrettyTable to the report.

        Converts the table to markdown format when saving to file.

        :param pretty_table: PrettyTable object to add.
        :type pretty_table: prettytable.PrettyTable
        :param on_screen_only: If True, only display on screen, defaults to False.
        :type on_screen_only: bool, optional
        :param on_mmd_only: If True, only save to markdown file, defaults to False.
        :type on_mmd_only: bool, optional
        """
        if self.on_screen:
            self.add_text(str(pretty_table), on_screen_only, on_mmd_only)
        else:
            self.add_text(to_markdown_table(pretty_table), on_screen_only, on_mmd_only)

    def add_figure(self, fig: Any = None, on_screen_only: bool = False) -> None:
        """Add a figure to the report.

        Saves matplotlib or plotly figures to file and includes them in the markdown report.

        :param fig: Plotly figure object. If None, saves the current matplotlib figure, defaults to None.
        :type fig: Any, optional
        :param on_screen_only: If True, only display on screen (not saved), defaults to False.
        :type on_screen_only: bool, optional
        """
        if not self.on_screen and not on_screen_only:
            figure_name: str = LambdaParametricData.setup('folders', 'figures') + 'figure%i.png' % self.figure_counter
            self.figure_counter += 1
            if fig is None:
                plt.savefig(LambdaParametricData.setup('folders', 'results') + figure_name, dpi=600, bbox_inches='tight', pad_inches=0)
                plt.close()
            else:
                fig.write_image(LambdaParametricData.setup('folders', 'results') + figure_name, scale=2)
            # Add newline before figure for proper PDF rendering
            self.add_text('\n![](%s)' % figure_name)

    def add_event_plot(self, main_data_name: str, datetimes: list[datetime], values: list[float]) -> None:
        """Add an event plot showing duration and intensity of precipitation events.

        Creates a heatmap showing the number of occurrences of events with
        specific duration and quantity characteristics.

        :param main_data_name: Title for the plot.
        :type main_data_name: str
        :param datetimes: List of datetime objects corresponding to values.
        :type datetimes: list[datetime]
        :param values: Precipitation values in mm per hour.
        :type values: list[float]
        """
        fig, axes = plt.subplots(figsize=plot_size)
        resolution = 20
        days_with_rain: list[str] = list()
        days: list[str] = list()
        rain_duration_h_quantity_mm_n_events: dict[tuple[float, float], int] = dict()
        rains_months_dict: dict[tuple[float, float], list[str]] = dict()
        rain_duration_h: int = 0
        max_duration = 0
        rain_quantity_mm: float = 0
        max_quantity = 0
        threshold = 0.1
        was_raining = False

        for k, precipitation in enumerate(values):
            month: int = datetimes[k].month
            stringdate: str = datetime_to_stringdate(datetimes[k]).split(' ')[0]
            if stringdate not in days:
                days.append(stringdate)
            if was_raining and precipitation > 0:  # ongoing rain event
                rain_duration_h += 1
                rain_quantity_mm += precipitation
                if stringdate not in days_with_rain:
                    days_with_rain.append(stringdate)
            elif was_raining and precipitation == 0:  # end of rain event
                rain_duration_h_quantity_mm: tuple[int, int] = (rain_duration_h, round(rain_quantity_mm, 0))
                max_duration: int = max(max_duration, rain_duration_h_quantity_mm[0])
                max_quantity: int = max(max_quantity, rain_duration_h_quantity_mm[1])

                if rain_duration_h_quantity_mm in rain_duration_h_quantity_mm_n_events:
                    rain_duration_h_quantity_mm_n_events[rain_duration_h_quantity_mm] += 1
                    if str(month) not in rains_months_dict[rain_duration_h_quantity_mm]:
                        rains_months_dict[rain_duration_h_quantity_mm].append(str(month))
                else:
                    rain_duration_h_quantity_mm_n_events[rain_duration_h_quantity_mm] = 1
                    rains_months_dict[rain_duration_h_quantity_mm] = [str(month)]
                was_raining = False
                rain_duration_h = 0
                rain_quantity_mm = 0
            elif not was_raining and precipitation > threshold:  # beginning of rain event
                if stringdate not in days_with_rain:
                    days_with_rain.append(stringdate)
                rain_duration_h = 1
                rain_quantity_mm = precipitation
                was_raining = True
        rain_duration_scale: list[float] = [_/resolution*max_duration for _ in range(resolution)]
        rain_quantity_scale: list[float] = [_/resolution*max_quantity for _ in range(resolution)]
        rain_duration_quantity_events: list[list[float]] = [[float('NaN') for _ in range(resolution)] for _ in range(resolution)]
        max_number_of_rain_events = 0
        for rain_duration_h_quantity_mm in rain_duration_h_quantity_mm_n_events:
            rain_duration_h, rain_quantity_mm = rain_duration_h_quantity_mm
            n_events = rain_duration_h_quantity_mm_n_events[rain_duration_h_quantity_mm]
            rain_duration_h_index = min(resolution-1, int(rain_duration_h/max_duration*resolution))
            rain_quantity_mm_index = min(resolution-1, int(rain_quantity_mm/max_quantity*resolution))
            rain_duration_quantity_events[rain_duration_h_index][rain_quantity_mm_index] = n_events
            max_number_of_rain_events: int = max(max_number_of_rain_events, rain_duration_h_quantity_mm_n_events[rain_duration_h_quantity_mm])
        cmap: LinearSegmentedColormap = LinearSegmentedColormap.from_list('custom', ['green', 'orange', 'red', 'purple', 'blue'], N=max_number_of_rain_events)
        im: plt.AxesImage = axes.imshow(rain_duration_quantity_events, aspect='auto', origin='lower', extent=[rain_duration_scale[0], rain_duration_scale[-1], rain_quantity_scale[0], rain_quantity_scale[-1]], cmap=cmap)
        color_bar: Colorbar = plt.colorbar(im, ax=axes, orientation='horizontal')
        color_bar.ax.set_ylabel("# events", rotation=-90, va="bottom")
        axes.set_title(main_data_name + ' events: %i raining days out of %i' % (len(days_with_rain), len(days)))
        axes.set_xlabel('duration in hours')
        axes.set_ylabel('quantity in mm/event')
        self.add_figure()

    def add_month_week_averages(self, main_data_name: str, datetimes: list[datetime], values: list[float], snowfall_values: list[float] | None = None) -> None:
        """Add a plot showing monthly and weekly cumulated values.

        :param main_data_name: Title for the plot.
        :type main_data_name: str
        :param datetimes: List of datetime objects corresponding to values.
        :type datetimes: list[datetime]
        :param values: Time series values to aggregate.
        :type values: list[float]
        :param snowfall_values: Optional snowfall values to also plot cumulated weekly and monthly, defaults to None.
        :type snowfall_values: list[float] | None, optional
        """
        fig, axis = plt.subplots(figsize=plot_size)

        month_accumulator, month_cumulated_precipitations = list(), list()
        month_snowfall_accumulator, month_cumulated_snowfalls = list(), list()
        current_month_number: int = datetimes[0].month
        week_accumulator, week_cumulated_precipitations = list(), list()
        week_snowfall_accumulator, week_cumulated_snowfalls = list(), list()
        week_number: int = datetimes[0].isocalendar().week

        for k, precipitation_mm_per_hour in enumerate(values):

            month: int = datetimes[k].month
            if current_month_number != month or k == len(values)-1:
                month_quantity = sum(month_accumulator)
                month_cumulated_precipitations.extend([month_quantity for _ in range(len(month_accumulator))])
                month_accumulator: list[float] = [precipitation_mm_per_hour]
                if snowfall_values is not None:
                    month_snowfall_quantity = sum(month_snowfall_accumulator)
                    month_cumulated_snowfalls.extend([month_snowfall_quantity for _ in range(len(month_snowfall_accumulator))])
                    month_snowfall_accumulator: list[float] = [snowfall_values[k] if k < len(snowfall_values) else 0.0]
                current_month_number = month
            else:
                month_accumulator.append(precipitation_mm_per_hour)
                if snowfall_values is not None:
                    month_snowfall_accumulator.append(snowfall_values[k] if k < len(snowfall_values) else 0.0)

            week: int = datetimes[k].isocalendar().week
            if week_number != week or k == len(values)-1:
                week_quantity = sum(week_accumulator)
                week_cumulated_precipitations.extend([week_quantity for _ in range(len(week_accumulator))])
                week_accumulator: list[float] = [precipitation_mm_per_hour]
                if snowfall_values is not None:
                    week_snowfall_quantity = sum(week_snowfall_accumulator)
                    week_cumulated_snowfalls.extend([week_snowfall_quantity for _ in range(len(week_snowfall_accumulator))])
                    week_snowfall_accumulator: list[float] = [snowfall_values[k] if k < len(snowfall_values) else 0.0]
                week_number = week
            else:
                week_accumulator.append(precipitation_mm_per_hour)
                if snowfall_values is not None:
                    week_snowfall_accumulator.append(snowfall_values[k] if k < len(snowfall_values) else 0.0)

        axis.stairs(month_cumulated_precipitations, datetimes, fill=True, color='cyan', label='Monthly cumulated precipitation', alpha=0.6)
        axis.stairs(week_cumulated_precipitations, datetimes, fill=True, color='pink', label='Weekly cumulated precipitation', alpha=0.6)
        if snowfall_values is not None:
            axis.stairs(month_cumulated_snowfalls, datetimes, fill=True, color='lightblue', label='Monthly cumulated snowfall', alpha=0.8)
            axis.stairs(week_cumulated_snowfalls, datetimes, fill=True, color='lightcoral', label='Weekly cumulated snowfall', alpha=0.8)
        axis.set_xlabel('times')
        axis.set_ylabel('quantity (mm)')
        axis.set_title(main_data_name)
        axis.legend()
        self.add_figure()

    def add_time_plot(self, main_data_name: str, datetimes: list[datetime], values: list[float], datetime_marks: list[datetime] = [], value_marks: list[float] = [], heating_period_indices: tuple = None, cooling_period_indices: tuple = None, **other_values: list[float]) -> None:
        """Add a time series plot to the report.

        :param main_data_name: Title for the plot.
        :type main_data_name: str
        :param datetimes: List of datetime objects for the x-axis.
        :type datetimes: list[datetime]
        :param values: Main time series values to plot.
        :type values: list[float]
        :param datetime_marks: Optional vertical lines at specific datetimes, defaults to [].
        :type datetime_marks: list[datetime], optional
        :param value_marks: Optional horizontal lines at specific values, defaults to [].
        :type value_marks: list[float], optional
        :param heating_period_indices: Optional tuple of heating period indices (start, end) or (start1, end1, start2, end2), defaults to None.
        :type heating_period_indices: tuple, optional
        :param cooling_period_indices: Optional tuple of cooling period indices (start, end) or (start1, end1, start2, end2), defaults to None.
        :type cooling_period_indices: tuple, optional
        :param other_values: Additional time series to plot as dashed lines (keyword arguments).
        :type other_values: list[float]
        """
        _, axis = plt.subplots(figsize=plot_size)
        
        # Add background colors for heating and cooling periods (before plotting lines)
        min_value, max_value = None, None
        for i in range(len(values)):
            if values[i] is not None:
                if min_value is None:
                    min_value = values[i]
                    max_value = values[i]
                else:
                    min_value = min(min_value, values[i])
                    max_value = max(max_value, values[i])
        
        # Add heating period background (light red)
        if heating_period_indices is not None:
            if len(heating_period_indices) == 2:
                axis.axvspan(datetimes[heating_period_indices[0]], datetimes[heating_period_indices[1]], color='red', alpha=0.15, zorder=0)
            elif len(heating_period_indices) == 4:
                axis.axvspan(datetimes[0], datetimes[heating_period_indices[1]], color='red', alpha=0.15, zorder=0)
                axis.axvspan(datetimes[heating_period_indices[2]], datetimes[-1], color='red', alpha=0.15, zorder=0)

        # Add cooling period background (light orange)
        if cooling_period_indices is not None:
            if len(cooling_period_indices) == 2:
                axis.axvspan(datetimes[cooling_period_indices[0]], datetimes[cooling_period_indices[1]], color='orange', alpha=0.15, zorder=0)
            elif len(cooling_period_indices) == 4:
                axis.axvspan(datetimes[0], datetimes[cooling_period_indices[1]], color='orange', alpha=0.15, zorder=0)
                axis.axvspan(datetimes[cooling_period_indices[2]], datetimes[-1], color='orange', alpha=0.15, zorder=0)
        
        axis.plot(datetimes, values, alpha=1)
        for series_name in other_values:
            # Use solid lines for monthly energy need and PV energy produced
            if series_name in ('monthly_energy_need_kWh', 'monthly_PV_energy_produced_all_usages_kWh', 'monthly_PV_energy_produced_hvac_kWh'):
                axis.plot(datetimes, other_values[series_name], '-', alpha=1, linewidth=2)
            else:
                axis.plot(datetimes, other_values[series_name], ':', alpha=.7, linewidth=2)
        for datetime_mark in datetime_marks:
            axis.plot([datetime_mark, datetime_mark], [min_value, max_value], 'r-.', alpha=0.5)
        for value_mark in value_marks:
            axis.plot([datetimes[0], datetimes[-1]], [value_mark, value_mark], 'r-.', alpha=0.5)
        if len(other_values) > 0:
            legends: list[str] = [main_data_name]
            legends.extend([value_name.replace('_', ' ') for value_name in other_values])
            axis.legend(legends)
            axis.grid()
        self.add_figure()

    def add_monotonic(self, title: str, datetimes: list[datetime], values: list[float], datetime_marks: list[datetime] = [], value_marks: list[float] = []) -> None:
        """Add a monotonic plot showing value distribution sorted in descending order.

        The x-axis represents the percentage of values higher than the corresponding
        value. The right y-axis shows month numbers indicating when values occurred.

        :param title: Title for the plot.
        :type title: str
        :param datetimes: List of datetime objects corresponding to values.
        :type datetimes: list[datetime]
        :param values: Time series values to plot.
        :type values: list[float]
        :param datetime_marks: Optional vertical lines at specific datetimes, defaults to [].
        :type datetime_marks: list[datetime], optional
        :param value_marks: Optional horizontal lines at specific values, defaults to [].
        :type value_marks: list[float], optional
        """
        indices: list[float] = [100*i/(len(values)-1) for i in range(len(values))]
        sorted_months, sorted_outdoor_temperatures = sort_values(datetimes, values)
        _, axis = plt.subplots(figsize=plot_size)
        axis.fill_between(indices, sorted_outdoor_temperatures, alpha=1)
        min_value, max_value = min(values), max(values)
        avg_value: float = (sum(values) / len(values))
        for datetime_mark in datetime_marks:
            axis.plot([datetime_mark, datetime_mark], [min_value, max_value], 'r:')
        for value_mark in value_marks:
            axis.plot([0, 100], [value_mark, value_mark], 'r:')
        axis.plot([0, 100], [avg_value, avg_value], 'b')
        axis.set_xlim(left=0, right=100)
        axis.grid(True)
        axis.set_xlabel('% of the year')
        axis.set_ylabel(title)
        for label in axis.get_xticklabels():
            label.set_visible(True)
        ax2 = axis.twinx()
        ax2.plot(indices, sorted_months, '.c')
        ax2.set_ylabel('month number')
        plt.tight_layout()
        self.add_figure()

    def add_windrose(self, wind_directions_deg: list[float], wind_speeds_m_s: list[float], direction_bins: int = 16, speed_bins: int = 20, to_km_h: bool = True) -> None:
        """Add a windrose plot showing wind direction and speed distribution.

        :param wind_directions_deg: Wind directions in degrees (meteorological convention: direction from which wind comes).
        :type wind_directions_deg: list[float]
        :param wind_speeds_m_s: Wind speeds in meters per second.
        :type wind_speeds_m_s: list[float]
        :param direction_bins: Number of direction bins for the windrose, defaults to 16.
        :type direction_bins: int, optional
        :param speed_bins: Number of speed bins for the windrose, defaults to 20.
        :type speed_bins: int, optional
        :param to_km_h: Whether to convert speeds to km/h for display, defaults to True.
        :type to_km_h: bool, optional
        :raises ImportError: Raised if windrose module is not available.
        """
        if WindroseAxes is None:
            raise ImportError("windrose module is required for windrose plots. Install it with: pip install windrose")
        if to_km_h:
            wind_speeds_km_h = [speed * 3.6 for speed in wind_speeds_m_s]
        ax = WindroseAxes.from_ax()
        ax.contourf(direction=wind_directions_deg, var=wind_speeds_km_h, bins=speed_bins, normed=True, cmap=cm.hot)
        ax.contour(direction=wind_directions_deg, var=wind_speeds_km_h, bins=speed_bins, normed=True, colors='black', linewidth=.5)
        ax.set_legend()
        ax.set_xlabel('radius stands for number of occurrences')
        ax.set_title('windrose where color stands for wind speed in km/h')
        ax.yaxis.set_major_formatter(PercentFormatter(100))
        self.add_figure()

    def add_histogram(self, title: str | list[str], values: list[float], max_range: float, categories: int | list[str]) -> None:
        """Add a histogram plot to the report.

        :param title: Title or list of titles for the histogram.
        :type title: str | list[str]
        :param values: Values to create histogram from.
        :type values: list[float]
        :param max_range: Maximum value for the histogram range.
        :type max_range: float
        :param categories: Number of bins or list of category labels.
        :type categories: int | list[str]
        :raises ImportError: Raised if windrose module is not available.
        """
        if type(categories) not in (int, float):
            width = max_range * .8 / len(categories)
            # value_counts, value_bin_edges = numpy.histogram(values, bins, range=(0, max_range))
            categories = len(categories)
        else:
            width = .8
        value_counts, category_bin_edges = numpy.histogram(values, categories, range=(0, max_range))
        if WindAxes is None:
            raise ImportError("windrose module is required for histogram plots. Install it with: pip install windrose")
        ax = WindAxes.from_ax()
        ax.bar(category_bin_edges[:-1], [count/len(values) for count in value_counts], width=width, align='center')
        if type(categories) not in (int, float):
            ax.set_xticks(category_bin_edges[:-1])
            ax.set_xticklabels(categories)
        ax.grid()
        ax.set_xlabel(title)
        ax.set_ylabel('probability')
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        self.add_figure()

    def add_wind_distributions(self, wind_speeds_km_h: list[float], wind_directions_deg: list[float]) -> None:
        """Add a combined figure with wind speed and direction distributions.

        Creates a single figure with two subplots: one for wind speed distribution
        and one for wind direction distribution.

        :param wind_speeds_km_h: Wind speeds in km/h.
        :type wind_speeds_km_h: list[float]
        :param wind_directions_deg: Wind directions in degrees.
        :type wind_directions_deg: list[float]
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Subplot 1: Wind speed distribution
        max_speed = max(wind_speeds_km_h)
        value_counts, category_bin_edges = numpy.histogram(wind_speeds_km_h, 20, range=(0, max_speed))
        width = 0.8 * (category_bin_edges[1] - category_bin_edges[0])
        ax1.bar(category_bin_edges[:-1], [count/len(wind_speeds_km_h) for count in value_counts], width=width, align='center')
        ax1.grid()
        ax1.set_xlabel('Wind speed (km/h)')
        ax1.set_ylabel('Probability')
        ax1.yaxis.set_major_formatter(PercentFormatter(1))
        ax1.set_title('Wind speed distribution over the year')

        # Subplot 2: Wind direction distribution
        direction_categories = ('N', '', 'N-E', '', 'E', '', 'S-E', '', 'S', '', 'S-W', '', 'W', '', 'N-W', '')
        direction_width = 360 * 0.8 / len(direction_categories)
        value_counts_dir, category_bin_edges_dir = numpy.histogram(wind_directions_deg, len(direction_categories), range=(0, 360))
        ax2.bar(category_bin_edges_dir[:-1], [count/len(wind_directions_deg) for count in value_counts_dir], width=direction_width, align='center')
        ax2.set_xticks(category_bin_edges_dir[:-1])
        ax2.set_xticklabels(direction_categories)
        ax2.grid()
        ax2.set_xlabel('Wind direction (coming from)')
        ax2.set_ylabel('Probability')
        ax2.yaxis.set_major_formatter(PercentFormatter(1))
        ax2.set_title('Wind direction distribution over the year')

        fig.tight_layout()
        # Save the figure - add_figure will use plt.savefig when fig is None
        # Make sure this figure is the current one for plt.savefig
        plt.figure(fig.number)
        self.add_figure()

    def add_givoni_diagram(self, dry_bulb_temperature_deg: list[float], absolute_humidity_kg_kg: list[float], chart_name: str = '') -> None:
        """Add a psychrometric (Givoni) diagram to the report.

        :param dry_bulb_temperature_deg: Dry bulb temperatures in degrees Celsius.
        :type dry_bulb_temperature_deg: list[float]
        :param absolute_humidity_kg_kg: Absolute humidity values in kg/kg.
        :type absolute_humidity_kg_kg: list[float]
        :param chart_name: Optional name for the chart, defaults to ''.
        :type chart_name: str, optional
        :note: Requires psychrochart library to be installed.
        """
        from matplotlib.patches import Polygon

        chart: PsychroChart = PsychroChart.create()
        plt.figure()
        axes = chart.plot(ax=plt.gca())

        # Define comfort zone boundaries
        temp_min = 20.0  # °C
        temp_max = 25.0  # °C
        rh_min = 0.20    # 20%
        rh_max = 0.80    # 80%

        # Calculate absolute humidity at the four corners of the comfort zone
        # Using psychrometric equations: W = 0.622 * (Pw / (P - Pw))
        # where Pw = RH * Pws, and Pws is saturation pressure
        # Approximate formula: Pws ≈ 611.2 * exp(17.67 * T / (T + 243.5)) in Pa
        # W ≈ 0.622 * (RH * Pws) / (101325 - RH * Pws) in kg/kg

        def calc_abs_humidity(temp_c: float, rh: float) -> float:
            """Calculate absolute humidity from temperature and relative humidity."""
            # Saturation vapor pressure in Pa
            pws = 611.2 * numpy.exp(17.67 * temp_c / (temp_c + 243.5))
            # Vapor pressure
            pw = rh * pws
            # Absolute humidity in kg/kg
            w = 0.622 * pw / (101325 - pw)
            return w * 1000  # Convert to g/kg for display

        # Get absolute humidity at the four corners
        abs_hum_min_temp_min_rh = calc_abs_humidity(temp_min, rh_min)  # 20°C, 20% RH
        abs_hum_max_temp_min_rh = calc_abs_humidity(temp_min, rh_max)  # 20°C, 80% RH
        abs_hum_min_temp_max_rh = calc_abs_humidity(temp_max, rh_min)  # 25°C, 20% RH
        abs_hum_max_temp_max_rh = calc_abs_humidity(temp_max, rh_max)  # 25°C, 80% RH

        # Draw comfort zone as a polygon (since RH lines are curved, use corners)
        # Create polygon vertices: lower-left, upper-left, upper-right, lower-right
        comfort_zone = Polygon([
            [temp_min, abs_hum_min_temp_min_rh],  # Lower left (20°C, 20% RH)
            [temp_min, abs_hum_max_temp_min_rh],  # Upper left (20°C, 80% RH)
            [temp_max, abs_hum_max_temp_max_rh],  # Upper right (25°C, 80% RH)
            [temp_max, abs_hum_min_temp_max_rh],   # Lower right (25°C, 20% RH)
        ], closed=True, edgecolor='green', facecolor='none', linewidth=2.5, linestyle='-', label='Comfort zone')

        axes.add_patch(comfort_zone)
        
        axes.scatter(dry_bulb_temperature_deg, [1000*h for h in absolute_humidity_kg_kg], marker='o', alpha=.1)
        axes.set_title("Psychrometric diagram: %s" % chart_name)
        self.add_figure()

    def add_monthly_heatmap(self, title: str, datetimes: list[datetime], values: list[float], value_label: str = '') -> None:
        """Add a monthly heatmap showing values organized by month and day.

        Creates a heatmap with months (1-12) on x-axis, days (1-31) on y-axis,
        and values represented by color intensity.

        :param title: Title for the heatmap.
        :type title: str
        :param datetimes: List of datetime objects corresponding to values.
        :type datetimes: list[datetime]
        :param values: Values to display in the heatmap.
        :type values: list[float]
        :param value_label: Label for the colorbar (e.g., 'cloudiness %').
        :type value_label: str
        """
        # Initialize a 2D array: rows = days (1-31), columns = months (1-12)
        # Use NaN for days that don't exist in a month
        heatmap_data = numpy.full((31, 12), numpy.nan)
        value_counts = numpy.zeros((31, 12))  # Track number of values per day for averaging
        
        # Fill the heatmap with hourly values, averaging by day
        for i, dt in enumerate(datetimes):
            month_idx = dt.month - 1  # 0-11
            day_idx = dt.day - 1  # 0-30
            
            if numpy.isnan(heatmap_data[day_idx, month_idx]):
                heatmap_data[day_idx, month_idx] = values[i]
                value_counts[day_idx, month_idx] = 1
            else:
                # Average multiple hourly values for the same day
                current_sum = heatmap_data[day_idx, month_idx] * value_counts[day_idx, month_idx]
                heatmap_data[day_idx, month_idx] = (current_sum + values[i]) / (value_counts[day_idx, month_idx] + 1)
                value_counts[day_idx, month_idx] += 1
        
        # Calculate monthly averages
        monthly_averages = []
        for month_idx in range(12):
            month_data = heatmap_data[:, month_idx]
            valid_data = month_data[~numpy.isnan(month_data)]
            if len(valid_data) > 0:
                monthly_averages.append(numpy.mean(valid_data))
            else:
                monthly_averages.append(numpy.nan)
        
        # Create extended heatmap data with monthly averages as bottom row
        # Add a row at the bottom for monthly averages
        extended_heatmap_data = numpy.full((32, 12), numpy.nan)
        extended_heatmap_data[:31, :] = heatmap_data  # Copy original data
        extended_heatmap_data[31, :] = monthly_averages  # Add monthly averages as bottom row
        
        # Create the heatmap
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Use imshow with reversed y-axis so day 1 is at the top
        im = ax.imshow(extended_heatmap_data, aspect='auto', cmap='YlGnBu', interpolation='nearest', origin='upper')
        
        # Set x-axis: months
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ax.set_xticks(range(12))
        ax.set_xticklabels(month_names)
        ax.set_xlabel('Month')
        
        # Set y-axis: days (show every 5 days for readability) + monthly average row
        y_ticks = list(range(0, 31, 5)) + [31]  # Add tick for monthly average row
        y_labels = [str(i) for i in range(1, 32, 5)] + ['Avg']
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        ax.set_ylabel('Day of month / Monthly average')
        
        # Add text annotations for monthly averages in the bottom row (without units)
        for month_idx in range(12):
            if not numpy.isnan(monthly_averages[month_idx]):
                text = f'{monthly_averages[month_idx]:.1f}'
                ax.text(month_idx, 31, text, ha='center', va='center', fontweight='bold',
                        color='white' if monthly_averages[month_idx] > numpy.nanmean(monthly_averages) else 'black',
                        fontsize=9)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        if value_label:
            cbar.set_label(value_label, rotation=270, labelpad=20)
        
        ax.set_title(title.replace('_', ' '))
        self.add_figure()

    def add_barchart(self, title: str, ylabel: str, **category_series_sets: dict[str, float] | dict[str, dict[str, float]]) -> None:
        """Add a bar chart with a title and y-axis label.

        Supports both simple bar charts (single value per category) and
        grouped bar charts (multiple series per category).

        :param title: Title for the bar chart.
        :type title: str
        :param ylabel: Label for the y-axis.
        :type ylabel: str
        :param category_series_sets: Dictionary of category names to values or series dictionaries.
        :type category_series_sets: dict[str, float] | dict[str, dict[str, float]]
        """
        category_names: list[str] = list(category_series_sets.keys())
        fig, ax = plt.subplots(tight_layout=True, figsize=plot_size)

        if not isinstance(category_series_sets[category_names[0]], (int, float)):
            width = 1/len(category_names)
            bars = list()
            for series_position, series_set_name in enumerate(category_series_sets):
                series = category_series_sets[series_set_name]
                w = width / (len(series)-1)
                for i, series_name in enumerate(series):
                    bars.append(ax.bar(series_position - width + i * w, round(series[series_name], 1), w, label=series_name))
            ax.set_xticks([p - width/2 for p in range(len(category_series_sets))], category_names)
            for bar in bars:
                ax.bar_label(bar, padding=3)
            ax.legend()
        else:
            ax.bar(x=[i for i in range(len(category_names))], height=[round(category_series_sets[category_name], 1) for category_name in category_series_sets], label=[category_name for category_name in category_series_sets])
            ax.set_xticks([p for p in range(len(category_series_sets))], category_names)

        ax.set_ylabel(ylabel)
        ax.set_title(title.replace('_', ' '))
        self.add_figure()

    def add_monthly_trend(self, title: str, datetimes: list[datetime], values: list[float], average: bool = True) -> None:
        """Add a polar plot showing monthly trends over multiple years.

        :param title: Title for the plot.
        :type title: str
        :param datetimes: List of datetime objects corresponding to values.
        :type datetimes: list[datetime]
        :param values: Time series values to aggregate.
        :type values: list[float]
        :param average: If True, compute monthly averages; if False, compute monthly sums, defaults to True.
        :type average: bool, optional
        """
        class YearMonthData:

            def __init__(self) -> None:
                self.month_data = dict()
                self.months = list()

            def add(self, datetime, value):
                month_name = datetime.strftime('%b')
                if month_name not in self.months:
                    self.month_data[month_name] = list()
                    self.months.append(month_name)
                self.month_data[month_name].append(value)

            def data(self) -> tuple[list, list]:
                months_value = dict()
                for month in self.months:
                    if month in self.month_data:
                        try:
                            if average:
                                months_value[month] = sum(self.month_data[month]) / len(self.month_data[month])
                            else:
                                months_value[month] = sum(self.month_data[month])
                        except:  # noqa
                            months_value[month] = None
                return self.months, [months_value[month] for month in self.months]

        year_monthly_values = dict()
        for i, dt in enumerate(datetimes):
            if dt.year not in year_monthly_values:
                year_monthly_values[dt.year] = YearMonthData()
            year_monthly_values[dt.year].add(dt, values[i])

        fig = go.Figure()  # create a figure
        if len(year_monthly_values) > 0:
            colors = ['rgb(%i,%i,%i)' % (255-i*255/len(year_monthly_values), abs(128-i*255/len(year_monthly_values)), i*255/len(year_monthly_values)) for i in range(len(year_monthly_values))]   # Get the colors

            for i, year in enumerate(year_monthly_values):  # Plot each year with a corresponding color
                months, values = year_monthly_values[year].data()
                fig.add_trace(go.Scatterpolar(r=values, theta=months, name=str(year), line_color=colors[i]))
            fig.update_layout(autosize=False, width=1000, height=800, title=title)  # Adjust the size of the figure
        self.add_figure(fig=fig)

    def add_annual_temperature_trend(self, title: str, datetimes: list[datetime], temperatures: list[float], reference_year: int, start_year: int = 1980) -> None:
        """Add a plot showing annual average temperature trend from start_year to reference_year.

        Calculates the average temperature for each year and displays a trend line
        with the slope in °C/year.

        :param title: Title for the plot.
        :type title: str
        :param datetimes: List of datetime objects corresponding to temperatures.
        :type datetimes: list[datetime]
        :param temperatures: Temperature values in degrees Celsius.
        :type temperatures: list[float]
        :param reference_year: Reference year (end year for the analysis).
        :type reference_year: int
        :param start_year: Starting year for the analysis, defaults to 1980.
        :type start_year: int, optional
        """
        # Calculate annual average temperatures
        year_temperatures: dict[int, list[float]] = {}
        for i, dt in enumerate(datetimes):
            year = dt.year
            if start_year <= year <= reference_year:
                if year not in year_temperatures:
                    year_temperatures[year] = []
                if temperatures[i] is not None:
                    year_temperatures[year].append(temperatures[i])

        # Calculate average temperature for each year
        years = sorted(year_temperatures.keys())
        avg_temperatures = [sum(year_temperatures[year]) / len(year_temperatures[year]) for year in years]

        if len(years) < 2:
            # Not enough data for trend analysis
            return

        # Calculate linear trend using numpy
        years_array = numpy.array(years)
        temps_array = numpy.array(avg_temperatures)

        # Linear regression: y = a*x + b
        # Using numpy.polyfit for degree 1 (linear)
        coeffs = numpy.polyfit(years_array, temps_array, 1)
        slope = coeffs[0]  # °C per year
        intercept = coeffs[1]

        # Calculate trend line
        trend_line = slope * years_array + intercept

        # Create the plot
        fig, axis = plt.subplots(figsize=plot_size)
        
        # Plot data points
        axis.scatter(years, avg_temperatures, alpha=0.6, s=50, label='Annual average temperature', color='blue')
        
        # Plot trend line
        axis.plot(years, trend_line, 'r-', linewidth=2, label=f'Trend: {slope:.4f} °C/year', alpha=0.8)
        
        axis.set_xlabel('Year')
        axis.set_ylabel('Average temperature (°C)')
        axis.set_title(f'{title}\nTrend: {slope:.4f} °C/year')
        axis.legend()
        axis.grid(True, alpha=0.3)
        
        self.add_figure()

    def add_annual_rainfall_trend(self, title: str, datetimes: list[datetime], precipitations: list[float], reference_year: int, start_year: int = 1980) -> None:
        """Add a plot showing annual cumulative rainfall trend from start_year to reference_year.

        Calculates the cumulative rainfall for each year and displays a trend line
        with the slope in mm/year.

        :param title: Title for the plot.
        :type title: str
        :param datetimes: List of datetime objects corresponding to precipitations.
        :type datetimes: list[datetime]
        :param precipitations: Precipitation values in mm (typically mm/hour).
        :type precipitations: list[float]
        :param reference_year: Reference year (end year for the analysis).
        :type reference_year: int
        :param start_year: Starting year for the analysis, defaults to 1980.
        :type start_year: int, optional
        """
        # Calculate annual cumulative rainfall
        year_precipitations: dict[int, list[float]] = {}
        for i, dt in enumerate(datetimes):
            year = dt.year
            if start_year <= year <= reference_year:
                if year not in year_precipitations:
                    year_precipitations[year] = []
                if precipitations[i] is not None and precipitations[i] >= 0:
                    year_precipitations[year].append(precipitations[i])

        # Calculate cumulative rainfall for each year (sum of all precipitation values)
        years = sorted(year_precipitations.keys())
        cumulative_rainfall = [sum(year_precipitations[year]) for year in years]

        if len(years) < 2:
            # Not enough data for trend analysis
            return

        # Calculate linear trend using numpy
        years_array = numpy.array(years)
        rainfall_array = numpy.array(cumulative_rainfall)

        # Linear regression: y = a*x + b
        # Using numpy.polyfit for degree 1 (linear)
        coeffs = numpy.polyfit(years_array, rainfall_array, 1)
        slope = coeffs[0]  # mm per year
        intercept = coeffs[1]

        # Calculate trend line
        trend_line = slope * years_array + intercept

        # Create the plot
        fig, axis = plt.subplots(figsize=plot_size)

        # Plot data points
        axis.scatter(years, cumulative_rainfall, alpha=0.6, s=50, label='Annual cumulative rainfall', color='blue')

        # Plot trend line
        axis.plot(years, trend_line, 'r-', linewidth=2, label=f'Trend: {slope:.2f} mm/year', alpha=0.8)

        axis.set_xlabel('Year')
        axis.set_ylabel('Cumulative rainfall (mm)')
        axis.set_title(f'{title}\nTrend: {slope:.2f} mm/year')
        axis.legend()
        axis.grid(True, alpha=0.3)
        self.add_figure()

    def add_monthly_daily_balance_histogram(self, title: str, datetimes: list[datetime], pv_production_W: list[float], electricity_needs_W: list[float]) -> None:
        """Add a 3x4 histogram grid showing daily electricity balance by month.

        Creates a figure with 12 subplots (3 rows, 4 columns) representing the 12 months.
        Each subplot shows a histogram of daily electricity balance values for that month.
        Positive values indicate PV surplus (covers needs), negative values indicate deficit.

        :param title: Title for the overall figure.
        :type title: str
        :param datetimes: List of datetime objects corresponding to hourly data.
        :type datetimes: list[datetime]
        :param pv_production_W: Hourly PV production values in watts.
        :type pv_production_W: list[float]
        :param electricity_needs_W: Hourly electricity needs values in watts.
        :type electricity_needs_W: list[float]
        """
        # Calculate hourly balance (PV - needs) in watts
        hourly_balance_W = [pv_production_W[i] - electricity_needs_W[i] for i in range(len(electricity_needs_W))]
        
        # Group hourly data by day and calculate daily balance
        daily_balance_kWh: dict[tuple[int, int], list[float]] = {}  # (month, day) -> list of daily balances
        current_date = None
        daily_balance_sum_W = 0.0
        hour_count = 0
        
        for i, dt in enumerate(datetimes):
            if current_date is None or dt.date() != current_date:
                # Save previous day's balance if exists
                if current_date is not None and hour_count > 0:
                    daily_balance_kWh_value = daily_balance_sum_W / 1000.0  # Convert to kWh
                    month_day = (current_date.month, current_date.day)
                    if month_day not in daily_balance_kWh:
                        daily_balance_kWh[month_day] = []
                    daily_balance_kWh[month_day].append(daily_balance_kWh_value)
                
                # Start new day
                current_date = dt.date()
                daily_balance_sum_W = hourly_balance_W[i]
                hour_count = 1
            else:
                daily_balance_sum_W += hourly_balance_W[i]
                hour_count += 1
        
        # Handle last day
        if current_date is not None and hour_count > 0:
            daily_balance_kWh_value = daily_balance_sum_W / 1000.0  # Convert to kWh
            month_day = (current_date.month, current_date.day)
            if month_day not in daily_balance_kWh:
                daily_balance_kWh[month_day] = []
            daily_balance_kWh[month_day].append(daily_balance_kWh_value)
        
        # Create 3x4 grid of subplots (12 months)
        fig, axes = plt.subplots(3, 4, figsize=(16, 12))
        fig.suptitle(title, fontsize=14, fontweight='bold')
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for month_idx in range(12):
            row = month_idx // 4
            col = month_idx % 4
            ax = axes[row, col]
            
            # Collect all daily balances for this month
            month_balances = []
            for (m, d), balances in daily_balance_kWh.items():
                if m == month_idx + 1:  # month_idx is 0-based, month is 1-based
                    month_balances.extend(balances)
            
            if month_balances:
                # Create histogram
                ax.hist(month_balances, bins=20, edgecolor='black', alpha=0.7)
                ax.axvline(x=0, color='red', linestyle='--', linewidth=1.5, label='Balance = 0')
                ax.set_xlabel('Daily Balance (kWh)')
                ax.set_ylabel('Frequency')
                ax.set_title(f'{month_names[month_idx]}')
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                # Add statistics text
                min_balance = min(month_balances)
                max_balance = max(month_balances)
                mean_balance = sum(month_balances) / len(month_balances)
                stats_text = f'Range: [{min_balance:.1f}, {max_balance:.1f}] kWh\nMean: {mean_balance:.1f} kWh'
                ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                        fontsize=8)
            else:
                ax.text(0.5, 0.5, 'No data', transform=ax.transAxes,
                        ha='center', va='center', fontsize=12)
                ax.set_title(f'{month_names[month_idx]}')
        
        plt.tight_layout()
        # Save directly using the figure object to ensure correct figure is saved
        if not self.on_screen:
            figure_name: str = LambdaParametricData.setup('folders', 'figures') + 'figure%i.png' % self.figure_counter
            self.figure_counter += 1
            fig.savefig(LambdaParametricData.setup('folders', 'results') + figure_name, dpi=600, bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            # Add newline before figure for proper PDF rendering
            self.add_text('\n![](%s)' % figure_name)
        else:
            plt.figure(fig.number)  # Make it current for plt.show
            plt.show()
            plt.close(fig)

    def add_parametric(self, parameter_name: str, parameter_values: list[float], left_indicators: dict[str, list[float]], left_label: str = '', right_indicators: dict[str, list[float]] | None = None, right_label: str = '') -> None:
        """Add a parametric analysis plot with two y-axes.

        :param parameter_name: Name of the parameter being analyzed.
        :type parameter_name: str
        :param parameter_values: List of parameter values tested.
        :type parameter_values: list[float]
        :param left_indicators: Dictionary of indicator names and values for left y-axis.
        :type left_indicators: dict[str, list[float]]
        :param left_label: Label for the left y-axis.
        :type left_label: str, optional
        :param right_indicators: Optional dictionary of indicator names and values for right y-axis.
        :type right_indicators: dict[str, list[float]] | None, optional
        :param right_label: Label for the right y-axis.
        :type right_label: str, optional
        """
        # Check if all left indicators are null (or very close to zero)
        all_left_null = True
        null_left_indicators = []
        for indicator_name, indicator_values in left_indicators.items():
            if any(abs(v) > 1e-6 for v in indicator_values):
                all_left_null = False
            else:
                null_left_indicators.append(indicator_name)
        
        # Check if all right indicators are null (or very close to zero)
        all_right_null = True
        null_right_indicators = []
        if right_indicators is not None:
            for indicator_name, indicator_values in right_indicators.items():
                if any(abs(v) > 1e-6 for v in indicator_values):
                    all_right_null = False
                else:
                    null_right_indicators.append(indicator_name)
        else:
            all_right_null = False  # No right indicators to check
        
        # If all indicators are null, display a text message instead of a plot
        if all_left_null and (right_indicators is None or all_right_null):
            # Build message about which indicators are null
            null_indicators_list = null_left_indicators.copy()
            if right_indicators is not None:
                null_indicators_list.extend(null_right_indicators)
            
            indicator_names = ', '.join(null_indicators_list)
            self.add_text(f'**Note:** Parametric analysis for `{parameter_name.replace("_", " ")}` shows that all indicators ({indicator_names}) are null (zero) across all parameter values. No plot is generated.')
            return
        
        # If only some indicators are null, still create the plot but mention null indicators
        if null_left_indicators or null_right_indicators:
            null_indicators_list = null_left_indicators.copy()
            if right_indicators is not None:
                null_indicators_list.extend(null_right_indicators)
            indicator_names = ', '.join(null_indicators_list)
            self.add_text(f'**Note:** The following indicators are null (zero) for all parameter values: {indicator_names}. They are not shown in the plot.')
        
        fig, ax1 = plt.subplots(figsize=plot_size)

        # Only plot non-null indicators
        for i, indicator in enumerate(left_indicators):
            if indicator not in null_left_indicators:
                color = f'C{i}'
                ax1.plot(parameter_values, left_indicators[indicator], color=color, label=indicator)

        ax1.set_xlabel(parameter_name.replace('_', ' '))
        ax1.set_ylabel(left_label)
        ax1.grid()
        ax1.tick_params(axis='y')
        if len([ind for ind in left_indicators if ind not in null_left_indicators]) > 0:
            ax1.legend(loc='upper left')

        # Plot right indicators
        if right_indicators is not None:
            ax2 = ax1.twinx()
            for i, indicator in enumerate(right_indicators):
                if indicator not in null_right_indicators:
                    color = f'C{i+len([ind for ind in left_indicators if ind not in null_left_indicators])}'
                    ax2.plot(parameter_values, right_indicators[indicator], color=color, linestyle='--', label=indicator)

            ax2.set_ylabel(right_label)
            ax2.grid()
            ax2.tick_params(axis='y')
            if len([ind for ind in right_indicators if ind not in null_right_indicators]) > 0:
                ax2.legend(loc='upper right')

        fig.tight_layout()
        self.add_figure()  # fig=fig


class Analyzes:
    """Comprehensive analysis suite for building performance evaluation.

    This class provides a complete set of analysis methods for evaluating building
    performance across multiple dimensions including climate analysis, energy
    performance, thermal behavior, and solar energy utilization. It integrates
    simulation results with automated reporting and visualization capabilities.

    :param lpd: Lambda house parametric data with simulation results.
    :type lpd: LambdaParametricData
    :param on_screen: Whether to display reports on screen or save to file, defaults to True.
    :type on_screen: bool, optional
    :ivar report_generator: Report generator instance for creating analysis reports.
    :ivar lpd: Lambda house parametric data instance.
    :ivar datetimes: List of datetime objects for the analysis period.
    """

    def __init__(self, lpd: LambdaParametricData, on_screen: bool = True) -> None:
        """Initialize the analysis suite.

        :param lpd: Lambda house parametric data with simulation results.
        :type lpd: LambdaParametricData
        :param on_screen: Whether to display reports on screen or save to file, defaults to True.
        :type on_screen: bool, optional
        """
        self.report_generator: ReportGenerator = ReportGenerator(location=lpd.site_weather_data.location, year=lpd('year'), on_screen=on_screen)
        self.lpd: LambdaParametricData = lpd
        try:
            Simulator.run(self.lpd)  # first simulation is taken as reference (nominal)
            self.datetimes: list[datetime.datetime] = self.lpd('datetimes')
            # Fall back to site_weather_data.datetimes if datetimes is empty or None
            if self.datetimes is None or len(self.datetimes) == 0:
                self.datetimes = self.lpd.site_weather_data.datetimes
        except Exception as e:
            self.report_generator.add_text(f'**SIMULATION ERROR: {str(e)}**')
            self.report_generator.add_text('The building energy simulation failed. This will prevent house analysis from working properly.')
            import traceback
            self.report_generator.add_text(f'**Technical details:** {traceback.format_exc()}')
            # Fall back to site_weather_data.datetimes instead of empty list
            self.datetimes: list[datetime.datetime] = self.lpd.site_weather_data.datetimes if hasattr(self.lpd, 'site_weather_data') and self.lpd.site_weather_data else []

    def close(self, pdf: bool = True, latex_template: str | None = None, features: bool = True) -> None:
        """Close the analysis report and save it.

        :param pdf: Whether to generate a PDF version of the report, defaults to True.
        :type pdf: bool, optional
        :param latex_template: Optional path to a custom LaTeX template file for PDF generation, defaults to None.
        :type latex_template: str | None, optional
        """
        self.report_generator.close(str(self.lpd), pdf=pdf, latex_template=latex_template, features=features)

    def climate(self) -> None:
        """Perform comprehensive climate analysis.

        Analyzes outdoor temperature, precipitation, wind patterns, and outdoor
        comfort conditions. Generates plots and statistics for heating/cooling
        period detection, precipitation events, wind distribution, and thermal
        comfort assessment.
        """
        # Ensure self.datetimes is initialized from site_weather_data if empty or None
        if (self.datetimes is None or len(self.datetimes) == 0) and hasattr(self.lpd, 'site_weather_data') and self.lpd.site_weather_data:
            self.datetimes = self.lpd.site_weather_data.datetimes
        
        if self.datetimes is None or len(self.datetimes) == 0:
            self.report_generator.add_text('**ERROR: No datetime data available. Cannot generate climate analysis.**')
            return
        
        felt_temperatures_deg: list[float] = [OutdoorTemperatureIndices.feels_like(self.lpd('outdoor_temperatures_deg')[i], self.lpd('humidities_percentage')[i], self.lpd('wind_speeds_m_s')[i]) for i in range(len(self.datetimes))]
        self.report_generator.add_text('# Local climate Analysis <a name="climate"></a>')
        self.report_generator.add_text('## Analysis of the local outdoor temperature')
        self.report_generator.add_text('### Evolution of the outdoor and its averaged temperatures with detected heating and cooling periods')
        self.report_generator.add_text(f'The first time the averaged outdoor temperatures pass over the threshold "summer_hvac_trigger_temperature", here equal to {self.lpd("summer_hvac_trigger_temperature_deg")}°C determines the end of the heating period, and the last time it passed under, it determines the start of the heating period. Similarly, the first time the averaged outdoor temperature passes over the "winter_hvac_trigger_temperature" threshold, here equal to {self.lpd("winter_hvac_trigger_temperature_deg")}°C, determines the beginning the cooling period, and last time it passes down, the end.')

        datetime_marks: list[datetime.datetime] = []
        heating_period_indices: float = self.lpd('heating_period_indices')
        if heating_period_indices is not None and len(heating_period_indices) >= 2:
            max_index = len(self.datetimes) - 1
            if len(heating_period_indices) == 2:
                idx0, idx1 = int(heating_period_indices[0]), int(heating_period_indices[1])
                if 0 <= idx0 <= max_index and 0 <= idx1 <= max_index:
                    datetime_marks.append(self.datetimes[idx0])
                    datetime_marks.append(self.datetimes[idx1])
                    self.report_generator.add_text('- The detected heating period lasts from ' + datetime_to_stringdate(self.datetimes[idx0], date_format='%d %B') + ' to ' + datetime_to_stringdate(self.datetimes[idx1], date_format='%d %B') + '.\n')
            elif len(heating_period_indices) == 4:
                idx1, idx2 = int(heating_period_indices[1]), int(heating_period_indices[2])
                if 0 <= idx1 <= max_index and 0 <= idx2 <= max_index:
                    datetime_marks.append(self.datetimes[idx1])
                    datetime_marks.append(self.datetimes[idx2])
                    self.report_generator.add_text('- The detected heating period is actually composed of 2 periods: one from January 1st until ' + datetime_to_stringdate(self.datetimes[idx1], date_format='%d %B') + ' and another one from ' + datetime_to_stringdate(self.datetimes[idx2], date_format='%d %B') + ' to the end of the year.\n')
        self.report_generator.add_text('- The duration of the heating period is %d days.\n' % (round(self.lpd('heating_period_duration_h')/24)))

        cooling_period_indices: float = self.lpd('cooling_period_indices')
        if cooling_period_indices is not None and len(cooling_period_indices) >= 2:
            max_index = len(self.datetimes) - 1
            if len(cooling_period_indices) == 2:
                idx0, idx1 = int(cooling_period_indices[0]), int(cooling_period_indices[1])
                if 0 <= idx0 <= max_index and 0 <= idx1 <= max_index:
                    datetime_marks.append(self.datetimes[idx0])
                    datetime_marks.append(self.datetimes[idx1])
                    self.report_generator.add_text('- The detected cooling period lasts from ' + datetime_to_stringdate(self.datetimes[idx0], date_format='%d %B') + ' to ' + datetime_to_stringdate(self.datetimes[idx1], date_format='%d %B') + '.\n')
            elif len(cooling_period_indices) == 4:
                idx1, idx2 = int(cooling_period_indices[1]), int(cooling_period_indices[2])
                if 0 <= idx1 <= max_index and 0 <= idx2 <= max_index:
                    datetime_marks.append(self.datetimes[idx1])
                    datetime_marks.append(self.datetimes[idx2])
                    self.report_generator.add_text('- The detected cooling period is actually composed of 2 periods: one from January 1st until ' + datetime_to_stringdate(self.datetimes[idx1], date_format='%d %B') + ' and another one from ' + datetime_to_stringdate(self.datetimes[idx2], date_format='%d %B') + ' to the end of the year.\n')
        self.report_generator.add_text('- The duration of the cooling period is %d days.\n' % (round(self.lpd('cooling_period_duration_h')/24)))

        self.report_generator.add_text('This curve shows the local outdoor temperatures along with time during the reference year specified for the analysis. It comes from the [http://open-weather.com](http://open-weather.com) file. The orange curve is the averaged temperature values used to detect the heating and cooling periods. The red lines corresponds to the detection thresholds used to detect the heating and cooling periods.')
        self.report_generator.add_text('### Outdoor temperature and averaged values with heating/cooling periods')
        self.report_generator.add_time_plot('Outdoor temperature and averaged values', self.datetimes, self.lpd('outdoor_temperatures_deg'), datetime_marks=datetime_marks, value_marks=[self.lpd('winter_hvac_trigger_temperature_deg'), self.lpd('summer_hvac_trigger_temperature_deg')], averaged_values=self.lpd('smooth_outdoor_temperatures_for_hvac_periods_deg'))

        self.report_generator.add_text('The following figure is named a monotone. The values are not sorted with respect to the time but in a decreasing order: it corresponds to the curve filled with blue, left y-axis scale. The x-axis stands for the percentage of the values higher than the corresponding value given by the curve. It is therefore easy to analyse how values are distributed. On the right y-axis scale, the month number (1=January,..., 12=December) is given and the time where the value has been recorded is marked by a cyan dot.')
        self.report_generator.add_image('monotonic.png')

        self.report_generator.add_text('### Monotone of the outdoor temperatures in Celsius')
        self.report_generator.add_text('The following figure represents the distribution of the outdoor temperatures over the year. The cyan dots represent the date where the related outdoor temperature has been recorded. The red lines represents the detection thresholds for the heating and cooling periods.')
        self.report_generator.add_monotonic('Monotone of the outdoor temperatures in Celsius', self.datetimes, self.lpd('outdoor_temperatures_deg'), value_marks=(self.lpd('winter_hvac_trigger_temperature_deg'), self.lpd('summer_hvac_trigger_temperature_deg')))

        self.report_generator.add_text('## Analysis of the precipitations')
        self.report_generator.add_text('### Heatmap of the cloudiness in percentage of the sky covered by clouds')
        self.report_generator.add_text('The following heatmap represents the cloudiness distribution over the year. Each cell shows the average cloudiness percentage for a specific day of a specific month, with darker colors indicating higher cloudiness.')
        self.report_generator.add_monthly_heatmap('Cloudiness in percentage of the sky covered by clouds', self.datetimes, self.lpd('cloudiness_percentage'), value_label='Cloudiness (%)')

        self.report_generator.add_text('### Precipitations (rain + hail + snow) along time in mm/h')
        self.report_generator.add_text('It represents the precipitations (rain + hail + snow) along the year in mm/h. The dashed orange curve represents the cumulated snowfalls.')
        self.report_generator.add_time_plot('Precipitations', self.datetimes, self.lpd('precipitations_mm_per_hour'), snowfalls=self.lpd('snowfalls_mm_per_hour'))
        self.report_generator.add_text('### Rain, hail or snow events: duration, intensity and occurrences')
        self.report_generator.add_text('Here is a heatmap of the rain, hail and snow events: the color intensity represents the number of occurrences of each event situated in a 2D space where the x-axis represents the duration of precipitation events while the y-axis represents the quantity in mm of precipitations fallen during the event.')
        self.report_generator.add_event_plot('Rain, hail or snow', self.datetimes, self.lpd('precipitations_mm_per_hour'))
        self.report_generator.add_text('### Month & week cumulated rain, hail or snow')
        self.report_generator.add_text('It represents the cumulated rain, hail or snow over each month (in cyan) and week (in pink color). The monthly and weekly cumulated snowfall are also shown (in light blue and light coral, dashed lines).')
        
        self.report_generator.add_month_week_averages('Rain, hail or snow', self.datetimes, self.lpd('precipitations_mm_per_hour'), snowfall_values=self.lpd('snowfalls_mm_per_hour'))
        self.report_generator.add_text('## Analysis of the local wind')

        self.report_generator.add_text('The wind speeds and directions over a time period, are usually represented by a wind rose. The colors represent the speed of the wind and a radius stands for the so-called meteorological direction i.e. the direction from where the wind is coming from.')
        self.report_generator.add_windrose(self.lpd('wind_directions_deg'), self.lpd('wind_speeds_m_s'))

        self.report_generator.add_text('The following figure shows the wind speed and direction distributions over the year. The left subplot represents the wind speed distribution in km/h, and the right subplot represents the wind direction distribution. Like for the windrose, the direction is given in degrees and corresponds to where the wind is coming from.')
        wind_speeds_km_h = [3.6 * _ for _ in self.lpd('wind_speeds_m_s')]
        self.report_generator.add_wind_distributions(wind_speeds_km_h, self.lpd('wind_directions_deg'))

        self.report_generator.add_text('## Analysis of the outdoor comfort')
        self.report_generator.add_text('The following figure represents the Givoni diagram, which is a psychrometric chart. The comfort region is delimited by the [20°C, 25°C] temperature range and the [20%, 80%] relative humidity range.')

        min_feel_like_temperatures_deg: list[float] = list()
        max_feel_like_temperatures_deg: list[float] = list()
        avg_feel_like_temperatures_deg: list[float] = list()
        for i in range(len(self.datetimes)):
            if i < 72:
                min_feel_like_temperatures_deg.append(felt_temperatures_deg[i])
                max_feel_like_temperatures_deg.append(felt_temperatures_deg[i])
                avg_feel_like_temperatures_deg.append(felt_temperatures_deg[i])
            else:
                min_feel_like_temperatures_deg.append(min(felt_temperatures_deg[i-72:i]))
                max_feel_like_temperatures_deg.append(max(felt_temperatures_deg[i-72:i]))
                avg_feel_like_temperatures_deg.append(sum(felt_temperatures_deg[i-72:i]) / 72)
        
        # Detect tropical nights: nights where temperature doesn't pass below 20°C
        # A night is typically from 18:00 (6 PM) to 06:00 (6 AM) the next day
        tropical_night_datetimes: list[datetime.datetime] = []
        tropical_night_threshold = 20.0  # °C
        
        # Group datetimes by date to check each night once
        current_date = None
        for i in range(len(self.datetimes)):
            dt = self.datetimes[i]
            date = dt.date()
            hour = dt.hour

            # Check if this is 18:00 (start of a night) and we haven't checked this date yet
            if hour == 18 and date != current_date:
                current_date = date

                # Find the night period: from 18:00 to 6 AM next day
                # Look ahead to find 6 AM of the next day
                from datetime import timedelta
                night_end_idx = i
                for j in range(i, min(i + 15, len(self.datetimes))):
                    if self.datetimes[j].date() == date + timedelta(days=1) and self.datetimes[j].hour == 6:
                        night_end_idx = j
                        break
                else:
                    # If we didn't find 6 AM next day, use up to 12 hours ahead
                    night_end_idx = min(i + 12, len(self.datetimes) - 1)
                
                # Get temperatures during the night period
                night_temperatures = self.lpd('outdoor_temperatures_deg')[i:night_end_idx+1]
                
                # Check if minimum temperature during the night is >= 20°C
                if night_temperatures and min(night_temperatures) >= tropical_night_threshold:
                    # Mark the start of the night (18:00)
                    tropical_night_datetimes.append(dt)
        
        last_decile_feel_like_temperature: float = list(numpy.percentile(felt_temperatures_deg, [0, 90]))[-1]
        self.report_generator.add_text('The following figure is based on the felt temperatures along time. The red curve represents the minimum felt temperature over the last 3 days, the dashed red curve represents the maximum felt temperature over the last 3 days, the blue curve represents the average felt temperature over the last 3 days, and the horizontal red line represents the last decile of the felt temperature over the year. Blue vertical lines indicate tropical nights (nights where temperature does not pass below 20°C). It is an indicator for scorching periods: if the 3-days minimum felt temperature is reaching or passing over the horizontal line standing for the last year temperature decile, it reveals a scorching period.')
        
        # Create custom plot with specific colors and tropical night markers
        fig, axis = plt.subplots(figsize=plot_size)
        
        # Plot 3-day minimum felt temperature in red
        axis.plot(self.datetimes, min_feel_like_temperatures_deg, 'r-', alpha=1, linewidth=2, label='3 days min felt temperature')
        
        # Plot 3-day maximum felt temperature in dashed red
        axis.plot(self.datetimes, max_feel_like_temperatures_deg, 'r--', alpha=0.7, linewidth=2, label='3 days max felt temperature')
        
        # Plot 3-day average felt temperature in blue
        axis.plot(self.datetimes, avg_feel_like_temperatures_deg, 'b-', alpha=0.7, linewidth=2, label='3 days avg felt temperature')
        
        # Plot threshold line in red
        axis.plot([self.datetimes[0], self.datetimes[-1]], [last_decile_feel_like_temperature, last_decile_feel_like_temperature], 'r-.', alpha=0.5, linewidth=1.5, label='Last decile threshold')
        
        # Add blue vertical lines for tropical nights (more visible)
        tropical_night_line = None
        for tropical_night_dt in tropical_night_datetimes:
            line = axis.axvline(x=tropical_night_dt, color='blue', linestyle='--', alpha=0.7, linewidth=2)
            if tropical_night_line is None:
                tropical_night_line = line  # Store first line for legend
        
        # Add tropical nights to legend if any were found
        if tropical_night_line is not None:
            # Create a proxy artist for the legend
            from matplotlib.lines import Line2D
            tropical_night_proxy = Line2D([0], [0], color='blue', linestyle='--', linewidth=2, alpha=0.7, label='Tropical nights')
            # Get current legend handles and labels
            handles, labels = axis.get_legend_handles_labels()
            handles.append(tropical_night_proxy)
            labels.append('Tropical nights')
            axis.legend(handles, labels)
        else:
            axis.legend()
        
        axis.set_xlabel('Time')
        axis.set_ylabel('Felt temperature (°C)')
        axis.set_title('3 days min/max/avg Felt temperature')
        axis.grid()
        self.report_generator.add_figure()

    def evolution(self) -> None:
        """Analyze long-term climate evolution trends.

        Generates polar plots showing monthly trends over multiple years for
        temperature and precipitation, allowing identification of climate change
        patterns and long-term variations.
        """
        self.report_generator.add_text('# Long term climate Evolution <a name="evolution"></a>')
        self.report_generator.add_text('These curves represent the long term evolution of the weather variables. Each radius corresponds to a month. Each curve corresponds to a year with averaged month values. Yellow color stands for oldest years, violet for middle and blue to most recent years.')
        all_years_site_weather_data: SiteWeatherData = self.lpd.full_site_weather_data
        self.report_generator.add_text('## Outdoor temperature evolution (month average)')
        self.report_generator.add_text('The following figure represents the evolution of the annual average outdoor temperature from 1980 to the reference year. The blue dots represent the annual average temperature for each year, and the red line shows the linear trend with the slope displayed in °C/year.')
        self.report_generator.add_text('### Long term outdoor temperature evolution')
        reference_year = self.lpd('year')
        self.report_generator.add_annual_temperature_trend('Long term outdoor temperature evolution', all_years_site_weather_data.datetimes, all_years_site_weather_data.get('temperature'), reference_year, start_year=1980)
        self.report_generator.add_text('### Long term outdoor rainfalls evolution (annual cumulated)')
        self.report_generator.add_text('The following figure represents the evolution of the annual cumulative rainfall from 1980 to the reference year. The blue dots represent the annual cumulative rainfall for each year, and the red line shows the linear trend with the slope displayed in mm/year.')
        self.report_generator.add_annual_rainfall_trend('Long term outdoor rainfalls evolution (annual cumulated)', all_years_site_weather_data.datetimes, all_years_site_weather_data.get('precipitation'), reference_year, start_year=1980)

    def solar(self) -> None:
        """Perform solar radiation analysis.

        Analyzes solar position, optimal PV panel orientation, and solar energy
        collection on different surface orientations. Generates heliodon plots
        and calculates best exposure and tilt angles for photovoltaic systems.
        """
        # Calculate daily solar energy on horizontal surface (kWh/day)
        # Get hourly solar power in W for horizontal surface
        horizontal_hourly_power_W = self.lpd.unit_canonic_solar_powers_W['HORIZONTAL_UP']
        
        # Convert hourly W to daily kWh: group by day, sum hours, convert to kWh
        from datetime import time
        daily_solar_energy_kWh = []
        daily_datetimes = []
        current_date = None
        daily_sum_W = 0.0
        
        for i, dt in enumerate(self.datetimes):
            date = dt.date()
            
            if current_date is None:
                current_date = date
                daily_sum_W = horizontal_hourly_power_W[i]
            elif date == current_date:
                # Same day, accumulate
                daily_sum_W += horizontal_hourly_power_W[i]
            else:
                # New day, save previous day's total and start new day
                daily_solar_energy_kWh.append(daily_sum_W / 1000.0)  # Convert W to kWh
                daily_datetimes.append(datetime.combine(current_date, time(12, 0)))  # Use noon as representative time
                current_date = date
                daily_sum_W = horizontal_hourly_power_W[i]
        
        # Don't forget the last day
        if current_date is not None:
            daily_solar_energy_kWh.append(daily_sum_W / 1000.0)
            daily_datetimes.append(datetime.combine(current_date, time(12, 0)))

        self.report_generator.add_text('# Solar radiation analysis <a name="solar"></a>')

        # Add the heatmap chart
        self.report_generator.add_text('### Solar energy in kWh/day.m2')
        self.report_generator.add_text('The following heatmap represents the daily solar energy collected on a horizontal surface (1 m²) for each day of each month. The values account for solar masks (horizon and distant masks) and cloudiness. Darker colors indicate higher solar energy collection.')
        self.report_generator.add_monthly_heatmap('Solar energy in kWh/day.m2', daily_datetimes, daily_solar_energy_kWh, value_label='Solar energy (kWh/day.m2)')

        self.report_generator.add_text('An heliodon represents the sun path along the year. The position of the sun is represented by 2 angles: the azimuth, the angle formed by a vertical plan directed to the south and the vertical plan where the sun is i.e. the azimuth angle, and the altitude (or elevation) of the sun formed by the horizontal plan tangent to earth and the horizontal where the sun is with 0° means: directed to the south (for azimuth, east is negative and west positive, and altitude 0° and 90° stand respectively for horizontal and vertical positions). The heliodon plot represents the trajectory of the sun the 21th of each month of the year.')
        self.report_generator.add_image('solar_angles.png')
        self.report_generator.add_text('Additionally, the solar masks coming from the skyline in particular (specified in the configuration file) are also drawn: gray dots represent the angles where the sun is visible.')
        self.report_generator.add_text('- Heliodon at local position, with the azimuth angles on the x-axis and the altitude angle on the y-axis')
        self.lpd.solar_model.plot_heliodon(self.lpd('year'))  # axis: plt.Axes =
        self.report_generator.add_figure()
        self.report_generator.add_text("The best exposure (horizontal angle of the perpendicular to the PV panel wrt the south) and best tilt angle (vertical angle of the perpendicular to the PV panel wrt to the south), have been computed. An exposure of -90° means the panel is directed to the the east, +90° to the west. A slope of 90° means the panel is facing the south whereas 0° means facing the ground and 180°,facing the sky.")
        self.report_generator.add_image("exposure_tilt.png")
        # Check if required data exists before trying to access it
        if 'best_exposure_deg' in self.lpd and 'best_slope_deg' in self.lpd:
            best_exposure_deg = self.lpd("best_exposure_deg")
            best_slope_deg = self.lpd('best_slope_deg')
        else:
            # If exposure/slope are not available, use defaults
            best_exposure_deg = 0.0
            best_slope_deg = 90.0
        
        if 'best_PV_plant_powers_W' in self.lpd:
            pv_production_kwh = sum(self.lpd('best_PV_plant_powers_W')) / 1000
        else:
            # If PV plant powers are not available, use 0 as default
            pv_production_kwh = 0.0
        
        floor_surface_m2 = self.lpd('floor_surface_m2') if 'floor_surface_m2' in self.lpd else 0.0
        
        self.report_generator.add_text("- The best PV exposure angle is: %g°E with a tilt angle of %g° (%g°) with a production of %ikWh/year for %im2" % (best_exposure_deg, best_slope_deg, 180-best_slope_deg, pv_production_kwh, floor_surface_m2))
        # CHECK
        self.report_generator.add_text('- The next figure gives the collected solar energy (not PV production) on different ($1m^2$) surface direction')
        self.report_generator.add_barchart('Collected solar energy on different surfaces', 'kWh/m2.year', **{direction: sum(self.lpd.unit_canonic_solar_powers_W[direction])/1000 for direction in self.lpd.unit_canonic_solar_powers_W})

    def house(self) -> None:
        """Perform comprehensive house energy performance analysis.

        Analyzes building energy needs, indoor comfort, and parametric
        sensitivity. Generates plots for indoor temperatures, energy consumption,
        discomfort indicators, and parametric studies of key design parameters.
        """
        try:
            self.report_generator.add_text('# House Analysis <a name="house"></a>')
            self.report_generator.add_text('### Global results')

            # Check if simulation data is available
            if 'indoor_temperatures_deg' not in self.lpd._resulting_data:
                self.report_generator.add_text('**ERROR: Simulation data not available. House analysis cannot be performed.**')
                self.report_generator.add_text('This usually indicates that the simulation failed during initialization or execution.')
                
                # Try to provide more diagnostic information
                missing_params = []
                required_params = [
                    'occupancy', 'air_volume_m3', 'windows_solar_gains_W', 
                    'US_wall', 'US_glass', 'US_roof', 'US_ground',
                    'smooth_outdoor_temperatures_for_hvac_periods_deg', 
                    'average_outdoor_temperature_deg',
                    'heating_period_indices', 'cooling_period_indices',
                    'heating_setpoint_deg', 'cooling_setpoint_deg',
                    'hvac_COP', 'ventilation_heat_recovery_efficiency',
                    'air_renewal_presence_vol_per_h', 'air_renewal_absence_vol_per_h'
                ]
                
                for param in required_params:
                    if param not in self.lpd._nominal_parametric_data and param not in self.lpd._resulting_data:
                        missing_params.append(param)
                
                if missing_params:
                    self.report_generator.add_text(f'**Missing required parameters:** {", ".join(missing_params)}')
                    self.report_generator.add_text('These parameters may have been deleted from the lambda_parameter_data initialization.')
                
                # Check if datetimes are available
                if len(self.lpd('datetimes')) == 0:
                    self.report_generator.add_text('**No time series data available.** The datetimes list is empty.')
                else:
                    self.report_generator.add_text(f'Time series data available: {len(self.lpd("datetimes"))} hours')
                
                # Try to run simulation again to get the actual error
                self.report_generator.add_text('**Attempting to run simulation to capture error details:**')
                simulation_succeeded = False
                try:
                    Simulator.run(self.lpd)
                    if 'indoor_temperatures_deg' in self.lpd._resulting_data:
                        self.report_generator.add_text('✓ Simulation succeeded on retry. Continuing with analysis...')
                        simulation_succeeded = True
                    else:
                        self.report_generator.add_text('✗ Simulation completed but indoor_temperatures_deg was not set.')
                except KeyError as e:
                    param_name = e.args[0] if e.args else str(e)
                    self.report_generator.add_text(f'**KeyError: Missing parameter "{param_name}"**')
                    self.report_generator.add_text(f'This parameter is required for the simulation but is not defined.')
                    self.report_generator.add_text(f'**Action required:** Add this parameter back to the lambda_parameter_data initialization.')
                except Exception as e:
                    import traceback
                    self.report_generator.add_text(f'**Simulation failed with error:**')
                    self.report_generator.add_text(f'**Error type:** {type(e).__name__}')
                    self.report_generator.add_text(f'**Error message:** {str(e)}')
                    self.report_generator.add_text(f'**Full traceback:**')
                    self.report_generator.add_text(f'```\n{traceback.format_exc()}\n```')
                
                if not simulation_succeeded:
                    return

            self.report_generator.add_text('- The following time plot represents the evolution along time of the indoor temperatures (blue), the setpoints of the HVAC system (orange) and the outdoor temperatures (green).')
            self.report_generator.add_text('The horizontal dashed red lines point out the values that are used to estimate the inhabitant discomfort. The percentage of the occupancy hours where the temperature is over 29°C stands for summer discomfort and the percentage of the occupancy hours where the temperature is under 18°C stands for winter discomfort. These values may be more important than in reality because the model does not represent all reactive actions done by the occupants in reaction to overheating.')
            self.report_generator.add_time_plot('indoor temperatures', self.lpd.datetimes, self.lpd('indoor_temperatures_deg'), value_marks=[18, 29], setpoints=self.lpd('setpoint_temperatures_deg'), outdoor_temperatures_deg=self.lpd('outdoor_temperatures_deg'), heating_period_indices=self.lpd('heating_period_indices'), cooling_period_indices=self.lpd('cooling_period_indices'))

            self.report_generator.add_text('The resulting primary energy needs are given below. In addition to these values, the final energy need taking into account the coefficient of performance of the HVAC system are also given.')
            
            self.report_generator.add_text('### HVAC System Operation')
            self.report_generator.add_text('The HVAC system operates with adaptive setpoint temperatures based on occupancy to optimize energy consumption while maintaining comfort:')
            self.report_generator.add_text('')
            self.report_generator.add_text('**Heating mode:**')
            self.report_generator.add_text(f'- During presence: the heating setpoint is {self.lpd("heating_setpoint_deg")}°C (high setpoint for comfort)')
            self.report_generator.add_text(f'- During absence: the heating setpoint is {self.lpd("heating_setpoint_deg") - self.lpd("delta_temperature_absence_mode_deg")}°C (low setpoint, {self.lpd("heating_setpoint_deg")}°C - {self.lpd("delta_temperature_absence_mode_deg")}°C = {self.lpd("heating_setpoint_deg") - self.lpd("delta_temperature_absence_mode_deg")}°C) to save energy')
            self.report_generator.add_text('')
            self.report_generator.add_text('**Cooling mode:**')
            self.report_generator.add_text(f'- During presence: the cooling setpoint is {self.lpd("cooling_setpoint_deg")}°C (setpoint for comfort)')
            self.report_generator.add_text('- During absence: the air conditioning system is turned off (no setpoint) to save energy')
            self.report_generator.add_text('')
            self.report_generator.add_text('The temperature difference between presence and absence modes for heating is controlled by the parameter `delta_temperature_absence_mode_deg` (currently {:.1f}°C). This allows the system to reduce energy consumption during unoccupied periods while maintaining comfort when occupants are present.'.format(self.lpd('delta_temperature_absence_mode_deg')))

            self.report_generator.add_text('- The primary year heat needed for heating the lambda-house is: %gkWh, with a final energy needs = %.fkWh and a maximum power of %gW' % (sum(self.lpd('heating_needs_W'))/1000, sum(self.lpd('heating_needs_W')) / self.lpd('hvac_COP') / 1000, self.lpd('max_heating_power_W')))

            self.report_generator.add_text('- The primary year heat removal needed for cooling the lambda-house is: %gkWh, with a final energy needs = %gkWh and a maximum power of %gW' % (sum(self.lpd('cooling_needs_W'))/1000, sum(self.lpd('cooling_needs_W')) / 1000 / self.lpd('hvac_COP'), self.lpd('max_cooling_power_W')))
            self.report_generator.add_text('- The primary year heat needs for the HVAC system (heating and cooling) is: %gkWh (with a final energy needs = %gkWh)' % (sum(self.lpd('hvac_needs_W'))/1000, sum(self.lpd('hvac_needs_W')) / 1000 / self.lpd('hvac_COP')))

            # consumption comparison

            self.report_generator.add_text('- The following bar chart represents the final energy from a heat pump (COP=%.1f) needed per square meter of useful living surface.' % (self.lpd('hvac_COP')))
            self.report_generator.add_barchart('Final energy for heating and cooling with a heat pump', 'kWh/m2/year', needed_energy={
                'heating': sum(self.lpd('heating_needs_W'))/1000/self.lpd('total_living_surface_m2')/self.lpd('hvac_COP'),
                'cooling': sum(self.lpd('cooling_needs_W'))/1000/self.lpd('total_living_surface_m2')/self.lpd('hvac_COP')
                })

            self.report_generator.add_text('- The following bar chart represents the discomfort18 (the ratio of hours of presence where the temperature is lower than 18°C) and discomfort29 (the ratio of hours of presence where the temperature is higher than 29°C).')
            self.report_generator.add_barchart('ratio of hours of presence with discomfort', 'hours in discomfort / hours of occupancy in %', needed_energy={'discomfort18': self.lpd('discomfort18'), 'discomfort29': self.lpd('discomfort29')})

            # Collect all values to find worst and best
            sides = ['south', 'west', 'east', 'north']
            heating_values = {}
            cooling_values = {}
            for side in sides:
                heating_values[side] = self.lpd(f'{side}_heating_windows_global_gains_W')
                cooling_values[side] = self.lpd(f'{side}_cooling_windows_global_gains_W')
            
            # Find worst and best for heating (positive is best, negative is worst)
            heating_best_side = max(heating_values, key=heating_values.get)
            heating_worst_side = min(heating_values, key=heating_values.get)
            heating_best_value = heating_values[heating_best_side]
            heating_worst_value = heating_values[heating_worst_side]
            
            # Find worst and best for cooling (negative is best, positive is worst)
            cooling_best_side = min(cooling_values, key=cooling_values.get)
            cooling_worst_side = max(cooling_values, key=cooling_values.get)
            cooling_best_value = cooling_values[cooling_best_side]
            cooling_worst_value = cooling_values[cooling_worst_side]
            
            self.report_generator.add_text('### Solar gain / loss balance computation')
            self.report_generator.add_text('The solar gain / loss balance for each window is computed as the net energy exchange through the glazing:')
            self.report_generator.add_text('- **Solar gains** (positive): incoming solar radiation through the window')
            self.report_generator.add_text('- **Thermal losses** (negative): heat transfer through the glass due to temperature difference between indoor and outdoor, calculated as U_glass × glazing_surface × (T_indoor - T_outdoor)')
            self.report_generator.add_text('- **Net balance** = Solar gains - Thermal losses')
            self.report_generator.add_text('')
            
            # Create a summary table for all window directions
            table = prettytable.PrettyTable()
            table.field_names = ('Window direction', 'Heating period (W/m²)', 'Cooling period (W/m²)')
            table.align['Window direction'] = 'l'
            table.align['Heating period (W/m²)'] = 'r'
            table.align['Cooling period (W/m²)'] = 'r'
            for side in sides:
                table.add_row((side.capitalize(), f'{heating_values[side]:.1f}', f'{cooling_values[side]:.1f}'))
            self.report_generator.add_pretty_table(table)
            self.report_generator.add_text('')
            
            self.report_generator.add_text('**In heating context:**')
            self.report_generator.add_text('- Positive values (gains) are beneficial: they reduce heating needs')
            self.report_generator.add_text('- Negative values (losses) are detrimental: they increase heating needs')
            self.report_generator.add_text(f'- Best orientation: {heating_best_side.capitalize()} window with {heating_best_value:.1f} W/m² (highest gain)')
            self.report_generator.add_text(f'- Worst orientation: {heating_worst_side.capitalize()} window with {heating_worst_value:.1f} W/m² (highest loss)')
            self.report_generator.add_text('')
            self.report_generator.add_text('**In cooling context:**')
            self.report_generator.add_text('- Negative values (losses) are beneficial: they help remove heat and reduce cooling needs')
            self.report_generator.add_text('- Positive values (gains) are detrimental: they add heat and increase cooling needs')
            self.report_generator.add_text(f'- Best orientation: {cooling_best_side.capitalize()} window with {cooling_best_value:.1f} W/m² (lowest gain / highest loss)')
            self.report_generator.add_text(f'- Worst orientation: {cooling_worst_side.capitalize()} window with {cooling_worst_value:.1f} W/m² (highest gain)')
            
        except Exception as e:
            self.report_generator.add_text(f'**ERROR in house analysis: {str(e)}**')
            self.report_generator.add_text('The house analysis failed due to an error. This usually indicates missing simulation data or calculation errors.')
            import traceback
            self.report_generator.add_text(f'**Technical details:** {traceback.format_exc()}')
            
        self.report_generator.add_text("### Parametric analyses")
        self.parametric()
        self.report_generator.add_text("Different parametric analyses are performed in the next. It consists in modifying one parameter while keeping all the others at their nominal values. The impact is computed in percentage of variation wrt nominal impacts: heating primary energy needs, cooling primary energy needs (and their total), but also indicators dealing with inhabitant comfort: Discomfort18, the frequency of hours with presence where indoor temperature is lower than 18°C. In the same way, Discomfort29 is the frequency of hours where the indoor temperature is higher than 29°C.")
        self.report_generator.add_text("Right hand scale is representing the percentage of variation wrt to nominal value. For instance, 0% means the result is the same than the one of the nominal parameter values. 100% means the value is the double of the case of nominal results, and -50% stands for half of the nominal value. It concerns the variable representing the heating, cooling and total energy needs.")
        self.report_generator.add_text("Left hand scale represents the discomfort indicators: discomfort18 and discomfort29, see above).")
        self.report_generator.add_text("The first parametric analysis focuses on glazing. Variation of the surface of glazing (10% for each house side for nominal) are computed: there are as many plot that the studied direction.")

    def parametric(self) -> None:
        """Perform parametric sensitivity analysis.

        Systematically varies key design parameters (glazing ratios, shape factor,
        number of floors, insulation thickness, HVAC setpoints, etc.) and analyzes
        their impact on energy needs and comfort indicators. Generates parametric
        plots showing the sensitivity of performance metrics to design choices.
        """
        # Create table showing glazing ratios and corresponding window sizes
        self.report_generator.add_text("- Parametric analysis of the glazing for each side")  # Parametric analysis of the glazing for each side
        self.report_generator.add_text("The following table shows the glazing ratios and the corresponding window surface areas for each direction:")
        
        # Get parametric values for glazing ratio (same for all directions)
        self.lpd.reset()
        self.lpd.select('glazing_ratio_south')
        glazing_ratio_values = list(self.lpd.parametric('glazing_ratio_south'))
        
        # Get building parameters needed for window size calculation
        floor_height_m = self.lpd('floor_height_m')
        number_of_floors = self.lpd('number_of_floors')
        total_living_surface_m2 = self.lpd('total_living_surface_m2')
        shape_factor = self.lpd('shape_factor')
        
        # Calculate side lengths
        largest_side_length_m = math.sqrt(number_of_floors * total_living_surface_m2 * shape_factor)
        smallest_side_length_m = math.sqrt(number_of_floors * total_living_surface_m2 / shape_factor)
        
        # Create table
        table = prettytable.PrettyTable()
        table.field_names = ['Glazing Ratio', 'South (m²)', 'West (m²)', 'East (m²)', 'North (m²)']
        table.align['Glazing Ratio'] = 'r'
        table.align['South (m²)'] = 'r'
        table.align['West (m²)'] = 'r'
        table.align['East (m²)'] = 'r'
        table.align['North (m²)'] = 'r'
        
        # Add rows for each glazing ratio
        for ratio in glazing_ratio_values:
            south_window_m2 = floor_height_m * ratio * largest_side_length_m
            north_window_m2 = floor_height_m * ratio * largest_side_length_m
            west_window_m2 = floor_height_m * ratio * smallest_side_length_m
            east_window_m2 = floor_height_m * ratio * smallest_side_length_m
            table.add_row([f'{ratio:.2f}', f'{south_window_m2:.2f}', f'{west_window_m2:.2f}', f'{east_window_m2:.2f}', f'{north_window_m2:.2f}'])
        
        self.report_generator.add_pretty_table(table)
        self.report_generator.add_text('')

        # Calculate reference total glazing surface to keep it constant during parametric analysis
        # This ensures that when we vary one direction's glazing ratio, we adjust the others
        # to maintain the same total glazing surface, isolating the effect of orientation
        self.lpd.reset()
        reference_total_glazing_surface_m2 = self.lpd('glazing_surface_m2')
        reference_glazing_ratios = {
            'north': self.lpd('glazing_ratio_north'),
            'south': self.lpd('glazing_ratio_south'),
            'east': self.lpd('glazing_ratio_east'),
            'west': self.lpd('glazing_ratio_west')
        }
        
        # Calculate side lengths for reference (these don't change in parametric analysis)
        floor_height_m = self.lpd('floor_height_m')
        number_of_floors = self.lpd('number_of_floors')
        total_living_surface_m2 = self.lpd('total_living_surface_m2')
        shape_factor = self.lpd('shape_factor')
        primary_side_length_m = math.sqrt(number_of_floors * total_living_surface_m2 * shape_factor)
        secondary_side_length_m = math.sqrt(number_of_floors * total_living_surface_m2 / shape_factor)
        
        for side in ['south', 'west', 'east', 'north']:
            self.lpd.reset()
            parameter_name: str = 'glazing_ratio_%s' % side
            self.lpd.select(parameter_name)
            parameter_values: list[str] = list()
            left_indicators: dict[str, list[float]] = {'heating_needs_kWh': list(), 'cooling_needs_kWh': list(), 'hvac_needs_kWh': list()}
            right_indicators: dict[str, list[float]] = {'discomfort18': list(), 'discomfort29': list()}
            for parameter_value in self.lpd:
                parameter_values.append(parameter_value)
                
                # Adjust other glazing ratios to maintain constant total glazing surface
                new_ratio = float(parameter_value)
                current_ratios = reference_glazing_ratios.copy()
                current_ratios[side] = new_ratio
                
                # Calculate current total glazing surface with the new ratio
                current_total_glazing_surface_m2 = floor_height_m * (
                    primary_side_length_m * (current_ratios['north'] + current_ratios['south']) +
                    secondary_side_length_m * (current_ratios['east'] + current_ratios['west'])
                )
                
                # Calculate difference to maintain constant total
                surface_difference_m2 = reference_total_glazing_surface_m2 - current_total_glazing_surface_m2
                
                # Distribute the difference proportionally among other directions
                # Strategy: adjust the opposite direction on the same side first, then adjust the other side
                if abs(surface_difference_m2) > 1e-6:
                    if side in ['north', 'south']:
                        # Adjust the other primary side direction first
                        other_primary = 'south' if side == 'north' else 'north'
                        primary_surface_diff = surface_difference_m2 / floor_height_m / primary_side_length_m
                        current_ratios[other_primary] = max(0.01, min(0.99, current_ratios[other_primary] - primary_surface_diff))
                        
                        # Recalculate to check if we need to adjust secondary sides
                        remaining_surface = reference_total_glazing_surface_m2 - floor_height_m * (
                            primary_side_length_m * (current_ratios['north'] + current_ratios['south']) +
                            secondary_side_length_m * (current_ratios['east'] + current_ratios['west'])
                        )
                        if abs(remaining_surface) > 1e-6:
                            # Adjust secondary sides proportionally
                            secondary_diff = remaining_surface / floor_height_m / secondary_side_length_m
                            # Distribute equally between east and west
                            current_ratios['east'] = max(0.01, min(0.99, current_ratios['east'] - secondary_diff / 2))
                            current_ratios['west'] = max(0.01, min(0.99, current_ratios['west'] - secondary_diff / 2))
                    else:  # side in ['east', 'west']
                        # Adjust the other secondary side direction first
                        other_secondary = 'west' if side == 'east' else 'east'
                        secondary_surface_diff = surface_difference_m2 / floor_height_m / secondary_side_length_m
                        current_ratios[other_secondary] = max(0.01, min(0.99, current_ratios[other_secondary] - secondary_surface_diff))
                        
                        # Recalculate to check if we need to adjust primary sides
                        remaining_surface = reference_total_glazing_surface_m2 - floor_height_m * (
                            primary_side_length_m * (current_ratios['north'] + current_ratios['south']) +
                            secondary_side_length_m * (current_ratios['east'] + current_ratios['west'])
                        )
                        if abs(remaining_surface) > 1e-6:
                            # Adjust primary sides proportionally
                            primary_diff = remaining_surface / floor_height_m / primary_side_length_m
                            # Distribute equally between north and south
                            current_ratios['north'] = max(0.01, min(0.99, current_ratios['north'] - primary_diff / 2))
                            current_ratios['south'] = max(0.01, min(0.99, current_ratios['south'] - primary_diff / 2))
                
                # Set the adjusted ratios
                for other_side in ['north', 'south', 'east', 'west']:
                    if other_side != side:
                        self.lpd.set('glazing_ratio_%s' % other_side, current_ratios[other_side])
                
                Simulator.run(self.lpd)
                left_indicators['heating_needs_kWh'].append(self.lpd('heating_needs_kWh'))
                left_indicators['cooling_needs_kWh'].append(self.lpd('cooling_needs_kWh'))
                left_indicators['hvac_needs_kWh'].append(self.lpd('hvac_needs_kWh'))
                right_indicators['discomfort18'].append(self.lpd('discomfort18'))
                right_indicators['discomfort29'].append(self.lpd('discomfort29'))
            self.report_generator.add_parametric(parameter_name=parameter_name, parameter_values=parameter_values, left_indicators=left_indicators, left_label='primary energy needs in kWh/year', right_indicators=right_indicators, right_label='discomfort in %')

        self.lpd.reset()
        Simulator.run(self.lpd)

        self.report_generator.add_text("- Parametric analysis of lambda-house direction (exposure of the south side).")

        self.report_generator.add_text("The house is rotated east/west to analyze the resulting global impacts (remember that the skyline is also impacting the results).")
        self.report_generator.add_text('The best angle of the south wall with the South (0° stands for South wall facing the South, 90° the West and -90° the East.) ')
        self.report_generator.add_image('exposure.png')

        self.report_generator.add_text("- Parametric analysis of the offset exposure")  # Parametric analysis of the glazing for each side

        parameter_name: str = 'offset_exposure_deg'
        self.lpd.select(parameter_name)
        parameter_values: list[str] = list()
        left_indicators: dict[str, list[float]] = {'heating_needs_kWh': list(), 'cooling_needs_kWh': list(), 'hvac_needs_kWh': list()}
        right_indicators: dict[str, list[float]] = {'discomfort18': list(), 'discomfort29': list()}
        for parameter_value in self.lpd:
            parameter_values.append(parameter_value)
            Simulator.run(self.lpd)
            [left_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in left_indicators]
            [right_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in right_indicators]
        self.report_generator.add_parametric(parameter_name=parameter_name, parameter_values=parameter_values, left_indicators=left_indicators, left_label='energy needs in kWh/year', right_indicators=right_indicators, right_label='discomfort in %')

        self.report_generator.add_text('- The shape factor parametric analysis')
        self.report_generator.add_text("Changing the shape factor, a square ground print at first, aims at defining the best house shape.")
        self.report_generator.add_text('It keeps the useful building surface constant, 1 yields a square,  and higher than 1 value yields a rectangle with South/North sides bigger than East/West sides and lower than one, the opposite')
        table = prettytable.PrettyTable()
        Sfloor: float = self.lpd('total_living_surface_m2') / self.lpd('number_of_floors')
        table.field_names = ('shape factor', 'south/north side length', 'west/east side length')
        for shape_factor in self.lpd.parametric('shape_factor'):
            Lsouth_north_wall: float = math.sqrt(Sfloor * shape_factor)
            Least_west_wall: float = math.sqrt(Sfloor / shape_factor)
            table.add_row(('%g' % shape_factor, '%g' % Lsouth_north_wall, '%g' % Least_west_wall))
        self.report_generator.add_pretty_table(table)  # delta_temperature_absence_mode

        parameter_name: str = 'shape_factor'
        self.lpd.select(parameter_name)
        parameter_values: list[str] = list()
        left_indicators: dict[str, list[float]] = {'heating_needs_kWh': list(), 'cooling_needs_kWh': list(), 'hvac_needs_kWh': list()}
        right_indicators: dict[str, list[float]] = {'discomfort18': list(), 'discomfort29': list()}
        for parameter_value in self.lpd:
            parameter_values.append(parameter_value)
            Simulator.run(self.lpd)
            [left_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in left_indicators]
            [right_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in right_indicators]
        self.report_generator.add_parametric(parameter_name=parameter_name, parameter_values=parameter_values, left_indicators=left_indicators, left_label='energy needs in kWh/year', right_indicators=right_indicators, right_label='discomfort in %')

        self.report_generator.add_text('- The number_of_floors: the useful surface can be distributed over different floors, reducing thus the floor print, and increasing the height of the house.')
        parameter_name: str = 'number_of_floors'
        self.lpd.select(parameter_name)
        parameter_values: list[str] = list()
        left_indicators: dict[str, list[float]] = {'heating_needs_kWh': list(), 'cooling_needs_kWh': list(), 'hvac_needs_kWh': list()}
        right_indicators: dict[str, list[float]] = {'discomfort18': list(), 'discomfort29': list()}
        for parameter_value in self.lpd:
            parameter_values.append(parameter_value)
            Simulator.run(self.lpd)
            [left_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in left_indicators]
            [right_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in right_indicators]
        self.report_generator.add_parametric(parameter_name=parameter_name, parameter_values=parameter_values, left_indicators=left_indicators, left_label='energy needs in kWh/year', right_indicators=right_indicators, right_label='discomfort in %')

        self.report_generator.add_text('- Parametric study of the solar protection over the South glazing')
        self.report_generator.add_text('The parameter "south_solar_protection_angle_deg" stands for the maximum altitude angle where the sun is not hidden by the passive solar protection mask over the South glazing.')
        self.report_generator.add_text('The nominal lambda house has a passive solar mask, which is masking the sun at a specified altitude:. This parametric analysis makes it possible to define a relevant compromise for this exposure angle leading to lower energy needs while limiting the inhabitant discomfort.')
        parameter_name: str = 'south_solar_protection_angle_deg'
        self.lpd.select(parameter_name)
        parameter_values: list[str] = list()
        left_indicators: dict[str, list[float]] = {'heating_needs_kWh': list(), 'cooling_needs_kWh': list(), 'hvac_needs_kWh': list()}
        right_indicators: dict[str, list[float]] = {'discomfort18': list(), 'discomfort29': list()}
        for parameter_value in self.lpd:
            parameter_values.append(parameter_value)
            Simulator.run(self.lpd)
            [left_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in left_indicators]
            [right_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in right_indicators]
        self.report_generator.add_parametric(parameter_name=parameter_name, parameter_values=parameter_values, left_indicators=left_indicators, left_label='energy needs in kWh/year', right_indicators=right_indicators, right_label='discomfort in %')

        # self.report_generator.add_text('- Parametric study of the air renewal through ventilation in indoor volume per hour in case a presence has been detected')
        # self.parametric_analysis(parameter_name='air_renewal_presence_vol_per_h')

        self.report_generator.add_text('- Parametric study of the ventilation heat recovery efficiency')
        self.report_generator.add_text('The ventilation heat recovery efficiency reduces the heat exchanges between indoor and outdoor. 0% means there is no dual flow ventilation system and 85%, which is the greatest value than can be found on rotating heat exchangers with wheels, means that 85% of the heat from the extracted air is recovered and reinjected into the new air (heat exchange represents 15% of the one of a single flow ventilation system).')
        # self.parametric_analysis(parameter_name='ventilation_heat_recovery_efficiency')
        parameter_name: str = 'ventilation_heat_recovery_efficiency'
        self.lpd.select(parameter_name)
        parameter_values: list[str] = list()
        left_indicators: dict[str, list[float]] = {'heating_needs_kWh': list(), 'cooling_needs_kWh': list(), 'hvac_needs_kWh': list()}
        right_indicators: dict[str, list[float]] = {'discomfort18': list(), 'discomfort29': list()}
        for parameter_value in self.lpd:
            parameter_values.append(parameter_value)
            Simulator.run(self.lpd)
            [left_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in left_indicators]
            [right_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in right_indicators]
        self.report_generator.add_parametric(parameter_name=parameter_name, parameter_values=parameter_values, left_indicators=left_indicators, left_label='energy needs in kWh/year', right_indicators=right_indicators, right_label='discomfort in %')

        self.report_generator.add_text('- Parametric study of the HVAC heating temperature setpoint')
        self.report_generator.add_text('This setpoint temperature is applied only during time periods where at least an inhabitant is present.')
        parameter_name: str = 'heating_setpoint_deg'
        self.lpd.select(parameter_name)
        parameter_values: list[str] = list()
        left_indicators: dict[str, list[float]] = {'heating_needs_kWh': list(), 'cooling_needs_kWh': list(), 'hvac_needs_kWh': list()}
        right_indicators: dict[str, list[float]] = {'discomfort18': list(), 'discomfort29': list()}
        for parameter_value in self.lpd:
            parameter_values.append(parameter_value)
            Simulator.run(self.lpd)
            [left_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in left_indicators]
            [right_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in right_indicators]
        self.report_generator.add_parametric(parameter_name=parameter_name, parameter_values=parameter_values, left_indicators=left_indicators, left_label='energy needs in kWh/year', right_indicators=right_indicators, right_label='discomfort in %')

        self.report_generator.add_text('- Parametric study of the HVAC cooling temperature setpoint')
        self.report_generator.add_text('This setpoint temperature is applied only during time periods where at least an inhabitant is present.')
        parameter_name: str = 'cooling_setpoint_deg'
        self.lpd.select(parameter_name)
        parameter_values: list[str] = list()
        left_indicators: dict[str, list[float]] = {'heating_needs_kWh': list(), 'cooling_needs_kWh': list(), 'hvac_needs_kWh': list()}
        right_indicators: dict[str, list[float]] = {'discomfort18': list(), 'discomfort29': list()}
        for parameter_value in self.lpd:
            parameter_values.append(parameter_value)
            Simulator.run(self.lpd)
            [left_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in left_indicators]
            [right_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in right_indicators]
        self.report_generator.add_parametric(parameter_name=parameter_name, parameter_values=parameter_values, left_indicators=left_indicators, left_label='energy needs in kWh/year', right_indicators=right_indicators, right_label='discomfort in %')

        self.report_generator.add_text('- Parametric study of the insulation thickness')
        self.report_generator.add_text('It modifies the thickness of the chosen material for insulation.')

        parameter_name: str = 'thickness_m'
        self.lpd.select(parameter_name)
        parameter_values: list[str] = list()
        left_indicators: dict[str, list[float]] = {'heating_needs_kWh': list(), 'cooling_needs_kWh': list(), 'hvac_needs_kWh': list()}
        right_indicators: dict[str, list[float]] = {'discomfort18': list(), 'discomfort29': list()}
        for parameter_value in self.lpd:
            parameter_values.append(parameter_value)
            Simulator.run(self.lpd)
            [left_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in left_indicators]
            [right_indicators[indicator_name].append(self.lpd(indicator_name)) for indicator_name in right_indicators]
        self.report_generator.add_parametric(parameter_name=parameter_name, parameter_values=parameter_values, left_indicators=left_indicators, left_label='energy needs in kWh/year', right_indicators=right_indicators, right_label='discomfort in %')

    def neutrality(self) -> None:
        """Perform energy neutrality analysis.

        Analyzes the relationship between building energy consumption and
        photovoltaic production. Calculates required PV surface area for energy
        neutrality, self-consumption, self-production, and grid independence
        indicators.
        """
        self.lpd.reset()
        Simulator.run(lpd=self.lpd)
        self.report_generator.add_text('# Neutrality analysis <a name="neutrality"></a>')

        self.report_generator.add_text('## Zero energy over the year')
        self.report_generator.add_text('The aim is to appreciate the yearly energy needed by the HVAC system. To do it, the energy neutrality is searched thanks to a certain surface of photovoltaic panels.')

        self.report_generator.add_text('- The required surface of photovoltaic panels for balancing the annual energy consumption of the HVAC system is:')

        # Create a temporary PV plant with fixed reference surface to calculate production per m²
        reference_PV_surface_m2 = 1.0  # Fixed reference surface for calculating production per m²
        temp_PV_plant = PVplant(
            self.lpd.solar_model, 
            self.lpd('best_exposure_deg'), 
            self.lpd('best_slope_deg'), 
            mount_type=MOUNT_TYPES.PLAN, 
            number_of_panels_per_array=10, 
            panel_width_m=1, 
            panel_height_m=1, 
            pv_efficiency=self.lpd('PV_efficiency'), 
            temperature_coefficient=0.0035, 
            distance_between_arrays_m=1, 
            surface_pv_m2=reference_PV_surface_m2
        )
        best_PV_plant_powers_W = temp_PV_plant.powers_W()
        
        # Calculate PV production per m² per year (kWh/m²/year)
        pv_production_per_m2_per_year = sum(best_PV_plant_powers_W) / 1000 / reference_PV_surface_m2
        self.report_generator.add_text(f'PV production per m² per year: {pv_production_per_m2_per_year:.1f} kWh/m²/year')
        
        neutrality_all_usages_pv_surface_m2 = self.lpd('electricity_needs_kWh') / pv_production_per_m2_per_year
        neutrality_hvac_pv_surface_m2 = self.lpd('hvac_needs_kWh') / self.lpd('hvac_COP') / pv_production_per_m2_per_year
        
        # Calculate scaling factors for both neutrality surfaces
        scaling_factor_all_usages = neutrality_all_usages_pv_surface_m2 / reference_PV_surface_m2
        scaling_factor_hvac = neutrality_hvac_pv_surface_m2 / reference_PV_surface_m2
        
        # Calculate PV production powers for both surfaces by scaling from the reference
        PV_plant_powers_all_usages_W = [p * scaling_factor_all_usages for p in best_PV_plant_powers_W]
        PV_plant_powers_hvac_W = [p * scaling_factor_hvac for p in best_PV_plant_powers_W]
        
        table = prettytable.PrettyTable()
        table.field_names = ('PV (efficiency: %g%%)' % (100*self.lpd('PV_efficiency')), 'energy needs (in best eq. PV m²)')
        # Set alignment: left for first column, right for second column (numbers)
        table.align['PV (efficiency: %g%%)' % (100*self.lpd('PV_efficiency'))] = 'l'
        table.align['energy needs (in best eq. PV m²)'] = 'r'
        # Format values with proper spacing and 2 decimal places
        table.add_row(('1. heater', '%.2f m²' % (self.lpd('heating_needs_kWh') / self.lpd('hvac_COP') / pv_production_per_m2_per_year)))
        table.add_row(('2. air conditioning', '%.2f m²' % (self.lpd('cooling_needs_kWh') / self.lpd('hvac_COP') / pv_production_per_m2_per_year)))
        table.add_row(('1+2. HVAC', '%.2f m²' % (neutrality_hvac_pv_surface_m2)))  # (self.lpd('hvac_needs_kWh') / self.lpd('hvac_COP') / pv_production_per_m2_per_year)))
        table.add_row(('1+2+other usages', '%.2f m²' % (neutrality_all_usages_pv_surface_m2)))  # (self.lpd('electricity_needs_kWh') / pv_production_per_m2_per_year)))
        self.report_generator.add_pretty_table(table)
        
        self.report_generator.add_text('## Monthly electricity needs for surfaces corresponding to year neutrality')
        
        # Calculate monthly averages for both PV surfaces
        month_average_PV_energy_all_usages_W, _ = Averager(PV_plant_powers_all_usages_W).day_month_average(self.lpd('datetimes'), month=True, sum_up=True)
        month_average_PV_energy_hvac_W, _ = Averager(PV_plant_powers_hvac_W).day_month_average(self.lpd('datetimes'), month=True, sum_up=True)
        # Convert to kW for display
        month_average_PV_energy_all_usages_kW = [p/1000 for p in month_average_PV_energy_all_usages_W]
        month_average_PV_energy_hvac_kW = [p/1000 for p in month_average_PV_energy_hvac_W]
        
        self.report_generator.add_text('Monthly electricity needs are plotted below, together with heat needs and the PV production for both neutrality surfaces:')
        self.report_generator.add_text(f'- All usages neutrality: {neutrality_all_usages_pv_surface_m2:.2f} m²')
        self.report_generator.add_text(f'- HVAC only neutrality: {neutrality_hvac_pv_surface_m2:.2f} m²')
        self.report_generator.add_time_plot('monthly electricity needs in kWh', self.lpd.datetimes, self.lpd('monthly_electricity_consumption_kW'), monthly_energy_need_kWh=self.lpd('month_average_needed_energy_kW'), monthly_PV_energy_produced_all_usages_kWh=month_average_PV_energy_all_usages_kW, monthly_PV_energy_produced_hvac_kWh=month_average_PV_energy_hvac_kW)

        self.report_generator.add_text('The electricity hourly consumption and photovoltaic production are plotted below for two neutrality surfaces:')
        self.report_generator.add_text(f'- All usages neutrality: {neutrality_all_usages_pv_surface_m2:.2f} m²')
        self.report_generator.add_text(f'- HVAC only neutrality: {neutrality_hvac_pv_surface_m2:.2f} m²')
        self.report_generator.add_time_plot('electricity needs (kWh/year)', self.lpd('datetimes'), self.lpd('electricity_needs_W'), PV_production_all_usages_W=PV_plant_powers_all_usages_W, PV_production_hvac_W=PV_plant_powers_hvac_W)

        # Calculate indicators for both neutrality surfaces
        electricity_needs_W = self.lpd('electricity_needs_W')
        year_autonomy_all_usages = 100 * year_autonomy(electricity_needs_W, PV_plant_powers_all_usages_W)
        year_autonomy_hvac = 100 * year_autonomy(electricity_needs_W, PV_plant_powers_hvac_W)
        neeg_all_usages = 100 * NEEG_percent(electricity_needs_W, PV_plant_powers_all_usages_W)
        neeg_hvac = 100 * NEEG_percent(electricity_needs_W, PV_plant_powers_hvac_W)
        self_consumption_all_usages = 100 * self_consumption(electricity_needs_W, PV_plant_powers_all_usages_W)
        self_consumption_hvac = 100 * self_consumption(electricity_needs_W, PV_plant_powers_hvac_W)
        self_production_all_usages = 100 * self_sufficiency(electricity_needs_W, PV_plant_powers_all_usages_W)
        self_production_hvac = 100 * self_sufficiency(electricity_needs_W, PV_plant_powers_hvac_W)
        
        # Calculate max grid withdraw for both surfaces
        electricity_grid_exchange_all_usages_W = [PV_plant_powers_all_usages_W[i] - electricity_needs_W[i] for i in range(len(electricity_needs_W))]
        electricity_grid_exchange_hvac_W = [PV_plant_powers_hvac_W[i] - electricity_needs_W[i] for i in range(len(electricity_needs_W))]
        filter_all_usages = Averager(electricity_grid_exchange_all_usages_W)
        filter_hvac = Averager(electricity_grid_exchange_hvac_W)
        daily_grid_exchange_all_usages_W, day_numbers_all_usages = filter_all_usages.day_month_average(self.lpd('datetimes'))
        daily_grid_exchange_hvac_W, day_numbers_hvac = filter_hvac.day_month_average(self.lpd('datetimes'))
        daily_electricity_grid_exchange_all_usages_W = [-p*24 for p in daily_grid_exchange_all_usages_W]
        daily_electricity_grid_exchange_hvac_W = [-p*24 for p in daily_grid_exchange_hvac_W]
        max_grid_withdraw_all_usages_W = max(daily_electricity_grid_exchange_all_usages_W)
        max_grid_withdraw_hvac_W = max(daily_electricity_grid_exchange_hvac_W)

        self.report_generator.add_text('Different indicators are used to appreciate the level of autonomy and dependency from the grid:')

        self.report_generator.add_text('### For all usages neutrality surface (%.2f m²):' % neutrality_all_usages_pv_surface_m2)
        # Add monthly daily balance histograms for both surfaces
        
        self.report_generator.add_text('- the self-consumption is the part of the PV electricity consumed locally: the more, the lower the electricity bill: %.1f%%' % self_consumption_all_usages)
        self.report_generator.add_text('- the self-production is the part of the consumption produced locally by PV: it is representing how much the energy needs are covered: %.1f%%' % self_production_all_usages)
        self.report_generator.add_text('- the L-NEEG is the net energy exchange with the grid (import + export) normalized by the total load. The less, the more independent of the grid: %.1f%%' % neeg_all_usages)
        self.report_generator.add_text('- The year electricity autonomy is: %.1f%%' % year_autonomy_all_usages)
        if max_grid_withdraw_all_usages_W <= 0:
            self.report_generator.add_text('- the surface of PV (%.2f m²) is sufficient to cover the everyday electricity needs' % neutrality_all_usages_pv_surface_m2)
        else:
            starting_day_hour_idx_all = daily_electricity_grid_exchange_all_usages_W.index(max_grid_withdraw_all_usages_W)
            ending_day_hour_idx_all = starting_day_hour_idx_all + 1
            if ending_day_hour_idx_all < len(day_numbers_all_usages):
                while ending_day_hour_idx_all < len(day_numbers_all_usages) and day_numbers_all_usages[ending_day_hour_idx_all] == day_numbers_all_usages[starting_day_hour_idx_all]:
                    ending_day_hour_idx_all += 1
                max_grid_withdraw_datetime_all = self.lpd('datetimes')[round((starting_day_hour_idx_all+ending_day_hour_idx_all)/2)]
                the_date_all: str = max_grid_withdraw_datetime_all.strftime('%d/%m/%Y')
                max_grid_withdraw_PV_covering_all = max_grid_withdraw_all_usages_W / sum(PV_plant_powers_all_usages_W[starting_day_hour_idx_all:ending_day_hour_idx_all]) * neutrality_all_usages_pv_surface_m2
                self.report_generator.add_text('- the surface of PV (%.2f m²) is not sufficient to cover all the daily electricity needs. The worst day of the year is %s: %.2f m² of PV should be added' % (neutrality_all_usages_pv_surface_m2, the_date_all, max_grid_withdraw_PV_covering_all - neutrality_all_usages_pv_surface_m2))

        self.report_generator.add_text('The following histograms show the distribution of daily electricity balance (PV production - electricity needs) for each month. Positive values indicate that PV production covers the daily needs (surplus), while negative values indicate a deficit.')
        self.report_generator.add_monthly_daily_balance_histogram(f'Daily Electricity Balance - All Usages Neutrality Surface ({neutrality_all_usages_pv_surface_m2:.2f} m²)', self.lpd('datetimes'), PV_plant_powers_all_usages_W, electricity_needs_W)

        self.report_generator.add_text('### For HVAC only neutrality surface (%.2f m²):' % neutrality_hvac_pv_surface_m2)
        
        self.report_generator.add_text('- the self-consumption is the part of the PV electricity consumed locally: the more, the lower the electricity bill: %.1f%%' % self_consumption_hvac)
        self.report_generator.add_text('- the self-production is the part of the consumption produced locally by PV: it is representing how much the energy needs are covered: %.1f%%' % self_production_hvac)
        self.report_generator.add_text('- the L-NEEG is the net energy exchange with the grid (import + export) normalized by the total load. The less, the more independent of the grid: %.1f%%' % neeg_hvac)
        self.report_generator.add_text('- The year electricity autonomy is: %.1f%%' % year_autonomy_hvac)
        if max_grid_withdraw_hvac_W <= 0:
            self.report_generator.add_text('- the surface of PV (%.2f m²) is sufficient to cover the everyday electricity needs' % neutrality_hvac_pv_surface_m2)
        else:
            starting_day_hour_idx_hvac = daily_electricity_grid_exchange_hvac_W.index(max_grid_withdraw_hvac_W)
            ending_day_hour_idx_hvac = starting_day_hour_idx_hvac + 1
            if ending_day_hour_idx_hvac < len(day_numbers_hvac):
                while ending_day_hour_idx_hvac < len(day_numbers_hvac) and day_numbers_hvac[ending_day_hour_idx_hvac] == day_numbers_hvac[starting_day_hour_idx_hvac]:
                    ending_day_hour_idx_hvac += 1
                max_grid_withdraw_datetime_hvac = self.lpd('datetimes')[round((starting_day_hour_idx_hvac+ending_day_hour_idx_hvac)/2)]
                the_date_hvac: str = max_grid_withdraw_datetime_hvac.strftime('%d/%m/%Y')
                max_grid_withdraw_PV_covering_hvac = max_grid_withdraw_hvac_W / sum(PV_plant_powers_hvac_W[starting_day_hour_idx_hvac:ending_day_hour_idx_hvac]) * neutrality_hvac_pv_surface_m2
                self.report_generator.add_text('- the surface of PV (%.2f m²) is not sufficient to cover all the daily electricity needs. The worst day of the year is %s: %.2f m² of PV should be added' % (neutrality_hvac_pv_surface_m2, the_date_hvac, max_grid_withdraw_PV_covering_hvac - neutrality_hvac_pv_surface_m2))
        self.report_generator.add_text('The following histograms show the distribution of daily electricity balance (PV production - electricity needs) for each month. Positive values indicate that PV production covers the daily needs (surplus), while negative values indicate a deficit.')
        self.report_generator.add_monthly_daily_balance_histogram(f'Daily Electricity Balance - HVAC Only Neutrality Surface ({neutrality_hvac_pv_surface_m2:.2f} m²)', self.lpd('datetimes'), PV_plant_powers_hvac_W, electricity_needs_W)
        # self.report_generator.add_text('- Parametric study of the net energy exchange with the grid, the self consumption and self-production')
        # self.lpd.reset()
        # PV_surface_m2 removed: replaced by neutrality_all_usages_pv_surface_m2 and neutrality_hvac_pv_surface_m2
        # self.parametric()


class Simulator:
    """Building energy simulation engine for thermal and solar calculations.

    This class provides the core simulation engine for building energy analysis,
    implementing thermal calculations, solar energy modeling, and energy balance
    computations. It integrates building geometry, material properties, and
    environmental conditions to predict building energy performance.

    The simulator performs hourly calculations of:
    - Thermal features (U-values, thermal resistances)
    - Solar gains through windows
    - Indoor temperatures and HVAC needs
    - Energy consumption and grid exchange
    - Comfort indicators (discomfort18, discomfort29)
    """

    @staticmethod
    def cumsum(list_of_floats: list[float]) -> list[float]:
        """Compute cumulative sum of a list of floats.

        :param list_of_floats: List of float values to sum cumulatively.
        :type list_of_floats: list[float]
        :return: List of cumulative sums.
        :rtype: list[float]
        """
        cumulated_list_of_floats = []
        total = 0
        for x in list_of_floats:
            total: float = total + x
            cumulated_list_of_floats.append(total)
        return cumulated_list_of_floats

    @staticmethod
    def __compute_thermal_features(lpd: LambdaParametricData, parameter_variation: tuple[str, float] | None = None) -> None:
        """Compute thermal features including U-values and thermal conductances.

        Calculates thermal properties for wall, glass, roof, and ground compositions
        and stores them as results in the parametric data.

        :param lpd: Lambda house parametric data with building compositions.
        :type lpd: LambdaParametricData
        :param parameter_variation: Tuple of parameter name and value to vary. Defaults to None.
        :type parameter_variation: tuple[str, float] | None
        """
        if parameter_variation is None:
            lpd.section('thermal')
        else:
            parameter_name, parameter_value = parameter_variation
            lpd.section('thermal')
            lpd.set(parameter_name, parameter_value)
        wall_composition = Composition(first_layer_indoor=True, last_layer_indoor=False, position='vertical', indoor_average_temperature_in_celsius=21, outdoor_average_temperature_in_celsius=lpd('average_outdoor_temperature_deg'), wind_speed_is_m_per_sec=lpd('average_wind_speed_m_s'), heating_floor=False)
        for material, thickness_m in lpd('wall_composition_in_out'):
            wall_composition.layer(material, thickness_m)

        glass_composition = Composition(first_layer_indoor=True, last_layer_indoor=False, position='vertical', indoor_average_temperature_in_celsius=21, outdoor_average_temperature_in_celsius=lpd('average_outdoor_temperature_deg'), wind_speed_is_m_per_sec=lpd('average_wind_speed_m_s'), heating_floor=False)
        for material, thickness_m in lpd('glass_composition_in_out'):
            glass_composition.layer(material, thickness_m)

        roof_composition = Composition(first_layer_indoor=True, last_layer_indoor=False, position='horizontal', indoor_average_temperature_in_celsius=21, outdoor_average_temperature_in_celsius=lpd('average_outdoor_temperature_deg'), wind_speed_is_m_per_sec=lpd('average_wind_speed_m_s'), heating_floor=False)
        for material, thickness_m in lpd('roof_composition_in_out'):
            roof_composition.layer(material, thickness_m)

        ground_composition = Composition(first_layer_indoor=True, last_layer_indoor=False, position='horizontal', indoor_average_temperature_in_celsius=21, outdoor_average_temperature_in_celsius=lpd('average_outdoor_temperature_deg'), wind_speed_is_m_per_sec=lpd('average_wind_speed_m_s'), heating_floor=False)
        for material, thickness_m in lpd('ground_composition_in_out'):
            ground_composition.layer(material, thickness_m)

        lpd.section('thermal')
        lpd.result('U_wall', wall_composition.U)  # Store U-value, not US
        lpd.result('U_glass', glass_composition.U)
        
        # Compute US values (U * Surface) for thermal calculations
        lpd.result('US_wall', wall_composition.U * lpd('wall_surface_m2'))
        lpd.result('US_glass', glass_composition.U * lpd('glazing_surface_m2'))
        lpd.result('US_roof', roof_composition.U * lpd('floor_surface_m2'))
        lpd.result('US_ground', ground_composition.U * lpd('floor_surface_m2'))
        
        # Store reference US_outdoor for denominator (to maintain sensitivity to solar gains)
        # This is calculated once at initialization with nominal glazing ratios
        # and used in the denominator to prevent masking of direction-specific solar gain effects
        # Calculate reference US_outdoor with nominal glazing ratios
        # This reference should be calculated once and preserved to isolate solar gain effects
        # from thermal loss effects when doing parametric analysis
        if 'US_wall_reference' not in lpd._resulting_data or 'US_glass_reference' not in lpd._resulting_data:
            # Get nominal glazing ratios (first value in parametric range, or current value if not parametric)
            # IMPORTANT: Use nominal values (first in range) to ensure reference is constant across parametric iterations
            try:
                nominal_glazing_ratios = {}
                for direction in ['north', 'south', 'east', 'west']:
                    if f'glazing_ratio_{direction}' in lpd._parametric_possible_values:
                        # Use first value in parametric range as nominal (this is the baseline)
                        nominal_glazing_ratios[direction] = lpd._parametric_possible_values[f'glazing_ratio_{direction}'][1][0]
                    else:
                        # Use nominal parametric value if available, otherwise current value
                        if direction in lpd._nominal_parametric_data:
                            nominal_glazing_ratios[direction] = lpd._nominal_parametric_data[direction]
                        else:
                            nominal_glazing_ratios[direction] = lpd(f'glazing_ratio_{direction}')
                
                # Calculate reference surfaces with nominal ratios
                floor_height_m = lpd('floor_height_m')
                number_of_floors = lpd('number_of_floors')
                total_living_surface_m2 = lpd('total_living_surface_m2')
                shape_factor = lpd('shape_factor')
                
                primary_side_length_m = math.sqrt(number_of_floors * total_living_surface_m2 * shape_factor)
                secondary_side_length_m = math.sqrt(number_of_floors * total_living_surface_m2 / shape_factor)
                
                reference_wall_surface_m2 = floor_height_m * ((2 - nominal_glazing_ratios['north'] - nominal_glazing_ratios['south']) * primary_side_length_m + (2 - nominal_glazing_ratios['west'] - nominal_glazing_ratios['east']) * secondary_side_length_m)
                reference_glazing_surface_m2 = floor_height_m * ((nominal_glazing_ratios['north'] + nominal_glazing_ratios['south']) * primary_side_length_m + (nominal_glazing_ratios['east'] + nominal_glazing_ratios['west']) * secondary_side_length_m)
                
                # Store reference US_wall and US_glass (these are constant across parametric iterations)
                # This ensures the denominator in the thermal balance stays constant, highlighting solar gain differences
                lpd.result('US_wall_reference', wall_composition.U * reference_wall_surface_m2)
                lpd.result('US_glass_reference', glass_composition.U * reference_glazing_surface_m2)
            except Exception:
                # Fallback: use current US_wall and US_glass as reference (they should now always exist)
                try:
                    lpd.result('US_wall_reference', lpd('US_wall'))
                    lpd.result('US_glass_reference', lpd('US_glass'))
                except Exception:
                    # Last resort: compute from current surfaces
                    try:
                        current_wall_surface_m2 = lpd('wall_surface_m2')
                        current_glazing_surface_m2 = lpd('glazing_surface_m2')
                        lpd.result('US_wall_reference', wall_composition.U * current_wall_surface_m2)
                        lpd.result('US_glass_reference', glass_composition.U * current_glazing_surface_m2)
                    except Exception:
                        # Absolute fallback: use zero (should not happen in normal operation)
                        lpd.result('US_wall_reference', 0.0)
                        lpd.result('US_glass_reference', 0.0)

    @staticmethod
    def __compute_solar_gain(lpd: LambdaParametricData) -> None:
        """Compute solar gains through windows for each orientation.

        Creates solar collectors for each window orientation with appropriate
        masks and calculates hourly solar gains.

        :param lpd: Lambda house parametric data with window configurations.
        :type lpd: LambdaParametricData
        """
        # Always create a fresh solar system to ensure we use current glazing surface values
        # This is critical for parametric analysis where glazing ratios vary
        # A new SolarSystem is already empty, so no need to clear_collectors()
        solar_building_system = SolarSystem(lpd.solar_model)
        lpd.result('solar_building_system', solar_building_system)
        for direction in DIRECTIONS_SREF:
            direction_name: str = direction.name.lower()
            # Get current glazing surface for this direction (may vary in parametric analysis)
            glazing_surface_m2: float = lpd('glazing_surface_%s_m2' % direction_name)
            # Solar protection mask: blocks high-altitude sun (summer) while allowing low-altitude sun (winter)
            # For south direction: if protection_angle = 45°, sun is NOT hidden up to 45°, IS hidden above 45°
            # We want to block altitudes > protection_angle, i.e., block altitudes in (angle, 90]
            # RectangularMask with inverted=True blocks altitudes INSIDE the range
            # So we use (angle, 90) with inverted=True to block altitudes in (angle, 90]
            if direction == DIRECTIONS_SREF.SOUTH:
                protection_angle = lpd('south_solar_protection_angle_deg')
                # Block altitudes > protection_angle: use (protection_angle, 90) with inverted=True
                # This blocks altitudes inside (protection_angle, 90], which is what we want
                mask: RectangularMask = RectangularMask(
                    minmax_azimuths_deg=(-90+direction.value, 90+direction.value),
                    minmax_altitudes_deg=(protection_angle, 90),
                    inverted=True
                )
            else:
                # No protection for other directions: allow all altitudes (0, 90)
                mask: RectangularMask = RectangularMask(
                    minmax_azimuths_deg=(-90+direction.value, 90+direction.value),
                    minmax_altitudes_deg=(0, 90),
                    inverted=False
                )
            Collector(solar_building_system, direction_name, exposure_deg=direction.value + lpd('offset_exposure_deg'), slope_deg=SLOPES.VERTICAL.value, surface_m2=glazing_surface_m2, scale_factor=lpd('solar_factor'), close_mask=mask)

        collectors_window_solar_gains_W = solar_building_system.powers_W(gather_collectors=False)
        for collector_name in collectors_window_solar_gains_W:
            lpd.result(collector_name + '_window_solar_gains_W', collectors_window_solar_gains_W[collector_name])
        lpd.result('windows_solar_gains_W', solar_building_system.powers_W(gather_collectors=True))

    @staticmethod
    def hvac_on(indices: tuple[int, int] | tuple[int, int, int, int], i: int) -> bool:
        """Check if HVAC should be active at time index i.

        :param indices: Heating or cooling period indices (2 or 4 values).
                      For 2 values: (start, end) - single period
                      For 4 values: (start1, end1, start2, end2) - two periods (e.g., year-spanning)
        :type indices: tuple[int, int] | tuple[int, int, int, int]
        :param i: Current time index.
        :type i: int
        :return: True if HVAC should be active, False otherwise.
        :rtype: bool
        """
        if indices is None:
            return False
        # Check if period is empty (0, 0) - this means no period
        if len(indices) == 2 and indices[0] == 0 and indices[1] == 0:
            return False
        if len(indices) == 2:
            return indices[0] <= i <= indices[1]
        elif len(indices) == 4:
            # Two periods: check if i is in either the first period (indices[0] to indices[1])
            # or the second period (indices[2] to indices[3])
            return (indices[0] <= i <= indices[1]) or (indices[2] <= i <= indices[3])
        else:
            return False

    @staticmethod
    def __step(lpd: LambdaParametricData, i: int) -> tuple[float, float, float, float]:
        """Compute one simulation time step.

        Calculates indoor temperature, heating needs, cooling needs, and setpoint
        temperature for a single hour based on occupancy, solar gains, and HVAC
        operation.

        :param lpd: Lambda house parametric data.
        :type lpd: LambdaParametricData
        :param i: Time index for the current hour.
        :type i: int
        :return: Tuple of (indoor_temperature, heating_need_W, cooling_need_W, setpoint_temperature_deg).
        :rtype: tuple[float, float, float, float]
        """
        occupancy: float = lpd('occupancy')[i]
        presence: bool = occupancy > 0
        air_volume_m3: float = lpd('air_volume_m3')
        if not presence:
            UQ_ventilation: float = 0
        else:
            UQ_ventilation = (1 - lpd('ventilation_heat_recovery_efficiency')) * 1.204 * 1005 * air_volume_m3 * lpd('air_renewal_presence_vol_per_h')/3600

        # Check if indoor temperature is too high (>26°C) - if so, set solar gains to 0
        # to represent inhabitants closing shutters
        windows_solar_gain_W: float = lpd('windows_solar_gains_W')[i]
        # First, calculate free_indoor_temperature with normal solar gains
        free_gain_W: float = windows_solar_gain_W + occupancy * (lpd('average_occupancy_electric_gain_w') + lpd('average_occupancy_metabolic_gain_w')) + lpd('average_permanent_electric_gain_w')
        
        # Calculate US_outdoor using total wall and glazing surfaces
        # Note: US_wall and US_glass are recalculated when glazing ratios change,
        # so they reflect the current parametric configuration
        US_outdoor: float = lpd('US_wall') + lpd('US_glass') + lpd('US_roof') + UQ_ventilation
        
        # CRITICAL FIX: Use reference US_glass in BOTH numerator and denominator to isolate solar gain effects
        # The problem: When you change glazing_ratio_south, you get:
        #   - More south solar gains (direction-specific, good!)
        #   - More total glazing surface → more US_glass → more thermal loss (affects ALL directions equally, bad!)
        # The thermal loss change is the SAME regardless of which direction you change,
        # which masks the direction-specific solar gain differences.
        # Solution: Use reference US_glass in both numerator and denominator so thermal losses stay constant,
        # allowing only solar gains to vary. This makes direction-specific differences visible.
        if 'US_wall_reference' in lpd._resulting_data and 'US_glass_reference' in lpd._resulting_data:
            # Use reference US_wall and US_glass in BOTH numerator and denominator to isolate solar gain effects
            # wall_surface_m2 changes when glazing ratios change, so we must use US_wall_reference too
            # Use actual US_roof and UQ_ventilation (these don't change with glazing ratios)
            US_outdoor_reference: float = lpd('US_wall_reference') + lpd('US_glass_reference') + lpd('US_roof') + UQ_ventilation
            # Use reference US_wall and US_glass in numerator to keep thermal losses constant
            US_outdoor_for_balance: float = lpd('US_wall_reference') + lpd('US_glass_reference') + lpd('US_roof') + UQ_ventilation
        else:
            # Fallback: use current values if reference not available
            US_outdoor_reference: float = US_outdoor
            US_outdoor_for_balance: float = US_outdoor
        
        # Calculate free indoor temperature using thermal balance
        # Use reference US_glass in BOTH numerator and denominator to isolate solar gain effects
        # This ensures that when you change one direction's glazing ratio:
        #   - Only the solar gains change (direction-specific)
        #   - Thermal losses stay constant (reference US_glass)
        # This makes direction-specific differences clearly visible in parametric analysis
        free_indoor_temperature: float = (free_gain_W + US_outdoor_for_balance * lpd('smooth_outdoor_temperatures_for_hvac_periods_deg')[i] + lpd('US_ground') * lpd('average_outdoor_temperature_deg')) / (US_outdoor_reference + lpd('US_ground'))
        
        # If free indoor temperature > 26°C, recalculate with solar gains = 0 (shutters closed)
        if free_indoor_temperature > 26.0:
            windows_solar_gain_W = 0.0
            free_gain_W = windows_solar_gain_W + occupancy * (lpd('average_occupancy_electric_gain_w') + lpd('average_occupancy_metabolic_gain_w')) + lpd('average_permanent_electric_gain_w')
            free_indoor_temperature = (free_gain_W + US_outdoor_for_balance * lpd('smooth_outdoor_temperatures_for_hvac_periods_deg')[i] + lpd('US_ground') * lpd('average_outdoor_temperature_deg')) / (US_outdoor_reference + lpd('US_ground'))

        heating_period_indices: tuple[int, int] = lpd('heating_period_indices')
        cooling_period_indices: tuple[int, int] = lpd('cooling_period_indices')

        if Simulator.hvac_on(heating_period_indices, i):
            if presence:
                setpoint_temperature_deg: float = lpd('heating_setpoint_deg')
            else:
                setpoint_temperature_deg: float = lpd('heating_setpoint_deg') - lpd('delta_temperature_absence_mode_deg')

            # Use reference US_outdoor for heating need calculation to isolate solar gain effects
            heating_need_W = max(0, (US_outdoor_reference + lpd('US_ground')) * (setpoint_temperature_deg - free_indoor_temperature))
            cooling_need_W = 0

        elif Simulator.hvac_on(cooling_period_indices, i):  # cooling period
            if presence:
                setpoint_temperature_deg = lpd('cooling_setpoint_deg')
                # Use reference US_outdoor for cooling need calculation to isolate solar gain effects
                cooling_need_W = max(0, (US_outdoor_reference + lpd('US_ground')) * (free_indoor_temperature - setpoint_temperature_deg))
                heating_need_W = 0
            else:
                # During absence in cooling period, HVAC is turned off
                setpoint_temperature_deg = None
                cooling_need_W = 0
                heating_need_W = 0
        else:
            heating_need_W = 0
            cooling_need_W = 0
            setpoint_temperature_deg = None

        # Use reference US_outdoor for final temperature calculation to maintain consistency
        indoor_temperature = float(free_indoor_temperature + (heating_need_W - cooling_need_W) / (US_outdoor_reference + lpd('US_ground')))
        return indoor_temperature, heating_need_W, cooling_need_W, setpoint_temperature_deg

    @staticmethod
    def run(lpd: LambdaParametricData) -> None:
        """Run the complete building energy simulation.

        Performs thermal and solar calculations, then simulates hourly building
        behavior over the entire analysis period. Computes energy needs, comfort
        indicators, and grid exchange metrics.

        :param lpd: Lambda house parametric data with building configuration.
        :type lpd: LambdaParametricData
        """

        Simulator.__compute_thermal_features(lpd)
        Simulator.__compute_solar_gain(lpd)

        # Create PV plant with fixed reference surface for electricity calculations
        # This is needed for electricity grid exchange calculations
        if HAS_SOLAR and hasattr(lpd, 'solar_model') and lpd.solar_model is not None:
            try:
                # best_exposure_deg and best_slope_deg should already be set in __init__
                # Just verify they exist, don't try to set them again
                try:
                    _ = lpd('best_exposure_deg')
                    _ = lpd('best_slope_deg')
                except (KeyError, ValueError):
                    # If they're truly missing, calculate them now
                    best_exposure_deg, best_slope_deg = lpd.solar_model.best_direction()
                    # Use result() instead of set() since these are computed values
                    lpd.result('best_exposure_deg', best_exposure_deg)
                    lpd.result('best_slope_deg', best_slope_deg)
                
                reference_PV_surface_m2 = 20.0  # Fixed reference surface for initialization
                lpd.PV_plant = PVplant(
                    lpd.solar_model, 
                    lpd('best_exposure_deg'), 
                    lpd('best_slope_deg'), 
                    mount_type=MOUNT_TYPES.PLAN, 
                    number_of_panels_per_array=10, 
                    panel_width_m=1, 
                    panel_height_m=1, 
                    pv_efficiency=lpd('PV_efficiency'), 
                    temperature_coefficient=0.0035, 
                    distance_between_arrays_m=1, 
                    surface_pv_m2=reference_PV_surface_m2
                )
                # Use result() instead of set() since this is a simulation result
                lpd.result('best_PV_plant_powers_W', lpd.PV_plant.powers_W())
            except Exception as e:
                # If PV plant creation fails, create empty powers list to prevent errors
                # This allows the simulation to continue even if PV calculations fail
                # Use result() instead of set() since this is a simulation result
                lpd.result('best_PV_plant_powers_W', [0.0] * len(lpd))
                warn(f'PV plant creation failed: {e}. Using zero PV production.')
        else:
            # If solar module is not available, use zero PV production
            # Use result() instead of set() since this is a simulation result
            lpd.result('best_PV_plant_powers_W', [0.0] * len(lpd))

        heating_needs_W: list[float] = list()
        cooling_needs_W: list[float] = list()
        hvac_needs_W: list[float] = list()
        max_heating_power_W, max_cooling_power_W = 0, 0
        setpoint_temperatures_deg: list[float | None] = list()
        indoor_temperatures_deg: list[float] = list()

        # Check if we have data to simulate
        if len(lpd) == 0:
            raise ValueError('No time series data available. Cannot run simulation.')

        try:
            for k in range(len(lpd)):
                indoor_temperature_deg, heating_need_W, cooling_need_W, setpoint_temperature_deg = Simulator.__step(lpd, k)
                indoor_temperatures_deg.append(indoor_temperature_deg)
                heating_needs_W.append(float(heating_need_W))
                cooling_needs_W.append(float(cooling_need_W))
                hvac_needs_W.append(float(heating_need_W + cooling_need_W))

                if setpoint_temperature_deg is not None:
                    setpoint_temperatures_deg.append(float(setpoint_temperature_deg))
                else:
                    setpoint_temperatures_deg.append(None)
                if heating_need_W is not None:
                    max_heating_power_W: float = max(float(heating_need_W), max_heating_power_W)
                if cooling_need_W is not None:
                    max_cooling_power_W: float = max(float(cooling_need_W), max_cooling_power_W)
        except KeyError as e:
            raise KeyError(f'Missing required parameter: {e}. This may be due to a deleted section in lambda_parameter_data initialization.') from e
        except Exception as e:
            raise RuntimeError(f'Simulation failed at step {len(indoor_temperatures_deg)}/{len(lpd)}: {e}') from e

        lpd.result('indoor_temperatures_deg', indoor_temperatures_deg)
        lpd.result('avg_indoor_temperatures_deg', sum(indoor_temperatures_deg) / len(lpd))
        lpd.result('setpoint_temperatures_deg', setpoint_temperatures_deg)
        lpd.result('cooling_needs_W', cooling_needs_W)
        lpd.result('heating_needs_W', heating_needs_W)
        lpd.result('hvac_needs_W', hvac_needs_W)
        lpd.result('max_heating_power_W', max_heating_power_W)
        lpd.result('max_cooling_power_W', max_cooling_power_W)
        
        # Calculate energy needs in kWh (primary energy = thermal energy)
        # Primary energy = sum(heating_needs_W) / 1000 (thermal energy in kWh)
        # Final energy = primary energy / COP (electrical energy in kWh)
        lpd.result('heating_needs_kWh', sum(heating_needs_W) / 1000)
        lpd.result('cooling_needs_kWh', sum(cooling_needs_W) / 1000)
        lpd.result('hvac_needs_kWh', sum(hvac_needs_W) / 1000)

        windows_global_gains_W: dict[str, float] = {}
        solar_building_system: SolarSystem = lpd('solar_building_system')
        for collector_name in solar_building_system.collectors:
            collector_windows_solar_gains_W: list[float] = lpd(collector_name + '_window_solar_gains_W')
            smooth_outdoor_temperatures_for_hvac_periods_deg: list[float] = lpd('smooth_outdoor_temperatures_for_hvac_periods_deg')
            glazing_surface_m2: float = lpd('glazing_surface_%s_m2' % collector_name)

            windows_global_gains_W[collector_name] = [collector_windows_solar_gains_W[i] - lpd('U_glass') * glazing_surface_m2 * (indoor_temperatures_deg[i] - smooth_outdoor_temperatures_for_hvac_periods_deg[i]) for i in range(len(lpd))]

        for collector_name in solar_building_system.collectors:
            glazing_surface_m2: float = lpd('glazing_surface_%s_m2' % collector_name)
            
            if lpd('heating_period_duration_h') > 0:
                if lpd('heating_period_indices') is not None and len(lpd('heating_period_indices')) == 2:
                    # Calculate average power in W, then normalize to W/m²
                    avg_power_W = sum([windows_global_gains_W[collector_name][i] for i in range(len(lpd)) if lpd('heating_period_indices')[0] <= i <= lpd('heating_period_indices')[1]]) / lpd('heating_period_duration_h')
                    lpd.result(collector_name + '_heating_windows_global_gains_W', avg_power_W / glazing_surface_m2 if glazing_surface_m2 > 0 else 0)
                else:
                    avg_power_W = sum([windows_global_gains_W[collector_name][i] for i in range(len(lpd)) if lpd('heating_period_indices')[0] <= i <= lpd('heating_period_indices')[1] or lpd('heating_period_indices')[2] <= i <= lpd('heating_period_indices')[3]]) / lpd('heating_period_duration_h')
                    lpd.result(collector_name + '_heating_windows_global_gains_W', avg_power_W / glazing_surface_m2 if glazing_surface_m2 > 0 else 0)
            else:
                lpd.result(collector_name + '_heating_windows_global_gains_W', float('-inf'))  # No heating period, so balance is undefined

            if lpd('cooling_period_duration_h') > 0:
                if lpd('cooling_period_indices') is not None and len(lpd('cooling_period_indices')) == 2:
                    avg_power_W = sum([windows_global_gains_W[collector_name][i] for i in range(len(lpd)) if lpd('cooling_period_indices')[0] <= i <= lpd('cooling_period_indices')[1]]) / lpd('cooling_period_duration_h')
                    lpd.result(collector_name + '_cooling_windows_global_gains_W', avg_power_W / glazing_surface_m2 if glazing_surface_m2 > 0 else 0)
                else:
                    avg_power_W = sum([windows_global_gains_W[collector_name][i] for i in range(len(lpd)) if lpd('cooling_period_indices')[0] <= i <= lpd('cooling_period_indices')[1] or lpd('cooling_period_indices')[2] <= i <= lpd('cooling_period_indices')[3]]) / lpd('cooling_period_duration_h')
                    lpd.result(collector_name + '_cooling_windows_global_gains_W', avg_power_W / glazing_surface_m2 if glazing_surface_m2 > 0 else 0)
            else:
                lpd.result(collector_name + '_cooling_windows_global_gains_W', float('inf'))  # No cooling period, so balance is undefined

        discomfort18_29: list[int] = [0, 0]
        occupancy_counter = 0
        for k, temperature in enumerate(indoor_temperatures_deg):
            if lpd('occupancy')[k] > 0:
                occupancy_counter += 1
                if temperature < 18:
                    discomfort18_29[0] += 1
                if temperature > 29:
                    discomfort18_29[1] += 1

        lpd.result('discomfort18', round(100*discomfort18_29[0]/occupancy_counter, 0) if occupancy_counter != 0 else 0)
        lpd.result('discomfort29', round(100*discomfort18_29[1]/occupancy_counter, 0) if occupancy_counter != 0 else 0)

        lpd.section('electricity')
        lpd.result('electricity_needs_W', [(lpd('heating_needs_W')[i] + lpd('cooling_needs_W')[i]) / lpd('hvac_COP') + (lpd('average_permanent_electric_gain_w') + lpd('occupancy')[i] * lpd('average_occupancy_electric_gain_w')) for i in range(len(lpd))])

        lpd.result('electricity_grid_exchange_W', [lpd('best_PV_plant_powers_W')[i] - lpd('electricity_needs_W')[i] for i in range(len(lpd))])
        filter: Averager = Averager(lpd('electricity_grid_exchange_W'))
        daily_grid_exchange_W, day_numbers = filter.day_month_average(lpd('datetimes'))
        lpd.result('daily_electricity_grid_exchange_W', [-p*24 for p in daily_grid_exchange_W])

        max_grid_withdraw_W: float = max(lpd('daily_electricity_grid_exchange_W'))
        starting_day_hour_index: int = lpd('daily_electricity_grid_exchange_W').index(max_grid_withdraw_W)
        ending_day_hour_index: int = starting_day_hour_index + 1
        if ending_day_hour_index < len(day_numbers):
            while ending_day_hour_index < len(day_numbers) and day_numbers[ending_day_hour_index] == day_numbers[starting_day_hour_index]:
                ending_day_hour_index += 1
            max_grid_withdraw_datetime: datetime = lpd('datetimes')[round((starting_day_hour_index+ending_day_hour_index)/2)]
            max_grid_withdraw_PV_covering_m2: float = max_grid_withdraw_W / sum(lpd('best_PV_plant_powers_W')[starting_day_hour_index: ending_day_hour_index])

            lpd.result('max_grid_withdraw_datetime', max_grid_withdraw_datetime)
            lpd.result('max_grid_withdraw_W', max_grid_withdraw_W)
            lpd.result('max_grid_withdraw_PV_covering_m2', max_grid_withdraw_PV_covering_m2)

        lpd.result('year_autonomy', 100 * year_autonomy(lpd('electricity_needs_W'), lpd('best_PV_plant_powers_W')))
        lpd.result('neeg', 100 * NEEG_percent(lpd('electricity_needs_W'), lpd('best_PV_plant_powers_W')))

        lpd.result('self_consumption', 100 * self_consumption(lpd('electricity_needs_W'), lpd('best_PV_plant_powers_W')))
        lpd.result('self_production', 100 * self_sufficiency(lpd('electricity_needs_W'), lpd('best_PV_plant_powers_W')))

        _month_average_needed_energy_W, days = Averager(lpd('hvac_needs_W')).day_month_average(lpd('datetimes'), month=True, sum_up=True)
        _month_average_PV_energy_W, days = Averager(lpd('best_PV_plant_powers_W')).day_month_average(lpd('datetimes'), month=True, sum_up=True)
        lpd.result('month_average_needed_energy_W', _month_average_needed_energy_W)
        lpd.result('month_average_PV_energy_W', _month_average_PV_energy_W)
        _monthly_electricity_consumption_W, days = Averager(lpd('electricity_needs_W')).day_month_average(lpd('datetimes'), month=True, sum_up=True)
        lpd.result('monthly_electricity_consumption_W', _monthly_electricity_consumption_W)
