"""Solar radiation modeling and photovoltaic system analysis module for building energy analysis.

.. module:: batem.core.solar

This module provides comprehensive tools for solar radiation modeling, photovoltaic
system analysis, and solar energy calculations for building energy applications.
It includes solar position calculations, radiation modeling, masking systems,
collector modeling, and photovoltaic plant design and analysis.

Classes
-------

.. autosummary::
   :toctree: generated/

   SolarModel
   SolarSystem
   Collector
   PVplant
   MOUNT_TYPES
   CANONICAL_RADIATIONS
   COLLECTED_RADIATIONS
   EXTRA_DIRECTIONS

Classes Description
-------------------

**SolarModel**
    Main class for solar radiation calculations and modeling.

**SolarSystem**
    Solar collector system management and analysis.

**Collector**
    Solar collector modeling with orientation and efficiency calculations.

**PVplant**
    Photovoltaic plant design and performance analysis.

**Mask classes**
    Abstract and concrete mask implementations for solar obstruction modeling.

**MOUNT_TYPES, CANONICAL_RADIATIONS, COLLECTED_RADIATIONS, EXTRA_DIRECTIONS**
    Enumeration classes for photovoltaic and solar radiation types.

Key Features
------------

* Solar position calculations using pvlib with accurate astronomical algorithms
* Solar radiation modeling including direct, diffuse, and reflected components
* Cloud cover and atmospheric condition integration for realistic radiation estimates
* Horizon masking and obstruction modeling for building and terrain shadows
* Solar collector modeling with orientation, slope, and efficiency calculations
* Photovoltaic plant design with mounting system optimization
* Solar system performance analysis and energy yield calculations
* Integration with weather data and atmospheric conditions
* Support for various collector types and mounting configurations
* Visualization tools for solar analysis and system performance

The module is designed for building energy analysis, solar energy system design,
and comprehensive solar radiation modeling in research and practice.

.. note::
    This module requires pvlib for solar position calculations.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""
from __future__ import annotations
from scipy.optimize import minimize
import pandas as pd
try:
    from pvlib.location import Location
    import pvlib
    HAS_PVLIB = True
except ImportError:
    HAS_PVLIB = False
    # Fallback for when pvlib is not available

    class Location:
        def __init__(self, *args, **kwargs):
            pass

        def get_solarposition(self, *args, **kwargs):
            return pd.DataFrame()

        def get_clearsky(self, *args, **kwargs):
            return pd.DataFrame()

    class pvlib:
        @staticmethod
        def irradiance_dirint(*args, **kwargs):
            return pd.Series()
from abc import ABC, abstractmethod
from math import atan2, cos, sin, sqrt, floor, radians, degrees, pi, ceil
from pathlib import Path
import json
from batem.core.library import SLOPES, DIRECTIONS_SREF, Setup
import matplotlib.pyplot as plt
import datetime
import pyexcelerate
import warnings
from batem.core.weather import SiteWeatherData
from batem.core import timemg
import numpy as np
import enum
import prettytable
from batem.core.utils import day_averager, mkdir_if_not_exist
from batem.core.utils import FilePathBuilder
# import plotly.io as pio

# logging.basicConfig(level=logging.ERROR)
# # Configure Plotly to avoid Tkinter crashes on macOS
# # pio.renderers.default = "plotly_mimetype+notebook"


class MOUNT_TYPES(enum.Enum):
    PLAN = 0
    FLAT = 1
    BACK2BACK = 2


class CANONICAL_RADIATIONS(enum.Enum):
    DNI = 1
    DHI = 2
    RHI = 3
    TSI = 4
    GHI = 5


class COLLECTED_RADIATIONS(enum.Enum):
    TILT_TOTAL = 1
    TILT_DIRECT = 2
    TILT_DIFFUSE = 3
    TILT_REFLECTED = 4
    NORMAL = 5


class EXTRA_DIRECTIONS(enum.Enum):
    PERSO = 10
    BEST = 11


_RESULTS_FOLDER = Setup.data('folders', 'results')
plot_size: tuple[int, int] = (8, 8)


def _horizon_cache_path() -> Path:
    """Resolve the cache file path used to store PVGIS horizon lookups."""
    data_folder = Path(FilePathBuilder().get_work_folder()).expanduser()
    data_folder.mkdir(parents=True, exist_ok=True)
    return data_folder / 'pvgis_horizons.json'


def _load_horizon_from_cache(latitude_deg: float, longitude_deg: float) -> pd.Series | None:
    """Load horizon data from the local cache if present."""
    cache_path = _horizon_cache_path()
    if not cache_path.exists():
        return None
    cache_key = f'{latitude_deg:.6f},{longitude_deg:.6f}'
    try:
        with cache_path.open('r', encoding='utf-8') as cache_file:
            cache_data = json.load(cache_file)
        entry = cache_data.get(cache_key)
        if entry is None:
            return None
        azimuths = entry.get('azimuths')
        altitudes = entry.get('altitudes')
        if azimuths is None or altitudes is None:
            return None
        return pd.Series(
            data=[float(value) for value in altitudes],
            index=pd.Index([float(value) for value in azimuths], dtype=float),
            dtype=float,
        )
    except Exception as exc:  # noqa: BLE001 - cache issues should not abort execution
        warnings.warn(f'Failed to read PVGIS horizon cache ({exc}); ignoring cache.', RuntimeWarning)
        return None


def _store_horizon_in_cache(latitude_deg: float, longitude_deg: float, horizon_series: pd.Series) -> None:
    """Persist horizon data to the local cache."""
    cache_path = _horizon_cache_path()
    cache_key = f'{latitude_deg:.6f},{longitude_deg:.6f}'
    try:
        if cache_path.exists():
            with cache_path.open('r', encoding='utf-8') as cache_file:
                cache_data = json.load(cache_file)
        else:
            cache_data = {}
        cache_data[cache_key] = {
            'azimuths': [float(value) for value in horizon_series.index.tolist()],
            'altitudes': [float(value) for value in horizon_series.tolist()],
        }
        tmp_path = cache_path.with_suffix(cache_path.suffix + '.tmp')
        with tmp_path.open('w', encoding='utf-8') as tmp_file:
            json.dump(cache_data, tmp_file)
        tmp_path.replace(cache_path)
    except Exception as exc:  # noqa: BLE001 - cache write failures must not stop execution
        warnings.warn(f'Failed to write PVGIS horizon cache ({exc}).', RuntimeWarning)


def _encode4file(string: str, number: float = None):  # type: ignore
    if number is not None:
        string += '='+(str(number).replace('.', ','))
    return string.encode("iso-8859-1")


class SolarModel():
    """Main class for solar radiation calculations and modeling.

    This class provides comprehensive solar radiation modeling capabilities using
    solar position calculations and weather data to compute solar radiations on
    directed surfaces. It integrates atmospheric conditions, cloud cover, and
    terrain effects for accurate solar energy analysis.
    """

    def __init__(self, site_weather_data: SiteWeatherData, parameters: SolarModel.Parameters = None, distant_masks: list[Mask] = list()) -> None:
        """Initialize a new SolarModel instance and compute all the data that are not specific to a collector.
            :param site_weather_data: contains site data like location, altitude, albedo, etc... It is generated by an Weather object, that contains site data like location, altitude,... (see openweather.SiteWeatherData)
            :type site_weather_data: buildingenergy.weather.SiteWeatherData
            :param solar_mask: Optional mask for additional obstructions. If None, only horizon mask is used.
            :type solar_mask: Mask
            :param parameters: Optional Parameters object with model coefficients. If None, default parameters are used.
        """
        # self._use_measurements = False,
        self.site_weather_data: SiteWeatherData = site_weather_data
        if parameters is None:
            self.parameters = SolarModel.Parameters()
        else:
            self.parameters: SolarModel.Parameters = parameters
        self._global_masks: list[SideMask] = distant_masks
        self.datetimes: list[datetime.datetime] = self.site_weather_data.datetimes
        self.pd_datetimes = pd.DatetimeIndex(self.site_weather_data.datetimes, tz=self.site_weather_data.timezone_str)

        pd_cloud_cover = pd.Series(self.site_weather_data.get('cloudiness'), index=self.pd_datetimes)
        pd_air_temperature_C = pd.Series(self.site_weather_data.get('temperature'), index=self.pd_datetimes)
        pd_dew_point_temperature = pd.Series(self.site_weather_data.get('dew_point_temperature'), index=self.pd_datetimes)  # °C
        # Pressure as Series; ensure units are Pascals (Pa)
        pd_pressure_raw = pd.Series(self.site_weather_data.get('pressure'), index=self.pd_datetimes)
        # If pressure looks like hPa (typical ~1013), convert to Pa
        if pd_pressure_raw.dropna().median() < 2000:
            pd_pressure_Pa: pd.Series = pd_pressure_raw * 100.0
        else:
            pd_pressure_Pa = pd_pressure_raw

        self.site_location = Location(latitude=self.site_weather_data.site_latitude_north_deg, longitude=self.site_weather_data.site_longitude_east_deg, tz=self.site_weather_data.timezone_str, altitude=self.site_weather_data.site_elevation_m)

        self.pd_solar_positions: pd.DataFrame = self.site_location.get_solarposition(self.pd_datetimes, pressure=pd_pressure_Pa, temperature=pd_air_temperature_C)
        self.pd_solar_positions['altitude'] = 90 - self.pd_solar_positions['zenith']
        self.pd_solar_positions.loc[self.pd_solar_positions['altitude'] < 0, 'altitude'] = np.nan

        clearsky_ghi_dni_dhi = self.site_location.get_clearsky(self.pd_datetimes, model='simplified_solis', aod700=self.site_weather_data.pollution, precipitable_water=1.5, pressure=pd_pressure_Pa)

        # Scale GHI with a linear cloud factor (Larson-style offset)
        offset = 0.35  # GHI at 100% cloud cover is 35% of clear-sky
        pd_scale = offset + (1 - offset) * (1 - pd_cloud_cover / 100.0)

        # Cloud-adjusted GHI (not yet horizon-masked)
        self.ghi_cloud_nomask = clearsky_ghi_dni_dhi['ghi'] * pd_scale
        # self._ghi_cloud_nomask.replace([np.inf, -np.inf], 0, inplace=True)

        # Use DIRINT (more robust than DISC) to derive DNI from GHI
        dni_cloud_nomask = pvlib.irradiance.dirint(
            ghi=self.ghi_cloud_nomask, solar_zenith=self.pd_solar_positions['zenith'], times=self.pd_datetimes, pressure=pd_pressure_Pa, temp_dew=pd_dew_point_temperature)
        self._dni_cloud_nomask = dni_cloud_nomask.clip(lower=0).fillna(0)

        self._cos_zenith = np.cos(np.radians(self.pd_solar_positions['zenith']))
        # Diffuse from GHI and DNI (non-negative)
        self.dhi_cloud_nomask = (self.ghi_cloud_nomask - self._dni_cloud_nomask * self._cos_zenith).clip(lower=0).fillna(0)

        # --- Apply far-field horizon mask to the beam only ---
        cached_horizon = _load_horizon_from_cache(
            self.site_weather_data.site_latitude_north_deg,
            self.site_weather_data.site_longitude_east_deg,
        )
        if cached_horizon is not None:
            self.pd_horizon_mask_deg = cached_horizon
        else:
            try:
                horizon_series, _ = pvlib.iotools.get_pvgis_horizon(
                    self.site_weather_data.site_latitude_north_deg,
                    self.site_weather_data.site_longitude_east_deg,
                )
                self.pd_horizon_mask_deg = horizon_series
                _store_horizon_in_cache(
                    self.site_weather_data.site_latitude_north_deg,
                    self.site_weather_data.site_longitude_east_deg,
                    self.pd_horizon_mask_deg,
                )
            except Exception as exc:  # noqa: BLE001 - any network/IO error should trigger fallback
                warnings.warn(
                    f'PVGIS horizon lookup failed ({exc}); falling back to flat horizon (0°). '
                    'Set the PVGIS_HORIZON_CACHE environment variable or provide distant masks to avoid this request.',
                    RuntimeWarning,
                )
                horizon_azimuths = np.arange(0, 361, 1, dtype=float)
                self.pd_horizon_mask_deg = pd.Series(0.0, index=horizon_azimuths)

        self.pd_azimuth_deg = self.pd_solar_positions['azimuth']
        self.pd_altitude_deg = 90 - self.pd_solar_positions['zenith']
        self.pd_zenith_deg = self.pd_solar_positions['zenith']
        self.pd_dni = self._dni_cloud_nomask
        self.pd_ghi = self.ghi_cloud_nomask
        self.pd_dhi = self.dhi_cloud_nomask

    @property
    def cos_zenith(self) -> np.array:
        return self._cos_zenith

    @property
    def horizon_azimuths_deg(self) -> np.array:
        return self.pd_horizon_mask_deg.index.values

    @property
    def horizon_altitudes_deg(self) -> np.array:
        return self.pd_horizon_mask_deg.values

    @property
    def azimuths_deg(self) -> np.array:
        return self.pd_azimuth_deg.values - 180

    @property
    def altitudes_deg(self) -> np.array:
        """Return solar altitudes in degrees with negative values set to 0.

        Negative altitude values represent when the sun is below the horizon.
        This property transforms those negative values to 0 for practical calculations.

        :return: Array of solar altitudes in degrees (negative values set to 0)
        :rtype: np.array
        """
        altitudes = self.pd_altitude_deg.values
        return np.where(altitudes < 0, 0, altitudes)

    @property
    def zeniths_deg(self) -> np.array:
        return self.pd_zenith_deg.values

    @property
    def dni(self) -> np.array:
        return self.pd_dni.values

    @property
    def ghi(self) -> np.array:
        return self.pd_ghi.values

    @property
    def dhi(self) -> np.array:
        return self.pd_dhi.values

    @property
    def temperatures_C(self) -> list[float]:
        return self.site_weather_data.get('temperature')

    def global_masks(self) -> list[Mask]:
        return self._global_masks

    @property
    def rhi(self) -> np.array:
        """Reflected Horizontal Irradiance (RHI) based on albedo.

        RHI represents the solar radiation reflected from the ground surface
        back to the atmosphere. It is calculated as:
        RHI = albedo × GHI

        :return: Reflected horizontal irradiance in W/m²
        :rtype: np.array
        """
        return self.site_weather_data.albedo * self.pd_ghi.values

    def apply_mask(self, azimuths_deg: np.ndarray, altitudes_deg: np.ndarray, observer_elevation_m: float, mask: Mask = None) -> tuple[np.ndarray, Mask]:
        """Apply horizon mask and optional additional mask to solar positions.

        :param azimuths_deg: Horizon azimuth angles in degrees
        :param altitudes_deg: Horizon altitude angles in degrees
        :param observer_elevation_m: Observer elevation in meters
        :param mask: Optional additional mask to combine with horizon mask
        :return: Tuple of (blocked_mask_array, combined_mask_object)
        """
        # Create combined mask
        combined_mask: StackedMask = StackedMask(HorizonMask(azimuths_deg, altitudes_deg))
        for global_mask in self._global_masks:
            combined_mask.merge(global_mask)
        if mask is not None:
            combined_mask.merge(mask)

        # Convert solar positions from pvlib convention (North=0°) to BATEM convention (South=0°)
        solar_positions_batem: pd.DataFrame = self.pd_solar_positions.copy()
        solar_positions_batem['azimuth'] = self.pd_solar_positions['azimuth'] - 180

        # Use vectorized mask application with converted DataFrame
        mask_blocked = ~combined_mask.passthrough(solar_positions_batem, observer_elevation_m)
        return mask_blocked, combined_mask

    def _corrected_slope_irradiance(self, exposure_deg: float, slope_deg: float, dni_masked: pd.Series, dhi_masked: pd.Series, ghi_masked: pd.Series, scale_factor: float = 1) -> dict[str, pd.Series]:
        """Calculate slope-dependent irradiance with proper handling of ground-facing and sky-facing surfaces.

        This method implements the correct physics for slope-dependent irradiance:
        - slope = 0° (facing ground): receives only RHI (reflected horizontal irradiance)
        - slope = 180° (facing sky): receives only DHI (diffuse horizontal irradiance)

        :param exposure_deg: Surface azimuth angle in degrees
        :type exposure_deg: float
        :param slope_deg: Surface slope angle in degrees (0°=ground, 180°=sky)
        :type slope_deg: float
        :param dni_masked: Direct normal irradiance (masked)
        :type dni_masked: pd.Series
        :param dhi_masked: Diffuse horizontal irradiance (masked)
        :type dhi_masked: pd.Series
        :param ghi_masked: Global horizontal irradiance (masked)
        :type ghi_masked: pd.Series
        :param scale_factor: Scale factor for irradiances
        :type scale_factor: float
        :return: Dictionary with irradiance components
        :rtype: dict[str, pd.Series]
        """
        from math import cos, radians

        # Convert slope to radians for calculations
        slope_rad: float = radians(slope_deg)

        # Calculate view factors for diffuse and reflected components
        # These are the key equations that ensure proper behavior:
        # - For slope = 0° (facing ground): cos(0°) = 1 → diffuse_factor = 0, reflected_factor = 1
        # - For slope = 180° (facing sky): cos(180°) = -1 → diffuse_factor = 1, reflected_factor = 0
        diffuse_factor = (1 - cos(slope_rad)) / 2
        reflected_factor = (1 + cos(slope_rad)) / 2

        # Calculate RHI (Reflected Horizontal Irradiance) from GHI and albedo
        rhi = ghi_masked * self.site_weather_data.albedo

        # Calculate direct irradiance using pvlib (this handles the geometric calculations correctly)
        poa_direct = pvlib.irradiance.get_total_irradiance(
            surface_azimuth=exposure_deg-180,
            surface_tilt=180-slope_deg,
            solar_zenith=self.pd_solar_positions['apparent_zenith'],
            solar_azimuth=self.pd_solar_positions['azimuth'],
            dni=dni_masked * scale_factor,
            ghi=ghi_masked * scale_factor,
            dhi=dhi_masked * scale_factor,
            albedo=0  # We handle albedo separately for reflected component
        )['poa_direct']

        # Calculate diffuse and reflected components with proper slope dependence
        poa_diffuse = dhi_masked * diffuse_factor * scale_factor
        poa_ground_diffuse = rhi * reflected_factor * scale_factor

        # Total irradiance is the sum of all components
        poa_global = poa_direct + poa_diffuse + poa_ground_diffuse

        return {
            'poa_global': poa_global,
            'poa_direct': poa_direct,
            'poa_diffuse': poa_diffuse,
            'poa_ground_diffuse': poa_ground_diffuse
        }

    @property
    def horizon_mask(self) -> HorizonMask:
        return HorizonMask(self.horizon_azimuths_deg, self.horizon_altitudes_deg, south_reference=False)

    def irradiances_W(self, exposure_deg: float, slope_deg: float, mask: Mask = None, scale_factor: float = 1, details: bool = False, observer_elevation_m: float = 0.0) -> float:
        """Compute the irradiances on a 1m2 flat surface.
        :param exposure_deg: clockwise angle in degrees between the south and the normal of collecting surface. O means south oriented, 90 means West, -90 East and 180 north oriented
        :type exposure_deg: float
        :param slope_deg: angle in degrees from horizontal ground plane. 0 means horizontal facing downward (toward ground), 90 means vertical, 180 means horizontal facing upward (toward sky)
        :type slope_deg: float
        :param mask: Optional mask to apply in addition to horizon mask
        :type mask: Mask
        :param scale_factor: Scale factor for irradiances
        :type scale_factor: float
        :param details: Whether to return detailed breakdown
        :type details: bool
        :return: irradiances
        :rtype: float
        """
        mask_blocked, combined_mask = self.apply_mask(self.horizon_azimuths_deg, self.horizon_altitudes_deg, observer_elevation_m)
        mask_blocked_series = pd.Series(mask_blocked, index=self.pd_datetimes)
        dni_masked = self.pd_dni.where(~mask_blocked_series, 0.0)
        dhi_masked = self.dhi

        # Recompute GHI with the additional masking
        ghi_masked = dni_masked * self.cos_zenith + dhi_masked

        # Use corrected slope-dependent irradiance calculation
        poa_adj = self._corrected_slope_irradiance(
            exposure_deg=exposure_deg,
            slope_deg=slope_deg,
            dni_masked=dni_masked,
            dhi_masked=dhi_masked,
            ghi_masked=ghi_masked,
            scale_factor=scale_factor
        )

        if details:
            # Handle both pandas Series and numpy arrays
            def to_list(x):
                if hasattr(x, 'to_list'):
                    return x.to_list()
                elif hasattr(x, 'tolist'):
                    return x.tolist()
                else:
                    return list(x)
            return {COLLECTED_RADIATIONS.TILT_TOTAL: to_list(poa_adj['poa_global']),
                    COLLECTED_RADIATIONS.TILT_DIRECT: to_list(poa_adj['poa_direct']),
                    COLLECTED_RADIATIONS.TILT_DIFFUSE: to_list(poa_adj['poa_diffuse']),
                    COLLECTED_RADIATIONS.TILT_REFLECTED: to_list(poa_adj['poa_ground_diffuse']),
                    'mask': combined_mask}
        else:
            result = poa_adj['poa_global']
            if hasattr(result, 'to_list'):
                return result.to_list()
            elif hasattr(result, 'tolist'):
                return result.tolist()
            else:
                return list(result)

    def best_direction(self, initial_slope_deg: float = 180, initial_exposure_deg: float = 0, mask: Mask = None, details: bool = False) -> dict[str, float]:
        neighborhood: list[tuple[float, float]] = [(-1, 0), (-1, 1), (-1, -1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        taboo = list()
        exposure_slope_in_deg_candidate: tuple[float, float] = (initial_exposure_deg, initial_slope_deg)
        best_exposure_slope_in_deg = tuple(exposure_slope_in_deg_candidate)
        best_total_energy_in_Wh = sum(self.irradiances_W(exposure_slope_in_deg_candidate[0], exposure_slope_in_deg_candidate[1], mask=mask, scale_factor=1))
        initial_production_Wh: float = best_total_energy_in_Wh
        taboo.append(exposure_slope_in_deg_candidate)

        improvement = True
        while improvement:
            improvement = False
            for neighbor in neighborhood:
                exposure_slope_in_deg_candidate = (best_exposure_slope_in_deg[0] + neighbor[0], best_exposure_slope_in_deg[1] + neighbor[1])
                exposure_in_deg: float = exposure_slope_in_deg_candidate[0]
                slope_in_deg: float = exposure_slope_in_deg_candidate[1]
                if -180 <= exposure_in_deg <= 180 and 0 <= slope_in_deg <= 180 and exposure_slope_in_deg_candidate not in taboo:
                    taboo.append(exposure_slope_in_deg_candidate)
                    solar_energy_in_Wh: list[float] = sum(self.irradiances_W(exposure_deg=exposure_in_deg, slope_deg=slope_in_deg, mask=mask, scale_factor=1))
                    if solar_energy_in_Wh > best_total_energy_in_Wh:
                        improvement = True
                        best_exposure_slope_in_deg: tuple[float, float] = exposure_slope_in_deg_candidate
                        best_total_energy_in_Wh: float = solar_energy_in_Wh
        if details:
            return best_exposure_slope_in_deg[0], best_exposure_slope_in_deg[1], {'best_energy_kWh': best_total_energy_in_Wh / 1000, 'initial_slope_deg': initial_slope_deg, 'initial_slope_deg': initial_slope_deg, 'initial_production_kWh': initial_production_Wh / 1000, 'complementary_slope_deg': 180 - best_exposure_slope_in_deg[1]}
        else:
            return best_exposure_slope_in_deg[0], best_exposure_slope_in_deg[1]

    def cardinal_irradiances_W(self, mask: Mask = None) -> dict[SLOPES | DIRECTIONS_SREF, list[float]]:
        _cardinal_irradiances_W = dict()
        _cardinal_irradiances_W[SLOPES.HORIZONTAL_DOWN] = self.irradiances_W(exposure_deg=DIRECTIONS_SREF.SOUTH.value, slope_deg=SLOPES.HORIZONTAL_DOWN.value, mask=mask)
        _cardinal_irradiances_W[SLOPES.HORIZONTAL_UP] = self.irradiances_W(exposure_deg=DIRECTIONS_SREF.SOUTH.value, slope_deg=SLOPES.HORIZONTAL_UP.value, mask=mask)
        _cardinal_irradiances_W[DIRECTIONS_SREF.SOUTH] = self.irradiances_W(exposure_deg=DIRECTIONS_SREF.SOUTH.value, slope_deg=SLOPES.VERTICAL.value, mask=mask)
        _cardinal_irradiances_W[DIRECTIONS_SREF.WEST] = self.irradiances_W(exposure_deg=DIRECTIONS_SREF.WEST.value, slope_deg=SLOPES.VERTICAL.value, mask=mask)
        _cardinal_irradiances_W[DIRECTIONS_SREF.EAST] = self.irradiances_W(exposure_deg=DIRECTIONS_SREF.EAST.value, slope_deg=SLOPES.VERTICAL.value, mask=mask)
        _cardinal_irradiances_W[DIRECTIONS_SREF.NORTH] = self.irradiances_W(exposure_deg=DIRECTIONS_SREF.NORTH.value, slope_deg=SLOPES.VERTICAL.value, mask=mask)
        return _cardinal_irradiances_W

    def try_export(self) -> None:
        """Export a TRY weather files for IZUBA Pleiades software. It generates 2 files per full year:
        - site_location + '_' + 'year' + '.INI'
        - site_location + '_' + 'year' + '.TRY'
        The station ID will correspond to the 3 first characters of the site_location in upper case
        """
        site_location: str = self.site_weather_data.location
        location_id: str = site_location[0:3].upper()
        temperatures: list[float] = self.site_weather_data.get('temperature')
        TempSol: float = round(sum(temperatures) / len(temperatures))
        temperature_tenth: list[float] = [10 * t for t in temperatures]
        humidities: list[float] = self.site_weather_data.get('humidity')
        # Try to get wind speed in m/s first, then km/h, convert to m/s if needed
        if 'wind_speed_m_s' in self.site_weather_data.variable_names:
            wind_speeds: list[float] = self.site_weather_data.get('wind_speed_m_s')
        elif 'wind_speed_km_h' in self.site_weather_data.variable_names:
            wind_speeds: list[float] = [w / 3.6 for w in self.site_weather_data.get('wind_speed_km_h')]
        else:
            raise ValueError('Wind speed data not available. Expected "wind_speed_m_s" or "wind_speed_km_h"')
        wind_directions_in_deg: list[float] = self.site_weather_data.get('wind_direction_in_deg')
        global_horizontal_irradiances: list[float] = self.ghi
        direct_normal_irradiances: list[float] = self.dni
        diffuse_horizontal_irradiances: list[float] = self.ghi
        ini_file = None
        try_file = None
        for i, dt in enumerate(self.datetimes):
            year, month, day, hour = dt.year, dt.month, dt.day, dt.hour+1
            if month == 1 and day == 1 and hour == 1:
                if ini_file is not None:
                    ini_file.close()
                    try_file.close()
                file_name: str = _RESULTS_FOLDER + site_location + '_' + str(year)
                new_line = '\r\n'
                ini_file = open(file_name + '.ini', "w")
                ini_file.write('[Station]' + new_line)
                ini_file.write('Nom=' + site_location + new_line)
                elevation_m = self.site_weather_data.site_elevation_m if self.site_weather_data.site_elevation_m is not None else self.site_weather_data.elevation
                latitude_deg = self.site_weather_data.site_latitude_north_deg
                longitude_deg = self.site_weather_data.site_longitude_east_deg
                ini_file.write('Altitude=%i%s' % (int(elevation_m), new_line))
                ini_file.write('Lattitude=%s%s' % (en2fr(latitude_deg), new_line))
                ini_file.write('Longitude=%s%s' % (en2fr(longitude_deg), new_line))
                ini_file.write('NomFichier=' + site_location + '_' + str(year) + '.try' + new_line)
                ini_file.write('TempSol=%i%s' % (round(TempSol), new_line))
                ini_file.write('TypeFichier=xx' + new_line)
                ini_file.write('Heure solaire=0' + new_line)
                # Meridian calculation: convert latitude degrees to radians, then to hours (12 hours = pi radians)
                ini_file.write('Meridien=%i%s' % (int(floor(latitude_deg * pi / 180 / pi * 12)), new_line))
                ini_file.write('LectureSeule=1' + new_line)
                ini_file.write('Categorie=OpenMeteo' + new_line)
                ini_file.close()
                try_file = open(file_name + '.try', "bw")
            irradiance_coefficient = 3600 / 10000
            if try_file is not None:
                row: str = f"{location_id}{round(temperature_tenth[i]):4d}{round(global_horizontal_irradiances[i]*irradiance_coefficient):4d}{round(diffuse_horizontal_irradiances[i]*irradiance_coefficient):4d}{round(direct_normal_irradiances[i]*irradiance_coefficient):4d}   E{round(humidities[i]):3d}{round(wind_speeds[i]):3d}{month:2d}{day:2d}{hour:2d}{round(wind_directions_in_deg[i]):4d} 130     E{self.altitudes_deg[i]:6.2f}{self.azimuths_deg[i]+180:7.2f}\r\n"
                row = row.replace('.', ',')
                try_file.write(_encode4file(row))
        try:
            try_file.close()
        except:  # noqa
            pass

    def plot_heliodon(self, name: str = '', year: int = 2020, observer_elevation_m: float = 0.0, mask: Mask = None, axes: plt.Axes = None) -> plt.Axes:
        """Plot heliodon at current location.

        :param year: year to be displayed in figure
        :type year: int
        :param name: file_name to be displayed in figure, default to ''
        :type name: str
        :param mask: Optional mask to combine with horizon mask
        :type mask: Mask
        """
        name_months_str: list[str] = ['Jan 21', 'Feb 21', 'Mar 21', 'Apr 21', 'May 21', 'Jun 21', 'Jul 21', 'Aug 21', 'Sep 21', 'Oct 21', 'Nov 21', 'Dec 21']
        plt.rcParams['font.size'] = 12
        if axes is None:
            _, axes = plt.subplots(figsize=plot_size)

        # Plot monthly sun paths (21st of each month)
        for month_index in range(12):
            stringdate = f'21/{month_index + 1}/{year}'
            month21_datetimes = [timemg.stringdate_to_datetime(stringdate + ' %i:%i:0' % (hour_in_day, minutes)) for hour_in_day in range(0, 24, 1) for minutes in range(0, 60, 1)]
            month21_solar_positions = self.site_location.get_solarposition(pd.DatetimeIndex(month21_datetimes, tz=self.site_weather_data.timezone_str))
            month21_azimuths = month21_solar_positions['azimuth'].values - 180
            month21_altitudes = (90 - month21_solar_positions['zenith']).values
            # Only plot when sun is above horizon
            positive_altitudes_mask = month21_altitudes > 0
            if np.any(positive_altitudes_mask):
                axes.plot(month21_azimuths[positive_altitudes_mask], month21_altitudes[positive_altitudes_mask])
                # Add month annotation at a random position
                positive_altitudes_indices = np.where(positive_altitudes_mask)[0]
                distance_between_points = len(positive_altitudes_indices)//12
                i_position = min(distance_between_points * (1 + month_index), len(positive_altitudes_indices) - 1)
                # i_position = positive_altitudes_indices[len(positive_altitudes_indices)//6]
                axes.annotate(name_months_str[month_index], (month21_azimuths[positive_altitudes_indices][i_position], month21_altitudes[positive_altitudes_indices][i_position]), color='red', fontweight='bold')

        axes.legend(name_months_str)
        axes.set_title('heliodon %s (21th of each month)' % name)

        # Plot hourly sun paths throughout the year
        initial_datetime = timemg.stringdate_to_datetime(f'1/1/{year} 0:00:00')
        for hour_in_day in range(0, 24):
            yearly_datetimes = [initial_datetime + datetime.timedelta(days=day_in_year, hours=hour_in_day, minutes=0) for day_in_year in range(0, 365, 1)]
            yearly_solar_positions = self.site_location.get_solarposition(pd.DatetimeIndex(yearly_datetimes, tz=self.site_weather_data.timezone_str))
            yearly_azimuths = yearly_solar_positions['azimuth'].values - 180
            yearly_altitudes = (90 - yearly_solar_positions['zenith']).values
            # Only plot when sun is above horizon
            positive_altitudes_mask = yearly_altitudes > 0
            if np.any(positive_altitudes_mask):
                axes.plot(yearly_azimuths[positive_altitudes_mask], yearly_altitudes[positive_altitudes_mask], '.c')
                # Add hour annotation at midpoint
                positive_altitudes_indices = np.where(positive_altitudes_mask)[0]
                if len(positive_altitudes_indices) > 0:
                    i = positive_altitudes_indices[len(positive_altitudes_indices) // 2]
                    axes.annotate(str(hour_in_day)+'h', (yearly_azimuths[i], yearly_altitudes[i]))

        # Plot the mask using apply_mask
        _, combined_mask = self.apply_mask(self.horizon_azimuths_deg, self.horizon_altitudes_deg, observer_elevation_m, mask)
        combined_mask.plot(axis=axes, observer_elevation_m=observer_elevation_m)
        # mask.plot(axis=axes)

        y_pos_compass: float = 5.0
        labels = {'E': -90, 'S': 0, 'W': 90, 'N': 180}
        # Place labels near the bottom
        for label, az in labels.items():
            axes.text(az, y_pos_compass, label, ha='center', va='center', fontsize=12, fontweight='bold')
        # Draw a baseline and ticks
        axes.hlines(y=y_pos_compass - 1.0, xmin=-180, xmax=180, colors='k', linestyles='-', linewidth=0.5)
        for az in (-180, -90, 0, 90, 180):
            axes.vlines(x=az, ymin=y_pos_compass - 2.0, ymax=y_pos_compass, colors='k', linestyles='-', linewidth=0.5)

        # Set explicit axis bounds: azimuth -180° to 180°, altitude 0° to 90°
        axes.set_xlim(-180, 180)
        axes.set_ylim(0, 90)
        axes.grid()
        return axes

    def plot_angles(self, with_matplotlib: bool = True, title: str = ''):
        """Plot solar angles for the dates corresponding to dates in site_weather_data."""
        if with_matplotlib:
            plt.figure()
            plt.plot(self.datetimes, self.altitudes_deg, self.datetimes, self.azimuths_deg)
            plt.legend(('altitude in deg', 'azimuth in deg'))
            plt.title(title)
            plt.axis('tight')
            plt.grid()
        else:
            import plotly.graph_objs as go
            from plotly.subplots import make_subplots

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
            fig.add_trace(go.Scatter(x=self.datetimes, y=self.altitudes_deg, name='sun altitude in °', line_shape='hv'), row=1, col=1)
            # azimuths_deg = [az if az >= -180 else 360+az for az in self.azimuths_deg]
            fig.add_trace(go.Scatter(x=self.datetimes, y=self.azimuths_deg, name='sun azimuth in °', line_shape='hv'), row=2, col=1)
            fig.update_layout(title=title)
            # Use non-interactive backend to avoid Tkinter crashes on macOS
            try:
                # Try to show in browser if possible
                fig.show()
            except Exception:
                # Fallback: save to HTML file instead
                fig.write_html("solar_angles.html")
                print("Plot saved to solar_angles.html")

    def plot_albedo_variation(self, with_matplotlib: bool = True) -> None:
        """Plot albedo variation over time to visualize seasonal and weather effects."""

        import plotly.graph_objs as go
        from plotly.subplots import make_subplots

        if hasattr(self, 'albedo_timeseries'):
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=('Albedo Variation Over Time', 'Temperature vs Albedo'))

            # Plot albedo timeseries
            fig.add_trace(go.Scatter(x=self.albedo_timeseries.index, y=self.albedo_timeseries.values,  name='Albedo', line=dict(color='brown', width=2)), row=1, col=1)

            # Plot temperature for context
            temperatures = self.site_weather_data.get('temperature')
            fig.add_trace(go.Scatter(x=self.datetimes, y=temperatures, name='Temperature (°C)', line=dict(color='blue', width=1)), row=2, col=1)

            fig.update_layout(title="Albedo Analysis: Seasonal and Weather-Dependent Variations", height=600, showlegend=True)
            fig.update_xaxes(title_text="Date", row=2, col=1)
            fig.update_yaxes(title_text="Albedo", row=1, col=1)
            fig.update_yaxes(title_text="Temperature (°C)", row=2, col=1)

            try:
                fig.show()
            except Exception:
                fig.write_html("albedo_analysis.html")
                print("Albedo analysis plot saved to albedo_analysis.html")
        else:
            print("No albedo timeseries available. Run the enhanced CanonicalSolarModel first.")

    def plot_cardinal_irradiances(self, mask: Mask = None, with_matplotlib: bool = True, my_exp_slope_angles: tuple[float, float] = None) -> None:
        """Plot total solar irradiation on all cardinal direction and an horizontal one, for the dates corresponding to dates in site_weather_data."""

        import plotly.graph_objs as go
        from plotly.subplots import make_subplots

        direction_irradiances_W = self.cardinal_irradiances_W()
        best_exposure, best_slope = self.best_direction(mask=mask)
        print(f'Best exposure: {best_exposure}°, best slope: {best_slope}°')
        direction_irradiances_W[EXTRA_DIRECTIONS.BEST] = self.irradiances_W(best_exposure, best_slope, mask=mask, scale_factor=1)
        if my_exp_slope_angles is not None:
            print(f'Best exposure: {my_exp_slope_angles[0]}°, best slope: {my_exp_slope_angles[1]}°')
            direction_irradiances_W[EXTRA_DIRECTIONS.PERSO] = self.irradiances_W(exposure_deg=my_exp_slope_angles[0], slope_deg=my_exp_slope_angles[1], mask=mask, scale_factor=1)

        for direction_name in direction_irradiances_W:
            print('energy', direction_name.name, ':', sum(direction_irradiances_W[direction_name])/1000, 'kWh')

        if with_matplotlib:
            plt.figure()
            for direction_name in direction_irradiances_W:
                plt.plot(self.datetimes, direction_irradiances_W[direction_name], label=direction_name.name)
            plt.legend()
            plt.ylabel('Watt')
            plt.axis('tight')
            plt.grid()
        else:
            fig: go.Figure = make_subplots(rows=1, cols=1, shared_xaxes=True)
            for direction_name in direction_irradiances_W:
                fig.add_trace(go.Scatter(x=self.datetimes, y=direction_irradiances_W[direction_name], name=direction_name.name, line_shape='hv'), row=1, col=1)
            if mask is not None:
                mask.plot(axis=fig.axes[0])
            # Use non-interactive backend to avoid Tkinter crashes on macOS
            try:
                # Try to show in browser if possible
                fig.show()
            except Exception:
                # Fallback: save to HTML file instead
                fig.write_html("cardinal_irradiances.html")
                print("Plot saved to cardinal_irradiances.html")

    class Parameters:

        def __init__(self, vals: tuple[str] = None) -> None:
            self.parameters = dict()
            self.parameters['tau_direct'] = [0.9, (0, 1)]  # 0.9
            self.parameters['tau_diffuse'] = [0.9, (0, 1)]  # 0.9
            self.parameters['power_nebulosity'] = [3.4, (0, 20)]   # 3.4
            self.parameters['M0_correct'] = [614, (400, 4000)]  # 614
            self.parameters['ratio_nebulosity'] = [0.75, (0, 1)]  # 0.75
            self.parameters['alpha'] = [0.271, (0, 2)]  # 0.271
            self.parameters['beta'] = [0.294, (0, 1)]  # 0.294
            self.parameters['Mh_0'] = [0.0065, (0, .1)]  # 0.0065
            self.parameters['Mh_1'] = [5.256, (0, 10)]  # 5.256
            self.parameters['rhi_0'] = [0.271, (0, 1)]  # 0.271
            self.parameters['rhi_1'] = [0.706, (0, 2)]  # 0.706
            self.parameters['rayleigh'] = [9.4, (0, 20)]  # 9.4
            self.parameters['steam_1'] = [6.112, (1, 10)]  # 6.112
            self.parameters['steam_2'] = [17.67, (10, 30)]  # 17.67
            self.parameters['steam_3'] = [243.5, (100, 500)]  # 243.5
            self.parameters['linke_1'] = [2.4, (.5, 5)]  # 2.4
            self.parameters['linke_2'] = [14.6, (1, 30)]  # 14.6
            self.parameters['linke_3'] = [0.4, (0, 2)]  # 0.4
            if vals is not None:
                self(value=vals)

        def bounds(self, pname: str = None):
            if pname is not None:
                return self.parameters[pname][1]
            else:
                return [self.parameters[pname][1] for pname in self.parameters]

        def __call__(self, pname: str | list[str] = None, value: float | list[float] = None):
            if value is None:
                if type(pname) is str:
                    return self.parameters[pname][0]
                else:
                    return [self.parameters[_][0] for _ in self.parameters]
            else:
                if type(pname) is str:
                    self.parameters[pname][0] = value
                else:
                    pnames = self.names()
                    for _ in range(len(self.parameters)):
                        self.parameters[pnames[_]][0] = value[_]

        def names(self):
            return tuple(self.parameters.keys())

        def __str__(self):
            return '\n'.join(['%s: %g in (%g, %g)' % (pname, self.parameters[pname][0], *self.parameters[pname][1]) for pname in self.parameters])

    @staticmethod
    def matching_error(vals: list[float], site_weather_data: SiteWeatherData, solar_model: SolarModel):
        parameters = SolarModel.Parameters(vals)
        new_solar_model = SolarModel(solar_model.site_weather_data, horizon_mask=solar_model.horizon_mask, parameters=parameters)
        irradiances_W = new_solar_model.irradiances_W(exposure_deg=0, slope_deg=180, details=True)
        # dhi: list[float] = solar_model.ghi
        model_total_irradiances_W = irradiances_W[COLLECTED_RADIATIONS.TILT_TOTAL]
        # model_diffuse_irradiances_W = irradiances_W[COLLECTED_RADIATIONS.TILT_DIFFUSE]
        # gni: list[float] = solar_model.gni
        measured_total_irradiances_W = site_weather_data('ghi')
        # measured_diffuse_irradiances_W: list[float] = site_weather_data('dhi')
        # return sum([abs(model_diffuse_irradiances_W[i] - measured_diffuse_irradiances_W[i]) + abs(model_total_irradiances_W[i] - measured_total_irradiances_W[i]) for i in range(len(site_weather_data))]) / len(site_weather_data) / 2
        return sum([abs(measured_total_irradiances_W[i] - model_total_irradiances_W[i]) for i in range(len(site_weather_data))]) / len(site_weather_data)

    def match_measurements(self, plot: bool = False):
        dts_optim: list[datetime.datetime] = self.site_weather_data.datetimes
        # direct_radiation = self.site_weather_data('direct_radiation')
        # diffuse_radiation = self.site_weather_data('diffuse_radiation')
        # direct_normal_irradiance = self.site_weather_data('direct_normal_irradiance')
        # shortwave_radiation = self.site_weather_data('shortwave_radiation')
        print("initial error:", SolarModel.matching_error(self.parameters(), self.site_weather_data, self))

        # Callback function to display optimization progress
        iteration_count = [0]  # Use list to allow modification in nested function

        def optimization_callback(xk):
            iteration_count[0] += 1
            current_error = SolarModel.matching_error(xk, self.site_weather_data, self)
            print(f"Iteration {iteration_count[0]:3d}: Error = {current_error:.6f}")

            # Show parameter values every 5 iterations to verify they're changing
            if iteration_count[0] % 5 == 0:
                params = SolarModel.Parameters(xk)
                print(f"  Parameters at iteration {iteration_count[0]}:")
                for pname in params.names():
                    print(f"    {pname}: {params(pname):.6f}")

            return False  # Continue optimization

        if plot:
            import plotly.graph_objs as go
            from plotly.subplots import make_subplots

            fig = make_subplots(rows=1, cols=1, shared_xaxes=True)
            irradiances_W = self.irradiances_W(exposure_deg=0, slope_deg=0, details=True)
            model_total_irradiances_W = irradiances_W[COLLECTED_RADIATIONS.TILT_TOTAL]
            model_diffuse_irradiances_W = irradiances_W[COLLECTED_RADIATIONS.TILT_DIFFUSE]
            measured_total_irradiances_W = self.site_weather_data('direct_radiation')
            measured_diffuse_irradiances_W: list[float] = self.site_weather_data('diffuse_radiation')
            fig.add_trace(go.Scatter(x=dts_optim, y=model_total_irradiances_W, name='model_total_irradiances_W', line_shape='hv'), row=1, col=1)
            fig.add_trace(go.Scatter(x=dts_optim, y=model_diffuse_irradiances_W, name='model_diffuse_irradiances_W', line_shape='hv'), row=1, col=1)
            fig.add_trace(go.Scatter(x=dts_optim, y=measured_total_irradiances_W, name='measured_total_irradiances_W', line_shape='hv'), row=1, col=1)
            fig.add_trace(go.Scatter(x=dts_optim, y=measured_diffuse_irradiances_W, name='measured_diffuse_irradiances_W', line_shape='hv'), row=1, col=1)
            fig.update_layout(title='before parameter adjustment')
            # Use non-interactive backend to avoid Tkinter crashes on macOS
            try:
                # Try to show in browser if possible
                fig.show()
            except Exception:
                # Fallback: save to HTML file instead
                fig.write_html("solar_before_adjustment.html")
                print("Plot saved to solar_before_adjustment.html")
            # fig.add_trace(go.Scatter(x=dts_optim, y=diffuse_radiation, name='diffuse_radiation', line_shape='hv'), row=1, col=1)

        optim_result = minimize(SolarModel.matching_error, self.parameters(), args=(self.site_weather_data, self), method='NELDER-MEAD',
                                bounds=self.parameters.bounds(), callback=optimization_callback, tol=1e-6, options={'disp': True})
        # optim_result = differential_evolution(SolarModel.matching_error, bounds=self.parameters.bounds(), args=(self.site_weather_data, self), disp=True, polish=True, workers=-1)
        print(optim_result)
        parameters = SolarModel.Parameters(optim_result.x)
        print(parameters)
        solar_model = SolarModel(self.site_weather_data, horizon_mask=self.horizon_mask, parameters=parameters)

        if plot:
            import plotly.graph_objs as go
            from plotly.subplots import make_subplots

            # Get measured data for comparison
            measured_direct_radiation = self.site_weather_data('direct_radiation')
            measured_diffuse_radiation = self.site_weather_data('diffuse_radiation')

            # Get optimized model data
            irradiances_W = solar_model.irradiances_W(exposure_deg=0, slope_deg=0, details=True)
            model_total_irradiances_W = irradiances_W[COLLECTED_RADIATIONS.TILT_TOTAL]
            model_diffuse_irradiances_W = irradiances_W[COLLECTED_RADIATIONS.TILT_DIFFUSE]

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=('Total Irradiances (W/m²)', 'Diffuse Irradiances (W/m²)'))

            # Plot total irradiances comparison
            fig.add_trace(go.Scatter(x=dts_optim, y=model_total_irradiances_W, name='model_total', line_shape='hv'), row=1, col=1)
            fig.add_trace(go.Scatter(x=dts_optim, y=measured_direct_radiation, name='measured_direct', line_shape='hv'), row=1, col=1)

            # Plot diffuse irradiances comparison
            fig.add_trace(go.Scatter(x=dts_optim, y=model_diffuse_irradiances_W, name='model_diffuse', line_shape='hv'), row=2, col=1)
            fig.add_trace(go.Scatter(x=dts_optim, y=measured_diffuse_radiation, name='measured_diffuse', line_shape='hv'), row=2, col=1)

            # Update layout
            fig.update_layout(title='Solar Model: After Parameter Optimization', height=600, showlegend=True)
            fig.update_xaxes(title_text="Date/Time", row=2, col=1)
            fig.update_yaxes(title_text="Irradiance (W/m²)", row=1, col=1)
            fig.update_yaxes(title_text="Irradiance (W/m²)", row=2, col=1)

            # Use non-interactive backend to avoid Tkinter crashes on macOS
            try:
                # Try to show in browser if possible
                fig.show()
            except Exception:
                # Fallback: save to HTML file instead
                fig.write_html("solar_after_adjustment.html")
                print("Plot saved to solar_after_adjustment.html")
        return solar_model


def regular_angle_to_decimal_angle_converter(decimals, minutes, seconds):
    """Convert decimals, minutes, seconds to float value.

    :param decimals: number of degrees as an integer
    :type decimals: int
    :param minutes: number of minutes
    :type minutes: int
    :param seconds: number of seconds
    :type seconds: int
    :return: angle in decimal format
    :rtype: float
    """
    return decimals + minutes/60 + seconds/3600


def en2fr(val: float) -> str:
    val = str(val)
    if '.' in val:
        return val.replace('.', ',')
    return str(val)


class SolarSystem:
    """Solar collector system management and analysis class.

    This class provides comprehensive solar collector system management capabilities
    for building energy analysis. It handles multiple collectors, masking systems,
    and solar gain calculations through building openings and solar installations.
    """

    def __init__(self, solar_model: SolarModel):
        """Create a set of solar collectors with masks to estimate the global solar gain.

        :param site_weather_data: weather data
        :type site_weather_data: SiteWeatherData
        :param solar_mask: distant solar mask used for the whole building. None means no global solar masks
        :type solar_mask: ComplexZone
        """
        self.datetimes: list[datetime.datetime] = solar_model.site_weather_data.datetimes
        self.stringdates: list[str] = solar_model.site_weather_data.stringdates
        self.temperatures: list[float] = solar_model.site_weather_data.get('temperature')
        self.nebulosities_in_percent: list[float] = solar_model.site_weather_data.get('cloudiness')
        self.humidities: list[float] = solar_model.site_weather_data.get('humidity')
        self.pollution: float = solar_model.site_weather_data.pollution
        self.albedo: float = solar_model.site_weather_data.albedo
        self.solar_model: SolarModel = solar_model
        self.collectors: dict[str, Collector] = dict()

    @property
    def collector_names(self) -> tuple[str]:
        return tuple(self.collectors.keys())

    def collector(self, name: str) -> Collector:
        return self.collectors[name]

    def mask(self, collector_name: str = None) -> Mask:
        if collector_name is None:
            return self.solar_model.horizon_mask
        elif collector_name in self.collectors:
            if collector_name in self.collectors:
                return StackedMask(self.solar_model.horizon_mask, self.collectors[collector_name].mask)
            else:
                return self.solar_model.horizon_mask
        else:
            raise ValueError('unknown collector name: %s' % collector_name)

    def plot_mask(self, collector_name: str = None, **kwargs):
        self.mask(collector_name).plot(**kwargs)

    def clear_collectors(self, collector_name: str = None):
        if collector_name is None:
            self.collectors.clear()
        elif collector_name in self.collector_names:
            del self.collectors[collector_name]

    def powers_W(self, gather_collectors: bool = False) -> list[float] | dict[str, dict[str, list[float]]]:
        """Return hourly solar gains coming through the collectors and with the type of radiation (RADIATION_TYPE.TOTAL, RADIATION_TYPE.DIRECT, RADIATION_TYPE.DIFFUSE, RADIATION_TYPE.REFLECTED).

        :return: a dictionary with collectors as keys and a dictionary with types of radiations as values
        :rtype: dict[str, dict[str, list[float]]]
        """
        collectors_powers = dict()
        for collector_name in self.collectors:
            collectors_powers[collector_name] = self.collectors[collector_name].powers_W()

        if not gather_collectors:
            return collectors_powers
        else:
            powers_W = None
            for collector_name in self.collector_names:
                if powers_W is None:
                    powers_W = collectors_powers[collector_name]
                else:
                    for k in range(len(self.datetimes)):
                        powers_W[k] += collectors_powers[collector_name][k]
            return powers_W

    def __len__(self):
        """Return the number of hours in the weather data.

        :return: number of hours in the weather data
        :rtype: int
        """
        return len(self.stringdates)

    def day_degrees_solar_gain_xls(self, file_name='calculations', heat_temperature_reference=18,  cool_temperature_reference=26):
        """Save day degrees and solar gains per window for each day in an xls file.

        :param file_name: file name without extension, default to 'calculation'
        :type file_name: str
        :param temperature_reference: reference temperature for heating day degrees
        :type heat_temperature_reference: float
        :param cool_temperature_reference: reference temperature for cooling day degrees
        :type cool_temperature_reference: float
        """
        print('Heating day degrees')
        stringdate_days, average_temperature_days, min_temperature_days, max_temperature_days, dju_heat_days = self.solar_model.site_weather_data.day_degrees(temperature_reference=heat_temperature_reference, heat=True)
        print('Cooling day degrees')
        _, _, _, _, dju_cool_days = self.solar_model.site_weather_data.day_degrees(temperature_reference=cool_temperature_reference, heat=False)

        data: list[list[str]] = [['date'], ['Tout'], ['Tout_min'], ['Tout_max'], ['dju_heat'], ['dju_cool']]
        data[0].extend(stringdate_days)
        data[1].extend(average_temperature_days)
        data[2].extend(min_temperature_days)
        data[3].extend(max_temperature_days)
        data[4].extend(dju_heat_days)
        data[5].extend(dju_cool_days)

        collectors_solar_gains_in_kWh: dict[str, list[float]] = self.powers_W()
        i = 6
        for collector_name in self.collector_names:
            data.append([collector_name+'(Wh)'])
            if len(self.collector_names) > 1:
                data[i].extend(day_averager(self.datetimes, collectors_solar_gains_in_kWh[collector_name], average=False))
            else:
                data[i].extend(day_averager(self.datetimes, collectors_solar_gains_in_kWh[collector_name], average=False))
            i += 1

        excel_workbook = pyexcelerate.Workbook()
        excel_workbook.new_sheet(file_name, data=list(map(list, zip(*data))))
        result_folder = _RESULTS_FOLDER
        excel_workbook.save(mkdir_if_not_exist(result_folder + file_name + '.xlsx'))


class Mask(ABC):
    """Abstract base class for solar obstruction masking systems.

    This abstract class provides the foundation for solar obstruction modeling
    systems used in building energy analysis. It defines the interface for
    determining solar position visibility and obstruction calculations.
    """

    _azimuth_min_max_deg: tuple = (-180, 180)
    _altitude_min_max_deg: tuple = (0, 90)

    @staticmethod
    def _normalize_input(solar_positions) -> tuple[np.ndarray, np.ndarray]:
        """Normalize input to azimuth and altitude arrays."""
        if isinstance(solar_positions, pd.DataFrame):
            # DataFrame input
            azimuths = solar_positions['azimuth'].values
            altitudes = solar_positions['altitude'].values
        elif isinstance(solar_positions, np.ndarray):
            # Numpy array input [azimuth, altitude]
            if solar_positions.ndim == 1:
                # Single position
                azimuths: np.ndarray = np.array([solar_positions[0]])
                altitudes: np.ndarray = np.array([solar_positions[1]])
            else:
                azimuths: np.ndarray = solar_positions[:, 0]
                altitudes: np.ndarray = solar_positions[:, 1]
        else:
            raise TypeError(f"Unsupported input type: {type(solar_positions)}. Use pd.DataFrame or np.ndarray.")
        return azimuths, altitudes

    @abstractmethod
    def passthrough(self, solar_positions: pd.DataFrame | np.ndarray, observer_elevation_m: float = 0.0) -> np.ndarray:
        """Determine whether solar positions pass through the mask (True) or are blocked (False).

        :param solar_positions: DataFrame with 'azimuth' and 'altitude' columns,
                               or numpy array with shape (N, 2) where columns are [azimuth, altitude] in degrees
        :type solar_positions: pd.DataFrame | np.ndarray
        :param observer_elevation_m: Observer elevation in meters, defaults to 0
        :type observer_elevation_m: float
        :return: Boolean array indicating if each position passes through (True) or is blocked (False)
        :rtype: np.ndarray
        """
        raise NotImplementedError

    def plot(self, axis=None, name: str = '', resolution: int = 100, observer_elevation_m: float = 0.0):
        """Plot the mask according to the specified max_plot_resolution and print a description of the zone.

        :param name: file_name of the plot, default to ''
        :return: the zone
        """
        # Create coordinate grids using numpy in degrees (much more intuitive)
        azimuth_range = np.linspace(Mask._azimuth_min_max_deg[0], Mask._azimuth_min_max_deg[1], resolution)
        altitude_range = np.linspace(Mask._altitude_min_max_deg[0], Mask._altitude_min_max_deg[1], resolution)

        # Create meshgrid for all combinations
        azimuth_grid, altitude_grid = np.meshgrid(azimuth_range, altitude_range)

        # Flatten grids - already in degrees, no conversion needed!
        azimuth_flat_deg: np.ndarray = azimuth_grid.flatten()
        altitude_flat_deg: np.ndarray = altitude_grid.flatten()

        # Create numpy array of all test positions [azimuth, altitude]
        test_positions: np.ndarray = np.column_stack([azimuth_flat_deg, altitude_flat_deg])

        # Vectorized mask evaluation - single call for all positions!
        blocked_mask: np.ndarray = ~self.passthrough(test_positions, observer_elevation_m)

        # Convert back to grid shape for plotting
        blocked_grid = blocked_mask.reshape(azimuth_grid.shape)

        # Setup plot
        if axis is None:
            figure, axis = plt.subplots(figsize=plot_size)
            axis.set_xlim(Mask._azimuth_min_max_deg)
            axis.set_ylim(Mask._altitude_min_max_deg)
            axis.axis('tight')
            axis.grid()
            axis.set_xlabel('Azimuth in degrees (0° = South, +90° =West)')
        axis.set_ylabel('Altitude in degrees')
        axis.set_title(name)
        # Don't override the axis parameter - use the one passed in or created above

        # Plot blocked positions efficiently using numpy boolean indexing
        azimuth_blocked: np.ndarray = azimuth_grid[blocked_grid]
        altitude_blocked: np.ndarray = altitude_grid[blocked_grid]

        if len(azimuth_blocked) > 0:
            axis.scatter(azimuth_blocked, altitude_blocked, c='grey', marker='x', s=1)
        return axis

    @abstractmethod
    def __repr__(self) -> str:
        pass


class RectangularMask(Mask):
    """Rectangular solar obstruction mask for building and terrain modeling.

    This class implements a rectangular mask for solar obstruction modeling,
    commonly used for building facades, windows, and rectangular terrain features
    in solar energy analysis and building energy modeling.
    """

    def __init__(self, azimuths_deg: np.ndarray = None, altitudes_deg: np.ndarray = None, minmax_azimuths_deg: tuple[float, float] = None, minmax_altitudes_deg: tuple[float, float] = None, inverted: bool = False) -> None:
        super().__init__()
        self.inverted = inverted
        # Handle both new numpy array format and legacy tuple format
        # Check if first positional argument is a tuple of 2 values (minmax format)
        if azimuths_deg is not None and not isinstance(azimuths_deg, np.ndarray) and isinstance(azimuths_deg, (tuple, list)) and len(azimuths_deg) == 2:
            # First argument is a minmax tuple, treat it as minmax_azimuths_deg
            az_min = float(azimuths_deg[0])
            az_max = float(azimuths_deg[1])
            # Normalize angles to [-180, 180] range
            if az_max > 180:
                az_max = az_max - 360
            if az_min < -180:
                az_min = az_min + 360
            self.minmax_azimuths_deg = (az_min, az_max)
        elif azimuths_deg is not None:
            azimuths_deg = np.asarray(azimuths_deg, dtype=float)
            self.minmax_azimuths_deg = (float(np.min(azimuths_deg)), float(np.max(azimuths_deg)))
        elif minmax_azimuths_deg is not None:
            az_min = float(minmax_azimuths_deg[0])
            az_max = float(minmax_azimuths_deg[1])
            # Normalize angles to [-180, 180] range
            # If az_max > 180, convert to negative equivalent (e.g., 270° -> -90°)
            if az_max > 180:
                az_max = az_max - 360
            # If az_min < -180, convert to positive equivalent (e.g., -270° -> 90°)
            if az_min < -180:
                az_min = az_min + 360
            self.minmax_azimuths_deg = (az_min, az_max)
        else:
            self.minmax_azimuths_deg = None

        if altitudes_deg is not None:
            altitudes_deg = np.asarray(altitudes_deg, dtype=float)
            self.minmax_altitudes_deg = (float(np.min(altitudes_deg)), float(np.max(altitudes_deg)))
        elif minmax_altitudes_deg is not None:
            self.minmax_altitudes_deg = (float(minmax_altitudes_deg[0]), float(minmax_altitudes_deg[1]))
        else:
            self.minmax_altitudes_deg = None

    def passthrough(self, solar_positions: pd.DataFrame | np.ndarray, observer_elevation_m: float = 0.0) -> np.ndarray:
        azimuths_deg, altitudes_deg = self._normalize_input(solar_positions)

        if not self.inverted:
            result = np.zeros(len(azimuths_deg), dtype=bool)
            if self.minmax_azimuths_deg is not None:
                az_min = self.minmax_azimuths_deg[0]
                az_max = self.minmax_azimuths_deg[1]
                # Handle azimuth wrap-around: ranges that cross the -180°/180° boundary
                azimuths_normalized = azimuths_deg.copy()

                # Check if range wraps around (az_min > az_max after normalization)
                if az_min > az_max:
                    # Range wraps around: blocks everything OUTSIDE [az_min, 180] and [-180, az_max]
                    # So passes through [az_min, 180] and [-180, az_max]
                    result |= ~(
                        ((azimuths_normalized >= az_min) & (azimuths_normalized <= 180))
                        | ((azimuths_normalized >= -180) & (azimuths_normalized <= az_max))
                    )
                else:
                    # Normal range: no wrap-around
                    # Handle 180° and -180° equivalence at boundaries
                    if az_max == 180 or az_min == -180:
                        azimuths_normalized = np.where(azimuths_normalized == -180, 180, azimuths_normalized)
                        az_max_normalized = 180 if az_max == 180 else az_max
                        az_min_normalized = -180 if az_min == -180 else az_min
                        result |= (azimuths_normalized <= az_min_normalized) | (azimuths_normalized >= az_max_normalized)
                    else:
                        result |= (azimuths_deg <= az_min) | (azimuths_deg >= az_max)

            # Apply altitude constraints
            if self.minmax_altitudes_deg is not None:
                alt_min = self.minmax_altitudes_deg[0]
                alt_max = self.minmax_altitudes_deg[1]
                result |= (altitudes_deg <= alt_min) | (altitudes_deg >= alt_max)
        else:
            result = np.ones(len(azimuths_deg), dtype=bool)
            # Apply azimuth constraints
            if self.minmax_azimuths_deg is not None:
                az_min = self.minmax_azimuths_deg[0]
                az_max = self.minmax_azimuths_deg[1]
                # Handle azimuth wrap-around: ranges that cross the -180°/180° boundary
                # Normalize azimuths to handle wrap-around
                azimuths_normalized = azimuths_deg.copy()

                # Check if range wraps around (az_min > az_max after normalization)
                if az_min > az_max:
                    # Range wraps around: covers [az_min, 180] and [-180, az_max]
                    # Example: (90, -90) covers [90, 180] and [-180, -90]
                    result &= (
                        ((azimuths_normalized >= az_min) & (azimuths_normalized <= 180))
                        | ((azimuths_normalized >= -180) & (azimuths_normalized <= az_max))
                    )
                else:
                    # Normal range: no wrap-around
                    # Handle 180° and -180° equivalence at boundaries
                    if az_max == 180:
                        # Map -180 to 180 so both are treated as the same angle
                        azimuths_normalized = np.where(azimuths_normalized == -180, 180, azimuths_normalized)
                        result &= (azimuths_normalized >= az_min) & (azimuths_normalized <= az_max)
                    elif az_min == -180:
                        # Map 180 to -180 so both are treated as the same angle
                        azimuths_normalized = np.where(azimuths_normalized == 180, -180, azimuths_normalized)
                        result &= (azimuths_normalized >= az_min) & (azimuths_normalized <= az_max)
                    else:
                        result &= (azimuths_deg >= az_min) & (azimuths_deg <= az_max)

            # Apply altitude constraints
            if self.minmax_altitudes_deg is not None:
                alt_min = self.minmax_altitudes_deg[0]
                alt_max = self.minmax_altitudes_deg[1]
                result &= (altitudes_deg >= alt_min) & (altitudes_deg <= alt_max)

        return result

    def __repr__(self) -> str:
        az_str = f'({self.minmax_azimuths_deg[0]:.1f}°,{self.minmax_azimuths_deg[1]:.1f}°)' if self.minmax_azimuths_deg else 'None'
        alt_str = f'({self.minmax_altitudes_deg[0]:.1f}°,{self.minmax_altitudes_deg[1]:.1f}°)' if self.minmax_altitudes_deg else 'None'
        return f'RectangularMask[AZ{az_str}:AL{alt_str}]'


class SideMask(Mask):
    """Side obstruction mask for building facade and wall modeling.

    This class implements a side mask for modeling building facades, walls, and
    other vertical or tilted surfaces that can obstruct solar radiation. It
    provides detailed geometric modeling for accurate solar shadow calculations.
    """

    def __init__(self, x_center: float, y_center: float, width: float, height: float, exposure_deg: float, slope_deg: float = 90, elevation: float = 0, normal_rotation_angle_deg: float = 0.0):
        super().__init__()
        self.x_center: float = x_center
        self.y_center: float = y_center
        self.width: float = width
        self.height: float = height
        self.exposure_deg: float = exposure_deg
        self.slope_deg: float = slope_deg
        self.side_rotation_deg: float = normal_rotation_angle_deg
        self.side_elevation_m: float = elevation
        self.observer_elevation_m: float = 0

        # Calculate distance from origin to center point
        self.distance_m: float = sqrt(self.x_center**2 + self.y_center**2)
        # Set width and height in meters (aliases for consistency)
        self.width_m: float = width
        self.height_m: float = height
        # Margin for intersection calculations (default: 0)
        self.margin_m: float = 0.0

        # Normalize exposure angle to ensure 180° and -180° are treated identically
        normalized_exposure_deg = self.exposure_deg % 360
        if normalized_exposure_deg > 180:
            normalized_exposure_deg -= 360
        exposure_rad = radians(normalized_exposure_deg)

        # Convert slope angle to radians
        if not (0 <= self.slope_deg <= 180):
            warnings.warn(f"Slope angle must be between 0 and 180 degrees, got {self.slope_deg}")

        # Calculate the normal vector using spherical coordinates
        # Start with a vertical surface facing the exposure direction
        cos_exposure = cos(exposure_rad)
        sin_exposure = sin(exposure_rad)

        # Base normal vector (vertical surface facing exposure direction)
        base_normal = [cos_exposure, sin_exposure, 0.0]

        # Apply slope first (rotation around horizontal axis perpendicular to exposure)

        # Rotation axis for slope (perpendicular to exposure direction)
        rotation_axis = [-sin_exposure, cos_exposure, 0.0]

        # Apply slope using Rodrigues' rotation formula
        # With new convention: 0°=ground, 90°=vertical, 180°=sky
        # Need to rotate by (90 - slope_deg) to convert from new convention to internal calculation
        internal_slope_rad = radians(90 - self.slope_deg)
        cos_internal_slope = cos(internal_slope_rad)
        sin_internal_slope = sin(internal_slope_rad)
        self.side_coord_normal = self._rodrigues_rotation(base_normal, rotation_axis, cos_internal_slope, sin_internal_slope)

        # Height vector: perpendicular to normal and width
        # For a consistent coordinate system, define height first
        base_height = [0.0, 0.0, 1.0]  # Upward direction

        # Apply slope to height vector using internal slope calculation
        self.side_coord_height = self._rodrigues_rotation(base_height, rotation_axis, cos_internal_slope, sin_internal_slope)

        # Width vector: perpendicular to normal and height
        self.side_coord_width = self._cross_product(self.side_coord_height, self.side_coord_normal)

        # Ensure normalization (numerical safety)
        self.side_coord_normal = self._normalize_vector(self.side_coord_normal)
        self.side_coord_width = self._normalize_vector(self.side_coord_width)
        self.side_coord_height = self._normalize_vector(self.side_coord_height)

    def _rodrigues_rotation(self, vector, axis, cos_angle, sin_angle):
        """Apply Rodrigues' rotation formula to rotate a vector around an axis."""
        # v_rot = v*cos(θ) + (k×v)*sin(θ) + k(k·v)(1-cos(θ))
        cross_product = self._cross_product(axis, vector)
        dot_product = self._dot_product(axis, vector)

        result = [
            vector[0] * cos_angle + cross_product[0] * sin_angle + axis[0] * dot_product * (1 - cos_angle),
            vector[1] * cos_angle + cross_product[1] * sin_angle + axis[1] * dot_product * (1 - cos_angle),
            vector[2] * cos_angle + cross_product[2] * sin_angle + axis[2] * dot_product * (1 - cos_angle)
        ]
        return result

    def _cross_product(self, a, b):
        """Compute cross product of two 3D vectors."""
        return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        ]

    def _dot_product(self, a, b):
        """Compute dot product of two 3D vectors."""
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    def _normalize_vector(self, vector):
        """Normalize a 3D vector to unit length."""
        magnitude = sqrt(vector[0]**2 + vector[1]**2 + vector[2]**2)
        if magnitude == 0:
            return [0, 0, 0]
        return [vector[0] / magnitude, vector[1] / magnitude, vector[2] / magnitude]

    def passthrough(self, solar_positions, observer_elevation_m: float = 0.0) -> np.ndarray:
        azimuths, altitudes = self._normalize_input(solar_positions)
        n_positions = len(azimuths)
        result = np.ones(n_positions, dtype=bool)

        # Use the passed observer_elevation_m parameter (which may be 0)
        # This allows overriding the instance default value

        # Convert degrees to radians for calculations
        azimuths_rad = np.radians(azimuths)
        altitudes_rad = np.radians(altitudes)

        # Convert sun positions to 3D direction vectors
        sun_directions = np.column_stack([
            np.cos(altitudes_rad) * np.cos(azimuths_rad),
            np.cos(altitudes_rad) * np.sin(azimuths_rad),
            np.sin(altitudes_rad)
        ])

        # Check if sun is behind the plane (vectorized dot product)
        ndots = np.dot(sun_directions, self.side_coord_normal)
        behind_plane = ndots <= 0.0
        result[behind_plane] = True  # Sun behind plane -> no blocking

        # For positions not behind plane, calculate ray-plane intersections
        valid_mask = ~behind_plane
        if not np.any(valid_mask):
            return result

        valid_ndots = ndots[valid_mask]
        valid_directions = sun_directions[valid_mask]

        # Calculate the lower central reference point of the surface
        # Position is given by x_center, y_center (horizontal) and side_elevation_m (vertical)
        # This is the absolute position of the lower central point of the surface
        lower_central_reference = np.array([
            self.x_center,
            self.y_center,
            self.side_elevation_m
        ])

        # Observer position (rays start from here, not from origin)
        observer_pos = np.array([0.0, 0.0, observer_elevation_m])

        # Ray-plane intersection: t = (plane_point - observer_pos) · normal / (sun_direction · normal)
        # For a plane with point P and normal n: (point - P) · n = 0
        # Ray: point = observer_pos + t * sun_direction
        # Solving: (observer_pos + t*s - plane_point) · n = 0
        # Rearranging: (observer_pos - plane_point) · n + t * (s · n) = 0
        # So: t = -((observer_pos - plane_point) · n) / (s · n)
        # Or: t = ((plane_point - observer_pos) · n) / (s · n)
        plane_to_observer_vec = lower_central_reference - observer_pos
        numerator = np.dot(plane_to_observer_vec, self.side_coord_normal)
        t_values = numerator / valid_ndots
        behind_observer = t_values <= 0.0

        # Calculate intersection points on the plane: start from observer position
        intersection_points = observer_pos[np.newaxis, :] + t_values[:, np.newaxis] * valid_directions

        # Note: The surface center would be at lower_central_reference + 0.5 * height_m * height_vector
        # but we use the lower central reference as the primary reference point for calculations

        # Calculate lower left corner from lower central reference point
        lower_left_corner = lower_central_reference - 0.5 * self.width_m * np.array(self.side_coord_width)

        # Calculate relative positions from lower left corner
        dP = intersection_points - lower_left_corner

        # Project onto width and height axes (vectorized)
        pu = np.dot(dP, self.side_coord_width)
        pv = np.dot(dP, self.side_coord_height)

        # Check if points are inside the rectangle
        inside_rectangle = ((0 <= pu) & (pu <= self.width_m + self.margin_m) &
                            (0 <= pv) & (pv <= self.height_m + self.margin_m))

        # Update result for valid positions
        valid_indices = np.where(valid_mask)[0]
        result[valid_indices[behind_observer]] = True  # Behind observer -> no blocking
        result[valid_indices[~behind_observer]] = ~inside_rectangle[~behind_observer]  # Blocked if inside rectangle

        return result

    def __repr__(self) -> str:
        return f"Side Mask (W:{self.width_m}m, H:{self.height_m}m) with center at {self.distance_m}m and directed to (EXP:{self.exposure_deg}°, SLOPE:{self.slope_deg}°, ROT:{self.side_rotation_deg}°) with observer elevation {self.observer_elevation_m}m, side elevation {self.side_elevation_m}m and margin of {self.margin_m}m"


class EllipsoidalMask(Mask):

    def __init__(self, center1_AZ_ALT, center2_AZ_ALT, perimeter_AZ_ALT, inverted: bool = False) -> None:
        super().__init__()
        self.inverted = inverted
        center1_azimuth_deg, center1_altitude_deg = center1_AZ_ALT
        center2_azimuth_deg, center2_altitude_deg = center2_AZ_ALT
        perimeter_azimuth_deg, perimeter_altitude_deg = perimeter_AZ_ALT
        # Handle both new separate parameter format and legacy tuple format
        self.center1_deg = np.array([float(center1_azimuth_deg), float(center1_altitude_deg)])
        self.center2_deg = np.array([float(center2_azimuth_deg), float(center2_altitude_deg)])
        self.perimeter_deg = np.array([float(perimeter_azimuth_deg), float(perimeter_altitude_deg)])

        # Calculate ellipse parameter (sum of distances from perimeter to two centers)
        self.ellipse_parameter = self._distance(self.center1_deg, self.center2_deg) + self._distance(self.center2_deg, self.perimeter_deg) + self._distance(self.perimeter_deg, self.center1_deg)

    def _distance(self, point1: np.ndarray, point2: np.ndarray) -> float:
        """Calculate euclidean distance between two points in degrees."""
        return np.sqrt(np.sum((point1 - point2) ** 2))

    def _three_positions_distance_sum(self, test_point: np.ndarray) -> float:
        """Calculate sum of distances from test point to the two centers."""
        return self._distance(self.center1_deg, self.center2_deg) + self._distance(self.center2_deg, test_point) + self._distance(test_point, self.center1_deg)

    def passthrough(self, solar_positions, observer_elevation_m: float = 0.0) -> np.ndarray:
        azimuths, altitudes = self._normalize_input(solar_positions)
        n_positions = len(azimuths)

        # Vectorized distance calculations
        test_points = np.column_stack([azimuths, altitudes])

        if not self.inverted:
            result = np.ones(n_positions, dtype=bool)
            # Calculate distance sums for all points at once
            for i in range(n_positions):
                distance_sum = self._three_positions_distance_sum(test_points[i])
                result[i] = self.ellipse_parameter < distance_sum
        else:
            result = np.zeros(n_positions, dtype=bool)
            # Calculate distance sums for all points at once
            for i in range(n_positions):
                distance_sum = self._three_positions_distance_sum(test_points[i])
                result[i] = self.ellipse_parameter > distance_sum

        return result

    def __repr__(self) -> str:
        return f'EllipsoidalMask[center1({self.center1_deg[0]:.1f}°,{self.center1_deg[1]:.1f}°),center2({self.center2_deg[0]:.1f}°,{self.center2_deg[1]:.1f}°),perimeter({self.perimeter_deg[0]:.1f}°,{self.perimeter_deg[1]:.1f}°)]'


class HorizonMask(Mask):

    def __init__(self, horizon_azimuths_deg: np.ndarray, horizon_altitudes_deg: np.ndarray, inverted: bool = False, south_reference: bool = False) -> None:
        super().__init__()
        azimuth_shift_deg = 0 if south_reference else -180
        self.inverted = inverted
        # Convert to numpy arrays if not already
        self.horizon_azimuths_deg = np.asarray(horizon_azimuths_deg, dtype=float) + azimuth_shift_deg
        self.horizon_altitudes_deg = np.asarray(horizon_altitudes_deg, dtype=float)

        if self.horizon_azimuths_deg[0] != -180:
            self.horizon_azimuths_deg = np.insert(self.horizon_azimuths_deg, 0, -180)
            self.horizon_altitudes_deg = np.insert(self.horizon_altitudes_deg, 0, self.horizon_altitudes_deg[0])
        if self.horizon_azimuths_deg[-1] != 180:
            self.horizon_azimuths_deg = np.append(self.horizon_azimuths_deg, 180)
            self.horizon_altitudes_deg = np.append(self.horizon_altitudes_deg, self.horizon_altitudes_deg[0])

        # Check for increasing azimuth values
        for i in range(1, len(self.horizon_azimuths_deg)):
            if self.horizon_azimuths_deg[i-1] > self.horizon_azimuths_deg[i]:
                raise ValueError(f'Skyline is not increasing in azimuth at index {i}: {self.horizon_azimuths_deg}')

        # Store horizon profile as numpy arrays
        self.horizon_azimuths = self.horizon_azimuths_deg
        self.horizon_altitudes = self.horizon_altitudes_deg

    def passthrough(self, solar_positions, observer_elevation_m: float = 0.0) -> np.ndarray:
        azimuths_deg, altitudes_deg = self._normalize_input(solar_positions)

        # Interpolate horizon altitude for each solar position azimuth
        horizon_altitudes_deg = np.interp(azimuths_deg, self.horizon_azimuths, self.horizon_altitudes)

        # Sun passes through if its altitude is above the horizon at that azimuth
        return horizon_altitudes_deg < altitudes_deg

    def __repr__(self) -> str:
        horizon_points = [f'({az:.1f}°,{alt:.1f}°)' for az, alt in zip(self.horizon_azimuths, self.horizon_altitudes)]
        return 'HorizonMask[%s]' % (','.join(horizon_points))


class StackedMask(Mask):

    def __init__(self, *masks: list[Mask]) -> None:
        super().__init__()
        self.masks: list[Mask] = list(masks)

    def add(self, mask: Mask):
        if mask is not None:
            self.masks.append(mask)

    def merge(self, mask: Mask | 'StackedMask' | None):
        if mask is None:
            pass
        elif isinstance(mask, StackedMask):
            self.masks.extend(mask.masks)
        elif isinstance(mask, Mask):
            self.masks.append(mask)
        else:
            raise ValueError(f'Invalid mask type: {type(mask)}')

    def passthrough(self, solar_positions, observer_elevation_m: float = 0.0) -> np.ndarray:
        azimuths, altitudes = self._normalize_input(solar_positions)
        n_positions = len(azimuths)

        # Start with all positions passing through
        result = np.ones(n_positions, dtype=bool)

        # Apply each mask (logical AND)
        for mask in self.masks:
            if mask is not None:
                mask_result = mask.passthrough(solar_positions, observer_elevation_m)
                result &= mask_result

        return result

    def __repr__(self) -> str:
        return '[' + ' + '.join([str(m) for m in self.masks]) + ']'


class InvertedMask(Mask):
    def __init__(self, mask: Mask) -> None:
        super().__init__()
        self.mask: Mask = mask

    def passthrough(self, solar_positions, observer_elevation_m: float = 0.0) -> np.ndarray:
        if self.mask is None:
            azimuths, altitudes = self._normalize_input(solar_positions)
            return np.ones(len(azimuths), dtype=bool)
        return ~self.mask.passthrough(solar_positions, observer_elevation_m)

    def __repr__(self) -> str:
        return f'Invert[{str(self.mask)}]'


class Collector:
    """Solar collector modeling with orientation and efficiency calculations.

    This class provides comprehensive solar collector modeling capabilities including
    orientation calculations, efficiency modeling, and solar gain analysis for
    building energy applications and solar system design.
    """

    def __init__(self, solar_system: SolarSystem, name: str, exposure_deg: float, slope_deg: float, surface_m2: float, solar_factor: float = 1, min_incidence_deg: float = 0, scale_factor: int = 1, close_mask: Mask = None, temperature_coefficient: float = 0, observer_elevation_m: float = 0.0) -> None:
        # if not (-180 <= exposure_deg <= 180):
        #     raise ValueError(f'Incorrect exposure value: {exposure_deg}')
        # if not (0 <= slope_deg <= 180):
        #     raise ValueError(f'Incorrect slope value: {slope_deg}')
        self.solar_system: SolarSystem = solar_system
        self.solar_model: SolarModel = solar_system.solar_model
        self.datetimes: list[datetime.datetime] = self.solar_model.datetimes
        self.outdoor_temperatures: list[float] = self.solar_model.temperatures_C
        self.name: str = name
        if name in self.solar_system.collector_names:
            raise ValueError('Solar collector "%s" still exists' % name)
        self.exposure_deg: float = exposure_deg
        self.slope_deg: float = slope_deg
        self.surface_m2: float = surface_m2
        self.solar_factor: float = solar_factor
        self.scale_factor: float = scale_factor
        self.mask: Mask = RectangularMask((exposure_deg-90+min_incidence_deg, exposure_deg+90-min_incidence_deg), (max(0, slope_deg-180+min_incidence_deg), min(180, slope_deg+min_incidence_deg)), inverted=True)
        if close_mask is not None:
            self.mask = StackedMask(self.mask, close_mask)
        self.temperature_coefficient: float = temperature_coefficient
        self.observer_elevation_m: float = observer_elevation_m
        if name in self.solar_system.collectors:
            raise ValueError(f'Collector {name} is already existing')
        self.solar_system.collectors[name] = self

    def powers_W(self, details: bool = False) -> dict[CANONICAL_RADIATIONS, list[float]] | list[float]:
        powers_W: list[float] = list()

        if not details:
            irradiances_W_per_m2: list[float] = self.solar_model.irradiances_W(exposure_deg=self.exposure_deg, slope_deg=self.slope_deg, scale_factor=1, mask=self.mask, observer_elevation_m=self.observer_elevation_m)
            irradiances_composites_W = dict()
        else:
            irradiances_composites_W = self.solar_model.irradiances_W(
                exposure_deg=self.exposure_deg, slope_deg=self.slope_deg, scale_factor=1, mask=self.mask, details=True, observer_elevation_m=self.observer_elevation_m)
            irradiances_W_per_m2: list[float] = irradiances_composites_W[COLLECTED_RADIATIONS.TILT_TOTAL]
            powers_components_W: dict[CANONICAL_RADIATIONS, list[float]] = {radiation_type: list() for radiation_type in irradiances_composites_W}

        for k in range(len(self.datetimes)):
            if self.temperature_coefficient > 0:
                temperature_factor: float = Collector.temperature_factor(irradiances_W_per_m2[k], self.outdoor_temperatures[k], self.temperature_coefficient)
            else:
                temperature_factor = 1
            powers_W.append(irradiances_W_per_m2[k] * self.surface_m2 * self.scale_factor * self.solar_factor * temperature_factor)
            for radiation_type in irradiances_composites_W:
                powers_components_W[radiation_type].append(irradiances_W_per_m2[k] * self.surface_m2 * self.scale_factor * self.solar_factor * temperature_factor)
        if not details:
            return powers_W
        else:
            return powers_W, powers_components_W

    @staticmethod
    def temperature_factor(irradiance_W_per_m2: float, outdoor_temperature: float, temperature_coefficient: float):
        TaNOCT: float = 46  # in °Celsius
        cell_temperature: float = outdoor_temperature + irradiance_W_per_m2 / 800 * (TaNOCT - 20)
        if cell_temperature > 25:
            return 1 - temperature_coefficient * max(cell_temperature - 25, 0)
        else:
            return 1

    def __str__(self):
        string: str = 'Collector "%s" (EXP:%g°, SLO:%g°) with a surface = %ix%gm2 and a solar factor = %g' % (
            self.name, self.exposure_deg, self.slope_deg, self.scale_factor, self.surface_m2, self.solar_factor)
        if self.mask is not None:
            string += ', has a specific mask: ' + str(self.mask)
        if self.temperature_coefficient != 0:
            string += ' (PV collector with a temperature coefficient = %g%%)' % (100*self.temperature_coefficient)
        return string


class PVplant:
    """Photovoltaic plant design and performance analysis class.

    This class provides comprehensive photovoltaic plant design and analysis
    capabilities including mounting system optimization, panel configuration,
    performance modeling, and energy yield calculations for solar energy systems.
    """

    def __init__(self, solar_model: SolarModel, exposure_deg: float, slope_deg: float, mount_type: MOUNT_TYPES, distance_between_arrays_m: float = None, number_of_panels: int = None, peak_power_kW: float = None, surface_pv_m2: float = None, number_of_panels_per_array: float = None, panel_width_m: float = 1, panel_height_m: float = 1.7, pv_efficiency: float = 0.2, number_of_cell_rows: float = 10, temperature_coefficient: float = 0.0035) -> None:

        self.solar_model: SolarModel = solar_model
        self.solar_system: SolarSystem = SolarSystem(self.solar_model)

        if exposure_deg is None or slope_deg is None:
            print('Compute best angle')
            exposure_deg, slope_deg = solar_model.best_direction()
        self.exposure_deg: float = exposure_deg
        self.exposure_rad: float = radians(exposure_deg)
        self.slope_deg: float = slope_deg
        self.slope_rad: float = radians(slope_deg)

        self.panel_width_m: float = panel_width_m
        self.panel_height_m: float = panel_height_m
        self.panel_surface_m2: float = panel_width_m * panel_height_m
        self.pv_efficiency: float = pv_efficiency

        self.mount_type: MOUNT_TYPES = mount_type

        if mount_type == MOUNT_TYPES.PLAN:
            if distance_between_arrays_m is None:
                self.distance_between_arrays_m: float = panel_height_m
            else:
                self.distance_between_arrays_m: float = max(distance_between_arrays_m, panel_height_m)
        else:
            if distance_between_arrays_m is None:
                self.distance_between_arrays_m: float = panel_height_m
            else:
                self.distance_between_arrays_m = distance_between_arrays_m

        if peak_power_kW is None and surface_pv_m2 is None and number_of_panels is None:
            raise ValueError('At one among number of panels, peak power or total surface of photovoltaic panels must be provided')
        if number_of_panels is not None:
            self.number_of_panels: int = number_of_panels
        elif surface_pv_m2 is not None:
            self.number_of_panels: int = ceil(surface_pv_m2 / self.panel_surface_m2)
            self.surface_pv_m2 = self.number_of_panels * self.panel_surface_m2
        else:
            self.number_of_panels: int = round(peak_power_kW / self.pv_efficiency / self.panel_surface_m2)
        self.peak_power_kW: float = self.number_of_panels * self.panel_surface_m2 * self.pv_efficiency
        self.surface_pv_m2: float = self.number_of_panels * self.panel_surface_m2

        if number_of_panels_per_array is None:
            self.number_of_panels_per_array = round(sqrt(self.number_of_panels))
        else:
            self.number_of_panels_per_array = number_of_panels_per_array
        self.array_width_m: float = self.number_of_panels_per_array * self.panel_width_m
        self.array_surface_in_m2 = self.array_width_m * self.panel_height_m

        self.number_of_cell_rows = number_of_cell_rows
        self.temperature_coefficient = temperature_coefficient

        self.number_of_panels_per_array: int = floor(self.array_width_m / self.panel_width_m)
        self.array_surface_in_m2: float = self.number_of_panels_per_array * self.panel_surface_m2

        self.n_panels: dict[str, int] = {'front_clear': 0, 'front_shadow': 0, 'rear_clear': 0, 'rear_shadow': 0}
        if self.mount_type == MOUNT_TYPES.PLAN:
            self.n_panels['front_clear'] = self.number_of_panels
            self.ground_surface_m2 = self.number_of_panels * self.panel_surface_m2 * abs(cos(self.slope_rad))

        elif self.mount_type == MOUNT_TYPES.FLAT:
            number_of_complete_arrays: int = floor(self.number_of_panels / self.number_of_panels_per_array)
            if number_of_complete_arrays == 0:
                self.n_panels['front_clear'] += self.number_of_panels
            else:
                self.n_panels['front_clear'] += self.number_of_panels_per_array
                self.n_panels['front_shadow'] += self.number_of_panels_per_array * (number_of_complete_arrays-1)
                self.n_panels['front_shadow'] += self.number_of_panels - self.number_of_panels_per_array * number_of_complete_arrays

        elif self.mount_type == MOUNT_TYPES.BACK2BACK:
            if distance_between_arrays_m < abs(self.panel_height_m * cos(self.slope_rad)) and self.number_of_panels > 1:
                print('The distance between arrays is too short')
                self.number_of_panels = 0
            is_an_unpaired_panel: int = self.number_of_panels % 2
            number_of_panel_pairs: int = self.number_of_panels // 2

            number_of_complete_panel_paired_arrays: int = number_of_panel_pairs // self.number_of_panels_per_array
            number_of_incomplete_paired_panels: int = number_of_panel_pairs % self.number_of_panels_per_array
            if number_of_complete_panel_paired_arrays > 0:  # there are several arrays of paired panels
                self.n_panels['front_clear'] += self.number_of_panels_per_array
                self.n_panels['rear_clear'] += self.number_of_panels_per_array
                self.n_panels['front_shadow'] += is_an_unpaired_panel
            else:  # there is only one array of paired panels
                self.n_panels['front_clear'] += number_of_incomplete_paired_panels
                self.n_panels['rear_clear'] += number_of_incomplete_paired_panels
                self.n_panels['front_clear'] += is_an_unpaired_panel
            remaining_panels_paired: int = (self.number_of_panels - self.number_of_panels_per_array*2 - is_an_unpaired_panel) / 2
            if remaining_panels_paired > 0:  # there are incomplete pairs of panels at the back
                self.n_panels['rear_shadow'] += remaining_panels_paired
                self.n_panels['front_shadow'] += remaining_panels_paired

        self.outdoor_temperatures: list[float] = self.solar_model.temperatures_C
        self.temperature_coefficient: float = temperature_coefficient
        self.number_of_cell_rows: float = number_of_cell_rows
        self.datetimes: list[datetime.datetime] = self.solar_model.datetimes

        self.cell_row_surface_in_m2: float = self.panel_surface_m2 / self.number_of_cell_rows
        if self.n_panels['front_clear'] > 0:
            Collector(self.solar_system, 'front_clear', exposure_deg=self.exposure_deg, slope_deg=slope_deg, surface_m2=self.cell_row_surface_in_m2,
                      solar_factor=self.pv_efficiency, scale_factor=self.number_of_cell_rows * self.n_panels['front_clear'], temperature_coefficient=self.temperature_coefficient)
        if self.n_panels['rear_clear'] > 0:
            Collector(self.solar_system, 'rear_clear', exposure_deg=self.exposure_deg+180, slope_deg=slope_deg, surface_m2=self.cell_row_surface_in_m2,
                      solar_factor=self.pv_efficiency, scale_factor=self.number_of_cell_rows * self.n_panels['rear_clear'], temperature_coefficient=self.temperature_coefficient)
        if self.n_panels['front_shadow'] > 0:
            for k in range(self.number_of_cell_rows):
                hi: float = (2*k+1)/(2*self.number_of_cell_rows) * self.panel_height_m
                minimum_sun_visible_altitude_in_deg: float = degrees(atan2(sin(self.slope_rad), (self.distance_between_arrays_m/(self.panel_height_m-hi)+cos(self.slope_rad))))
                row_mask = InvertedMask(RectangularMask(minmax_azimuths_deg=(self.exposure_deg-90, self.exposure_deg+90),
                                        minmax_altitudes_deg=(minimum_sun_visible_altitude_in_deg, 180)))
                Collector(self.solar_system, 'front_shadow%i' % k, exposure_deg=self.exposure_deg, slope_deg=self.slope_deg, surface_m2=self.cell_row_surface_in_m2,
                          solar_factor=self.pv_efficiency, scale_factor=self.n_panels['front_shadow'], close_mask=row_mask, temperature_coefficient=self.temperature_coefficient)
        if self.n_panels['rear_shadow'] > 0:
            for k in range(self.number_of_cell_rows):
                hi: float = (2*k+1)/(2*self.number_of_cell_rows) * self.panel_height_m
                minimum_sun_visible_altitude_in_deg: float = degrees(atan2(sin(self.slope_rad), (self.distance_between_arrays_m/(self.panel_height_m-hi)+cos(self.slope_rad))))
                row_mask = InvertedMask(RectangularMask(minmax_azimuths_deg=(self.exposure_deg+180-90, self.exposure_deg+180+90),
                                        minmax_altitudes_deg=(minimum_sun_visible_altitude_in_deg, 180)))
                Collector(self.solar_system, 'rear_shadow%i' % k, exposure_deg=self.exposure_deg+180, slope_deg=self.slope_deg, surface_m2=self.cell_row_surface_in_m2,
                          solar_factor=self.pv_efficiency, scale_factor=self.n_panels['rear_shadow'], close_mask=row_mask, temperature_coefficient=self.temperature_coefficient)

    def powers_W(self, gather_collectors: bool = True) -> list[float] | dict[str, dict[str, list[float]]]:
        return self.solar_system.powers_W(gather_collectors=gather_collectors)

    def __str__(self) -> str:
        string = 'The PV system is composed of %i panels for a total PV surface = %gm2\n' % (self.number_of_panels, self.surface_pv_m2)
        string += 'A PV panel (EXP: %g°, SLO: %g°)' % (self.exposure_deg, self.slope_deg)
        string += ' is W:%gm x H:%gm (%gm2) with an efficiency of %g%% and cells distributed in %i rows\n' % (self.panel_width_m,
                                                                                                              self.panel_height_m, self.panel_surface_m2, 100 * self.pv_efficiency, self.number_of_cell_rows)
        string += 'The mount type is %s with a peak power of %gkW with a distance between arrays of %gm\n' % (
            self.mount_type.name, self.peak_power_kW, self.distance_between_arrays_m)
        string += 'There are:\n - %i front facing panels not shadowed\n' % self.n_panels['front_clear']
        if self.n_panels['front_shadow'] > 0:
            string += ' - %i front facing panels shadowed\n' % self.n_panels['front_shadow']
        if self.n_panels['rear_shadow'] > 0:
            string += ' - %i rear facing panels shadowed\n' % self.n_panels['rear_shadow']
        if self.n_panels['rear_clear'] > 0:
            string += ' - %i rear facing panels not shadowed\n' % self.n_panels['rear_clear']
        return string

    def best_angles(self, distance_between_arrays_m: float = None, mount_type: MOUNT_TYPES = MOUNT_TYPES.PLAN, error_message: bool = False, initial_exposure_deg: float = 0, initial_slope_deg: float = 180) -> dict[str, float]:
        neighborhood: list[tuple[float, float]] = [(-1, 0), (-1, 1), (-1, -1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        taboo = list()
        exposure_slope_in_deg_candidate: tuple[float, float] = (initial_exposure_deg, initial_slope_deg)
        best_exposure_slope_in_deg = tuple(exposure_slope_in_deg_candidate)
        best_total_production_in_Wh = sum(self.powers_W(
            exposure_slope_in_deg_candidate[0], exposure_slope_in_deg_candidate[1], distance_between_arrays_m, mount_type, error_message))
        initial_production_Wh = best_total_production_in_Wh
        taboo.append(exposure_slope_in_deg_candidate)

        improvement = True
        while improvement:
            improvement = False
            for neighbor in neighborhood:
                exposure_slope_in_deg_candidate = (best_exposure_slope_in_deg[0] + neighbor[0], best_exposure_slope_in_deg[1] + neighbor[1])
                exposure_in_deg: float = exposure_slope_in_deg_candidate[0]
                slope_in_deg: float = exposure_slope_in_deg_candidate[1]
                if -180 <= exposure_in_deg <= 180 and 0 <= slope_in_deg <= 180 and exposure_slope_in_deg_candidate not in taboo:
                    taboo.append(exposure_slope_in_deg_candidate)
                    productions_in_Wh = sum(self.powers_W(
                        exposure_slope_in_deg_candidate[0], exposure_slope_in_deg_candidate[1], distance_between_arrays_m, mount_type, error_message))
                    if productions_in_Wh > best_total_production_in_Wh:
                        improvement = True
                        best_exposure_slope_in_deg: tuple[float, float] = exposure_slope_in_deg_candidate
                        best_total_production_in_Wh: float = productions_in_Wh
        return {'exposure_deg': best_exposure_slope_in_deg[0], 'slope_deg': best_exposure_slope_in_deg[1], 'best_production_kWh': best_total_production_in_Wh / 1000, 'initial_slope_deg': initial_slope_deg, 'initial_slope_deg': initial_slope_deg, 'initial_production_kWh': initial_production_Wh / 1000, 'mount_type': mount_type.name, 'distance_between_arrays_m': distance_between_arrays_m}

    def print_month_hour_power_W(self):
        powers_W = self.powers_W()
        print('total electricity production: %.0fkWh' % (sum(powers_W)/1000))

        month_hour_occurrences: dict[int, dict[int, int]] = [[0 for j in range(24)] for i in range(12)]
        month_hour_productions_in_Wh: dict[int, dict[int, float]] = [[0 for j in range(24)] for i in range(12)]
        table = prettytable.PrettyTable()
        table.set_style(prettytable.TableStyle.MSWORD_FRIENDLY)
        labels: list[str] = ["month#", "cumul"]
        labels.extend(['%i:00' % i for i in range(24)])
        table.field_names = labels
        for i, dt in enumerate(self.datetimes):
            month_hour_occurrences[dt.month-1][dt.hour] += 1
            month_hour_productions_in_Wh[dt.month-1][dt.hour] += powers_W[i]
        for month in range(12):
            number_of_month_occurrences: int = sum(month_hour_occurrences[month-1])
            if number_of_month_occurrences != 0:
                total: str = '%.fkWh' % round(sum(month_hour_productions_in_Wh[month-1]))
            else:
                total: str = '0'
            month_row = [month, total]
            for hour in range(24):
                if month_hour_occurrences[month][hour] != 0:
                    month_row.append('%g' % round(month_hour_productions_in_Wh[month][hour] / month_hour_occurrences[month][hour]))
                else:
                    month_row.append('0.')
            table.add_row(month_row)
        print('Following PV productions are in Wh:')
        print(table)
