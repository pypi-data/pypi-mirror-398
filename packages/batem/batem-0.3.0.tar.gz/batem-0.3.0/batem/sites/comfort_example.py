# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

import matplotlib.pyplot as plt

from core.comfort import *


if __name__ == '__main__':
    temperatures = [_ for _ in range(-20, 38)]
    humidities = [_ for _ in range(0, 101, 10)]
    windspeeds = [_ for _ in range(0, 50, 10)]
    fig, ax = plt.subplots(2, 1)
    ax[0].set_title('MOAA feels like temperature')
    h = 50
    w = 0
    for w in windspeeds:
        ax[0].plot(temperatures, [OutdoorTemperatureIndices.feels_like(T, h, w) for T in temperatures], label='windspeed:%ikm/h' % (w,))
    ax[0].set_xlabel('actual temperature (humidity:%i%%)' % h)
    ax[0].set_ylabel('feels like temperature')
    ax[0].legend()
    h = 50
    w = 0
    for h in humidities:
        ax[1].plot(temperatures, [OutdoorTemperatureIndices.feels_like(T, h, w) for T in temperatures], label='humidity:%i%%' % (h,))
    ax[1].set_xlabel('actual temperature (windspeed:%ikm/h)' % w)
    ax[1].set_ylabel('feels like temperature')
    ax[1].legend()

    fig, ax = plt.subplots(2, 1)
    ax[0].set_title('Australian Apparent temperature')
    h = 50
    w = 0
    for w in windspeeds:
        ax[0].plot(temperatures, [apparent_temperature_celsius(T, h, w) for T in temperatures], label='windspeed:%ikm/h' % (w,))
    ax[0].set_xlabel('actual temperature (humidity:%i%%)' % h)
    ax[0].set_ylabel('feels like temperature')
    ax[0].legend()
    h = 50
    w = 0
    for h in humidities:
        ax[1].plot(temperatures, [apparent_temperature_celsius(T, h, w) for T in temperatures], label='humidity:%i%%' % (h,))
    ax[1].set_xlabel('actual temperature (windspeed:%ikm/h)' % w)
    ax[1].set_ylabel('feels like temperature')
    ax[1].legend()

    pmv_calculator = PMVcalculator()
    print(pmv_calculator)
    plt.figure()
    pmv_calculator.parametric_plot(parameter_name='relative_humidity_percent', x_variable_name='air_temperature_C', y_variable_name='PMV')
    plt.figure()
    pmv_calculator.parametric_plot(parameter_name='radiant_temperature_C', x_variable_name='air_temperature_C', y_variable_name='PMV')
    plt.figure()
    pmv_calculator.parametric_plot(parameter_name='Icl_CLO', x_variable_name='air_temperature_C', y_variable_name='PMV')
    plt.figure()
    pmv_calculator.parametric_plot(parameter_name='metabolism_MET', x_variable_name='air_temperature_C', y_variable_name='PMV')
    plt.figure()
    pmv_calculator.parametric_plot(parameter_name='air_speed_m_s', x_variable_name='air_temperature_C', y_variable_name='PMV')
    plt.figure()
    pmv_calculator.ppd_plot()
    plt.show()
