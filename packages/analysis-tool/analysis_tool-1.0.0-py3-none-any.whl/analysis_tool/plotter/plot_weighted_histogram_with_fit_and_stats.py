'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-10-18 06:14:22 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-02-27 03:36:44 +0100
FilePath     : plot_weighted_histogram_with_fit_and_stats.py
Description  : A tool for creating weighted histograms with statistical analysis and curve fitting

Copyright (c) 2024 by everyone, All Rights Reserved. 
'''

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Literal, Optional, Tuple, Union, cast

import colorama
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from iminuit import Minuit
from rich import print as rprint
from rich.logging import RichHandler
from scipy.stats import expon, norm

# Configure rich logging globally
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%x %X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)  # or "DEBUG"/"WARNING" as needed
logger = logging.getLogger(__name__)

# Type aliases for better readability
ArrayFloat = npt.NDArray[np.float64]
FitType = Literal["gauss", "exponential"]
PlotType = Literal["hist", "errorbar"]
StatsDict = Dict[str, float]
FitParamsDict = Dict[str, Any]


def compute_bin_uncertainties(
    data: ArrayFloat,
    weights: ArrayFloat,
    bin_edges: ArrayFloat,
) -> Tuple[ArrayFloat, ArrayFloat]:
    """
    Computes the bin centers and uncertainties for a weighted histogram.

    Parameters:
        data: Array of data points
        weights: Array of weights corresponding to each data point
        bin_edges: Bin edges of the histogram

    Returns:
        Tuple containing bin centers and their corresponding uncertainties
    """
    # Compute weighted counts per bin and sum of squared weights per bin
    sum_w, _ = np.histogram(data, bins=bin_edges, weights=weights)
    sum_w2, _ = np.histogram(data, bins=bin_edges, weights=weights**2)

    # Calculate uncertainties
    uncertainties = np.sqrt(sum_w2)

    # Compute bin centers
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    return bin_centers, uncertainties


def compute_statistics(data: ArrayFloat, weights: ArrayFloat) -> StatsDict:
    """
    Computes statistical metrics: weighted_sum, mean, and standard deviation.

    Parameters:
        data: Array of data points
        weights: Array of weights corresponding to each data point

    Returns:
        Dictionary containing 'weighted_sum', 'mean', and 'std_dev'
    """
    if len(data) != len(weights):
        raise ValueError(f"{colorama.Fore.RED}data and weights must be of the same length.{colorama.Style.RESET_ALL}")

    if np.any(weights < 0):
        logger.warning(f"{colorama.Fore.YELLOW}Some weights are negative.{colorama.Style.RESET_ALL}")

    weighted_sum = np.sum(weights)
    if weighted_sum == 0:
        raise ValueError(f"{colorama.Fore.RED}Sum of weights (weighted_sum) is zero. Cannot compute statistics.{colorama.Style.RESET_ALL}")

    mean = np.average(data, weights=weights)
    variance = np.average((data - mean) ** 2, weights=weights)
    std_dev = np.sqrt(variance)

    return {'weighted_sum': weighted_sum, 'mean': mean, 'std_dev': std_dev}


def gaussian_nll(mu: float, sigma: float, data: ArrayFloat, weights: ArrayFloat) -> float:
    """
    Negative Log-Likelihood function for Gaussian distribution with normalized weights.

    Parameters:
        mu: Mean of the Gaussian
        sigma: Standard deviation of the Gaussian
        data: Array of data points
        weights: Array of weights corresponding to each data point

    Returns:
        Negative log-likelihood value
    """
    if sigma <= 0:
        return np.inf

    pdf_vals = norm.pdf(data, loc=mu, scale=sigma)
    # Prevent log(0) by setting a lower bound
    pdf_vals = np.maximum(pdf_vals, 1e-300)

    # Normalize the weights to preserve the Effective Sample Size (ESS)
    sum_w = np.sum(weights)
    sum_w2 = np.sum(weights**2)
    normalized_weights = weights * sum_w / sum_w2

    # Calculate the Negative Log-Likelihood
    return -np.sum(normalized_weights * np.log(pdf_vals))


def exponential_nll(lambd: float, data: ArrayFloat, weights: ArrayFloat) -> float:
    """
    Negative Log-Likelihood function for Exponential distribution with normalized weights.

    Parameters:
        lambd: Rate parameter of the Exponential distribution
        data: Array of data points
        weights: Array of weights corresponding to each data point

    Returns:
        Negative log-likelihood value
    """
    if lambd <= 0:
        return np.inf

    pdf_vals = expon.pdf(data, scale=1 / lambd)
    # Prevent log(0) by setting a lower bound
    pdf_vals = np.maximum(pdf_vals, 1e-300)

    # Normalize the weights to preserve the Effective Sample Size (ESS)
    sum_w = np.sum(weights)
    sum_w2 = np.sum(weights**2)
    normalized_weights = weights * sum_w / sum_w2

    # Calculate the Negative Log-Likelihood
    return -np.sum(normalized_weights * np.log(pdf_vals))


def perform_fit(data: ArrayFloat, weights: ArrayFloat, fit_type: FitType) -> Optional[FitParamsDict]:
    """
    Performs an un-binned maximum likelihood fit to the data using iMinuit.

    Parameters:
        data: Array of data points
        weights: Array of weights corresponding to each data point
        fit_type: Type of fit to perform ('gauss' or 'exponential')

    Returns:
        Dictionary of fit parameters and their uncertainties if fit is successful, else None
    """
    fit_type = fit_type.lower()

    if fit_type == 'gauss':
        # Define the NLL function with fixed data and weights
        def nll(mu: float, sigma: float) -> float:
            return gaussian_nll(mu, sigma, data, weights)

        # Initial guesses
        initial_mu = np.average(data, weights=weights)
        initial_sigma = np.sqrt(np.average((data - initial_mu) ** 2, weights=weights))

        # Initialize Minuit
        m = Minuit(nll, mu=initial_mu, sigma=initial_sigma)
        m.limits['mu'] = (np.min(data), np.max(data))  # mu can vary within the data range
        m.limits['sigma'] = (1e-6, None)  # sigma > 0
        m.errordef = Minuit.LIKELIHOOD  # Required for NLL

        m.strategy = 2
        m.migrad()
        m.hesse()
        logger.info(m)

        if m.valid:
            fit_params: FitParamsDict = {
                'type': 'Gaussian',
                'mu': m.values['mu'],
                'mu_err': m.errors['mu'],
                'sigma': m.values['sigma'],
                'sigma_err': m.errors['sigma'],
            }
            return fit_params
        else:
            logger.warning(f'{colorama.Fore.YELLOW}Gaussian fit did not converge.{colorama.Style.RESET_ALL}')
            return None

    elif fit_type == 'exponential':
        # Define the NLL function with fixed data and weights
        def nll(lambd: float) -> float:
            return exponential_nll(lambd, data, weights)

        # Initial guess
        mean_val = np.average(data, weights=weights)
        initial_lambd = 1.0 / mean_val if mean_val > 0 else 1.0

        # Initialize Minuit
        m = Minuit(nll, lambd=initial_lambd)
        m.limits['lambd'] = (1e-6, None)  # lambd > 0
        m.errordef = Minuit.LIKELIHOOD  # Required for NLL

        # Suppress warnings for better control
        # with warnings.catch_warnings():
        #     warnings.simplefilter("ignore")

        m.strategy = 2
        m.migrad()
        m.hesse()
        logger.info(m)

        if m.valid:
            fit_params: FitParamsDict = {
                'type': 'Exponential',
                'lambda': m.values['lambd'],
                'lambda_err': m.errors['lambd'],
            }
            return fit_params
        else:
            logger.warning(f'{colorama.Fore.YELLOW}Exponential fit did not converge.{colorama.Style.RESET_ALL}')
            return None

    else:
        raise ValueError(f"{colorama.Fore.RED}Fit type '{fit_type}' is not supported.{colorama.Style.RESET_ALL}")


def plot_histogram(
    data: ArrayFloat,
    weights: ArrayFloat,
    ax: plt.Axes,
    plot_type: PlotType = 'hist',
    num_bins: Optional[int] = None,
    normalize: bool = False,
) -> Tuple[ArrayFloat, ArrayFloat, ArrayFloat, ArrayFloat]:
    """
    Plots a weighted histogram or errorbar plot with error bars on the provided Axes.

    Parameters:
        data: Array of data points
        weights: Array of weights corresponding to each data point
        ax: Matplotlib Axes object to plot on
        plot_type: Type of plot ('hist' for histogram, 'errorbar' for data points with error bars)
        num_bins: Number of bins for the histogram. If None, defaults to 30
        normalize: If True, normalize the histogram so that the total area equals one

    Returns:
        Tuple containing:
        - counts: Weighted counts per bin (normalized if specified)
        - bins: Bin edges
        - bin_centers: Centers of each bin
        - uncertainties: Uncertainties for each bin (normalized if specified)
    """
    if plot_type not in ['hist', 'errorbar']:
        raise ValueError(f"{colorama.Fore.RED}Invalid plot_type. Choose 'hist' or 'errorbar'.{colorama.Style.RESET_ALL}")

    # Compute bin edges manually using NumPy
    bin_edges = np.histogram_bin_edges(data, bins=num_bins or 30)

    # Compute weighted counts per bin
    counts, bin_edges = np.histogram(data, bins=bin_edges, weights=weights)

    # Compute bin centers and uncertainties using the helper function
    bin_centers, uncertainties = compute_bin_uncertainties(data, weights, bin_edges)

    # Normalize if requested
    if normalize:
        bin_width = bin_edges[1] - bin_edges[0]
        area = np.sum(counts * bin_width)
        if area == 0:
            raise ValueError(f"{colorama.Fore.RED}Total area of the histogram is zero. Cannot normalize.{colorama.Style.RESET_ALL}")
        counts = counts / area
        uncertainties = uncertainties / area
        # y_label = 'p.d.f.'  # Probability Density Function
    # else:
    # y_label = 'Entries' if np.all(weight_np == 1) else 'Weighted Entries'

    if plot_type == 'hist':
        # Plot histogram as bars
        ax.bar(bin_centers, counts, width=(bin_edges[1] - bin_edges[0]), color='skyblue', edgecolor='black', alpha=0.6, label='Data')
    else:  # plot_type == 'errorbar'
        # Plot data points with error bars
        ax.errorbar(bin_centers, counts, yerr=uncertainties, fmt='o', color='blue', ecolor='black', capsize=3, label='Data')

    return counts, bin_edges, bin_centers, uncertainties


def add_statistics_text(
    ax: plt.Axes,
    stats: StatsDict,
    fit_info: Optional[FitParamsDict] = None,
) -> None:
    """
    Adds a textbox to the plot displaying statistical information and fit results.

    Parameters:
        ax: Matplotlib Axes object to add text to
        stats: Dictionary containing 'weighted_sum', 'mean', and 'std_dev'
        fit_info: Dictionary containing fit parameters and their uncertainties
    """
    label_lines = [f"Weighted Sum: {stats['weighted_sum']:.2f}", f"Mean: {stats['mean']:.2f}", f"Std Dev: {stats['std_dev']:.2f}"]

    if fit_info:
        if fit_info['type'] == 'Gaussian':
            label_lines.extend([f"Fit: Gaussian", f"μ = {fit_info['mu']:.2f} ± {fit_info['mu_err']:.2f}", f"σ = {fit_info['sigma']:.2f} ± {fit_info['sigma_err']:.2f}"])
        elif fit_info['type'] == 'Exponential':
            label_lines.extend([f"Fit: Exponential", f"λ = {fit_info['lambda']:.2f} ± {fit_info['lambda_err']:.2f}"])

    label_text = "\n".join(label_lines)

    # Add textbox in the upper right corner
    ax.text(0.95, 0.95, label_text, verticalalignment='top', horizontalalignment='right', transform=ax.transAxes, fontsize=12, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))


def add_fit_curve(ax: plt.Axes, fit_params: FitParamsDict, bins: ArrayFloat, weighted_sum: float, normalize: bool) -> None:
    """
    Adds the fitted curve to the histogram or errorbar plot.

    Parameters:
        ax: Matplotlib Axes object to plot on
        fit_params: Dictionary containing fit parameters
        bins: Bin edges of the histogram
        weighted_sum: Total sum of weights
        normalize: Indicates whether the plot is normalized
    """
    bin_width = bins[1] - bins[0]
    x_fit = np.linspace(bins[0], bins[-1], 1000)

    if fit_params['type'] == 'Gaussian':
        y_fit = norm.pdf(x_fit, loc=fit_params['mu'], scale=fit_params['sigma'])
        if not normalize:
            y_fit *= weighted_sum * bin_width  # Scale to match weighted sum
        # No scaling needed if normalize=True
        ax.plot(x_fit, y_fit, 'r--', label='Gauss Fit')

    elif fit_params['type'] == 'Exponential':
        y_fit = expon.pdf(x_fit, scale=1 / fit_params['lambda'])
        if not normalize:
            y_fit *= weighted_sum * bin_width  # Scale to match weighted sum
        # No scaling needed if normalize=True
        ax.plot(x_fit, y_fit, 'r--', label='Exp. Fit')


def plot_weighted_histogram_with_fit_and_stats(
    var_np: ArrayFloat,
    output_plot_path: str,
    weight_np: Optional[Union[ArrayFloat, str]] = None,
    x_title: Optional[str] = None,
    fit_function_type: Optional[FitType] = None,
    num_bins: Optional[int] = None,
    plot_type: PlotType = 'errorbar',
    normalize: bool = False,
    plot_title: Optional[str] = None,
    x_range: Optional[Tuple[Optional[float], Optional[float]]] = None,
) -> Tuple[StatsDict, Optional[FitParamsDict]]:
    """
    Plots a weighted histogram or errorbar plot, displays statistical information,
    optionally fits the data to an exponential or Gaussian distribution using iMinuit,
    overlays the fit curve, and saves the plot.

    Parameters:
        var_np: Array of data points
        output_plot_path: File path to save the output plot image
        weight_np: Array of weights corresponding to each data point
        x_title: Label for the x-axis
        fit_function_type: Type of fit to perform ('exponential' or 'gauss')
                          If None or invalid, no fit is performed
        num_bins: Number of bins for the histogram. If None, defaults to 30
        plot_type: Type of plot ('hist' for histogram, 'errorbar' for data points with error bars)
        normalize: If True, normalize the histogram so that the total area equals one
        plot_title: Title for the plot. Defaults to 'Statistical Results'
        x_range: Tuple specifying the (min, max) range to analyze
                If None, uses the full data range

    Returns:
        Tuple containing:
        - stats: Dictionary with 'weighted_sum', 'mean', and 'std_dev'
        - fit_info: Dictionary with fit parameters and uncertainties if fit is performed, else None
    """
    # Validate and prepare weights
    if (weight_np is None) or (isinstance(weight_np, str) and weight_np.upper() == 'NONE'):
        weight_np = np.ones_like(var_np)

    # Cast to ensure type checking works
    weight_np_array = cast(ArrayFloat, weight_np)

    if len(var_np) != len(weight_np_array):
        raise ValueError(f"{colorama.Fore.RED}var_np and weight_np must be of the same length.{colorama.Style.RESET_ALL}")

    # Apply x_range filtering if specified
    if x_range is not None:
        if not (isinstance(x_range, (tuple, list)) and len(x_range) == 2):
            raise ValueError(f"{colorama.Fore.RED}x_range must be a tuple or list with two elements (min, max).{colorama.Style.RESET_ALL}")

        lower_bound, upper_bound = x_range
        # Create a boolean mask for the specified range
        mask_lower_bound = var_np >= lower_bound if lower_bound is not None else np.ones_like(var_np, dtype=bool)
        mask_upper_bound = var_np <= upper_bound if upper_bound is not None else np.ones_like(var_np, dtype=bool)

        mask = mask_lower_bound & mask_upper_bound
        # Filter the data
        data_filtered = var_np[mask]
        weights_filtered = weight_np_array[mask]

        # Log the filtering information
        range_info = []
        if lower_bound is not None:
            range_info.append(f"(x >= {lower_bound})")
        if upper_bound is not None:
            range_info.append(f"(x <= {upper_bound})")

        logger.info(f"Data filtered for x_range: {' '.join(range_info)}")
    else:
        data_filtered = var_np
        weights_filtered = weight_np_array

    # Compute statistics
    stats = compute_statistics(data_filtered, weights_filtered)

    # Initialize plot
    fig, ax = plt.subplots(figsize=(0.8 * 10, 0.8 * 7))

    # Plot histogram or scatter and get bin centers and uncertainties
    counts, bins, bin_centers, uncertainties = plot_histogram(data_filtered, weights_filtered, ax, plot_type=plot_type, num_bins=num_bins, normalize=normalize)

    # Apply x_range limits to the plot if specified
    if x_range is not None:
        lower_bound, upper_bound = x_range
        if lower_bound is not None:
            ax.set_xlim(left=lower_bound)
        if upper_bound is not None:
            ax.set_xlim(right=upper_bound)

    # Initialize fit info
    fit_info = None

    # Perform fit if requested
    if fit_function_type and fit_function_type.lower() in ['gauss', 'exponential']:
        fit_params = perform_fit(data_filtered, weights_filtered, fit_function_type)
        if fit_params:
            fit_info = fit_params
            add_fit_curve(ax, fit_params, bins, stats['weighted_sum'], normalize)

    # Update the legend to include the fit curve without duplicating entries
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(list(reversed(by_label.values())), list(reversed(by_label.keys())), loc='upper left')
    # ax.legend()

    # Add statistical information text
    add_statistics_text(ax, stats, fit_info)

    # Set plot labels and title
    if x_title:
        ax.set_xlabel(x_title, fontsize=14)

    y_label = 'p.d.f' if normalize else 'Entries'
    ax.set_ylabel(y_label, fontsize=14)

    if plot_title:
        ax.set_title(plot_title, fontsize=16)

    # Improve layout
    plt.tight_layout()

    # Save the plot
    output_path = Path(output_plot_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    logger.info(f"Plot saved to {output_path}")
    plt.close()

    # Return stats and fit_info
    return stats, fit_info


if __name__ == '__main__':
    # Example 1: Gaussian data with histogram plot
    if True:
        # Example data generation for Histogram Plot
        np.random.seed(42)  # For reproducibility
        data_hist = np.random.normal(loc=5, scale=2, size=1000)
        weights_hist = np.random.uniform(0.5, 1.5, size=1000)  # Random weights

        # Define parameters for Histogram Plot
        x_axis_title_hist = "Measurement Values"
        fit_function_type = "gauss"  # Options: 'gauss', 'exponential', or None for no fit
        output_path_hist = "statistical_plot_hist.png"

        # Call the function for Histogram Plot with Normalization
        stats_hist, fit_info_hist = plot_weighted_histogram_with_fit_and_stats(
            var_np=data_hist,
            weight_np=weights_hist,
            x_title=x_axis_title_hist,
            fit_function_type=fit_function_type,
            output_plot_path=output_path_hist,
            num_bins=30,  # Optional: specify number of bins
            plot_type='errorbar',  # Plot as histogram
            normalize=False,  # Enable normalization
            plot_title='Statistical Results',  # Optional: specify plot title
            x_range=(2, 12),  # Optional: specify x-axis range
        )

        logger.info(f"Histogram Plot saved to {output_path_hist}")
        logger.info(f"Statistics: {stats_hist}")
        logger.info(f"Fit Information: {fit_info_hist}")

    # Example 2: Exponential data with errorbar plot
    if True:
        # Example data generation for Scatter Plot
        np.random.seed(24)  # For reproducibility
        data_scatter = np.random.exponential(scale=2, size=1000)
        weights_scatter = np.random.uniform(0.5, 1.5, size=1000)  # Random weights

        # Define parameters for Scatter Plot
        x_axis_title_scatter = "Measurement Values"
        fit_type_scatter = "exponential"  # Options: 'gauss', 'exponential', or None for no fit
        output_path_scatter = "statistical_plot_scatter.png"

        # Call the function for Scatter Plot without Normalization
        stats_scatter, fit_info_scatter = plot_weighted_histogram_with_fit_and_stats(
            var_np=data_scatter,
            weight_np=weights_scatter,
            x_title=x_axis_title_scatter,
            fit_function_type=fit_type_scatter,
            output_plot_path=output_path_scatter,
            num_bins=30,  # Optional: specify number of bins
            plot_type='errorbar',  # Plot as data points with error bars
            plot_title='Statistical Results',  # Optional: specify plot title
            normalize=True,  # Enable normalization
        )

        logger.info(f"Scatter Plot saved to {output_path_scatter}")
        logger.info(f"Statistics: {stats_scatter}")
        logger.info(f"Fit Information: {fit_info_scatter}")
