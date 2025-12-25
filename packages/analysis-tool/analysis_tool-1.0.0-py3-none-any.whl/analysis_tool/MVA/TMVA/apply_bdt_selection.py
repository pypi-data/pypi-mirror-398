'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-12-06 14:06:45 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-04-17 02:52:55 +0200
FilePath     : apply_bdt_selection.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import os
import argparse
from pathlib import Path

import yaml
from array import array
from ROOT import ROOT, RDataFrame, gROOT, TMVA, TFile, TChain, TMath, PyConfig, addressof, TString

from tqdm import tqdm
from rich import print as rprint


# Use rich backend for logging
import logging
from rich.logging import RichHandler

# Configure rich logging globally
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%x %X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)  # or "DEBUG"/"WARNING" as needed
logger = logging.getLogger(__name__)


INVALID_VALUE = -9999

from .train_tmva import MODULO_LARGE_VALUE


def read_from_yaml(mode: str, selection_files: list) -> dict:
    """
    Read and merge configuration dictionaries from multiple YAML files under a given mode key.

    Parameters
    ----------
    mode : str
        The key in the YAML files that corresponds to the relevant configuration.
    selection_files : list of str or Path
        Paths to YAML files containing the BDT configuration.

    Returns
    -------
    dict
        Merged dictionary from all specified files for the given mode.
    """
    bdt_dict = {}
    for file_path in selection_files:
        file_path = Path(file_path)
        if not file_path.is_file():
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        with file_path.open('r') as stream:
            file_data = yaml.safe_load(stream)
            if mode not in file_data:
                raise KeyError(f"Mode '{mode}' not found in {file_path}")
            # Merge dictionaries (requires Python 3.9+ for |= operator)
            bdt_dict |= file_data[mode]
    return bdt_dict


def apply_bdt_selection(
    input_files: list,
    input_tree_name: str,
    output_file: str,
    output_tree_name: str,
    mode: str,
    bdt_branches: list,
    bdt_cut_file: list,
    tmva_weight_dir: str,
    bdt_method_name: str,
    bdt_mode: str,
    bdt_year: str,
    output_mva_branch_name: str = '',
):
    """
    Apply a BDT selection to input ROOT trees and save the filtered events along with a BDT score branch.

    Parameters
    ----------
    input_files : list of str
        Paths to input ROOT files.
    input_tree_name : str
        Name of the input tree inside the ROOT files.
    output_file : str
        Path to the output ROOT file to create.
    output_tree_name : str
        Name of the output tree inside the output ROOT file.
    mode : str
        Mode key to read BDT conversion variables from YAML files.
    bdt_branches : list of str
        List of YAML files containing BDT variable definitions.
    bdt_cut_file : list of str
        List of YAML files containing BDT cut definitions. If None or empty, no cut is applied.
    tmva_weight_dir : str
        Directory containing the TMVA weight files.
    bdt_method_name : str
        Name of the BDT method.
    bdt_mode : str
        Mode key to read BDT cut values from the cut YAML files.
    bdt_year : str
        Year key to read BDT cut values corresponding to the given year.
    output_mva_branch_name : str
        Name of the output branch containing the BDT score. If empty, the BDT method name is used.
    """

    # Read variable definitions from YAML
    bdt_conversion = read_from_yaml(mode, bdt_branches)

    # Read the BDT cut value if provided
    if bdt_cut_file and len(bdt_cut_file) > 0:
        bdt_cut = read_from_yaml(bdt_mode, bdt_cut_file).get(bdt_year)
        if bdt_cut is None:
            raise ValueError(f"No BDT cut found for year '{bdt_year}' in the provided cut file(s).")
        logger.info(f"Applying BDT cut: {bdt_cut}")
    else:
        bdt_cut = None
        logger.info("No BDT cut is applied")

    # Locate the TMVA weight file
    tmva_weight_path = Path(tmva_weight_dir)
    if (tmva_weight_path / 'dataset').exists():
        tmva_weight_path = tmva_weight_path / 'dataset'

    tmva_weight_file = None
    if tmva_weight_path.is_dir():
        for f in tmva_weight_path.iterdir():
            if f.name.endswith(f"{bdt_method_name}.weights.xml"):
                tmva_weight_file = f
                logger.info(f"Found TMVA weight file: {tmva_weight_file}")
                break

    if tmva_weight_file is None:
        raise FileNotFoundError(f"Could not find tmva weight file '{bdt_method_name}.weights.xml' in {tmva_weight_path}")

    # Check if folding (cross-validation) is applied
    folding = "TMVACrossValidation" in str(tmva_weight_file)

    # Initialize TMVA Reader
    TMVA.Tools.Instance()
    reader = TMVA.Reader()

    # Set up arrays for MVA training variables
    mva_vars = {}
    for var in bdt_conversion.keys():
        mva_vars[var] = array('f', [INVALID_VALUE])
        reader.AddVariable(var, mva_vars[var])

    # Add spectator if folding
    event_vars = {}
    if folding:
        event_vars["eventNumber"] = array('f', [INVALID_VALUE])
        # Note: The spectator formula is evaluated in TMVA, here we just register the variable
        reader.AddSpectator(f"eventNumber := eventNumber % {MODULO_LARGE_VALUE}", event_vars["eventNumber"])

    # Book the MVA method
    reader.BookMVA(bdt_method_name, str(tmva_weight_file))

    # Set up input chain
    input_tree = TChain(input_tree_name)
    for f in input_files:
        if not Path(f).is_file():
            raise FileNotFoundError(f"Input ROOT file not found: {f}")
        input_tree.Add(f)
        logger.info(f"Added file {f} to the chain")

    # Prepare the output file and tree
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_tuple_file = TFile.Open(str(output_path), 'recreate')
    output_tuple_file.cd()

    # Create a cloneccloneopy tree with no entries to allow adding branches
    output_tree = input_tree.CloneTree(0)

    # Create a struct for the BDT variable and add a branch
    gROOT.ProcessLine('struct bdt_vars { Double_t bdtVar; };')
    from ROOT import bdt_vars

    bdt_struct = bdt_vars()

    output_mva_branch_name = output_mva_branch_name or bdt_method_name
    if output_mva_branch_name in [b.GetName() for b in output_tree.GetListOfBranches()]:
        raise ValueError(f"Output branch name '{output_mva_branch_name}' already exists in the output tree.")

    bdt_branch = output_tree.Branch(output_mva_branch_name, addressof(bdt_struct, 'bdtVar'), f'{output_mva_branch_name}/D')

    # Loop over entries and fill in BDT response
    num_entries = input_tree.GetEntries()

    for i in tqdm(range(num_entries), total=num_entries, ascii=' >=', desc="Adding MVA branches and applying BDT cut"):
        input_tree.GetEntry(i)

        # Fill the MVA variables
        for var in bdt_conversion.keys():
            mva_vars[var][0] = getattr(input_tree, var)

        if folding:
            # No need for further conversion, just pass the event number
            # event_vars["eventNumber"] = getattr(input_tree, "eventNumber")
            # rprint(f"Event number: {event_vars['eventNumber']}")

            event_vars["eventNumber"][0] = getattr(input_tree, "eventNumber") % MODULO_LARGE_VALUE
            # # rprint(f"Event number: {event_vars['eventNumber'][0]}")
            # if event_vars["eventNumber"][0] < 0:
            #     raise ValueError(f"Event number is negative: {event_vars['eventNumber'][0]}")

        bdt_struct.bdtVar = reader.EvaluateMVA(bdt_method_name)

        # Apply the BDT cut if given
        if bdt_cut is not None and bdt_struct.bdtVar < float(bdt_cut):
            continue

        # Save event if passed the cut
        output_tree.Fill()

    if bdt_cut:
        logger.info(f"The BDT cut was applied, {output_tree.GetEntries()} events passed the cut, efficiency: {output_tree.GetEntries() / num_entries * 100:.2f}%")

    # Rename the output tree if necessary
    if input_tree_name != output_tree_name:
        output_tree.SetName(output_tree_name)
        logger.info(f"Changed the name of the output tree to {output_tree_name}")

    # save the tree
    output_tree.AutoSave('saveself')
    output_tuple_file.Close()

    logger.info(f"BDT selection application completed successfully, saved to {output_path}")


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-files', nargs='+', help='Path to the input files')
    parser.add_argument('--input-tree-name', default='DecayTree', help='Name of the tree')
    parser.add_argument('--output-file', help='Output ROOT file')
    parser.add_argument('--output-tree-name', default='DecayTree', help='Name of the tree')
    parser.add_argument('--mode', help='Name of the selection in yaml')
    parser.add_argument('--bdt-mode', help='Name of the bdt-selection in yaml')
    parser.add_argument('--bdt-year', help='Year of the bdt-selection in yaml')
    parser.add_argument('--bdt-branches', nargs='+', required=True, help='Yaml files with selection')
    parser.add_argument('--bdt-cut-file', nargs='+', required=False, default=[], help='Yaml file with bdt cut to be applied, if not given, no cut is applied')
    parser.add_argument('--tmva-weight-dir', help='File to read TMVA weight from')
    parser.add_argument('--bdt-method-name', default='BDTG3', required=True, type=str, help='Choose which BDT to apply')

    parser.add_argument('--output-mva-branch-name', default='', help='Name of the output branch')

    return parser


def main(args=None):
    if args is None:
        args = get_parser().parse_args()
    apply_bdt_selection(**vars(args))


if __name__ == '__main__':
    main()
