'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-03-06 19:04:11 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-04-08 04:40:28 +0200
FilePath     : compare_data_with_errorbar.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
from copy import deepcopy

from uncertainties import ufloat, unumpy
from dataclasses import dataclass, field
from typing import List
from rich import print as rprint

# import mplhep as hep
# from .utils import adjust_color


# hist_colors = {0: 'red', 1: 'black', 2: 'blue', 3: 'green', 4: 'magenta', 5: 'cyan', 6: 'yellow', 7: 'white'}

hist_colors = {
    0: 'red',
    1: '#E69F00',  # Orange
    2: 'black',
    3: '#56B4E9',  # Sky Blue
    4: '#009E73',  # Bluish Green
    5: '#F0E442',  # Yellow
    6: '#0072B2',  # Blue
    7: '#D55E00',  # Vermillion
    8: '#CC79A7',  # Reddish Purple
}
hist_fmt = {0: 'o', 1: 's', 2: 'x', 3: 'D', 4: 'p', 5: 'H', 6: 'P', 7: '*'}

matplotlib.use('Agg')  # or 'TkAgg' want interactive


@dataclass
class PlotElement:
    """
    A container holding arrays for x-positions, y-positions, and different
    error components for each dataset we will plot.
    Each 'list[...]' entry corresponds to one data set in the final plot.
    """

    x_positions: List[np.ndarray] = field(default_factory=list)
    y_positions: List[np.ndarray] = field(default_factory=list)
    statistical_errors: List[np.ndarray] = field(default_factory=list)
    systematic_errors: List[np.ndarray] = field(default_factory=list)
    combined_errors: List[np.ndarray] = field(default_factory=list)

    # Optionally storing scaled errors (e.g. if we want separate error bars for stat vs. syst):
    statistical_errors_scaled: List[np.ndarray] = field(default_factory=list)
    systematic_errors_scaled: List[np.ndarray] = field(default_factory=list)


# ---------------------------------------------------------------------
# Helper: Prepare data for plotting, applying shift or shift+project logic
# ---------------------------------------------------------------------
def prepare_plot_elements(
    x_labels: list,
    stat_ufloats_lists: list,  # The main data sets, each a list (or array) of ufloats (val ± stat_err).
    syst_ufloats_lists: list = None,  # Additional error term in each bin (often systematic).
    option: str = 'compareRawValues',
    shift_x: float = 0.05,
) -> PlotElement:
    """
    Prepares the data to be plotted, applying different transformations based on `option`.

    :param x_labels: The 'labels' or categories on the x-axis (one for each bin).
    :param stat_ufloats_lists: A list of arrays, where each array is a set of ufloat(...) values
                           representing (central_value ± stat_error).
                           Example shape: [dataset0, dataset1, ...], each dataset an array of ufloats.
    :param syst_ufloats_lists: A list of arrays, same shape as stat_ufloats_lists, with
                                      additional (systematic) uncertainties. If None, we treat them as zero.
    :param option: One of:
       1) 'compareRawValues' => plot the data as-is,
       2) 'shiftToBaseline' => subtract the first dataset's nominal from each subsequent dataset,
       3) 'shiftToBaseline_and_projectToSigmaPlane' => also skip plotting the first dataset,
          and convert the difference to "sigma units" by dividing (val - ref) / combined_error.
    :param shift_x: A small offset so we can shift each data set horizontally to avoid overlapping.

    :return: PlotElement containing arrays for each data set we decide to keep (possibly skipping the first set
             for the sigma-plane approach).
    """

    # Create an empty container for the results

    PE = PlotElement()

    # If user didn’t specify the second set of ufloats for systematic errors, build zero placeholders
    if syst_ufloats_lists is None:
        syst_ufloats_lists = [np.array([ufloat(0, 0) for _ in arr]) for arr in stat_ufloats_lists]
    else:
        syst_ufloats_lists = deepcopy(syst_ufloats_lists)

    # Possibly define a reference set for “shiftToNominal” logic:
    ref_stat_ufloats = None
    ref_syst_ufloats = None
    if ('shiftToBaseline' in option) and len(stat_ufloats_lists) > 0:
        ref_stat_ufloats = np.array(stat_ufloats_lists[0])
        ref_syst_ufloats = np.array(syst_ufloats_lists[0])

    # Now iterate over each data set
    for i, (main_uf_arr, addi_uf_arr) in enumerate(zip(stat_ufloats_lists, syst_ufloats_lists)):

        # If in “shiftToNominal_and_projectToSigmaPlane”, skip the first dataset
        if ('shiftToBaseline' in option) and (i == 0):
            continue

        # X positions are offset slightly to avoid overlap
        x_positions = np.arange(len(x_labels)) + (-shift_x * (len(stat_ufloats_lists) - 1) / 2 + shift_x * i)

        # Convert from ufloat to numeric arrays (nominal and error)
        main_values = np.array([val.n for val in main_uf_arr])  # central values
        main_errors = np.array([val.s for val in main_uf_arr])  # typically stat. error

        addi_values = np.array([val.n for val in addi_uf_arr])  # additional (syst) nominal, rarely used
        addi_errors = np.array([val.s for val in addi_uf_arr])  # additional (syst) error

        # Combine the main+addi arrays to get total uncertainty
        total_uf_arr = np.array(main_uf_arr) + np.array(addi_uf_arr)
        total_errors = np.array([val.s for val in total_uf_arr])

        # SHIFT/PROJECT logic
        if ref_stat_ufloats is not None:
            # Subtract reference set’s nominal
            main_values = main_values - np.array([rval.n for rval in ref_stat_ufloats])
            addi_values = addi_values - np.array([rval.n for rval in ref_syst_ufloats])

            if option == 'shiftToBaseline_and_projectToSigmaPlane':
                # Recompute the difference in errors
                main_diff_errs = np.array([(m - r).s for (m, r) in zip(main_uf_arr, ref_stat_ufloats)])
                addi_diff_errs = np.array([(m - r).s for (m, r) in zip(addi_uf_arr, ref_syst_ufloats)])
                total_errors = np.sqrt(main_diff_errs**2 + addi_diff_errs**2)

                # Convert difference to sigma units
                safe_total = np.where(total_errors == 0, 1e-15, total_errors)
                main_values = main_values / safe_total
                # in sigma-plane, the total error is 1.0
                total_errors = np.ones_like(main_values)

        # Now define a scale factor if we want to separately draw “stat” vs “syst”:
        denominator = main_errors + addi_errors
        safe_denom = np.where(denominator == 0, 1e-15, denominator)
        scale_factor = total_errors / safe_denom

        # Then the “statistical_errors_scaled” is main_errors * scale_factor, etc.
        scaled_stat_errs = main_errors * scale_factor
        scaled_syst_errs = addi_errors * scale_factor

        # Finally store everything in the PlotElement
        PE.x_positions.append(x_positions)
        PE.y_positions.append(main_values)
        PE.statistical_errors.append(main_errors)
        PE.systematic_errors.append(addi_errors)
        PE.combined_errors.append(total_errors)
        PE.statistical_errors_scaled.append(scaled_stat_errs)
        PE.systematic_errors_scaled.append(scaled_syst_errs)

    return PE


# ---------------------------------------------------------------------
# Helpers: Chi2 computations for a single bin
# ---------------------------------------------------------------------
def compute_chi2_bin_weighted_avg(
    y_values: np.ndarray,
    y_errors: np.ndarray,
) -> float:
    """
    Weighted-average approach for chi2 across multiple datasets in one bin:
      1) Weighted average => w_i=1/err_i^2
      2) sum((y_i - avg)^2 / err_i^2)
    """
    if len(y_values) <= 1:
        return 0.0
    safe_errs = np.where(y_errors == 0, 1e-15, y_errors)
    weights = 1.0 / (safe_errs**2)
    wavg = np.sum(y_values * weights) / np.sum(weights)
    chi2 = np.sum(((y_values - wavg) ** 2) / (safe_errs**2))
    return chi2


def compute_chi2_bin_baseline(
    baseline_val: float,
    baseline_err: float,
    y_values: np.ndarray,
    y_errors: np.ndarray,
) -> float:
    """
    Baseline approach: sum_i( (y_i - baseline)^2 / (err_i^2 + baseline_err^2) ).
    Typically skip the baseline's own bin if you want.
    """
    if len(y_values) < 1:
        return 0.0
    safe_errs = np.where(y_errors == 0, 1e-15, y_errors)
    # Combine baseline's error in quadrature
    denom = safe_errs**2 + baseline_err**2
    chi2 = np.sum(((y_values - baseline_val) ** 2) / denom)
    return chi2


def compute_bin_chi2_for_mode(
    bin_index: int,
    yvals_bin: np.ndarray,
    yerrs_bin: np.ndarray,
    orig_idx_bin: np.ndarray,
    chi2_mode: str,
    baseline_dataset=None,
    baseline_syst=None,
) -> float:
    """
    Decide how to compute the chi2 for a single bin
    based on the chi2_mode: 'weighted_average', 'no_baseline', or 'baseline'.

    :param bin_index: integer specifying which bin we're on.
    :param yvals_bin: array of y-values from all plotted datasets in this bin.
    :param yerrs_bin: array of combined errors for each dataset in this bin.
    :param orig_idx_bin: which *original* dataset index each entry belongs to
    :param chi2_mode: 'weighted_average', 'baseline', 'no_baseline'
    :param baseline_dataset: (optional) if 'baseline' mode is used
    :param baseline_syst: (optional) if 'baseline' mode is used
    """
    # If not enough points, return zero
    if len(yvals_bin) < 2:
        return 0.0

    if chi2_mode == 'weighted_average':
        chi2_val = compute_chi2_bin_weighted_avg(yvals_bin, yerrs_bin)

    elif chi2_mode == 'no_baseline':
        # Weighted-average approach but skip dataset0 if present
        mask = orig_idx_bin != 0
        yvals_bin_nobase = yvals_bin[mask]
        yerrs_bin_nobase = yerrs_bin[mask]
        if len(yvals_bin_nobase) > 1:
            chi2_val = compute_chi2_bin_weighted_avg(yvals_bin_nobase, yerrs_bin_nobase)
        else:
            chi2_val = 0.0

    elif chi2_mode == 'baseline':
        # Compare each dataset to the first dataset (index=0) for that bin
        if baseline_dataset is None or bin_index >= len(baseline_dataset):
            return 0.0
        # get baseline
        b_nom = baseline_dataset[bin_index].n
        b_err = baseline_dataset[bin_index].s
        if baseline_syst is not None and bin_index < len(baseline_syst):
            b_err = np.sqrt(b_err**2 + baseline_syst[bin_index].s ** 2)

        # filter out dataset0 from the sum
        mask = orig_idx_bin != 0
        yvals_bin_b = yvals_bin[mask]
        yerrs_bin_b = yerrs_bin[mask]

        chi2_val = 0.0
        for val_i, err_i in zip(yvals_bin_b, yerrs_bin_b):
            safe_e2 = err_i**2 + b_err**2
            if safe_e2 < 1e-15:
                safe_e2 = 1e-15
            chi2_val += (val_i - b_nom) ** 2 / safe_e2

    else:
        raise ValueError(f"Unknown chi2_mode: {chi2_mode}")

    return chi2_val


# ---------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------
def compare_data_with_errorbar(
    x_labels: list,
    stat_ufloats_lists: list,  # e.g. [ array_of_ufloats (N bins), array_of_ufloats (N bins), ... ]
    syst_ufloats_lists: list = None,  # e.g. same shape, for systematic errors
    labels: list = None,
    xlabel: str = None,
    ylabel: str = 'Y Label',
    title: str = '',
    option: str = 'compareRawValues',
    y_limits: tuple = None,
    draw_axhline: float = None,
    draw_grid: bool = True,
    connect_points: bool = False,
    shift_x: float = 0.05,
    output_file: str = None,
    # to show chi2 in each bin
    show_chi2: bool = False,
    chi2_mode: str = 'baseline',
):
    """
    Compare multiple data sets with error bars, optionally shifting or projecting data.

    :param x_labels: The x-axis categories or bin labels.
    :param stat_ufloats_lists: Each element is an array of ufloats representing (value ± statErr).
    :param syst_ufloats_lists: Additional errors in the same shape. If None, treat as zero.
    :param labels: A list of strings, one per data set. If None, auto-generate.
    :param xlabel: x-axis label
    :param ylabel: y-axis label
    :param title: title string
    :param option: 'compareRawValues', 'shiftToNominal', or 'shiftToNominal_and_projectToSigmaPlane'.
    :param y_limits: If provided, a (ymin, ymax) to set the axis range.
    :param draw_axhline: If not None, draw a horizontal line at that y-value.
    :param draw_grid: Whether to enable the background grid
    :param connect_points: If True, plot a line connecting points. If False, just markers.
    :param shift_x: A small horizontal offset for each data set in the same bin
    :param output_file: If provided, path to save the plot as a file (png, pdf, etc).
    :param show_chi2: if True, compute chi2 among the plotted points in each bin
    :param chi2_mode: 'weighted_average','baseline','no_baseline'.
                    If use weighted_average, it will calculate the chi2 with the weighted average of the plotted points in each bin, use this value as the reference.
                    If use baseline, it will calculate the chi2 with the first dataset as the baseline in each bin for reference.
                    If use no_baseline, it will calculate the chi2 with the weighted average of the plotted points in each bin, but skip the first dataset. And the reference is the weighted average of the rest datasets.
                    Default is 'baseline'.
    """

    # Check input file lengths
    assert len(x_labels) == len(stat_ufloats_lists[0]), f'Length mismatch: {len(x_labels)} vs {len(stat_ufloats_lists[0])}'

    assert option in {'compareRawValues', 'shiftToBaseline', 'shiftToBaseline_and_projectToSigmaPlane'}
    assert chi2_mode in {'baseline', 'weighted_average', 'no_baseline'}, "Unsupported chi2_mode."

    # If user didn’t specify label names, generate
    if labels is None:
        labels = [f"DataSet_{i}" for i in range(len(stat_ufloats_lists))]

    # Step 1: Build the PlotElement structure that transforms data if necessary
    PE = prepare_plot_elements(
        x_labels,
        stat_ufloats_lists,
        syst_ufloats_lists,
        option=option,
        shift_x=shift_x,
    )

    # Create a matplotlib figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # If we do "shiftToBaseline_and_projectToSigmaPlane", we skip the first dataset in the results
    # So the number of items in PE might be len(stat_ufloats_lists) minus 1
    skip_first = 'shiftToBaseline' in option

    # We'll plot each item in PlotElement arrays
    # The index i_data enumerates them in the new list
    for i_data in range(len(PE.x_positions)):
        # The label index should skip the first label if skip_first
        i_label = i_data if not skip_first else (i_data + 1)

        # If i_label >= len(labels), we fallback or build a placeholder
        label_str = labels[i_label] if i_label < len(labels) else f"Data_{i_label}"

        xpos = PE.x_positions[i_data]
        ypos = PE.y_positions[i_data]
        err_comb = PE.combined_errors[i_data]

        # Decide the line/marker format
        # E.g. "o-", "s-", "x--", or just "o" if not connecting points
        fmt_style = f'{hist_fmt.get(i_label, "o")}-' if connect_points else hist_fmt.get(i_label, "o")
        ccolor = hist_colors.get(i_label, 'black')

        # Plot total error bars
        ax.errorbar(
            xpos,
            ypos,
            yerr=err_comb,
            fmt=fmt_style,
            color=ccolor,
            markersize=8,
            capsize=3,
            elinewidth=2.5,
            label=label_str,
        )

        # If we do have additional errors, show them separately
        if syst_ufloats_lists is not None:
            # e.g. we can plot them as sub-error bars for systematic or stat
            stat_scaled = PE.statistical_errors_scaled[i_data]
            syst_scaled = PE.systematic_errors_scaled[i_data]

            # Example: systematics in orange, stat in green
            ax.errorbar(
                xpos,
                ypos,
                yerr=syst_scaled,
                fmt='none',
                ecolor='orange',
                capsize=3,
                elinewidth=2,
                alpha=0.7,
                label=f"{label_str} (Syst.)",
            )
            ax.errorbar(
                xpos,
                ypos,
                yerr=stat_scaled,
                fmt='none',
                ecolor='green',
                capsize=2,
                elinewidth=1.5,
                alpha=0.7,
                label=f"{label_str} (Stat.)",
            )

    # Basic labeling
    ax.set_xlabel(xlabel if xlabel else "")
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    # X-axis ticks
    # The “official” x-locations for the categories are from range(len(x_labels)).
    # If you want them pinned to the first dataset’s x_positions:
    # x_ref = PE.x_positions[0] if len(PE.x_positions)>0 else np.arange(len(x_labels))
    # ax.set_xticks(x_ref)
    # But if you want them exactly at integer indices:
    ax.set_xticks(np.arange(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=45, ha="right", rotation_mode="anchor")

    if draw_grid:
        ax.grid(True, which='major', linestyle='--', alpha=0.7)

    # Possibly set y-limits
    if y_limits is not None and len(y_limits) == 2:
        (ymin, ymax) = y_limits
        if ymin is not None:
            ax.set_ylim(bottom=ymin)
        if ymax is not None:
            ax.set_ylim(top=ymax)

    # If user wants a horizontal line:
    if draw_axhline is not None:
        ax.axhline(draw_axhline, color='black', alpha=0.5)

    # Show legend
    ax.legend(fontsize='large')

    # Tidy up layout so labels don't get cut off
    plt.tight_layout()

    # * --------------- Optionally compute & show chi2 ---------------
    if show_chi2:
        # For 'baseline', we might need the first dataset as a reference
        if chi2_mode == 'baseline':
            if skip_first:
                if option == 'shiftToBaseline':
                    # as the first is used as a baseline, and be skippied in drawing, it means others have shifted to the first, and thus the baseline here for chi2 calculation is actually with central value =0, error = input error
                    baseline_dataset = [ufloat(0, unc_avr.s) for unc_avr in stat_ufloats_lists[0]]
                    baseline_syst = [ufloat(0, unc_avr.s) for unc_avr in syst_ufloats_lists[0]] if syst_ufloats_lists else None

                else:  # == 'shiftToBaseline_and_projectToSigmaPlane', because the error has already been propagated
                    baseline_dataset = [ufloat(0, 0) for _ in stat_ufloats_lists[0]]
                    baseline_syst = [ufloat(0, 0) for _ in syst_ufloats_lists[0]] if syst_ufloats_lists else None

            else:
                baseline_dataset = stat_ufloats_lists[0] if stat_ufloats_lists else None
                baseline_syst = syst_ufloats_lists[0] if syst_ufloats_lists else None
        else:
            baseline_dataset = None
            baseline_syst = None

        # We'll place the text near the bottom
        y_bottom = ax.get_ylim()[0]
        text_y = y_bottom + 0.06 * (ax.get_ylim()[1] - y_bottom)

        n_plotted = len(PE.x_positions)
        n_bins = len(x_labels)

        for bin_index in range(n_bins):
            # gather y-values, errors, and the original dataset index
            yvals_bin = []
            yerrs_bin = []
            xvals_bin = []
            orig_idx_bin = []
            for i_data_pl in range(n_plotted):
                i_label = i_data_pl if not skip_first else (i_data_pl + 1)
                # skip if bin_index out of range
                if bin_index >= len(PE.y_positions[i_data_pl]):
                    continue
                yvals_bin.append(PE.y_positions[i_data_pl][bin_index])
                yerrs_bin.append(PE.combined_errors[i_data_pl][bin_index])
                xvals_bin.append(PE.x_positions[i_data_pl][bin_index])
                orig_idx_bin.append(i_label)

            yvals_bin = np.array(yvals_bin)
            yerrs_bin = np.array(yerrs_bin)
            orig_idx_bin = np.array(orig_idx_bin)

            if len(yvals_bin) < 2:
                continue

            chi2_val = compute_bin_chi2_for_mode(
                bin_index=bin_index,
                yvals_bin=yvals_bin,
                yerrs_bin=yerrs_bin,
                orig_idx_bin=orig_idx_bin,
                chi2_mode=chi2_mode,
                baseline_dataset=baseline_dataset,
                baseline_syst=baseline_syst,
            )

            x_for_text = np.mean(xvals_bin) if len(xvals_bin) > 0 else bin_index
            rprint(f"[INFO] Bin {bin_index}: chi2={chi2_val:.2f}")
            ax.text(x_for_text, text_y, rf"$\chi^2={chi2_val:.2f}$", ha='center', va='bottom', fontsize=9, color='purple', alpha=0.8)

    if output_file:
        output_file = str(Path(output_file).resolve())
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file)
        rprint(f"[INFO] Figure saved to {output_file}")

    # Close the plot
    plt.close()


if __name__ == '__main__':
    # Test the function
    x_labels = ['A', 'B', 'C']
    stat_ufloats_lists = [
        np.array([ufloat(1, 0.1), ufloat(2, 0.2), ufloat(3, 0.3)]),
        np.array([ufloat(1, 0.1), ufloat(2, 0.2), ufloat(3, 0.3)]) + 0.1,
        np.array([ufloat(1, 0.1), ufloat(2, 0.2), ufloat(3, 0.3)]) + 0.2,
    ]
    syst_ufloats_lists = None
    labels = ['Data Set 1', 'Data Set 2', 'Data Set 3']
    xlabel = 'X Label'
    ylabel = 'Y Label'
    title = 'Title'
    # option = 'shiftToBaseline'  # [compareRawValues, shiftToBaseline, shiftToBaseline_and_projectToSigmaPlane]
    draw_axhline = None
    draw_grid = True

    for option in ['compareRawValues', 'shiftToBaseline', 'shiftToBaseline_and_projectToSigmaPlane']:
        output_file = f'output/test_{option}.png'

        # compare_data_with_errorbar
        compare_data_with_errorbar(
            x_labels=x_labels,
            stat_ufloats_lists=stat_ufloats_lists,
            syst_ufloats_lists=syst_ufloats_lists,
            labels=labels,
            xlabel=xlabel,
            ylabel=ylabel,
            title=title,
            option=option,
            draw_axhline=draw_axhline,
            draw_grid=draw_grid,
            output_file=output_file,
            show_chi2=True,
            chi2_mode='baseline',
        )
