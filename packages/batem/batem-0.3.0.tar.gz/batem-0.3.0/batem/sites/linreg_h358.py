"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

ARX model for H358 office.

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
import core.linreg
import sites.data_h358
import sites.simulation_h358
import core.data

validation_data_provider = sites.data_h358.generate_h358_data_provider(starting_stringdate='15/02/2015', ending_stringdate='15/02/2016')
training_data_provider = validation_data_provider.excerpt('12/10/2015', '31/12/2015')

#  ####### tuning parameter zone #######
offset: bool = True
minimum_input_delay: int = 0
input_names: tuple[str] = ('weather_temperature', 'window_opening', 'Tcorridor', 'door_opening', 'total_electric_power', 'Psun_window', 'dT_heat', 'occupancy')
inputs_maximum_delays = 4  # (2, 0, 0, 0, 2, 1, 1)  # int: same delay for each input of tuple[int], specific delay for each input
output_name: str = 'Toffice_reference'
output_maximum_delay = 4
#  #####################################

print(training_data_provider)

core.linreg.arx_estimation(output_name, input_names, training_data_provider, validation_data_provider, offset=offset, minimum_input_delay=minimum_input_delay, inputs_maximum_delays=inputs_maximum_delays, output_maximum_delay=output_maximum_delay)

print('Results have been saved as a markdown document in the "results/linreg" folder')
