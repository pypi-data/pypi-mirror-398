from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any


@dataclass
class PlotConfig:
    """Typical base configuration for plots."""
    as_png: bool
    file_path: str
    size: tuple[float, float]


class DataProcessor(ABC):
    """
    Base class for data processors.
    A data processor is responsible for processing the
    data before it is rendered in the plot.
    """

    @abstractmethod
    def process_data(self, data: Any, config: PlotConfig) -> Any:
        """
        Process the data before it is rendered in the plot.
        """
        raise NotImplementedError


class PlotRenderer(ABC):
    """
    Base class for plot renderers.
    A plot renderer is responsible for rendering the plot
    on a figure.
    """

    @abstractmethod
    def render_plot(self, fig: Any, data: Any, config: PlotConfig):
        """
        Render the plot on the given figure,
        according to the given configuration.
        """
        raise NotImplementedError


class AxesConfigurator(ABC):
    """
    Base class for axes configurators.
    An axes configurator is responsible for configuring the axes
    of the plot.
    """

    @abstractmethod
    def configure_axes(self, fig: Any, config: PlotConfig):
        """
        Configure the axes of the plot, according to the given configuration.
        """
        raise NotImplementedError

    @abstractmethod
    def create_figure(self, config: PlotConfig) -> Any:
        """
        Create the figure for the plot, according to the given configuration.
        """
        raise NotImplementedError


class FigureSaver(ABC):
    """
    Base class for figure savers.
    A figure saver is responsible for saving the figure
    to the given file path.
    """

    @abstractmethod
    def save_figure(self, fig: Any, config: PlotConfig):
        """
        Save the figure to the given file path,
        according to the given configuration.
        """
        raise NotImplementedError


class Plotter:
    """
    A plotter is responsible for:
    - processing the data
    - creating the figure
    - rendering the plot
    - configuring the axes
    - saving the figure
    according to the given configuration.
    """

    def __init__(self,
                 config: PlotConfig,
                 data_processor: DataProcessor,
                 renderer: PlotRenderer,
                 axes_configurator: AxesConfigurator,
                 figure_saver: FigureSaver):
        """
        Initialize the plotter.
        """

        self._config = config
        self._data_processor = data_processor
        self._renderer = renderer
        self._axes_configurator = axes_configurator
        self._figure_saver = figure_saver

    def plot(self, data: Any):
        """
        Plot the data, according to the given configuration.
        """
        processed_data = self._data_processor.process_data(data, self._config)
        fig = self._axes_configurator.create_figure(self._config)
        self._renderer.render_plot(fig, processed_data, self._config)
        self._axes_configurator.configure_axes(fig, self._config)
        self._figure_saver.save_figure(fig, self._config)
