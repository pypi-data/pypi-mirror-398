'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-11-07 08:29:31 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-11-07 09:49:21 +0100
FilePath     : search_optimal_hyperparameter_test.py
Description  :

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

import optuna
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score
from sklearn.datasets import load_breast_cancer  # Changed to binary classification dataset
from sklearn.model_selection import train_test_split

from search_optimal_hyperparameter import save_best_params_to_yaml, generate_optimization_plots

from rich import print as rprint


class OptunaXGBoostObjective:
    def __init__(self):
        # Load dataset once during initialization
        data = load_breast_cancer()
        self.X, self.y = data.data, data.target
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y, test_size=0.3, random_state=42)

    def __call__(self, trial):

        # ========================================
        # Define hyperparameter search space
        # ========================================

        # Learning parameters
        learning_rate = trial.suggest_float("learning_rate", 0.001, 0.2, log=True)
        max_depth = trial.suggest_int("max_depth", 3, 10)  # Reduced for faster testing
        min_child_weight = trial.suggest_float("min_child_weight", 0.01, 10.0, log=True)
        gamma = trial.suggest_float("gamma", 0.0, 5.0)  # Reduced range

        # Regularization parameters
        subsample = trial.suggest_float("subsample", 0.5, 1.0)
        colsample_bytree = trial.suggest_float("colsample_bytree", 0.5, 1.0)
        reg_alpha = trial.suggest_float("reg_alpha", 0.0, 2.0)
        reg_lambda = trial.suggest_float("reg_lambda", 0.0, 2.0)

        # Tree-specific parameters
        max_delta_step = trial.suggest_float("max_delta_step", 0.0, 5.0)

        # Number of estimators (boosting rounds)
        # Reduced for faster testing
        n_estimators = trial.suggest_int("n_estimators", 100, 1000, step=100)

        # ========================================
        # Create XGBoost model with trial parameters
        # ========================================
        model = XGBClassifier(
            objective='binary:logistic',
            booster='gbtree',
            tree_method='hist',
            learning_rate=learning_rate,
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_child_weight=min_child_weight,
            gamma=gamma,
            max_delta_step=max_delta_step,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            colsample_bylevel=1.0,
            reg_alpha=reg_alpha,
            reg_lambda=reg_lambda,
            scale_pos_weight=1,
            importance_type='gain',
            n_jobs=4,
            verbosity=0,  # Suppress XGBoost output
            random_state=42,
            eval_metric=['auc', 'logloss'],
            early_stopping_rounds=int(n_estimators * 0.2),  # Reduced from 0.3
        )

        try:
            # Train and evaluate model
            eval_set = [(self.X_train, self.y_train), (self.X_test, self.y_test)]
            model.fit(
                self.X_train,
                self.y_train,
                eval_set=eval_set,
                verbose=False,  # Suppress fit output
            )

            # Get predictions for the positive class
            y_pred_proba = model.predict_proba(self.X_test)[:, 1]
            auc_score = roc_auc_score(self.y_test, y_pred_proba)

            # Report for pruning
            trial.report(auc_score, step=model.best_iteration if hasattr(model, 'best_iteration') else n_estimators)

            # Check if trial should be pruned
            if trial.should_prune():
                raise optuna.TrialPruned()

            rprint(f"Trial {trial.number}: AUC = {auc_score:.4f}")

            return auc_score

        except optuna.TrialPruned:
            raise
        except Exception as e:
            rprint(f"[red]Trial {trial.number} failed with error: {e}[/red]")
            return 0.0  # Return worst score on failure


def main():
    rprint("[bold green]Starting hyperparameter optimization test...[/bold green]")

    # Create study with pruner
    study = optuna.create_study(
        direction="maximize",
        pruner=optuna.pruners.MedianPruner(
            n_startup_trials=5,
            n_warmup_steps=5,
            interval_steps=1,
        ),
    )

    objective = OptunaXGBoostObjective()

    rprint(f"[bold]Running {50} trials...[/bold]")  # Reduced for testing
    study.optimize(objective, n_trials=50, show_progress_bar=True)

    rprint("\n[bold cyan]Optimization completed![/bold cyan]")
    rprint(f"[green]Best hyperparameters:[/green] {study.best_params}")
    rprint(f"[green]Best AUC score:[/green] {study.best_value:.4f}")
    rprint(f"[green]Best trial number:[/green] {study.best_trial.number}")

    # Save results
    output_yaml_file = "output/best_params.yaml"
    save_best_params_to_yaml(study, output_yaml_file)
    rprint(f"[blue]Hyperparameters saved to:[/blue] {output_yaml_file}")

    # Generate plots
    output_plots_dir = "output/optimization_plots"
    generate_optimization_plots(study, output_plots_dir)
    rprint(f"[blue]Plots saved to:[/blue] {output_plots_dir}")


if __name__ == "__main__":
    main()
