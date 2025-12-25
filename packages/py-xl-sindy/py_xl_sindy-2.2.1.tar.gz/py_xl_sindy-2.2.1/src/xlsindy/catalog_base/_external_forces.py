"""
Contains the function responsible for the external forces part of the catalog.
"""

from typing import List
import numpy as np

from ..catalog import CatalogCategory


class ExternalForces(CatalogCategory):
    """
    External forces catalog.

    Args:
        interlink_list (List[List[int]]) : Presence of the forces on each of the coordinate, 1-indexed can be negative for retroactive forces.
        symbol_matrix (np.ndarray) : Symbolic variable matrix for the system.
    """

    def __init__(self, interlink_list: List[List[int]], symbol_matrix: np.ndarray):
        self.interlink_list = interlink_list
        self.symbolic_matrix = symbol_matrix
        ## Required variable
        self.num_coordinate = len(self.interlink_list)
        self.catalog_length = self.num_coordinate

    def create_solution_vector(self):
        return np.ones(( self.num_coordinate,1))*-1.0

    def expand_catalog(self):
        res = np.empty((self.num_coordinate, self.num_coordinate), dtype=object)
        res.fill(0)

        for i, additive in enumerate(self.interlink_list):
            for index in additive:
                if res[i, i] is None:
                    res[i, i] = (
                        np.sign(index) * self.symbolic_matrix[0, np.abs(index) - 1]
                    )

                else:
                    res[i, i] += (
                        np.sign(index) * self.symbolic_matrix[0, np.abs(index) - 1]
                    )

        return res

    def label(self):
        """
        Return a place holder lab for the external forces.
        """

        return [f"$$F_{{ext_{{{i}}}}}$$" for i in range(0, self.num_coordinate)]

    # externl forces are not separable by mask
    def separate_by_mask(self, mask):
        return ExternalForces(
            interlink_list=self.interlink_list, symbol_matrix=self.symbolic_matrix
        ), ExternalForces(
            interlink_list=self.interlink_list, symbol_matrix=self.symbolic_matrix
        )
