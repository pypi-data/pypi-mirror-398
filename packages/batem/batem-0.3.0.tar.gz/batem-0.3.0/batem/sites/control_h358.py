# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from batem.core.data import DataProvider
from batem.core.control import HVACcontinuousModePort, OpeningPort, Simulation, SignalBuilder
from batem.core.inhabitants import Preference
from batem.sites.building_h358 import make_building_state_model_k
from batem.sites.data_h358 import generate_h358_data_provider


# #### INITIALIZATION OF THE DATA PROVIDER AND THE SIMULATION DURATION ####``
starting_stringdate, ending_stringdate = '15/02/2015', '15/02/2016'
dp: DataProvider = generate_h358_data_provider(starting_stringdate, ending_stringdate, control=True)
Pheater_recorded: list[float] = dp.series('office:Pheater')

# ### GENERATION OF THE SETPOINT AND MODE SIGNALS ####
signal_builder = SignalBuilder(dp.datetimes)

modes: list[float | None] = signal_builder.build_seasonal(day_month_start='15/10', day_month_end='15/4', seasonal_value=1, out_season_value=0)
absences: list[float] = signal_builder.build_long_absence(dp.series('presence'), 1, 0, 7)
modes = signal_builder.merge(modes, absences, operator=lambda x, y: x*y)
dp.add_var('mode', modes)  # add the HVAC modes signal to the data provider

# ### INITIALIZATION OF THE CONTROL PORTS ####
window_opening_port = OpeningPort(data_provider=dp, feeding_variable_name='window_opening', presence_variable='presence')
door_opening_port = OpeningPort(data_provider=dp, feeding_variable_name='door_opening', presence_variable='presence')
heater_port = HVACcontinuousModePort(dp, 'PZoffice', 'office:Pheater', max_heating_power=2000, max_cooling_power=2000, mode_variable='mode')


window_opening_port = OpeningPort(data_provider=dp, feeding_variable_name='window_opening', presence_variable='presence')
door_opening_port = OpeningPort(data_provider=dp, feeding_variable_name='door_opening', presence_variable='presence')

# #### INITIALIZATION OF THE SIMULATION TYPE-DEPENDENT CONTROL PORTS, AND BUILDING STATE MODEL ####
building_state_model_maker, state_model_nominal = make_building_state_model_k(dp, control=True)

simulation = Simulation(dp, building_state_model_maker, control_ports=[window_opening_port, door_opening_port, heater_port,])

simulation.add_temperature_controller(zone_name='office', heat_gain_name='office:Pheat_gain', CO2production_name='office:PCO2', hvac_power_port=heater_port, temperature_controller=None,)

# #### RUN THE SIMULATION ####
simulation.run(suffix='#sim')

# #### PRINT THE SIMULATION RESULTS ####
preference = Preference(preferred_temperatures=(19, 24), extreme_temperatures=(16, 29), preferred_CO2_concentration=(500, 1500), temperature_weight_wrt_CO2=0.5, power_weight_wrt_comfort=0.5, mode_cop={1: 2, })

print(simulation)
print(simulation.control_ports)
preference.print_assessment(dp.datetimes, dp.series('office:Pheater'), dp.series('TZoffice_sim'), dp.series('CCO2office_sim'), dp.series('occupancy'), action_sets=(dp.series('window_opening'), dp.series('door_opening')))

Pheaters: list[float] = dp.series('office:Pheater')
Heats: list[float] = dp.series('office:Pheat_gain')
print('ratio heater power / total heating power: ', round(100 * sum([Pheaters[k] for k in range(len(dp))]) / sum([Heats[k] for k in range(len(dp))]), 2), '%')

dp.add_var('Pheater_recorded', Pheater_recorded)    

dp.plot('office:Pheat_gain', 'office:Pheater', 'office:Pheat', 'mode', 'PZoffice', 'TZoffice_sim', 'PZoffice', 'TZoffice_setpoint', 'window_opening', 'door_opening')
dp.plot()
