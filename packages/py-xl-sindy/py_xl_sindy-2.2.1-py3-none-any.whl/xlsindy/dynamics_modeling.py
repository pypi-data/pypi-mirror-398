"""
This module contain every function in order to integrate and generate the dynamic function.

"""

import numpy as np
from .utils import print_progress
from scipy import interpolate
from scipy.integrate import RK45
from typing import List, Callable

import jax.numpy as jnp
import sympy
from typing import Tuple
from .logger import setup_logger


from .catalog import CatalogRepartition

logger = setup_logger(__name__)


def generate_acceleration_function(
    regression_solution: np.ndarray,
    catalog_repartition: CatalogRepartition,
    symbol_matrix: np.ndarray,
    time_symbol: sympy.Symbol,
    lambdify_module: str = "numpy",
) -> Tuple[Callable[[np.ndarray], np.ndarray], bool]:
    """
    Generate a function for computing accelerations based on the Lagrangian.

    This is actually a multi step process that will convert a Lagrangian into an acceleration function through euler lagrange theory.

    Some information about clever solve : there is two mains way to retrieve the acceleration from the other variable.
    The first one is to ask sympy to symbolically solve our equation and after to lambify it for use afterward.
    The main drawback of this is that when system is not perfectly retrieved it is theorically extremely hard to get a simple equation giving acceleration from the other variable.
    This usually lead to code running forever trying to solve this symbolic issue.

    The other way is to create a linear system of b=Ax where x are the acceleration coordinate and b is the force vector.
    At runtime one's need to replace every term in b and A and solve the linear equation (of dimension n so really fast)

    Args:
        regression_solution (np.ndarray): the solution vector from the regression
        catalog_repartition (List[tuple]): a listing of the different part of the catalog used need to follow the following structure : [("lagrangian",lagrangian_catalog),...,("classical",classical_catalog,expand_matrix)]
        symbol_matrix (np.ndarray): Matrix containing symbolic variables (external forces, positions, velocities, accelerations).
        time_symbol (sp.Symbol): The time symbol in the Lagrangian.

    Returns:
        function: A function that computes the accelerations given system state. takes as input a numerical symbol matrix
        bool: Whether the acceleration function generation was successful.
    """
    num_coords = symbol_matrix.shape[1]

    expanded_catalog = catalog_repartition.expand_catalog()

    dynamic_equations = regression_solution.T @ expanded_catalog
    dynamic_equations = dynamic_equations.flatten()

    # dynamic_equations -= np.array(
    #     [symbol_matrix[0, i] for i in range(num_coords)], dtype=object
    # )  # Add external forces
    # maybe not necessary now !! (Added when fusing the experiment matrix and forces function through the function catalog) To test

    valid = True

    for i in range(num_coords):
        if str(symbol_matrix[3, i]) not in str(dynamic_equations[i]):
            valid = False

    if valid:
        system_matrix, force_vector = (
            np.empty((num_coords, num_coords), dtype=object),
            np.empty((num_coords, 1), dtype=object),
        )

        for i in range(num_coords):
            equation = dynamic_equations[i]
            for j in range(num_coords):
                equation = equation.collect(symbol_matrix[3, j])
                term = equation.coeff(symbol_matrix[3, j])
                system_matrix[i, j] = -term
                equation -= term * symbol_matrix[3, j]

            force_vector[i, 0] = equation

        system_func = sympy.lambdify([symbol_matrix], system_matrix, lambdify_module)
        force_func = sympy.lambdify([symbol_matrix], force_vector, lambdify_module)

        if lambdify_module == "jax":

            def acceleration_solver(input_values):
                system_eval = system_func(input_values)
                force_eval = force_func(input_values)
                return jnp.linalg.solve(system_eval, force_eval)

        else:

            def acceleration_solver(input_values):
                system_eval = system_func(input_values)
                force_eval = force_func(input_values)
                return np.linalg.solve(system_eval, force_eval)

        acc_func = acceleration_solver

    else:  # Fail
        acc_func = None
    return acc_func, valid


def dynamics_function(
    acceleration_function: Callable[[np.ndarray], np.ndarray],
    external_forces: Callable[[np.ndarray], np.ndarray],
) -> Callable[[float, np.ndarray], np.ndarray]:
    """
    Transforms the acceleration function into something understandable by usual integration method.

    The acceleration function ( output of euler_lagrange.generate_acceleration_function() ) takes as input a numerical symbol matrix.
    It is not suitable for the majority of the integration function that need to take as input (t,[q0,q0_d,...,qn,qn_d]) and output (q0_d,q0_dd,...,qn_d,qn_dd).

    Args:
        acceleration_function (function): Array of functions representing accelerations.
        external_forces (function): Function returning external forces at time `t`.

    Returns:
        function: Dynamics function compatible with classical integration solver.
    """

    def func(t, state):
        state = np.reshape(state, (-1, 2))
        state_transposed = np.transpose(state)

        # Prepare input matrix for dynamics calculations as a numerical symbol matrix
        input_matrix = np.zeros(
            (state_transposed.shape[0] + 2, state_transposed.shape[1])
        )
        input_matrix[1:3, :] = state_transposed
        input_matrix[0, :] = external_forces(t)

        # Create the result use the same size as before
        result = np.zeros(state.shape)
        result[:, 0] = state[:, 1]
        result[:, 1] = acceleration_function(input_matrix)[:, 0]
        return np.reshape(result, (-1,))

    return func


def dynamics_function_fixed_external(
    acceleration_function: Callable[[np.ndarray], np.ndarray],
) -> Callable[[np.ndarray], Callable[[float, np.ndarray], np.ndarray]]:
    """
    Transforms the acceleration function into something understandable by usual integration method. (will be deprecated in v2.0)

    The acceleration function ( output of euler_lagrange.generate_acceleration_function() ) takes as input a numerical symbol matrix.
    It is not suitable for the majority of the integration function that need to take as input (t,[q0,q0_d,...,qn,qn_d]) and output (q0_d,q0_dd,...,qn_d,qn_dd).
    Due to the fact that it has been modified to perform one time step RK4, it introduces slight overhead

    Args:
        acceleration_function (function): Array of functions representing accelerations.

    Returns:
        function: return a function that take in input fixed force vector and return a Dynamics function compatible with classical integration solver.
    """

    def ret_func(forces):
        def func(t, state):
            state = np.reshape(state, (-1, 2))
            state_transposed = np.transpose(state)

            # Prepare input matrix for dynamics calculations as a numerical symbol matrix
            input_matrix = np.zeros(
                (state_transposed.shape[0] + 2, state_transposed.shape[1])
            )
            input_matrix[1:3, :] = state_transposed
            input_matrix[0, :] = forces

            # Create the result use the same size as before
            result = np.zeros(state.shape)
            result[:, 0] = state[:, 1]
            result[:, 1] = acceleration_function(input_matrix)[:, 0]
            return np.reshape(result, (-1,))

        return func

    return ret_func


def dynamics_function_RK4_env(
    acceleration_function: Callable[[np.ndarray], np.ndarray],
) -> Callable[[np.ndarray], Callable[[float, np.ndarray], np.ndarray]]:
    """
    Transforms the acceleration function into something compatible for the RK4 integration method. (into reinforcement-learning-sindy )

    The acceleration function ( output of euler_lagrange.generate_acceleration_function() ) takes as input a numerical symbol matrix.
    It is not suitable for the integration function of RK4 environment that need to take as input ([q0,q0_d,...,qn,qn_d],[f0,...,fn]) and output (q0_d,q0_dd,...,qn_d,qn_dd).
    Use jax jnp instead of numpy for better performance. need to be use in accordance with euler_lagrange.generate_acceleration_function(lambdify_module="jax")

    Args:
        acceleration_function (function): Array of functions representing accelerations.

    Returns:
        function: return a function that take in input fixed force vector and forces and return a Dynamics function compatible with classical integration solver.
    """

    def ret_func(state, forces):
        state = jnp.reshape(state, (-1, 2))

        state_transposed = jnp.transpose(state)
        input_matrix = jnp.concatenate(
            [
                jnp.reshape(forces, (1, -1)),
                state_transposed,
                jnp.zeros((1, forces.shape[0])),
            ],
            axis=0,
        )

        result = jnp.concatenate(
            [
                jnp.reshape(state[:, 1], (-1, 1)),
                jnp.reshape(acceleration_function(input_matrix)[:, 0], (-1, 1)),
            ],
            axis=1,
        )

        return jnp.reshape(result, (-1,))

    return ret_func


def run_rk45_integration(
    dynamics: Callable[[float, np.ndarray], np.ndarray],
    initial_state: np.ndarray,
    time_end: float,
    max_step: float = 0.05,
    min_step: float = 1e-4,
) -> List[np.ndarray]:
    """
    Runs an RK45 integration on a dynamics model.

    Args:
        dynamics (function): Dynamics function for integration.
        initial_state (np.ndarray): Initial state of the system.
        time_end (float): End time for the integration.
        max_step (float, optional): Maximum step size for the integration. Defaults to 0.05.

    Returns:
        tuple: Arrays of time values and states.
    """
    initial_state_flat = np.reshape(initial_state, (-1,))

    model = RK45(
        dynamics,
        0,
        initial_state_flat,
        time_end,
        max_step,
        0.001,
        np.e**-6,
        first_step=min_step * 5,
    )  # TO INVESTIGATE

    time_values = [0]
    state_values = [initial_state_flat]

    first_step_cursed = np.abs(np.sum(dynamics(0, initial_state_flat)))

    if np.isnan(first_step_cursed) or np.isinf(first_step_cursed):
        logger.error("Dynamics function fail on first step")
        time_values.append(model.t)
        state_values.append(model.y)
        return np.array(time_values), np.array(state_values)

    try:
        while model.status != "finished":
            for _ in range(200):
                if model.status != "finished":
                    model.step()
                    time_values.append(model.t)
                    state_values.append(model.y)

                    if (model.step_size is not None) and (model.step_size < min_step):
                        raise RuntimeError()
            print_progress(model.t, time_end)

    except RuntimeError:
        logger.error("RuntimeError in RK45 integration")

    return np.array(time_values), np.array(state_values)


def generate_random_force(
    time_end: float,
    current_augmentation: int,
    target_augmentation: int,
    period_initial: float,
    period_shift_initial: float,
    component_count: int,
    random_gen: np.random.Generator,
) -> Callable[[float], np.ndarray]:
    """
    Recursively generates a random external force function with specified augmentations.

    Parameters:
        time_end (float): End time for the generated force.
        current_augmentation (int): Current augmentation step in recursion.
        target_augmentation (int): Target augmentation level.
        period_initial (float): Initial period for the force oscillations.
        period_shift_initial (float): Initial shift for random variations in the period.
        component_count (int): Number of components in the force vector.

    Returns:
        Callable[[float], np.ndarray]: A function that generates a random force vector over time.
    """
    if current_augmentation == target_augmentation:
        return lambda t: t * np.zeros((component_count, 1))

    # Recursive call to generate the baseline force function
    baseline_force_function = generate_random_force(
        time_end,
        current_augmentation + 1,
        target_augmentation,
        period_initial,
        period_shift_initial,
        component_count,
        random_gen,
    )

    # Calculate period, shift, and variance for the current augmentation level
    multiplier = target_augmentation - current_augmentation
    period = period_initial / multiplier
    period_shift = period_shift_initial / multiplier
    variance = 1 / multiplier

    # Generate time points with random shifts
    time_points = np.arange(0, time_end + period, period)
    time_points += (random_gen.random(len(time_points)) - 0.5) * 2 * period_shift

    # Generate random force values with variance
    force_values = (
        random_gen.random((component_count, len(time_points))) * 2 - 1
    ) * variance
    force_values += baseline_force_function(time_points)
    force_values /= np.std(force_values)  # Normalize to standard deviation of 1

    # Create an interpolating function to return force values over time
    return interpolate.CubicSpline(time_points, force_values, axis=1)


def optimized_force_generator(
    component_count: int,
    scale_vector: np.ndarray,
    time_end: float,
    period: float,
    period_shift: float,
    augmentations: int = 50,
    random_seed: List[int] = [20],
) -> Callable[[float], np.ndarray]:
    """
    Generates an optimized force function, applying a scale vector to the generated force.

    Parameters:
        component_count (int): Number of components in the force vector.
        scale_vector (np.ndarray): Scaling factors for each component.
        time_end (float): End time for the generated force.
        period (float): Base period for force oscillations.
        period_shift (float): Base shift applied to the period for randomness.
        augmentations (int): Number of augmentations in the recursive force generation.

    Returns:
        Callable[[float], np.ndarray]: A function that returns the optimized force at time `t`.
    """
    scale_vector = np.reshape(scale_vector, (component_count, 1))

    rng = np.random.default_rng(random_seed)

    # Generate the recursive force function
    base_force_function = generate_random_force(
        time_end,
        0,
        augmentations,
        period,
        period_shift,
        component_count,
        random_gen=rng,
    )

    def force_function(t: float) -> np.ndarray:
        force_value = base_force_function(t)
        # Apply scaling vector to each component
        if len(force_value.shape) == 1:
            return force_value * scale_vector.flatten()
        return force_value * scale_vector

    return force_function


def sinusoidal_force_generator(
    component_count: int,
    scale_vector: np.ndarray,
    time_end: float,
    num_frequencies: int = 5,
    freq_range: Tuple[float, float] = (0.5, 5.0),
    random_seed: List[int] = [42],
) -> Callable[[float], np.ndarray]:
    """
    Generates a force function based on stacked sinusoidal signals with varying frequencies and amplitudes.

    The function creates a sum of sinusoids with random frequencies, amplitudes, and phases for each component.
    Each sinusoidal component has a frequency within the specified range and a random amplitude and phase.

    Parameters:
        component_count (int): Number of components in the force vector.
        scale_vector (np.ndarray): Scaling factors for each component.
        time_end (float): End time for the generated force (used for normalization).
        num_frequencies (int): Number of sinusoidal components to stack. Defaults to 5.
        freq_range (Tuple[float, float]): Range of frequencies (min, max) in Hz. Defaults to (0.5, 5.0).
        random_seed (List[int]): Seed for random number generation. Defaults to [42].

    Returns:
        Callable[[float], np.ndarray]: A function that returns the sinusoidal force at time `t`.
    """
    scale_vector = np.reshape(scale_vector, (component_count, 1))
    rng = np.random.default_rng(random_seed)

    # Generate random frequencies, amplitudes, and phases for each component
    frequencies = np.zeros((component_count, num_frequencies))
    amplitudes = np.zeros((component_count, num_frequencies))
    phases = np.zeros((component_count, num_frequencies))

    for i in range(component_count):
        # Random frequencies within the specified range
        frequencies[i, :] = rng.uniform(
            freq_range[0], freq_range[1], num_frequencies
        )
        # Random amplitudes (uniform distribution)
        amplitudes[i, :] = rng.uniform(0.5, 1.5, num_frequencies)
        # Random phases
        phases[i, :] = rng.uniform(0, 2 * np.pi, num_frequencies)

    # Normalize amplitudes so the sum has unit variance
    normalization_factors = np.zeros(component_count)
    sample_times = np.linspace(0, time_end, 1000)
    for i in range(component_count):
        sample_signal = np.sum(
            amplitudes[i, :, np.newaxis]
            * np.sin(
                2 * np.pi * frequencies[i, :, np.newaxis] * sample_times
                + phases[i, :, np.newaxis]
            ),
            axis=0,
        )
        normalization_factors[i] = np.std(sample_signal)

    def force_function(t: float) -> np.ndarray:
        if isinstance(t, np.ndarray):
            # Handle array input
            force_value = np.zeros((component_count, len(t)))
            for i in range(component_count):
                for j in range(num_frequencies):
                    force_value[i, :] += amplitudes[i, j] * np.sin(
                        2 * np.pi * frequencies[i, j] * t + phases[i, j]
                    )
                force_value[i, :] /= normalization_factors[i]
        else:
            # Handle scalar input
            force_value = np.zeros((component_count,))
            for i in range(component_count):
                for j in range(num_frequencies):
                    force_value[i] += amplitudes[i, j] * np.sin(
                        2 * np.pi * frequencies[i, j] * t + phases[i, j]
                    )
                force_value[i] /= normalization_factors[i]

        # Apply scaling vector to each component
        if len(force_value.shape) == 1:
            return force_value * scale_vector.flatten()
        return force_value * scale_vector

    return force_function


def vectorised_acceleration_generation(dynamic_system: Callable, qpos, qvel, force):
    """
    Take a dynamic system function after being vectorised model_dynamics_system = vmap(model_dynamics_system, in_axes=(1,1),out_axes=1) and return a batch of acceleration
    """

    T, n = qpos.shape

    # base_vectors = np.empty((T, 2 * n), dtype=qpos.dtype)
    # base_vectors[:, 0::2] = qpos
    # base_vectors[:, 1::2] = qvel

    base_vectors = np.stack((qpos, qvel), axis=2)  # shape: (1001, 4, 2)
    base_vectors = base_vectors.reshape(T, 2 * n)  # shape: (1001, 8)

    base_vectors = jnp.array(base_vectors)

    return dynamic_system(base_vectors.T, force.T).T
