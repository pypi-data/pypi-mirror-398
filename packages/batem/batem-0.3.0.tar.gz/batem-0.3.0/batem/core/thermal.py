"""Thermal network modeling and RC circuit analysis module for building energy analysis.

.. module:: batem.core.thermal

This module provides comprehensive tools for thermal network modeling and RC circuit
analysis in building energy systems. It transforms RC graphical representations into
state space models for multi-zone building thermal analysis, including both thermal
behavior and CO2 concentration evolution modeling.

Classes
-------

.. autosummary::
   :toctree: generated/

   CAUSALITY
   NODE_TYPE
   ELEMENT_TYPE
   AbstractThermalNetwork
   ThermalNetwork
   ThermalNetworkMaker

Classes Description
-------------------

**CAUSALITY, NODE_TYPE, ELEMENT_TYPE**
    Enumeration classes for labeling thermal network variables and elements.

**AbstractThermalNetwork**
    Abstract base class for thermal network modeling.

**ThermalNetwork**
    Main class for RC graph to state space model transformation.

**ThermalNetworkMaker**
    Builder class for thermal network construction and management.

Key Features
------------

* RC circuit representation and analysis for building thermal systems
* State space model generation from thermal network graphs
* Multi-zone building thermal modeling with zone connectivity
* Thermal resistance and capacitance modeling for building components
* Heat flow and temperature variable management in thermal networks
* Matrix operations for thermal network analysis and state space conversion
* Building component modeling with layered and block wall sides
* CO2 concentration evolution modeling in building zones
* Thermal network visualization and analysis capabilities
* Integration with building energy data providers and measurement systems
* Support for periodic depth analysis and thermal wave propagation

The module is designed for building energy analysis, thermal modeling, and
comprehensive building performance evaluation in research and practice.

.. note::
    This module requires networkx for graph representation and numpy for matrix operations.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""
from __future__ import annotations
import enum
from typing import List, Tuple
import matplotlib.pyplot as plt
import networkx
from .statemodel import StateModel
import numpy
import numpy.linalg
import scipy.linalg
from math import pi, sqrt
from typing import Any
import abc
from batem.core.library import properties
import copy
from batem.core.library import ZONE_TYPES, SIDE_TYPES
from batem.core.components import Zone, WallSide, LayeredWallSide, BlockWallSide
from .data import DataProvider
import warnings

# Suppress specific warnings
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*overflow.*')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*invalid value.*')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*divide by zero.*')


class CAUSALITY(enum.Enum):
    """Enumeration for labeling causality of thermal network node variables.

    This enumeration defines the causality tags used for labeling node variables
    in thermal network analysis, indicating whether variables are inputs, outputs,
    or undefined in the thermal system modeling.
    """
    IN = "IN"
    UNDEF = "-"
    OUT = "OUT"


def concatenate(*lists):
    """ Combine tuples of lists into a single list without duplicated values.

    :param lists: a tuple [of tuple of tuple] of list of elements
    :type lists: a tuple [of tuple of tuple] of list of elements
    :return: a concatenated list of elements
    :rtype: list (of str usually)
    """
    if lists is None:
        return list()
    while type(lists[0]) is tuple:
        lists = lists[0]
    returned_list = list()
    for a_list in lists:
        for element in a_list:
            if element not in returned_list:
                returned_list.append(element)
    return returned_list


def clean(selection_matrix: numpy.matrix) -> numpy.matrix:
    """
    Remove row full of zeros in a selection matrix (one value per row and at most one value per column).

    :param selection_matrix: a selection matrix
    :type selection_matrix: numpy.matrix
    :raises ValueError: triggered if the matrix given as argument is not a selection matrix
    :return: the provided selection but without rows full of zeros
    :rtype: Matrix
    """
    if selection_matrix.shape[0] > selection_matrix.shape[1]:
        raise ValueError('bar only operates on row matrices')
    i: int = 0
    while i < selection_matrix.shape[0]:
        number_of_non_null_elements: int = 0
        for j in range(selection_matrix.shape[1]):
            if selection_matrix[i, j] != 0:
                number_of_non_null_elements += 1
        if number_of_non_null_elements == 0:
            selection_matrix = numpy.delete(selection_matrix, i, axis=0)
        elif number_of_non_null_elements > 1:
            raise ValueError('bar only operates on selection matrices')
        else:
            i += 1
    return selection_matrix


def bar(a_matrix: numpy.matrix) -> numpy.matrix:
    """
    Compute the complementary matrix to the provided row matrix i.e bar_M such as [[M], [bar_M]] is invertible, bar_M.T * bar_M = I and M.T * bar_M = 0.

    A specific fast computation approach is used if M is a selection matrix.

    :param matrix: a row matrix, possibly a selection Matrix (one value per row and at most one value per column)
    :type matrix: Matrix
    :return: a complementary matrix
    :rtype: sympy.Matrix
    """
    try:
        i: int = 0
        while i < a_matrix.shape[0]:
            number_of_non_null_elements: int = 0
            for j in range(a_matrix.shape[1]):
                if a_matrix[i, j] != 0:
                    number_of_non_null_elements += 1
            if number_of_non_null_elements == 0:
                a_matrix: numpy.matrix = numpy.delete(a_matrix, i, axis=0)
            elif number_of_non_null_elements > 1:
                pass
            else:
                i += 1
        n_rows, n_columns = a_matrix.shape
        complement_matrix: numpy.matrix = numpy.matrix(numpy.zeros((n_columns - n_rows, n_columns)))
        k: int = 0
        for i in range(n_columns):
            found: bool = False
            j: int = 0
            while (not found) and j < n_rows:
                if a_matrix[j, i] != 0:
                    found = True
                j += 1
            if not found:
                complement_matrix[k, i] = 1
                k += 1
    except:  # noqa
        vectors: numpy.matrix = numpy.matrix(scipy.linalg.null_space(a_matrix.T))
        complement_matrix = vectors[0]
        for i in range(1, len(vectors)):
            complement_matrix = numpy.concatenate((complement_matrix, vectors[i]), axis=1)
        complement_matrix = complement_matrix.T
    return complement_matrix


def pinv(matrix: numpy.matrix) -> numpy.matrix:
    """
    compute pseudo-inverse of a full column rank matrix

    :param matrix: a full column rank matrix
    :type matrix: sympy.Matrix
    :return: the pseudo inverse computed as (matrix*matrix.T).inv() * matrix
    :rtype: numpy.matrix
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return scipy.linalg.pinv(matrix, atol=1e-10)


class NODE_TYPE(enum.Enum):
    """Enumeration for labeling the type of thermal network node variables.

    This enumeration defines the node type tags used for labeling variables
    in thermal network analysis, distinguishing between temperature and heat
    flow variables in the thermal system modeling.
    """
    HEAT = "heat"
    TEMPERATURE = "temperature"


class ELEMENT_TYPE(enum.Enum):
    """Enumeration for labeling different types of thermal network elements.

    This enumeration defines the element type tags used for labeling edges
    in thermal network analysis, distinguishing between thermal resistance,
    thermal capacitance, and heat source elements in the thermal system modeling.
    """
    R = "Rth"
    C = "Cth"
    P = "heat"


class AbstractThermalNetwork(networkx.DiGraph):
    """Abstract base class for thermal network modeling and analysis.

    This abstract class provides the foundation for thermal network modeling using
    directed graphs where nodes represent variables (temperatures or heat flows)
    and edges represent thermal elements (resistance, capacitance, heat sources).
    The primary aim is to generate state space models corresponding to thermal networks.
    """

    def __init__(self) -> None:
        """Initialize an empty thermal network
        """
        super().__init__(directed=True)
        self.Tref = self.T('TREF', CAUSALITY.IN)
        self.R_counter = 0
        self.C_counter = 0
        self.P_counter = 0
        self.T_counter = 1
        self.__select_elements = dict()

    def _edge_attr_str_vals(self, edge: Tuple[str, str]):
        """Convert edge attributes into a printable string

        :param edge: edge whose attributes have to be converted
        :type node: (str, str)
        :return: a string representing the edge attributes with values
        :rtype: str
        """
        _attr_vals = list()
        for attr_name in self.edges[edge]:
            _attr_value = self.edges[edge][attr_name]
            if type(_attr_value) is str:
                _attr_vals.append(_attr_value)
            elif isinstance(_attr_value, ELEMENT_TYPE):
                _attr_vals.append(_attr_value.value)
        return _attr_vals

    def _node_attr_str_vals(self, node: str):
        """Convert node attributes into a printable string

        :param node: node whose attributes have to be converted
        :type node: str
        :return: a string representing the node attributes with values
        :rtype: str
        """
        _attr_vals = list()
        for attr_name in self.nodes[node]:
            _attr_value = self.nodes[node][attr_name]
            if type(_attr_value) is str:
                _attr_vals.append(_attr_value)
            elif isinstance(_attr_value, NODE_TYPE) or isinstance(_attr_value, CAUSALITY):
                _attr_vals.append(_attr_value.value)
        return _attr_vals

    def T(self, name: str = None, causality: CAUSALITY = CAUSALITY.UNDEF) -> str:
        """Create a temperature node.

        :param name: temperature node name (should conventionally start by T), defaults to None with name generated automatically
        :type name: str, optional
        :param causality: type of causality, defaults to NODE_CAUSALITY.UNDEF
        :type causality: NODE_CAUSALITY, optional
        :return: name of the temperature node
        :rtype: str
        """
        if name in self.nodes:
            return name
        elif name is None:
            name: str = 'T' + str(self.T_counter)
            self.T_counter += 1
            symbol = name
        elif name == 'TREF':
            symbol: int = 0
        else:
            symbol = name
        self.add_node(name, causality=causality, ntype=NODE_TYPE.TEMPERATURE, value=symbol)
        return name

    def HEAT(self, T: str,  name: str = None) -> str:
        """Create a heat source node.

        :param T: temperature node where the heat source will inject its power
        :type T: str
        :param name: name of the heat source (should conventionally start by P), defaults to None with name generated automatically
        :type name: str, optional
        :return: name of the heat source node
        :rtype: str
        """
        if name is None:
            name = 'P'+str(self.P_counter)
            self.P_counter += 1
        self.add_node(name, causality=CAUSALITY.IN, ntype=NODE_TYPE.HEAT, value=name)
        self.add_edge(name, T, flow=name, element=ELEMENT_TYPE.P, value=name)
        return name

    def R(self, fromT: str = None, toT: str = None, name: str = None, heat_flow_name: str = None, val: float = None) -> tuple(str, str):
        """Create a resistance edge element between 2 temperature nodes, directed by the conventional heat flow.

        :param fromT: name of the temperature node where heat flow starts, defaults to None (0 reference temperature)
        :type fromT: str, optional
        :param toT: name of the temperature node where heat flow ends, defaults to None (0 reference temperature)
        :type toT: str, optional
        :param resistance_name: name of the thermal resistance, defaults to None with name generated automatically (RXXX)
        :type resistance_name: str, optional
        :param heat_flow_name: name of the heat_flow passing through thermal resistance, defaults to None with name generated automatically (PXX`X)
        :type heat_flow_name: str, optional
        :param value: value of the thermal resistance, defaults to None
        :type float: float, optional
        :raises ValueError: fromT and toT cannot be set to None simultaneously
        :return: thermal resistance name and heat flow name
        :rtype: tuple(str, str)
        """
        if fromT is None and toT is None:
            raise ValueError('At least one temperature must not be None')
        elif fromT is None:
            fromT: str = self.Tref
        elif fromT not in self.nodes:
            self.T(name=fromT)
        elif toT is None:
            toT: str = self.Tref
        elif toT not in self.nodes:
            self.T(name=toT)
        if name is None:
            name: str = 'R'+str(self.R_counter)
            self.R_counter += 1
        if heat_flow_name is None:
            heat_flow_name: str = 'P'+str(self.P_counter)
        self.P_counter += 1
        if val is not None:
            self.add_edge(fromT, toT, name=name, flow=heat_flow_name, element=ELEMENT_TYPE.R, value=val)
        return name, heat_flow_name

    def C(self, toT: str, name: str = None, heat_flow_name: str = None, val: float = None):
        """Create a thermal capacitance edge element between 0 reference temperature and a temperature node, directed by the conventional heat flow to the specified temperature node.

        :param T: name of the temperature node where heat flow ends, defaults to None (0 reference temperature)
        :type toT: str, optional
        :param capacitance_name: name of the thermal resistance, defaults to None with name generated automatically (CXXX)
        :type capacitance_name: str, optional
        :param heat_flow_name: name of the heat_flow passing through thermal resistance, defaults to None with name generated automatically (PXXX)
        :type heat_flow_name: str, optional
        :return: thermal resistance name and heat flow name
        :rtype: tuple(str, str)
        """
        if toT not in self.nodes:
            self.T(name=toT)
        if name is None:
            name: str = 'C' + str(self.C_counter)
            self.C_counter += 1
        if heat_flow_name is None:
            heat_flow_name: str = 'P'+str(self.P_counter)
        self.P_counter += 1
        self.add_edge(self.Tref, toT, name=name, flow=heat_flow_name, element=ELEMENT_TYPE.C, value=float(val))
        return name, heat_flow_name

    def RCs(self, fromT: str, toT: str = None, n_layers: int = 1, name: str = None, Rtotal: float = None, Ctotal: float = None):
        if name is None:
            if fromT is None:
                name = toT
                fromT, toT = toT, fromT
            else:
                if toT is not None:
                    name = fromT + '-' + toT
                else:
                    name = fromT
            if fromT is None:
                raise ValueError('At least one temperature node must be specified')
        if n_layers <= 1:
            middle_layer_temperature_name = name + 'm'
            self.R(fromT=fromT, toT=middle_layer_temperature_name, name='R0_'+middle_layer_temperature_name,  val=Rtotal/2)
            self.R(fromT=middle_layer_temperature_name, toT=toT, name='R1_'+middle_layer_temperature_name, val=Rtotal/2)
            self.C(toT=middle_layer_temperature_name, name='C_', val=Ctotal)
        else:
            R = Rtotal / 2 / n_layers
            C = Ctotal / n_layers
            for layer_index in range(n_layers):
                layer_name0: str = fromT if layer_index == 0 else name + '_%i' % layer_index
                layer1_name: str = toT if layer_index == n_layers - 1 else name + '_%i' % (layer_index+1)
                layer_middle_name: str = name + '_%i' % layer_index + 'm'
                self.R(fromT=layer_name0, toT=layer_middle_name, name='R0_'+layer_middle_name, val=R)
                self.R(fromT=layer_middle_name, toT=layer1_name, name='R1_'+layer_middle_name, val=R)
                self.C(toT=layer_middle_name, val=C)

    def _select_elements(self, element_type: ELEMENT_TYPE = None):
        """Return a list of a specified type of elements

        :param element_type: type of elements ELEMENT_TYPE (ELEMENT_TYPE.R for resistance, ELEMENT_TYPE.C for capacitance and ELEMENT_TYPE.P for heat source), defaults to None for all edge elements
        :type element_type: ELEMENT_TYPE, optional
        :return: list of requested elements
        :rtype: list of Networkx edges i.e. list of tuples (str, str)
        **SLOW**
        """
        if element_type is None:
            return self.edges
        else:
            if element_type not in self.__select_elements:
                self.__select_elements[element_type] = list(filter(lambda edge: edge is not None and self.edges[edge]['element'] == element_type, self.edges))
            return self.__select_elements[element_type]

    def _select_nodes(self, node_type: NODE_TYPE, node_causality: CAUSALITY = None):
        """Return a list of a specified type of nodes

        :param node_type: type of nodes (NODE_TYPE.TEMPERATURE for temperature, NODE_TYPE.HEAT for heat source), defaults to None for all node types
        :type node_type: NODE_TYPE
        :param node_causality: causality of nodes (NODE_CAUSALITY.IN for input, NODE_CAUSALITY.OUT for output and NODE_CAUSALITY.UNDEF for intermediate), defaults to None for all causalities
        :type node_causality: NODE_CAUSALITY
        :return: list of requested nodes
        :rtype: list of Networkx nodes i.e. list of str
        **SLOW**
        """
        if node_type is None and node_causality is None:
            return self.nodes
        elif node_type is None:
            return list(filter(lambda node: self.nodes[node]['causality'] == node_causality, self.nodes))
        elif node_causality is None:
            return list(filter(lambda node: self.nodes[node]['ntype'] == node_type, self.nodes))
        else:
            # l1 = list(filter(lambda node: self.nodes[node]['ntype'] == node_type, self.nodes))
            # l2 = list(filter(lambda node: self.nodes[node]['causality'] == node_causality, self.nodes))
            # l3 = list(filter(lambda node: self.nodes[node]['ntype'] == node_type and self.nodes[node]['causality'] == node_causality, self.nodes))
            return list(filter(lambda node: self.nodes[node]['ntype'] == node_type and self.nodes[node]['causality'] == node_causality, self.nodes))

    def _causal_temperatures(self) -> tuple:
        """ Return a tuple of lists of categorized temperature names
        :return: input temperatures, temperatures appearing as derivative, intermediate temperatures and output temperatures
        :rtype: tuple of lists of str
        """
        temperatures_state = list()
        for Cedge in self._select_elements(ELEMENT_TYPE.C):
            if Cedge[0] != "TREF" and Cedge[0] not in temperatures_state:
                temperatures_state.append(Cedge[0])
            if Cedge[1] != "TREF" and Cedge[1] not in temperatures_state:
                temperatures_state.append(Cedge[1])
        temperatures_remaining = list()
        for temperature in self._select_nodes(NODE_TYPE.TEMPERATURE):
            if temperature not in self.temperatures_in and temperature not in temperatures_state:
                temperatures_remaining.append(temperature)
        return temperatures_state, temperatures_remaining

    @property
    def temperatures_in(self) -> List[str]:
        """
        Return the names of temperatures tagged with Causality.IN. These variables are obtained either from the state vector, or from a combination of input variables and variables from state vector

        :return: temperature names requested for being simulated
        :rtype: Tuple[str]
        """
        _temperatures_in = list(self._select_nodes(NODE_TYPE.TEMPERATURE, CAUSALITY.IN))
        _temperatures_in.remove('TREF')
        return _temperatures_in

    @property
    def temperatures_out(self) -> Tuple[str]:
        """
        Return the names of temperatures tagged with Causality.OUT. These variables are obtained either from the state vector, or from a combination of input variables and variables from state vector

        :return: temperature names requested for being simulated
        :rtype: Tuple[str]
        """
        _temperatures_out = self._select_nodes(NODE_TYPE.TEMPERATURE, CAUSALITY.OUT)
        if len(_temperatures_out) == 0:
            for temperature in self._select_nodes(NODE_TYPE.TEMPERATURE):
                if temperature not in self._select_nodes(NODE_TYPE.TEMPERATURE, CAUSALITY.IN) and temperature != 'TREF':
                    _temperatures_out.append(temperature)
        return _temperatures_out

    @property
    def all_temperatures(self):
        """
        Return the list of all the variables representing temperatures

        :return: list of temperature names
        :rtype: List[str]
        """
        return concatenate(self.temperatures_in, *self._causal_temperatures())

    def _typed_heatflows(self):
        """Return the list of edge element heatflows by type. It returns 3 vectors of heat flows:
        - heatflows_R: the list of heatflows going through thermal resistances
        - heatflows_C: the list of heatflows going through thermal capacitances
        - heatflows_P: the list of heatflows sources

        :return: list of edge element heatflows by type: edges corresponding to resistance, then those corresponding to capacitance and finally those corresponding to power heatflows
        :rtype: Tuple[List[(str, str)]]
        """
        heatflows_R = [self.edges[edge]['flow'] for edge in self._select_elements(ELEMENT_TYPE.R)]
        heatflows_C = [self.edges[edge]['flow'] for edge in self._select_elements(ELEMENT_TYPE.C)]
        heatflows_P = [self.edges[edge]['flow'] for edge in self._select_elements(ELEMENT_TYPE.P)]
        return heatflows_R, heatflows_C, heatflows_P

    @property
    def heatflows_sources(self):
        """
        Return the list of heatflow sources

        :return: heatflow sources
        :rtype: List[str]
        """
        _, _, heatflows_P = self._typed_heatflows()
        return heatflows_P

    def _number_of_elements(self, type: ELEMENT_TYPE) -> int:
        """number of elements of the specified type in the thermal network

        :param type: type of elements to be counted
        :type type: ELEMENT_TYPE
        :return: number of edges tags as resistances
        :rtype: int
        """
        return len(self._select_elements(type))


class ThermalNetwork(AbstractThermalNetwork):
    """Main class for RC graph to state space model transformation.

    This specialized class extends AbstractThermalNetwork to provide comprehensive
    functionality for transforming RC (Resistance-Capacitance) thermal graphs into
    state space models for building energy analysis and thermal system simulation.
    """

    def __init__(self) -> None:
        """
        See superclass AbstractThermalNetwork.
        """
        super().__init__()
        self.zone_surface_nodes: dict[str, list[tuple[str, float, str]]] = dict()
        self.zone_air_nodes: dict[str, str] = dict()

    def register_zone_air(self, zone_name: str, air_temperature_node: str) -> None:
        self.zone_air_nodes[zone_name] = air_temperature_node
        if zone_name not in self.zone_surface_nodes:
            self.zone_surface_nodes[zone_name] = list()

    def add_zone_surface(self, zone_name: str, surface_node: str, surface_area: float, side_type: SIDE_TYPES) -> None:
        if zone_name not in self.zone_surface_nodes:
            self.zone_surface_nodes[zone_name] = list()
        orientation = 'vertical' if side_type.value > 0 else 'horizontal'
        if not any(existing_node == surface_node for existing_node, _, _ in self.zone_surface_nodes[zone_name]):
            self.zone_surface_nodes[zone_name].append((surface_node, surface_area, orientation))

    def _matrices_MR_MC(self) -> Tuple[numpy.matrix, numpy.matrix]:
        """
        incidence matrices (-1 for starting flow and +1 for ending) leading to delta temperatures for R and C elements from temperatures
        :return: matrices MR and MC
        :rtype: sympy.Matrix, sympy.Matrix
        """
        Redges = self._select_elements(ELEMENT_TYPE.R)
        Cedges = self._select_elements(ELEMENT_TYPE.C)
        all_temperatures = self.all_temperatures
        MR: numpy.matrix = numpy.matrix(numpy.zeros((self._number_of_elements(ELEMENT_TYPE.R), len(all_temperatures))))
        MC: numpy.matrix = numpy.matrix(numpy.zeros((self._number_of_elements(ELEMENT_TYPE.C), len(all_temperatures))))
        components = []
        for i, Redge in enumerate(Redges):
            components.append(self.edges[Redge]['name'])
            for j, node in enumerate(Redge):
                if node in all_temperatures:
                    MR[i, all_temperatures.index(node)] = 1 - 2 * j
        for i, Cedge in enumerate(Cedges):
            components.append(self.edges[Cedge]['name'])
            for j, node in enumerate(Cedge):
                if node in all_temperatures:
                    MC[i, all_temperatures.index(node)] = 1 - 2 * j
        return MR, MC

    def _matrix_R(self) -> numpy.matrix:
        """ Return a diagonal matrix with thermal resistance coefficient in the diagonal.

        :return: diagonal matrix R
        :rtype: sympy.matrix
        """
        Redges = self._select_elements(ELEMENT_TYPE.R)
        R_heat_flows = self._typed_heatflows()[0]
        matrix_R: numpy.matrix = numpy.matrix(numpy.zeros((len(R_heat_flows), len(R_heat_flows))))
        for Redge in Redges:
            i: int = R_heat_flows.index(self.edges[Redge]['flow'])
            matrix_R[i, i] = self.edges[Redge]['value']
        return matrix_R

    def _matrix_C(self) -> numpy.matrix:
        """" Return a diagonal matrix with thermal capacitance coefficient in the diagonal.

        :return: diagonal matrix C
        :rtype: sympy.matrix
        """
        Cedges = self._select_elements(ELEMENT_TYPE.C)
        C_heat_flows = self._typed_heatflows()[1]
        matrix_C: numpy.matrix = numpy.matrix(numpy.zeros((len(C_heat_flows), len(C_heat_flows))))
        for Cedge in Cedges:
            i: int = C_heat_flows.index(self.edges[Cedge]['flow'])
            matrix_C[i, i] = self.edges[Cedge]['value']
        return matrix_C

    @property
    def _matrices_Gamma_RCP(self) -> Tuple[numpy.matrix, numpy.matrix, numpy.matrix]:
        """ Return heatflow balances at each node as a set of 3 incidence (-1: node leaving flow and 1: node entering flow) matrices:

        heatflows_balance_R_matrix * R_heatflows + heatflows_balance_C_matrix * C_heatflows + heatflows_balance_P_matrix * P_heatflows = 0

        :return: matrices heatflows_balance_R_matrix (GammaR), heatflows_balance_C_matrix (GammaC), heatflows_balance_P_matrix (GammaP)
        :rtype: sympy.Matrix, sympy.Matrix, sympy.Matrix
        """
        heatflows_R, heatflows_C, heatflows_P = self._typed_heatflows()
        heatflows_R_matrix = list()
        heatflows_C_matrix = list()
        heatflows_P_matrix = list()
        number_of_heat_balances = 0
        for node in self.all_temperatures:
            flows_in = [self.edges[edge]['flow'] for edge in self.in_edges(nbunch=node)]
            flows_out = [self.edges[edge]['flow'] for edge in self.out_edges(nbunch=node)]
            if node != 'TREF' and len(flows_in) + len(flows_out) > 1:
                heatflows_R_matrix.append([0 for i in range(len(heatflows_R))])
                heatflows_C_matrix.append([0 for i in range(len(heatflows_C))])
                heatflows_P_matrix.append([0 for i in range(len(heatflows_P))])
                for flow in concatenate(flows_in, flows_out):
                    incidence = -1 if flow in flows_out else 1
                    flow_index = self.all_heatflows.index(flow)
                    if flow_index < len(heatflows_R):
                        heatflows_R_matrix[number_of_heat_balances][flow_index] = incidence
                    elif flow_index < len(heatflows_R) + len(heatflows_C):
                        heatflows_C_matrix[number_of_heat_balances][flow_index - len(heatflows_R)] = incidence
                    else:
                        heatflows_P_matrix[number_of_heat_balances][flow_index - len(heatflows_R) - len(heatflows_C)] = - incidence
                number_of_heat_balances += 1
        return numpy.matrix(heatflows_R_matrix), numpy.matrix(heatflows_C_matrix), numpy.matrix(heatflows_P_matrix)

    def _temperatures_selection_matrix(self, selected_temperatures: List[str], all_temperatures: List[str] = None):
        """Create a selection matrix for the temperature provided as inputs and considering all the temperature nodes

        :param selected_temperatures: list of temperatures for which the selection matrix is computer
        :type selected_temperatures: List[str]
        :return: the selection matrix
        :rtype: scipy.Matrix
        """
        if all_temperatures is None:
            all_temperatures: List[str] = self.all_temperatures
        selection_matrix: numpy.matrix = numpy.matrix(numpy.zeros((len(selected_temperatures), len(all_temperatures))))
        for i, temperature in enumerate(selected_temperatures):
            selection_matrix[i, all_temperatures.index(temperature)] = 1
        return selection_matrix

    def _Sselect(self) -> numpy.matrix:
        """
        Generate a selection matrix to get from all the temperatures except the input and the state ones, the ones that has been tagged with CAUSALITY.OUT

        :return: a selection matrix with 0 or 1 insides
        :rtype: Matrix
        """
        if self.temperatures_select is None or len(self.temperatures_select) == 0:
            selection_matrix: numpy.matrix = numpy.matrix(numpy.eye(len(self.temperatures_remaining)))
        else:
            selection_matrix: numpy.matrix = numpy.matrix(numpy.zeros((len(self.temperatures_select), len(self.temperatures_remaining))))
            for i, temperature in enumerate(self.temperatures_select):
                if temperature in self.temperatures_remaining:
                    selection_matrix[i, self.temperatures_remaining.index(temperature)] = 1
        return selection_matrix

    @property
    def all_heatflows(self):
        """
        List 3 vectors of heat flows:
        - heatflows_R: the list of heatflows going to thermal resistances
        - heatflows_C: the list of heatflows going to thermal capacitances
        - heatflows_P: the list of heatflows sources

        :return: _description_
        :rtype: List[str,
        """
        heatflows_R, heatflows_C, P_heatflows = self._typed_heatflows()
        return concatenate(heatflows_R, heatflows_C, P_heatflows)

    def _heatflows_selection_matrix(self, selected_heat_flows: List[str]):
        """
        Internally used to generate a selection matrix for extracting some heatflows .

        :param selected_heat_flows: the heatflows that will correspond to the selection matrix
        :type selected_heat_flows: List[str]
        :return: a selection matrix S such as:

            selected_heat_flows = S * all_heatflows
        :rtype: List[str]
        """
        selection_matrix: numpy.matrix = numpy.matrix(numpy.zeros((len(selected_heat_flows), len(self.all_heatflows))))
        for i, heat_flow in enumerate(selected_heat_flows):
            selection_matrix[i, self.all_heatflows.index(heat_flow)] = 1
        return selection_matrix

    def _Sin(self):
        """
        Generate a selection matrix corresponding to the known temperatures temperatures_in used as inputs.

        :return: a full row rank selection Matrix that can be used to extract the known value variables i.e. variables in the vector temperatures_in
        :rtype: sympy.Matrix
        """
        return self._temperatures_selection_matrix(self.temperatures_in)

    def _Sstate(self):
        """
        Generate a selection matrix corresponding to the temperatures with derivatives temperatures_state used as state vector.

        :return: a full row rank selection Matrix that can be used to extract the state variables
        :rtype: sympy.Matrix
        """
        temperatures_state, _ = self._causal_temperatures()
        Sstate = self._temperatures_selection_matrix(temperatures_state)
        return Sstate

    @property
    def temperatures_state(self):
        """
        Vector containing the list of state variables

        :return: the temperatures corresponding to the state variables
        :rtype: sympy.Matrix
        """
        temperatures_state, _ = self._causal_temperatures()
        return temperatures_state

    def _Sremaining(self):
        """
        Generate a selection matrix corresponding to the temperatures which are not belonging to the inputs and to the states.

        :return: a full row rank selection Matrix that can be used to extract the temperatures which are not belonging to the inputs and to the states.
        :rtype: sympy.Matrix
        """
        _, temperatures_remaining = self._causal_temperatures()
        Sremaining = self._temperatures_selection_matrix(temperatures_remaining)
        return Sremaining

    @property
    def temperatures_ignore(self):
        _temperatures_ignore = list()
        for temperature in self.temperatures_remaining:
            if temperature not in self.temperatures_out:
                _temperatures_ignore.append(temperature)
        return _temperatures_ignore

    def _Signore(self):
        """
        Generate a selection matrix corresponding to the temperatures which are not belonging to the inputs and to the states.

        :return: a full row rank selection Matrix that can be used to extract the temperatures which are not belonging to the inputs and to the states.
        :rtype: sympy.Matrix
        """
        Signore = self._temperatures_selection_matrix(self.temperatures_ignore)
        return Signore

    def _Sout(self):
        """
        Return a selection matrix leading to output temperature variable from the vector of all the temperature variables

        :return: a selection matrix for extracting temperature variables, which have been tagged with Causality.OUT
        :rtype: Matrix
        """
        return self._temperatures_selection_matrix(self.temperatures_out)

    @property
    def temperatures_remaining(self):
        """
        Vector containing the list of temperatures which are not belonging to the inputs and to the states.

        :return: the temperatures corresponding to the temperatures which are not belonging to the inputs and to the states.
        :rtype: sympy.Matrix
        """
        _, temperatures_remaining = self._causal_temperatures()
        return temperatures_remaining

    @property
    def temperatures_select(self) -> tuple:
        """
        Return the selected temperatures, tagged with CAUSALITY.OUT, to be at the output of the state space output equation except the temperatures belonging to the state ones

        :return: _description_
        :rtype: tuple
        """
        temperatures_sel = list()
        for temperature in self.temperatures_out:
            if temperature in self.temperatures_remaining:
                temperatures_sel.append(temperature)
        return temperatures_sel

    @property
    def CDstate_heatflows_matrices(self):
        """
        Return the matrices of the following linear static model:

        temperatures_out = D_temperatures_in temperatures_in + D_heatflow_sources heatflows_sources

        :return: Matrices D_temperatures_in and D_heatflow_sources
        :rtype: Tuple(sympy.Matrix, sympy.Matrix)
        :raises ValueError: if the graphical model contains capacitance
        """
        if len(self.temperatures_state) != 0:
            raise ValueError('A linear static model can\'t be obtained from a model with capacitance')
        GammaR, _, GammaP = self._matrices_Gamma_RCP
        MR, _ = self._matrices_MR_MC()
        Psi_R = numpy.linalg.inv(GammaR * self._matrix_R()) * MR
        D_Tin = numpy.linalg.inv(self._matrix_R()) * MR * (numpy.eye(len(self.all_temperatures)) - self._Sremaining().T * pinv(Psi_R * self._Sremaining().T) * Psi_R) * self._Sin().T
        if len(self.heatflows_sources) == 0:
            D_heat = GammaP
        else:
            D_heat = numpy.linalg.inv(self._matrix_R()) * MR * self._Sremaining().T * pinv(Psi_R * self._Sremaining().T) * GammaP
        return D_Tin, D_heat

    def _diffeq_variables(self):
        """
        Compute internal matrices for state space model

        :return: internal matrices: GammaR, GammaC, GammaP, MR, MC, Psi_R, Psi_C, Phi, Pi
        :rtype: List[float]
        """
        GammaR, GammaC, GammaP = self._matrices_Gamma_RCP
        MR, MC = self._matrices_MR_MC()
        Psi_R = GammaR * numpy.linalg.inv(self._matrix_R()) * MR
        Psi_C = GammaC * self._matrix_C() * MC
        Phi = bar(self._Sstate() * Psi_C.T) * Psi_R * self._Sremaining().T
        Pi = pinv(Psi_C * self._Sstate().T) * (numpy.eye(Psi_R.shape[0]) - Psi_R * self._Sremaining().T * pinv(Phi) * bar(self._Sstate()*Psi_C.T))
        return GammaR, GammaC, GammaP, MR, MC, Psi_R, Psi_C, Phi, Pi

    def _ABstate_matrices(self):
        """ Compute matrices A, B of the state space model corresponding to the thermal network

        d/dt temperatures_state = A temperatures_state + B_in temperatures_in + B_heat heat_sources

        :return: matrices of the state space representation corresponding to the thermal network with temperature corresponding to capacitance as state variables
        :rtype: List[sympy.matrix]
        """
        if len(self.temperatures_state) == 0:
            raise ValueError('A state space model can only be obtained for a model with capacitance')

        _, _, GammaP, _, _, Psi_R, _, _, Pi = self._diffeq_variables()
        A = - Pi * Psi_R * self._Sstate().T
        B_temperatures_in = - Pi * Psi_R * self._Sin().T
        if len(self.heatflows_sources) == 0:
            B_heatflow_sources = GammaP
        else:
            B_heatflow_sources = Pi * GammaP

        return A, B_temperatures_in, B_heatflow_sources

    def _CDstate_matrices(self):
        """
        Compute matrices C_rem, D_temperatures_in and D_heatflow_sources of the state space model corresponding to the thermal network where output temperature is corresponding to temperatures_in

        :return: matrices C_rem, D_temperatures_in and D_heatflow_source
        :rtype: _type_
        """
        _, _, GammaP, _, _, Psi_R, Psi_C, Phi, _ = self._diffeq_variables()
        if numpy.any(Psi_C):
            C_rem = - pinv(Phi) * bar(self._Sstate() * Psi_C.T) * Psi_R * self._Sstate().T
            D_rem_temperatures_in = - pinv(Phi) * bar(self._Sstate() * Psi_C.T) * Psi_R * self._Sin().T
            if len(self.heatflows_sources) == 0:
                D_rem_heatflow_sources = GammaP
            else:
                D_rem_heatflow_sources = pinv(Phi) * bar(self._Sstate() * Psi_C.T) * GammaP
            if self.temperatures_select is None or self.temperatures_select == 0:
                return C_rem, D_rem_temperatures_in, D_rem_heatflow_sources
            if len(self.heatflows_sources) > 0:
                return self._Sselect() * C_rem, self._Sselect() * D_rem_temperatures_in, self._Sselect() * D_rem_heatflow_sources
            else:
                return self._Sselect() * C_rem, self._Sselect() * D_rem_temperatures_in, None
        else:
            Kout = pinv(Psi_R * self._Sout().T)
            Kignore = - pinv(Psi_R * self._Signore().T)
            if numpy.any(Kignore) and not ('TREF' in self.temperatures_ignore and len(self.temperatures_ignore) == 1):
                raise ValueError("Missing temperatures: "+','.join(self.temperatures_ignore))
            D_rem_temperatures_in = - Kout * Psi_R * self._Sin().T
            D_rem_heatflow_sources = Kout * GammaP
            return None, D_rem_temperatures_in, D_rem_heatflow_sources

    @property
    def CDheatflows_matrices(self) -> Tuple[numpy.matrix]:
        """
        Compute matrices C and D leading to the estimations of heatflows going through resistances and capacitances

        :return: Matrices
        :rtype: Tuple[Matrix]
        """
        GammaR, GammaC, GammaP, MR, MC, Psi_R, Psi_C, Phi, Pi = self._diffeq_variables()
        Pi1 = numpy.linalg.inv(self._matrix_R()) * MR * (numpy.eye(len(self.all_temperatures)) + self._Sremaining().T * pinv(Phi) * bar(self._Sstate() * Psi_C.T) * Psi_R)
        C_R = Pi1 * self._Sstate().T
        D_R_in = Pi1 * self._Sin().T
        if len(self.heatflows_sources) == 0:
            D_R_varphi_P = GammaP
        else:
            D_R_varphi_P = -numpy.linalg.inv(self._matrix_R()) * MR * self._Sremaining().T * pinv(Phi) * bar(self._Sstate() * Psi_C.T) * GammaP
        Pi2 = - self._matrix_C() * MC * self._Sstate().T * Pi * Psi_R
        C_C = Pi2 * self._Sstate().T
        D_C_in = Pi2 * self._Sin().T
        if len(self.heatflows_sources) == 0:
            D_C_varphi_P = GammaP
        else:
            D_C_varphi_P = self._matrix_C() * MC * self._Sstate().T * Pi * GammaP
        C = numpy.concatenate((C_R, C_C), axis=0)
        D_in = numpy.concatenate((D_R_in, D_C_in), axis=0)
        D_varphi_P = numpy.concatenate((D_R_varphi_P, D_C_varphi_P), axis=0)
        return C, D_in, D_varphi_P

    def draw(self):
        """
        plot the thermal network
        """
        layout = networkx.shell_layout(self)
        node_colors = list()
        for node in self.nodes():
            if node[0] == 'P':
                node_colors.append('yellow')
            elif node == 'TREF':
                node_colors.append('blue')
            else:
                if self.nodes[node]['causality'] == CAUSALITY.IN:
                    node_colors.append('cyan')
                else:
                    node_colors.append('pink')
        edge_colors = list()
        for edge in self.edges():
            if edge in self._select_elements(ELEMENT_TYPE.R):
                edge_colors.append('blue')
            elif edge in self._select_elements(ELEMENT_TYPE.C):
                edge_colors.append('red')
            else:
                edge_colors.append('black')

        plt.figure()
        networkx.draw(self, layout, with_labels=True, edge_color=edge_colors, width=1, linewidths=1, node_size=500, font_size='medium', node_color=node_colors, alpha=1)
        networkx.drawing.draw_networkx_labels(self, layout,  font_size='x-small', verticalalignment='top', labels={node: '\n'+','.join(self._node_attr_str_vals(node)) for node in self.nodes})
        networkx.draw_networkx_edge_labels(self, layout, font_size='x-small', font_color='r', edge_labels={edge: ','.join(self._edge_attr_str_vals(edge)) for edge in self.edges})

    def state_model(self) -> StateModel | dict:
        """
        Return the matrices of state space model (with capacitance) or the static model (no capacitance)

        :return: list of matrices A, B_Tin, B_heat, C, D_Tin, D_heat with variables Y, X, U_Tin, U_heat. Additionally, the type 'differential' or 'static' is given depending on wether there is at least one capacitance or not.
        :rtype: Tuple[Matrix, Matrix, Matrix, Matrix, Matrix, Matrix, Matrix, List[float], List[float], List[float], List[float], str]
        """

        temperatures_out_state = list()
        for temperature in self.temperatures_out:
            if temperature in self.temperatures_state:
                temperatures_out_state.append(temperature)
        if len(self.temperatures_state) > 0:  # dynamic model
            X = self.temperatures_state
            A, B_Tin, B_heat = self._ABstate_matrices()
            input_names: list[str] = list(self.temperatures_in)
            input_names.extend(self.heatflows_sources)
            B_total = numpy.hstack((B_Tin, B_heat))
            n_inputs = B_total.shape[1]

            C_blocks: list[numpy.matrix] = list()
            D_blocks: list[numpy.matrix] = list()
            output_names: list[str] = list()

            if len(temperatures_out_state) > 0:
                C_state: numpy.matrix = self._temperatures_selection_matrix(temperatures_out_state, X)
                D_state_Tin: numpy.matrix = numpy.matrix(numpy.zeros((C_state.shape[0], len(self.temperatures_in))))
                D_state_heat: numpy.matrix = numpy.matrix(numpy.zeros((C_state.shape[0], len(self.heatflows_sources))))
                C_blocks.append(C_state)
                D_blocks.append(self._combine_d_matrices(D_state_Tin, D_state_heat))
                output_names.extend(temperatures_out_state)

            temperatures_out_select = list()
            C_select = None
            D_select_Tin = None
            D_select_heat = None
            for temperature in self.temperatures_out:
                if temperature in self.temperatures_select and temperature not in self.temperatures_state:
                    temperatures_out_select.append(temperature)
            if len(temperatures_out_select) > 0:
                _Sout = self._temperatures_selection_matrix(temperatures_out_select, self.temperatures_select)
                C_select, D_select_Tin, D_select_heat = self._CDstate_matrices()
                C_select = _Sout * C_select
                D_select_Tin = _Sout * D_select_Tin
                if D_select_heat is not None:
                    D_select_heat = _Sout * D_select_heat
                C_blocks.append(C_select)
                D_blocks.append(self._combine_d_matrices(D_select_Tin, D_select_heat))
                output_names.extend(temperatures_out_select)

            if len(C_blocks) == 0:
                C_identity: numpy.matrix = numpy.matrix(numpy.eye(len(self.temperatures_state)))
                D_Tin = numpy.matrix(numpy.zeros((C_identity.shape[0], len(self.temperatures_in))))
                D_heat = numpy.matrix(numpy.zeros((C_identity.shape[0], len(self.heatflows_sources))))
                C_blocks.append(C_identity)
                D_blocks.append(self._combine_d_matrices(D_Tin, D_heat))
                output_names.extend(self.temperatures_state)

            C_total = C_blocks[0] if len(C_blocks) == 1 else numpy.vstack(C_blocks)
            D_total = D_blocks[0] if len(D_blocks) == 1 else numpy.vstack(D_blocks)

            C_total, D_total, output_names = self._append_operative_outputs(C_total, D_total, output_names, n_inputs)

            # Filter out intermediate RC network nodes (those with suffixes like 'm', '_0m', '_1m', ':0m', ':1m', etc.)
            # These are internal nodes used for thermal calculations and should not be exposed as outputs
            filtered_output_names = []
            filtered_indices = []
            for idx, name in enumerate(output_names):
                # Check if this is an intermediate node (contains 'm' after '-' or ':' followed by digit)
                # Examples: "TZ:floor1-TZ:floor2:1m", "TZ:floor1-TZ:floor2_0m", "TZ:floor1-TZ:floor2m"
                is_intermediate = any([
                    name.endswith('m'),  # Simple middle nodes
                    ':0m' in name, ':1m' in name, ':2m' in name, ':3m' in name,  # Numbered middle nodes with :
                    '_0m' in name, '_1m' in name, '_2m' in name, '_3m' in name,  # Numbered middle nodes with _
                ])
                if not is_intermediate:
                    filtered_output_names.append(name)
                    filtered_indices.append(idx)
            
            # Filter the C and D matrices to match the filtered outputs
            if len(filtered_indices) < len(output_names):
                filtered_indices_array = numpy.array(filtered_indices)
                C_total = C_total[filtered_indices_array, :]
                D_total = D_total[filtered_indices_array, :]
                output_names = filtered_output_names

            state_model = StateModel((A, B_total, C_total, D_total), input_names=input_names, output_names=output_names)
            state_model.create_Upartition('main', temperatures=self.temperatures_in, heats=self.heatflows_sources)
            return state_model
        else:  # static model
            D_state_Tin: numpy.matrix = numpy.matrix(numpy.zeros((len(self.temperatures_out), len(self.temperatures_in))))
            D_state_heat: numpy.matrix = numpy.matrix(numpy.zeros((len(self.temperatures_out), len(self.heatflows_sources))))

            C_select, D_select_Tin, D_select_heat = None, None, None
            temperatures_out_select = list()
            for temperature in self.temperatures_out:
                if temperature in self.temperatures_select:
                    temperatures_out_select.append(temperature)
            if len(temperatures_out_select) > 0:
                C_select, D_select_Tin, D_select_heat = self._CDstate_matrices()
            input_names = self.temperatures_in
            input_names.extend(self.heatflows_sources)
            D = numpy.hstack((D_select_Tin, D_select_heat))
            
            # Filter out intermediate RC network nodes (same as dynamic model)
            filtered_output_names = []
            filtered_indices = []
            for idx, name in enumerate(temperatures_out_select):
                is_intermediate = any([
                    name.endswith('m'),
                    ':0m' in name, ':1m' in name, ':2m' in name, ':3m' in name,
                    '_0m' in name, '_1m' in name, '_2m' in name, '_3m' in name,
                ])
                if not is_intermediate:
                    filtered_output_names.append(name)
                    filtered_indices.append(idx)
            
            # Filter the D matrix to match the filtered outputs
            if len(filtered_indices) < len(temperatures_out_select):
                filtered_indices_array = numpy.array(filtered_indices)
                D = D[filtered_indices_array, :]
                temperatures_out_select = filtered_output_names
            
            _state_model = StateModel((None, None, None, D), input_names=input_names, output_names=temperatures_out_select)
            _state_model.create_Upartition('main', temperatures=self.temperatures_in, heats=self.heatflows_sources)
            return _state_model

    def _combine_d_matrices(self, D_tin: numpy.matrix | None, D_heat: numpy.matrix | None) -> numpy.matrix:
        n_temperatures_in = len(self.temperatures_in)
        n_heatflows = len(self.heatflows_sources)

        if D_tin is None:
            D_tin = numpy.matrix(numpy.zeros((0, n_temperatures_in)))
        if D_heat is None:
            D_heat = numpy.matrix(numpy.zeros((0, n_heatflows)))

        if D_tin.shape[0] == 0 and D_heat.shape[0] > 0:
            D_tin = numpy.matrix(numpy.zeros((D_heat.shape[0], n_temperatures_in)))
        if D_heat.shape[0] == 0 and D_tin.shape[0] > 0:
            D_heat = numpy.matrix(numpy.zeros((D_tin.shape[0], n_heatflows)))

        if D_tin.shape[0] != D_heat.shape[0]:
            raise ValueError('Matrices D_tin and D_heat must have the same number of rows to be concatenated.')

        return numpy.hstack((D_tin, D_heat))

    def _append_operative_outputs(self, C_matrix: numpy.matrix, D_matrix: numpy.matrix, output_names: list[str], n_inputs: int) -> tuple[numpy.matrix, numpy.matrix, list[str]]:
        if len(self.temperatures_state) == 0:
            return C_matrix, D_matrix, output_names
        if not hasattr(self, 'zone_surface_nodes') or not hasattr(self, 'zone_air_nodes'):
            return C_matrix, D_matrix, output_names
        if len(self.zone_surface_nodes) == 0 or len(self.zone_air_nodes) == 0:
            return C_matrix, D_matrix, output_names

        operative_rows: list[numpy.matrix] = list()
        operative_d_rows: list[numpy.matrix] = list()
        operative_names: list[str] = list()
        states = self.temperatures_state

        name_zones = getattr(self, 'name_zones', {})

        for zone_name, surfaces in self.zone_surface_nodes.items():
            if zone_name not in self.zone_air_nodes or zone_name not in name_zones:
                continue
            zone = name_zones[zone_name]
            if not zone.simulated:
                continue

            air_node = self.zone_air_nodes[zone_name]
            if air_node not in states:
                continue

            state_indices = {name: idx for idx, name in enumerate(states)}
            row = numpy.zeros((1, len(states)))
            air_index = state_indices[air_node]
            valid_surfaces = [
                (node, area, orientation)
                for node, area, orientation in surfaces
                if area is not None and area > 0 and node in state_indices
            ]

            if len(valid_surfaces) == 0:
                row[0, air_index] = 1.0
            else:
                vertical_surfaces = [
                    (node, area) for node, area, orientation in valid_surfaces if orientation == 'vertical'
                ]
                horizontal_surfaces = [
                    (node, area) for node, area, orientation in valid_surfaces if orientation == 'horizontal'
                ]

                vertical_area = sum(area for _, area in vertical_surfaces)
                horizontal_area = sum(area for _, area in horizontal_surfaces)

                row[0, air_index] = 0.5
                surface_weight = 0.5
                vertical_fraction = 0.7
                horizontal_fraction = 0.3

                vert_weight = surface_weight * vertical_fraction if vertical_area > 0 else 0.0
                horiz_weight = surface_weight * horizontal_fraction if horizontal_area > 0 else 0.0

                if vertical_area <= 0 < horizontal_area:
                    horiz_weight = surface_weight
                elif horizontal_area <= 0 < vertical_area:
                    vert_weight = surface_weight

                distributed = vert_weight + horiz_weight
                if distributed < surface_weight:
                    remaining = surface_weight - distributed
                    if vertical_area > 0:
                        vert_weight += remaining
                    elif horizontal_area > 0:
                        horiz_weight += remaining

                if vertical_area > 0 and vert_weight > 0:
                    for node, area in vertical_surfaces:
                        row[0, state_indices[node]] += vert_weight * area / vertical_area

                if horizontal_area > 0 and horiz_weight > 0:
                    for node, area in horizontal_surfaces:
                        row[0, state_indices[node]] += horiz_weight * area / horizontal_area

            output_name = f'TZ_OP:{zone_name}'
            if output_name in output_names or output_name in operative_names:
                continue

            operative_rows.append(numpy.matrix(row))
            operative_d_rows.append(numpy.matrix(numpy.zeros((1, n_inputs))))
            operative_names.append(output_name)

        if len(operative_rows) == 0:
            return C_matrix, D_matrix, output_names

        operative_C = operative_rows[0] if len(operative_rows) == 1 else numpy.vstack(operative_rows)
        operative_D = operative_d_rows[0] if len(operative_d_rows) == 1 else numpy.vstack(operative_d_rows)

        C_augmented = numpy.vstack((C_matrix, operative_C))
        D_augmented = numpy.vstack((D_matrix, operative_D))
        output_names_extended = output_names + operative_names
        return C_augmented, D_augmented, output_names_extended


def name_layers(left_name: str, right_name: str, number_of_layers: int, prefix: str = '') -> tuple[list[str], list[tuple[str, str]]]:
    """generate series of suffixes to name a given number of layers: name are provided for each layer but also for the 2 borders delimiting a layer

    :param left_name: left hand side existing layer name
    :type left_name: str
    :param right_name: right hand side existing layer name
    :type right_name: str
    :param number_of_layers: number of layers to be named
    :type number_of_layers: int
    :param prefix: prefix added to each name (and inside name by composition of names), defaults to ''
    :type prefix: str, optional
    :return: first a list of names for each layer and second, a list of pairs of variable names representing both sides of a layer. Of course, the left hand side name of a layer n is equal to the right hand side name of the layer n-1
    :rtype: tuple[list[str], list[tuple[str, str]]]
    """
    layer_border_names = list()
    layer_names = list()
    for i in range(number_of_layers):
        left_border_name: str = left_name + '-' + right_name + ':' + str(i - 1) if i > 0 else left_name
        right_border_name: str = left_name + '-' + right_name + ':' + str(i) if i < number_of_layers-1 else right_name
        layer_border_names.append((prefix+left_border_name, prefix+right_border_name))
        layer_names.append(prefix+left_name + '-' + right_name + ':' + str(i) + 'm')
    return layer_names, layer_border_names


class ThermalNetworkMaker(abc.ABC):
    """Builder class for thermal network construction and management.

    This abstract class represents the thermal part of a building with its zones,
    layered and block wall sides separating zones. It provides the thermal API
    for building designers and contains the superset of building thermal components
    for comprehensive thermal network construction and analysis.
    """

    def __init__(self, *zone_names: str, periodic_depth_seconds: float, data_provider: DataProvider):
        """
        Initialize a site

        :param zone_names: names of the zones except for 'outdoor', which is automatically created
        :type zone_names: Tuple[str]
        :param args: set the order of the resulting reduced order thermal state model with order=integer value. If the value is set to None, there won't be order reduction of the thermal state model, default to None
        :type args: Dict[str, float], optional
        """
        self.sample_time_seconds: int = data_provider.sample_time_in_secs
        self.data_provider: DataProvider = data_provider
        # self.state_model_order_max: int = state_model_order_max
        self.name_zones: dict[str, Zone] = dict()
        self.zone_names: tuple[str] = zone_names
        for zone_name in zone_names:
            if zone_name in self.name_zones:
                raise ValueError('Zone %s is duplicated' % zone_name)
            self.name_zones[zone_name] = Zone(zone_name)
        self.layered_wall_sides: list[WallSide] = list()
        self.block_wall_sides: list[WallSide] = list()
        # self.thermal_state_model_order = None
        self.name_zones['outdoor'] = Zone('outdoor', kind=ZONE_TYPES.OUTDOOR)
        self.thermal_network = None
        self._thermal_network_cache: dict[int | str, ThermalNetwork] = dict()
        self.periodic_depth_seconds: float = periodic_depth_seconds

    @property
    def wall_sides(self) -> list[WallSide]:
        _wall_sides: list[WallSide] = self.layered_wall_sides.copy()
        _wall_sides.extend(self.block_wall_sides)
        return _wall_sides

    def wall_transmitivities(self, zone1_name: str = None, zone2_name: str = None) -> float | dict[frozenset[str, str], float]:
        _wall_Us = dict()
        for wall_side in self.wall_sides:
            zones: frozenset[str, str] = wall_side.zones
            if zones in _wall_Us:
                _wall_Us[zones] += wall_side.global_USs1_2
            else:
                _wall_Us[zones] = wall_side.global_USs1_2
        if zone1_name is not None and zone2_name is not None:
            return _wall_Us[frozenset((zone1_name, zone2_name))]
        return _wall_Us

    # def wall_capacitances(self, zone1_name: str = None, zone2_name: str = None) -> float | dict[frozenset[str, str], float]:
    #     _wall_Cs = dict()
    #     for wall_side in self.wall_sides:
    #         zones: frozenset[str, str] = wall_side.zones
    #         if zones in _wall_Cs:
    #             _wall_Cs[zones] += wall_side.global_Cs1_2
    #         else:
    #             _wall_Cs[zones] = wall_side.global_Cs1_2
    #     if zone1_name is not None and zone2_name is not None:
    #         return _wall_Cs[frozenset((zone1_name, zone2_name))]
    #     return _wall_Cs

    def wall_resistances(self, zone1_name: str = None, zone2_name: str = None):
        if zone1_name is not None and zone2_name is not None:
            return 1 / self.wall_transmitivities(zone1_name, zone2_name)
        else:
            _wall_transmitivities = self.wall_transmitivities()
            return {1 / _wall_transmitivities[zones] for zones in _wall_transmitivities}

    def wall_global_capacitances(self, zone1_name: str, zone2_name: str) -> Any | set[Any | float]:
        _wall_capacitance = 0
        wall = frozenset((zone1_name, zone2_name))
        for wall_side in self.wall_sides:
            if wall_side.zones == wall:
                _wall_capacitance += wall_side.global_Cs1_2
        return _wall_capacitance
        # _wall_capacitance = self.wall_transmitivities()
        # return {_wall_capacitance[zones] for zones in _wall_capacitance}

    @property
    def simulated_zone_names(self) -> list[str]:
        simulated_zone_names: list[str] = list()
        for zone in self.zone_names:
            if self.name_zones[zone].volume is not None:
                simulated_zone_names.append(self.name_zones[zone])
        return simulated_zone_names

    def zones_to_simulate(self, zone_name_volumes: dict[str, float]) -> None:
        """
        define a zone as for being simulated regarding CO2 concentration

        :param zone_name: name of the zone
        :type zone_name: str
        """
        for zone_name, zone_volume in zone_name_volumes.items():
            if zone_name not in self.name_zones:
                raise ValueError("Can't simulate the zone %s because it has not been created before" % zone_name)

            data_name = 'volume:' + zone_name
            if data_name not in self.data_provider and zone_volume is None:
                return
            if zone_volume is not None:
                self.data_provider.add_param(data_name, zone_volume)
            else:
                zone_volume = self.data_provider(data_name)
            self.name_zones[zone_name].set_volume(zone_volume)

        if hasattr(self, '_thermal_network_cache'):
            self._thermal_network_cache.clear()

    def layered_wall_side(self, zone1_name: str, zone2_name: str, side_type: SIDE_TYPES, surface: float) -> LayeredWallSide:
        """
        add a layered wall side between 2 zones

        :param zone1_name: first zone name
        :type zone1_name: str
        :param zone2_name: second zone name
        :type zone2_name: str
        :param side_type: type of wall side
        :type side_type: SideType
        :param surface: surface of the interface in m2
        :type surface: float
        :return: the layered wall side where the layers can be added from zone1 to zone2
        :rtype: LayeredWallSide
        """
        layered_side = LayeredWallSide(self.name_zones[zone1_name], self.name_zones[zone2_name], side_type, surface)
        self.layered_wall_sides.append(layered_side)
        return layered_side

    def block_wall_side(self, zone1_name: str, zone2_name: str, side_type: SIDE_TYPES, total_US: float, total_capacitance: float = None) -> BlockWallSide:
        """add a block wall side with only one layer and potentially no capacitance

        :param zone1_name: first zone name
        :type zone1_name: str
        :param zone2_name: seconde zone name
        :type zone2_name: str
        :param side_type: type of side
        :type side_type: SideType
        :param total_US: total transmission coefficient for the whole block side
        :type total_US: float
        :param total_capacitance: total capacitance for the whole block side, defaults to None
        :type total_capacitance: float, optional
        :return: the created block side
        :rtype: BlockSide
        """
        self.block_wall_sides.append(BlockWallSide(self.name_zones[zone1_name], self.name_zones[zone2_name], side_type, total_US, total_capacitance))

    def _build_thermal_network_base(self) -> ThermalNetwork:
        """
        Utility private method that transforms the geometrical description of a building, taking into account adjustment factors for model calibration, into a thermal network, from which a state model can be deduced. This method is called by the method 'make_state_model()' in Building.
        It has to be called anytime an adjustment factor is changed to regenerate a thermal network.

        :param side_Rfactor: adjustment multiplicative factors applying to the resulting resistances for the referred wall sides. It's a dictionary {(zone1, zone2): Rfactor1_2, (zone1, zone5): Rfactor1_5, ...}
        :type side_Rfactor: dict[tuple[str,str], float]
        :param side_Cfactor: adjustment multiplicative factors applying to the resulting capacitances for the referred wall sides. It's a dictionary {(zone1, zone2): Cfactor1_2, (zone1, zone5): Cfactor1_5, ...}
        :type side_Cfactor: dict[tuple[str,str], float]
        :param Vfactor: adjustment multiplicative factors applying to the specified zone. It's a dictionary {zone1: Vfactor1, zone2: Vfactor2, ...}
        :type Vfactor: dict[str,float]
        :return: the thermal network
        :rtype: buildingenergy.thermal.ThermalNetwork
        """
        thermal_network = ThermalNetwork()
        thermal_network.name_zones = self.name_zones
        air_properties: dict[str, float] = properties.get('air')
        rhoCp_air: float = air_properties['density'] * air_properties['Cp']

        for zone_name in self.name_zones:
            zone: Zone = self.name_zones[zone_name]
            if zone.zone_type == ZONE_TYPES.SIMULATED:
                thermal_network.T(zone.air_temperature_name, CAUSALITY.OUT)
                thermal_network.HEAT(T=zone.air_temperature_name, name=zone.heat_power_name)
                Cair: float = rhoCp_air * self.data_provider('volume:%s' % zone_name)
                thermal_network.C(toT=zone.air_temperature_name, name=zone.air_capacitance_name, val=Cair)
                thermal_network.register_zone_air(zone.name, zone.air_temperature_name)
            else:
                thermal_network.T(zone.air_temperature_name, CAUSALITY.IN)

        for wall_side in self.wall_sides:
            zone1_surface_added = False
            zone2_surface_added = False
            if ('%s-%s:Rfactor' % (wall_side.zone1.name, wall_side.zone2.name)) in self.data_provider:
                Rfactor = self.data_provider('%s-%s:Rfactor' % (wall_side.zone1.name, wall_side.zone2.name))
            else:
                Rfactor = 1
            if ('%s-%s:Cfactor' % (wall_side.zone1.name, wall_side.zone2.name)) in self.data_provider:
                Cfactor = self.data_provider('%s-%s:Cfactor' % (wall_side.zone1.name, wall_side.zone2.name))
            else:
                Cfactor = 1
            number_of_layers: int = len(wall_side.Rs1_2)
            layer_names, layer_border_names = name_layers(wall_side.zone1.air_temperature_name, wall_side.zone2.air_temperature_name, number_of_layers)
            for layer_index in range(number_of_layers):
                layer_left_temperature_name: str = layer_border_names[layer_index][0]
                middle_layer_temperature_name: str = layer_names[layer_index]
                layer_right_temperature_name: str = layer_border_names[layer_index][1]
                R = Rfactor * wall_side.Rs1_2[layer_index] / 2
                if wall_side.Cs1_2[layer_index] is None:
                    thermal_network.R(fromT=layer_left_temperature_name, toT=layer_right_temperature_name, val=2*R)
                else:
                    C = Cfactor * wall_side.Cs1_2[layer_index]
                    n_sublayers = 1
                    try:
                        n_sublayers: int = round(sqrt(pi * R * C / self.periodic_depth_seconds))
                    except:  # noqa
                        n_sublayers = 1
                    if n_sublayers <= 1:
                        if (
                            not zone1_surface_added
                            and wall_side.zone1.zone_type == ZONE_TYPES.SIMULATED
                            and (
                                layer_left_temperature_name == wall_side.zone1.air_temperature_name
                                or layer_left_temperature_name.startswith(f'{wall_side.zone1.air_temperature_name}-')
                            )
                        ):
                            thermal_network.T(middle_layer_temperature_name, CAUSALITY.OUT)
                            thermal_network.add_zone_surface(
                                wall_side.zone1.name, middle_layer_temperature_name, wall_side.surface, wall_side.side_type
                            )
                            zone1_surface_added = True
                        if (
                            not zone2_surface_added
                            and wall_side.zone2.zone_type == ZONE_TYPES.SIMULATED
                            and (
                                layer_right_temperature_name == wall_side.zone2.air_temperature_name
                                or layer_right_temperature_name.startswith(f'{wall_side.zone2.air_temperature_name}-')
                            )
                        ):
                            thermal_network.T(middle_layer_temperature_name, CAUSALITY.OUT)
                            thermal_network.add_zone_surface(
                                wall_side.zone2.name, middle_layer_temperature_name, wall_side.surface, wall_side.side_type
                            )
                            zone2_surface_added = True
                        thermal_network.R(fromT=layer_left_temperature_name, toT=middle_layer_temperature_name, val=R)
                        thermal_network.R(fromT=middle_layer_temperature_name, toT=layer_right_temperature_name, val=R)
                        thermal_network.C(toT=middle_layer_temperature_name, val=C)
                    else:
                        sublayer_names, sublayer_border_names = name_layers(layer_left_temperature_name, layer_right_temperature_name, n_sublayers)
                        R = Rfactor * wall_side.Rs1_2[layer_index] / 2 / n_sublayers
                        C = Cfactor * wall_side.Cs1_2[layer_index] / n_sublayers
                        for sublayer_index in range(n_sublayers):
                            sublayer_left_name: str = sublayer_border_names[sublayer_index][0]
                            sublayer_middle_name: str = sublayer_names[sublayer_index]
                            sublayer_right_name: str = sublayer_border_names[sublayer_index][1]
                            if (
                                not zone1_surface_added
                                and wall_side.zone1.zone_type == ZONE_TYPES.SIMULATED
                                and (
                                    sublayer_left_name == wall_side.zone1.air_temperature_name
                                    or sublayer_left_name.startswith(f'{wall_side.zone1.air_temperature_name}-')
                                )
                            ):
                                thermal_network.T(sublayer_middle_name, CAUSALITY.OUT)
                                thermal_network.add_zone_surface(
                                    wall_side.zone1.name, sublayer_middle_name, wall_side.surface, wall_side.side_type
                                )
                                zone1_surface_added = True
                            if (
                                not zone2_surface_added
                                and wall_side.zone2.zone_type == ZONE_TYPES.SIMULATED
                                and (
                                    sublayer_right_name == wall_side.zone2.air_temperature_name
                                    or sublayer_right_name.startswith(f'{wall_side.zone2.air_temperature_name}-')
                                )
                            ):
                                thermal_network.T(sublayer_middle_name, CAUSALITY.OUT)
                                thermal_network.add_zone_surface(
                                    wall_side.zone2.name, sublayer_middle_name, wall_side.surface, wall_side.side_type
                                )
                                zone2_surface_added = True
                            thermal_network.R(fromT=sublayer_left_name, toT=sublayer_middle_name, val=R)
                            thermal_network.R(fromT=sublayer_middle_name, toT=sublayer_right_name, val=R)
                            thermal_network.C(toT=sublayer_middle_name, val=C)
        return thermal_network

    def make_thermal_network_k(self, fingerprint: int | str | tuple | list | None = None) -> ThermalNetwork:
        if fingerprint is None:
            cache_key: int | str | tuple = 'nominal'
        elif isinstance(fingerprint, list):
            cache_key = tuple(fingerprint)
        else:
            cache_key = fingerprint

        if cache_key not in self._thermal_network_cache:
            base_network = self._build_thermal_network_base()
            self._thermal_network_cache[cache_key] = base_network
            node_count = len(base_network.nodes)
            edge_count = len(base_network.edges)
            state_count = len(base_network.temperatures_state)
        else:
            base_network = self._thermal_network_cache[cache_key]

        thermal_network = copy.deepcopy(base_network)
        self.thermal_network = thermal_network
        return thermal_network

    def __str__(self) -> str:
        string = 'Zones are:\n'
        for zone in self.name_zones:
            string += str(self.name_zones[zone])
        string += 'Wall sides are:\n'
        for wall_side in self.wall_sides:
            string += str(wall_side)
        return string
