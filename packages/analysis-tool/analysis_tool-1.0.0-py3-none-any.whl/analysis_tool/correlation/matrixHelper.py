'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-06-19 16:05:26 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-05-18 16:12:57 +0200
FilePath     : matrixHelper.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import contextlib
import os, sys
import random
import json, yaml
import re
import inspect
import textwrap
from itertools import chain
from collections.abc import Mapping
import multiprocessing
import string
import shlex
import argparse
import timeit
from copy import deepcopy
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import colorsys

import seaborn as sns


# -------- correlations part --------
def plot_correlation_matrix(
    correlationMatrix: np.ndarray,
    varNames: list,
    output_file: str = None,
    ylabel='Linear correlation coefficient',
    title="Correlations",
):
    """Plot correlation matrix

    Args:
        correlationMatrix (np.ndarray): Two dimensional array of correlation coefficients
        varNames (list): List of variable names, same order as the correlation matrix
        output_file (str): Path to output file
        ylabel (str, optional): Label of y-axis. Defaults to None.
        title (str, optional): Title of the plot.  Defaults to "Correlation".

    Returns:
        fig, ax: Figure and axis objects
    """
    # Create a figure with a larger size
    fig_width, fig_height = 12, 10
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # Create a heatmap with the correlation matrix
    im = ax.imshow(correlationMatrix, cmap='coolwarm', vmin=-1, vmax=1)

    # Add a colorbar to the plot
    cbar = ax.figure.colorbar(im, ax=ax, pad=0.01)

    # Set the title and axis labels
    def _get_xylabel_fontsize(num_vars, fig_width, fig_height):
        return int(min(20, (min(fig_width, fig_height) / num_vars) * 40))

    cbar.ax.set_ylabel(ylabel, rotation=-90, va="bottom") if ylabel else None
    ax.set_xticks(np.arange(len(varNames)))
    ax.set_yticks(np.arange(len(varNames)))
    ax.set_xticklabels(varNames, fontsize=_get_xylabel_fontsize(len(varNames), fig_width, fig_height))
    ax.set_yticklabels(varNames, fontsize=_get_xylabel_fontsize(len(varNames), fig_width, fig_height))

    # Rotate the x-axis labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Add the correlation values to the plot
    def _calculate_cell_fontsize(nVar, fig_width, fig_height):
        return 16 * min(fig_width, fig_height) / nVar

    for i, j in product(range(len(varNames)), range(len(varNames))):
        text = ax.text(j, i, "{:.2f}".format(correlationMatrix[i, j]), ha="center", va="center", color="w", fontsize=_calculate_cell_fontsize(len(varNames), fig_width, fig_height))

    # Set the title
    ax.set_title(title) if title else None

    # automatically adjust spacing between subplots (make sure the labels are not cut off)
    fig.tight_layout()

    # save plots
    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True) if '/' in output_file else None
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"INFO::SavePlot::Correlation matrix saved to: {output_file}")

    return fig, ax


def write_correlation_matrix_latex(correlationMatrix: np.ndarray, varNames: list, output_file: str, column_width=None, rotate_column_headers=90):  # fitResult: RooFitResult,
    """Write the correlation matrix to a LaTeX file with sideways table and full page

    Args:
        fitResult (RooFitResult): RooFitResult object containing the fit result
        output_file (str): The name of the output file
        column_width (str, optional): The width be specified for the column. i.e. 2cm. Defaults to None, and will be adjust audomatically.
        rotate_column_headers (int, optional): Specify the angle that the column headers to be rotated. Defaults to 90.
    """

    # check input arguments
    rotate_column_headers = float(rotate_column_headers)

    # Check the number of variables
    varNames = [var.replace("_", "\\_") for var in varNames]

    # Calculate the default column width if not specified
    if column_width is None:
        num_vars = len(varNames)
        # Default to a minimum width of 1cm and a maximum width of 4cm
        column_width = max(min(4 / num_vars, 1), 0.4)

        page_width, page_length = 21, 29.7  # A4 paper width in cm (21cm × 29.7cm)
        column_width = min(column_width, page_width / (num_vars + 4))

    # Set the total table width based on the number of variables and the column width
    table_width = min((num_vars + 8) * column_width, page_length)

    # Calculate the font size and row spacing
    font_size = max(min(int(120 / num_vars), 8), 5)
    row_spacing = max(min(1.5 / num_vars, 0.5), 0.3)
    col_spacing = max(min(1.5 / num_vars, 0.15), 0.01)

    # Create the output folder if not existed
    os.makedirs(os.path.dirname(output_file), exist_ok=True) if '/' in output_file else None

    # Write the correlation matrix to a LaTeX file with sideways table and full page
    with open(output_file, 'w') as f:
        f.write("\\begin{landscape}\n")
        f.write("\\begin{table}[htbp]\n")
        f.write("\\small\n")
        f.write("\\centering\n")
        f.write("\\caption{Correlation matrix}\n")

        f.write("\\renewcommand{\\arraystretch}{%.1f}\n" % (1 + row_spacing))
        f.write("\\fontsize{%dpt}{%dpt}\\selectfont\n" % (font_size, font_size))
        f.write("\\setlength\\tabcolsep{%.2fcm}\n" % col_spacing)

        # f.write("\\begin{tabular}{@{}l")
        f.write("\\begin{tabularx}{%.2fcm}{@{}l" % table_width)
        for i in range(len(varNames)):
            f.write("p{%.2fcm}" % column_width)
            if i < len(varNames) - 1:
                f.write(" ")
        f.write("@{}}\n")
        f.write("\\toprule\n")
        f.write("\\multicolumn{1}{@{}l}{\\textbf{}}")
        for varName in varNames:
            f.write(" & \\multicolumn{1}{c}{\\rotatebox[origin=c]{%s}{\\textbf{%s}}}" % (rotate_column_headers, varName))
        f.write("\\\\\n")
        f.write("\\midrule\n")
        for i in range(correlationMatrix.shape[0]):
            # Write the row header
            f.write("\\multicolumn{1}{@{}l}{\\textbf{%s}}" % varNames[i])
            for j in range(correlationMatrix.shape[1]):
                f.write(" & {:.0f}".format(correlationMatrix[i][j] * 100))
            f.write(" \\\\\n")
        f.write("\\bottomrule\n")
        # f.write("\\end{tabular}\n")
        f.write("\\end{tabularx}\n")
        f.write("\\end{table}\n")
        f.write("\\end{landscape}\n")


def calculate_correlation_matrix(df: pd.DataFrame, weights: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculate the weighted correlation matrix for a dataframe.

    Parameters:
    df (pd.DataFrame): The input data frame containing the data for correlation.
    weights (pd.DataFrame, optional): An optional DataFrame containing weights for each row.

    Returns:
    pd.DataFrame: A DataFrame representing the weighted correlation matrix.
    """

    """Calculate the weighted correlation matrix for a dataframe."""

    # Check if weights are provided
    if weights is not None:
        assert len(df) == len(weights), "Inputs weights and df must be of the same length."
        # save weights as np.array if weights is pd.DataFrame, as weights only contains one column
        weights = weights.iloc[:, 0].to_numpy() if isinstance(weights, pd.DataFrame) else weights

    else:
        weights = np.ones(len(df))

    # Initialization of the correlation matrix with ones on the diagonal and zeros elsewhere
    corr_matrix = pd.DataFrame(np.eye(len(df.columns)), index=df.columns, columns=df.columns)

    for i in range(len(df.columns)):
        for j in range(i + 1, len(df.columns)):
            x = df.iloc[:, i]
            y = df.iloc[:, j]

            # Handle potential constant column
            if x.nunique() == 1 or y.nunique() == 1:
                corr_matrix.iloc[i, j] = 0
                corr_matrix.iloc[j, i] = 0
                continue

            # Calculate the weighted covariance and correlation
            cov_xy = calculate_covariance(x, y, weights)
            variance_x = calculate_covariance(x, x, weights)
            variance_y = calculate_covariance(y, y, weights)

            # set the value to 0 if the denominator is 0
            corr_xy = np.divide(cov_xy, np.sqrt(variance_x * variance_y), out=np.zeros_like(cov_xy), where=np.sqrt(variance_x * variance_y) != 0)

            # Fill in the correlation matrix symmetrically
            corr_matrix.iloc[i, j] = corr_xy
            corr_matrix.iloc[j, i] = corr_xy
    return corr_matrix


# def dfPlotCorrelations(df: pd.DataFrame, output_plot_name: str, title: str = None, dfWeight: pd.DataFrame = None):
def plot_correlation_heatmap(
    df: pd.DataFrame,
    output_plot_name: str,
    title: str = None,
    df_weight: pd.DataFrame = None,
    figsize: tuple = (16, 14),
    cluster: bool = False,
):
    """
    Plots a heatmap of the correlation matrix from a pandas DataFrame.

    Parameters:
    df (pd.DataFrame): The input data frame containing the data for correlation.
    output_plot_name (str): The file path to save the output plot.
    title (str, optional): Title of the heatmap. Defaults to 'Correlation between variables'.
    df_weight (pd.DataFrame, optional): An optional DataFrame containing weights.

    Returns:
    (matplotlib.figure.Figure, matplotlib.axes._subplots.AxesSubplot)
    """

    # Calculate the correlation matrix
    corr = calculate_correlation_matrix(df, df_weight) if df_weight is not None else df.corr()

    if cluster:
        # Use clustermap for hierarchical clustering
        g = sns.clustermap(corr, annot=True, cmap='PiYG_r', fmt=".2f", linewidths=0.5, vmin=-1, vmax=1, figsize=figsize, cbar_kws={"shrink": 0.78, 'pad': 0.02})

        fig = g.fig
        ax = g.ax_heatmap

        # Improve readability
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=11)
        ax.set_yticklabels(ax.get_yticklabels(), fontsize=11)

        # Add title
        plt.title(label=title or 'Correlation between variables', fontsize=20)

    else:

        # Set up the matplotlib figure
        fig, ax = plt.subplots(figsize=figsize)

        # Draw the heatmap with the mask and correct aspect ratio, require the color bar shown to be from -1 to 1
        sns.heatmap(corr, annot=True, ax=ax, cmap='PiYG_r', fmt=".2f", square=True, linewidths=0.5, vmin=-1, vmax=1, cbar_kws={"shrink": 0.78, 'pad': 0.02})

        # Improve readability
        plt.xticks(rotation=45, ha='right', fontsize=11)
        plt.yticks(fontsize=11)

        # Add title
        plt.title(label=title or 'Correlation between variables', fontsize=20)

        # Tight layout
        plt.tight_layout()

    # Save plot
    output_plot_name = Path(output_plot_name).resolve().as_posix()
    Path(output_plot_name).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_plot_name, bbox_inches='tight')
    print(f"INFO::plot_correlation_heatmap::Correlation heatmap saved to: {output_plot_name}")

    return fig, ax


# -------- covariance part --------
def calculate_covariance(x: np.array, y: np.array, weights: np.array) -> float:
    """
    Calculate the weighted covariance between two numpy arrays.

    Parameters:
    x (np.array): First data series.
    y (np.array): Second data series.
    weights (np.array): Weights for each element.

    Returns:
    float: Weighted covariance of the two data series.
    """

    """Calculate the weighted covariance between two series."""
    assert len(x) == len(y) == len(weights), "Inputs must be of the same length."

    # Normalize weights
    weights = np.array(weights) / np.sum(weights)
    mean_x = np.average(x, weights=weights)
    mean_y = np.average(y, weights=weights)

    # Calculate weighted covariance
    result = np.sum(weights * (x - mean_x) * (y - mean_y))

    return result
