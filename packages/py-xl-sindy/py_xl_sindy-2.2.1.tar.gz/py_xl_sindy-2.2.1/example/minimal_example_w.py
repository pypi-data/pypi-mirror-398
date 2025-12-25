"""
    Generates the following trajectories:

    training_trajectory: partial (e.g. 10 sec) true (Mujoco) trajectory used to fit model
    predicted_trajectory: SINDy-calculated trajectory (e.g. 30 sec) trained on training_trajectory
    true_trajectory: full (same length as predicted_trajectory), true (Mujoco) trajectory used as a ground truth
"""

### START PROLOGUE ###
import numpy as np
import sympy as sp 
import pandas as pd
import xlsindy
from generate_trajectory import generate_mujoco_trajectory,generate_theoretical_trajectory
from xlsindy.logger import setup_logger
from xlsindy.optimization import lasso_regression, proximal_gradient_descent
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

### END PROLOGUE ###


class Catalog:
    """ 
        SINDy catalog to create with the provided methods

        Uses a series of setters to seemlessly calculate all needed information

        FIXME: Degree 2 only
    """
    
    # Catalog variables, size, ratio, length, samples, etc.
    def __init__(self, time_sym):
        """ Define the most basic parameters """
        self.time_sym = time_sym

        # Private variables
        self._friction_forces = None
        self._friction_function = None
        self._function_catalog_1 = None
        self._function_catalog_2 = None

    @property
    def friction_forces(self):
        return self._friction_forces
    
    @property
    def friction_function(self):
        return self._friction_function
    
    @property
    def function_catalog_1(self):
        return self._function_catalog_1
    
    @property
    def function_catalog_2(self):
        return self._function_catalog_2
    
    @property
    def lagrange_catalog(self):
        return xlsindy.symbolic_util.cross_catalog(
            self.catalog_part_1, self.catalog_part_2
        )
    
    @property 
    def friction_catalog(self):
        return self.friction_function.flatten()
    
    @property
    def catalog(self):
        # Note there are two catalog functions for optimization purposes
        expand_matrix = np.ones((len(self.friction_catalog), self.num_coordinates), dtype=int)

        catalog = xlsindy.catalog.CatalogRepartition(
            [
                xlsindy.catalog_base.ExternalForces(
                    [[1], [2]], self.symbols_matrix
                ),
                xlsindy.catalog_base.Lagrange(
                    self.lagrange_catalog, self.symbols_matrix, self.time_sym
                ),
                xlsindy.catalog_base.Classical(
                    self.friction_catalog, expand_matrix
                ),
            ]
        )

        self.catalog_size = catalog.catalog_length
        self.cached_catalog = catalog
        return catalog

    @friction_forces.setter
    def friction_forces(self, new_value):
        self._friction_forces = new_value
        self.num_coordinates = len(new_value) # FIXME: is this a correct abstraction?
        self.symbols_matrix = xlsindy.symbolic_util.generate_symbolic_matrix(
            self.num_coordinates, self.time_sym
        ) 

    @friction_function.setter
    def friction_function(self, new_function):
        self._friction_function = new_function

    @function_catalog_1.setter
    def function_catalog_1(self, new_value):
        self._function_catalog_1 = new_value
        self.catalog_part_1 = np.array(
            xlsindy.symbolic_util.generate_full_catalog(
                self._function_catalog_1, self.num_coordinates, 2
            )
        )

    @function_catalog_2.setter
    def function_catalog_2(self, new_value):
        self._function_catalog_2 = new_value
        self.catalog_part_2 = np.array(
            xlsindy.symbolic_util.generate_full_catalog(
                self._function_catalog_2, self.num_coordinates, 2
            )
        )

class Trajectory:
    """ Particle dynamics for a specific system """

    def __init__(self, time, qpos, qvel, qacc, force, batch_starting_times):
        self.time = time
        self.qpos = qpos
        self.qvel = qvel
        self.qacc = qacc
        self.force = force
        self.batch_starting_times = batch_starting_times

    def add_normal_noise(self, rng, noise_level):
        """ 
            Adds normal N(mu = 0, theta = noise_level) noise
            NOTE: Why N(mu = 0, theta = noise_level)? Is this actually representative of the real world? if "yes," do you have literature to back up that statement?
        """
        self.qpos += rng.normal(loc=0, scale=noise_level, size=self.qpos.shape)*np.linalg.norm(self.qpos)/self.qpos.shape[0]
        self.qvel += rng.normal(loc=0, scale=noise_level, size=self.qvel.shape)*np.linalg.norm(self.qvel)/self.qvel.shape[0]
        self.qacc += rng.normal(loc=0, scale=noise_level, size=self.qacc.shape)*np.linalg.norm(self.qacc)/self.qacc.shape[0]
        self.force += rng.normal(loc=0, scale=noise_level, size=self.force.shape)*np.linalg.norm(self.force)/self.force.shape[0]
        return self

    def slice(self, indices):
        self.time = self.time[indices] # NOTE added
        self.qpos = self.qpos[indices]
        self.qvel = self.qvel[indices]
        self.qacc = self.qacc[indices]
        self.force = self.force[indices]
    
    def generate_solution(self, catalog: Catalog, regression_function):
        return xlsindy.simulation.regression_mixed(
            theta_values=self.qpos,
            velocity_values=self.qvel,
            acceleration_values=self.qacc,
            time_symbol=catalog.time_sym,
            symbol_matrix=catalog.symbols_matrix,
            catalog_repartition=catalog.cached_catalog, # cached catalog (vs catalog) for optimization purposes
            external_force=self.force,
            regression_function=regression_function
        ) # NOTE model (regression)




def simulation(
        mode="uniform_unshuffled",
        num_coordinates = 2,
        random_seed = 0,
        batch_number = 10,
        max_time = 10.0,
        initial_position = np.array([0.0, 0.0,0.0,0.0]),
        initial_condition_randomness = np.array([0.1]),
        forces_scale_vector = np.array([2.0, 2.0]),
        forces_period = 3.0,
        forces_period_shift = 0.5,
        data_ratio = 2.0,
        validation_time = 30.0,
        # NOTE: noise_level is standard deviation of noise, so with a default of 0, **there is no noise**
        noise_level = 0.0,
        validation_trajectory_threshold = 1e-2 
):
    # Random number generator (RNG) determined by the seed
    rng = np.random.default_rng(random_seed)

    # Import the XML file for the mujoco simulation
    xml_content = open("cart_pole.xml", "r").read()
    print("XML")

    # Calculate Mujoco trajectory
    training_trajectory = Trajectory(*generate_mujoco_trajectory(
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
    )).add_normal_noise(rng, noise_level)

    # Create catalog
    catalog = Catalog("t")
    catalog.friction_forces = np.array([[-1.5, 0], [0, -1.5]])
    catalog.friction_function = np.array(
        [[catalog.symbols_matrix[2, x] for x in range(catalog.num_coordinates)]] # \dot{q}
    )
    catalog.function_catalog_1 = [lambda x: catalog.symbols_matrix[2, x]]
    catalog.function_catalog_2 = [
        lambda x: sp.sin(catalog.symbols_matrix[1, x]), # \sin(q)
        lambda x: sp.cos(catalog.symbols_matrix[1, x]), # \cos(q)
    ]
    cat = catalog.catalog

    # Sampling
    n_samples = int(catalog.catalog_size * data_ratio)
    total_samples = training_trajectory.qpos.shape[0]

    if n_samples < total_samples:
        # Evenly spaced sampling (deterministic, uniform distribution)

        if mode == "uniform_unshuffled":
            sample_indices = np.linspace(0, total_samples - 1, n_samples, dtype=int)
        elif mode == "uniform_shuffled":
            sample_indices = np.linspace(0, total_samples - 1, n_samples, dtype=int)
            sample_indices = np.sort(sample_indices)
        elif mode == "random_replaced":
            sample_indices = np.random.choice(a=total_samples, size=n_samples, replace=True)
        elif mode == "random_unreplaced":
            sample_indices = np.random.choice(a=total_samples, size=n_samples, replace=False)
        else:
            raise AssertionError(f"invalid mode {mode}")

        # Apply sampling to all arrays
        # NOTE <main part to modify>
        training_trajectory.slice(sample_indices)
        # NOTE </main part to modify>
        logger.info(f"Sampled {n_samples} points uniformly from {total_samples} total samples")
    else:
        logger.info(f"Using all {total_samples} samples (requested {n_samples})")

        logger.info("Starting mixed regression")

    # Calculate SINDy solution on the mujoco trajectory and catalog
    start_time = time.perf_counter()
    solution, exp_matrix = training_trajectory.generate_solution(
        catalog=catalog,
        regression_function=proximal_gradient_descent
    )
    end_time = time.perf_counter()
    regressoin_time = end_time - start_time
    logger.info(f"Regression completed in {end_time - start_time:.2f} seconds")

    solution = np.where(np.abs(solution)/np.linalg.norm(solution) < validation_trajectory_threshold, 0, solution)
    
    model_acceleration_func_np, valid_model = (
        xlsindy.dynamics_modeling.generate_acceleration_function(
            solution, 
            cat,
            catalog.symbols_matrix,
            catalog.time_sym,
            lambdify_module="numpy",
        )
    )

    if valid_model:
        true_trajectory = Trajectory(*generate_mujoco_trajectory(
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
        ))

        predicted_trajecotry = Trajectory(*generate_theoretical_trajectory( 
             num_coordinates,
             initial_position,
             initial_condition_randomness,
             [random_seed,0], # Ensure same seed as for data generation
             1,
             validation_time,
             solution,
             cat,
             catalog.time_sym,
             catalog.symbols_matrix,
             forces_scale_vector,
             forces_period,
             forces_period_shift
         ))
        
        return training_trajectory, true_trajectory, predicted_trajecotry

def visualization(training_trajectory: Trajectory, true_trajectory: Trajectory, predicted_trajecotry: Trajectory, filename):
        # Create a figure with 4 subplots stacked vertically
        fig, axes = plt.subplots(4, 1, figsize=(12, 18), sharex=True)
        fig.suptitle('Trajectory Comparison: Mujoco vs. Theoretical', fontsize=16)

        # --- 1. Plot Position Data ---
        # axes[0].plot(training_trajectory.time, training_trajectory.qpos, label='Training Trajectory')
        axes[0].plot(true_trajectory.time, true_trajectory.qpos, label='True (Mujoco) Trajectory')
        axes[0].plot(predicted_trajecotry.time, predicted_trajecotry.qpos, label='Predicted (SINDy) Trajectory', linestyle='--')
        axes[0].set_title('Position vs. Time')
        axes[0].set_ylabel('Position')
        axes[0].legend()
        axes[0].grid(True)

        # --- 2. Plot Velocity Data ---
        # axes[0].plot(training_trajectory.time, training_trajectory.qvel, label='Training Trajectory')
        axes[1].plot(true_trajectory.time, true_trajectory.qvel, label='True (Mujoco) Trajectory')
        axes[1].plot(predicted_trajecotry.time, predicted_trajecotry.qvel, label='Predicted (SINDy) Trajectory', linestyle='--')
        axes[1].set_title('Velocity vs. Time')
        axes[1].set_ylabel('Velocity')
        axes[1].legend()
        axes[1].grid(True)

        # --- 3. Plot Acceleration Data ---
        # axes[0].plot(training_trajectory.time, training_trajectory.qacc, label='Training Trajectory')
        axes[2].plot(true_trajectory.time, true_trajectory.qacc, label='True (Mujoco) Trajectory')
        axes[2].plot(predicted_trajecotry.time, predicted_trajecotry.qacc, label='Predicted (SINDy) Trajectory', linestyle='--')
        axes[2].set_title('Acceleration vs. Time')
        axes[2].set_ylabel('Acceleration')
        axes[2].legend()
        axes[2].grid(True)

        # --- 4. Plot Force Data ---
        # axes[0].plot(training_trajectory.time, training_trajectory.force, label='Training Trajectory')
        axes[3].plot(true_trajectory.time, true_trajectory.force, label='True (Mujoco) Trajectory')
        axes[3].plot(predicted_trajecotry.time, predicted_trajecotry.force, label='Predicted (SINDy) Trajectory', linestyle='--')
        axes[3].set_title('Force vs. Time')
        axes[3].set_ylabel('Force')
        axes[3].set_xlabel('Time (s)')
        axes[3].legend()
        axes[3].grid(True)

        # Improve layout to prevent labels from overlapping
        plt.tight_layout(rect=[0, 0.03, 1, 0.96]) # Adjust layout to make room for the suptitle

        # Display the plots
        plt.savefig(filename)
        

if __name__ == '__main__':
    sampling_method = "uniform_unshuffled"

    print("Begin program")

    training_trajectory, true_trajectory, predicted_trajecotry = simulation(
        sampling_method,
        num_coordinates = 2,
        random_seed = 2,
        batch_number = 10,
        max_time = 10.0,
        initial_position = np.array([0.0, 0.0,0.0,0.0]),
        initial_condition_randomness = np.array([0.1]),
        forces_scale_vector = np.array([2.0, 2.0]),
        forces_period = 3.0,
        forces_period_shift = 0.5,
        data_ratio = 2.0,
        validation_time = 30.0,
        noise_level = 0.0,
    )

    visualization(training_trajectory, true_trajectory, predicted_trajecotry, "trajectory_comparison.png")
    
    print("End program")
