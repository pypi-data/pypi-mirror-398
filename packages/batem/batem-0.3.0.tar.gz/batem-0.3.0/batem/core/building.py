"""Building model construction and simulation orchestration utilities.

.. module:: batem.core.building

This module provides the high-level orchestration logic required to build a
BATEM building model from contextual data, generate thermal networks, configure
HVAC controllers, and run coupled simulations. It binds together solar,
thermal, control, and model-making subsystems to offer a cohesive workflow.

The dataclasses defined here use reStructuredText field lists so that automated
documentation can surface every parameter accepted by the simulation pipeline.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""
from abc import ABC, abstractmethod
from functools import cached_property
from datetime import datetime
from batem.core.data import DataProvider, Bindings
from batem.core.control import HeatingPeriod, CoolingPeriod, OccupancyProfile, SignalGenerator, TemperatureController, Simulation, TemperatureSetpointPort, HVACcontinuousModePort, LongAbsencePeriod
from batem.core.inhabitants import Preference
from batem.core.model import ModelMaker
from batem.core.components import Side, Composition
from batem.core.library import SIDE_TYPES, SLOPES
from batem.core.solar import SolarModel, SolarSystem, Collector, SideMask, Mask
from batem.core.statemodel import StateModel
from batem.core.utils import FilePathBuilder
from pyvista.core.pointset import PolyData
from dataclasses import dataclass, field
from pyvista.plotting.plotter import Plotter
from math import sqrt, sin, cos, radians, atan2, degrees
import pyvista as pv
import matplotlib.pyplot as plt
import numpy as np
import types
import prettytable

pv.set_jupyter_backend('html')


@dataclass
class WindowData:
    side: str
    surface: float
    rotation_angle_deg: float


@dataclass
class FloorData:
    length: float
    width: float
    elevation: float
    windows_data: list[WindowData]
    
    
@dataclass
class FloorResult:
    floor_number: int
    external_envelope_surface_m2: float
    heat_production_Wh: list[float]

    @cached_property 
    def heat_production_heating_Wh(self) -> list[float]:
        return [p if p > 0 else 0 for p in self.heat_production_Wh]

    @cached_property
    def heat_production_cooling_Wh(self) -> list[float]:
        return [p if p < 0 else 0 for p in self.heat_production_Wh]

@dataclass
class BuildingResult:
    hvac_cop_heating: float
    hvac_cop_cooling: float
    floor_results: list[FloorResult]

    @cached_property
    def external_envelope_surface_m2(self) -> float:
        return sum(floor_result.external_envelope_surface_m2 for floor_result in self.floor_results)

    @cached_property
    def heat_production_Wh(self) -> list[float]:
        return [sum(floor_result.heat_production_Wh[i] for floor_result in self.floor_results) for i in range(len(self.floor_results[0].heat_production_Wh))]

    @cached_property
    def heat_production_heating_Wh(self) -> list[float]:
        return [p if p > 0 else 0 for p in self.heat_production_Wh]

    @cached_property
    def heat_production_cooling_Wh(self) -> list[float]:
        return [p if p < 0 else 0 for p in self.heat_production_Wh]


@dataclass
class SideMaskData:
    x_center: float
    y_center: float
    width: float
    height: float
    elevation: float
    exposure_deg: float
    slope_deg: float
    normal_rotation_angle_deg: float


@dataclass
class ContextData:
    """Metadata describing the geographic and climatic context for a simulation.

    :param latitude_north_deg: Site latitude in decimal degrees (positive north).
    :param longitude_east_deg: Site longitude in decimal degrees (positive east).
    :param starting_stringdate: Inclusive start date for the simulation window.
    :param ending_stringdate: Exclusive end date for the simulation window.
    :param location: Human-readable site name used in reports.
    :param albedo: Ground albedo coefficient in the ``[0, 1]`` range.
    :param pollution: Atmospheric pollution factor used for solar attenuation.
    :param number_of_levels: Number of distinct vertical atmospheric layers to
        load in the weather data set.
    :param ground_temperature: Average ground temperature in degrees Celsius.
    :param side_masks: Optional list of distant masks describing surrounding
        obstacles.
    :ivar side_masks: Always stored as a list for downstream iteration.
    """
    latitude_north_deg: float
    longitude_east_deg: float
    starting_stringdate: str
    ending_stringdate: str
    location: str
    albedo: float
    pollution: float
    number_of_levels: int
    ground_temperature: float
    side_masks: list[SideMaskData] = field(default_factory=list)
    initial_year: int = 1980


@dataclass
class BuildingData:
    """Physical and operational parameters defining a BATEM building model.

    This dataclass stores the geometry, material compositions, HVAC capacities,
    and occupant-related assumptions used when generating thermal networks and
    control systems.

    :param length: Building length along the X-axis in metres.
    :param width: Building width along the Y-axis in metres.
    :param n_floors: Number of occupied floors (excluding the basement zone).
    :param floor_height: Storey height in metres for regular floors.
    :param base_elevation: Basement height in metres.
    :param z_rotation_angle_deg: Clockwise rotation of the building footprint.
    :param ref_glazing_ratio: Ratio of window surface to façade surface for the
        reference side (at rotation_angle_deg, typically South).
    :param right_glazing_ratio: Ratio of window surface to façade surface for the
        right side (at rotation_angle_deg + 90°, typically East).
    :param opposite_glazing_ratio: Ratio of window surface to façade surface for the
        opposite side (at rotation_angle_deg + 180°, typically North).
    :param left_glazing_ratio: Ratio of window surface to façade surface for the
        left side (at rotation_angle_deg - 90°, typically West).
    :param glazing_solar_factor: Solar heat gain coefficient applied to glazing.
    :param shutter_closed_temperature: Outdoor temperature threshold (°C) above which
        shutters are closed and solar gains are set to 0. If None, shutters are never closed.
    :param compositions: Mapping of envelope component names to layer tuples
        ``(material_name, thickness_m)``.
    :param max_heating_power: Maximum heating power available per zone in watts.
    :param max_cooling_power: Maximum cooling power available per zone in watts.
    :param body_metabolism: Basal metabolic heat production per occupant in watts (typically 100W).
    :param occupant_consumption: Additional heat gains per occupant from activities and appliances in watts (typically 150W).
    :param body_PCO2: CO₂ production per occupant in litres per hour.
    :param density_occupants_per_100m2: Occupant density used for gain profiles.
    :param regular_air_renewal_rate_vol_per_hour: Baseline ventilation rate used
        for nominal operation (volumes per hour).
    :param super_air_renewal_rate_vol_per_hour: Ventilation rate applied during
        forced ventilation or free-cooling strategies (volumes per hour).
    :param initial_temperature: Initial temperature (°C) for all thermal states.
    :param low_heating_setpoint: Setback heating setpoint in degrees Celsius.
    :param normal_heating_setpoint: Comfort heating setpoint in degrees Celsius.
    :param high_heating_setpoint: Boost heating setpoint in degrees Celsius.
    :param state_model_order_max: Optional upper bound for model reduction.
    :param periodic_depth_seconds: Maximum penetration depth for periodic inputs.
    :param combinations: dictionary with keys 'wall', 'intermediate_floor', 'roof', 'glazing', 'ground_floor', 'basement_floor' and values are lists of tuples of materials and thicknesses
    :param intermediate_floor: dict[str, tuple[tuple[str, float], ...]]
    """
    length: float
    width: float
    n_floors: int
    floor_height: float
    base_elevation: float
    z_rotation_angle_deg: float
    ref_glazing_ratio: float
    opposite_glazing_ratio: float
    left_glazing_ratio: float
    right_glazing_ratio: float
    glazing_solar_factor: float
    compositions: dict[str, tuple[tuple[str, float], ...]]
    max_heating_power: float
    max_cooling_power: float
    density_occupants_per_100m2: float
    initial_temperature: float
    low_heating_setpoint: float
    normal_heating_setpoint: float
    normal_cooling_setpoint: float
    regular_air_renewal_rate_vol_per_hour: float
    body_metabolism: float = 100.0
    occupant_consumption: float = 150.0
    body_PCO2: float = 7.0
    shutter_closed_temperature: float | None = None  # if not None, shutters are closed and solar gains are set to 0 when outdoor temperature exceeds this threshold
    free_cooling_setpoint_margin: float | None = None
    long_absence_period: tuple[str, str] = ('1/8', '15/8')
    heating_period: tuple[str, str] = ('1/11', '1/5')
    cooling_period: tuple[str, str] = ('1/6', '30/9')
    hvac_cop_heating: float = 3.5
    hvac_cop_cooling: float = 3.5
    regular_ventilation_heat_recovery_efficiency: float = 0.8
    state_model_order_max: int | None = None
    periodic_depth_seconds: int = 3600
    wall: Side = field(init=False)
    intermediate_floor: Side | None = field(init=False)
    roof: Side = field(init=False)
    glazing: Side = field(init=False)
    ground_floor: Side = field(init=False)
    basement_floor: Side | None = field(init=False)

    def __post_init__(self) -> None:
        """Post initialization method to validate and initialize building components.
        Validates that all required compositions are present and initializes the building components.

        :param self: The instance of the class.
        :raises ValueError: Raised if required compositions are missing.
        """
        # Always required components
        required_components: list[str] = ['wall', 'roof', 'glazing', 'ground_floor']

        # intermediate_floor is only needed when there are multiple floors
        if self.n_floors > 1:
            required_components.append('intermediate_floor')

        # basement_floor is only needed when there's a basement
        if self.base_elevation > 0:
            required_components.append('basement_floor')

        missing_keys: list[str] = [key for key in required_components if key not in self.compositions]
        if missing_keys:
            raise ValueError(f"Missing compositions for: {', '.join(missing_keys)}")

        self.wall = Side(*self.compositions['wall'])
        self.roof = Side(*self.compositions['roof'])
        self.glazing = Side(*self.compositions['glazing'])
        self.ground_floor = Side(*self.compositions['ground_floor'])

        # Initialize optional components only if present
        if 'intermediate_floor' in self.compositions:
            self.intermediate_floor = Side(*self.compositions['intermediate_floor'])
        else:
            self.intermediate_floor = None

        if 'basement_floor' in self.compositions:
            self.basement_floor = Side(*self.compositions['basement_floor'])
        else:
            self.basement_floor = None

        self.indoor_outdoor_surface_m2: float = 2 * (self.length + self.width) * self.floor_height * self.n_floors + self.length * self.width
        self.indoor_outdoor_floor_surface_m2: float = 2 * (self.length + self.width) * self.floor_height
        self.indoor_outdoor_upper_floor_surface_m2: float = 2 * (self.length + self.width) * self.floor_height + self.length * self.width


class FloorZoneView:

    @staticmethod
    def _normalize(angle: float) -> float:
        return (angle + 180) % 360 - 180

    def __init__(self, xmin: float, xmax: float, ymin: float, ymax: float, zmin: float, zmax: float, ref_glazing_ratio: float = 0.0, right_glazing_ratio: float = 0.0, opposite_glazing_ratio: float = 0.0, left_glazing_ratio: float = 0.0, rotation_angle_deg: float = 0.0) -> None:
        self.xmin: float = xmin
        self.xmax: float = xmax
        self.ymin: float = ymin
        self.ymax: float = ymax
        self.zmin: float = zmin
        self.zmax: float = zmax
        self._rotation_angle_deg: float = rotation_angle_deg
        self.ref_glazing_ratio: float = ref_glazing_ratio
        self.right_glazing_ratio: float = right_glazing_ratio
        self.opposite_glazing_ratio: float = opposite_glazing_ratio
        self.left_glazing_ratio: float = left_glazing_ratio
        # For visualization, use max glazing ratio to determine if windows should be shown
        self.glazing_ratio: float = max(ref_glazing_ratio, right_glazing_ratio, opposite_glazing_ratio, left_glazing_ratio)

        floor_length: float = xmax - xmin
        floor_width: float = ymax - ymin
        floor_height: float = zmax - zmin
        self._elevation: float = (zmin + zmax) / 2
        self._north_south_surface: float = floor_length * floor_height
        self._east_west_surface: float = floor_width * floor_height

    @property
    def floor_center(self) -> tuple:
        return (0, 0, (self.zmin + self.zmax) / 2)

    def make(self) -> pv.PolyData:
        main_box: PolyData = pv.Box(bounds=(self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax))
        if self.glazing_ratio == 0:
            return main_box

        floor_length: float = self.xmax - self.xmin
        floor_width: float = self.ymax - self.ymin
        floor_height: float = self.zmax - self.zmin
        elevation: float = (self.zmin + self.zmax) / 2

        self._elevation: float = elevation
        self._north_south_surface: float = floor_length * floor_height
        self._east_west_surface: float = floor_width * floor_height

        # Use a large padding so cutter boxes pass fully through the floor
        pad: float = max(floor_length, floor_width, floor_height) * 5.0
        # Use a small epsilon to position windows slightly inside the building to avoid edge issues
        epsilon: float = 0.01

        # Create window holes for each side with individual glazing ratios
        # Convention: 0°=South(+X), 90°=East(+Y), -90°=West(-Y), 180°=North(-X)
        # ref is at rotation_angle_deg (typically South), opposite is +180°, right is +90°, left is -90°
        # Windows are created as holes that pass through the building
        # To avoid affecting multiple sides, we position windows at the faces and limit their extent
        result: PolyData = main_box

        # Calculate window dimensions for each side based on their individual glazing ratios
        # Window size: width = wall_length * sqrt(glazing_ratio), height = wall_height * sqrt(glazing_ratio)
        # Windows are centered in the middle of each wall
        # ref side (primary direction - typically South, at xmax face)
        # The wall spans in Y direction (floor_width) and Z direction (floor_height)
        # Wall surface = floor_width * floor_height
        # clip_box bounds: (xmin, xmax, ymin, ymax, zmin, zmax)
        if self.ref_glazing_ratio > 0:
            ref_window_width: float = floor_width * sqrt(self.ref_glazing_ratio)
            ref_window_height: float = floor_height * sqrt(self.ref_glazing_ratio)
            ref_window_center_y: float = (self.ymin + self.ymax) / 2  # Centered in middle of wall
            # Position window hole at xmax face - passes through in Y direction
            ref_bounds = (
                self.xmax - epsilon,  # Start just inside xmax face
                self.xmax + pad,  # Extend outward
                ref_window_center_y - ref_window_width/2,
                ref_window_center_y + ref_window_width/2,
                elevation - ref_window_height/2,
                elevation + ref_window_height/2,
            )
            try:
                result = result.clip_box(ref_bounds, invert=True)
            except Exception:
                pass

        # opposite side (primary direction + 180° - typically North, at xmin face)
        # The wall spans in Y direction (floor_width) and Z direction (floor_height)
        # Wall surface = floor_width * floor_height
        if self.opposite_glazing_ratio > 0:
            opposite_window_width: float = floor_width * sqrt(self.opposite_glazing_ratio)
            opposite_window_height: float = floor_height * sqrt(self.opposite_glazing_ratio)
            opposite_window_center_y: float = (self.ymin + self.ymax) / 2  # Centered in middle of wall
            # Position window hole at xmin face - passes through in Y direction
            opposite_bounds = (
                self.xmin - pad,  # Extend outward
                self.xmin + epsilon,  # Start just inside xmin face
                opposite_window_center_y - opposite_window_width/2,
                opposite_window_center_y + opposite_window_width/2,
                elevation - opposite_window_height/2,
                elevation + opposite_window_height/2,
            )
            try:
                result = result.clip_box(opposite_bounds, invert=True)
            except Exception:
                pass

        # right side (secondary direction + 90° - typically East, at ymax face)
        # Note: Windows are created in local coordinates before rotation, so right is at +Y direction
        # The wall spans in X direction (floor_length) and Z direction (floor_height)
        # Wall surface = floor_length * floor_height
        if self.right_glazing_ratio > 0:
            right_window_width: float = floor_length * sqrt(self.right_glazing_ratio)
            right_window_height: float = floor_height * sqrt(self.right_glazing_ratio)
            right_window_center_x: float = (self.xmin + self.xmax) / 2  # Centered in middle of wall
            # Position window hole at ymax face - passes through in X direction
            right_bounds = (
                right_window_center_x - right_window_width/2,
                right_window_center_x + right_window_width/2,
                self.ymax - epsilon,  # Start just inside ymax face
                self.ymax + pad,  # Extend outward
                elevation - right_window_height/2,
                elevation + right_window_height/2,
            )
            try:
                result = result.clip_box(right_bounds, invert=True)
            except Exception:
                pass

        # left side (secondary direction - 90° - typically West, at ymin face)
        # Note: Windows are created in local coordinates before rotation, so left is at -Y direction
        # The wall spans in X direction (floor_length) and Z direction (floor_height)
        # Wall surface = floor_length * floor_height
        if self.left_glazing_ratio > 0:
            left_window_width: float = floor_length * sqrt(self.left_glazing_ratio)
            left_window_height: float = floor_height * sqrt(self.left_glazing_ratio)
            left_window_center_x: float = (self.xmin + self.xmax) / 2  # Centered in middle of wall
            # Position window hole at ymin face - passes through in X direction
            left_bounds = (
                left_window_center_x - left_window_width/2,
                left_window_center_x + left_window_width/2,
                self.ymin - pad,  # Extend outward
                self.ymin + epsilon,  # Start just inside ymin face
                elevation - left_window_height/2,
                elevation + left_window_height/2,
            )
            try:
                result = result.clip_box(left_bounds, invert=True)
            except Exception as e:
                print(f"Clipping operation failed for left window: {e}")

        return result

    @property
    def elevation(self) -> float:
        return self._elevation

    @property
    def windows_data(self) -> list[WindowData]:
        floor_length: float = self.xmax - self.xmin
        floor_width: float = self.ymax - self.ymin
        floor_height: float = self.zmax - self.zmin
        # Calculate window surfaces using individual glazing ratios
        # Order: ref, right, opposite, left
        # Note: ref and opposite walls span in Y direction (floor_width), left and right walls span in X direction (floor_length)
        return [
            WindowData(side="ref", surface=self.ref_glazing_ratio * floor_width * floor_height, rotation_angle_deg=FloorZoneView._normalize(self._rotation_angle_deg)),
            WindowData(side="right", surface=self.right_glazing_ratio * floor_length * floor_height, rotation_angle_deg=FloorZoneView._normalize(self._rotation_angle_deg+90)),
            WindowData(side="opposite", surface=self.opposite_glazing_ratio * floor_width * floor_height, rotation_angle_deg=FloorZoneView._normalize(self._rotation_angle_deg+180)),
            WindowData(side="left", surface=self.left_glazing_ratio * floor_length * floor_height, rotation_angle_deg=FloorZoneView._normalize(self._rotation_angle_deg-90)),
        ]


class BuildingView:

    def __init__(self, length=10.0, width=8.0, n_floors=5, floor_height=2.7, base_elevation=0, ref_glazing_ratio=0.4, right_glazing_ratio=0.4, opposite_glazing_ratio=0.4, left_glazing_ratio=0.4) -> None:
        self._building_data: list[FloorData] = []
        self.rotation_angle_deg: float = None
        self.building_color: str = "lightgray"
        self.base_color: str = "darkgray"
        self.edge_color: str = "black"
        self.length: float = length
        self.width: float = width
        self.n_floors: int = n_floors
        self.floor_height: float = floor_height
        self.base_elevation: float = base_elevation
        self.ref_glazing_ratio: float = ref_glazing_ratio
        self.right_glazing_ratio: float = right_glazing_ratio
        self.opposite_glazing_ratio: float = opposite_glazing_ratio
        self.left_glazing_ratio: float = left_glazing_ratio
        # For backward compatibility in visualization
        self.glazing_ratio: float = max(ref_glazing_ratio, right_glazing_ratio, opposite_glazing_ratio, left_glazing_ratio)
        self.xmin: float = -length/2
        self.xmax: float = length/2
        self.ymin: float = -width/2
        self.ymax: float = width/2
        self.total_height: float = base_elevation + n_floors * floor_height
        self.center_elevation: float = self.total_height / 2
        self.zmin = 0
        self.zmax: float = self.total_height
        self.z_floors: list[float] = [base_elevation + i * floor_height for i in range(n_floors)] + [self.total_height]
        self.floors: list[FloorZoneView] = []
        if base_elevation > 0:
            self.floors.append(FloorZoneView(xmin=self.xmin, xmax=self.xmax, ymin=self.ymin, ymax=self.ymax, zmin=0, zmax=base_elevation, ref_glazing_ratio=0, right_glazing_ratio=0, opposite_glazing_ratio=0, left_glazing_ratio=0))
        self.slabs: list[pv.PolyData] = []
        for i in range(n_floors):
            self.floors.append(FloorZoneView(xmin=self.xmin, xmax=self.xmax, ymin=self.ymin, ymax=self.ymax, zmin=self.z_floors[i], zmax=self.z_floors[i+1], ref_glazing_ratio=ref_glazing_ratio, right_glazing_ratio=right_glazing_ratio, opposite_glazing_ratio=opposite_glazing_ratio, left_glazing_ratio=left_glazing_ratio))
            self.slabs.append(pv.Box(bounds=(self.xmin, self.xmax, self.ymin, self.ymax, self.z_floors[i], self.z_floors[i]+self.total_height/20)))

    def make(self, rotation_angle_deg: float = 0) -> list[FloorData]:
        # rotation_angle_deg follows convention: 0°=South, 90°=East, -90°=West, 180°=North
        self.rotation_angle_deg = rotation_angle_deg
        building_data: list[FloorData] = []
        for floor in self.floors:
            floor._rotation_angle_deg = rotation_angle_deg
            windows_data: list[WindowData] = []
            for window in floor.windows_data:
                windows_data.append(WindowData(side=window.side, surface=window.surface, rotation_angle_deg=window.rotation_angle_deg))
                # floor_data.windows_data.append(window_data)
            floor_data: FloorData = FloorData(length=self.length, width=self.width, elevation=floor.elevation, windows_data=floor.windows_data)
            building_data.append(floor_data)
        self._building_data = building_data
        return self._building_data

    def draw(self, plotter: pv.Plotter) -> None:
        if self.rotation_angle_deg is None:
            self.rotation_angle_deg = 0.0

        base_box: PolyData | None = None
        if self.floors and self.base_elevation > 0:
            base_box = self.floors[0].make().rotate_z(self.rotation_angle_deg, inplace=False)
        # Upper floors have windows
        upper_boxes: list[PolyData] = []
        start_index = 1 if self.base_elevation > 0 else 0
        for floor in self.floors[start_index:]:
            floor._rotation_angle_deg = self.rotation_angle_deg
            upper_boxes.append(floor.make().rotate_z(self.rotation_angle_deg, inplace=False))

        merged_upper: PolyData | None = None
        if upper_boxes:
            merged_upper = upper_boxes[0].copy()
            for ub in upper_boxes[1:]:
                merged_upper = merged_upper.merge(ub)

        # Slabs
        slab_boxes: list[PolyData] = [slab.rotate_z(self.rotation_angle_deg, inplace=False) for slab in self.slabs]

        for slab in slab_boxes:  # type: ignore[index]
            plotter.add_mesh(slab, color=self.building_color, opacity=0.2, show_edges=False)
        if base_box is not None:
            plotter.add_mesh(base_box, color=self.base_color, smooth_shading=True, metallic=0.1, roughness=0.6, show_edges=True, edge_color="black", line_width=1.5)  # type: ignore[arg-type]
        if merged_upper is not None:
            plotter.add_mesh(merged_upper, color=self.building_color, smooth_shading=True, metallic=0.1, roughness=0.6, show_edges=True, edge_color=self.edge_color, line_width=1.5)  # type: ignore[arg-type]

        building_data: list[FloorData] = []
        for floor in self.floors:
            windows_data: list[WindowData] = []
            for window in floor.windows_data:
                windows_data.append(WindowData(side=window.side, surface=window.surface, rotation_angle_deg=window.rotation_angle_deg))
            floor_data: FloorData = FloorData(length=self.length, width=self.width, elevation=floor.elevation, windows_data=floor.windows_data)
            building_data.append(floor_data)
        self._building_data = building_data

    @property
    def building_data(self) -> list[FloorData]:
        return self._building_data


class SideMaskView:

    def __init__(self, side_mask_data: SideMaskData) -> None:
        self.color: str = "red"
        self.opacity: float = 0.35
        # World coordinates: +X=South, +Y=East (as requested)
        self.x_center: float = side_mask_data.x_center
        self.y_center: float = side_mask_data.y_center
        self.z_center: float = side_mask_data.elevation + side_mask_data.height / 2
        self.center_ref: tuple[float, float, float] = (side_mask_data.x_center, side_mask_data.y_center, self.z_center)
        self.width: float = side_mask_data.width
        self.height: float = side_mask_data.height
        self.elevation: float = side_mask_data.elevation
        self.exposure_deg: float = side_mask_data.exposure_deg
        self.slope_deg: float = side_mask_data.slope_deg
        self.normal_rotation_deg: float = side_mask_data.normal_rotation_angle_deg

        self.azimuth_deg: float = degrees(atan2(self.y_center, self.x_center))
        self.altitude_deg: float = degrees(atan2(self.elevation, sqrt(self.x_center**2 + self.y_center**2)))
        self.distance_m: float = sqrt(self.x_center**2 + self.y_center**2)

        slope_rad: float = radians(self.slope_deg)
        # Convention: +X is South, +Y is East; 0°=South(+X), 90°=East(+Y), -90°=West(-Y), 180°=North(-X)
        exposure_rad: float = radians(side_mask_data.exposure_deg)

        # Normal mapping in world XY directly: (cos(theta), sin(theta))
        nx: float = cos(exposure_rad) * sin(slope_rad)
        ny: float = sin(exposure_rad) * sin(slope_rad)
        nz: float = -cos(slope_rad)
        self.normal: tuple[float, float, float] = (nx, ny, nz)

    def make(self) -> SideMaskData:
        return SideMaskData(x_center=self.x_center, y_center=self.y_center, width=self.width, height=self.height, elevation=self.elevation, exposure_deg=self.exposure_deg, slope_deg=self.slope_deg, normal_rotation_angle_deg=self.normal_rotation_deg)

    def draw(self, plotter: pv.Plotter) -> None:
        plane: pv.Plane = pv.Plane(center=self.center_ref, direction=self.normal, i_size=self.height, j_size=self.width)
        if abs(self.normal_rotation_deg) > 1e-9:
            plane.rotate_vector(vector=self.normal, angle=self.normal_rotation_deg, point=self.center_ref, inplace=True)
        tail: list[float] = self.center_ref
        head: list[float] = (self.center_ref[0] + 3.0 * self.normal[0], self.center_ref[1] + 3.0 * self.normal[1], self.center_ref[2] + 3.0 * self.normal[2])
        arrow: pv.Arrow = pv.Arrow(start=tail, direction=[head[i] - tail[i] for i in range(3)], tip_length=0.2, tip_radius=0.15, shaft_radius=0.05)

        plotter.add_mesh(plane, color=self.color, opacity=self.opacity, smooth_shading=True)
        plotter.add_mesh(arrow, color="black")


class Context:

    def __init__(self, context_data: ContextData) -> None:
        self.context_data: ContextData = context_data
        self.distant_masks: list[SideMask] = list()
        self.side_mask_views: list[SideMaskView] = list()
        for side_mask in context_data.side_masks:
            self.distant_masks.append(SideMask(side_mask.x_center, side_mask.y_center, side_mask.width, side_mask.height, side_mask.exposure_deg, side_mask.slope_deg, side_mask.elevation, side_mask.normal_rotation_angle_deg))
            side_mask_view: SideMaskView = SideMaskView(side_mask)
            side_mask_view.make()
            self.side_mask_views.append(side_mask_view)

        bindings: Bindings = Bindings()
        bindings('TZ:outdoor', 'weather_temperature')

        self.dp: DataProvider = DataProvider(location=context_data.location, latitude_north_deg=context_data.latitude_north_deg, longitude_east_deg=context_data.longitude_east_deg, starting_stringdate=context_data.starting_stringdate, ending_stringdate=context_data.ending_stringdate, bindings=bindings, albedo=context_data.albedo, pollution=context_data.pollution, number_of_levels=context_data.number_of_levels, initial_year=context_data.initial_year)
        self.solar_model: SolarModel = SolarModel(self.dp.weather_data, distant_masks=self.distant_masks)


class Zone(ABC):

    def __init__(self, floor_number: int, building_data: BuildingData, solar_model: SolarModel) -> None:
        self.floor_number: int = floor_number
        self.name: str = f"floor{floor_number}"
        self.length: float = building_data.length
        self.width: float = building_data.width
        self.floor_height: float = building_data.floor_height
        self.floor_surface: float = self.length * self.width
        self.base_elevation: float = building_data.base_elevation
        self.z_rotation_angle_deg: float = building_data.z_rotation_angle_deg
        self.building_data: BuildingData = building_data
        self.solar_model: SolarModel = solar_model
        self.solar_system: SolarSystem = SolarSystem(solar_model)
        self.n_floors: int = building_data.n_floors

    @abstractmethod
    def make(self, model_maker: ModelMaker, dp: DataProvider) -> None:
        pass

    @abstractmethod
    def window_masks(self) -> dict[str, Mask]:
        """Return window masks dictionary."""
        pass


class BasementZone(Zone):

    def __init__(self, floor_number: int, building_data: BuildingData, solar_model: SolarModel) -> None:
        super().__init__(floor_number, building_data, solar_model)
        self.volume: float = self.length * self.width * self.base_elevation
        self.mid_elevation: float = self.building_data.base_elevation/2
        self.wall_surface: float = 2 * (self.length + self.width) * self.base_elevation
        # External envelope surface for basement (walls only, no roof)
        self.external_envelope_surface_m2: float = self.wall_surface

    def window_masks(self) -> dict[str, Mask]:
        return dict()

    def make(self, model_maker: ModelMaker, dp: DataProvider) -> None:
        # basement_floor is guaranteed to exist when BasementZone is created (base_elevation > 0)
        assert self.building_data.basement_floor is not None, "basement_floor should be defined when base_elevation > 0"
        model_maker.make_side(self.building_data.basement_floor(self.name, 'ground', SIDE_TYPES.FLOOR, self.floor_surface))
        model_maker.make_side(self.building_data.wall(self.name, 'outdoor', SIDE_TYPES.WALL, self.wall_surface))
        model_maker.make_side(self.building_data.ground_floor(self.name, 'floor1', SIDE_TYPES.FLOOR, self.floor_surface))


class ZoneFloor(Zone):

    def __init__(self, floor_number: int, building_data: BuildingData, solar_model: SolarModel) -> None:
        super().__init__(floor_number, building_data, solar_model)
        self.volume: float = self.length * self.width * self.floor_height
        self.mid_elevation: float = self.base_elevation + self.floor_height * (floor_number - 1 / 2)
        self.window_angles_deg: list[float] = [self.z_rotation_angle_deg, 90+self.z_rotation_angle_deg, 180+self.z_rotation_angle_deg, -90+self.z_rotation_angle_deg]
        # Calculate window surfaces using individual glazing ratios for each side
        # Order: ref, right, opposite, left
        # Note: ref and opposite walls span in Y direction (width), left and right walls span in X direction (length)
        self.window_surfaces: list[float] = [
            building_data.ref_glazing_ratio * self.width * self.floor_height,  # ref (primary direction)
            building_data.right_glazing_ratio * self.length * self.floor_height,  # right (secondary direction)
            building_data.opposite_glazing_ratio * self.width * self.floor_height,  # opposite (primary direction)
            building_data.left_glazing_ratio * self.length * self.floor_height  # left (secondary direction)
        ]
        # Total glazing surface for thermal model
        self.glazing_surface: float = sum(self.window_surfaces)
        self.wall_surface: float = 2 * (self.length + self.width) * self.floor_height - self.glazing_surface
        self._window_masks: dict[str, Mask] = dict()
        self.zone_window_collectors: list[Collector] = []
        self.windows_names: list[str] = ['ref', 'right', 'opposite', 'left']
        self.external_envelope_surface_m2: float = 2 * (self.length + self.width) * self.floor_height
        if self.floor_number == self.n_floors:
            self.external_envelope_surface_m2 += self.length * self.width
        self.hvac_heat_production_kWh_per_year_cooling: float = 0
        self.hvac_heat_production_kWh_per_year_heating: float = 0
        self.hvac_electric_consumption_kWh_per_year_cooling: float = 0
        self.hvac_electric_consumption_kWh_per_year_heating: float = 0

    def window_masks(self) -> dict[str, Mask]:
        return self._window_masks

    def make(self, model_maker: ModelMaker, dp: DataProvider) -> None:
        # n_floors is the number of regular floors, so the top floor number equals n_floors
        if self.floor_number == self.n_floors:
            model_maker.make_side(self.building_data.roof(self.name, 'outdoor', SIDE_TYPES.CEILING, self.volume))
        else:
            # intermediate_floor is guaranteed to exist when there are multiple floors (n_floors > 1)
            assert self.building_data.intermediate_floor is not None, "intermediate_floor should be defined when n_floors > 1"
            model_maker.make_side(self.building_data.intermediate_floor(self.name, f'floor{self.floor_number+1}', SIDE_TYPES.FLOOR, self.floor_surface))
        # If this is the first floor (floor_number == 1) and there's no basement (base_elevation == 0), connect to ground
        if self.floor_number == 1 and self.base_elevation == 0:
            model_maker.make_side(self.building_data.ground_floor(self.name, 'ground', SIDE_TYPES.FLOOR, self.floor_surface))
        model_maker.make_side(self.building_data.wall(self.name, 'outdoor', SIDE_TYPES.WALL, self.wall_surface))
        model_maker.make_side(self.building_data.glazing(self.name, 'outdoor', SIDE_TYPES.GLAZING, self.glazing_surface))
        regular_rate = self.building_data.regular_air_renewal_rate_vol_per_hour
        if regular_rate is not None:
            nominal_airflow = regular_rate * self.volume / 3600
        else:
            nominal_airflow = 0.0
        model_maker.connect_airflow(self.name, 'outdoor', nominal_value=nominal_airflow)

        for window_name, window_angle, window_surface in zip(self.windows_names, self.window_angles_deg, self.window_surfaces):
            window_collector: Collector = Collector(self.solar_system, f'{window_name}', surface_m2=window_surface, exposure_deg=window_angle, slope_deg=SLOPES.VERTICAL.value, solar_factor=self.building_data.glazing_solar_factor, observer_elevation_m=self.mid_elevation)
            self.zone_window_collectors.append(window_collector)
            self._window_masks[window_name] = window_collector.mask


class Building:
    """High-level orchestrator for generating and simulating a BATEM building.

    The class assembles the context, solar model, thermal network, HVAC
    controllers, and simulation engine required to execute a full-year building
    simulation.

    :param context_data: Geographic and climatic context description.
    :param building_data: Physical parameters and HVAC capacities.
    :ivar context: Instantiated :class:`Context` wrapping weather and bindings.
    :ivar dp: Shared :class:`~batem.core.data.DataProvider` used across modules.
    :ivar simulation: Configured :class:`~batem.core.control.Simulation` object.
    :ivar floors: List of :class:`Zone` instances representing each building
        level.
    """

    def __init__(self, context_data: ContextData, building_data: BuildingData) -> None:
        self.context: Context = Context(context_data)
        self.context_data: ContextData = context_data
        self.dp: DataProvider = self.context.dp
        self.building_data: BuildingData = building_data
        self.building_view: BuildingView = BuildingView(length=building_data.length, width=building_data.width, n_floors=building_data.n_floors, floor_height=building_data.floor_height, base_elevation=building_data.base_elevation, ref_glazing_ratio=building_data.ref_glazing_ratio, right_glazing_ratio=building_data.right_glazing_ratio, opposite_glazing_ratio=building_data.opposite_glazing_ratio, left_glazing_ratio=building_data.left_glazing_ratio)
        self.building_view.make(rotation_angle_deg=building_data.z_rotation_angle_deg)
        self.dp.add_param('CCO2:outdoor', 400)
        self.dp.add_param('TZ:ground', context_data.ground_temperature)

        solar_model: SolarModel = self.context.solar_model

        zone_floors: list[Zone] = []
        zone_name_volumes: dict[str, float] = {}
        if building_data.base_elevation > 0:
            zone_floors.append(BasementZone(0, building_data, solar_model))
            zone_name_volumes[zone_floors[0].name] = zone_floors[0].volume
        # n_floors represents the number of regular floors (excluding basement)
        # So we create floors 1 through n_floors
        for floor_number in range(1, building_data.n_floors + 1):
            zone_floor = ZoneFloor(floor_number, building_data, solar_model)
            zone_floors.append(zone_floor)
            zone_name_volumes[zone_floor.name] = zone_floor.volume
        zone_name_volumes['outdoor'] = None
        zone_name_volumes['ground'] = None
        self.zone_names: list[str] = [zone_floor.name for zone_floor in zone_floors]
        self.zone_floors: list[Zone] = zone_floors
        self.zone_outdoor_regular_airflows_m3_per_s: dict[str, float] = {}
        airflow_defaults: dict[str, float] = {}
        airflow_bounds: dict[str, float] = {}
        airflow_names: list[str] = []
        # Set up airflow for each floor (exclude floor 0, which is the basement)
        for zone_floor in zone_floors:
            if zone_floor.floor_number == 0:  # Skip basement (floor 0) - no regular outdoor airflow
                continue
            volume: float | None = getattr(zone_floor, 'volume', None)
            if volume is None:
                continue
            airflow_name = f'Q:{zone_floor.name}-outdoor'
            base_value: float | None = None
            bound_upper: float = 0.0
            if self.building_data.regular_air_renewal_rate_vol_per_hour is not None:
                print(f"Floor {zone_floor.name} has a regular airflow: {self.building_data.regular_air_renewal_rate_vol_per_hour} vol/h")
                regular_airflow_m3_per_s: float = (self.building_data.regular_air_renewal_rate_vol_per_hour * volume) / 3600.0
                self.zone_outdoor_regular_airflows_m3_per_s[zone_floor.name] = regular_airflow_m3_per_s
                base_value = regular_airflow_m3_per_s
                bound_upper = max(bound_upper, regular_airflow_m3_per_s)
            if base_value is None:
                base_value = 0.0
            bound_upper = max(bound_upper, base_value)
            airflow_defaults[airflow_name] = base_value
            airflow_bounds[airflow_name] = bound_upper
            airflow_names.append(airflow_name)
        if airflow_names:
            self.dp.add_data_names_in_fingerprint(*airflow_names)
            for airflow_name, default_value in airflow_defaults.items():
                values = [default_value for _ in self.dp.ks]
                if airflow_name in self.dp:
                    self.dp.add_var(airflow_name, values, force=True)
                else:
                    self.dp.add_var(airflow_name, values)
                bound_upper = airflow_bounds.get(airflow_name, default_value)
                if bound_upper <= 0.0:
                    bound_upper = 1e-6
                if hasattr(self.dp, 'independent_variable_set'):
                    self.dp.independent_variable_set.variable_bounds[airflow_name] = (0.0, bound_upper)

        # Store initial heat recovery efficiency as parameter (will be updated as time series after simulation)
        # The actual time-varying efficiency will be set in _update_ventilation_heat_recovery_efficiency()
        self.dp.add_param('ventilation_heat_recovery_efficiency', building_data.regular_ventilation_heat_recovery_efficiency)
        
        # #### STATE MODEL MAKER AND SURFACES ####
        model_maker: ModelMaker = ModelMaker(data_provider=self.dp, periodic_depth_seconds=building_data.periodic_depth_seconds, state_model_order_max=building_data.state_model_order_max, **zone_name_volumes)

        # Calculate max occupancy per floor based on floor area and density
        # density_occupants_per_100m2 is per unit area, applied to each floor independently
        max_occupancy_per_floor: float = building_data.density_occupants_per_100m2 * (building_data.length * building_data.width) / 100

        siggen: SignalGenerator = SignalGenerator(self.dp, OccupancyProfile(weekday_profile={0: max_occupancy_per_floor, 7: max_occupancy_per_floor*.95, 8: max_occupancy_per_floor*.7, 9: max_occupancy_per_floor*.3, 12: max_occupancy_per_floor*.5, 17: max_occupancy_per_floor*.7, 18: max_occupancy_per_floor*.8, 19: max_occupancy_per_floor*.9, 20: max_occupancy_per_floor}, weekend_profile={0: max_occupancy_per_floor}))
        siggen.add_hvac_period(HeatingPeriod(building_data.heating_period[0], building_data.heating_period[1], weekday_profile={0: building_data.low_heating_setpoint, 7: building_data.normal_heating_setpoint}, weekend_profile={00: building_data.low_heating_setpoint, 7: building_data.normal_heating_setpoint}))
        siggen.add_hvac_period(CoolingPeriod(building_data.cooling_period[0], building_data.cooling_period[1], weekday_profile={0: None, 10: building_data.normal_cooling_setpoint, 18: None}, weekend_profile={0: None, 10: building_data.normal_cooling_setpoint, 18: None}))
        if building_data.long_absence_period is not None:
            siggen.add_long_absence_period(LongAbsencePeriod(building_data.long_absence_period[0], building_data.long_absence_period[1]))
        else:
            siggen.add_long_absence_period(LongAbsencePeriod(building_data.long_absence_period[0], building_data.long_absence_period[1]))
        # Create per-floor signals
        controllers: dict[str, TemperatureController] = {}

        for zone_floor in zone_floors:
            zone_floor.make(model_maker, self.dp)
            # Occupancy profile and HVAC seasons
            if zone_floor.floor_number == 0:
                # Basement: generate signals but no HVAC controller
                siggen.generate(zone_floor.name)
            else:
                # Regular floors: generate signals (SETPOINT, MODE, OCCUPANCY, PRESENCE)
                siggen.generate(zone_floor.name)
                # Get solar gain (returns None if no collectors)
                solar_gain = zone_floor.solar_system.powers_W(gather_collectors=True)
                # Handle case where there are no collectors (solar_gain is None)
                if solar_gain is None:
                    solar_gain = [0.0 for _ in self.dp.ks]
                # Apply shutter control: set solar gains to 0 when outdoor temperature exceeds threshold
                if building_data.shutter_closed_temperature is not None:
                    weather_temperature = self.dp.series('weather_temperature')
                    solar_gain = [0.0 if weather_temperature[k] > building_data.shutter_closed_temperature else solar_gain[k] for k in self.dp.ks]
                self.dp.add_var(f'GAIN_SOLAR:{zone_floor.name}', solar_gain)
                # Add solar to gains
                zone_occupancy: list[float | None] = self.dp.series(f'OCCUPANCY:{zone_floor.name}')

                # Handle None values in occupancy (convert None to 0 for gain calculation)
                # OCCUPANCY contains the actual number of occupants (0 to max_occupancy), not a ratio
                # Total occupancy gain = body_metabolism + occupant_consumption (activities/appliances)
                occupancy_gain: list[float] = [(building_data.body_metabolism + building_data.occupant_consumption) * (_ if _ is not None else 0.0) for _ in zone_occupancy]
                self.dp.add_var(f'GAIN_OCCUPANCY:{zone_floor.name}', occupancy_gain)
                self.dp.add_var(f'GAIN:{zone_floor.name}', [occupancy_gain[k] + solar_gain[k] for k in self.dp.ks])
                self.dp.add_var(f'PCO2:{zone_floor.name}', (siggen.filter(zone_occupancy, lambda x: x * building_data.body_PCO2 if x is not None else 0)))

        model_maker.zones_to_simulate({floor.name: floor.volume for floor in zone_floors})
        # Nominal state model - must be created before TemperatureControllers
        model_maker.nominal
        if self.building_data.initial_temperature is not None:
            self._initialize_state_models(model_maker, self.building_data.initial_temperature)

        # Create HVAC controllers after nominal state model is ready
        for zone_floor in zone_floors:
            if zone_floor.floor_number > 0:
                hvac_port: HVACcontinuousModePort = HVACcontinuousModePort(data_provider=self.dp, zone_name=zone_floor.name, max_heating_power=building_data.max_heating_power, max_cooling_power=building_data.max_cooling_power)
                temperature_setpoint_port: TemperatureSetpointPort = TemperatureSetpointPort(data_provider=self.dp, zone_name=zone_floor.name, heating_levels=[16, 19, 20, 21, 22, 23, 24], cooling_levels=[24, 25, 26, 27, 28])
                controllers[zone_floor.name] = TemperatureController(hvac_heat_port=hvac_port, temperature_setpoint_port=temperature_setpoint_port, model_maker=model_maker)

        self.simulation: Simulation = Simulation(model_maker, body_metabolism=building_data.body_metabolism, occupant_consumption=building_data.occupant_consumption)
        for zone_floor in zone_floors:
            if zone_floor.floor_number > 0:
                self.simulation.add_temperature_controller(zone_name=zone_floor.name, temperature_controller=controllers[zone_floor.name])

    def _initialize_state_models(self, model_maker: ModelMaker, temperature: float) -> None:
        def _set_uniform_initial_state(state_model: StateModel, temp: float) -> StateModel:
            if state_model is None or state_model.n_states == 0:
                return state_model
            target_state: np.ndarray = np.full((state_model.n_states, 1), float(temp))
            state_model.set_state(target_state)
            return state_model

        if hasattr(model_maker, "state_models_cache"):
            model_maker.state_models_cache = {
                key: _set_uniform_initial_state(sm, temperature) for key, sm in model_maker.state_models_cache.items()
            }

        nominal_model: StateModel | None = getattr(model_maker, "nominal_state_model", None)
        if nominal_model is not None:
            _set_uniform_initial_state(nominal_model, temperature)

        original_make_k = model_maker.make_k

        def make_k_with_initial_state(self, *args, **kwargs):
            state_model: StateModel = original_make_k(*args, **kwargs)
            return _set_uniform_initial_state(state_model, temperature)

        model_maker.make_k = types.MethodType(make_k_with_initial_state, model_maker)

    def _calculate_hvac_electric_consumption(self, heat_production_Wh: list[float]) -> list[float]:
        """Calculate HVAC electrical consumption from heat production using appropriate COP."""
        return [
            production / self.building_data.hvac_cop_heating if production > 0
            else production / self.building_data.hvac_cop_cooling
            for production in heat_production_Wh
        ]

    def _initialize_ventilation_heat_recovery_efficiency(self, suffix: str = 'sim') -> None:
        """Initialize ventilation heat recovery efficiency with default values per floor.
        
        Initializes RECOV variables with regular_ventilation_heat_recovery_efficiency.
        These will be updated during simulation based on free cooling conditions.
        Adds RECOV variables to fingerprint so model is rebuilt when they change.
        """
        # Format suffix with # prefix if not empty (e.g., 'sim' -> '#sim')
        if suffix:
            suffix_formatted = f'#{suffix}' if not suffix.startswith('#') else suffix
        else:
            suffix_formatted = ''
        
        # Process each floor separately
        recovery_var_names = []
        for floor in self.zone_floors:
            if floor.floor_number == 0:  # Skip basement
                continue
            
            recovery_var_name = f'RECOV:{floor.name}{suffix_formatted}'
            recovery_var_names.append(recovery_var_name)
            # Initialize with regular efficiency for all time steps
            efficiency_values = [self.building_data.regular_ventilation_heat_recovery_efficiency] * len(self.dp.ks)
            self.dp.add_var(recovery_var_name, efficiency_values)
            # Set bounds for fingerprint calculation (efficiency ranges from 0.0 to 1.0)
            # Use a small range to avoid division by zero, but allow for 0.0 to 1.0
            if hasattr(self.dp, 'independent_variable_set'):
                self.dp.independent_variable_set.variable_bounds[recovery_var_name] = (0.0, 1.0)
        
        # Add RECOV variables to fingerprint so model is rebuilt when they change
        if recovery_var_names:
            self.dp.add_data_names_in_fingerprint(*recovery_var_names)
            # Also add to model maker's fingerprint list (accessed through simulation)
            if hasattr(self, 'simulation') and self.simulation is not None:
                model_maker = self.simulation.model_maker
                for recovery_var_name in recovery_var_names:
                    if recovery_var_name not in model_maker.data_names_in_fingerprint:
                        model_maker.data_names_in_fingerprint = recovery_var_name
    
    def _update_ventilation_heat_recovery_efficiency_at_k(self, k: int, suffix: str = 'sim', pre_control_outputs: dict = None) -> None:
        """Update ventilation heat recovery efficiency at time step k based on previous time step conditions.
        
        Updates RECOV[k] based on conditions from time step k-1 (or k=0 for first time step).
        This allows RECOV[k] to affect the model at time step k.
        
        Free cooling (RECOV=0) is active when:
        - HVAC mode is not heating (mode != 1) AND
        - Indoor temperature > normal_heating_setpoint + free_cooling_setpoint_margin (too hot) AND
        - (outdoor temperature + free_cooling_setpoint_margin) < indoor temperature (outdoor is cooler)
        
        Otherwise sets it to regular_ventilation_heat_recovery_efficiency.
        """
        if self.building_data.free_cooling_setpoint_margin is None:
            return
        
        # Format suffix with # prefix if not empty
        if suffix:
            suffix_formatted = f'#{suffix}' if not suffix.startswith('#') else suffix
        else:
            suffix_formatted = ''
        
        # Process each floor separately
        for floor in self.zone_floors:
            if floor.floor_number == 0:  # Skip basement
                continue
            
            recovery_var_name = f'RECOV:{floor.name}{suffix_formatted}'
            mode_var_name = f'MODE:{floor.name}{suffix_formatted}'
            indoor_temp_var_name = f'TZ_OP:{floor.name}{suffix_formatted}'
            
            try:
                # Use previous time step's conditions to determine RECOV[k]
                # For k=0, use k=0 (will use defaults if not available)
                prev_k = max(0, k - 1)
                
                # Get outdoor temp for current time step k
                outdoor_temp_k = self.dp('weather_temperature', k)
                
                # Try to get mode from previous time step
                try:
                    mode = self.dp(mode_var_name, prev_k)
                except Exception:
                    # If not available, default to heating mode
                    mode = 1
                
                # Try to get indoor temp from previous time step
                try:
                    indoor_temp = self.dp(indoor_temp_var_name, prev_k)
                except Exception:
                    # If not available, use outdoor temp as fallback
                    indoor_temp = self.dp('weather_temperature', prev_k) if prev_k >= 0 else outdoor_temp_k
                
                # Free cooling condition:
                # 1. Mode is not heating (mode != 1) AND
                # 2. Indoor temp > normal_heating_setpoint + free_cooling_setpoint_margin (too hot) AND
                # 3. (outdoor temp + free_cooling_setpoint_margin) < indoor temp (outdoor is cooler)
                if (mode != 1 and  # mode 1 is heating
                        indoor_temp > (self.building_data.normal_heating_setpoint + self.building_data.free_cooling_setpoint_margin) and
                        (outdoor_temp_k + self.building_data.free_cooling_setpoint_margin) < indoor_temp):
                    # Free cooling active: disable heat recovery
                    efficiency_k = 0.0
                else:
                    # Use regular efficiency
                    efficiency_k = self.building_data.regular_ventilation_heat_recovery_efficiency
                
                # Update RECOV at time step k (this will be used for the model at time step k)
                # Note: This updates RECOV[k] which affects the fingerprint, so the model will be rebuilt
                self.dp(recovery_var_name, k, efficiency_k)
            except Exception:
                # If update fails, keep existing value
                pass

    def simulate(self, suffix: str = 'sim') -> BuildingResult:
        """Run the building simulation and return results.
        
        If free_cooling_setpoint_margin is defined, RECOV is updated during simulation
        at each time step based on previous time step conditions (to avoid circular dependency).
        """
        # Initialize RECOV variables with default values before simulation
        self._initialize_ventilation_heat_recovery_efficiency(suffix=suffix)
        
        # Define action rule to update RECOV at each time step (called before state model is built)
        def update_recovery_action_rule(simulation, k: int) -> None:
            """Action rule to update RECOV[k] based on previous time step (k-1) conditions."""
            self._update_ventilation_heat_recovery_efficiency_at_k(k, suffix=suffix)
        
        # Run simulation with action rule to update RECOV during simulation
        if self.building_data.free_cooling_setpoint_margin is not None:
            self.simulation.run(suffix=suffix, action_rule=update_recovery_action_rule)
        else:
            self.simulation.run(suffix=suffix)
        
        floor_results: list[FloorResult] = []
        
        # Calculate HVAC consumption for each floor
        for floor in self.zone_floors:
            if floor.floor_number > 0:  # Regular floors have HVAC systems
                phvac_var_name: str = f'PHVAC:{floor.name}#sim'
                phvac_production_Wh: list[float] = self.dp.series(phvac_var_name)
            else:  # Basement (floor 0) has no HVAC systems
                phvac_production_Wh = [0.0] * len(self.dp.ks)
            
            floor_results.append(FloorResult(
                floor_number=floor.floor_number,
                external_envelope_surface_m2=floor.external_envelope_surface_m2,
                heat_production_Wh=phvac_production_Wh
            ))

        self.building_result: BuildingResult = BuildingResult(
            hvac_cop_heating=self.building_data.hvac_cop_heating,
            hvac_cop_cooling=self.building_data.hvac_cop_cooling,
            floor_results=floor_results
        )
        
        # Store building-level results
        building_heat_production_Wh: list[float] = self.building_result.heat_production_Wh
        self.dp.add_var('PHVAC:building#sim', building_heat_production_Wh)  # , force=True
        self.dp.add_var('HVAC_ELEC:building#sim', self._calculate_hvac_electric_consumption(building_heat_production_Wh))

        # Store floor-level results
        for floor_result in floor_results:
            # Use force=True to allow overwriting variables that may have been created during simulation
            # self.dp.add_var(f'PHVAC:floor{floor_result.floor_number}#sim', floor_result.heat_production_Wh) # , force=True
            self.dp.add_var(f'HVAC_ELEC:{floor_result.floor_number}#sim', self._calculate_hvac_electric_consumption(floor_result.heat_production_Wh))
        
        return self.building_result

    def _print_hvac_power_recommendations(self) -> None:
        """Print recommended HVAC power sizing based on peak and top 5% average demands.
        
        Analyzes the HVAC power time series to recommend appropriate heating and cooling
        capacities. The maximum value represents absolute peak demand, while the top 5%
        average provides a more robust sizing recommendation that avoids over-sizing for
        rare extreme events.
        """
        print("\n" + "=" * 30)
        print("RECOMMENDED HVAC POWER SIZING")
        print("=" * 30)
        
        # Collect data per floor and building-wide
        floor_recommendations: list[dict] = []
        all_heating_powers: list[float] = []
        all_cooling_powers: list[float] = []
        
        for floor in self.zone_floors:
            if f'PHVAC:{floor.name}#sim' in self.dp:
                phvac_series = self.dp.series(f'PHVAC:{floor.name}#sim')
                
                # Separate heating and cooling for this floor
                floor_heating_powers: list[float] = [p for p in phvac_series if p > 0]
                floor_cooling_powers: list[float] = [abs(p) for p in phvac_series if p < 0]
                
                # Calculate floor-level recommendations
                floor_rec = {'floor_name': floor.name}
                
                if floor_heating_powers:
                    max_heating = max(floor_heating_powers)
                    sorted_heating = sorted(floor_heating_powers, reverse=True)
                    top_5_count = max(1, int(len(sorted_heating) * 0.05))
                    avg_top_5_heating = sum(sorted_heating[:top_5_count]) / top_5_count
                    floor_rec['max_heating_kW'] = max_heating / 1000
                    floor_rec['avg5_heating_kW'] = avg_top_5_heating / 1000
                    all_heating_powers.extend(floor_heating_powers)
                else:
                    floor_rec['max_heating_kW'] = 0.0
                    floor_rec['avg5_heating_kW'] = 0.0
                
                if floor_cooling_powers:
                    max_cooling = max(floor_cooling_powers)
                    sorted_cooling = sorted(floor_cooling_powers, reverse=True)
                    top_5_count = max(1, int(len(sorted_cooling) * 0.05))
                    avg_top_5_cooling = sum(sorted_cooling[:top_5_count]) / top_5_count
                    floor_rec['max_cooling_kW'] = max_cooling / 1000
                    floor_rec['avg5_cooling_kW'] = avg_top_5_cooling / 1000
                    all_cooling_powers.extend(floor_cooling_powers)
                else:
                    floor_rec['max_cooling_kW'] = 0.0
                    floor_rec['avg5_cooling_kW'] = 0.0
                
                floor_recommendations.append(floor_rec)
        
        # Print per-floor recommendations
        if floor_recommendations:
            print("\nPer-Floor Recommendations:")
            print("-" * 30)
            for rec in floor_recommendations:
                floor_name = rec['floor_name']
                
                # Heating line
                if rec['max_heating_kW'] > 0:
                    print(f"  {floor_name:15s} - Heating: {rec['max_heating_kW']:5.1f} kW ({rec['avg5_heating_kW']:5.1f} kW @5%)", end="")
                else:
                    print(f"  {floor_name:15s} - Heating: None", end="")
                
                # Cooling line
                if rec['max_cooling_kW'] > 0:
                    print(f"   |   Cooling: {rec['max_cooling_kW']:5.1f} kW ({rec['avg5_cooling_kW']:5.1f} kW @5%)")
                else:
                    print("   |   Cooling: None")
        
        print("=" * 30 + "\n")

    def print_results(self, augmented: bool = False, report_name: str = None) -> None:
        """Print building and floor-level HVAC results in a formatted table.
        
        Displays heat needs (total, heating, cooling) and electric consumption
        for each floor and the building total, including per m² values.
        
        :param augmented: If True, includes detailed comfort assessment per floor
        :type augmented: bool
        :param report_name: If provided, generates a markdown report with this name in the results folder
        :type report_name: str | None
        """

        if self.building_result is None:
            # Try to get results from stored variables if available
            try:
                floor_results: list[FloorResult] = []
                for floor in self.zone_floors:
                    phvac_var_name: str = f'PHVAC:{floor.name}#sim'
                    if phvac_var_name in self.dp:
                        phvac_production_Wh: list[float] = self.dp.series(phvac_var_name)
                    else:
                        phvac_production_Wh = [0.0] * len(self.dp.ks)
                    
                    floor_results.append(FloorResult(
                        floor_number=floor.floor_number,
                        external_envelope_surface_m2=floor.external_envelope_surface_m2,
                        heat_production_Wh=phvac_production_Wh
                    ))
                
                self.building_result = BuildingResult(
                    hvac_cop_heating=self.building_data.hvac_cop_heating,
                    hvac_cop_cooling=self.building_data.hvac_cop_cooling,
                    floor_results=floor_results
                )
            except Exception:
                raise ValueError("No building_result provided and cannot reconstruct from stored data. Please run simulate() first or provide a BuildingResult.")
        
        # Collect data for all floors
        floor_data: list[dict] = []
        floor_names: list[str] = []
        
        for floor_result in self.building_result.floor_results:
            # Calculate totals in kWh
            heat_heating_kWh = sum(floor_result.heat_production_heating_Wh) / 1000.0
            heat_cooling_kWh = sum(floor_result.heat_production_cooling_Wh) / 1000.0  # Keep negative for cooling
            # Total heat is the sum of absolute values of heating and cooling
            heat_total_kWh = abs(heat_heating_kWh) + abs(heat_cooling_kWh)
            
            # Calculate electric consumption (use absolute value for cooling when calculating electricity)
            elec_heating_kWh = heat_heating_kWh / self.building_result.hvac_cop_heating if heat_heating_kWh > 0 else 0.0
            elec_cooling_kWh = abs(heat_cooling_kWh) / self.building_result.hvac_cop_cooling if heat_cooling_kWh < 0 else 0.0
            elec_total_kWh = elec_heating_kWh + elec_cooling_kWh
            
            # Calculate per m² values using external_envelope_surface_m2
            surface = floor_result.external_envelope_surface_m2
            heat_total_per_m2 = heat_total_kWh / surface if surface > 0 else 0.0
            heat_heating_per_m2 = heat_heating_kWh / surface if surface > 0 else 0.0
            heat_cooling_per_m2 = heat_cooling_kWh / surface if surface > 0 else 0.0
            elec_total_per_m2 = elec_total_kWh / surface if surface > 0 else 0.0
            elec_heating_per_m2 = elec_heating_kWh / surface if surface > 0 else 0.0
            elec_cooling_per_m2 = elec_cooling_kWh / surface if surface > 0 else 0.0
            
            floor_name = f"floor{floor_result.floor_number}"
            if floor_result.floor_number == 0:
                floor_name = "basement"
            
            floor_names.append(floor_name)
            floor_data.append({
                'surface': surface,
                'heat_total_kWh': heat_total_kWh,
                'heat_heating_kWh': heat_heating_kWh,
                'heat_cooling_kWh': heat_cooling_kWh,
                'elec_total_kWh': elec_total_kWh,
                'elec_heating_kWh': elec_heating_kWh,
                'elec_cooling_kWh': elec_cooling_kWh,
                'heat_total_per_m2': heat_total_per_m2,
                'heat_heating_per_m2': heat_heating_per_m2,
                'heat_cooling_per_m2': heat_cooling_per_m2,
                'elec_total_per_m2': elec_total_per_m2,
                'elec_heating_per_m2': elec_heating_per_m2,
                'elec_cooling_per_m2': elec_cooling_per_m2
            })
        
        # Calculate building totals as sum of floor values (excluding basement)
        # Exclude basement (floor_number == 0) from totals since it has no HVAC
        building_heat_heating_kWh = sum(data['heat_heating_kWh'] for name, data in zip(floor_names, floor_data) if name != "basement")
        building_heat_cooling_kWh = sum(data['heat_cooling_kWh'] for name, data in zip(floor_names, floor_data) if name != "basement")  # Keep negative for cooling
        # Total heat is the sum of absolute values of heating and cooling
        building_heat_total_kWh = sum(data['heat_total_kWh'] for name, data in zip(floor_names, floor_data) if name != "basement")
        
        building_elec_heating_kWh = sum(data['elec_heating_kWh'] for name, data in zip(floor_names, floor_data) if name != "basement")
        building_elec_cooling_kWh = sum(data['elec_cooling_kWh'] for name, data in zip(floor_names, floor_data) if name != "basement")
        building_elec_total_kWh = sum(data['elec_total_kWh'] for name, data in zip(floor_names, floor_data) if name != "basement")
        
        building_surface = sum(data['surface'] for name, data in zip(floor_names, floor_data) if name != "basement")
        building_heat_total_per_m2 = building_heat_total_kWh / building_surface if building_surface > 0 else 0.0
        building_heat_heating_per_m2 = building_heat_heating_kWh / building_surface if building_surface > 0 else 0.0
        building_heat_cooling_per_m2 = building_heat_cooling_kWh / building_surface if building_surface > 0 else 0.0
        building_elec_total_per_m2 = building_elec_total_kWh / building_surface if building_surface > 0 else 0.0
        building_elec_heating_per_m2 = building_elec_heating_kWh / building_surface if building_surface > 0 else 0.0
        building_elec_cooling_per_m2 = building_elec_cooling_kWh / building_surface if building_surface > 0 else 0.0
        
        # Add building total to floor_names and floor_data
        floor_names.append("BUILDING TOTAL")
        floor_data.append({
            'surface': building_surface,
            'heat_total_kWh': building_heat_total_kWh,
            'heat_heating_kWh': building_heat_heating_kWh,
            'heat_cooling_kWh': building_heat_cooling_kWh,
            'elec_total_kWh': building_elec_total_kWh,
            'elec_heating_kWh': building_elec_heating_kWh,
            'elec_cooling_kWh': building_elec_cooling_kWh,
            'heat_total_per_m2': building_heat_total_per_m2,
            'heat_heating_per_m2': building_heat_heating_per_m2,
            'heat_cooling_per_m2': building_heat_cooling_per_m2,
            'elec_total_per_m2': building_elec_total_per_m2,
            'elec_heating_per_m2': building_elec_heating_per_m2,
            'elec_cooling_per_m2': building_elec_cooling_per_m2
        })
        
        # Create transposed table with metrics as rows and floors as columns
        table = prettytable.PrettyTable()
        table.field_names = ["Metric"] + floor_names
        
        # Add rows for each metric with both kWh and kWh/m²
        table.add_row(["External envelope (m²)"] + [f"{int(round(data['surface']))}" for data in floor_data])
        table.add_row([""] + [""] * len(floor_names))  # Empty row for spacing
        
        table.add_row(["Heat Total (kWh)"] + [f"{int(round(data['heat_total_kWh']))}" for data in floor_data])
        table.add_row(["Heat Total (kWh/m²)"] + [f"{int(round(data['heat_total_per_m2']))}" for data in floor_data])
        table.add_row([""] + [""] * len(floor_names))  # Empty row for spacing
        
        table.add_row(["Heat Heating (kWh)"] + [f"{int(round(data['heat_heating_kWh']))}" for data in floor_data])
        table.add_row(["Heat Heating (kWh/m²)"] + [f"{int(round(data['heat_heating_per_m2']))}" for data in floor_data])
        table.add_row([""] + [""] * len(floor_names))  # Empty row for spacing
        
        table.add_row(["Heat Cooling (kWh)"] + [f"{int(round(data['heat_cooling_kWh']))}" for data in floor_data])
        table.add_row(["Heat Cooling (kWh/m²)"] + [f"{int(round(data['heat_cooling_per_m2']))}" for data in floor_data])
        table.add_row([""] + [""] * len(floor_names))  # Empty row for spacing
        
        table.add_row(["Elec Total (kWh)"] + [f"{int(round(data['elec_total_kWh']))}" for data in floor_data])
        table.add_row(["Elec Total (kWh/m²)"] + [f"{int(round(data['elec_total_per_m2']))}" for data in floor_data])
        table.add_row([""] + [""] * len(floor_names))  # Empty row for spacing
        
        table.add_row(["Elec Heating (kWh)"] + [f"{int(round(data['elec_heating_kWh']))}" for data in floor_data])
        table.add_row(["Elec Heating (kWh/m²)"] + [f"{int(round(data['elec_heating_per_m2']))}" for data in floor_data])
        table.add_row([""] + [""] * len(floor_names))  # Empty row for spacing
        
        table.add_row(["Elec Cooling (kWh)"] + [f"{int(round(data['elec_cooling_kWh']))}" for data in floor_data])
        table.add_row(["Elec Cooling (kWh/m²)"] + [f"{int(round(data['elec_cooling_per_m2']))}" for data in floor_data])
        
        # Set alignment - left for metric column, right for all floor columns
        table.align["Metric"] = "l"
        for floor_name in floor_names:
            table.align[floor_name] = "r"
        
        # Print table
        print("\n" + "=" * 30)
        print("BUILDING HVAC RESULTS")
        print("=" * 30)
        print(f"COP Heating: {self.building_result.hvac_cop_heating:.2f} | COP Cooling: {self.building_result.hvac_cop_cooling:.2f}")
        print("=" * 30)
        print(table)
        print("=" * 30 + "\n")
        
        # Calculate and print recommended HVAC power sizing
        self._print_hvac_power_recommendations()
        
        total_energy_needs: float = 0
        # Print comfort assessment summary for all floors
        # Configure preference with HVAC COPs so energy costs are calculated correctly
        # Assuming mode 1 = heating, mode -1 = cooling (you may need to adjust based on your mode conventions)
        preference: Preference = Preference(
            mode_cop={
                1: self.building_data.hvac_cop_heating,
                -1: self.building_data.hvac_cop_cooling
            }
        )
        floor_comfort_data: list[dict] = []
        for floor in self.zone_floors:
            print(f'\n##### Zone {floor.name} ######\n')
            # Only floors with HVAC controllers have PHVAC variables (floor0/basement doesn't have HVAC)
            if f'PHVAC:{floor.name}#sim' in self.dp:
                floor_energy_needs: float = sum([abs(_) for _ in self.dp.series(f'PHVAC:{floor.name}#sim')])
                cooling_energy_needs: float = sum([abs(_) for _ in self.dp.series(f'PHVAC:{floor.name}#sim') if _ < 0])
                heating_energy_needs: float = sum([abs(_) for _ in self.dp.series(f'PHVAC:{floor.name}#sim') if _ > 0])
                # Calculate total envelope surface (walls + glazing + roof if top floor)
                # This is the surface that exchanges heat with outdoor environment
                floor_surface: float = self.building_data.length * self.building_data.width
                if hasattr(floor, 'wall_surface') and hasattr(floor, 'glazing_surface'):
                    # Use the actual surfaces from the floor object
                    envelope_surface: float = floor.wall_surface + floor.glazing_surface
                    # Add roof surface if this is the top floor
                    if floor.floor_number == self.building_data.n_floors:
                        envelope_surface += floor_surface
                else:
                    # Fallback calculation: wall + glazing + roof for top floor
                    wall_surface: float = 2 * (self.building_data.length + self.building_data.width) * self.building_data.floor_height
                    glazing_surface: float = sum([
                        self.building_data.ref_glazing_ratio * self.building_data.width * self.building_data.floor_height,
                        self.building_data.right_glazing_ratio * self.building_data.length * self.building_data.floor_height,
                        self.building_data.opposite_glazing_ratio * self.building_data.width * self.building_data.floor_height,
                        self.building_data.left_glazing_ratio * self.building_data.length * self.building_data.floor_height
                    ])
                    wall_surface -= glazing_surface  # Remove glazing area from wall area
                    envelope_surface: float = wall_surface + glazing_surface
                    if floor.floor_number == self.building_data.n_floors:
                        envelope_surface += floor_surface
                print(f'Floor {floor.name} HVAC system consumption: {round(floor_energy_needs/1000/envelope_surface)} kWh/m2.year (cooling: {round(cooling_energy_needs/1000/envelope_surface)} kWh/m2.year, heating: {round(heating_energy_needs/1000/envelope_surface)} kWh/m2.year)')
                total_energy_needs += floor_energy_needs
                
                # Get MODE data if available for accurate cost calculation
                modes_data = self.dp.series(f'MODE:{floor.name}') if f'MODE:{floor.name}' in self.dp else None
                
                if augmented:
                    preference.print_assessment(
                        self.dp.datetimes,
                        self.dp.series(f'PHVAC:{floor.name}#sim'),
                        self.dp.series(f'TZ_OP:{floor.name}#sim'),
                        self.dp.series(f'CCO2:{floor.name}#sim'),
                        self.dp.series(f'OCCUPANCY:{floor.name}'),
                        modes=modes_data
                    )
                
                # Collect floor data for comfort summary table
                floor_comfort_data.append({
                    'floor_name': floor.name,
                    'datetimes': self.dp.datetimes,
                    'PHVAC': self.dp.series(f'PHVAC:{floor.name}#sim'),
                    'temperatures': self.dp.series(f'TZ_OP:{floor.name}#sim'),
                    'CO2_concentrations': self.dp.series(f'CCO2:{floor.name}#sim'),
                    'occupancies': self.dp.series(f'OCCUPANCY:{floor.name}'),
                    'modes': modes_data
                })
            else:
                print(f'Floor {floor.name} has no HVAC system')
        
        # Print compact comfort summary table for all floors
        if floor_comfort_data:
            preference.print_comfort(floor_comfort_data)
        
        # Generate markdown report if requested
        if report_name is not None:
            self._generate_markdown_report(
                report_name=report_name,
                floor_names=floor_names,
                floor_data=floor_data,
                floor_comfort_data=floor_comfort_data,
                preference=preference
            )

    def _generate_markdown_report(
        self,
        report_name: str,
        floor_names: list[str],
        floor_data: list[dict],
        floor_comfort_data: list[dict],
        preference: Preference
    ) -> None:
        """Generate a markdown report with building simulation results.
        
        :param report_name: Name of the markdown file (without extension)
        :param floor_names: List of floor names
        :param floor_data: List of dictionaries containing floor data
        :param floor_comfort_data: List of dictionaries containing comfort data
        :param preference: Preference object for comfort calculations
        """
        import os
        
        # Get results folder path
        file_path_builder = FilePathBuilder()
        results_folder = file_path_builder.get_work_folder("results")
        
        # Create figures subfolder
        figures_folder = os.path.join(results_folder, "figures")
        os.makedirs(figures_folder, exist_ok=True)
        
        # Ensure .md extension
        if not report_name.endswith('.md'):
            report_name += '.md'
        
        report_path = os.path.join(results_folder, report_name)
        
        # Generate markdown content
        markdown_content = []
        
        # Title
        markdown_content.append("# Building HVAC Simulation Results\n")
        markdown_content.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        # Add 3D building visualization
        markdown_content.append("## 3D Building View\n\n")
        try:
            building_3d_filename = f"{report_name.replace('.md', '')}_building_3d.png"
            building_3d_path = os.path.join(figures_folder, building_3d_filename)
            self.save_building_plot(building_3d_path)
            markdown_content.append(f"![3D Building View](figures/{building_3d_filename})\n\n")
            markdown_content.append(f"*Building geometry with {self.building_data.n_floors} floors, " +
                                    f"dimensions: {self.building_data.length}m × {self.building_data.width}m*\n\n")
        except Exception as e:
            print(f"Warning: Could not generate 3D building plot: {e}")
            markdown_content.append("*3D building visualization not available*\n\n")
        
        # COP Information
        markdown_content.append("## HVAC System Configuration\n")
        markdown_content.append(f"- **Heating COP**: {self.building_result.hvac_cop_heating:.2f}\n")
        markdown_content.append(f"- **Cooling COP**: {self.building_result.hvac_cop_cooling:.2f}\n\n")
        
        # Add recommended HVAC power sizing
        markdown_content.append("## Recommended HVAC Power Sizing\n\n")
        markdown_content.append("Recommended HVAC capacities based on peak demand and top 5% average:\n\n")
        
        # Calculate recommended powers (same logic as _print_hvac_power_recommendations)
        floor_recommendations: list[dict] = []
        for floor in self.zone_floors:
            if f'PHVAC:{floor.name}#sim' in self.dp:
                phvac_series = self.dp.series(f'PHVAC:{floor.name}#sim')
                
                floor_heating_powers: list[float] = [p for p in phvac_series if p > 0]
                floor_cooling_powers: list[float] = [abs(p) for p in phvac_series if p < 0]
                
                floor_rec = {'floor_name': floor.name}
                
                if floor_heating_powers:
                    max_heating = max(floor_heating_powers)
                    sorted_heating = sorted(floor_heating_powers, reverse=True)
                    top_5_count = max(1, int(len(sorted_heating) * 0.05))
                    avg_top_5_heating = sum(sorted_heating[:top_5_count]) / top_5_count
                    floor_rec['max_heating_kW'] = max_heating / 1000
                    floor_rec['avg5_heating_kW'] = avg_top_5_heating / 1000
                else:
                    floor_rec['max_heating_kW'] = 0.0
                    floor_rec['avg5_heating_kW'] = 0.0
                
                if floor_cooling_powers:
                    max_cooling = max(floor_cooling_powers)
                    sorted_cooling = sorted(floor_cooling_powers, reverse=True)
                    top_5_count = max(1, int(len(sorted_cooling) * 0.05))
                    avg_top_5_cooling = sum(sorted_cooling[:top_5_count]) / top_5_count
                    floor_rec['max_cooling_kW'] = max_cooling / 1000
                    floor_rec['avg5_cooling_kW'] = avg_top_5_cooling / 1000
                else:
                    floor_rec['max_cooling_kW'] = 0.0
                    floor_rec['avg5_cooling_kW'] = 0.0
                
                floor_recommendations.append(floor_rec)
        
        if floor_recommendations:
            markdown_content.append("| Floor | Heating (max) | Heating (@5%) | Cooling (max) | Cooling (@5%) |\n")
            markdown_content.append("|-------|---------------|---------------|---------------|---------------|\n")
            for rec in floor_recommendations:
                heating_max = f"{rec['max_heating_kW']:.1f} kW" if rec['max_heating_kW'] > 0 else "None"
                heating_5 = f"{rec['avg5_heating_kW']:.1f} kW" if rec['avg5_heating_kW'] > 0 else "None"
                cooling_max = f"{rec['max_cooling_kW']:.1f} kW" if rec['max_cooling_kW'] > 0 else "None"
                cooling_5 = f"{rec['avg5_cooling_kW']:.1f} kW" if rec['avg5_cooling_kW'] > 0 else "None"
                markdown_content.append(f"| {rec['floor_name']} | {heating_max} | {heating_5} | {cooling_max} | {cooling_5} |\n")
            markdown_content.append("\n*@5%: Average of the top 5% highest power values*\n\n")
        
        # Main results table
        markdown_content.append("## Energy Consumption Summary\n\n")
        
        # Create markdown table
        markdown_content.append("| Metric | " + " | ".join(floor_names) + " |\n")
        markdown_content.append("|" + "---|" * (len(floor_names) + 1) + "\n")
        
        # Add data rows
        markdown_content.append("| **External envelope (m²)** | " + " | ".join([f"{int(round(data['surface']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| | " + " | ".join([""] * len(floor_names)) + " |\n")
        
        markdown_content.append("| **Heat Total (kWh)** | " + " | ".join([f"{int(round(data['heat_total_kWh']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| **Heat Total (kWh/m²)** | " + " | ".join([f"{int(round(data['heat_total_per_m2']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| | " + " | ".join([""] * len(floor_names)) + " |\n")
        
        markdown_content.append("| **Heat Heating (kWh)** | " + " | ".join([f"{int(round(data['heat_heating_kWh']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| **Heat Heating (kWh/m²)** | " + " | ".join([f"{int(round(data['heat_heating_per_m2']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| | " + " | ".join([""] * len(floor_names)) + " |\n")
        
        markdown_content.append("| **Heat Cooling (kWh)** | " + " | ".join([f"{int(round(data['heat_cooling_kWh']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| **Heat Cooling (kWh/m²)** | " + " | ".join([f"{int(round(data['heat_cooling_per_m2']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| | " + " | ".join([""] * len(floor_names)) + " |\n")
        
        markdown_content.append("| **Elec Total (kWh)** | " + " | ".join([f"{int(round(data['elec_total_kWh']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| **Elec Total (kWh/m²)** | " + " | ".join([f"{int(round(data['elec_total_per_m2']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| | " + " | ".join([""] * len(floor_names)) + " |\n")
        
        markdown_content.append("| **Elec Heating (kWh)** | " + " | ".join([f"{int(round(data['elec_heating_kWh']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| **Elec Heating (kWh/m²)** | " + " | ".join([f"{int(round(data['elec_heating_per_m2']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| | " + " | ".join([""] * len(floor_names)) + " |\n")
        
        markdown_content.append("| **Elec Cooling (kWh)** | " + " | ".join([f"{int(round(data['elec_cooling_kWh']))}" for data in floor_data]) + " |\n")
        markdown_content.append("| **Elec Cooling (kWh/m²)** | " + " | ".join([f"{int(round(data['elec_cooling_per_m2']))}" for data in floor_data]) + " |\n")
        markdown_content.append("\n")
        
        # Add comfort summary if available
        if floor_comfort_data:
            markdown_content.append("## Comfort Assessment Summary\n\n")
            
            # Calculate comfort metrics for each floor using the same logic as print_comfort
            comfort_metrics = []
            for floor_data_item in floor_comfort_data:
                datetimes = floor_data_item['datetimes']
                temperatures = floor_data_item['temperatures']
                co2_concentrations = floor_data_item['CO2_concentrations']
                occupancies = floor_data_item['occupancies']
                phvac = floor_data_item['PHVAC']
                modes = floor_data_item.get('modes')
                
                # Calculate metrics using Preference methods
                hours = [dt.hour for dt in datetimes]
                thermal_dis = preference.thermal_comfort_dissatisfaction(temperatures, occupancies, hours) * 100
                co2_dis = preference.air_quality_dissatisfaction(co2_concentrations, occupancies) * 100
                comfort_dis = preference.comfort_dissatisfaction(temperatures, co2_concentrations, occupancies, hours) * 100
                
                # Calculate temperature quality distribution
                hour_quality_counters = {'extreme cold': 0, 'cold': 0, 'perfect': 0, 'warm': 0, 'extreme warm': 0}
                n_hours_with_presence = 0
                sleeping_hours_set = preference.sleeping_hours
                
                for k, temperature in enumerate(temperatures):
                    if occupancies[k] > 0:
                        if sleeping_hours_set and hours[k] in sleeping_hours_set:
                            continue
                        n_hours_with_presence += 1
                        
                        if temperature < preference.extreme_temperatures[0]:
                            hour_quality_counters['extreme cold'] += 1
                        elif temperature < preference.preferred_temperatures[0]:
                            hour_quality_counters['cold'] += 1
                        elif temperature > preference.extreme_temperatures[1]:
                            hour_quality_counters['extreme warm'] += 1
                        elif temperature > preference.preferred_temperatures[1]:
                            hour_quality_counters['warm'] += 1
                        else:
                            hour_quality_counters['perfect'] += 1
                
                perfect_pct = (100 * hour_quality_counters['perfect'] / n_hours_with_presence) if n_hours_with_presence > 0 else 0.0
                cold_pct = (100 * hour_quality_counters['cold'] / n_hours_with_presence) if n_hours_with_presence > 0 else 0.0
                warm_pct = (100 * hour_quality_counters['warm'] / n_hours_with_presence) if n_hours_with_presence > 0 else 0.0
                extreme_pct = (100 * (hour_quality_counters['extreme cold'] + hour_quality_counters['extreme warm']) / n_hours_with_presence) if n_hours_with_presence > 0 else 0.0
                
                # ICONE indicator and daily electricity cost (€/day)
                icone_value = preference.icone(co2_concentrations, occupancies)
                daily_cost = preference.daily_cost_euros(phvac, modes, power_unit='Wh')
                
                comfort_metrics.append({
                    'floor': floor_data_item['floor_name'],
                    'thermal_discomfort': thermal_dis,
                    'co2_discomfort': co2_dis,
                    'comfort_discomfort': comfort_dis,
                    'perfect': perfect_pct,
                    'cold': cold_pct,
                    'warm': warm_pct,
                    'extreme': extreme_pct,
                    'icone': icone_value,
                    'daily_cost_eur': daily_cost
                })
            
            # Create comfort table
            markdown_content.append("| Metric | " + " | ".join([m['floor'] for m in comfort_metrics]) + " |\n")
            markdown_content.append("|" + "---|" * (len(comfort_metrics) + 1) + "\n")
            markdown_content.append("| **Thermal Discomfort (%)** | " + " | ".join([f"{m['thermal_discomfort']:.1f}" for m in comfort_metrics]) + " |\n")
            markdown_content.append("| **CO2 Discomfort (%)** | " + " | ".join([f"{m['co2_discomfort']:.1f}" for m in comfort_metrics]) + " |\n")
            markdown_content.append("| **Overall Discomfort (%)** | " + " | ".join([f"{m['comfort_discomfort']:.1f}" for m in comfort_metrics]) + " |\n")
            markdown_content.append("| | " + " | ".join([""] * len(comfort_metrics)) + " |\n")
            markdown_content.append("| **Perfect (%)** | " + " | ".join([f"{m['perfect']:.1f}" for m in comfort_metrics]) + " |\n")
            markdown_content.append("| **Cold (%)** | " + " | ".join([f"{m['cold']:.1f}" for m in comfort_metrics]) + " |\n")
            markdown_content.append("| **Warm (%)** | " + " | ".join([f"{m['warm']:.1f}" for m in comfort_metrics]) + " |\n")
            markdown_content.append("| **Extreme (%)** | " + " | ".join([f"{m['extreme']:.1f}" for m in comfort_metrics]) + " |\n")
            markdown_content.append("| **ICONE** | " + " | ".join([f"{m['icone']:.2f}" for m in comfort_metrics]) + " |\n")
            markdown_content.append("| **Electricity Cost (€/day)** | " + " | ".join([f"{m['daily_cost_eur']:.2f}" for m in comfort_metrics]) + " |\n")
            markdown_content.append("\n")
            
            # Add comfort definitions
            markdown_content.append("### Comfort Definitions\n\n")
            markdown_content.append("**Thermal Comfort Zones:**\n")
            markdown_content.append(f"- **Preferred temperature range**: {preference.preferred_temperatures[0]:.1f}°C to {preference.preferred_temperatures[1]:.1f}°C\n")
            markdown_content.append(f"- **Extreme temperature bounds**: {preference.extreme_temperatures[0]:.1f}°C to {preference.extreme_temperatures[1]:.1f}°C\n")
            markdown_content.append("- **Perfect**: Temperature within preferred range\n")
            markdown_content.append("- **Cold**: Below preferred range but above extreme cold\n")
            markdown_content.append("- **Warm**: Above preferred range but below extreme warm\n")
            markdown_content.append("- **Extreme**: Outside extreme temperature bounds\n\n")
            
            markdown_content.append("**Air Quality:**\n")
            markdown_content.append(f"- **Preferred CO₂ concentration**: {preference.preferred_CO2_concentration[0]:.0f} to {preference.preferred_CO2_concentration[1]:.0f} ppm\n")
            markdown_content.append(f"- **Thermal weight vs CO₂**: {preference.temperature_weight_wrt_CO2:.2f}\n")
            markdown_content.append(f"- **Energy cost weight vs comfort**: {preference.power_weight_wrt_comfort:.2f}\n\n")
            
            if preference.sleeping_hours:
                sleeping_hours_str = ", ".join([str(h) for h in sorted(preference.sleeping_hours)])
                markdown_content.append(f"**Sleeping hours** (excluded from thermal comfort): {sleeping_hours_str}\n\n")
        
        # Add heliodon plots section
        markdown_content.append("## Solar Access Analysis (Heliodon Plots)\n\n")
        markdown_content.append("The following diagrams show the sun path and solar access for each floor's windows, " +
                                "including horizon masks and obstacles.\n\n")
        
        # Generate and save heliodon plots for each floor
        heliodon_images = []
        for floor in self.zone_floors:
            if floor.floor_number == 0:
                continue  # Skip basement
            
            try:
                # Generate heliodon plot
                axes = self.plot_heliodon(floor.floor_number)
                
                if axes is not None:
                    # Get the current figure
                    fig = plt.gcf()
                    
                    # Save figure to figures subfolder
                    heliodon_filename = f"{report_name.replace('.md', '')}_heliodon_floor{floor.floor_number}.png"
                    heliodon_path = os.path.join(figures_folder, heliodon_filename)
                    fig.savefig(heliodon_path, dpi=150, bbox_inches='tight')
                    plt.close(fig)  # Close the figure to free memory
                    
                    heliodon_images.append({
                        'floor': floor.name,
                        'filename': f"figures/{heliodon_filename}",  # Relative path from results folder
                        'elevation': floor.mid_elevation
                    })
            except Exception as e:
                print(f"Warning: Could not generate heliodon plot for {floor.name}: {e}")
                continue
        
        # Add heliodon images to markdown
        if heliodon_images:
            for img_info in heliodon_images:
                markdown_content.append(f"### {img_info['floor']} (Elevation: {img_info['elevation']:.1f}m)\n\n")
                markdown_content.append(f"![Heliodon for {img_info['floor']}]({img_info['filename']})\n\n")
        else:
            markdown_content.append("*No heliodon plots available (no windows or solar data)*\n\n")
        
        # Add building parameters section
        markdown_content.append("## Building Parameters\n\n")
        markdown_content.append("### Geometry\n")
        markdown_content.append(f"- **Length**: {self.building_data.length:.2f} m\n")
        markdown_content.append(f"- **Width**: {self.building_data.width:.2f} m\n")
        markdown_content.append(f"- **Number of floors**: {self.building_data.n_floors}\n")
        markdown_content.append(f"- **Floor height**: {self.building_data.floor_height:.2f} m\n")
        markdown_content.append(f"- **Base elevation**: {self.building_data.base_elevation:.2f} m\n")
        markdown_content.append(f"- **Rotation angle**: {self.building_data.z_rotation_angle_deg:.1f}°\n\n")
        
        markdown_content.append("### Glazing\n")
        markdown_content.append(f"- **Reference side glazing ratio**: {self.building_data.ref_glazing_ratio:.2%}\n")
        markdown_content.append(f"- **Opposite side glazing ratio**: {self.building_data.opposite_glazing_ratio:.2%}\n")
        markdown_content.append(f"- **Left side glazing ratio**: {self.building_data.left_glazing_ratio:.2%}\n")
        markdown_content.append(f"- **Right side glazing ratio**: {self.building_data.right_glazing_ratio:.2%}\n")
        markdown_content.append(f"- **Glazing solar factor**: {self.building_data.glazing_solar_factor:.2f}\n")
        if self.building_data.shutter_closed_temperature is not None:
            markdown_content.append(f"- **Shutter closed temperature**: {self.building_data.shutter_closed_temperature:.1f}°C\n")
        markdown_content.append("\n")
        
        # Add wall compositions with surfaces
        markdown_content.append("### Wall Compositions and Surfaces\n\n")
        
        # Calculate U-values for each composition type
        composition_u_values = {}
        from batem.core.library import properties as props_lib
        
        for comp_name, layers in self.building_data.compositions.items():
            try:
                # Determine position based on composition type
                if comp_name in ['roof', 'ground_floor', 'basement_floor', 'intermediate_floor']:
                    position = 'horizontal'
                    first_layer_indoor = True
                    last_layer_indoor = False
                    heating_floor = (comp_name == 'ground_floor')
                else:  # wall
                    position = 'vertical'
                    first_layer_indoor = True
                    last_layer_indoor = False
                    heating_floor = False
                
                # Create composition to calculate U-value
                comp = Composition(
                    first_layer_indoor=first_layer_indoor,
                    last_layer_indoor=last_layer_indoor,
                    position=position,
                    indoor_average_temperature_in_celsius=20,
                    outdoor_average_temperature_in_celsius=5,
                    wind_speed_is_m_per_sec=2.4,
                    heating_floor=heating_floor
                )
                for material, thickness in layers:
                    comp.layer(material, thickness)
                
                composition_u_values[comp_name] = comp.U
            except (KeyError, ValueError, AttributeError) as e:
                # Material not in library or calculation error - show as N/A
                composition_u_values[comp_name] = None
            except Exception as e:
                # Other errors - also show as N/A
                composition_u_values[comp_name] = None
        
        # Calculate wall surfaces per side for each floor
        markdown_content.append("**Wall Compositions:**\n\n")
        markdown_content.append("| Component | U-value (W/m²·K) | Layers |\n")
        markdown_content.append("|-----------|------------------|--------|\n")
        has_na = False
        for comp_name, layers in self.building_data.compositions.items():
            u_value = composition_u_values.get(comp_name, None)
            u_str = f"{u_value:.3f}" if u_value is not None else "N/A"
            if u_value is None:
                has_na = True
            layers_str = ", ".join([f"{mat}({th*1000:.0f}mm)" for mat, th in layers])
            markdown_content.append(f"| {comp_name} | {u_str} | {layers_str} |\n")
        if has_na:
            markdown_content.append("\n*Note: N/A indicates that U-value could not be calculated (material may need to be loaded into properties library)*\n")
        markdown_content.append("\n")
        
        # Add wall and glazing surfaces per side for each floor
        markdown_content.append("**Surfaces per Side (per floor):**\n\n")
        markdown_content.append("| Floor | Side | Wall Surface (m²) | Glazing Surface (m²) | Normal Direction (°) |\n")
        markdown_content.append("|-------|------|-------------------|----------------------|----------------------|\n")
        
        for floor in self.zone_floors:
            if floor.floor_number == 0:
                continue  # Skip basement
            
            # Calculate wall surfaces per side
            # ref and opposite: width * floor_height - glazing
            # right and left: length * floor_height - glazing
            side_names = ['ref', 'right', 'opposite', 'left']
            side_dimensions = [
                (floor.width, 'width'),   # ref
                (floor.length, 'length'),  # right
                (floor.width, 'width'),   # opposite
                (floor.length, 'length')  # left
            ]
            
            for i, (side_name, (dim, dim_type)) in enumerate(zip(side_names, side_dimensions)):
                total_side_surface = dim * floor.floor_height
                glazing_surface = floor.window_surfaces[i] if i < len(floor.window_surfaces) else 0.0
                wall_surface = total_side_surface - glazing_surface
                
                # Get normal direction (azimuth angle)
                normal_angle = floor.window_angles_deg[i] if i < len(floor.window_angles_deg) else 0.0
                # Normalize to 0-360 range
                normal_angle = normal_angle % 360
                if normal_angle < 0:
                    normal_angle += 360
                
                markdown_content.append(f"| {floor.name} | {side_name} | {wall_surface:.1f} | {glazing_surface:.1f} | {normal_angle:.1f}° |\n")
        
        # Add roof surface if applicable
        for floor in self.zone_floors:
            if floor.floor_number == self.building_data.n_floors:
                roof_surface = floor.length * floor.width
                markdown_content.append(f"| {floor.name} | roof | {roof_surface:.1f} | 0.0 | 90.0° (up) |\n")
                break
        
        markdown_content.append("\n")
        markdown_content.append("*Normal direction: azimuth angle in degrees (0° = South, 90° = West, 180° = North, 270° = East)*\n\n")
        
        markdown_content.append("### HVAC Control\n")
        markdown_content.append(f"- **Low heating setpoint**: {self.building_data.low_heating_setpoint:.1f}°C\n")
        markdown_content.append(f"- **Normal heating setpoint**: {self.building_data.normal_heating_setpoint:.1f}°C\n")
        markdown_content.append(f"- **Normal cooling setpoint**: {self.building_data.normal_cooling_setpoint:.1f}°C\n")
        markdown_content.append(f"- **Heating period**: {self.building_data.heating_period[0]} to {self.building_data.heating_period[1]}\n")
        markdown_content.append(f"- **Cooling period**: {self.building_data.cooling_period[0]} to {self.building_data.cooling_period[1]}\n")
        markdown_content.append(f"- **Max heating power**: {self.building_data.max_heating_power/1000:.1f} kW\n")
        markdown_content.append(f"- **Max cooling power**: {self.building_data.max_cooling_power/1000:.1f} kW\n")
        markdown_content.append(f"- **Heat recovery efficiency**: {self.building_data.regular_ventilation_heat_recovery_efficiency:.1%}\n")
        markdown_content.append(f"- **Air renewal rate**: {self.building_data.regular_air_renewal_rate_vol_per_hour:.2f} vol/h\n")
        if self.building_data.free_cooling_setpoint_margin is not None:
            markdown_content.append(f"- **Free cooling setpoint margin**: {self.building_data.free_cooling_setpoint_margin:.1f}°C\n")
        markdown_content.append("\n")
        
        markdown_content.append("### Occupancy\n")
        markdown_content.append(f"- **Density**: {self.building_data.density_occupants_per_100m2:.1f} occupants per 100 m²\n")
        markdown_content.append(f"- **Body metabolism**: {self.building_data.body_metabolism:.0f} W per person (at 20°C)\n")
        markdown_content.append(f"- **Occupant consumption**: {self.building_data.occupant_consumption:.0f} W per person\n")
        markdown_content.append(f"- **CO₂ production**: {self.building_data.body_PCO2:.1f} L/h per person\n")
        if self.building_data.long_absence_period:
            markdown_content.append(f"- **Long absence period**: {self.building_data.long_absence_period[0]} to {self.building_data.long_absence_period[1]}\n")
        markdown_content.append("\n")
        
        markdown_content.append("### Simulation Settings\n")
        markdown_content.append(f"- **Initial temperature**: {self.building_data.initial_temperature:.1f}°C\n")
        if self.building_data.state_model_order_max is not None:
            markdown_content.append(f"- **State model order max**: {self.building_data.state_model_order_max}\n")
        markdown_content.append(f"- **Periodic depth**: {self.building_data.periodic_depth_seconds:.0f} seconds\n")
        markdown_content.append("\n")
        
        # Write to file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.writelines(markdown_content)
        
        print(f"\n✓ Markdown report generated: {report_path}")
        if heliodon_images:
            print(f"✓ Generated {len(heliodon_images)} heliodon plot(s)\n")
        else:
            print()
        
        # Generate PDF if possible
        self._generate_pdf_from_markdown(report_path, results_folder)

    def _generate_pdf_from_markdown(self, markdown_path: str, output_folder: str) -> None:
        """Generate a PDF from the markdown report if PDF conversion tools are available.
        
        Tries multiple methods in order:
        1. pypandoc (requires pandoc installed)
        2. markdown + weasyprint (HTML to PDF)
        3. markdown + xhtml2pdf (HTML to PDF)
        
        :param markdown_path: Path to the markdown file
        :param output_folder: Folder where PDF should be saved
        """
        import os
        import tempfile
        
        # Generate PDF filename
        pdf_filename = os.path.splitext(os.path.basename(markdown_path))[0] + '.pdf'
        pdf_path = os.path.join(output_folder, pdf_filename)
        
        # Method 1: Try pypandoc (requires pandoc binary)
        try:
            import pypandoc
            base_dir = os.path.dirname(os.path.abspath(markdown_path))
            
            # Read markdown content and replace Unicode characters with LaTeX-safe equivalents
            with open(markdown_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Replace Unicode characters that cause LaTeX issues
            # Use simple text replacements that work with standard LaTeX
            unicode_replacements = {
                '₂': '$_{2}$',  # Subscript 2 (CO₂ -> CO$_{2}$)
                '₀': '$_{0}$',  # Subscript 0
                '₁': '$_{1}$',  # Subscript 1
                '₃': '$_{3}$',  # Subscript 3
                '²': '$^{2}$',  # Superscript 2 (m² -> m$^{2}$)
                '³': '$^{3}$',  # Superscript 3
                '°': '$^{\\circ}$',  # Degree symbol (°C -> $^{\circ}$C)
                '·': '$\\cdot$',  # Middle dot (in math mode)
            }
            
            md_content_safe = md_content
            for unicode_char, latex_replacement in unicode_replacements.items():
                md_content_safe = md_content_safe.replace(unicode_char, latex_replacement)
            
            # Write to temporary markdown file with safe characters
            temp_md_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
            temp_md_file.write(md_content_safe)
            temp_md_file.close()
            temp_md_path = temp_md_file.name
            
            # Create a temporary LaTeX header file for better formatting
            header_file = tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8')
            header_file.write('\\usepackage{extsizes}\n')
            header_file.write('\\usepackage{graphicx}\n')
            header_file.write('\\usepackage{float}\n')
            header_file.write('\\usepackage{amsmath}\n')  # For math mode support
            header_file.write('\\renewcommand{\\normalsize}{\\fontsize{11pt}{13pt}\\selectfont}\n')
            header_file.write('\\renewcommand{\\small}{\\fontsize{10pt}{12pt}\\selectfont}\n')
            header_file.write('\\renewcommand{\\footnotesize}{\\fontsize{9pt}{11pt}\\selectfont}\n')
            header_file.close()
            
            extra_args = [
                '--resource-path', base_dir,
                '--variable', 'geometry=margin=0.75in',
                '--variable', 'linestretch=1.0',
                '--variable', 'documentclass=article',
                '--variable', 'fontsize=11pt',
                '--variable', 'toc-depth=2',
                '--include-in-header', header_file.name
            ]
            
            # Try XeLaTeX first (better Unicode support), fall back to pdflatex
            try:
                output = pypandoc.convert_file(
                    temp_md_path, 'pdf', outputfile=pdf_path,
                    extra_args=extra_args + ['--pdf-engine=xelatex']
                )
            except Exception:
                # Fall back to pdflatex
                output = pypandoc.convert_file(
                    temp_md_path, 'pdf', outputfile=pdf_path,
                    extra_args=extra_args + ['--pdf-engine=pdflatex']
                )
            
            assert output == "", "Error during conversion"
            
            # Clean up temporary files
            try:
                os.unlink(header_file.name)
                os.unlink(temp_md_path)
            except Exception:
                pass
            
            # Clean up temporary header file
            try:
                os.unlink(header_file.name)
            except Exception:
                pass
            
            print(f"✓ PDF report generated: {pdf_path}")
            return
            
        except ImportError:
            pass  # pypandoc not available
        except Exception as e:
            # pypandoc available but conversion failed
            print(f"⚠ PDF generation with pypandoc failed: {e}")
        
        # Method 2: Try markdown + weasyprint
        try:
            import markdown
            from weasyprint import HTML, CSS
            
            # Read markdown file
            with open(markdown_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert markdown to HTML
            html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
            
            # Add basic CSS styling
            css_content = """
            @page {
                size: A4;
                margin: 0.75in;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.4;
            }
            h1 { font-size: 18pt; margin-top: 0.5em; margin-bottom: 0.3em; }
            h2 { font-size: 16pt; margin-top: 0.5em; margin-bottom: 0.3em; }
            h3 { font-size: 14pt; margin-top: 0.4em; margin-bottom: 0.2em; }
            table { border-collapse: collapse; width: 100%; margin: 1em 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            img { max-width: 100%; height: auto; }
            code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
            pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
            """
            
            # Generate PDF
            HTML(string=html_content, base_url=os.path.dirname(markdown_path)).write_pdf(
                pdf_path,
                stylesheets=[CSS(string=css_content)]
            )
            
            print(f"✓ PDF report generated: {pdf_path}")
            return
            
        except ImportError:
            pass  # weasyprint not available
        except Exception as e:
            print(f"⚠ PDF generation with weasyprint failed: {e}")
        
        # Method 3: Try markdown + xhtml2pdf
        try:
            import markdown
            from xhtml2pdf import pisa
            
            # Read markdown file
            with open(markdown_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert markdown to HTML
            html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
            
            # Add basic CSS styling
            html_with_style = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{
                        size: A4;
                        margin: 0.75in;
                    }}
                    body {{
                        font-family: Arial, sans-serif;
                        font-size: 11pt;
                        line-height: 1.4;
                    }}
                    h1 {{ font-size: 18pt; margin-top: 0.5em; margin-bottom: 0.3em; }}
                    h2 {{ font-size: 16pt; margin-top: 0.5em; margin-bottom: 0.3em; }}
                    h3 {{ font-size: 14pt; margin-top: 0.4em; margin-bottom: 0.2em; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    img {{ max-width: 100%; height: auto; }}
                </style>
            </head>
            <body>
            {html_content}
            </body>
            </html>
            """
            
            # Generate PDF
            with open(pdf_path, 'wb') as pdf_file:
                pisa.CreatePDF(html_with_style, dest=pdf_file)
            
            print(f"✓ PDF report generated: {pdf_path}")
            return
            
        except ImportError:
            pass  # xhtml2pdf not available
        except Exception as e:
            print(f"⚠ PDF generation with xhtml2pdf failed: {e}")
        
        # If all methods failed
        print("⚠ PDF generation skipped: No PDF conversion tools available. Install 'pypandoc' (requires pandoc), 'weasyprint', or 'xhtml2pdf' to generate PDF reports.")

    def draw(self, window_size: tuple[int, int] = (1024, 768)) -> None:
        """Display the 3D building visualization in an interactive window.
        
        :param window_size: Window size in pixels (width, height)
        :type window_size: tuple[int, int]
        """
        plotter: Plotter = pv.Plotter(window_size=window_size)
        plotter.set_background("white")
        plotter.clear()
        if self.building_view is not None:
            self.building_view.draw(plotter)
        ground: PolyData = pv.Plane(center=(0, 0, 0), direction=(0, 0, 1), i_size=60, j_size=60)
        plotter.add_mesh(ground, color="#DDDDDD", opacity=1)
        if self.context.side_mask_views is not None:
            for side_mask_view in self.context.side_mask_views:
                side_mask_view.draw(plotter)
        plotter.add_axes(line_width=2)
        plotter.show_bounds(grid="front", location="outer", all_edges=True, xtitle="X (North -> South)", ytitle="Y (West -> East)", ztitle="Z (Up)")
        plotter.enable_eye_dome_lighting()
        plotter.camera_position = [(25, -35, 25), (0, 0, 5), (0, 0, 1)]
        plotter.show(auto_close=False)
    
    def save_building_plot(self, output_path: str, window_size: tuple[int, int] = (1600, 1200)) -> None:
        """Save the 3D building visualization to an image file.
        
        Automatically frames the entire building in view with a 3/4 perspective angle.
        
        :param output_path: Path where the image will be saved
        :type output_path: str
        :param window_size: Window size in pixels (width, height) for rendering
        :type window_size: tuple[int, int]
        """
        plotter: Plotter = pv.Plotter(off_screen=True, window_size=window_size)
        plotter.set_background("white")
        plotter.clear()
        if self.building_view is not None:
            self.building_view.draw(plotter)
        ground: PolyData = pv.Plane(center=(0, 0, 0), direction=(0, 0, 1), i_size=60, j_size=60)
        plotter.add_mesh(ground, color="#DDDDDD", opacity=1)
        if self.context.side_mask_views is not None:
            for side_mask_view in self.context.side_mask_views:
                side_mask_view.draw(plotter)
        plotter.add_axes(line_width=2)
        plotter.show_bounds(grid="front", location="outer", all_edges=True, xtitle="X (North -> South)", ytitle="Y (West -> East)", ztitle="Z (Up)")
        plotter.enable_eye_dome_lighting()
        
        # Reset camera to fit all actors (building, ground, masks, etc.)
        plotter.reset_camera()
        
        # Get the bounds of all actors to calculate building center and size
        bounds = plotter.renderer.ComputeVisiblePropBounds()
        if bounds[0] < bounds[1]:  # Check if we have valid bounds
            # Calculate building center
            center_x = (bounds[0] + bounds[1]) / 2
            center_y = (bounds[2] + bounds[3]) / 2
            center_z = (bounds[4] + bounds[5]) / 2
            
            # Calculate building dimensions
            size_x = bounds[1] - bounds[0]
            size_y = bounds[3] - bounds[2]
            size_z = bounds[5] - bounds[4]
            max_size = max(size_x, size_y, size_z)
            
            # Set camera position for a 3/4 perspective view
            # Position camera at a distance proportional to building size
            distance = max_size * 2.5
            camera_position = [
                center_x + distance * 0.7,  # Offset in X
                center_y - distance * 0.7,   # Offset in Y (negative for better angle)
                center_z + distance * 0.4     # Offset in Z (elevated view)
            ]
            focal_point = [center_x, center_y, center_z + size_z * 0.3]  # Focus slightly above ground
            view_up = [0, 0, 1]  # Z-axis is up
            
            plotter.camera_position = [camera_position, focal_point, view_up]
            
            # Zoom out slightly to ensure everything is visible with some margin
            plotter.camera.zoom(0.9)
        
        plotter.screenshot(output_path)
        plotter.close()

    def plot_heliodon(self, floor_number: int) -> plt.Axes:
        """Plot heliodon charts with horizon mask and collector-specific side masks for each floor.

        Generates one heliodon chart per floor showing the complete mask (horizon + distant + collector)
        for the South-facing window, demonstrating how solar access changes with floor elevation.

        :param floor_number: Floor number to plot (1-based index)
        :type floor_number: int (from 0 ground floor to n_floors - 1 to top floor)
        :param year: Year for heliodon plot (defaults to first year in weather data)
        :type collector_name: str (name of the collector to plot)
        :type collector_name: str (name of the collector to plot)
        :type year: int, optional
        """
        # Get year from weather data if not provided

        first_date: datetime = self.dp.weather_data.datetimes[0]
        year: int = first_date.year
        # Find the floor by matching floor_number attribute (not by index, since indices depend on whether basement exists)
        floor: Zone | None = None
        for f in self.zone_floors:
            if f.floor_number == floor_number:
                floor = f
                break
        if floor is None:
            raise ValueError(f'Floor number {floor_number} not found in building')
        window_masks_dict: dict[str, Mask] = floor.window_masks()
        if len(window_masks_dict) == 0:
            # Skip floors with no windows (e.g., basement)
            return None
        
        # Filter windows to only include those with surface > 0
        # Check if floor has window_surfaces attribute (RegularZone) and filter accordingly
        windows_with_surface: dict[str, Mask] = {}
        if hasattr(floor, 'window_surfaces') and hasattr(floor, 'windows_names'):
            for window_name, window_surface in zip(floor.windows_names, floor.window_surfaces):
                if window_name in window_masks_dict and window_surface > 0:
                    windows_with_surface[window_name] = window_masks_dict[window_name]
        else:
            # Fallback: use all windows if we can't check surface
            windows_with_surface = window_masks_dict
        
        if len(windows_with_surface) == 0:
            # Skip floors with no windows with surface > 0
            return None
        
        # Calculate grid size based on number of windows
        n_windows = len(windows_with_surface)
        if n_windows == 1:
            n_rows, n_cols = 1, 1
        elif n_windows == 2:
            n_rows, n_cols = 1, 2
        elif n_windows == 3:
            n_rows, n_cols = 2, 2
        else:  # 4 or more
            n_rows, n_cols = 2, 2
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 8))
        if n_windows == 1:
            axes = [axes]  # Make it a list for consistent iteration
        else:
            axes = axes.flatten()  # Flatten 2D array to 1D for easier indexing
        fig.suptitle(f'Heliodon for {floor.name}, Elevation: {floor.mid_elevation:.1f}m', fontsize=12)
        
        for i, (window_name, window_mask) in enumerate(windows_with_surface.items()):
            if i >= len(axes):
                break  # Safety check: don't exceed available subplots
            self.context.solar_model.plot_heliodon(name=f'Window {window_name}', year=year, observer_elevation_m=floor.mid_elevation, mask=window_mask, axes=axes[i])
            axes[i].set_title(f'Window {window_name}')
            axes[i].set_xlabel('Azimuth in degrees (0° = South, +90° =West)')
        
        # Hide unused subplots
        for i in range(len(windows_with_surface), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        return axes
