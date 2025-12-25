'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2023-10-11 10:32:26 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-11-07 14:33:41 +0100
FilePath     : train_xgboost_model.py
Description  :

Copyright (c) 2023 by everyone, All Rights Reserved.
'''

'''
XGBoost Model Training Module for Binary Classification

This module provides a comprehensive framework for training XGBoost binary classifiers
with k-fold cross-validation support, extensive validation plots, and performance analysis.

Key Features:
- K-fold cross-validation training
- Parallel training support for multiple folds
- Comprehensive model validation and plotting
- ROC curve analysis and feature importance plotting
- Overtraining detection via train/test comparison
- Mass distribution analysis with BDT cuts
- Correlation matrix analysis
'''


import sys, os
import argparse
from typing import Dict, List, Optional, Union, Tuple, Any, NamedTuple, Callable
from copy import deepcopy

import pandas as pd
import numpy as np


from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.metrics import roc_curve
from sklearn.metrics import auc

import xgboost as xgb
from xgboost import XGBClassifier, plot_importance

from scipy import stats
from matplotlib.patches import Rectangle

import matplotlib
import matplotlib.pyplot as plt

import concurrent.futures
from functools import partial

# import mplhep as hep

from pathlib import Path
from dataclasses import dataclass, asdict, field

from tqdm import tqdm
from itertools import product
from copy import deepcopy


from analysis_tool.utils.utils_yaml import read_yaml
from analysis_tool.utils.utils_uproot import load_variables_to_pd_by_uproot
from analysis_tool.correlation.matrixHelper import plot_correlation_heatmap
from analysis_tool.multiprocess.poolHelper import get_optimal_n_threads

from analysis_tool.plotter.compare_distributions import plot_individual_variable_comparison, collect_all_plots_in_one_canvas

from analysis_tool.utils.utils_logging import get_logger

logger = get_logger(__name__, auto_setup_rich_logging=True)


# Use non-interactive backend for matplotlib in batch processing
matplotlib.use("Agg")

# Set the style of the plots
# hep.style.use("LHCb2")

from analysis_tool.MVA.XGBoost.xgboost_helper import DEFAULT_HYPERPARAMETERS, load_hyperparameters_from_yaml
from analysis_tool.MVA.XGBoost.xgboost_helper import TrainingDataContainer, EventWeights, distribute_threads_across_folds, generate_model_paths
from analysis_tool.MVA.XGBoost.xgboost_helper import ModelPredictions, extract_train_test_predictions
from analysis_tool.MVA.XGBoost.xgboost_helper import (
    plot_train_test_comparison,
    plot_single_roc_curve,
    plot_multiple_roc_curves,
    plot_significance_curve,
    plot_feature_importance,
    plot_training_evolution,
    plot_mass_distribution_with_bdt_cuts,
)
from analysis_tool.MVA.XGBoost.xgboost_helper import create_training_test_datasets


def train_xgboost_model(
    X_train_features: np.ndarray,
    y_train_targets: np.ndarray,
    train_weights: np.ndarray,
    *,
    X_test_features: np.ndarray = None,
    y_test_targets: np.ndarray = None,
    test_weights: np.ndarray = None,
    model_output_path: str = "model.json",
    num_parallel_jobs: int = -1,
    feature_names: List[str] = None,
    hyperparameters: Dict[str, Any] = None,
) -> XGBClassifier:
    """
    Train an XGBoost binary classifier with comprehensive configuration options.

    This function creates and trains an XGBoost model with optimized hyperparameters
    for binary classification tasks, including early stopping and evaluation metrics.

    Parameters
    ----------
    X_train_features : np.ndarray
        Training feature matrix
    y_train_targets : np.ndarray
        Training target labels (0=background, 1=signal)
    train_weights : np.ndarray
        Training sample weights
    X_test_features : np.ndarray, optional
        Test feature matrix for validation during training
    y_test_targets : np.ndarray, optional
        Test target labels for validation
    test_weights : np.ndarray, optional
        Test sample weights for validation
    model_output_path : str, default="model.json"
        Path to save the trained model
    num_parallel_jobs : int, default=-1
        Number of parallel jobs for training
    feature_names : List[str], optional
        Names of features for model interpretability
    hyperparameters : Dict[str, Any], optional
        Hyperparameters for the XGBoost model

    Returns
    -------
    XGBClassifier
        Trained XGBoost classifier model
    """
    logger.info(f"Training XGBoost model with {num_parallel_jobs} parallel jobs")

    # ========================================
    # Initialize XGBoost classifier with optimized parameters
    # ========================================
    num_estimators = hyperparameters['num_estimators']
    xgb_model = XGBClassifier(
        # ========================================
        # Core model configuration
        # ========================================
        objective='binary:logistic',  # Binary classification
        booster='gbtree',  # Gradient boosting trees
        tree_method='hist',  # Histogram-based algorithm
        # ! ------- hyperparameters -------
        **hyperparameters,
        # # ========================================
        # # Learning parameters
        # # ========================================
        # learning_rate=learning_rate,  # Step size shrinkage
        # n_estimators=num_estimators,  # Number of boosting rounds
        # max_depth=max_depth,  # Maximum tree depth
        # min_child_weight=min_child_weight,  # Minimum child weight
        # gamma=gamma,  # Minimum split loss
        # max_delta_step=max_delta_step,  # Maximum delta step
        # # ========================================
        # # Regularization parameters
        # # ========================================
        # subsample=0.85,  # Fraction of samples per tree
        # colsample_bytree=0.8,  # Fraction of features per tree
        # reg_alpha=0,  # L1 regularization term
        # reg_lambda=1,  # L2 regularization term
        # # ========================================
        # # Tree-specific parameters (not in DEFAULT_HYPERPARAMETERS)
        # # ========================================
        # colsample_bylevel=1.0,  # Fraction of features per level
        # ! ------- hyperparameters -------
        # ========================================
        # Training configuration
        # ========================================
        scale_pos_weight=1,  # Balance positive/negative weights
        importance_type='gain',  # Feature importance metric
        n_jobs=num_parallel_jobs,  # Parallel processing
        verbosity=1,  # Logging level
        random_state=42,  # Reproducible results
        # ========================================
        # Evaluation and early stopping
        # ========================================
        eval_metric=['auc', 'logloss', 'error'],  # Evaluation metrics
        early_stopping_rounds=int(num_estimators * 0.25),  # Early stopping patience
    )

    # ========================================
    # Configure training with validation
    # ========================================
    logger.info("Starting XGBoost training with early stopping...")

    if X_test_features is not None and y_test_targets is not None:
        # ========================================
        # Training with validation set
        # ========================================
        evaluation_sets = [(X_train_features, y_train_targets), (X_test_features, y_test_targets)]  # Training set  # Validation set

        evaluation_weights = [train_weights, test_weights] if test_weights is not None else None

        # Train with validation monitoring
        xgb_model.fit(X_train_features, y_train_targets, sample_weight=train_weights, eval_set=evaluation_sets, sample_weight_eval_set=evaluation_weights, verbose=True)
    else:
        # ========================================
        # Training without separate validation set
        # ========================================
        logger.warning("No validation set provided - early stopping may be less effective")

        xgb_model.fit(X_train_features, y_train_targets, sample_weight=train_weights, eval_set=[(X_train_features, y_train_targets)], sample_weight_eval_set=[train_weights], verbose=True)

    # ========================================
    # Set feature names for interpretability
    # ========================================
    if feature_names:
        xgb_model.get_booster().feature_names = feature_names

    # ========================================
    # Save trained model
    # ========================================
    Path(model_output_path).parent.mkdir(parents=True, exist_ok=True)
    xgb_model.save_model(model_output_path)
    logger.info(f"Model saved to {model_output_path}")

    return xgb_model


def evaluate_model_performance(model: XGBClassifier, training_data: TrainingDataContainer):
    """
    Evaluate and log comprehensive model performance metrics.

    This function calculates and displays various performance metrics for both
    training and test datasets, including AUC, accuracy, and detailed classification reports.

    Parameters
    ----------
    model : XGBClassifier
        Trained XGBoost model to evaluate
    training_data : TrainingDataContainer
        Container with training and test data
    """
    # ========================================
    # Generate predictions for training and test sets
    # ========================================
    train_predictions_proba = model.predict_proba(training_data.X_train_features)[:, 1]
    test_predictions_proba = model.predict_proba(training_data.X_test_features)[:, 1]

    # ========================================
    # Calculate AUC scores
    # ========================================
    train_auc = roc_auc_score(training_data.y_train_targets, train_predictions_proba, sample_weight=training_data.weight_set.train_all)

    test_auc = roc_auc_score(training_data.y_test_targets, test_predictions_proba, sample_weight=training_data.weight_set.test_all)

    # ========================================
    # Calculate accuracy scores (using 0.5 threshold)
    # ========================================
    train_predictions_binary = (train_predictions_proba > 0.5).astype(int)
    test_predictions_binary = (test_predictions_proba > 0.5).astype(int)

    train_accuracy = accuracy_score(training_data.y_train_targets, train_predictions_binary, sample_weight=training_data.weight_set.train_all)

    test_accuracy = accuracy_score(training_data.y_test_targets, test_predictions_binary, sample_weight=training_data.weight_set.test_all)

    # ========================================
    # Log performance summary
    # ========================================
    logger.info("=" * 50)
    logger.info("MODEL PERFORMANCE SUMMARY")
    logger.info("=" * 50)

    logger.info("Training Set Performance:")
    logger.info(f"  AUC Score: {train_auc:.4f}")
    logger.info(f"  Accuracy:  {train_accuracy:.4f}")

    logger.info("\nTest Set Performance:")
    logger.info(f"  AUC Score: {test_auc:.4f}")
    logger.info(f"  Accuracy:  {test_accuracy:.4f}")

    # ========================================
    # Generate detailed classification report
    # ========================================
    logger.info("\nDetailed Classification Report (Test Set):")
    logger.info("-" * 50)

    classification_report_text = classification_report(training_data.y_test_targets, test_predictions_binary, target_names=["Background", "Signal"], sample_weight=training_data.weight_set.test_all)
    logger.info(classification_report_text)

    # ========================================
    # Check for potential performance issues
    # ========================================
    if test_auc < 0.5:
        logger.warning(f"Test AUC ({test_auc:.4f}) is below random performance - check model configuration")

    auc_difference = abs(train_auc - test_auc)
    if auc_difference > 0.1:
        logger.warning(f"Large AUC difference ({auc_difference:.4f}) between train and test - possible overfitting")

    return test_auc


def run_comprehensive_model_validation(
    model: XGBClassifier,
    training_data: TrainingDataContainer,
    *,
    bdt_cut_threshold: float = 0.5,
    validation_output_dir: str = "validation_plots",
    fold_index: int = -1,
    mass_variable_name: Optional[str] = None,
    mass_variable_display_name: Optional[str] = None,
):
    """
    Run comprehensive model validation with extensive plotting and analysis.

    This function generates a complete set of validation plots and analyses to assess
    model performance, including overtraining detection, ROC analysis, feature importance,
    and optional mass distribution analysis.

    Parameters
    ----------
    model : XGBClassifier
        Trained XGBoost model to validate
    training_data : TrainingDataContainer
        Container with training and test data
    bdt_cut_threshold : float, default=0.5
        BDT score threshold for signal/background separation
    validation_output_dir : str, default="validation_plots"
        Directory to save validation plots
    fold_index : int, default=-1
        Fold number for labeling (-1 for single model)
    mass_variable_name : str, optional
        Name of mass variable for distribution analysis
    mass_variable_display_name : str, optional
        Display name for mass variable in plots
    """

    # ========================================
    # Create validation output directory
    # ========================================
    Path(validation_output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Running model validation - outputs will be saved to {validation_output_dir}")

    # ========================================
    # Generate overtraining analysis plot
    # ========================================
    logger.info("Generating overtraining analysis plot...")

    model_predictions = extract_train_test_predictions(model, training_data)
    plot_train_test_comparison(
        predictions=model_predictions, num_bins=40, weight_set=training_data.weight_set, output_plot_path=f"{validation_output_dir}/overtraining_analysis.pdf", fold_index=fold_index
    )

    # ========================================
    # Generate ROC curve analysis
    # ========================================
    logger.info("Generating ROC curve analysis...")

    plot_single_roc_curve(
        X_test=training_data.X_test_features,
        y_test=training_data.y_test_targets,
        test_weights=training_data.weight_set.test_all,
        model=model,
        plot_title="XGBoost ROC Curve",
        line_color="navy",
        output_plot_path=f"{validation_output_dir}/roc_curve.pdf",
    )

    # ========================================
    # Generate significance optimization plot
    # ========================================
    logger.info("Generating significance optimization plot...")

    plot_significance_curve(
        X_test=training_data.X_test_features,
        y_test=training_data.y_test_targets,
        test_weights=training_data.weight_set.test_all,
        model=model,
        num_signal_events=len(training_data.signal_dataframe),
        num_background_events=len(training_data.background_dataframe),
        output_plot_path=f"{validation_output_dir}/significance_optimization.pdf",
    )

    # ========================================
    # Generate feature importance plot
    # ========================================
    logger.info("Generating feature importance plot...")

    plot_feature_importance(model=model, output_plot_path=f"{validation_output_dir}/feature_importance.pdf", feature_names=training_data.bdt_feature_names)

    # ========================================
    # Generate training evolution plot
    # ========================================
    logger.info("Generating training evolution plot...")

    plot_training_evolution(model=model, output_plot_path=f"{validation_output_dir}/training_evolution.pdf", metrics_to_plot=None, figure_size=(10, 8))

    # ========================================
    # Generate mass distribution analysis (if requested)
    # ========================================
    if mass_variable_name:
        logger.info("Generating mass distribution analysis...")

        # Apply BDT predictions to data
        for dataset_name, dataframe in [("signal", training_data.signal_dataframe), ("background", training_data.background_dataframe)]:

            # Generate BDT predictions
            bdt_predictions = model.predict_proba(dataframe[training_data.bdt_feature_names])[:, 1]
            dataframe_with_bdt = dataframe.assign(_XGBDT=bdt_predictions)

            # Create mass distribution plot
            plot_mass_distribution_with_bdt_cuts(
                mass_variable=mass_variable_name,
                dataframe=dataframe_with_bdt,
                bdt_cut_threshold=bdt_cut_threshold,
                weight_column=training_data.standardized_weight_column,
                output_plot_path=f"{validation_output_dir}/mass_distribution_{dataset_name}.pdf",
                particle_name=mass_variable_display_name or mass_variable_name,
            )

    # ========================================
    # Generate BDT variable distribution comparisons
    # ========================================
    logger.info("Generating BDT variable distribution comparisons...")

    # Create directories for individual and collective plots
    individual_plots_dir = Path(validation_output_dir) / "variable_distributions" / "individual"
    collective_plots_dir = Path(validation_output_dir) / "variable_distributions" / "collective"
    individual_plots_dir.mkdir(parents=True, exist_ok=True)
    collective_plots_dir.mkdir(parents=True, exist_ok=True)

    # Generate individual variable comparison plots
    individual_plot_paths = []
    for variable_name in training_data.bdt_feature_names:
        plot_path = plot_individual_variable_comparison(
            var_title=variable_name,
            datas=[training_data.signal_dataframe[variable_name], training_data.background_dataframe[variable_name]],
            weights=[training_data.signal_dataframe[training_data.standardized_weight_column], training_data.background_dataframe[training_data.standardized_weight_column]],
            labels=["Signal", "Background"],
            output_plot_dir=str(individual_plots_dir),
        )
        individual_plot_paths.append(plot_path)

    # Collect all individual plots into a single canvas
    collect_all_plots_in_one_canvas(path_to_single_figs=individual_plot_paths, output_plot_dir=str(collective_plots_dir), exts=["pdf", "png"])

    # ========================================
    # Generate correlation matrix analysis
    # ========================================
    logger.info("Generating correlation matrix analysis...")

    for clustering_enabled in [True, False]:
        cluster_suffix = "clustered" if clustering_enabled else "unclustered"

        # Signal correlation matrix
        plot_correlation_heatmap(
            training_data.signal_dataframe[training_data.bdt_feature_names],
            output_plot_name=f"{validation_output_dir}/correlation_matrix_signal_{cluster_suffix}.pdf",
            df_weight=training_data.signal_dataframe[training_data.standardized_weight_column],
            figsize=(14, 12),
            title="Feature Correlation Matrix - Signal",
            cluster=clustering_enabled,
        )

        # Background correlation matrix
        plot_correlation_heatmap(
            training_data.background_dataframe[training_data.bdt_feature_names],
            output_plot_name=f"{validation_output_dir}/correlation_matrix_background_{cluster_suffix}.pdf",
            df_weight=training_data.background_dataframe[training_data.standardized_weight_column],
            figsize=(14, 12),
            title="Feature Correlation Matrix - Background",
            cluster=clustering_enabled,
        )

    logger.info("Model validation complete!")


# ========================================
# Parallel training support functions
# ========================================


def train_single_fold_model(
    fold_index: int,
    training_data: TrainingDataContainer,
    model_output_path: str,
    num_threads: int,
    bdt_feature_names: List[str],
    hyperparameters_yaml: str,
) -> Tuple[int, XGBClassifier]:
    """
    Train a single fold model for parallel k-fold cross-validation.

    This function is designed to be called in parallel for efficient k-fold training.

    Parameters
    ----------
    fold_index : int
        Index of the current fold being trained
    training_data : TrainingDataContainer
        Training data container for this fold
    model_output_path : str
        Path to save the trained model
    num_threads : int
        Number of threads to use for this model
    bdt_feature_names : List[str]
        Names of BDT features

    hyperparameters_yaml : str
        Path to YAML file with hyperparameters (from Optuna optimization)

    Returns
    -------
    Tuple[int, XGBClassifier]
        Tuple of (fold_index, trained_model)
    """
    # ========================================
    # Train the model for this fold
    # ========================================
    logger.info(f"Training model for fold {fold_index}")

    # Load hyperparameters from YAML file if provided
    if hyperparameters_yaml:
        hyperparameters = load_hyperparameters_from_yaml(hyperparameters_yaml)
    else:
        hyperparameters = deepcopy(DEFAULT_HYPERPARAMETERS)

    trained_model = train_xgboost_model(
        X_train_features=training_data.X_train_features,
        y_train_targets=training_data.y_train_targets,
        train_weights=training_data.weight_set.train_all,
        X_test_features=training_data.X_test_features,
        y_test_targets=training_data.y_test_targets,
        test_weights=training_data.weight_set.test_all,
        model_output_path=model_output_path,
        num_parallel_jobs=num_threads,
        feature_names=bdt_feature_names,
        hyperparameters=hyperparameters,
    )

    return fold_index, trained_model


def execute_complete_xgboost_training_pipeline(
    signal_file_paths: List[str],
    signal_tree_name: str,
    background_file_paths: List[str],
    background_tree_name: str,
    signal_weight_expression: str,
    background_weight_expression: str,
    bdt_variables_config_file: str,
    config_mode: str,
    hyperparameters_yaml: str,
    num_cross_validation_folds: int,
    fold_splitting_variable: str,
    model_output_directory: str,
    model_filename: str,
    n_threads: int,
    # Optional parameters for mass distribution analysis
    plot_mass_var_branch_name: Optional[str] = None,
    plot_mass_var_display_name: Optional[str] = None,
    max_signal_events: int = -1,
    max_background_events: int = -1,
    training_timeout_seconds: int = 12 * 60 * 60,  # 12 hours default
):
    """
    Execute the complete XGBoost training pipeline with k-fold cross-validation.

    This is the main orchestration function that coordinates all aspects of model training,
    validation, and analysis. It handles both single model training and k-fold cross-validation
    with comprehensive plotting and performance analysis.

    Parameters
    ----------
    signal_file_paths : List[str]
        List of paths to signal ROOT files
    signal_tree_name : str
        Name of TTree in signal files
    background_file_paths : List[str]
        List of paths to background ROOT files
    background_tree_name : str
        Name of TTree in background files
    signal_weight_expression : str
        Expression for calculating signal event weights
    background_weight_expression : str
        Expression for calculating background event weights
    bdt_variables_config_file : str
        Path to YAML configuration file containing BDT variables
    config_mode : str
        Configuration mode for reading BDT variables from the bdt_variables_config_file which is a YAML file
    hyperparameters_yaml : str
        Path to YAML file with hyperparameters (from Optuna optimization)
    num_cross_validation_folds : int
        Number of k-fold cross-validation splits
    fold_splitting_variable : str
        Variable name for splitting events into folds
    model_output_directory : str
        Directory to save trained models and validation plots
    model_filename : str
        Filename for saved models
    n_threads : int
        Number of threads for parallel processing
    plot_mass_var_branch_name : Optional[str]
        Name of mass variable for distribution analysis
    plot_mass_var_display_name : Optional[str]
        Display name for mass variable in plots
    max_signal_events : int, default=-1
        Maximum number of signal events to use (-1 = all)
    max_background_events : int, default=-1
        Maximum number of background events to use (-1 = all)
    training_timeout_seconds : int, default=43200
        Timeout for training in seconds (12 hours default)
    """

    # ========================================
    # Initialize and validate configuration
    # ========================================
    logger.info("=" * 60)
    logger.info("STARTING XGBOOST TRAINING PIPELINE")
    logger.info("=" * 60)

    # Convert file lists to semicolon-separated strings for compatibility
    signal_files_combined = ';'.join(signal_file_paths)
    background_files_combined = ';'.join(background_file_paths)

    # Validate and adjust thread configuration
    validated_thread_count = get_optimal_n_threads(n_threads)

    logger.info(f"Configuration Summary:")
    logger.info(f"  Signal files: {len(signal_file_paths)} files")
    logger.info(f"  Background files: {len(background_file_paths)} files")
    logger.info(f"  Cross-validation folds: {num_cross_validation_folds}")
    logger.info(f"  Parallel threads: {validated_thread_count}")
    logger.info(f"  Output directory: {model_output_directory}")

    # ========================================
    # Load BDT variable configuration
    # ========================================
    logger.info("Loading BDT variable configuration...")

    bdt_feature_list = read_yaml(bdt_variables_config_file, config_mode)
    logger.info(f"Loaded {len(bdt_feature_list)} BDT variables: {bdt_feature_list}")

    # ========================================
    # Create training and test datasets
    # ========================================
    logger.info("Creating training and test datasets...")

    training_data_containers = create_training_test_datasets(
        signal_files=signal_files_combined,
        background_files=background_files_combined,
        signal_tree_name=signal_tree_name,
        background_tree_name=background_tree_name,
        bdt_feature_list=bdt_feature_list,
        signal_weight_expression=signal_weight_expression,
        background_weight_expression=background_weight_expression,
        max_signal_events=max_signal_events,
        max_background_events=max_background_events,
        num_folds=num_cross_validation_folds,
        fold_split_variable=fold_splitting_variable,
        additional_signal_variables=[plot_mass_var_branch_name] if plot_mass_var_branch_name else [],
        additional_background_variables=[plot_mass_var_branch_name] if plot_mass_var_branch_name else [],
    )

    # ========================================
    # Generate model output paths
    # ========================================
    model_output_paths = generate_model_paths(output_dir=model_output_directory, model_filename=model_filename, num_folds=num_cross_validation_folds)

    # ========================================
    # Create output directories
    # ========================================
    for fold_idx in range(num_cross_validation_folds if num_cross_validation_folds > 1 else 1):
        fold_output_dir = f"{model_output_directory}/{fold_idx}" if num_cross_validation_folds > 1 else model_output_directory
        Path(fold_output_dir).mkdir(parents=True, exist_ok=True)

    # ========================================
    # Execute parallel model training
    # ========================================
    logger.info("=" * 50)
    logger.info("STARTING PARALLEL MODEL TRAINING")
    logger.info("=" * 50)

    # Calculate thread distribution across folds
    thread_distribution = distribute_threads_across_folds(total_threads=validated_thread_count, num_folds=len(training_data_containers), min_threads_per_fold=1)

    # Dictionary to store trained models
    trained_models_dict = {}

    # Execute parallel training using ProcessPoolExecutor
    with concurrent.futures.ProcessPoolExecutor(max_workers=validated_thread_count) as executor:

        # ========================================
        # Submit training tasks for each fold
        # ========================================
        future_to_fold_mapping = {}

        for fold_idx, training_data in training_data_containers.items():

            # Submit training task for this fold
            training_future = executor.submit(train_single_fold_model, fold_idx, training_data, model_output_paths[fold_idx], thread_distribution[fold_idx], bdt_feature_list, hyperparameters_yaml)

            future_to_fold_mapping[training_future] = fold_idx

        # ========================================
        # Process completed training tasks
        # ========================================
        progress_bar = tqdm(
            concurrent.futures.as_completed(future_to_fold_mapping.keys(), timeout=training_timeout_seconds), total=len(future_to_fold_mapping), desc="Training models in parallel", colour="blue"
        )

        for completed_future in progress_bar:
            fold_idx = future_to_fold_mapping[completed_future]

            try:
                # Retrieve training results
                returned_fold_idx, trained_model = completed_future.result()
                trained_models_dict[returned_fold_idx] = trained_model

                logger.info(f"Training completed successfully for fold {returned_fold_idx}")

            except Exception as training_exception:
                logger.error(f"Training failed for fold {fold_idx}: {training_exception}")
                raise training_exception

    # ========================================
    # Execute sequential model validation and analysis
    # ========================================
    logger.info("=" * 50)
    logger.info("STARTING MODEL VALIDATION AND ANALYSIS")
    logger.info("=" * 50)

    validation_progress = tqdm(training_data_containers.items(), desc="Validating models", colour="green", ascii=" >━")

    for fold_idx, training_data in validation_progress:

        # ========================================
        # Retrieve trained model for this fold
        # ========================================
        trained_model = trained_models_dict[fold_idx]

        # Configure model threading for validation
        trained_model.get_booster().set_param('nthread', validated_thread_count)

        # ========================================
        # Evaluate model performance
        # ========================================
        logger.info(f"Evaluating performance for fold {fold_idx}")

        test_auc_score = evaluate_model_performance(trained_model, training_data)

        # Warn about poor performance
        if test_auc_score < 0.5:
            logger.warning(f"Fold {fold_idx} has poor performance (AUC: {test_auc_score:.3f})")

        # ========================================
        # Run comprehensive validation analysis
        # ========================================
        validation_output_directory = f"{Path(model_output_paths[fold_idx]).parent}/comprehensive_validation"
        fold_display_index = -1 if num_cross_validation_folds <= 1 else fold_idx

        run_comprehensive_model_validation(
            model=trained_model,
            training_data=training_data,
            validation_output_dir=validation_output_directory,
            fold_index=fold_display_index,
            mass_variable_name=plot_mass_var_branch_name,
            mass_variable_display_name=plot_mass_var_display_name,
            bdt_cut_threshold=0.5,
        )

    # ========================================
    # Generate combined k-fold analysis (if applicable)
    # ========================================
    if num_cross_validation_folds > 1:
        logger.info("Generating combined k-fold cross-validation analysis...")

        # Create combined ROC curve plot
        combined_roc_output_path = f"{model_output_directory}/combined_kfold_roc_curves.pdf"
        plot_multiple_roc_curves(fold_data_dict=training_data_containers, model_dict=trained_models_dict, output_plot_path=combined_roc_output_path, plot_title="XGBoost K-Fold CV ROC Curves")

        logger.info(f"Combined k-fold analysis saved to {combined_roc_output_path}")

    # ========================================
    # Training pipeline completion
    # ========================================
    logger.info("=" * 60)
    logger.info("XGBOOST TRAINING PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)

    logger.info(f"Trained models saved to: {model_output_directory}")
    logger.info("Validation plots and analysis available in respective validation directories")

    return trained_models_dict, training_data_containers


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="XGBoost Binary Classification Training Pipeline")

    # ========================================
    # Input data configuration
    # ========================================
    parser.add_argument('--signal-file-paths', type=str, required=True, nargs='+', help='Signal file paths')
    parser.add_argument('--signal-tree-name', type=str, default='DecayTree', help='Signal tree name')
    parser.add_argument('--background-file-paths', type=str, required=True, nargs='+', help='Background file paths')
    parser.add_argument('--background-tree-name', type=str, default='DecayTree', help='Background tree name')

    # ========================================
    # Event weighting configuration
    # ========================================
    parser.add_argument('--signal-weight-expression', type=str, required=False, default='1', help='Signal weight expression')
    parser.add_argument('--background-weight-expression', type=str, required=False, default='1', help='Background weight expression')

    # ========================================
    # BDT feature configuration
    # ========================================
    parser.add_argument('--bdt-variables-config-file', type=str, required=True, help='Path to the YAML file containing the BDT variables')
    parser.add_argument('--config-mode', type=str, required=True, help='Configuration mode for reading the BDT variables from the config file')

    # ========================================
    # Hyperparameter configuration
    # ========================================
    parser.add_argument('--hyperparameters-yaml', type=str, default=None, help='Path to YAML file with hyperparameters (from Optuna optimization)')

    # ========================================
    # Cross-validation configuration
    # ========================================
    parser.add_argument('--num-cross-validation-folds', type=int, default=10, help='Number of cross-validation folds')
    parser.add_argument('--fold-splitting-variable', type=str, default='eventNumber', help='Variable name for splitting events into folds')

    # ========================================
    # Output configuration
    # ========================================
    parser.add_argument('--model-output-directory', type=str, default='output/models', help='Output directory for models and plots')
    parser.add_argument(
        '--model-filename',
        type=str,
        default='xgb_model.json',
        help='Output model JSON name, will be saved in the output directory (k-fold models will be saved in the output directory/kFolds subdirectory, be handled automatically)',
    )

    # ========================================
    # Performance and resource configuration
    # ========================================
    parser.add_argument('--n-threads', type=int, default=0, help='Number of threads to use. Default: 0. [0: half of the threads, -1: all threads, other: specific number of threads]')

    parser.add_argument('--training-timeout-seconds', type=int, default=24 * 60 * 60, help='Timeout for training in seconds, default is 24h')

    # ========================================
    # Mass distribution analysis (optional)
    # ========================================
    parser.add_argument('--plot-mass-var-branch-name', type=str, default=None, help='Branch name for the particle mass variable')
    parser.add_argument('--plot-mass-var-display-name', type=str, default=None, help='Display name for the particle mass variable')

    # ========================================
    # Event limit configuration
    # ========================================
    parser.add_argument('--max-signal-events', type=int, default=-1, help='Maximum number of signal events to use for training and testing')
    parser.add_argument('--max-background-events', type=int, default=-1, help='Maximum number of background events to use for training and testing')

    return parser


def main(args=None):
    """Main entry point for the script."""
    if args is None:
        args = get_parser().parse_args()
    execute_complete_xgboost_training_pipeline(**vars(args))


if __name__ == "__main__":

    # Run the main function
    main()
