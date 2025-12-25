'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-11-07 10:05:05 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-12-11 08:27:54 +0100
FilePath     : xgboost_helper.py
Description  :

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

import sys, os
import argparse
from typing import Dict, List, Optional, Union, Tuple, Any, NamedTuple, Callable
import gc
from copy import deepcopy

import pandas as pd
import numpy as np

import multiprocessing

from datetime import datetime

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
from analysis_tool.utils.utils_dict import compare_dicts, update_config

from analysis_tool.plotter.compare_distributions import plot_individual_variable_comparison, collect_all_plots_in_one_canvas

# Use rich backend for logging
import logging
from analysis_tool.utils.utils_logging import get_logger

logger = get_logger(__name__, auto_setup_rich_logging=True)


# ========================================
# Event weights
# ========================================
class EventWeights(NamedTuple):
    """Container for organized event weights across different sample categories."""

    train_all: np.ndarray  # All training sample weights
    test_all: np.ndarray  # All test sample weights
    train_signal: np.ndarray  # Training signal weights
    train_background: np.ndarray  # Training background weights
    test_signal: np.ndarray  # Test signal weights
    test_background: np.ndarray  # Test background weights


# ========================================
# Training data container
# ========================================
@dataclass
class TrainingDataContainer:
    """
    Comprehensive container for all training and validation data.

    This dataclass organizes all components needed for BDT training,
    including original dataframes, processed features, targets, and weights.
    """

    # ========================================
    # Original dataframes
    # ========================================
    signal_dataframe: pd.DataFrame = field(default_factory=pd.DataFrame)
    background_dataframe: pd.DataFrame = field(default_factory=pd.DataFrame)

    # ========================================
    # Processed training/test arrays
    # ========================================
    X_train_features: np.ndarray = field(default_factory=lambda: np.array([]))
    X_test_features: np.ndarray = field(default_factory=lambda: np.array([]))
    y_train_targets: np.ndarray = field(default_factory=lambda: np.array([]))
    y_test_targets: np.ndarray = field(default_factory=lambda: np.array([]))

    # ========================================
    # Event weights and metadata
    # ========================================
    weight_set: Optional[EventWeights] = None
    bdt_feature_names: List[str] = field(default_factory=list)
    signal_weight_expression: str = field(default_factory=str)
    background_weight_expression: str = field(default_factory=str)
    standardized_weight_column: str = field(default_factory=lambda: "standardized_bdt_weight")


@dataclass
class ModelPredictions:
    """Container for BDT predictions across different sample categories."""

    train_signal: np.ndarray = None  # Training signal predictions
    train_background: np.ndarray = None  # Training background predictions
    test_signal: np.ndarray = None  # Test signal predictions
    test_background: np.ndarray = None  # Test background predictions


def extract_train_test_predictions(model: XGBClassifier, data_train_test: TrainingDataContainer) -> ModelPredictions:
    """
    Extract BDT predictions for signal and background from training and test datasets.

    This function generates predictions needed for overtraining analysis by comparing
    the BDT output distributions between training and test samples.

    Parameters
    ----------
    model : XGBClassifier
        Trained XGBoost classifier
    data_train_test : TrainingDataContainer
        Container with training and test data splits

    Returns
    -------
    ModelPredictions
        Dataclass containing predictions for all sample categories
    """

    predictions = ModelPredictions()

    # Extract signal events (y > 0.5) and background events (y ≤ 0.5)
    # Get probability predictions for class 1 (signal class)
    train_signal_mask = data_train_test.y_train_targets > 0.5
    train_background_mask = data_train_test.y_train_targets <= 0.5
    test_signal_mask = data_train_test.y_test_targets > 0.5
    test_background_mask = data_train_test.y_test_targets <= 0.5

    # Generate predictions for each category
    predictions.train_signal = model.predict_proba(data_train_test.X_train_features[train_signal_mask])[:, 1].ravel()
    predictions.train_background = model.predict_proba(data_train_test.X_train_features[train_background_mask])[:, 1].ravel()
    predictions.test_signal = model.predict_proba(data_train_test.X_test_features[test_signal_mask])[:, 1].ravel()
    predictions.test_background = model.predict_proba(data_train_test.X_test_features[test_background_mask])[:, 1].ravel()

    return predictions


def plot_train_test_comparison(predictions: ModelPredictions, num_bins: int, weight_set: EventWeights, output_plot_path: str = None, fold_index: int = -1):
    """
    Create overtraining analysis plot comparing BDT output distributions.

    This plot helps identify overtraining by comparing the BDT score distributions
    between training and test samples for both signal and background. Good agreement
    indicates the model generalizes well.

    Parameters
    ----------
    predictions : ModelPredictions
        BDT predictions for train/test signal/background samples
    num_bins : int
        Number of histogram bins for the distributions
    weight_set : EventWeights
        Event weights for proper histogram normalization
    output_plot_path : str, optional
        Path to save the plot (if None, plot is not saved)
    fold_index : int, default=-1
        Fold number for plot labeling (-1 for single model)
    """

    # ========================================
    # Determine plot range from all predictions
    # ========================================

    all_predictions = [predictions.train_signal, predictions.train_background, predictions.test_signal, predictions.test_background]

    min_score = min(np.min(pred) for pred in all_predictions)
    max_score = max(np.max(pred) for pred in all_predictions)

    # Adjust boundaries for cleaner plots
    if min_score > 0 and min_score < 0.05:
        min_score = 0
    if max_score < 1 and max_score > 0.95:
        max_score = 1

    score_range = (min_score, max_score)

    # Create the comparison plot
    plt.figure(figsize=(8, 6))

    # ========================================
    # Plot training samples as filled histograms
    # ========================================

    plt.hist(predictions.train_signal, color="blue", alpha=0.5, range=score_range, bins=num_bins, histtype="stepfilled", density=True, label="Signal (train)", weights=weight_set.train_signal)
    plt.hist(
        predictions.train_background, color="red", alpha=0.5, range=score_range, bins=num_bins, histtype="stepfilled", density=True, label="Background (train)", weights=weight_set.train_background
    )

    # ========================================
    # Plot test samples as error bars
    # ========================================

    for pred_data, weights, color, label in [
        (predictions.test_signal, weight_set.test_signal, "blue", "Signal (test)"),
        (predictions.test_background, weight_set.test_background, "red", "Background (test)"),
    ]:

        # Compute weighted histogram with proper uncertainty calculation
        hist_raw, bin_edges = np.histogram(pred_data, bins=num_bins, range=score_range, weights=weights)
        weights_sq, _ = np.histogram(pred_data, bins=num_bins, range=score_range, weights=weights**2)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        # Calculate density normalization
        bin_width = (score_range[1] - score_range[0]) / num_bins
        norm_factor = np.sum(weights) * bin_width if np.sum(weights) > 0 else 1.0

        # Apply density normalization
        hist_counts = hist_raw / norm_factor
        uncertainties = np.sqrt(weights_sq) / norm_factor

        plt.errorbar(bin_centers, hist_counts, yerr=uncertainties, fmt="o", color=color, label=label)

    # Perform Kolmogorov-Smirnov tests for overtraining assessment
    # Note: K-S test does not account for event weights
    # For weighted samples, interpret with caution
    ks_stat_signal, p_val_signal = stats.ks_2samp(predictions.train_signal, predictions.test_signal)
    ks_stat_background, p_val_background = stats.ks_2samp(predictions.train_background, predictions.test_background)

    # ========================================
    # Add KS test results to plot
    # ========================================

    ks_text = f"Kolmogorov-Smirnov Tests:\n" f"Signal: stat={ks_stat_signal:.3f}\n" f"Background: stat={ks_stat_background:.3f}"

    # Position text box in upper left
    text_props = dict(boxstyle='round', facecolor='white', alpha=0.8)
    plt.gca().text(0.02, 0.98, ks_text, transform=plt.gca().transAxes, fontsize=11, verticalalignment='top', bbox=text_props)

    # ========================================
    # Configure plot appearance
    # ========================================
    plt.xticks(np.arange(min_score, max_score * 1.01, step=0.1))
    xlabel = "BDT Score" if fold_index == -1 else f"BDT Score (Fold {fold_index})"
    plt.xlabel(xlabel)
    plt.ylabel("Normalized Event Density")
    plt.legend(loc="best", ncol=2, fontsize=11)
    plt.grid(alpha=0.3)
    plt.tight_layout()

    # ========================================
    # Save plot if path provided
    # ========================================

    if output_plot_path:
        Path(output_plot_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_plot_path, dpi=300, bbox_inches='tight')
        logger.info(f"Overtraining analysis plot saved to {output_plot_path}")

    plt.close()


def plot_single_roc_curve(
    X_test: np.ndarray, y_test: np.ndarray, test_weights: np.ndarray, model: XGBClassifier, plot_title: str, line_color: str, output_plot_path: str = None, custom_label: str = None
) -> str:
    """
    Generate ROC curve plot for binary classification performance evaluation.

    Parameters
    ----------
    X_test : np.ndarray
        Test feature matrix
    y_test : np.ndarray
        Test target labels (0=background, 1=signal)
    test_weights : np.ndarray
        Sample weights for test events
    model : XGBClassifier
        Trained classifier model
    plot_title : str
        Plot title
    line_color : str
        Color for ROC curve line
    output_plot_path : str, optional
        Path to save the plot
    custom_label : str, optional
        Custom label for the ROC curve

    Returns
    -------
    str
        Path to saved plot (or None if not saved)
    """
    # Generate predictions and ROC curve data
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    false_pos_rate, true_pos_rate, thresholds = roc_curve(y_test, y_pred_proba, sample_weight=test_weights)
    roc_auc_score_val = roc_auc_score(y_test, y_pred_proba, sample_weight=test_weights)
    auc_score = auc(false_pos_rate, true_pos_rate)

    # Log performance metrics
    logger.info("ROC Analysis Results:")
    logger.info(classification_report(y_test, model.predict(X_test), target_names=["background", "signal"], sample_weight=test_weights))
    logger.info(f"Area under ROC curve: {roc_auc_score_val:.4f}")

    # Create ROC curve plot
    plt.figure(figsize=(8, 6))
    plt.xlim([-0.01, 1.00])
    plt.ylim([-0.01, 1.01])

    # Plot diagonal reference line (random classifier)
    plt.plot([0, 1], [0, 1], color="grey", linestyle="--", alpha=0.7, label="Random Classifier")

    # Plot ROC curve
    curve_label = custom_label if custom_label else f"ROC Curve (AUC = {auc_score:.3f})"
    plt.plot(false_pos_rate, true_pos_rate, linewidth=2, color=line_color, label=curve_label)

    # Configure plot
    plt.xlabel("False Positive Rate", fontsize=12)
    plt.ylabel("True Positive Rate", fontsize=12)
    plt.title(plot_title, fontsize=14)
    plt.legend(loc="lower right", fontsize=12)
    plt.grid(alpha=0.3)
    plt.tight_layout()

    # Save plot
    if output_plot_path:
        Path(output_plot_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_plot_path, dpi=300, bbox_inches='tight')
        logger.info(f"ROC curve saved to {output_plot_path}")

    plt.close()
    return output_plot_path


def plot_multiple_roc_curves(fold_data_dict: Dict, model_dict: Dict, output_plot_path: str, plot_title: str = "XGBoost ROC Curves", curve_colors: List = None) -> str:
    """
    Create combined ROC plot showing performance across all k-fold models.

    This visualization helps assess model stability and performance variation
    across different training/validation splits in k-fold cross-validation.

    Parameters
    ----------
    fold_data_dict : Dict
        Dictionary mapping fold indices to TrainingDataContainer objects
    model_dict : Dict
        Dictionary mapping fold indices to trained models
    output_plot_path : str
        Path for saving the combined ROC plot
    plot_title : str, default="XGBoost ROC Curves"
        Plot title
    curve_colors : List, optional
        Colors for individual fold curves

    Returns
    -------
    str
        Path to the saved plot
    """

    # ========================================
    # Create figure
    # ========================================
    plt.figure(figsize=(10, 8))
    plt.xlim([-0.01, 1.00])
    plt.ylim([-0.01, 1.01])
    plt.plot([0, 1], [0, 1], color='grey', linestyle='--', label='Random classifier')

    # ========================================
    # Generate colors if not provided
    # ========================================
    if curve_colors is None:
        import matplotlib.cm as cm

        curve_colors = cm.tab10(np.linspace(0, 1, len(fold_data_dict)))

    # ========================================
    # Storage for mean ROC calculation
    # ========================================
    mean_false_pos_rate = np.linspace(0, 1, 100)
    interpolated_true_pos_rates = []
    auc_scores = []

    # ========================================
    # Plot ROC curve for each fold
    # ========================================
    for fold_idx, data in fold_data_dict.items():
        model = model_dict[fold_idx]

        # Generate ROC data
        y_pred_proba = model.predict_proba(data.X_test_features)[:, 1]
        fpr, tpr, _ = roc_curve(data.y_test_targets, y_pred_proba, sample_weight=data.weight_set.test_all)
        fold_auc = roc_auc_score(data.y_test_targets, y_pred_proba, sample_weight=data.weight_set.test_all)
        auc_scores.append(fold_auc)

        # Interpolate TPR to common FPR grid
        interp_tpr = np.interp(mean_false_pos_rate, fpr, tpr)
        interp_tpr[0] = 0.0  # Ensure curve starts at origin
        interpolated_true_pos_rates.append(interp_tpr)

        # Plot individual fold curve
        fold_color = curve_colors[fold_idx] if isinstance(curve_colors, list) else f'C{fold_idx}'
        plt.plot(fpr, tpr, linewidth=1, alpha=0.6, color=fold_color, label=f'Fold {fold_idx} (AUC = {fold_auc:.3f})')

    # ========================================
    # Calculate and plot mean ROC curve
    # ========================================
    mean_true_pos_rate = np.mean(interpolated_true_pos_rates, axis=0)
    mean_true_pos_rate[-1] = 1.0  # Ensure curve ends at (1,1)
    mean_auc = np.mean(auc_scores)
    std_auc = np.std(auc_scores)

    plt.plot(mean_false_pos_rate, mean_true_pos_rate, 'navy', linewidth=3, alpha=0.9, label=f'Mean ROC (AUC = {mean_auc:.3f} ± {std_auc:.3f})')

    # ========================================
    # Add confidence interval
    # ========================================
    std_true_pos_rate = np.std(interpolated_true_pos_rates, axis=0)
    tpr_upper = np.minimum(mean_true_pos_rate + std_true_pos_rate, 1)
    tpr_lower = np.maximum(mean_true_pos_rate - std_true_pos_rate, 0)
    plt.fill_between(mean_false_pos_rate, tpr_lower, tpr_upper, color='grey', alpha=0.2, label='± 1 std. dev.')

    # ========================================
    # Configure plot
    # ========================================
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title(plot_title, fontsize=14)
    plt.legend(loc='lower right', fontsize=9)
    plt.grid(alpha=0.3)

    # ========================================
    # Save plot
    # ========================================
    Path(output_plot_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_plot_path, bbox_inches='tight', dpi=300)
    plt.close()

    logger.info(f"Combined ROC curves saved to {output_plot_path}")
    return output_plot_path


def plot_significance_curve(
    X_test: np.ndarray, y_test: np.ndarray, test_weights: np.ndarray, model: XGBClassifier, num_signal_events: int, num_background_events: int, output_plot_path: str, custom_label: str = None
) -> str:
    """
    Plot significance metric (S/√(S+B)) as a function of BDT cut threshold.

    This plot helps determine the optimal BDT cut value that maximizes the
    statistical significance for signal discovery or measurement.

    Parameters
    ----------
    X_test : np.ndarray
        Test feature matrix
    y_test : np.ndarray
        Test target labels (0=background, 1=signal)
    test_weights : np.ndarray
        Sample weights for test events
    model : XGBClassifier
        Trained classifier model
    num_signal_events : int
        Expected number of signal events in analysis
    num_background_events : int
        Expected number of background events in analysis
    output_plot_path : str
        Path to save the significance plot
    custom_label : str, optional
        Custom label for the significance curve

    Returns
    -------
    str
        Path to the saved plot
    """
    # ========================================
    # Generate BDT predictions and ROC data
    # ========================================
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    false_pos_rate, true_pos_rate, bdt_thresholds = roc_curve(y_test, y_pred_proba, sample_weight=test_weights)

    # ========================================
    # Calculate significance for each threshold
    # ========================================
    signal_efficiency = true_pos_rate
    background_efficiency = false_pos_rate

    # Expected signal and background yields after cuts
    expected_signal = num_signal_events * signal_efficiency
    expected_background = num_background_events * background_efficiency

    # Calculate significance metric: S/√(S+B)
    # Use safe division to avoid division by zero
    significance_metric = np.divide(expected_signal, np.sqrt(expected_signal + expected_background), out=np.zeros_like(expected_signal), where=(expected_signal + expected_background) > 0)

    # ========================================
    # Find optimal cut point
    # ========================================
    max_significance = np.max(significance_metric)
    optimal_threshold_idx = np.argmax(significance_metric)
    optimal_bdt_cut = bdt_thresholds[optimal_threshold_idx] if optimal_threshold_idx < len(bdt_thresholds) else 0.5

    # ========================================
    # Create significance plot
    # ========================================
    plt.figure(figsize=(8, 6))

    curve_label = custom_label if custom_label else "Significance Curve"
    plt.plot(bdt_thresholds, significance_metric, linewidth=2, label=curve_label)

    # Mark optimal cut point
    plt.axhline(max_significance, color="red", linestyle="--", alpha=0.8, label=f"Max Significance: {max_significance:.2f}")
    plt.axvline(optimal_bdt_cut, color="green", linestyle="--", alpha=0.8, label=f"Optimal Cut: {optimal_bdt_cut:.3f}")

    # ========================================
    # Configure plot appearance
    # ========================================
    plt.xlabel("BDT Score Threshold", fontsize=12)
    plt.ylabel(r"Significance: $S/\sqrt{S+B}$", fontsize=12)
    plt.title("BDT Cut Optimization", fontsize=14)
    plt.xlim(0, 1.0)
    plt.legend(loc="best", fontsize=10)
    plt.grid(alpha=0.3)
    plt.tight_layout()

    # ========================================
    # Save plot to file
    # ========================================
    Path(output_plot_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Significance plot saved to {output_plot_path}")
    logger.info(f"Optimal BDT cut: {optimal_bdt_cut:.3f}, Max significance: {max_significance:.2f}")

    return output_plot_path


def plot_feature_importance(model: XGBClassifier, output_plot_path: str, feature_names: List[str] = None, importance_type: str = "gain") -> str:
    """
    Generate feature importance plot showing relative contribution of each variable.

    Parameters
    ----------
    model : XGBClassifier
        Trained XGBoost model
    output_plot_path : str
        Path to save the importance plot
    feature_names : List[str], optional
        Names of features for labeling (uses model's feature names if None)
    importance_type : str, default="gain"
        Type of importance metric ("gain", "weight", "cover")

    Returns
    -------
    str
        Path to the saved plot
    """

    # ========================================
    # Set feature names if provided
    # ========================================
    if feature_names:
        model.get_booster().feature_names = feature_names

    # ========================================
    # Generate feature importance plot
    # ========================================
    fig, ax = plt.subplots(figsize=(10, 10))

    plot_importance(model, ax=ax, xlabel=f"F-score ({importance_type})", importance_type=importance_type, grid=False, height=0.8, values_format="{v:.2f}")

    # ========================================
    # Configure plot appearance
    # ========================================
    plt.title(f"Feature Importance ({importance_type.capitalize()})", fontsize=14)
    plt.tight_layout()

    # ========================================
    # Save plot to file
    # ========================================
    Path(output_plot_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_plot_path, bbox_inches="tight", dpi=300)
    plt.close(fig)

    logger.info(f"Feature importance plot saved to {output_plot_path}")
    return output_plot_path


def plot_training_evolution(model: XGBClassifier, output_plot_path: str, metrics_to_plot: List[str] = None, figure_size: Tuple = (10, 8)) -> str:
    """
    Plot evolution of training and validation metrics during model training.

    This visualization helps assess convergence behavior, early stopping effectiveness,
    and potential overfitting during the training process.

    Parameters
    ----------
    model : XGBClassifier
        Trained XGBoost model with evaluation results
    output_plot_path : str
        Path to save the evolution plot
    metrics_to_plot : List[str], optional
        Specific metrics to plot (if None, plots all available metrics)
    figure_size : Tuple, default=(10, 8)
        Figure dimensions (width, height)

    Returns
    -------
    str
        Path to the saved plot
    """

    # ========================================
    # Extract evaluation results from model
    # ========================================
    evaluation_results = model.evals_result()

    if not evaluation_results:
        raise ValueError("Model evaluation results are empty. Cannot plot training evolution.")

    # ========================================
    # Determine metrics to plot
    # ========================================
    if metrics_to_plot is None:
        # Use all metrics from first dataset
        first_dataset_results = list(evaluation_results.values())[0]
        metrics_to_plot = list(first_dataset_results.keys())

    # ========================================
    # Create subplots for each metric
    # ========================================
    fig, axes = plt.subplots(len(metrics_to_plot), 1, figsize=figure_size, sharex=True)
    if len(metrics_to_plot) == 1:
        axes = [axes]  # Ensure axes is always iterable

    # ========================================
    # Plot evolution for each metric
    # ========================================
    for metric_idx, metric_name in enumerate(metrics_to_plot):
        current_axis = axes[metric_idx]

        # Plot training and validation curves for this metric
        for dataset_name, dataset_results in evaluation_results.items():
            if metric_name in dataset_results:
                iterations = range(len(dataset_results[metric_name]))
                current_axis.plot(iterations, dataset_results[metric_name], label=f"{dataset_name} {metric_name}", alpha=0.8, linewidth=2)

        # ========================================
        # Configure subplot appearance
        # ========================================
        current_axis.set_title(f"{metric_name.upper()} Evolution", fontsize=12)
        current_axis.set_ylabel(metric_name, fontsize=10)
        current_axis.grid(alpha=0.3)
        current_axis.legend(loc='best', fontsize=9)

    # ========================================
    # Configure overall plot appearance
    # ========================================
    axes[-1].set_xlabel("Training Iterations", fontsize=12)
    plt.suptitle("Training and Validation Metrics Evolution", fontsize=14)
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)  # Make room for main title

    # ========================================
    # Save plot to file
    # ========================================
    Path(output_plot_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_plot_path, bbox_inches="tight", dpi=300)
    plt.close(fig)

    logger.info(f"Training evolution plot saved to {output_plot_path}")
    return output_plot_path


def plot_mass_distribution_with_bdt_cuts(
    mass_variable: str,
    dataframe: pd.DataFrame,
    bdt_cut_threshold: float,
    weight_column: str,
    output_plot_path: str,
    particle_name: str = "",
    mass_unit: str = "MeV",
    figure_size: Tuple = (18, 5),
    num_bins: int = 30,
):
    """
    Plot particle mass distributions before and after applying BDT cuts.

    This analysis shows the effect of BDT selection on the mass distribution,
    helping assess signal enhancement and background rejection efficiency.

    Parameters
    ----------
    mass_variable : str
        Name of mass variable column in dataframe
    dataframe : pd.DataFrame
        DataFrame containing mass data and BDT scores
    bdt_cut_threshold : float
        BDT score threshold for signal/background separation
    weight_column : str
        Name of event weight column
    output_plot_path : str
        Path to save the mass distribution plot
    particle_name : str, default=""
        Particle name for plot labels (uses mass_variable if empty)
    mass_unit : str, default="MeV"
        Unit for mass axis labeling
    figure_size : Tuple, default=(18, 5)
        Figure dimensions (width, height)
    num_bins : int, default=30
        Number of histogram bins

    Returns
    -------
    str
        Path to the saved plot
    """

    # ========================================
    # Set particle name for labeling
    # ========================================
    display_particle_name = particle_name if particle_name else mass_variable

    # ========================================
    # Extract mass distributions by BDT cut
    # ========================================
    # Events passing BDT cut (signal-like)
    signal_like_mask = dataframe["_XGBDT"] > bdt_cut_threshold
    mass_signal_like = dataframe.loc[signal_like_mask, mass_variable]
    weights_signal_like = dataframe.loc[signal_like_mask, weight_column]

    # Events failing BDT cut (background-like)
    background_like_mask = dataframe["_XGBDT"] <= bdt_cut_threshold
    mass_background_like = dataframe.loc[background_like_mask, mass_variable]
    weights_background_like = dataframe.loc[background_like_mask, weight_column]

    # All events (no cut)
    mass_all_events = dataframe[mass_variable]
    weights_all_events = dataframe[weight_column]

    # ========================================
    # Determine mass range for consistent plotting
    # ========================================
    mass_range = (mass_all_events.min(), mass_all_events.max())

    # ========================================
    # Configure histogram styling
    # ========================================
    histogram_options = {
        "alpha": 0.9,
        "density": False,
        "bins": num_bins,
        "histtype": "step",
        "linewidth": 2,
        "range": mass_range,
    }

    # ========================================
    # Create three-panel mass distribution plot
    # ========================================
    fig = plt.figure(figsize=figure_size)

    # Panel 1: Signal-like events (BDT > threshold)
    subplot_signal = plt.subplot(1, 3, 1)
    subplot_signal.set_xlabel(f"{display_particle_name} Mass ({mass_unit})")
    plt.hist(mass_signal_like, color="blue", bins=num_bins, edgecolor="black", alpha=0.7)
    subplot_signal.set_title(f"BDT > {bdt_cut_threshold}")

    # Panel 2: Background-like events (BDT ≤ threshold)
    subplot_background = plt.subplot(1, 3, 2, sharex=subplot_signal)
    subplot_background.set_xlabel(f"{display_particle_name} Mass ({mass_unit})")
    plt.hist(mass_background_like, color="red", bins=num_bins, edgecolor="black", alpha=0.7)
    subplot_background.set_title(f"BDT ≤ {bdt_cut_threshold}")

    # Panel 3: Comparison of all categories
    subplot_comparison = plt.subplot(1, 3, 3, sharex=subplot_signal)
    subplot_comparison.set_xlabel(f"{display_particle_name} Mass ({mass_unit})")

    # Plot all three distributions on comparison panel
    subplot_comparison.hist(mass_all_events, color="green", label="No BDT Cut", weights=weights_all_events, **histogram_options)
    subplot_comparison.hist(mass_background_like, color="red", label=f"BDT ≤ {bdt_cut_threshold}", weights=weights_background_like, **histogram_options)
    subplot_comparison.hist(mass_signal_like, color="blue", label=f"BDT > {bdt_cut_threshold}", weights=weights_signal_like, **histogram_options)

    subplot_comparison.legend(prop={"size": 10}, loc="best")
    subplot_comparison.set_title("BDT Cut Comparison")

    # ========================================
    # Configure overall plot appearance
    # ========================================
    plt.tight_layout()

    # ========================================
    # Save plot to file
    # ========================================
    Path(output_plot_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_plot_path, bbox_inches="tight", dpi=300)
    plt.close(fig)

    logger.info(f"Mass distribution plot saved to {output_plot_path}")
    return output_plot_path


# ========================================
# Default hyperparameters
# ========================================

DEFAULT_HYPERPARAMETERS = {
    # ========================================
    # Learning parameters
    # ========================================
    'learning_rate': 0.005,  # Step size shrinkage
    'max_depth': 9,  # Maximum tree depth
    'min_child_weight': 0.08,  # Minimum child weight
    'gamma': 2,  # Minimum split loss
    # ========================================
    # Tree-specific parameters
    # ========================================
    'max_delta_step': 0,  # Maximum delta step
    # ========================================
    # Regularization parameters
    # ========================================
    'subsample': 0.85,  # Fraction of samples per tree
    'colsample_bytree': 0.8,  # Fraction of features per tree
    'colsample_bylevel': 1.0,  # Fraction of features per level
    'reg_alpha': 0,  # L1 regularization term
    'reg_lambda': 1,  # L2 regularization term
    # ========================================
    # Number of estimators (boosting rounds)
    # Use a reasonable range for optimization speed
    # ========================================
    'num_estimators': 5000,  # Number of boosting rounds
}


# ========================================
# Load hyperparameters from YAML file
# ========================================
def load_hyperparameters_from_yaml(yaml_file: str, mode: str = 'hyperparameters') -> Dict:
    """
    Load hyperparameters from YAML file generated by Optuna optimization.

    Parameters
    ----------
    yaml_file : str
        Path to YAML file containing hyperparameters

    Returns
    -------
    Dict
        Dictionary of hyperparameters
    """

    # Load hyperparameters from YAML file
    params: Dict[str, Any] = read_yaml(yaml_file, mode=mode)
    logger.info(f"Loaded hyperparameters from {yaml_file}: {params}")

    # Update default hyperparameters with parameters from YAML file
    param_updated = update_config(DEFAULT_HYPERPARAMETERS, params)

    # Compare default hyperparameters with parameters from YAML file
    logger.info("Comparing default hyperparameters with parameters from YAML file:")
    compare_dicts(DEFAULT_HYPERPARAMETERS, param_updated)

    return param_updated


# ========================================
# Distribute threads across folds
# ========================================
def distribute_threads_across_folds(total_threads: int, num_folds: int, min_threads_per_fold: int = 1) -> List[int]:
    """
    Optimally distribute available threads across k-fold training jobs.

    This function ensures efficient utilization of computational resources when
    training multiple models in parallel, while respecting minimum thread requirements.

    Parameters
    ----------
    total_threads : int
        Total number of threads available for distribution
    num_folds : int
        Number of k-fold models to train simultaneously
    min_threads_per_fold : int, default=1
        Minimum threads each model must receive

    Returns
    -------
    List[int]
        List containing thread allocation for each fold

    Examples
    --------
    >>> distribute_threads_across_folds(8, 3, 1)
    [3, 3, 2]  # Distribute 8 threads across 3 folds

    >>> distribute_threads_across_folds(4, 10, 1)
    [1, 1, 1, 1]  # Not enough threads, fall back to minimum
    """
    if num_folds <= 0:
        return [total_threads]

    # Check if we can meet minimum requirements
    min_required_threads = num_folds * min_threads_per_fold
    if total_threads < min_required_threads:
        logger.warning(f"Insufficient threads: need {min_required_threads} " f"({num_folds} folds x {min_threads_per_fold} min threads), " f"got {total_threads}. Using 1 thread per fold.")
        return [1] * num_folds

    # Distribute threads evenly with remainder handling
    base_threads_per_fold = max(total_threads // num_folds, min_threads_per_fold)
    remaining_threads = total_threads % num_folds

    # Assign base threads plus extra thread to first 'remaining_threads' folds
    thread_distribution = [base_threads_per_fold + (1 if fold_idx < remaining_threads else 0) for fold_idx in range(num_folds)]

    logger.info(f"Thread distribution across {num_folds} folds: {thread_distribution}")
    return thread_distribution


# ========================================
# Generate model paths
# ========================================
def generate_model_paths(output_dir: str = "output/models", model_filename: str = "xgb_model.json", num_folds: int = 0) -> Dict[int, str]:
    """
    Generate standardized file paths for saving trained models.

    For single model training (num_folds=0), saves model directly in output_dir.
    For k-fold training, creates separate subdirectories for each fold.

    Parameters
    ----------
    output_dir : str, default="output/models"
        Base directory for saving models
    model_filename : str, default="xgb_model.json"
        Filename for the model file
    num_folds : int, default=0
        Number of k-fold splits (0 = single model)

    Returns
    -------
    Dict[int, str]
        Dictionary mapping fold index to full model path

    Examples
    --------
    >>> generate_model_paths("models", "my_model.json", 0)
    {0: "models/my_model.json"}

    >>> generate_model_paths("models", "my_model.json", 3)
    {0: "models/0/my_model.json", 1: "models/1/my_model.json", 2: "models/2/my_model.json"}
    """
    if num_folds <= 1:
        # Single model case
        return {0: f"{output_dir}/{model_filename}"}
    else:
        # K-fold case: separate directory for each fold
        return {fold_idx: f"{output_dir}/{fold_idx}/{model_filename}" for fold_idx in range(num_folds)}


# ========================================
# Split dataframe by k-fold
# ========================================
def split_dataframe_by_kfold(dataframe: pd.DataFrame, num_folds: int, fold_split_variable: str) -> Dict[int, pd.DataFrame]:
    """
    Split dataframe into k-fold training samples using modulo operation.

    This function creates k training datasets by excluding one fold from each,
    effectively implementing k-fold cross-validation data splitting.

    Parameters
    ----------
    dataframe : pd.DataFrame
        Input dataframe to split
    num_folds : int
        Number of k-fold splits (must be > 1)
    fold_split_variable : str
        Column name used for modulo-based fold assignment

    Returns
    -------
    Dict[int, pd.DataFrame]
        Dictionary mapping fold index to training dataframe
        (each contains all data except one fold)

    Raises
    ------
    AssertionError
        If num_folds ≤ 1 or fold_split_variable not in dataframe
    """

    # ========================================
    # Validate input parameters
    # ========================================
    assert num_folds > 1, f"Number of folds must be greater than 1, got {num_folds}"
    assert fold_split_variable in dataframe.columns, f"Split variable '{fold_split_variable}' not found in dataframe"

    # ========================================
    # Prepare dataframe for splitting
    # ========================================
    df_copy = dataframe.copy()
    df_copy[fold_split_variable] = df_copy[fold_split_variable].astype("int64")

    # ========================================
    # Create k-fold splits using modulo operation
    # ========================================
    # For each fold i, exclude events where split_variable % num_folds == i
    fold_dataframes = {fold_idx: df_copy.query(f"{fold_split_variable} % {num_folds} != {fold_idx}") for fold_idx in range(num_folds)}

    # ========================================
    # Log split statistics
    # ========================================
    total_events = len(dataframe)
    for fold_idx, fold_df in fold_dataframes.items():
        excluded_events = total_events - len(fold_df)
        logger.info(f"Fold {fold_idx}: {len(fold_df)} training events ({excluded_events} excluded with {num_folds}-Fold Cross-Validation)")

    return fold_dataframes


# ========================================
# Data structures for training pipeline
# ========================================
def create_training_test_datasets(
    signal_files: str,
    background_files: str,
    signal_tree_name: str,
    background_tree_name: str,
    bdt_feature_list: List[str],
    signal_weight_expression: str = None,
    background_weight_expression: str = None,
    num_folds: int = 0,
    fold_split_variable: str = None,
    max_signal_events: int = -1,
    max_background_events: int = -1,
    additional_signal_variables: List[str] = [],
    additional_background_variables: List[str] = [],
) -> Dict:
    """
    Create comprehensive training and test datasets from ROOT files.

    This function handles the complete data preparation pipeline including:
    - Loading data from ROOT files
    - Weight standardization and validation
    - Train/test splitting
    - K-fold cross-validation setup
    - Event balancing and quality checks

    Parameters
    ----------
    signal_files : str
        Semicolon-separated paths to signal ROOT files
    background_files : str
        Semicolon-separated paths to background ROOT files
    signal_tree_name : str
        Name of TTree in signal files
    background_tree_name : str
        Name of TTree in background files
    bdt_feature_list : List[str]
        List of feature variable names for BDT training
    signal_weight_expression : str, optional
        Expression for calculating signal event weights
    background_weight_expression : str, optional
        Expression for calculating background event weights
    num_folds : int, default=0
        Number of k-fold splits (0 = single training)
    fold_split_variable : str, optional
        Variable name for k-fold splitting
    max_signal_events : int, default=-1
        Maximum signal events to use (-1 = all)
    max_background_events : int, default=-1
        Maximum background events to use (-1 = all)
    additional_signal_variables : List[str], default=[]
        Extra variables to load from signal files
    additional_background_variables : List[str], default=[]
        Extra variables to load from background files

    Returns
    -------
    Dict
        Dictionary mapping fold indices to TrainingDataContainer objects
    """

    logger.info(f"Creating training datasets from:\n  Signal: {signal_files}\n  Background: {background_files}")

    # ========================================
    # Initialize data container
    # ========================================
    data_container = TrainingDataContainer()

    # ========================================
    # Determine variables to load from files
    # ========================================
    signal_variables_to_load = []
    signal_variables_to_load.extend(bdt_feature_list)
    if signal_weight_expression:
        signal_variables_to_load.append(signal_weight_expression)
    if fold_split_variable:
        signal_variables_to_load.append(fold_split_variable)
    signal_variables_to_load.extend(additional_signal_variables)

    background_variables_to_load = []
    background_variables_to_load.extend(bdt_feature_list)
    if background_weight_expression:
        background_variables_to_load.append(background_weight_expression)
    if fold_split_variable:
        background_variables_to_load.append(fold_split_variable)
    background_variables_to_load.extend(additional_background_variables)

    # ========================================
    # Load data from ROOT files
    # ========================================
    logger.info("Loading signal data from ROOT files...")
    signal_df_raw = load_variables_to_pd_by_uproot(signal_files, input_tree_name=signal_tree_name, variables=signal_variables_to_load, library="pd", num_workers=4)

    logger.info("Loading background data from ROOT files...")
    background_df_raw = load_variables_to_pd_by_uproot(background_files, input_tree_name=background_tree_name, variables=background_variables_to_load, library="pd", num_workers=4)

    # ========================================
    # Clean data and handle missing values
    # ========================================
    # Remove events with NaN values in BDT features
    signal_df_clean = signal_df_raw.dropna(subset=bdt_feature_list)
    background_df_clean = background_df_raw.dropna(subset=bdt_feature_list)

    if signal_df_clean.empty:
        raise ValueError("No signal events remain after cleaning")

    if background_df_clean.empty:
        raise ValueError("No background events remain after cleaning")

    logger.info(f"After NaN removal: {len(signal_df_clean)} signal, {len(background_df_clean)} background events")

    # Check if there are enough events per class
    min_events_limit = 100
    if len(signal_df_clean) < min_events_limit:
        raise ValueError(f"Insufficient signal events: {len(signal_df_clean)} < {min_events_limit}")

    if len(background_df_clean) < min_events_limit:
        raise ValueError(f"Insufficient background events: {len(background_df_clean)} < {min_events_limit}")

    # ========================================
    # Apply event number limits if specified
    # ========================================
    if max_signal_events > 0:
        signal_df_clean = signal_df_clean.head(max_signal_events)
        logger.info(f"Limited to {len(signal_df_clean)} signal events")

    if max_background_events > 0:
        background_df_clean = background_df_clean.head(max_background_events)
        logger.info(f"Limited to {len(background_df_clean)} background events")

    # ========================================
    # Balance dataset sizes (prevent extreme imbalance)
    # ========================================
    max_background_ratio = 10  # Allow at most 10:1 background:signal ratio

    if len(background_df_clean) > len(signal_df_clean) * max_background_ratio:
        target_background_size = len(signal_df_clean) * max_background_ratio
        background_df_clean = background_df_clean.head(target_background_size)
        logger.info(f"Balanced dataset: reduced background to {len(background_df_clean)} events")

    # ========================================
    # Standardize event weights
    # ========================================
    def standardize_event_weights(dataframe, weight_expression, weight_column_name):
        """Helper function to create standardized weight column."""
        df_result = dataframe.copy()

        if weight_expression is None or weight_expression.upper() in {"NONE", "1"}:
            # Use uniform weights
            df_result[weight_column_name] = np.ones(len(df_result))
        else:
            try:
                # Validate weight expression before evaluation
                df_result[weight_column_name] = df_result.eval(weight_expression)

                # Check for invalid weights
                if df_result[weight_column_name].isna().any():
                    raise ValueError(f"Weight expression '{weight_expression}' produced NaN values")

                if not np.isfinite(df_result[weight_column_name]).all():
                    raise ValueError(f"Weight expression '{weight_expression}' produced infinite values")

            except Exception as e:
                raise ValueError(f"Invalid weight expression '{weight_expression}': {e}")

        return df_result

    signal_df_weighted = standardize_event_weights(signal_df_clean, signal_weight_expression, data_container.standardized_weight_column)
    background_df_weighted = standardize_event_weights(background_df_clean, background_weight_expression, data_container.standardized_weight_column)

    # ========================================
    # Handle negative weights (XGBoost limitation)
    # ========================================
    def remove_negative_weights(dataframe, sample_type):
        """Remove events with negative weights and log statistics."""
        negative_mask = dataframe[data_container.standardized_weight_column] < 0
        num_negative = negative_mask.sum()

        if num_negative > 0:
            logger.warning(f"Found {num_negative} {sample_type} events with negative weights - removing them")
            dataframe = dataframe[~negative_mask].dropna(subset=[data_container.standardized_weight_column])

        return dataframe

    signal_df_positive = remove_negative_weights(signal_df_weighted, "signal")
    background_df_positive = remove_negative_weights(background_df_weighted, "background")

    # ========================================
    # Normalize weight integrals for balance
    # ========================================
    signal_weight_sum = signal_df_positive[data_container.standardized_weight_column].sum()
    background_weight_sum = background_df_positive[data_container.standardized_weight_column].sum()

    if signal_weight_sum == 0 or background_weight_sum == 0:
        raise ValueError(f"Zero weight sum detected: signal={signal_weight_sum}, background={background_weight_sum}")

    # Scale to the smaller weight sum for balance
    if signal_weight_sum < background_weight_sum:
        scaling_factor = signal_weight_sum / background_weight_sum
        background_df_positive = background_df_positive.copy()
        background_df_positive[data_container.standardized_weight_column] *= scaling_factor
        logger.info(f"Scaled background weights by {scaling_factor:.3f} to match signal integral")
    else:
        scaling_factor = background_weight_sum / signal_weight_sum
        signal_df_positive = signal_df_positive.copy()
        signal_df_positive[data_container.standardized_weight_column] *= scaling_factor
        logger.info(f"Scaled signal weights by {scaling_factor:.3f} to match background integral")

    # ========================================
    # Create training data containers for each fold
    # ========================================
    def create_single_training_container(signal_df, background_df, feature_list, weight_column):
        """Helper function to create a single training container from signal and background data."""

        # ========================================
        # Ensure consistent data types for numerical operations
        # ========================================
        signal_features = signal_df[feature_list + [weight_column]].astype(float)
        background_features = background_df[feature_list + [weight_column]].astype(float)

        # ========================================
        # Handle infinite values (replace with NaN, then drop)
        # ========================================
        signal_features.replace([np.inf, -np.inf], np.nan, inplace=True)
        background_features.replace([np.inf, -np.inf], np.nan, inplace=True)

        # Clean up NaN values
        signal_features.dropna(inplace=True)
        background_features.dropna(inplace=True)

        # ========================================
        # Prepare feature matrix and target vector
        # ========================================
        # Combine signal and background features
        X_combined = np.concatenate([signal_features[feature_list], background_features[feature_list]])

        # Create target labels: 1 for signal, 0 for background
        y_combined = np.concatenate([np.ones(len(signal_features)), np.zeros(len(background_features))])  # Signal events = 1  # Background events = 0

        # Combine event weights
        weights_combined = np.concatenate([signal_features[weight_column].values, background_features[weight_column].values])

        # ========================================
        # Split into training and test sets
        # ========================================
        # Use stratified split to maintain class balance
        X_train, X_test, y_train, y_test, weights_train, weights_test = train_test_split(
            X_combined, y_combined, weights_combined, test_size=0.4, random_state=42, stratify=y_combined  # 40% for testing  # Reproducible results  # Maintain class proportions
        )

        logger.info(f"Training set: {len(X_train)} events, Test set: {len(X_test)} events")

        # ========================================
        # Organize weights by category for plotting
        # ========================================
        # Training weights by category
        train_signal_weights = weights_train[y_train > 0.5]
        train_background_weights = weights_train[y_train <= 0.5]

        # Test weights by category
        test_signal_weights = weights_test[y_test > 0.5]
        test_background_weights = weights_test[y_test <= 0.5]

        # Create weight container
        event_weights = EventWeights(
            train_all=weights_train,
            test_all=weights_test,
            train_signal=train_signal_weights,
            train_background=train_background_weights,
            test_signal=test_signal_weights,
            test_background=test_background_weights,
        )

        # ========================================
        # Create and return training container
        # ========================================
        return TrainingDataContainer(
            signal_dataframe=signal_df,
            background_dataframe=background_df,
            X_train_features=X_train,
            X_test_features=X_test,
            y_train_targets=y_train,
            y_test_targets=y_test,
            weight_set=event_weights,
            bdt_feature_names=feature_list,
            signal_weight_expression=signal_weight_expression,
            background_weight_expression=background_weight_expression,
            standardized_weight_column=data_container.standardized_weight_column,
        )

    # ========================================
    # Generate training containers for each fold
    # ========================================
    training_containers = {}

    if num_folds > 1:
        # ========================================
        # K-fold cross-validation setup
        # ========================================
        # Split data into k folds
        signal_fold_splits = split_dataframe_by_kfold(signal_df_positive, num_folds, fold_split_variable)
        background_fold_splits = split_dataframe_by_kfold(background_df_positive, num_folds, fold_split_variable)

        # Create training container for each fold
        for fold_idx in range(num_folds):
            logger.info(f"Preparing fold {fold_idx + 1}/{num_folds}")

            signal_fold_data = signal_fold_splits[fold_idx]
            background_fold_data = background_fold_splits[fold_idx]

            logger.info(f"Fold {fold_idx}: {len(signal_fold_data)} signal, {len(background_fold_data)} background events")

            # Create training container for this fold
            training_containers[fold_idx] = create_single_training_container(signal_fold_data, background_fold_data, bdt_feature_list, data_container.standardized_weight_column)
    else:
        # ========================================
        # Single model training (no cross-validation)
        # ========================================
        training_containers[0] = create_single_training_container(signal_df_positive, background_df_positive, bdt_feature_list, data_container.standardized_weight_column)

    return training_containers
