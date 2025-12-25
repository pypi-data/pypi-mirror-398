"""
This code has been written by stephane.ploix@grenoble-inp.fr
It is protected under GNU General Public License v3.0/

It is an instance of Model for the office H358

Author: stephane.ploix@grenoble-inp.fr
License: GNU General Public License v3.0"""
from __future__ import annotations
import time
from batem.core.data import DataProvider
from batem.core.model import TimeVaryingStateModelSimulator
from batem.core.statemodel import StateModel
from batem.sites.building_h358 import make_building_state_model_k
from batem.sites.data_h358 import generate_h358_data_provider


def make_building_state_model(dp: DataProvider, periodic_depth_seconds=60*60, state_model_order_max=3) -> tuple[TimeVaryingStateModelSimulator, StateModel]:
    state_model_maker, nominal_state_model = make_building_state_model_k(dp,  periodic_depth_seconds=periodic_depth_seconds, state_model_order_max=state_model_order_max)
    return TimeVaryingStateModelSimulator(state_model_maker), nominal_state_model


if __name__ == "__main__":

    print('Loading data')
    start: float = time.time()
    h358_dp: DataProvider = generate_h358_data_provider(starting_stringdate='15/02/2015', ending_stringdate='15/02/2016')
    h358_dp_excerpt = h358_dp.excerpt('1/03/2015', '20/03/2015')
    print('\nduration: %i secondes' % round(time.time() - start))

    print('Caching state models')
    start: float = time.time()
    h358_state_model, nominal_state_model = make_building_state_model(h358_dp_excerpt, periodic_depth_seconds=60*60, state_model_order_max=5)
    print('\nduration: %i secondes' % round(time.time() - start))

    print('Nominal simulation')
    start: float = time.time()
    nominal_state_model.simulate(h358_dp_excerpt, suffix='NOMINAL')
    print('\nduration: %i secondes' % round(time.time() - start))

    print('Time varying simulation')
    start = time.time()
    variable_simulated_values: dict[str, list[float]] = h358_state_model.simulate()
    print('\nduration: %i secondes' % round(time.time() - start))

    for variable_name in variable_simulated_values:
        h358_dp_excerpt.add_var(variable_name + '_VARYING', variable_simulated_values[variable_name])

    h358_dp
    h358_dp_excerpt.plot()


# python3.11 -m cProfile -o model_h358.prof sites/model_h358.py
# snakeviz model_h358.prof
#
# pip3.11 install line_profiler
# python3.11 -m kernprof -l -v sites/model_h358.py
