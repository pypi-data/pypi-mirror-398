"""

This module include every function in order to run the optimisation step for getting the sparse solution

"""

import numpy as np
from sklearn.linear_model import Lasso, LassoCV
from sklearn.metrics import make_scorer, r2_score
from typing import Callable, Tuple

from .logger import setup_logger

logger = setup_logger(__name__,level="DEBUG")


def condition_value(exp_matrix: np.ndarray, solution: np.ndarray) -> np.ndarray:
    """
    Calculate condition values based on the variance of the experimental matrix.

    Parameters:
        exp_matrix (np.ndarray): Experimental matrix.
        solution (np.ndarray): Solution vector.

    Returns:
        np.ndarray: Array of condition values.
    """
    return np.abs(np.var(exp_matrix, axis=0) * solution[:, 0])


def optimal_sampling(theta_values: np.ndarray, distance_threshold: float) -> np.ndarray:
    """
    (experimetnal) Selects optimal samples from a set of points based on a distance threshold.

    Parameters:
        theta_values (np.ndarray): Array of points.
        distance_threshold (float): Minimum distance to include a point.

    Returns:
        np.ndarray: Indices of selected points.
    """
    num_values = theta_values.shape[0]
    result_points = np.empty(theta_values.shape)
    selected_indices = np.zeros((num_values,), dtype=int)

    result_points[0, :] = theta_values[0, :]
    count = 1

    for i in range(1, num_values):
        point = theta_values[i, :]
        distance = np.sqrt(
            np.min(np.sum(np.power(result_points[:count, :] - point, 2), axis=1))
        )
        if distance > distance_threshold:
            result_points[count, :] = point
            selected_indices[count] = i
            count += 1

    return selected_indices[:count]


def bipartite_link(exp_matrix, num_coordinate, x_names, b_names):
    """
    This function is used to create the list of edges for the bipartite graph
    """
    group_sums = (
        np.abs(exp_matrix).reshape(num_coordinate, -1, exp_matrix.shape[1]).sum(axis=1)
    )

    rooted_links = [
        (x_names[i_idx], b_names[p_idx])
        for p_idx in range(group_sums.shape[0])
        for i_idx in range(group_sums.shape[1])
        if group_sums[p_idx, i_idx] != 0
    ]

    return rooted_links


def activated_catalog(
    exp_matrix: np.ndarray,
    pre_knowledge_mask: np.ndarray,
    num_coordinate: int,
):
    """
    Perform a recursive search to find the part ot the catalog that could be activated by the force vector.

    Args
        exp_matrix (np.ndarray): The experimental matrix.
        pre_knowledge_mask (np.ndarray): The pre-knowledge mask.
        noise_level (float): The noise level to consider for activation.
        sample_number (int): The number of samples in the experimental matrix.
        num_coordinate (int): The number of generalized coordinates.
        

    Returns:
        np.ndarray (num_coordinate,1): Activated catalog.
        np.ndarray (1,catalog_lenght): Activated coordinate.
    """

    logger.info("Starting activated catalog detection")
    logger.debug(f"Experimental matrix shape: {exp_matrix.shape}")

    exp_matrix_compressed = np.abs(exp_matrix).reshape(num_coordinate, -1, exp_matrix.shape[1]).sum(axis=1)

    logger.debug(f"Experimental matrix: {exp_matrix_compressed}")

    binary_compressed_exp_matrix = np.where(
        np.abs(exp_matrix).reshape(num_coordinate, -1, exp_matrix.shape[1]).sum(axis=1)
        > 0,
        1,
        0,
    )

    # Retrieve the pre-knowledge part of the matrix
    pre_knowledge_matrix = binary_compressed_exp_matrix[:, pre_knowledge_mask == 1].sum(axis=1, keepdims=True)

    logger.debug(f"Compressed force matrix: {pre_knowledge_matrix}")

    activation, activate_function = _recursive_activation(
        binary_compressed_exp_matrix,
        pre_knowledge_matrix,
    )

    return activate_function, activation


def _recursive_activation(
    binary_compressed_exp_matrix: np.ndarray,
    activate_vector: np.ndarray,
):
    """
    recursive function to find the activated catalog

    Args:
        compressed_exp_matrix (np.ndarray): Compressed experimental matrix.
        activate_vector (np.ndarray): Activated catalog.

    Returns:
        np.ndarray: Activated catalog.
    """

    activate_function = np.where(
        np.where(binary_compressed_exp_matrix + activate_vector > 1, 1, 0).sum(
            axis=0, keepdims=True
        )
        > 0,
        1,
        0,
    )

    activated_line = binary_compressed_exp_matrix.copy()

    activated_line[:, activate_function[0] == 0] = 0

    new_activate_vector = np.where(activated_line.sum(axis=1, keepdims=True) > 0, 1, 0)

    if np.sum(new_activate_vector) <= np.sum(activate_vector):
        return activate_vector, activate_function

    else:
        activation_vector, activation_function = _recursive_activation(
            binary_compressed_exp_matrix, new_activate_vector
        )

        return activation_vector, np.where(
            activation_function + activate_function > 0, 1, 0
        )


def remaining_catalog(
    exp_matrix: np.ndarray,
    activated_coordinates: np.ndarray,
    num_coordinate: int,
):
    """
    Get the remaining activated function after the explicit solution

    the remaining activated function (0) are the one that doesn't touche an activated coordinate.

    Args
        exp_matrix (np.ndarray): The experimental matrix.
        activated_coordinates (np.ndarray): The activated coordinates.
        num_coordinate (int): The number of generalized coordinates.
    Returns:
        np.ndarray (1,catalog_lenght): Remaining explicit activated catalog.
    """

    exp_matrix_compressed = np.abs(exp_matrix).reshape(num_coordinate, -1, exp_matrix.shape[1]).sum(axis=1)

    function_mask = exp_matrix_compressed[activated_coordinates.flatten() == 1, :].sum(axis=0,keepdims=True)

    return np.where(function_mask > 0, 1, 0)


def normalize_experiment_matrix(
    exp_matrix: np.ndarray, null_effect: bool = False
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    (Deprecated) Clearly not in use for a long time...
    Normalizes an experimental matrix by its variance and mean.

    Parameters:
        exp_matrix (np.ndarray): Experimental matrix to normalize.
        null_effect (bool): Whether to consider null effect in normalization.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: Normalized matrix, reduction indices, and variance.
    """
    variance = np.var(exp_matrix, axis=0) * int(not null_effect) + int(null_effect)
    mean = np.mean(exp_matrix, axis=0) * int(not null_effect)

    reduction_indices = np.argwhere(variance != 0).flatten()
    reduced_matrix = exp_matrix[:, reduction_indices]
    normalized_matrix = (reduced_matrix - mean[reduction_indices]) / variance[
        reduction_indices
    ]

    return normalized_matrix, reduction_indices, variance


def unnormalize_experiment(
    coefficients: np.ndarray,
    variance: np.ndarray,
    reduction_indices: np.ndarray,
    exp_matrix: np.ndarray,
) -> np.ndarray:
    """
    (Deprecated) Clearly not in use for a long time...
    Reverts normalization of a solution vector.

    Parameters:
        coefficients (np.ndarray): Normalized coefficients.
        variance (np.ndarray): Variance used for normalization.
        reduction_indices (np.ndarray): Indices used for dimensionality reduction.
        exp_matrix (np.ndarray): Original experimental matrix.

    Returns:
        np.ndarray: Unnormalized solution vector.
    """
    solution_unscaled = coefficients / variance[reduction_indices]
    # friction_coefficient = -solution_unscaled[-1]

    solution = np.zeros((exp_matrix.shape[1], 1))
    solution[reduction_indices, 0] = solution_unscaled

    return solution


def covariance_vector(
    exp_matrix: np.ndarray, covariance_matrix: np.ndarray, num_time_steps: int
) -> np.ndarray:
    """
    Calculates the covariance vector across time steps for an experimental matrix.

    Parameters:
        exp_matrix (np.ndarray): Experimental matrix.
        covariance_matrix (np.ndarray): Covariance matrix.
        num_time_steps (int): Number of time steps.

    Returns:
        np.ndarray: Covariance vector summed across time steps.
    """
    result_matrix = exp_matrix @ covariance_matrix @ exp_matrix.T
    diagonal_covariance = np.diagonal(result_matrix).reshape(-1, num_time_steps)
    summed_covariance = np.sum(diagonal_covariance, axis=1)

    return summed_covariance


## Optimisation function


def amputate_experiment_matrix(
    experiment_matrix: np.ndarray,
    mask: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simple function to split the experiment matrix into an reduced experiment matrix and an external vector.

    Can be used to split experiment matrix in the case of implicit or explicit regression

    Parameters:
        exp_matrix (pre_knowledge_mask): Experimental matrix.
        mask (pre_knowledge_mask): a mask to indicate the position of the pre-knowledge column.

    Returns:
        np.ndarray : Reduced experiment matrix .
        np.ndarray : Left Hand Side vector (forces vector)
    """

    logger.info("Amputating experiment matrix")
    logger.debug(f"Mask index: {mask}")

    LHS = experiment_matrix[:, mask==1].sum(axis=1).reshape(-1, 1)

    experiment_matrix = experiment_matrix[:,mask==0]

    return experiment_matrix, LHS


def populate_solution(
    solution: np.ndarray,
    mask: np.ndarray,
) -> np.ndarray:
    """
    Opposite of amputate_experiment_matrix add a -1 in the solution where the mask should have been. (Because Left Hand Side is -1 )
    """

    logger.info("Populate experiment solution")
    logger.debug(f"Mask index: {mask}")

    logger.debug(f"Solution before populate: {solution.flatten()}")

    new_solution = np.zeros_like(mask, dtype=solution.dtype)
    new_solution[mask==0] = solution.flatten()
    new_solution[mask==1] = -1.0

    return new_solution.reshape(-1,1)


## TODO maybe I could turn everything on jax...


def hard_threshold_sparse_regression_old(
    forces_vector: np.ndarray,
    exp_matrix: np.ndarray,
    # catalog: np.ndarray,
    condition_func: Callable = condition_value,
    threshold: float = 0.03,
) -> np.ndarray:
    """
    (DEPRECATED) should use the new formalism for regression function (experiment_matrix, position of b vector (mask))
    Performs sparse regression with a hard threshold to select significant features.

    Parameters:
        exp_matrix (np.ndarray): Experimental matrix.
        forces_vector (np.ndarray): Forces vector.
        condition_func (Callable): Function to calculate condition values.
        threshold (float): Threshold for feature selection.

    Returns:
        np.ndarray: solution vector. shape (-1,)
    """

    forces_vector, exp_matrix = np.array(forces_vector), np.array(exp_matrix)

    solution, residuals, rank, _ = np.linalg.lstsq(
        exp_matrix, forces_vector, rcond=None
    )

    retained_solution = solution.copy()
    result_solution = np.zeros(solution.shape)
    active_indices = np.arange(len(solution))
    steps = []

    prev_num_indices = len(solution) + 1
    current_num_indices = len(solution)

    while current_num_indices < prev_num_indices:
        prev_num_indices = current_num_indices
        condition_values = condition_func(exp_matrix, retained_solution)
        steps.append((retained_solution, condition_values, active_indices))

        significant_indices = np.argwhere(
            condition_values / np.max(condition_values) > threshold
        ).flatten()
        active_indices = active_indices[significant_indices]
        exp_matrix = exp_matrix[:, significant_indices]

        retained_solution, residuals, rank, _ = np.linalg.lstsq(
            exp_matrix, forces_vector, rcond=None
        )
        current_num_indices = len(active_indices)

    result_solution[active_indices] = retained_solution

    result_solution = np.reshape(result_solution, (-1,))  # flatten

    return result_solution  # model_fit, result_solution, reduction_count, steps # deprecated


def hard_threshold_sparse_regression(
    whole_exp_matrix: np.ndarray,
    mask: int|np.ndarray,
    condition_func: Callable = condition_value,
    threshold: float = 0.03,
) -> np.ndarray:
    """
    Performs sparse regression with a hard threshold to select significant features.

    Parameters:
        exp_matrix (np.ndarray): Experimental matrix.
        mask (int): the forces column
        condition_func (Callable): Function to calculate condition values.
        threshold (float): Threshold for feature selection.

    Returns:
        np.ndarray: solution vector. shape (-1,1)
    """

    exp_matrix, forces_vector = amputate_experiment_matrix(whole_exp_matrix, mask)

    solution, residuals, rank, _ = np.linalg.lstsq(
        exp_matrix, forces_vector, rcond=None
    )

    retained_solution = solution.copy()
    result_solution = np.zeros(solution.shape)
    active_indices = np.arange(len(solution))
    steps = []

    prev_num_indices = len(solution) + 1
    current_num_indices = len(solution)

    while current_num_indices < prev_num_indices:
        prev_num_indices = current_num_indices
        condition_values = condition_func(exp_matrix, retained_solution)
        steps.append((retained_solution, condition_values, active_indices))

        significant_indices = np.argwhere(
            condition_values / np.max(condition_values) > threshold
        ).flatten()
        active_indices = active_indices[significant_indices]
        exp_matrix = exp_matrix[:, significant_indices]

        retained_solution, residuals, rank, _ = np.linalg.lstsq(
            exp_matrix, forces_vector, rcond=None
        )
        current_num_indices = len(active_indices)

    result_solution[active_indices] = retained_solution

    result_solution = np.reshape(result_solution, (-1, 1))

    result_solution = populate_solution(result_solution, mask)

    return result_solution  # model_fit, result_solution, reduction_count, steps # deprecated


def soft_threshold(x: np.ndarray, threshold: float) -> np.ndarray:
    """
    Soft-thresholding operator (proximal operator for L1 norm).
    
    Parameters:
        x (np.ndarray): Input array.
        threshold (float): Threshold value.
    
    Returns:
        np.ndarray: Soft-thresholded array.
    """
    return np.sign(x) * np.maximum(np.abs(x) - threshold, 0)


def proximal_gradient_descent(
    whole_exp_matrix: np.ndarray,
    mask: np.ndarray,
    sparsity_factor: float = 0.01,
    learning_rate: float = None,
    max_iterations: int = 10**4,
    tolerance: float = 1e-5,
    adaptive_lr: bool = True,
) -> np.ndarray:
    """
    Performs proximal gradient descent with L1 regularization for sparse feature selection.
    
    This implements the iterative soft-thresholding algorithm (ISTA), which is equivalent
    to Lasso regression but with explicit control over the optimization process.
    
    Parameters:
        whole_exp_matrix (np.ndarray): Experimental matrix including forces column.
        mask (int): The forces column index.
        sparsity_factor (float): L1 regularization parameter (lambda). Higher values increase sparsity.
        learning_rate (float): Step size. If None, uses 1/(largest eigenvalue of X^T X).
        max_iterations (int): Maximum number of iterations.
        tolerance (float): Convergence tolerance based on coefficient change.
        adaptive_lr (bool): Whether to use adaptive learning rate (Lipschitz constant).
    
    Returns:
        np.ndarray: Coefficients of the fitted model. shape (-1, 1)
    """
    exp_matrix, forces_vector = amputate_experiment_matrix(whole_exp_matrix, mask)
    
    y = forces_vector[:, 0]
    n_samples, n_features = exp_matrix.shape
    
    # Normalize for numerical stability
    X_mean = np.mean(exp_matrix, axis=0)
    X_std = np.std(exp_matrix, axis=0) + 1e-10
    X_normalized = (exp_matrix - X_mean) / X_std
    
    y_mean = np.mean(y)
    y_centered = y - y_mean
    
    # Initialize coefficients
    beta = np.zeros(n_features)
    
    # Compute learning rate based on Lipschitz constant if not provided
    if learning_rate is None:
        if adaptive_lr:
            # Lipschitz constant L = largest eigenvalue of X^T X / n
            XTX = X_normalized.T @ X_normalized / n_samples
            eigenvalues = np.linalg.eigvalsh(XTX)
            L = eigenvalues[-1]
            learning_rate = 1.0 / (L + 1e-10)
            logger.info(f"Computed adaptive learning rate: {learning_rate:.6f}")
        else:
            learning_rate = 0.001
    
    logger.info(f"Starting proximal gradient descent with sparsity_factor={sparsity_factor}")
    
    # Proximal gradient descent iterations
    for iteration in range(max_iterations):
        beta_old = beta.copy()
        
        # Compute gradient of squared loss: (1/n) * X^T (X*beta - y)
        residual = X_normalized @ beta - y_centered
        gradient = (X_normalized.T @ residual) / n_samples
        
        # Gradient descent step
        beta_temp = beta - learning_rate * gradient
        
        # Proximal step (soft-thresholding)
        beta = soft_threshold(beta_temp, learning_rate * sparsity_factor)
        
        # Check convergence
        coef_change = np.max(np.abs(beta - beta_old))
        if coef_change < tolerance:
            logger.info(f"Converged at iteration {iteration + 1} with coefficient change {coef_change:.2e}")
            break
        
        if (iteration + 1) % 1000 == 0:
            n_nonzero = np.sum(beta != 0)
            loss = 0.5 * np.mean(residual**2) + sparsity_factor * np.sum(np.abs(beta))
            logger.info(f"Iteration {iteration + 1}: Loss={loss:.6f}, Non-zero coeffs={n_nonzero}, Change={coef_change:.2e}")
    else:
        logger.warning(f"Maximum iterations ({max_iterations}) reached without convergence")
    
    # Denormalize coefficients
    beta_denormalized = beta / X_std
    
    # Report sparsity
    n_nonzero = np.sum(beta_denormalized != 0)
    logger.info(f"Final solution has {n_nonzero}/{n_features} non-zero coefficients ({100*n_nonzero/n_features:.1f}%)")
    
    # Reshape and populate solution
    result_solution = np.reshape(beta_denormalized, (-1, 1))
    result_solution = populate_solution(result_solution, mask)
    
    return result_solution


def lasso_regression(
    whole_exp_matrix: np.ndarray,
    mask: np.ndarray,
    max_iterations: int = 10**4,
    tolerance: float = 1e-5,
    eps: float = 5e-4,
) -> np.ndarray:
    """
    Performs Lasso regression to select sparse features.

    Parameters:
        exp_matrix (np.ndarray): Experimental matrix.
        mask (int): the forces column
        max_iterations (int): Maximum number of iterations.
        tolerance (float): Convergence tolerance.
        eps (float): Regularization parameter.

    Returns:
        np.ndarray: Coefficients of the fitted model. shape (-1,)
    """

    exp_matrix, forces_vector = amputate_experiment_matrix(whole_exp_matrix, mask)

    y = forces_vector[:, 0]
    model_cv = LassoCV(
        cv=5, random_state=0, max_iter=max_iterations, eps=eps, tol=tolerance, verbose=2
    )
    model_cv.fit(exp_matrix, y)
    best_alpha = model_cv.alpha_

    logger.info(f"LassoCV complete. Best alpha found: {best_alpha}")

    lasso_model = Lasso(
        alpha=best_alpha,
        max_iter=max_iterations,
        tol=tolerance,
    )
    lasso_model.fit(exp_matrix, y)

    result_solution = np.reshape(lasso_model.coef_, (-1, 1))

    result_solution = populate_solution(result_solution, mask)

    return result_solution


def sparse_tradeoff_score(estimator, X, y, alpha=0.2):
    y_pred = estimator.predict(X)
    r2 = r2_score(y, y_pred)
    nonzero_ratio = np.mean(estimator.coef_ != 0)
    # trade-off: accuracy – penalty
    return r2 - alpha * nonzero_ratio


sparse_soft_scorer = make_scorer(sparse_tradeoff_score, greater_is_better=True)


def lasso_regression_rapids(
    whole_exp_matrix: np.ndarray,
    mask: np.ndarray,
    max_iterations: int = 10000,
    tolerance: float = 1e-5,
) -> np.ndarray:
    """
    Performs Lasso regression on the GPU using the correct cuml pattern:
    Lasso + GridSearchCV.
    """

    from cuml.model_selection import GridSearchCV

    # 1. CPU PRE-PROCESSING
    exp_matrix_np, forces_vector_np = amputate_experiment_matrix(whole_exp_matrix, mask)

    # 2. HOST-TO-DEVICE TRANSFER
    # exp_matrix_gpu = cp.asarray(exp_matrix_np)
    # y_gpu = cp.asarray(forces_vector_np[:, 0])

    # logger.info(" shape of element",exp_matrix_gpu.shape,y_gpu.shape)
    exp_matrix_gpu = exp_matrix_np
    y_gpu = forces_vector_np[:, 0]

    # exp_matrix_gpu = exp_matrix_np
    # y_gpu = forces_vector_np.flatten()

    # 3. GPU COMPUTATION with GridSearchCV
    # Step 3a: Define the parameter grid to search.
    # A logarithmic space is standard for regularization parameters.
    param_grid = {"alpha": np.logspace(-3.5, 1, 20).astype(np.float32)}

    # param_grid = {
    #     'alpha': np.array([0.003742043051845873])
    # }

    # # Step 3b: Create the base Lasso model instance.
    lasso_base_model = Lasso(max_iter=max_iterations, tol=tolerance)

    # # Step 3c: Set up and run the GridSearchCV
    # # This will train multiple models on the GPU in parallel folds.
    grid_search = GridSearchCV(
        lasso_base_model, param_grid, cv=5, verbose=3, scoring="r2"
    )
    grid_search.fit(exp_matrix_gpu, y_gpu)

    # # The best estimator is a fully trained Lasso model with the optimal alpha
    # best_lasso_model = grid_search.best_estimator_
    logger.info(
        f"GridSearchCV complete. Best alpha found: {grid_search.best_estimator_.alpha}"
    )

    lasso_model = Lasso(
        alpha=grid_search.best_estimator_.alpha, max_iter=max_iterations, tol=tolerance
    )
    lasso_model.fit(exp_matrix_gpu, y_gpu)

    # 4. DEVICE-TO-HOST TRANSFER
    result_amputated_np = lasso_model.coef_  # .get()
    # result_amputated_np = lasso_model.coef_.get()
    result_amputated_np = np.reshape(result_amputated_np, (-1, 1))

    # 5. CPU POST-PROCESSING
    final_solution = populate_solution(result_amputated_np, mask)

    return final_solution


def lasso_regression_old(
    forces_vector: np.ndarray,
    exp_matrix: np.ndarray,
    max_iterations: int = 10**4,
    tolerance: float = 1e-5,
    eps: float = 5e-4,
) -> np.ndarray:
    """
    (DEPRECATED) should use the new formalism for regression function (experiment_matrix, position of b vector (mask))
    Performs Lasso regression to select sparse features.

    Parameters:
        forces_vector (np.ndarray): Dependent variable vector.
        exp_matrix (np.ndarray): Normalized experimental matrix.
        max_iterations (int): Maximum number of iterations.
        tolerance (float): Convergence tolerance.
        eps (float): Regularization parameter.

    Returns:
        np.ndarray: Coefficients of the fitted model. shape (-1,)
    """

    forces_vector, exp_matrix = np.array(forces_vector), np.array(exp_matrix)

    y = forces_vector[:, 0]
    model_cv = LassoCV(
        cv=5, random_state=0, max_iter=max_iterations, eps=eps, tol=tolerance
    )
    model_cv.fit(exp_matrix, y)
    best_alpha = model_cv.alpha_

    lasso_model = Lasso(alpha=best_alpha, max_iter=max_iterations, tol=tolerance)
    lasso_model.fit(exp_matrix, y)

    return lasso_model.coef_


# Optimisation in Jax Framework

"""
So the goal is to use the jax framework in order to run the optimisation step, parallesing if multiple regression are run.
Instead of going into a constrained optimisation problem like suggested in the original SINDy-PI paper,
I prefer to go for a masked regression. This enable to run a simpler version of regression algorithm.

In order to be able to run normal regression we should merge maybe the experimental matrix with the forces vector ?
It may imply that it break the unify catalog formalism... As a whole it may be better to keep the catalog formalism
and add the forces vector as a new column in the experiment matrix and in the catalog...

After thinking about it, it would be clearly the best thing to add ? everything will be put inside a only matrix and retrieval is done with it.
If multiple function need to be put aside for a regression they can be easily merged by spcifying the mask.
In addition, if the experiment matrix is made through jax, it could be easily parallelized.

Input are the following :
- exp_matrix (n_sample,function): experimental matrix 
- mask (k): the mask to apply

Since now the experiment matrix contain also the external forces vector, every regression function should stick with these input.


"""

# def jax_hard_treshold(
#     exp_matrix: np.ndarray,
#     mask: int,
#     condition_func: Callable = condition_value,
#     threshold: float = 0.03,
# ) -> np.ndarray:
#     """
#     Performs sparse regression with a hard threshold to select significant features.

#     Parameters:
#         exp_matrix (np.ndarray): Experimental matrix.
#         mask (k): the mask to apply
#         condition_func (Callable): Function to calculate condition values.
#         threshold (float): Threshold for feature selection.

#     Returns:
#         np.ndarray: solution vector. shape (-1,)
#     """

#     b_vector = exp_matrix[:, mask]

#     exp_matrix

#     solution, residuals, rank, _ = np.linalg.lstsq(
#         exp_matrix, forces_vector, rcond=None
#     )

#     # print("solution shape",solution.shape)

#     retained_solution = solution.copy()
#     result_solution = np.zeros(solution.shape)
#     active_indices = np.arange(len(solution))
#     steps = []

#     prev_num_indices = len(solution) + 1
#     current_num_indices = len(solution)

#     while current_num_indices < prev_num_indices:
#         prev_num_indices = current_num_indices
#         condition_values = condition_func(exp_matrix, retained_solution)
#         steps.append((retained_solution, condition_values, active_indices))

#         significant_indices = np.argwhere(
#             condition_values / np.max(condition_values) > threshold
#         ).flatten()
#         active_indices = active_indices[significant_indices]
#         exp_matrix = exp_matrix[:, significant_indices]

#         retained_solution, residuals, rank, _ = np.linalg.lstsq(
#             exp_matrix, forces_vector, rcond=None
#         )
#         current_num_indices = len(active_indices)

#     result_solution[active_indices] = retained_solution

#     result_solution = np.reshape(result_solution, (-1,))  # flatten

#     return result_solution  # model_fit, result_solution, reduction_count, steps # deprecated
