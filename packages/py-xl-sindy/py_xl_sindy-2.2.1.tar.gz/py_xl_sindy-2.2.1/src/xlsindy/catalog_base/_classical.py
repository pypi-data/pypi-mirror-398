"""
Contains the function responsible for the classical part of the catalog.
"""

import numpy as np

from ..catalog import CatalogCategory

from sympy import latex


class Classical(CatalogCategory):
    """
    Classical newtonnian catalog.

    Args:
        symbolic_catalog (np.ndarray) : the catalog listing every symbolic function of the catalog (k,)
        binary_matrix (np.ndarray) : the matrix of repartition of the symbolic function (k,num_coordinate)
    """

    def __init__(self, symbolic_catalog: np.ndarray, binary_matrix: np.ndarray):
        self.symbolic_catalog = symbolic_catalog
        self.binary_matrix = binary_matrix

        self.symbolic_catalog_length = self.binary_matrix.shape[0]

        # Required variable
        self.catalog_length = int(self.binary_matrix.sum())
        self.num_coordinate = int(self.binary_matrix.shape[1])

    def create_solution_vector(self, coeff_matrix: np.ndarray):
        """
        Args:
            coeff_matrix (np.ndarray) : a matrix of size (symbolic_catalog_length,num_coordinate) which coefficient represent the ideal solution coefficient
        """

        # Flatten the expand matrix in row-major order and find indices where its value is 1.
        mask = self.binary_matrix.ravel() == 1

        # Use boolean indexing to select corresponding coefficients (works for any dtype).
        coeff_flat = coeff_matrix.ravel()[mask]

        # Reshape into a column vector.
        coeff_vector = coeff_flat.reshape(-1, 1)
        return coeff_vector

    def expand_catalog(self):
        # Create the output array
        res = np.zeros((self.catalog_length, self.num_coordinate), dtype=object)

        # Compute the cumulative row indices (flattened order, then reshaped)
        line_count = np.cumsum(self.binary_matrix.ravel()) - 1
        line_count = line_count.reshape(self.binary_matrix.shape)

        # Compute the product in a vectorized way
        prod = (self.binary_matrix * self.symbolic_catalog[:, None]).ravel()
        indices = np.argwhere(prod != 0)

        # Create an array of column indices that match the row-major flattening order
        cols = np.tile(np.arange(self.num_coordinate), self.binary_matrix.shape[0])

        # Use fancy indexing to assign the values
        res[line_count.ravel()[indices], cols[indices]] = prod[indices]

        return res

    def label(self):
        """
        Return a list of labels from the catalog.
        """
        mask = self.binary_matrix.ravel() == 1

        # Create the label_matrix array with shape (symbolic_catalog_length, num_coordinate)
        label_matrix = np.empty(
            (self.symbolic_catalog_length, self.num_coordinate), dtype=object
        )

        # Fill the label_matrix with the format "{symbolic_catalog[p]} coor_{n}"
        for p in range(self.symbolic_catalog_length):
            for n in range(self.num_coordinate):
                text = f"$$\\text{{coordinate}}_{{{n}}} \\ {latex(self.symbolic_catalog[p])}$$"
                text = text.replace("qdd", "\\ddot{{q}}")
                text = text.replace("qd", "\\dot{{q}}")

                label_matrix[p, n] = text

        label_vector = label_matrix.ravel()[mask]

        return list(label_vector)

    def separate_by_mask(self, mask):
        flat_binary_matrix = self.binary_matrix.flatten()

        one_indices = np.flatnonzero(flat_binary_matrix)

        binary_matrix_masked = flat_binary_matrix.copy()
        binary_matrix_masked[one_indices] = mask
        binary_matrix_masked = binary_matrix_masked.reshape(self.binary_matrix.shape)

        symbolic_mask = np.flatnonzero(binary_matrix_masked.sum(axis=1))

        binary_matrix_anti_masked = flat_binary_matrix.copy()
        binary_matrix_anti_masked[one_indices] = ~mask
        binary_matrix_anti_masked = binary_matrix_anti_masked.reshape(
            self.binary_matrix.shape
        )

        symbolic_anti_mask = np.flatnonzero(binary_matrix_anti_masked.sum(axis=1))

        return Classical(
            symbolic_catalog=self.symbolic_catalog[symbolic_mask],
            binary_matrix=binary_matrix_masked[symbolic_mask],
        ), Classical(
            symbolic_catalog=self.symbolic_catalog[symbolic_anti_mask],
            binary_matrix=binary_matrix_anti_masked[symbolic_anti_mask],
        )
