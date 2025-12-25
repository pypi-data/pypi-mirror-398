"""Thermal and indoor air quality comfort assessment module for building energy analysis.

.. module:: batem.core.comfort

This module provides comprehensive tools for evaluating human comfort in indoor environments
based on established international standards and methodologies. It implements various comfort
indices and assessment methods used in building energy analysis, thermal comfort evaluation,
and indoor air quality monitoring.

Classes
-------

.. autosummary::
   :toctree: generated/

   OutdoorTemperatureIndices
   PMVcalculator
   AdaptiveComfort

Classes Description
-------------------

**OutdoorTemperatureIndices**
    Heat index calculations based on NOAA equations for outdoor thermal comfort assessment.

**PMVcalculator**
    Predicted Mean Vote (PMV) calculations following ISO 7730 standard for thermal comfort evaluation.

**AdaptiveComfort**
    Adaptive thermal comfort model based on outdoor temperature and occupancy patterns.

Key Features
------------

* Heat index calculations using NOAA equations for outdoor thermal comfort
* PMV/PPD calculations following ISO 7730 standard for indoor thermal comfort
* Adaptive comfort model implementation for naturally ventilated buildings
* ICONE indicator for indoor air quality and confinement assessment
* Psychrometric chart visualization using Givoni diagrams
* Statistical analysis tools for comfort data during occupancy periods
* Support for various comfort parameters (temperature, humidity, air speed, clothing, metabolism)

The module is designed for building energy analysis, thermal comfort studies, and indoor
environmental quality assessment in both residential and commercial buildings.

.. note::
    This module optionally uses psychrochart for psychrometric chart visualization.

:Author: stephane.ploix@g-scop.grenoble-inp.fr
:License: GNU General Public License v3.0
"""
from math import sqrt, exp
import matplotlib.pyplot as plt
from math import log10, ceil, floor
from batem.core.utils import Averager

try:
    from psychrochart import PsychroChart
    HAS_PSYCHROCHART = True
except ImportError:
    HAS_PSYCHROCHART = False
    # Fallback for when psychrochart is not available

    class PsychroChart:
        @staticmethod
        def create():
            return None


def plot_givoni(temperature_deg: list[float], relative_humidity_percent: list[float], chart_name: str = '') -> None:
    """Plot a psychrometric (Givoni) diagram with temperature and humidity data.

    Creates a psychrometric chart showing the relationship between dry bulb
    temperature and relative humidity, useful for thermal comfort analysis.

    :param temperature_deg: Dry bulb temperatures in degrees Celsius.
    :type temperature_deg: list[float]
    :param relative_humidity_percent: Relative humidity values as percentages (0-100).
    :type relative_humidity_percent: list[float]
    :param chart_name: Optional name for the chart, defaults to ''.
    :type chart_name: str, optional
    :raises ImportError: Raised if psychrochart module is not available.
    """
    if not HAS_PSYCHROCHART:
        raise ImportError("psychrochart module is required for Givoni diagram. Install it with: pip install psychrochart")
    chart: PsychroChart = PsychroChart.create()
    plt.figure()
    axes = chart.plot(ax=plt.gca())
    axes.scatter(temperature_deg, [1000*h for h in relative_humidity_percent], marker='o', alpha=.1)
    axes.set_title("Psychrometric diagram: %s" % chart_name)
    plt.show()


class OutdoorTemperatureIndices:
    """Static methods for calculating outdoor temperature comfort indices.

    This class provides methods for computing various "feels like" temperature
    indices based on National Oceanic and Atmospheric Administration (NOAA)
    equations. These indices account for the combined effects of temperature,
    humidity, and wind speed on human thermal perception.
    """

    @staticmethod
    def heat_index(temperature_celsius: float, relative_humidity: float) -> float:
        """Calculate Heat Index (feels like temperature) based on NOAA equation.

        Heat Index or humiture is an index that combines air temperature and
        relative humidity to determine the human-perceived equivalent temperature.
        The full Rothfusz regression formula is used when the average temperature
        is >= 80°F (approximately 27°C), otherwise a simplified formula is applied.

        :param temperature_celsius: Air temperature in degrees Celsius.
        :type temperature_celsius: float
        :param relative_humidity: Relative humidity as a percentage (0-100).
        :type relative_humidity: float
        :return: Heat index in degrees Celsius.
        :rtype: float

        .. note::
            Heat Index is most accurate when temperature > 27°C and
            relative_humidity > 40%.

        References:
            - `Wikipedia: Heat Index <https://en.wikipedia.org/wiki/Heat_index>`_
            - `NOAA Heat Index Equation <http://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml>`_
            - `Weathermetrics R Package <https://github.com/geanders/weathermetrics/blob/master/R/heat_index.R>`_
        """

        c1: float = -8.78469475556  # SI units (Celsius)
        c2: float = 1.61139411
        c3: float = 2.33854883889
        c4: float = -0.14611605
        c5: float = -0.012308094
        c6: float = -0.0164248277778
        c7: float = 0.002211732
        c8: float = 0.00072546
        c9: float = -0.000003582

        temperature_fahrenheit: float = (temperature_celsius * 9/5) + 32
        heat_index_fahrenheit: float = 0.5 * (temperature_fahrenheit + 61 + (temperature_fahrenheit - 68) * 1.2 + relative_humidity * 0.094)
        temperature_fahrenheit_avg: float = (heat_index_fahrenheit + temperature_fahrenheit)/2   # Instructions in [3] call for averaging

        if temperature_fahrenheit_avg >= 80:
            # if (temperature > 27°C) & (relative_humidity > 40%), then use the full Rothfusz regression formula
            heat_index: float = sum([c1, c2 * temperature_celsius, c3 * relative_humidity, c4 * temperature_celsius * relative_humidity, c5 * temperature_celsius**2, c6 * relative_humidity**2, c7 * temperature_celsius**2 * relative_humidity, c8 * temperature_celsius * relative_humidity**2, c9 * temperature_celsius**2 * relative_humidity**2])
        else:
            heat_index = (heat_index_fahrenheit - 32) * 5/9

        return heat_index

    @staticmethod
    def wind_chill(temperature_celsius: float, wind_speed_km_h: float) -> float:
        """Calculate Wind Chill (feels like temperature) based on NOAA equation.

        Wind-chill or windchill (popularly wind chill factor) is the lowering of
        body temperature due to the passing-flow of lower-temperature air. Wind
        chill numbers are always lower than the air temperature for values where
        the formula is valid. When the apparent temperature is higher than the
        air temperature, the heat index is used instead.

        :param temperature_celsius: Air temperature in degrees Celsius.
        :type temperature_celsius: float
        :param wind_speed_km_h: Wind speed in kilometers per hour.
        :type wind_speed_km_h: float
        :return: Wind chill temperature in degrees Celsius.
        :rtype: float
        :raises ValueError: Raised if temperature > 10°C or wind speed <= 4.8 km/h.

        .. note::
            Wind Chill Temperature is only defined for temperatures at or below
            10°C and wind speeds above 4.8 km/h.

        References:
            - `Wikipedia: Wind Chill <https://en.wikipedia.org/wiki/Wind_chill>`_
            - `NOAA Wind Chill <https://www.wpc.ncep.noaa.gov/html/windchill.shtml>`_
        """

        if temperature_celsius > 10 or wind_speed_km_h <= 4.8:
            raise ValueError("Wind Chill Temperature is only defined for temperatures at or below 10°C and wind speeds above 4.8 Km/h")
        return 13.12 + (0.6215 * temperature_celsius) - 11.37 * wind_speed_km_h**0.16 + 0.3965 * temperature_celsius * wind_speed_km_h**0.16

    @staticmethod
    def feels_like(temperature_celsius: float, relative_humidity: float, wind_speed_km_h: float) -> float:
        """Calculate the "feels like" temperature based on NOAA logic.

        Automatically selects the appropriate comfort index based on temperature
        and wind conditions:
        - Wind Chill: temperature <= 10°C and wind > 4.8 km/h
        - Heat Index: temperature >= 26.7°C
        - Temperature as is: all other cases

        :param temperature_celsius: Air temperature in degrees Celsius.
        :type temperature_celsius: float
        :param relative_humidity: Relative humidity as a percentage (0-100).
        :type relative_humidity: float
        :param wind_speed_km_h: Wind speed in kilometers per hour.
        :type wind_speed_km_h: float
        :return: Feels like temperature in degrees Celsius, rounded to 1 decimal place.
        :rtype: float
        """

        if temperature_celsius <= 10 and wind_speed_km_h > 4.8:
            # Wind Chill for low temp cases (and wind)
            feels_like: float = OutdoorTemperatureIndices.wind_chill(temperature_celsius, wind_speed_km_h)
        elif temperature_celsius >= 26.7:
            # Heat Index for High temp cases
            feels_like = OutdoorTemperatureIndices.heat_index(temperature_celsius, relative_humidity)
        else:
            feels_like = temperature_celsius

        return round(feels_like, 1)

    @staticmethod
    def apparent_temperature(temperature_celsius: float, relative_humidity_percent: float, wind_speed_km_h: float) -> float:
        """Calculate apparent temperature based on Steadman (1994) model.

        The apparent temperature is based on a mathematical model of an adult,
        walking outdoors, in the shade. The apparent temperature is defined as
        the temperature, at the reference relative humidity level, producing the
        same amount of discomfort as that experienced under the current ambient
        temperature and relative humidity.

        :param temperature_celsius: Air temperature in degrees Celsius.
        :type temperature_celsius: float
        :param relative_humidity_percent: Relative humidity as a percentage (0-100).
        :type relative_humidity_percent: float
        :param wind_speed_km_h: Wind speed in kilometers per hour.
        :type wind_speed_km_h: float
        :return: Apparent temperature in degrees Celsius, rounded to 1 decimal place.
        :rtype: float

        References:
            - `Bureau of Meteorology: Apparent Temperature <http://www.bom.gov.au/info/thermal_stress/#atapproximation>`_
        """
        vapor_pressure: float = (relative_humidity_percent/100) * 6.105 * exp((17.27 * temperature_celsius) / (237.7 + temperature_celsius))
        apparent_temperature: float = temperature_celsius + 0.33 * vapor_pressure - 0.7 * wind_speed_km_h - 4
        return round(apparent_temperature, 1)


class PMVcalculator:
    """Predicted Mean Vote (PMV) calculator following ISO 7730 standard.

    This class implements the PMV/PPD (Predicted Mean Vote / Predicted Percentage
    of Dissatisfied) thermal comfort model as defined in ISO 7730. The PMV index
    predicts the mean thermal sensation vote of a large group of people on a
    seven-point thermal sensation scale.

    The calculation considers:
    - Air temperature and radiant temperature
    - Air speed
    - Relative humidity
    - Clothing insulation (CLO)
    - Metabolic rate (MET)

    :param air_temperature_C: Air temperature in degrees Celsius, defaults to 21.
    :type air_temperature_C: float, optional
    :param relative_humidity_percent: Relative humidity as percentage (0-100), defaults to 50.
    :type relative_humidity_percent: float, optional
    :param radiant_temperature_C: Average radiant temperature in degrees Celsius. If None, uses air temperature, defaults to None.
    :type radiant_temperature_C: float | None, optional
    :param Icl_CLO: Clothing insulation in CLO units, defaults to 1.
    :type Icl_CLO: float, optional
    :param metabolism_MET: Metabolic rate in MET units (typically 0.8 to 4), defaults to 1.
    :type metabolism_MET: float, optional
    :param air_speed_m_s: Air speed in meters per second (typically 0 to 1), defaults to 0.1.
    :type air_speed_m_s: float, optional
    :param precision: Convergence precision for iterative calculations, defaults to 1e-5.
    :type precision: float, optional
    """

    @staticmethod
    def __pmv(precision: float, input_data: dict[str, float]) -> dict[str, float]:
        """Internal method to calculate PMV and related thermal comfort parameters.

        :param precision: Convergence precision for iterative temperature calculation.
        :type precision: float
        :param input_data: Dictionary containing all input parameters for PMV calculation.
        :type input_data: dict[str, float]
        :return: Dictionary containing PMV, PPD, and all heat transfer components.
        :rtype: dict[str, float]
        :raises StopIteration: Raised if maximum iterations (150) are exceeded.
        """
        air_temperature_C: float = input_data['air_temperature_C']
        air_temperature_K: float = 273.15 + air_temperature_C
        if input_data['radiant_temperature_C'] is None:
            radiant_temperature_C: float = air_temperature_C
        else:
            radiant_temperature_C = input_data['radiant_temperature_C']
        air_speed_m_s: float = input_data['air_speed_m_s']
        metabolism_MET: float = input_data['metabolism_MET']
        Icl_CLO: float = input_data['Icl_CLO']
        relative_humidity_percent: float = input_data['relative_humidity_percent']
        work_MET = 0

        P_vapor_Pa: float = relative_humidity_percent * 10 * exp(16.6536 - 4030.183 / (air_temperature_C + 235))

        R_clothes: float = 0.155 * Icl_CLO  # thermal insulation of the clothing in M2K/W
        metabolism_W_m2: float = metabolism_MET * 58.15  # metabolic rate in W/M2
        work_W_m2: float = work_MET * 58.15  # external work in W/M2
        base_metabolism_W_m2: float = metabolism_W_m2 - work_W_m2  # internal heat production in the human body
        # calculation of the clothing area factor
        if R_clothes <= 0.078:
            F_cl: float = 1 + (1.29 * R_clothes)  # ratio of surface clothed body over nude body
        else:
            F_cl = 1.05 + (0.645 * R_clothes)

        # heat transfer coefficient by forced convection
        hc_ventilated: float = 12.1 * sqrt(air_speed_m_s)
        hc: float = hc_ventilated  # initialize variable
        air_temperature_K: float = air_temperature_C + 273
        radiant_temperature_K: float = radiant_temperature_C + 273
        T_clothes_last_C: float = air_temperature_K + (35.5 - air_temperature_C) / (3.5 * R_clothes + 0.1)

        xn: float = T_clothes_last_C / 100
        xf: float = T_clothes_last_C / 50
        precision = 0.00015

        n = 0
        while abs(xn - xf) > precision:
            xf = (xf + xn) / 2
            hc_non_ventilated: float = 2.38 * abs(100.0 * xf - air_temperature_K) ** 0.25
            if hc_ventilated > hc_non_ventilated:
                hc = hc_ventilated
            else:
                hc = hc_non_ventilated
            xn = ((308.7 - 0.028 * base_metabolism_W_m2) + (R_clothes * F_cl * 3.96 * (radiant_temperature_K / 100.0) ** 4) + R_clothes * F_cl * air_temperature_K * hc - R_clothes * F_cl * 3.96 * xf**4) / (100 + R_clothes * F_cl * 100 * hc)
            n += 1
            if n > 150:
                raise StopIteration("Max iterations exceeded")

        T_clothes_C: float = 100 * xn - 273

        # heat loss diff. through skin
        P_perspiration_sweat_W_m2: float = 3.05 * 0.001 * (5733 - (6.99 * base_metabolism_W_m2) - P_vapor_Pa)
        # heat loss by sweating
        if base_metabolism_W_m2 > 58.15:
            P_perspiration_diffusion_W_m2: float = 0.42 * (base_metabolism_W_m2 - 58.15)
        else:
            P_perspiration_diffusion_W_m2 = 0
        # latent respiration heat loss
        P_breath_latent_W_m2: float = 1.7 * 0.00001 * metabolism_W_m2 * (5867 - P_vapor_Pa)
        # dry respiration heat loss
        P_breath_sensitive_W_m2: float = 0.0014 * metabolism_W_m2 * (34 - air_temperature_C)
        # heat loss by radiation
        P_rad_W_m2: float = 3.96 * F_cl * (xn**4 - (radiant_temperature_K / 100.0) ** 4)
        # heat loss by convection
        P_conv_W_m2 = F_cl * hc * (T_clothes_C - air_temperature_C)

        ts: float = 0.303 * exp(-0.036 * metabolism_W_m2) + 0.028
        PMV: float = ts * (base_metabolism_W_m2 - P_perspiration_sweat_W_m2 - P_perspiration_diffusion_W_m2 - P_breath_latent_W_m2 - P_breath_sensitive_W_m2 - P_rad_W_m2 - P_conv_W_m2)
        PPD: float = 100 - 95 * exp(-0.03353 * PMV**4 - 0.2179 * PMV**2)

        return {'PMV': PMV, 'P_metabolism_W_m2': metabolism_W_m2, 'P_perspiration_sweat_W_m2': P_perspiration_sweat_W_m2, 'P_perspiration_diffusion_W_m2': P_perspiration_diffusion_W_m2, 'P_breath_latent_W_m2': P_breath_latent_W_m2, 'P_breath_sensitive_W_m2': P_breath_sensitive_W_m2, 'P_rad_W_m2': P_rad_W_m2, 'P_conv_W_m2':  P_conv_W_m2, 'T_clothes_C': T_clothes_C, 'P_vapor_Pa': P_vapor_Pa, 'PPD': PPD}

    class Sampler:
        """Helper class for generating parameter value samples for parametric analysis.

        :param bounds: Dictionary mapping parameter names to (min, max) value tuples, defaults to standard PMV parameter ranges.
        :type bounds: dict[str, tuple[float, float]], optional
        :ivar bounds: Parameter bounds dictionary.
        """

        def __init__(self, bounds: dict[str, tuple[float, float]] = {'air_temperature_C': (17, 27), 'relative_humidity_percent': (0, 100), 'radiant_temperature_C': (14, 37), 'Icl_CLO': (0, 1.5), 'metabolism_MET': (0.5, 4.0), 'air_speed_m_s': (0, 1)}):
            """Initialize the sampler with parameter bounds.

            :param bounds: Dictionary mapping parameter names to (min, max) value tuples.
            :type bounds: dict[str, tuple[float, float]], optional
            """
            self.bounds: dict[str, tuple[float, float]] = bounds

        @property
        def data_names(self) -> list[str]:
            """Get list of parameter names defined in bounds.

            :return: List of parameter names.
            :rtype: list[str]
            """
            return list(self.bounds.keys())

        def __call__(self, data_name: str, n_samples: int = 10) -> list[float]:
            """Generate evenly spaced samples for a parameter.

            :param data_name: Name of the parameter to sample.
            :type data_name: str
            :param n_samples: Number of samples to generate, defaults to 10.
            :type n_samples: int, optional
            :return: List of evenly spaced parameter values.
            :rtype: list[float]
            """
            m, M = self.bounds[data_name]
            delta: float = (M - m) / (n_samples - 1)
            return [m + i * delta for i in range(n_samples)]

    def __init__(self, air_temperature_C: float = 21, relative_humidity_percent: float = 50, radiant_temperature_C: float | None = None, Icl_CLO: float = 1, metabolism_MET: float = 1, air_speed_m_s: float = 0.1, precision: float = 1e-5) -> None:
        """Initialize PMV calculator with thermal comfort parameters.

        :param air_temperature_C: Air temperature in degrees Celsius, defaults to 21.
        :type air_temperature_C: float, optional
        :param relative_humidity_percent: Relative humidity as percentage (0-100), defaults to 50.
        :type relative_humidity_percent: float, optional
        :param radiant_temperature_C: Average radiant temperature in degrees Celsius. If None, uses air temperature, defaults to None.
        :type radiant_temperature_C: float | None, optional
        :param Icl_CLO: Clothing insulation in CLO units, defaults to 1.
        :type Icl_CLO: float, optional
        :param metabolism_MET: Metabolic rate in MET units (typically 0.8 to 4), defaults to 1.
        :type metabolism_MET: float, optional
        :param air_speed_m_s: Air speed in meters per second (typically 0 to 1), defaults to 0.1.
        :type air_speed_m_s: float, optional
        :param precision: Convergence precision for iterative calculations, defaults to 1e-5.
        :type precision: float, optional
        """
        self.precision: float = precision
        self.__input_data = dict()
        self.__input_data['air_temperature_C'] = air_temperature_C
        self.__input_data['relative_humidity_percent'] = relative_humidity_percent
        self.__input_data['radiant_temperature_C'] = radiant_temperature_C
        self.__input_data['Icl_CLO'] = Icl_CLO
        self.__input_data['metabolism_MET'] = metabolism_MET
        self.__input_data['air_speed_m_s'] = air_speed_m_s

        self._input_names: list = list(self.__input_data.keys())
        self._output_names: list[str] = ['PMV', 'P_metabolism_W_m2', 'P_perspiration_sweat_W_m2', 'P_perspiration_diffusion_W_m2', 'P_breath_latent_W_m2', 'P_breath_sensitive_W_m2', 'P_rad_W_m2', 'P_conv_W_m2', 'T_clothes_C', 'P_vapor_Pa', 'PPD']

    def set_input_data(self, **name_values: float) -> None:
        """Update input parameter values.

        :param name_values: Keyword arguments with parameter names and new values.
        :type name_values: float
        """
        for name in name_values:
            self.__input_data[name] = name_values[name]

    @property
    def input_names(self) -> list[str]:
        """Get list of input parameter names.

        :return: List of input parameter names.
        :rtype: list[str]
        """
        return self._input_names

    @property
    def output_names(self) -> list[str]:
        """Get list of output parameter names.

        :return: List of output parameter names (PMV, PPD, heat transfer components, etc.).
        :rtype: list[str]
        """
        return self._output_names

    def PMV(self, **input_data: float) -> float:
        """Calculate Predicted Mean Vote.

        :param input_data: Optional keyword arguments to override default input values.
        :type input_data: float
        :return: PMV value (typically in range -3 to +3).
        :rtype: float
        """
        return self.output_data('PMV', **input_data)['PMV']

    def PPD(self, **input_data: float) -> float:
        """Calculate Predicted Percentage of Dissatisfied.

        :param input_data: Optional keyword arguments to override default input values.
        :type input_data: float
        :return: PPD value as percentage (0-100).
        :rtype: float
        """
        return self.output_data('PPD', **input_data)['PPD']

    def abs_PMV(self, **input_data: float) -> float:
        """Calculate absolute value of PMV.

        :param input_data: Optional keyword arguments to override default input values.
        :type input_data: float
        :return: Absolute PMV value.
        :rtype: float
        """
        return abs(self.PMV(**input_data))

    def output_data(self, *output_names: str, **input_data: float) -> dict[str, float]:
        """Calculate PMV output data with optional input overrides.

        Returns a dictionary containing PMV, PPD, and all heat transfer components
        (metabolism, perspiration, breathing, radiation, convection) in Watts per
        square meter, plus clothing temperature and vapor pressure.

        :param output_names: Optional names of specific outputs to return. If empty, returns all outputs.
        :type output_names: str
        :param input_data: Optional keyword arguments to override default input values.
        :type input_data: float
        :return: Dictionary of output values. Keys include: PMV, PPD, P_metabolism_W_m2,
            P_perspiration_sweat_W_m2, P_perspiration_diffusion_W_m2, P_breath_latent_W_m2,
            P_breath_sensitive_W_m2, P_rad_W_m2, P_conv_W_m2, T_clothes_C, P_vapor_Pa.
        :rtype: dict[str, float]
        """
        my_input_data: dict[str, float] = dict()
        for input_name in self.input_names:
            if input_name in input_data:
                my_input_data[input_name] = input_data[input_name]
            else:
                my_input_data[input_name] = self.__input_data[input_name]
        output_data: dict[str, float] = PMVcalculator.__pmv(self.precision, my_input_data)
        if len(output_names) == 0:
            return output_data
        return {output_name: output_data[output_name] for output_name in output_names}

    def variate(self, input_name: str, input_values: list[float], overloaded_data: dict[str, float] = {}) -> dict[str, list[float]]:
        """Vary one input parameter and calculate outputs for each value.

        :param input_name: Name of the input parameter to vary.
        :type input_name: str
        :param input_values: List of values to test for the input parameter.
        :type input_values: list[float]
        :param overloaded_data: Optional dictionary of additional input overrides, defaults to {}.
        :type overloaded_data: dict[str, float], optional
        :return: Dictionary mapping output names to lists of values for each input variation.
        :rtype: dict[str, list[float]]
        """
        results: dict[str, list[float]] = {output_name: [] for output_name in self.output_names}
        for input_value in input_values:
            data = dict()
            for an_input_name in self._input_names:
                if an_input_name == input_name:
                    data[input_name] = input_value
                elif an_input_name in overloaded_data:
                    data[an_input_name] = overloaded_data[an_input_name]
                else:
                    data[an_input_name] = self.__input_data[an_input_name]
            result: dict[str, float] = PMVcalculator.__pmv(self.precision, data)
            for output_name in self.output_names:
                results[output_name].append(result[output_name])
        return results

    def __str__(self) -> str:
        """Generate string representation of PMV calculator with input and output values.

        :return: Formatted string showing all input and output parameters.
        :rtype: str
        """
        string = '* Input data with default value:\n'
        for v in self._input_names:
            if self.__input_data[v] is not None:
                string += '%s: %g\n' % (v, self.__input_data[v])
            else:
                string += '%s: None\n' % (v)
        string += '\n* Output data with default value:\n'
        output_data: dict[str, float] = self.output_data()
        for v in output_data:
            string += '%s: %g\n' % (v, output_data[v])
        return string + '\n'

    def parametric_plot(self, parameter_name: str, x_variable_name: str, y_variable_name: str = 'PMV') -> None:
        """Create a parametric plot showing the effect of varying parameters on PMV outputs.

        :param parameter_name: Name of the parameter to vary across multiple curves.
        :type parameter_name: str
        :param x_variable_name: Name of the parameter to vary along the x-axis.
        :type x_variable_name: str
        :param y_variable_name: Name of the output variable to plot on y-axis, defaults to 'PMV'.
        :type y_variable_name: str, optional
        """
        sampler = PMVcalculator.Sampler()
        parameter_samples: list[float] = sampler(parameter_name, n_samples=6)
        for p_val in parameter_samples:
            x_variable_samples: list[float] = sampler(x_variable_name, 16)
            results: dict[str, list[float]] = self.variate(x_variable_name, x_variable_samples, overloaded_data={parameter_name: p_val})
            plt.plot(x_variable_samples, results[y_variable_name], label='%s=%g' % (parameter_name, p_val))
        plt.legend()
        plt.xlabel(x_variable_name)
        plt.ylabel(y_variable_name)
        plt.grid()

    def ppd_plot(self) -> None:
        """Plot the relationship between PMV and PPD (Predicted Percentage of Dissatisfied).

        Creates a standard PMV-PPD curve showing how the percentage of dissatisfied
        people increases with absolute PMV values.
        """
        PMVs: list[float] = [_/10 for _ in range(-30, 31)]
        PPDs: list[float] = [100 - 95 * exp(-0.03353 * PMV**4 - 0.2179 * PMV**2) for PMV in PMVs]
        plt.plot(PMVs, PPDs)
        plt.xlabel('PMV')
        plt.ylabel('Predicted Percentage of Dissatisfied')
        plt.grid()


class AdaptiveComfort:
    """Adaptive thermal comfort model based on outdoor temperature and occupancy.

    This class implements an adaptive comfort model that adjusts comfort
    temperature based on running average outdoor temperature. The model is
    suitable for naturally ventilated buildings where occupants adapt to
    outdoor conditions.

    The comfort temperature is calculated as: T_comfort = 0.33 * T_out_avg + 18.8

    :param outdoor_temperatures: List of outdoor temperatures in degrees Celsius.
    :type outdoor_temperatures: list[float]
    :param occupancy: List of occupancy values (0 = absent, >0 = present).
    :type occupancy: list[float]
    :param n_hours_averager: Number of hours for running average of outdoor temperature, defaults to 7*24 (1 week).
    :type n_hours_averager: int, optional
    :ivar Tout_avg: Running average of outdoor temperatures.
    :ivar occupancy: Occupancy time series.
    """

    @staticmethod
    def comfort_class(Tin: float, Tcomfort: float) -> int:
        """Classify comfort level based on indoor temperature and comfort temperature.

        Comfort classes:
        - Class 1: Within ±2°C of comfort temperature (optimal)
        - Class 2: Within ±3°C of comfort temperature (acceptable)
        - Class 3: Within ±4°C of comfort temperature (marginally acceptable)
        - Class 4: Outside ±4°C of comfort temperature (unacceptable)

        :param Tin: Indoor temperature in degrees Celsius.
        :type Tin: float
        :param Tcomfort: Comfort temperature in degrees Celsius.
        :type Tcomfort: float
        :return: Comfort class (1-4).
        :rtype: int
        """
        if Tcomfort - 2 <= Tin <= Tcomfort + 2:
            return 1
        elif Tcomfort - 3 <= Tin <= Tcomfort + 3:
            return 2
        elif Tcomfort - 4 <= Tin <= Tcomfort + 4:
            return 3
        else:
            return 4

    def __init__(self, outdoor_temperatures: list[float], occupancy: list[float], n_hours_averager: int = 7*24) -> None:
        """Initialize adaptive comfort model.

        :param outdoor_temperatures: List of outdoor temperatures in degrees Celsius.
        :type outdoor_temperatures: list[float]
        :param occupancy: List of occupancy values (0 = absent, >0 = present).
        :type occupancy: list[float]
        :param n_hours_averager: Number of hours for running average of outdoor temperature, defaults to 7*24 (1 week).
        :type n_hours_averager: int, optional
        """
        self.Tout_avg: list[float] = Averager(outdoor_temperatures).average(n_hours_averager)
        self.occupancy: list[float] = occupancy

    def Tcomfort(self, level: int = 0) -> list[float]:
        """Calculate adaptive comfort temperature time series.

        :param level: Comfort level adjustment in degrees Celsius, defaults to 0.
        :type level: int, optional
        :return: List of comfort temperatures in degrees Celsius.
        :rtype: list[float]
        """
        return [0.33 * self.Tout_avg[k] + 18.8 + level for k in range(len(self.Tout_avg))]

    def __call__(self, Tin: list[float]) -> list[int]:
        """Evaluate comfort class for indoor temperature time series.

        :param Tin: List of indoor temperatures in degrees Celsius.
        :type Tin: list[float]
        :return: List of comfort classes (0 = unoccupied, 1-4 = occupied comfort classes).
        :rtype: list[int]
        """
        _Tcomfort: list[float] = self.Tcomfort()
        return [0 if self.occupancy[k] == 0 else AdaptiveComfort.comfort_class(Tin[k], _Tcomfort[k]) for k in range(len(self.Tout_avg))]


def icone(CO2_concentration: list[float], occupancies: list[float]) -> float:
    """Compute the ICONE indicator for indoor air quality and confinement assessment.

    ICONE (Indicateur de CONfinement) evaluates air quality based on CO2
    concentration levels during occupancy periods. The indicator ranges from
    0 (excellent) to 5 (poor), with thresholds at 1000 ppm (medium confinement)
    and 1700 ppm (high confinement).

    :param CO2_concentration: List of CO2 concentrations in parts per million (ppm).
    :type CO2_concentration: list[float]
    :param occupancies: List of occupancy values (0 = absent, >0 = present).
    :type occupancies: list[float]
    :return: ICONE indicator value between 0 and 5.
    :rtype: float
    """
    n_presence = 0
    n1_medium_containment = 0
    n2_high_containment = 0
    for k in range(len(occupancies)):
        if occupancies[k] > 0:
            n_presence += 1
            if 1000 <= CO2_concentration[k] < 1700:
                n1_medium_containment += 1
            elif CO2_concentration[k] >= 1700:
                n2_high_containment += 1
    f1 = n1_medium_containment / n_presence if n_presence > 0 else 0
    f2 = n2_high_containment / n_presence if n_presence > 0 else 0
    return 8.3 * log10(1 + f1 + 3 * f2)


def extreme_quantiles_during_presence(values: list[float], occupancies: list[float], cut: float = .1) -> dict[str, float | None]:
    """Calculate statistical indicators for values during occupancy periods.

    Computes average, lowest quantile average, and highest quantile average
    of values only during periods when occupancy is present. Useful for
    analyzing comfort conditions or air quality during actual use.

    :param values: Time series of values to analyze.
    :type values: list[float]
    :param occupancies: List of occupancy values (0 = absent, >0 = present).
    :type occupancies: list[float]
    :param cut: Fraction of data to include in lowest/highest quantiles, defaults to 0.1 (10%).
    :type cut: float, optional
    :return: Dictionary with keys 'average', 'cut', 'lowest', 'highest'. Values are None if no occupancy periods exist.
    :rtype: dict[str, float | None]
    """
    values_when_presence = list()
    for i in range(len(occupancies)):
        if occupancies[i] > 0:
            values_when_presence.append(values[i])

    if len(values_when_presence) > 0:
        values_when_presence.sort()
        values_when_presence_lowest = values_when_presence[:ceil(len(values_when_presence) * cut)]
        values_when_presence_highest = values_when_presence[floor(len(values_when_presence) * (1-cut)):]
        return {'average': sum(values_when_presence) / len(values_when_presence), 'cut': cut,
                'lowest': sum(values_when_presence_lowest) / len(values_when_presence_lowest),
                'highest': sum(values_when_presence_highest) / len(values_when_presence_highest)
                }
    else:
        return {'average': None, 'cut': cut, 'lowest': None, 'highest': None}
