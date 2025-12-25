'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-08-22 04:36:31 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-11-07 11:48:29 +0100
FilePath     : add_xgboost_info.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

'''
This module provides functionality to apply trained XGBoost models to new datasets
and add BDT predictions as new branches to ROOT files. It supports both single model
application and k-fold cross-validation model application.

Key Features:
- Single model and k-fold cross-validation model application
- Automatic data cleaning and preprocessing
- ROOT file integration with temporary file handling
- Robust error handling and validation
- Memory-efficient processing for large datasets
- Comprehensive logging and progress tracking
'''


########################################
# Import required modules and libraries
########################################
import sys
import os
import argparse
from typing import Dict, List, Optional, Union, Tuple, Any

import pandas as pd
import numpy as np
import uproot as ur
import xgboost as xgb
from xgboost import XGBClassifier

from pathlib import Path
import tempfile

from tqdm import tqdm
from itertools import product
from copy import deepcopy


from analysis_tool.utils.utils_yaml import read_yaml
from analysis_tool.utils.utils_uproot import load_variables_to_pd_by_uproot
from analysis_tool.utils.utils_ROOT import rdfMergeFriends
from analysis_tool.utils.utils_numpy import analyze_distribution

from analysis_tool.utils.utils_logging import get_logger

logger = get_logger(__name__, auto_setup_rich_logging=True)


# Internal modules for BDT training pipeline integration
from analysis_tool.MVA.XGBoost.xgboost_helper import generate_model_paths


########################################
# Global constants and configuration
########################################
# Default value to use for replacing NaN and infinite values
# This should be chosen to be outside the typical range of BDT features
NAN_REPLACEMENT_VALUE = -9999


def clean_bdt_feature_data(df: pd.DataFrame, bdt_variables: List[str]) -> None:
    """
    Clean and preprocess BDT feature data by handling NaN and infinite values.

    This function identifies and replaces problematic values (NaN, +inf, -inf)
    in BDT feature columns with a standardized replacement value. This ensures
    that the XGBoost model can process the data without encountering numerical
    issues.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing BDT features (modified in-place)
    bdt_variables : List[str]
        List of column names corresponding to BDT features

    Notes
    -----
    - Modifies the input dataframe in-place for memory efficiency
    - Logs the number of problematic values found and replaced
    - Uses a global constant NAN_REPLACEMENT_VALUE for consistency
    """

    ########################################
    # Count problematic values before cleaning
    ########################################
    nan_count = df[bdt_variables].isna().sum().sum()
    inf_count = np.isinf(df[bdt_variables].values).sum()
    total_problematic = nan_count + inf_count

    ########################################
    # Perform cleaning if problematic values found
    ########################################
    if total_problematic > 0:
        logger.warning(f"Found [bold yellow]{nan_count}[/] NaN values and " f"[bold yellow]{inf_count}[/] infinite values in BDT features", extra={"markup": True})

        logger.info(f"Replacing problematic values with [bold yellow]{NAN_REPLACEMENT_VALUE}[/]", extra={"markup": True})

        # Replace infinite values with NaN first, then fill all NaN with replacement value
        df[bdt_variables] = df[bdt_variables].replace([np.inf, -np.inf], np.nan).fillna(NAN_REPLACEMENT_VALUE)

        # Verify cleaning was successful
        remaining_nan = df[bdt_variables].isna().sum().sum()
        remaining_inf = np.isinf(df[bdt_variables].values).sum()

        if remaining_nan > 0 or remaining_inf > 0:
            logger.error(f"Data cleaning failed: {remaining_nan} NaN, {remaining_inf} infinite values remain")
            raise ValueError("Data cleaning was not successful")

        logger.info(f"Successfully cleaned {total_problematic} problematic values")
    else:
        logger.info("No problematic values found in BDT features")


########################################
# Data loading and preprocessing functions
########################################


def load_and_preprocess_input_data(
    input_file: str,
    input_tree_name: str,
    bdt_variables_config_file: str,
    config_mode: str,
    num_cross_validation_folds: int,
    fold_splitting_variable: Optional[str],
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load input data from ROOT file and prepare it for BDT application.

    This function reads the input ROOT file, loads the specified BDT variables
    from the configuration file, and prepares the dataset for model application.
    It handles both single model and k-fold cross-validation scenarios.

    Parameters
    ----------
    input_file : str
        Path to input ROOT file containing the data
    input_tree_name : str
        Name of the TTree in the ROOT file
    bdt_variables_config_file : str
        Path to YAML configuration file containing BDT variable definitions
    config_mode : str
        Configuration mode/section to read from the YAML file
    num_cross_validation_folds : int
        Number of k-fold cross-validation folds
    fold_splitting_variable : Optional[str]
        Variable name used for k-fold event splitting

    Returns
    -------
    Tuple[pd.DataFrame, List[str]]
        Tuple containing:
        - Loaded and preprocessed dataframe
        - List of BDT variable names

    Raises
    ------
    Exception
        If file reading fails or configuration is invalid
    ValueError
        If insufficient data is loaded or BDT variables are invalid
    """

    ########################################
    # Load BDT variable configuration
    ########################################
    logger.info(f"Loading BDT variables from config: {bdt_variables_config_file}")

    try:
        bdt_variables = read_yaml(bdt_variables_config_file, config_mode)
    except Exception as e:
        raise Exception(f"Failed to read BDT variables from config file: {e}")

    # Validate BDT variables configuration
    if not bdt_variables or len(bdt_variables) == 0:
        raise ValueError("No BDT variables found in configuration file")

    logger.info(f"Loaded {len(bdt_variables)} BDT variables: {bdt_variables}")

    ########################################
    # Determine variables to read from ROOT file
    ########################################
    variables_to_read = bdt_variables.copy()

    # Add fold splitting variable if k-fold mode is enabled
    if num_cross_validation_folds > 1 and fold_splitting_variable is not None:
        variables_to_read.append(fold_splitting_variable)
        logger.info(f"Added fold splitting variable: {fold_splitting_variable}")

    ########################################
    # Load data from ROOT file
    ########################################
    logger.info(f"Reading input file: {input_file} (tree: {input_tree_name})")

    try:
        dataframe = load_variables_to_pd_by_uproot(
            input_file,
            input_tree_name=input_tree_name,
            variables=variables_to_read,
            library="pd",
        )
    except Exception as e:
        raise Exception(f"Failed to read input ROOT file: {e}")

    ########################################
    # Validate loaded data
    ########################################
    if dataframe.empty:
        raise ValueError("Loaded dataframe is empty - no events found")

    # Check that all required BDT variables are present
    missing_variables = set(bdt_variables) - set(dataframe.columns)
    if missing_variables:
        raise ValueError(f"Missing BDT variables in input file: {missing_variables}")

    logger.info(f"Successfully loaded {len(dataframe)} events with {len(bdt_variables)} BDT features")

    ########################################
    # Clean and preprocess the data
    ########################################
    clean_bdt_feature_data(dataframe, bdt_variables)

    return dataframe, bdt_variables


########################################
# Model loading and application functions
########################################


def load_trained_xgboost_model(model_path: str) -> XGBClassifier:
    """
    Load a trained XGBoost model from the specified file path.

    This function creates a new XGBClassifier instance and loads the trained
    model from the specified path. It includes comprehensive error handling
    and validation to ensure the model loads correctly.

    Parameters
    ----------
    model_path : str
        Full path to the saved XGBoost model file (typically .json or .model)

    Returns
    -------
    XGBClassifier
        Loaded XGBoost classifier ready for prediction

    Raises
    ------
    FileNotFoundError
        If the model file does not exist
    Exception
        If model loading fails for any reason
    """

    ########################################
    # Validate model file existence
    ########################################
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    if not os.access(model_path, os.R_OK):
        raise PermissionError(f"Model file not readable: {model_path}")

    ########################################
    # Load the model
    ########################################
    try:
        model = XGBClassifier()
        model.load_model(model_path)

        logger.info(f"Successfully loaded model: {model_path}")
        return model

    except Exception as e:
        logger.error(f"Failed to load model from {model_path}: {e}")
        raise Exception(f"Model loading failed: {e}")


def apply_single_xgboost_model(
    dataframe: pd.DataFrame,
    bdt_variables: List[str],
    model_path: str,
    output_branch_name: str,
    n_threads: int,
) -> None:
    """
    Apply a single trained XGBoost model to the entire dataset.

    This function loads a single XGBoost model and applies it to all events
    in the input dataframe. It's used when k-fold cross-validation is not
    employed (single model scenario).

    Parameters
    ----------
    dataframe : pd.DataFrame
        Input dataframe containing BDT features (modified in-place)
    bdt_variables : List[str]
        List of BDT feature column names
    model_path : str
        Path to the trained XGBoost model file
    output_branch_name : str
        Name for the output column containing BDT predictions
    n_threads : int
        Number of threads to use for model prediction

    Notes
    -----
    - Modifies the input dataframe in-place by adding the prediction column
    - Uses predict_proba()[:, 1] to get signal class probabilities
    - Automatically handles data cleaning before prediction
    """

    ########################################
    # Load the trained model
    ########################################
    logger.info(f"Applying single model: {model_path}")
    model = load_trained_xgboost_model(model_path)

    ########################################
    # Configure model threading
    ########################################
    if n_threads > 0:
        model.get_booster().set_param('nthread', n_threads)
        logger.info(f"Set model to use {n_threads} threads")

    ########################################
    # Additional data cleaning before prediction
    ########################################
    # Double-check for any remaining problematic values
    if dataframe[bdt_variables].isnull().values.any() or np.isinf(dataframe[bdt_variables].values).any():
        logger.warning("Found problematic values during model application - performing additional cleaning")
        dataframe[bdt_variables] = dataframe[bdt_variables].replace([np.inf, -np.inf], np.nan).fillna(NAN_REPLACEMENT_VALUE)

    ########################################
    # Generate predictions
    ########################################
    try:
        # Get signal class probabilities (index 1 corresponds to positive class)
        predictions = model.predict_proba(dataframe[bdt_variables])[:, 1]
        dataframe[output_branch_name] = predictions

        logger.info(f"Applied BDT to {len(dataframe)} events")
        logger.info(f"BDT score range: [{predictions.min():.6f}, {predictions.max():.6f}]")

    except Exception as e:
        logger.error(f"Model prediction failed: {e}")
        raise Exception(f"Failed to apply model: {e}")


def apply_kfold_xgboost_models(
    dataframe: pd.DataFrame,
    bdt_variables: List[str],
    model_paths: Dict[int, str],
    num_cross_validation_folds: int,
    fold_splitting_variable: str,
    output_branch_name: str,
    n_threads: int,
) -> None:
    """
    Apply k-fold cross-validation trained models to the dataset.

    This function applies different XGBoost models to different subsets of the
    data based on the fold splitting variable. Each event is processed by the
    model that was NOT trained on events from the same fold, ensuring proper
    out-of-fold predictions for unbiased evaluation.

    Parameters
    ----------
    dataframe : pd.DataFrame
        Input dataframe containing BDT features (modified in-place)
    bdt_variables : List[str]
        List of BDT feature column names
    model_paths : Dict[int, str]
        Dictionary mapping fold indices to model file paths
    num_cross_validation_folds : int
        Number of k-fold cross-validation folds
    fold_splitting_variable : str
        Column name used for determining event fold assignment
    output_branch_name : str
        Name for the output column containing BDT predictions
    n_threads : int
        Number of threads to use for each model prediction

    Notes
    -----
    - Modifies the input dataframe in-place by adding the prediction column
    - Uses modulo operation on fold_splitting_variable to assign events to folds
    - Ensures each event is predicted by a model not trained on its fold
    - Handles cases where some folds may have no events
    """

    ########################################
    # Initialize prediction column and prepare fold variable
    ########################################
    dataframe[output_branch_name] = np.nan
    dataframe[fold_splitting_variable] = dataframe[fold_splitting_variable].astype("int64")

    logger.info(f"Starting k-fold model application with {num_cross_validation_folds} folds")

    ########################################
    # Validate that all model files exist
    ########################################
    missing_models = []
    for fold_idx in range(num_cross_validation_folds):
        if fold_idx not in model_paths or not os.path.exists(model_paths[fold_idx]):
            missing_models.append(fold_idx)

    if missing_models:
        raise FileNotFoundError(f"Missing model files for folds: {missing_models}")

    ########################################
    # Apply each fold model to corresponding data subset
    ########################################
    total_processed_events = 0

    for fold_idx in tqdm(range(num_cross_validation_folds), desc="Applying k-fold models", colour="GREEN"):
        model_path = model_paths[fold_idx]

        ########################################
        # Load model for this fold
        ########################################
        model = load_trained_xgboost_model(model_path)

        # Configure threading
        if n_threads > 0:
            model.get_booster().set_param('nthread', n_threads)

        ########################################
        # Identify events for this fold
        ########################################
        # Events with (fold_splitting_variable % num_folds == fold_idx) were excluded
        # from training for this model, so they should be predicted by this model
        fold_mask = dataframe[fold_splitting_variable] % num_cross_validation_folds == fold_idx
        fold_event_count = fold_mask.sum()

        ########################################
        # Apply model to fold events
        ########################################
        if fold_event_count > 0:
            fold_data = dataframe.loc[fold_mask, bdt_variables]

            # Additional data cleaning for this fold
            if fold_data.isnull().values.any() or np.isinf(fold_data.values).any():
                logger.warning(f"Found problematic values in fold {fold_idx} - performing cleaning")
                fold_data = fold_data.replace([np.inf, -np.inf], np.nan).fillna(NAN_REPLACEMENT_VALUE)

            # Generate predictions for this fold
            try:
                fold_predictions = model.predict_proba(fold_data)[:, 1]
                dataframe.loc[fold_mask, output_branch_name] = fold_predictions

                total_processed_events += fold_event_count
                logger.info(f"Fold {fold_idx}: Applied BDT to {fold_event_count} events")

            except Exception as e:
                logger.error(f"Failed to apply model for fold {fold_idx}: {e}")
                raise Exception(f"Fold {fold_idx} prediction failed: {e}")

        else:
            logger.info(f"Fold {fold_idx}: No events to process")

    ########################################
    # Validate that all events were processed
    ########################################
    unprocessed_events = dataframe[output_branch_name].isna().sum()

    if unprocessed_events > 0:
        logger.warning(f"[bold yellow]{unprocessed_events}[/] events were not processed by any fold model", extra={"markup": True})
        logger.warning(f"Filling unprocessed events with [bold yellow]{NAN_REPLACEMENT_VALUE}[/]", extra={"markup": True})
        dataframe[output_branch_name] = dataframe[output_branch_name].fillna(NAN_REPLACEMENT_VALUE)

    logger.info(f"K-fold application complete: {total_processed_events} events processed")

    # Log prediction statistics
    valid_predictions = dataframe[output_branch_name] != NAN_REPLACEMENT_VALUE
    if valid_predictions.any():
        valid_scores = dataframe.loc[valid_predictions, output_branch_name]
        logger.info(f"BDT score range: [{valid_scores.min():.6f}, {valid_scores.max():.6f}]")

        ########################################
        # Analyze BDT predictions distribution
        ########################################
        analyze_distribution(dataframe[output_branch_name].to_numpy(), title="BDT Predictions Distribution")


########################################
# Output handling and file merging functions
########################################


def save_predictions_and_merge_with_original(
    dataframe: pd.DataFrame,
    input_file: str,
    input_tree_name: str,
    output_file: str,
    output_tree_name: str,
    output_branch_name: str,
    fold_splitting_variable: Optional[str] = None,
    num_cross_validation_folds: int = 0,
    save_minimal_output: int = 0,
) -> None:
    """
    Save BDT predictions to a temporary ROOT file and merge with the original data.

    This function creates a minimal ROOT file containing only the BDT predictions
    (and fold splitting variable if applicable), then merges it with the original
    ROOT file to create the final output. This approach is memory-efficient and
    preserves all original branches while adding the new BDT information.

    Parameters
    ----------
    dataframe : pd.DataFrame
        Dataframe containing the BDT predictions
    input_file : str
        Path to the original input ROOT file
    input_tree_name : str
        Name of the tree in the input ROOT file
    output_file : str
        Path for the final output ROOT file
    output_tree_name : str
        Name for the output tree in the final file
    output_branch_name : str
        Name of the branch containing BDT predictions
    fold_splitting_variable : Optional[str]
        Name of the fold splitting variable (included if k-fold mode)
    num_cross_validation_folds : int
        Number of k-fold cross-validation folds
    save_minimal_output : int
        If 1, save only BDT branches. If 0, merge with original file.


    Raises
    ------
    Exception
        If file operations or merging fails
    """

    ########################################
    # Prepare output dataframe with minimal columns
    ########################################
    output_dataframe = pd.DataFrame()
    output_branches = []

    # Include fold splitting variable for k-fold mode
    if num_cross_validation_folds > 1 and fold_splitting_variable is not None:
        output_dataframe[fold_splitting_variable] = dataframe[fold_splitting_variable]
        output_branches.append(fold_splitting_variable)
        logger.info(f"Including fold splitting variable: {fold_splitting_variable}")

    # Always include the BDT predictions
    output_dataframe[output_branch_name] = dataframe[output_branch_name]
    output_branches.append(output_branch_name)

    logger.info(f"Preparing output with branches: {output_branches}")

    ########################################
    # Create output directory if needed
    ########################################
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ########################################
    # Handle minimal output mode (NEW)
    ########################################
    if bool(save_minimal_output):
        logger.info("Minimal output mode: Saving only BDT branches")

        try:
            # Save directly to output file without merging
            with ur.recreate(output_file) as root_file:
                root_file[output_tree_name] = output_dataframe[output_branches].to_dict('series')

            logger.info(f"Successfully saved minimal output to: {output_file}")
            logger.info(f"Output contains {len(output_branches)} branch(es): {output_branches}")
            return

        except Exception as e:
            logger.error(f"Failed to save minimal output: {e}")
            raise Exception(f"Minimal output file creation failed: {e}")

    ########################################
    # Create temporary file for BDT predictions
    ########################################
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f'{output_path.stem}_bdt_temp_',
            suffix=output_path.suffix,
            dir=output_path.parent,
            delete=False,
        ) as temp_file:
            temp_file_path = Path(temp_file.name).resolve().as_posix()

        logger.info(f"Created temporary file: {temp_file_path}")

        ########################################
        # Save predictions to temporary ROOT file
        ########################################
        with ur.recreate(temp_file_path) as temp_root_file:
            temp_root_file[output_tree_name] = output_dataframe[output_branches].to_dict('series')

        logger.info("Saved BDT predictions to temporary file")

        ########################################
        # Merge with original ROOT file
        ########################################
        logger.info(f"Merging BDT predictions with original file: {input_file} -> {output_file}")

        rdfMergeFriends(
            input_file_nominal=input_file,
            input_file_friends=[temp_file_path],
            tree_nominal=input_tree_name,
            tree_friends=[output_tree_name],
            output_file_name=output_file,
            output_tree_name=output_tree_name,
            ignore_k_entries_reshuffled=True,
        )

        logger.info("Successfully merged files")

        ########################################
        # Clean up temporary file
        ########################################
        try:
            os.remove(temp_file_path)
            logger.info(f"Removed temporary file: {temp_file_path}")
        except OSError as e:
            logger.warning(f"Could not remove temporary file {temp_file_path}: {e}")

    except Exception as e:
        logger.error(f"Failed during file operations: {e}")
        # Keep temporary file for debugging if merge failed
        if 'temp_file_path' in locals():
            logger.info(f"Keeping temporary file for debugging: {temp_file_path}")
        raise Exception(f"Output file creation failed: {e}")


########################################
# Input validation and preprocessing functions
########################################
def validate_input_parameters(
    input_file: str,
    model_directory: str,
    bdt_variables_config_file: str,
    num_cross_validation_folds: int,
    fold_splitting_variable: Optional[str],
) -> None:
    """
    Validate all input parameters before processing begins.

    This function performs comprehensive validation of input parameters to ensure
    that all required files exist, parameters are within valid ranges, and
    configurations are consistent.

    Parameters
    ----------
    input_file : str
        Path to input ROOT file containing data for BDT application
    model_directory : str
        Directory containing trained XGBoost model files
    bdt_variables_config_file : str
        Path to YAML file containing BDT variable definitions
    num_cross_validation_folds : int
        Number of k-fold cross-validation folds (0 or 1 = single model)
    fold_splitting_variable : Optional[str]
        Variable name used for k-fold splitting (required if num_folds > 1)

    Raises
    ------
    FileNotFoundError
        If required input files do not exist
    ValueError
        If parameter values are invalid or inconsistent
    PermissionError
        If files exist but are not readable
    """

    ########################################
    # Validate file existence and accessibility
    ########################################

    # Check input ROOT file
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input ROOT file not found: {input_file}")

    if not os.access(input_file, os.R_OK):
        raise PermissionError(f"Input ROOT file not readable: {input_file}")

    # Check BDT variables configuration file
    if not os.path.exists(bdt_variables_config_file):
        raise FileNotFoundError(f"BDT variables config file not found: {bdt_variables_config_file}")

    if not os.access(bdt_variables_config_file, os.R_OK):
        raise PermissionError(f"BDT variables config file not readable: {bdt_variables_config_file}")

    # Check model directory
    if not os.path.exists(model_directory):
        raise FileNotFoundError(f"Model directory not found: {model_directory}")

    if not os.access(model_directory, os.R_OK):
        raise PermissionError(f"Model directory not accessible: {model_directory}")

    ########################################
    # Validate parameter consistency
    ########################################

    # Validate k-fold parameters
    if num_cross_validation_folds < 0:
        raise ValueError(f"Number of folds must be non-negative, got: {num_cross_validation_folds}")

    # For k-fold application, splitting variable is mandatory
    if num_cross_validation_folds > 1 and (fold_splitting_variable is None or fold_splitting_variable == ""):
        raise ValueError("fold_splitting_variable is required when num_cross_validation_folds > 1")

    logger.info(f"Input validation passed for {input_file}")


########################################
# Main application function
########################################


def add_xgboost_bdt_predictions(
    input_file: str,
    input_tree_name: str,
    bdt_variables_config_file: str,
    model_directory: str,
    model_filename: str,
    config_mode: str,
    num_cross_validation_folds: int,
    fold_splitting_variable: Optional[str],
    output_file: str,
    output_tree_name: str,
    output_branch_name: str,
    n_threads: int,
    save_minimal_output: int,
) -> bool:
    """
    Main function to add XGBoost BDT predictions to ROOT files.

    This is the primary entry point for applying trained XGBoost models to new
    datasets. It orchestrates the entire pipeline from data loading through
    model application to output file creation.

    The function supports two main operating modes:
    1. Single model application: Uses one trained model for all events
    2. K-fold model application: Uses different models for different event subsets
       based on the fold splitting variable

    Parameters
    ----------
    input_file : str
        Full path to input ROOT file containing the data to be processed
    input_tree_name : str
        Name of the TTree in the input ROOT file
    bdt_variables_config_file : str
        Path to YAML configuration file containing BDT variable definitions
    model_directory : str
        Directory containing the trained XGBoost model files
    model_filename : str
        Base filename for the model files (e.g., 'xgb_model.json')
    config_mode : str
        Configuration mode/section to read from the YAML file
    num_cross_validation_folds : int
        Number of k-fold cross-validation folds (0 or 1 = single model)
    fold_splitting_variable : Optional[str]
        Variable name used for k-fold event splitting (required if k-fold mode)
    output_file : str
        Full path for the output ROOT file with BDT predictions added
    output_tree_name : str
        Name for the output tree in the final ROOT file
    output_branch_name : str
        Name for the new branch containing BDT predictions
    n_threads : int
        Number of threads to use for model prediction (0 = auto)
    save_minimal_output : int
        If 1, save only BDT branches. If 0, merge with original file.

    Returns
    -------
    bool
        True if the operation completed successfully, False otherwise

    Raises
    ------
    Various exceptions may be raised by constituent functions for file I/O errors,
    invalid configurations, missing models, or other processing failures.

    Examples
    --------
    Single model application:
    >>> success = add_xgboost_bdt_predictions(
    ...     input_file="data.root",
    ...     input_tree_name="DecayTree",
    ...     bdt_variables_config_file="config.yaml",
    ...     model_directory="models/",
    ...     model_filename="xgb_model.json",
    ...     config_mode="default",
    ...     num_cross_validation_folds=0,
    ...     fold_splitting_variable=None,
    ...     output_file="data_with_bdt.root",
    ...     output_tree_name="DecayTree",
    ...     output_branch_name="BDT_response",
    ...     n_threads=4
    ... )

    K-fold model application:
    >>> success = add_xgboost_bdt_predictions(
    ...     input_file="data.root",
    ...     input_tree_name="DecayTree",
    ...     bdt_variables_config_file="config.yaml",
    ...     model_directory="models/",
    ...     model_filename="xgb_model.json",
    ...     config_mode="default",
    ...     num_cross_validation_folds=10,
    ...     fold_splitting_variable="eventNumber",
    ...     output_file="data_with_bdt.root",
    ...     output_tree_name="DecayTree",
    ...     output_branch_name="BDT_response",
    ...     n_threads=4
    ... )
    """

    ########################################
    # Log operation start and configuration
    ########################################
    logger.info("=" * 60)
    logger.info("STARTING XGBOOST BDT PREDICTION APPLICATION")
    logger.info("=" * 60)

    logger.info(f"Input file: {input_file}")
    logger.info(f"Model directory: {model_directory}")
    logger.info(f"Output file: {output_file}")

    if num_cross_validation_folds > 1:
        logger.info(f"Mode: K-fold cross-validation ({num_cross_validation_folds} folds)")
        logger.info(f"Fold splitting variable: {fold_splitting_variable}")
    else:
        logger.info("Mode: Single model application")

    ########################################
    # Step 1: Validate all input parameters
    ########################################
    logger.info("Step 1: Validating input parameters...")
    validate_input_parameters(
        input_file=input_file,
        model_directory=model_directory,
        bdt_variables_config_file=bdt_variables_config_file,
        num_cross_validation_folds=num_cross_validation_folds,
        fold_splitting_variable=fold_splitting_variable,
    )

    ########################################
    # Step 2: Load and preprocess input data
    ########################################
    logger.info("Step 2: Loading and preprocessing input data...")
    dataframe, bdt_variables = load_and_preprocess_input_data(
        input_file=input_file,
        input_tree_name=input_tree_name,
        bdt_variables_config_file=bdt_variables_config_file,
        config_mode=config_mode,
        num_cross_validation_folds=num_cross_validation_folds,
        fold_splitting_variable=fold_splitting_variable,
    )

    ########################################
    # Step 3: Generate model file paths
    ########################################
    logger.info("Step 3: Generating model file paths...")

    # FIXED: Correct parameter names for generate_model_paths function
    model_paths = generate_model_paths(output_dir=model_directory, model_filename=model_filename, num_folds=num_cross_validation_folds)

    logger.info(f"Generated paths for {len(model_paths)} model(s)")

    ########################################
    # Step 4: Apply XGBoost models to data
    ########################################
    logger.info("Step 4: Applying XGBoost models...")

    if num_cross_validation_folds > 1 and fold_splitting_variable is not None:
        # K-fold cross-validation mode
        apply_kfold_xgboost_models(
            dataframe=dataframe,
            bdt_variables=bdt_variables,
            model_paths=model_paths,
            num_cross_validation_folds=num_cross_validation_folds,
            fold_splitting_variable=fold_splitting_variable,
            output_branch_name=output_branch_name,
            n_threads=n_threads,
        )
    else:
        # Single model mode
        apply_single_xgboost_model(
            dataframe=dataframe,
            bdt_variables=bdt_variables,
            model_path=model_paths[0],
            output_branch_name=output_branch_name,
            n_threads=n_threads,
        )

    ########################################
    # Step 5: Save predictions and merge with original file
    ########################################
    logger.info("Step 5: Saving predictions and merging with original file...")

    save_predictions_and_merge_with_original(
        dataframe=dataframe,
        input_file=input_file,
        input_tree_name=input_tree_name,
        output_file=output_file,
        output_tree_name=output_tree_name,
        output_branch_name=output_branch_name,
        fold_splitting_variable=fold_splitting_variable,
        num_cross_validation_folds=num_cross_validation_folds,
        save_minimal_output=save_minimal_output,
    )

    ########################################
    # Operation completed successfully
    ########################################
    logger.info("=" * 60)
    logger.info("XGBOOST BDT PREDICTION APPLICATION COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
    logger.info(f"Output saved to: {output_file}")
    logger.info(f"BDT predictions available in branch: {output_branch_name}")

    return True


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-file', type=str, required=True, help='Path to input ROOT file containing data for BDT application')
    parser.add_argument('--input-tree-name', type=str, required=True, help='Name of the TTree in the input ROOT file')

    parser.add_argument('--bdt-variables-config-file', type=str, required=True, help='Path to YAML configuration file containing BDT variable definitions')
    parser.add_argument('--config-mode', type=str, required=True, help='Configuration mode/section to read from the YAML file')

    parser.add_argument('--output-file', type=str, required=True, help='Path for output ROOT file with BDT predictions added')

    parser.add_argument('--output-branch-name', type=str, required=True, help='Name for the BDT prediction branch (default: BDT_response)')

    ########################################
    # Model-related arguments
    ########################################

    parser.add_argument('--model-directory', type=str, default='output/models', help='Directory containing trained XGBoost model files (default: output/models)')
    parser.add_argument('--model-filename', type=str, default='xgb_model.json', help='Base filename for model files (default: xgb_model.json)')

    ########################################
    # K-fold cross-validation arguments
    ########################################

    parser.add_argument('--num-cross-validation-folds', type=int, default=10, help='Number of k-fold cross-validation folds (0 or 1 = single model, default: 10)')
    parser.add_argument('--fold-splitting-variable', type=str, default='eventNumber', help='Variable name for k-fold event splitting (default: eventNumber)')

    ########################################
    # Output configuration arguments
    ########################################
    parser.add_argument('--output-tree-name', type=str, default='DecayTree', help='Name for the output tree (default: DecayTree)')

    parser.add_argument('--save-minimal-output', type=int, default=0, help='If 1, save only BDT branches. If 0, merge with original file.')

    ########################################
    # Performance arguments
    ########################################
    parser.add_argument('--n-threads', type=int, default=1, help='Number of threads to use. Default: 1. [0: half of the threads, -1: all threads, other: specific number of threads]')

    return parser


def main(args: Optional[argparse.Namespace] = None) -> None:
    """Main entry point for the script."""
    if args is None:
        args = get_parser().parse_args()
    add_xgboost_bdt_predictions(**vars(args))


if __name__ == "__main__":
    # Run the main function
    main()
