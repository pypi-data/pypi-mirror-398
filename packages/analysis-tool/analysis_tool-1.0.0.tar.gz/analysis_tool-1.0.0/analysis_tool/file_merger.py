'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-09-28 05:24:20 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-07-07 11:05:02 +0200
FilePath     : file_merger.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import argparse
from pathlib import Path

import ROOT as r
from ROOT import TObject, TFile, TTree, TChain
from ROOT import TTreeFormula
from array import array
import colorama

from .utils.utils_ROOT import get_branch_names
from tqdm import tqdm
from multiprocessing import cpu_count

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


def file_merger(
    input_files: list[str],
    input_tree_name: str,
    output_file: str,
    output_tree_name: str,
    save_common_branches_only: bool = True,
    default_missing_value: float = -9999,
    output_fileIndex_branch_name: str = "fileIndex",
    cut_string: str = "NONE",
):
    """
    Merges multiple ROOT files into a single output ROOT file, combining the specified trees.

    Args:
        input_files (list[str]): List of paths to the input ROOT files to be merged.
        input_tree_name (str): Name of the tree to be merged from the input files.
        output_file (str): Path to the output ROOT file.
        output_tree_name (str): Name of the tree in the merged output file.
        save_common_branches_only (bool): If True, only save branches that are common across all input files.

    Returns:
        None: The merged file is saved as `output_file`.
    """
    # Ensure input_files is a list, even if a single file is provided
    input_files = [input_files] if isinstance(input_files, str) else input_files

    # Validate input file list
    if not input_files:
        raise ValueError(f"{colorama.Fore.RED}No input files provided. Please specify at least one input file.{colorama.Style.RESET_ALL}")

    logger.info(f"Merging {len(input_files)} file(s) into {output_file} using tree '{input_tree_name}'")

    # Collect branches from all input files
    file_branches_dict = {f: get_branch_names(f, input_tree_name) for f in input_files}
    common_branches = set.intersection(*map(set, file_branches_dict.values()))
    all_branches = set.union(*map(set, file_branches_dict.values()))

    # Determine common branches across all input files if required
    if save_common_branches_only:
        branches_to_save = common_branches

        # Warn if there are any branches that are not common across all input files
        for _f, _branches in file_branches_dict.items():
            if non_common_branches := set(_branches) - branches_to_save:
                logger.warning(f"File [bold yellow]{_f}[/] contains non-common branches: [bold yellow]{non_common_branches}[/], will be dropped in the merged file.", extra={"markup": True})

    else:
        # NotImplementedError: This feature is not yet implemented
        branches_to_save = all_branches

        # Check if save_branches == all_branches, if not, raise an error
        if branches_to_save.symmetric_difference(common_branches):
            raise NotImplementedError(
                f'{colorama.Fore.RED}you set save_common_branches_only=False, trying to save all branches and use default values for the branches that are not common across all input files. But this feature is not yet implemented{colorama.Style.RESET_ALL}'
            )

    # Create a TChain and add the input files
    chain = TChain(input_tree_name)
    for entry in input_files:
        logger.info(f"Adding file {entry}")
        chain.Add(entry)

    # Create the output file and the new tree and open the output file
    output_file = Path(output_file).resolve().as_posix()
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    output_root_file = TFile(output_file, 'RECREATE')

    # Set the status of all branches to 0, then enable only the branches to be saved
    chain.SetBranchStatus("*", 0)
    for branch_name in branches_to_save:
        chain.SetBranchStatus(branch_name, 1)

    output_tree = chain.CloneTree(0)
    output_tree.SetName(output_tree_name)

    # Add a new branch 'file_index' to indicate the source file index
    if output_fileIndex_branch_name:
        file_index = array('i', [0])
        output_tree.Branch(output_fileIndex_branch_name, file_index, f"{output_fileIndex_branch_name}/I")

    # Copy entries from chain to the new tree, updating fileIndex branch as needed
    current_file_index = -1

    # Create a TTreeFormula for the cut string
    if cut_string.upper() != "NONE":
        ttfTreecut = TTreeFormula("ttfTreecut", cut_string, chain.GetTree())

    for entry_num in tqdm(range(chain.GetEntries()), ascii=' >=', desc="Merging entries", colour='green'):
        chain.GetEntry(entry_num)

        # Update the file index when switching to a new file
        if (output_fileIndex_branch_name) and (chain.GetTreeNumber() != current_file_index):
            current_file_index = chain.GetTreeNumber()
            file_index[0] = current_file_index

        # Apply the cut string if provided
        if cut_string.upper() != "NONE":
            ttfTreecut.UpdateFormulaLeaves()  # Update the formula with the new tree
            if not ttfTreecut.EvalInstance():
                continue

        # Fill the new tree
        output_tree.Fill()

    # Write the cloned tree to the output file
    output_tree.Write()
    output_root_file.Close()

    logger.info(f"Successfully merged {len(input_files)} files into {output_file} as tree '{output_tree_name}'")


def get_parser() -> argparse.ArgumentParser:
    """
    Parses command-line arguments using argparse.

    Returns:
        argparse.Namespace: Parsed arguments with values.
    """
    parser = argparse.ArgumentParser(description="Merge multiple ROOT files into one with a specified tree.")
    parser.add_argument('--input-files', nargs='+', required=True, help='Path to the input ROOT files (space-separated list)')
    parser.add_argument('--input-tree-name', default='DecayTree', help='Name of the tree to be merged (default: DecayTree)')
    parser.add_argument('--output-file', required=True, help='Path to the output ROOT file')
    parser.add_argument('--output-tree-name', default='DecayTree', help='Name of the tree to be merged (default: DecayTree)')
    parser.add_argument('--save-common-branches-only', type=bool, default=True, help='Save only the branches common across all input files')
    parser.add_argument('--default-missing-value', type=float, default=-9999, help='Default value for missing branches (default: -9999)')
    parser.add_argument('--output-fileIndex-branch-name', default='fileIndex', help='Name of the file index branch (default: fileIndex)')
    parser.add_argument('--cut-string', default='NONE', type=str, help='Cut string to apply to the input tree (default: None)')

    return parser


def main(args=None):
    if args is None:
        args = get_parser().parse_args()
    file_merger(**vars(args))


if __name__ == '__main__':
    # Batch mode
    r.gROOT.SetBatch(True)

    ########################
    main()

    # Enable multi-threading
    # r.ROOT.EnableImplicitMT(max(cpu_count() // 2, 1))

    # main_file_dir = '/home/uzh/wjie/repository/RLcMuonic2016/output/v1r0/tuple/fullSim/selectChannels'
    # file_merger(
    #     input_files=[
    #         f'{main_file_dir}/MC_Lb_Lc2593taunu/MC_Lb_Lc2593taunu_2016_Down_selected_branchAdded_Kenriched.root',
    #         f'{main_file_dir}/MC_Lb_Lc2593Ds/MC_Lb_Lc2593Ds_2016_Up_selected_branchAdded_Kenriched.root',
    #         f'{main_file_dir}/MC_Lb_LcDs/MC_Lb_LcDs_2016_Down_selected_branchAdded_Lcpipi.root',
    #     ],
    #     input_tree_name="DecayTree",
    #     output_file="tmp_output/merged_output.root",
    #     output_tree_name="DecayTree",
    #     save_common_branches_only=True,
    #     default_missing_value=-9999,
    #     output_fileIndex_branch_name="fileIndex",
    # )

    # exit(1)
    ########################
