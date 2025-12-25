"""Case-Based Reasoning (CBR) module for building energy management and advising systems.

.. module:: batem.core.cbr

This module implements a Case-Based Reasoning framework for analyzing building energy performance
and providing recommendations based on historical data patterns. It extracts and normalizes data
from DataProvider instances to build a knowledge base of cases, where each case represents a
specific building state with context variables (uncontrollable causes), action variables
(controllable causes), and effect variables (outcomes).

Classes
-------

.. autosummary::
   :toctree: generated/

   AbstractCaseBaseAdviser
   CaseBase
   SimpleCaseBaseAdviser

Classes Description
-------------------

**AbstractCaseBaseAdviser**
    Base class for CBR systems with data normalization and case management.

**CaseBase**
    Container for managing and querying cases with similarity-based retrieval.

**SimpleCaseBaseAdviser**
    Specialized implementation for thermal and CO2 comfort analysis.

Key Features
------------

* Automatic data normalization for consistent case comparison
* Similarity-based case retrieval using weighted distance calculations
* Case base management with automatic case generation from time series data
* Support for context-action-effect variable relationships
* Sensitivity analysis for effect variables to account for human perception thresholds

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""
import matplotlib.pyplot as plt
from typing import Self
from statistics import mean
from datetime import datetime
from prettytable import PrettyTable
from .timemg import datetime_to_stringdate, stringdate_to_datetime
from .data import DataProvider
from abc import ABC, abstractmethod
from scipy.optimize import differential_evolution


class AbstractCaseBaseAdviser(ABC):
    """General Abstract class used to generate and interact with a base of cases. It extracts and normalizes data coming from a DataProvider.
    """

    def __init__(self, dp: DataProvider, context_variables: tuple[str], action_variables: tuple[str], effect_variables_sensitivities: dict[str, float]) -> None:
        """Initializer

        :param dp: the data provider from which data are collected
        :type dp: DataProvider
        :param context_variables: name of the variables describing the context i.e uncontrollable causes
        :type context_variables: tuple[str]
        :param action_variables: name of the variables describing the action i.e. controllable causes
        :type action_variables: tuple[str]
        :param effect_variables_sensitivities: dictionary containing the effect variables together with the minimum human perceivable resolution i.e the related sensitivity.
        :type effect_variables_sensitivities: dict[str, float]
        """
        self.counter = 0
        self._context_variables: tuple[str] = context_variables
        self._action_variables: tuple[str] = action_variables
        self._context_action_variables: tuple[str] = list(context_variables)
        self._context_action_variables.extend(action_variables)
        self._effect_variables: tuple[str] = tuple(effect_variables_sensitivities.keys())
        self._effect_variable_sensitivities = tuple(effect_variables_sensitivities.values())

        self._context_data: dict[str, list[float]] = {variable_name: AbstractCaseBaseAdviser.normalize(dp.series(variable_name)) for variable_name in self._context_variables}
        self._action_data: dict[str, list[float]] = {variable_name: AbstractCaseBaseAdviser.normalize(dp.series(variable_name)) for variable_name in self._action_variables}
        self._effect_data: dict[str, list[float]] = {variable_name: dp.series(variable_name) for variable_name in self._effect_variables}
        self._case_base = CaseBase()

    @property
    def context_variables(self) -> tuple[str]:
        return self._context_variables

    @property
    def action_variables(self) -> tuple[str]:
        return self._action_variables

    @property
    def context_action_variables(self) -> tuple[str]:
        return self._context_action_variables

    @property
    def effect_variables(self) -> tuple[str]:
        return self._effect_variables

    @property
    def effect_variables_sensitivities(self) -> tuple[float]:
        return self._effect_variable_sensitivities

    @property
    def context_data(self) -> dict[str, list[float]]:
        return self._context_data

    @property
    def action_data(self) -> dict[str, list[float]]:
        return self._action_data

    @property
    def effect_data(self) -> dict[str, list[float]]:
        return self._effect_data

    @property
    def case_base(self) -> 'CaseBase':
        return self._case_base

    @property
    @abstractmethod
    def CA_weights(self) -> list[float]:
        raise NotImplementedError

    @CA_weights.setter
    @abstractmethod
    def CA_weights(self, variable_weights: list[float]) -> None:
        raise NotImplementedError

    @abstractmethod
    def performance(self, case) -> float:
        raise NotImplementedError

    def best_close_context_cases(self, the_case: 'CaseBase.Case', number_of_neighbors: int) -> tuple['CaseBase.Case', float, float]:
        cases_distances: list[tuple[CaseBase.Case, float]] = self.case_base.close_context_case(the_case)
        case_distances_performances = list()
        for i in range(number_of_neighbors):
            a_case: CaseBase.Case = cases_distances[i][0]
            case_distances_performances.append((a_case, cases_distances[i][1], self.performance(a_case)))
        return case_distances_performances

    def incompleteness(self, weights: list[float] = None, with_plot: bool = False) -> float:
        incompleteness: float = self.case_base.incompleteness(weights=weights, with_plot=with_plot)[0]
        self.counter += 1
        if self.counter % 10 == 0:
            print('.', end='')
        return incompleteness

    def weights_optimizer(self, maxiter=1000, popsize=15, tol=0.01, mutation=(0.5, 1), recombination=0.7, seed=None, with_plot: bool = False):
        results = differential_evolution(self.incompleteness, [(0, 1) for _ in range(len(self.context_variables) + len(self.action_variables))], args=(), strategy='best1bin', maxiter=maxiter, popsize=popsize, tol=tol, mutation=mutation, recombination=recombination, seed=seed, callback=None, disp=True, polish=True, init='latinhypercube', atol=0, updating='deferred', workers=-1, constraints=(), x0=self.CA_weights)  # deferred
        self.counter = 0
        self.CA_weights = [float(f) for f in results.x]
        print()
        print('Best score is %f and best weights are:\n' % results.fun, self.CA_weights)
        self.case_base.incompleteness(with_plot=with_plot)
        return results.x

    def cap_cases(self, threshold_value: float, reoptimize: bool = False) -> list['CaseBase.Case']:
        if not reoptimize:
            _, alphas = self.case_base.incompleteness()
            cases_to_be_removed = list()
            for i in range(len(self.case_base)):
                if alphas['max'][i] > threshold_value:
                    cases_to_be_removed.append(self.case_base(i))
            for case in cases_to_be_removed:
                self.case_base.rm_case(case)
            return cases_to_be_removed
        else:
            all_removed_cases = list()
            removed_cases = None
            while removed_cases is None or len(removed_cases) > 0:
                removed_cases: list[CaseBase.Case] = self.cap_cases(threshold_value)
                all_removed_cases.extend(removed_cases)
                print('Removed cases:' + ',\t'.join([repr(case) for case in removed_cases]))
                self.weights_optimizer(maxiter=10, with_plot=False)
            return sorted(all_removed_cases)

    @staticmethod
    def normalize(data: list[float]) -> list[float]:
        """Normalized a data series, considering minimum and maximum values

        :param data: the data series
        :type data: list[float]
        :return: the normalized data series
        :rtype: list[float]
        """
        min_data, max_data = min(data), max(data)
        if min_data != max_data:
            return [(d - min_data) / (max_data - min_data) for d in data]
        else:
            if min_data != 0:
                return [1 for d in data]
            else:
                return list(data)


class CaseBase:

    class Case:

        def __init__(self, case_base: 'CaseBase', id: int, name: str, context_data: list[float], action_data: list[float], effect_data: list[float]) -> None:
            """General utility class gathering all the data related to one day as a case in a case base reasoning.
            This class is used internally by the Advisor class and MUST NOT BE DIRECTLY IMPLEMENTED

            :param case_base: Case base that belongs the case
            :type case_base: CaseBase
            :param name: name of the case, typically the date as dd/MM/yyyy
            :type name: str
            :param context_data: list of data describing uncontrollable causes data impacting the current case.
            :type context_data: list[float]
            :param action_data: list of data describing inhabitant controllable causes data impacting the current case.
            :type action_data: list[float]
            :param effect_data: list of data describing impact data of causes of the current case.
            :type effect_data: list[float]
            """
            self.id: int = id
            self.case_base: CaseBase = case_base
            self.name: str = name
            self.context_data: list[float] = context_data
            self.action_data: list[float] = action_data
            self.effect_data: list[float] = effect_data

        def C_distance(self, other_case: "Self") -> float:
            """compute the normalized C-distance (between context data)

            :param other_case: another case
            :type other_case: Self
            :return: the C-distance
            :rtype: float
            """
            return sum([self.case_base.C_weights[i] * abs(self.context_data[i] - other_case.context_data[i]) for i in range(self.case_base.n_contexts)])

        def A_distance(self, other_case: "Self") -> float:
            """compute the normalized A-distance (between action data)

            :param other_case: another case
            :type other_case: Self
            :return: the A-distance
            :rtype: float
            """
            return sum([self.case_base.A_weights[i] * abs(self.action_data[i] - other_case.action_data[i]) for i in range(self.case_base.n_actions)])

        def CA_distance(self, other_case: "Self") -> float:
            """compute the normalized CA-distance (between context and action data)

            :param other_case: another case
            :type other_case: Self
            :return: the A-distance
            :rtype: float
            """
            return self.C_distance(other_case) + self.A_distance(other_case)

        def E_distance(self, other_case: "Self") -> float:
            """compute the normalized sensitive distance between effect data

            :param other_case: another case
            :type other_case: Self
            :return: the E-distance
            :rtype: float
            """
            return sum([abs(round(self.case_base.effect_sensitivities[i]/2 + self.effect_data[i] - other_case.effect_data[i]) / self.case_base.effect_sensitivities[i]) for i in range(self.case_base.n_effects)])

        def I_distance(self, other_case: "Self") -> int:
            return abs(self.id - other_case.id)

        def __lt__(self, other_case: "Self") -> bool:
            return self.id < other_case.id

        def __le__(self, other_case: "Self") -> bool:
            return self.id <= other_case.id

        def __eq__(self, other_case: "Self") -> bool:
            return self.id == other_case.id

        def __neq__(self, other_case: "Self") -> bool:
            return self.id != other_case.id

        def __gt__(self, other_case: "Self") -> bool:
            return self.id > other_case.id

        def __ge__(self, other_case: "Self") -> bool:
            return self.id >= other_case.id

        def __repr__(self) -> str:
            return self.name

        def __str__(self) -> str:
            return repr(self) + '\n\n> C: ' + ','.join("%.2f" % _ for _ in self.context_data) + '\n\n> A: ' + ','.join("%.2f" % _ for _ in self.action_data) + '\n\n> E: ' + ','.join("%.2f" % _ for _ in self.effect_data) + '\n'

    def __init__(self) -> None:
        """Base of cases
        """
        self.n_contexts: int = None
        self.n_actions: int = None
        self.n_effects: int = None
        self.C_weights: tuple[float] = None
        self.A_weights: tuple[float] = None
        self.effect_sensitivities: tuple[float] = None
        self._cases: list[CaseBase.Case] = list()
        self.case_counter = 0

    def add_case(self, case_name: str, case_context: tuple[float], case_action: tuple[float], case_effect: tuple[float]):
        self._cases.append(CaseBase.Case(self, self.case_counter, case_name, case_context, case_action, case_effect))
        self.case_counter += 1

    def close_context_case(self, the_case: 'CaseBase.Case') -> list[tuple['CaseBase.Case', float]]:
        cases_distances: list[tuple['CaseBase.Case', float]] = list()
        for a_case in self.cases:
            if the_case != a_case:
                cases_distances.append((a_case, the_case.C_distance(a_case)))
        sorted_case_indices_distances: list[tuple[int, float]] = sorted(cases_distances, key=lambda x: x[1])
        return sorted_case_indices_distances

    def rm_case(self, case_ref: int | str) -> None:
        for case in self._cases:
            if (type(case_ref) is int and case.id == case_ref) or (type(case_ref) is str and case.name == case_ref) or (type(case_ref) is CaseBase.Case and case == case_ref):
                self._cases.remove(case)
                break

    @property
    def case_ids(self) -> list[int]:
        ids: list[int] = list()
        for case in self._cases:
            ids.append(case.id)
        return ids

    @property
    def case_names(self) -> list[str]:
        names: list[str] = list()
        for case in self._cases:
            names.append(case.name)
        return names

    @property
    def cases(self):
        return self._cases

    def __call__(self, k: int = None) -> list[Case] | Case:
        """return either a specified case number of all the cases

        :param k: the case number, defaults to None
        :type k: int, optional
        :return: the requested case(s)
        :rtype: list[_Case] | _Case
        """
        if k is None:
            return self._cases
        else:
            return self._cases[k]

    def __len__(self) -> int:
        """return the number of cases in the base

        :return: the number of available cases
        :rtype: int
        """
        return len(self._cases)

    def __str__(self) -> str:
        return f"{len(self)} cases with \n-context: "+", ".join(self.context_variables)+'\n-action: '+", ".join(self.action_variables)+'\n-effect: '+", ".join(self.effect_variables)+'\n'

    def incompleteness(self, weights: list[float] = None, with_plot: bool = False) -> float:
        """Compute an incompleteness indicator (the lower, the more complete)

        :param weights: weights to be applied, defaults to None
        :type weights: list[float], optional
        :param with_plot: True if a plot is requested, defaults to False
        :type with_plot: bool, optional
        :return: the best weights for context action variables
        :rtype: float
        """
        if weights is not None:
            self.CA_weights: list[float] = weights
        alphas = list()
        cases_alphas: list[list[float]] = [[] for _ in range(len(self))]
        for i in range(len(self)):
            for j in range(i):
                alpha: float = self(i).E_distance(self(j)) / (self(i).CA_distance(self(j)) + .0001)
                alphas.append(alpha)
                cases_alphas[i].append(alpha)
                cases_alphas[j].append(alpha)

        alphas_min, alphas_avg, alphas_max = list(), list(), list()
        for i in range(len(self)):
            alphas_min.append(min(cases_alphas[i]))
            alphas_avg.append(mean(cases_alphas[i]))
            alphas_max.append(max(cases_alphas[i]))

        if with_plot:
            _, ax = plt.subplots(2, 1)
            ax[0].hist(alphas, density=False, bins=50)  # density=False would make counts
            ax[0].set_ylabel('occurrences')
            ax[0].set_xlabel('alpha')

            ax[1].plot(self.case_ids, alphas_min)
            ax[1].plot(self.case_ids, alphas_avg)
            ax[1].plot(self.case_ids, alphas_max)
            ax[1].grid()
            ax[1].set_xlabel('cases')
            ax[1].set_ylabel('alphas')
            ax[1].legend(('min', 'avg', 'max'))
        return mean(alphas_avg), {'min': alphas_min, 'avg': alphas_avg, 'max': alphas_max}


class SimpleCaseBaseAdviser(AbstractCaseBaseAdviser, ABC):
    """Specific Case Base Handler for H358"""

    def __init__(self, dp: DataProvider, context_variables: tuple[str], action_variables: tuple[str], effect_variables_sensitivities: dict[str, float], first_day_hour: int = 6, last_day_hour: int = 23) -> None:
        """The case base handler dedicated to the thermal and CO2 concentration comfort for the H358 office

        :param dp: the data provider containing the measurements and past weather records
        :type dp: DataProvider
        :param context_variables: the names of context variables (uncontrollable causes) to be taken into account
        :type context_variables: tuple[str]
        :param action_variables: the names of action variables (uncontrollable causes) to be taken into account
        :type action_variables: tuple[str]
        :param effect_variables_sensitivities: the sensitive perceivable resolution
        :type effect_variables_sensitivities: dict[str, float]
        :param first_day_hour: the starting hour of each day to 6 (previous hours in the day are ignored)
        :type first_day_hour: int, optional
        :param last_day_hour: the last hour of the day (included) taken into account, defaults to 23
        :type last_day_hour: int, optional
        """
        super().__init__(dp, context_variables, action_variables, effect_variables_sensitivities)
        self.first_day_hour: int = first_day_hour
        self.last_day_hour: int = last_day_hour
        self.n_data: int = last_day_hour - first_day_hour + 1
        self.datetimes: list[datetime] = dp.series('datetime')
        self.case_base.n_contexts = len(context_variables) * self.n_data
        self.case_base.n_actions = len(action_variables) * self.n_data
        self.case_base.n_effects = len(self.effect_variables) * self.n_data
        self.case_base.C_weights = tuple(1/(self.case_base.n_contexts+self.case_base.n_actions) for _ in range(self.case_base.n_contexts))
        self.case_base.A_weights = tuple(1/(self.case_base.n_contexts+self.case_base.n_actions) for _ in range(self.case_base.n_actions))
        self.case_base.effect_sensitivities = tuple(s for s in self.effect_variables_sensitivities for _ in range(self.n_data))

        cases_indices: dict[str, list[int, int, int, int]] = dict()
        indices = list()
        for k, dt in enumerate(dp.datetimes):
            hour_in_day: int = dt.hour
            if hour_in_day in (0, first_day_hour, last_day_hour):
                indices.append(k)
            if hour_in_day == 23:  # hour 23
                indices.append(k)
                cases_indices[datetime_to_stringdate(dt, date_format='%d/%m/%Y')] = tuple(indices)
                indices = list()

        for day in cases_indices:
            case_indices: list[int] = cases_indices[day][1:3]
            case_context: list[float] = [self.context_data[context_variable][i] for context_variable in self.context_variables for i in range(case_indices[0], case_indices[1]+1)]
            case_action: list[float] = [self.action_data[action_variable][i] for action_variable in self.action_variables for i in range(case_indices[0], case_indices[1]+1)]
            case_effect: list[list[float]] = [self.effect_data[effect_variable][i] for effect_variable in self.effect_variables for i in range(case_indices[0], case_indices[1]+1)]
            self.case_base.add_case(day, case_context, case_action, case_effect)

    @property
    def CA_weights(self) -> list[float]:
        """return the weights used for context-action data

        :return: the Context-Action weights
        :rtype: list[float]
        """
        _CA_weights: list[float] = [sum([self.case_base.C_weights[i*self.n_data+j] for j in range(self.n_data)]) for i in range(len(self.context_variables))]
        _CA_weights.extend([sum([self.case_base.A_weights[i*self.n_data+j] for j in range(self.n_data)]) for i in range(len(self.action_variables))])
        return _CA_weights

    @CA_weights.setter
    def CA_weights(self, variable_weights: list[float]) -> None:
        """Make it possible to set directly the weights used for context-action distance calculations. In case of recomputation of the weights, the provided variable_weights will be introduce into the initial solution vector differential evolution optimization algorithm.

        :param variable_weights: a list of variable_weights
        :type variable_weights: list[float]
        """
        normalization: float = sum(variable_weights) * self.n_data
        self.case_base.C_weights = [variable_weights[i] / normalization for i in range(len(self.context_variables)) for _ in range(self.n_data)]
        self.case_base.A_weights = [variable_weights[i] / normalization for i in range(len(self.context_variables), len(self.context_action_variables)) for _ in range(self.n_data)]

    def case_variable_data(self, case: CaseBase.Case) -> dict[str, list[float]]:
        """Extract the data values related to context, action and effect variables, into a dictionary variable name → series of values

        :return:  a dictionary variable name → series of values
        :rtype: dict[str, list[float]]
        """
        variable_values: dict[str, list[float]] = dict()
        for i in range(len(self.context_variables)):
            variable_values[self.context_variables[i]] = case.context_data[i*self.n_data: (i+1)*self.n_data]
        for i in range(len(self.action_variables)):
            variable_values[self.action_variables[i]] = case.action_data[i*self.n_data: (i+1)*self.n_data]
        for i in range(len(self.effect_variables)):
            variable_values[self.effect_variables[i]] = case.effect_data[i*self.n_data: (i+1)*self.n_data]
        return variable_values

    @abstractmethod
    def performance(self, case: CaseBase.Case) -> float:
        """Evaluate the performance of a case

        :param case: a case
        :type case: CaseBase.Case
        :return: the performance
        :rtype: float
        """
        raise NotImplementedError('Performance method must be implemented in a sub-class')

    def statistics(self, number_of_neighbors: int = 5) -> None:
        """ print statistics about the case based reasoning results
        :param number_of_neighbors: number of neighbors considered for searching for a better case in the history
        """
        pretty_table = PrettyTable()
        pretty_table.field_names = ('case', 'close case', 'distance', 'initial perf.', 'final perf.', 'delta perf. %')
        for the_case in self.case_base.cases:
            initial_performance: float = self.performance(the_case)
            best_close_context_cases: list[tuple[CaseBase.Case, float, float]] = self.best_close_context_cases(the_case, number_of_neighbors)
            best_close_context_cases.append((the_case, 0, initial_performance))
            case_indices_distances_performances: list[tuple[CaseBase.Case, float, float]] = sorted(best_close_context_cases, key=lambda x: (x[2], x[1]))
            best_case_tuple: tuple[CaseBase.Case, float, float] = case_indices_distances_performances[0]
            row = (repr(the_case), repr(best_case_tuple[0]), best_case_tuple[1], initial_performance, best_case_tuple[2], 100*(best_case_tuple[2]-initial_performance)/initial_performance if initial_performance != 0 else 0)
            pretty_table.add_row(row)
        print(pretty_table)

    def suggest(self, the_case: CaseBase.Case, number_of_neighbors: int, adaptation: bool = False) -> list[float]:
        """determine the best actions in the neighborhood of the given case (considering a given number of neighbors)

        :param the_case: the case under consideration
        :type the_case: CaseBase.Case
        :param number_of_neighbors: the number of neighbors considered in the neighborhood
        :type number_of_neighbors: int
        :return: a list of actions formatted as in a case
        :rtype: list[float]
        """
        initial_performance: float = self.performance(the_case)
        best_close_context_case_tuples: list[tuple[CaseBase.Case, float, float]] = self.best_close_context_cases(the_case, number_of_neighbors)
        best_close_context_case_tuples.append((the_case, 0, initial_performance))
        if not adaptation:
            best_case_tuple: tuple[CaseBase.Case, float, float] = sorted(best_close_context_case_tuples, key=lambda x: (x[2], x[1]))[0]
            return best_case_tuple[0].action_data
        else:
            max_distance = max([t[1] for t in best_close_context_case_tuples])
            # max_performance = max([t[2] for t in best_close_context_case_tuples])
            action_data_weights = list()
            total_weight = 0
            if max_distance == 0:
                best_case_tuple: tuple[CaseBase.Case, float, float] = sorted(best_close_context_case_tuples, key=lambda x: (x[2]))[0]
                return best_case_tuple[0].action_data
            else:
                for t in best_close_context_case_tuples:
                    weight = (max_distance - t[1]) / max_distance * (1 - t[2])
                    total_weight += weight
                    action_data_weights.append((t[0].action_data, weight))
                if total_weight == 0:
                    return the_case.action_data
                else:
                    adapted_action_data = [0 for _ in range(len(the_case.action_data))]
                    for i in range(len(the_case.action_data)):
                        for adw in action_data_weights:
                            adapted_action_data[i] += adw[0][i] * adw[1] / total_weight
                    return adapted_action_data

    def get_datetime_index(self, case: CaseBase.Case) -> int:
        """determine the index of the values corresponding to the first time slot of the case

        :param case: the case for which the first time index has to be determined
        :type case: CaseBase.Case
        :return: the index of the first time slot in the data provider
        :rtype: int
        """
        the_datetime = stringdate_to_datetime(repr(case) + ' %i:00:00' % self.first_day_hour)
        return self.datetimes.index(the_datetime)

    def set_actions(self, action_variable_data: dict[str, list[float]], original_case: CaseBase.Case, action_data: list[float]):
        """set the actions of the action case to the original case

        :param action_variable_data: a dictionary with the action variable values
        :type action_variable_data: dict[str, list[float]]
        :param original_case: the original case
        :type original_case: CaseBase.Case
        :param action_case: the case for which the action will be applied
        :type action_case: CaseBase.Case
        """
        k: int = self.get_datetime_index(original_case)
        for i in range(len(self.action_data)):
            action_variable = self.action_variables[i]
            for j in range(self.n_data):
                action_variable_data[action_variable][k+j] = action_data[i*self.n_data + j]
