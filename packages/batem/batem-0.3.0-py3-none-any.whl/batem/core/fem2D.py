"""2D Finite Element Method (FEM) module for heat transfer analysis in building components.

This module provides a comprehensive implementation of the finite element method for
solving 2D heat transfer problems in building components. It implements triangular
elements with linear shape functions for steady-state heat conduction analysis,
including boundary conditions, material properties, and thermal constraints.

The module provides:
- Node: Geometric nodes with temperature and coordinate management
- Properties: Material properties including thermal conductivity and heat sources
- Boundary: Boundary condition definitions (Dirichlet, Neumann, convection)
- Element: Triangular finite elements with shape functions and integration
- Problem: Main FEM problem solver with mesh generation and assembly
- Constraint: Boundary constraint definitions for different edge types
- Rectangle: Rectangular domain definition and mesh generation
- Assembly: Complete assembly management for complex geometries
- Predefined functions: Ready-to-use building component configurations

Key features:
- Triangular element mesh generation with automatic refinement
- Linear shape functions for temperature interpolation
- Support for Dirichlet (fixed temperature) and Neumann (fixed flux) boundary conditions
- Convection boundary conditions with ambient temperature
- Material property management with thermal conductivity and heat sources
- Automatic mesh assembly and global stiffness matrix construction
- Temperature field visualization and plotting capabilities
- Predefined building component configurations (walls, insulation, floors)
- Integration with Stefan-Boltzmann law for radiation effects
- Support for complex geometries with multiple material regions

The module is designed for building energy analysis, thermal bridge calculations,
and heat transfer studies in building components and construction elements.

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0
"""
from __future__ import annotations
from math import sqrt
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
from matplotlib import cm
from matplotlib.tri import Triangulation
import numpy
import numpy.linalg
from scipy.constants import Stefan_Boltzmann


class Node:

    existing_nodes: list['Node'] = list()

    @classmethod
    def get(cls, x: float, y: float) -> 'Node':
        for node in Node.existing_nodes:
            if node.is_similar(x, y):
                return node
        new_node: Node = Node(x, y)
        Node.existing_nodes.append(new_node)
        return new_node

    def __init__(self, x: float, y: float) -> None:  # don't call it directly: use Node.get(x, y)
        self.x: float = x
        self.y: float = y
        self.id: int | None = None
        self.temperature: None | float = None
        Node.existing_nodes.append(self)

    def assigned(self) -> bool:
        return self.temperature is not None

    def is_similar(self, x: float, y: float) -> bool:
        return self.x == x and self.y == y

    def distance(self, node: 'Node') -> float:
        return sqrt((self.x - node.x) * (self.x - node.x) + (self.y - node.y) * (self.y - node.y))

    def __str__(self) -> str:
        _str: str = 'node x={}, y={}, '.format(self.x, self.y)
        _str += 'id = %s, ' % (self.id) if self.id is not None else 'no id, '
        _str += 'assigned value = ' + str(self.temperature) if self.temperature is not None else 'no assigned value'
        return _str


class Properties:

    def __init__(self, conductivity: float, source: float = 0):
        self.conductivity: float = conductivity
        self.source: float = source

    def __str__(self) -> str:
        return '(conductivity: %fW/m.K, source: %fW/m)' % (self.conductivity, self.source)


class Boundary:

    def __init__(self, node1: Node, node2: Node, dirichlet_temperature: float | None = None, neumann_flux: float | None = None, temperature_at_infinity: float | None = None, convection: float | None = None):
        self.node1: Node = node1
        self.node2: Node = node2
        self.edge: frozenset[Node] = frozenset({node1, node2})
        self.dirichlet_temperature: float | None = dirichlet_temperature
        self.neumann_flux: float | None = neumann_flux
        self.temperature_at_infinity: float | None = temperature_at_infinity
        self.convection: float | None = convection
        if self.dirichlet_temperature is not None:
            self.node1.temperature = dirichlet_temperature
            self.node2.temperature = dirichlet_temperature

    def is_diriclet(self) -> bool:
        return self.dirichlet_temperature is not None

    def is_neumann(self) -> bool:
        return self.neumann_flux is not None

    def is_convection(self) -> bool:
        return self.convection is not None

    def split(self, mid_node) -> tuple['Boundary', 'Boundary']:
        if self.dirichlet_temperature is not None:
            mid_node.temperature = self.dirichlet_temperature
        sub_boundary1: Boundary = Boundary(self.node1, mid_node, self.dirichlet_temperature, self.neumann_flux, self.temperature_at_infinity, self.convection)
        sub_boundary2: Boundary = Boundary(mid_node, self.node2, self.dirichlet_temperature, self.neumann_flux, self.temperature_at_infinity, self.convection)
        return sub_boundary1, sub_boundary2

    def __str__(self) -> str:
        _str = 'Boundary on nodes (' + self.node1.__str__() + ',' + self.node2.__str__() + ') is '
        if self.is_diriclet():
            return _str + 'Diriclet with T=%f°C' % self.dirichlet_temperature
        elif self.is_neumann():
            return _str + 'Neumann with phi=%fW/m' % self.neumann_flux
        elif self.is_convection():
            return _str + 'Convection with h=%f and Tinf=%f' % (self.convection, self.temperature_at_infinity)
        else:
            return _str + 'None'


class Element:

    def __init__(self, nodes: tuple[Node, Node, Node], property: Properties) -> None:
        self.property: Properties = property
        self.nodes: tuple[Node, Node, Node] = nodes
        if self.area() < 0:
            self.nodes = (self.nodes[0], self.nodes[1], self.nodes[2])
        self.boundaries: dict[frozenset[Node], Boundary] = dict()

    def add_boundary(self, node1: Node, node2: Node, dirichlet_temperature: float | None = None, neumann_flux: float | None = None, temperature_at_infinity: float | None = None, convection: float | None = None, constraint=None) -> None:
        if constraint is not None:
            boundary: Boundary = Boundary(node1, node2, dirichlet_temperature=constraint.dirichlet_temperature, neumann_flux=neumann_flux, temperature_at_infinity=constraint.temperature_at_infinity, convection=constraint.convection)
        else:
            boundary: Boundary = Boundary(node1, node2, dirichlet_temperature, neumann_flux, temperature_at_infinity, convection)
        self.boundaries[boundary.edge] = boundary
        if boundary.dirichlet_temperature is not None:
            for node in boundary.edge:
                node.temperature = boundary.dirichlet_temperature

    def _add_boundaries(self, boundaries: list[Boundary]) -> None:
        for boundary in boundaries:
            if set(boundary.edge).issubset(set(self.nodes)):
                self.boundaries[boundary.edge] = boundary
                if boundary.dirichlet_temperature is not None:
                    for node in boundary.edge:
                        node.temperature = boundary.dirichlet_temperature

    def center(self) -> tuple[float, float]:
        return sum([node.x for node in self.nodes])/3, sum([node.y for node in self.nodes])/3

    def temperature(self, x: float | None = None, y: float | None = None) -> float:
        if x is None or y is None:
            x, y = self.center()
        return sum([self.phis(x, y)[i] * self.nodes[i].temperature for i in range(3)])

    def gradient_temperature(self, x: float | None = None, y: float | None = None) -> tuple[float, float]:
        if x is None or y is None:
            x, y = self.center()
        gradient_x: float = 0
        gradient_y: float = 0
        for i in range(len(self.nodes)):
            gradient_x += self.nodes[i].temperature * self.grad_phis()[i][0]
            gradient_y += self.nodes[i].temperature * self.grad_phis()[i][1]
        return gradient_x, gradient_y

    def heatflow_on_edge(self):
        conductivity: float = self.property.conductivity
        edges = ((self.nodes[0], self.nodes[1]), (self.nodes[1], self.nodes[2]), (self.nodes[2], self.nodes[0]))
        phi_edges = list()
        for edge in edges:
            node_inf, node_sup = edge
            center_edge: tuple[float, float] = (node_inf.x + node_sup.x)/2, (node_inf.y + node_sup.y)/2
            # denom: float = sqrt((node_sup.x-node_inf.x)**2 + (node_sup.y-node_inf.y)**2)
            normal_edge: tuple[float, float] = (- (node_sup.y-node_inf.y), (node_sup.x-node_inf.x))  # /denom)
            gradT_edge: tuple[float, float] = self.gradient_temperature(center_edge)
            phi_edges.append(- conductivity * (gradT_edge[0]*normal_edge[0] + gradT_edge[1]*normal_edge[1]))
        return {edges[i]: phi_edges[i] for i in range(len(edges))}

    def get_diriclet_edge_temperature_heatflows(self):
        _diriclet_edge_temperature_heatflows: dict[edge, tuple[float, float]] = dict()  # type: ignore

        _heatflow_on_edge = self.heatflow_on_edge()
        for edge in self.boundaries:
            boundary: Boundary = self.boundaries[edge]
            if boundary.is_diriclet():
                node1, node2 = tuple(edge)
                if (node2, node1) in _heatflow_on_edge:
                    node1, node2 = node2, node1
                if (node1, node2) in _heatflow_on_edge:
                    _diriclet_edge_temperature_heatflows[(node1, node2)] = (boundary.dirichlet_temperature, _heatflow_on_edge[(node1, node2)])  # type: ignore
        return _diriclet_edge_temperature_heatflows

    def area(self) -> float:
        return ((self.nodes[1].x - self.nodes[0].x) * (self.nodes[2].y - self.nodes[0].y) - (self.nodes[2].x - self.nodes[0].x) * (self.nodes[1].y - self.nodes[0].y)) / 2

    def phis(self, x: float | None = None, y: float | None = None) -> tuple[float, float, float]:
        if x is None or y is None:
            x, y = self.center()
        x1, y1 = self.nodes[0].x, self.nodes[0].y
        x2, y2 = self.nodes[1].x, self.nodes[1].y
        x3, y3 = self.nodes[2].x, self.nodes[2].y
        phi0: float = ((y3 - y2) * (x2 - x) - (x3 - x2) * (y2 - y)) / self.area() / 2
        phi1: float = ((y1 - y3) * (x3 - x) - (x1 - x3) * (y3 - y)) / self.area() / 2
        phi2: float = ((y2 - y1) * (x1 - x) - (x2 - x1) * (y1 - y)) / self.area() / 2
        return (phi0, phi1, phi2)

    def grad_phis(self) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        _grad_phis: list[float] = list()
        x1, y1 = self.nodes[0].x, self.nodes[0].y
        x2, y2 = self.nodes[1].x, self.nodes[1].y
        x3, y3 = self.nodes[2].x, self.nodes[2].y
        _grad_phis.append(((y2 - y3) / self.area() / 2, (x3 - x2) / self.area() / 2))
        _grad_phis.append(((y3 - y1) / self.area() / 2, (x1 - x3) / self.area() / 2))
        _grad_phis.append(((y1 - y2) / self.area() / 2, (x2 - x1) / self.area() / 2))
        return tuple(_grad_phis)

    def m_ij(self) -> dict[tuple[int, int], float]:
        _grad_phis: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] = self.grad_phis()
        elementary_matrix: dict[tuple[int, int], float] = dict()
        for i in range(3):
            for j in range(3):
                elementary_matrix[(self.nodes[i].id, self.nodes[j].id)] = self.property.conductivity * self.area() * (_grad_phis[i][0] * _grad_phis[j][0] + (_grad_phis[i][1] * _grad_phis[j][1]))  # type: ignore
        return elementary_matrix

    def n_j(self) -> dict[int, float]:
        element_vector: dict[int, float] = dict()
        for i in range(3):
            element_vector[self.nodes[i].id] = self.property.source * self.area() / 3.0  # type: ignore
        return element_vector

    def divide(self) -> tuple['Element', 'Element', 'Element', 'Element']:
        node0, node1, node2 = self.nodes
        if (node0.x == 0 and node1.x == 0) or (node1.x == 0 and node2.x == 0) or (node2.x == 0 and node0.x == 0):
            pass
        node3 = Node.get((node0.x + node1.x) / 2, (node0.y + node1.y) / 2)
        node4: Node = Node.get((node1.x + node2.x) / 2, (node1.y + node2.y) / 2)
        node5 = Node.get((node2.x + node0.x) / 2, (node2.y + node0.y) / 2)
        element035: Element = Element((node0, node3, node5), self.property)
        element314: Element = Element((node3, node1, node4), self.property)
        element542: Element = Element((node5, node4, node2), self.property)
        element534: Element = Element((node5, node3, node4), self.property)
        if frozenset({node0, node1}) in self.boundaries:
            boundaries: tuple[Boundary, Boundary] = self.boundaries[frozenset({node0, node1})].split(node3)  # type: ignore
            element035._add_boundaries(boundaries)
            element314._add_boundaries(boundaries)
        if frozenset({node1, node2}) in self.boundaries:
            boundaries = self.boundaries[frozenset({node1, node2})].split(node4)  # type: ignore
            element314._add_boundaries(boundaries)
            element542._add_boundaries(boundaries)
        if frozenset({node2, node0}) in self.boundaries:
            boundaries = self.boundaries[frozenset({node2, node0})].split(node5)  # type: ignore
            element542._add_boundaries(boundaries)
            element035._add_boundaries(boundaries)
        return element035, element314, element542, element534

    def __str__(self) -> str:
        string: str = '* Element  \nN1:%s\nN2:%s\nN3:%s\n' % (self.nodes[0].__str__(), self.nodes[1].__str__(), self.nodes[2].__str__())
        for edge in self.boundaries:
            string += '> ' + self.boundaries[edge].__str__() + '\n'  # type: ignore
        for i in range(3):
            string += 'phi%i=' % (i+1) + str(self.phis()[i]) + '\n'
        for i in range(3):
            for j, coord in enumerate(['x', 'y']):
                string += 'grad_%s phi%i=' % (coord, i+1) + self.grad_phis()[i][j].__str__() + '\n'
        return string


class Problem:

    def __init__(self, *elements: Element, n_splits: int) -> None:
        self.elements: list[Element] = list(elements)
        self.constrained_temperature_nodes: set[Node] = set()
        self.solved: bool = False
        self.nodes: list[Node] = list()
        self._mesh(n_splits)
        for element in self.elements:
            for node in element.nodes:
                if node not in self.nodes:
                    self.nodes.append(node)

    def _mesh(self, n_divisions: int) -> None:
        for _ in range(n_divisions):
            divided_elements: list[Element] = list()
            while len(self.elements) > 0:
                divided_elements.extend(self.elements.pop().divide())
            self.elements = divided_elements

    def solve(self, display: bool = True) -> None:
        self.free_nodes: list[Node] = list()
        self.assigned_nodes: list[Node] = list()
        for node in self.nodes:
            if node.assigned():
                self.assigned_nodes.append(node)
                self.constrained_temperature_nodes.add(node)
            else:
                self.free_nodes.append(node)
        for i in range(len(self.free_nodes)):
            self.free_nodes[i].id = i
        for i in range(len(self.assigned_nodes)):
            self.assigned_nodes[i].id = len(self.free_nodes) + i
        Mij_ndarray: numpy.ndarray = numpy.zeros((len(self.free_nodes), len(self.free_nodes)))
        Nj_ndarray: numpy.ndarray = numpy.zeros((len(self.free_nodes), 1))

        for element in self.elements:
            mij_terms: dict[tuple[int, int], float] = element.m_ij()
            nj_terms: dict[int, float] = element.n_j()
            for j in nj_terms:
                if j < len(self.free_nodes):  # type: ignore
                    Nj_ndarray[j] += nj_terms[j]
            for ij_indices in mij_terms:
                i, j = ij_indices
                if i < len(self.free_nodes):
                    if j < len(self.free_nodes):
                        Mij_ndarray[i, j] += mij_terms[ij_indices]
                    else:
                        Nj_ndarray[i, 0] -= mij_terms[ij_indices] * self.assigned_nodes[j-len(self.free_nodes)].temperature  # type: ignore
            for edge in element.boundaries:
                boundary: Boundary = element.boundaries[edge]
                # print(boundary)
                node1: Node = boundary.node1
                node2: Node = boundary.node2
                edge_length: float = node1.distance(node2)
                if boundary.is_convection():
                    self.constrained_temperature_nodes.add(node1)
                    self.constrained_temperature_nodes.add(node2)
                    Mij_ndarray[node1.id, node1.id] += boundary.convection * edge_length / 3.0
                    Mij_ndarray[node2.id, node2.id] += boundary.convection * edge_length / 3.0
                    Mij_ndarray[node1.id, node2.id] += boundary.convection * edge_length / 6.0
                    Mij_ndarray[node2.id, node1.id] += boundary.convection * edge_length / 6.0
                    Nj_ndarray[node1.id, 0] += boundary.convection * boundary.temperature_at_infinity * edge_length / 2.0
                    Nj_ndarray[node2.id, 0] += boundary.convection * boundary.temperature_at_infinity * edge_length / 2.0

                if boundary.is_neumann():
                    if node1.id < len(self.free_nodes):
                        Nj_ndarray[node1.id] += boundary.neumann_flux * edge_length / 2.0
                    if node2.id < len(self.free_nodes):
                        Nj_ndarray[node2.id] += boundary.neumann_flux * edge_length / 2.0

        solution: numpy.ndarray = numpy.linalg.solve(Mij_ndarray, Nj_ndarray)
        for i in range(len(self.free_nodes)):
            self.free_nodes[i].temperature = solution[i, 0]
        self.solved = True

        if display:
            print('global matrix:')
            print(Mij_ndarray)
            print('global vector:')
            print(Nj_ndarray)
            print('solution for temperatures:')

    def energy(self) -> float:
        if not self.solved:
            raise PermissionError('Solve the problem before calling')
        energy: float = 0
        for element in self.elements:
            [ex, ey] = element.gradient_temperature(None, None)
            energy += (ex * ex + ey * ey) * element.area() * element.property.conductivity
        return energy

    def solution(self) -> dict[str, float]:
        temperatures_heatflows = dict()
        for element in self.elements:
            diriclet_edge_temperature_heatflows = element.get_diriclet_edge_temperature_heatflows()
            if len(diriclet_edge_temperature_heatflows) != 0:
                for edge in diriclet_edge_temperature_heatflows:
                    temperature, heatflow = diriclet_edge_temperature_heatflows[edge]
                    if temperature not in temperatures_heatflows:
                        temperatures_heatflows[temperature] = heatflow
                    else:
                        temperatures_heatflows[temperature] += heatflow
        temperature1, temperature2 = tuple(temperatures_heatflows.keys())
        if temperature1 < temperature2:
            temperature2, temperature1 = temperature1, temperature2
        if len(temperatures_heatflows) != 2:
            raise ValueError('Abnormal constrained temperatures: 2 are required instead of %i > %s' % (len(temperatures_heatflows), ','.join([str(T) for T in (temperature1, temperature2)])))
        heatflow = temperatures_heatflows[temperature1] if temperatures_heatflows[temperature1] >= 0 else temperatures_heatflows[temperature2]

        return {'resistance': (temperature1 - temperature2) / heatflow, 'temperature1': temperature1, 'temperature2': temperature2, 'heatflow': heatflow}
        # return (temperature2-temperature1) ** 2 / self.energy()

    def get_node_coordinates(self) -> list:
        return [(node.x, node.y) for node in self.nodes]

    def get_node_temperatures(self) -> list:
        return [node.temperature for node in self.nodes]

    def __str__(self) -> str:
        return 'Problem:\n' + '\n'.join(e.__str__() for e in self.elements)

    def plot(self) -> None:
        X: list[float] = list()
        Y: list[float] = list()
        T: list[float] = list()
        nodes: list[Node] = list()
        triangles: list[list[int]] = list()
        for node in self.nodes:
            nodes.append(node)
            X.append(node.x)
            Y.append(node.y)
            T.append(node.temperature)  # type: ignore
        for element in self.elements:
            triangle: list[int] = list()
            for node in element.nodes:
                triangle.append(nodes.index(node))
            triangles.append(triangle)
        triangulation: Triangulation = Triangulation(X, Y, triangles)

        fig, ax = plt.subplots(subplot_kw={'projection': '3d'})
        # ax: = plt.axes(projection='3d')
        ax.plot_trisurf(X, Y, T, triangles=triangulation.triangles, linewidth=0.2, antialiased=True, cmap=cm.coolwarm)  # type: ignore
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        # ax.axis('equal')
        ax.set_zlabel('temperature')
        fig.tight_layout()
        plt.show()


class Constraint:

    def __init__(self, position: str, temperature: float | None = None, flux: float | None = None, temperature_at_infinity: float | None = None, convection: float | None = None) -> None:
        if position not in ('LEFT', 'RIGHT', 'UP', 'DOWN'):
            raise ValueError('Unknown position: %s' % position)
        self.position = position
        self.dirichlet_temperature: float | None = temperature
        self.neumann_flux: float | None = flux
        self.temperature_at_infinity: float | None = temperature_at_infinity
        self.convection: float | None = convection

    def is_dirichlet(self) -> bool:
        return self.dirichlet_temperature is not None

    def is_neumann(self) -> bool:
        return self.neumann_flux is not None

    def is_convection(self) -> bool:
        return self.temperature_at_infinity is not None and self.convection is not None

    def edge(self, rectangle: 'Rectangle'):
        if self.position == 'LEFT':
            return (rectangle.ll_x, rectangle.ll_y), (rectangle.ll_x, rectangle.ur_y)
        if self.position == 'RIGHT':
            return (rectangle.ur_x, rectangle.ll_y), (rectangle.ur_x, rectangle.ur_y)
        if self.position == 'UP':
            return (rectangle.ll_x, rectangle.ur_y), (rectangle.ur_x, rectangle.ur_y)
        if self.position == 'DOWN':
            return (rectangle.ll_x, rectangle.ll_y), (rectangle.ur_x, rectangle.ll_y)


class Rectangle:

    def __init__(self, ll_corner: tuple[float, float], ur_corner: tuple[float, float], properties: Properties, *constraints: Constraint) -> None:
        self.ll_x, self.ll_y = ll_corner
        self.ur_x, self.ur_y = ur_corner
        self.constraints: dict[str, Constraint] = {constraint.position: constraint for constraint in constraints}
        self.sub_rectangles = [self]
        self.properties = properties

    def remaining_constraints(self, position_to_remove: str) -> dict[str, Constraint]:
        constraints = list()
        for position in self.constraints:
            if position != position_to_remove:
                constraints.append(self.constraints[position])
        return constraints

    def _x_split(self) -> tuple['Rectangle', 'Rectangle']:
        mid_x: float = (self.ll_x + self.ur_x) / 2
        rectangle_left = Rectangle((self.ll_x, self.ll_y), (mid_x, self.ur_y), self.properties, *self.remaining_constraints('RIGHT'))
        rectangle_right = Rectangle((mid_x, self.ll_y), (self.ur_x, self.ur_y), self.properties, *self.remaining_constraints('LEFT'))
        return rectangle_left, rectangle_right

    def _y_split(self) -> tuple['Rectangle', 'Rectangle']:
        mid_y: float = (self.ll_y + self.ur_y) / 2
        rectangle_down = Rectangle((self.ll_x, self.ll_y), (self.ur_x, mid_y), self.properties, *self.remaining_constraints('UP'))
        rectangle_up = Rectangle((self.ll_x, mid_y), (self.ur_x, self.ur_y), self.properties, *self.remaining_constraints('DOWN'))
        return rectangle_down, rectangle_up

    def get_sub_elements(self) -> Element:
        node_ll, node_lr, node_ul, node_ur = Node.get(self.ll_x, self.ll_y), Node.get(self.ur_x, self.ll_y), Node.get(self.ll_x, self.ur_y), Node.get(self.ur_x, self.ur_y)

        element_ll = Element((node_ll, node_lr, node_ul), self.properties)
        element_ur = Element((node_lr, node_ur, node_ul), self.properties)

        for position in self.constraints:
            if position == 'LEFT':
                element_ll.add_boundary(node_ll, node_ul, dirichlet_temperature=self.constraints[position].dirichlet_temperature, neumann_flux=self.constraints[position].neumann_flux, temperature_at_infinity=self.constraints[position].temperature_at_infinity, convection=self.constraints[position].convection)
            if position == 'RIGHT':
                element_ur.add_boundary(node_lr, node_ur, constraint=self.constraints[position])
            if position == 'UP':
                element_ur.add_boundary(node_ul, node_ur, constraint=self.constraints[position])
            if position == 'DOWN':
                element_ll.add_boundary(node_ll, node_lr, constraint=self.constraints[position])
        return element_ll, element_ur

    def divide(self, x_split: int = 0, y_split: int = 0):
        if x_split > 0:
            new_rectangles = list()
            for rectangle in self.sub_rectangles:
                rectangle1, rectangle2 = rectangle._x_split()
                new_rectangles.append(rectangle1)
                new_rectangles.append(rectangle2)
            self.sub_rectangles = new_rectangles
            self.divide(x_split-1, y_split)
        elif y_split > 0:
            new_rectangles = list()
            for rectangle in self.sub_rectangles:
                rectangle1, rectangle2 = rectangle._y_split()
                new_rectangles.append(rectangle1)
                new_rectangles.append(rectangle2)
            self.sub_rectangles = new_rectangles
            self.divide(x_split, y_split-1)
        else:
            return

    def get_elements(self):
        elements = list()
        for rectangle in self.sub_rectangles:
            for e in rectangle.get_sub_elements():
                elements.append(e)
        return elements

    def shape(self):
        return plt.Rectangle((self.ll_x, self.ll_y), self.ur_x-self.ll_x, self.ur_y-self.ll_y, ec='black', fc=None)

    def points(self):
        return (self.ll_x, self.ll_y), (self.ll_x, self.ur_y), (self.ur_x, self.ll_y), (self.ur_x, self.ur_y)

    def free_points(self):
        if len(self.constraints) == 0:
            return self.points()
        if len(self.constraints) == 2:
            if 'DOWN' in self.constraints and 'LEFT' in self.constraints:
                return (self.ur_x, self.ur_y),
            if 'DOWN' in self.constraints and 'RIGHT' in self.constraints:
                return (self.ll_x, self.ur_y),
            if 'UP' in self.constraints and 'LEFT' in self.constraints:
                return (self.ur_x, self.ll_y),
            if 'UP' in self.constraints and 'RIGHT' in self.constraints:
                return (self.ll_x, self.ll_y),
        if len(self.constraints) == 1:
            if 'DOWN' in self.constraints:
                return (self.ll_x, self.ur_y), (self.ur_x, self.ur_y)
            if 'UP' in self.constraints:
                return (self.ll_x, self.ll_y), (self.ur_x, self.ll_y)
            if 'LEFT' in self.constraints:
                return (self.ur_x, self.ll_y), (self.ur_x, self.ur_y)
            if 'RIGHT' in self.constraints:
                return (self.ll_x, self.ll_y), (self.ll_x, self.ur_y)
        return ()

    def boundary_colors(constraint: Constraint):
        if constraint.is_dirichlet():
            return 'red'
        elif constraint.is_neumann():
            return 'yellow'
        elif constraint.is_convection():
            return 'green'
        else:
            return 'black'

    def constraint_lines(self):
        _boundary_lines = list()
        for position, point1, point2 in self.constraint_edges():
            constraint: Constraint = self.constraints[position]
            if point1[0] == point2[0]:
                _boundary_lines.append(plt.Rectangle(point1, (self.ur_x-self.ll_x)/100, point2[1]-point1[1], ec=Rectangle.boundary_colors(constraint), fc=Rectangle.boundary_colors(constraint)))
            elif point1[1] == point2[1]:
                _boundary_lines.append(plt.Rectangle(point1, point2[0]-point1[0], (self.ur_y-self.ll_y)/100, ec=Rectangle.boundary_colors(constraint), fc=Rectangle.boundary_colors(constraint)))
        return _boundary_lines

    def constraint_edges(self):
        edges: list[str, tuple[float, float], tuple[float, float]] = list()
        for position in self.constraints:
            edges.append((position, *self.constraints[position].edge(self)))
        return edges

    def __str__(self) -> str:
        return "[Rectangle (%s,%s)~(%s,%s)]: " % (self.ll_x, self.ll_y, self.ur_x, self.ur_y) + ','.join([str(_) for _ in self.constraint_edges()])


class Assembly:

    def __init__(self) -> None:
        Node.existing_nodes = list()
        self.rectangles = list()
        self.problem = None

    def add(self, rectangle: Rectangle):
        self.rectangles.extend(rectangle.sub_rectangles)

    def check(self):
        point_occurrences: dict[tuple[float, float], int] = dict()
        for rectangle in self.rectangles:
            for point in rectangle.points():
                if point not in point_occurrences:
                    point_occurrences[point] = 1
                else:
                    point_occurrences[point] += 1
        error: bool = False
        for rectangle in self.rectangles:
            free_points = rectangle.free_points()
            if len(free_points) > 0:
                for point in free_points:
                    if point_occurrences[point] < 2:
                        error = True
                        print('isolated point:', str(point))
        if error:
            raise ValueError('presence of isolated points')

    def get_elements(self) -> list[Element]:
        elements = list()
        for rectangle in self.rectangles:
            elements.extend(rectangle.get_elements())
        return elements

    def solve(self, n_triangle_splits: int = 3):
        self.check()
        self.problem: Problem = Problem(*self.get_elements(), n_splits=n_triangle_splits)
        self.problem.solve(display=False)
        solution: dict[str, float] = self.problem.solution()
        print('heatflow: %f W' % solution['heatflow'])
        print('temperatures: %f°C, %f°C' % (solution['temperature1'], solution['temperature2']))
        return solution

    def print_grid(self):
        print('Grid is:')
        xs, ys = list(), list()
        for rectangle in self.rectangles:
            if rectangle.ll_x not in xs:
                xs.append(rectangle.ll_x)
            if rectangle.ur_x not in xs:
                xs.append(rectangle.ur_x)
            if rectangle.ll_y not in ys:
                ys.append(rectangle.ll_y)
            if rectangle.ur_y not in ys:
                ys.append(rectangle.ur_y)
        xs.sort()
        ys.sort()
        print('x_grid='+','.join([str(x) for x in xs]))
        print('y_grid='+','.join([str(y) for y in ys]))
        return xs, ys

    def design_plot(self):
        xs, ys = self.print_grid()
        fig, ax = plt.subplots()
        ax.xaxis.grid(True)
        ax.set_xticks(xs)
        ax.set_xticklabels(xs)
        ax.yaxis.grid(True)
        ax.set_yticks(ys)
        ax.set_yticklabels(ys)
        for rectangle in self.rectangles:
            ax.add_patch(rectangle.shape())
            for boundary_line in rectangle.constraint_lines():
                ax.add_patch(boundary_line)
        plt.axis('scaled')
        plt.show()

    def solution_plot(self):
        self.problem.plot()


def concrete_wall(french: bool = False):
    assembly = Assembly()
    concrete = Properties(conductivity=1)
    conductivity_vert_1cm_i = Properties(conductivity=0.01 * (7.69 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))
    conductivity_1cm_e = Properties(conductivity=0.01 * (25 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 13)**3)))
    # conductivity_horiz_1cm_i = Properties(conductivity=0.01 * (5.88 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))
    n_rectangle_splits = 3
    n_triangle_splits = 3
    if not french:
        wall = Rectangle((1.00, -1.00), (1.10, 1.13), concrete, Constraint('UP', flux=0), Constraint('DOWN', flux=0))
        left_insulation = Rectangle((0.99, -1), (1.0, 1.13), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('UP', flux=0), Constraint('DOWN', flux=0))
        right_insulation = Rectangle((1.1, -1), (1.11, 1.13), conductivity_1cm_e,  Constraint('RIGHT', temperature=0), Constraint('UP', flux=0), Constraint('DOWN', flux=0))
    else:
        wall = Rectangle((1.00, -1.00), (1.10, 1.00), concrete, Constraint('UP', flux=0), Constraint('DOWN', flux=0))
        left_insulation = Rectangle((0.99, -1), (1.0, 1.00), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('UP', flux=0), Constraint('DOWN', flux=0))
        right_insulation = Rectangle((1.1, -1), (1.11, 1.00), conductivity_1cm_e,  Constraint('RIGHT', temperature=0), Constraint('UP', flux=0), Constraint('DOWN', flux=0))

    wall.divide(x_split=0, y_split=n_rectangle_splits)
    left_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    right_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(wall)
    assembly.add(left_insulation)
    assembly.add(right_insulation)
    assembly.design_plot()
    assembly.solve(n_triangle_splits=n_triangle_splits)
    return assembly


def concrete_wall_with_insulation(partial: bool = False):
    assembly = Assembly()
    concrete = Properties(conductivity=1)
    insulation = Properties(conductivity=0.05)
    conductivity_vert_1cm_i = Properties(conductivity=0.01 * (7.69 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))
    conductivity_1cm_e = Properties(conductivity=0.01 * (25 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 13)**3)))
    # conductivity_horiz_1cm_i = Properties(conductivity = 0.01 * ( 5.88 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))

    n_rectangle_splits = 3
    n_triangle_splits = 3

    if not partial:
        wall = Rectangle((1.00, -1.00), (1.10, 1.13), concrete, Constraint('UP', flux=0), Constraint('DOWN', flux=0))
        outdoor_insulation = Rectangle((1.1, -1), (1.3, 1.13), insulation, Constraint('RIGHT', temperature=0), Constraint('UP', flux=0), Constraint('DOWN', flux=0))
        left_insulation = Rectangle((0.99, -1), (1.0, 1.13), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('UP', flux=0), Constraint('DOWN', flux=0))
        right_insulation = Rectangle((1.3, -1), (1.31, 1.13), conductivity_1cm_e,  Constraint('RIGHT', temperature=0), Constraint('UP', flux=0), Constraint('DOWN', flux=0))
    else:
        wall = Rectangle((1.00, -1.00), (1.10, 1.0), concrete, Constraint('UP', flux=0), Constraint('DOWN', flux=0))
        outdoor_insulation = Rectangle((1.1, -1), (1.3, 1.0), insulation, Constraint('RIGHT', temperature=0), Constraint('UP', flux=0), Constraint('DOWN', flux=0))
        left_insulation = Rectangle((0.99, -1), (1.0, 1.0), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('UP', flux=0), Constraint('DOWN', flux=0))
        right_insulation = Rectangle((1.3, -1), (1.31, 1.0), conductivity_1cm_e,  Constraint('RIGHT', temperature=0), Constraint('UP', flux=0), Constraint('DOWN', flux=0))

    wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(wall)
    outdoor_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(outdoor_insulation)
    left_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(left_insulation)
    right_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(right_insulation)

    assembly.design_plot()
    assembly.solve(n_triangle_splits=n_triangle_splits)
    return assembly


def concrete_wall_with_intermediate_floor():
    assembly = Assembly()
    concrete = Properties(conductivity=1)
    # insulation = Properties(conductivity=0.05)
    conductivity_vert_1cm_i = Properties(conductivity=0.01 * (7.69 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))
    conductivity_1cm_e = Properties(conductivity=0.01 * (25 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 13)**3)))
    conductivity_horiz_1cm_i = Properties(conductivity=0.01 * (5.88 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))

    n_rectangle_splits = 3
    n_triangle_splits = 3

    floor: Rectangle = Rectangle((0, 0), (1.00, .13), concrete, Constraint('LEFT', flux=0))
    floor.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor)

    floor_upper = Rectangle((0, 0.13), (1.00, 0.14), conductivity_horiz_1cm_i, Constraint('LEFT', flux=0), Constraint('UP', temperature=20), Constraint('DOWN', temperature=20))
    floor_upper.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor_upper)

    floor_upper = Rectangle((0, -0.01), (1.00, 0), conductivity_horiz_1cm_i, Constraint('LEFT', flux=0), Constraint('DOWN', temperature=20))
    floor_upper.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor_upper)

    corner: Rectangle = Rectangle((1.00, 0), (1.10, 0.13), concrete)
    assembly.add(corner)

    corner_left = Rectangle((1.10, 0), (1.11, 0.13), conductivity_1cm_e, Constraint('RIGHT', temperature=0))
    assembly.add(corner_left)

    upper_wall = Rectangle((1.00, 0.13), (1.10, 1.13), concrete, Constraint('UP', flux=0))
    upper_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall)

    upper_wall_right = Rectangle((1.10, .13), (1.11, 1.13), conductivity_1cm_e, Constraint('RIGHT', temperature=0), Constraint('UP', flux=0))
    upper_wall_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall_right)

    upper_wall_left = Rectangle((0.99, .13), (1.00, 1.13), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('UP', flux=0))
    upper_wall_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall_left)

    lower_wall = Rectangle((1.00, -1.00), (1.10, 0), concrete, Constraint('DOWN', flux=0))
    lower_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall)

    lower_wall_right = Rectangle((1.10, -1.00), (1.11, 0), conductivity_1cm_e,  Constraint('RIGHT', temperature=0), Constraint('DOWN', flux=0))
    lower_wall_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall_right)

    lower_wall_left = Rectangle((0.99, -1.00), (1.0, 0), conductivity_vert_1cm_i,  Constraint('LEFT', temperature=20), Constraint('DOWN', flux=0))
    lower_wall_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall_left)

    assembly.design_plot()
    assembly.solve(n_triangle_splits=n_triangle_splits)
    return assembly


def concrete_wall_with_intermediate_floor_outdoor_insulation():
    assembly = Assembly()
    concrete = Properties(conductivity=1)
    insulation = Properties(conductivity=0.05)
    conductivity_vert_1cm_i = Properties(conductivity=0.01 * (7.69 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))
    conductivity_1cm_e = Properties(conductivity=0.01 * (25 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 13)**3)))
    conductivity_horiz_1cm_i = Properties(conductivity=0.01 * (5.88 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))

    n_rectangle_splits = 3
    n_triangle_splits = 3

    floor: Rectangle = Rectangle((0, 0), (1.00, .13), concrete, Constraint('LEFT', flux=0))
    floor.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor)

    floor_upper = Rectangle((0, 0.13), (1.00, 0.14), conductivity_horiz_1cm_i, Constraint('LEFT', flux=0), Constraint('UP', temperature=20), Constraint('DOWN', temperature=20))
    floor_upper.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor_upper)

    floor_upper = Rectangle((0, -0.01), (1.00, 0), conductivity_horiz_1cm_i, Constraint('LEFT', flux=0), Constraint('DOWN', temperature=20))
    floor_upper.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor_upper)

    corner: Rectangle = Rectangle((1.00, 0), (1.10, .13), concrete)
    assembly.add(corner)

    upper_wall = Rectangle((1.00, .13), (1.10, 1.13), concrete, Constraint('UP', flux=0))
    upper_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall)

    upper_wall_left = Rectangle((0.99, .13), (1.00, 1.13), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('UP', flux=0))
    upper_wall_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall_left)

    lower_wall = Rectangle((1.00, -1.00), (1.10, 0), concrete, Constraint('DOWN', flux=0))
    lower_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall)

    lower_wall_left = Rectangle((0.99, -1.00), (1.0, 0), conductivity_vert_1cm_i,  Constraint('LEFT', temperature=20), Constraint('DOWN', flux=0))
    lower_wall_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall_left)

    upper_outdoor_insulation = Rectangle((1.10, 0.13), (1.30, 1.13), insulation, Constraint('UP', flux=0))
    upper_outdoor_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_outdoor_insulation)

    upper_outdoor_insulation_right = Rectangle((1.30, 0.13), (1.31, 1.13), conductivity_1cm_e, Constraint('RIGHT', temperature=0),  Constraint('UP', flux=0))
    upper_outdoor_insulation_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_outdoor_insulation_right)

    lower_outdoor_insulation = Rectangle((1.1, -1), (1.3, 0), insulation, Constraint('DOWN', flux=0))
    lower_outdoor_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_outdoor_insulation)

    lower_outdoor_insulation_right = Rectangle((1.3, -1), (1.31, 0), conductivity_1cm_e, Constraint('RIGHT', temperature=0), Constraint('DOWN', flux=0))
    lower_outdoor_insulation_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_outdoor_insulation_right)

    corner_insulation = Rectangle((1.1, 0), (1.30, 0.13), insulation)
    assembly.add(corner_insulation)

    corner_insulation_right = Rectangle((1.3, 0), (1.31, 0.13), conductivity_1cm_e, Constraint('RIGHT', temperature=0))
    assembly.add(corner_insulation_right)

    assembly.design_plot()
    assembly.solve(n_triangle_splits=n_triangle_splits)
    return assembly


def concrete_wall_with_intermediate_floor_indoor_insulation():
    assembly = Assembly()
    concrete = Properties(conductivity=1)
    insulation = Properties(conductivity=0.05)
    conductivity_vert_1cm_i = Properties(conductivity=0.01 * (7.69 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))
    conductivity_1cm_e = Properties(conductivity=0.01 * (25 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 13)**3)))
    # conductivity_horiz_1cm_i = Properties(conductivity=0.01 * (5.88 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))

    n_rectangle_splits = 3
    n_triangle_splits = 3

    floor: Rectangle = Rectangle((0, 0), (1.00, .13), concrete, Constraint('LEFT', flux=0), Constraint('UP', temperature=20), Constraint('DOWN', temperature=20))
    floor.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor)

    upper_wall = Rectangle((1.20, 0.13), (1.30, 1.13), insulation, Constraint('UP', flux=0))
    upper_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall)

    lower_wall = Rectangle((1.2, -1), (1.3, 0), insulation, Constraint('DOWN', flux=0))
    lower_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall)

    corner: Rectangle = Rectangle((1.00, 0), (1.20, .13), concrete)
    assembly.add(corner)

    corner_wall = Rectangle((1.20, 0), (1.30, 0.13), concrete)
    assembly.add(corner_wall)

    corner_right = Rectangle((1.30, 0), (1.31, 0.13), conductivity_1cm_e, Constraint('RIGHT', temperature=0))
    assembly.add(corner_right)

    lower_indoor_insulation = Rectangle((1.00, -1.00), (1.20, 0), insulation, Constraint('DOWN', flux=0))
    lower_indoor_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_indoor_insulation)

    upper_indoor_insulation = Rectangle((1.00, .13), (1.20, 1.13), insulation, Constraint('UP', flux=0))
    upper_indoor_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_indoor_insulation)

    upper_wall_right = Rectangle((1.30, .13), (1.31, 1.13), conductivity_1cm_e, Constraint('RIGHT', temperature=0), Constraint('UP', flux=0))
    upper_wall_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall_right)

    upper_wall_left = Rectangle((0.99, .13), (1.00, 1.13), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('UP', flux=0))
    upper_wall_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall_left)

    lower_wall_right = Rectangle((1.30, -1.00), (1.31, 0), conductivity_1cm_e,  Constraint('RIGHT', temperature=0), Constraint('DOWN', flux=0))
    lower_wall_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall_right)

    lower_wall_left = Rectangle((0.99, -1.00), (1.0, 0), conductivity_vert_1cm_i,  Constraint('LEFT', temperature=20), Constraint('DOWN', flux=0))
    lower_wall_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall_left)

    assembly.design_plot()
    assembly.solve(n_triangle_splits=n_triangle_splits)
    return assembly


def concrete_wall_with_intermediate_floor_balcony():
    assembly = Assembly()
    concrete = Properties(conductivity=1)
    # insulation = Properties(conductivity=0.05)
    conductivity_vert_1cm_i = Properties(conductivity=0.01 * (7.69 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))
    conductivity_1cm_e = Properties(conductivity=0.01 * (25 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 13)**3)))
    conductivity_horiz_1cm_i = Properties(conductivity=0.01 * (5.88 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))

    n_rectangle_splits = 3
    n_triangle_splits = 3

    floor: Rectangle = Rectangle((0, 0), (1.00, .13), concrete, Constraint('LEFT', flux=0))
    floor.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor)

    floor_upper: Rectangle = Rectangle((0, .13), (1.00, .14), conductivity_horiz_1cm_i, Constraint('LEFT', flux=0), Constraint('UP', temperature=20), Constraint('DOWN', temperature=20))
    floor_upper.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor_upper)

    floor_lower: Rectangle = Rectangle((0, -0.01), (1.00, 0), conductivity_horiz_1cm_i, Constraint('LEFT', flux=0), Constraint('DOWN', temperature=20))
    floor_lower.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor_lower)

    corner: Rectangle = Rectangle((1.00, 0), (1.10, .13), concrete)
    assembly.add(corner)

    upper_wall = Rectangle((1.00, .13), (1.10, 1.13), concrete, Constraint('UP', flux=0))
    upper_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall)

    upper_wall_left = Rectangle((0.99, .13), (1.00, 1.13), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('UP', flux=0))
    upper_wall_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall_left)

    upper_wall_right = Rectangle((1.10, .13), (1.11, 1.13), conductivity_1cm_e, Constraint('RIGHT', temperature=0), Constraint('UP', flux=0))
    upper_wall_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall_right)

    lower_wall = Rectangle((1.00, -1.00), (1.10, 0), concrete, Constraint('DOWN', flux=0))
    lower_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall)

    lower_wall_left = Rectangle((0.99, -1.00), (1.0, 0), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('DOWN', flux=0))
    lower_wall_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall_left)

    lower_wall_right = Rectangle((1.00, -1.00), (1.10, 0), conductivity_1cm_e, Constraint('RIGHT', temperature=0), Constraint('DOWN', flux=0))
    lower_wall_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall_right)

    balcony = Rectangle((1.10, 0), (2.10, .13), concrete)
    balcony.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(balcony)

    balcony_upper = Rectangle((1.10, 0.13), (2.10, .14), conductivity_1cm_e, Constraint('UP', temperature=0), Constraint('RIGHT', temperature=0))
    balcony_upper.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(balcony_upper)

    balcony_lower = Rectangle((1.10, -0.01), (2.10, 0), conductivity_1cm_e,  Constraint('DOWN', temperature=0))
    balcony_lower.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(balcony_lower)

    balcony_right = Rectangle((2.10, 0), (2.11, .13), conductivity_1cm_e, Constraint('RIGHT', temperature=0))
    assembly.add(balcony_right)

    assembly.design_plot()
    assembly.solve(n_triangle_splits=n_triangle_splits)
    return assembly


def concrete_wall_with_intermediate_floor_indoor_insulation_balcony():
    assembly = Assembly()
    concrete = Properties(conductivity=1)
    insulation = Properties(conductivity=0.05)
    conductivity_vert_1cm_i = Properties(conductivity=0.01 * (7.69 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))
    conductivity_1cm_e = Properties(conductivity=0.01 * (25 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 13)**3)))
    conductivity_horiz_1cm_i = Properties(conductivity=0.01 * (5.88 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))

    n_rectangle_splits = 3
    n_triangle_splits = 3

    floor: Rectangle = Rectangle((0, 0), (1.00, .13), concrete, Constraint('LEFT', flux=0))
    floor.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor)

    floor_upper: Rectangle = Rectangle((0, 0.13), (1.00, .14), conductivity_horiz_1cm_i, Constraint('LEFT', flux=0), Constraint('UP', temperature=20))
    floor_upper.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor_upper)

    floor_lower: Rectangle = Rectangle((0, -0.01), (1.00, 0), conductivity_vert_1cm_i, Constraint('LEFT', flux=0), Constraint('DOWN', temperature=20))
    floor_lower.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor_lower)

    corner: Rectangle = Rectangle((1.00, 0), (1.20, .13), concrete)
    assembly.add(corner)

    upper_indoor_insulation = Rectangle((1.00, .13), (1.20, 1.13), insulation, Constraint('UP', flux=0))
    upper_indoor_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_indoor_insulation)

    upper_indoor_insulation_left = Rectangle((1.00, .13), (1.20, 1.13), insulation, Constraint('LEFT', temperature=20), Constraint('UP', flux=0))
    upper_indoor_insulation_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_indoor_insulation_left)

    lower_indoor_insulation = Rectangle((1.00, -1.00), (1.20, 0), concrete, Constraint('DOWN', flux=0))
    lower_indoor_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_indoor_insulation)

    lower_indoor_insulation_left = Rectangle((0.99, -1.00), (1.0, 0), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('DOWN', flux=0))
    lower_indoor_insulation_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_indoor_insulation_left)

    upper_wall = Rectangle((1.20, 0.13), (1.30, 1.13), insulation, Constraint('UP', flux=0))
    upper_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall)

    upper_wall_right = Rectangle((1.30, 0.13), (1.31, 1.13), conductivity_1cm_e, Constraint('RIGHT', temperature=0), Constraint('UP', flux=0))
    upper_wall_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall_right)

    lower_wall = Rectangle((1.2, -1), (1.3, 0), insulation, Constraint('DOWN', flux=0))
    lower_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall)

    lower_wall_right = Rectangle((1.3, -1), (1.31, 0), conductivity_1cm_e, Constraint('RIGHT', temperature=0), Constraint('DOWN', flux=0))
    lower_wall_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall_right)

    corner_wall = Rectangle((1.2, 0), (1.30, 0.13), concrete)
    assembly.add(corner_wall)

    balcony: Rectangle = Rectangle((1.3, 0), (2.30, .13), concrete)
    balcony.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(balcony)

    balcony_up: Rectangle = Rectangle((1.3, 0.13), (2.30, .14), conductivity_1cm_e, Constraint('UP', temperature=0))
    balcony_up.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(balcony_up)

    balcony_down: Rectangle = Rectangle((1.3, -0.01), (2.30, 0), conductivity_1cm_e, Constraint('DOWN', temperature=0))
    balcony_down.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(balcony_down)

    balcony_right: Rectangle = Rectangle((1.3, 0), (2.30, .13), conductivity_1cm_e, Constraint('RIGHT', temperature=0))
    balcony_right.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(balcony_right)

    assembly.design_plot()
    assembly.solve(n_triangle_splits=n_triangle_splits)
    return assembly


def concrete_wall_with_intermediate_floor_outdoor_insulation_balcony():
    assembly = Assembly()
    concrete = Properties(conductivity=1)
    insulation = Properties(conductivity=0.05)
    conductivity_vert_1cm_i = Properties(conductivity=0.01 * (7.69 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))
    conductivity_1cm_e = Properties(conductivity=0.01 * (25 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 13)**3)))
    conductivity_horiz_1cm_i = Properties(conductivity=0.01 * (5.88 + (4 * 0.9 * Stefan_Boltzmann * (273.15 + 20)**3)))

    n_rectangle_splits = 3
    n_triangle_splits = 3

    floor: Rectangle = Rectangle((0, 0), (1.00, .13), concrete, Constraint('LEFT', flux=0))
    floor.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor)

    floor_up: Rectangle = Rectangle((0, 0.13), (1.00, .14), conductivity_horiz_1cm_i, Constraint('LEFT', flux=0), Constraint('UP', temperature=20))
    floor_up.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor_up)

    floor_down: Rectangle = Rectangle((0, -0.01), (1.00, 0), conductivity_horiz_1cm_i, Constraint('LEFT', flux=0), Constraint('DOWN', temperature=20))
    floor_down.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(floor_down)

    corner_wall: Rectangle = Rectangle((1.00, 0), (1.10, .13), concrete)
    assembly.add(corner_wall)

    upper_wall = Rectangle((1.00, .13), (1.10, 1.13), concrete, Constraint('UP', flux=0))
    upper_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall)

    upper_wall_left = Rectangle((0.99, .13), (1.00, 1.13), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('UP', flux=0))
    upper_wall_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_wall_left)

    lower_wall = Rectangle((1.00, -1.00), (1.10, 0), concrete, Constraint('DOWN', flux=0))
    lower_wall.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall)

    lower_wall_left = Rectangle((0.99, -1.00), (1.0, 0), conductivity_vert_1cm_i, Constraint('LEFT', temperature=20), Constraint('DOWN', flux=0))
    lower_wall_left.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_wall_left)

    upper_outdoor_insulation = Rectangle((1.10, 0.13), (1.30, 1.13), insulation, Constraint('UP', flux=0))
    upper_outdoor_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_outdoor_insulation)

    upper_outdoor_insulation_right = Rectangle((1.30, 0.13), (1.31, 1.13), conductivity_1cm_e, Constraint('RIGHT', temperature=0), Constraint('UP', flux=0))
    upper_outdoor_insulation_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(upper_outdoor_insulation_right)

    lower_outdoor_insulation = Rectangle((1.1, -1), (1.3, 0), insulation,  Constraint('DOWN', flux=0))
    lower_outdoor_insulation.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_outdoor_insulation)

    lower_outdoor_insulation_right = Rectangle((1.3, -1), (1.31, 0), conductivity_1cm_e, Constraint('RIGHT', temperature=0), Constraint('DOWN', flux=0))
    lower_outdoor_insulation_right.divide(x_split=0, y_split=n_rectangle_splits)
    assembly.add(lower_outdoor_insulation_right)

    corner_insulation = Rectangle((1.1, 0), (1.30, 0.13), insulation)
    assembly.add(corner_insulation)

    balcony: Rectangle = Rectangle((1.3, 0), (2.30, .13), concrete)
    balcony.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(balcony)

    balcony_up: Rectangle = Rectangle((1.3, 0.13), (2.30, 0.14), conductivity_1cm_e,  Constraint('UP', temperature=0))
    balcony_up.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(balcony_up)

    balcony_down: Rectangle = Rectangle((1.3, -0.01), (2.30, 0), conductivity_1cm_e, Constraint('DOWN', temperature=0))
    balcony_down.divide(x_split=n_rectangle_splits, y_split=0)
    assembly.add(balcony_down)

    balcony_right: Rectangle = Rectangle((2.3, 0), (2.31, .13), conductivity_1cm_e, Constraint('RIGHT', temperature=0))
    assembly.add(balcony_right)

    assembly.design_plot()
    assembly.solve(n_triangle_splits=n_triangle_splits)
    return assembly


if __name__ == '__main__':
    concrete_wall().solution_plot()
