'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-06-19 16:49:33 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-12-12 10:21:58 +0100
FilePath     : utils_histo.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import sys, os
import random
from datetime import datetime
from typing import Union, Dict, List, Tuple, Optional


import math
import pandas as pd
import numpy as np
import ROOT as r
from ROOT import gROOT, gStyle
from ROOT import RDF, RDataFrame, TFile
from ROOT import TCanvas, TLegend, TGraph, TRatioPlot
from ROOT import TH1, TH2, TH3, TH1D, TH2D, TH3D, TH1F, TH2F, TH3F, TAxis

from pathlib import Path
from itertools import product

from rich import print as rprint
from rich.table import Table


# Use rich backend for logging
import logging
from rich.logging import RichHandler

# Configure rich logging globally
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%x %X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

from .utils_yaml import read_yaml
from .utils_ROOT import check_root_file, apply_cut_to_rdf, add_tmp_var_to_rdf, add_tmp_weight_to_rdf, create_selected_dataframe


# * ----------------------------------------------------------------------------------------------------------------------
# * Core Histogram Utility Functions
# * ----------------------------------------------------------------------------------------------------------------------


def validate_histogram(hist: TH1 | TH2 | TH3) -> None:
    """
    Validate that input is a valid ROOT histogram.

    Args:
        hist: Object to validate

    Raises:
        TypeError: If the input is not a valid ROOT histogram
    """
    if not isinstance(hist, (TH1, TH2, TH3)):
        raise TypeError(f"Input must be a ROOT histogram (TH1, TH2, or TH3), got {type(hist)}")


def get_bin_content_safely(hist: TH1 | TH2 | TH3, bin_indices: tuple[int, ...]) -> float:
    """
    Get bin content with proper bin number indexing based on histogram dimension.

    Args:
        hist: ROOT histogram object
        bin_indices: Tuple of bin indices (x,) for 1D, (x,y) for 2D, (x,y,z) for 3D

    Returns:
        float: Bin content value

    Raises:
        ValueError: If histogram dimension is unsupported
    """
    ndim = len(bin_indices)

    # Because the content is found by using the bin number, a naive check could be performed that the bin_indices are all int values, instead of float (avoid people use actual axis values as bin_indices)
    if not all(isinstance(i, int) for i in bin_indices):
        raise ValueError(f"Indices must be integers, got {bin_indices}. Please use the bin number instead of the axis value.")

    # Get the bin content
    if ndim == 1:
        return hist.GetBinContent(bin_indices[0])
    elif ndim == 2:
        return hist.GetBinContent(bin_indices[0], bin_indices[1])
    elif ndim == 3:
        return hist.GetBinContent(bin_indices[0], bin_indices[1], bin_indices[2])
    else:
        raise ValueError(f"Unsupported histogram dimension: {ndim}")


def get_bin_error_safely(hist: TH1 | TH2 | TH3, bin_indices: tuple[int, ...]) -> float:
    """
    Get bin error with proper indexing based on histogram dimension.

    Args:
        hist: ROOT histogram object
        bin_indices: Tuple of bin indices

    Returns:
        float: Bin error value

    Raises:
        ValueError: If histogram dimension is unsupported
    """
    ndim = len(bin_indices)

    # Because the content is found by using the bin number, a naive check could be performed that the bin_indices are all int values, instead of float (avoid people use actual axis values as bin_indices)
    if not all(isinstance(i, int) for i in bin_indices):
        raise ValueError(f"Indices must be integers, got {bin_indices}. Please use the bin number instead of the axis value.")

    if ndim == 1:
        return hist.GetBinError(bin_indices[0])
    elif ndim == 2:
        return hist.GetBinError(bin_indices[0], bin_indices[1])
    elif ndim == 3:
        return hist.GetBinError(bin_indices[0], bin_indices[1], bin_indices[2])
    else:
        raise ValueError(f"Unsupported histogram dimension: {ndim}")


def set_bin_content_safely(hist: TH1 | TH2 | TH3, bin_indices: tuple[int, ...], value: float) -> None:
    """
    Set bin content with proper indexing based on histogram dimension.

    Args:
        hist: ROOT histogram object
        bin_indices: Tuple of bin indices
        value: Value to set

    Raises:
        ValueError: If histogram dimension is unsupported
    """
    ndim = len(bin_indices)

    # Because the content is found by using the bin number, a naive check could be performed that the bin_indices are all int values, instead of float (avoid people use actual axis values as bin_indices)
    if not all(isinstance(i, int) for i in bin_indices):
        raise ValueError(f"Indices must be integers, got {bin_indices}. Please use the bin number instead of the axis value.")

    if ndim == 1:
        hist.SetBinContent(bin_indices[0], value)
    elif ndim == 2:
        hist.SetBinContent(bin_indices[0], bin_indices[1], value)
    elif ndim == 3:
        hist.SetBinContent(bin_indices[0], bin_indices[1], bin_indices[2], value)
    else:
        raise ValueError(f"Unsupported histogram dimension: {ndim}")


def set_bin_error_safely(hist: TH1 | TH2 | TH3, bin_indices: tuple[int, ...], error: float) -> None:
    """
    Set bin error with proper indexing based on histogram dimension.

    Args:
        hist: ROOT histogram object
        bin_indices: Tuple of bin indices
        error: Error value to set (will be converted to absolute value)

    Raises:
        ValueError: If histogram dimension is unsupported
    """
    ndim = len(bin_indices)

    # Because the content is found by using the bin number, a naive check could be performed that the bin_indices are all int values, instead of float (avoid people use actual axis values as bin_indices)
    if not all(isinstance(i, int) for i in bin_indices):
        raise ValueError(f"Indices must be integers, got {bin_indices}. Please use the bin number instead of the axis value.")

    abs_error = abs(error)
    if ndim == 1:
        hist.SetBinError(bin_indices[0], abs_error)
    elif ndim == 2:
        hist.SetBinError(bin_indices[0], bin_indices[1], abs_error)
    elif ndim == 3:
        hist.SetBinError(bin_indices[0], bin_indices[1], bin_indices[2], abs_error)
    else:
        raise ValueError(f"Unsupported histogram dimension: {ndim}")


def set_bin_safely(hist: TH1 | TH2 | TH3, bin_indices: tuple[int, ...], value: float = None, error: float = None) -> None:
    """
    Set bin content and/or error with proper indexing based on histogram dimension.

    Args:
        hist: ROOT histogram object
        bin_indices: Tuple of bin indices
        value: Value to set (optional)
        error: Error to set (optional)
    """
    if value is not None:
        set_bin_content_safely(hist, bin_indices, value)
    if error is not None:
        set_bin_error_safely(hist, bin_indices, error)


def get_histogram_bin_ranges(hist: TH1 | TH2 | TH3) -> list[range]:
    """
    Get bin ranges for each dimension of a histogram.

    Args:
        hist: ROOT histogram object (TH1, TH2, or TH3)

    Returns:
        list[range]: List of ranges for each dimension of the histogram.

        Examples:
            - 1D histogram: [range(1, hist.GetNbinsX() + 1)]
            - 2D histogram: [range(1, hist.GetNbinsX() + 1), range(1, hist.GetNbinsY() + 1)]
            - 3D histogram: [range(1, hist.GetNbinsX() + 1), range(1, hist.GetNbinsY() + 1), range(1, hist.GetNbinsZ() + 1)]
    """
    ndim = hist.GetDimension()
    ranges: list[range] = [range(1, hist.GetNbinsX() + 1)]

    if ndim >= 2:
        ranges.append(range(1, hist.GetNbinsY() + 1))
    if ndim == 3:
        ranges.append(range(1, hist.GetNbinsZ() + 1))

    return ranges


def format_bin_position(hist: TH1 | TH2 | TH3, bin_indices: tuple[int, ...]) -> str:
    """
    Format bin position string with bin indices and total bins.

    Args:
        hist: ROOT histogram object
        bin_indices: Tuple of bin indices

    Returns:
        str: Formatted position string (e.g., "x = 1 (10), y = 2 (5)")
    """
    ndim = hist.GetDimension()
    pos_parts = []

    if ndim >= 1:
        pos_parts.append(f"x = {bin_indices[0]} ({hist.GetNbinsX()})")
    if ndim >= 2:
        pos_parts.append(f"y = {bin_indices[1]} ({hist.GetNbinsY()})")
    if ndim == 3:
        pos_parts.append(f"z = {bin_indices[2]} ({hist.GetNbinsZ()})")

    return ", ".join(pos_parts)


def should_modify_bin(bin_content: float, option: str) -> bool:
    """
    Determine if a bin should be modified based on its content and the specified option.

    Args:
        bin_content: Current bin content value
        option: Modification criteria option

    Returns:
        bool: True if bin should be modified

    Raises:
        ValueError: If option is invalid
    """
    conditions = {
        'all': lambda x: True,
        'zero': lambda x: x == 0,
        'non_zero': lambda x: x != 0,
        'negative': lambda x: x < 0,
        'non_negative': lambda x: x >= 0,
        'positive': lambda x: x > 0,
        'non_positive': lambda x: x <= 0,
    }

    if option not in conditions:
        raise ValueError(f"Invalid option: {option}. Valid options: {list(conditions.keys())}")

    return conditions[option](bin_content)


def get_full_hist_title(hist: TH1 | TH2 | TH3) -> str:
    """
    Get the complete title of a histogram including all axis titles.

    Args:
        hist: ROOT histogram object (TH1, TH2, or TH3)

    Returns:
        str: Complete title with axis labels separated by semicolons (ROOT format)
    """
    # Get the main title
    title: str = hist.GetTitle()
    titles: list[str] = [title]

    # Map dimension index to axis name
    axes: dict[int, str] = {0: 'X', 1: 'Y', 2: 'Z'}

    # Get the title for each axis based on histogram dimension
    for i in range(hist.GetDimension()):
        axis = getattr(hist, f'Get{axes[i]}axis')()
        titles.append(axis.GetTitle())

    # Join all titles with semicolons (ROOT title format)
    return ";".join(titles)


def is_inside_axis_range(axis: TAxis, x: float) -> bool:
    """
    Check if a given x-coordinate is inside the valid range of a axis.

    Args:
        axis: Input axis
        x: X-coordinate to check

    Returns:
        bool: True if x is inside the valid range, False otherwise

    Note:
        ROOT uses a consistent bin numbering system across all histogram types:
            bin = 0: underflow bin
            bin = 1: first bin with low-edge INCLUDED
            bin = nbins: last bin with upper-edge EXCLUDED
            bin = nbins+1: overflow bin
    """
    return axis.GetXmin() <= x < axis.GetXmax()


def print_histogram_info(
    hist: TH1 | TH2 | TH3,
    print_bin_contents: bool = True,
    print_bin_edges: bool = True,
    print_overflow_bins: bool = True,
    print_style_info: bool = False,
    max_bins_per_axis: int = 20,
    precision: int = 4,
) -> None:
    """
    Print comprehensive information about a ROOT histogram including edges, bin contents, and statistics.

    Args:
        hist: ROOT histogram object (TH1, TH2, or TH3)
        print_bin_contents: Whether to print bin contents and errors
        print_bin_edges: Whether to print bin edge information
        print_overflow_bins: Whether to include underflow/overflow bins in output
        print_style_info: Whether to print style information (colors, markers, etc.)
        max_bins_per_axis: Maximum number of bins to print per axis (prevents overwhelming output)
        precision: Number of decimal places for floating point values

    Raises:
        TypeError: If input is not a valid ROOT histogram
    """

    # Validate input
    validate_histogram(hist)

    # Helper function for formatting numbers
    def fmt(value: float) -> str:
        return f"{value:.{precision}f}"

    # Get basic histogram properties
    ndim = hist.GetDimension()
    axes = [hist.GetXaxis()]
    if ndim >= 2:
        axes.append(hist.GetYaxis())
    if ndim == 3:
        axes.append(hist.GetZaxis())

    axis_names = ['X', 'Y', 'Z'][:ndim]

    # Print header
    rprint("=" * 80)
    rprint(f"HISTOGRAM INFORMATION: {hist.GetName()}")
    rprint("=" * 80)

    # Basic information
    rprint(f"Name:           {hist.GetName()}")
    rprint(f"Title:          {hist.GetTitle()}")
    rprint(f"Full Title:     {get_full_hist_title(hist)}")
    rprint(f"Dimension:      {ndim}D")
    rprint(f"Class:          {hist.ClassName()}")
    rprint(f"Entries:        {hist.GetEntries()}")
    rprint(f"Sum of weights: {fmt(hist.GetSumOfWeights())}")
    rprint(f"Integral:       {fmt(hist.Integral())}")

    # Include overflow/underflow in integral if requested
    if print_overflow_bins:
        if ndim == 1:
            integral_all = hist.Integral(0, hist.GetNbinsX() + 1)
        elif ndim == 2:
            integral_all = hist.Integral(0, hist.GetNbinsX() + 1, 0, hist.GetNbinsY() + 1)
        else:  # ndim == 3
            integral_all = hist.Integral(0, hist.GetNbinsX() + 1, 0, hist.GetNbinsY() + 1, 0, hist.GetNbinsZ() + 1)
        rprint(f"Integral (w/ u/o): {fmt(integral_all)}")

    rprint()

    # Add NaN counting in STATISTICS section
    bin_ranges = get_histogram_bin_ranges(hist)
    nan_bins = 0
    total_checked = 0

    # Include overflow bins in NaN counting if requested
    if print_overflow_bins:
        extended_bin_ranges = []
        for i, r in enumerate(bin_ranges):
            if i == 0:  # X-axis
                extended_bin_ranges.append(range(0, hist.GetNbinsX() + 2))
            elif i == 1:  # Y-axis
                extended_bin_ranges.append(range(0, hist.GetNbinsY() + 2))
            elif i == 2:  # Z-axis
                extended_bin_ranges.append(range(0, hist.GetNbinsZ() + 2))
        count_bin_ranges = extended_bin_ranges
    else:
        count_bin_ranges = bin_ranges

    for bin_indices in product(*count_bin_ranges):
        content = get_bin_content_safely(hist, bin_indices)
        total_checked += 1
        if math.isnan(content):
            nan_bins += 1

    if nan_bins > 0:
        rprint(f"[red] NaN bins:        {nan_bins}/{total_checked} ({nan_bins/total_checked*100:.2f}%)[/red]")
        rprint()

    # Axis information
    rprint("AXIS INFORMATION:")
    rprint("-" * 50)

    for i, (axis, name) in enumerate(zip(axes, axis_names)):
        rprint(f"{name}-axis:")
        rprint(f"  Title:      {axis.GetTitle()}")
        rprint(f"  Bins:       {axis.GetNbins()}")
        rprint(f"  Range:      [{fmt(axis.GetXmin())}, {fmt(axis.GetXmax())})")
        rprint(f"  Bin width:  {fmt(axis.GetBinWidth(1))} (if uniform)")

        # Print bin edges if requested
        if print_bin_edges:
            nbins = axis.GetNbins()
            if nbins <= max_bins_per_axis:
                # Print all edges
                edges = [axis.GetBinLowEdge(i) for i in range(1, nbins + 2)]
                edges_str = ", ".join([fmt(edge) for edge in edges])
                rprint(f"  Edges:      [{edges_str}]")
            else:
                # Print first and last few edges
                n_show = min(5, max_bins_per_axis // 2)
                first_edges = [axis.GetBinLowEdge(i) for i in range(1, n_show + 1)]
                last_edges = [axis.GetBinLowEdge(i) for i in range(nbins - n_show + 2, nbins + 2)]

                first_str = ", ".join([fmt(edge) for edge in first_edges])
                last_str = ", ".join([fmt(edge) for edge in last_edges])
                rprint(f"  Edges:      [{first_str}, ..., {last_str}] ({nbins + 1} total)")
        rprint()

    # Statistics
    rprint("STATISTICS:")
    rprint("-" * 50)

    # Get statistics for each axis
    if ndim == 1:
        rprint(f"Mean:           {fmt(hist.GetMean())}")
        rprint(f"RMS:            {fmt(hist.GetRMS())}")
        rprint(f"Std Dev:        {fmt(hist.GetStdDev())}")
    else:
        for i, name in enumerate(axis_names):
            axis_num = i + 1  # ROOT uses 1-based indexing
            rprint(f"Mean {name}:        {fmt(hist.GetMean(axis_num))}")
            rprint(f"RMS {name}:         {fmt(hist.GetRMS(axis_num))}")
            rprint(f"Std Dev {name}:     {fmt(hist.GetStdDev(axis_num))}")

    # Min/Max bin content
    rprint(f"Min bin content: {fmt(hist.GetMinimum())}")
    rprint(f"Max bin content: {fmt(hist.GetMaximum())}")

    # Under/overflow information
    if print_overflow_bins:
        rprint("UNDERFLOW/OVERFLOW BINS:")
        rprint("-" * 50)

        if ndim == 1:
            underflow = hist.GetBinContent(0)
            overflow = hist.GetBinContent(hist.GetNbinsX() + 1)
            rprint(f"Underflow: {fmt(underflow)}")
            rprint(f"Overflow:  {fmt(overflow)}")

        elif ndim == 2:
            # For 2D, there are multiple under/overflow regions
            nx, ny = hist.GetNbinsX(), hist.GetNbinsY()

            # Corner bins
            rprint(f"Underflow XY:    {fmt(hist.GetBinContent(0, 0))}")
            rprint(f"Underflow X:     {fmt(sum(hist.GetBinContent(0, j) for j in range(1, ny + 1)))}")
            rprint(f"Underflow Y:     {fmt(sum(hist.GetBinContent(i, 0) for i in range(1, nx + 1)))}")
            rprint(f"Overflow XY:     {fmt(hist.GetBinContent(nx + 1, ny + 1))}")
            rprint(f"Overflow X:      {fmt(sum(hist.GetBinContent(nx + 1, j) for j in range(1, ny + 1)))}")
            rprint(f"Overflow Y:      {fmt(sum(hist.GetBinContent(i, ny + 1) for i in range(1, nx + 1)))}")

        elif ndim == 3:
            # For 3D, just show total under/overflow
            nx, ny, nz = hist.GetNbinsX(), hist.GetNbinsY(), hist.GetNbinsZ()

            underflow_total = 0
            overflow_total = 0

            # This is simplified - full 3D under/overflow analysis would be very complex
            for i in range(nx + 2):
                for j in range(ny + 2):
                    for k in range(nz + 2):
                        content = hist.GetBinContent(i, j, k)
                        if i == 0 or j == 0 or k == 0:
                            underflow_total += content
                        elif i == nx + 1 or j == ny + 1 or k == nz + 1:
                            overflow_total += content

            rprint(f"Total underflow: {fmt(underflow_total)}")
            rprint(f"Total overflow:  {fmt(overflow_total)}")

        rprint()

    # Bin contents
    if print_bin_contents:
        rprint("BIN CONTENTS:")
        rprint("-" * 50)

        bin_ranges = get_histogram_bin_ranges(hist)

        # Calculate total bins and check if we should limit output
        total_bins = 1
        for r in bin_ranges:
            total_bins *= len(r)

        # Decide whether to print all bins or limit output
        max_total_bins = max_bins_per_axis**ndim

        if total_bins <= max_total_bins:
            # Print all bins
            rprint("Bin contents (indices: content ± error):")

            bin_count = 0
            for bin_indices in product(*bin_ranges):
                content = get_bin_content_safely(hist, bin_indices)
                error = get_bin_error_safely(hist, bin_indices)

                # Format bin_indices
                indices_str = "(" + ", ".join([f"{idx}" for idx in bin_indices]) + ")"
                if math.isnan(content) or content < 0:
                    # Red color for negative or NaN bins
                    rprint(f"[red]  {indices_str:12}: {fmt(content)} ± {fmt(error)}[/red]")
                elif content == 0:
                    rprint(f"[yellow]  {indices_str:12}: {fmt(content)} ± {fmt(error)}[/yellow]")
                else:
                    rprint(f"  {indices_str:12}: {fmt(content)} ± {fmt(error)}")

                bin_count += 1

        else:
            # Print summary information and some sample bins
            rprint(f"Too many bins ({total_bins}) to display all. Showing sample:")

            # Count non-zero bins
            zero_bins = 0
            nonzero_bins = 0
            min_content = float('inf')
            max_content = float('-inf')

            sample_bins = []
            sample_count = 0
            max_samples = min(20, max_total_bins)

            for bin_indices in product(*bin_ranges):
                content = get_bin_content_safely(hist, bin_indices)
                error = get_bin_error_safely(hist, bin_indices)

                if content == 0:
                    zero_bins += 1
                else:
                    nonzero_bins += 1
                    min_content = min(min_content, content)
                    max_content = max(max_content, content)

                # Collect sample bins (prefer non-zero bins)
                if sample_count < max_samples and (content != 0 or sample_count < max_samples // 2):
                    bin_indices_str = "(" + ", ".join([f"{idx}" for idx in bin_indices]) + ")"
                    sample_bins.append(f"  {bin_indices_str:12}: {fmt(content)} ± {fmt(error)}")
                    sample_count += 1

            rprint(f"  Total bins:    {total_bins}")
            rprint(f"  Zero bins:     {zero_bins}")
            rprint(f"  Non-zero bins: {nonzero_bins}")
            if nonzero_bins > 0:
                rprint(f"  Content range: [{fmt(min_content)}, {fmt(max_content)}]")

            rprint(f"\nSample bins (showing {len(sample_bins)} of {total_bins}):")
            for line in sample_bins:
                rprint(line)

        rprint()

    # Style information
    if print_style_info:
        rprint("STYLE INFORMATION:")
        rprint("-" * 50)
        rprint(f"Line color:     {hist.GetLineColor()}")
        rprint(f"Line style:     {hist.GetLineStyle()}")
        rprint(f"Line width:     {hist.GetLineWidth()}")
        rprint(f"Fill color:     {hist.GetFillColor()}")
        rprint(f"Fill style:     {hist.GetFillStyle()}")
        rprint(f"Marker color:   {hist.GetMarkerColor()}")
        rprint(f"Marker style:   {hist.GetMarkerStyle()}")
        rprint(f"Marker size:    {fmt(hist.GetMarkerSize())}")
        rprint()

    rprint("=" * 80)


# ----------------------------------------------------------------------------------------------------------------------
# Histogram Creation and Template Functions
# ----------------------------------------------------------------------------------------------------------------------


def construct_histo_template_from_yaml(input_yaml_file: str | dict, mode: str | list, histo_name: str = None) -> TH1 | TH2 | TH3:
    """
    Construct a ROOT histogram from a YAML configuration file.

    Args:
        input_yaml_file: Path to YAML file or dict with histogram configuration
        mode: Mode or section to read from the YAML file
        histo_name: Optional name for the created histogram

    Returns:
        A ROOT histogram (TH1D, TH2D, or TH3D) based on the configuration

    Raises:
        AssertionError: If input file doesn't exist
        ValueError: If histogram dimension is invalid
        KeyError: If required configuration keys are missing
    """
    # Check whether input file exists
    if isinstance(input_yaml_file, str):
        assert Path(input_yaml_file).is_file(), f"Input file {input_yaml_file} does not exist!"

    # Read histogram template from the yaml file
    config = read_yaml(input_yaml_file, mode)

    # Validate dimension
    dim = config.get('dim')
    if dim not in [1, 2, 3]:
        raise ValueError(f"Invalid histogram dimension: {dim}. Must be 1, 2, or 3.")

    def format_axis_title(axis_config: dict) -> str:
        """Format axis title with optional unit."""
        title = axis_config['title']
        if 'unit' in axis_config and axis_config['unit']:
            return f"{title} [{axis_config['unit']}]"
        return title

    # Create histogram based on dimension
    if dim == 1:
        axis_x = config['x']
        hist = TH1D(
            config['name'],
            f";{format_axis_title(axis_x)}",
            int(axis_x['nbins']),
            float(axis_x['min']),
            float(axis_x['max']),
        )
    elif dim == 2:
        axis_x, axis_y = config['x'], config['y']
        hist = TH2D(
            config['name'],
            f";{format_axis_title(axis_x)};{format_axis_title(axis_y)}",
            int(axis_x['nbins']),
            float(axis_x['min']),
            float(axis_x['max']),
            int(axis_y['nbins']),
            float(axis_y['min']),
            float(axis_y['max']),
        )
    elif dim == 3:
        axis_x, axis_y, axis_z = config['x'], config['y'], config['z']
        hist = TH3D(
            config['name'],
            f";{format_axis_title(axis_x)};{format_axis_title(axis_y)};{format_axis_title(axis_z)}",
            int(axis_x['nbins']),
            float(axis_x['min']),
            float(axis_x['max']),
            int(axis_y['nbins']),
            float(axis_y['min']),
            float(axis_y['max']),
            int(axis_z['nbins']),
            float(axis_z['min']),
            float(axis_z['max']),
        )

    # Return the histogram, cloning if a new name is provided
    return hist if histo_name is None else hist.Clone(histo_name)


def copy_histo_to_float_precision(hist: TH1 | TH2 | TH3) -> TH1F | TH2F | TH3F:
    """
    Copy a histogram to a float precision histogram.

    Args:
        hist: Input ROOT histogram

    Returns:
        Float precision copy of the input histogram

    Raises:
        AssertionError: If input is not a valid ROOT histogram
    """
    validate_histogram(hist)

    # Create the appropriate histogram type
    if isinstance(hist, TH3):
        hist_f = r.TH3F()
    elif isinstance(hist, TH2):
        hist_f = r.TH2F()
    else:
        hist_f = r.TH1F()

    # Copy template to the new histogram by overriding the existing histogram
    hist.Copy(hist_f)
    hist_f.SetName(hist.GetName())

    return hist_f


def copy_histo_to_double_precision(hist: TH1 | TH2 | TH3) -> TH1D | TH2D | TH3D:
    """
    Copy a histogram to a double precision histogram.

    Args:
        hist: Input ROOT histogram

    Returns:
        Double precision copy of the input histogram

    Raises:
        AssertionError: If input is not a valid ROOT histogram
    """
    validate_histogram(hist)

    # Create the appropriate histogram type
    if isinstance(hist, TH3):
        hist_d = r.TH3D()
    elif isinstance(hist, TH2):
        hist_d = r.TH2D()
    else:
        hist_d = r.TH1D()

    # Copy template to the new histogram
    hist.Copy(hist_d)
    hist_d.SetName(hist.GetName())

    return hist_d


# ----------------------------------------------------------------------------------------------------------------------
# Histogram Manipulation Functions
# ----------------------------------------------------------------------------------------------------------------------


def set_bins_to_value(hist: TH1 | TH2 | TH3, value: float = 1.0e-6, error: float = 1.0, option: str = 'all') -> TH1 | TH2 | TH3:
    """
    Set bins of a histogram to a specific value and error based on filtering criteria.

    Args:
        hist: ROOT histogram (TH1, TH2, or TH3)
        value: Value to set for each bin content (default: 1.0e-6), if None, then do not set the content
        error: Error to set for each bin (default: 1.0), if None, then do not set the error
        option: Filtering option for which bins to modify:
                'all' - set all bins
                'zero' - only bins with zero content
                'non_zero' - only bins with non-zero content
                'negative' - only bins with negative content
                'non_negative' - only bins with non-negative content (>= 0)
                'positive' - only bins with positive content
                'non_positive' - only bins with non-positive content (<= 0)

    Returns:
        The modified histogram

    Raises:
        TypeError: If the input is not a valid ROOT histogram
        ValueError: If option is invalid
    """
    validate_histogram(hist)

    # Get histogram bin ranges
    bin_ranges: list[range] = get_histogram_bin_ranges(hist)

    # Process all bins
    modified_count = 0
    total_bins = 0
    for bin_indices in product(*bin_ranges):
        bin_content = get_bin_content_safely(hist, bin_indices)
        total_bins += 1
        if should_modify_bin(bin_content, option):
            set_bin_safely(hist, bin_indices, value, error)
            modified_count += 1

    logger.info(f"Modified {modified_count} bins out of {total_bins} ({modified_count/total_bins*100:.2f}%) in histogram '{hist.GetName()}' with option '{option}'")

    return hist


def scale_histogram(hist: TH1 | TH2 | TH3, target_integral: float) -> TH1 | TH2 | TH3:
    """
    Scale histogram to achieve target integral.

    Args:
        hist: ROOT histogram to scale
        target_integral: Target integral value

    Returns:
        The scaled histogram

    Note:
        If histogram has zero integral, warning is logged and no scaling is performed
    """
    current_integral = hist.Integral()
    if current_integral > 0:
        scale_factor = target_integral / current_integral
        hist.Scale(scale_factor)
    else:
        logger.warning(f"Cannot scale histogram with zero integral, current integral: {current_integral}")
    return hist


###########################!TODO TESTING########################


def zero_histogram_bins(hist: TH1 | TH2 | TH3, bins_to_modify: dict, enable: bool = True) -> None:
    """
    Modify specific bins of a ROOT histogram (1D to 3D) by zeroing out or retaining data
    based on the 'enable' flag. This function is robust to handle different histogram dimensions.

    Args:
        hist (TH1, TH2, TH3): The ROOT histogram to modify.
        bins_to_modify (dict): A dictionary specifying bins to modify for each dimension.
                               Example: {'x': [1, 5, 10], 'y': [2, 3]}.
        enable (bool): If True, retains data in the specified bins and zeros out the rest.
                       If False, zeros out data in the specified bins only.

    Raises:
        ValueError: If inappropriate dimensions are provided or bins are out of range.
    """
    # Check histogram dimension
    ndim = hist.GetDimension()
    allowed_dims = ['x', 'y', 'z'][:ndim]

    # Validate the input dictionary dimensions against the histogram's allowed dimensions
    if any(dim not in allowed_dims for dim in bins_to_modify):
        raise ValueError(f"Invalid dimension(s) in bins_to_modify. Allowed dimensions: {allowed_dims}, Provided: {bins_to_modify.keys()}")

    # Validate and normalize bins_to_modify: ensure values are lists
    bins_to_modify = {k: v if isinstance(v, list) else [v] for k, v in bins_to_modify.items()}

    # Set bin ranges for each axis of the histogram
    bin_range = {
        'x': (1, hist.GetNbinsX() + 1),
        'y': (1, hist.GetNbinsY() + 1 if ndim > 1 else 2),
        'z': (1, hist.GetNbinsZ() + 1 if ndim > 2 else 2),
    }

    # Loop over all bins and modify based on enable flag
    for binx in range(*bin_range['x']):
        x_condition = 'x' in bins_to_modify and binx in bins_to_modify['x']

        for biny in range(*bin_range['y']):
            y_condition = 'y' in bins_to_modify and biny in bins_to_modify['y']

            for binz in range(*bin_range['z']):
                z_condition = 'z' in bins_to_modify and binz in bins_to_modify['z']

                # Determine if the current bin should be modified based on the axis conditions and enable flag
                condition = (x_condition if 'x' in bins_to_modify else True) and (y_condition if 'y' in bins_to_modify else True) and (z_condition if 'z' in bins_to_modify else True)

                # Modify bins: zero out if (enabled and not this bin) or (disabled and this bin)
                if (enable and not condition) or (not enable and condition):
                    if ndim == 1:
                        hist.SetBinContent(binx, 0)
                    elif ndim == 2:
                        hist.SetBinContent(binx, biny, 0)
                    elif ndim == 3:
                        hist.SetBinContent(binx, biny, binz, 0)


# # Example usage:
# if __name__ == "__main__":
#     # Load a 2D histogram from a ROOT file
#     hist_2d = get_hist_from_file("path_to_file.root", "hist2d_name")

#     # Enable specific bins: keep only specified bins in 'x' and 'y' dimensions, zero the rest
#     zero_histogram_bins(hist_2d, {'x': [1, 5, 10], 'y': [2, 3]}, enable=True)

#     # Disable specific bins: zero out the specified bins in 'x' and 'y' dimensions
#     zero_histogram_bins(hist_2d, {'x': [1, 5, 10], 'y': [2, 3]}, enable=False)

###########################!TODO TESTING########################


# ----------------------------------------------------------------------------------------------------------------------
# Histogram Filling Functions
# ----------------------------------------------------------------------------------------------------------------------


def fill_hist_template_from_rdf(rdf: RDataFrame, variables: str | list[str], weight: str, hist_template: TH1 | TH2 | TH3) -> TH1 | TH2 | TH3:
    """
    Fill a histogram from RDataFrame data using the provided template.

    Args:
        rdf: RDataFrame containing the data
        variables: Variable(s) to plot (string or list of strings)
        weight: Expression for the event weight
        hist_template: Template histogram defining binning and axes

    Returns:
        Filled histogram with data from RDataFrame

    Raises:
        AssertionError: If hist_template is not a valid ROOT histogram
    """
    validate_histogram(hist_template)

    # Normalize variables to list format
    vars_list = variables if isinstance(variables, list) else [variables]

    # Add variables to RDataFrame
    temp_vars = []
    for i, var in enumerate(vars_list):
        rdf, temp_var = add_tmp_var_to_rdf(rdf, var, f'__var{i}')
        temp_vars.append(temp_var)

    # Add weight variable
    rdf, temp_weight = add_tmp_weight_to_rdf(rdf, weight)

    # Copy the histogram to double precision which is required by RDF
    hist_d = copy_histo_to_double_precision(hist_template)

    # Reset the histogram to remove any existing content
    hist_d.Reset()

    # Create the appropriate histogram type with double precision
    if isinstance(hist_template, TH3):
        result: TH3 = rdf.Histo3D(r.ROOT.RDF.TH3DModel(hist_d), *temp_vars, temp_weight).GetValue()
    elif isinstance(hist_template, TH2):
        result: TH2 = rdf.Histo2D(r.ROOT.RDF.TH2DModel(hist_d), *temp_vars, temp_weight).GetValue()
    else:
        result: TH1 = rdf.Histo1D(r.ROOT.RDF.TH1DModel(hist_d), *temp_vars, temp_weight).GetValue()

    # Proper error handling (THn::Clone copies the Sumw2 setting, but THnDModel only copies name, title and axes parameters, not further settings.)
    result.Sumw2() if result.GetSumw2N() == 0 else None  # Enable proper error calculation. Call sumw2() if it is not already enabled.

    # Ensure title is preserved
    result.SetTitle(get_full_hist_title(hist_template))

    return result


def get_histo_with_given_template_from_rdf(
    rdf: RDataFrame,
    variables: str | list[str],
    weight: str,
    hist_template: TH1 | TH2 | TH3,
    output_hist_name: str,
    *,
    cut_str: str = 'NONE',
    fill_histo_if_empty: bool = False,
    fill_histo_with_default_value: float = 1e-6,
    verbose: bool = False,
) -> TH1 | TH2 | TH3:
    """
    Create a histogram from RDataFrame data using a template histogram for binning and axis properties.

    Args:
        rdf: RDataFrame containing the data
        variables: Variable(s) to plot (must match histogram dimension)
        weight: Expression for the event weight
        hist_template: Template histogram defining binning and axes
        output_hist_name: Name for the output histogram
        cut_str: Selection criteria to apply to the data
        fill_histo_if_empty: If True, fills histogram with small values when dataframe is empty
        fill_histo_with_default_value: Value to fill the histogram with if it is empty
        verbose: If True, print additional information about the histogram

    Returns:
        Filled histogram with properties from the template

    Raises:
        ValueError: If number of variables doesn't match histogram dimension
        TypeError: If histogram template has invalid type
    """
    # Create the histogram from template
    hist = hist_template.Clone(output_hist_name)
    hist.Sumw2() if hist.GetSumw2N() == 0 else None  # Enable proper error calculation. Call sumw2() if it is not already enabled.

    # Apply cuts to RDataFrame
    rdf = apply_cut_to_rdf(rdf, cut_str)

    # Process data if available
    if rdf.Count().GetValue() > 0:
        # Fill the histogram from the rdf
        hist = fill_hist_template_from_rdf(rdf, variables, weight, hist)
    else:
        logger.warning(f'The dataframe is empty after applying the cut: {cut_str}')
        if fill_histo_if_empty:
            logger.info(f'Filling histogram "{output_hist_name}" with default values ({fill_histo_with_default_value})')

            # Copy the histogram to double precision which is required by RDF
            hist_d = copy_histo_to_double_precision(hist)

            # Fill the histogram with default values
            hist = set_bins_to_value(hist_d, fill_histo_with_default_value)

    # Preserve full title information from template
    hist.SetTitle(get_full_hist_title(hist_template))

    # Print histogram statistics
    logger.info(f'Information about the histogram "{output_hist_name}":')
    logger.info(f'Number of entries : {hist.GetEntries()}')
    logger.info(f'Sum of weights    : {hist.GetSumOfWeights()}')

    # Check if there are any bins with zero content or negative content
    bin_ranges: list[range] = get_histogram_bin_ranges(hist)

    # Check how many bins are zero or negative
    zero_bins = 0
    negative_bins = 0
    total_bins = 0
    for bin_indices in product(*bin_ranges):
        bin_content = get_bin_content_safely(hist, bin_indices)
        total_bins += 1
        if bin_content == 0:
            zero_bins += 1
        if bin_content < 0:
            negative_bins += 1
    logger.info(
        f'Number of bins with zero content: {zero_bins}/{total_bins} ({zero_bins/total_bins*100:.2f}%), Number of bins with negative content: {negative_bins}/{total_bins} ({negative_bins/total_bins*100:.2f}%)'
    )

    if verbose:
        for bin_indices in product(*bin_ranges):
            bin_content = get_bin_content_safely(hist, bin_indices)

            if bin_content <= 0:
                position_str = format_bin_position(hist, bin_indices)
                logger.warning(f'Histogram "{output_hist_name}" has a bin with zero content or negative content (content: {bin_content}) at {position_str}')

    return hist


def get_histo_with_given_template_from_file(
    inputfile: Union[str, list, RDataFrame],
    variables: Union[str, list[str]],
    weight: str,
    hist_template: TH1 | TH2 | TH3,
    output_hist_name: str,
    tree_name: str = 'DecayTree',
    cut_str: str = 'NONE',
    fill_histo_if_empty: bool = False,
    fill_histo_with_default_value: float = 1e-6,
) -> TH1 | TH2 | TH3:
    """
    Create a histogram from file data using a template histogram for binning and axis properties.

    Args:
        inputfile: ROOT file path(s) or RDataFrame containing the data
        variables: Variable(s) to plot (must match histogram dimension)
        weight: Expression for the event weight
        hist_template: Template histogram defining binning and axes
        output_hist_name: Name for the output histogram
        tree_name: Name of the tree in ROOT file(s) (ignored if inputfile is RDataFrame)
        cut_str: Selection criteria to apply to the data
        fill_histo_if_empty: If True, fills histogram with small values when dataframe is empty
        fill_histo_with_default_value: Value to fill the histogram with if it is empty

    Returns:
        Filled histogram with properties from the template

    Raises:
        ValueError: If number of variables doesn't match histogram dimension
        TypeError: If inputfile has invalid type
    """
    # Create RDataFrame from input
    rdf = create_selected_dataframe(inputfile, tree_name, cut_str)

    # Get the histogram from the RDataFrame
    hist = get_histo_with_given_template_from_rdf(
        rdf,
        variables,
        weight,
        hist_template,
        output_hist_name,
        cut_str=cut_str,
        fill_histo_if_empty=fill_histo_if_empty,
        fill_histo_with_default_value=fill_histo_with_default_value,
    )

    return hist


# ----------------------------------------------------------------------------------------------------------------------
# File I/O Functions
# ----------------------------------------------------------------------------------------------------------------------


def get_hist_from_file(file_path: str, hist_name: str, new_hist_name: str = None) -> TH1 | TH2 | TH3:
    """
    Retrieve a histogram from a ROOT file with proper memory management.

    Args:
        file_path: Path to the ROOT file
        hist_name: Name of the histogram to retrieve
        new_hist_name: Optional new name for the retrieved histogram, if None, the histogram will be returned without cloning

    Returns:
        The retrieved histogram (TH1, TH2, or TH3)

    Raises:
        FileNotFoundError: If file cannot be opened or histogram not found
        ValueError: If object is not a valid histogram
    """

    # Generate a unique name if none provided
    target_name = hist_name if new_hist_name is None else new_hist_name

    # Check if an object with this name already exists
    if new_hist_name and gROOT.FindObject(target_name):
        logger.warning(f"Object with name {target_name} already exists, please consider using a unique name for the histogram.")

        # Generate a unique name
        # target_name = get_unique_hist_name(target_name)

    # Validate the input file
    if not check_root_file(file_path, hist_name):
        raise FileNotFoundError(f"Unable to find histogram: {hist_name} in file: {file_path}")

    # Open the file
    root_file = TFile.Open(file_path, "READ")

    # Get the histogram
    hist_obj = root_file.Get(hist_name)

    # Clone and verify the histogram
    histogram = hist_obj.Clone(target_name) if new_hist_name else hist_obj
    validate_histogram(histogram)

    # Detach from file and close
    histogram.SetDirectory(0)

    root_file.Close()

    return histogram


def get_hists_from_ROOT_to_dict(input_file_path: str, new_hist_name_suffix: str = "") -> dict[str, TH1]:
    """
    Extract all histograms from a ROOT file into a dictionary.

    Args:
        input_file_path: Path to the ROOT file
        new_hist_name_suffix: Optional suffix to append to histogram names (default: "")

    Returns:
        Dictionary mapping original histogram names to their cloned objects

    Raises:
        FileNotFoundError: If the file cannot be opened
        RuntimeError: If no histograms are found in the file
    """
    # Log the operation
    logger.info(f'Reading histograms from {input_file_path}')

    # Open the ROOT file
    root_file = TFile.Open(input_file_path, "READ")
    if not root_file or root_file.IsZombie():
        raise FileNotFoundError(f"Unable to open file: {input_file_path}")

    # Dictionary to store the histograms
    histograms = {}

    # Process histogram suffix
    suffix = f"_{new_hist_name_suffix}" if new_hist_name_suffix else ""

    # Loop over all keys in the ROOT file
    for key in root_file.GetListOfKeys():
        obj = key.ReadObj()

        # Check if object is a histogram
        if obj and obj.InheritsFrom("TH1"):
            orig_name = obj.GetName()
            new_name = f"{orig_name}{suffix}"

            # Clone the histogram with the new name
            hist_clone = obj.Clone(new_name)

            # Detach from file to prevent deletion when file is closed
            hist_clone.SetDirectory(0)

            # Store in dictionary using original name as key
            histograms[orig_name] = hist_clone

    # Close the file after processing all objects
    root_file.Close()

    # Check if any histograms were found
    if not histograms:
        logger.warning(f"No histograms found in {input_file_path}")
    else:
        logger.info(f"Successfully loaded {len(histograms)} histograms from {input_file_path}")

    return histograms


# ----------------------------------------------------------------------------------------------------------------------
# Accessing Histogram Properties
# ----------------------------------------------------------------------------------------------------------------------
def get_bin_indices_from_coordinates(coordinates: Union[list[float], tuple[float, ...], np.ndarray, pd.Series], hist: TH1 | TH2 | TH3) -> tuple[tuple[int, ...], list[bool]]:
    """
    Get the bin indices from the physical coordinates for a given histogram.

    Args:
        coordinates: Actual physical coordinates to lookup (not bin numbers)
                    - (x,) for 1D histograms
                    - (x,y) for 2D histograms
                    - (x,y,z) for 3D histograms
        hist: Input histogram (TH1, TH2, or TH3)

    Returns:
        Tuple containing:
        - bin_indices (tuple[int, ...]): Bin indices for each dimension
        - is_inside_per_axis (list[bool]): True if point lies within valid histogram range for ALL dimensions

    """

    # Input validation using existing utility function
    validate_histogram(hist)

    # Convert input to tuple of coordinates
    if isinstance(coordinates, pd.Series):
        coordinates = tuple(coordinates.values)
    else:
        coordinates = tuple(coordinates)

    # Check coordinate dimension compatibility
    ndim = hist.GetDimension()
    if len(coordinates) != ndim:
        raise ValueError(f"Coordinate dimension mismatch: got {len(coordinates)} coordinates " f"for {ndim}D histogram '{hist.GetName()}'")

    # Step 1: Get histogram axes for each dimension
    # This creates a list of TAxis objects [X-axis, Y-axis, Z-axis] based on histogram dimension
    axes: list[TAxis] = [hist.GetXaxis()]
    if ndim >= 2:
        axes.append(hist.GetYaxis())
    if ndim == 3:
        axes.append(hist.GetZaxis())

    # Find the bin indices for each axis using ROOT's FindBin method
    # Note: FindBin returns the bin number (1-indexed for valid bins)
    bin_indices = tuple(axis.FindBin(coord) for axis, coord in zip(axes, coordinates))

    # Step 2: Check if point lies within valid histogram range for ALL dimensions
    # Using existing utility function that respects ROOT's boundary conventions:
    # - Lower edge INCLUDED: GetXmin() <= x
    # - Upper edge EXCLUDED: x < GetXmax()
    is_inside_per_axis: list[bool] = [is_inside_axis_range(axis, coord) for axis, coord in zip(axes, coordinates)]

    return bin_indices, is_inside_per_axis


def get_closest_histogram_bin_content_by_distance(
    coordinates: Union[list[float], tuple[float, ...], np.ndarray, pd.Series],
    hist: TH1 | TH2 | TH3,
    verbose_level: int = 0,
) -> tuple[int, float, bool]:
    """
    Find the closest bin and its content for a given point in histogram (1D, 2D, or 3D).

    This function handles two main cases:
    1. Point inside histogram range: Returns exact bin content
    2. Point outside histogram range: Finds closest bin using normalized Euclidean distance

    Args:
        coordinates: Actual physical coordinates to lookup (not bin numbers)
                    - (x,) for 1D histograms
                    - (x,y) for 2D histograms
                    - (x,y,z) for 3D histograms
        hist: Input histogram (TH1, TH2, or TH3)
        verbose_level: Level of verbosity for diagnostics (0=silent, 1=info, 2=debug)

    Returns:
        Tuple containing:
        - global_bin (int): ROOT global bin number
        - bin_content (float): Content of the (closest) bin
        - is_inside (bool): True if point was inside valid histogram range

    Raises:
        ValueError: If number of coordinates doesn't match histogram dimension

    Examples:
        >>> # 1D histogram lookup
        >>> bin_num, content, inside = get_closest_histogram_bin_content(hist1d, (2.5,))
        >>>
        >>> # 2D histogram lookup
        >>> bin_num, content, inside = get_closest_histogram_bin_content(hist2d, (1.2, 3.4))
        >>>
        >>> # 3D histogram lookup
        >>> bin_num, content, inside = get_closest_histogram_bin_content(hist3d, (1.2, 3.4, 5.6))
    """

    # Input validation using existing utility function
    validate_histogram(hist)

    # Convert input to tuple of coordinates
    if isinstance(coordinates, pd.Series):
        coordinates = tuple(coordinates.values)
    else:
        coordinates = tuple(coordinates)

    # Check coordinate dimension compatibility
    ndim = hist.GetDimension()
    if len(coordinates) != ndim:
        raise ValueError(f"Coordinate dimension mismatch: got {len(coordinates)} coordinates " f"for {ndim}D histogram '{hist.GetName()}'")

    # Step 1: Get histogram axes for each dimension
    # This creates a list of TAxis objects [X-axis, Y-axis, Z-axis] based on histogram dimension
    axes: list[TAxis] = [hist.GetXaxis()]
    if ndim >= 2:
        axes.append(hist.GetYaxis())
    if ndim == 3:
        axes.append(hist.GetZaxis())

    # Step 2: Get bin indices from the physical coordinates and check if point lies within valid histogram range for ALL dimensions
    # Using existing utility function that respects ROOT's boundary conventions:
    # - Lower edge INCLUDED: GetXmin() <= x
    # - Upper edge EXCLUDED: x < GetXmax()
    bin_indices, is_inside_per_axis = get_bin_indices_from_coordinates(coordinates, hist)

    if all(is_inside_per_axis):

        # Convert multi-dimensional bin indices to global bin number
        # ROOT uses different methods based on histogram dimension
        if ndim == 1:
            global_bin = hist.GetBin(bin_indices[0])
        elif ndim == 2:
            global_bin = hist.GetBin(bin_indices[0], bin_indices[1])
        else:  # ndim == 3
            global_bin = hist.GetBin(bin_indices[0], bin_indices[1], bin_indices[2])

        # Get bin content
        bin_content = get_bin_content_safely(hist, bin_indices)

        return global_bin, bin_content, True

    # Case 2: Point is outside valid histogram range - find closest valid bin
    # Get bin ranges for iteration
    bin_ranges = get_histogram_bin_ranges(hist)

    # Step 3: Prepare for distance calculation with normalization
    # Get axis ranges for normalization to ensure fair distance weighting across dimensions
    axis_ranges: list[float] = []
    for axis in axes:
        axis_range = axis.GetXmax() - axis.GetXmin()
        axis_ranges.append(1 if axis_range == 0 else axis_range)

    # Initialize tracking variables for closest bin search
    min_distance_squared = float('inf')  # Use squared distance to avoid sqrt in loop
    closest_global_bin = -999
    closest_bin_content = 0.0
    closest_indices: tuple[int, ...] = None

    # Loop over all valid bins to find the closest one
    for bin_indices in product(*bin_ranges):
        # Get bin centers for current bin combination
        bin_centers: list[float] = [axis.GetBinCenter(bin_idx) for axis, bin_idx in zip(axes, bin_indices)]

        # Calculate normalized distance
        distance_squared = 0
        for coord, center, axis_range in zip(coordinates, bin_centers, axis_ranges):
            normalized_diff = (coord - center) / axis_range
            distance_squared += normalized_diff * normalized_diff

        # Check if this is the closest bin so far
        if distance_squared < min_distance_squared:
            min_distance_squared = distance_squared
            closest_indices = bin_indices

            # Calculate global bin number for this closest bin
            if ndim == 1:
                closest_global_bin = hist.GetBin(bin_indices[0])
            elif ndim == 2:
                closest_global_bin = hist.GetBin(bin_indices[0], bin_indices[1])
            else:  # ndim == 3
                closest_global_bin = hist.GetBin(bin_indices[0], bin_indices[1], bin_indices[2])

            # Get bin content using existing safe utility function
            closest_bin_content = get_bin_content_safely(hist, bin_indices)

    # Final distance calculation for reporting
    final_distance = math.sqrt(min_distance_squared)

    if verbose_level > 0:
        coord_str = ", ".join([f"{coord:.3f}" for coord in coordinates])
        logger.info(f"Closest bin search completed for point [{coord_str}]:")
        logger.info(f"  → Global bin number: {closest_global_bin}")
        logger.info(f"  → Bin content: {closest_bin_content}")
        logger.info(f"  → Normalized distance: {final_distance:.4f}")

    return closest_global_bin, closest_bin_content, False


# ----------------------------------------------------------------------------------------------------------------------
# Utility Functions for Visualization
# ----------------------------------------------------------------------------------------------------------------------


def get_legend_option_from_draw_option(obj) -> str:
    """
    Determine the appropriate legend option based on histogram draw options and style settings.

    Args:
        obj: ROOT histogram or graph object

    Returns:
        str: Legend option string for ROOT TLegend
    """
    if isinstance(obj, TH1):
        # Get the draw option if available
        draw_option = ""
        try:
            draw_option = obj.GetDrawOption().lower()
        except:
            draw_option = ""

        # Check if markers are set (marker style != 1 which is default "no marker")
        has_markers = obj.GetMarkerStyle() != 1

        # Check if histogram has a fill
        has_fill = obj.GetFillStyle() != 0 and obj.GetFillColor() != 0

        # Check if line is visible (line width > 0 and line color is set)
        has_line = obj.GetLineWidth() > 0 and obj.GetLineColor() != 0

        # Determine legend option based on draw style and object properties
        if "pe" in draw_option or ("p" in draw_option and "e" in draw_option):
            return "lep"  # Line, error bars, and points
        elif "p" in draw_option or has_markers:
            if "e" in draw_option:
                return "lep"  # Line, error bars, and points
            elif has_line:
                return "lp"  # Line and points
            else:
                return "p"  # Points only
        elif "e" in draw_option:
            if has_line:
                return "le"  # Line and error bars
            else:
                return "e"  # Error bars only
        elif "hist" in draw_option:
            return "l"  # Histogram drawn as a line
        elif has_fill:
            return "f"  # Filled histogram
        elif has_line:
            return "l"  # Line
        else:
            # Default: if markers are set, show them; otherwise show line
            return "lp" if has_markers else "l"

    elif isinstance(obj, TGraph):
        draw_option = ""
        try:
            draw_option = obj.GetDrawOption().lower()
        except:
            draw_option = ""

        if "p" in draw_option:
            return "p"  # Graph with markers
        elif "l" in draw_option:
            return "l"  # Graph with a line
        elif "f" in draw_option:
            return "f"  # Filled graph
        else:
            return "lp"  # Default to line and marker

    # Default fallback
    return "l"


def calculate_y_axis_range(histos: list[TH1 | TH2 | TH3], y_range_factor: float = 1.0) -> tuple[float, float]:
    """
    Calculate the Y-axis range for a set of histograms.

    Args:
        histos: A list of histograms or a single histogram
        y_range_factor: Factor to scale the y-axis range. 1.0 means no scaling

    Returns:
        tuple: A tuple containing the minimum and maximum Y-axis values

    Raises:
        ValueError: If 'histos' is empty or contains invalid elements
    """
    if not isinstance(histos, list):
        histos = [histos]
    if not histos or any(not hasattr(h, 'GetMinimum') for h in histos):
        raise ValueError("Invalid input: 'histos' must be a list of histograms.")

    y_min = min(h.GetMinimum() for h in histos)
    y_max = max(h.GetMaximum() for h in histos)

    if np.isinf(y_min) or np.isinf(y_max):
        raise ValueError("Could not determine valid y-axis range")

    if y_range_factor:
        y_min = max(y_min, 0) if y_min >= 0 else y_min * y_range_factor
        y_max *= y_range_factor

    return (y_min, y_max)


def get_unique_hist_name(target_name: str) -> str:
    """
    Generate a unique name for a histogram by checking for existing objects.

    Args:
        target_name: Desired histogram name

    Returns:
        str: Unique histogram name
    """
    attempt = 0
    while gROOT.FindObject(target_name):
        attempt += 1
        timestamp = datetime.now().strftime('%S%f')
        target_name = f"{target_name}_{attempt}_{timestamp}"
        logger.info(f"Object with name {target_name.rsplit('_', 2)[0]} already exists.")

    logger.info(f"Using {target_name} as the histogram name.")

    return target_name


def define_plots_nx_ny(nplots: int) -> list[int]:
    """
    Calculate optimal canvas division for given number of plots.

    Args:
        nplots: Number of plots to arrange

    Returns:
        list[int]: [nx, ny] dimensions for canvas division
    """
    nx: int = int(math.sqrt(nplots)) if (nplots > 3) else nplots
    ny: int = math.ceil(nplots / nx)

    return [nx, ny]


################################ ! ################################################################################################


# ----------------------------------------------------------------------------------------------------------------------
# Draw the comparison of histograms
# ----------------------------------------------------------------------------------------------------------------------


def draw_histo_comparison(
    h_ref: list,
    h_cmp: list,
    output_file: str,
    rp_type: str = 'divsym',
    legend_ref: str = '',
    legend_cmp: str = '',
    normalize_opt: int = 1,
) -> None:
    """
    Draw comparison of histograms with ratio plots.

    Args:
        h_ref: List of reference histograms, the errors are used from these histograms
        h_cmp: List of comparison histograms (should be in the same order as h_ref). The errors from these histograms are not used
        output_file: Path to save the output file
        rp_type: Type of ratio plot. Options: 'divsym', 'diff', 'diffsig'
        legend_ref: Legend entry for reference histograms
        legend_cmp: Legend entry for comparison histograms
        normalize_opt: Normalization option. 0: no normalization; 1: normalize all histograms to 1; 2: normalize comparison histograms to reference histograms

    Raises:
        AssertionError: If input validation fails
    """

    # rp_type: []"divsym", "diff", "diffsig"]
    # normalize_opt. 0: no normalization; 1: normalize all histograms to 1; 2: normalize the comparison histograms to the reference histograms accordingly.

    # Input validation
    h_ref = h_ref if isinstance(h_ref, list) else [h_ref]
    h_cmp = h_cmp if isinstance(h_cmp, list) else [h_cmp]

    assert len(h_ref) == len(h_cmp), f"The number of reference histograms and comparison histograms should be the same."
    assert rp_type in {"divsym", "diff", "diffsig"}, "Invalid ratio plot type."
    assert normalize_opt in {0, 1, 2}, "Invalid normalization option."

    # Create a canvas and divide it based on the number of histograms
    c1 = TCanvas("canvas", "canvas", 950 * len(h_ref), 800)

    nx, ny = define_plots_nx_ny(len(h_ref))
    c1.Divide(nx, ny)

    # List to keep ratio plots in scope
    ratio_plots = []

    for i, h1 in enumerate(h_ref):
        c1.cd(i + 1)
        h2 = h_cmp[i]

        # Rebin the histograms of h2 to the binning of h1
        if h1.GetNbinsX() != h2.GetNbinsX():
            logger.warning(f"Rebinning {h2.GetName()} to the binning of {h1.GetName()}")
            x_axis = h1.GetXaxis()
            if x_axis.GetXbins().GetSize() > 0:  # Variable binning
                h2 = h2.Rebin(h1.GetNbinsX(), f'{h2.GetName()}_rebin', x_axis.GetXbins().GetArray())
            else:  # Uniform binning
                rebin_factor = h2.GetNbinsX() // h1.GetNbinsX()
                if h2.GetNbinsX() % h1.GetNbinsX() == 0:
                    h2 = h2.Rebin(rebin_factor, f'{h2.GetName()}_rebin')
                else:
                    raise ValueError("Cannot rebin: bin counts are incompatible")

        # Ensure bin limits match
        assert h1.GetXaxis().GetXmin() == h2.GetXaxis().GetXmin(), f"{h1.GetName()} and {h2.GetName()} have different bin left limits"
        assert h1.GetXaxis().GetXmax() == h2.GetXaxis().GetXmax(), f"{h1.GetName()} and {h2.GetName()} have different bin right limits"

        # Print out all bin limits
        # import numpy as np
        # rprint(f'--- {h1.GetName()} ---')
        # rprint(np.array([h1.GetXaxis().GetBinLowEdge(i) for i in range(1, h1.GetNbinsX() + 2)]))
        # rprint(f'--- {h2.GetName()} ---')
        # rprint(np.array([h2.GetXaxis().GetBinLowEdge(i) for i in range(1, h2.GetNbinsX() + 2)]))

        # Normalize the histograms
        if normalize_opt == 1:
            h1.Scale(1.0 / h1.Integral())
            h2.Scale(1.0 / h2.Integral())
        elif normalize_opt == 2:
            h2.Scale(h1.Integral() / h2.Integral())

        # Set the line color
        h1.SetLineColor(r.kRed)
        h2.SetLineColor(r.kBlue)

        # Create and configure ratio plot
        rp = TRatioPlot(h1, h2, rp_type)  #  "divsym", "diff", "diffsig"

        rp.SetH1DrawOpt("E1")
        rp.SetH2DrawOpt("E1")

        # h1.GetXaxis().SetTitle("x")
        # h1.GetYaxis().SetTitle("y")

        # c1.SetTicks(0, 1)
        # rp.SetLeftMargin(0.05)
        rp.SetRightMargin(0.03)
        # rp.SetUpTopMargin(0.05)
        # rp.SetLowBottomMargin(0.05)
        rp.GetLowYaxis().SetNdivisions(505)
        rp.SetSeparationMargin(0.0)

        # Draw lines in the ratio plot
        lines = [0]
        if rp_type == "divsym":
            lines = [1]
        elif rp_type == "diffsig":
            lines = [3, -3]
        rp.SetGridlines(lines)

        ratio_plots.append(rp)
        rp.SetGraphDrawOpt("LE0")

        rp.Draw()
        # rp.GetUpperRefObject.SetTitle(f'{h_ref[dim]["title"]}; {h_ref[dim]["unit"]}')

        # Configure y-axis titles and ranges
        rp.GetUpperRefYaxis().SetTitle("p.d.f.")
        rp.GetUpperRefYaxis().SetRangeUser(0, max(h1.GetMaximum(), h2.GetMaximum()) * 1.1)

        # Set the y axis title of the ratio plot
        title_ratio = "ratio" if rp_type == "divsym" else "difference" if rp_type == "diff" else "pull"
        rp.GetLowerRefYaxis().SetTitle(title_ratio)

        # Set the y range of the lower plot
        if rp_type == "divsym":
            rp.GetLowerRefGraph().SetMinimum(0)
            rp.GetLowerRefGraph().SetMaximum(3)
            # pass
        elif rp_type == "diffsig":
            rp.GetLowerRefGraph().SetMinimum(-5)
            rp.GetLowerRefGraph().SetMaximum(5)

        # Add legend
        rp.GetUpperPad().cd()
        legend = TLegend(0.65, 0.75, 0.98, 0.90)
        legend_ref = legend_ref or h1.GetName()
        legend_cmp = legend_cmp or h2.GetName()
        legend.AddEntry(h1, legend_ref, "lpe")
        legend.AddEntry(h2, legend_cmp, "lpe")

        # Add legend to the plotable
        rp.GetUpperRefObject().GetListOfFunctions().Add(legend)

    # Update canvas and turn off stats box
    c1.Update()

    # Turn off stats box
    gStyle.SetOptStat(0)

    # Save the canvas
    output_file = str(Path(output_file).resolve())
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    c1.SaveAs(output_file)

    # Close the canvas
    c1.Close()


def create_histogram_projections(
    input_histo: TH1 | TH2 | TH3,
    histo_name: str,
    normalize: bool = True,
) -> tuple[dict[int, TH1], list[TH1 | TH2 | TH3]]:
    """
    Create projections of a histogram along each dimension.

    For multi-dimensional histograms (2D, 3D), creates 1D projections along each axis.
    For 1D histograms, returns the histogram itself.

    Args:
        input_histo: ROOT histogram to process (TH1, TH2, or TH3)
        histo_name: Name to use for projection naming
        normalize: Whether to normalize projections to unit integral

    Returns:
        tuple containing:
            - Dictionary mapping dimension index to projection histogram:
                Format: {0: x_projection, 1: y_projection, 2: z_projection}
            - List of created projection objects that need cleanup (empty for 1D)

    Raises:
        TypeError: If input is not a valid histogram

    Example:
        >>> projections, cleanup_list = create_histogram_projections(hist2d, 'signal', normalize=True)
        >>> x_proj = projections[0]  # X projection
        >>> y_proj = projections[1]  # Y projection
        >>> # Clean up later: for proj in cleanup_list: proj.Delete()
    """
    # Validate input
    validate_histogram(input_histo)

    ndim = input_histo.GetDimension()

    # Dimension mapping for projections
    dim_map: dict[int, str] = {0: 'X', 1: 'Y', 2: 'Z'}

    projections: dict[int, TH1] = {}
    projections_to_cleanup: list[TH1 | TH2 | TH3] = []

    # Create projections for each dimension
    for i_dim in range(ndim):
        if ndim > 1:
            proj_name = f'{input_histo.GetName()}_{dim_map[i_dim]}_proj_{histo_name}'
            proj = input_histo.__getattribute__(f'Projection{dim_map[i_dim]}')(proj_name)
            proj.SetDirectory(0)  # Detach from file
            projections[i_dim] = proj
            projections_to_cleanup.append(proj)
        else:
            # For 1D histograms, just use the histogram itself (no projection needed)
            projections[i_dim] = input_histo

        # Normalize if requested
        if normalize:
            integral = projections[i_dim].Integral()
            if integral > 0:
                projections[i_dim].Scale(1.0 / integral)
            else:
                logger.warning(f"Histogram '{histo_name}' dimension {i_dim} has zero integral, " f"skipping normalization")

    return projections, projections_to_cleanup


def draw_histo_comparison_no_pulls(
    input_histos: list[TH1 | TH2 | TH3],
    histo_names: list[str],
    output_pic: str,
    histo_draw_options: Optional[list[str]] = None,
    normalize: bool = True,
    set_y_min: Optional[float] = None,
    legend_labels: Optional[list[str]] = None,
    canvas_width: int = 950,
    canvas_height: int = 800,
    legend_position: tuple[float, float, float, float] = (0.68, 0.72, 0.95, 0.95),
    y_range_factor: float = 1.3,
    y_title: str = None,
) -> None:
    """
    Draw histogram comparisons without pull plots, supporting 1D, 2D, and 3D histograms.

    Args:
        input_histos: List of ROOT histograms to compare
        histo_names: List of names for each histogram (must match input_histos length), to be used for the projection names, and be used for the legend labels if not provided
        output_pic: Output file path for the saved plot
        histo_draw_options: List of ROOT draw options for each histogram, e.g. ['PE0', 'HIST SAME']
        normalize: Whether to normalize histograms to unit integral
        set_y_min: Minimum y-axis value (overrides automatic range)
        legend_labels: Custom legend labels (defaults to histo_names)
        canvas_width: Canvas width per dimension
        canvas_height: Canvas height
        legend_position: Legend position as (x1, y1, x2, y2)
        y_range_factor: Factor to scale the y-axis range. 1.0 means no scaling
        y_title: Y-axis title for the plot

    Raises:
        ValueError: If input validation fails
        RuntimeError: If histogram operations fail
    """
    # Input validation and normalization
    if not input_histos:
        raise ValueError("input_histos cannot be empty")

    input_histos = input_histos if isinstance(input_histos, list) else [input_histos]
    histo_names = histo_names if isinstance(histo_names, list) else [histo_names]

    if len(input_histos) != len(histo_names):
        raise ValueError(f'Number of histograms ({len(input_histos)}) does not match number of names ({len(histo_names)})')

    # Validate all histograms have the same dimension
    ndim = input_histos[0].GetDimension()
    if not all(h.GetDimension() == ndim for h in input_histos):
        raise ValueError("All histograms must have the same dimension")

    # Handle draw options
    if histo_draw_options is None:
        histo_draw_options = ['PE0'] + ['HIST SAME'] * (len(input_histos) - 1)
    else:
        histo_draw_options = histo_draw_options if isinstance(histo_draw_options, list) else [histo_draw_options] * len(input_histos)

        if len(input_histos) != len(histo_draw_options):
            raise ValueError(f'Number of histograms ({len(input_histos)}) does not match number of draw options ({len(histo_draw_options)})')

        # Ensure subsequent options include SAME
        for i in range(1, len(histo_draw_options)):
            if 'SAME' not in histo_draw_options[i].upper():
                histo_draw_options[i] = f'{histo_draw_options[i]} SAME'

    # Extended color palette
    COLORS = [r.kBlack, r.kBlue, r.kRed, r.kGreen, r.kMagenta, r.kOrange, r.kCyan, r.kYellow, r.kPink, r.kSpring, r.kTeal, r.kAzure]

    if len(input_histos) > len(COLORS):
        # Generate additional colors by cycling through with different styles
        for i in range(len(COLORS), len(input_histos)):
            COLORS.append(COLORS[i % len(COLORS)])

    # Create working copies and projections
    histos: dict[str, dict[str, TH1 | TH2 | TH3]] = {}
    projections_to_cleanup: list[TH1 | TH2 | TH3] = []  # Track projections for cleanup

    try:
        for i, (name, h) in enumerate(zip(histo_names, input_histos)):
            # Create a working copy to avoid modifying originals
            h_copy = h.Clone(f"{h.GetName()}_working_{i}")
            h_copy.SetDirectory(0)  # Detach from file

            # Use the extracted function to create projections
            projections, cleanup_list = create_histogram_projections(
                input_histo=h_copy,
                histo_name=name,
                normalize=normalize,
            )

            histos[name] = projections
            projections_to_cleanup.extend(cleanup_list)

            # Store the working copy for later cleanup
            if h_copy not in projections.values():
                projections_to_cleanup.append(h_copy)

        # Create canvas
        c1 = TCanvas('c1', 'Histogram Comparison', ndim * canvas_width, canvas_height)
        c1.Divide(ndim, 1)

        def _set_histogram_style(h: TH1, color: int, y_range: Optional[tuple] = None) -> None:
            """Apply consistent styling to histogram."""
            h.GetYaxis().SetLabelSize(0.045)
            h.GetXaxis().SetLabelSize(0.045)
            h.GetXaxis().SetTitleSize(0.045)
            # h.SetMarkerStyle(20)
            h.SetMarkerSize(0.8)
            h.SetLineColor(color)
            h.SetMarkerColor(color)

            if y_range:
                h.GetYaxis().SetRangeUser(*y_range)

        # Draw histograms for each dimension
        for i_dim in range(ndim):
            c1.cd(i_dim + 1)

            # Calculate y-axis range for this dimension
            dim_histos = [histos[name][i_dim] for name in histos]
            y_range = calculate_y_axis_range(dim_histos, y_range_factor=y_range_factor)

            # Override minimum if specified
            if set_y_min is not None:
                y_range = (set_y_min, y_range[1])

            # Draw each histogram
            for j, name in enumerate(histos):
                h = histos[name][i_dim]
                _set_histogram_style(h, COLORS[j], y_range)

                if y_title:
                    h.GetYaxis().SetTitle(y_title)
                else:
                    if not h.GetYaxis().GetTitle():
                        if normalize:
                            h.GetYaxis().SetTitle('p.d.f.')
                        else:
                            h.GetYaxis().SetTitle('a.u.')

                # h.GetYaxis().SetTitleOffset(1.55)

                h.Draw(histo_draw_options[j])

        # Add legend to first pad
        c1.cd(1)
        legend = TLegend(*legend_position)
        legend.SetBorderSize(1)
        legend.SetFillStyle(1001)
        legend.SetFillColor(0)

        # Use custom labels if provided, otherwise use histo names
        labels = legend_labels if legend_labels else histo_names
        if len(labels) != len(histos):
            raise ValueError(f'Number of legend labels ({len(labels)}) does not match number of histograms ({len(histos)})')

        for i, (name, label) in enumerate(zip(histos.keys(), labels)):
            h = histos[name][0]  # Use first dimension for legend
            legend_option = get_legend_option_from_draw_option(h)
            legend.AddEntry(h, label, legend_option)

        legend.Draw()

        # Configure global settings
        gStyle.SetOptTitle(1)  # Enable titles
        gStyle.SetOptStat(0)
        c1.Update()

        # Save output
        output_pic = str(Path(output_pic).resolve())
        Path(output_pic).parent.mkdir(parents=True, exist_ok=True)
        c1.SaveAs(output_pic)

        logger.info(f"Plot saved to: {output_pic}")

    except Exception as e:
        raise RuntimeError(f"Failed to create histogram comparison: {e}")

    finally:

        # Cleanup
        c1.Close()


def draw_2d_histogram(
    hist: TH2,
    output_file: str,
    *,
    draw_option: str = "COLZ",
    canvas_width: int = 950,
    canvas_height: int = 800,
    title: str = None,
    x_title: str = None,
    y_title: str = None,
    z_title: str = None,
    z_min: float = None,
    z_max: float = None,
    log_z: bool = False,
    palette: int = None,
    left_margin: float = 0.12,
    right_margin: float = 0.18,
    top_margin: float = 0.08,
    bottom_margin: float = 0.12,
    palette_y1_offset: float = 0.0,
    palette_y2_offset: float = 0.0,
    show_stats: bool = False,
) -> None:
    """
    Draw a 2D histogram using ROOT with configurable options.

    Args:
        hist: ROOT TH2 histogram to draw
        output_file: Path to save the output file (supports .pdf, .png, .root, etc.)
        draw_option: ROOT draw option (default: "COLZ")
        canvas_width: Canvas width in pixels
        canvas_height: Canvas height in pixels
        title: Histogram title (overrides existing title if provided)
        x_title: X-axis title (overrides existing if provided)
        y_title: Y-axis title (overrides existing if provided)
        z_title: Z-axis (color bar) title (overrides existing if provided)
        z_min: Minimum value for z-axis (color scale)
        z_max: Maximum value for z-axis (color scale)
        log_z: Use logarithmic z-axis scale
        palette: ROOT color palette number (e.g., 1 for default, 57 for kBird)
        left_margin: Left margin fraction
        right_margin: Right margin fraction (for color palette)
        top_margin: Top margin fraction
        bottom_margin: Bottom margin fraction
        palette_y1_offset: Offset to raise palette bottom
        palette_y2_offset: Offset to lower palette top
        show_stats: Whether to show the statistics box

    Raises:
        TypeError: If input is not a TH2 histogram
        ValueError: If histogram is not 2D
    """
    # Validate input
    if not isinstance(hist, TH2):
        raise TypeError(f"Input must be a TH2 histogram, got {type(hist)}")

    if hist.GetDimension() != 2:
        raise ValueError(f"Expected 2D histogram, got {hist.GetDimension()}D")

    # Create canvas
    canvas_name = f"c_{hist.GetName()}_{random.randint(1000, 9999)}"
    c1 = TCanvas(canvas_name, hist.GetTitle(), canvas_width, canvas_height)

    # Set margins - right margin must be large enough for palette
    c1.SetLeftMargin(left_margin)
    c1.SetRightMargin(right_margin)
    c1.SetTopMargin(top_margin)
    c1.SetBottomMargin(bottom_margin)

    # Set log scale if requested
    if log_z:
        c1.SetLogz(1)

    # Set color palette if specified
    if palette is not None:
        gStyle.SetPalette(palette)

    # Configure stats box
    gStyle.SetOptStat(1 if show_stats else 0)

    # Clone histogram to avoid modifying original
    h_draw = hist.Clone(f"{hist.GetName()}_draw")
    h_draw.SetDirectory(0)

    # Set titles if provided
    if title is not None:
        h_draw.SetTitle(title)
    if x_title is not None:
        h_draw.GetXaxis().SetTitle(x_title)
    if y_title is not None:
        h_draw.GetYaxis().SetTitle(y_title)
    if z_title is not None:
        h_draw.GetZaxis().SetTitle(z_title)

    # Set z-axis range if provided
    if z_min is not None:
        h_draw.SetMinimum(z_min)
    if z_max is not None:
        h_draw.SetMaximum(z_max)

    # Style adjustments
    h_draw.GetXaxis().SetTitleOffset(1.1)
    h_draw.GetYaxis().SetTitleOffset(1.3)
    h_draw.GetZaxis().SetTitleOffset(1.3)

    h_draw.GetXaxis().SetLabelSize(0.04)
    h_draw.GetYaxis().SetLabelSize(0.04)
    h_draw.GetZaxis().SetLabelSize(0.04)

    h_draw.GetXaxis().SetTitleSize(0.045)
    h_draw.GetYaxis().SetTitleSize(0.045)
    h_draw.GetZaxis().SetTitleSize(0.045)

    # Draw histogram
    h_draw.Draw(draw_option)

    # Update canvas FIRST to create the palette axis
    c1.Update()

    # Reposition the palette axis to avoid overlap
    # The palette is stored in the histogram's list of functions after drawing
    palette_axis = h_draw.GetListOfFunctions().FindObject("palette")
    if palette_axis:
        # Position palette: X1, Y1, X2, Y2 in NDC coordinates
        # Place it in the right margin area, not overlapping with plot
        palette_axis.SetX1NDC(1.0 - right_margin + 0.02)
        palette_axis.SetX2NDC(1.0 - right_margin + 0.05)
        palette_axis.SetY1NDC(bottom_margin + palette_y1_offset)
        palette_axis.SetY2NDC(1.0 - top_margin - palette_y2_offset)


    # Update again after repositioning
    c1.Modified()
    c1.Update()

    # Save output
    output_file = str(Path(output_file).resolve())
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    c1.SaveAs(output_file)

    logger.info(f"2D histogram saved to: {output_file}")

    # Cleanup
    c1.Close()
