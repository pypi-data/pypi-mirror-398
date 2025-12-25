'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-05-22 03:54:18 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-05-22 04:01:17 +0200
FilePath     : utils_numpy.py
Description  :

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

import numpy as np
import hist
from rich import print as rprint
from rich.table import Table
from typing import Optional, Union, Tuple


def analyze_distribution(
    values: np.ndarray,
    weights: Optional[np.ndarray] = None,
    title: str = "Data Distribution",
    bins: int = 15,
    outlier_threshold: float = np.inf,
    verbose: bool = True,
) -> Tuple[hist.Hist, dict]:
    """
    Analyzes a distribution of values and creates a histogram visualization.

    Args:
        values: Array of values to analyze
        weights: Optional weights for each value (default: None)
        title: Title for the analysis output
        bins: Number of bins for histogram
        outlier_threshold: Threshold for warning about extreme values
        verbose: Whether to print the analysis (True) or just return the results (False)

    Returns:
        Tuple containing:
        - hist.Hist object with the histogram
        - Dictionary with summary statistics
    """
    # Input validation
    if values.size == 0:
        raise ValueError("Input array is empty")

    # Prepare weights if not provided
    if weights is None:
        weights = np.ones_like(values)
    elif weights.shape != values.shape:
        raise ValueError(f"Values shape {values.shape} doesn't match weights shape {weights.shape}")

    # Calculate summary statistics
    stats: dict = {
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "std": float(np.std(values)),
        "count": int(len(values)),
        "has_outliers": bool(abs(np.min(values)) > outlier_threshold or abs(np.max(values)) > outlier_threshold),
        "count_outliers": int(np.sum(abs(values) > outlier_threshold)),
    }

    # Create histogram
    histogram = hist.Hist(hist.axis.Regular(bins=bins, start=stats["min"], stop=stats["max"], name=title))
    histogram.fill(values, weight=weights)

    # Print analysis if verbose
    if verbose:
        _print_distribution_analysis(histogram, stats, title, outlier_threshold)

    return histogram, stats


def _print_distribution_analysis(histogram: hist.Hist, stats: dict, title: str, outlier_threshold: float) -> None:
    """
    Prints the distribution analysis in a formatted way.

    Args:
        histogram: The histogram to display
        stats: Dictionary with summary statistics
        title: Title for the output
        outlier_threshold: Threshold used for outlier warnings
    """
    separator = "-" * 50

    # Print header
    rprint(f"\n[bold]{title}[/bold]")
    rprint(separator)

    # Print statistics table
    stats_table = Table(show_header=False, box=None)
    stats_table.add_column("Statistic", style="cyan")
    stats_table.add_column("Value", style="green")

    stats_table.add_row("Count", f"{stats['count']:,}")
    stats_table.add_row("Min", f"{stats['min']:.4f}")
    stats_table.add_row("Max", f"{stats['max']:.4f}")
    stats_table.add_row("Mean", f"{stats['mean']:.4f}")
    stats_table.add_row("Median", f"{stats['median']:.4f}")
    stats_table.add_row("Std Dev", f"{stats['std']:.4f}")

    rprint(stats_table)

    # Print warnings if needed
    if stats["has_outliers"]:
        rprint(f"[bold yellow]Warning:[/bold yellow] Distribution contains {stats['count_outliers']} / {stats['count']} extreme values (>{outlier_threshold} or <-{outlier_threshold})")

    # Print histogram
    rprint("\n[bold]Histogram:[/bold]")
    rprint(histogram)
    rprint(separator, "\n")


if __name__ == "__main__":
    # Sample data for testing
    values = np.concatenate([np.random.normal(loc=5, scale=2, size=1000), np.random.normal(loc=15, scale=3, size=500)])

    weights = np.concatenate([np.random.normal(loc=1, scale=0.2, size=1000), np.random.normal(loc=1, scale=0.3, size=500)])

    # Run analysis with weighted values
    analyze_distribution(values=values, weights=weights, title="Sample Weight Distribution")

    # Run analysis with some extreme values
    extreme_values = np.concatenate([values, np.array([150, -200])])
    extreme_weights = np.concatenate([weights, np.array([1, 1])])

    analyze_distribution(
        values=extreme_values,
        weights=extreme_weights,
        title="Distribution with Outliers",
        bins=20,
        outlier_threshold=100,
        verbose=True,
    )
