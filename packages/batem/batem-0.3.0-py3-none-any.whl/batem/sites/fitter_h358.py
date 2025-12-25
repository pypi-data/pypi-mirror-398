# Author: stephane.ploix@grenoble-inp.fr
# License: GNU General Public License v3.0

from __future__ import annotations
import time
from core.data import DataProvider
from core.model import ModelFitter
from sites.data_h358 import generate_h358_data_provider
from sites.simulation_h358 import make_building_state_model

print('Load data')

dp_full: DataProvider = generate_h358_data_provider(starting_stringdate='15/02/2015', ending_stringdate='15/02/2016')
dp_train: DataProvider = dp_full.excerpt('11/12/2015', '3/01/2016')
print(dp_train.parameter_set)
dp_train.parameter_set.load("best_parameters")

print('Make state models and put in cache')
start = time.time()
varying_state_model, nominal_state_model = make_building_state_model(dp_train,  periodic_depth_seconds=60*60, state_model_order_max=None)
print('\nduration: %i secondes' % round(time.time() - start))

fitter: ModelFitter = ModelFitter(varying_state_model)

print('Sensitivity analysis')
start = time.time()
fitter.sensitivity(2)
print('\nduration: %i secondes' % round(time.time() - start))

print('- Model fitting')
start: float = time.time()
best_parameter_levels, best_outputs, best_error = fitter.fit(100)
print('\nduration: %i secondes' % round(time.time() - start))
dp_train.parameter_set.save('best_parameters')

print("best_parameters")
print('levels=(', ', '.join(['%i' % level for level in best_parameter_levels]), ')')

varying_state_model, nominal_state_model = make_building_state_model(dp_full,  periodic_depth_seconds=60*60, state_model_order_max=None)
validation_output_values = varying_state_model.simulate(pre_cache=True)

for simulated_output_name in validation_output_values:
    dp_full.add_var(simulated_output_name+'_VALID', validation_output_values[simulated_output_name])


dp_full.plot()
