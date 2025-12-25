"""Nonlinear regression and NARX neural network model design helper for building energy analysis.

This module provides comprehensive tools for designing and implementing Nonlinear AutoRegressive
with eXogenous inputs (NARX) models using artificial neural networks for building energy analysis
and system identification. It includes MLP-NARX (Multi-Layer Perceptron NARX) parameter estimation,
model validation, and sliding window analysis for time-varying system behavior in building energy systems.

The module provides:
- NonlinearRegression: Main class for NARX neural network model design and parameter estimation
- narx_estimation: Function for standard NARX model estimation with training and validation
- sliding_narx_estimation: Function for sliding window NARX analysis for time-varying systems

Key features:
- NARX model structure design with configurable input/output delays
- Multi-layer perceptron neural network parameter estimation
- Multi-output support for predicting indoor temperature and CO2 concentration simultaneously
- Recurrent NARX structure with dynamic feedback
- Model validation with training and validation datasets
- Sliding window analysis for time-varying system behavior
- Automated report generation with model performance metrics
- Integration with building energy data providers and measurement systems
- Support for multiple input variables with different delay structures
- Model simulation and prediction capabilities
- Statistical analysis and impact assessment of model parameters
- Visualization tools for model performance and parameter analysis

The module is designed for building energy analysis, system identification, and
model-based control applications in building energy management systems.

Author: stephane.ploix@g-scop.grenoble-inp.fr
License: GNU General Public License v3.0
"""
from __future__ import annotations
import copy
import math
import matplotlib
import matplotlib.pyplot
import numpy
import numpy.linalg
import os
import shutil
import sys
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from batem.core.data import DataProvider
from batem.core.utils import PlotSaver
from batem.core.library import Setup


class NonlinearRegression:
    """NARX neural network model design and parameter estimation class for building energy analysis.

    This class provides comprehensive functionality for designing and implementing
    Nonlinear AutoRegressive with eXogenous inputs (NARX) models using MLP neural networks
    for building energy systems. It supports configurable model structures, parameter estimation,
    validation, and simulation capabilities for system identification and model-based control.
    Supports multi-output prediction for indoor temperature and CO2 concentration.
    """

    def __init__(self, input_labels: list[str], output_labels: list[str], minimum_input_delay: int, inputs_maximum_delays: int | tuple[int], output_maximum_delay: int, hidden_layer_sizes: tuple[int, ...] = (50, 50), activation: str = 'tanh', solver: str = 'adam', alpha: float = 0.0001, batch_size: int | str = 'auto', learning_rate: str = 'constant', learning_rate_init: float = 0.001, max_iter: int = 200, shuffle: bool = True, random_state: int | None = None, tol: float = 0.0001, verbose: bool = False, warm_start: bool = False, momentum: float = 0.9, nesterovs_momentum: bool = True, early_stopping: bool = False, validation_fraction: float = 0.1, beta_1: float = 0.9, beta_2: float = 0.999, epsilon: float = 1e-08, n_iter_no_change: int = 10, max_fun: int = 15000):
        """Estimate nonlinear regression coefficients for a dataset using NARX neural network.

        The meta-parameters for tuning the NARX model structure are:
            minimum_input_delay = 1
            inputs_maximum_delays = [2 3] (if a single int value, 4 for instance, is used, it would be equal to [4 4])
            output_maximum_delay = 3
        we can get the following NARX structure:
            y{k} = f(y{k-1}, y{k-2}, y{k-3} (output_maximum_delay),
                     u1{k-1} (minimum_input_delay), u1{k-2} (inputs_maximum_delays[0]),
                     u2{k-1} (minimum_input_delay), u2{k-2}, u2{k-3} (inputs_maximum_delays[1]))

        :param input_labels: input variable names
        :type input_labels: list[str]
        :param output_labels: output variable names (for multi-output prediction, e.g., ['temperature', 'CO2'])
        :type output_labels: list[str]
        :param minimum_input_delay: int standing for the delay_order variable represents the time delay to the system
        :type minimum_input_delay: int
        :param inputs_maximum_delays: int or list standing for the num_orders variable represents the order for the different inputs
        :type inputs_maximum_delays: int | tuple[int]
        :param output_maximum_delay: int standing for the den_order variable represents the order for the output
        :type output_maximum_delay: int
        :param hidden_layer_sizes: The ith element represents the number of neurons in the ith hidden layer
        :type hidden_layer_sizes: tuple[int, ...]
        :param activation: Activation function for the hidden layer ('identity', 'logistic', 'tanh', 'relu')
        :type activation: str
        :param solver: The solver for weight optimization ('lbfgs', 'sgd', 'adam')
        :type solver: str
        :param alpha: L2 penalty (regularization term) parameter
        :type alpha: float
        :param batch_size: Size of minibatches for stochastic optimizers
        :type batch_size: int | str
        :param learning_rate: Learning rate schedule for weight updates
        :type learning_rate: str
        :param learning_rate_init: The initial learning rate used
        :type learning_rate_init: float
        :param max_iter: Maximum number of iterations
        :type max_iter: int
        :param shuffle: Whether to shuffle samples in each iteration
        :type shuffle: bool
        :param random_state: Random state for reproducibility
        :type random_state: int | None
        :param tol: Tolerance for the optimization
        :type tol: float
        :param verbose: Whether to print progress messages
        :type verbose: bool
        :param warm_start: When set to True, reuse the solution of the previous call to fit as initialization
        :type warm_start: bool
        :param momentum: Momentum for gradient descent update (only used when solver='sgd')
        :type momentum: float
        :param nesterovs_momentum: Whether to use Nesterov's momentum (only used when solver='sgd')
        :type nesterovs_momentum: bool
        :param early_stopping: Whether to use early stopping to terminate training when validation score is not improving
        :type early_stopping: bool
        :param validation_fraction: The proportion of training data to set aside as validation set for early stopping
        :type validation_fraction: float
        :param beta_1: Exponential decay rate for estimates of first moment vector in adam (only used when solver='adam')
        :type beta_1: float
        :param beta_2: Exponential decay rate for estimates of second moment vector in adam (only used when solver='adam')
        :type beta_2: float
        :param epsilon: Value for numerical stability in adam (only used when solver='adam')
        :type epsilon: float
        :param n_iter_no_change: Maximum number of epochs to not meet tol improvement (only used when solver='sgd' or 'adam')
        :type n_iter_no_change: int
        :param max_fun: Maximum number of loss function calls (only used when solver='lbfgs')
        :type max_fun: int
        """
        self.__input_labels = input_labels
        self.__number_of_inputs = len(input_labels)
        self.__output_labels = output_labels
        self.__number_of_outputs = len(output_labels)
        if type(inputs_maximum_delays) is int:
            inputs_maximum_delays = [inputs_maximum_delays for i in range(len(input_labels))]
        self.__inputs_maximum_delays = [max(minimum_input_delay, num_order) for num_order in inputs_maximum_delays]
        self.__output_maximum_delay = output_maximum_delay
        self.__input_minimum_delay = minimum_input_delay
        self.__hidden_layer_sizes = hidden_layer_sizes
        self.__activation = activation
        self.__solver = solver
        self.__alpha = alpha
        self.__batch_size = batch_size
        self.__learning_rate = learning_rate
        self.__learning_rate_init = learning_rate_init
        self.__max_iter = max_iter
        self.__shuffle = shuffle
        self.__random_state = random_state
        self.__tol = tol
        self.__verbose = verbose
        self.__warm_start = warm_start
        self.__momentum = momentum
        self.__nesterovs_momentum = nesterovs_momentum
        self.__early_stopping = early_stopping
        self.__validation_fraction = validation_fraction
        self.__beta_1 = beta_1
        self.__beta_2 = beta_2
        self.__epsilon = epsilon
        self.__n_iter_no_change = n_iter_no_change
        self.__max_fun = max_fun
        self.__model: MLPRegressor | None = None
        self.__input_scaler: StandardScaler | None = None
        self.__output_scaler: StandardScaler | None = None
        self.__feature_names: list[str] = []

    def learn(self, list_of_input_values: list[list[float]], list_of_output_values: list[list[float]]):
        """Estimate the parameters of the nonlinear regression according to the structure specified in the initializer.

        :param list_of_input_values: list of variable data to be used for input variables where size = number of input variables x number of data
        :type list_of_input_values: list[list[float]]
        :param list_of_output_values: list of variable data to be used for output variables where size = number of output variables x number of data
        :type list_of_output_values: list[list[float]]
        """
        __number_of_values = len(list_of_output_values[0])
        for output_values in list_of_output_values:
            if len(output_values) != __number_of_values:
                raise ValueError('All output variables must have the same number of values')
        for input_values in list_of_input_values:
            if len(input_values) != __number_of_values:
                raise ValueError('All input variables must have the same number of values as output variables')

        __X_matrix = list()
        __Y_matrix = list()
        max_delay = max(self.__output_maximum_delay, max(self.__inputs_maximum_delays))
        self.__feature_names = []
        for k in range(max_delay, __number_of_values):
            __X_matrix_row = list()
            # Add autoregressive terms (delayed outputs)
            for i in range(self.__output_maximum_delay):
                for output_idx in range(self.__number_of_outputs):
                    __X_matrix_row.append(list_of_output_values[output_idx][k - i - 1])
                    if k == max_delay:
                        self.__feature_names.append(f'{self.__output_labels[output_idx]}{{k-{i+1}}}')
            # Add exogenous terms (delayed inputs)
            for j in range(self.__number_of_inputs):
                for i in range(self.__inputs_maximum_delays[j] - self.__input_minimum_delay + 1):
                    delay = i + self.__input_minimum_delay
                    __X_matrix_row.append(list_of_input_values[j][k - delay])
                    if k == max_delay:
                        self.__feature_names.append(f'{self.__input_labels[j]}{{k-{delay}}}')
            __X_matrix.append(__X_matrix_row)
            # Prepare output matrix (current outputs)
            __Y_matrix_row = [list_of_output_values[output_idx][k] for output_idx in range(self.__number_of_outputs)]
            __Y_matrix.append(__Y_matrix_row)

        __X_matrix: numpy.ndarray = numpy.array(__X_matrix)
        __Y_matrix: numpy.ndarray = numpy.array(__Y_matrix)

        # Scale inputs and outputs
        self.__input_scaler = StandardScaler()
        __X_matrix_scaled = self.__input_scaler.fit_transform(__X_matrix)
        self.__output_scaler = StandardScaler()
        __Y_matrix_scaled = self.__output_scaler.fit_transform(__Y_matrix)

        # Create and train MLP model
        self.__model = MLPRegressor(hidden_layer_sizes=self.__hidden_layer_sizes, activation=self.__activation, solver=self.__solver, alpha=self.__alpha, batch_size=self.__batch_size, learning_rate=self.__learning_rate, learning_rate_init=self.__learning_rate_init, max_iter=self.__max_iter, shuffle=self.__shuffle, random_state=self.__random_state, tol=self.__tol, verbose=self.__verbose, warm_start=self.__warm_start, momentum=self.__momentum, nesterovs_momentum=self.__nesterovs_momentum, early_stopping=self.__early_stopping, validation_fraction=self.__validation_fraction, beta_1=self.__beta_1, beta_2=self.__beta_2, epsilon=self.__epsilon, n_iter_no_change=self.__n_iter_no_change, max_fun=self.__max_fun)
        self.__model.fit(__X_matrix_scaled, __Y_matrix_scaled)

    @property
    def model(self):
        """Get the trained MLPRegressor model.

        :return: trained MLPRegressor model
        :rtype: MLPRegressor | None
        """
        return self.__model

    @property
    def maximum_delay(self) -> int:
        """Estimate the maximum delay considering delays in output but also in all inputs.

        :return: the maximum delay considering delays in output but also in all inputs
        :rtype: int
        """
        __maximum_delay = 0
        if self.__output_maximum_delay > 0:
            __maximum_delay = self.__output_maximum_delay
        for input_delay in self.__inputs_maximum_delays:
            __maximum_delay = max(__maximum_delay, input_delay)
        return __maximum_delay

    def simulate(self, list_of_inputs_values: list[list[float]], list_of_initial_output_values: list[list[float]] | None = None):
        """Simulate the output response using input values and estimated (with learn) nonlinear regression.

        Uses recurrent NARX structure where past predicted outputs are fed back as inputs.

        :param list_of_inputs_values: list of variable data to be used for input variables where size = number of input variables x number of data
        :type list_of_inputs_values: list[list[float]]
        :param list_of_initial_output_values: list of variable data to be used for output variables to initialize the nonlinear regression, where size = number of output variables x (maximum delay) (values corresponding to index > maximum delay are ignored). If None, zeros will be used. Default to None
        :type list_of_initial_output_values: list[list[float]] | None
        :return: simulated outputs with learnt nonlinear regression, list of lists where each inner list is one output variable
        :rtype: list[list[float]]
        """
        if self.__model is None:
            raise ValueError('Model has not been trained. Call learn() first.')
        number_of_samples = len(list_of_inputs_values[0])
        for i in range(1, len(list_of_inputs_values)):
            if len(list_of_inputs_values[i]) != number_of_samples:
                raise ValueError('All input variables must have the same number of values')
        if list_of_initial_output_values is None:
            estimated_output_values = [[0.0 for _ in range(self.maximum_delay + 1)] for _ in range(self.__number_of_outputs)]
        else:
            estimated_output_values = [[list_of_initial_output_values[output_idx][i] if i < len(list_of_initial_output_values[output_idx]) else list_of_initial_output_values[output_idx][-1] for i in range(self.maximum_delay + 1)] for output_idx in range(self.__number_of_outputs)]

        for k in range(self.maximum_delay + 1, number_of_samples):
            # Build feature vector using predicted outputs (recurrent structure)
            __X_matrix_row = list()
            # Add autoregressive terms (delayed outputs - use predicted values)
            for i in range(self.__output_maximum_delay):
                for output_idx in range(self.__number_of_outputs):
                    __X_matrix_row.append(estimated_output_values[output_idx][k - i - 1])
            # Add exogenous terms (delayed inputs)
            for j in range(self.__number_of_inputs):
                for i in range(self.__inputs_maximum_delays[j] - self.__input_minimum_delay + 1):
                    delay = i + self.__input_minimum_delay
                    __X_matrix_row.append(list_of_inputs_values[j][k - delay])
            __X_matrix_row: numpy.ndarray = numpy.array([__X_matrix_row])
            # Scale input
            __X_matrix_row_scaled = self.__input_scaler.transform(__X_matrix_row)
            # Predict
            __Y_matrix_row_scaled = self.__model.predict(__X_matrix_row_scaled)
            # Inverse scale output
            __Y_matrix_row = self.__output_scaler.inverse_transform(__Y_matrix_row_scaled)
            # Store predictions
            for output_idx in range(self.__number_of_outputs):
                estimated_output_values[output_idx].append(float(__Y_matrix_row[0][output_idx]))

        return estimated_output_values

    def sliding(self, list_of_inputs_values: list[list[float]], list_of_output_values: list[list[float]], time_slice_size: int = 24, minimum_time_slices: int = 15, time_slice_memory: int | None = None, log: bool = True):
        """Simulate with sliding window jumping from time slice to time slice to learn new parameters of nonlinear regression and predict output.

        :param list_of_inputs_values: list of variable data to be used for input variables where size = number of input variables x number of data
        :type list_of_inputs_values: list[list[float]]
        :param list_of_output_values: list of variable data to be used for output variables, where size = number of output variables x number of data
        :type list_of_output_values: list[list[float]]
        :param time_slice_size: size of the time slice (default: 24) usually corresponding to one day
        :type time_slice_size: int
        :param minimum_time_slices: the initial number of time slices used to learn parameters. If too small, it will generate an error. Default to 15
        :type minimum_time_slices: int
        :param time_slice_memory: maximum number of time slices kept for learning parameters. If smaller then minimum_time_slices, time_slice_memory will be set to minimum_time_slices. Default is None, which means no memory limitation. Default to None
        :type time_slice_memory: int | None
        :param log: log results if True. Default is True
        :type log: bool
        :return: estimated outputs simulated per time slice, list of lists where each inner list is one output variable
        :rtype: list[list[float]]
        """
        if time_slice_memory is not None:
            time_slice_memory = max(time_slice_memory, minimum_time_slices)
        inputs_slices = [NonlinearRegression.__extract_inputs(k, (k + 1) * time_slice_size, list_of_inputs_values) for k in range(0, minimum_time_slices * time_slice_size, time_slice_size)]
        outputs_slices = [NonlinearRegression.__extract_outputs(k, (k + 1) * time_slice_size, list_of_output_values) for k in range(0, minimum_time_slices * time_slice_size, time_slice_size)]
        estimated_outputs = [[list_of_output_values[output_idx][k] for k in range(minimum_time_slices * time_slice_size)] for output_idx in range(self.__number_of_outputs)]
        for k in range(minimum_time_slices * time_slice_size, len(list_of_output_values[0]), time_slice_size):
            merged_inputs = NonlinearRegression.__merge_inputs(inputs_slices)
            merged_outputs = NonlinearRegression.__merge_outputs(outputs_slices)
            self.learn(merged_inputs, merged_outputs)
            if log:
                print(f'Learned model at time slice starting at index {k}')
            inputs_slices.append(NonlinearRegression.__extract_inputs(k, k + time_slice_size, list_of_inputs_values))
            all_estimated_outputs = self.simulate(NonlinearRegression.__merge_inputs(inputs_slices), estimated_outputs)
            for output_idx in range(self.__number_of_outputs):
                estimated_outputs[output_idx].extend(all_estimated_outputs[output_idx][-time_slice_size:])
            outputs_slices.append(NonlinearRegression.__extract_outputs(k, k + time_slice_size, list_of_output_values))
            if time_slice_memory is not None and len(outputs_slices) > time_slice_memory:
                inputs_slices = inputs_slices[-time_slice_memory:]
                outputs_slices = outputs_slices[-time_slice_memory:]
        return estimated_outputs

    @staticmethod
    def __extract_inputs(from_k: int, to_k: int, list_of_input_values: list[list[float]]):
        """Extract a slice of time for the input data.

        :param from_k: beginning of the time slice
        :type from_k: int
        :param to_k: end of the time slice
        :type to_k: int
        :param list_of_input_values: input data
        :type list_of_input_values: list[list[float]]
        :return: time slice of the input data
        :rtype: list[list[float]]
        """
        extracted_inputs = list()
        for i in range(len(list_of_input_values)):
            extracted_inputs.append(list_of_input_values[i][from_k:to_k])
        return extracted_inputs

    @staticmethod
    def __extract_outputs(from_k: int, to_k: int, list_of_output_values: list[list[float]]):
        """Extract a slice of time for the output data.

        :param from_k: beginning of the time slice
        :type from_k: int
        :param to_k: end of the time slice
        :type to_k: int
        :param list_of_output_values: output data
        :type list_of_output_values: list[list[float]]
        :return: time slice of the output data
        :rtype: list[list[float]]
        """
        extracted_outputs = list()
        for output_idx in range(len(list_of_output_values)):
            extracted_outputs.append(list_of_output_values[output_idx][from_k:to_k])
        return extracted_outputs

    @staticmethod
    def __merge_inputs(list_of_inputs_slices: list[list[list[float]]]):
        """Merge several input time slices into a single one.

        :param list_of_inputs_slices: time slices
        :type list_of_inputs_slices: list[list[list[float]]]
        :return: an unique time slice, which is the concatenation of the slices, respected to order with which they have been provided
        :rtype: list[list[float]]
        """
        merged_inputs = copy.deepcopy(list_of_inputs_slices[0])
        for j in range(1, len(list_of_inputs_slices)):
            for i in range(len(list_of_inputs_slices[0])):
                merged_inputs[i].extend(list_of_inputs_slices[j][i])
        return merged_inputs

    @staticmethod
    def __merge_outputs(list_of_output_slices: list[list[list[float]]]):
        """Merge several output time slices into a single one.

        :param list_of_output_slices: time slices
        :type list_of_output_slices: list[list[list[float]]]
        :return: an unique time slice, which is the concatenation of the slices, respected to order with which they have been provided
        :rtype: list[list[float]]
        """
        merged_outputs = copy.deepcopy(list_of_output_slices[0])
        for j in range(1, len(list_of_output_slices)):
            for output_idx in range(len(list_of_output_slices[0])):
                merged_outputs[output_idx].extend(list_of_output_slices[j][output_idx])
        return merged_outputs

    def __str__(self):
        """Return a descriptive string of the nonlinear regression.

        :return: text representation
        """
        string = 'NARX Neural Network Model\n'
        string += f'Outputs: {", ".join(self.__output_labels)}\n'
        string += f'Inputs: {", ".join(self.__input_labels)}\n'
        string += f'Output maximum delay: {self.__output_maximum_delay}\n'
        string += f'Input delays: {self.__inputs_maximum_delays}\n'
        string += f'Network architecture: {self.__hidden_layer_sizes}\n'
        string += f'Activation: {self.__activation}\n'
        string += f'Solver: {self.__solver}\n'
        if self.__model is not None:
            string += 'Model trained: Yes\n'
            string += f'Loss: {self.__model.loss_}\n'
            string += f'Iterations: {self.__model.n_iter_}\n'
        else:
            string += 'Model trained: No\n'
        return string

    def error_analysis(self, list_of_inputs_values: list[list[float]], list_of_actual_output_values: list[list[float]], list_of_estimated_output_values: list[list[float]], maxlags: int = 10, folder_name: str = 'log'):
        """Analyse the error of estimation by characterizing error, and analyzing correlations with input and auto-correlation of the output.

        :param list_of_inputs_values: input data values
        :type list_of_inputs_values: list[list[float]]
        :param list_of_actual_output_values: actual recorded output values (list of lists, one per output)
        :type list_of_actual_output_values: list[list[float]]
        :param list_of_estimated_output_values: estimated values with the learnt nonlinear regression (list of lists, one per output)
        :type list_of_estimated_output_values: list[list[float]]
        :param maxlags: optional parameter used for cross correlation, default is 10.
        :type maxlags: int
        :param folder_name: folder name for saving plots
        :type folder_name: str
        """
        for output_idx, output_label in enumerate(self.__output_labels):
            number_of_data = len(list_of_actual_output_values[output_idx])
            output_errors = [list_of_actual_output_values[output_idx][_] - list_of_estimated_output_values[output_idx][_] for _ in range(number_of_data)]
            mse = mean_squared_error(list_of_actual_output_values[output_idx], list_of_estimated_output_values[output_idx])
            r2 = r2_score(list_of_actual_output_values[output_idx], list_of_estimated_output_values[output_idx])
            print(f'## Error Analysis for {output_label}')
            print(f'* Average output error = {sum(output_errors) / len(output_errors):.6f}')
            print(f'* Average absolute output error = {sum([abs(error) for error in output_errors]) / len(output_errors):.6f}')
            print(f'* MSE = {mse:.6f}')
            print(f'* R² score = {r2:.6f}')
            print(f'* RMSE = {math.sqrt(mse):.6f}')
            print(f'* Max output error = {max(output_errors):.6f}')
            print(f'* Min output error = {min(output_errors):.6f}')
            print(f'* Standard deviation for output error = {numpy.std(output_errors):.6f}')
            sorted_output_errors = output_errors.copy()
            sorted_output_errors.sort()
            output_errors10 = sorted_output_errors[0: int(number_of_data / 10)]
            output_errors90 = sorted_output_errors[number_of_data - int(number_of_data/10): number_of_data]
            print(f'* 10% lowest error average = {sum(output_errors10)/len(output_errors10):.6f}')
            print(f'* 90% highest error average = {sum(output_errors90)/len(output_errors10):.6f}')

            # Histogram
            fig = matplotlib.pyplot.figure()
            fig.suptitle(f'Output error Histogram - {output_label}')
            axes = fig.add_subplot(1, 1, 1)
            axes.hist(output_errors, bins=50)
            axes.set_ylabel('Frequency')
            fig.tight_layout()
            matplotlib.pyplot.savefig(f'{folder_name}histogram_{output_label}.png')
            print('* Histogram')
            print(f'![histogram](histogram_{output_label}.png)')

            # Trend analysis
            number_of_rows = math.ceil(math.sqrt(self.__number_of_inputs))
            number_of_columns = math.ceil(self.__number_of_inputs / number_of_rows) if number_of_rows > 0 else 1
            if self.__number_of_inputs > 0:
                fig = matplotlib.pyplot.figure()
                fig.suptitle(f'Trend analysis - {output_label}')
                for i in range(self.__number_of_inputs):
                    axes1 = fig.add_subplot(number_of_rows, number_of_columns, i + 1)
                    axes1.set_xlabel('time')
                    axes1.set_ylabel('output errors', color='tab:red')
                    axes1.plot([i for i in range(number_of_data)], output_errors, color='tab:red')
                    axes1.tick_params(axis='y', labelcolor='tab:red')
                    axes1.grid()
                    axes2 = axes1.twinx()
                    axes2.set_ylabel(self.__input_labels[i], color='tab:blue')
                    axes2.plot([i for i in range(number_of_data)], list_of_inputs_values[i], color='tab:blue')
                    axes2.tick_params(axis='y', labelcolor='tab:blue')
                fig.tight_layout()
                matplotlib.pyplot.savefig(f'{folder_name}trends_{output_label}.png')
                print('* Trends')
                print(f'![trends](trends_{output_label}.png)')

            # Auto-correlation
            fig, axes = matplotlib.pyplot.subplots()
            fig.suptitle(f"Auto-correlation error - {output_label}")
            axes.acorr(output_errors, normed=True, usevlines=True, maxlags=maxlags)
            axes.set_xlim([-maxlags - 0.5, maxlags + 0.5])
            axes.grid()
            fig.tight_layout()
            matplotlib.pyplot.savefig(f'{folder_name}autocorrelations_{output_label}.png')
            print('* Auto-correlations error')
            print(f'![correlations](autocorrelations_{output_label}.png)')

            # Cross correlation
            if self.__number_of_inputs > 0:
                fig, axes = matplotlib.pyplot.subplots()
                fig.suptitle(f'Cross correlation inputs-error analysis - {output_label}')
                for i in range(self.__number_of_inputs):
                    axes = fig.add_subplot(number_of_rows, number_of_columns, i + 1)
                    axes.set_xlabel(self.__input_labels[i])
                    axes.xcorr(output_errors, list_of_inputs_values[i], normed=True, usevlines=True, maxlags=maxlags)
                    axes.set_xlim([-maxlags - 0.5, 0.5])
                    axes.grid()
                fig.tight_layout()
                matplotlib.pyplot.savefig(f'{folder_name}cross-correlations_{output_label}.png')
                print('* Cross correlations inputs-errors')
                print(f'![correlations](cross-correlations_{output_label}.png)')


def narx_estimation(output_variable_name: str | list[str], input_variable_names: list[str], training_data: DataProvider, validation_data: DataProvider, minimum_input_delay: int, inputs_maximum_delays: list[int] | int, output_maximum_delay: int, hidden_layer_sizes: tuple[int, ...] = (50, 50), activation: str = 'tanh', solver: str = 'adam', max_iter: int = 200, **kwargs) -> NonlinearRegression:
    """Perform standard NARX model estimation with training and validation datasets.

    This function performs comprehensive NARX model estimation using training and validation
    datasets. It creates a NonlinearRegression model, estimates parameters, validates the model,
    and generates detailed reports with performance metrics and visualizations.
    Supports both single output (like ARX) and multi-output prediction.

    :param output_variable_name: Name(s) of the output variable(s) to model. Can be a single string for single output (like ARX) or a list of strings for multi-output (e.g., ['temperature', 'CO2'])
    :type output_variable_name: str | list[str]
    :param input_variable_names: List of input variable names
    :type input_variable_names: list[str]
    :param training_data: DataProvider containing training dataset
    :type training_data: DataProvider
    :param validation_data: DataProvider containing validation dataset
    :type validation_data: DataProvider
    :param minimum_input_delay: Minimum delay for input variables
    :type minimum_input_delay: int
    :param inputs_maximum_delays: Maximum delays for each input variable (can be int or list)
    :type inputs_maximum_delays: list[int] | int
    :param output_maximum_delay: Maximum delay for output variable
    :type output_maximum_delay: int
    :param hidden_layer_sizes: The ith element represents the number of neurons in the ith hidden layer
    :type hidden_layer_sizes: tuple[int, ...]
    :param activation: Activation function for the hidden layer
    :type activation: str
    :param solver: The solver for weight optimization
    :type solver: str
    :param max_iter: Maximum number of iterations
    :type max_iter: int
    :param kwargs: Additional keyword arguments passed to NonlinearRegression
    :return: Trained NonlinearRegression model
    :rtype: NonlinearRegression
    """
    # Normalize output_variable_name to always be a list for internal processing
    if isinstance(output_variable_name, str):
        output_variable_names = [output_variable_name]
        single_output = True
    else:
        output_variable_names = output_variable_name
        single_output = False

    # Normalize inputs_maximum_delays to always be a list
    if isinstance(inputs_maximum_delays, int):
        inputs_maximum_delays_list = [inputs_maximum_delays for _ in range(len(input_variable_names))]
    else:
        inputs_maximum_delays_list = inputs_maximum_delays

    folder_name: str = Setup.data('folders', 'results') + 'nlreg/'
    if os.path.isdir(folder_name):
        shutil.rmtree(folder_name)
    os.mkdir(folder_name)
    original = sys.stdout
    sys.stdout = open(folder_name + "results.md", 'w')

    print("# Nonlinear Regression (NARX Neural Network)")
    print(f'* minimum_input_delay: {minimum_input_delay}')
    print(f'* inputs_maximum_delays: {inputs_maximum_delays_list}')
    print(f'* output_maximum_delay: {output_maximum_delay}')
    print(f'* hidden_layer_sizes: {hidden_layer_sizes}')
    print(f'* activation: {activation}')
    print(f'* solver: {solver}')
    print(f'* max_iter: {max_iter}')

    print('## Training')

    nonlinear_regression = NonlinearRegression(input_labels=input_variable_names, output_labels=output_variable_names, minimum_input_delay=minimum_input_delay, inputs_maximum_delays=inputs_maximum_delays_list, output_maximum_delay=output_maximum_delay, hidden_layer_sizes=hidden_layer_sizes, activation=activation, solver=solver, max_iter=max_iter, **kwargs)

    training_inputs = [training_data.series(data_label) for data_label in input_variable_names]
    training_outputs = [training_data.series(data_label) for data_label in output_variable_names]
    nonlinear_regression.learn(training_inputs, training_outputs)

    output_training = nonlinear_regression.simulate(training_inputs, training_outputs)
    for output_idx, output_name in enumerate(output_variable_names):
        training_data.add_var(output_name + '_learnt', output_training[output_idx])
    plot_saver_training = PlotSaver(training_data.datetimes, training_data.variables_data())
    filename: str = 'simulate_training'
    if single_output:
        # For single output, match ARX behavior exactly
        plot_vars = [output_variable_names[0], output_variable_names[0] + '_learnt']
    else:
        plot_vars = output_variable_names + [name + '_learnt' for name in output_variable_names]
    plot_saver_training.time_plot(plot_vars, filename=folder_name + filename)
    print('![](%s.png)' % filename)

    print('## model')
    print(nonlinear_regression)

    print('## Error Analysis on Training Data')
    nonlinear_regression.error_analysis(training_inputs, training_outputs, output_training, maxlags=10, folder_name=folder_name)

    print('## Testing')

    testing_inputs = [validation_data.series(data_label) for data_label in input_variable_names]
    testing_outputs = [validation_data.series(data_label) for data_label in output_variable_names]
    output_estimated = nonlinear_regression.simulate(testing_inputs, testing_outputs)
    for output_idx, output_name in enumerate(output_variable_names):
        validation_data.add_var(output_name + '_estimated', output_estimated[output_idx])
    plot_saver_testing = PlotSaver(validation_data.datetimes, validation_data.variables_data())
    filename: str = 'simulate_testing'
    if single_output:
        # For single output, match ARX behavior exactly
        plot_vars = [output_variable_names[0], output_variable_names[0] + '_estimated']
        plot_saver_testing.time_plot(plot_vars, folder_name + filename)
        print('![](%s.png)' % filename)
        print(f'* Estimated {output_variable_names[0]} at testing')
        print(f'![Testing {output_variable_names[0]}](output_testing.png)')
    else:
        plot_vars = output_variable_names + [name + '_estimated' for name in output_variable_names]
        plot_saver_testing.time_plot(plot_vars, folder_name + filename)
        print('![](%s.png)' % filename)

    print('## Error Analysis on Testing Data')
    nonlinear_regression.error_analysis(testing_inputs, testing_outputs, output_estimated, maxlags=10, folder_name=folder_name)

    sys.stdout.close()
    sys.stdout = original
    return nonlinear_regression


def sliding_narx_estimation(output_variable_names: list[str], input_variable_names: list[str], data_container: DataProvider, minimum_input_delay: int, inputs_maximum_delays: list[int] | int, output_maximum_delay: int, slice_size: int = 24, minimum_slices: int = 12, slice_memory: int = 24*7, hidden_layer_sizes: tuple[int, ...] = (50, 50), activation: str = 'tanh', solver: str = 'adam', max_iter: int = 200, **kwargs):
    """Perform sliding window NARX model estimation for time-varying system analysis.

    This function performs sliding window NARX model estimation to analyze time-varying
    system behavior in building energy systems. It uses a moving window approach to
    estimate model parameters over time, allowing for detection of system changes
    and adaptive modeling capabilities.

    :param output_variable_names: Names of the output variables to model
    :type output_variable_names: list[str]
    :param input_variable_names: List of input variable names
    :type input_variable_names: list[str]
    :param data_container: DataProvider containing the complete dataset
    :type data_container: DataProvider
    :param minimum_input_delay: Minimum delay for input variables
    :type minimum_input_delay: int
    :param inputs_maximum_delays: Maximum delays for each input variable
    :type inputs_maximum_delays: list[int] | int
    :param output_maximum_delay: Maximum delay for output variable
    :type output_maximum_delay: int
    :param slice_size: Size of each time slice in hours (default: 24)
    :type slice_size: int
    :param minimum_slices: Minimum number of slices for initial training (default: 12)
    :type minimum_slices: int
    :param slice_memory: Memory limit for slice history in hours (default: 24*7)
    :type slice_memory: int
    :param hidden_layer_sizes: The ith element represents the number of neurons in the ith hidden layer
    :type hidden_layer_sizes: tuple[int, ...]
    :param activation: Activation function for the hidden layer
    :type activation: str
    :param solver: The solver for weight optimization
    :type solver: str
    :param max_iter: Maximum number of iterations
    :type max_iter: int
    :param kwargs: Additional keyword arguments passed to NonlinearRegression
    :return: Trained NonlinearRegression model
    :rtype: NonlinearRegression
    """
    folder_name: str = Setup.data('folders', 'results') + 'sliding_nlreg/'
    if os.path.isdir(folder_name):
        shutil.rmtree(folder_name)
    os.mkdir(folder_name)
    original = sys.stdout
    sys.stdout = open(folder_name + "results.md", 'w')

    print("# Nonlinear Regression (NARX Neural Network) - Sliding Window")
    print(f'* minimum_input_delay: {minimum_input_delay}')
    print(f'* inputs_maximum_delays: {inputs_maximum_delays}')
    print(f'* output_maximum_delay: {output_maximum_delay}')
    print(f'* slice_size: {slice_size}')
    print(f'* minimum_slices: {minimum_slices}')
    print(f'* slice_memory: {slice_memory}')
    print(f'* hidden_layer_sizes: {hidden_layer_sizes}')
    print(f'* activation: {activation}')
    print(f'* solver: {solver}')
    print(f'* max_iter: {max_iter}')

    print('## Training')

    nonlinear_regression = NonlinearRegression(input_labels=input_variable_names, output_labels=output_variable_names, minimum_input_delay=minimum_input_delay, inputs_maximum_delays=inputs_maximum_delays, output_maximum_delay=output_maximum_delay, hidden_layer_sizes=hidden_layer_sizes, activation=activation, solver=solver, max_iter=max_iter, **kwargs)

    sliding_inputs = [data_container.series(data_label) for data_label in input_variable_names]
    sliding_outputs = [data_container.series(data_label) for data_label in output_variable_names]
    output_estimated_sliding = nonlinear_regression.sliding(sliding_inputs, sliding_outputs, time_slice_size=slice_size, minimum_time_slices=minimum_slices, time_slice_memory=slice_memory)

    for output_idx, output_name in enumerate(output_variable_names):
        data_container.add_var('%s_estimated' % output_name, output_estimated_sliding[output_idx])

    plot_saver_sliding = PlotSaver(data_container.datetimes, data_container.variables_data())
    plot_vars = output_variable_names + [name + '_estimated' for name in output_variable_names]
    plot_saver_sliding.time_plot(plot_vars, folder_name + 'output_sliding')
    print('* Estimated outputs at sliding')
    print('![Sliding output](output_sliding.png)')
    nonlinear_regression.error_analysis(sliding_inputs, sliding_outputs, output_estimated_sliding, folder_name=folder_name)

    sys.stdout.close()
    sys.stdout = original
    return nonlinear_regression
