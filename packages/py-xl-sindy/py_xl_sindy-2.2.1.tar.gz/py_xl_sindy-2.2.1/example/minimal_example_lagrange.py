"""
VERIFIED FOR VERSION 2.1.3

Minimal example script to demonstrate functionality of py-xl-sindy package.

This script generates synthetic data from a mujoco simulation of a cartpole.
It then uses the py-xl-sindy package to identify a model from the data.

The identified model is then simulated and compared to the original data.

"""

import numpy as np
import sympy as sp 
import xlsindy
from generate_trajectory import generate_mujoco_trajectory,generate_theoretical_trajectory
from xlsindy.logger import setup_logger
from xlsindy.optimization import lasso_regression
import time
import matplotlib.pyplot as plt

from jax import vmap

def mujoco_transform(pos, vel, acc):

    return -pos, -vel, -acc

def inverse_mujoco_transform(pos, vel, acc):
    if acc is not None:
        return -pos, -vel, -acc
    else:
        return -pos, -vel, None
    
logger = setup_logger(__name__)

if __name__=="__main__":
    
    num_coordinates = 2
    random_seed = 0
    batch_number = 10
    max_time = 10.0
    initial_position = np.array([0.0, 0.0,0.0,0.0])
    initial_condition_randomness = np.array([0.1])
    forces_scale_vector = np.array([2.0, 2.0])
    forces_period = 3.0
    forces_period_shift = 0.5
    data_ratio = 2.0
    validation_time = 30.0
    noise_level = 0.0

    rng = np.random.default_rng(random_seed)


    # Import the XML file for the mujoco simulation
    xml_content = open("cart_pole.xml", "r").read()

    # Create the mujoco trajectory
    (simulation_time_t, 
    simulation_qpos_t, 
    simulation_qvel_t, 
    simulation_qacc_t, 
    force_vector_t,
    _) = generate_mujoco_trajectory(
        num_coordinates,
        initial_position,
        initial_condition_randomness,
        random_seed,
        batch_number,
        max_time,
        xml_content,
        forces_scale_vector,
        forces_period,
        forces_period_shift,
        mujoco_transform,
        inverse_mujoco_transform
    )

    # Add noise
    simulation_qpos_t += rng.normal(loc=0, scale=noise_level, size=simulation_qpos_t.shape)*np.linalg.norm(simulation_qpos_t)/simulation_qpos_t.shape[0]
    simulation_qvel_t += rng.normal(loc=0, scale=noise_level, size=simulation_qvel_t.shape)*np.linalg.norm(simulation_qvel_t)/simulation_qvel_t.shape[0]
    simulation_qacc_t += rng.normal(loc=0, scale=noise_level, size=simulation_qacc_t.shape)*np.linalg.norm(simulation_qacc_t)/simulation_qacc_t.shape[0]
    force_vector_t += rng.normal(loc=0, scale=noise_level, size=force_vector_t.shape)*np.linalg.norm(force_vector_t)/force_vector_t.shape[0]


    # Create the catalog
    time_sym = sp.symbols("t")

    symbols_matrix = xlsindy.symbolic_util.generate_symbolic_matrix(
        num_coordinates, time_sym
    )

    friction_forces = np.array([[-1.5, 0], [0, -1.5]])

    friction_function = np.array(
        [[symbols_matrix[2, x] for x in range(num_coordinates)]] # \dot{q}
    )

    function_catalog_1 = [lambda x: symbols_matrix[2, x]]  # \dot{q}
    function_catalog_2 = [
        lambda x: sp.sin(symbols_matrix[1, x]), # \sin(q)
        lambda x: sp.cos(symbols_matrix[1, x]), # \cos(q)
    ]

    catalog_part1 = np.array(
        xlsindy.symbolic_util.generate_full_catalog(
            function_catalog_1, num_coordinates, 2
        )
    )
    catalog_part2 = np.array(
        xlsindy.symbolic_util.generate_full_catalog(
            function_catalog_2, num_coordinates, 2
        )
    )

    lagrange_catalog = xlsindy.symbolic_util.cross_catalog(
        catalog_part1, catalog_part2
    )

    friction_catalog = (
        friction_function.flatten()
    )
    # fully exand friction catalog for maximum number of term
    expand_matrix = np.ones((len(friction_catalog), num_coordinates), dtype=int)

    catalog = xlsindy.catalog.CatalogRepartition(
        [
            xlsindy.catalog_base.ExternalForces(
                [[1], [2]], symbols_matrix
            ),
            xlsindy.catalog_base.Lagrange(
                lagrange_catalog, symbols_matrix, time_sym
            ),
            xlsindy.catalog_base.Classical(
                friction_catalog, expand_matrix
            ),
        ]
    )

    # Use a fixed ratio of the data in respect with catalog size
    catalog_size = catalog.catalog_length
    data_ratio = data_ratio
    
    # Sample uniformly n samples from the imported arrays
    n_samples = int(catalog_size * data_ratio)
    total_samples = simulation_qpos_t.shape[0]

    if n_samples < total_samples:

        # Evenly spaced sampling (deterministic, uniform distribution)
        sample_indices = np.linspace(0, total_samples - 1, n_samples, dtype=int)
        
        # Apply sampling to all arrays
        simulation_qpos_t = simulation_qpos_t[sample_indices]
        simulation_qvel_t = simulation_qvel_t[sample_indices]
        simulation_qacc_t = simulation_qacc_t[sample_indices]
        force_vector_t = force_vector_t[sample_indices]
        
        logger.info(f"Sampled {n_samples} points uniformly from {total_samples} total samples")
    else:
        logger.info(f"Using all {total_samples} samples (requested {n_samples})")

    logger.info("Starting mixed regression")

    start_time = time.perf_counter()

    solution, exp_matrix = xlsindy.simulation.regression_mixed(
        theta_values=simulation_qpos_t,
        velocity_values=simulation_qvel_t,
        acceleration_values=simulation_qacc_t,
        time_symbol=time_sym,
        symbol_matrix=symbols_matrix,
        catalog_repartition=catalog,
        external_force=force_vector_t,
        regression_function=lasso_regression,
    )

    end_time = time.perf_counter()

    regression_time = end_time - start_time

    logger.info(f"Regression completed in {end_time - start_time:.2f} seconds")

    # Use the result to generate validation trajectory

    threshold = 1e-2  # Adjust threshold value as needed
    solution = np.where(np.abs(solution)/np.linalg.norm(solution) < threshold, 0, solution)

    model_acceleration_func_np, valid_model = (
        xlsindy.dynamics_modeling.generate_acceleration_function(
            solution, 
            catalog,
            symbols_matrix,
            time_sym,
            lambdify_module="numpy",
        )
    )

    if valid_model:

        (simulation_time_v, 
        simulation_qpos_v, 
        simulation_qvel_v, 
        simulation_qacc_v, 
        force_vector_v,
        _) = generate_mujoco_trajectory(
            num_coordinates,
            initial_position,
            initial_condition_randomness,
            [random_seed,0], # Ensure same seed as for data generation
            1,
            validation_time,
            xml_content,
            forces_scale_vector,
            forces_period,
            forces_period_shift,
            mujoco_transform,
            inverse_mujoco_transform
        )

        (simulation_time_vs, 
         simulation_qpos_vs, 
         simulation_qvel_vs, 
         simulation_qacc_vs, 
         force_vector_vs,
         _) = generate_theoretical_trajectory(
             num_coordinates,
             initial_position,
             initial_condition_randomness,
             [random_seed,0], # Ensure same seed as for data generation
             1,
             validation_time,
             solution,
             catalog,
             time_sym,
             symbols_matrix,
             forces_scale_vector,
             forces_period,
             forces_period_shift
         )
        
        # Create a figure with 4 subplots stacked vertically
        fig, axes = plt.subplots(4, 1, figsize=(12, 18), sharex=True)
        fig.suptitle('Trajectory Comparison: Mujoco vs. Theoretical', fontsize=16)

        # --- 1. Plot Position Data ---
        axes[0].plot(simulation_time_v, simulation_qpos_v, label='Mujoco Simulation')
        axes[0].plot(simulation_time_vs, simulation_qpos_vs, label='Theoretical Simulation', linestyle='--')
        axes[0].set_title('Position vs. Time')
        axes[0].set_ylabel('Position')
        axes[0].legend()
        axes[0].grid(True)

        # --- 2. Plot Velocity Data ---
        axes[1].plot(simulation_time_v, simulation_qvel_v, label='Mujoco Simulation')
        axes[1].plot(simulation_time_vs, simulation_qvel_vs, label='Theoretical Simulation', linestyle='--')
        axes[1].set_title('Velocity vs. Time')
        axes[1].set_ylabel('Velocity')
        axes[1].legend()
        axes[1].grid(True)

        # --- 3. Plot Acceleration Data ---
        axes[2].plot(simulation_time_v, simulation_qacc_v, label='Mujoco Simulation')
        axes[2].plot(simulation_time_vs, simulation_qacc_vs, label='Theoretical Simulation', linestyle='--')
        axes[2].set_title('Acceleration vs. Time')
        axes[2].set_ylabel('Acceleration')
        axes[2].legend()
        axes[2].grid(True)

        # --- 4. Plot Force Data ---
        axes[3].plot(simulation_time_v, force_vector_v, label='Mujoco Force')
        axes[3].plot(simulation_time_vs, force_vector_vs, label='Theoretical Force', linestyle='--')
        axes[3].set_title('Force vs. Time')
        axes[3].set_ylabel('Force')
        axes[3].set_xlabel('Time (s)')
        axes[3].legend()
        axes[3].grid(True)

        # Improve layout to prevent labels from overlapping
        plt.tight_layout(rect=[0, 0.03, 1, 0.96]) # Adjust layout to make room for the suptitle

        # Display the plots
        plt.savefig("trajectory_comparison.png")
 
    else:

        logger.warning("Model is not valid, skipping validation trajectory generation")
        
