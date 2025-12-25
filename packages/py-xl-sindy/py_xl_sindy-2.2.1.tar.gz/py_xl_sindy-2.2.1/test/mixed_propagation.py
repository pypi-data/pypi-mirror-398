import matplotlib.pyplot as plt
import numpy as np 

from xlsindy.optimization import activated_catalog,remaining_catalog


if __name__ == "__main__":
    
    experiment_matrix = np.array(
        [
            [1, 0, 0, 1, 0, 0, 0, 0, 1],
            [0, 1, 0, 1, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 1, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 1, 0]
        ]
    )

    pre_knowledge_mask = np.array(
        [0, 1, 1, 0, 0, 0, 0, 0, 0]
    )

    num_coordinates = experiment_matrix.shape[0]

    print("Experiment matrix:")
    print(experiment_matrix)
    print("Pre-knowledge mask:")
    print(pre_knowledge_mask)
    print("Number of coordinates:", num_coordinates)

    plt.imshow(experiment_matrix, cmap="Greys", interpolation="nearest")
    plt.title("Experiment Matrix")
    plt.ylabel("Coordinates")
    plt.xlabel("Functions")
    plt.savefig("mixed_propagation_test_original_matrix.png")

    activated_functions, activated_coordinates = activated_catalog(
        experiment_matrix,
        pre_knowledge_mask,
        num_coordinates
    )

    print("Activated functions:", activated_functions)
    print("Activated coordinates:", activated_coordinates)

    explicit_activated_coordinates = np.array(
        [0, 1, 1, 0, 0, 0]
    ).T

    remaining_functions = remaining_catalog(
        experiment_matrix,
        explicit_activated_coordinates,
        num_coordinates
    )

    print("Remaining functions:", remaining_functions)