import numpy as np
from scipy.spatial import KDTree
from scipy.special import gamma


def estimate_volumes(data, k):
    """Estimate the total volume of a distribution of point"""
    n, d = data.shape
    tree = KDTree(data)
    distances, _ = tree.query(data, k=k + 1)

    R_k = distances[:, -1]  # Distance to the k-th nearest neighbor

    unit_ball_volume = (np.pi ** (d / 2)) / gamma(d / 2 + 1)
    local_volumes = unit_ball_volume * (R_k**d) / k
    return np.sum(local_volumes)


def relative_mse(X, Y):
    """Relative Mean Squared Error (scale-invariant)"""
    return np.sqrt(np.mean(((X - Y) / (np.max(X) - np.min(X))) ** 2)) * 100


def normalise_solution(X):
    """Normalise the solution vector because Lagrangian can be translated and multiply by singleton"""

    max_ind = np.argmax(np.abs(X))
    return X / X[max_ind]


def estimate_local_volumes_emp(data, k):
    n, d = data.shape
    tree = KDTree(data)
    distances, indices = tree.query(data, k=k + 1)

    neighboor_vec_norm = (
        data[indices[:, 1:]] - np.repeat(data[:, np.newaxis, :], repeats=k, axis=1)
    ) / distances[:, 1:, np.newaxis]

    discount = 1 - np.linalg.norm(np.mean(neighboor_vec_norm, axis=1), axis=1)

    R_k = distances[:, -1]  # Distance to the k-th nearest neighbor

    unit_ball_volume = (np.pi ** (d / 2)) / gamma(d / 2 + 1)
    local_volumes = discount * unit_ball_volume * (R_k**d) / k
    return local_volumes


def convert_to_lists(d):
    if isinstance(d, dict):
        return {k: convert_to_lists(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_to_lists(i) for i in d]
    elif isinstance(d, np.ndarray):
        return convert_to_lists(d.tolist())
    elif isinstance(d, (np.float32, np.float64)):
        return float(d)
    else:
        return d


# Example usage:

if __name__ == "__main__":
    sample = 10

    res = np.zeros(sample)

    for i in range(sample):
        data = np.random.rand(10000, 3)  # 100 points in 3D space
        k = 3
        local_volumes = estimate_volumes(data, k)

        res[i] = local_volumes

    print(f"Estimated Volume of the Data Distribution: {np.mean(res):.4f}")
