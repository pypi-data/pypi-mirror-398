'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-11-07
Description  : Optuna hyperparameter optimization for XGBoost binary classification
'''

import sys
import os
import argparse
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import yaml

import pandas as pd
import numpy as np

import optuna


import xgboost as xgb
from xgboost import XGBClassifier

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

# Import matplotlib for saving as PDF
import matplotlib.pyplot as plt
from optuna.visualization.matplotlib import (
    plot_optimization_history as plot_optimization_history_mpl,
    plot_param_importances as plot_param_importances_mpl,
    plot_parallel_coordinate as plot_parallel_coordinate_mpl,
    plot_contour as plot_contour_mpl,
)

# Use non-interactive backend for batch processing
import matplotlib

matplotlib.use('Agg')


import logging
from rich.logging import RichHandler

from analysis_tool.multiprocess.poolHelper import get_optimal_n_threads
from analysis_tool.utils.utils_yaml import read_yaml

from analysis_tool.utils.utils_logging import get_logger

logger = get_logger(__name__, auto_setup_rich_logging=True)

from analysis_tool.MVA.XGBoost.xgboost_helper import create_training_test_datasets, TrainingDataContainer


class OptunaXGBoostObjective:
    """
    Objective function for Optuna hyperparameter optimization.

    This class encapsulates the objective function that Optuna will optimize.
    It trains an XGBoost model with trial-suggested hyperparameters and returns
    the validation AUC score.
    """

    def __init__(
        self,
        training_data: TrainingDataContainer,
        n_threads: int = 1,
        use_early_stopping: bool = True,
    ):
        """
        Initialize the objective function.

        Parameters
        ----------
        training_data : TrainingDataContainer
            Training data container with features and targets
        n_threads : int
            Number of threads for XGBoost training
        use_early_stopping : bool
            Whether to use early stopping during training
        """
        self.training_data = training_data
        self.n_threads = n_threads
        self.use_early_stopping = use_early_stopping

    def __call__(self, trial: optuna.Trial) -> float:
        """
        Objective function called by Optuna for each trial.

        Parameters
        ----------
        trial : optuna.Trial
            Optuna trial object for suggesting hyperparameters

        Returns
        -------
        float
            Validation AUC score (metric to maximize)
        """

        # ========================================
        # Define hyperparameter search space
        # ========================================

        trial_hyperparameters = {
            # ========================================
            # Learning parameters
            # ========================================
            'learning_rate': trial.suggest_float("learning_rate", 0.001, 0.2, log=True),
            'max_depth': trial.suggest_int("max_depth", 5, 15),
            'min_child_weight': trial.suggest_float("min_child_weight", 0.01, 10.0, log=True),
            'gamma': trial.suggest_float("gamma", 0.0, 10.0),
            # ========================================
            # Regularization parameters
            # ========================================
            'subsample': trial.suggest_float("subsample", 0.5, 1.0),
            'colsample_bytree': trial.suggest_float("colsample_bytree", 0.5, 1.0),
            'reg_alpha': trial.suggest_float("reg_alpha", 0.0, 3.0),
            'reg_lambda': trial.suggest_float("reg_lambda", 0.0, 3.0),
            # ========================================
            # Tree-specific parameters
            # ========================================
            'max_delta_step': trial.suggest_float("max_delta_step", 0.0, 5.0),
            # ========================================
            # Number of estimators (boosting rounds)
            # ========================================
            'n_estimators': trial.suggest_int("n_estimators", 1000, 10000, step=100),
        }

        # ========================================
        # Create XGBoost model with trial parameters
        # ========================================
        model = XGBClassifier(
            objective='binary:logistic',
            booster='gbtree',
            tree_method='hist',
            # ! ------- trial hyperparameters -------
            **trial_hyperparameters,
            # learning_rate=learning_rate,
            # n_estimators=n_estimators,
            # max_depth=max_depth,
            # min_child_weight=min_child_weight,
            # gamma=gamma,
            # max_delta_step=max_delta_step,
            # subsample=subsample,
            # colsample_bytree=colsample_bytree,
            # reg_alpha=reg_alpha,
            # reg_lambda=reg_lambda,
            colsample_bylevel=1.0,
            scale_pos_weight=1,
            importance_type='gain',
            n_jobs=self.n_threads,
            verbosity=0,  # Suppress XGBoost output
            random_state=42,
            eval_metric=['auc', 'logloss'],
            early_stopping_rounds=int(trial_hyperparameters['n_estimators'] * 0.3) if self.use_early_stopping else None,
        )

        # ========================================
        # Train model and evaluate
        # ========================================
        try:
            # Prepare evaluation sets
            eval_set = [(self.training_data.X_train_features, self.training_data.y_train_targets), (self.training_data.X_test_features, self.training_data.y_test_targets)]

            eval_weights = [self.training_data.weight_set.train_all, self.training_data.weight_set.test_all]

            # Train the model
            model.fit(
                self.training_data.X_train_features,
                self.training_data.y_train_targets,
                sample_weight=self.training_data.weight_set.train_all,
                eval_set=eval_set,
                sample_weight_eval_set=eval_weights,
                verbose=False,
            )

            # ========================================
            # Calculate validation AUC score
            # ========================================
            y_pred_proba = model.predict_proba(self.training_data.X_test_features)[:, 1]
            auc_score = roc_auc_score(self.training_data.y_test_targets, y_pred_proba, sample_weight=self.training_data.weight_set.test_all)

            # Report intermediate value for pruning
            trial.report(auc_score, step=model.best_iteration if hasattr(model, 'best_iteration') else trial_hyperparameters['n_estimators'])

            # Check if trial should be pruned
            if trial.should_prune():
                raise optuna.TrialPruned()

            return auc_score

        except optuna.TrialPruned:
            raise  # Re-raise pruned trials properly
        except Exception as e:
            logger.warning(f"Trial {trial.number} failed with error: {e}")
            return 0.0  # Return worst score on failure


def run_optuna_optimization(
    training_data: TrainingDataContainer,
    n_trials: int = 200,
    n_threads: int = 1,
    study_name: str = "xgboost_optimization",
    storage: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
) -> optuna.Study:
    """
    Run Optuna hyperparameter optimization.

    Parameters
    ----------
    training_data : TrainingDataContainer
        Training data container
    n_trials : int
        Number of optimization trials
    n_threads : int
        Number of threads for each trial
    study_name : str
        Name of the Optuna study
    storage : Optional[str]
        Database URL for storing study (None = in-memory)
    timeout_seconds : Optional[int]
        Timeout for optimization in seconds

    Returns
    -------
    optuna.Study
        Completed Optuna study with optimization results
    """

    logger.info("=" * 60)
    logger.info("STARTING OPTUNA HYPERPARAMETER OPTIMIZATION")
    logger.info("=" * 60)

    # ========================================
    # Create Optuna study
    # ========================================
    study = optuna.create_study(
        study_name=study_name,
        direction="maximize",  # Maximize AUC score
        storage=storage,
        load_if_exists=True,
        pruner=optuna.pruners.MedianPruner(
            n_startup_trials=5,
            n_warmup_steps=10,
            interval_steps=1,
        ),
    )

    # ========================================
    # Create objective function
    # ========================================
    objective = OptunaXGBoostObjective(
        training_data=training_data,
        n_threads=n_threads,
        use_early_stopping=True,
    )

    # ========================================
    # Run optimization
    # ========================================
    logger.info(f"Running optimization with {n_trials} trials...")
    logger.info(f"Threads per trial: {n_threads}")

    study.optimize(
        objective,
        n_trials=n_trials,
        timeout=timeout_seconds,
        gc_after_trial=True,  # Clean up memory after each trial
        show_progress_bar=True,
    )

    # ========================================
    # Log optimization results
    # ========================================
    logger.info("=" * 60)
    logger.info("OPTIMIZATION COMPLETED")
    logger.info("=" * 60)

    logger.info(f"Number of finished trials: {len(study.trials)}")
    logger.info(f"Best trial number: {study.best_trial.number}")
    logger.info(f"Best AUC score: {study.best_value:.4f}")

    logger.info("\nBest hyperparameters:")
    for key, value in study.best_params.items():
        logger.info(f"  {key}: {value}")

    return study


def save_best_params_to_yaml(
    study: optuna.Study,
    output_file: str,
    include_metadata: bool = True,
) -> None:
    """
    Save best hyperparameters to YAML file.

    Parameters
    ----------
    study : optuna.Study
        Completed Optuna study
    output_file : str
        Path to output YAML file
    include_metadata : bool
        Whether to include metadata about the optimization


    Will be saved like:
    ----------------------------------
        hyperparameters:
            learning_rate: 0.0234
            max_depth: 9
            min_child_weight: 0.156
            gamma: 1.89
            max_delta_step: 0.42
            subsample: 0.873
            colsample_bytree: 0.756
            reg_alpha: 0.234
            reg_lambda: 2.145
            n_estimators: 4500

        metadata:
            best_trial_number: 87
            best_auc_score: 0.9823
            n_trials: 200
            study_name: xgboost_optimization

        optimization_info:
            note: These are the optimal parameters found by Optuna
            usage: Use these parameters with train_xgboost_model.py
    ----------------------------------
    """

    # ========================================
    # Prepare output dictionary
    # ========================================
    output_dict = {
        "hyperparameters": study.best_params,
    }

    if include_metadata:
        output_dict["metadata"] = {
            "best_trial_number": study.best_trial.number,
            "best_auc_score": float(study.best_value),
            "n_trials": len(study.trials),
            "study_name": study.study_name,
        }

        # Add parameter ranges for reference
        output_dict["optimization_info"] = {
            "note": "These are the optimal parameters found by Optuna",
            "usage": "Use these parameters with train_xgboost_model.py",
        }

    # ========================================
    # Save to YAML file
    # ========================================
    output_file = Path(output_file).resolve().as_posix()
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        yaml.dump(output_dict, f, default_flow_style=False, sort_keys=False, indent=4)

    logger.info(f"Best hyperparameters saved to: {output_file}")


def generate_optimization_plots(
    study: optuna.Study,
    output_dir: str,
) -> None:
    """
    Generate visualization plots for the optimization study as PDF files.

    Parameters
    ----------
    study : optuna.Study
        Completed Optuna study
    output_dir : str
        Directory to save plots
    """

    logger.info("Generating optimization visualization plots...")

    output_dir = Path(output_dir).resolve().as_posix()
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ========================================
    # Optimization history
    # ========================================
    try:
        ax = plot_optimization_history_mpl(study)  # Returns Axes, not Figure
        fig = ax.figure  # Get the Figure from Axes
        fig.tight_layout()
        output_path = f"{output_dir}/optimization_history.pdf"
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Saved optimization_history to {output_path}")
    except Exception as e:
        logger.warning(f"Could not create optimization history plot: {e}")

    # ========================================
    # Parameter importance
    # ========================================
    try:
        ax = plot_param_importances_mpl(study)  # Returns Axes, not Figure
        fig = ax.figure  # Get the Figure from Axes
        fig.tight_layout()
        output_path = f"{output_dir}/param_importances.pdf"
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Saved param_importances to {output_path}")
    except Exception as e:
        logger.warning(f"Could not create parameter importance plot: {e}")

    # ========================================
    # Parallel coordinate plot
    # ========================================
    try:
        ax = plot_parallel_coordinate_mpl(study)  # Returns Axes, not Figure
        fig = ax.figure  # Get the Figure from Axes
        fig.tight_layout()
        output_path = f"{output_dir}/parallel_coordinate.pdf"
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Saved parallel_coordinate to {output_path}")
    except Exception as e:
        logger.warning(f"Could not create parallel coordinate plot: {e}")

    # ========================================
    # Contour plots for parameter interactions
    # ========================================
    if len(study.best_params) >= 2:
        param_names = list(study.best_params.keys())[: min(6, len(study.best_params))]

        contour_count = 0
        for i in range(len(param_names)):
            for j in range(i + 1, len(param_names)):
                try:
                    ax = plot_contour_mpl(study, params=[param_names[i], param_names[j]])  # Returns Axes
                    fig = ax.figure  # Get the Figure from Axes
                    fig.tight_layout()
                    output_path = f"{output_dir}/contour_{param_names[i]}_{param_names[j]}.pdf"
                    fig.savefig(output_path, dpi=300, bbox_inches='tight')
                    plt.close(fig)
                    contour_count += 1
                except Exception as e:
                    logger.warning(f"Could not create contour plot for {param_names[i]} vs {param_names[j]}: {e}")

        if contour_count > 0:
            logger.info(f"Saved {contour_count} contour plots to {output_dir}")

    logger.info(f"All optimization plots saved to: {output_dir}")


def execute_hyperparameter_optimization_pipeline(
    signal_file_paths: List[str],
    signal_tree_name: str,
    background_file_paths: List[str],
    background_tree_name: str,
    signal_weight_expression: str,
    background_weight_expression: str,
    bdt_variables_config_file: str,
    config_mode: str,
    output_yaml_file: str,
    output_plots_dir: str,
    n_trials: int = 200,
    n_threads: int = 0,
    max_signal_events: int = -1,
    max_background_events: int = -1,
    optimization_timeout_seconds: Optional[int] = None,
    study_name: str = "xgboost_optimization",
    storage: Optional[str] = None,
):
    """
    Execute the complete hyperparameter optimization pipeline.

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
        Configuration mode for reading BDT variables
    output_yaml_file : str
        Path to save optimal hyperparameters YAML file
    output_plots_dir : str
        Directory to save optimization plots
    n_trials : int
        Number of Optuna trials
    n_threads : int
        Number of threads to use
    max_signal_events : int
        Maximum signal events to use (-1 = all)
    max_background_events : int
        Maximum background events to use (-1 = all)
    optimization_timeout_seconds : Optional[int]
        Timeout for optimization in seconds
    study_name : str
        Name of the Optuna study
    storage : Optional[str]
        Database URL for persistent storage
    """

    # ========================================
    # Validate and adjust thread configuration
    # ========================================
    validated_thread_count = get_optimal_n_threads(n_threads)
    logger.info(f"Using {validated_thread_count} threads for optimization")

    # ========================================
    # Load BDT variable configuration
    # ========================================
    logger.info("Loading BDT variable configuration...")
    bdt_feature_list = read_yaml(bdt_variables_config_file, config_mode)
    logger.info(f"Loaded {len(bdt_feature_list)} BDT variables")

    # ========================================
    # Create training and test datasets
    # ========================================
    logger.info("Creating training and test datasets...")

    signal_files_combined = ';'.join(signal_file_paths)
    background_files_combined = ';'.join(background_file_paths)

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
    )

    # Use the first (and only) training container
    training_data = training_data_containers[0]

    # ========================================
    # Run Optuna optimization
    # ========================================
    study = run_optuna_optimization(
        training_data=training_data,
        n_trials=n_trials,
        n_threads=validated_thread_count,
        study_name=study_name,
        storage=storage,
        timeout_seconds=optimization_timeout_seconds,
    )

    # ========================================
    # Save best hyperparameters to YAML
    # ========================================
    save_best_params_to_yaml(
        study=study,
        output_file=output_yaml_file,
        include_metadata=True,
    )

    # ========================================
    # Generate optimization plots
    # ========================================
    if output_plots_dir.upper() == 'DEFAULT':
        output_plots_dir = Path(output_yaml_file).parent / "optimization_plots"

    generate_optimization_plots(study, str(output_plots_dir))

    logger.info("=" * 60)
    logger.info("HYPERPARAMETER OPTIMIZATION PIPELINE COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Best hyperparameters saved to: {output_yaml_file}")
    logger.info(f"Use these parameters with train_xgboost_model.py")


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Optuna Hyperparameter Optimization for XGBoost Binary Classification")

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
    parser.add_argument('--signal-weight-expression', type=str, default='1', help='Signal weight expression')
    parser.add_argument('--background-weight-expression', type=str, default='1', help='Background weight expression')

    # ========================================
    # BDT feature configuration
    # ========================================
    parser.add_argument('--bdt-variables-config-file', type=str, required=True, help='Path to the YAML file containing the BDT variables')
    parser.add_argument('--config-mode', type=str, required=True, help='Configuration mode for reading the BDT variables')

    # ========================================
    # Optimization configuration
    # ========================================
    parser.add_argument('--n-trials', type=int, default=100, help='Number of Optuna optimization trials')
    parser.add_argument('--optimization-timeout-seconds', type=int, default=48 * 60 * 60, help='Timeout for optimization in seconds, default is 48h')
    parser.add_argument('--study-name', type=str, default='xgboost_optimization', help='Name of the Optuna study')
    parser.add_argument('--storage', type=str, default=None, help='Database URL for persistent study storage (e.g., sqlite:///optuna.db)')

    # ========================================
    # Output configuration
    # ========================================
    parser.add_argument('--output-yaml-file', type=str, required=True, help='Output YAML file for optimal hyperparameters')
    parser.add_argument('--output-plots-dir', type=str, default='Default', help='Directory to save optimization plots, default: same as output YAML file')

    # ========================================
    # Performance and resource configuration
    # ========================================
    parser.add_argument('--n-threads', type=int, default=0, help='Number of threads. 0: half, -1: all, other: specific number')

    # ========================================
    # Event limit configuration
    # ========================================
    parser.add_argument('--max-signal-events', type=int, default=-1, help='Maximum signal events (-1 = all)')
    parser.add_argument('--max-background-events', type=int, default=-1, help='Maximum background events (-1 = all)')

    return parser


def main(args=None):
    """Main entry point for the script."""
    if args is None:
        args = get_parser().parse_args()

    execute_hyperparameter_optimization_pipeline(**vars(args))


if __name__ == "__main__":
    main()
