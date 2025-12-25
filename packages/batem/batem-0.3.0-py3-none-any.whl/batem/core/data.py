"""Data management and measurement processing module for building energy analysis.

.. module:: batem.core.data

This module provides comprehensive tools for managing and processing measurement data from
building energy systems. It serves as a container for hourly sampled measurement data loaded
from CSV files and weather data from external APIs, with capabilities for data binding,
variable access, and integration with other building energy analysis modules.

Classes
-------

.. autosummary::
   :toctree: generated/

   DataProvider
   IndependentVariableSet
   ParameterSet
   ParameterizedVariableSet
   VariableAccessorRegistry
   Bindings
   VariableAccessor

Classes Description
-------------------

**DataProvider**
    Main interface for accessing all types of measurement and weather data.

**IndependentVariableSet**
    Container for time-series measurement data with regular sampling.

**ParameterSet**
    Container for constant parameters and configuration values.

**ParameterizedVariableSet**
    Container for variables that depend on other parameters.

**VariableAccessorRegistry**
    Registry system for managing data accessors and bindings.

**Bindings**
    System for linking model variable names to measurement data names.

**VariableAccessor**
    Abstract and concrete implementations for data access patterns.

Key Features
------------

* Hourly sampled measurement data management from CSV files
* Weather data integration from OpenWeatherMap and Open-Meteo APIs
* Solar irradiation data generation with weather and masking considerations
* Data binding system for flexible model-measurement variable mapping
* Variable accessor registry for organized data management
* Support for parameter, independent, and parameterized variable types
* Data visualization and export capabilities
* Time series data processing with datetime handling
* Integration with solar module for irradiation calculations
* Support for data subset generation and parent-child relationships

The module is designed for building energy analysis, measurement data processing, and
integration with building energy modeling and simulation systems.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""

from __future__ import annotations
from pathlib import Path
from collections.abc import Iterator
from typing import Type, Any
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import warnings
import pandas
import numpy
import re
import json
import prettytable
from batem.core import timemg
from batem.core.utils import TimeSeriesPlotter
from batem.core.weather import SiteWeatherData, SWDbuilder, convert_from_to_naming
from batem.core.library import Setup
warnings.simplefilter("ignore", category=FutureWarning)

_RESULTS_FOLDER: Path = Setup.folder_path('results')
_DATA_FOLDER: Path = Setup.folder_path('data')


def minmaxval(sequence: list[float]) -> tuple[float | None, float | None]:
    """Return the minimum and the maximum value of a sequence to go faster than compute min and max values separately

    :param sequence: the sequence
    :type sequence: list[float]
    :return: minimum and maximum value
    :rtype: tuple[float, float]
    """
    i: int = 0
    while i < len(sequence) and sequence[i] is None:
        i += 1
    if i < len(sequence):
        _minval = sequence[i]
        _maxval = sequence[i]
        for j in range(i+1, len(sequence)):
            if sequence[j] is not None:
                if sequence[j] < _minval:
                    _minval = sequence[j]
                elif sequence[j] > _maxval:
                    _maxval = sequence[j]
        return _minval, _maxval
    else:
        return None, None


class VariableAccessorRegistry:
    """It is a registry where all the data accessors (parameter, independent or parameterized data accessors)
    have to be registered with the corresponding model name i.e. the data accessor name directly or the
    equivalent model name if the name patterns satisfies the 2-zones'pattern or if there is a measurement-model data
    binding on the data name.
    """

    def __init__(self, bindings: Bindings):
        """Initialize a data accessor registry, taking into account the data name bindings.

        :param bindings: a list of bounds between model data names and measurement data names.
        :type bindings: Bindings
        """
        self.registry: dict[str, Type[VariableAccessor]] = dict()
        self.parameter_variable_accessor: dict[str,
                                               Type[VariableAccessor]] = dict()
        self.independent_variable_accessor: dict[str,
                                                 Type[VariableAccessor]] = dict()
        self.parameterized_variable_accessor: dict[str, Type[VariableAccessor]] = dict(
        )
        self._bindings: Bindings = bindings

    def __call__(self, data_name: str, variable_accessor: Type[VariableAccessor] | None = None) -> None | Type[VariableAccessor]:
        """As a setter if a Data is provided, it searches for the equivalent name (reordered 2 zones'pattern name,
        model name instead of bound data name), identify the type of data (IndependentData,
        ParameterData or ParameterizedData) and record the data into the identified data type set.
        As a getter if no data_accessor is provided (data_accessor is None), it returns the data whose name corresponds to the provided
        or to an equivalent name (reordered 2 zones'pattern name, model name instead of bound data name) whatever the
        type of data is.

        :param data_name: the name of the data
        :type data_name: str
        :param data: the data if used as setter or None id used as a getter, defaults to None
        :type data: Data, optional
        :return: the corresponding data if used as a getter, None otherwise
        :rtype: None | Data
        """
        model_data_name: str = VariableAccessorRegistry.reference(data_name)
        if self._bindings is not None:
            if model_data_name not in self.registry:
                model_data_name = self._bindings.model_name(
                    VariableAccessorRegistry.reference(data_name))

        # getter
        if variable_accessor is None:
            return self.registry[model_data_name]
        else:  # setter
            # if data_model_name in self.data_model_name_data:
            #     raise ValueError("data %s is already existing" % data_name)
            self.registry[model_data_name] = variable_accessor
            if variable_accessor.kind == 'IndependentVariableAccessor':
                self.independent_variable_accessor[model_data_name] = variable_accessor
            elif variable_accessor.kind == 'ParameterAccessor':
                self.parameter_variable_accessor[model_data_name] = variable_accessor
            elif variable_accessor.kind == 'ParameterizedVariableAccessor':
                self.parameterized_variable_accessor[model_data_name] = variable_accessor
            else:
                raise ValueError("Unknown kind of data accessor")
            return None

    def required_data(self, data_accessor_name: str) -> list[Type[VariableAccessor]]:
        """Return the data that are required to determine the given data name.
        It returns a list with a single data when the given data name corresponds
        either to a parameter or to an independent data.
        If the given data name corresponds to a parameterized data, it returns the
        list of the data required to compute the parameterized data.

        :param data_name: the data accessor name
        :type data_name: str
        :return: a list of data
        :rtype: list[Data]
        """
        data_model_name: str = self._bindings.model_name(
            VariableAccessorRegistry.reference(data_accessor_name))
        if data_model_name in self.parameter_variable_accessor:
            return [self.parameter_variable_accessor[data_model_name]]
        elif data_model_name in self.independent_variable_accessor:
            return [self.independent_variable_accessor[data_model_name]]
        else:  # data_model_name in self.parameterized_variable_accessor:
            # type: ignore
            return self.parameterized_variable_accessor[data_model_name].required_data

    @staticmethod
    def reference(name: str) -> str:
        """Reorder zone names by alphabetic order for variable names composed according to the pattern <name>:<zone_x>-<zone_y>
        :param name: data name
        :type name: str
        :return: either <name>:<zone_x>-<zone_y> or <name>:<zone_y>-<zone_x> or the provided name if it does not match the pattern
        """
        if re.match('^\\w+:\\w+-\\w+$', name):
            simple_name, zone1_name, zone2_name = re.findall(
                '^(\\w+):(\\w+)-(\\w+)$', name)[0]
            if zone1_name > zone2_name:
                return simple_name + ':' + zone2_name + '-' + zone1_name
            else:
                return simple_name + ':' + zone1_name + '-' + zone2_name
        return name

    def __contains__(self, data_accessor_name) -> bool:
        """check is the data accessor name is known. If the name satisfies the pattern
        <zone_x>-<zone_y>:<name>, zone names are re-organized in an alphabetic order.
        It the name corresponds to a bound measurement or to a model name,
        it returns True, otherwise False.

        :param data_name: the data name
        :type data_name: str
        :return: True if the name is known, else False
        :rtype: bool
        """
        data_model_name: str = self._bindings.model_name(
            VariableAccessorRegistry.reference(data_accessor_name))
        return data_model_name in self.registry or data_accessor_name in self.registry


class VariableSet(ABC):
    """Abstract class defining what is a variable set. A variable set gives access to all the values of the variables
    of the same kind: there are 3 kinds of variable sets: 'ParameterSet', 'IndependentSet' or 'ParameterizedSet'. Generally speaking, a variable set should not be accessed by the user directly but through a Data Provider. The variable sets are used internally.
    """

    def __init__(self, kind: str) -> None:
        """Initialize a variable set of a specific kind.

        :param kind: the kind of variable set
        :type kind: str
        """
        super().__init__()
        self.kind: str = kind

    @abstractmethod
    def __call__(self, *args: "Any", **kwds: "Any") -> None | float | list[float]:
        """Getter and Setter to interact with the values of a variable from the current set

        :return: _description_
        :rtype: None | float | list[float]
        """
        raise NotImplementedError

    @abstractmethod
    def value_to_level(self, variable_name: str, variable_value: float) -> int:
        """Returns an integer, named level, which is a discretization of the given variable value

        :param variable_name: the variable name
        :type variable_name: str
        :param variable_value: the variable value
        :type variable_value: float
        :rtype: int
        """
        raise NotImplementedError

    @abstractmethod
    def level_to_value(self, variable_name: str, level: int) -> float:
        """Convert a discrete level into a value

        :param variable_name: the variable name
        :type variable_name: str
        :param level: an integer representing the discrete level of a variable
        :type level: int
        :return: the variable value corresponding to the discrete level
        :rtype: float
        """
        raise NotImplementedError

    @abstractmethod
    def __contains__(self, variable_name: str) -> bool:
        """Check wether the variable name exists in the variable set.

        :param data_name: the variable name
        :type data_name: str
        :return: True if exists, False otherwise
        :rtype: bool
        """
        raise NotImplementedError


class ParameterSet(VariableSet):
    """
    A parameter is referring to a single value that may change from one hour simulation step to another, but more commonly, from a simulation to another. If lower and upper bounds of the value domain are specified but also the resolution (the smallest possible
    variation of the value), the parameter is said adjustable.
    """

    def __init__(self) -> None:
        """
        Initialize a parameter set with given resolution, used to store in a cache of already computed state models in order to reduce computations but also to estimate the parameters' values. If resolution = n, then the parameter intervals will be decomposed in n and all the state models belonging to the same hypercube are considered as equal.
        """
        super().__init__('ParameterSet')
        self.initial_parameter_values: dict[str, float] = dict()
        self._parameter_names: list[str] = list()
        self.known_parameter_values: dict[str, float] = dict()
        self.__adjustable_parameter_names: list[str] = list()
        self.adjustable_resolutions: dict[str, float] = dict()
        self.adjustable_parameter_levels: dict[str, int] = dict()
        self.adjustable_level_bounds: dict[str, tuple[int, int]] = dict()
        self.adjustable_parameter_bounds: dict[str,
                                               tuple[float, float]] = dict()
        self.zone_parameters: dict[str, list[str]] = dict()
        self.connected_zones_parameters: dict[tuple[str, str], list[str]] = dict(
        )

    def reference(self, parameter_name: str):
        if re.match('^\\w+:\\w+-\\w+$', parameter_name):
            simple_parameter_name, zone1, zone2 = re.findall(
                '^(\\w+):(\\w+)-(\\w+)$', parameter_name)[0]
            if zone2 < zone1:
                zone1, zone2 = zone2, zone1
            parameter_name = '%s:%s-%s' % (simple_parameter_name, zone1, zone2)
        return parameter_name

    def __contains__(self, parameter_name: str) -> bool:
        """Check wether a parameter exists or not.
        If the parameter is named as "zone_x:zone_y:name" and if zone_y is lower than zone_x according to the alphabetic order,
        the name "zone_y:zone_x:name" will be used instead.

        :param parameter_name: the parameter name
        :type parameter_name: str
        :return: True if the parameter exist, False otherwise
        :rtype: bool
        """
        return self.reference(parameter_name) in self._parameter_names

    def __call__(self, name: str, value: float | None = None, bounds_resolution: tuple[float, float, float] | None = None) -> None | float:
        """Getter if value and bounds_resolution are not given, setter otherwise

        :param name: the parameter name
        :type name: str
        :param value: the parameter value, defaults to None
        :type value: float, optional
        :param bounds_resolution: a tuple containing the lower bound, the upper bound and the resolution of the parameter, defaults to None
        :type bounds_resolution: tuple[float, float, float], optional
        :return: return the parameter value if used as a getter, None otherwise
        :rtype: None | float
        """
        if re.match('^\\w+:\\w+$', name):  # zone related parameter
            zone, simple_parameter_name = re.findall(
                '^(\\w+):(\\w+)$', name)[0]
            if zone in self.zone_parameters and simple_parameter_name not in self.zone_parameters[zone]:
                self.zone_parameters[zone].append(simple_parameter_name)
            else:
                self.zone_parameters[zone] = [simple_parameter_name]
        elif re.match('^\\w+:\\w+-\\w+$', name):  # connected zones related parameters
            simple_parameter_name, zone1, zone2 = re.findall(
                '^(\\w+):(\\w+)-(\\w+)$', name)[0]
            if zone2 < zone1:
                zone1, zone2 = zone2, zone1
            if (zone1, zone2) in self.connected_zones_parameters and simple_parameter_name not in self.connected_zones_parameters[(zone1, zone2)]:
                self.connected_zones_parameters[(zone1, zone2)].append(
                    simple_parameter_name)
            else:
                self.connected_zones_parameters[(zone1, zone2)] = [
                    simple_parameter_name]
            name = '%s:%s-%s' % (simple_parameter_name, zone1, zone2)
        elif not re.match('^\\w+$', name):
            raise ValueError("Invalid parameter name: %s" % name)
        if value is None:  # getter
            if name in self.known_parameter_values:
                return self.known_parameter_values[name]
            elif name in self.__adjustable_parameter_names:
                return self.level_to_value(name, self.adjustable_parameter_levels[name])
            else:
                raise ValueError('Unknown parameter "%s"' % name)
        # setter for a simple float/int parameter value, possibly adjustable
        elif type(value) is float or type(value) is int:
            if name not in self._parameter_names:
                self._parameter_names.append(name)
            if name not in self.initial_parameter_values:
                self.initial_parameter_values[name] = value
            if bounds_resolution is not None:
                if bounds_resolution[0] < bounds_resolution[1]:
                    if value < bounds_resolution[0] or value > bounds_resolution[1]:
                        raise ValueError(
                            'Parameter name "%s" is initialized out of is range' % name)
                    self.adjustable_resolutions[name] = bounds_resolution[2]
                    self.adjustable_parameter_bounds[name] = (
                        bounds_resolution[0], bounds_resolution[1])
                    self.adjustable_level_bounds[name] = (
                        0, int((bounds_resolution[1] - bounds_resolution[0]) // bounds_resolution[2]))
                    self.__adjustable_parameter_names.append(name)
                else:
                    raise ValueError(
                        'Recheck bounds and resolution for parameter "%s"' % name)
                self.adjustable_parameter_levels[name] = self.value_to_level(
                    name, self.initial_parameter_values[name])
            elif name in self.__adjustable_parameter_names:
                self.adjustable_parameter_levels[name] = self.value_to_level(
                    name, value)
            else:
                self.known_parameter_values[name] = value
        else:
            raise ValueError(
                'Incompatible value type for parameter value "%s"' % name)
        return None

    def __iter__(self) -> Iterator[str]:
        return self._parameter_names.__iter__()

    def __next__(self):
        return self._parameter_names.__next__()

    def get_zone_parameter_names(self, zone_name: str) -> list[str]:
        """Return all the parameter names related to the specified zone i.e. parameters named like "zone_x:name"

        :param zone_name: the zone name
        :type zone_name: str
        :return: the list of parameter names related to the specified zone
        :rtype: list[str]
        """
        return ['%s:%s' % (zone_name, parameter_name) for parameter_name in self.zone_parameters[zone_name]]

    def get_connected_zones_parameter_names(self, zone1_name: str, zone2_name: str) -> list[str]:
        """Return all the parameter names related to the interface between 2 zones i.e. parameters named like "zone_x-zone_y:name"

        :param zone1_name: one of the 2 zone names
        :type zone1_name: str
        :param zone2_name: the second zone name
        :type zone2_name: str
        :return: the list of parameter names related to the interface between the 2 specified zones
        :rtype: list[str]
        """
        if zone2_name < zone1_name:
            zone1_name, zone2_name = zone2_name, zone1_name
        return ['%s:%s-%s' % (parameter_name, zone1_name, zone2_name) for parameter_name in self.connected_zones_parameters[(zone1_name, zone2_name)]]

    def set_adjustable_levels(self, levels: list[int]) -> None:
        """Modify the levels, and indirectly the values, of all the adjustable parameters at once

        :param levels: list of levels according to the list of adjustable parameters
        :type levels: list[int]
        """
        for i, adjustable_parameter in enumerate(self.__adjustable_parameter_names):
            self.adjustable_parameter_levels[adjustable_parameter] = levels[i]

    @property
    def values(self) -> dict[str, float]:
        """Return a dictionary with each parameter name and its corresponding value

        :return: the parameter values
        :rtype: dict[str, float]
        """
        return {parameter_name: self(parameter_name) for parameter_name in self._parameter_names}  # type: ignore

    @property
    def adjustable_parameter_names(self):
        """Return a dictionary with each adjustable parameter name and its corresponding value

        :return: the adjustable parameter values
        :rtype: dict[str, float]
        """
        return self.__adjustable_parameter_names

    def value_to_level(self, parameter_name: str, parameter_value: float | None = None) -> int:
        """Convert a parameter value into a parameter level

        :param parameter_name: the parameter name
        :type parameter_name: str
        :param parameter_value: the parameter value, defaults to None
        :type parameter_value: float, optional
        :return: the corresponding parameter level
        :rtype: int
        """
        parameter_name = self.reference(parameter_name)
        if len(self.adjustable_parameter_bounds) == 0:
            return 0
        if parameter_value is None:
            parameter_value = self(parameter_name, 0)
        return int((parameter_value - self.adjustable_parameter_bounds[parameter_name][0]) // self.adjustable_resolutions[parameter_name])

    def level_to_value(self, parameter_name: str, level: int) -> float:
        """Convert a parameter level into a parameter value

        :param parameter_name: the parameter name
        :type parameter_name: str
        :param level: the parameter level
        :type level: int
        :return: the corresponding parameter value
        :rtype: float
        """
        parameter_name = self.reference(parameter_name)
        return self.adjustable_parameter_bounds[parameter_name][0] + level * self.adjustable_resolutions[parameter_name]

    def reset(self) -> None:
        """Reset adjustable parameters to their initial values
        """
        initial_levels: list[int] = list()
        for i in range(self.number_of_ajustables):
            initial_levels[self.__adjustable_parameter_names[i]] = self.value_to_level(
                self.__adjustable_parameter_names[i], self.initial_parameter_values[self.__adjustable_parameter_names[i]])
        self.adjustable_parameter_levels = initial_levels

    def levels(self, adjustable_parameter_names: str | None = None) -> int | tuple[int]:
        """Return the levels of the specified adjustable parameter names. If None is given, all the adjustable parameter names are returned

        :param parameter_names: the list of adjustable parameter names of interest, defaults to None
        :type parameter_names: str, optional
        :return: a tuple with levels of the specified adjustable parameters
        :rtype: int | tuple[int]
        """
        adjustable_parameter_names = self.reference(adjustable_parameter_names)
        if adjustable_parameter_names is None:
            adjustable_parameter_names = self.__adjustable_parameter_names
        if type(adjustable_parameter_names) is not list:
            adjustable_parameter_names = list(adjustable_parameter_names)
        return [self.adjustable_parameter_levels[parameter_name] for parameter_name in adjustable_parameter_names]

    @property
    def number_of_ajustables(self) -> int:
        """Return the number of adjustable parameters

        :return: the number of adjustable parameters
        :rtype: int
        """
        return len(self.__adjustable_parameter_names)

    @property
    def adjustable_values(self) -> list[float]:
        """Return the list of all the adjustable values

        :return: the list of all the adjustable values
        :rtype: list[float]
        """
        return [self.level_to_value(parameter_name, self.adjustable_parameter_levels[parameter_name]) for i, parameter_name in enumerate(self.__adjustable_parameter_names)]

    def save(self, file_name: str = 'best_parameters') -> None:
        """Save in a json file, the state of the parameter set

        :param file_name: the json file name without the ".json" extension, default to "best_parameters"
        :type file_name: str
        """
        saved: dict = dict()
        saved['initial_parameter_values'] = self.initial_parameter_values
        saved['parameter_names'] = self._parameter_names
        saved['known_parameter_values'] = self.known_parameter_values
        saved['adjustable_parameter_names'] = self.__adjustable_parameter_names
        saved['adjustable_resolutions'] = self.adjustable_resolutions
        saved['adjustable_parameter_levels'] = self.adjustable_parameter_levels
        saved['adjustable_level_bounds'] = self.adjustable_level_bounds
        saved['adjustable_parameter_bounds'] = self.adjustable_parameter_bounds
        output_path = _RESULTS_FOLDER / f"{file_name}.json"
        with open(output_path, "w", encoding='utf-8') as outfile:
            outfile.write(json.dumps(saved))

    def load(self, file_name: str = "best_parameters"):
        """Load the state of the parameter set from a json file

        :param file_name: the json file name without the ".json" extension, default to "best_parameters"
        :type file_name: str
        """
        # Use _RESULTS_FOLDER to match where save() writes the file
        data_json_path = _RESULTS_FOLDER / f"{file_name}.json"
        if data_json_path.exists():
            with open(data_json_path, 'r', encoding='utf-8') as file:
                saved: dict = json.load(file)
            self.initial_parameter_values = saved['initial_parameter_values']
            self._parameter_names = saved['parameter_names']
            self.known_parameter_values = saved['known_parameter_values']
            self.__adjustable_parameter_names = saved['adjustable_parameter_names']
            self.adjustable_resolutions = saved['adjustable_resolutions']
            self.adjustable_parameter_levels = saved['adjustable_parameter_levels']
            # Convert lists to tuples when loading from JSON (JSON doesn't support tuples)
            self.adjustable_level_bounds = {k: tuple(v) if isinstance(v, list) else v for k, v in saved['adjustable_level_bounds'].items()}
            self.adjustable_parameter_bounds = {k: tuple(v) if isinstance(v, list) else v for k, v in saved['adjustable_parameter_bounds'].items()}
            print(f"Loaded parameters from {data_json_path}")
        else:
            print(f"Parameter file {data_json_path} not found, using default parameters")

    def __len__(self) -> int:
        """Return the total number of parameters

        :return: the total number of parameters
        :rtype: int
        """
        return len(self._parameter_names)

    def __str__(self) -> str:
        """
        Return a string representation of a parameter set

        :return: a string representation of a parameter set
        :rtype: str
        """
        pretty_table = prettytable.PrettyTable(header=True)
        pretty_table.add_column('name', self.__adjustable_parameter_names)
        pretty_table.add_column(
            'value', ['%.3g' % v for v in self.adjustable_values])
        pretty_table.add_column('v. bounds', [
                                '(%.3g, %.3g)' % self.adjustable_parameter_bounds[pname] for pname in self.__adjustable_parameter_names])
        pretty_table.add_column('level', ['%i' % self.adjustable_parameter_levels[parameter_name]
                                for parameter_name in self.adjustable_parameter_levels])
        pretty_table.add_column('l. bounds', [
                                '(%i, %i)' % self.adjustable_level_bounds[pname] for pname in self.__adjustable_parameter_names])
        return pretty_table.__str__()


class IndependentVariableSet(VariableSet):
    """It gathers measurement data corresponding to dates with a regular sample time. A Independent Variable Set (IVS) gives an easy access to recorded data, starting at 0:00:00 of a specified day a ending at 23:00:00 (included) of another specified day (included) with a one-hour sampling period. It can plot or save data. Indeed, data whose length is equal to the number of hours of the IVS, can be added at any time and analyzed at the end."""

    # type: ignore
    def __init__(self, location: str, latitude_north_deg: float, longitude_east_deg: float, csv_measurement_filename: str | None = None,  starting_stringdate: str | None = None, ending_stringdate: str | None = None, parent_ivs: IndependentVariableSet | None = None, albedo: float = .1, pollution: float = 0.1,  deleted_variables: tuple[str] = (),  number_of_levels: int = 4, initial_year: int = 1980):
        """Create a set with data collected from a csv or a json openweather or open-meteo.com file.

        :param csv_measurement_filename: name of the csv file containing measurement data with different format of date in the 3 first columns (string like '15/02/2015 00:00:00' for the first one, epochtime in ms for the second one, and datetime.datetime for the 3rd one). The first row is used as name for the data of the related column. The file with the provided name will be search in the data folder defined in the setup.ini file in the project root folder. Data must be organized in ascending order. If None, consider a json weather file name is provided, default to None.
        :type csv_measurement_filename: str
        :param json_openweather_filename: name of the json weather file that can come either from the openweathermap.org (https://openweathermap.org) web site or from the open-meteo.com web site (https://open-meteo.com)
        :type json_openweather_filename: str
        :param parent_ivs: parent independent variable set used internally to generate excerpt of existing independent variable set. Default to None
        :type parent_ivs: IndependentVariableSet
        :param starting_stringdate: initial date in format 'dd/mm/YYYY' or None. If None the first date of the file starting at 0:00:00 time will be selected, default to None, optional
        :type starting_stringdate: str
        :param ending_stringdate: final date in format 'dd/mm/YYYY' or None. If None the latest date of the file starting at 23:00:00 time will be selected, default to None, optional
        :type ending_stringdate: str
        :param albedo: the albedo at current location. Default to 0.1
        :type albedo: float
        :param location: name of the location
        :type location: str
        :param deleted_variables: list of the weather variables to be deleted after loading. Default to empty list
        :type deleted_variables: list[str]
        :param number_of_levels: number of levels to convert each data value into a level. It is used for handling nonlinearities in state models: different . Default to 4.
        """
        super().__init__('IndependentVariableSet')
        self._dataframe = pandas.DataFrame()
        self.sample_time_in_secs: int = 3600
        self.specified_starting_stringdatetime = None
        self.specified_ending_stringdatetime = None
        self.variable_bounds: dict[str, tuple[float, float]] = dict()
        self.site_weather_data: None = None
        self.number_of_levels: int = number_of_levels
        self._variable_levels: dict[str, list[int]] = dict()
        if starting_stringdate is not None:
            self.specified_starting_stringdatetime: str = starting_stringdate + " 0:00:00"
        if ending_stringdate is not None:
            self.specified_ending_stringdatetime = ending_stringdate + " 23:00:00"
        # Calculate end_year from ending_stringdate if available, otherwise let SWDbuilder calculate it
        # initial_year is the start year for downloading the weather archive
        # end_year should cover the requested date range
        end_year: int | None = None
        if ending_stringdate is not None:
            end_year = int(ending_stringdate.split('/')[-1])
        # Use initial_year as provided - it determines the start of the download range
        swd_builder: SWDbuilder = SWDbuilder(location=location, latitude_north_deg=latitude_north_deg, longitude_east_deg=longitude_east_deg, initial_year=initial_year, end_year=end_year)

        all_deleted_variables: list[str] = [
            'dewpoint_2m',
            'weather_code',  # Updated from weathercode to weather_code
            'et0_fao_evapotranspiration',
            'vapor_pressure_deficit',
            'weather_soil_temperature_0cm',
            'soil_moisture_0_to_7cm',
            'soil_moisture_7_to_28cm',
            'soil_moisture_28_to_100cm',
            'soil_moisture_100_to_255cm',
            'is_day',
            'Tyanis',
            'zetaW7',
            'zetaW9',
            'occupancy',
            'temp_min',
            'temp_max',
            'description',
            'power_heater',
            'temperature_2m',
            'relativehumidity_2m',
            'dewpoint_2m',
            'apparent_temperature',
            'pressure_msl',
            'surface_pressure']
        all_deleted_variables.extend(deleted_variables)

        self.site_weather_data = swd_builder(from_stringdate=self.specified_starting_stringdatetime.split(' ')[0], to_stringdate=self.specified_ending_stringdatetime.split(' ')[0], albedo=albedo, pollution=pollution, from_to_naming=convert_from_to_naming())

        if parent_ivs is None:
            if csv_measurement_filename is not None:
                self._dataframe = pandas.read_csv(
                    _DATA_FOLDER / csv_measurement_filename, sep=',', parse_dates=['datetime'])
                self._dataframe = self._dataframe.astype(
                    {'epochtime': 'int64', 'stringtime': 'str'})
                self._dataframe['datetime'] = pandas.to_datetime(
                    self._dataframe['datetime']).dt.tz_localize(self.site_weather_data.timezone_str, ambiguous=True)
                self._dataframe = self._dataframe.astype(
                    {v: float for v in self._dataframe.columns[3:]})
                min_values: float = self._dataframe.min()
                max_values: float = self._dataframe.max()
                for i, column_name in enumerate(self._dataframe.columns):
                    self.variable_bounds[column_name] = (
                        min_values.iloc[i], max_values.iloc[i])  # type: ignore
                if self.specified_starting_stringdatetime is not None:
                    specified_starting_datetime = pandas.Timestamp(timemg.stringdate_to_datetime(
                        self.specified_starting_stringdatetime, date_format='%d/%m/%Y %H:%M:%S', timezone_str=self.site_weather_data.timezone_str))
                    self._dataframe.drop(
                        self._dataframe[self._dataframe['datetime'] < specified_starting_datetime].index, inplace=True)
                else:
                    i: int = 0
                    while not (self._dataframe['stringtime'][i].split(' ')[1] == '0:00:00' or self._dataframe['stringtime'][i].split(' ')[1] == '00:00:00'):
                        i += 1
                    # i -= 1  ######
                    if i != 0:
                        self._dataframe: pandas.dataframe = self._dataframe[i:]
                    self.specified_starting_stringdatetime = self._dataframe['stringtime'].iloc[0]

                if self.specified_ending_stringdatetime is not None:
                    specified_ending_datetime = pandas.Timestamp(timemg.stringdate_to_datetime(
                        self.specified_ending_stringdatetime, date_format='%d/%m/%Y %H:%M:%S', timezone_str=self.site_weather_data.timezone_str))
                    self._dataframe.drop(
                        self._dataframe[self._dataframe['datetime'] > specified_ending_datetime].index, inplace=True)
                else:
                    i: int = len(self._dataframe)-1
                    while self._dataframe['stringtime'][i].split(' ')[1] != '23:00:00':
                        i -= 1
                    if i != len(self._dataframe)-1:
                        self._dataframe = self._dataframe[:i+1]
                    self.specified_ending_stringdatetime = self._dataframe['stringtime'].iloc[-1]
                print('recorded data loaded')
            # Weather data was already loaded earlier (line 674), so we don't need to load it again
            # Just update the string datetimes if they weren't set from CSV
            if csv_measurement_filename is None:
                self.starting_weather_stringdatetime: str = self.site_weather_data.from_stringdate
                self.ending_weather_stringdatetime = self.site_weather_data.to_stringdate
                data = dict()
                data['datetime'] = self.site_weather_data.datetimes  # type: ignore
                data['stringtime'] = self.site_weather_data.stringdates
                data['epochtime'] = [int(timemg.datetime_to_epochtimems(dt) / 1000) for dt in data['datetime']]
                self._dataframe = pandas.DataFrame.from_dict(data, orient='columns')

            self._dataframe.reset_index(inplace=True, drop=True)
            self._dataframe['day_of_year'] = self._dataframe['datetime'].dt.day_of_year
            self._dataframe['day_of_week'] = self._dataframe['datetime'].dt.day_of_week
            self._dataframe['hour'] = self._dataframe['datetime'].dt.hour
            self._dataframe['year'] = self._dataframe['datetime'].dt.year

            self.day_counter: int = -1
            _current_day: int = -1
            day_index: list[int] = list()
            hour_index: list[int] = list()
            for i in self._dataframe.index:
                hour_index.append(i)
                if self._dataframe['day_of_year'][i] != _current_day:
                    self.day_counter += 1
                    _current_day: int = self._dataframe['day_of_year'][i]
                day_index.append(self.day_counter)
            self.variable_bounds['day_of_year'] = (0, self.day_counter)
            self.variable_bounds['day_of_week'] = (
                self._dataframe['day_of_week'].min(), self._dataframe['day_of_week'].max())
            self.variable_bounds['hour'] = (
                self._dataframe['hour'].min(), self._dataframe['hour'].max())
            self.variable_bounds['year'] = (
                self._dataframe['year'].min(), self._dataframe['year'].max())
            self.add_var('hour_index', hour_index)
            self.add_var('day_index', day_index)
            self.datetime_pd_series: pandas.TimestampSeries = pandas.to_datetime(
                self._dataframe["datetime"])
            self.specified_starting_stringdatetime: str = self._dataframe['stringtime'][0]
            self.specified_ending_stringdatetime: str = self._dataframe['stringtime'][len(
                self._dataframe)-1]

            deleted_column_names = []
            for deleted_variable in all_deleted_variables:
                if deleted_variable in self._dataframe.columns:
                    deleted_column_names.append(deleted_variable)
            self._dataframe.drop(columns=deleted_column_names, inplace=True)

            for variable_name in self.site_weather_data.variable_names:
                if variable_name not in all_deleted_variables and variable_name != "epochtimems":
                    values: list[float] = self.site_weather_data.series(
                        variable_name)

                    # Try to align weather data with measurement data timestamps
                    if len(values) != len(self._dataframe):
                        aligned_values = self._align_weather_data(values, variable_name)
                        if aligned_values is not None:
                            values = aligned_values

                    self.add_var(
                        'weather_' + variable_name, values)
                    self.variable_bounds[variable_name] = minmaxval(values)

        else:  # parent_independent_variable_set is not None

            self.number_of_levels = parent_ivs.number_of_levels
            self.variable_bounds = parent_ivs.variable_bounds
            self.kind: str = 'IndependentVariableSet'
            self._variable_levels: dict[str,
                                        list[int]] = parent_ivs._variable_levels
            self.site_weather_data = parent_ivs.site_weather_data.clone()  # type: ignore  # noqa (...,starting_stringdate, ending_stringdate)

            if starting_stringdate is not None:
                self.specified_starting_stringdatetime = starting_stringdate + " 0:00:00"
                specified_starting_datetime = timemg.stringdate_to_datetime(  # type: ignore  # noqa
                    self.specified_starting_stringdatetime, date_format='%d/%m/%Y %H:%M:%S')
            else:
                self.specified_starting_stringdatetime = parent_ivs.specified_starting_stringdatetime

            if ending_stringdate is not None:
                self.specified_ending_stringdatetime = ending_stringdate + " 23:00:00"
                specified_ending_datetime: datetime = timemg.stringdate_to_datetime(  # type: ignore  # noqa
                    self.specified_ending_stringdatetime, date_format='%d/%m/%Y %H:%M:%S')
                specified_ending_datetime += timedelta(hours=1)
            else:
                self.specified_ending_stringdatetime = parent_ivs.specified_ending_stringdatetime

            timezone_str: str = self.site_weather_data.timezone_str
            datetime_series = pandas.to_datetime(  # type: ignore  # noqa
                parent_ivs._dataframe['datetime'], unit='ns').dt.tz_convert(timezone_str)
            mask = (datetime_series >= specified_starting_datetime) & (
                datetime_series <= specified_ending_datetime)
            self._dataframe = parent_ivs._dataframe[mask].copy()  # type: ignore  # noqa    # type: ignore  # noqa

    def value_to_level(self, variable_name: str, variable_value: float) -> int:
        """Convert a variable value into a discrete level

        :param variable_name: the name of the variable
        :type variable_name: str
        :param variable_value: the variable name
        :type variable_value: float
        :return: the discrete level
        :rtype: int
        """
        if variable_name in self.variable_bounds:
            lower_bound = self.variable_bounds[variable_name][0]
            upper_bound = self.variable_bounds[variable_name][1]
            bound_range = upper_bound - lower_bound
            if bound_range == 0:
                # If bounds are the same, return a fixed level (middle of range)
                return round((self.number_of_levels - 1) / 2)
            return round(((self.number_of_levels - 1) * (variable_value - lower_bound)) // bound_range)
        else:
            return 0

    def level_to_value(self, variable_name: str, level: int) -> float:
        """Convert the discrete level of a variable into a value

        :param variable_name: the name of the variable
        :type variable_name: str
        :param level: the discrete level
        :type level: int
        :return: the value of the variable
        :rtype: float
        """
        return self.variable_bounds[variable_name][0] + level / (self.number_of_levels - 1) * (self.variable_bounds[variable_name][1] - self.variable_bounds[variable_name][0])

    def levels(self, variable_names: str | list[str], k: int = None) -> list[list[int]] | list[int] | int:
        """Return the level(s) of either a variable or a list of variables. If a single variable is specified, it return the level corresponding to the specified time slot k or, if None, the list of all the discrete levels for all time slots. Similarly, if a list of variables is specified, a list of levels for each variable is returned.

        :param variable_names: a single or multiple variable names
        :type variable_names: str | list[str]
        :param k: an optional specific time sample or None for all time slots, defaults to None
        :type k: int, optional
        :return: a level, a list of levels, a list of list of levels corresponding to the request
        :rtype: list[list[int]] | list[int] | int
        """
        if type(variable_names) is not list:
            variable_names = list(variable_names)
            return [self.value_to_level(variable_name, self(variable_name, k)) for i, variable_name in enumerate(variable_names)]
        else:
            _levels = list()
            for k_slot in range(len(self)):
                _levels.append([self.value_to_level(variable_name, self(
                    variable_name, k_slot)) for i, variable_name in enumerate(variable_names)])
        return _levels

    def bounds(self, variable_name: str) -> tuple[float, float]:
        """Return the minimum and maximum values of a given variable

        :param variable_name: the given variable name
        :type variable_name: str
        :return: the interval of the variable value domain
        :rtype: tuple[float, float]
        """
        return self.variable_bounds[variable_name]

    def __contains__(self, variable_name: str) -> bool:
        """check if a variable name is belonging to the independent variable set

        :param variable_name: the variable name
        :type variable_name: str
        :return: True is the variable name is known, False otherwise
        :rtype: bool
        """
        return variable_name in self._dataframe.columns

    @property
    def starting_stringdate(self) -> str:
        """Return the starting day of the IVS

        :return: the starting day of the IVS as a string 'DD/MM/YYYY'
        :rtype: str
        """
        return self.specified_starting_stringdatetime.split(' ')[0]

    @property
    def ending_stringdate(self) -> str:
        """Return the ending day of the IVS

        :return: the ending day of the IVS as a string 'DD/MM/YYYY'
        :rtype: str
        """
        return self.specified_ending_stringdatetime.split(' ')[0]

    @property
    def number_of_variables(self) -> int:
        """Return the number of variables in the IVS (without counting the variables related to the time)

        :return:  the number of variables
        :rtype: int
        """
        return len(self._dataframe.columns) - 3

    @property
    def variable_names(self) -> list[str]:
        """Return the list of variables in the IVS

        :return: the list of variable
        :rtype: list[str]
        """
        return [self._dataframe.columns[i] for i in range(3, len(self._dataframe.columns))]

    def import_weather_variable(self, weather_variable_name: str, new_variable_name: str = None) -> None:
        """Add an variable belonging to the weather data to the IVS, either with a prefix 'weather_' or under the specified name.

        :param weather_variable_name: the name of the weather variable
        :type weather_variable_name: str
        :param new_variable_name: the possible specified name of the variable into the IVS, defaults to None
        :type new_variable_name: str, optional
        """
        if new_variable_name is None:
            new_variable_name = 'weather_' + weather_variable_name

        self.add_var(
            new_variable_name, self.weather_data.get(weather_variable_name))

    def add_var(self, name: str, values: list[float], force: bool = False) -> None:
        """Use to add a invariant series of values to the IVS. It will appears as any other measurements. The number of values must correspond to the number of hours for the data container.

        :param label: name of the series of timed values (each value corresponds to 1 hour)
        :type label: str
        :param values: series of values but it must be compatible with the times which are common to all series
        :type values: list[float]
        :param force: if True, replace existing variable with same name if it has the same size, defaults to False
        :type force: bool, optional
        """

        try:
            self._dataframe[name] = values
        except:  # noqa
            # Handle length mismatch due to daylight saving time or timezone issues
            expected_length = len(self)
            actual_length = len(values)

            if abs(expected_length - actual_length) == 1:
                print(f"Warning: Length mismatch for variable '{name}': expected {expected_length}, got {actual_length}")
                print("This is likely due to daylight saving time transition. Adjusting data length...")

                if actual_length < expected_length:
                    # Weather data is shorter - pad with the last value or interpolate
                    if len(values) > 0:
                        # Use the last value to pad
                        values = values + [values[-1]]
                    else:
                        # If no values, pad with 0
                        values = [0.0] * expected_length
                else:
                    # Weather data is longer - truncate to match
                    values = values[:expected_length]

                # Try again with adjusted values
                self._dataframe[name] = values
            else:
                raise ValueError('Variable "%s" has a length equal to %i instead of %i' % (
                    name, len(values), len(self)))

        self.variable_bounds[name] = minmaxval(values)
        self._dataframe = self._dataframe.astype({name: float}).copy()

    def _align_weather_data(self, weather_values: list[float], variable_name: str) -> list[float] | None:
        """
        Attempt to align weather data with measurement data timestamps.
        This handles cases where daylight saving time causes length mismatches.

        :param weather_values: The weather data values
        :param variable_name: Name of the weather variable
        :return: Aligned values or None if alignment fails
        """
        try:
            # Get the measurement timestamps
            measurement_times = self._dataframe['datetime'].tolist()
            weather_times = self.site_weather_data.datetimes

            if len(weather_values) != len(weather_times):
                print(f"Warning: Weather data length mismatch for {variable_name}")
                return None

            # Create a mapping from weather times to values
            weather_dict = dict(zip(weather_times, weather_values))

            # Align weather data with measurement times
            aligned_values = []
            for measurement_time in measurement_times:
                if measurement_time in weather_dict:
                    aligned_values.append(weather_dict[measurement_time])
                else:
                    # Find the closest weather time
                    closest_time = min(weather_times, key=lambda x: abs((x - measurement_time).total_seconds()))
                    if abs((closest_time - measurement_time).total_seconds()) <= 3600:  # Within 1 hour
                        aligned_values.append(weather_dict[closest_time])
                    else:
                        # Use interpolation or last known value
                        if len(aligned_values) > 0:
                            aligned_values.append(aligned_values[-1])
                        else:
                            aligned_values.append(0.0)

            return aligned_values

        except Exception as e:
            print(f"Failed to align weather data for '{variable_name}': {e}")
            return None

    @property
    def weather_data(self) -> SiteWeatherData:
        """Return the related SiteWeatherData, which contains all the data for weather

        :return: the set of weather data
        :rtype: SiteWeatherData
        """
        return self.site_weather_data

    @property
    def number_of_days(self) -> int:
        """Return the number of days stored in the IVS

        :return: the number of days
        :rtype: int
        """
        return self.day_counter

    def __call__(self, name: str, k: int = None) -> float | list[float]:
        """
        Return the data related a single hour or to all the hours in IVS (the length is therefore equal to the number of hours)

        :param name: name of the variable
        :type variable_name: str
        :param k: index of the hour in the data series (get the priority on day index if provided), defaults to None
        :type hour_index: int, optional
        :return: the variable value or values, depending on the request
        :rtype: dict[str]
        """
        if k is None:
            if name == "datetime":
                return self._dataframe[name].tolist()
            elif name in self._dataframe:
                return self._dataframe[name].values.tolist()
        else:
            if name == "datetime":
                return self.datetime_pd_series.iloc[[k]]
            elif name in self._dataframe:
                return self._dataframe.iloc[k][name]
        raise ValueError('Unknown data "%s"' % name)

    def __len__(self) -> int:
        """Return the number of time slots (hours) in the IVS

        :return: the number of time slots (hours) in the IVS
        :rtype: int
        """
        return len(self._dataframe)

    def __str__(self) -> str:
        """Make it possible to print a data container.

        :return: description of the data container
        :rtype: str
        """
        string: str = '__________\nData cover period from %s to %s with time period: %d seconds\n' % (
            self.specified_starting_stringdatetime, self.specified_ending_stringdatetime, self.sample_time_in_secs)
        string += '%i levels/values are considered to represent nonlinearities\n' % self.number_of_levels
        string += '\n- Available invariant variables:\n' + \
            '\n'.join(self.variable_names) + '\n'
        return string

    def save(self, file_name: str = 'results.csv', selected_variables: list[str] = None) -> None:
        """Save the IVS as a CSV file for reused

        :param file_name: the file name, defaults to 'results.csv'
        :type file_name: str, optional
        :param selected_variables: the variable so be saved if specified, or all the variables if None, defaults to None
        :type selected_variables: list[str], optional
        """
        if selected_variables is None:
            _selected_variables = self._dataframe.columns
        else:
            _selected_variables: list[str] = [
                'epochtime', 'stringtime', 'datetime']
            _selected_variables.extend(selected_variables)
        file_name = str(_RESULTS_FOLDER / file_name)
        self._dataframe[_selected_variables].to_csv(file_name, index=False)

        print('Following variables have been saved into file "%s": ' %
              file_name, end='')
        for selected_variable in _selected_variables:
            print(selected_variable, end=', ')
        print()


class ParameterizedVariableSet(VariableSet):
    """It handles calculated from parameters and independent data"""

    def __init__(self, data_provider: DataProvider) -> None:
        """Initialize the set with double dependency with the data provider thanks to a formula

        :param data_provider: the main data container that gathers all the data, including the parameterized ones
        :type data_provider: DataProvider
        """
        super().__init__('ParameterizedVariableSet')
        self.data_provider: DataProvider = data_provider
        self.formulas: dict[str, function] = dict()  # noqa
        self.variable_names = list()

    def excerpt(self, data_provider: DataProvider) -> ParameterizedVariableSet:
        """Return another parameterized variable set with the same calculated variables but with an excerpt of the original data provider.

        :param data_provider: the data provider that will be used in the excerpt
        :type data_provider: DataProvider
        :return: the parameterized variables but based  on an excerpt of the original data provider
        :rtype: DataProvider
        """

        child_parameterized_variable_set: DataProvider = ParameterizedVariableSet(
            data_provider)
        child_parameterized_variable_set.formulas = self.formulas
        child_parameterized_variable_set.variable_names = self.variable_names
        return child_parameterized_variable_set

    def __contains__(self, variable_name: str) -> bool:
        """Check wether the provided variable name belongs to the parameterized variable set.

        :param variable_name: the variable name
        :type variable_name: str
        :return: True if the name is known, False otherwise
        :rtype: bool
        """
        return variable_name in self.variable_names

    def __call__(self, name: str, k: int = None) -> float | list[float]:
        """Getter for a parameterized variable. It can return a float if the time slot is specified or the list of all the calculated values along time if k is None, default is None

        :param name: the parameterized variable
        :type name: str
        :param k: the time slot, defaults to None
        :type k: int, optional
        :return: a single or a list of values
        :rtype: float | list[float]
        """
        if name in self.variable_names:
            if k is not None:
                return self.formulas[name](k)
            else:
                return [self.formulas[name](k) for k in range(len(self.data_provider))]
        raise ValueError('Unknown data "%s"' % name)

    def series(self, name: str) -> list[float]:
        """Equivalent to self(name)

        :param name:  the parameterized variable
        :type name: str
        :return: a list of values
        :rtype: list[float]
        """
        return self(name)

    def __str__(self) -> str:
        return "- Available parameterized variables: \n" + "\n".join(self.variable_names) + "\n"

    def __iter__(self):
        return self.variable_names.__iter__()

    def __next__(self):
        return self.variable_names.__next__()

    def value_to_level(self, variable_name: str, variable_value: float) -> int:
        raise ValueError('Not available')

    def level_to_value(self, variable_name: str, level: int) -> float:
        raise ValueError('Not available')

    @property
    def number_of_parameterized_variables(self) -> int:
        return len(self.variable_names)


class VariableAccessor(ABC):
    """A data accessor is related to a variable and makes a link with its related variable set (that contains its values). The value can be overloaded (masked) by another value set at runtime"""

    def __init__(self, name: str, kind: str, variable_set: VariableSet, source: str = None) -> None:
        """Create a variable accessor based on a variable name, the kind of variable set it belongs and a source. If the source is None, the source is equal to the variable name itself.
        The source might be different from the variable name if a binding is defined: the source is the data source name (belonging to an invariant variable set) whereas the name stands for the model name.

        :param name: the model name of the variable
        :type name: str
        :param kind: the kind of related data set ("ParameterSet", "InvariantVariableSet" or "ParameterizedVariableSet")
        :type kind: str
        :param variable_set: the variable set the variable values belong to.
        :type variable_set: VariableSet
        :param source: the data source name, defaults to None
        :type source: str, optional
        """
        super().__init__()
        self.name: str = name
        self.kind: str = kind
        self.source: str = source if source is not None else name
        self.variable_set: VariableSet = variable_set
        self.overloaded_values: dict[int, float] = dict()

    def __call__(self, k: int | None = None, value: float | list[float] | None = None, mask: bool = False) -> None | float | list[float]:
        """Getter or setter depending on whether a value is given or not. As a getter, if some data have been overloaded, the overloaded values will be returned except if the mask flag is set to True.
        If used as a setter, a value or a set of values is provided if the time slot k is None.

        :param k: the time slot or None for all time slots, defaults to None
        :type k: int | None, optional
        :param value: value or set of values to overload the original values if None, defaults to None
        :type value: float | list[float], optional
        :param unmask: mask the overloaded values if True, return them otherwise if exists, default is False
        :return: a value or a list of values is used as a getter
        :rtype: float | list[float]
        """
        if value is None:  # a getter
            if type(k) is int:
                if not mask and self.overloaded and k in self.overloaded_values:
                    return self.overloaded_values[k]
                else:
                    if self.variable_set.kind == 'ParameterSet':
                        return self.variable_set(name=self.source)
                    else:
                        return self.variable_set(name=self.source, k=k)
            elif k is None:
                values = list(self.variable_set(self.source))
                if self.overloaded:
                    for k in self.overloaded_values:
                        values[k] = self.overloaded_values[k]
                return values
        elif value is not None:  # a setter
            if type(k) is int:
                self.overloaded_values[k] = value
            elif k is None:
                self.overloaded_values = [value for _ in range(
                    len(self.variable_set(self.name)))]
        return None

    @abstractmethod
    # , forced_data_values: dict[str, float] = dict()
    def signature(self, k: int | None) -> int | list[int]:
        """Return a unique integer (a discrete level) representing the current variable value if the time slot k is not None. If it is None, a series of integers corresponding to each time slot is returned.

        :param k: the time slot or None for all the available time slots
        :type k: int | None
        :return: a discrete level, or a set of discrete levels, of the variable
        :rtype: int | list[int]
        """
        raise NotImplementedError

    @property
    def overloaded(self) -> bool:
        """Return True if some values has been overloaded

        :return: True if some values has been overloaded, False otherwise.
        :rtype: bool
        """
        return len(self.overloaded_values) > 0

    def clear(self) -> None:
        """Clear all the overloaded values
        """
        self.overload.clear()


class ParameterAccessor(VariableAccessor):

    def __init__(self, parameter_set: ParameterSet, name: str) -> None:
        super().__init__(name, self.__class__.__name__, parameter_set)

    def __call__(self, k: int | None = 0, value: float | list[float] = None, mask: bool = False) -> float | list[float]:
        if k is None:
            k = 0
        return super().__call__(k, value, mask)

    def signature(self, k: int = 0) -> int:
        if k is None:
            k = 0
        return self.variable_set.value_to_level(self.name, self(k))


class IndependentVariableAccessor(VariableAccessor):

    def __init__(self, independent_variable_set: IndependentVariableSet, reference_name: str, source_name: str) -> None:
        super().__init__(reference_name, self.__class__.__name__,
                         independent_variable_set, source_name)

    # 0
    def __call__(self, k: int | None = None, value: float | list[float] = None, mask: bool = False) -> float | list[float]:
        return super().__call__(k, value, mask)

    def signature(self, k: int) -> int:
        if k is None:
            k = 0
        if type(k) is int:
            return self.variable_set.value_to_level(self.source, self(k))
        else:
            raise ValueError(
                f"IndependentVariableAccessor.signature k: {k} is not an integer")


class ParameterizedVariableAccessor(VariableAccessor):

    def __init__(self, parameterized_variable_set: ParameterizedVariableSet, name: str, required_data: list[VariableAccessor], nominal_value: float, resolution: float) -> None:
        super().__init__(name, self.__class__.__name__, parameterized_variable_set, None)
        self.required_data: list[VariableAccessor] = required_data
        self.nominal_value: float = nominal_value
        self.resolution: float = resolution
        self.default_signature: int = round(
            self.nominal_value // self.resolution)

    # 0
    def __call__(self, k: int | None = None, value: float | list[float] | None = None, mask: bool = False) -> float | list[float]:
        return super().__call__(k, value, mask)

    def signature(self, k: int | None = None) -> int:
        if k is None:
            return self.default_signature
        else:
            return round(self.variable_set.formulas[self.name](k) // self.resolution)


class Bindings:
    """A binding is a link between a data model and recorded data, no matter the way they are named.
    The bindings class gathers all the bindings of a same problem.
    """

    @staticmethod
    def normalize_zone_variable_name(name: str) -> str:
        """Normalize zone-related variable names to ensure colon after prefix.

        Converts patterns like TZoutdoor to TZ:outdoor, PZroom to PZ:room, etc.

        :param name: the variable name to normalize
        :type name: str
        :return: normalized variable name
        :rtype: str
        """
        # List of known zone variable prefixes
        prefixes = ['TZ', 'PZ', 'CZ', 'CCO2', 'PCO2', 'GAIN', 'SETPOINT', 'MODE', 'PHVAC']

        for prefix in prefixes:
            # Check if name starts with prefix followed by a letter (not underscore or colon)
            if name.startswith(prefix) and len(name) > len(prefix):
                next_char = name[len(prefix)]
                # Check if there's not already a colon or underscore after the prefix
                if next_char not in (':', '_'):
                    # Insert colon after prefix
                    return prefix + ':' + name[len(prefix):]
                # If there's an underscore, replace it with a colon
                elif next_char == '_':
                    return prefix + ':' + name[len(prefix)+1:]

        return name

    def __init__(self, **model_to_data: dict[str, str]) -> None:
        """Initializer
        """
        self.model_to_data: dict[str, str] = dict()
        self.data_to_model: dict[str, str] = dict()
        for model_name in model_to_data:
            self.link_model_data(model_name, model_to_data[model_name])

    def __call__(self, model_name: str, data_name: str) -> None:
        """Shortcut method for link_model_data(self, model_name: str, data_name: str)

        :param model_name: _description_
        :type model_name: str
        :param data_name: _description_
        :type data_name: str
        """
        self.link_model_data(model_name, data_name)

    def link_model_data(self, model_name: str, data_name: str) -> None:
        """create a link between a model variable and recorded one.

        :param model_name: the name of the model variable
        :type model_name: str
        :param data_name: the name of the data variable
        :type data_name: str
        """
        # Normalize zone variable names first
        model_name = self.normalize_zone_variable_name(model_name)
        # Then apply standard reference normalization
        model_name = VariableAccessorRegistry.reference(model_name)
        self.model_to_data[model_name] = data_name
        self.data_to_model[data_name] = model_name

    def data_name(self, model_name: str) -> str:
        """return the variable name corresponding to the given model name

        :param model_name: the model name
        :type model_name: str
        :return: the variable name
        :rtype: str
        """
        # Normalize zone variable names first
        model_name = self.normalize_zone_variable_name(model_name)
        # Then apply standard reference normalization
        model_name = VariableAccessorRegistry.reference(model_name)
        if model_name in self.model_to_data:
            return self.model_to_data[model_name]
        return model_name

    def model_name(self, data_name: str) -> str:
        """return the given model name corresponding to the variable name

        :param model_name: the data name
        :type model_name: str
        :return: the model name
        :rtype: str
        """
        if data_name in self.data_to_model:
            return self.data_to_model[data_name]
        # If no binding exists, normalize the data_name in case it's used as a model name
        return self.normalize_zone_variable_name(data_name)

    def data_has_synonym(self, data_name: str) -> bool:
        """check wether a data name is appearing in a binding

        :param data_name: the data variable name
        :type data_name: str
        :return: True if the data variable name is appearing in a binding
        :rtype: bool
        """

        return data_name in self.data_to_model

    def create_internal_aliases(self, data_provider) -> None:
        """Create parameterized variable aliases for bindings that point to internal variables.

        This allows bindings to create aliases between internal variables, not just map to external data.
        For example: bindings.link_model_data('PZ:office', 'GAIN:office') will create PZ:office as an alias.

        :param data_provider: The data provider to add aliases to
        :type data_provider: DataProvider
        """
        for model_name, data_name in self.model_to_data.items():
            # Check if data_name refers to an existing internal variable
            if data_name in data_provider.variable_accessor_registry:
                # Create an alias by adding a parameterized variable
                data_provider.add_parameterized(
                    model_name,
                    lambda k, var_name=data_name: data_provider(var_name, k),
                    default=0,
                    resolution=1
                )

    def model_has_synonym(self, model_name: str) -> bool:
        """check wether a model variable name is appearing in a binding

        :param model_name: the model name
        :type model_name: str
        :return: True if the model variable name is appearing in a binding
        :rtype: bool
        """
        return model_name in self.model_to_data

    def __str__(self) -> str:
        string: str = ''
        for model in self.model_to_data:
            string += "%s -> %s\n" % (model, self.model_to_data[model])
        return string


class DataProvider:

    def __init__(self, location: str, latitude_north_deg: float, longitude_east_deg: float, csv_measurement_filename: str | None = None, starting_stringdate: str | None = None, ending_stringdate: str | None = None, bindings: Bindings = Bindings(), parent_dp: DataProvider = None, albedo: float = .1, pollution: float = 0.1,  number_of_levels: int = 4, deleted_variables: list[str] = [], initial_year: int = 1980) -> None:
        """The data provider is the front end class that must be used for interacting with data. It covers all types of variables: parameters, independent variables and parameterized variables.

        :param starting_stringdate: the initial string date as "DD/MM/YYYY" for selecting the period of loaded data.
        :type starting_stringdate: str
        :param ending_stringdate: the ending string date as "DD/MM/YYYY" for selecting the period of loaded data.
        :type ending_stringdate: str
        :param bindings: the bindings used to link model variable to independent or parameterized variables, defaults to None
        :type bindings: Bindings, optional
        :param parent_dp: internally used to generated a subset of the IVS behind, defaults to None
        :type parent_dp: DataProvider, optional
        :param json_openweather_filename: a json file name where to load weather data (openweather or openmeteo formats) if provided, defaults to None
        :type json_openweather_filename: str, optional
        :param albedo: albedo value for the location, defaults to .1
        :type albedo: float, optional
        :param pollution: pollution coefficient for the location, defaults to 0.1
        :type pollution: float, optional
        :param location: name of the location if provided, defaults to None
        :type location: str, optional
        :param number_of_levels: number of discrete levels for locally linearizing the problem and thus accelerating the resolution, defaults to 4
        :type number_of_levels: int, optional
        :param deleted_variables: the variables to be deleted after initial data loading, defaults to ()
        :type deleted_variables: tuple[str], optional
        :param csv_measurement_filename: CSV file name containing measurements if available, defaults to None
        :type csv_measurement_filename: str, optional
        """
        self.bindings: Bindings = bindings

        self.recording = False
        self.collected_data: list[VariableAccessor] = list()
        self.data_names_in_fingerprint: list[str] = list()

        if parent_dp is not None:  # generate child data provider with other starting and ending date
            self.data_nominal_values_in_fingerprint = parent_dp.data_nominal_values_in_fingerprint
            self.required_data_in_fingerprint = parent_dp.required_data_in_fingerprint
            self.location = parent_dp.location
            self.sample_time_in_secs = parent_dp.sample_time_in_secs
            self.parameter_set = parent_dp.parameter_set
            self.independent_variable_set = IndependentVariableSet(parent_dp.location, parent_dp.latitude_north_deg, parent_dp.longitude_east_deg, parent_dp.independent_variable_set,
                                                                   starting_stringdate=starting_stringdate, ending_stringdate=ending_stringdate, parent_ivs=parent_dp.independent_variable_set, albedo=parent_dp.albedo, pollution=parent_dp.pollution)
            self.parameterized_variable_set = ParameterizedVariableSet(self)
            self.data_names_in_fingerprint = parent_dp.data_names_in_fingerprint
            self.variable_accessor_registry: VariableAccessorRegistry = VariableAccessorRegistry(
                self.bindings)
            for parameter_name in self.parameter_set:
                self.variable_accessor_registry(
                    parameter_name, ParameterAccessor(self.parameter_set, parameter_name))
            for independent_variable_name in self.independent_variable_set.variable_names:
                self.variable_accessor_registry(independent_variable_name, IndependentVariableAccessor(
                    self.independent_variable_set, independent_variable_name, independent_variable_name))
            return

        self.location: str = location
        self.albedo: float = albedo
        self.pollution: float = pollution
        self.sample_time_in_secs = 3600
        self.parameter_set: ParameterSet = ParameterSet()
        self.latitude_north_deg: float = latitude_north_deg
        self.longitude_east_deg: float = longitude_east_deg
        self.number_of_levels: int = number_of_levels

        self.independent_variable_set: IndependentVariableSet = IndependentVariableSet(location=location, latitude_north_deg=latitude_north_deg, longitude_east_deg=longitude_east_deg, csv_measurement_filename=csv_measurement_filename, starting_stringdate=starting_stringdate, ending_stringdate=ending_stringdate, parent_ivs=None, albedo=albedo, pollution=pollution, deleted_variables=deleted_variables, number_of_levels=number_of_levels, initial_year=initial_year)
        self.parameterized_variable_set = ParameterizedVariableSet(self)
        self.variable_accessor_registry: VariableAccessorRegistry = VariableAccessorRegistry(
            self.bindings)
        self.site_weather_data: SiteWeatherData = self.independent_variable_set.site_weather_data

        for parameter_name in self.parameter_set:
            parameter_data = ParameterAccessor(
                self.parameter_set, parameter_name)
            self.variable_accessor_registry(parameter_name, parameter_data)

        for independent_variable_name in self.independent_variable_set.variable_names:
            self.variable_accessor_registry(independent_variable_name, IndependentVariableAccessor(
                self.independent_variable_set, independent_variable_name, independent_variable_name))

        for parameterized_variable_name in self.parameterized_variable_set.variable_names:
            self.variable_accessor_registry(parameterized_variable_name, ParameterizedVariableAccessor(
                self.parameterized_variable_set, parameterized_variable_name))
        self.data_nominal_values_in_fingerprint: dict[VariableAccessor, float] = dict(
        )
        self.required_data_in_fingerprint: set[str] = set()
        self.sample_time_in_secs: int = self.independent_variable_set.sample_time_in_secs

    def __contains__(self, data_name: str) -> bool:
        return data_name in self.variable_accessor_registry

    def add_binding(self, model_name: str, data_name: str) -> None:
        """Add a binding between a model name and a data name
        """
        self.bindings.link_model_data(model_name, data_name)

    def excerpt(self, starting_stringdate: str = None, ending_stringdate: str = None) -> "DataProvider":
        """Generate another data provider, based on a shorter period of time, but on the same parameter set

        :param starting_stringdate: the initial date as "DD/MM/YYYY"
        :type starting_stringdate: str
        :param ending_stringdate: the ending date as "DD/MM/YYYY"
        :type ending_stringdate: str
        :return: the inherited data
        :rtype: DataProvider
        """
        if starting_stringdate is None:
            starting_stringdate = self.starting_stringdate
        if ending_stringdate is None:
            ending_stringdate = self.ending_stringdate
        excerpt_data_provider = DataProvider(self.location, self.latitude_north_deg, self.longitude_east_deg,
                                             starting_stringdate=starting_stringdate, ending_stringdate=ending_stringdate, bindings=self.bindings, parent_dp=self)
        for reference_name in self.parameterized_variable_set.formulas:
            excerpt_data_provider.parameterized_variable_set.variable_names.append(
                reference_name)
            excerpt_data_provider.parameterized_variable_set.formulas[
                reference_name] = self.parameterized_variable_set.formulas[reference_name]
            required_data_names: list[str] = [
                data.name for data in self.variable_accessor_registry(reference_name).required_data]
            parameterized_data = ParameterizedVariableAccessor(excerpt_data_provider.parameterized_variable_set, reference_name, [excerpt_data_provider.variable_accessor_registry(
                required_data_name) for required_data_name in required_data_names], nominal_value=self.variable_accessor_registry(reference_name).nominal_value, resolution=self.variable_accessor_registry(reference_name).resolution)
            excerpt_data_provider.variable_accessor_registry(
                reference_name, parameterized_data)

        return excerpt_data_provider

    def add_parameterized(self, parameterized_data_name: str, formula: callable, default: float, resolution: float) -> None:  # noqa
        """add a parameterized variable, which is calculated from a formula involving parameters and invariant variables

        :param parameterized_data_name: tha name of the parameterized variable
        :type parameterized_data_name: str
        :param formula: the formula involving parameters and invariant variables as data_provider(variable_name, k) for variables or data_provider(parameter_name) for parameter
        :type formula: callable
        :param default: a default or nominal value used when the time slot k is not None
        :type default: float
        :param resolution: a step in the variable value used to discretize the variable
        :type resolution: float
        """
        reference_name: str = VariableAccessorRegistry.reference(
            parameterized_data_name)
        self.parameterized_variable_set.variable_names.append(reference_name)
        self.parameterized_variable_set.formulas[reference_name] = formula
        self._record()
        formula(0)
        required_data_names: list[str] = self._collect_data()
        # type: ignore
        self.parameterized_variable_set.required_data = list()
        for required_data_name in required_data_names:
            self.parameterized_variable_set.required_data.append(
                self.variable_accessor_registry(required_data_name))
        parameterized_data = ParameterizedVariableAccessor(
            self.parameterized_variable_set, reference_name, self.parameterized_variable_set.required_data, nominal_value=default, resolution=resolution)
        self.variable_accessor_registry(reference_name, parameterized_data)

    def add_data_names_in_fingerprint(self, *data_names: list[str]):
        """Add data names for their current value to be taken in the fingerprint, a long integer representing selected variable values at the current time slot, in order to faster simulations by avoiding the recomputation of some linearized models.
        """
        for data_name in data_names:
            self.data_names_in_fingerprint.append(VariableAccessorRegistry.reference(data_name))

    @property
    def weather_data(self) -> SiteWeatherData:
        """Return a site weather data object that gathers all the data dealing with weather

        :return: the site weather data object
        :rtype: SiteWeatherData
        """
        return self.independent_variable_set.weather_data

    def add_param(self, parameter_name: str, value: float, bounds_resolution: tuple[float, float, float] = None) -> None:
        """Create a parameter with a name, an initial value, and possibly a triplet of values with a lower bound of the possible value domain, an upper bound and a resolution leading to discrete levels used to search values best fitting recorded data. If the triplet is not provided, the parameter will be considered as not adjustable.

        :param parameter_name: the parameter name
        :type parameter_name: str
        :param value: the parameter initial value
        :type value: float, optional
        :param bounds_resolution:  a triplet of values with a lower bound of the possible value domain, an upper bound and a resolution
        :type bounds_resolution: tuple[float, float, float], optional
        """
        self.parameter_set(parameter_name, value, bounds_resolution)
        self.variable_accessor_registry(
            parameter_name, ParameterAccessor(self.parameter_set, parameter_name))
        if parameter_name in self.parameter_set.adjustable_parameter_names and parameter_name not in self.data_names_in_fingerprint:
            self.data_names_in_fingerprint.append(parameter_name)

    def clear(self) -> None:
        """Clear all the overloaded values
        """
        for name in self.variable_accessor_registry:
            self.variable_accessor_registry(name).clear()

    def _record(self) -> None:
        """Internally used to collect parameters and independent variables used in the formula of a parameterized variable
        """
        self.collected_data.clear()
        self.recording = True

    def __call__(self, data_name: str, k: int | None = 0, value: float = None) -> float | list[float]:
        """Getter or setter for a named data depending on whether value is given or not, except if "datetime" is requested: it just can be a getter.
        Get or set operations are done accordingly to the specified time slot k or None, which means all the time slots for independent and parameterized variables. k is not considered for parameters.

        :param data_name: the variable name
        :type data_name: str
        :param k: the time slot, defaults to 0
        :type k: int | None, optional
        :param value: the value to be set if specified, defaults to None
        :type value: float, optional
        :return: the requested value if used as a setter
        :rtype: float | list[float]
        """
        if data_name == 'datetime':
            datetimes = self.independent_variable_set._dataframe.datetime.tolist()
            if k is None:
                return datetimes
            else:
                return datetimes[k]
        # if data_name[0:5] == "GAIN:":
        #     pass
        if type(k) is int:
            if value is None:
                if data_name in self.variable_accessor_registry:
                    variable_accessor: VariableAccessor = self.variable_accessor_registry(data_name)
                    if self.recording and variable_accessor not in self.collected_data:
                        self.collected_data.append(variable_accessor)
                    try:
                        return variable_accessor(k)
                    except Exception:
                        raise ValueError('Missing data "%s"' % data_name)
            elif type(value) in (float, int, numpy.float64):
                if data_name not in self.variable_accessor_registry:
                    self.add_var(
                        data_name, [None for _ in self.ks])
                    variable_accessor = IndependentVariableAccessor(
                        self.independent_variable_set, data_name, data_name)
                    self.variable_accessor_registry(
                        data_name, variable_accessor)
                else:
                    variable_accessor = self.variable_accessor_registry(
                        data_name)
                variable_accessor(k, value)
                return
        if k is None:
            if value is None:
                data_accessor: None | type[VariableAccessor] = self.variable_accessor_registry(
                    data_name)
                return data_accessor()
            if type(value) in (list, tuple):
                self.add_var(data_name, value)
                return
        raise ValueError('Operation on variable %s is not possible' % data_name)

    def series(self, data_name: str) -> list[float]:
        """It is a shortcut for self.__call__(data_name, None) that returns the values corresponding to all time slots.

        :param data_name: the variable name
        :type data_name: str
        :return: the list of values corresponding to all time slots
        :rtype: list[float]
        """
        values = self.__call__(data_name, k=None, value=None)
        if type(values) is int:
            return [values for _ in range(len(self))]
        else:
            return values

    @property
    def ks(self) -> list[int]:
        """Return all the time slots

        :return: the time slots
        :rtype: list[int]
        """
        return [_ for _ in range(len(self))]

    @property
    def datetimes(self) -> list[datetime]:
        """Return the list of datetimes for all time slots

        :return: the list of datetimes
        :rtype: list[float]
        """
        return self.series('datetime')

    def _collect_data(self) -> list[str]:
        """Internally used to collect data used by parameterized variables

        :return: the collected variable names
        :rtype: list[str]
        """
        self.recording = False
        collected_data: list[str] = list()
        for cdata in self.collected_data:
            collected_data.append(cdata.name)
        return collected_data

    def add_var(self, name: str, values: list[float], force: bool = False):
        """Add a series of values to the independent variable set, provided the number of values is consistent with the variable set size.

        :param name: the name of the new independent variable
        :type name: str
        :param values: the list of values to add
        :type values: list[float]
        :param force: if True, replace existing variable with same name if it has the same size, defaults to False
        :type force: bool, optional
        """

        if name not in self.variable_accessor_registry:
            self.independent_variable_set.add_var(name, values)
            self.variable_accessor_registry(name, IndependentVariableAccessor(
                self.independent_variable_set, name, name))
        else:
            if force:
                # Check if variable exists in dataframe and sizes match
                if name in self.independent_variable_set._dataframe.columns:
                    existing_size = len(self.independent_variable_set._dataframe[name])
                    new_size = len(values)
                    if existing_size == new_size:
                        # Replace the existing variable
                        self.independent_variable_set.add_var(name, values, force=True)
                    else:
                        raise ValueError("Cannot force replace variable '%s': size mismatch (existing: %d, new: %d)" % (name, existing_size, new_size))
                else:
                    # Variable in registry but not in dataframe - just add it
                    self.independent_variable_set.add_var(name, values, force=True)
            else:
                raise ValueError("Existing data name '%s'" % name)

    @property
    def starting_stringdate(self) -> str:
        """the starting date as string like "DD/MM/YYYY"

        :return: the starting date
        :rtype: str
        """
        return self.independent_variable_set.starting_stringdate

    @property
    def ending_stringdate(self) -> str:
        """the ending date as string like "DD/MM/YYYY"

        :return: the ending date
        :rtype: str
        """
        return self.independent_variable_set.ending_stringdate

    @property
    def starting_stringdatetime(self) -> str:
        """the starting date as string like "DD/MM/YYYY hh:mm:ss"

        :return: the starting date
        :rtype: str
        """
        return self.independent_variable_set.specified_starting_stringdatetime

    @property
    def ending_stringdatetime(self) -> str:
        """the ending date as string like "DD/MM/YYYY hh:mm:ss"

        :return: the ending date
        :rtype: str
        """
        return self.independent_variable_set.specified_ending_stringdatetime

    @property
    def variable_names(self) -> list[str]:
        """return the list of the independent and parameterized variables

        :return: the list of the independent and parameterized variables
        :rtype: list[str]
        """
        _variable_names: list[str] = self.independent_variable_set.variable_names
        _variable_names.extend(self.parameterized_variable_set.variable_names)
        return _variable_names

    def variables_data(self, with_weather: bool = False) -> dict[str, list[float]]:
        """Return a dictionary with variable names as keys and their values as lists of floats.

        :return: the dictionary with variable names as keys and their values as lists of floats
        :rtype: dict[str, list[float]]
        """
        _data: dict[str, list[float]] = {variable_name: self.series(
            variable_name) for variable_name in self.variable_names}
        if with_weather:
            _data.update(self.weather_data.variables_data())
        return _data

    def save(self, file_name: str = 'results.csv', selected_variables: list[str] = None) -> None:
        """Save data a CSV file

        :param file_name: the file name, defaults to 'results.csv'
        :type file_name: str, optional
        :param selected_variables: the variable so be saved if specified, or all the variables if None, defaults to None
        :type selected_variables: list[str], optional
        """

        if selected_variables is None:
            _selected_variables = self.independent_variable_set._dataframe.columns
        else:
            _selected_variables: list[str] = [
                'epochtime', 'stringtime', 'datetime']
            _selected_variables.extend(selected_variables)
        file_name = str(_RESULTS_FOLDER / file_name)
        self.independent_variable_set._dataframe[_selected_variables].to_csv(
            file_name, index=False)
        print('Following variables have been saved into file "%s": ' %
              file_name, end='')
        for selected_variable in _selected_variables:
            print(selected_variable, end=', ')
        print()

    @property
    def parameter_names(self) -> list[str]:
        """return the list of all the parameter names

        :return: the list of all the parameter names
        :rtype: list[str]
        """
        return self.parameter_set._parameter_names

    def __len__(self) -> int:
        """return the number of time slots characterizing the data provider

        :return: the number of time slots characterizing the data provider
        :rtype: int
        """
        return self.independent_variable_set.__len__()

    def _fingerprint(self, k: int) -> int:
        """Internal method used to generate a long integer representing in unique way all the required variables' for parameterized variables and parameters'values at time slot k.
        The long integer results from the concatenation of integers related to individual signatures.

        :param k: the time slot or None
        :type k: int
        :return: a long integer representing in unique way all the registered variables' and parameters'values at time slot k
        :rtype: int
        """
        signatures: list[int] = list()
        for data_name in self.data_names_in_fingerprint:
            signatures.append(self.variable_accessor_registry(data_name).signature(k))
        if len(signatures) > 0:
            return int(''.join([str(int(_)) for _ in signatures]))

    def fingerprint(self, k: list[int] | int | None = None) -> list[int]:
        """fingerprint based on the adjustable parameter values and the required variables for parameterized variables

        :param k: the time sample or all the time samples, defaults to None
        :type k: int, optional
        :return: list of hash codes (if k is None), or a single hash code (if k is specified) representing the adjustable parameter values and the required variables for parameterized variables
        :rtype: int | list[int]
        """

        if type(k) is list:
            return [self._fingerprint(_) for _ in k]
        else:
            return self._fingerprint(k)

    def __str__(self):
        string: str = '\n# Data provider:\n'
        if self.independent_variable_set is not None:
            string += '\n' + self.independent_variable_set.__str__() + '\n'
        if self.parameterized_variable_set is not None:
            string += '\n' + self.parameterized_variable_set.__str__() + '\n'
        if self.parameter_set is not None:
            string += '\n' + self.parameter_set.__str__() + '\n'
        if self.bindings is not None:
            string += '\nwith the following data to model bindings:\n'
            string += self.bindings.__str__()
        return string

    def plot(self, *variable_names, plot_type='timeplot', threshold: float = .7, averager: str = '- hour') -> None:
        if len(variable_names) > 0:
            variable_values: dict[str, list[float]] = dict()
            variable_names = list(set(variable_names))
            for v in variable_names:
                if v in self.independent_variable_set.variable_names:
                    variable_values[v] = self.series(
                        v)  # independent_variable_set
                elif v in self.parameterized_variable_set.variable_names:
                    variable_values[v] = self.series(
                        v)  # parameterized_variable_set
                else:
                    # Try to get variable via series() as fallback (for variables accessible but not in variable_names)
                    try:
                        variable_values[v] = self.series(v)
                    except (ValueError, KeyError):
                        # Variable not found, skip it
                        pass
            if len(variable_values) > 0:
                TimeSeriesPlotter(variable_values=variable_values, datetimes=self.datetimes,
                                  all=True, plot_type=plot_type, averager=averager, threshold=threshold)
        else:
            variable_values: dict[str, list[float]] = {v: self.series(
                v) for v in self.independent_variable_set.variable_names}  # independent_variable_set
            for v in self.parameterized_variable_set.variable_names:
                variable_values[v] = self.series(
                    v)  # parameterized_variable_set
            TimeSeriesPlotter(variable_values=variable_values,
                              datetimes=self.datetimes)
