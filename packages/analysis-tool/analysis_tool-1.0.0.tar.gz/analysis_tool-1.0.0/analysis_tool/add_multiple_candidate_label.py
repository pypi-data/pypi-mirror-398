'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-06-19 16:23:35 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-11-06 12:57:10 +0100
FilePath     : add_multiple_candidate_label.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import os, sys, argparse
from pathlib import Path
from typing import List, Dict, Union, Optional
import uproot as ur
import pandas as pd
from colorama import Fore, Style


import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


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


from .utils.utils_uproot import load_variables_to_pd_by_uproot


def plot_multiple_candidates(
    data_dict: Dict[str, pd.Series],
    output_pic_path: str,
    title: str = 'Percentage of Multiple Candidates per Category',
) -> None:
    """
    Generates a bar plot showing the number of multiple candidates per category.

    Parameters:
        data_dict (Dict[str, pd.Series]): A dictionary where keys are category names and values are pandas.Series
                                          with counts of 'multiple_candidate_label'.
        output_pic_path (str): The file path where the output plot image will be saved.
    """
    # Initialize lists to store categories and counts
    categories: list[str] = []
    total_counts: list[int] = []
    multiple_candidate_counts: list[int] = []
    fraction: list[float] = []

    # Process each category
    for category, series in data_dict.items():
        # Ensure the series index is integer type
        series.index = series.index.astype('int64')

        # Sum counts where multiple_candidate_label > 0
        multiple_candidates = series.loc[series.index > 0].sum()
        categories.append(category)
        multiple_candidate_counts.append(int(multiple_candidates))
        total_counts.append(int(series.sum()))
        fraction.append(multiple_candidates / series.sum())

    # Create a DataFrame and sort it
    df: pd.DataFrame = pd.DataFrame(
        {
            'Category': categories,
            'MultipleCandidates_counts': multiple_candidate_counts,
            'TotalCandidates_counts': total_counts,
            'MultipleCandidates_fraction': fraction,
        }
    )

    # Sort the DataFrame by 'MultipleCandidates_fraction' in descending order
    df = df.sort_values('MultipleCandidates_fraction', ascending=False)

    # Extract sorted categories and counts
    categories = df['Category'].tolist()
    multiple_candidate_counts = df['MultipleCandidates_counts'].tolist()
    total_counts = df['TotalCandidates_counts'].tolist()
    fraction = df['MultipleCandidates_fraction'].tolist()

    # Create the plot
    plt.figure(figsize=(12, 6))
    bars = plt.bar(categories, fraction, color='skyblue')

    # Add data labels on top of each bar
    for bar in bars:
        yval: float = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + max(fraction) * 0.01,
            f"{yval:.2%}",
            ha='center',
            va='bottom',
        )

    # Scale y-axis to percentage
    ax = plt.gca()
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    # Rotate x-axis labels if necessary
    plt.xticks(rotation=45, ha='right')

    # Set labels and title
    plt.xlabel('Category')
    plt.ylabel('Number of Multiple Candidates')
    plt.title(title)

    # Adjust layout to prevent clipping of tick-labels
    plt.tight_layout()

    # Ensure the output directory exists
    output_pic_path = Path(output_pic_path).resolve().as_posix()
    Path(output_pic_path).parent.mkdir(parents=True, exist_ok=True)

    # Save the plot to the specified output path
    plt.savefig(output_pic_path)
    plt.close()

    print(f"Plot saved to {output_pic_path}")


def generate_latex_table(
    data_dict: Dict[str, pd.Series],
    output_tex_path: str,
    label_unique: str = None,
) -> None:
    """
    Generates a LaTeX table showing total counts, multiple candidate counts, and fractions for each category.

    Parameters:
        data_dict (Dict[str, pd.Series]): A dictionary where keys are category names and values are pandas.Series
                                          with counts of 'multiple_candidate_label'.
        output_tex_path (str): The file path where the LaTeX table will be saved.
    """
    # Initialize lists to store data for the table
    categories = []
    total_counts = []
    multiple_candidate_counts = []
    fractions = []

    # Process each category
    for category, series in data_dict.items():
        # Ensure the series index is integer type
        series.index = series.index.astype('int64')

        # Total count is the sum of all counts
        total_count = series.sum()

        # Multiple candidate counts where multiple_candidate_label > 0
        multiple_candidates = series.loc[series.index > 0].sum()

        # Fraction calculation
        fraction = multiple_candidates / total_count if total_count > 0 else 0

        # Append data to lists
        categories.append(category)
        total_counts.append(total_count)
        multiple_candidate_counts.append(multiple_candidates)
        fractions.append(fraction)

    # Create a DataFrame
    df = pd.DataFrame({'Category': categories, 'Total Counts': total_counts, 'Multiple Candidates': multiple_candidate_counts, 'Fraction (%)': fractions})

    # Format the fractions as percentages with four decimal places
    df['Fraction (%)'] = df['Fraction (%)'].apply(lambda x: f"{x:.2%}")

    # Format numbers with commas
    df['Total Counts'] = df['Total Counts'].apply(lambda x: f"{int(x):,}")
    df['Multiple Candidates'] = df['Multiple Candidates'].apply(lambda x: f"{int(x):,}")

    # Sort the DataFrame by 'Multiple Candidates' in descending order
    df = df.sort_values('Fraction (%)', ascending=False)

    # Generate LaTeX table
    latex_table = df.to_latex(
        index=False,
        caption=f'Summary of Multiple Candidates per Category ({label_unique})' if label_unique else 'Summary of Multiple Candidates per Category',
        label=f'tab:multiple_candidates:{label_unique}' if label_unique else 'tab:multiple_candidates',
        position='!htb',
        column_format='lrrr',
        escape=True,  # To allow underscores in category names
    )

    # Ensure the output directory exists
    output_tex_path = Path(output_tex_path).resolve().as_posix()
    Path(output_tex_path).parent.mkdir(parents=True, exist_ok=True)

    # Write the LaTeX table to the specified output path
    with open(output_tex_path, 'w') as f:
        f.write(latex_table)

    print(latex_table)
    print(f"LaTeX table saved to {output_tex_path}")


def add_multiple_candidate_label(
    input_file_name: str,
    output_file_name: str,
    check_vars: Union[str, List[str]],
    output_branch_name: str,
    tree_name: str = "DecayTree",
    cut_selection: Optional[str] = None,
    branches: Optional[List[str]] = None,
    output_pic_path: Optional[str] = None,
    output_tex_path: Optional[str] = None,
) -> pd.Series:
    """
    Adds a new branch to a ROOT tree that labels duplicated candidates based on specified variables.

    Parameters:
        input_file_name (str): The path to the input ROOT file. Multiple files can be provided by separating them with semicolons(;).
        output_file_name (str): The path to the output ROOT file.
        check_vars (str or List[str]): Variables to check for duplicates, e.g., "runNumber,eventNumber" or ["runNumber", "eventNumber"].
        output_branch_name (str): The name of the new branch to be added.
        tree_name (str, optional): The name of the tree in the ROOT file. Defaults to "DecayTree".
        cut_selection (str, optional): A cut expression to filter the data. Defaults to None.
        branches (List[str], optional): List of branches to read. If None, all branches are read.
        output_pic_path (str, optional): The file path where the output plot image will be saved. Defaults to None.
        output_tex_path (str, optional): The file path where the LaTeX table will be saved. Defaults to None.

    Returns:
        pd.Series: A pandas Series containing the counts of each label.
    """

    # Ensure check_vars is a list
    if isinstance(check_vars, str):
        check_vars = [var.strip() for var in check_vars.split(",")]
    print(f"Variables used for duplicate checking: {check_vars}")

    # Only check the multiple candidate information if the output file is not a ROOT file
    if not (output_file_name and output_file_name.upper().endswith(".ROOT")):
        print("Output file is not a ROOT file. The updated tree will not be saved, will only print the summary table.")
        # Only load the variables corresponding to the check variables to speed up the process
        branches = check_vars

    # We open the file and get the tree as a pandas.DataFrame
    df = load_variables_to_pd_by_uproot(
        input_file_name,
        tree_name,
        branches,
        cut_selection,
    )

    # Check if the necessary variables are in the DataFrame
    for var in check_vars:
        if var not in df.columns:
            raise ValueError(f"Variable {var} not found in the DataFrame {df.columns}")

    # Generate a new column labeling duplicate candidates by counting the number of unique (runNumber, eventNumber) pairs
    # and assigning a number to each duplicate candidate
    # The first candidate is labeled as 0, the second as 1, and so on
    df[output_branch_name] = df.groupby(check_vars).cumcount()

    # Generate summary table of labels
    label_counts = df[output_branch_name].value_counts().sort_index()
    print("\nSummary of multiple candidate labels:")
    print(label_counts.to_string())

    # Write the updated DataFrame to a new ROOT file
    if output_file_name and output_file_name.upper().endswith(".ROOT"):
        try:
            # Ensure the output directory exists
            output_path = Path(output_file_name).resolve().as_posix()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            with ur.recreate(output_file_name) as ofile:
                ofile[tree_name] = df
            print(f"Successfully wrote the updated tree to {output_file_name}")

        except Exception as e:
            print("Error writing to the ROOT file")
            raise e
    else:
        logger.warning(f"Output file name [bold yellow]{output_file_name}[/] does not end with [bold yellow]'.root'[/]. The updated tree will not be saved.", extra={"markup": True})

    # Generate a bar plot and LaTeX table if output_pic_path and output_tex_path are provided
    label_counts_dict = {
        "Total": label_counts,
    }

    # Generate a bar plot showing the number of multiple candidates per category
    if output_pic_path:

        output_pic_path = Path(output_pic_path).resolve().as_posix()
        Path(output_pic_path).parent.mkdir(parents=True, exist_ok=True)
        plot_multiple_candidates(label_counts_dict, output_pic_path)

    # Generate a LaTeX table showing total counts, multiple candidate counts, and fractions for each category
    if output_tex_path:
        output_tex_path = Path(output_tex_path).resolve().as_posix()
        Path(output_tex_path).parent.mkdir(parents=True, exist_ok=True)
        generate_latex_table(label_counts_dict, output_tex_path, label_unique=None)

    return label_counts


def get_parser():
    parser = argparse.ArgumentParser(description="Add a new branch to a ROOT tree that labels duplicated candidates based on specified variables.")
    parser.add_argument("--input-file-name", type=str, help="The path to the input ROOT file.")
    parser.add_argument("--output-file-name", type=str, help="The path to the output ROOT file.")
    parser.add_argument("--check-vars", type=str, help="Variables to check for duplicates, e.g., 'runNumber,eventNumber'.")
    parser.add_argument("--output-branch-name", type=str, help="The name of the new branch to be added.")
    parser.add_argument("--tree-name", type=str, default="DecayTree", help="The name of the tree in the ROOT file. Defaults to 'DecayTree'.")
    parser.add_argument("--cut-selection", type=str, default=None, help="A cut expression to filter the data. Defaults to None.")
    parser.add_argument("--branches", type=str, default=None, help="List of branches to read. If None, all branches are read.")
    parser.add_argument("--output-pic-path", type=str, default=None, help="The file path where the output plot image will be saved.")
    parser.add_argument("--output-tex-path", type=str, default=None, help="The file path where the LaTeX table will be saved.")
    return parser


def main(args=None):
    if args is None:
        args = get_parser().parse_args()
    add_multiple_candidate_label(**vars(args))


# ------------------------ Local Test ------------------------
def __local_test():
    input_file_name = "/data/lhcb/users/jwua/RLcMuonic/RLc-3body/data/Data/Lb_DataSSMisIDFull.root"
    output_file_name = "/data/lhcb/users/jwua/RLcMuonic/RLc-3body/data/Data/Lb_DataSSMisIDFull_with_candidate_label.root"
    check_vars = ["runNumber", "eventNumber"]
    output_branch_name = "multiple_candidate_label"
    tree_name = "DecayTree"
    cut_selection = None
    branches = None

    add_multiple_candidate_label(
        input_file_name,
        output_file_name,
        check_vars,
        output_branch_name,
        tree_name,
        cut_selection,
        branches,
    )


if __name__ == '__main__':
    main()

    # __local_test()
