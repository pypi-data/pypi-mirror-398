"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
from sites.data_h358 import generate_h358_data_provider
from core.linreg import sliding_arx_estimation


# training_data = sites.data_h358.H358IndependentVariableSet(None, None)
# training_data = make_data_provider(starting_stringdate='15/02/2015', ending_stringdate='15/02/2016')
training_data = generate_h358_data_provider(starting_stringdate='1/09/2015', ending_stringdate='3/01/2016')


#  ####### tuning parameter zone #######
offset: bool = True
minimum_input_delay: int = 0
input_names: tuple[str] = ('weather_temperature', 'window_opening', 'Tcorridor', 'door_opening', 'total_electric_power', 'Psun_window', 'dT_heat', 'occupancy')
inputs_maximum_delays: tuple[int] = 10  # (2, 0, 0, 0, 2, 1, 1)
output_name: str = 'Toffice_reference'
output_maximum_delay: int = 10
######################################

sliding_arx_estimation(output_name, input_names, training_data, offset=offset, minimum_input_delay=minimum_input_delay, inputs_maximum_delays=inputs_maximum_delays, output_maximum_delay=output_maximum_delay)

print('Results have been saved as a markdown document in the "results/sliding" folder')
