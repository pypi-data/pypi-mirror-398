'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-12-06 08:00:27 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-11-07 11:31:30 +0100
FilePath     : cli.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

# analysis_tool/cli.py

import argparse
import sys
import importlib
from typing import Dict, Optional, Callable, List, Type


# Import modules
from . import apply_selection
from . import file_merger
from . import add_multiple_candidate_label
from . import track_combination_mass_calculator
from .reweight import reweighting, apply_weights
from .MVA.TMVA import train_tmva, apply_bdt_selection
from .MVA.XGBoost import search_optimal_hyperparameter, train_xgboost_model, add_xgboost_info
from .plotter import (
    compare_distributions,
    compare_distributions_classicalWay,
    Plot_BeforeAfter_Weights_comparison,
    Plotter,
)

from .bootstrap import bootstrap_sample

# from .PIDcorrection import PIDCorr, PIDGen


def remove_help_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Removes '-h' and '--help' arguments from the given parser.

    Args:
        parser: The argument parser to modify
    """
    actions = parser._actions[:]
    for action in actions:
        if set(action.option_strings) == {'-h', '--help'}:
            parser._remove_action(action)


def register_subcommand(
    subparsers: argparse._SubParsersAction,
    name: str,
    description: str,
    parent_parser: Optional[argparse.ArgumentParser] = None,
    func: Optional[Callable] = None,
) -> argparse.ArgumentParser:
    """
    Registers a subcommand with the given parameters.

    Args:
        subparsers: The subparsers object from argparse
        name: The name of the subcommand
        description: A brief description of the subcommand
        parent_parser: A parent parser for shared arguments
        func: The function to execute for this subcommand

    Returns:
        The created subparser
    """
    if parent_parser:
        remove_help_arguments(parent_parser)  # Remove help options to prevent conflicts
    parser = subparsers.add_parser(
        name,
        description=description,
        parents=[parent_parser] if parent_parser else [],
        add_help=True,  # Allow subparser to add its own help
    )
    if func:
        parser.set_defaults(func=func)
    return parser


def register_command_group(
    subparsers: argparse._SubParsersAction,
    commands: List[Dict],
) -> None:
    """
    Register a group of related commands at once.

    Args:
        subparsers: The subparsers object from argparse
        commands: List of command dictionaries with name, description, parent_parser, and func
    """
    for cmd in commands:
        register_subcommand(
            subparsers,
            name=cmd['name'],
            description=cmd['description'],
            parent_parser=cmd.get('parent_parser'),
            func=cmd.get('func'),
        )


def main():
    parser = argparse.ArgumentParser(
        prog='analysis_tool',
        description='Command-line interface for various analysis tools.',
        add_help=True,
    )
    subparsers = parser.add_subparsers(
        title='Available commands',
        dest='command',
        description='Use "<command> --help" for more information about each command',
    )

    # Define command groups
    data_processing_commands = [
        {
            'name': 'apply_selection',
            'description': 'Apply selection criteria to the data',
            'parent_parser': apply_selection.get_parser(),
            'func': apply_selection.main,
        },
        {
            'name': 'file_merger',
            'description': 'Merge multiple files into a single file',
            'parent_parser': file_merger.get_parser(),
            'func': file_merger.main,
        },
        {
            'name': 'add_candidate_label',
            'description': 'Add multiple candidate labels',
            'parent_parser': add_multiple_candidate_label.get_parser(),
            'func': add_multiple_candidate_label.main,
        },
        {
            'name': 'track_combination_mass_calculator',
            'description': 'Calculate the invariant mass of track combinations',
            'parent_parser': track_combination_mass_calculator.get_parser(),
            'func': track_combination_mass_calculator.main,
        },
        {
            'name': 'bootstrap_sample',
            'description': 'Bootstrap sample for the data',
            'parent_parser': bootstrap_sample.get_parser(),
            'func': bootstrap_sample.main,
        },
    ]

    reweighting_commands = [
        {
            'name': 'reweighting',
            'description': 'Reweight the data',
            'parent_parser': reweighting.get_parser(),
            'func': reweighting.main,
        },
        {
            'name': 'apply_weights',
            'description': 'Apply weights to the data',
            'parent_parser': apply_weights.get_parser(),
            'func': apply_weights.main,
        },
    ]

    mva_commands = [
        # TMVA
        {
            'name': 'train_tmva',
            'description': 'Train TMVA BDT',
            'parent_parser': train_tmva.get_parser(),
            'func': train_tmva.main,
        },
        {
            'name': 'apply_bdt_selection',
            'description': 'Apply BDT selection',
            'parent_parser': apply_bdt_selection.get_parser(),
            'func': apply_bdt_selection.main,
        },
        # XGBoost
        {
            'name': 'search_optimal_hyperparameter',
            'description': 'Search optimal hyperparameters for XGBoost model',
            'parent_parser': search_optimal_hyperparameter.get_parser(),
            'func': search_optimal_hyperparameter.main,
        },
        {
            'name': 'train_xgboost_model',
            'description': 'Train XGBoost model',
            'parent_parser': train_xgboost_model.get_parser(),
            'func': train_xgboost_model.main,
        },
        {
            'name': 'add_xgboost_info',
            'description': 'Add XGBoost info to the data',
            'parent_parser': add_xgboost_info.get_parser(),
            'func': add_xgboost_info.main,
        },
    ]

    plotting_commands = [
        {
            'name': 'compare_distributions',
            'description': 'Plot distribution comparisons between samples',
            'parent_parser': compare_distributions.get_parser(),
            'func': compare_distributions.main,
        },
        {
            'name': 'compare_distributions_classicalWay',
            'description': 'Plot distribution comparisons in a classical way',
            'parent_parser': compare_distributions_classicalWay.get_parser(),
            'func': compare_distributions_classicalWay.main,
        },
        {
            'name': 'Plot_BeforeAfter_Weights_comparison',
            'description': 'Plot distribution comparisons before and after weighting',
            'parent_parser': Plot_BeforeAfter_Weights_comparison.get_parser(),
            'func': Plot_BeforeAfter_Weights_comparison.main,
        },
        {
            'name': 'Plotter',
            'description': 'General plotting tool for distribution comparisons',
            'parent_parser': Plotter.get_parser(),
            'func': Plotter.main,
        },
    ]

    # Register all command groups
    for commands in [
        data_processing_commands,
        reweighting_commands,
        mva_commands,
        plotting_commands,
    ]:
        register_command_group(subparsers, commands)

    # Parse and execute
    args = parser.parse_args()

    if hasattr(args, 'func'):
        # Create a clean copy of args without internal attributes
        args_dict = {k: v for k, v in vars(args).items() if not k.startswith('_') and k not in ('command', 'func')}

        # Call the function with the cleaned args
        args.func(argparse.Namespace(**args_dict))
    else:
        parser.print_help()
        sys.exit(1)

    # # ---------------- Register PID correction subcommands directly ----------------
    # register_subcommand(
    #     subparsers,
    #     name='PIDCorr',
    #     description='PID correction tool for PID variables (PIDCorr).',
    #     parent_parser=PIDCorr.get_parser(),
    #     func=PIDCorr.main,
    # )

    # register_subcommand(
    #     subparsers,
    #     name='PIDGen',
    #     description='PID correction tool for PID variables (PIDGen).',
    #     parent_parser=PIDGen.get_parser(),
    #     func=PIDGen.main,
    # )


if __name__ == '__main__':
    main()
