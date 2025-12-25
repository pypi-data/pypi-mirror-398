"""Building state model and time-varying state space modeling module for building energy analysis.

.. module:: batem.core.model

This module provides comprehensive tools for designing and implementing time-varying
state space models for building energy analysis, approximated by bilinear state space
models. It includes building thermal network modeling, parameter fitting, simulation
capabilities, and model optimization for building energy systems.

Classes
-------

.. autosummary::
   :toctree: generated/

   ModelMaker
   TimeVaryingStateModelSimulator
   ModelFitter

Classes Description
-------------------

**ModelMaker**
    Builder class for creating building state models from thermal networks.

**TimeVaryingStateModelSimulator**
    Main class for time-varying state space model management and simulation.

**ModelFitter**
    Parameter fitting and optimization class for model calibration.

Key Features
------------

* Time-varying state space model design with bilinear approximations
* Building thermal network modeling with RC circuit representations
* Parameter fitting and optimization using Morris sensitivity analysis
* Parallel model caching and simulation for performance optimization
* Multi-zone building modeling with airflow and CO2 concentration tracking
* State model order reduction and model simplification capabilities
* Integration with building energy data providers and measurement systems
* Support for adjustable parameters and parameter sensitivity analysis
* Model validation and error assessment with training data
* Visualization tools for model performance and parameter analysis

The module is designed for building energy analysis, thermal modeling, and
comprehensive building performance evaluation in research and practice.

.. note::
    This module requires numpy, networkx, and SALib for parameter sensitivity analysis.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""
from __future__ import annotations
from numpy import matrix

import numpy
import networkx
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from batem.core.components import Side, Zone, Airflow, LayeredWallSide
from batem.core.thermal import ThermalNetworkMaker
from batem.core.thermal import ThermalNetwork
from batem.core.statemodel import StateModel
from batem.core.data import DataProvider
from batem.core.library import ZONE_TYPES, properties, Setup
import numpy.linalg
import time
import prettytable
import SALib.sample.morris
import SALib.analyze.morris
import plotly.express
from random import randint
from batem.core.data import ParameterSet


class _CoreModelMaker(ThermalNetworkMaker):
    """Builder class for creating building state models from thermal networks.

    This class extends ThermalNetworkMaker to provide comprehensive building state model
    creation capabilities. It handles thermal network processing, state space model
    generation, parameter management, and model optimization for building energy analysis.
    """

    def __init__(self, *zone_names: str, data_provider: DataProvider, periodic_depth_seconds: float = 60*60, state_model_order_max: int = None, ignore_co2: bool = False):
        """
        Initialize a building and help to create it. It generates as state model afterwards thanks to the method 'make_state_model()', that must be called anytime an adjustment multiplicative factor is modified

        :param zone_names: names of the zones except for 'outdoor', which is automatically created
        :type zone_names: tuple[str]
        :param periodic_depth_seconds: the target periodic depth penetration is a wave length, which is defining the decomposition in sublayers, each sublayer is decomposed such that its thickness is attenuating a temperature of this wave length: the smallest, the more precise but also the more computation time.
        :type periodic_depth_seconds:
        :param state_model_order_max: set a maximum order for the final state model. If the value is set to None, there won't be order reduction, default to None
        :type state_model_order_max: int, optional
        :param ignore_co2: if True, CO2 differential equation will be ignored in the state model, default to False
        :type ignore_co2: bool, optional
        :param sample_time_in_secs: sample time for future version (only the default 3600s has been tested), default is 3600s, don't change it
        :type sample_time_in_secs: int, optional
        """
        super().__init__(*zone_names, periodic_depth_seconds=periodic_depth_seconds, data_provider=data_provider)
        self.dp: DataProvider = data_provider
        self.__data_names_in_fingerprint = list()
        self.data_names_in_fingerprint: list[str] = data_provider.parameter_set.adjustable_parameter_names
        self.airflow_network: networkx.Graph = networkx.Graph()
        for zone_name in self.name_zones:
            self.airflow_network.add_node(zone_name)
        self.V_nominal_reduction_matrix: numpy.matrix = None
        self.W_nominal_reduction_matrix: numpy.matrix = None
        self.nominal_fingerprint: int = None
        self.airflows: list[Airflow] = list()
        self.airflow_names: list[str] = list()
        self.CO2_connected_zones = list()
        self.state_model_order_max: int = state_model_order_max
        self.ignore_co2: bool = ignore_co2
        # Reset reduction matrices when CO2 is ignored to avoid dimension mismatches
        if self.ignore_co2:
            self.V_nominal_reduction_matrix = None
            self.W_nominal_reduction_matrix = None

    @property
    def data_names_in_fingerprint(self) -> list[str]:
        """
        Get the list of data names used in fingerprint generation

        :return: list of data names included in the fingerprint
        :rtype: list[str]
        """
        return self.__data_names_in_fingerprint

    @data_names_in_fingerprint.setter
    def data_names_in_fingerprint(self, data_names: list[str]) -> None:
        """
        Set the data names to be included in fingerprint generation

        :param data_names: single data name or list of data names to include in fingerprint
        :type data_names: list[str] or str
        """
        if type(data_names) is str:
            data_names = [data_names]
        for data_name in data_names:
            if data_name not in self.data_names_in_fingerprint:
                self.__data_names_in_fingerprint.append(data_name)
            if data_name not in self.dp.data_names_in_fingerprint:
                self.dp.data_names_in_fingerprint.append(data_name)

    def make_side(self, side_factory: Side) -> None:
        """
        Create a layered wall side from a side factory object

        :param side_factory: side factory object containing zone names, side type, surface area and layer specifications
        :type side_factory: Side
        """
        side: LayeredWallSide = self.layered_wall_side(side_factory.zone1_name, side_factory.zone2_name, side_factory.side_type, side_factory.surface)
        for layer in side_factory.layers:
            side.layer(*layer)

    def connect_airflow(self, zone1_name: str, zone2_name: str, nominal_value: float = None):
        """
        create an airflow exchange between 2 zones

        :param zone1_name: zone name of the origin of the air flow
        :type zone1_name: str
        :param zone2_name: zone name of the destination of the air flow
        :type zone2_name: str
        :param nominal_value: nominal value for air exchange, used if not overloaded
        :type nominal_value: float
        """
        if zone1_name > zone2_name:
            zone1_name, zone2_name = zone2_name, zone1_name
        self.airflow_network.add_edge(zone1_name, zone2_name)
        if nominal_value is None:
            nominal_value: float | None = self.data_provider(f'Q:{zone1_name}-{zone2_name}', 0)
        airflow: Airflow = Airflow(self.name_zones[zone1_name], self.name_zones[zone2_name], nominal_value)
        self.airflows.append(airflow)
        self.airflow_names.append(airflow.name)
        try:
            self.dp.add_data_names_in_fingerprint(airflow.name)
        except Exception:
            pass
        if airflow.name not in self.dp:
            try:
                base_value = nominal_value if nominal_value is not None else 0.0
                default_series = [base_value for _ in self.dp.ks]
                self.dp.add_var(airflow.name, default_series)
                if hasattr(self.dp, 'independent_variable_set'):
                    lower = base_value
                    upper = base_value
                    if upper - lower == 0.0:
                        upper = lower + 1e-6
                    self.dp.independent_variable_set.variable_bounds[airflow.name] = (lower, upper)
            except Exception:
                # If we cannot add the variable (e.g., dp is partially configured), skip silently
                pass
        if self.name_zones[zone1_name].simulated or self.name_zones[zone2_name].simulated:
            if airflow.name in self.data_provider.variable_accessor_registry.parameterized_variable_accessor:
                dependent_data = self.data_provider.variable_accessor_registry.required_data(airflow.name)
                for data in dependent_data:
                    self.data_names_in_fingerprint = data.name

        if self.name_zones[zone1_name] not in self.CO2_connected_zones:
            self.CO2_connected_zones.append(self.name_zones[zone1_name])
        if self.name_zones[zone2_name] not in self.CO2_connected_zones:
            self.CO2_connected_zones.append(self.name_zones[zone2_name])

    # def make_state_model_nominal(self) -> StateModel:
    #     """
    #     Compile and initialize the nominal state model with input and output names

    #     :return: compiled nominal state model
    #     :rtype: StateModel
    #     """
    #     self.nominal_state_model: StateModel = self.make_state_model_k(k=None, reset_reduction=True, fingerprint=0)
    #     self.input_names: list[str] = self.nominal_state_model.input_names
    #     self.output_names: list[str] = self.nominal_state_model.output_names

    def make_k(self, k: int | None = None, reset_reduction: bool = False, fingerprint: int | list | tuple | str = 0) -> StateModel:  # current_airflow_values: dict[str, float] = dict(),
        """
        Generate state model at time step k with optional order reduction

        :param k: time step index, None for nominal model, defaults to None
        :type k: int or None, optional
        :param reset_reduction: if True, reset reduction matrices before computation, defaults to False
        :type reset_reduction: bool, optional
        :param fingerprint: fingerprint identifier for model caching, defaults to 0
        :type fingerprint: int, optional
        :return: state space model at time step k with optional order reduction
        :rtype: StateModel
        """
        nominal: bool = k is None
        cache_key = self._fingerprint_key(fingerprint)
        if not reset_reduction and cache_key in self.state_models_cache:
            cached_model = self.state_models_cache.get(cache_key)
            if cached_model is not None:
                return cached_model
        if self.state_model_order_max is not None:
            if reset_reduction:
                self.V_nominal_reduction_matrix = None
                self.W_nominal_reduction_matrix = None
            if nominal:
                self.global_state_model: StateModel = self.__make_full_order_state_model_k(k=None, fingerprint=cache_key)
                self.V_nominal_reduction_matrix, self.W_nominal_reduction_matrix = self.global_state_model.reduce(
                    self.state_model_order_max, self.V_nominal_reduction_matrix, self.W_nominal_reduction_matrix)
                self.state_models_cache[cache_key] = self.global_state_model
                return self.global_state_model

        if self.state_model_order_max is not None and self.V_nominal_reduction_matrix is None:
            self.global_state_model = self.__make_full_order_state_model_k(k, fingerprint=cache_key)
            self.V_nominal_reduction_matrix, self.W_nominal_reduction_matrix = self.global_state_model.reduce(
                self.state_model_order_max, self.V_nominal_reduction_matrix, self.W_nominal_reduction_matrix)
        self.global_state_model = self.__make_full_order_state_model_k(k, fingerprint=cache_key)
        if self.state_model_order_max is not None:
            # Force recomputation of reduction matrices when CO2 is ignored
            if self.ignore_co2:
                self.V_nominal_reduction_matrix = None
                self.W_nominal_reduction_matrix = None
            self.V_nominal_reduction_matrix, self.W_nominal_reduction_matrix = self.global_state_model.reduce(
                self.state_model_order_max, self.V_nominal_reduction_matrix, self.W_nominal_reduction_matrix)
        self.state_models_cache[cache_key] = self.global_state_model
        return self.global_state_model

    def __make_full_order_state_model_k(self, k: int, fingerprint: int = None) -> StateModel:  # nominal: bool = False,
        """
        Generate full-order state model at time step k without order reduction

        :param k: time step index, None for nominal model
        :type k: int or None
        :param fingerprint: fingerprint identifier for model caching, defaults to None
        :type fingerprint: int, optional
        :return: full-order state space model including thermal and CO2 dynamics
        :rtype: StateModel
        """
        nominal = k is None

        self.thermal_network: ThermalNetwork = self.make_thermal_network_k(fingerprint=fingerprint)
        air_properties: dict[str, float] = properties.get('air')
        rhoCp_air: float = air_properties['density'] * air_properties['Cp']
        
        # Get heat recovery efficiency (default to 0 if not set, meaning no heat recovery)
        # Clamp to [0, 0.99] to avoid division by zero (1.0 would mean perfect recovery with no heat loss)
        # Read with time index k if available (for time-varying efficiency), otherwise read as parameter
        if 'ventilation_heat_recovery_efficiency' in self.data_provider:
            if k is not None:
                # Try to read as time series variable with index k
                try:
                    heat_recovery_efficiency_raw: float = self.data_provider('ventilation_heat_recovery_efficiency', k)
                except Exception:
                    # If reading with k fails, try without k (parameter)
                    heat_recovery_efficiency_raw: float = self.data_provider('ventilation_heat_recovery_efficiency')
            else:
                # Nominal model: read as parameter
                heat_recovery_efficiency_raw: float = self.data_provider('ventilation_heat_recovery_efficiency')
        else:
            heat_recovery_efficiency_raw: float = 0.0
        heat_recovery_efficiency: float = min(max(heat_recovery_efficiency_raw, 0.0), 0.99)
        
        for airflow in self.airflows:
            zone1, zone2 = airflow.connected_zones
            # Check if this is a zone-to-outdoor connection (dual ventilation with heat recovery)
            is_zone_outdoor_connection: bool = (zone1.name == 'outdoor' or zone2.name == 'outdoor')
            
            if not nominal:
                # Use dynamic airflow value when available
                airflow_value: float = self.data_provider(airflow.name, k) if airflow.name in self.data_provider else airflow.nominal_value
                
                # Get floor-specific heat recovery efficiency if available
                # Extract zone name (the non-outdoor zone)
                zone_name = zone1.name if zone1.name != 'outdoor' else zone2.name
                
                # Try to read floor-specific efficiency with common suffixes, fall back to global efficiency
                floor_heat_recovery_efficiency = heat_recovery_efficiency
                recovery_var_names = [
                    f'RECOV:{zone_name}#sim',  # Try with #sim suffix first (most common)
                    f'RECOV:{zone_name}',      # Try without suffix for backward compatibility
                ]
                
                for recovery_var_name in recovery_var_names:
                    if recovery_var_name in self.data_provider:
                        try:
                            if k is not None:
                                # Read time series value at time step k
                                floor_heat_recovery_efficiency_raw = self.data_provider(recovery_var_name, k)
                                floor_heat_recovery_efficiency = min(max(floor_heat_recovery_efficiency_raw, 0.0), 0.99)
                            else:
                                # Nominal model: use first value from time series or parameter value
                                floor_heat_recovery_efficiency_raw = self.data_provider(recovery_var_name, 0)
                                if isinstance(floor_heat_recovery_efficiency_raw, list):
                                    floor_heat_recovery_efficiency_raw = floor_heat_recovery_efficiency_raw[0] if floor_heat_recovery_efficiency_raw else heat_recovery_efficiency
                                floor_heat_recovery_efficiency = min(max(floor_heat_recovery_efficiency_raw, 0.0), 0.99)
                            break  # Successfully read, no need to try other names
                        except Exception:
                            continue  # Try next variable name
                
                # Apply heat recovery efficiency: effective resistance is increased by 1/(1-η)
                # This reduces heat loss through ventilation by factor (1-η)
                if is_zone_outdoor_connection and floor_heat_recovery_efficiency > 0:
                    # With heat recovery, effective heat loss is reduced: Q_loss = ρCp * Q * (1-η) * ΔT
                    # So effective resistance is: R = 1 / (ρCp * Q * (1-η))
                    effective_resistance: float = 1 / (rhoCp_air * airflow_value * (1 - floor_heat_recovery_efficiency))
                else:
                    # No heat recovery: standard resistance
                    effective_resistance: float = 1 / (rhoCp_air * airflow_value)
                
                self.thermal_network.R(
                    fromT=zone1.air_temperature_name,
                    toT=zone2.air_temperature_name,
                    name='Rv%s_%s' % (zone1.name, zone2.name),
                    val=effective_resistance
                )
            else:
                # Nominal branch
                if is_zone_outdoor_connection and heat_recovery_efficiency > 0:
                    # Apply heat recovery to nominal value
                    effective_resistance: float = 1 / (rhoCp_air * airflow.nominal_value * (1 - heat_recovery_efficiency))
                else:
                    # Standard resistance
                    effective_resistance: float = 1 / (rhoCp_air * airflow.nominal_value)
                
                self.thermal_network.R(
                    fromT=zone1.air_temperature_name,
                    toT=zone2.air_temperature_name,
                    name='Rv%s_%s' % (zone1.name, zone2.name),
                    val=effective_resistance
                )

        full_order_state_model = self.thermal_network.state_model()

        # Only include CO2 differential equation if not ignored
        if not self.ignore_co2:
            CO2state_matrices = self.make_CO2_k(k)
            A_CO2 = CO2state_matrices['A']
            B_CO2 = numpy.hstack((CO2state_matrices['B_CO2'], CO2state_matrices['B_prod']))
            C_CO2 = CO2state_matrices['C']
            D_CO2 = numpy.hstack((CO2state_matrices['D_CO2'], CO2state_matrices['D_prod']))
            input_names = CO2state_matrices['U_CO2']
            input_names.extend(CO2state_matrices['U_prod'])
            output_names = CO2state_matrices['Y']
            full_order_state_model.extend('CO2', (A_CO2, B_CO2, C_CO2, D_CO2), input_names, output_names)

        full_order_state_model.fingerprint = fingerprint
        return full_order_state_model

    def make_CO2_k(self, k: int = 0, nominal: bool = False) -> dict:  # airflow_values: dict[str, float]
        """
        Generate the state model representing the CO2 evolution

        :param airflow_values: connecting airflows values as a dictionary with the airflow names as keys and the values as airflow values
        :type airflow_values: dict[str, float]
        :param zone_Vfactors: multiplicative adjustment factors for the zone air volumes as a dictionary with zone names as keys and corrective factor as value, default to empty dictionary
        :type zone_Vfactors: dict[str, float], optional
        :return: State space model for the CO2
        :rtype: STATE_MODEL
        """
        simulated_zones = list()
        input_zones = list()
        state_variable_names: list[str] = list()
        input_variable_names: list[str] = list()
        production_names: list[str] = list()
        if k is None:
            k = 0

        for zone_name in self.name_zones:
            zone: Zone = self.name_zones[zone_name]
            if zone.simulated:
                simulated_zones.append(zone)
                state_variable_names.append(zone.CO2_concentration_name)
                production_names.append(zone.CO2_production_name)
            elif len(zone.connected_zones) > 0:
                input_zones.append(zone)
                input_variable_names.append(zone.CO2_concentration_name)

        A_CO2 = numpy.zeros((len(state_variable_names), len(state_variable_names)))
        B_CO2 = numpy.zeros((len(state_variable_names), len(input_variable_names)))
        B_prod = numpy.zeros((len(state_variable_names), len(production_names)))
        C_CO2 = numpy.eye(len(state_variable_names))
        D_CO2 = numpy.zeros((len(state_variable_names), len(input_variable_names)))
        D_prod = numpy.zeros((len(state_variable_names), len(production_names)))

        for i, zone in enumerate(simulated_zones):
            A_CO2[i, i] = 0
            for connecting_airflow in zone.connected_airflows:
                if not nominal and connecting_airflow.name in self.data_provider:
                    A_CO2[i, i] += -self.data_provider(connecting_airflow.name, k) / zone.volume
                else:
                    A_CO2[i, i] += -connecting_airflow.nominal_value / zone.volume
            B_prod[i, i] = 1/zone.volume  # Each zone gets its own CO2 production, not production from zone 0
            for connected_zone in zone.connected_zones:
                if connected_zone.simulated:
                    connecting_airflow = zone._airflow(connected_zone)
                    j: int = state_variable_names.index(connected_zone.CO2_concentration_name)
                    if not nominal and connecting_airflow.name in self.data_provider:
                        A_CO2[i, j] = self.data_provider(connecting_airflow.name, k) / zone.volume
                    else:
                        A_CO2[i, j] = connecting_airflow.nominal_value / zone.volume
                else:
                    connecting_airflow = zone._airflow(connected_zone)
                    j = input_variable_names.index(connected_zone.CO2_concentration_name)
                    if not nominal and connecting_airflow.name in self.data_provider:
                        B_CO2[i, j] = self.data_provider(connecting_airflow.name, k) / zone.volume
                    else:
                        B_CO2[i, j] = connecting_airflow.nominal_value / zone.volume

        self.CO2_state_model = StateModel((A_CO2, B_CO2, C_CO2, D_CO2), input_variable_names, state_variable_names, self.sample_time_seconds)
        return {'A': A_CO2, 'B_CO2': B_CO2, 'B_prod': B_prod, 'C': C_CO2, 'D_CO2': D_CO2, 'D_prod': D_prod, 'Y': state_variable_names, 'X': state_variable_names, 'U_CO2': input_variable_names, 'U_prod': production_names, 'type': 'differential'}

    def plot_thermal_net(self):
        """
        draw digraph of the thermal network (use matplotlib.show() to display)
        """
        self.thermal_network.draw()

    def plot_airflow_net(self):
        """
        draw digraph of the airflow network (use matplotlib.show() to display)
        """

        pos = networkx.shell_layout(self.airflow_network)
        node_colors = list()
        for zone_name in self.zones:
            if self.zones[zone_name].is_known:
                node_colors.append('blue')
            elif self.zones[zone_name].simulated:
                node_colors.append('pink')
            else:
                node_colors.append('yellow')
        labels = dict()
        for node in self.airflow_network.nodes:
            label = '\n' + str(self.zones[node]._propagated_airflow)
            labels[node] = label
        plt.figure()
        networkx.draw(self.airflow_network, pos, with_labels=True, edge_color='black', width=1, linewidths=1, node_size=500, font_size='medium', node_color=node_colors, alpha=1)
        networkx.drawing.draw_networkx_labels(self, pos,  font_size='x-small', verticalalignment='top', labels=labels)

    def features_as_string(self) -> str:
        string = str(super().__str__())
        string += 'Connected zones:\n'
        rho_air = 1.2  # kg/m3
        cp_air = 1006  # J/kg.K
        for airflow in self.airflows:
            air_flow_m3_s = airflow.nominal_value  # m3/s
            heat_loss_W = rho_air * air_flow_m3_s * cp_air  # W/K
            string += '* %s with a nominal value of %.2fm3/h (heat loss: %.2fW/K)\n' % (str(airflow), 3600 * airflow.nominal_value, heat_loss_W)
        return string

    def __str__(self) -> str:
        """
        :return: string depicting the site
        :rtype: str
        """
        return self.features_as_string()

    def copy(self, periodic_depth_seconds: float = None, state_model_order_max: int = None) -> _CoreModelMaker:
        """
        Create a twin copy of the building state model maker with same configuration

        :param periodic_depth_seconds: periodic depth penetration for sublayer decomposition, defaults to current value
        :type periodic_depth_seconds: float, optional
        :param state_model_order_max: maximum order for state model reduction, defaults to current value
        :type state_model_order_max: int, optional
        :return: twin building state model maker with copied configuration
        :rtype: BuildingStateModelMaker
        """
        if periodic_depth_seconds is None:
            periodic_depth_seconds: float = self.periodic_depth_seconds
        if state_model_order_max is None:
            self.state_model_order_max = self.state_model_order_max
        twin: _CoreModelMaker = _CoreModelMaker(*self.zone_names, periodic_depth_seconds=periodic_depth_seconds, state_model_order_max=state_model_order_max, data_provider=self.data_provider)

        twin.layered_wall_sides = self.layered_wall_sides
        twin.block_wall_sides = self.block_wall_sides

        for airflow in self.airflows:
            twin.connect_airflow(airflow.connected_zones[0].name, airflow.connected_zones[1].name, airflow.nominal_value)
        simulated_zone_names: list[str] = list()
        for zone_name in self.name_zones:
            if self.name_zones[zone_name].zone_type == ZONE_TYPES.SIMULATED:
                simulated_zone_names.append(zone_name)
        twin.zones_to_simulate(*simulated_zone_names)
        return twin


class ModelMaker(_CoreModelMaker):
    """Main class for time-varying state space model management and simulation.

    This class manages time-varying state space models generated from RC thermal networks
    and building physics. It provides discrete-time recurrent nonlinear state model
    capabilities, variable organization by type and kind, and comprehensive simulation
    functionality for building energy analysis with temperature, heat gain, and CO2
    concentration tracking.
    """

    def __init__(self, data_provider: DataProvider, periodic_depth_seconds: float = 60*60, state_model_order_max: int = None, ignore_co2: bool = False, **zones_volumes: dict[str, float], ) -> None:
        """
        Initialize time-varying state model simulator with building state model maker

        :param building_state_model_maker: building state model maker instance for generating state models
        :type building_state_model_maker: BuildingStateModelMaker
        """
        super().__init__(*zones_volumes.keys(), data_provider=data_provider, periodic_depth_seconds=periodic_depth_seconds, state_model_order_max=state_model_order_max, ignore_co2=ignore_co2)
        self.dp: DataProvider = self.data_provider
        self.zone_names_volumes: dict[str, float] = zones_volumes
        self.zones_to_simulate(zones_volumes)
        if len(self.airflows) > 0:
            self.dp.add_data_names_in_fingerprint(*[airflow.name for airflow in self.airflows])
        self.nominal_fingerprint: str | tuple | int = 'nominal'
        self.state_models_cache: dict[int | str | tuple, StateModel] = {}
        self.nominal_state_model: StateModel | None = None
        self.input_names: list[str] = []
        self.output_names: list[str] = []
        # Don't cache the initial incomplete model - will be properly built on first access
        self.counter: int = 0
        
    def copy(self, data_provider: DataProvider = None, periodic_depth_seconds: float = None, state_model_order_max: int = None) -> ModelMaker:
        """
        Create a twin copy of the model maker with same configuration
        
        :param data_provider: data provider for the new model maker, defaults to current one
        :param periodic_depth_seconds: periodic depth penetration, defaults to current value
        :param state_model_order_max: maximum state model order, defaults to current value
        :return: twin model maker with copied configuration
        """
        if data_provider is None:
            data_provider: DataProvider = self.dp
        if periodic_depth_seconds is None:
            periodic_depth_seconds: float = self.periodic_depth_seconds
        if state_model_order_max is None:
            state_model_order_max: int = self.state_model_order_max
        
        # Create new ModelMaker instance with same zone configuration
        twin: ModelMaker = ModelMaker(data_provider=data_provider, periodic_depth_seconds=periodic_depth_seconds, state_model_order_max=state_model_order_max, ignore_co2=self.ignore_co2, **self.zone_names_volumes)
        
        # Copy thermal network configuration
        twin.layered_wall_sides = self.layered_wall_sides
        twin.block_wall_sides = self.block_wall_sides
        
        # Copy airflows
        for airflow in self.airflows:
            twin.connect_airflow(airflow.connected_zones[0].name, airflow.connected_zones[1].name, airflow.nominal_value)
        
        return twin

    @staticmethod
    def _fingerprint_key(fingerprint):
        if fingerprint is None:
            return 'nominal'
        if isinstance(fingerprint, list):
            return tuple(fingerprint)
        return fingerprint
    
    def update(self, clear_cache: bool = False) -> None:
        """
        Remake the model
        """
        if clear_cache:
            self.state_models_cache.clear()  # Clear cache
        self.nominal_state_model = self.make_k(k=None, reset_reduction=True, fingerprint=self.nominal_fingerprint)
        self.state_models_cache[self.nominal_fingerprint] = self.nominal_state_model
        self.input_names = self.nominal_state_model.input_names
        self.output_names = self.nominal_state_model.output_names

    @property
    def nominal(self) -> StateModel:
        """
        Get the nominal state space model
        
        :return: Nominal state model with default parameters
        :rtype: StateModel
        """
        # Check cache first to avoid unnecessary recomputation
        if self.nominal_fingerprint in self.state_models_cache:
            model = self.state_models_cache[self.nominal_fingerprint]
        else:
            # Build and cache the nominal model lazily once geometry and airflows are configured
            model = self.make_k(k=None, reset_reduction=False, fingerprint=self.nominal_fingerprint)
            self.state_models_cache[self.nominal_fingerprint] = model
        if self.nominal_state_model is not model:
            self.nominal_state_model = model
            self.input_names = model.input_names
            self.output_names = model.output_names
        return model

    @property
    def inputs(self) -> list[str]:
        """
        Get the input names of the state model
        
        :return: List of input variable names
        :rtype: list[str]
        """
        return self.nominal.input_names

    @property
    def outputs(self) -> list[str]:
        """
        Get the output names of the state model
        
        :return: List of output variable names
        :rtype: list[str]
        """
        return self.nominal.output_names

    @property
    def is_time_varying(self) -> bool:
        """
        Check if the state model varies with time
        
        :return: True if model changes with time (time-varying), False if constant (time-invariant)
        :rtype: bool
        """
        if len(self.airflows) == 0:
            return False  # No airflows means no time-varying behavior
        
        # Check if any airflow values change over time
        if len(self.dp) < 2:
            return False  # Need at least 2 time steps to check
        
        # Sample multiple time steps to check for variations
        # Check at 0, 25%, 50%, 75%, and 100% of the time series
        n = len(self.dp)
        sample_indices = [0, n // 4, n // 2, 3 * n // 4, n - 1]
        fingerprints = [self.dp.fingerprint(k) for k in sample_indices]
        
        # If all fingerprints are the same, model is time-invariant
        return len(set(fingerprints)) > 1

    def time_k(self, k: int) -> StateModel:
        """
        Get the state model at time index k
        
        :param k: Time index
        :type k: int
        :return: State model at time k with time-varying parameters
        :rtype: StateModel
        """
        fingerprint = self.dp.fingerprint(k)
        if fingerprint in self.state_models_cache:
            return self.state_models_cache[fingerprint]
        else:
            model = self.make_k(k, reset_reduction=False, fingerprint=fingerprint)
            self.state_models_cache[fingerprint] = model
            return model

    def clear_cache(self):
        """
        Clear the state model cache, keeping only the nominal state model
        """
        nominal = self.nominal  # Ensure nominal is cached
        self.state_models_cache: dict[int | str | tuple, StateModel] = {self.nominal_fingerprint: nominal}

    def cache_state_models(self, timeout: float = None):
        """
        Pre-compute and cache all state models for different fingerprints using parallel processing

        :param timeout: Maximum time in seconds to wait for workers to complete. If None, uses environment
                        variable JOBLIB_TIMEOUT or default 3600s (1 hour). Increase this value if you get
                        worker timeout errors. To set via environment: export JOBLIB_TIMEOUT=7200
        :type timeout: float, optional
        """
        import os
        # Get timeout from parameter, environment variable, or use default (1 hour)
        if timeout is None:
            timeout = float(os.environ.get('JOBLIB_TIMEOUT', '3600'))
        
        print()
        delayed_calls = list()
        fingerprints_seen = {}  # Use dict to track seen fingerprints with their k values
        
        # Collect unique fingerprints
        for k in range(len(self.dp)):
            fingerprint: list[int] = self.dp.fingerprint(k)
            if fingerprint not in self.state_models_cache:
                fingerprint_key = tuple(fingerprint) if isinstance(fingerprint, list) else fingerprint
                if fingerprint_key not in fingerprints_seen:
                    fingerprints_seen[fingerprint_key] = k
                    delayed_calls.append(delayed(self.make_k)(k, fingerprint=fingerprint))
                    print('*', end='')
                    self.state_models_cache[fingerprint] = None
        
        print()
        if len(delayed_calls) > 0:
            # Configure parallel execution
            # Note: joblib's loky backend doesn't support direct timeout parameter
            # but you can increase worker timeout by setting environment variables:
            # - JOBLIB_TIMEOUT: overall timeout (used here for reference)
            # - LOKY_MAX_DURATION: maximum duration for loky workers (in seconds)
            # For very long computations, set: export LOKY_MAX_DURATION=7200  (2 hours)
            parallel_kwargs = {'n_jobs': -1}
            
            # Try to set timeout via backend_options if supported (joblib >= 1.2.0)
            try:
                # Some joblib versions support timeout in backend_options
                parallel_kwargs['backend_options'] = {'timeout': timeout}
            except (TypeError, KeyError):
                # Fallback: timeout not directly supported, rely on environment variables
                if timeout != 3600:  # Only warn if non-default timeout was requested
                    print(f"Note: Setting timeout via parameter not supported. Use environment variable:")
                    print(f"      export LOKY_MAX_DURATION={int(timeout)}  # for loky backend")
                    print(f"      or set JOBLIB_TIMEOUT={int(timeout)} for reference")
            
            results_delayed = Parallel(**parallel_kwargs)(delayed_calls)
            for state_model in results_delayed:
                if state_model is not None:
                    self.state_models_cache[state_model.fingerprint] = state_model
        
        # Remove any None entries from cache
        self.state_models_cache = {k: v for k, v in self.state_models_cache.items() if v is not None}
        print("\n%i models in cache" % len(self.state_models_cache))

    def simulate(self, suffix: str = '', data_provider: DataProvider = None, pre_cache: bool = True) -> dict[str, list[float]]:
        """
        Run time-varying state model simulation over the entire data provider time range

        :param pre_cache: if True, pre-compute all state models before simulation, defaults to True
        :type pre_cache: bool, optional
        :param suffix: suffix to append to output variable names (e.g., '#LN'), defaults to empty string
        :type suffix: str, optional
        :return: dictionary of simulated outputs with variable names as keys and time series as values
        :rtype: dict[str, list[float]]
        """
        if data_provider is None:
            data_provider: DataProvider = self.dp
        if suffix and not suffix.startswith('#'):
            suffix = '#' + suffix
        
        # Optimization: skip pre-caching if model is time-invariant
        if pre_cache and self.is_time_varying:
            self.cache_state_models()  # Timeout configured via environment variable or method parameter
        elif not self.is_time_varying:
            # For time-invariant models, just ensure nominal is cached
            _ = self.nominal
        simulated_outputs: dict[str, list[float]] = dict()
        X: matrix = None
        state_model_k = None
        current_fingerprint = -1  # Use -1 to ensure first iteration always creates model
        
        for k in range(len(data_provider)):
            fingerprint_k = data_provider.fingerprint(k)
            
            # Only retrieve/create state model if fingerprint changed
            if fingerprint_k != current_fingerprint:
                current_fingerprint = fingerprint_k
                if current_fingerprint in self.state_models_cache:
                    state_model_k = self.state_models_cache[current_fingerprint]
                    self.counter += 1
                    if self.counter % 10 == 0:
                        print('.', end='')
                else:
                    state_model_k: StateModel = self.make_k(k, reset_reduction=(k == 0))
                    self.state_models_cache[current_fingerprint] = state_model_k
                    print('*', end='')
            
            # Safety check - skip if state model is None
            if state_model_k is None:
                continue
            
            # Get inputs based on the actual state model's input names
            current_input_values: dict[str, float] = {}
            for input_name in state_model_k.input_names:
                try:
                    current_input_values[input_name] = data_provider(input_name, k)
                except (KeyError, ValueError):
                    current_input_values[input_name] = 0.0  # Default value for missing inputs
            
            if X is None:
                X: numpy.matrix = state_model_k.initialize(**current_input_values)
            state_model_k.set_state(X)
            output_values: list[float] = state_model_k.output(**current_input_values)
            for i, output_name in enumerate(state_model_k.output_names):
                output_key = output_name + suffix
                if output_key not in simulated_outputs:
                    simulated_outputs[output_key] = list()
                simulated_outputs[output_key].append(output_values[i])
            X: matrix = state_model_k.step(**current_input_values)
        
        # Add simulated outputs to data provider if suffix is provided
        if suffix:
            for var_name, values in simulated_outputs.items():
                data_provider.add_var(var_name, values)
        
        return simulated_outputs

    def __str__(self) -> str:
        """
        Generate string representation of the time-varying state model simulator

        :return: formatted string describing model variables and bindings
        :rtype: str
        """
        string: str = super().__str__()
        string += '\n=== State Model ===\n'
        string += str(self.nominal)
        string += '\n=== Inputs/Outputs ===\n'
        string += 'inputs: \n  %s\n' % (', '.join(self.inputs))
        string += 'outputs:\n  %s\n' % (', '.join(self.outputs))
        
        return string


def setup(*references):
    """Convenience wrapper around project configuration access."""
    return Setup.data(*references)


class ModelFitter:
    """Parameter fitting and optimization class for model calibration.

    This class provides comprehensive parameter fitting and optimization capabilities
    for building state models. It connects measurement data, parameters, and models
    to perform model calibration, parameter sensitivity analysis, and optimization
    for building energy analysis applications.
    """

    def __init__(self, building_state_model, verbose: bool = True) -> None:
        """
        Initialize model fitter with time-varying state model simulator

        :param building_state_model: time-varying state model simulator instance to fit
        :type building_state_model: TimeVaryingStateModelSimulator
        :param verbose: if True, print detailed fitting progress information, defaults to True
        :type verbose: bool, optional
        """

        self.varying_state_model = building_state_model
        self.dp = building_state_model.dp
        self.parameters: ParameterSet = self.dp.parameter_set
        self.verbose = verbose
        self.output_ranges: dict[str, float] = dict()

        self.adjustable_parameter_level_bounds: dict[str, tuple[int, int]] = self.parameters.adjustable_level_bounds
        # Store as list in the order of adjustable_parameter_names for easy access
        self.adjustable_parameter_levels: list[int] = [self.parameters.adjustable_parameter_levels[pname] for pname in self.parameters.adjustable_parameter_names]

    @property
    def training_data_provider(self):
        """
        Get the data provider used for training

        :return: data provider instance
        :rtype: DataProvider
        """
        return self.dp

    def run(self, pre_cache: bool = True, clear_cache: bool = False) -> dict[str, list[float]]:
        """
        Run simulation with current parameter settings

        :param pre_cache: if True, pre-compute all state models before simulation, defaults to True
        :type pre_cache: bool, optional
        :param clear_cache: if True, clear the cache before running, defaults to False
        :type clear_cache: bool, optional
        :return: dictionary of simulated outputs with variable names as keys and time series as values
        :rtype: dict[str, list[float]]
        """
        # Convert dict of parameter levels to list in the correct order
        level_list = [self.parameters.adjustable_parameter_levels[pname] for pname in self.parameters.adjustable_parameter_names]
        self.parameters.set_adjustable_levels(level_list)
        if clear_cache:
            self.varying_state_model.clear_cache()
        return self.varying_state_model.simulate(pre_cache=pre_cache)

    def error(self, output_values: dict[str, list[float]]) -> float:
        """
        Calculate normalized simulation error between output values and measured data

        :param output_values: dictionary of simulated output values with variable names as keys
        :type output_values: dict[str, list[float]]
        :return: normalized total error across all output variables
        :rtype: float
        """
        total_error: float = 0
        evaluated_outputs: int = 0
        for output_name, simulated_series in output_values.items():
            # output_name is the model output name (e.g., "TZ:office")
            # We need to get the corresponding measured data, which may be linked via bindings
            # The bindings link model names to data names (e.g., "TZ:office" -> "Toffice_reference_offset")
            try:
                # Try to get observed data using the model name - bindings should resolve it
                observed_series = self.dp.series(output_name)
            except Exception:
                # Skip outputs that are not available in the training data provider
                if self.verbose:
                    print(f"Warning: Could not find observed data for {output_name}, skipping from error calculation")
                continue

            series_length = min(len(simulated_series), len(observed_series), len(self.dp))
            if series_length == 0:
                continue

            if output_name not in self.output_ranges:
                observed_range = max(observed_series) - min(observed_series)
                if observed_range == 0 or observed_range is None:
                    observed_range = 1.0
                self.output_ranges[output_name] = observed_range

            output_error = 0.0
            for k in range(series_length):
                try:
                    # Use __call__ which respects bindings to get the measured value
                    observed_value = self.dp(output_name, k)
                except Exception:
                    observed_value = observed_series[k]
                output_error += abs(simulated_series[k] - observed_value)

            total_error += (output_error / series_length) / self.output_ranges[output_name]
            evaluated_outputs += 1

        if evaluated_outputs == 0:
            return 0.0

        total_error /= evaluated_outputs
        return total_error

    def error_analysis(self, output_values: dict[str, list[float]]) -> dict[str, dict[str, float]]:
        """
        Calculate detailed error analysis for each output variable showing both normalized and absolute errors

        :param output_values: dictionary of simulated output values with variable names as keys
        :type output_values: dict[str, list[float]]
        :return: dictionary with output names as keys and error metrics as values
        :rtype: dict[str, dict[str, float]]
        """
        error_details: dict[str, dict[str, float]] = {}
        
        for output_name, simulated_series in output_values.items():
            try:
                observed_series = self.dp.series(output_name)
            except Exception:
                continue

            series_length = min(len(simulated_series), len(observed_series), len(self.dp))
            if series_length == 0:
                continue

            # Calculate absolute errors
            absolute_errors = []
            for k in range(series_length):
                try:
                    observed_value = self.dp(output_name, k)
                except Exception:
                    observed_value = observed_series[k]
                absolute_errors.append(abs(simulated_series[k] - observed_value))

            # Calculate statistics
            mean_absolute_error = sum(absolute_errors) / len(absolute_errors)
            max_absolute_error = max(absolute_errors)
            min_absolute_error = min(absolute_errors)
            
            # Get range for normalization
            observed_range = self.output_ranges.get(output_name, max(observed_series) - min(observed_series))
            if observed_range == 0 or observed_range is None:
                observed_range = 1.0
            
            # Normalized error
            normalized_error = mean_absolute_error / observed_range
            
            # Calculate RMSE
            squared_errors = [e**2 for e in absolute_errors]
            rmse = (sum(squared_errors) / len(squared_errors)) ** 0.5
            
            error_details[output_name] = {
                'mean_absolute_error': mean_absolute_error,
                'normalized_error': normalized_error,
                'rmse': rmse,
                'max_error': max_absolute_error,
                'min_error': min_absolute_error,
                'observed_range': observed_range,
                'observed_mean': sum(observed_series[:series_length]) / series_length,
                'simulated_mean': sum(simulated_series[:series_length]) / series_length
            }
        
        return error_details

    def fit(self, n_iterations: int) -> tuple[dict[str, list[float]], float]:
        """
        Fit model parameters using randomized local search optimization

        :param n_iterations: maximum number of iterations for the fitting process
        :type n_iterations: int
        :return: tuple containing best parameter levels, best simulated outputs, and best error value
        :rtype: tuple[dict[str, list[float]], float]
        """
        iteration: int = 0
        best_error: float = None
        best_outputs: dict[str, list[float]] = None
        parameters_tabu_list: list[tuple[int]] = list()
        number_of_adjustable_parameters: int = len(self.parameters.adjustable_parameter_names)
        adjustable_parameter_levels: tuple[int] = tuple([self.parameters.adjustable_parameter_levels[pname] for pname in self.parameters.adjustable_parameter_names])
        no_progress_counter: int = 0

        while iteration < n_iterations and no_progress_counter < 2 * number_of_adjustable_parameters:
            if self.verbose:
                print('levels: ' + ','.join([str(level) for level in adjustable_parameter_levels]))
            # Use pre_cache=False for faster iterations since parameters change every iteration anyway
            # Only clear cache on first iteration (old parameter fingerprints won't match new ones anyway)
            should_clear_cache = (iteration == 0)
            candidate_outputs: dict[str, list[float]] = self.run(clear_cache=should_clear_cache, pre_cache=False)
            candidate_error: float = self.error(candidate_outputs)
            if self.verbose:
                print('\n-> candidate error:', candidate_error)
                print('* Iteration %i/%i' % (iteration, n_iterations-1))  # time analysis
            parameters_tabu_list.append(adjustable_parameter_levels)
            if best_error is None or candidate_error < best_error:
                if best_error is None:
                    initial_error: float = candidate_error
                    initial_levels: tuple[int] = adjustable_parameter_levels
                best_parameter_levels: tuple[int] = adjustable_parameter_levels
                best_outputs = candidate_outputs
                best_error = candidate_error
                print('\nBest error is: %f' % (best_error,))
                no_progress_counter = 0
            else:
                no_progress_counter += 1
            candidate_found: bool = False
            counter: int = 0
            new_parameter_levels = None
            while not candidate_found and counter < 2 * number_of_adjustable_parameters:
                new_parameter_levels: list[int] = list(best_parameter_levels)
                parameter_to_change = randint(0, number_of_adjustable_parameters-1)
                change = randint(0, 1) * 2 - 1
                if new_parameter_levels[parameter_to_change] + change < 0 or new_parameter_levels[parameter_to_change] + change > number_of_adjustable_parameters - 1:
                    change = - change
                new_parameter_levels[parameter_to_change] = new_parameter_levels[parameter_to_change] + change
                candidate_found = new_parameter_levels not in parameters_tabu_list
                counter += 1
            if counter >= 2 * number_of_adjustable_parameters:
                iteration = n_iterations
            else:
                adjustable_parameter_levels: tuple[int] = tuple(new_parameter_levels)
                self.dp.parameter_set.set_adjustable_levels(new_parameter_levels)
                iteration += 1

        self.dp.parameter_set.set_adjustable_levels(best_parameter_levels)
        self.dp.parameter_set.save('parameters%i' % time.time())

        contact = []
        # Ensure bounds are unpacked as tuple for string formatting
        adjustables_bounds_str: list[str] = ['(%.5f,%.5f)' % tuple(self.dp.parameter_set.adjustable_parameter_bounds[name]) for name in self.dp.parameter_set.adjustable_parameter_names]
        for parameter_name in self.parameters.adjustable_parameter_names:
            if abs(self.dp.parameter_set(parameter_name)-self.dp.parameter_set.adjustable_parameter_bounds[parameter_name][0]) < 1e-2 * abs(self.dp.parameter_set.adjustable_parameter_bounds[parameter_name][0]):
                contact.append('<')
            elif abs(self.dp.parameter_set(parameter_name)-self.dp.parameter_set.adjustable_parameter_bounds[parameter_name][1]) < 1e-2 * abs(self.dp.parameter_set.adjustable_parameter_bounds[parameter_name][1]):
                contact.append('>')
            else:
                contact.append('-')

        pretty_table = prettytable.PrettyTable(header=True)
        pretty_table.add_column('name', self.dp.parameter_set.adjustable_parameter_names)
        pretty_table.add_column('initial level', initial_levels)
        pretty_table.add_column('final level', best_parameter_levels)
        pretty_table.add_column('final values', self.dp.parameter_set.adjustable_values)
        pretty_table.add_column('bounds', adjustables_bounds_str)
        pretty_table.add_column('contact', contact)
        pretty_table.float_format['final values'] = ".4"

        print(pretty_table)
        print('Learning error from %f to %f ' % (initial_error, best_error))

        return best_parameter_levels, best_outputs, best_error

    def save(self, file_name: str = 'results.csv', selected_variables: list[str] = None):
        """
        save the selected data in a csv file

        :param file_name: name of the csv file, defaults to 'results.csv' saved in the 'results' folder specified in the setup.ini file
        :type file_name: str, optional
        :param selected_variables: list of the variable names to be saved (None for all), defaults to None
        :type selected_variables: list[str], optional
        """
        self.data.save(file_name, selected_variables)

    def sensitivity(self, number_of_trajectories: int, number_of_levels: int = 4) -> dict:
        """Perform a Morris sensitivity analysis for average simulation error both for indoor temperature and CO2 concentration. It returns 2 plots related to each output variable. mu_star axis deals with the simulation variation bias, and sigma for standard deviation of the simulation variations wrt to each parameter.
        :param number_of_trajectories: [description], defaults to 100
        :type number_of_trajectories: int, optional
        :param number_of_levels: [description], defaults to 4
        :type number_of_levels: int, optional
        :return: a dictionary with the output variables as key and another dictionary as values. It admits 'names', 'mu', 'mu_star', 'sigma', 'mu_star_conf' as keys and corresponding values as lists
        :rtype: dict[str,dict[str,list[float|str]]]
        """

        print('number of levels:', number_of_levels)
        print('number of trajectories:', number_of_trajectories)
        problem: dict[str, float] = dict()
        adjustable_parameters: list[str] = self.parameters.adjustable_parameter_names
        problem['num_vars'] = len(adjustable_parameters)
        problem['names'] = []
        problem['bounds'] = []
        for parameter_name in adjustable_parameters:
            parameter_name = self.dp.variable_accessor_registry.reference(parameter_name)  # .name_data.
            problem['names'].append(parameter_name)
            problem['bounds'].append((0, self.parameters.adjustable_level_bounds[parameter_name][1]))

        parameter_value_sets = SALib.sample.morris.sample(problem, number_of_trajectories, num_levels=number_of_levels)

        errors = list()
        for i, parameter_value_set in enumerate(parameter_value_sets):
            parameter_value_set = [round(p) for p in parameter_value_set]
            self.dp.parameter_set.set_adjustable_levels(parameter_value_set)
            print('\nsimulation %i/%i>' % (i+1, len(parameter_value_sets)), '\t', parameter_value_set)
            simulated_output_data: dict[str, list[float]] = self.run(clear_cache=True)
            output_error = self.error(simulated_output_data)
            errors.append(output_error)
        print()
        print('Analyzing simulation results')
        print('\n* estimation errors')
        results: dict = SALib.analyze.morris.analyze(problem, parameter_value_sets, numpy.array(errors, dtype=float),
                                                     conf_level=0.95, print_to_console=True, num_levels=number_of_levels)
        fig = plotly.express.scatter(results, x='mu_star', y='sigma', text=adjustable_parameters, title='estimation errors')
        fig.show()
        return results
