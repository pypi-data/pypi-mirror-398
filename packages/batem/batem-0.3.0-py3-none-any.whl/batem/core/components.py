"""Building components and thermal modeling module for multi-zone building design and simulation.

.. module:: batem.core.components

This module provides comprehensive tools for modeling the thermal behavior and CO2 concentration
evolution in multi-zone buildings. It implements a component-based approach for building design,
allowing easy construction of complex building models with thermal zones, walls, airflows, and
material compositions.

Classes
-------

.. autosummary::
   :toctree: generated/

   Zone
   Airflow
   WallSide
   LayeredWallSide
   BlockWallSide
   Composition
   Wall
   SideFactory

Classes Description
-------------------

**Zone**
    Thermal zones representing rooms or spaces with temperature and CO2 concentration modeling.

**Airflow**
    Bi-directional air flow connections between zones for ventilation and infiltration.

**WallSide**
    Abstract base class for wall components with thermal resistance and capacitance.

**LayeredWallSide**
    Wall side implementation with multiple material layers.

**BlockWallSide**
    Simplified wall side implementation for homogeneous materials.

**Composition**
    Material composition definitions with thermal properties and layer configurations.

**Wall**
    Complete wall assemblies combining compositions, thermal bridges, and infiltration.

**SideFactory**
    Factory class for creating wall sides with predefined layer configurations.

Key Features
------------

* Multi-zone building thermal modeling with automatic zone connectivity
* CO2 concentration tracking and air quality modeling
* Layered wall construction with thermal resistance and capacitance calculations
* Thermal bridge modeling for accurate heat transfer calculations
* Air infiltration and ventilation flow modeling between zones
* Material property database integration for realistic building components
* Support for various wall orientations and surface types
* Automatic naming conventions for thermal variables and components

The module is designed for building energy analysis, thermal comfort studies, and indoor
environmental quality assessment in both residential and commercial buildings.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""
from __future__ import annotations
import abc
from typing import Any
from .library import ZONE_TYPES, SIDE_TYPES, SLOPES, properties
import warnings
from numpy import interp
import scipy.constants


class Airflow:

    def __init__(self, zone1: Zone, zone2: Zone, nominal_value: float) -> None:  # , name: str=None
        """
        Create a bi-directional air flow between 2 zones. It is named as Q(name of zone1, name of zone2)

        :param zone1: first zone
        :type zone1: Zone
        :param zone2: second zone
        :type zone2: Zone
        :param nominal_value: the nominal value in m3/s used if not overloaded
        :type nominal_value: float
        """
        if zone1.name == zone2.name:
            raise ValueError("Can't connect zone %s with itself" % zone1.name)
        if zone2.name < zone1.name:
            zone1, zone2 = zone2, zone1
        self.connected_zones: list[Zone] = [zone1, zone2]
        self.name: str = 'Q:%s-%s' % (zone1.name, zone2.name)
        self.nominal_value: float = nominal_value
        zone1.connected_airflows.append(self)
        zone2.connected_airflows.append(self)
        zone1.connected_zones.append(zone2)
        zone2.connected_zones.append(zone1)

    def __eq__(self, other_airflow) -> bool:
        return (other_airflow.zone1 in self.connected_zones) and (other_airflow.zone2 in self.connected_zones)

    def __repr__(self) -> str:
        return f"Airflow(zone1={self.connected_zones[0].name}, zone2={self.connected_zones[1].name}, nominal_value={self.nominal_value})"

    def __str__(self) -> str:
        return 'airflow named "%s" connecting zone "%s" and zone "%s"' % (self.name, self.connected_zones[0].name, self.connected_zones[1].name)


class Side:

    def __init__(self, *layers1_2: tuple[str, float]) -> None:
        self.layers: tuple[tuple[str, float]] = layers1_2
        self.zone1_name: str = None
        self.zone2_name: str = None
        self.side_type: SIDE_TYPES = None
        self.surface: float = None

    def __call__(self, zone_name1: str, zone_name2: str, side_type: SIDE_TYPES, surface: float) -> dict[str, "Any"]:
        self.zone1_name = zone_name1
        self.zone2_name = zone_name2
        self.side_type = side_type
        self.surface = surface
        return self


class Zone:

    def __init__(self, name: str, kind: ZONE_TYPES = ZONE_TYPES.GIVEN):
        """
        Create a zone

        :param name: name of the zone (it will be trimmed and space will be replaced by '_'
        :type name: str
        :param kind: kind of zone, defaults to Kind.GIVEN, corresponding to a bounding zone where temperature and CO2 concentration are known. Outdoor is a special GIVEN zone, whereas INDOOR kind represents a room that must be simulated. The kind should not be provided: it is deduced by the system from the description of the building
        :type kind: Kind, optional
        """
        self.name: str = name.strip().replace(" ", "_")
        self.air_temperature_name: str = 'TZ:' + self.name
        self.heat_power_name: str = 'PZ:' + self.name
        self.air_capacitance_name: str = 'CZ:' + self.name
        self.CO2_concentration_name: str = 'CCO2:' + self.name
        self.CO2_production_name: str = 'PCO2:' + self.name
        self.connected_zones: Zone = list()
        self.connected_airflows: list[Airflow] = list()
        self.volume = None
        self.zone_type: ZONE_TYPES = kind

    def _airflow(self, zone: Zone) -> Airflow:
        """Utility method giving the airflow joining the current zone to the specified one. None is returned if there's no airflow between the 2 zones

        :param zone: the zone that be connected to the current one
        :type zone: Zone
        :return: the connecting airflow or if it doesn't exist
        :rtype: Airflow
        """
        if zone not in self.connected_zones:
            return None
        i = self.connected_zones.index(zone)
        return self.connected_airflows[i]

    def set_volume(self, volume: float) -> None:
        """Set the volume of the zone and define it as a zone to be simulated

        :param volume: volume of the zone
        :type volume: float
        """
        self.volume: float = volume
        self.zone_type = ZONE_TYPES.SIMULATED

    @property
    def simulated(self, ) -> bool:
        """
        True is the current zone total incoming (or outgoing) air flow has to be simulated: it gets this status by setting a volume to the current zone.

        :return: True if it has to be simulated, False elsewhere;
        :rtype: bool
        """
        return self.volume is not None

    def __str__(self) -> str:
        string: str = '* ' if self.simulated else '* '
        string += '%s "%s" with temperature "%s", CO2 concentration "%s"' % (self.zone_type.name, self.name, self.air_temperature_name, self.CO2_concentration_name)
        if self.simulated:
            string += ', power gain "%s" and CO2 production "%s"' % (self.heat_power_name, self.CO2_production_name)
        string += ' with connected air flows:\n- ' + '\n- '.join([airflow.name for airflow in self.connected_airflows])
        return string + '\n'

    def __lt__(self, other_zone: Zone):
        return self.name < other_zone.name


class WallSide(abc.ABC):

    def __init__(self, zone1: Zone, zone2: Zone, side_type: SIDE_TYPES):
        """Initialize an abstract wall side i.e. a part of a wall. It can be a layered side or a block side.

        :param zone1: the 1st zone
        :type zone1: Zone
        :param zone2: the second zone
        :type zone2: Zone
        :param side_type: type of side (see SideType)
        :type side_type: SideType
        """
        self.zone1, self.zone2 = zone1, zone2
        self.side_type: SIDE_TYPES = side_type

    @property
    @abc.abstractmethod
    def Rs1_2(self) -> list[float]:
        """return a list of resistances corresponding to each layer, in the direction 1 to 2

        :raises NotImplementedError: abstract method
        :return: list of thermal resistances' values
        :rtype: list[float]
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def Cs1_2(self) -> list[float]:
        """return a list of capacitances corresponding to each layer, in the direction 1 to 2

        :raises NotImplementedError: abstract method
        :return: list of thermal capacitances' values
        :rtype: list[float]
        """
        raise NotImplementedError

    @property
    def global_USs1_2(self) -> float:
        return 1 / sum([R if not None else 0 for R in self.Rs1_2])

    @property
    def global_Cs1_2(self) -> float | int:
        return sum([C if C is not None else 0 for C in self.Cs1_2])

    @property
    def zones(self) -> frozenset[str, str]:
        return frozenset((self.zone1.name, self.zone2.name))


class LayeredWallSide(WallSide):
    """
    A layered wall side is a part of wall composed by layers, where both extreme layers cannot be air layers. Additionally, 2 air layers cannot be stacked consecutively.
    """

    def __init__(self, zone1: Zone, zone2: Zone, side_type: SIDE_TYPES, surface: float):
        """
        Initialize a layered interface

        :param zone1: zone next to side 1
        :type zone1: Zone
        :param zone2: zone next to side 2
        :type zone2: Zone
        :param interface_type: type interface corresponding to layered interface
        :type interface_type: Interface
        :param surface: surface of the interface
        :type surface: float
        """
        super().__init__(zone1, zone2, side_type)
        self.surface: float = surface

        if self.side_type.value > 60:
            self.slope: SLOPES = SLOPES.VERTICAL
        else:
            self.slope: SLOPES = SLOPES.HORIZONTAL_UP
        self.layers1_2: list[dict[str, float]] = list()

    def layer(self, material: str, thickness: float):
        """
        add a layer to the wall side starting from side 1

        :param material: short name of the thermal
        :type material: str
        :param thickness: _description_
        :type thickness: float
        """
        if material in properties:
            self.layers1_2.append({'material': material, 'thickness': thickness})
        else:
            raise ValueError('"%s" not loaded in library' % material)

    @property
    def n_layers(self) -> int:
        return len(self.layers1_2)

    @property
    def name(self) -> str:
        return '%s-%s' % (self.zone1.name, self.zone2.name)

    @property
    def total_US(self) -> float:
        return 1 / sum([R if not None else 0 for R in self.Rs1_2])

    @property
    def total_capacitance(self) -> float:
        return sum([C if C is not None else 0 for C in self.Cs1_2])

    @property
    def Rs1_2(self) -> list[float]:
        """
        Return the list of resistances, one for each layer of an interface, plus 2 surface resistances, one at each extremity

        :return: list of resistances, the values depends on thicknesses and on surfaces
        :rtype: list[float]
        """
        resistances = list()
        if self.side_type.value == SIDE_TYPES.BRIDGE:
            raise ValueError('A bridge cannot appear in an wall side')
        if self.layers1_2[0]['material'] == 'air' or self.layers1_2[-1]['material'] == 'air':
            raise ValueError('An air layer cannot appear in an external layer.')
        for i in range(1, len(self.layers1_2)-1):
            if self.layers1_2[i]['material'] == 'air' and self.layers1_2[i+1]['material'] == 'air':
                raise ValueError('Consecutive air layer are prohibited: gather air layers.')
        if self.zone1.zone_type != ZONE_TYPES.OUTDOOR:
            resistances.append(properties.indoor_surface_resistance(self.layers1_2[0]['material'], self.slope) / self.surface)
        else:
            resistances.append(properties.outdoor_surface_resistance(self.layers1_2[0]['material'], self.slope) / self.surface)
        for i in range(len(self.layers1_2)):
            if self.layers1_2[i]['material'] != 'air':
                resistances.append(properties.conduction_resistance(self.layers1_2[i]['material'], self.layers1_2[i]['thickness']) / self.surface)
            else:
                resistances.append(properties.cavity_resistance(self.layers1_2[i-1]['material'], self.layers1_2[i+1]['material'], self.layers1_2[i]['thickness'], slope=self.slope) / self.surface)
        if self.zone2.zone_type != ZONE_TYPES.OUTDOOR:
            resistances.append(properties.indoor_surface_resistance(self.layers1_2[-1]['material'], self.slope) / self.surface)
        else:
            resistances.append(properties.outdoor_surface_resistance(self.layers1_2[-1]['material'], self.slope) / self.surface)
        return resistances

    @property
    def Cs1_2(self) -> list[float]:
        """
        Return the list of capacitances, one for each layer of an interface

        :return: list of capacitances, one for each layer of an interface. The values depends on thicknesses and on surface
        :rtype: list[float]
        """
        capacitances = [None]
        for layer1_2 in self.layers1_2:
            if layer1_2['material'] == 'air':
                capacitances.append(None)
            else:
                density: float = properties.get(layer1_2['material'])['density']
                Cp: float = properties.get(layer1_2['material'])['Cp']
                capacitances.append(layer1_2['thickness'] * self.surface*density*Cp)
        capacitances.append(None)
        return capacitances

    def __str__(self) -> str:
        """
        :return: string depicting the layered interface
        :rtype: str
        """
        string: str = 'Layered wall side \033[91m(%s, %s)\033[0m type: %s surface: \033[91m%.3fm2\033[0m with heat transfer: \033[91m%gW/K\033[0m and a capacitance C=%gkJ/K composed of\n' % (self.zone1.name, self.zone2.name, str(self.side_type).split('.')[1], self.surface, 1/sum([R if R is not None else 0 for R in self.Rs1_2]), sum([C/1000 if C is not None else 0 for C in self.Cs1_2]))
        for i in range(len(self.Rs1_2)):
            if (i == 0) or (i == len(self.Rs1_2) - 1):
                string += '\t* %s %s > %g°C/W)\n' % ('air', 'surface', self.Rs1_2[i])
            else:
                string += '\t* %s, %gm > %g°C/W, %.1fkJ/K\n' % (self.layers1_2[i-1]['material'], self.layers1_2[i-1]['thickness'], self.Rs1_2[i], self.Cs1_2[i]/1000 if self.Cs1_2[i] is not None else 0)
        return string


class BlockWallSide(WallSide):
    """
    A component interface is a wall side depicted by a global heat transmission coefficient without inertia
    """

    def __init__(self, zone1: Zone, zone2: Zone, side_type: SIDE_TYPES, total_US: float, total_capacitance: float = None):
        """
        Initialize a component interface

        :param zone1: zone next to side 1
        :type zone1: Zone
        :param zone2: zone next to side 2
        :type zone2: Zone
        :param interface_type: type interface corresponding to layered interface
        :type interface_type: Interface
        :param heat_transmission_coefficient: heat transmission coefficient in W/m2/K or in W/K if the surface is 1
        :type heat_transmission_coefficient: float
        :param surface: surface of the interface, default to 1
        :type surface: float, optional
        """
        super().__init__(zone1, zone2, side_type)
        self.total_US: float = total_US
        self.total_capacitance: float = total_capacitance

    @property
    def name(self) -> str:
        return '%s-%s' % (self.zone1.name, self.zone2.name)

    # @property
    # def total_US(self) -> float:
    #     return 1 / sum([R if not None else 0 for R in self.Rs1_2])

    # @property
    # def total_capacitance(self) -> float:
    #     return sum([C if C is not None else 0 for C in self.Cs1_2])

    @property
    def Rs1_2(self) -> list[float]:
        """
        global thermal loss (U) of the block side

        :return: thermal loss in W/K
        :rtype: float
        """
        return [1/self.total_US]

    @property
    def Cs1_2(self) -> list[float]:
        """
        global thermal capacitance (C) of the block side

        :return: thermal capacitance in J/K
        :rtype: float
        """
        return [None]

    def __str__(self) -> str:
        """
        :return: string depicting the component interface
        :rtype: str
        """
        return 'Block wall side (%s, %s) type: %s with losses at %fW/K and capacitance %.0fkJ/K\n' % (self.zone1.name, self.zone2.name, str(self.side_type).split('.')[1], 1/self.Rs1_2[0], self.Cs1_2[0]/1000 if self.Cs1_2[0] is not None else 0)


class Composition:
    """A composition is composed of successive layers related to a unit surface.

    Physical values can be added to the data on top of the class.
    """

    _his = {'vertical': 7.69, 'ascending': 10, 'descending': 5.88}
    _he_wind = 5.7
    _he_constant = 11.4
    _thicknesses = (0, 5e-3, 7e-3, 10e-3, 15e-3, 25e-3, 30e-3)
    _thermal_resistances = (0, 0.11, 0.13, 0.15, 0.17, 0.18, 0.18)
    _positions = ['horizontal', 'vertical']

    @classmethod
    def _hi_unit(cls, position='vertical'):
        """Return indoor convective transmission coefficient.

        :param position: 'vertical' or 'horizontal'
        :type position: string
        :return:  the hi coefficient in W/m2.K
        :rtype: float
        """
        return cls._his[position]

    @classmethod
    def _he_unit(cls, wind_speed_in_ms=2.4):
        """
        Return outdoor convective transmission coefficient.

        :param wind_speed_in_ms: wind speed in m/s, default is to 2.4m/S
        :type wind_speed_in_ms: float
        :return: the coefficient in W/m2.K
        :rtype: float
        """
        return cls._he_wind * wind_speed_in_ms + cls._he_constant

    @classmethod
    def _hr_unit(cls, material, average_temperature_celsius=20):
        """Return radiative transmission coefficient.

        :param material: one string among 'usual', 'glass', 'wood', 'plaster', 'concrete' or 'polystyrene'
        :type material: str
        :param average_temperature_celsius: the temperature for which the coefficient is calculated
        :return: the coefficient in W/m2.K
        :rtype: float
        """
        if material not in properties:
            warnings.warn('material '+material+'has been replaced by usual')
        return 4 * scipy.constants.sigma * properties.get(material)['emissivity'] * (average_temperature_celsius + 273.15) ** 3

    @classmethod
    def Rsout_unit(cls, material, average_temperature_celsius=13, wind_speed_is_m_per_sec=2.9):
        """Return outdoor convective and radiative transmission coefficient.

        :param material: one string among 'usual', 'glass', 'wood', 'plaster', 'concrete' or 'polystyrene'
        :type material: str
        :param average_temperature_celsius: the temperature for which the coefficient is calculated
        :type average_temperature_celsius: float
        :param wind_speed_is_m_per_sec: wind speed in m/s
        :type wind_speed_is_m_per_sec: wind speed on site
        :return: the coefficient in W/m2.K
        :rtype: float
        """
        return 1 / (cls._he_unit(wind_speed_is_m_per_sec) + Composition._hr_unit(material, average_temperature_celsius))

    @classmethod
    def Rsin_unit_vertical(cls, material, average_temperature_celsius=20):
        """Indoor convective and radiative transmission coefficient for a vertical surface.

        :param material: one string among 'usual', 'glass', 'wood', 'plaster', 'concrete' or 'polystyrene'
        :type material: str
        :param average_temperature_celsius: the temperature for which the coefficient is calculated
        :type average_temperature_celsius: float
        :return: the coefficient in W/m2.K
        :rtype: float
        """
        return 1 / (Composition._hi_unit('vertical') + Composition._hr_unit(material, average_temperature_celsius))

    @classmethod
    def Rsin_unit_ascending(cls, material='usual', average_temperature_celsius=20):
        """Compute an indoor air limit surface: convective and radiative transmission coefficient for a horizontal surface with ascending heat flow.

        :param material: one string among 'usual', 'glass', 'wood', 'plaster', 'concrete' or 'polystyrene'
        :type material: string
        :param average_temperature_celsius: the temperature for which the coefficient is calculated
        :type average_temperature_celsius: average magnitude temperature i celsius, default to 20.
        :return: the coefficient in W/m2.
        :rtype: float
        """
        return 1 / (Composition._hi_unit('ascending') + Composition._hr_unit(material, average_temperature_celsius))

    @classmethod
    def Rsin_unit_descending(cls, material='usual', average_temperature_celsius=20):
        """Compute: Indoor convective and radiative transmission coefficient for a horizontal surface with descending heat flow.

        :param material: one string among 'usual', 'glass', 'wood', 'plaster', 'concrete' or 'polystyrene'
        :type material: str
        :param average_temperature_celsius: the temperature for which the coefficient is calculated, default is to 20
        :type average_temperature_celsius: float
        :return: the coefficient in W/m2.K
        :rtype: float
        """
        return 1 / (Composition._hi_unit('descending') + Composition._hr_unit(material, average_temperature_celsius))

    @classmethod
    def R_air_layer_unit_resistance(cls, thickness, position, material1, material2, average_temperature_celsius=20):
        """Return the thermal resistance of an air layer depending of its position.

        :param thickness: thickness of the air layer
        :type thickness: float
        :param position: 'horizontal' or 'vertical'
        :type position: float
        :param material1: one string among 'usual', 'glass', 'wood', 'plaster', 'concrete' or 'polystyrene'
        :type material1: str
        :param material2: one string among 'usual', 'glass', 'wood', 'plaster', 'concrete' or 'polystyrene'
        :type material2: str
        :param average_temperature_celsius: the temperature for which the coefficient is calculated, default is to 20
        :type average_temperature_celsius: float
        :return: thermal resistance in K.m2/W
        :rtype: float
        """
        if thickness <= cls._thicknesses[-1]:
            return interp(thickness, cls._thicknesses, cls._thermal_resistances, left=0, right=cls._thermal_resistances[-1])
        else:
            if position == 'vertical':
                return cls.Rsin_unit_vertical(material1, average_temperature_celsius) + cls.Rsin_unit_vertical(material2, average_temperature_celsius)
            else:
                return cls.Rsin_unit_descending(material2, average_temperature_celsius) + cls.Rsin_unit_ascending(material1, average_temperature_celsius)

    @classmethod
    def R_unit_conduction(cls, thickness, material):
        """Compute the conductive resistance of an layer depending of its thickness.

        :param thickness: thickness of the layer
        :type thickness: float
        :param material: one string among 'usual', 'glass', 'wood', 'plaster', 'concrete' or 'polystyrene'
        :type material: str
        :return: thermal resistance in K.m2/W
        :rtype: float
        """
        return thickness / properties.get(material)['conductivity']

    def _R_unit_added(self, layer_material):
        """Compute unit resistance of a layer added to a composition under construction.

        :param layer_material: one string among 'usual', 'glass', 'wood', 'plaster', 'concrete' or 'polystyrene'
        :type layer_material: str
        :return: unit resistance
        :rtype: float
        """
        if not self.first_layer_indoor:
            return Composition.Rsout_unit(material=layer_material, average_temperature_celsius=self.outdoor_average_temperature, wind_speed_is_m_per_sec=self.wind_speed_is_m_per_sec)
        else:
            if self.position == 'vertical':
                return Composition.Rsin_unit_vertical(material=layer_material, average_temperature_celsius=self.indoor_average_temperature)
            elif self.position == 'horizontal':
                if not self.heating_floor:
                    return Composition.Rsin_unit_descending(material=layer_material, average_temperature_celsius=self.indoor_average_temperature)
                else:
                    return Composition.Rsin_unit_ascending(material=layer_material, average_temperature_celsius=self.indoor_average_temperature)
            raise ValueError('Unknown position')

    def __init__(self, first_layer_indoor, last_layer_indoor, position, indoor_average_temperature_in_celsius=20, outdoor_average_temperature_in_celsius=5, wind_speed_is_m_per_sec=2.4, heating_floor=False):
        """Create a composition is composed of successive layers.

        Physical values can be added to the data on top of the class.

        :param first_layer_indoor: True if first layer is indoor, False if it's outdoor and None if it's not in contact with air
        :type first_layer_indoor: bool or None
        :param last_layer_indoor: True if last layer is indoor, False if it's outdoor and None if it's not in contact with air
        :type last_layer_indoor: bool or None
        :param position: can be either 'vertical' or 'horizontal'
        :type position: str
        :param indoor_average_temperature_in_celsius: average indoor temperature used for linearization of radiative heat in Celsius, default is to 20°C
        :type indoor_average_temperature_in_celsius: float
        :param outdoor_average_temperature_in_celsius: average outdoor temperature used for linearization of radiative heat in Celsius, default is to 5°C
        :type outdoor_average_temperature_in_celsius: float
        :param wind_speed_is_m_per_sec (default is 2.4m/s): average wind speed in m/s
        :type wind_speed_is_m_per_sec: float
        :param heating_floor: True if there is a heating floor, False otherwise. Default is to False
        :type heating_floor: bool
        """
        self.position: str = position
        self.first_layer_indoor: bool = first_layer_indoor
        self.last_layer_indoor: bool = last_layer_indoor
        self.indoor_average_temperature: float = indoor_average_temperature_in_celsius
        self.outdoor_average_temperature: float = outdoor_average_temperature_in_celsius
        self.wind_speed_is_m_per_sec: float = wind_speed_is_m_per_sec
        self.heating_floor: bool = heating_floor
        self.layers = list()

    def layer(self, material, thickness):
        """Add a layer in the composition. First and last layers cannot be air layers.

        :param material: name of the material
        :type material: str
        :param thickness: thickness of the layer
        :type thickness: float
        """
        self.layers.append({'material': material, 'thickness': thickness})

    @property
    def R(self):
        """Compute the thermal resistance for the composition in W.m2/K.

        :return: unit resistance value (for 1m2)
        :rtype: float
        """
        _resistance = 0
        if self.first_layer_indoor is not None:
            if self.layers[0]['material'] == 'air' or self.layers[-1]['material'] == 'air':
                raise ValueError('an external layer cannot be made of air')
            _resistance += self._R_unit_added(self.layers[0]['material'])
        for layer in range(len(self.layers)):
            if self.layers[layer] is not None:
                if self.layers[layer]['material'] == 'air':
                    radiative_resistance = (1 / Composition._hr_unit(self.layers[layer-1]['material'], self.indoor_average_temperature)) + 1 / Composition._hr_unit(self.layers[layer+1]['material'], self.indoor_average_temperature)
                    position = self.position
                    if self.position == 'horizontal' and self.heating_floor:
                        position = 'ascending'
                    elif self.position == 'horizontal' and not self.heating_floor:
                        position = 'descending'
                    air_layer_resistance = Composition.R_air_layer_unit_resistance(self.layers[layer]['thickness'], position, self.layers[layer-1]['material'], self.layers[layer+1]['material'])
                    _resistance += 1 / (1 / air_layer_resistance + 1 / radiative_resistance)
                else:
                    _resistance += Composition.R_unit_conduction(self.layers[layer]['thickness'], self.layers[layer]['material'])
        if self.last_layer_indoor is not None:
            _resistance += self._R_unit_added(self.layers[-1]['material'])
        return _resistance

    @property
    def U(self):
        """Compute thermal transmission coefficient in W/m2.K (1/R of the unit resistance).

        :return: thermal transmission coefficient in W/m2.K
        :rtype: float
        """
        return 1/self.R

    def __str__(self):
        """Return a descriptive string.

        :return: string representative of the composition
        """
        string = 'U=%.4fW/K.m2 (R_unit=%.4fK.m2/W) composed of ' % (self.U, self.R)
        if self.first_layer_indoor is None:
            string += 'contact:'
        elif self.first_layer_indoor:
            string += 'indoor(%s):' % self.position
        else:
            string += 'outdoor(%s):' % self.position
        for layer in self.layers:
            string += '%s(%.3fm):' % (layer['material'], layer['thickness'])
        if self.last_layer_indoor is None:
            string += 'contact\n'
        elif self.last_layer_indoor:
            string += 'indoor(%s)\n' % self.position
        else:
            string += 'outdoor(%s)\n' % self.position
        return string


class Wall:
    """A wall is a set of compositions and thermal bridges of different dimensions (surface for compositions and length for thermal bridges) but also an infiltration varying from a minimum to a maximum value in m3/s."""

    def __init__(self, name):
        """Create a wall.

        :param name: name of the wall.
        :type name: str
        """
        self.name = name
        self.compositions = list()
        self.surfaces = list()
        self.bridges = list()
        self.lengths = list()
        self._infiltration_air_flow = 0
        self._max_opening_air_flow = 0

    def add_composition(self, composition, surface):
        """Add a part of wall in parallel with others defined by a composition and a surface.

        :param composition: composition of the part of wall
        :type composition: Composition
        :param surface: surface of the part of wall
        :type surface: float
        """
        self.compositions.append(composition)
        self.surfaces.append(surface)

    def add_bridge(self, psi, length):
        """Add a thermal bridge.

        :param psi: linear transmission coefficient in W/m.K
        :type psi: float
        :param length: length of the thermal bridge
        :type length: float
        """
        self.bridges.append(psi)
        self.lengths.append(length)

    def add_infiltration(self, minimum_infiltration):
        """Add a minimum infiltration air flow through the wall.

        :param minimum_infiltration: minimum infiltration air flow in m3/s
        :type minimum_infiltration: float
        """
        self._infiltration_air_flow = minimum_infiltration

    def add_max_opening_air_flow(self, maximum_infiltration):
        """Add a maximum infiltration air flow reached when opening ration is equal to 1.

        :param maximum_infiltration: maximum infiltration air flow in m3/s
        :type maximum_infiltration: float
        """
        self._max_opening_air_flow = maximum_infiltration

    def air_volumic_thermal_transmission(self, opening_ratio=0):
        """Return heat transmitted by volumetric exchange for an intermediate value of infiltration.

        :param opening_ratio: value between 0 and 1 changing the infiltration air flow from minimum to maximum, default is to 0.
        :type opening_ratio: float
        :return: heat transmitted by volumetric exchange in W/K
        :rtype: float
        """
        Q = self._infiltration_air_flow + opening_ratio * (self._max_opening_air_flow - self._infiltration_air_flow)
        return Composition.volumic_masses['air'] * Composition.specific_heats['air'] * Q

    def US(self, opening_ratio=0):
        """Compute the total heat loss of the wall in W/K.

        :param opening_ratio: value between 0 and 1 changing the infiltration aor flow from minimum to maximum
        :type opening_ratio: float
        :return: total heat loss of the wall in W/K
        :rtype: float
        """
        thermal_transmission_coefficient = 0
        for i in range(len(self.compositions)):
            thermal_transmission_coefficient += self.compositions[i].U * self.surfaces[i]
        for i in range(len(self.bridges)):
            thermal_transmission_coefficient += self.bridges[i] * self.lengths[i]
        thermal_transmission_coefficient += self.air_volumic_thermal_transmission(opening_ratio)
        return thermal_transmission_coefficient

    def R(self, opening_ratio=0):
        """Compute the total thermal resistance of the wall.

        :param opening_ratio: value between 0 and 1 changing the infiltration air flow from minimum to maximum
        :type opening_ratio: float
        :return: total thermal resistance of the wall in K/W
        :rtype: float
        """
        return 1 / self.US(opening_ratio)

    def __str__(self):
        """Return a descriptive string.

        :return: string representative of the wall
        """
        string = '+ Wall % s,' % self.name
        if self.US() == self.US(opening_ratio=1):
            string += 'US=%fW/K (R=%fK/W)\n' % (self.US(), self.R())
        else:
            string += 'US=%f>%fW/K (R=%f<%fK/W)\n' % (self.US(), self.US(1), self.R(), self.R(1))
        for i in range(len(self.compositions)):
            string += 'Composition(%.2fm2):' % (self.surfaces[i])
            string += self.compositions[i].__str__()
        for i in range(len(self.bridges)):
            string += 'Thermal bridge (length=%fm): psiL=%fW/K\n' % (self.lengths[i], self.lengths[i]*self.bridges[i])
        if self.air_volumic_thermal_transmission() == self.air_volumic_thermal_transmission(opening_ratio=1) == 0:
            return string + '\n'
        string += 'Infiltration loss: U=%fW/K' % self.air_volumic_thermal_transmission()
        if self.air_volumic_thermal_transmission(opening_ratio=1) != 0:
            string += '>%fW/K' % self.air_volumic_thermal_transmission(opening_ratio=1)
        return string + '\n'
