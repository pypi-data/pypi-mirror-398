'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-03-19 19:52:05 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-05-18 07:22:43 +0200
FilePath     : bootstrap_sample.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import os
import argparse

import ROOT
from ROOT import gROOT
from pathlib import Path
from scipy.stats import norm, poisson

import math
import uproot as ur
import pandas as pd
import numpy as np

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


# A simple helper function to fill a test tree: this makes the example stand-alone.
def generate_test_sample(output_tree_name, output_file):
    rdf = ROOT.RDataFrame(5)
    rdf.Define("b1", "(double) rdfentry_").Define("b2", "(int) rdfentry_ * rdfentry_").Define("weight", "(int) pow(-1, rdfentry_)").Snapshot(output_tree_name, output_file)


def split_dataset(pdf: pd.DataFrame, spectator_requirement: str):
    """Split the dataset based on the selection requirement.

    Args:
        pdf (pd.DataFrame): The input DataFrame.
        spectator_requirement (str): The selection requirement for the spectator columns.

    Returns:
        pd.DataFrame: The DataFrame that satisfies the requirement.
        pd.DataFrame: The DataFrame that does not satisfy the requirement.
    """
    if spectator_requirement and spectator_requirement.upper() != 'NONE':
        pdf_to_append = pdf.query(spectator_requirement)
        pdf_to_bootstrap = pdf.drop(pdf_to_append.index)

        logger.info(f'Dataset is splitted based on spectator requirement "{spectator_requirement}"')

        logger.info('Pdf to bootstrap')
        rprint(pdf_to_bootstrap)

        logger.info('Pdf to append')
        rprint(pdf_to_append)

    else:
        pdf_to_append = pd.DataFrame()
        pdf_to_bootstrap = pdf

    return pdf_to_bootstrap, pdf_to_append


def bootstrap_sample(
    input_file: str,
    input_tree_name: str,
    output_file: str,
    output_tree_name: str,
    nEvts: int = -1,
    replace: bool = True,
    gauss_variation_std_sigma: float = 0,
    spectator_requirement: str = 'NONE',  # The selection requirement for the spectator columns
):
    """Use bootstrap method to sample original dataset, apply Gaussian variation to the total yields, and
    exclude certain events based on selection requirements.

    Args:
        input_file (str): Path to the input file.
        input_tree_name (str): Name of the input tree.
        output_file (str): Path to the output file.
        output_tree_name (str): Name of the output tree.
        nEvts (int, optional): Number of events to sample. Defaults to -1.
        replace (bool, optional): Whether to sample with replacement. Defaults to True.
        gauss_variation_std_sigma (float, optional): Scale factor for the Gaussian variation's std. deviation. Defaults to 0.
        spectator_requirement (str, optional): The selection requirement for the spectator columns, which will not be sampled, but appended to the output. Defaults to 'NONE'.
    """

    ROOT.EnableImplicitMT()
    gROOT.SetBatch(1)

    # We open the file and get the tree as a pandas.DataFrame
    rtf = ur.open(f"{input_file}:{input_tree_name}")
    pdf_original = rtf.arrays(library="pd")
    logger.info('Pdf before sampling')
    rprint(pdf_original)

    # Split the dataset based on the selection requirement, if provided
    pdf_to_bootstrap, pdf_to_append = split_dataset(pdf_original, spectator_requirement)

    # ------------------------------------------------
    # Determine the number of events to sample from pdf_to_bootstrap instead of pdf_original
    # If nEvts is -1, sample the same number of events as the original dataset
    total_events = len(pdf_to_bootstrap)
    nEvts = nEvts if nEvts != -1 else total_events

    # Apply Gaussian variation to the total yields
    if gauss_variation_std_sigma != 0:
        assert gauss_variation_std_sigma > 0, "The standard deviation scale factor must be positive"
        # Scale the standard deviation by the specified factor. This is based on the principle
        # that statistical fluctuations can be approximated by sqrt(N), where N is the number
        # of events. By multiplying this by 'gauss_variation_std_sigma', we simulate increased
        # or decreased statistical variations.
        gauss_variation_std = gauss_variation_std_sigma * math.sqrt(nEvts)
        if gauss_variation_std_sigma == 1:
            varied_total_events = round(poisson.rvs(mu=nEvts))  # use poisson distribution
            logger.info(f'INFO::bootstrap_sample: use poisson distribution, nEvts(bootstrap): {nEvts}, varied_total_events: {varied_total_events}')
        else:
            varied_total_events = round(norm.rvs(loc=nEvts, scale=gauss_variation_std))  # use gaussian distribution
            logger.info(f'INFO::bootstrap_sample: use gaussian distribution, nEvts(bootstrap): {nEvts}, gauss_variation_std: {gauss_variation_std:.3f}, varied_total_events: {varied_total_events}')

        # Ensure that the varied total is not negative, setting a minimum of 1 event.
        if varied_total_events <= 0:
            logger.warning(f"The varied total number of events is negative or zero ([bold yellow]{varied_total_events}[/]). Setting it to [bold yellow]1[/].", extra={"markup": True})
        nEvts = max(1, varied_total_events)

    # ------------------------------------------------

    # Use the pandas.DataFrame.sample method to do the bootstrap sampling
    pdf_after = pdf_to_bootstrap.sample(n=nEvts, replace=replace)

    # # We use the pandas.DataFrame.sample method to do the bootstrap sampling
    # pdf_after = pdf_to_bootstrap.sample(frac=1, replace=replace) if nEvts == -1 else pdf_to_bootstrap.sample(n=nEvts, replace=replace)

    # Append the events that satisfied the requirement to the bootstrapped sample
    final_pdf = pd.concat([pdf_after, pdf_to_append])

    if pdf_to_append.empty:
        logger.info('Pdf after sampling')
    else:
        logger.info('Pdf after sampling and appending')

    rprint(final_pdf)

    # We create a new file and write the new tree to it
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with ur.recreate(output_file) as ofile:
        ofile[output_tree_name] = final_pdf


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", help="Path to the input file")
    parser.add_argument("--input-tree-name", default="DecayTree", help="Name of the input tree")

    parser.add_argument("--output-file", help="Output ROOT file")
    parser.add_argument("--output-tree-name", default="DecayTree", help="Name of the output tree")

    parser.add_argument(
        "--nEvts",
        type=int,
        default=-1,
        help="Number of events to sample. If -1, sample all events. Default: -1",
    )
    parser.add_argument(
        "--replace",
        type=bool,
        default=True,
        help="Whether to sample with replacement. Default: True",
    )
    parser.add_argument(
        "--gauss-variation-std-sigma",
        type=float,
        default=0,
        help="The scale factor to apply to the standard deviation of the Gaussian variation. Default: 0",
    )
    parser.add_argument(
        "--spectator-requirement",
        default='NONE',
        help="The selection requirement for the spectator columns. Default: NONE",
    )

    return parser


def main(args=None):
    if args is None:
        args = get_parser().parse_args()
    bootstrap_sample(**vars(args))


if __name__ == "__main__":
    main()
    # # We prepare an input tree to run on
    # input_file = "bootstrap_test.root"
    # input_tree_name = 'DecayTree'

    # # generate root file for test purpose
    # generate_test_sample(input_tree_name, input_file)

    # output_file = './tmp/bootstrap_strapped.root'
    # output_tree_name = 'DecayTree'

    # # use bootstrap to sample the tree
    # print("\n--- 1. Sample the tree with the same number of events as the original dataset")
    # bootstrap_sample(input_file, input_tree_name, output_file, output_tree_name, replace=True)

    # print("\n--- 2. Sample the tree with the same number of events as the original dataset, but with Gaussian variation")
    # bootstrap_sample(input_file, input_tree_name, output_file, output_tree_name, replace=True, gauss_variation_std_sigma=1)

    # print("\n--- 3. Sample the tree with the same number of events as the original dataset, but with Gaussian variation, and exclude events with weight < 0")
    # bootstrap_sample(input_file, input_tree_name, output_file, output_tree_name, replace=True, gauss_variation_std_sigma=1, spectator_requirement='(weight < 0)')

    # exit(1)
    ##############################
