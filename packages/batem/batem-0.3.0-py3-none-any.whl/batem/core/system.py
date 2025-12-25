"""Thermal system components and HVAC equipment modeling module for building energy analysis.

.. module:: batem.core.system

This module provides comprehensive tools for modeling thermal system components
including heat pumps, radiators, and refrigerant cycles used in building energy
systems. It includes thermodynamic calculations, heat transfer modeling, and
system performance analysis for HVAC equipment and thermal systems.

Classes
-------

.. autosummary::
   :toctree: generated/

   RadiatorType
   Refrigerant
   HeatPump
   WaterRadiator
   HorizontalRadiator
   VerticalRadiator
   HeatPumpRadiator

Classes Description
-------------------

**RadiatorType**
    Enumeration for radiator types and orientations.

**Refrigerant**
    Refrigerant fluid properties and thermodynamic cycle calculations.

**HeatPump**
    Heat pump system model with refrigerant cycle analysis.

**WaterRadiator**
    Abstract base class for water radiators.

**HorizontalRadiator**
    Horizontal water radiator implementation.

**VerticalRadiator**
    Vertical water radiator implementation.

**HeatPumpRadiator**
    Combined heat pump and radiator system model.

Key Features
------------

* Refrigerant property calculations using CoolProp library integration
* Thermodynamic cycle analysis for heat pump systems
* Heat transfer modeling for radiators and heating/cooling systems
* Coefficient of performance (COP) calculations for heat pumps
* Water radiator modeling with orientation-specific heat transfer
* Combined system modeling for heat pump-radiator interactions
* Temperature and pressure calculations for refrigerant cycles
* System performance analysis and optimization capabilities
* Integration with building energy analysis and thermal modeling
* Support for various refrigerant fluids and system configurations

The module is designed for building energy analysis, HVAC system design,
and thermal system performance evaluation in research and practice.

.. note::
    This module requires CoolProp library for refrigerant property calculations.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""

try:
    import CoolProp.CoolProp as CP
    from CoolProp.CoolProp import PropsSI
    HAS_COOLPROP = True
except ImportError:
    HAS_COOLPROP = False
    # Fallback for when CoolProp is not available

    class CP:
        @staticmethod
        def get_global_param_string(param):
            return "R32,R134a,R410A,R407C"

    class PropsSI:
        @staticmethod
        def __call__(*args, **kwargs):
            return 0.0
from math import exp, sqrt
from enum import Enum
from abc import ABC, abstractmethod
from batem.core.library import Air, Properties
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
from batem.core.utils import in_jupyter

# Configure plotly for proper display
import plotly.io as pio
if not in_jupyter():
    pio.renderers.default = 'plotly_mimetype+notebook'
else:
    pio.renderers.default = 'notebook'


class RadiatorType(Enum):
    """Enumeration for radiator types.

    Defines the available radiator orientations for heat transfer calculations.

    Attributes:
        VERTICAL: Vertical radiator orientation
        HEATING_FLOOR: Horizontal heating floor orientation
    """
    VERTICAL = 'vertical'
    HEATING_FLOOR = 'heating_floor'


class Refrigerant:
    """Refrigerant fluid properties and thermodynamic cycle calculations.

    This class provides access to refrigerant properties using CoolProp library
    and calculates thermodynamic cycles for heat pump systems.

    Attributes:
        known_refrigerants (list[str]): List of all available refrigerants in CoolProp
        refrigerant_name (str): Name of the refrigerant fluid
    """

    known_refrigerants: list[str] = CP.get_global_param_string("FluidsList").split(",")

    def __init__(self, refrigerant_name):
        """Initialize refrigerant with specified fluid name.

        :param refrigerant_name: Name of the refrigerant fluid
        :type refrigerant_name: str
        :raises ValueError: If the refrigerant name is not recognized by CoolProp
        """
        if refrigerant_name not in self.known_refrigerants:
            raise ValueError(f"Refrigerant {refrigerant_name} is not known. Known fluids are: {self.known_refrigerants}")
        self.refrigerant_name = refrigerant_name

    def heat_pump_cycle(self, T1_cold_K: float, T3_hot_K: float, pressure_drop_evaporator_Pa: float = 10000, pressure_drop_condenser_Pa: float = 20000, eta_is: float = 0.75, display: bool = False, plot: bool = False) -> float:
        """Calculate thermodynamic cycle points for standard vapor compression cycle.

        Performs thermodynamic analysis of a heat pump cycle including compression,
        condensation, expansion, and evaporation processes.

        :param T1_cold_K: Evaporator outlet temperature in Kelvin
        :type T1_cold_K: float
        :param T3_hot_K: Condenser outlet temperature in Kelvin
        :type T3_hot_K: float
        :param pressure_drop_evaporator_Pa: Pressure drop in evaporator, defaults to 10000
        :type pressure_drop_evaporator_Pa: float, optional
        :param pressure_drop_condenser_Pa: Pressure drop in condenser, defaults to 20000
        :type pressure_drop_condenser_Pa: float, optional
        :param eta_is: Isentropic efficiency, defaults to 0.75
        :type eta_is: float, optional
        :param display: Print cycle description, defaults to False
        :type display: bool, optional
        :param plot: Plot the cycle on P-h diagram, defaults to False
        :type plot: bool, optional
        :returns: Dictionary containing cycle thermodynamic properties
        :rtype: dict

        Note:
            The cycle follows standard vapor compression cycle with points:
            - Point 1: Superheated vapor at evaporator exit
            - Point 2s: Isentropic compression to condenser pressure
            - Point 2: Actual compression (accounting for isentropic efficiency)
            - Point 3: Saturated liquid at condenser exit
            - Point 4: Throttling process (isenthalpic)
        """

        # Calculate pressures exactly like the reference
        p14_evap_Pa = CP.PropsSI('P', 'T', T1_cold_K, 'Q', 1, self.refrigerant_name) - pressure_drop_evaporator_Pa
        p23_cond_Pa = CP.PropsSI('P', 'T', T3_hot_K, 'Q', 0, self.refrigerant_name) + pressure_drop_condenser_Pa

        # Calculate enthalpies exactly like the reference
        h1 = CP.PropsSI('H', 'P', p14_evap_Pa, 'Q', 1, self.refrigerant_name)
        s1 = CP.PropsSI('S', 'P', p14_evap_Pa, 'Q', 1, self.refrigerant_name)
        h2s = CP.PropsSI('H', 'P', p23_cond_Pa, 'S', s1, self.refrigerant_name)
        h3 = CP.PropsSI('H', 'P', p23_cond_Pa, 'Q', 0, self.refrigerant_name)
        h4 = h3  # Throttling process (isenthalpic)
        t3 = CP.PropsSI('T', 'P', p23_cond_Pa, 'Q', 0, self.refrigerant_name)

        h2 = h1 + (h2s - h1) / eta_is

        cycle = {
            'T1': T1_cold_K,
            'T3': T3_hot_K,
            'p14': p14_evap_Pa,
            'p23': p23_cond_Pa,
            'h1': h1,
            'h2s': h2s,
            'h2': h2,
            'h3': h3,
            'h4': h4,
            's1': s1,
            'eta_is': eta_is,
            't3': t3,
            'compr12': h2 - h1,
            'h14': h1 - h4,
            'h23': h2 - h3
        }
        if display:
            description = self.heat_pump_cycle_description()
            print(description['description'])
            for var, value in cycle.items():
                print(f"{var}: {value} -> {description[var]}")
        if plot:
            self.plot_cycle(cycle)
        return cycle

    def plot_cycle(self, cycle: dict[str, float]) -> None:
        """Plot the thermodynamic cycle on a log(P)-h diagram.

        Creates a pressure-enthalpy diagram showing the thermodynamic cycle
        with saturated liquid and vapor lines, and cycle points.

        :param cycle: Dictionary containing cycle thermodynamic properties
        :type cycle: dict[str, float]
        """
        fluid = self.refrigerant_name

        min_p = min(cycle['p14'], cycle['p23']) / 1e5  # Convert to bar
        max_p = max(cycle['p14'], cycle['p23']) / 1e5  # Convert to bar
        pressure_range = max_p - min_p
        min_plot_p = max(0.1, min_p - pressure_range * 0.2)  # At least 0.1 bar
        max_plot_p = max_p + pressure_range * 0.2
        pressures = np.logspace(np.log10(min_plot_p*1e5), np.log10(max_plot_p*1e5), 500)
        h_liq = []
        h_vap = []
        log_p = []
        plt.figure(figsize=(10, 6))
        for p in pressures:
            try:
                h1 = PropsSI('H', 'P', p, 'Q', 0, fluid) / 1000  # kJ/kg
                h2 = PropsSI('H', 'P', p, 'Q', 1, fluid) / 1000  # kJ/kg
                h_liq.append(h1)
                h_vap.append(h2)
                log_p.append(np.log10(p/1e5))  # log10(bar)
            except Exception:
                continue
        plt.plot(h_liq, log_p, label='Saturated Liquid', color='blue')
        plt.plot(h_vap, log_p, label='Saturated Vapor', color='red')

        cycle_logp = [np.log10(cycle['p14']/1e5), np.log10(cycle['p23']/1e5), np.log10(cycle['p23']/1e5),
                      np.log10(cycle['p23']/1e5), np.log10(cycle['p14']/1e5), np.log10(cycle['p14']/1e5)]
        cycle_h = [cycle['h1']/1000, cycle['h2']/1000, cycle['h2s']/1000, cycle['h3']/1000, cycle['h4']/1000, cycle['h1']/1000]
        labels = ['h1', 'h2', 'h2s', 'h3', 'h4']
        for i in range(len(cycle_h)-1):
            plt.annotate(labels[i], xy=(cycle_h[i], cycle_logp[i]), xytext=(cycle_h[i]+5, cycle_logp[i]+.1), arrowprops=dict(facecolor='black', arrowstyle="->"))
        plt.plot(cycle_h, cycle_logp, label='thermodynamic cycle', color='green')

        plt.xlabel('Enthalpy [kJ/kg]')
        plt.ylabel('Pressure [bar]')
        plt.title(f'Thermodynamic cycle in a log(p)-h diagram for {self.refrigerant_name}')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def heat_pump_cycle_description(self) -> dict[str, str]:
        """Get description of the thermodynamic cycle points and variables.

        :returns: Dictionary containing descriptions of cycle points and variables
        :rtype: dict[str, str]
        """
        return {
            'description':
            """Thermodynamic cycle points (standard vapor compression cycle)
            Point 1: Superheated vapor at evaporator exit (h1 already set)
            Point 2s: Isentropic compression to condenser pressure (h2s already set)
            Point 2: Actual compression (accounting for isentropic efficiency)
            Point 3: Saturated liquid at condenser exit (h3 already set)
            Point 4: Throttling process (isenthalpic) (h4 already set)
            """,
            'T1': 'temperature at evaporator outlet (cold side) [K]',
            'T3': 'temperature at condenser outlet (hot side) [K]',
            'p14': 'pressure in evaporator (cold side) [Pa]',
            'p23': 'pressure in condenser [Pa]',
            'h1': 'enthalpy superheated vapor at evaporator outlet [J_per_kg]',
            'h2s': 'enthalpy isentropic compression at compressor outlet [J_per_kg]',
            'h2': 'enthalpy compressor outlet [J_per_kg]',
            'h3': 'enthalpy saturated liquid at condenser outlet [J_per_kg]',
            'h4': 'enthalpy throttling process at condenser outlet [J_per_kg]',
            's1': 'entropy superheated vapor at evaporator outlet [J_per_kg_K]',
            'eta_is': 'isentropic efficiency',
            't3': 'temperature saturated liquid at condenser outlet [K]',
            'compr12': 'compressor work during isentropic compression [J_per_kg]',
            'h14': 'heat absorbed by evaporator [J_per_kg]',
            'h23': 'heat released by condenser [J_per_kg]'
        }

    def enthalpy_J_per_kg(self, temperature_K: float, pressure_Pa: float) -> float:
        """Calculate specific enthalpy of the refrigerant.

        :param temperature_K: Temperature in Kelvin
        :type temperature_K: float
        :param pressure_Pa: Pressure in Pascal
        :type pressure_Pa: float
        :returns: Specific enthalpy in J/kg
        :rtype: float
        """
        return PropsSI('H', 'T', temperature_K, 'P', pressure_Pa, self.refrigerant_name)

    def internal_energy_J_per_kg(self, temperature_K: float, pressure_Pa: float) -> float:
        """Calculate specific internal energy of the refrigerant.

        :param temperature_K: Temperature in Kelvin
        :type temperature_K: float
        :param pressure_Pa: Pressure in Pascal
        :type pressure_Pa: float
        :returns: Specific internal energy in J/kg
        :rtype: float
        """
        return PropsSI('U', 'T', temperature_K, 'P', pressure_Pa, self.refrigerant_name)

    def entropy_J_per_kg_K(self, temperature_K: float, pressure_Pa: float) -> float:
        """Calculate specific entropy of the refrigerant.

        :param temperature_K: Temperature in Kelvin
        :type temperature_K: float
        :param pressure_Pa: Pressure in Pascal
        :type pressure_Pa: float
        :returns: Specific entropy in J/kg·K
        :rtype: float
        """
        return PropsSI('S', 'T', temperature_K, 'P', pressure_Pa, self.refrigerant_name)

    def density_m3_per_kg(self, temperature_K: float, pressure_Pa: float) -> float:
        """Calculate specific volume of the refrigerant.

        :param temperature_K: Temperature in Kelvin
        :type temperature_K: float
        :param pressure_Pa: Pressure in Pascal
        :type pressure_Pa: float
        :returns: Specific volume in m³/kg
        :rtype: float
        """
        return 1 / PropsSI('D', 'T', temperature_K, 'P', pressure_Pa, self.refrigerant_name)

    def dryness_fraction(self, temperature_K: float, pressure_Pa: float) -> float:
        """Calculate dryness fraction (quality) of the refrigerant.

        :param temperature_K: Temperature in Kelvin
        :type temperature_K: float
        :param pressure_Pa: Pressure in Pascal
        :type pressure_Pa: float
        :returns: Dryness fraction (0 for saturated liquid, 1 for saturated vapor)
        :rtype: float
        """
        return PropsSI('Q', 'T', temperature_K, 'P', pressure_Pa, self.refrigerant_name)

    def temperature_K(self, pressure_Pa: float, dryness_fraction: float) -> float:
        """Calculate saturation temperature for given pressure and dryness fraction.

        :param pressure_Pa: Pressure in Pascal
        :type pressure_Pa: float
        :param dryness_fraction: Dryness fraction (0 for saturated liquid, 1 for saturated vapor)
        :type dryness_fraction: float
        :returns: Saturation temperature in Kelvin
        :rtype: float
        """
        return PropsSI('T', 'P', pressure_Pa, 'Q', dryness_fraction, self.refrigerant_name)


class HeatPump:
    """Heat pump system model.

    This class models a heat pump system, including refrigerant cycle analysis
    and heat transfer to/from indoor and outdoor environments.

    Attributes:
        refrigerant: Refrigerant object for thermodynamic calculations
        _mode: Operating mode ('heating', 'cooling', 'off')
        _Tcold_C: Indoor temperature in Celsius
        _Thot_C: Outdoor temperature in Celsius
        _cop: Coefficient of performance
        _thermal_power_W: Thermal power output/input in Watts
        _electrical_power_W: Electrical power input in Watts
        _refrigerant_mass_flow_rate_kg_per_s: Mass flow rate of refrigerant in kg/s
    """

    def __init__(self, refrigerant: str = 'R32', eta_compressor: float = 1, max_thermal_power_W: float = None, max_electrical_power_W: float = None):
        """Initialize heat pump with specified refrigerant.

        :param refrigerant: Name of the refrigerant fluid, defaults to 'R32'
        :type refrigerant: str, optional
        :param eta_compressor: Compressor efficiency, defaults to 1
        :type eta_compressor: float, optional
        :param max_thermal_power_W: Maximum thermal power in Watts, defaults to None
        :type max_thermal_power_W: float, optional
        :param max_electrical_power_W: Maximum electrical power in Watts, defaults to None
        :type max_electrical_power_W: float, optional
        """
        self.refrigerant: Refrigerant = Refrigerant(refrigerant)
        self.eta_compressor_drive: float = eta_compressor
        self.max_thermal_power_W: float = max_thermal_power_W
        self.max_electrical_power_W: float = max_electrical_power_W

    def solve(self, mode: str, demanded_thermal_power_W: float, Tcold_C: float, Thot_C: float, display: bool = False) -> dict[str, float]:
        """Calculate heat pump performance for a given mode and thermal power.

        Determines the operating mode, calculates the refrigerant cycle, and
        computes the electrical power and COP based on the thermal power.

        :param mode: Operating mode ('heating', 'cooling', 'auto')
        :type mode: str
        :param thermal_power_W: Thermal power output/input in Watts
        :type thermal_power_W: float
        :param Tcold_C: Indoor temperature in Celsius
        :type Tcold_C: float
        :param Thot_C: Outdoor temperature in Celsius
        :type Thot_C: float
        """
        info: str = ''
        if self.max_thermal_power_W is not None and demanded_thermal_power_W > self.max_thermal_power_W:
            demanded_thermal_power_W = self.max_thermal_power_W
            info += 'thermal power limited to ' + str(self.max_thermal_power_W) + ' W\n'
        if mode.lower() == "auto":
            if demanded_thermal_power_W >= 0:
                mode = "heating"
            else:
                mode = "cooling"
        if mode.lower() not in ["heating", "cooling"]:
            raise ValueError("Mode must be 'heating', 'cooling' or 'auto'")
        demanded_thermal_power_W = abs(demanded_thermal_power_W)

        temperature_diff: float = Thot_C - Tcold_C
        temperature_factor = 1.0 + max(0, temperature_diff - 20) * 0.02  # 2% increase per °C above 20°C difference
        temperature_factor = max(0.5, min(1.5, temperature_factor))  # Limit between 50% and 150%
        temperature_factor = temperature_factor / self.eta_compressor_drive

        T_evaporator_K = Tcold_C + 273.15
        T_condenser_K = Thot_C + 273.15
        if T_evaporator_K > T_condenser_K:
            return {'cop': float('nan'), 'electrical_power_W': 0, 'thermal_power_W': 0, 'mode': 'off', 'Tevaporator_C': T_evaporator_K - 273.15, 'Tcondenser_C': T_condenser_K - 273.15, 'refrigerant_mass_flow_rate_kg_per_s': 0, 'info': info}

        # Initialize refrigerant_mass_flow_rate_kg_per_s to avoid UnboundLocalError
        refrigerant_mass_flow_rate_kg_per_s: float = 0.0

        try:
            cycle = self.refrigerant.heat_pump_cycle(T_evaporator_K, T_condenser_K)
            h14_J_per_kg = cycle['h14']  # J/kg - specific enthalpy
            h23_J_per_kg = cycle['h23']    # J/kg - specific enthalpy
            compr12_J_per_kg = cycle['compr12']       # J/kg - specific work

            if mode.lower() == "heating":
                cop = h23_J_per_kg / compr12_J_per_kg / temperature_factor
                refrigerant_mass_flow_rate_kg_per_s = demanded_thermal_power_W / h23_J_per_kg
            elif mode.lower() == "cooling":
                cop = h14_J_per_kg / compr12_J_per_kg / temperature_factor
                refrigerant_mass_flow_rate_kg_per_s = demanded_thermal_power_W / h14_J_per_kg
            else:
                raise ValueError("Mode must be 'heating' or 'cooling'")
            
            if self.max_electrical_power_W is not None:
                truncated_thermal_power_W = min(self.max_electrical_power_W * cop, demanded_thermal_power_W)  # (cop * temperature_factor)
                if truncated_thermal_power_W != demanded_thermal_power_W:
                    info += 'electrical power limited to ' + str(self.max_electrical_power_W) + ' W\n'
                demanded_thermal_power_W = truncated_thermal_power_W

            electrical_power_W: float = demanded_thermal_power_W / cop

        except Exception:
            cop = 1
            electrical_power_W = demanded_thermal_power_W
            refrigerant_mass_flow_rate_kg_per_s = 0.0

        cop = cop / temperature_factor
        if cop < 1:
            cop = 1

        result = {'cop': cop if demanded_thermal_power_W != 0 else 0, 'electrical_power_W': electrical_power_W, 'thermal_power_W': demanded_thermal_power_W if mode.lower() == "heating" else - demanded_thermal_power_W, 'mode': mode, 'Tevaporator_C': T_evaporator_K - 273.15, 'Tcondenser_C': T_condenser_K - 273.15, 'refrigerant_mass_flow_rate_kg_per_s': refrigerant_mass_flow_rate_kg_per_s, 'info': info}
        
        if display:
            print('\n'.join([f"{key}: {value}" for key, value in result.items()]))

        # Store results
        return result

    def __str__(self):
        """String representation of the heat pump.

        :returns: Formatted string with heat pump properties
        :rtype: str
        """
        return f"----HeatPump----\nrefrigerant={self.refrigerant.refrigerant_name}\nmax_thermal_power_W={self.max_thermal_power_W}\nmax_electrical_power_W={self.max_electrical_power_W}\nmode={self._mode})"


class WaterRadiator(ABC):
    """Base class for water radiators.

    Provides common functionality for water-based heating and cooling radiators.

    Attributes:
        radiator_surface_m2: Surface area of the radiator in square meters
        radiator_thickness_m: Thickness of the radiator material in meters
        radiator_material: Material of the radiator (e.g., 'copper', 'aluminum')
        direction: Orientation of the radiator ('horizontal' or 'vertical')
        radiator_length_mm: Length of the radiator in millimeters
        typical_Tindoor_C: Typical indoor temperature for heat transfer calculations
        typical_Tsurface_C: Typical surface temperature for heat transfer calculations
        rho_a: Air density in kg/m³
        cp_a: Air specific heat in J/kg·K
        rho_w: Water density in kg/m³
        cp_w: Water specific heat in J/kg·K
        radiator_emissivity: Emissivity of the radiator material
        radiator_conductivity: Conductivity of the radiator material in W/m·K
        cp_r: Specific heat of the radiator material in J/kg·K
        hi_horizontal: Heat transfer coefficient for horizontal heat flow
        hi_vertical: Heat transfer coefficient for vertical heat flow
        hr_any: Radiation heat transfer coefficient
        ho_horizontal: Heat transfer coefficient for horizontal heat flow
        ho_vertical: Heat transfer coefficient for vertical heat flow
    """

    def __init__(self, radiator_surface_m2: float, thickness_m: float, material: str, direction: str, radiator_length_m: float = None, typical_Tindoor_C: float = 20, typical_Tsurface_C: float = 40) -> float:
        """Initialize water radiator.

        :param radiator_surface_m2: Surface area of the radiator in square meters
        :type radiator_surface_m2: float
        :param thickness_m: Thickness of the radiator material in meters
        :type thickness_m: float
        :param material: Material of the radiator (e.g., 'copper', 'aluminum')
        :type material: str
        :param direction: Orientation of the radiator ('horizontal' or 'vertical')
        :type direction: str
        :param radiator_length_m: Length of the radiator in meters, defaults to None
        :type radiator_length_m: float, optional
        :param typical_Tindoor_C: Typical indoor temperature for heat transfer calculations, defaults to 20
        :type typical_Tindoor_C: float, optional
        :param typical_Tsurface_C: Typical surface temperature for heat transfer calculations, defaults to 40
        :type typical_Tsurface_C: float, optional
        """
        if radiator_length_m is None:
            radiator_length_m = sqrt(radiator_surface_m2)
        self.typical_Tindoor_C = typical_Tindoor_C
        self.typical_Tsurface_C = typical_Tsurface_C
        self.radiator_length_mm = radiator_length_m * 1000

        self.radiator_surface_m2: float = radiator_surface_m2  # surface area in m²
        self.radiator_thickness_m: float = thickness_m  # thickness in m
        self.radiator_material: str = material  # material
        if direction == 'horizontal':
            self.direction = 'horizontal'
        elif direction == 'vertical':
            self.direction = 'vertical'
        else:
            raise ValueError(f"Direction must be 'horizontal' or 'vertical', not {direction}")

        properties = Properties()
        self.air = Air()
        air_properties: dict[str, float] = properties.get('air')
        self.rho_a: float = air_properties['density']  # kg/m³ - air density
        self.cp_a: float = air_properties['Cp']  # J/kg·K - air specific heat

        water_properties: dict[str, float] = properties.get('water')
        self.rho_w: float = water_properties['density']  # kg/m³ - water density
        self.cp_w: float = water_properties['Cp']  # J/kg·K - water specific heat

        radiator_properties: dict[str, float] = properties.get(self.radiator_material)
        self.radiator_emissivity: float = radiator_properties['emissivity']
        self.radiator_conductivity: float = radiator_properties['conductivity']
        self.cp_r: float = radiator_properties['Cp']  # J/kg·K - water specific heat

        self.hi_horizontal: float = self.air.hi_horizontal_surface(T_surface_celsius=typical_Tsurface_C, T_air_celsius=typical_Tindoor_C, typical_length_mm=self.radiator_length_mm, emissivity=self.radiator_emissivity)
        self.hi_vertical: float = self.air.hi_vertical_surface(T_surface_celsius=typical_Tsurface_C, T_air_celsius=typical_Tindoor_C, typical_length_mm=self.radiator_length_mm, emissivity=self.radiator_emissivity)
        self.hr_any: float = self.air.hr(emissivity=self.radiator_emissivity, temperature_celsius=typical_Tsurface_C)

        self.ho_horizontal = self.air.ho_horizontal_surface(T_surface_celsius=typical_Tsurface_C, T_air_celsius=typical_Tindoor_C, typical_length_mm=self.radiator_length_mm, emissivity=self.radiator_emissivity, air_speed_km_h=0)
        air_speed_vertical = sqrt(2*9.81/300*(typical_Tsurface_C-typical_Tindoor_C)*self.radiator_length_mm/1000)
        self.ho_vertical = self.air.ho_vertical_surface(T_surface_celsius=typical_Tsurface_C, T_air_celsius=typical_Tindoor_C, typical_length_mm=self.radiator_length_mm, emissivity=self.radiator_emissivity, wind_speed_km_h=air_speed_vertical)

    def set_indoor_temperature(self, Tindoor_C: float) -> None:
        """Update heat transfer coefficients based on indoor temperature.

        :param Tindoor_C: Indoor temperature in Celsius
        :type Tindoor_C: float
        """
        self.typical_Tindoor_C = Tindoor_C
        self.hi_horizontal = self.air.hi_horizontal_surface(T_surface_celsius=self.typical_Tsurface_C, T_air_celsius=Tindoor_C, typical_length_mm=self.radiator_length_mm, emissivity=self.radiator_emissivity)
        self.hi_vertical = self.air.hi_vertical_surface(T_surface_celsius=self.typical_Tsurface_C, T_air_celsius=Tindoor_C, typical_length_mm=self.radiator_length_mm, emissivity=self.radiator_emissivity)
        self.hr_any = self.air.hr(emissivity=self.radiator_emissivity, temperature_celsius=self.typical_Tsurface_C)
        self.ho_horizontal = self.air.ho_horizontal_surface(T_surface_celsius=self.typical_Tsurface_C, T_air_celsius=Tindoor_C, typical_length_mm=self.radiator_length_mm, emissivity=self.radiator_emissivity, air_speed_km_h=0)
        air_speed_vertical = sqrt(2*9.81/300*(self.typical_Tsurface_C-Tindoor_C)*self.radiator_length_mm/1000)
        self.ho_vertical = self.air.ho_vertical_surface(T_surface_celsius=self.typical_Tsurface_C, T_air_celsius=Tindoor_C, typical_length_mm=self.radiator_length_mm, emissivity=self.radiator_emissivity, wind_speed_km_h=air_speed_vertical)

    @property
    def hi(self) -> float:
        """Get the combined heat transfer coefficient (hi) for the radiator."""
        if self.direction == 'horizontal':
            return self.hi_horizontal
        else:
            return self.hi_vertical

    @property
    def hr(self) -> float:
        """Get the radiation heat transfer coefficient (hr) for the radiator."""
        return self.hr_any

    @property
    def ho(self) -> float:
        """Get the combined heat transfer coefficient (ho) for the radiator."""
        if self.direction == 'horizontal':
            return self.ho_horizontal
        else:
            return self.ho_vertical

    @property
    def hio(self) -> float:
        """Get the combined heat transfer coefficient (hio) for the radiator."""
        if self.direction == 'horizontal':
            return self.hi
        else:
            return self.ho

    @property
    def U_total(self):
        """Get the total heat transfer coefficient (U_total) for the radiator."""
        if self.direction == 'horizontal':
            return 1 / (1 / self.U_partial + 1 / self.hi_horizontal)
        else:
            return 1 / (1 / self.U_partial + 1 / self.ho_vertical)

    @property
    def U_partial(self) -> float:
        """Get the partial heat transfer coefficient (U_partial) for the radiator."""
        return self.radiator_conductivity / self.radiator_thickness_m

    def Tsa_C(self, T_indoor_C: float, thermal_power_W: float) -> float:
        """Calculate the surface temperature of the radiator (Tsa) in Celsius.

        :param T_indoor_C: Indoor temperature in Celsius
        :type T_indoor_C: float
        :param thermal_power_W: Thermal power input/output in Watts
        :type thermal_power_W: float
        :returns: Surface temperature of the radiator in Celsius
        :rtype: float
        """
        return T_indoor_C + thermal_power_W / (self.hio * self.radiator_surface_m2)

    def Tw_C(self, T_indoor_C: float, thermal_power_W: float) -> float:
        """Calculate the water temperature (Tw) in Celsius.

        :param T_indoor_C: Indoor temperature in Celsius
        :type T_indoor_C: float
        :param thermal_power_W: Thermal power input/output in Watts
        :type thermal_power_W: float
        :returns: Water temperature in Celsius
        :rtype: float
        """
        return self.Tsa_C(T_indoor_C, thermal_power_W) + thermal_power_W / (self.U_partial * self.radiator_surface_m2)

    def Tw_in_C(self, Tw_out_C: float, thermal_power_W: float, delta_T: float) -> float:
        """Calculate the inlet water temperature (Tw_in) in Celsius.

        :param Tw_out_C: Outlet water temperature in Celsius
        :type Tw_out_C: float
        :param thermal_power_W: Thermal power input/output in Watts
        :type thermal_power_W: float
        :param delta_T: Temperature difference across the radiator, defaults to 0
        :type delta_T: float, optional
        :returns: Inlet water temperature in Celsius
        :rtype: float
        """
        return self.Tw_C(Tw_out_C, thermal_power_W) + delta_T / 2

    def radiative_power_ratio(self, T_indoor_C: float, thermal_power_W: float) -> float:
        """Calculate the radiative power ratio (RPR) for the radiator.

        :param T_indoor_C: Indoor temperature in Celsius
        :type T_indoor_C: float
        :param thermal_power_W: Thermal power input/output in Watts
        :type thermal_power_W: float
        :returns: Radiative power ratio
        :rtype: float
        """
        if thermal_power_W == 0:
            return 0
        else:
            return self.radiator_surface_m2 * self.hr * (self.Tsa_C(T_indoor_C, thermal_power_W) - T_indoor_C) / thermal_power_W

    def __str__(self) -> str:
        """String representation of the radiator."""
        string = f"RADIATOR:\n\t{self.__class__.__name__}\n\tsurface area: {self.radiator_surface_m2:.2f}m²\n\tthickness: {self.radiator_thickness_m:.3f}m\n\tmaterial: {self.radiator_material}\n"
        return string

    def solve(self, Tw_out_C: float, thermal_power_W: float, display: bool = False) -> dict[str, float]:
        """Solve the heat transfer problem for the radiator.

        Calculates the water mass flow rate and temperature difference across
        the radiator based on the given outlet water temperature, thermal power,
        and typical indoor temperature.

        :param Tw_out_C: Outlet water temperature in Celsius
        :type Tw_out_C: float
        :param thermal_power_W: Thermal power input/output in Watts
        :type thermal_power_W: float
        :param display: Print debug information, defaults to False
        :type display: bool, optional
        :returns: Dictionary containing calculated temperatures and flow rate
        :rtype: dict
        """
        # if Tw_out_C < self.typical_Tindoor_C:
        #     raise Exception(f"Tw_out_C ({Tw_out_C}°C) must be greater than the indoor temperature ({self.typical_Tindoor_C}°C)")
        water_mass_flow_rate_kg_per_s = (self.U_total * self.radiator_surface_m2) / (2 * self.cp_w)
        delta_T = 2 * thermal_power_W / (self.U_total * self.radiator_surface_m2)

        self.display(Tw_out_C=Tw_out_C, thermal_power_W=thermal_power_W, water_mass_flow_rate_kg_per_s=water_mass_flow_rate_kg_per_s, delta_T=delta_T, display=display)

        return {'Tsa_C': self.Tsa_C(Tw_out_C, thermal_power_W), 'Tw_in_C': self.Tw_in_C(Tw_out_C=Tw_out_C, thermal_power_W=thermal_power_W, delta_T=delta_T), 'Tw_out_C': Tw_out_C, 'radiative_power_ratio': self.radiative_power_ratio(Tw_out_C, thermal_power_W), 'water_mass_flow_rate_kg_per_s': water_mass_flow_rate_kg_per_s, 'Tindoor_C': Tw_out_C}

    def display(self, Tw_out_C: float, thermal_power_W: float, water_mass_flow_rate_kg_per_s: float, delta_T: float, display: bool = False) -> None:
        """Print debug information for the radiator."""
        if display:
            print(self, f"\t____\n\tinlet_water: {self.Tw_in_C(Tw_out_C, thermal_power_W, delta_T):.2f}°C\n\toutlet_water: {Tw_out_C:.2f}°C\n\theating surface temperature: {self.Tsa_C(Tw_out_C, thermal_power_W):.2f}°C\n\tmass flow rate: {water_mass_flow_rate_kg_per_s:.2f}kg/s\n\tradiative power ratio: {self.radiative_power_ratio(Tw_out_C, thermal_power_W)*100:.0f}%")


class HorizontalRadiator(WaterRadiator):
    """Horizontal water radiator implementation.

    Inherits from WaterRadiator and provides specific initialization for
    horizontal radiator orientation.
    """

    def __init__(self, radiator_surface_m2: float, thickness_m: float, material: str,  T_indoor: float = 20, T_surface_C: float = 40, display: bool = False) -> float:
        """Initialize horizontal radiator.

        :param radiator_surface_m2: Surface area of the radiator in square meters
        :type radiator_surface_m2: float
        :param thickness_m: Thickness of the radiator material in meters
        :type thickness_m: float
        :param material: Material of the radiator (e.g., 'copper', 'aluminum')
        :type material: str
        :param T_indoor: Indoor temperature for heat transfer calculations, defaults to 20
        :type T_indoor: float, optional
        :param T_surface_C: Surface temperature for heat transfer calculations, defaults to 40
        :type T_surface_C: float, optional
        :param display: Print debug information, defaults to False
        :type display: bool, optional
        """
        super().__init__(radiator_surface_m2, radiator_length_m=None, thickness_m=thickness_m, material=material, direction='horizontal', typical_Tindoor_C=T_indoor, typical_Tsurface_C=T_surface_C)


class VerticalRadiator(WaterRadiator):
    """Vertical water radiator implementation.

    Inherits from WaterRadiator and provides specific initialization for
    vertical radiator orientation.
    """

    def __init__(self, radiator_surface_m2: float, radiator_height_m: float, thickness_m: float, material: str, T_indoor_C: float = 20, T_surface_C: float = 40, display: bool = False) -> float:
        """Initialize vertical radiator.

        :param radiator_surface_m2: Surface area of the radiator in square meters
        :type radiator_surface_m2: float
        :param radiator_height_m: Height of the radiator in meters
        :type radiator_height_m: float
        :param thickness_m: Thickness of the radiator material in meters
        :type thickness_m: float
        :param material: Material of the radiator (e.g., 'copper', 'aluminum')
        :type material: str
        :param T_indoor_C: Indoor temperature for heat transfer calculations, defaults to 20
        :type T_indoor_C: float, optional
        :param T_surface_C: Surface temperature for heat transfer calculations, defaults to 40
        :type T_surface_C: float, optional
        :param display: Print debug information, defaults to False
        :type display: bool, optional
        """
        super().__init__(radiator_surface_m2, radiator_length_m=radiator_height_m, thickness_m=thickness_m, material=material, direction='vertical', typical_Tindoor_C=T_indoor_C, typical_Tsurface_C=T_surface_C)


class HeatPumpRadiator:
    """Combined heat pump and radiator system model.

    This class models the interaction between a heat pump and a water radiator,
    including the refrigerant cycle and heat transfer across the system.

    Attributes:
        heat_pump: Heat pump object for thermodynamic calculations
        radiator: Water radiator object for heat transfer calculations
        pinch_temperature_C: Temperature difference across the radiator for heat transfer, defaults to 2
    """

    def __init__(self, heat_pump: HeatPump, radiator: WaterRadiator, pinch_temperature_C: float = 2) -> None:
        """Initialize heat pump radiator system.

        :param heat_pump: Heat pump object
        :type heat_pump: HeatPump
        :param radiator: Water radiator object
        :type radiator: WaterRadiator
        :param pinch_temperature_C: Temperature difference across the radiator for heat transfer, defaults to 2
        :type pinch_temperature_C: float, optional
        """
        self.heat_pump: HeatPump = heat_pump
        self.radiator: WaterRadiator = radiator
        self.pinch_temperature_C: float = pinch_temperature_C

    def solve(self, mode: str, Tindoor_C: float, Toutdoor_C: float, thermal_power_W: float, display: bool = False) -> dict[str, float]:
        """Solve the combined system for a given mode and thermal power.

        Determines the operating mode, updates radiator and heat pump properties,
        and calculates the COP and power outputs.

        :param mode: Operating mode ('heating', 'cooling', 'auto')
        :type mode: str
        :param Tindoor_C: Indoor temperature in Celsius
        :type Tindoor_C: float
        :param Toutdoor_C: Outdoor temperature in Celsius
        :type Toutdoor_C: float
        :param thermal_power_W: Thermal power output/input in Watts
        :type thermal_power_W: float
        :returns: Dictionary containing COP, power outputs, and temperatures
        :rtype: dict
        """
        if mode.lower() == 'auto':
            if thermal_power_W >= 0:
                mode = 'heating'
            else:
                mode = 'cooling'
        self.radiator.set_indoor_temperature(Tindoor_C)
        if mode.lower() == 'heating':
            Tw_out_C = Tindoor_C + self.pinch_temperature_C
            radiator_result: dict[str, float] = self.radiator.solve(Tw_out_C=Tw_out_C, thermal_power_W=thermal_power_W, display=display)
            heatpump_result: dict[str, float] = self.heat_pump.solve(mode='heating', Tcold_C=Toutdoor_C, Thot_C=radiator_result['Tw_in_C'], demanded_thermal_power_W=thermal_power_W, display=display)
        elif mode.lower() == 'cooling':
            Tw_out_C = Tindoor_C - self.pinch_temperature_C
            radiator_result: dict[str, float] = self.radiator.solve(Tw_out_C=Tw_out_C, thermal_power_W=thermal_power_W, display=display)
            heatpump_result: dict[str, float] = self.heat_pump.solve(mode='cooling', Tcold_C=radiator_result['Tw_in_C'], Thot_C=Toutdoor_C, demanded_thermal_power_W=thermal_power_W, display=display)
        else:
            raise ValueError(f"Mode must be 'heating' or 'cooling', not {mode}")

        return heatpump_result | radiator_result

    def __str__(self) -> str:
        """String representation of the heat pump radiator system."""
        return f"HEAT PUMP with RADIATOR:\n{self.heat_pump}\n{self.radiator}"
