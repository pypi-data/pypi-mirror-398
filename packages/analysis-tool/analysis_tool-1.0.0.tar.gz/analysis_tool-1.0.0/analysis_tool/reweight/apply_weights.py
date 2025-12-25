'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-01-17 13:15:08 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-11-10 13:14:25 +0100
FilePath     : apply_weights.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import time
import os
import argparse
import yaml
import uproot as ur
import numpy as np
import pandas as pd
import pickle
import tempfile
import shutil
from typing import List, Optional, Union, Dict, Any
from pathlib import Path

import ROOT as r
from ROOT import RDataFrame, TChain, TTree, TFile

import hep_ml

from ..utils.utils_uproot import get_variables_pd, get_weights_np, save_dict_to_root
from ..utils.utils_numpy import analyze_distribution
from ..utils.utils_yaml import read_yaml
from ..utils.utils_ROOT import reset_tree_reshuffled_bit

from .reweighting import load_input_variables

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


def create_temp_file(weights: np.ndarray, output_tree_name: str, output_branch_name: str, temp_dir: Union[str, Path]) -> Path:
    """
    Create a temporary file with weights in a specified directory

    Args:
        weights: Array of weights to save
        output_tree_name: Name of the tree to create
        output_branch_name: Name of the branch to save
        temp_dir: Directory to store the temporary file

    Returns:
        Path to the created temporary file
    """
    # Ensure the temporary directory exists
    temp_dir = Path(temp_dir).resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Create a temporary file in the specified directory
    prefix = "weights_"
    suffix = ".root"

    # Use tempfile to create a unique filename but in our specified directory
    with tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, dir=temp_dir, delete=False) as tmp:
        temp_file = Path(tmp.name)

    logger.info(f"Creating temporary weights file: {temp_file}")

    # Save weights to temporary file
    save_dict_to_root(
        dict_data={output_branch_name: weights},
        output_file_path=temp_file,
        output_tree_name=output_tree_name,
    )

    return temp_file


# Create a new function to load with version checking
def load_reweighter(weights_file: str) -> tuple[Any, Optional[List[str]]]:
    """
    Load reweighter with version compatibility checking

    Args:
        weights_file: Path to the pickle file containing the trained reweighter

    Returns:
        Tuple of (reweighter, variables_list)
    """
    with open(weights_file, 'rb') as f:
        model_data = pickle.load(f)

    # Check if it's the new format (dict with metadata) or old format (direct reweighter)
    if isinstance(model_data, dict) and 'reweighter' in model_data:
        # New format with metadata
        logger.info(f"Loading reweighter (version: {model_data.get('version', 'unknown')})")
        logger.info(f"Model created with hep_ml version: {model_data.get('hep_ml_version', 'unknown')}")
        logger.info(f"Created on: {model_data.get('created_at', 'unknown')}")

        # Version compatibility check
        current_hep_ml = getattr(hep_ml, '__version__', 'unknown')
        model_hep_ml = model_data.get('hep_ml_version', 'unknown')

        if current_hep_ml != model_hep_ml and model_hep_ml != 'unknown' and current_hep_ml != 'unknown':
            logger.warning(f"Current hep_ml version [bold yellow]({current_hep_ml})[/] differs from model version [bold yellow]({model_hep_ml})[/]", extra={"markup": True})
            logger.warning("This might cause compatibility issues")

        return model_data['reweighter'], model_data.get('variables', [])
    else:
        # Old format, direct reweighter
        logger.warning("Loading legacy model format without version information")
        return model_data, None


def get_branches_to_save(branches_input: list[str], additional_branches_to_save: str | List[str], output_weight_name: str, mode: str) -> List[str]:
    """
    Process additional_branches_to_save parameter to determine which branches to save

    Args:
        branches_input: List of branch names from the input tree
        additional_branches_to_save: Specification of branches to save
        output_weight_name: Name of the weight branch
        mode: Mode to use when reading from YAML files

    Returns:
        List of branch names to save
    """
    branches_to_save: List[str] = [output_weight_name]

    if not additional_branches_to_save:
        logger.info("No additional branches to save, only the weight will be saved")
        return list(set(branches_to_save))

    if isinstance(additional_branches_to_save, str) and additional_branches_to_save.upper() == 'ALL':
        logger.info("Saving all original branches along with the weight")
        branches_to_save.extend(branches_input)
        return list(set(branches_to_save))

    # Process branches from comma-separated string or list
    branch_items = additional_branches_to_save.split(',') if isinstance(additional_branches_to_save, str) else additional_branches_to_save

    for item in branch_items:
        if item.endswith('.yaml'):
            try:
                yaml_content = read_yaml(item, mode)
                if isinstance(yaml_content, dict):
                    branches_to_save.extend(list(yaml_content.keys()))
                elif isinstance(yaml_content, list):
                    branches_to_save.extend(yaml_content)
                else:
                    logger.warning(f"Unexpected data format in YAML file {item}, mode {mode}. Expected dict or list.")
            except Exception as e:
                logger.error(f"Error loading branches from YAML file {item}: {e}")
        else:
            branches_to_save.append(item)

    logger.info(f"The following branches will be saved together with the weight: \n{branches_to_save}")

    # Make branches list unique and ensure weight branch is included
    branches_to_save.append(output_weight_name)
    return list(set(branches_to_save))


def clean_temp_directory(temp_dir: Path) -> None:
    """
    Clean up the temporary directory if it's empty and not a system directory

    Args:
        temp_dir: Path to the temporary directory
    """
    try:
        if temp_dir.exists() and temp_dir.is_dir():
            # Check if this is a system directory we should never remove
            system_dirs = ['/tmp', '/var/tmp', '/usr', '/etc', '/bin', '/sbin', '/lib', '/home']
            temp_dir_str = str(temp_dir.resolve())

            # Don't attempt to remove system directories
            if any(temp_dir_str == system_dir or temp_dir_str.startswith(f"{system_dir}/") for system_dir in system_dirs):
                logger.warning(f"Refusing to remove system directory: [bold yellow]{temp_dir}[/]", extra={"markup": True})
            else:
                # Check if directory is empty
                contents = list(temp_dir.iterdir())
                if not contents:
                    # Directory is verified empty, safe to remove
                    temp_dir.rmdir()
                    logger.info(f"Removed empty temporary directory: {temp_dir}")
                else:
                    # Log what remains in the directory
                    logger.info(f"Temporary directory {temp_dir} contains {len(contents)} items. Not removing.")
    except Exception as e:
        logger.warning(f"Failed to check/remove temporary directory: [bold yellow]{e}[/]", extra={"markup": True})


def apply_weights(
    input_file: str,
    input_tree_name: str,
    input_weight: str,
    variables_files: List[str],
    weight_method: str,
    weights_file: str,
    mode: str,
    output_file: str,
    output_tree_name: str,
    output_weight_name: str,
    output_tmp_dir: Optional[str] = None,
    additional_branches_to_save: str | List[str] = 'All',
    n_threads: int = 1,
) -> None:
    """
    Apply weights to an input file using a trained reweighter

    Args:
        input_file: File to add weights to
        input_tree_name: Name of the tree in file
        input_weight: Name of branch of existing weights to incorporate
        variables_files: Path to files with variable lists or the variables themselves
        weight_method: Method used for reweighting (e.g., 'gb')
        weights_file: Pickle file containing trained reweighter
        mode: Name of the selection in yaml
        output_file: File to store the ntuple with weights
        output_tree_name: Name of the tree in output file
        output_weight_name: Name of the output weight branch
        output_tmp_dir: Directory to store temporary files
        additional_branches_to_save: Branches to save with weights. 'All' to save all original branches together with the weight, '' to save none branches from the input file but only the weight,
                            comma-separated list for specific branches, or yaml files ending with '.yaml'
        n_threads: Maximum number of threads to be used, default is 1
    """

    # Disable ROOT's multithreading
    if n_threads == 1:
        r.ROOT.DisableImplicitMT()
    else:
        r.ROOT.EnableImplicitMT(n_threads)

    # Load input variables and original weights
    logger.info("Loading input variables and weights")
    variables, original_pd = load_input_variables(input_file, input_tree_name, variables_files, mode)

    if (input_weight) and (input_weight.upper() not in ['NONE', 'FALSE']):
        original_weight_np = get_weights_np(input_file, input_tree_name, input_weight)
    else:
        original_weight_np = np.ones(len(original_pd))

    # Load reweighter and calculate weights
    logger.info(f"Loading reweighter from {weights_file}")
    reweighter, saved_variables = load_reweighter(weights_file)

    # Check if the variables used to train the reweighter are the same as the input variables
    if saved_variables != variables:
        logger.warning(f'The input variables are [bold yellow]{variables}[/], but the variables used to train the reweighter are [bold yellow]{saved_variables}[/]', extra={"markup": True})
        logger.warning('The input variables will be used to apply the weights, but please make sure that the ordered variables have the same physical meaning, otherwise the weights are not correct')

    logger.info("Calculating weights...")
    weights = reweighter.predict_weights(original_pd[variables], original_weight_np)

    # Analyze the distribution of the weights
    analyze_distribution(values=weights, weights=None, title="Weight Distribution", outlier_threshold=20)

    # * Check if we only need the weight branch
    if not additional_branches_to_save or (isinstance(additional_branches_to_save, str) and additional_branches_to_save.strip() == ''):
        # If we only need the weight branch, we can save directly using uproot
        logger.info("Saving only the weight branch directly to output file")
        save_dict_to_root(
            dict_data={output_weight_name: weights},
            output_file_path=output_file,
            output_tree_name=output_tree_name,
        )

        logger.info(f'Weights saved directly to {output_file}')
        return  # Early return, no cleanup needed

    # * For other cases, we need to merge with the input file
    # Determine temporary directory location
    if not output_tmp_dir or output_tmp_dir.upper() == 'NONE':
        # Default to a 'tmp' folder in the same directory as the output file
        temp_dir = Path(output_file).parent / f'tmp_{time.strftime("%Y%m%d_%H%M%S")}'
    else:
        temp_dir = Path(output_tmp_dir)

    logger.info(f"Using temporary directory: {temp_dir}")

    # Create temporary file
    temp_file = create_temp_file(weights=weights, output_tree_name=output_tree_name, output_branch_name=output_weight_name, temp_dir=temp_dir)

    try:
        # Merge the weights with the input file
        logger.info(f"Merging weights into output file:")
        logger.info(f"  - Input file: {input_file}")
        logger.info(f"  - Weights file: {temp_file}")
        logger.info(f"  - Output file: {output_file}")

        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        # Open files and merge
        f_tmp = TFile(str(temp_file))
        t_tmp = f_tmp.Get(output_tree_name)

        f_input = TFile(input_file)
        t_input = f_input.Get(input_tree_name)

        # Check if the input tree has been reshuffled
        input_tree_reshuffled = t_input.TestBit(TTree.EStatusBits.kEntriesReshuffled)
        if input_tree_reshuffled:
            logger.warning("The input tree has been reshuffled, please check the input file")
            logger.warning("Here we will try to reset the status bit and add the friend tree, but please take your own risk")
            reset_tree_reshuffled_bit(t_input)

        t_tmp.AddFriend(t_input)

        # Set kEntriesReshuffled bit before saving
        if input_tree_reshuffled:
            t_tmp.SetBit(TTree.EStatusBits.kEntriesReshuffled)
            logger.warning("kEntriesReshuffled bit set to True after adding the friend tree")

        # Create a RDataFrame from the temporary tree with the friend tree
        dataframe = RDataFrame(t_tmp)

        branches_input: list[str] = [branch.GetName() for branch in t_input.GetListOfBranches()]

        # Determine branches to save and save the output
        branches_to_save: List[str] = get_branches_to_save(branches_input, additional_branches_to_save, output_weight_name, mode)

        # Save the output
        dataframe.Snapshot(output_tree_name, output_file, branches_to_save)

        # Clean up
        f_tmp.Close()
        f_input.Close()

        logger.info(f'Merged tree saved to {output_file}')

    finally:
        # Clean up the temporary file
        if temp_file.exists():
            os.unlink(temp_file)
            logger.info(f"Removed temporary file: {temp_file}")

            # Clean up the temporary directory if possible
            clean_temp_directory(temp_dir)


def get_parser() -> argparse.ArgumentParser:
    """
    Create and configure argument parser

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Apply weights to ROOT files using trained reweighter")
    parser.add_argument('--input-file', help='File to add weights to', required=True)
    parser.add_argument('--input-tree-name', default='DecayTree', help='Name of the tree in file')
    parser.add_argument('--input-weight', default='', help='Name of branch of existing weights to incorporate. Just leave it to be false if you want to get pure response.')
    parser.add_argument('--variables-files', nargs='+', required=True, help='Path to the file with variable lists or the list of concerned variables')
    parser.add_argument(
        '--weight-method',
        default='gb',
        # choices=['gb', 'binned'],
        help='Specify method used to reweight (e.g., gb, binned), but actually it is not used as all the reweighter information is stored in the pickle file',
    )
    parser.add_argument('--weights-file', required=True, help='Pickle file containing trained reweighter')
    parser.add_argument('--mode', required=True, help='Name of the selection in yaml')
    parser.add_argument('--output-file', required=True, help='File to store the ntuple with weights')
    parser.add_argument('--output-tree-name', default='DecayTree', help='Name of the tree in output file')
    parser.add_argument('--output-weight-name', required=True, help='Name of the output weight branch')
    parser.add_argument('--output-tmp-dir', default='None', help='Directory to store temporary files')

    parser.add_argument(
        '--additional-branches-to-save',
        default='All',
        type=str,
        help='Branches to save with weights. "All" to save all original branches, "" for none, and a comma-separated list for specific branches (for exmpale, "runNumber,eventNumber"), or yaml files ending with ".yaml"',
    )

    parser.add_argument('--n-threads', default=1, type=int, help='Maximum number of threads to be used')

    return parser


def main(args: Optional[argparse.Namespace] = None) -> None:
    """
    Main entry point for the script

    Args:
        args: Command line arguments (parsed by argparse)
    """
    if args is None:
        args = get_parser().parse_args()
    apply_weights(**vars(args))


if __name__ == '__main__':
    main()
