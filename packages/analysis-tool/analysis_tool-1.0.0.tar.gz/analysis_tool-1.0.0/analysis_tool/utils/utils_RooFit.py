'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-06-19 16:16:39 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-07-01 03:31:40 +0200
FilePath     : utils_RooFit.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import os
import math
import json, yaml
import argparse
import cppyy
from array import array
import uuid
import multiprocessing
from fnmatch import fnmatch

from pathlib import Path
import colorama
import warnings

import uproot as ur
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import product
from tqdm import tqdm
from typing import Any, List, Dict, Optional, Union, Tuple


import ROOT as r
from ROOT import addressof
from ROOT import (
    kDashed,
    kRed,
    kGreen,
    kBlue,
    kBlack,
    kTRUE,
    kFALSE,
    gPad,
    std,
    TArrow,
    TGraph,
    TLine,
)
from ROOT import (
    TMath,
    TAxis,
    TH1,
    TH1F,
    TLegend,
    TLatex,
    TPaveText,
    TROOT,
    TSystem,
    TCanvas,
    TChain,
    TFile,
    TTree,
    TTreeFormula,
    TObject,
    gROOT,
    gStyle,
)
from ROOT import ROOT, RDataFrame, vector, gInterpreter, gSystem
from ROOT import (
    RooFit,
    RooFitResult,
    RooAbsData,
    RooAbsPdf,
    RooArgSet,
    RooArgList,
    RooAbsDataStore,
    RooAddModel,
    RooAddPdf,
    RooAddition,
    RooCBShape,
    RooChebychev,
    RooConstVar,
    RooDataSet,
    RooExponential,
    RooFFTConvPdf,
    RooFormulaVar,
    RooGaussian,
    #    RooGlobalFunc,
    RooHypatia2,
    RooMinimizer,
    RooPlot,
    RooPolynomial,
    RooProdPdf,
    RooRealVar,
    RooVoigtian,
    RooStats,
)


# Logging setup
from rich import print as rprint
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


from warnings import warn

from ..correlation.matrixHelper import plot_correlation_matrix, write_correlation_matrix_latex
from .utils_json import read_json
from .utils_ROOT import save_pic_from_tcanvas
from .utils_general import disentangle_expression_ast


# =============================================================#
# ----------------------RooFit area----------------------------#


# * ------------------------------ Create RooDataSet ----------------------------- #
def create_dataset_with_ttreeformula(
    sig_tree: TTree,
    input_fit_branch: str,
    input_weight_branch: str,
    *,
    data_name: str = None,
    fit_var: Optional[Union[RooRealVar, str]] = None,
    weight_var: Optional[Union[RooRealVar, str]] = None,
) -> Tuple[RooDataSet, RooRealVar, RooRealVar]:
    """
    Create RooDataSet using TTreeFormula for weight evaluation.

    Args:
        sig_tree: [TTree] Input TTree
        input_fit_branch: [str] Name of the branch to fit (mass variable)
        input_weight_branch: [str] Name of weight branch or formula expression
        data_name: [str] Name of the dataset (default: f'ds_{input_fit_branch}')
        fit_var: [RooRealVar|str] Fit variable as RooRealVar or string name (default: None)
        weight_var: [RooRealVar|str] Weight variable as RooRealVar or string name (default: None)

    Returns:
        Tuple containing:
        - [RooDataSet] RooDataSet with proper weights applied
        - [RooRealVar] RooRealVar for fit variable
        - [RooRealVar] RooRealVar for weight variable (dummy for unweighted case, where the weight variable constructed as a constant variable with value 1.0)
    """

    # Validate inputs
    if not sig_tree or sig_tree.GetEntries() == 0:
        raise RuntimeError("Tree is empty or invalid")

    if not sig_tree.GetBranch(input_fit_branch):
        raise ValueError(f"Branch '{input_fit_branch}' not found in tree")

    if not data_name:
        data_name = f'ds_{input_fit_branch}'

    # Helper function to create or validate fit variable
    def _create_fit_variable() -> RooRealVar:
        if fit_var is None:
            return RooRealVar(input_fit_branch, input_fit_branch, math.floor(sig_tree.GetMinimum(input_fit_branch)), math.ceil(sig_tree.GetMaximum(input_fit_branch)))
        elif isinstance(fit_var, str):
            return RooRealVar(fit_var, fit_var, math.floor(sig_tree.GetMinimum(input_fit_branch)), math.ceil(sig_tree.GetMaximum(input_fit_branch)))
        elif isinstance(fit_var, RooRealVar):
            return fit_var
        else:
            raise ValueError(f"Invalid fit variable: {fit_var}, expected RooRealVar or str, got {type(fit_var)}")

    # Helper function to create weight variable
    def _create_weight_variable(var_name: str, title: str = "") -> RooRealVar:
        if weight_var is None:
            return RooRealVar(var_name, title, -1e6, 1e6)
        elif isinstance(weight_var, str):
            return RooRealVar(weight_var, title, -1e6, 1e6)
        elif isinstance(weight_var, RooRealVar):
            return weight_var
        else:
            raise ValueError(f"Invalid weight variable: {weight_var}, expected RooRealVar or str, got {type(weight_var)}")

    # Create mass variable
    roo_fit_var = _create_fit_variable()

    # Check if weights are used
    if not input_weight_branch or input_weight_branch.upper() in ['NONE', 'ONE', '1']:
        # Unweighted case
        logger.info(f"Creating unweighted RooDataSet with variable: {input_fit_branch}")
        data = RooDataSet(data_name, data_name, RooArgSet(roo_fit_var), RooFit.Import(sig_tree))

        # Create dummy weight variable for consistent return signature
        unique_id = str(uuid.uuid4().hex)[:8]
        roo_weight_var = _create_weight_variable(f"weight_dummy_{unique_id}", "Dummy weight (unweighted)")
        roo_weight_var.setVal(1.0)
        roo_weight_var.setConstant(True)

    else:
        # Weighted case
        weight_var_name = weight_var if isinstance(weight_var, str) else (weight_var.GetName() if isinstance(weight_var, RooRealVar) else "weight")
        roo_weight_var = _create_weight_variable(weight_var_name, f'Expression: {input_weight_branch}')

        # Create and validate formula
        weight_formula = TTreeFormula(f"weight_formula_for_{weight_var_name}", input_weight_branch, sig_tree)
        if weight_formula.GetNdim() == 0:
            raise ValueError(f"Invalid formula: {input_weight_branch}")

        # Find weight range by evaluating formula for all entries
        n_entries = sig_tree.GetEntries()
        weight_values = np.empty(n_entries, dtype=np.float64)
        for i in range(n_entries):
            sig_tree.GetEntry(i)
            weight_values[i] = weight_formula.EvalInstance()

        # Set weight variable with proper range before creating dataset
        if not isinstance(weight_var, RooRealVar):
            weight_min, weight_max = np.min(weight_values), np.max(weight_values)
            range_min, range_max = math.floor(weight_min), math.ceil(weight_max)
            roo_weight_var.setRange(range_min, range_max)
            logger.info(f"Weight range set: [{range_min}, {range_max}] for variable: {roo_weight_var.GetName()}")

        # Create dataset
        data = RooDataSet(data_name, data_name, RooArgSet(roo_fit_var, roo_weight_var), RooFit.WeightVar(roo_weight_var))

        # Pass through tree to fill dataset
        logger.info(f"Filling RooDataSet with: \n variables: {input_fit_branch} ({input_fit_branch}) \n weights: {weight_var_name} ({input_weight_branch})")
        for i in tqdm(range(sig_tree.GetEntries()), desc="Filling RooDataSet with weights", colour="green", ascii=" >━", leave=False):
            sig_tree.GetEntry(i)

            # Set mass value
            roo_fit_var.setVal(getattr(sig_tree, input_fit_branch))

            # Add entry with both mass and weight
            data.add(row=RooArgSet(roo_fit_var), weight=float(weight_values[i]))

    logger.info(f"Dataset created: {data.GetName()} with {data.numEntries()} entries, the sum of weights is {data.sumEntries()}")
    return data, roo_fit_var, roo_weight_var


# * ------------------------------ Read parameters ----------------------------- #


def read_params(params_file: str) -> dict:
    """Common helper
    Read parameters from json file.
        params_file: [str] the address to the parameter file.
    """
    with open(params_file, "r") as stream:
        return json.load(stream)


def fix_param(par_name: str, mc_param: dict[str, float], pdfPars_Arg: RooArgSet) -> None:
    """
    Set the parameter to be fixed
        par_name: [str] the name of the parameter to be fixed
        mc_param: [dict] the parameter to be fixed (read from previous fit result)
        pdfPars_Arg: [RooArgSet] the RooArgSet containing parameters
    """
    par = pdfPars_Arg.find(par_name)
    if par:
        par.setVal(mc_param["Value"])
        par.setConstant(True)
        logger.info(f"Setting parameter {par_name} to constant with value {mc_param['Value']}")
    else:
        logger.warning(f"Could not find parameter {par_name} in the RooFit RooArgSet")


def extract_matching_params(params: Union[RooArgSet, RooArgList], pattern_list: List[str], fuzzy_match: bool = True) -> RooArgSet:
    """
    Extract RooRealVar objects from RooArgSet/RooArgList based on pattern matching

    Args:
        params: RooArgSet or RooArgList containing parameters to search
        pattern_list: List of string patterns to match against parameter names
        fuzzy_match: Whether to use fuzzy matching (fnmatch) or exact matching

    Returns:
        RooArgSet containing matched RooRealVar parameters
    """
    # Check if pattern list is empty
    if not pattern_list or all(item == "" for item in pattern_list):
        return RooArgSet()

    if isinstance(params, RooArgSet):
        paramsList = RooArgList(params)

    matched_params = RooArgSet()

    # Iterate through RooArgSet
    for i in range(paramsList.getSize()):
        param = paramsList.at(i)
        if isinstance(param, RooRealVar):
            param_name = param.GetName()

            # Check if parameter matches any pattern
            for pattern in pattern_list:
                if fuzzy_match:
                    if fnmatch(param_name, pattern):
                        add_unique_to_argset(matched_params, param)
                        break
                else:
                    if pattern == param_name:
                        add_unique_to_argset(matched_params, param)
                        break

    return matched_params


def params_to_fix_helper_json(
    params_to_fix_file: str,
    pdfPars_Arg: RooArgSet,
    params_to_fix_list: List[str],
    fuzzyMatch: bool = True,
    dict_key: str = "Params",
) -> None:
    """params_to_fix helper
    Helper function to fix parameters with the value derived from MC conveniently.
    MC fit results are stored in json format.
        params_to_fix_file: [str] the path to where json file stored.
        pdfPars_Arg: [RooArgSet] the RooArgList format class which stores all variables used in PDF construction.
        params_to_fix_list: [list] a list referes to the variables need to be read from file and then be fixed
        fuzzyMatch: [bool] whether use fuzzy match mode.
    """
    # Check if params list is empty
    if all(item == "" for item in params_to_fix_list):
        return None

    # Read parameters from JSON file
    cat_params = read_json(params_to_fix_file, dict_key) if params_to_fix_file else None
    if not cat_params:
        logger.warning(f"Could not find parameters in the JSON file {params_to_fix_file}")
        return None

    # Extract matching parameters from the RooArgSet
    matching_params = extract_matching_params(pdfPars_Arg, params_to_fix_list, fuzzyMatch)

    # Fix each matching parameter
    for i in range(matching_params.size()):
        param = matching_params[i]
        param_name = param.GetName()

        # Find corresponding MC parameter
        mc_param_matches = [p for p in cat_params if p["Name"] == param_name]
        if mc_param_matches:
            mc_param = mc_param_matches[0]
            fix_param(param_name, mc_param, pdfPars_Arg)

    ##################################################
    # def find_param(param_toFind, fuzzyMatch, cat_params):
    #     # find the parameter to be fixed from previous fit result
    #     if fuzzyMatch:
    #         # support fuzzy matching
    #         mc_param_list = [p for p in cat_params if param_toFind in p['Name']]
    #         for mc_param in mc_param_list:
    #             par_name = mc_param['Name']

    #             if pdfPars_Arg.find(par_name):
    #                 return par_name

    ##################################################

    # # if fix parameters in the fit
    # for par in params_to_fix_list:
    #     if fuzzyMatch:
    #         # support fuzzy matching
    #         mc_param_list = [p for p in cat_params if fnmatch(p["Name"], par)]
    #         for mc_param in mc_param_list:
    #             par_name = mc_param["Name"]

    #             fix_param(par_name, mc_param, pdfPars_Arg)
    #             # if pdfPars_Arg.find(par_name):
    #             #     pdfPars_Arg.find(par_name).setVal(mc_param['Value'])
    #             #     pdfPars_Arg.find(par_name).setConstant(True)
    #             #     rprint(f"params_to_fix_helper_json::Setting parameter {par_name} to constant with value {mc_param['Value']}")
    #             # else:
    #             #     rprint(f"params_to_fix_helper_json::Could not find parameter {par_name} in the RooFit RooArgSet")
    #     else:
    #         # for par in params_to_fix_list:
    #         mc_param_matches = [p for p in cat_params if par in p["Name"]]
    #         if mc_param_matches:
    #             mc_param = mc_param_matches[0]
    #             par_name = mc_param["Name"]

    #             # par_name should be exactly the name stored in RooRealVar
    #             fix_param(par_name, mc_param, pdfPars_Arg)

    #             # if pdfPars_Arg.find(par_name):
    #             #     pdfPars_Arg.find(par_name).setVal(mc_param['Value'])
    #             #     pdfPars_Arg.find(par_name).setConstant(True)
    #             #     rprint(f"params_to_fix_helper_json::Setting parameter {par_name} to constant with value {mc_param['Value']}")
    #             # else:
    #             #     rprint(f"params_to_fix_helper_json::Could not find parameter {par_name} in the RooFit RooArgSet")


def params_to_fix_helper_func(
    params_to_fix_file: str,
    pdfPars_Arg: RooArgList,
    params_to_fix_list: list,
    fuzzyMatch: bool = True,
):
    """params_to_fix helper
    Helper function to fix parameters with the value derived from MC conveniently.
    MC fit results are stored in func format (stored by calling RooFit embedded writeToFile method).
        params_to_fix_file: [str] the path to where json file stored.
        pdfPars_Arg: [RooArgList] the RooArgList format class which stores all variables used in PDF construction.
        params_to_fix_list: [list] a list referes to the variables need to be read from file and then be fixed
        fuzzyMatch: [bool] whether use fuzzy match mode.
    """
    # Check input arguments
    if all(item == "" for item in params_to_fix_list):
        return None

    # Extract matching parameters
    matching_params = extract_matching_params(pdfPars_Arg, params_to_fix_list, fuzzyMatch)

    # Fix each matching parameter
    for i in range(matching_params.size()):
        param = matching_params[i]
        param_name = param.GetName()

        _party = pdfPars_Arg.find(param_name)
        # Read from params_to_fix_file and set them to be constant
        RooArgSet(_party).readFromFile(params_to_fix_file)
        _party.setConstant(True)
        logger.info(f"Setting parameter {_party.GetName()} to constant with value {_party.getVal()}")

    # # Read parameters by using ROOT embedded methods
    # pdfPars_List = RooArgList(pdfPars_Arg)
    # for par in params_to_fix_list:
    #     for i in range(pdfPars_List.getSize()):
    #         party = RooRealVar(pdfPars_List.at(i))

    #         if (fuzzyMatch and fnmatch(party.GetName(), par)) or (not fuzzyMatch and par == party.GetName()):
    #             _party = pdfPars_Arg.find(party.GetName())
    #             # Read from params_to_fix_file and set them to be constant
    #             RooArgSet(_party).readFromFile(params_to_fix_file)
    #             _party.setConstant(True)
    #             logger.info(f"Setting parameter {_party.GetName()} to constant with value {_party.getVal()}")


def free_param(par_name: str, party: RooRealVar, pdfPars_Arg: RooArgList, fuzzyMatch: bool) -> None:
    """
    Set the parameter to be freed
        par_name: [str] the pattern to match for parameter freeing
        party: [RooRealVar] the parameter to check for potential freeing
        pdfPars_Arg: [RooArgList] list of all parameters
        fuzzyMatch: [bool] whether to use fuzzy matching
    """
    if (fuzzyMatch and fnmatch(party.GetName(), par_name)) or (not fuzzyMatch and par_name == party.GetName()):
        _party = pdfPars_Arg.find(party.GetName())
        _party.setConstant(False)
        logger.info(f"Setting parameter {_party.GetName()} to free with initial value {_party.getVal()} and range {list(_party.getRange())}")


# def free_param(param: RooRealVar, pdfPars_Arg: RooArgList) -> None:
#     """
#     Set the parameter to be freed
#         param: [RooRealVar] the parameter to be freed
#         pdfPars_Arg: [RooArgList] list of all parameters
#     """
#     _party = pdfPars_Arg.find(param.GetName())
#     _party.setConstant(False)
#     logger.info(f"Setting parameter {_party.GetName()} to free with initial value {_party.getVal()} and range {list(_party.getRange())}")


def params_to_free_helper(pdfPars_Arg: RooArgList, params_to_free_list: List[str], fuzzyMatch: bool = True) -> None:
    """params_to_free helper
    Helper function to free parameters with the value which was fixed.
        pdfPars_Arg: [RooArgList] the RooArgList format class which stores all variables used in PDF construction.
        params_to_free_list: [list] a list referes to the variables need to be freed.
        fuzzyMatch: [bool] whether use fuzzy match mode.
    """
    # Check if params list is empty
    if all(item == "" for item in params_to_free_list):
        return None

    # Extract matching parameters
    matching_params = extract_matching_params(pdfPars_Arg, params_to_free_list, fuzzyMatch)

    # Free each matching parameter
    for i in range(matching_params.size()):
        param = matching_params[i]
        param_name = param.GetName()

        _party = pdfPars_Arg.find(param_name)
        _party.setConstant(False)
        logger.info(f"Setting parameter {_party.GetName()} to free with initial value {_party.getVal()} and range {list(_party.getRange())}")

    # # Prepare info by using fuzzy matching
    # pdfPars_List = RooArgList(pdfPars_Arg)
    # for par in params_to_free_list:
    #     for i in range(pdfPars_List.getSize()):
    #         party = RooRealVar(pdfPars_List.at(i))

    #         free_param(par, party, pdfPars_Arg, fuzzyMatch)

    #         # if fuzzyMatch and par in party.GetName() or not fuzzyMatch and par == party.GetName():
    #         #     _party = pdfPars_Arg.find(party.GetName())
    #         #     _party.setConstant(False)
    #         #     rprint(f"Setting parameter {_party.GetName()} to free with initial value {_party.getVal()} and range {list(_party.getRange())}")


def add_unique_to_argset(
    argset: RooArgSet,
    arg: RooRealVar,
) -> None:
    """RooFit helper
    Add unique argument to RooArgSet
        argset: [RooArgSet] the RooArgSet object.
        arg: [RooAbsArg] the RooAbsArg object.
    """
    if not argset.find(arg.GetName()):
        argset.add(arg)
    else:
        logger.warning(f"{arg.GetName()} already exists in the RooArgSet")


# * ------------------------------ Add constraints ----------------------------- #
def read_parameter_constraints(fit_result_file: str, param_names: List[str], reference_params: RooArgSet) -> Optional[Dict[str, Tuple[float, float]]]:
    """
    Read parameter values and errors from a fit result file for Gaussian constraints.

    This function reads previously saved RooFit parameter results to create Gaussian constraints
    for subsequent fits. It's commonly used to constrain parameters based on previous fit results.

    Args:
        fit_result_file: [str] Path to the fit result file containing saved parameters.
                        Expected format: File created by RooArgSet.writeToFile() or similar.
                        Example: "/path/to/mc_fit_results.txt"

        param_names: [List[str]] List of parameter names to read constraints for.
                    Expected format: List of exact parameter names as they appear in the fit result file.
                    Example: ["mean_signal", "sigma_signal", "alpha_cb"]
                    Note: Names must match exactly with those in the fit result file.

        reference_params: [RooArgSet] RooArgSet containing reference parameters for structure validation.
                        Expected format: RooArgSet from your current model containing the parameters.
                        Example: RooArgSet containing RooRealVar objects with same names as param_names.
                        Purpose: Used to validate that requested parameters exist in current model.

    Returns:
        Optional[Dict[str, Tuple[float, float]]]: Dictionary mapping parameter names to (value, error) tuples.
        - Returns None if no valid constraints found or file doesn't exist
        - Returns dict like: {"mean_signal": (5.279, 0.001), "sigma_signal": (0.025, 0.002)}
        - Only includes parameters with positive errors (valid uncertainties)

    Example Usage:
        # Read constraints for signal parameters from MC fit
        model_params = RooArgSet(mean_var, sigma_var, alpha_var)
        constraint_names = ["mean_signal", "sigma_signal"]
        constraints = read_parameter_constraints("mc_fit_results.txt", constraint_names, model_params)
        # Result: {"mean_signal": (5.279, 0.001), "sigma_signal": (0.025, 0.002)}
    """
    if not param_names or not fit_result_file or not Path(fit_result_file).is_file():
        return None

    try:
        # Create parameter set for reading
        read_params = RooArgSet()

        # Add only parameters that exist in reference and are requested
        for param_name in param_names:
            ref_param = reference_params.find(param_name)
            if ref_param:
                read_params.add(ref_param)
            else:
                logger.warning(f"Parameter '{param_name}' not found in reference parameters, skipping")

        if read_params.getSize() == 0:
            logger.warning("No valid parameters found for constraint reading")
            return None

        # Read parameters from file
        read_params.readFromFile(str(fit_result_file))

        # Initialize constraint data dictionary, in the format of {param_name: (value, error)}
        constraint_data: Dict[str, Tuple[float, float]] = {}

        # Extract values and errors
        for param_name in param_names:
            param = read_params.find(param_name)
            if param:
                param_var = RooRealVar(param)
                error = param_var.getError()
                if error > 0:
                    value = param_var.getVal()
                    constraint_data[param_name] = (value, error)
                    logger.info(f"Read constraint for {param_name}: {value} ± {error}")
                else:
                    logger.warning(f"Parameter {param_name} has invalid error ({error}), skipping")

        return constraint_data if constraint_data else None

    except Exception as e:
        logger.error(f"Failed to read constraint parameters from {fit_result_file}: {e}")
        return None


def create_gaussian_constraints(model_params: RooArgSet, constraint_data: Dict[str, Tuple[float, float]]) -> RooArgSet:
    """
    Create Gaussian constraint PDFs for model parameters.

    This function creates RooGaussian constraint PDFs that can be multiplied with your main PDF
    to constrain parameters based on external information (e.g., from MC studies).

    Args:
        model_params: [RooArgSet] RooArgSet containing the model parameters to be constrained.
                        Expected format: RooArgSet containing RooRealVar objects that will be constrained.
                        Example: RooArgSet with variables like mean_signal, sigma_signal, etc.
                        Purpose: These are the "floating" parameters in your current fit that you want to constrain.

        constraint_data: [Dict[str, Tuple[float, float]]] Dictionary mapping parameter names to (central_value, uncertainty).
                        Expected format: {"param_name": (central_value, sigma), ...}
                        Example: {"mean_signal": (5.279, 0.001), "sigma_signal": (0.025, 0.002)}
                        Where:  - param_name must match names in model_params
                                - central_value is the constraint center (from previous fit)
                                - sigma is the constraint width (uncertainty from previous fit)

    Returns:
        RooArgSet: RooArgSet containing the Gaussian constraint PDFs.
        - Returns empty RooArgSet if no constraints created
        - Each constraint is a RooGaussian with name "gaussConstraint_{param_name}"
        - These can be multiplied with your main PDF: pdf_total = pdf_main * constraint1 * constraint2 * ...
        - Ownership is transferred to the RooArgSet (won't be garbage collected)

    Example Usage:
        # Create constraints for signal parameters
        model_params = RooArgSet(mean_var, sigma_var)  # Your fit variables
        constraint_data = {"mean_signal": (5.279, 0.001), "sigma_signal": (0.025, 0.002)}
        constraints = create_gaussian_constraints(model_params, constraint_data)

        # Use in fit: multiply main PDF with constraints
        pdf_constrained = RooProdPdf("constrained_pdf", "PDF with constraints",
                                    RooArgList(main_pdf, constraints))
    """
    constraints = RooArgSet("gaussConstraints_RooArgSet")

    if not constraint_data:
        return constraints

    for param_name, (central_value, uncertainty) in constraint_data.items():
        # Find parameter in model
        param = model_params.find(param_name)
        if param:
            # Create Gaussian constraint: Gaussian(param, central_value, uncertainty)
            # This creates: exp(-0.5 * ((param - central_value) / uncertainty)^2)
            constraint_pdf = RooGaussian(
                f"gaussConstraint_{param_name}",
                f"Gaussian constraint for {param_name}",
                param,  # The parameter to be constrained
                RooFit.RooConst(central_value),  # Central value (mean of Gaussian)
                RooFit.RooConst(uncertainty),  # Width (sigma of Gaussian)
            )

            # Use addOwned() to transfer ownership to the RooArgSet
            # This ensures the constraint PDFs won't be garbage collected
            constraints.addOwned(constraint_pdf)

            logger.info(f"Created Gaussian constraint for {param_name}: {central_value} ± {uncertainty}")

        else:
            logger.warning(f"Parameter {param_name} not found in model during constraint creation")

    logger.info(f"Created {constraints.getSize()} Gaussian constraints")

    return constraints


def parse_parameter_list(param_specification: List[str], available_params: RooArgSet, use_fuzzy_matching: bool = True) -> List[str]:
    """
    Parse parameter specification and validate against available parameters.

    This function takes a list of parameter name patterns and finds matching parameters
    in the available parameter set. Supports both exact matching and fuzzy/pattern matching.

    Args:
        param_specification: [List[str]] List of parameter name patterns to match.
                            Expected format: List of strings representing parameter names or patterns.
                            Special values: ["none"], ["false"], [""] - returns empty list
                            Examples:
                            - Exact names: ["mean_signal", "sigma_signal"]
                            - Patterns: ["*_signal", "alpha_*", "n_*"]
                            - Mixed: ["mean_signal", "*_bkg", "efficiency_*"]

        available_params: [RooArgSet] RooArgSet containing all available parameters to search in.
                            Expected format: RooArgSet containing RooRealVar objects.
                            Example: RooArgSet with parameters from your PDF model.
                            Purpose: The "universe" of parameters to search within.

        use_fuzzy_matching: [bool] Whether to use pattern matching (fnmatch) or exact string matching.
                            Default: True (use pattern matching)
                            - True: Supports wildcards like "*", "?", "[abc]"
                            - False: Only exact string matches
                            Examples with fuzzy matching:
                            - "*_signal" matches "mean_signal", "sigma_signal", "alpha_signal"
                            - "alpha_*" matches "alpha_signal", "alpha_bkg"
                            - "n_?" matches "n_1", "n_2", "n_L", etc.

    Returns:
        List[str]: List of valid parameter names that matched the specification.
        - Returns empty list if no matches found or param_specification is empty/None
        - Returns actual parameter names (not the patterns)
        - Only includes parameters that exist in available_params

    Example Usage:
        # Get all signal-related parameters
        available = RooArgSet(mean_signal, sigma_signal, alpha_signal, mean_bkg, sigma_bkg)
        patterns = ["*_signal"]
        matches = parse_parameter_list(patterns, available, use_fuzzy_matching=True)
        # Result: ["mean_signal", "sigma_signal", "alpha_signal"]

        # Get specific parameters exactly
        exact_names = ["mean_signal", "sigma_bkg"]
        matches = parse_parameter_list(exact_names, available, use_fuzzy_matching=False)
        # Result: ["mean_signal", "sigma_bkg"] (if they exist)
    """
    if not param_specification or param_specification[0].upper() in ['NONE', 'FALSE']:
        return []

    # Clean up the parameter names (remove whitespace)
    requested_names = [name.strip() for name in param_specification]

    if not requested_names:
        return []

    # Find matching parameters using the extract_matching_params helper
    matching_params = extract_matching_params(available_params, requested_names, use_fuzzy_matching)

    if matching_params.getSize() == 0:
        logger.warning(f"No matching parameters found for specification: {param_specification}")
        return []

    # Extract the actual parameter names
    valid_names = [param.GetName() for param in matching_params]
    logger.info(f"Matched parameters: {', '.join(valid_names)}")

    return valid_names


def apply_parameter_constraints(model_params: RooArgSet, constraint_specification: List[str], constraint_source_file: str, use_fuzzy_matching: bool = True) -> RooArgSet:
    """
    High-level function to parse, read, and create parameter constraints in one step.

    This is a convenience function that combines parameter parsing, constraint reading,
    and constraint PDF creation. It's the main entry point for adding Gaussian constraints
    to your fit based on previous fit results.

    Args:
        model_params: [RooArgSet] RooArgSet containing the model parameters that can be constrained.
                        Expected format: RooArgSet containing RooRealVar objects from your current model.
                        Example: RooArgSet with all fit parameters like mean, sigma, yields, etc.
                        Purpose: The "universe" of parameters available for constraining in your current fit.

        constraint_specification: [List[str]] List of parameter names/patterns to constrain.
                                    Expected format: List of strings (parameter names or patterns).
                                    Examples:
                                    - ["mean_signal", "sigma_signal"] - constrain specific parameters
                                    - ["*_signal"] - constrain all signal parameters
                                    - ["alpha_*", "n_*"] - constrain shape parameters
                                    - ["none"] or ["false"] - no constraints

        constraint_source_file: [str] Path to file containing constraint values from previous fit.
                                Expected format: Text file created by RooArgSet.writeToFile() or equivalent.
                                Example: "/path/to/mc_fit_results.txt"
                                Content: Parameter values and errors from previous fit (typically MC fit).

        use_fuzzy_matching: [bool] Whether to use pattern matching for parameter names.
                            Default: True (supports wildcards)
                            - True: "*_signal" matches multiple parameters
                            - False: Only exact parameter name matches

    Returns:
        RooArgSet: RooArgSet containing Gaussian constraint PDFs ready for use in fit.
        - Returns empty RooArgSet if no constraints could be created
        - Each constraint is a RooGaussian PDF
        - Can be used directly in RooProdPdf to create constrained model:
            constrained_pdf = RooProdPdf("constrained", "model with constraints", RooArgList(main_pdf, constraints))

    Example Usage:
        # Typical workflow: Constrain signal parameters based on MC fit
        model_params = pdf.getParameters(dataset)  # Get all parameters from your model
        constraint_spec = ["mean_signal", "sigma_signal", "alpha_*"]  # Parameters to constrain
        constraint_file = "mc_fit_results.txt"  # File with MC fit results

        constraints = apply_parameter_constraints(model_params, constraint_spec, constraint_file)

        if constraints.getSize() > 0:
            # Create constrained model
            constrained_pdf = RooProdPdf("constrained_pdf", "PDF with constraints",
                                        RooArgList(main_pdf, constraints))
            # Use constrained_pdf in your fit instead of main_pdf
        else:
            # No constraints applied, use original PDF
            constrained_pdf = main_pdf

    Workflow:
        1. Parse constraint_specification to find matching parameters in model_params
        2. Read constraint values (central values and errors) from constraint_source_file
        3. Create Gaussian constraint PDFs for each parameter
        4. Return RooArgSet containing all constraint PDFs
    """

    # Step 1: Parse parameter specification to get list of parameter names
    param_names = parse_parameter_list(constraint_specification, model_params, use_fuzzy_matching)

    if not param_names:
        logger.info("No parameters specified for constraints")
        return RooArgSet()

    # Step 2: Read constraint data from file
    constraint_data = read_parameter_constraints(constraint_source_file, param_names, model_params)

    if not constraint_data:
        logger.warning("No valid constraint data found")
        return RooArgSet()

    # Step 3: Create constraint PDFs
    constraints = create_gaussian_constraints(model_params, constraint_data)

    logger.info(f"Successfully created {constraints.getSize()} parameter constraints")
    return constraints


# * ------------------------------ Check fit convergence ----------------------------- #
def check_fit_convergence(r: RooFitResult, strategy: int) -> bool:
    """
    Check whether fit converged accoring to the following judging conditions
        1) covQual   | Fully accurate covariance matrix(after MIGRAD)
        2) edn       | Estimated distance to minimum
        3) fitStatus | Overall variable that characterises the goodness of the fit
    return:
        False : not converged
        True : converged
    """
    flag_covQual = r.covQual() == 3  # 0: not calculated, 1: approximated, 2: full matrix, 3: full accurate matrix
    flag_edm = r.edm() < 0.01 if strategy == 2 else r.edm() < 1  # 0.01 for strategy 2, 1 for strategy 1
    flag_fitStatus = r.status() == 0  # 0: OK, 1:Covariance was mad epos defined, 2:Hesse is invalid, 3:Edm is above max, 4:Reached call limit, 5:Any other failure

    return flag_covQual and flag_edm and flag_fitStatus


# * ------------------------------ RooMinimizer helper ----------------------------- #
def RooMinimizer_helper(
    mCC: RooMinimizer,
    strategy: int = 1,
    verbose: int = 1,
    minos: bool = False,
    maxTries: int = 2,
) -> RooFitResult:
    """RooFit helper
    RooMinimizer manager.
        mCC: [RooMinimizer] the RooMinizer prepared.
        strategy: [int] the fit strategy (0,1,2).
        verbose: [int] verbosity level option of RooMinimizer object (0,1,2,3).
        minos: [bool] whether execute minos after migrad.
        maxTries: [int] the maximum number of attempts for migrad if failed.
    """
    logger.info("Fit start")

    # Initialize status variables
    statusVal_migrad = -1  # Migrad status
    statusVal_hesse = -1  # hesse status
    statusVal_minos = -1  # minos status

    # Set the strategy and verbosity
    mCC.setStrategy(strategy)
    mCC.setVerbose(False)  # mCC.setVerbose(bool(verbose))
    mCC.setPrintLevel(verbose)
    # statusVal_migrad = mCC.migrad()
    statusVal_migrad = mCC.minimize("Minuit", "MIGRAD")  # minize with simplex and migrad
    RooFitRes = mCC.save()  # take snap-shot for roofit results, to retrieve fit info.(such as status info.)
    # Migrad status

    #  Check whether status of MIGRAD is OK
    #  0: OK, 1:Covariance was mad epos defined, 2:Hesse is invalid, 3:Edm is above max, 4:Reached call limit, 5:Any other failure
    Tries = max(maxTries, 2)

    while (not check_fit_convergence(RooFitRes, strategy)) and (Tries > 0):
        # statusVal_migrad = mCC.migrad()  # Migrad status
        if Tries == maxTries:
            statusVal_migrad = mCC.minimize("Minuit2", "SIMPLEX;MIGRAD")
        else:
            statusVal_migrad = mCC.minimize("Minuit", "MIGRAD")
        RooFitRes = mCC.save()
        Tries = Tries - 1
    if not check_fit_convergence(RooFitRes, strategy):
        warnings.warn(f"{colorama.Fore.YELLOW}migrad did not converge after {maxTries} tries\n{colorama.Style.RESET_ALL}")

    # Calculate error by using hesse
    statusVal_hesse = mCC.hesse()
    if minos:
        statusVal_minos = mCC.minos()

    RooFitRes = mCC.save()

    if verbose > 0:
        logger.info("Fit status:")
        logger.info(f'    overall status = {RooFitRes.status()}')
        logger.info(f"            migrad = {statusVal_migrad}")
        logger.info(f"            hesse  = {statusVal_hesse}")
        logger.info(f"            minos  = {statusVal_minos}")

    return RooFitRes


# * ------------------------------ Fit to data ----------------------------- #
def fitTo_helper(
    model: RooAbsPdf,
    data: RooDataSet,
    *,
    strategy: int = 1,
    minimizer: str = None,
    minos: bool = False,
    max_tries: int = 5,
    n_threads: int = 1,
    sumW2Error: bool = False,
    external_constraints: RooArgSet = None,
) -> RooFitResult:
    """
    Perform the fit with multiple attempts if needed.

    Args:
        model: Model to fit
        data: Dataset to fit against
        strategy: Strategy to use for the fit
        minimizer: Minimizer to use for the fit. If None, use the default minimizer.
        max_tries: Maximum number of attempts to perform the fit
        n_threads: Number of threads to use
        SumW2Error: Whether to use SumW2Error for the fit.  True:  reflect the error corresponding to the yields of input statistics;
                                                            False: reflect the error corresponding to the yields of weighted sum

    Returns:
        RooFitResult from the fit
    """
    external_constraints = RooArgSet() if external_constraints is None else external_constraints
    minimizer = r.Math.MinimizerOptions.DefaultMinimizerType() if minimizer is None else minimizer

    # Initialize variables for the fit attempts
    fitresult_status = -1
    n_tries = 0

    # Try multiple fits until convergence or max attempts reached
    while (fitresult_status != 0) and (n_tries < max_tries):
        logger.info(f'Attempting fit {n_tries+1}/{max_tries} ...')

        # Use strategy 2 for the 2nd last attempt
        _strategy = 2 if n_tries == max_tries - 2 else strategy

        fitresult = model.fitTo(
            data,
            RooFit.Minimizer(minimizer),
            RooFit.Strategy(_strategy),
            RooFit.Save(True),
            RooFit.Minos(minos),
            RooFit.NumCPU(n_threads),
            RooFit.SumW2Error(sumW2Error),
            RooFit.ExternalConstraints(external_constraints),
        )
        fitresult_status = fitresult.status()
        n_tries += 1

    if fitresult_status != 0:
        logger.warning(f'Fit did not converge after {max_tries} attempts: status = {fitresult_status}')

    return fitresult


def show_chi_square(frame: RooPlot, fit_plt_name: str, data_plt_name: str, title: str) -> None:
    """RooFit helper
    Calculate chi2 according to given data and pdf
        frame: [RooPlot] frame constructed as RooPlot object.
        fit_plt_name: [str] the name of fit plot within frame.
        data_plt_name: [str] the name of data plot within frame.
        title: [str] title for the output output information.
    """
    chi2_ndof2 = frame.chiSquare(fit_plt_name, data_plt_name, 2)
    chi2_ndof4 = frame.chiSquare(fit_plt_name, data_plt_name, 4)
    logger.info("=========================================")
    logger.info(f"------------- {title} -------------")
    logger.info(f"chiSquare_NDOF(2) = {chi2_ndof2}")
    logger.info(f"chiSquare_NDOF(4) = {chi2_ndof4}")
    logger.info("=========================================")


def PDF_inspect(mypdf: RooAbsPdf) -> None:
    """RooFit helper
    Inspect given PDF infomation.
        mypdf: [RooAbsPdf] the given pdf.
    """
    logger.info("\n- - - - - - - - - - - - - - - - -")
    logger.info("Debug Info: Inspect PDF")
    logger.info(f"PDF name : {mypdf.GetName()}")
    mypdf.Print()
    mypdf.Print("t")
    logger.info("- - - - - - - - - - - - - - - - -\n")


def Par_inspect(mypdf: RooAbsPdf, mydata: RooDataSet) -> None:
    """RooFit helper
    Inspect parameters information within given PDF and corresponding dataset.
        mypdf: [RooAbsPdf] the given pdf.
        mydata: [RooDataSet] the corresponding dataset.
    """
    logger.info("\n- - - - - - - - - - - - - - - - -")
    logger.info("Debug Info: Inspect Parameters")
    logger.info(f"PDF name : {mypdf.GetName()}         data name: {mydata.GetName()}")
    paramList = mypdf.getParameters(mydata)
    paramList.Print()
    paramList.Print("v")
    logger.info("- - - - - - - - - - - - - - - - -\n")


def print_RooArgSet(params: RooArgSet, print_constants: bool = True, print_option: str = "") -> Dict[str, RooArgSet]:
    """
    Print contents of a RooArgSet, separating free and fixed parameters

    Args:
        params: RooArgSet containing parameters to print
        print_constants: Whether to print constant parameters
        print_option: Print option flag passed to RooRealVar.Print()

    Returns:
        Dictionary containing free and fixed parameters as RooArgSets
    """
    # Start separator
    logger.info("\n" + "=" * 60)

    logger.info(f"Check RooArgSet {params.GetName()}")

    argSetFix = RooArgSet()
    argSetFree = RooArgSet()

    # Use range-based iteration
    for i in range(params.size()):
        arg = params[i]
        if isinstance(arg, RooRealVar):
            if arg.isConstant():
                argSetFix.add(arg)
            else:
                argSetFree.add(arg)

    def _print_arg_set(arg_set: RooArgSet, title: str) -> None:
        logger.info(f"--- {title} ---")

        if arg_set.getSize() == 0:
            logger.info("No parameters to print")
            return

        for i in range(arg_set.size()):
            arg_set[i].Print(print_option)

    # Print free parameters
    _print_arg_set(argSetFree, "Free parameters")

    # Print constants if requested
    if print_constants:
        _print_arg_set(argSetFix, "Constants")

    # End separator
    logger.info("=" * 60 + "\n")

    return {"free": argSetFree, "fix": argSetFix}


def plot_correlation_matrix_from_RooFitResult(r: RooFitResult, output_file: str) -> None:
    """Draw the correlation matrix using matplotlib

    Args:
        fitResult (RooFitResult): RooFitResult object containing the fit result
    """
    # Extract the correlation matrix as a numpy array
    correlationMatrix = np.zeros((r.correlationMatrix().GetNrows(), r.correlationMatrix().GetNcols()))
    for i, j in product(range(r.correlationMatrix().GetNrows()), range(r.correlationMatrix().GetNcols())):
        correlationMatrix[i][j] = r.correlationMatrix()[i][j]

    # varNames = [_spruce_varName(var.GetName()) for var in r.floatParsFinal()]
    varNames = [var.GetName() for var in r.floatParsFinal()]

    # def _latexnise_varName(varName):
    #     varName = varName.replace("delta", r"$\Delta$")
    #     varName = varName.replace("sigma", r"$\sigma$")
    #     varName = varName.replace("mean", r"$\mu$")
    #     varName = varName.replace("alpha", r"$\alpha$")
    #     varName = varName.replace("frac", r"f")

    #     varName = varName.replace("k_bkgcomb", r"$k_{comb}$")

    #     varName = varName.replace("nsig", r"$N_{sig}$")
    #     varName = varName.replace("n_bkgcomb", r"$N_{comb}$")

    #     # Bd -> B^0 and Bs -> B_s^0
    #     varName = varName.replace("Bd", r"$B^{0}$")
    #     varName = varName.replace("Bs", r"$B_{s}^{0}$")

    #     return varName

    # varNames = [_latexnise_varName(varName) for varName in varNames]

    # Draw the correlation matrix
    plot_correlation_matrix(correlationMatrix, varNames, output_file)


def write_correlation_matrix_latex_from_RooFitResult(
    r: RooFitResult,
    output_file: str,
    column_width: Optional[float] = None,
    rotate_column_headers: int = 90,
) -> None:
    """Write the correlation matrix to a latex file

    Args:
        r (RooFitResult): RooFitResult object containing the fit result
        output_file (str): Path to the output file
        column_width (float, optional): The column width will be fixed if specified (in the unit of cm). Defaults to None, automatically determined.
        rotate_column_headers (int, optional): Rotate the column headers. Defaults to 90.
    """
    # Extract the correlation matrix as a numpy array
    correlationMatrix_np = np.zeros((r.correlationMatrix().GetNrows(), r.correlationMatrix().GetNcols()))
    for i, j in product(range(r.correlationMatrix().GetNrows()), range(r.correlationMatrix().GetNcols())):
        correlationMatrix_np[i][j] = r.correlationMatrix()[i][j]

    # varNames = [_spruce_varName(var.GetName()) for var in r.floatParsFinal()]
    varNames = [var.GetName() for var in r.floatParsFinal()]

    write_correlation_matrix_latex(
        correlationMatrix=correlationMatrix_np,
        varNames=varNames,
        output_file=output_file,
        column_width=column_width,
        rotate_column_headers=rotate_column_headers,
    )


def EX_additional_FitRes(RooFitRes: RooFitResult, CorrMartix_PicName: str) -> None:
    """RooFit helper
    Extract additional fit results after fit (numerical results, Correlation matrix)
        RooFitResult: [RooFitRes] the fit result saved as RooFitRes object.
        CorrMartix_PicName: [str] the location where covariance and correlation matrix will be saved.
    """
    # Verbose printing: Basic info, values of constant parameters, initial and
    # final values of floating parameters, global correlations
    RooFitRes.Print("v")

    # The quality of covariance
    logger.info(f"covQual = {RooFitRes.covQual()}")
    # Extract covariance and correlation matrix as TMatrixDSym
    cor = RooFitRes.correlationMatrix()
    cov = RooFitRes.covarianceMatrix()

    # Print correlation, covariance matrix
    logger.info("correlation matrix")
    cor.Print()
    logger.info("covariance matrix")
    cov.Print()

    # Construct 2D color plot of correlation matrix
    gStyle.SetOptStat(0)
    gStyle.SetPalette(1)
    hcorr = RooFitRes.correlationHist()

    c_correlation = TCanvas("c_correlation", "", 1400, 1000)
    c_correlation.cd()
    gPad.SetLeftMargin(0.15)
    hcorr.GetYaxis().SetTitleOffset(1.4)
    hcorr.Draw("colz")

    extSuffix = [".pdf", ".png", ".C"]
    if os.path.splitext(CorrMartix_PicName)[1] in extSuffix:
        CorrMartix_PicName_full = CorrMartix_PicName
    else:
        CorrMartix_PicName_full = f"{CorrMartix_PicName}.pdf"

    c_correlation.SaveAs(CorrMartix_PicName_full)

    # Plot correlation matrix by using matplotlib
    plot_correlation_matrix_from_RooFitResult(
        r=RooFitRes,
        output_file=f"{CorrMartix_PicName_full.rsplit('.',1)[0]}_matplot.pdf",
    )

    # Save correlation matrix into a tex file in Latex format
    write_correlation_matrix_latex_from_RooFitResult(r=RooFitRes, output_file=f"{CorrMartix_PicName_full.rsplit('.',1)[0]}.tex")  # , column_width="1cm")


def _RooSaveFitPlot_helper_logo(logo: TPaveText) -> None:
    """RooFit helper sub"""
    logo.SetShadowColor(0)
    logo.SetFillStyle(0)
    logo.SetBorderSize(0)
    logo.SetTextAlign(12)
    # logo.SetTextSize(0.08)


def _RooSaveFitPlot_helper_latex(latex: TLatex) -> None:
    """RooFit helper sub"""
    latex.SetTextFont(132)
    latex.SetTextSize(0.05)
    latex.SetLineWidth(2)


def _RooSaveFitPlot_helper_leg(leg: TLegend) -> None:
    """RooFit helper sub"""
    leg.SetBorderSize(0)
    leg.SetTextFont(132)
    leg.SetTextSize(0.045)
    leg.SetFillColor(0)


def _RooSaveFitPlot_helper_pull(
    data: RooDataSet,
    fitpdf: RooAbsPdf,
    fitvar: RooRealVar,
    frame: RooPlot,
    pullstyle: int,
) -> RooPlot:
    """RooFit helper for preparing pull distribution

    Args:
        data: the dataset
        fitpdf: the corresponding pdf
        fitvar: the corresponding variable used
        frame: the corresponding frame respect to data and pdf
        pullstyle: pull distribution style option (0: not draw pull, 1: style1, 2: style2)

    Returns:
        RooPlot containing the pull distribution or None if pullstyle=0
    """

    if not pullstyle:
        return None

    # Get number of bins & [x_low,x_high] from plot
    nBin = frame.GetXaxis().GetNbins()
    x_l, x_h = frame.GetXaxis().GetXmin(), frame.GetXaxis().GetXmax()

    # Create frame for pull distribution
    pframe = fitvar.frame(RooFit.Title("Pull distribution"), RooFit.Bins(nBin), RooFit.Range(x_l, x_h))
    data.plotOn(pframe)
    fitpdf.plotOn(pframe)
    pull = fitvar.frame(RooFit.Bins(nBin), RooFit.Range(x_l, x_h))
    hpull = pframe.pullHist()

    # Helper to set Y-axis properties
    def helper_set_Yaxis(pull_frame):
        pull_frame.GetYaxis().SetRangeUser(-5, 5)
        pull_frame.GetYaxis().SetNdivisions(505)
        pull_frame.GetYaxis().SetLabelSize(0.20)

    if pullstyle == 1:
        # Style 1: filled histogram style
        hpull.SetFillColor(15)
        hpull.SetFillStyle(3144)
        pull.addPlotable(hpull, "L3")
        helper_set_Yaxis(pull)
        return pull

    elif pullstyle == 2:
        # Style 2: points with error bars and reference lines
        # First add the reference lines (so they'll be drawn behind the data points)
        xmin, xmax = pull.GetXaxis().GetXmin(), pull.GetXaxis().GetXmax()

        # Create and add reference lines
        lines = [
            TLine(xmin, 0, xmax, 0),  # Center line
            TLine(xmin, 3, xmax, 3),  # Upper line
            TLine(xmin, -3, xmax, -3),  # Lower line
        ]

        for line in lines:
            line.SetLineStyle(7)
            line.SetLineColor(2)
            line.SetLineWidth(2)
            pull.addObject(line)

        # Now add the data points on top of the lines
        hpull.SetLineWidth(1)
        hpull.SetFillStyle(3001)
        pull.addPlotable(hpull, "PE")

        pull.SetTitle("")
        pull.GetXaxis().SetTitle("")
        helper_set_Yaxis(pull)

        return pull


def RooSaveFitPlot_helper(
    data: RooDataSet,
    fitpdf: RooAbsPdf,
    fitvar: RooRealVar,
    frame: RooPlot,
    picname: str,
    logo: TPaveText = None,
    latex: TLatex = None,
    leg: TLegend = None,
    XTitle: str = "",
    YTitle: str = "",
    pullstyle: int = 2,
    SetYmax: float = 0,
) -> None:
    """RooFit helper
    Save plots
        data: [RooDataSet] the dataset.
        fitpdf: [RooAbsPdf] the corresponing pdf.
        fitvar: [RooRealVar] the corresponding variable used.
        frame: [RooPlot] the corresponding frame respect to data and pdf.
        logo: [TPaveText] add a logo.
        latex: [TLatex] add a latex.
        leg: [TLegend] add a legend.
        picname: [string] path to where picture be stored.
        XTitle: [str] title of x-axis.
        YTitle: [str] title of y-axis.
        pullstyle: [int] pull distribution syle option (0: not draw pull, 1: style1, 2: style2).
        SetYmax: [int] raw an additional plot with user customized height of y-axis.
    """
    gROOT.SetBatch(1)

    # minimum/maxmimum of y-axis
    YMIN = frame.GetMaximum()
    YMAX = frame.GetMaximum()
    # Intrinsic minimum/maximum of y-axis
    ymin = 1e-2
    ymax = YMAX * 1.3
    frame.SetMinimum(1e-2)  # we only want positive value while has negative caused by weight
    frame.SetMaximum(ymax)

    # set X/Y axis related
    # title
    if XTitle:
        frame.SetXTitle(XTitle)
    if YTitle:
        frame.SetYTitle(YTitle)

    xAxis, yAxis = [frame.GetXaxis(), frame.GetYaxis()]

    if ymax < 1e2:
        yoff = 0.9
    elif ymax >= 1e2 and ymax < 1e3:
        yoff = 0.95
    elif ymax >= 1e3 and ymax < 1e4:
        yoff = 1.10
    else:  # ymax >= 1e4:
        yoff = 1.20
    xAxis.SetTitleFont(132)
    yAxis.SetTitleFont(132)
    xAxis.SetTitleSize(0.06)
    yAxis.SetTitleSize(0.06)
    xAxis.SetTitleOffset(1.15)
    yAxis.SetTitleOffset(yoff)
    xAxis.SetLabelOffset(0.02)
    yAxis.SetLabelOffset(0.01)

    # Set LHCb logo
    if logo:
        _RooSaveFitPlot_helper_logo(logo)
        frame.addObject(logo)

    # Set latex
    if latex:
        _RooSaveFitPlot_helper_latex(latex)
        frame.addObject(latex)

    # Set legend
    if leg:
        _RooSaveFitPlot_helper_leg(leg)
        frame.addObject(leg)

    # Create a helper function for setting pad margins
    def helper_set_gPad_common(yl, yh):
        gPad.SetLeftMargin(0.15)
        gPad.SetRightMargin(0.03)
        gPad.SetPad(0.02, yl, 0.98, yh)

    # Draw the plot - handle differently based on whether we need a pull plot
    pic2 = TCanvas("pic2", "", 800, 600)

    if pullstyle:
        # We need a pull plot - divide canvas into two pads
        pic2.Divide(1, 2, 0, 0, 0)

        # Bottom pad for main plot (larger)
        pic2.cd(2)
        gPad.SetTopMargin(0.015)
        gPad.SetBottomMargin(0.15)
        helper_set_gPad_common(yl=0.02, yh=0.77)
        frame.Draw()

        # Top pad for pull plot (smaller)
        pic2.cd(1)
        gPad.SetTopMargin(0)
        helper_set_gPad_common(yl=0.8, yh=0.98)

        pull = _RooSaveFitPlot_helper_pull(data, fitpdf, fitvar, frame, pullstyle)
        pull.Draw()
    else:
        # No pull plot - use the full canvas for the main plot
        pic2.cd()
        gPad.SetTopMargin(0.05)
        gPad.SetBottomMargin(0.15)
        gPad.SetLeftMargin(0.15)
        gPad.SetRightMargin(0.03)
        frame.Draw()

    # prepare for saving plots
    extSuffix = [".pdf", ".png", ".C"]

    if os.path.splitext(picname)[1] in extSuffix:
        picname_noExt = os.path.splitext(picname)[0]
        picname_Ext = os.path.splitext(picname)[1]
    else:
        picname_noExt = picname
        picname_Ext = extSuffix

    # 1) Nominal plot
    save_pic_from_tcanvas(pic2, picname_noExt, picname_Ext)

    # 2) Log plot
    if pullstyle:
        pic2.cd(2)  # Select the main plot pad if we have a pull plot
    else:
        pic2.cd()  # Select the only pad if no pull plot

    frame.SetMaximum(frame.GetMaximum() * 200.0)
    frame.SetMinimum(1e-1)
    gPad.SetLogy(1)
    picname_noExt_log = f"{picname_noExt}_log"
    save_pic_from_tcanvas(pic2, picname_noExt_log, picname_Ext)

    # 3) plot with customized height
    if SetYmax:
        if pullstyle:
            pic2.cd(2)  # Select the main plot pad if we have a pull plot
        else:
            pic2.cd()  # Select the only pad if no pull plot

        frame.SetMaximum(SetYmax)
        frame.SetMinimum(1e-1)
        gPad.SetLogy(0)
        picname_noExt_customizedYmax = f"{picname_noExt}_customizedYmax"
        save_pic_from_tcanvas(pic2, picname_noExt_customizedYmax, picname_Ext)
