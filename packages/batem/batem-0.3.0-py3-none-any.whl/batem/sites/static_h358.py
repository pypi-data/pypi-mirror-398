# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from __future__ import annotations
from sites.data_h358 import generate_h358_data_provider

print('Loading data')
h358_data_provider = generate_h358_data_provider(starting_stringdate='15/02/2015', ending_stringdate='15/02/2016')

#  ###### HERE IS WHERE PARAMETERS SHOULD BE ADJUSTED ##################
h358_data_provider.parameter_set('office-outdoor:Q', 12/3600)
h358_data_provider.parameter_set('solar_factor', 0.4)
h358_data_provider.parameter_set('body_metabolism', 100)
h358_data_provider.parameter_set('heater_power_per_delta_surface_temperature', 35)
h358_data_provider.parameter_set('foam_thickness', 34e-2)
#  #####################################################################

Rout: float = 0.02
Rcor: float = 0.02
Qoutdoors: list[float | list[float]] = h358_data_provider.series('office-outdoor:Q')
Routvent: float = [1 / (1 / Rout + 1.005 * 1.26 * Qoutdoors[k]) for k in range(len(h358_data_provider))]

Tout: list[float] = h358_data_provider.series('weather_temperature')
Tcor: list[float] = h358_data_provider.series('Tcorridor')
Pin: list[float] = h358_data_provider.series('office:Pheat')

office_simulated_temperature = []

for k in range(len(h358_data_provider)):
    # ADD YOUR STATIC MODEL HERE: Tout[k], Tcor[k], Pin[k] -> Tin
    Tin: float = 21
    office_simulated_temperature.append(Tin)

h358_data_provider.add_var('office_simulated_temperature', office_simulated_temperature)
h358_data_provider.plot()
