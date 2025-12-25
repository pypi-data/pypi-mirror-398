"""State space model implementation for building energy analysis and control systems.

.. module:: batem.core.statemodel

This module provides comprehensive state space model functionality for building
energy analysis, including continuous and discrete-time models, model reduction,
simulation capabilities, and integration with building energy data providers.
It implements state space representations for building thermal dynamics and
control system analysis.

Classes
-------

.. autosummary::
   :toctree: generated/

   StateModel

Classes Description
-------------------

**StateModel**
    Main class for state space model implementation and management.

Key Features
------------

* State space model representation with A, B, C, D matrices
* Continuous to discrete-time model conversion using zero-order hold
* Model order reduction using balanced truncation methods
* State space model extension and composition capabilities
* Input/output variable management and grouping
* Model simulation with data provider integration
* Static gain matrix calculation and analysis
* Eigenvalue analysis for system stability assessment
* Integration with building energy data providers
* Support for partitioned input/output systems
* Model discretization for control system implementation

The module is designed for building energy analysis, thermal modeling, and
control system design in building energy management applications.

.. note::
    This module requires pymor for model order reduction and scipy for signal processing.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""

import numpy
import warnings
import sys
import io
import pymor.models.iosys
import pymor.reductors.bt
import scipy.signal
import scipy.linalg
import math
from .data import DataProvider


class StateModel:
    """State space model implementation for building energy analysis and control systems.

    This class provides comprehensive state space model functionality including
    continuous and discrete-time representations, model reduction, simulation
    capabilities, and integration with building energy data providers. It supports
    building thermal dynamics modeling and control system analysis.
    """

    def __init__(self, ABCD: tuple[numpy.matrix, numpy.matrix, numpy.matrix, numpy.matrix], input_names: list[str], output_names: list[str], sample_time_in_seconds: int = 3600, fingerprint: int = None):
        self.fingerprint: int = fingerprint
        self.sample_time_in_seconds: int = sample_time_in_seconds
        self.Ac, self.Bc, self.Cc, self.Dc = ABCD
        if self.Dc is not None:
            self.Dc = numpy.atleast_2d(self.Dc)
        self.n_inputs: int = self.Dc.shape[1] if self.Dc is not None and len(self.Dc.shape) > 1 else 0
        self.n_outputs: int = self.Dc.shape[0] if self.Dc is not None else 0

        self.input_names: list[str] = input_names
        self.output_names: list[str] = output_names
        self.state: numpy.matrix = None

        if self.Ac is not None:
            self._check(self.Ac, self.Bc, self.Cc, self.Dc, input_names, output_names)
            self.A, self.B, self.C, self.D = self._discretize(self.Ac, self.Bc, self.Cc, self.Dc, sample_time_in_seconds)
        else:
            self.A, self.B, self.C, self.D = self.Ac, self.Bc, self.Cc, self.Dc

        self.output_selections: dict[str, list[int]] = dict()  # contains group names and corresponding output variable indices
        self.input_groups_indices: dict[str, list[int]] = dict()  # contains group names and corresponding input variable indices
        self.input_partitions: dict[str, list[str]] = dict()

    def reduce(self, order: int, V_reduction=None, W_reduction=None):
        if self.A is None or order is None or self.A.shape[0] <= order:
            return V_reduction, W_reduction
        if V_reduction is None or W_reduction is None:
            # Suppress warnings and messages from pymor
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Temporarily redirect stdout to suppress print statements
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                try:
                    lti_model = pymor.models.iosys.LTIModel.from_matrices(numpy.array(self.A), numpy.array(self.B), numpy.array(self.C), D=numpy.array(self.D), E=None, sampling_time=self.sample_time_in_seconds, presets=None, solver_options=None, error_estimator=None, visualizer=None, name=None)
                    reductor = pymor.reductors.bt.BTReductor(lti_model)
                    reduced_order_model = reductor.reduce(r=order, projection='sr')
                    A_reduced, B_reduced, C_reduced, D_reduced, E_reduced = reduced_order_model.to_matrices()
                    V_reduction = numpy.matrix(reductor.V.to_numpy())
                    W_reduction = numpy.matrix(reductor.W.to_numpy())
                finally:
                    sys.stdout = old_stdout
        else:
            # Need to figure out orientation: we want W^T * A * V
            # Expected shapes: W^T: (r,n), A: (n,n), V: (n,r) -> result: (r,r)
            n = self.A.shape[0]  # Original state dimension
            
            # Check if W needs transposing
            if W_reduction.shape[0] == n and W_reduction.shape[1] < n:
                # W is (n, r) - needs transposing
                W_T = numpy.transpose(W_reduction)
            else:
                # W is already (r, n) - use as is
                W_T = W_reduction
            
            # Check if V needs transposing
            if V_reduction.shape[0] < n and V_reduction.shape[1] == n:
                # V is (r, n) - needs transposing to (n, r)
                V = numpy.transpose(V_reduction)
            else:
                # V is already (n, r) - use as is
                V = V_reduction
                
            A_reduced = W_T * self.A * V
            B_reduced = W_T * self.B
            C_reduced = self.C * V
            D_reduced = self.D
        self.A = numpy.matrix(A_reduced)
        self.B = numpy.matrix(B_reduced)
        self.C = numpy.matrix(C_reduced)
        self.D = numpy.matrix(D_reduced)
        return V_reduction, W_reduction

    def _discretize(self, A, B, C, D, Ts) -> tuple[numpy.matrix, numpy.matrix, numpy.matrix, numpy.matrix, float]:
        A_discrete, B_discrete, C_discrete, D_discrete, _ = scipy.signal.cont2discrete((A, B, C, D), Ts, method='zoh')
        A: numpy.matrix = numpy.matrix(A_discrete)
        B: numpy.matrix = numpy.matrix(B_discrete)
        C: numpy.matrix = numpy.matrix(C_discrete)
        D: numpy.matrix = numpy.matrix(D_discrete)
        return A, B, C, D

    def initialize(self, **Uvals: list[float]):
        U = self.decodeU(**Uvals)
        
        # Handle static models (A is None)
        if self.A is None:
            self.state = None
            return self.state
        
        try:
            I_minus_A = numpy.matrix(numpy.eye(self.A.shape[0])) - self.A
            try:
                I_minus_A_inv = numpy.linalg.inv(I_minus_A)
            except numpy.linalg.LinAlgError:
                # Use pseudo-inverse if matrix is singular
                I_minus_A_inv = scipy.linalg.pinv(I_minus_A, atol=1e-10)
            self.state = I_minus_A_inv * self.B * U
        except Exception as e:  # noqa
            # If initialization fails, start with zero state
            self.state = numpy.matrix(numpy.zeros((self.A.shape[0], 1)))
        previous_state = None
        while previous_state is None or numpy.linalg.norm(self.state - previous_state) > 1e-10:
            previous_state = self.state
            self.state = self.A * previous_state + self.B * U

        return self.state

    def set_state(self, state) -> None:
        self.state: numpy.matrix = state

    def output(self, **Uvals: list[float]) -> list[float]:
        U: numpy.matrix = numpy.matrix(self.decodeU(**Uvals))
        
        # Static model: Y = D * U only
        if self.A is None:
            if self.D is not None:
                Y = self.D * U
                return Y.flatten().tolist()[0]
            else:
                return []  # No outputs
        
        # Dynamic model: Y = C * X + D * U
        if self.state is None:
            self.initialize(**Uvals)
        Y = self.C * self.state + self.D * U
        return Y.flatten().tolist()[0]

    def step(self, **Uvals: list[float]):
        # Static models don't have state
        if self.A is None:
            return None
        
        U = self.decodeU(**Uvals)
        self.state = self.A * self.state + self.B * U
        return self.state

    def decodeU(self, **partition_input_values: list[float]):
        partition_name: str = ''
        if partition_name == '':
            # Map input values by name to handle potentially missing inputs
            U_values = []
            for input_name in self.input_names:
                if input_name in partition_input_values:
                    U_values.append(partition_input_values[input_name])
                else:
                    U_values.append(0.0)  # Default value for missing inputs
            U: numpy.matrix = numpy.transpose(numpy.matrix(U_values))
        else:
            U = numpy.matrix(numpy.zeros((self.n_inputs, 1)))
            for group_name in partition_input_values:
                for i, j in enumerate(self.input_groups_indices[group_name]):
                    U[j, 0] = partition_input_values[group_name][i]
        return U

    def extend(self, extension_name: str, ABCD: tuple[numpy.matrix, numpy.matrix, numpy.matrix, numpy.matrix], input_names: list[str], output_names: list[str]):
        Ac_ext, Bc_ext, Cc_ext, Dc_ext = ABCD
        self._check(Ac_ext, Bc_ext, Cc_ext, Dc_ext, input_names, output_names)
        
        if self.Ac is None:
            # Static model case - just extend D matrix and outputs
            p_ext: int = Dc_ext.shape[0]
            D_common = numpy.matrix(numpy.zeros((p_ext, self.n_inputs)))
            i: int = 0
            while i < len(input_names):
                new_input = input_names[i]
                if new_input in self.input_names:
                    j = self.input_names.index(new_input)
                    D_common[:, j] = Dc_ext[:, i]
                    Dc_ext = numpy.delete(Dc_ext, i, axis=1)
                    input_names.remove(new_input)
                else:
                    i += 1
            self.output_names.extend(output_names)
            self.Dc = numpy.vstack((self.Dc, D_common))
            if len(input_names) != 0:
                Dc_new = numpy.vstack((numpy.matrix(numpy.zeros((self.n_outputs, len(input_names)))), Dc_ext))
                self.Dc = numpy.hstack((self.Dc, Dc_new))
                self.input_groups_indices[extension_name] = [i for i in range(self.n_inputs, self.n_inputs + len(input_names))]
                for input_partition_name in self.input_partitions:
                    self.input_partitions[input_partition_name].append(extension_name)
                self.input_names.extend(input_names)
            self.n_outputs = self.n_outputs + p_ext
            self.n_inputs = self.n_inputs + len(input_names)
            self.D = self.Dc
            return
        
        n_ext = Ac_ext.shape[0]
        p_ext: int = Cc_ext.shape[0]
        B_common = numpy.matrix(numpy.zeros((n_ext, self.n_inputs)))
        D_common = numpy.matrix(numpy.zeros((p_ext, self.n_inputs)))
        i: int = 0
        while i < len(input_names):
            new_input = input_names[i]
            if new_input in self.input_names:
                j = self.input_names.index(new_input)
                B_common[:, j] = Bc_ext[:, i]
                D_common[:, j] = Dc_ext[:, i]
                Bc_ext = numpy.delete(Bc_ext, i, axis=1)
                Dc_ext = numpy.delete(Dc_ext, i, axis=1)
                input_names.remove(new_input)
            else:
                i += 1
        n = self.Ac.shape[0]
        self.Ac = scipy.linalg.block_diag(self.Ac, Ac_ext)
        self.Cc = scipy.linalg.block_diag(self.Cc, Cc_ext)
        self.output_names.extend(output_names)
        self.Bc = numpy.vstack((self.Bc, B_common))
        self.Dc = numpy.vstack((self.Dc, D_common))
        if len(input_names) != 0:
            Bc_new = numpy.vstack((numpy.matrix(numpy.zeros((n, len(input_names)))), Bc_ext))
            self.Bc = numpy.hstack((self.Bc, Bc_new))

            Dc_new = numpy.vstack((numpy.matrix(numpy.zeros((self.n_outputs, len(input_names)))), Dc_ext))
            self.Dc = numpy.hstack((self.Dc, Dc_new))
            self.input_groups_indices[extension_name] = [i for i in range(self.n_inputs, self.n_inputs + len(input_names))]
            for input_partition_name in self.input_partitions:
                self.input_partitions[input_partition_name].append(extension_name)
            self.input_names.extend(input_names)
        self.n_outputs = self.n_outputs + p_ext
        self.n_inputs = self.n_inputs + len(input_names)
        self.A, self.B, self.C, self.D = self._discretize(self.Ac, self.Bc, self.Cc, self.Dc, self.sample_time_in_seconds)

    @property
    def n_states(self):
        return self.A.shape[0]

    def _check(self, A, B, C, D, input_names, output_names):
        if not (A.shape[0] == A.shape[1] and A.shape[0] == C.shape[1]):
            raise ValueError('Invalid number of states')
        if not (B.shape[1] == D.shape[1] and D.shape[1] == len(input_names)):
            raise ValueError('Invalid number of inputs')
        if not (len(output_names) == C.shape[0] and D.shape[0] == len(output_names)):
            raise ValueError('Invalid number of outputs')
        return True

    def create_Upartition(self, Upartition_name, **Uvar_groups):
        input_check: list[int] = list()
        if Upartition_name in self.input_partitions:
            raise ValueError('partition named "%s" is already existing' % Upartition_name)
        self.input_partitions[Upartition_name] = list()
        for input_group_name in Uvar_groups:
            if input_group_name in self.input_groups_indices:
                raise ValueError('group named "%s" is already existing' % input_group_name)
            self.input_partitions[Upartition_name].append(input_group_name)
            input_variable_group_indices = list()
            for input_variable in Uvar_groups[input_group_name]:
                i = self.input_names.index(input_variable)
                input_check.append(i)
                input_variable_group_indices.append(i)
            self.input_groups_indices[input_group_name] = input_variable_group_indices
        input_check.sort()
        if self.A is not None and not (len(input_check) == self.n_inputs and input_check[-1] == self.n_inputs-1):
            raise ValueError('Variable of partition "%s" do not form a partition' % Upartition_name)

    def create_Yselection(self, output_selection_name: str, *selected_outputs: str):
        if output_selection_name in self.output_selections:
            raise ValueError('Output selection "%s" is already existing' % output_selection_name)
        self.output_selections[output_selection_name] = list()
        for output_name in selected_outputs:
            i: int = self.output_names.index(output_name)
            if i in self.output_selections[output_selection_name]:
                raise ValueError('Output variable has already been selected')
            self.output_selections[output_selection_name].append(i)

    def matrices(self, input_partition_name: str = '', output_selection_name: str = ''):
        state_model = {'A': self.A}

        if output_selection_name == '':
            output_variable_indices = [i for i in range(self.n_outputs)]
            state_model['Y'] = self.output_names
            state_model['C'] = self.C
        else:
            output_variable_indices = self.output_selections[output_selection_name]
            state_model['Y'] = [self.output_names[i] for i in output_variable_indices]
            state_model['C'] = self.C[output_variable_indices, :]

        if input_partition_name == '':
            state_model['U'] = self.input_names
            state_model['B'] = self.B
            state_model['D'] = self.D[output_variable_indices, :]
        else:
            for input_group in self.input_partitions[input_partition_name]:
                input_variable_indices: list[int] = self.input_groups_indices[input_group]
                state_model['U_%s' % input_group] = [self.input_names[i] for i in input_variable_indices]
                state_model['B_%s' % input_group] = self.B[:, tuple(input_variable_indices)]
                state_model['D_%s' % input_group] = self.D[numpy.ix_(output_variable_indices, input_variable_indices)]

        state_model['Ts'] = self.sample_time_in_seconds
        state_model['n_states'] = self.A.shape[0]
        state_model['n_inputs'] = self.n_inputs
        state_model['n_outputs'] = self.n_outputs
        return state_model

    def __str__(self) -> str:
        string: str = ''
        maxval = 4
        if self.A is not None:
            n_states: int = self.A.shape[0]
            n_inputs: int = self.B.shape[1]
            n_outputs: int = self.C.shape[0]
            string += 'Recurrent State Model (Ts=%i, n_states=%i): \n X_{k+1} = A X_k + B U_k\n Y_k = C X_k + D U_k\nwith (%s):\nA...=\n' % (self.sample_time_in_seconds,  n_states, 'full' if n_states <= maxval else 'excerpt')
            string += str(self.A[0:min(maxval, n_states), 0:min(maxval, n_states)]) + '\n B...=\n' + str(self.B[0:min(maxval, n_states), 0:min(maxval, n_inputs)]) + '\n C....=\n' + str(self.C[0:min(maxval, n_outputs), 0:min(maxval, n_states)]) + '\n D...=\n' + str(self.D[0:min(maxval, n_outputs), 0:min(maxval, n_inputs)]) + '\n'
            string += 'U (n_inputs=%i): ' % (len(self.input_names)) + ','.join(self.input_names) + '\n'
            string += 'Y (n_outputs=%i): ' % (len(self.output_names)) + ','.join(self.output_names) + '\n'
            string += '\nStatic gain matrix: Y = G U\n'
            try:
                I_minus_A = numpy.matrix(numpy.eye(n_states)) - self.A
                try:
                    I_minus_A_inv = numpy.linalg.inv(I_minus_A)
                except numpy.linalg.LinAlgError:
                    # Use pseudo-inverse if matrix is singular
                    I_minus_A_inv = scipy.linalg.pinv(I_minus_A, atol=1e-10)
                G = self.C * I_minus_A_inv * self.B + self.D
                string += G.__str__() + '\n'
                vps, VPs = numpy.linalg.eig(self.A)
                string += '\n Number of steps for an attenuation of 90%: '
                string += ','.join([str(round(math.log(0.1)/math.log(numpy.absolute(vp)), 2)) for vp in vps])
                string += '\nOrder is: %i' % len(vps)
            except:  # noqa
                pass
        else:
            string += 'Static Model: \n  Y_k = D U_k\nwith:\nD=\n' + str(self.D) + '\n'
            string += 'U (n_inputs=%i): ' % (len(self.input_names)) + ','.join(self.input_names) + '\n'
            string += 'Y (n_outputs=%i): ' % (len(self.output_names)) + ','.join(self.output_names)
        return string

    def simulate(self, data_provider: DataProvider, suffix: str = None) -> None:
        # Ensure suffix follows naming convention: prepend '#' if not present and suffix is not empty
        if suffix and not suffix.startswith('#'):
            suffix = '#' + suffix

        simulated_outputs: dict[str, list[float]] = {variable_name: list() for variable_name in self.output_names}
        X = None
        output_names: list[str] = self.output_names
        for k in range(len(data_provider)):
            current_input_values: dict[str, float] = {input_name: data_provider(input_name, k) for input_name in self.input_names}
            if X is None:
                X: numpy.matrix = self.initialize(**current_input_values)
            self.set_state(X)
            [simulated_outputs[output_names[i]].append(val) for i, val in enumerate(self.output(**current_input_values))]
            X = self.step(**current_input_values)
        for output_name in output_names:
            if suffix is None:
                data_provider.add_var(output_name + '#SIM', simulated_outputs[output_name])
            else:
                data_provider.add_var(output_name + suffix, simulated_outputs[output_name])
