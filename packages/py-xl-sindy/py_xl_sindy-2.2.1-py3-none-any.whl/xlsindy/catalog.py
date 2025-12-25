"""
This file implement catalog classes, it provides a unified way to treat of catalog category through abstract classes

This file replace the catalog_gen function from older version.

"""

from abc import ABC, abstractmethod, ABCMeta
import functools

import numpy as np

from typing import List,Tuple
from typing import Self


# Trick in order to get concatenated docstring for child of abstract class ! great explanation here :https://stackoverflow.com/questions/100003/what-are-metaclasses-in-python
class _CatalogMetaClass(ABCMeta):
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        # Concatenate the docstring between the abstract method and the child one
        for attr_name, attr in namespace.items():
            if not callable(attr) or attr_name.startswith("__"):
                continue

            for base in bases:
                base_method = getattr(base, attr_name, None)
                if base_method and base_method.__doc__:
                    child_doc = attr.__doc__ or ""
                    if base_method.__doc__ not in child_doc:
                        combined = (
                            f"{base_method.__doc__.strip()}\n\n{child_doc.strip()}"
                            if child_doc
                            else base_method.__doc__
                        )
                        attr.__doc__ = combined

        # Wrap __init__ to enforce attribute presence and type
        orig_init = namespace.get("__init__", None)
        if orig_init is None:
            # If __init__ not defined here, try to get from bases
            orig_init = getattr(cls, "__init__", None)

        if orig_init:

            @functools.wraps(orig_init)
            def wrapped_init(self, *args, **kwargs):
                # Run the wrapped function
                orig_init(self, *args, **kwargs)

                # The required variable with required type
                required_attrs = {
                    "catalog_length": int,
                    "num_coordinate": int,
                }

                missing = []
                wrong_type = []

                for attr_name, attr_type in required_attrs.items():
                    if not hasattr(self, attr_name):
                        missing.append(attr_name)
                    else:
                        val = getattr(self, attr_name)
                        if not isinstance(val, attr_type):
                            wrong_type.append((attr_name, type(val), attr_type))

                if missing:
                    raise AttributeError(
                        f"Instance of class '{cls.__name__}' is missing required "
                        f"attributes set in __init__: {missing}"
                    )
                if wrong_type:
                    msg = ", ".join(
                        f"'{attr}' has type {actual.__name__} but expected {expected.__name__}"
                        for attr, actual, expected in wrong_type
                    )
                    raise TypeError(
                        f"Instance of class '{cls.__name__}' has attribute type errors: {msg}"
                    )

            cls.__init__ = wrapped_init

        # Check method function
        def check_method(method_name, check_func):
            orig_method = namespace.get(method_name, None)
            if orig_method:

                @functools.wraps(orig_method)
                def wrapped_method(self, *args, **kwargs):
                    result = orig_method(self, *args, **kwargs)
                    check_func(self, result, method=method_name)
                    return result

                setattr(cls, method_name, wrapped_method)

        def check_ndarray_shape(expected_shape_func, expected_shape_hint=""):
            """
            Check if the output is a np.ndarray of the correct shape. Raise error if not compliant

            Args:
                expected_shape_func (function): a function that take self as input and return a shape tupe. (usufull to check dynamic variable like the one constrained in the init)
            """

            def check_func(self, result, method):
                if not isinstance(result, np.ndarray):
                    raise TypeError(
                        f"{cls.__name__}.{method}() must return a numpy.ndarray, got {type(result)}"
                    )
                expected_shape = expected_shape_func(self)
                if result.shape != expected_shape:
                    raise ValueError(
                        f"{cls.__name__}.{method}() must return array of shape {expected_shape}, got {result.shape} (expect : {expected_shape_hint})"
                    )

            return check_func

        # Method checked :
        check_method(
            "create_solution_vector",
            check_ndarray_shape(
                lambda self: (self.catalog_length, 1), "(self.catalog_length,1)"
            ),
        )
        check_method(
            "expand_catalog",
            check_ndarray_shape(
                lambda self: (self.catalog_length, self.num_coordinate),
                "(self.catalog_length,self.num_coordinate)",
            ),
        )

        return cls


class CatalogCategory(ABC, metaclass=_CatalogMetaClass):
    """
    The class that implement each of the subdictionnary for the general SINDy framework.

    Some variable are required :
        - catalog_length (int) : The total lenght of the output of the expanded catalog (should be infered without hard computation)
        - num_coordinate (int) : The number of coordinate of the system.

    """

    @abstractmethod
    def __init__(self, *args, **kwargs):
        """
        Initialisation of the Catalog class, each Catalog class can have a different base data on their init.
        """
        self.catalog_lenght = None
        self.num_coordinate = None
        super().__init__()

    ## Base method linked with other process (regression, output formatting )
    @abstractmethod
    def create_solution_vector(self, *args, **kwargs):
        """
        This method output the solution vector from any solution related data.

        Returns:
            np.ndarray: an array of shape (catalog_length,1) containing the coefficient that replicate the solution system.
        """

        pass

    @abstractmethod
    def expand_catalog(self):
        """
        This method expand the catalog in a (catalog_length,num_coordinate) matrix.

        Returns:
            np.ndarray: an array of shape (catalog_length,num_coordinate) containing all the function
        """

        pass

    @abstractmethod
    def label(self):
        """
        Return the label of the expanded catalog.
        """

        pass

    ## Additionnal (but not optionnal) method to manage catalog

    # maybe I should test the input thanks to the metaclass
    @abstractmethod
    def separate_by_mask(self, mask: np.ndarray) -> tuple:
        """
        Separate the catalog by a mask. The mask is a boolean array of shape (catalog_length,).

        Args:
            mask (np.ndarray): a boolean array of shape (catalog_length,) to separate the catalog.

        Returns:
            CatalogCategory: a new CatalogCategory with the masked data.
            CatalogCategory: a new CatalogCategory with the remaining data.
        """
        pass

    # actually separate_by mask can be used to do random reduction of the catalog and any reduction method, maybe only need to implement add and it will be the end.


class CatalogRepartition:
    """
    A class that manage the repartition of the catalog. It is used to create a global catalog from different part of the catalog.
    """

    def __init__(self, catalog_repartition: List[CatalogCategory]):
        """
        Initialisation of the CatalogRepartition class.

        Args:
            catalog_repartition (List[CatalogCategory]): a listing of the different part of the catalog used. list of catalog class.
        """
        self.catalog_repartition = catalog_repartition

        self.catalog_length = sum(
            catalog.catalog_length for catalog in self.catalog_repartition
        )

    def expand_catalog(self):
        """
        create a global catalog for the regression system

        Returns:
            np.ndarray: a global catalog of shape (catalog_length,num_coordinate) containing all the function
        """
        res = []

        for catalog in self.catalog_repartition:
            res += [catalog.expand_catalog()]

        return np.concatenate(res, axis=0)

    def create_solution_vector(
        self,
        solution_data: List[tuple],
    ) -> np.ndarray:
        """
        Create an unique solution vector from the catalog and the solution data.
        Args:
            solution_data (List[tuple]): the solution data composed of the different information to build the solution vector, each one dependend of the paradigm used [(Lagrangian,substitution),...,(coeff_matrix, binary_matrix)]

        Returns:
            np.ndarray: the solution vector
        """

        solution = []

        for catalog, data in zip(self.catalog_repartition, solution_data):
            solution += [catalog.create_solution_vector(*data)]

        return np.concatenate(solution, axis=0)

    def label(self):
        """
        Returns:
            List[str]: List of labels for the catalog.
        """

        label_list = [catalog.label() for catalog in self.catalog_repartition]

        ret = []
        for sublist in label_list:
            ret += sublist

        return ret

    def separate_by_mask(self, mask: np.ndarray) -> Tuple[Self, Self]:
        """
        Separate the catalog by a mask. The mask is a boolean array of shape (catalog_length,).

        Args:
            mask (np.ndarray): a boolean array of shape (catalog_length,) to separate the catalog.

        Returns:
            tuple: two CatalogRepartition with the masked data and the remaining data.
        """
        masked_catalogs = []
        remaining_catalogs = []

        remainer = 0

        for catalog in self.catalog_repartition:
            masked, remaining = catalog.separate_by_mask(
                mask[remainer : remainer + catalog.catalog_length]
            )
            masked_catalogs.append(masked)
            remaining_catalogs.append(remaining)

            remainer += catalog.catalog_length

        return CatalogRepartition(masked_catalogs), CatalogRepartition(
            remaining_catalogs
        )

    def seperate_by_type(self, type_mask: List[str]) -> Tuple[Self, Self]:
        """
        Separate the catalog by type. The type is a list of string that match the label of the catalog. the type is the name of the class.

        Args:
            type_mask (List[str]): a list of string that match the label of the catalog.

        Returns:
            tuple: two CatalogRepartition with the masked data and the remaining data.
        """
        masked_catalogs = []
        remaining_catalogs = []

        for catalog in self.catalog_repartition:
            if type(catalog).__name__ in type_mask:
                masked_catalogs.append(catalog)
            else:
                remaining_catalogs.append(catalog)

        return CatalogRepartition(masked_catalogs), CatalogRepartition(
            remaining_catalogs
        )
    
    def starting_index_by_type(self, type_mask: str) -> int:
        """
        Return the starting index of each catalog of a given type in the global catalog.

        Args:
            type_mask (List[str]): a list of string that match the label of the catalog.
        Returns:
            List[int]: a list of starting index of each catalog of the given type in the global catalog.
        """
        indices = []
        current_index = 0

        for catalog in self.catalog_repartition:
            if type(catalog).__name__ == type_mask:
                indices.append(current_index)
            current_index += catalog.catalog_length

        if len(indices) >1:
            raise ValueError(f"More than one catalog of type {type_mask} found in the catalog repartition. Ambiguous starting index.")
        if len(indices) == 0:
            raise ValueError(f"No catalog of type {type_mask} found in the catalog repartition.")

        return indices[0]

    def separate_solution_by_type(
        self, solution: np.ndarray, type_mask: List[str]
    ) -> tuple:
        """
        Separate the the solution vector by type. The type is a list of string that match the label of the catalog. the type is the name of the class.

        Args:
            solution (np.ndarray): the solution vector to be separated.
            type_mask (List[str]): a list of string that match the label of the catalog.

        Returns:
            tuple: two CatalogRepartition with the masked data and the remaining data.
        """
        masked_solution = []
        remaining_solution = []

        start_index = 0

        for catalog in self.catalog_repartition:
            if type(catalog).__name__ in type_mask:
                masked_solution.append(
                    solution[start_index : start_index + catalog.catalog_lenght]
                )

                start_index += catalog.catalog_lenght
            else:
                remaining_solution.append(catalog)

        return np.concatenate(masked_solution, axis=0), np.concatenate(
            remaining_solution, axis=0
        )

    def reunite_solution_by_type(
        self,
        type_mask: List[str],
        masked_solution: np.ndarray,
        remaining_solution: np.ndarray,
    ):
        """
        Reunite the solution vector by type. The type is a list of string that match the label of the catalog. the type is the name of the class.

        Args:
            type_mask (List[str]): a list of string that match the label of the catalog.
            masked_solution (np.ndarray): the masked solution vector to be reunited.
            remaining_solution (np.ndarray): the remaining solution vector to be reunited.

        Returns:
            np.ndarray: the reunited solution vector.
        """
        start_index_m = 0
        start_index_r = 0
        result = []

        for catalog in self.catalog_repartition:
            if type(catalog).__name__ in type_mask:
                result.append(
                    masked_solution[
                        start_index_m : start_index_m + catalog.catalog_lenght
                    ]
                )
                start_index_m += catalog.catalog_lenght
            else:
                result.append(
                    remaining_solution[
                        start_index_r : start_index_r + catalog.catalog_lenght
                    ]
                )
                start_index_r += catalog.catalog_lenght

        return np.concatenate(result, axis=0)
