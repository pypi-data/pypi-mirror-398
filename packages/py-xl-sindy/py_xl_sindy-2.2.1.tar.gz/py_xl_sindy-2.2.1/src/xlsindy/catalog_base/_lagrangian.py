"""
Contains the function responsible for the lagrangian part of the catalog.
"""

import sympy
import numpy as np
from .. import euler_lagrange

from ..catalog import CatalogCategory

from sympy import latex


class Lagrange(CatalogCategory):
    """
    Lagrange based catalog.

    Args:
        catalog (List[sympy.Expr]): The catalog of functions to be used in the Lagrangian equations.
        symbol_matrix (np.ndarray): The matrix of symbolic variables (external forces, positions, velocities, and accelerations).
        time_symbol (sympy.Symbol): The symbolic variable representing time.
    """

    def __init__(self, catalog, symbol_matrix: np.ndarray, time_symbol: sympy.Symbol):
        self.catalog = catalog
        self.symbol_matrix = symbol_matrix
        self.time_symbol = time_symbol

        ## Required attributes
        self.catalog_length = int(len(catalog))
        self.num_coordinate = int(self.symbol_matrix.shape[1])

    def create_solution_vector(self, expression: sympy.Expr):
        expanded_expression_terms = sympy.expand(
            sympy.expand_trig(expression)
        ).args  # Expand the expression in order to get base function (ex: x, x^2, sin(s), ...)
        solution_vector = np.zeros((len(self.catalog), 1))

        for term in expanded_expression_terms:
            for idx, catalog_term in enumerate(self.catalog):
                test = term / catalog_term
                if (
                    len(test.args) == 0
                ):  # if test is a constant it means that catalog_term is inside equation
                    solution_vector[idx, 0] = test

        return solution_vector.reshape(-1, 1)

    def expand_catalog(self):
        res = np.empty((len(self.catalog), self.num_coordinate), dtype=object)

        for i in range(self.num_coordinate):
            catalog_lagrange = list(
                map(
                    lambda x: euler_lagrange.compute_euler_lagrange_equation(
                        x, self.symbol_matrix, self.time_symbol, i
                    ),
                    self.catalog,
                )
            )
            res[:, i] = catalog_lagrange

        return res

    def label(self):
        """
        Return a label for each element of the catalog.
        """

        label_list = [f"$${latex(term)}$$" for term in self.catalog]

        label_list = list(map(lambda x: x.replace("qdd", "\\ddot{{q}}"), label_list))

        label_list = list(map(lambda x: x.replace("qd", "\\dot{{q}}"), label_list))

        return label_list

    def separate_by_mask(self, mask):
        return Lagrange(
            catalog=self.catalog[mask == 1],
            symbol_matrix=self.symbol_matrix,
            time_symbol=self.time_symbol,
        ), Lagrange(
            catalog=self.catalog[mask == 0],
            symbol_matrix=self.symbol_matrix,
            time_symbol=self.time_symbol,
        )
