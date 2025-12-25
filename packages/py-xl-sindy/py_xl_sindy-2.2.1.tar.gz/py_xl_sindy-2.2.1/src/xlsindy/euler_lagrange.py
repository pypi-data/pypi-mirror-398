"""

This module primarly focus on symbolic variable and enable to do the different manipulation in order to get the experiment matrix

"""

import numpy as np
import sympy
from typing import List
from xlsindy.logger import setup_logger

logger = setup_logger(__name__,level="DEBUG")


def compute_euler_lagrange_equation(
    lagrangian_expr: sympy.Expr,
    symbol_matrix: np.ndarray,
    time_symbol: sympy.Symbol,
    coordinate_index: int,
) -> sympy.Expr:
    """
    Compute the Euler-Lagrange equation for a given generalized coordinate.

    Args:
        lagrangian_expr (sp.Expr): The symbolic expression of the Lagrangian.
        symbol_matrix (np.ndarray): The matrix of symbolic variables (external forces, positions, velocities, and accelerations).
        time_symbol (sp.Symbol): The symbolic variable representing time.
        coordinate_index (int): The index of the generalized coordinate for differentiation.

    Returns:
        sympy.Expr: The Euler-Lagrange equation for the specified generalized coordinate.
    """
    dL_dq = sympy.diff(lagrangian_expr, symbol_matrix[1, coordinate_index])
    dL_dq_dot = sympy.diff(lagrangian_expr, symbol_matrix[2, coordinate_index])
    time_derivative = sympy.diff(dL_dq_dot, time_symbol)

    for j in range(
        symbol_matrix.shape[1]
    ):  # One can says there is the smart move when using symbolic variable
        time_derivative = time_derivative.replace(
            sympy.Derivative(symbol_matrix[1, j], time_symbol), symbol_matrix[2, j]
        )
        time_derivative = time_derivative.replace(
            sympy.Derivative(symbol_matrix[2, j], time_symbol), symbol_matrix[3, j]
        )

    return dL_dq - time_derivative


def newton_from_lagrangian(
    lagrangian_expr: sympy.Expr,
    symbol_matrix: np.ndarray,
    time_symbol: sympy.Symbol,
) -> List[sympy.Expr]:
    """
    Compute all the equation from the lagrangian in order to get newton system.

    Args:
        lagrangian_expr (sp.Expr): The symbolic expression of the Lagrangian.
        symbol_matrix (np.ndarray): The matrix of symbolic variables (external forces, positions, velocities, and accelerations).
        time_symbol (sp.Symbol): The symbolic variable representing time.

    Returns:
        List[sympy.Expr]: The Newton equations of the system.
    """

    n = symbol_matrix.shape[1]

    res = []

    for i in range(n):
        res += [
            compute_euler_lagrange_equation(
                lagrangian_expr, symbol_matrix, time_symbol, i
            )
        ]

    return res


def jax_create_experiment_matrix(
    num_coords: int,
    catalogs: np.ndarray,
    symbol_matrix: np.ndarray,
    position_values: np.ndarray,
    velocity_values: np.ndarray,
    acceleration_values: np.ndarray,
    forces_values: np.ndarray,
) -> np.ndarray:
    """
    Create the SINDy experiment matrix.

    For each function in the catalog create the times series of function for each coordinate.
    This matrix will afterward undergo the regression in order to retrieve the parse expression.

    Args:
        num_coords (int): Number of generalized coordinates.
        catalogs (list): array of catalog function of shape (p,n)
        symbol_matrix (sp.Matrix): Symbolic variable matrix for the system.
        position_values (np.array(sampled_step,num_coordinate)): Array of positions at each time step.
        velocity_values (np.array(sampled_step,num_coordinate)): Array of velocities.
        acceleration_values (np.array(sampled_step,num_coordinate)): Array of accelerations.
        forces_values (np.ndarray(sampled_step,num_coordinate)): Array of external forces.

    Returns:
        np.array (sampled_steps * num_coords, catalog_lenght): Experiment matrix.
    """
    sampled_steps = len(position_values)

    logger.debug(f"Creating experiment matrix with {sampled_steps} sampled steps and {num_coords} coordinates")

    catalog_lenght = catalogs.shape[0]

    experiment_matrix = np.zeros(((sampled_steps) * num_coords, catalog_lenght))

    q_matrix = np.zeros((symbol_matrix.shape[0], symbol_matrix.shape[1], sampled_steps))

    q_matrix[0, :, :] = np.transpose(forces_values)
    q_matrix[1, :, :] = np.transpose(position_values)
    q_matrix[2, :, :] = np.transpose(velocity_values)
    q_matrix[3, :, :] = np.transpose(acceleration_values)

    for i in range(num_coords):
        catalog_lambda = list(
            map(
                lambda x: sympy.lambdify([symbol_matrix], x, modules="numpy"),
                catalogs[:, i],
            )
        )

        for j, func in enumerate(catalog_lambda):
            experiment_matrix[i * sampled_steps : (i + 1) * sampled_steps, j] = func(
                q_matrix
            )

    return experiment_matrix


def create_experiment_matrix(
    num_coords: int,
    catalogs: np.ndarray,
    symbol_matrix: np.ndarray,
    position_values: np.ndarray,
    velocity_values: np.ndarray,
    acceleration_values: np.ndarray,
) -> np.ndarray:
    """
    Create the SINDy experiment matrix.

    For each function in the catalog create the times series of function for each coordinate.
    This matrix will afterward undergo the regression in order to retrieve the parse expression.

    Args:
        num_coords (int): Number of generalized coordinates.
        catalogs (list): array of catalog function of shape (p,n)
        symbol_matrix (sp.Matrix): Symbolic variable matrix for the system.
        position_values (np.array): Array of positions at each time step.
        velocity_values (np.array): Array of velocities.
        acceleration_values (np.array): Array of accelerations.

    Returns:
        experiment_matrix (np.array (sampled_steps * num_coords, catalog_lenght)): The experiment matrix.
    """
    sampled_steps = len(position_values)

    catalog_lenght = catalogs.shape[0]

    experiment_matrix = np.zeros((sampled_steps * num_coords, catalog_lenght))

    q_matrix = np.zeros((symbol_matrix.shape[0], symbol_matrix.shape[1], sampled_steps))
    q_matrix[1, :, :] = np.transpose(position_values)
    q_matrix[2, :, :] = np.transpose(velocity_values)
    q_matrix[3, :, :] = np.transpose(acceleration_values)

    for i in range(num_coords):
        catalog_lambda = list(
            map(
                lambda x: sympy.lambdify([symbol_matrix], x, modules="numpy"),
                catalogs[:, i],
            )
        )

        for j, func in enumerate(catalog_lambda):
            experiment_matrix[i * sampled_steps : (i + 1) * sampled_steps, j] = func(
                q_matrix
            )

    return experiment_matrix
