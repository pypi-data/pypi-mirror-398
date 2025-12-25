'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-01-17 13:25:27 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-07-20 14:35:11 +0200
FilePath     : reweighting.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import argparse
import yaml
import uproot as ur
import numpy as np
import pandas as pd
import pickle
from typing import List, Dict, Union, Tuple, Optional, Any
import hep_ml
from hep_ml.reweight import BinsReweighter, GBReweighter
from pathlib import Path
import time

from ..utils.utils_uproot import get_variables_pd, get_weights_np
from ..plotter.compare_distributions import plot_individual_variable_comparison, collect_all_plots_in_one_canvas
from ..correlation.matrixHelper import plot_correlation_heatmap

# Use rich backend for logging
import logging
from rich.logging import RichHandler
from rich import print as rprint

# Configure rich logging globally
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%x %X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)


# def read_variables_from_yaml(mode, variables_files):
#     variables = []
#     for f in variables_files:
#         with open(f, 'r') as stream:
#             variables += list(yaml.safe_load(stream)[mode].keys())
#     return variables


def read_variables_dict_from_yaml(mode: str, variables_files: List[str]) -> Dict[str, str]:
    """
    Read variables dictionary from YAML configuration files

    Args:
        mode: Mode/section name in YAML files to read variables from
        variables_files: List of YAML file paths

    Returns:
        Dictionary mapping variable names to expressions
    """
    variables_dict = {}
    for f in variables_files:
        with open(f, 'r') as stream:
            variables_dict |= yaml.safe_load(stream)[mode]
    return variables_dict


def load_input_variables(
    input_file: Union[str, List[str]],
    input_tree_name: str,
    variables_files: Union[str, List[str]],
    mode: str,
) -> Tuple[List[str], pd.DataFrame]:
    """
    Load variables from input file based on configuration

    Args:
        input_file: Path to the ROOT file(s)
        input_tree_name: Name of the tree to read
        variables_files: Either YAML files with variable definitions or direct variable list
        mode: Mode/section name to read from YAML files

    Returns:
        Tuple containing list of variable names and pandas DataFrame with data
    """
    # ========================================
    # Handle different input formats for variables_files
    # ========================================
    _variables_files = variables_files.split(',') if isinstance(variables_files, str) else variables_files

    # ========================================
    # Read variables from yaml file or directly use as variable list
    # ========================================
    if any(str(file).endswith('.yaml') for file in _variables_files):
        try:
            variables_dict = read_variables_dict_from_yaml(mode, _variables_files)

            exprs = list(variables_dict.values())
            variables = list(variables_dict.keys())

            logger.info("Variables used for training will be converted from expressions in YAML file:")
            rprint(variables_dict)

            # Read variables using the expressions
            input_pd_from_expr = get_variables_pd(input_file, input_tree_name, exprs)

            # Rename columns to use variable names instead of expressions
            rename_map = dict(zip(exprs, variables))
            input_pd = input_pd_from_expr.rename(columns=rename_map)
        except Exception as e:
            raise ValueError(f"Error reading variables from YAML: {e}") from e
    else:
        # Direct use of variable list
        variables = _variables_files
        input_pd = get_variables_pd(input_file, input_tree_name, variables)

    return variables, input_pd


def save_reweighter(reweighter, variables, output_path):
    """Save reweighter with metadata for better versioning and compatibility"""
    model_info = {
        'reweighter': reweighter,
        'variables': variables,
        'version': '1.0',
        'hep_ml_version': getattr(hep_ml, '__version__', 'unknown'),
        'created_at': time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(output_path, 'wb') as f:
        pickle.dump(model_info, f, protocol=pickle.HIGHEST_PROTOCOL)
    logger.info(f"Reweighter saved to {output_path} with version metadata")


def create_reweighter(weight_method: str) -> Union[GBReweighter, BinsReweighter]:
    """
    Create a reweighter based on specified method and parameters

    Args:
        weight_method: String specifying reweighting method and parameters
                        Format: "method:param1:param2:..."

    Returns:
        Initialized reweighter object
    """
    # ========================================
    # Parse training configuration
    # ========================================
    weight_conf = weight_method.split(':')
    method = weight_conf[0]

    if method == 'gb':
        # Default parameters
        n_estimators = 70
        learning_rate = 0.1
        max_depth = 7
        min_samples_leaf = 1000

        # Override with user parameters if provided
        if len(weight_conf) > 1:
            n_estimators = int(weight_conf[1])
            learning_rate = float(weight_conf[2])
            max_depth = int(weight_conf[3])
            min_samples_leaf = int(weight_conf[4])

        logger.info(f'BDT configuration: estimators={n_estimators}, ' f'learning_rate={learning_rate}, ' f'depth={max_depth}, ' f'min_samples_leaf={min_samples_leaf}')
        # reweighter = GBReweighter(n_estimators=60, learning_rate=0.1, max_depth=6, min_samples_leaf=1000, gb_args={'subsample': 1.0})

        return GBReweighter(n_estimators=n_estimators, learning_rate=learning_rate, max_depth=max_depth, min_samples_leaf=min_samples_leaf, gb_args={'subsample': 1.0})

    elif method == 'binned':
        # Default parameters
        n_bins = 20
        n_neighs = 1.0

        # Override with user parameters if provided
        if len(weight_conf) > 1:
            n_bins = int(weight_conf[1])
            n_neighs = float(weight_conf[2])

        logger.info(f'Binned configuration: n_bins={n_bins}, n_neighs={n_neighs}')

        return BinsReweighter(n_bins=n_bins, n_neighs=n_neighs)

    else:
        raise ValueError(f"Invalid reweighter type. Valid types are ['gb', 'binned'], " f"not {method}. Please check the configuration.")


def generate_validation_plots(
    variables: List[str],
    original_pd: pd.DataFrame,
    target_pd: pd.DataFrame,
    reweighter: Union[GBReweighter, BinsReweighter],
    original_weight_np: np.ndarray,
    target_weight_np: np.ndarray,
    output_plot_dir: str,
) -> None:
    """
    Generate validation plots for reweighting results

    Args:
        variables: List of variables to plot
        original_pd: Original DataFrame
        target_pd: Target DataFrame
        reweighter: Trained reweighter
        original_weight_np: Original weights
        target_weight_np: Target weights
        output_plot_dir: Directory to save plots
    """
    if not output_plot_dir:
        return

    # ========================================
    # Calculate weights with reweighter
    # ========================================
    logger.info("Calculating weights for validation plots...")
    reweighted_weights = reweighter.predict_weights(original_pd[variables], original_weight_np)

    # ========================================
    # 1. Plot individual variable distributions
    # ========================================
    path_to_single_figs = []
    for var in variables:
        _path = plot_individual_variable_comparison(
            var_title=var,
            datas=[target_pd[var], original_pd[var], original_pd[var]],
            weights=[target_weight_np, original_weight_np, reweighted_weights],
            labels=["Target", "Original", "Reweighted"],
            output_plot_dir=output_plot_dir,
            pull=2,
            exts=["pdf", "png"],
            use_sci_notation=True,
        )
        path_to_single_figs.append(_path)

    # ========================================
    # Combine all plots into one canvas
    # ========================================
    collect_all_plots_in_one_canvas(
        path_to_single_figs=path_to_single_figs,
        output_plot_dir=str(output_plot_dir),
        exts=["pdf", "png"],
    )

    # ========================================
    # Plot correlation matrices
    # ========================================
    if len(variables) > 1:
        corr_dir = Path(output_plot_dir) / "correlation_matrix"
        corr_dir.mkdir(parents=True, exist_ok=True)

        for cluster in [True, False]:

            # Original correlation
            plot_correlation_heatmap(
                df=original_pd[variables],
                output_plot_name=f'{corr_dir}/original_cluster{cluster}.pdf',
                title="Original",
                df_weight=original_weight_np,
                cluster=cluster,
            )

            # Target correlation
            plot_correlation_heatmap(
                df=target_pd[variables],
                output_plot_name=f'{corr_dir}/target_cluster{cluster}.pdf',
                title="Target",
                df_weight=target_weight_np,
                cluster=cluster,
            )

            # Reweighted correlation
            plot_correlation_heatmap(
                df=original_pd[variables],
                output_plot_name=f'{corr_dir}/reweighted_cluster{cluster}.pdf',
                title="Reweighted",
                df_weight=reweighted_weights,
                cluster=cluster,
            )


# -----------reweighting helper--------------#
def reweighting(
    original_file: Union[str, List[str]],
    original_tree_name: str,
    original_weight: Optional[str],
    target_file: Union[str, List[str]],
    target_tree_name: str,
    target_weight: Optional[str],
    mode: str,
    weight_method: str,
    variables_files: Union[str, List[str]],
    output_file: str,
    output_plot_dir: Optional[str] = None,
) -> None:
    """
    Train a reweighter to match distributions between original and target samples

    Args:
        original_file: Path to the original file to be reweighted
        original_tree_name: Name of the tree in original file
        original_weight: Name of branch of original weights (None for unweighted)
        target_file: Path to the target file to match
        target_tree_name: Name of the tree in target file
        target_weight: Name of branch of target weights (None for unweighted)
        mode: Name of the selection in yaml
        weight_method: Method used for reweighting (e.g., 'gb:70:0.1:7:1000')
        variables_files: Path to files with variable lists or the variables themselves
        output_file: Path to save trained reweighter
        output_plot_dir: Directory to save validation plots (None for no plots)
    """
    # ========================================
    # Load data
    # ========================================
    logger.info("Loading input variables and weights...")
    variables, original_pd = load_input_variables(original_file, original_tree_name, variables_files, mode)
    original_weight_np = get_weights_np(original_file, original_tree_name, original_weight) if original_weight else np.ones(len(original_pd))

    _variables, target_pd = load_input_variables(target_file, target_tree_name, variables_files, mode)
    if variables != _variables:
        raise ValueError(f"Variables in original and target files are different: {variables} vs {_variables}")
    target_weight_np = get_weights_np(target_file, target_tree_name, target_weight) if target_weight else np.ones(len(target_pd))

    # ========================================
    # Create and train reweighter
    # ========================================
    logger.info(f"Variables used for reweighting: {variables}")
    logger.info("Creating reweighter...")
    reweighter = create_reweighter(weight_method)

    logger.info("Training reweighter...")
    reweighter.fit(
        original_pd[variables],
        target_pd[variables],
        original_weight=original_weight_np,
        target_weight=target_weight_np,
    )

    # ========================================
    # Save the trained reweighter
    # ========================================
    output_path = Path(output_file).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save reweighter with metadata
    save_reweighter(reweighter, variables, output_path)

    # ========================================
    # Generate validation plots if requested
    # ========================================
    if output_plot_dir:
        logger.info("Generating validation plots...")
        generate_validation_plots(
            variables=variables,
            original_pd=original_pd,
            target_pd=target_pd,
            reweighter=reweighter,
            original_weight_np=original_weight_np,
            target_weight_np=target_weight_np,
            output_plot_dir=output_plot_dir,
        )


def get_parser() -> argparse.ArgumentParser:
    """
    Create and configure argument parser

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Train reweighter to match distributions between samples")

    parser.add_argument('--original-file', nargs='+', required=True, help='Path to the original file, to be reweighted')
    parser.add_argument('--original-tree-name', default='DecayTree', help='Name of the tree in original file')
    parser.add_argument('--original-weight', default='', help='Name of branch of original weights')
    parser.add_argument('--target-file', nargs='+', required=True, help='Path to the target file to match')
    parser.add_argument('--target-tree-name', default='DecayTree', help='Name of the tree in target file')
    parser.add_argument('--target-weight', default='', help='Name of branch of target weights')
    parser.add_argument('--mode', required=True, help='Name of the selection in yaml')
    parser.add_argument(
        '--weight-method',
        default='gb',
        # choices=['gb', 'binned'],
        help='Reweighting method and parameters (e.g., "gb:70:0.1:7:1000" or "binned:20:1.0")',
    )
    parser.add_argument('--variables-files', required=True, nargs='+', help='Path to YAML files with variable lists or direct list of variables')
    parser.add_argument('--output-file', required=True, help='Output pickle file to save trained reweighter')
    parser.add_argument('--output-plot-dir', default=None, help='Output directory for validation plots')
    return parser


def main(args: Optional[argparse.Namespace] = None) -> None:
    """
    Main entry point for the script

    Args:
        args: Command line arguments (parsed by argparse)
    """
    if args is None:
        args = get_parser().parse_args()
    reweighting(**vars(args))


if __name__ == '__main__':
    main()
