'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-02-10 15:20:22 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2024-09-29 10:41:06 +0200
FilePath     : compare_distributions.py
Description  : 

Copyright (c) 2024 by everyone, All Rights Reserved. 
'''

import os
import re
import argparse
import yaml
import copy
import colorama


import uproot as ur
import numpy as np
import pandas as pd

import hist
from hist import Hist

import uncertainties as unc
from uncertainties import ufloat
from uncertainties import unumpy as unp


import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from PIL import Image, ImageChops

import mplhep as hep

from collections import Counter
from pathlib import Path

import colorama
from pdf2image import convert_from_path
from tqdm import tqdm


from utils.utils_uproot import load_variables_to_pd_by_uproot

from multiprocessing import cpu_count


matplotlib.use("Agg")
plt.style.use(hep.styles.CMS)

hist_settings_hep_histErrBar = {
    "bins": 49,
    "density": True,
    "alpha": 0.9,
    "histtype": "step",
    "lw": 2,
    # 'xerr': True,
    "yerr": True,
}
hist_settings_hep_histFilled = {
    "bins": 49,
    "density": True,
    "alpha": 0.5,
    "histtype": "step",
    "lw": 2,
    "histtype": "fill",
    # 'xerr': True,
    # 'yerr': True,
}


hist_colors = {
    0: "black",
    1: "red",
    2: "blue",
    3: "green",
    4: "cyan",
    5: "magenta",
    6: "yellow",
    7: "white",
}
hist_hatches = ["/", "\\", "|", "-", "+", "x", "o", "O", ".", "*"]


def read_from_yaml(mode, variables_files):
    variables_dict = {}
    for file in variables_files:
        with open(file, "r") as stream:
            variables_dict |= yaml.safe_load(stream)[mode]
    return variables_dict


def create_variables_in_pd(datasets: pd.DataFrame, cmp_vars: dict, return_only_cmp_vars=False):

    # The dataframe to store the new columns
    new_columns_pd = pd.DataFrame()

    # cmp_vars is a dictionary, where keys are the name of the variables to be created, and values are the expressions to be used to create the variables
    for var_title, var_expr in cmp_vars.items():

        # Skip if the variable title matches the expression (no operation needed)
        if var_title == var_expr:
            continue

        # Check if the expression can be evaluated
        try:
            # Copy the existing branch if the expression is already in the dataset
            if var_expr in datasets.columns:
                if var_title in datasets.columns:
                    print(f"INFO::create_variables_in_pd: The variable {var_title} already exists in the dataset, and will be overwritten by {var_expr}")
                new_columns_pd[var_title] = datasets[var_expr]
                # new_columns[var_title] = datasets[var_expr]
            # Evaluate and store the new column temporarily
            else:
                new_columns_pd[var_title] = datasets.eval(var_expr)
                # new_columns[var_title] = datasets.eval(var_expr)

        except Exception as e:
            raise ValueError(f"{colorama.Fore.RED}failed to evaluate '{var_expr}': {e}{colorama.Style.RESET_ALL}")

            # if 'MIN' in var_expr.upper() or 'MAX' in var_expr.upper():
            #     raise ValueError(f'{colorama.Fore.RED}the expression {var_expr} contains min() or max() operation, which is not supported by pandas.{colorama.Style.RESET_ALL}')

    # Concatenate all new columns at once
    if return_only_cmp_vars:  # return only the columns that are in the cmp_vars
        # Get the compare columns that exist in the original dataset, and not exist in the new_columns
        cmp_columns_from_original_pd = pd.DataFrame({var_title: datasets[var_title] for var_title in cmp_vars if var_title in datasets.columns and var_title not in new_columns_pd.columns})
        # cmp_columns_from_original = {var_title: datasets[var_title] for var_title in cmp_vars if var_title in datasets.columns and var_title not in new_columns}

        return pd.concat([new_columns_pd, cmp_columns_from_original_pd], axis=1)

    else:
        return pd.concat([datasets, new_columns_pd], axis=1)
        # return pd.concat([datasets, pd.DataFrame(new_columns, index=datasets.index)], axis=1)


def load_data_from_root(datasets: list[list], cmp_vars: list[dict]):
    for i_dataset, dset in enumerate(datasets):

        input_weight_expr = dset[2]
        input_weight_expr = None if input_weight_expr.upper() in ["NONE", "1", "ONE"] else input_weight_expr

        # The variables to be loaded
        if input_weight_expr:
            _vars_to_load = list(cmp_vars[i_dataset].values()) + [input_weight_expr]
        else:
            _vars_to_load = list(cmp_vars[i_dataset].values())

        # Load all the variables needed for comparison
        variables_pd = load_variables_to_pd_by_uproot(
            input_file_path=dset[0],
            input_tree_name=dset[1],
            variables=_vars_to_load,
            selection=dset[3],
            library='pd',
            num_workers=max(cpu_count() // 2, 1),
        )

        # 1. Main comparison variables

        # Use frame.copy() to de-fragment the frame
        variables_pd = variables_pd.copy()

        # Create new variables in the dataset
        variables_pd = create_variables_in_pd(variables_pd, cmp_vars[i_dataset])

        # check datatype (bool->int)
        for var_title in cmp_vars[i_dataset]:
            if variables_pd[var_title].dtype == bool:
                print(f"INFO::Check datatype. Temporarily change the type of {var_title} from [bool] to [int] for plotting purpose")
                variables_pd[var_title] = variables_pd[var_title].astype(int)

        # 2. For weights
        _weight_name = "__weight_for_distribution_comparison__"

        if input_weight_expr:
            weight_pd = create_variables_in_pd(variables_pd, {_weight_name: input_weight_expr})[_weight_name]

        else:
            weight_pd = np.ones(len(variables_pd))

        # 3. Append the variables and weight to the list
        dset.append(variables_pd)  # [5]
        dset.append(weight_pd)  # [6]

    return datasets


def getRanges(datas, percentRange="auto"):
    """
    Get ranges of list of datasets
    datas: [list] a list of data given in numpy format.
    """
    #     datas = datas if isinstance(datas, list) else [datas]
    #     data = np.hstack(datas)
    #     return [data.min(), data.max()]

    datas = datas if isinstance(datas, list) else [datas]

    # Set auto range definition
    auto_percentRange = [0.1, 99.9] if max(len(Counter(_data)) for _data in datas) > 20 else [0, 100]

    # Get ranges
    percentRange = auto_percentRange if percentRange == "auto" else percentRange
    _ranges = [np.percentile(_data, percentRange) if (_data.size > 500) else [_data.min(), _data.max()] for _data in datas]

    ranges = [min(_r[0] for _r in _ranges), max(_r[1] for _r in _ranges)]
    # return ranges
    return [ranges[0] - abs(ranges[0]) * 1e-9, ranges[1] + abs(ranges[1]) * 1e-9]


def getRanges_main(datasets: list, var_exprs: list):
    """
    Get plot ranges
    """
    ranges = []
    datas = []
    for i_dataset in range(len(datasets)):
        dset = datasets[i_dataset]
        datas.append(dset[5][var_exprs[i_dataset]])
        ranges = getRanges(datas=datas)

    return ranges


def draw_hist(
    ax: plt.Axes,
    data: np.array,
    weight: np.array,
    label: str,
    hist_settings: dict,
    ranges="auto",
):
    if ranges == "auto":
        ranges = [data.min(), data.max()]
    else:
        assert isinstance(ranges, list), "ranges argument should be a list looks like: [leftRange, rightRange]"

    # Create a histogram with weighted data
    # histo, bin_edges = np.histogram(a=data, bins=hist_settings['bins'], range=ranges, weights=weight)
    histo = Hist.new.Reg(hist_settings["bins"], *ranges, name=" ", flow=False).Weight().fill(data, weight=weight)
    # histo = Hist.new.Reg(hist_settings['bins'], *ranges, name=' ', underflow=False, overflow=False).Weight().fill(data, weight=weight)

    ## Replace negative values with 0 in histogram's counts, then only the positive bin values will be plotted
    replace_negative_to_0 = False
    if replace_negative_to_0:
        # 1) Get histogram counts and errors as arrays
        counts = histo.counts()
        # 2) Replace negative values with 0 in histogram's counts and errors
        counts[counts < 0] = 0

    _hist_settings = {} | hist_settings
    _hist_settings.pop("bins") if "bins" in _hist_settings else None

    if "yerr" in _hist_settings and _hist_settings["yerr"] == True:
        _hist_settings["yerr"] = np.sqrt(histo.variances())
    histo.plot(ax=ax, label=label, **_hist_settings)
    # hep.histplot(ax=ax, H=histo, label=label, **_hist_settings)

    return histo


def draw_pull(
    ax: plt.Axes,
    hist_ref: hist.hist.Hist,
    hist_cmp: hist.hist.Hist,
    hist_settings: dict,
) -> None:
    # Scale the MC histogram to match the data
    Scale = hist_ref.sum().value / hist_cmp.sum().value
    _hist_cmp = hist_cmp * Scale

    # Calculate the pull
    h_diff = _hist_cmp + (-1 * hist_ref)  # hist.hist.Hist

    h_diff_values = h_diff.values()  # np.abs(h_diff.values())

    h_diff_errors = np.sqrt(np.array(h_diff.variances()))
    pull = np.divide(
        h_diff_values,
        h_diff_errors,
        out=np.zeros_like(h_diff_values, dtype=float),
        where=(h_diff_errors != 0),
    )

    #######################
    #    # Calculate the pull
    #    hist_ref_unc = unp.uarray(hist_ref.values(), np.sqrt(hist_ref.variances()))
    #    _hist_cmp_unc = unp.uarray(_hist_cmp.values(), np.sqrt(_hist_cmp.variances()))
    #
    #    hist_ref_unc[np.where(hist_ref_unc == 0)] = unp.uarray(0.0, 1.0)
    #    _hist_cmp_unc[np.where(_hist_cmp_unc == 0)] = unp.uarray(0.0, 1.0)
    #
    #    pull_diff_unc = _hist_cmp_unc - hist_ref_unc
    #    pull_diff = unp.nominal_values(pull_diff_unc)
    #    pull_uncertainty = unp.std_devs(pull_diff_unc)
    #    pull = pull_diff / pull_uncertainty
    ######################

    # Add a horizontal line at y=0 for reference
    ax.axhline(3, color="black", linestyle="--", alpha=0.9)  # Add a horizontal line at y=0 for reference
    ax.axhline(-3, color="black", linestyle="--", alpha=0.9)  # Add a horizontal line at y=0 for reference
    ax.axhline(0, color="black", linestyle=":", alpha=0.5)  # Add a horizontal line at y=0 for reference
    ax.set_ylim(-5, 5)

    # Set labels and title
    ax.set_ylabel("Pull")

    # Adjust spacing between subplots
    plt.subplots_adjust(hspace=0.1)
    ax.errorbar(
        hist_ref.axes[0].centers,
        pull,
        yerr=1,
        fmt="o",
        label="Pull",
        color=hist_settings["color"],
        alpha=hist_settings["alpha"],
    )

    return True


def draw_ratio(
    ax: plt.Axes,
    hist_ref: hist.hist.Hist,
    hist_cmp: hist.hist.Hist,
    hist_settings: dict,
) -> None:
    # Scale the MC histogram to match the data
    Scale = hist_ref.sum().value / hist_cmp.sum().value
    _hist_cmp = hist_cmp * Scale

    # Create arrays with uncertainties
    ref_unc = unp.uarray(hist_ref.values(), np.sqrt(hist_ref.variances()))
    cmp_unc = unp.uarray(_hist_cmp.values(), np.sqrt(_hist_cmp.variances()))

    # Safely handle division by zero: replace zeros in ref_unc with NaN or another placeholder
    # # ref_unc_safe_divide = np.where(unp.nominal_values(ref_unc) == 0, ufloat(np.inf, 0), ref_unc)
    ref_unc_safe_divide = np.where(unp.nominal_values(ref_unc) == 0, ufloat(np.inf, unc.std_dev(ref_unc)), ref_unc)

    # Perform the division
    ratio = cmp_unc / ref_unc_safe_divide

    # Extract the nominal values and standard deviations of the resulting ratio
    ratio_values = unp.nominal_values(ratio)
    ratio_uncertainties = unp.std_devs(ratio)
    # ratio_uncertainties[np.where(ratio_uncertainties == np.inf)] = 0
    # np.where(ratio_uncertainties < 0, 0, ratio_uncertainties)

    # # Calculate the ratio
    # h_ratio =  _hist_cmp/ hist_ref  # hist.hist.Hist
    # h_ratio_values = h_ratio.values()
    # h_ratio_errors = np.sqrt(np.array(h_ratio.variances()))

    # # Calculate the pull
    # h_diff = hist_ref + (-1 * _hist_cmp)  # hist.hist.Hist
    # h_diff_values = np.abs(h_diff.values())

    # h_diff_errors = np.sqrt(np.array(h_diff.variances()))
    # pull = np.divide(
    #     h_diff_values,
    #     h_diff_errors,
    #     out=np.zeros_like(h_diff_values, dtype=float),
    #     where=(h_diff_errors != 0),
    # )

    #######################
    #    # Calculate the pull
    #    hist_ref_unc = unp.uarray(hist_ref.values(), np.sqrt(hist_ref.variances()))
    #    _hist_cmp_unc = unp.uarray(_hist_cmp.values(), np.sqrt(_hist_cmp.variances()))
    #
    #    hist_ref_unc[np.where(hist_ref_unc == 0)] = unp.uarray(0.0, 1.0)
    #    _hist_cmp_unc[np.where(_hist_cmp_unc == 0)] = unp.uarray(0.0, 1.0)
    #
    #    pull_diff_unc = _hist_cmp_unc - hist_ref_unc
    #    pull_diff = unp.nominal_values(pull_diff_unc)
    #    pull_uncertainty = unp.std_devs(pull_diff_unc)
    #    pull = pull_diff / pull_uncertainty
    ######################

    # Add a horizontal line at y=0 for reference
    ax.axhline(1, color="black", linestyle="--", alpha=0.9)  # Add a horizontal line at y=0 for reference
    # ax.axhline(-3, color="black", linestyle="--", alpha=0.9)  # Add a horizontal line at y=0 for reference
    # ax.axhline(0, color="black", linestyle=":", alpha=0.5)  # Add a horizontal line at y=0 for reference
    ax.set_ylim(0, 3.0)

    # Set labels and title
    ax.set_ylabel("Ratio")

    # Adjust spacing between subplots
    plt.subplots_adjust(hspace=0.1)
    ax.errorbar(
        hist_ref.axes[0].centers,
        ratio_values,
        yerr=ratio_uncertainties,
        fmt="o",
        label="Pull",
        color=hist_settings["color"],
        alpha=hist_settings["alpha"],
    )

    return True


# Draw histograms


# Draw histograms
def draw_hists(
    ax: plt.Axes,
    datasets: list,
    #####################
    datas: list[np.array],
    weights: list[np.array],
    labels: list[str],
    ####################
    var_title: str,
    ranges,
    hist_settings,
):
    _hists = []
    print(f"var_title : {var_title}")
    for i_dataset in range(len(datas)):

        # modify the hist_settings
        _hist_settings = copy.deepcopy(hist_settings)
        _hist_settings |= {"color": hist_colors[i_dataset] if "color" not in _hist_settings else _hist_settings["color"]}
        _hist_settings |= {"hatch": hist_hatches[i_dataset] if "fill" in _hist_settings["histtype"] else None}

        # draw the histogram
        _h = draw_hist(
            ax=ax,
            data=datas,
            # weight=dset[6][dset[2]],
            weight=weights,
            label=labels,
            ranges=ranges,
            hist_settings=_hist_settings,
        )
        _hists.append(_h)

    # ax.legend(loc='upper left')
    ax.legend(loc="best")
    ax.set_title(var_title)
    ax.set_ylabel(r"$\mathcal{p.d.f.}$", loc="center")

    return _hists


# def draw_hists(
#     ax: plt.Axes,
#     datasets: list,
#     var_exprs: pd.DataFrame,
#     var_title: str,
#     ranges,
#     hist_settings,
# ):
#     _hists = []
#     print(f"var_title : {var_title}")
#     for i_dataset in range(len(datasets)):
#         dset = datasets[i_dataset]

#         # modify the hist_settings
#         _hist_settings = copy.deepcopy(hist_settings)
#         _hist_settings |= {"color": hist_colors[i_dataset] if "color" not in _hist_settings else _hist_settings["color"]}
#         _hist_settings |= {"hatch": hist_hatches[i_dataset] if "fill" in _hist_settings["histtype"] else None}

#         # draw the histogram
#         _h = draw_hist(
#             ax=ax,
#             data=dset[5][var_exprs[i_dataset]],
#             # weight=dset[6][dset[2]],
#             weight=dset[6],
#             label=dset[4],
#             ranges=ranges,
#             hist_settings=_hist_settings,
#         )
#         _hists.append(_h)
#         print(f"    var_expr : {var_exprs[i_dataset]},    weight : {dset[2]},    cut : {dset[3]}")
#     # ax.legend(loc='upper left')
#     ax.legend(loc="best")
#     ax.set_title(var_title)
#     ax.set_ylabel(r"$\mathcal{p.d.f.}$", loc="center")

#     return _hists


# def draw_pull(ax:plt.Axes, hist_ref:np.histogram, hist_cmp:np.histogram, bin_edges:np.array) -> None:
def draw_pulls(ax: plt.Axes, hists: list, pull_style: int, hist_settings: dict) -> None:
    # Check input arguments
    assert len(hists) >= 2, "The length of hists must be larger than 2 for comparison"

    # Call the private function
    for i in range(len(hists) - 1):
        # modify the hist_settings
        _hist_settings = copy.deepcopy(hist_settings)
        _hist_settings |= {"color": hist_colors[i + 1] if "color" not in _hist_settings else _hist_settings["color"]}

        if pull_style == 1:  # draw normal pull
            draw_pull(ax, hists[0], hists[i + 1], hist_settings=_hist_settings)
        elif pull_style == 2:  # draw ratio
            draw_ratio(ax, hists[0], hists[i + 1], hist_settings=_hist_settings)
        else:
            print("pull_style should be either 1 or 2")
            exit(1)
    return True


def plot_individual_variable_comparison(
    var_title: str,
    datasets: list,
    var_exprs: list,
    output_plot_dir: str,
    pull=False,
    hist_settings: dict = None,
    exts=["pdf", "png"],
):
    # var_exprs = [cmp_vars[i][var_title] for i in range(len(datasets))]
    ranges = getRanges_main(datasets=datasets, var_exprs=var_exprs)

    # Create the figure and axes
    if pull:
        fig, (ax_main, ax_pull) = plt.subplots(nrows=2, sharex=True, gridspec_kw={"height_ratios": [5, 1]}, figsize=(10, 8))
    else:
        fig, ax_main = plt.subplots(figsize=(10, 8))

    _hists = draw_hists(
        ax=ax_main,
        datasets=datasets,
        var_exprs=var_exprs,
        var_title=var_title,
        ranges=ranges,
        hist_settings=hist_settings,
    )

    # draw pulls
    if pull:
        draw_pulls(ax=ax_pull, hists=_hists, pull_style=pull, hist_settings=hist_settings)

    # Save the figure
    for ext in exts:
        output_fig = f"{output_plot_dir}/comparePlot_{var_title}.{ext}"
        fig.savefig(output_fig, bbox_inches="tight")
        print(f"INFO::The plot is saved as {output_fig}")

    return output_fig


def crop_image(img: Image) -> Image:
    """
    Crops the input image by removing unnecessary whitespace around the content.

    Args:
        img (PIL.Image.Image): The input image to be cropped.

    Returns:
        PIL.Image.Image: The cropped image with whitespace removed.
    """

    # Step 1: Convert the image to grayscale.
    # ----------------------------------------
    # Converting to grayscale simplifies the image by reducing it to a single
    # channel (intensity), which is sufficient for detecting edges and content.
    # This makes subsequent processing faster and easier.
    gray_img = img.convert('L')

    # Step 2: Invert the grayscale image.
    # ------------------------------------
    # Inverting the image changes dark areas to light and vice versa.
    # This is useful because we want to identify the actual content (which is
    # usually darker) against the background (which is usually lighter).
    # After inversion, the content becomes light on a dark background.
    inverted_img = ImageChops.invert(gray_img)

    # Step 3: Get the bounding box of the non-zero regions.
    # ------------------------------------------------------
    # The 'getbbox' method returns the bounding box (left, upper, right, lower)
    # of the non-zero (non-black) regions in the image.
    # If the image is completely black (no content after inversion), 'getbbox'
    # returns None.
    bbox = inverted_img.getbbox()

    # Step 4: Crop the image if a bounding box is found.
    # ---------------------------------------------------
    if bbox:
        # If a bounding box is found, crop the original image to this bounding box.
        # This effectively removes any unnecessary whitespace around the content.
        img = img.crop(bbox)
        # Note: We crop the original image (not the grayscale or inverted one)
        # to preserve the original colors and details.

    # Step 5: Return the cropped image.
    # ----------------------------------
    # If no bounding box was found (e.g., the image is blank), the original
    # image is returned without any cropping.
    return img


def collect_all_plots_in_one_canvas(plot_titles: list[str], path_to_single_figs: list[str], output_plot_dir: str, exts: list[str] = None) -> bool:
    """
    Collects individual plots and arranges them into a single canvas.

    Args:
        plot_titles (List[str]): List of variplotable titles corresponding to the plots.
        path_to_single_figs (List[str]): List of paths to the individual plots, and should be in the same order as plot_titles.
        output_plot_dir (str): Directory where the combined plot will be saved.
        ext (List[str], optional): List of file extensions for the combined plot. Defaults to ["pdf", "png"].

    Returns:
        bool: True if the operation is successful, False otherwise.
    """

    # Set default file extensions
    exts = ["pdf", "png"] if exts is None else exts

    # Check if the number of variable titles and paths match

    assert len(plot_titles) == len(
        path_to_single_figs
    ), f"{colorama.Fore.RED}the number of variable titles and paths to the individual plots must match. Found {len(plot_titles)} titles and {len(path_to_single_figs)} paths.{colorama.Style.RESET_ALL}"

    # Determine the number of columns and rows for the grid
    cols = int(np.floor(np.sqrt(len(plot_titles)))) if len(plot_titles) > 3 else len(plot_titles)
    rows = int(np.ceil(len(plot_titles) / cols))

    # Create the figure and grid
    fig = plt.figure(figsize=(cols * 10, rows * 8))
    gs = gridspec.GridSpec(rows, cols, wspace=0.0, hspace=0.0)

    # Loop through each variable title and add the corresponding image to the grid
    for i_var in tqdm(list(range(len(plot_titles))), desc="Collecting plots", leave=False):
        ax = fig.add_subplot(gs[i_var])

        # Get the file path and extension
        fig_path = Path(path_to_single_figs[i_var]).resolve().as_posix()
        ext = Path(fig_path).suffix

        try:
            if ext.lower() == '.png':
                img = Image.open(fig_path)
            elif ext.lower() == '.pdf':
                try:
                    # Convert the PDF to an image using pdf2image
                    print(f"INFO::collect_all_plots_in_one_canvas Converting PDF '{fig_path}' to image...")
                    images = convert_from_path(fig_path, dpi=200, first_page=1, last_page=1)
                    if images:
                        img = images[0]
                        # Crop the image to remove whitespace
                        img = crop_image(img)
                    else:
                        raise RuntimeError(f'{colorama.Fore.RED}could not convert PDF "{fig_path}" to image.{colorama.Style.RESET_ALL}')
                except Exception as e:
                    raise RuntimeError(f"{colorama.Fore.RED}could not convert PDF '{fig_path}' to image: {e}{colorama.Style.RESET_ALL}")

            else:
                raise ValueError(f"{colorama.Fore.RED}unsupported file extension '{ext}' for file '{fig_path}'. Supported extensions are '.pdf' and '.png'.{colorama.Style.RESET_ALL}")

            # Convert image to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Display the image
            ax.imshow(img)
            ax.axis('off')

        except Exception as e:
            raise RuntimeError(f"{colorama.Fore.RED}could not open image '{fig_path}': {e}{colorama.Style.RESET_ALL}")

    # Adjust layout
    plt.tight_layout()

    # Ensure the plot directory exists
    output_plot_dir = Path(output_plot_dir).resolve().as_posix()
    plot_dir_path = Path(output_plot_dir)
    plot_dir_path.mkdir(parents=True, exist_ok=True)

    # Save the figure in both PDF and PNG formats
    output_filename = "comparePlots"
    for ext in exts:
        output_fig = plot_dir_path / f"{output_filename}.{ext}"
        try:
            fig.savefig(output_fig, bbox_inches="tight")
            print(f"INFO::collect_all_plots_in_one_canvas The plot is saved as {output_fig}")
        except Exception as e:
            raise RuntimeError(f"{colorama.Fore.RED}could not save figure '{output_fig}': {e}{colorama.Style.RESET_ALL}")

    plt.close(fig)
    return True


def draw_distributions(
    dataset: list[str] | str,
    compare_variables: list[str] | str,
    mode: str,
    year: str,
    plot_dir: str,
    pull: int,
    style: str,
):
    """
    Draws distributions for comparison between datasets.

    Args:
        dataset (list or str): List of dataset strings or a single dataset string.
            Each dataset string should have 5 elements separated by commas:
            'path_to_file,tree_name,weight_name,(selection),label_name'.
            Example: './myroot,DecayTree,none,(1>0),MC'.
        compare_variables (list or str): Variables to compare between datasets.
            Can be a list of variable names or a single variable name.
        mode (str): Mode of operation (used for reading YAML files).
        year (str): Year of the data (used for labeling plots).
        plot_dir (str): Directory where plots will be saved.
        pull (int): Pull value for plotting.
        style (str): Plot style ('errorbar' or 'filledhist').
    """

    # ------------------ Input Validation ------------------ #
    # Ensure dataset is a list
    if isinstance(dataset, str):
        dataset = [dataset]

    # Validate each dataset string
    for ds in dataset:
        elements = ds.split(',')
        if len(elements) != 5:
            raise ValueError(f"{colorama.Fore.RED}each dataset should have 5 elements separated by commas. Dataset '{ds}' does not meet this requirement.{colorama.Style.RESET_ALL}")

    # Set histogram settings based on style
    style = style.lower()
    if style == "errorbar":
        hist_settings = hist_settings_hep_histErrBar
    elif style == "filledhist":
        hist_settings = hist_settings_hep_histFilled
    else:
        raise ValueError("{colorama.Fore.RED}style should be either 'errorbar' or 'filledhist'.{colorama.Style.RESET_ALL}")

    # ------------------ Compare Variables ------------------ #
    # Ensure compare_variables is a list
    compare_variables = [compare_variables] if isinstance(compare_variables, str) else compare_variables
    print("INFO::draw_distributions: compare_variables:", compare_variables)

    # Parse compare_variables
    variables_files = []
    num_datasets = len(dataset)
    if len(compare_variables) == 1:
        # Same variables for all datasets
        _variables_list = compare_variables[0].split(",")
        variables_files = [_variables_list for _ in range(num_datasets)]
    else:
        # Different variables for each dataset
        if len(compare_variables) != num_datasets:
            raise ValueError("{colorama.Fore.RED}when specifying different variables for each dataset, the number of compare_variables must match the number of datasets.{colorama.Style.RESET_ALL}")
        variables_files = [vars_str.split(",") for vars_str in compare_variables]

    # Read variables from YAML or create variable mappings
    cmp_vars = []
    for vars_list in variables_files:
        if vars_list and ".yaml" in vars_list[0]:
            cmp_var = read_from_yaml(mode, vars_list)
        else:
            cmp_var = {var: var for var in vars_list}
        cmp_vars.append(cmp_var)

    # ------------------ Load Data from ROOT Files ------------------ #
    # Split dataset strings into components
    # datasets_list is a list of lists: [[path_to_file, tree_name, weight_name, selection, label_name], ...]
    # datasets[*][0]=path_to_file, datasets[*][1]=tree_name, datasets[*][2]=weight_name, datasets[*][3]=cut_string, datasets[*][4]=label_name
    datasets_list = [ds.split(",") for ds in dataset]

    load_data_from_root(datasets_list, cmp_vars)

    # ------------------ Prepare Plot Directory ------------------ #
    plot_dir_path = Path(plot_dir).resolve()
    plot_dir_path.mkdir(parents=True, exist_ok=True)

    # -----------plot each variable--------------#
    # get list of list of var_exprs_list_sorted_by_expression (with the format of [[sample1_var_expr1, sample2_var_expr1], [sample1_var_exprs2, sample2_var_exprs2], ...])
    var_exprs_list_sorted_by_sample = [list(cmp_var.keys()) for cmp_var in cmp_vars]
    var_exprs_list_sorted_by_expression = [list(item) for item in zip(*var_exprs_list_sorted_by_sample)]
    var_titles = list(cmp_vars[0].keys())

    path_to_single_figs = [
        plot_individual_variable_comparison(
            var_title=var_title,
            datasets=datasets_list,
            var_exprs=var_exprs_list_sorted_by_expression[i],
            output_plot_dir=str(plot_dir_path),
            pull=pull,
            hist_settings=hist_settings,
            exts=["pdf", "png"],
        )
        for i, var_title in enumerate(var_titles)
    ]

    # -----------plot all in one canvas--------------#
    collect_all_plots_in_one_canvas(
        plot_titles=var_titles,
        path_to_single_figs=path_to_single_figs,
        output_plot_dir=str(plot_dir_path),
        exts=["pdf", "png"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        # nargs='+',
        action="append",
        required=True,
        help="Dataset to be compared (the following args are cocantated by comma, for example: ./myroot,DecayTree,none,(1>0),MC). Args order: dataset[0]=path_to_file, dataset[1]=tree_name, dataset[2]=weight_name(=none if N/A), dataset[3]=cut_string, dataset[4]=label_name.    Caution: As required by uproot, each cut should be enclosed in brackets! For example, (1>0 && 2>1) is invalid, while ((1>0) && (2>1)) is valid.",
    )
    parser.add_argument(
        "--compare-variables",
        action="append",
        required=True,
        help="List of variables to be compared; if dict is given, then take list of the dictionary values",
    )
    parser.add_argument("--mode", help="Name of the selection in yaml with variables")
    parser.add_argument("--year", type=int, help="Year of data taking")
    parser.add_argument("--plot-dir", type=str, default="./tmp", help="Output path of pdfs")
    parser.add_argument(
        "--pull",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help="Whether to draw pull distributions, the first dataset will be regared as the reference. [0: no pull, 1: draw pull, 2: draw ratio]",
    )
    parser.add_argument(
        "--style",
        type=str,
        default="errorbar",
        choices=["errorbar", "filledhist"],
        help="Whether draw errorbar or filledhist",
    )

    # parser = argument_parser()
    args = parser.parse_args()
    draw_distributions(**vars(args))
