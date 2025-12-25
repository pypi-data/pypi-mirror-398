"""Utility functions and helper classes for building energy analysis.

.. module:: batem.core.utils

This module provides comprehensive utility functions and helper classes for
building energy analysis, including file path management, data processing,
statistical analysis, visualization, and simulation capabilities. It includes
data averaging, clustering algorithms, time series plotting, and Monte Carlo
simulation tools for building energy analysis workflows.

Classes
-------

.. autosummary::
   :toctree: generated/

   FilePathChecker
   FilePathBuilder
   Averager
   TimeSeriesPlotter
   PlotSaver

Classes Description
-------------------

**FilePathChecker**
    File and folder existence checking utilities.

**FilePathBuilder**
    File path construction and data folder management.

**Averager**
    Data averaging with sliding window and periodic averaging.

**TimeSeriesPlotter**
    Time series visualization and plotting capabilities.

**PlotSaver**
    Figure saving and export utilities.

Key Features
------------

* File path management and data folder organization
* Data averaging with sliding window and periodic (day/month) methods
* Variable clustering using hierarchical clustering algorithms
* Time series visualization with multiple plot types and averaging options
* Monte Carlo simulation for uncertainty analysis and sensitivity studies
* Jupyter notebook environment detection and compatibility
* Statistical analysis and data processing utilities
* Plot export and saving capabilities for figures and visualizations
* Integration with building energy data providers and measurement systems
* Support for various data formats and visualization libraries

The module is designed for building energy analysis, data processing,
and comprehensive utility support in research and practice.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""
from __future__ import annotations
import os
import os.path
import ipywidgets
from random import uniform
from IPython.display import display
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, fcluster
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date, datetime, time
try:
    import tkinter as tk
    from tkinter import ttk
    TKINTER_AVAILABLE = True
except ImportError:
    # Tkinter not available - GUI features will be disabled
    TKINTER_AVAILABLE = False
    tk = None
    ttk = None
import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express
from batem.core.timemg import TimeSeriesMerger
from batem.core.library import Setup
from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.exceptions import ConvergenceWarning
import warnings
import plotly.io as pio

# Suppress ConvergenceWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)


class FilePathChecker:
    """File and folder existence checking utilities for building energy analysis.

    This class provides methods for checking the existence of files and folders
    in the file system, supporting file path validation and directory management
    for building energy analysis workflows.
    """

    def __init__(self) -> None:
        pass

    def is_file_exists(self, file_path: str) -> bool:
        return os.path.isfile(file_path)

    def is_folder_exists(self, folder_path: str) -> bool:
        return os.path.isdir(folder_path)


class FilePathBuilder:
    """File path construction and data folder management for building energy analysis.

    This class provides methods for constructing file paths and managing data folders,
    including automatic folder creation and path validation for building energy
    analysis data organization and file management.
    """

    def __init__(self) -> None:
        pass

    def get_work_folder(self, folder_name: str = 'data') -> str:
        """Get the data folder path. If it does not exist, create it.

        :return: the data folder path
        :rtype: str
        """
        return str(Setup.folder_path(folder_name))

    def get_localizations_file_path(self) -> str:
        """Get the localizations file path.

        :return: the localizations file path
        :rtype: str
        """
        return self.get_work_folder() + 'localizations.json'

    def get_weather_file_path(self, location: str) -> str:
        """Get the weather file path as a json file.

        :return: the weather file path
        :rtype: str
        """
        file_path = os.path.join(self.get_work_folder(), location + '.json')
        return file_path


def in_jupyter() -> bool:
    """Determine whether the code is executed as Python code or in Jupyter

    :return: True is executed in Jupyter, False otherwise.
    :rtype: bool
    """
    from IPython import get_ipython
    if get_ipython().__class__.__name__ != 'NoneType':
        return True
    return False


if in_jupyter():
    # plotly.offline.init_notebook_mode()
    pio.renderers.default = 'plotly_mimetype+notebook'
    # from plotly.offline import iplot
else:
    pio.renderers.default = 'browser'

    # import matplotlib
    # matplotlib.use('tkagg')
    # from matplotlib.backends.backend_tkagg import *  # noqa


def mkdir_if_not_exist(path_name: str) -> str:
    """Create directory structure if it doesn't exist.
    
    If path_name is a file path (contains a filename), extracts the directory
    and creates it. If it's a directory path, creates the directory structure.
    
    :param path_name: Full file path or directory path
    :type path_name: str
    :return: The original path_name
    :rtype: str
    """
    if not path_name:
        return path_name
    
    # Check if path_name is a directory path (ends with / or \)
    is_directory_path = path_name.endswith(('/', '\\'))
    
    if is_directory_path:
        # It's a directory path - create it directly
        dir_path = path_name.rstrip('/\\')
    else:
        # It's a file path - extract the directory
        # Use os.path.dirname which handles both forward and backward slashes correctly
        dir_path = os.path.dirname(path_name)
        # If dirname returns empty or '.', it means path_name is just a filename in current dir
        # In that case, no directory needs to be created
        if not dir_path or dir_path == '.':
            return path_name
    
    # Create directory structure if it doesn't exist
    # Use os.makedirs which creates all intermediate directories
    # exist_ok=True ensures no error if directory already exists
    if dir_path:
        try:
            # Check if it exists before creating to know if we should print
            dir_existed = os.path.isdir(dir_path)
            # Always try to create - exist_ok=True handles the case where it already exists
            os.makedirs(dir_path, exist_ok=True)
            if not dir_existed:
                print("make dir:", dir_path)
        except OSError as e:
            # If directory creation fails, raise a more informative error
            raise OSError(f"Failed to create directory '{dir_path}': {e}") from e
    
    return path_name


def day_averager(datetimes: list[datetime.datetime], vector: list[float], average=True):
    """Compute the average or integration hour-time data to get day data.

    :param average: True to compute an average, False for integration
    :type average: bool
    :param vector: vector of values to be down-sampled
    :return: list of floating numbers
    """
    current_day: int = datetimes[0].day
    day_integrated_vector = list()
    values = list()
    for k in range(len(datetimes)):
        if current_day == datetimes[k].day:
            values.append(vector[k])
        else:
            average_value = sum(values)
            if average:
                average_value = average_value/len(values)
            day_integrated_vector.append(average_value)
            values = list()
        current_day = datetimes[k].day
    return day_integrated_vector


class Averager:
    """Data averaging with sliding window and periodic averaging for building energy analysis.

    This class provides comprehensive data averaging capabilities including sliding
    window averaging and periodic averaging (day/month) for time series data processing
    in building energy analysis workflows.
    """

    def __init__(self, values: list[float]) -> None:
        """Initialize averager with a series of values.

        :param values: the series of values to be averaged
        :type values: list[float]
        """
        self._values: list[float] = values

    def average(self, horizon: int) -> list[float]:
        """compute the average of a series of values considering only the past values of the
        value to be averaged if they exist. If not, the average is computed on the available
        pas horizon

        :param horizon: _description_
        :type horizon: int
        :raises ValueError: _description_
        :return: _description_
        :rtype: list[float]
        """
        _avg_values: list[float] = list()
        for i in range(len(self._values)):
            i_min, i_max = max(0, i - horizon), i
            if i_max > i_min:
                _avg_values.append(
                    sum(self._values[i_min:i_max]) / (i_max - i_min))
            else:
                _avg_values.append(self._values[i])
        return _avg_values

    def day_month_average(self, datetimes: list[datetime], month: bool = False, sum_up: bool = False) -> tuple[list[float], list[int]]:
        """compute the sum or the average value of the current time series group by day or by month

        :param datetimes: the datetimes corresponding to the current time series
        :type datetimes: list[datetime]
        :param month: group by day if True or month otherwise, defaults to False
        :type month: bool, optional
        :param sum_up: compute,the,sum if True or the average otherwise, defaults to False
        :type sum_up: bool, optional
        :return: list of averages-d or summed values, repeated during the same type of period
        :rtype: tuple[list[float], list[int]]
        """
        current_period: int = -1
        accumulator: list[float] = list()
        _periods: list[int] = list()
        _avg_values: list[float] = list()
        for k, dt in enumerate(datetimes):
            if current_period == -1:  # initialization
                current_period = dt.day if not month else dt.month
                accumulator.append(self._values[k])
            else:
                if (not month and dt.day == current_period) or (month and dt.month == current_period):
                    accumulator.append(self._values[k])  # accumulating
                else:
                    if sum_up:
                        avg: float = sum(accumulator)
                    else:
                        avg: float = sum(accumulator) / len(accumulator)
                    _periods.extend(
                        [current_period for _ in range(len(accumulator))])
                    _avg_values.extend([avg for _ in range(len(accumulator))])
                    current_period = dt.day if not month else dt.month
                    accumulator = [self._values[k]]
        if sum_up:
            avg: float = sum(accumulator)
        else:
            avg: float = sum(accumulator) / len(accumulator)
        _periods.extend([current_period for _ in range(len(accumulator))])
        _avg_values.extend([avg for _ in range(len(accumulator))])
        return _avg_values, _periods

    def inertia_filter(self, num: list[float] = [0.019686971644799107, 0.014954617818522536, -0.02795458838964217], den: list[float] = [1, -1.393950, 0.400637], initial_values: list[float] = None) -> list[float]:
        """A realistic transfer function to represent standard inertia

        :param num: _description_, defaults to [0.019686971644799107, 0.014954617818522536, -0.02795458838964217]
        :type num: list[float], optional
        :param den: _description_, defaults to [1, -1.393950, 0.400637]
        :type den: list[float], optional
        :param initial_values: _description_, defaults to None
        :type initial_values: list[float], optional
        :return: _description_
        :rtype: list[float]
        """
        init: int = max(len(num), len(den))
        coef0: float = den[0]
        den = [- den[i] / coef0 for i in range(1, init)]
        num = [v / coef0 for v in num]
        if initial_values is None:
            _avg_values: list[float] = [self._values[k] for k in range(init)]
        else:
            _avg_values: list[float] = [initial_values[k] for k in range(init)]
        for k in range(init, len(self._values)):
            val = 0
            for i in range(len(den)):
                val += den[i] * _avg_values[k-i-1]
            for i in range(len(num)):
                val += num[i] * self._values[k-i]
            _avg_values.append(val)
        return _avg_values


def auto_kmeans(X, kmin=1, kmax=6, metric='range_distance', random_state=0, sensitivity=0):
    # Handle edge case: if X has fewer than 2 elements, return single cluster
    if len(X) < 2:
        return np.zeros(len(X), dtype=int), 1

    # Adjust kmax to not exceed the number of data points
    kmax = min(kmax, len(X))

    # If kmax < kmin after adjustment, set kmin to kmax
    if kmax < kmin:
        kmin = kmax

    best_k = kmin
    best_score = -1
    best_labels = None

    # Precompute pairwise distances (needed for custom metric)
    if metric == 'range_distance':
        D = pairwise_distances(X, metric=range_distance)
    else:
        D = pairwise_distances(X, metric=metric)

    if np.max(D) == 0:
        return np.zeros(len(X), dtype=int), 1

    for k in range(kmin, kmax + 1):
        # Skip if k is greater than the number of data points
        if k > len(X):
            continue

        model = KMeans(init='k-means++', n_clusters=k,
                       random_state=random_state, n_init='auto').fit(X)
        labels = model.labels_

        # Silhouette score with precomputed distance matrix
        if len(set(labels)) < 2:
            continue  # silhouette score not defined for one cluster

        # For very small datasets, silhouette score might fail
        try:
            score = silhouette_score(D, labels, metric='precomputed')
        except ValueError:
            # If silhouette score fails, use a simple distance-based score
            if len(set(labels)) == 2:
                # For 2 clusters, use the distance between cluster centers
                cluster_centers = []
                for cluster_id in set(labels):
                    cluster_points = X[labels == cluster_id]
                    if len(cluster_points) > 0:
                        cluster_centers.append(np.mean(cluster_points, axis=0))
                if len(cluster_centers) == 2:
                    score = np.linalg.norm(
                        cluster_centers[0] - cluster_centers[1])
                else:
                    score = 0
            else:
                score = 0

        if score > best_score - sensitivity:
            best_score = score
            best_k = k
            best_labels = labels

    return best_labels, best_k


def range_distance(range_1: list[float], range_2: list[float]) -> float:
    """Calculate distance between two ranges based on overlap."""

    # range_1 = (np.nanmin(data_1), np.nanmax(data_1))
    # range_2 = (np.nanmin(data_2), np.nanmax(data_2))
    delta_1 = abs(range_1[0] - range_2[0])
    delta_2 = abs(range_1[1] - range_2[1])
    range_1_2 = max(range_1[1], range_2[1]) - min(range_1[0], range_2[0])
    # width_1_2 = range_1_2[1] - range_1_2[0]
    if range_1_2 != 0:
        return max((delta_1 / range_1_2, delta_2 / range_1_2))
    else:
        return 0
    # width_1_2 = range_1_2[1] - range_1_2[0]
    # if width_1_2 != 0:
    #     return 1 - max((width_1 / width_1_2, width_2 / width_1_2))
    # else:
    #     return 0


def cluster_variables(variable_data: dict[str, list[float]], threshold: float = .7) -> list[list[str]]:
    variables = list(variable_data.keys())
    
    # Handle empty case: no variables to cluster
    if len(variables) == 0:
        return []
    
    # Handle single variable case: no clustering needed
    if len(variables) == 1:
        return [variables]
    
    extrema_data: np.ndarray = np.array([[np.nanmin(variable_data[v]), np.nanmax(variable_data[v])] for v in variables])

    pairwise_distances = pdist(extrema_data, metric=range_distance)  # Compute the condensed distance matrix (1D array)
    Z = linkage(pairwise_distances, method='complete')  # or 'complete', 'average','single', etc.
    labels = fcluster(Z, t=threshold, criterion='distance')
    groups: list[list[str]] = [[] for _ in range(np.max(labels))]
    for group_id in range(np.max(labels)):
        for i, label in enumerate(labels):
            if label == group_id + 1:
                groups[group_id].append(variables[i])
    return groups


class TimeSeriesPlotter:
    """Time series visualization and plotting capabilities for building energy analysis.

    This class provides comprehensive time series visualization and plotting capabilities
    with multiple plot types, averaging options, and interactive features for building
    energy analysis data visualization and presentation.
    """

    def __init__(self, variable_values: dict[str, list[float]], datetimes: list[datetime] | list[date] = None, units: dict[str, str] = dict[str, str](), all: bool = False, plot_type: str = None, averager: str = None, title: str = '', threshold: float = .7) -> None:
        """Initialize the time series plotter.

        :param variable_values: Mapping from variable name to its time series values. Special keys like 'datetime', 'epochtimems' or 'stringdate' are ignored for plotting data but can carry time information.
        :type variable_values: dict[str, list[float]]
        :param datetimes: The timestamps corresponding to the time series. Can be a list of :class:`datetime` or :class:`date`. If a list of dates is provided, midnight timings are assumed. Must match the length of the provided series.
        :type datetimes: list[datetime] | list[date]
        :param units: Optional mapping from variable name to its unit string used for labels.
        :type units: dict[str, str]
        :param all: If True, plot all variables directly without interactive selection.
        :type all: bool
        :param plot_type: Type of plot to display: 'timeplot', 'heatmap' or None to allow both.
        :type plot_type: str | None
        :param averager: Averaging specification such as '- hour', 'avg day', 'sum month', etc.
        :type averager: str | None
        :param title: Title prefix used in plots.
        :type title: str
        :param threshold: Distance threshold in [0, 1] used to cluster variables for multi-axis plotting.
        :type threshold: float
        :raises ValueError: If datetimes are missing or sizes are inconsistent with the data series.
        """
        self._variable_names = list()
        self._datetimes = datetimes
        self._variable_min_max: dict[tuple[float, float]] = dict()
        self._variable_values: dict[str, list[float]] = dict()
        self._units: dict[str, str] = units
        self._threshold: float = threshold
        averager_types: list[str] = ['- hour', 'avg day', 'avg week', 'avg month', 'avg year', 'sum day', 'sum week',
                                     'sum month', 'sum year', 'max day', 'max week', 'max month', 'max year', 'min day', 'min week', 'min month', 'min year']
        self._all: bool = all
        self._plot_type: str = plot_type
        self._averager: str = averager
        self._title: str = title

        number_of_values: int = None
        for variable_name in variable_values:
            if variable_name != 'datetime' and variable_name != 'epochtimems' and variable_name != 'stringdate':
                is_all_none: bool = False
                for v in variable_values[variable_name]:
                    is_all_none: bool = is_all_none or (v is None)
                if not is_all_none:
                    self._variable_values[variable_name] = variable_values[variable_name]
                    self._variable_min_max[variable_name] = self.minmax(
                        [variable_name])
                    self._variable_names.append(variable_name)
            elif variable_name == 'datetime' and self._datetimes is None:
                self._datetimes = datetimes
            if number_of_values is None:
                number_of_values = len(variable_values[variable_name])
            elif number_of_values != len(variable_values[variable_name]):
                raise ValueError('Variable %s has not the right size (%i instead of %i)' % (
                    variable_name, len(variable_values[variable_name]), number_of_values))
        if self._datetimes is None:
            raise ValueError('datetimes must be provided')
        if number_of_values is None:
            raise ValueError('Cannot plot: one or more variables are empty or None')
        if len(self._datetimes) != number_of_values:
            raise ValueError('datetimes do not match data time series (%i values instead of %i)' % (
                len(self._datetimes), number_of_values))
        if type(datetimes[0]) is date:
            self._datetimes: list[datetime] = [
                datetime.combine(d, time()) for d in datetimes]
        self.output = ipywidgets.Output()
        
        # Configure plotly renderer
        if not in_jupyter():
            # For non-Jupyter environments, save HTML files and optionally open in browser
            pio.renderers.default = "browser"
        
        if self._all:
            for i, variable_name in enumerate(self._variable_names):
                displayed_variable_name = variable_name
                if variable_name in self._units:
                    displayed_variable_name += ' in %s' % self._units[variable_name]
            selected_variable_values: dict[str,
                                           list[float]] = self._variable_values
            print('Averager: %s' % self._averager)
            for selected_variable_name in self._variable_values:
                operation, period = self._averager.split()
                selected_variable_values[selected_variable_name] = TimeSeriesMerger(
                    self._datetimes, values=self._variable_values[selected_variable_name], group_by=period)(operation)
            if self._plot_type == 'heatmap':
                self._plot_heatmap()
            elif self._plot_type == 'piechart':
                self._plot_pie_chart()
            else:
                self._plot_time_series()
        elif not in_jupyter():  # tkinter selector
            # Check if tkinter is available
            if not TKINTER_AVAILABLE:
                print("Tkinter not available. Falling back to non-interactive plotting...")
                # Fallback: just plot all variables without GUI
                self._all = True
                selected_variable_values: dict[str, list[float]] = self._variable_values
                print('Averager: %s' % self._averager)
                for selected_variable_name in self._variable_values:
                    operation, period = self._averager.split()
                    selected_variable_values[selected_variable_name] = TimeSeriesMerger(
                        self._datetimes, values=self._variable_values[selected_variable_name], group_by=period)(operation)
                if self._plot_type == 'heatmap':
                    self._plot_heatmap()
                elif self._plot_type == 'piechart':
                    self._plot_pie_chart()
                else:
                    self._plot_time_series()
                return

            # Avoid Tkinter crashes on macOS by using non-interactive backend
            try:
                root_window = tk.Tk()
            except Exception as e:
                print(f"Tkinter failed to initialize: {e}")
                print("Falling back to non-interactive plotting...")
                # Fallback: just plot all variables without GUI
                self._all = True
                selected_variable_values: dict[str, list[float]] = self._variable_values
                print('Averager: %s' % self._averager)
                for selected_variable_name in self._variable_values:
                    operation, period = self._averager.split()
                    selected_variable_values[selected_variable_name] = TimeSeriesMerger(
                        self._datetimes, values=self._variable_values[selected_variable_name], group_by=period)(operation)
                if self._plot_type == 'heatmap':
                    self._plot_heatmap()
                elif self._plot_type == 'piechart':
                    self._plot_pie_chart()
                else:
                    self._plot_time_series()
                return
            self.tk_int_vars = [  # : list[tk.IntVar]
                tk.IntVar(root_window, value=0) for variable_name in self._variable_names]
            self.tk_averager_var = tk.StringVar(
                root_window, value=averager if averager is not None else '- hour')
            root_window.title('variable plotter')
            root_window.protocol("WM_DELETE_WINDOW", exit)
            control_frame = ttk.Frame(root_window)
            control_frame.grid(row=0, column=0, sticky="nw")
            timeplot_button = ttk.Button(
                control_frame, text='timeplot', command=self._plot_time_series)
            timeplot_button.grid(row=0, column=0, sticky="wn")
            heatmap_button = ttk.Button(
                control_frame, text='heatmap', command=self._plot_heatmap)
            heatmap_button.grid(row=0, column=1, sticky="wn")
            piechart_button = ttk.Button(
                control_frame, text='piechart', command=self._plot_pie_chart)
            piechart_button.grid(row=0, column=2, sticky="wn")
            if self._plot_type == 'timeplot':
                heatmap_button.config(state="disabled")
                piechart_button.config(state="normal")
            if self._plot_type == 'heatmap':
                timeplot_button.config(state="disabled")
                piechart_button.config(state="normal")
            if self._plot_type == 'piechart':
                timeplot_button.config(state="normal")
                heatmap_button.config(state="normal")
                piechart_button.config(state="disabled")
            averager_combo = ttk.Combobox(
                control_frame, textvariable=self.tk_averager_var, values=averager_types)
            averager_combo.grid(row=0, column=3, sticky="wn", pady=4)
            if averager is not None:
                averager_combo.config(state="disabled")
            
            # Add filter frame
            filter_frame = ttk.Frame(root_window)
            filter_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
            filter_label = ttk.Label(filter_frame, text="Filter:")
            filter_label.grid(row=0, column=0, sticky="w")
            self.tk_filter_var = tk.StringVar(root_window, value='')
            filter_entry = ttk.Entry(filter_frame, textvariable=self.tk_filter_var, width=40)
            filter_entry.grid(row=0, column=1, sticky="ew", padx=5)
            filter_frame.grid_columnconfigure(1, weight=1)
            
            selection_frame = ttk.Frame(root_window)
            selection_frame.grid(row=2, column=0, sticky="nswe")
            # Configure the grid to expand the frame
            root_window.grid_columnconfigure(0, weight=1)
            root_window.grid_rowconfigure(2, weight=1)
            selection_canvas = tk.Canvas(selection_frame)
            selection_canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar = ttk.Scrollbar(
                selection_frame, orient="vertical", command=selection_canvas.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            selection_canvas.configure(yscrollcommand=scrollbar.set)
            # Configure the frame to expand with the canvas
            selection_frame.grid_columnconfigure(0, weight=1)
            selection_frame.grid_rowconfigure(0, weight=1)
            # Create a frame inside the canvas for the widgets
            checkboxes_frame = ttk.Frame(selection_canvas)
            canvas_window = selection_canvas.create_window(
                (0, 0), window=checkboxes_frame, anchor="nw")
            
            # Store all variable names and checkboxes for filtering
            self._all_variable_names = [variable_name for variable_name in self._variable_names]
            self.tk_checkboxes = []  # Store references to checkboxes
            
            for i, variable_name in enumerate(self._variable_names):
                tk_int_var = tk.IntVar(root_window, value=0)
                self.tk_int_vars.append(tk_int_var)
                displayed_variable_name = variable_name
                if variable_name in self._units:
                    displayed_variable_name += ' in %s' % self._units[variable_name]
                checkbox = ttk.Checkbutton(checkboxes_frame, text=displayed_variable_name,
                                variable=self.tk_int_vars[i], offvalue=0)
                checkbox.grid(row=i, column=0, sticky="w", padx=5, pady=2)
                self.tk_checkboxes.append((checkbox, variable_name))
            
            # Function to filter checkboxes based on filter text
            def on_filter_change(*args):
                filter_text = self.tk_filter_var.get().lower()
                visible_row = 0
                for checkbox, variable_name in self.tk_checkboxes:
                    if filter_text == '' or filter_text in variable_name.lower():
                        # Show this checkbox
                        checkbox.grid(row=visible_row, column=0, sticky="w", padx=5, pady=2)
                        visible_row += 1
                    else:
                        # Hide this checkbox
                        checkbox.grid_forget()
                # Update scroll region
                checkboxes_frame.update_idletasks()
                selection_canvas.configure(scrollregion=selection_canvas.bbox("all"))
            
            # Attach filter function to the filter entry
            self.tk_filter_var.trace('w', on_filter_change)
            # Update the canvas scroll region after adding all widgets
            checkboxes_frame.update_idletasks()
            selection_canvas.configure(scrollregion=selection_canvas.bbox("all"))
            # Bind configure event to update scroll region dynamically
            checkboxes_frame.bind("<Configure>", lambda event: selection_canvas.configure(
                scrollregion=selection_canvas.bbox("all")))
            root_window.maxsize(root_window.winfo_width(),
                                root_window.winfo_screenheight())
            root_window.geometry(
                str(root_window.winfo_width()) + "x" + str(root_window.winfo_screenheight()))
            root_window.mainloop()
        else:  # in jupyter
            # Store all variable names for filtering
            self._all_variable_names = [variable_name for variable_name in self._variable_names]
            
            # Create filter text input
            self.filter_text = ipywidgets.Text(
                value='',
                placeholder='Filter variables...',
                description='Filter:',
                disabled=False
            )
            
            # Create variable selector
            self.variable_selector = ipywidgets.SelectMultiple(
                options=self._all_variable_names,
                description='Variables',
                disable=False,
                rows=15  # Show more rows for better visibility
            )
            
            # Function to filter variables based on text input
            def on_filter_change(change):
                filter_text = change['new'].lower()
                if filter_text == '':
                    # No filter - show all variables
                    filtered_vars = self._all_variable_names
                else:
                    # Filter variables that contain the text
                    filtered_vars = [var for var in self._all_variable_names if filter_text in var.lower()]
                
                # Update the selector options while preserving current selection
                current_selection = list(self.variable_selector.value)
                self.variable_selector.options = filtered_vars
                # Restore selection for variables that are still visible
                valid_selection = [var for var in current_selection if var in filtered_vars]
                self.variable_selector.value = tuple(valid_selection)
            
            # Attach the filter function to the text widget
            self.filter_text.observe(on_filter_change, names='value')
            
            if averager is None:
                self._averager_selector = ipywidgets.Select(
                    value='- hour', options=averager_types, disabled=False, description='Averager')
            else:
                self._averager_selector = ipywidgets.Select(
                    value=averager, options=averager_types, disabled=True, description='Averager')

            timeplot_button, heatmap_button = None, None
            piechart_button = None
            if self._plot_type == 'timeplot':  # timeplot
                timeplot_button = ipywidgets.Button(description='timeplot')
                heatmap_button = ipywidgets.Button(
                    description='heatmap', disabled=True)
            if self._plot_type == 'heatmap':
                timeplot_button = ipywidgets.Button(
                    description='timeplot', disabled=True)
                heatmap_button = ipywidgets.Button(description='heatmap')
            if self._plot_type == 'piechart':
                timeplot_button = ipywidgets.Button(description='timeplot', disabled=True)
                heatmap_button = ipywidgets.Button(description='heatmap', disabled=True)
                piechart_button = ipywidgets.Button(description='piechart')
            else:  # both or other
                timeplot_button = ipywidgets.Button(description='timeplot')
                heatmap_button = ipywidgets.Button(description='heatmap')
                # Ensure piechart button is always defined to avoid UnboundLocalError
                piechart_button = ipywidgets.Button(description='piechart')

            button_box = ipywidgets.VBox([timeplot_button, heatmap_button, piechart_button])
            
            # Create a VBox for the filter and variable selector
            variable_selection_box = ipywidgets.VBox([self.filter_text, self.variable_selector])
            
            control_box = ipywidgets.HBox(
                [variable_selection_box, self._averager_selector, button_box])
            main_box = ipywidgets.VBox([control_box, self.output])
            display(main_box)

            def on_timeplot_button_clicked(timeplot_button):
                print('Timeplot coming...')
                self.output.clear_output()
                with self.output:
                    self._plot_time_series()
                self.variable_selector.value = ()
            timeplot_button.on_click(on_timeplot_button_clicked)

            def on_heatmap_button_clicked(heatmap_button):
                print('Heatmap coming...')
                self.output.clear_output()
                with self.output:
                    self._plot_heatmap()
                self.variable_selector.value = ()
            heatmap_button.on_click(on_heatmap_button_clicked)

            def on_piechart_button_clicked(piechart_button):
                print('Pie chart coming...')
                self.output.clear_output()
                with self.output:
                    self._plot_pie_chart()
                self.variable_selector.value = ()
            piechart_button.on_click(on_piechart_button_clicked)

    def minmax(self, variables: list[str]) -> tuple[float, float]:
        if len(variables) == 0:
            raise ValueError('No variables provided')
        min_value: float = min(
            min(self._variable_values[v]) for v in variables)
        max_value: float = max(
            max(self._variable_values[v]) for v in variables)
        return (min_value, max_value)

    def _plot_pie_chart(self) -> None:
        selected_variable_values: dict[str, list[float]] = self._get_selected_variable_values()
        if len(selected_variable_values) < 1:
            print('Please select at least one variable for the pie chart')
            return

        # Get averager/merger setting (default to 'sum' if None)
        if self._averager is None:
            merger = 'sum'
        else:
            merger: str = self._averager.split(' ')[0]

        # Convert dict_keys to list for plotly compatibility
        labels = list(selected_variable_values.keys())

        if merger == '-' or merger == 'sum':
            values = [sum(_) for _ in selected_variable_values.values()]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.show()
            return
        if merger == 'avg':
            values = [sum(_)/len(_) for _ in selected_variable_values.values()]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.show()
            return
        if merger == 'max':
            values = [max(_) for _ in selected_variable_values.values()]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.show()
            return
        if merger == 'min':
            values = [min(_) for _ in selected_variable_values.values()]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
            fig.show()
            return
        # Default: sum
        values = [sum(_) for _ in selected_variable_values.values()]
        fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
        fig.show()

    # # Create pie chart of heat losses breakdown (summer period)
    # dt_hours = 1.0  # 1 hour time step
    # loss_components: dict[str, float] = {
    #     'Inlet water': sum(dp_short.series('P_inlet_water_kW#short')) * dt_hours,
    #     'Precipitation': sum(dp_short.series('P_precipitation_kW#short')) * dt_hours,
    #     'Radiation (net)': sum(dp_short.series('P_radiation_net_kW#short')) * dt_hours,
    #     'Walls & Floor (insulated)': sum(dp_short.series('P_walls_floor_kW#short')) * dt_hours,
    #     'Evaporation': sum(dp_short.series('P_evaporation_kW#short')) * dt_hours,
    #     'Surface convection': sum(dp_short.series('P_surface_convection_kW#short')) * dt_hours,
    # }

    # Filter out zero or negative values for pie chart
    # loss_components = {k: v for k, v in loss_components.items() if v > 0}

    # fig = go.Figure(data=[go.Pie(
    #     labels=list(loss_components.keys()),
    #     values=list(loss_components.values()),
    #     textinfo='label+percent',
    #     hovertemplate='<b>%{label}</b><br>%{value:.1f} kWh<br>%{percent}<extra></extra>'
    # )])

    # insulation_info = f"With {pool_short.e_concrete*100:.0f}cm concrete + {pool_short.e_insulation*100:.0f}cm polystyrene insulation"
    # fig.update_layout(
    #     title=f'Heat Losses Breakdown - Summer Period (June-August)<br>{insulation_info}<br>Total: {sum(loss_components.values()):.0f} kWh',
    #     showlegend=True
    # )
    # fig.show()

    def _plot_heatmap(self) -> None:
        """Versatile method for plotting registered known variables. it detests and adapt the way of plotting to the current context: invoked from Python or from Jupyter. It can plot a heatmap or curves and if variables to be plotted are given, the plot is displayed without opening the selector of variables.

        :param heatmap: True for a heatmap and False for regular curves, defaults to False
        :type heatmap: bool, optional
        """
        selected_variable_values: dict[str, list[float]
                                       ] = self._get_selected_variable_values()
        normalized_values: list[list[float]] = list()
        displayed_variable_names: list[str] = list()
        for variable_name in selected_variable_values:
            normalized_values.append([100*(selected_variable_values[variable_name][j]-self._variable_min_max[variable_name][0]) / (self._variable_min_max[variable_name][1] - self._variable_min_max[variable_name]
                                     [0]) if self._variable_min_max[variable_name][1] != self._variable_min_max[variable_name][0] else 0 for j in range(len(selected_variable_values[variable_name]))])
            displayed_variable_name = '%s (%g→%g' % (
                variable_name, self._variable_min_max[variable_name][0], self._variable_min_max[variable_name][1])
            if variable_name in self._units:
                displayed_variable_name += self._units[variable_name] + ')'
            displayed_variable_names.append(displayed_variable_name)
        if len(normalized_values) > 0:
            fig = plotly.express.imshow(normalized_values, labels=dict(x="time", y='%s Averager: %s' % (self._title, self._averager),
                                        color="min/max normalization"), x=self._datetimes, y=displayed_variable_names, height=1000)
            fig.layout.coloraxis.showscale = True
            fig.update_xaxes(side="top")
            # Use non-interactive backend to avoid Tkinter crashes on macOS
            try:
                # Set renderer to browser for non-Jupyter environments
                if not in_jupyter():
                    pio.renderers.default = "browser"
                fig.show()
            except Exception as e:
                # Fallback: save to HTML file instead
                print(f"Plot display failed ({type(e).__name__}), saving to HTML file instead")
                fig.write_html("timeseries_heatmap.html")
                print("Plot saved to timeseries_heatmap.html")

    def _plot_time_series(self) -> None:
        """Use to plot curve using plotly library

        :param int_vars: reference to the variable to be plotted
        :type: list[int]
        """
        selected_variable_values: dict[str, list[float]] = self._get_selected_variable_values()
        if len(selected_variable_values) == 1:
            fig: go.Figure = make_subplots(rows=1, cols=1, shared_xaxes=True, y_title='%s Averager: %s' % (self._title, self._averager))
            fig.add_trace(go.Scatter(x=self._datetimes, y=selected_variable_values[list(selected_variable_values.keys())[
                          0]], name=list(selected_variable_values.keys())[0], showlegend=True, line_shape='hv'), row=1, col=1)
            # Use notebook renderer for Jupyter compatibility
            try:
                # Set renderer to browser for non-Jupyter environments
                if not in_jupyter():
                    pio.renderers.default = "browser"
                fig.show()
            except Exception as e:
                # Fallback: save to HTML file instead
                print(f"Plot display failed ({type(e).__name__}: {e}), saving to HTML file instead")
                fig.write_html("timeseries_plot.html")
                print("Plot saved to timeseries_plot.html")
            return
        variable_groups: list[list[str]] = cluster_variables(selected_variable_values, threshold=self._threshold)

        if len(variable_groups) > 0:
            fig = make_subplots(rows=len(variable_groups), cols=1, shared_xaxes=True,
                                y_title='%s Averager: %s' % (self._title, self._averager))
            for i, group in enumerate(variable_groups):
                for group_variable in group:
                    displayed_variable_name: str = group_variable
                    if group_variable in self._units:
                        displayed_variable_name += ' in %s' % (
                            self._units[group_variable],)
                    displayed_variable_name += ' (disp:%i)' % (i+1,)
                    fig.add_trace(go.Scatter(x=self._datetimes, y=selected_variable_values[group_variable],
                                  name=displayed_variable_name, showlegend=True, line_shape='hv'), row=1+i, col=1)
            # Use notebook renderer for Jupyter compatibility
            try:
                # Set renderer to browser for non-Jupyter environments
                if not in_jupyter():
                    pio.renderers.default = "browser"
                fig.show()
            except Exception as e:
                # Fallback: save to HTML file instead
                print(f"Plot display failed ({type(e).__name__}: {e}), saving to HTML file instead")
                fig.write_html("timeseries_plot.html")
                print("Plot saved to timeseries_plot.html")

    def _get_selected_variable_values(self) -> dict[str, list[float]]:
        if self._all:
            return self._variable_values
        selected_variable_values: dict[str, list[float]] = dict()
        if in_jupyter():  # in jupyter
            print('Averager: %s' % self._averager_selector.value)
            selected_variable_names = self.variable_selector.value
            operation, period = self._averager_selector.value.split()
        else:
            selected_variable_names = list()
            for i in range(len(self.tk_int_vars)):
                if self.tk_int_vars[i].get():
                    selected_variable_names.append(self._variable_names[i])
                    operation, period = self.tk_averager_var.get().split()
                self.tk_int_vars[i].set(0)
        for selected_variable_name in selected_variable_names:
            if operation == '-' or period == 'hour':
                selected_variable_values[selected_variable_name] = self._variable_values[selected_variable_name]
            else:
                selected_variable_values[selected_variable_name] = TimeSeriesMerger(
                    self._datetimes, values=self._variable_values[selected_variable_name], group_by=period)(operation)

        return selected_variable_values


class PlotSaver:
    """Figure saving and export utilities for building energy analysis.

    This class provides functionality for saving and exporting figures containing
    regular curves and plots into various file formats (PNG, etc.) for building
    energy analysis visualization and reporting.
    """

    def __init__(self, datetimes: list[datetime], data: dict[str, list[float]]) -> None:
        """Initialize the saver with an independent variable set

        :param datetimes: the list of datetimes
        :type datetimes: list[datetime]
        :param data: the dictionary with variable names as keys and their values as lists of floats
        :type data: dict[str, list[float]]
        """
        self.datetimes: list[datetime] = datetimes
        self.data: dict[str, list[float]] = data
        self.starting_stringdatetime: str = datetimes[0].strftime(
            '%d/%m/%Y %H:%M')
        self.ending_stringdatetime: str = datetimes[-1].strftime(
            '%d/%m/%Y %H:%M')

    def time_plot(self, variable_names: list[str], filename: str) -> None:
        """
        generate and save a time plot
        :param variable_names: names of the variables to be plot
        :type variable_names: list[str]
        :param filename: the file name
        :type filename: str
        """
        styles: tuple[str, str, str, str] = ('-', '--', '-.', ':')
        linewidths = (3.0, 2.5, 2.5, 1.5, 1.0, 0.5, 0.25)
        figure, axes = plt.subplots()
        axes.set_title('from %s to %s' % (
            self.starting_stringdatetime, self.ending_stringdatetime))
        text_legends = list()
        time_data: list[datetime] = self.datetimes
        if len(time_data) > 1:
            sample_time = time_data[-1] - time_data[-2]
            time_data.append(time_data[-1] + sample_time)
        for i in range(len(variable_names)):
            style = styles[i % len(styles)]
            linewidth = linewidths[i // len(styles) % len(linewidths)]
            variable_name: str = variable_names[i]
            variable_data: list[float] = self.data[variable_name]
            if len(time_data) > 1:
                variable_data.append(variable_data[-1])
            axes.step(time_data, variable_data, linewidth=linewidth,
                      linestyle=style, where='post')
            axes.set_xlim([time_data[0], time_data[-1]])
            text_legends.append(variable_names[i])
        axes.legend(text_legends, loc=0)
        axes.xaxis.set_minor_locator(mdates.DayLocator())
        axes.fmt_xdata = mdates.DateFormatter('%d/%m/%Y %H:%M')
        plt.gcf().autofmt_xdate()
        axes.grid(True)
        plt.savefig(filename+'.png')


def monte_carlo(function: callable, precision: float = 0.01, n_draws: int = 10000, **variable_values: dict[str, float | tuple[float, float]]):
    found_values = list()
    for i in range(n_draws):
        name_values: dict[str, float] = dict()
        for v in variable_values:
            variable_value: float = variable_values[v]
            if type(variable_value) is int or type(variable_value) is float:
                name_values[v] = variable_value
            else:
                name_values[v] = uniform(
                    a=variable_value[0], b=variable_value[1])
        PMV: float = function(**name_values)
        if PMV < precision:
            found_values.append(name_values)
    return found_values
