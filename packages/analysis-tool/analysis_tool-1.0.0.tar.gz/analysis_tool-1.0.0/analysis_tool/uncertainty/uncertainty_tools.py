'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-02-18 14:42:19 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-06-25 05:59:29 +0200
FilePath     : uncertainty_tools.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

from collections.abc import Mapping
from typing import Dict, List, Union, Optional, Any, Set, Sequence, TypeVar, cast
import numpy as np
from numpy.typing import NDArray

import uncertainties as unc
from uncertainties import unumpy as unp
from uncertainties import ufloat, umath, UFloat

from ROOT import RDataFrame
from rich import print as rprint

from ..utils.utils_dict import update_config


def add_correlation_to_uncVars(
    uncVarList: Sequence[UFloat],
    corrMatrix: Sequence[Sequence[float]],
    *,
    check_symmetry: bool = True,
    atol: float = 1e-12,
) -> list[UFloat]:
    """
    Return a new set of ``UFloat`` objects whose covariance structure follows
    the provided correlation matrix.

    Parameters
    ----------
    uncVarList : Sequence[UFloat]
        Input uncertainty variables.  Their nominal values and individual
        standard deviations are kept, only their *mutual* correlations are
        modified.
    corrMatrix : Sequence[Sequence[float]]
        Square correlation matrix (ρᵢⱼ) with dimension
        ``len(uncVarList)`` x ``len(uncVarList)``.
    check_symmetry : bool, default ``True``
        Validate that the matrix is symmetric with ones on the diagonal.
    atol : float, default ``1e-12``
        Absolute tolerance for the validation checks.

    Raises
    ------
    ValueError
        If the matrix shape is wrong, not symmetric, diagonal not unity or
        coefficients fall outside the \[-1, 1\] range.
    """
    n = len(uncVarList)
    corr: NDArray[np.float64] = np.asarray(corrMatrix, dtype=np.float64)

    if corr.shape != (n, n):
        raise ValueError(f"Correlation matrix shape {corr.shape} does not match number of variables ({n}).")

    if check_symmetry:
        if not np.allclose(corr, corr.T, atol=atol):
            raise ValueError(f"Correlation matrix must be symmetric, but got {corr}.")
        if not np.allclose(np.diag(corr), np.ones(n), atol=atol):
            raise ValueError(f"Correlation matrix must have ones on its diagonal, but got {np.diag(corr)}.")

    if np.any(np.abs(corr) - 1 > atol):
        raise ValueError(f"Correlation coefficients must lie within [-1, 1], but got {corr}.")

    value_with_std_dev = [(u.n, u.s) for u in uncVarList]
    return list(unc.correlated_values_norm(value_with_std_dev, corr))


def std_to_unc(d: Dict[str, float], keyValue: str = "Value", keyError: str = "Error") -> UFloat:
    """Convert standard value and error in dictionary to UFloat.

    Args:
        d: Dictionary containing value and error
        keyValue: Key for the value in dictionary
        keyError: Key for the error in dictionary

    Returns:
        UFloat object with value and uncertainty
    """
    return unc.ufloat(d[keyValue], d[keyError])


def unc_to_std(d: UFloat, keyValue: str = "Value", keyError: str = "Error") -> Dict[str, float]:
    """Convert UFloat to standard dictionary with value and error.

    Args:
        d: UFloat object to convert
        keyValue: Key for the value in output dictionary
        keyError: Key for the error in output dictionary

    Returns:
        Dictionary with value and error
    """
    return {keyValue: d.n, keyError: d.s}


def dict_from_unc_to_normal(input_dict: Dict[str, Any], keyValue: str = "Value", keyError: str = "Error") -> Dict[str, Any]:
    """Recursively convert UFloat values in a dictionary to standard value/error format.

    See
    http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    for details.

    Args:
        input_dict: Dictionary potentially containing UFloat values
        keyValue: Key for value in output dictionaries
        keyError: Key for error in output dictionaries

    Returns:
        Dictionary with UFloat values converted to standard format
    """

    def _update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in u.items():
            if isinstance(value, Mapping):
                d[key] = _update(d.get(key, {}), value)
            elif isinstance(value, unc.UFloat):
                d[key] = {keyValue: value.n, keyError: value.s}
            else:
                d[key] = value
        return d

    output_dict: Dict[str, Any] = {}
    _update(output_dict, input_dict)

    return output_dict


def dict_from_normal_to_unc(input_dict: Dict[str, Any], keyValue: str = "Value", keyError: str = "Error") -> Dict[str, Any]:
    """Recursively convert standard value/error pairs in a dictionary to UFloat format.

    See
    http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    for details.

    Args:
        input_dict: Dictionary potentially containing value/error pairs
        keyValue: Key for value in input dictionaries
        keyError: Key for error in input dictionaries

    Returns:
        Dictionary with value/error pairs converted to UFloat objects
    """

    def _update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in u.items():
            if isinstance(value, Mapping):
                d[key] = _update(d.get(key, {}), value)

                # Convert value/error pairs to UFloat objects
                if isinstance(value.get(keyValue), float) and isinstance(value.get(keyError), float):
                    d[key] = ufloat(value[keyValue], value[keyError])
            else:
                d[key] = value
        return d

    output_dict: Dict[str, Any] = {}
    _update(output_dict, input_dict)

    return output_dict


def get_weighted_ufloat_from_rdf(rdf: RDataFrame, weight_name: str) -> UFloat:
    """Calculate weighted sum with uncertainty from a ROOT RDataFrame.

    Args:
        rdf: ROOT RDataFrame containing data
        weight_name: Column name to use as weight. Use "1" for unweighted count.

    Returns:
        UFloat containing weighted sum and its uncertainty
    """
    # For unweighted counts, use Poisson uncertainty (sqrt(N))
    if weight_name == "1":
        return ufloat(rdf.Count().GetValue(), umath.sqrt(rdf.Count().GetValue()))

    # Define squared weights column if not already present
    rdf = rdf.Define("_sumw2", f"{weight_name}*{weight_name}") if "_sumw2" not in rdf.GetColumnNames() else rdf

    # Calculate weighted sum
    value = rdf.Sum(weight_name).GetValue()

    # Calculate uncertainty using sum of squared weights
    error = umath.sqrt(rdf.Sum("_sumw2").GetValue()) if rdf.Count().GetValue() != 0 else 0

    return ufloat(value, error)


class ValErrPropagator:
    """
    Error propagation and uncertainty management for computational analyses.

    This class handles operations with values and their uncertainties, supporting
    arithmetic operations while properly tracking error correlations. It maintains
    both basic representations (nominal values and errors) and uncertainty-aware
    representations using the `uncertainties` package.

    Attributes:
        input (Dict[str, Any]): Input data with keys for error categories
        name (str): Name identifier for this measurement
        key_value (str): Dictionary key for central/nominal value
        initialisation_method (str): Method for initializing error categories ('basic' or 'unc')
        data (Dict[str, Any]): Main data structure with processed information
        error_categories (List[str]): List of uncertainty categories
        basic_folder (Dict[str, float]): Standard deviations for each error category
        unc_folder (Dict[str, UFloat]): UFloat objects for each error category
    """

    def __init__(
        self,
        input: Dict[str, Any],
        name: str = "ValErrPropagator",
        key_value: str = "value",
        initialisation_method: str = "basic",
    ):
        """Initialize a new ValErrPropagator instance.

        Args:
            input: Dictionary with nominal value and uncertainty components
            name: Identifier name for this measurement
            key_value: Key in input dict for nominal value
            initialisation_method: Format of input ('basic' or 'unc')
        """
        self.input = input
        self.name = name
        self.key_value = key_value
        self.initialisation_method = initialisation_method

        # Validate input
        assert isinstance(self.input, dict), "input should be a dictionary"
        assert key_value in self.input, f"{key_value} is missing in the input"

        # Define folder names for organization
        self.basic_folder_name: str = "basic"  # For standard deviation values
        self.unc_folder_name: str = "unc"  # For UFloat uncertainty objects

        # Keys that aren't error categories
        self.nuisance_parameters: List[str] = [self.name, self.key_value]

        # Will store original error categories from input
        self.input_error_categories: Optional[List[str]] = None

        # Initialize data structure
        self.data: Dict[str, Any] = {}
        self.error_categories: List[str] = []
        self.basic_folder: Dict[str, float] = {}
        self.unc_folder: Dict[str, UFloat] = {}

        # Perform initialization
        self.initialisation()

    def update_error_categories_from_folder(self, source_folder_name: str) -> List[str]:
        """Extract error category names from a specified data folder.

        Args:
            source_folder_name: Folder name to extract categories from

        Returns:
            List of error category names
        """
        self.error_categories = [cat for cat in self.data[source_folder_name].keys() if cat not in self.nuisance_parameters]

        # Initialize input_error_categories if not already done
        if self.input_error_categories is None:
            self.input_error_categories = self.error_categories

        return self.error_categories

    def update_value_from_unc_folder(self) -> float:
        """Update central value from the first uncertainty variable.

        Returns:
            Updated nominal value
        """
        self.unc_folder = self.data[self.unc_folder_name]
        self.data[self.key_value] = self.unc_folder[self.error_categories[0]].nominal_value
        return self.data[self.key_value]

    # ! Be called each time after the operation
    def update_basic_folder_from_unc_folder(self) -> Dict[str, Any]:
        """Update standard deviations based on UFloat objects.

        This should be called after every operation to keep basic folder in sync.

        Returns:
            Updated data dictionary
        """
        # Initialize basic folder if needed
        if self.basic_folder_name not in self.data:
            self.data[self.basic_folder_name] = {}

        self.basic_folder = self.data[self.basic_folder_name]
        self.unc_folder = self.data[self.unc_folder_name]

        # Extract standard deviations from UFloat objects
        for cat in self.unc_folder:
            self.basic_folder[cat] = self.unc_folder[cat].std_dev

        # Update error categories list
        self.update_error_categories_from_folder(source_folder_name=self.basic_folder_name)
        return self.data

    # ! Only be used in the initialisation
    def update_unc_folder_from_basic_folder(self) -> Dict[str, UFloat]:
        """Create UFloat objects based on basic folder values.

        This should only be used during initialization.

        Returns:
            Dictionary of UFloat objects
        """
        # Initialize unc folder if needed
        if self.unc_folder_name not in self.data:
            self.data[self.unc_folder_name] = {}

        self.basic_folder = self.data[self.basic_folder_name]
        self.unc_folder = self.data[self.unc_folder_name]

        # Create UFloat objects for each error category
        for cat in self.basic_folder:
            if cat not in self.unc_folder:
                self.unc_folder[cat] = ufloat(self.data[self.key_value], self.basic_folder[cat])

        # Update error categories list
        self.update_error_categories_from_folder(source_folder_name=self.unc_folder_name)
        return self.unc_folder

    def initialisation(self) -> None:
        """Set up internal data structures based on input data.

        Handles two initialization methods:
        - 'basic': Input contains nominal value and standard deviations
        - 'unc': Input contains UFloat objects
        """
        # ! Only initialisation by using basic folder if the unc folder is not in the input
        if self.initialisation_method == "basic" and self.unc_folder_name not in self.input:
            # Initialize from basic error values
            self.data = (
                {self.key_value: self.input[self.key_value], self.basic_folder_name: {cat: self.input[cat] for cat in self.input if cat not in self.nuisance_parameters}}
                if self.basic_folder_name not in self.input
                else self.input
            )

            # Update error categories list
            self.update_error_categories_from_folder(source_folder_name=self.basic_folder_name)

            # Create UFloat objects
            self.update_unc_folder_from_basic_folder()
        else:
            # Initialize from UFloat objects
            assert self.unc_folder_name in self.input, f"{self.unc_folder_name} is missing in the input"

            self.data = {self.unc_folder_name: self.input[self.unc_folder_name]}

            # Update error categories list
            self.update_error_categories_from_folder(source_folder_name=self.unc_folder_name)

            # Extract standard deviations
            self.update_basic_folder_from_unc_folder()

            # Extract nominal value
            self.update_value_from_unc_folder()

        # Create shortcuts to commonly used folders
        self.basic_folder = self.data[self.basic_folder_name]
        self.unc_folder = self.data[self.unc_folder_name]

        # # Add uncertainties variables to each error category under the unc folder if not exist
        # self.data[self.unc_folder_name] = {} if self.unc_folder_name not in self.input.keys() else self.input[self.unc_folder_name]
        # self.unc_folder = self.data[self.unc_folder_name]

        # for cat in self.error_categories:
        #     self.unc_folder[cat] = ufloat(self.input[self.key_value], self.input[cat]) if cat not in self.unc_folder.keys() else self.unc_folder[cat]

    # Rewrite __repr__ method to print the result
    def __repr__(self) -> str:
        """String representation of the object.

        Returns:
            String showing name and data
        """
        return f"{self.name} = {self.data}"

    # Print the result
    def print_result(
        self,
        latex: bool = True,
        decimal: int = 4,
        unit_scale_factor: int = 1,
        verbose: bool = True,
    ) -> str:
        """Format and print measurement with uncertainties.

        Args:
            latex: Whether to format output for LaTeX
            decimal: Number of decimal places to show
            unit_scale_factor: Scale factor to divide values by
            verbose: Whether to print additional information

        Returns:
            Formatted string representation
        """
        result = f"{self.name} = "

        if latex:
            # Format for LaTeX output
            _val = self.data[self.key_value] * 1.0 / unit_scale_factor
            result += rf"{_val:.{decimal}f}"

            # Add each uncertainty component
            for cat in self.input_error_categories:
                _val = self.unc_folder[cat].s * 1.0 / unit_scale_factor
                result += rf" \pm {_val:.{decimal}f} ({cat})"

            # Add scale factor if used
            if unit_scale_factor != 1:
                result += rf" \times ({unit_scale_factor})"
        else:
            # Simple string representation
            result += str(self.data)

        rprint(result)

        # Show total uncertainty
        if verbose:
            _unc_array = np.array([self.unc_folder[cat] * 1.0 / unit_scale_factor for cat in self.input_error_categories])
            quadrature_sum_of_unc = _unc_array.sum().std_dev
            rprint(rf"{self.name} = {self.data[self.key_value] * 1.0 / unit_scale_factor:.{decimal}f} \pm {quadrature_sum_of_unc:.{decimal}f} (Quadrature sum of the uncertainties)")

        return result

    # Rewrite the __neg__ method
    def __neg__(self) -> 'ValErrPropagator':
        """Negate all values and uncertainties.

        Returns:
            New ValErrPropagator with negated values
        """
        # Create deep copy of data while preserving correlations
        new_result = update_config(self.data, self.data)
        new_result_unc_folder = new_result[self.unc_folder_name]

        # Negate each UFloat object
        for cat in self.error_categories:
            new_result_unc_folder[cat] = -new_result_unc_folder[cat]

        return ValErrPropagator(new_result, key_value=self.key_value)

    # Rewrite the __add__ method to add the uncertainties variables
    def __add__(self, other: Union[int, float, 'ValErrPropagator']) -> 'ValErrPropagator':
        """Add a scalar or another ValErrPropagator.

        Args:
            other: Value to add (number or ValErrPropagator)

        Returns:
            New ValErrPropagator with summed values
        """
        # Case 1: Adding a scalar
        if isinstance(other, (int, float)):
            # Deep copy data while preserving correlations
            new_result = update_config(self.data, self.data)
            new_result_unc_folder = new_result[self.unc_folder_name]

            # Add scalar to each UFloat
            for cat in self.error_categories:
                new_result_unc_folder[cat] = new_result_unc_folder[cat] + other

        # Case 2: Adding another ValErrPropagator
        elif isinstance(other, ValErrPropagator):
            # Ensure both objects have the same error categories
            self.check_error_categories_for_unc_variables(other.error_categories, add_missing=True, default_error=0.0)
            other.check_error_categories_for_unc_variables(self.error_categories, add_missing=True, default_error=0.0)

            # Deep copy data while preserving correlations
            new_result = update_config(self.data, self.data)
            new_result_unc_folder = new_result[self.unc_folder_name]

            # Sum corresponding UFloat objects
            for cat in self.error_categories:
                new_result_unc_folder[cat] = new_result_unc_folder[cat] + other.unc_folder[cat]
        else:
            return NotImplemented

        return ValErrPropagator(new_result, key_value=self.key_value)

    def __radd__(self, other: Union[int, float]) -> 'ValErrPropagator':
        """Support addition when ValErrPropagator is on right side.

        Args:
            other: Value to add

        Returns:
            New ValErrPropagator with summed values
        """
        return self.__add__(other)

    def __sub__(self, other: Union[int, float, 'ValErrPropagator']) -> 'ValErrPropagator':
        """Subtract a scalar or another ValErrPropagator.

        Args:
            other: Value to subtract

        Returns:
            New ValErrPropagator with difference
        """
        return self + (-other)

    # Rewrite the __mul__ method
    def __mul__(self, other: Union[int, float, 'ValErrPropagator']) -> 'ValErrPropagator':
        """Multiply by a scalar or another ValErrPropagator.

        Args:
            other: Value to multiply by

        Returns:
            New ValErrPropagator with product
        """
        # Case 1: Multiplying by a scalar
        if isinstance(other, (int, float)):
            # Deep copy data while preserving correlations
            new_result = update_config(self.data, self.data)
            new_result_unc_folder = new_result[self.unc_folder_name]

            # Multiply each UFloat by scalar
            for cat in self.error_categories:
                new_result_unc_folder[cat] = new_result_unc_folder[cat] * other

        # Case 2: Multiplying by another ValErrPropagator
        elif isinstance(other, ValErrPropagator):
            # Ensure both objects have the same error categories
            self.check_error_categories_for_unc_variables(other.error_categories, add_missing=True, default_error=0.0)
            other.check_error_categories_for_unc_variables(self.error_categories, add_missing=True, default_error=0.0)

            # Deep copy data while preserving correlations
            new_result = update_config(self.data, self.data)
            new_result_unc_folder = new_result[self.unc_folder_name]

            # Multiply corresponding UFloat objects
            for cat in self.error_categories:
                new_result_unc_folder[cat] = new_result_unc_folder[cat] * other.unc_folder[cat]
        else:
            return NotImplemented

        return ValErrPropagator(new_result, key_value=self.key_value)

    def __rmul__(self, other: Union[int, float]) -> 'ValErrPropagator':
        """Support multiplication when ValErrPropagator is on right side.

        Args:
            other: Value to multiply by

        Returns:
            New ValErrPropagator with product
        """
        return self.__mul__(other)

    def __truediv__(self, other: Union[int, float, 'ValErrPropagator']) -> 'ValErrPropagator':
        """Divide by a scalar or another ValErrPropagator.

        Args:
            other: Value to divide by

        Returns:
            New ValErrPropagator with quotient
        """
        # Case 1: Dividing by a scalar
        if isinstance(other, (int, float)):
            if other == 0:
                raise ValueError("Cannot divide by zero.")
            return self * (1 / other)

        # Case 2: Dividing by another ValErrPropagator
        elif isinstance(other, ValErrPropagator):
            # Ensure both objects have the same error categories
            self.check_error_categories_for_unc_variables(other.error_categories, add_missing=True, default_error=0.0)
            other.check_error_categories_for_unc_variables(self.error_categories, add_missing=True, default_error=0.0)

            # Deep copy data while preserving correlations
            new_result = update_config(self.data, self.data)
            new_result_unc_folder = new_result[self.unc_folder_name]

            # Divide corresponding UFloat objects
            for cat in self.error_categories:
                new_result_unc_folder[cat] = new_result_unc_folder[cat] / other.unc_folder[cat]
        else:
            return NotImplemented

        return ValErrPropagator(new_result, key_value=self.key_value)

    def __rtruediv__(self, other: Union[int, float]) -> 'ValErrPropagator':
        """Support division when ValErrPropagator is the denominator.

        Args:
            other: Numerator value

        Returns:
            New ValErrPropagator with quotient
        """
        if self.data[self.key_value] == 0:
            raise ZeroDivisionError("division by zero")

        if isinstance(other, (int, float)):
            # Create a ValErrPropagator for the numerator
            _instance_numerator = ValErrPropagator({"value": other})
            return _instance_numerator.__truediv__(self)
        else:
            return NotImplemented

    def check_error_categories_for_unc_variables(
        self,
        error_categories_to_check: Union[Set[str], List[str]],
        add_missing: bool = True,
        default_error: float = 0.0,
    ) -> 'ValErrPropagator':
        """Ensure all specified error categories exist in the object.

        Args:
            error_categories_to_check: Categories to verify or add
            add_missing: Whether to add missing categories
            default_error: Default error value for new categories

        Returns:
            Self (for method chaining)
        """
        # Add missing error categories if requested
        for cat in error_categories_to_check:
            if cat not in self.unc_folder and add_missing:
                # Create new UFloat with existing value but specified default error
                self.unc_folder[cat] = ufloat(self.data[self.key_value], default_error)

        # Update the error categories list
        self.update_error_categories_from_folder(source_folder_name=self.unc_folder_name)

        return self


def weighted_average(measurements: List[UFloat]) -> UFloat:
    """
    Calculate weighted average of measurements with uncertainties.

    This implements the standard weighted average formula using weights
    inversely proportional to the variance of each measurement.

    Args:
        measurements: List of measurements with uncertainties

    Returns:
        Combined measurement with appropriate uncertainty
    """
    # Extract nominal values and standard deviations
    x: NDArray[np.float_] = np.array([m.n for m in measurements])
    sigma: NDArray[np.float_] = np.array([m.s for m in measurements])

    # Check for zero uncertainties
    if np.any(sigma == 0):
        raise ValueError("One or more measurements have zero uncertainty.")

    # Calculate weights (inversely proportional to variance)
    weights: NDArray[np.float_] = 1 / sigma**2

    # Calculate weighted average
    x_combined: float = float(np.sum(weights * x) / np.sum(weights))

    # Calculate combined uncertainty
    sigma_combined: float = float(1 / np.sqrt(np.sum(weights)))

    # Return as UFloat
    return ufloat(x_combined, sigma_combined)


if __name__ == "__main__":
    # -----------------------
    # Usage examples
    # 1) ValErrPropagator
    val1_conf = {
        "value": 1,
        "stat": 0.1,
        "syst": 0.2,
        "syst1": 0.3,
    }
    val1 = ValErrPropagator(val1_conf, name="val1")

    val2 = 2

    val4_conf = {
        "value": 4,
        "stat": 0.4,
        "syst": 0.5,
        "syst2": 0.6,
    }
    val4 = ValErrPropagator(val4_conf, name="val4")

    rprint("\n\n\nExample of ValErrPropagator + ValErrPropagator")
    new_val = val1 + val4
    new_val.name = "new_val"
    rprint(new_val)
    new_val.print_result()

    # exit(1)
    rprint("\n val1 after the operation")
    rprint(val1)
    val1.print_result()

    rprint("\n val4 after the operation")
    rprint(val4)
    val4.print_result()

    # 2) weighted_average
    measurements = [
        ufloat(1.1, 0.1),
        ufloat(1.2, 0.2),
        ufloat(0.9, 0.3),
    ]

    combined_measurement = weighted_average(measurements)
    rprint("\n\n\nExample of weighted_average")
    rprint(f"Measurements: {measurements}")
    rprint(f"Combined measurement: {combined_measurement}")
