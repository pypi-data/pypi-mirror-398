'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-06-15 08:40:33 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-11-28 14:12:39 +0100
FilePath     : efficiency.py
Description  : Efficiency calculation with proper uncertainty handling for weighted events.

OVERVIEW:
=========
This module provides two main approaches for efficiency uncertainties:
1. Clopper-Pearson (Frequentist): Coverage guarantee, conservative, standard in HEP
2. Bayesian: Smoother intervals, better for low statistics, requires prior choice

METHOD SELECTION GUIDE:
======================
Use CLOPPER-PEARSON when:
    - You need frequentist coverage guarantees (official results, papers)
    - You want the "standard" HEP approach (ROOT TEfficiency default)
    - You prefer conservative uncertainties
    - Reviewer/collaboration requires frequentist methods

Use BAYESIAN when:
    - Low statistics (better behaved at boundaries 0 and 1)
    - Internal studies where smoothness matters
    - You understand and accept prior choice implications
    - You want posterior mean instead of ratio estimate

WEIGHTED EVENTS:
===============
Both methods handle weighted MC events via "effective entries":
    N_eff = (Σw)² / Σw²
This approximates unweighted event counts. Works well when:
    - Weights are relatively uniform
    - Sample size is reasonable
    - Not at extreme efficiencies (very close to 0 or 1)

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

import numpy as np
import ROOT
from ROOT import TEfficiency
from scipy.stats import beta
from typing import Union, Tuple
from dataclasses import dataclass


@dataclass
class EfficiencyResult:
    """Container for efficiency calculation results.

    Attributes:
        efficiency: Central value of efficiency (ε = N_pass / N_total)
        error_low: Lower uncertainty (subtract from efficiency to get lower bound)
        error_up: Upper uncertainty (add to efficiency to get upper bound)
        n_eff_passed: Effective number of passed events (for weighted samples)
        n_eff_total: Effective total number of events (for weighted samples)
        n_events_passed: Raw count of passed events (unweighted)
        n_events_total: Raw count of total events (unweighted)

    Example:
        If efficiency=0.75, error_low=0.05, error_up=0.06:
        - Interval is [0.70, 0.81]
        - Report as: ε = 0.75 +0.06/-0.05
    """

    efficiency: float
    error_low: float
    error_up: float
    n_eff_passed: float = None
    n_eff_total: float = None
    n_events_passed: int = None
    n_events_total: int = None


def effective_entries(weights: Union[list, np.ndarray]) -> float:
    """Calculate effective number of entries from event weights.

    CONCEPT:
    --------
    When events have different weights (MC reweighting, trigger prescales, etc.),
    simple counting doesn't work. Effective entries converts weighted events into
    an "equivalent" number of unweighted events.

    FORMULA:
    --------
    N_eff = (Σw)² / Σw²

    INTERPRETATION:
    ---------------
    - If all weights are equal (w_i = w): N_eff = N (exact)
    - If weights vary widely: N_eff < N (information loss)
    - Extreme example: One huge weight dominates → N_eff ≈ 1

    LIMITATIONS:
    ------------
    - Assumes weights are positive
    - Very non-uniform weights → poor approximation
    - Negative weights not supported (would need different treatment)

    Args:
        weights: Array of event weights (must be positive)

    Returns:
        Effective number of entries: (Σw)² / Σw²
    """
    if len(weights) == 0:
        return 0.0

    weights = np.asarray(weights)
    sum_w = np.sum(weights)
    sum_w2 = np.sum(weights**2)

    return sum_w**2 / sum_w2 if sum_w2 > 0 else 0.0


# ============================================================================
# CLOPPER-PEARSON METHOD (Frequentist)
# ============================================================================
def efficiency_clopper_pearson_approx(
    weights_passed: Union[list, np.ndarray],
    weights_total: Union[list, np.ndarray],
    confidence_level: float = 0.683,
) -> EfficiencyResult:
    """Calculate efficiency with Clopper-Pearson confidence intervals.

    METHOD:
    -------
    Clopper-Pearson (exact binomial method) provides confidence intervals with
    guaranteed frequentist coverage. This is the "gold standard" in HEP.

    APPROACH FOR WEIGHTED EVENTS:
    -----------------------------
    1. Calculate effective entries for passed and total events
    2. Round to integers: k_eff and n_eff
    3. Apply standard Clopper-Pearson to (k_eff, n_eff)
    4. Uses ROOT's TEfficiency (well-tested, standard in HEP)

    ADVANTAGES:
    -----------
    - Coverage guarantee: If you repeat experiment, stated CI contains true ε
    - Conservative (intervals may be wider than necessary)
    - Standard method in particle physics (reviewers expect this)
    - No prior assumptions needed

    DISADVANTAGES:
    --------------
    - Can be overly conservative (especially at boundaries)
    - Asymmetric intervals can be surprising
    - Rounding effective entries introduces approximation

    WHEN TO USE:
    ------------
    - Default choice for publication-quality results
    - When frequentist coverage is required
    - Official measurements and data/MC comparisons
    - Any time you need to justify to skeptical reviewers

    Args:
        weights_passed: Weights of events passing selection
        weights_total: Weights of all events (passed + failed)
        confidence_level: Confidence level (0.683 for 1σ, 0.95 for 2σ)

    Returns:
        EfficiencyResult with efficiency and confidence intervals

    Example:
        >>> weights_pass = np.array([1.2, 0.9, 1.1])  # 3 events passed
        >>> weights_all = np.array([1.2, 0.9, 1.1, 0.8, 1.0])  # 5 total
        >>> result = efficiency_clopper_pearson_approx(weights_pass, weights_all)
        >>> print(f"ε = {result.efficiency:.3f} +{result.error_up:.3f}/-{result.error_low:.3f}")
    """
    n_events_passed = len(weights_passed)
    n_events_total = len(weights_total)
    n_eff_passed = effective_entries(weights_passed)
    n_eff_total = effective_entries(weights_total)

    return efficiency_clopper_pearson_from_effective(n_eff_passed, n_eff_total, confidence_level, n_events_passed, n_events_total)


def efficiency_clopper_pearson_from_effective(
    n_eff_passed: float,
    n_eff_total: float,
    confidence_level: float = 0.683,
    n_events_passed: int = None,
    n_events_total: int = None,
) -> EfficiencyResult:
    """Clopper-Pearson intervals from pre-calculated effective entries.

    USE CASE:
    ---------
    When you've already computed effective entries elsewhere and want to avoid
    re-calculating them. Useful when effective entries come from histograms
    or when doing multiple calculations with the same effective counts.

    IMPLEMENTATION DETAILS:
    -----------------------
    - Converts effective entries to integers via rounding
    - Ensures k ≤ n (physical constraint)
    - Uses ROOT::TEfficiency with kFCP option (Feldman-Cousins-Pearson)
    - Central value is simple ratio: ε = n_eff_passed / n_eff_total

    Args:
        n_eff_passed: Effective number of passed events
        n_eff_total: Effective number of total events
        confidence_level: Confidence level (default: 0.683 for 1σ)
        n_events_passed: Raw number of passed events (optional, for bookkeeping)
        n_events_total: Raw number of total events (optional, for bookkeeping)

    Returns:
        EfficiencyResult with efficiency and uncertainties
    """
    if n_eff_total <= 0:
        return EfficiencyResult(0.0, 0.0, 0.0, n_eff_passed, n_eff_total, n_events_passed, n_events_total)

    # Convert to integers, ensuring k <= N
    k_int = max(0, min(int(round(n_eff_passed)), int(round(n_eff_total))))
    n_int = max(1, int(round(n_eff_total)))

    # Use ROOT's TEfficiency (battle-tested implementation)
    teff = TEfficiency()
    teff.SetStatisticOption(TEfficiency.kFCP)  # Clopper-Pearson
    teff.SetConfidenceLevel(confidence_level)

    teff.SetTotalEvents(0, n_int)
    teff.SetPassedEvents(0, k_int)

    # Central value is simple ratio (not from TEfficiency)
    efficiency = n_eff_passed / n_eff_total
    error_low = teff.GetEfficiencyErrorLow(0)
    error_up = teff.GetEfficiencyErrorUp(0)

    return EfficiencyResult(efficiency, error_low, error_up, n_eff_passed, n_eff_total, n_events_passed, n_events_total)


# ============================================================================
# BAYESIAN METHOD (Beta-Binomial Model)
# ============================================================================
def efficiency_bayesian(
    weights_passed: Union[list, np.ndarray],
    weights_failed: Union[list, np.ndarray],
    prior: str = "uniform",
    confidence_level: float = 0.683,
) -> EfficiencyResult:
    """Bayesian efficiency calculation for weighted events.

    METHOD:
    -------
    Uses Beta-Binomial conjugate prior model. Given data (k passed, n-k failed),
    posterior distribution is Beta(α', β') where:
        α' = k + α_prior
        β' = (n-k) + β_prior

    PRIOR CHOICES:
    --------------
    1. "uniform" (Bayes-Laplace): Beta(1, 1)
       - Flat prior: all efficiencies equally likely before seeing data
       - Equivalent to adding 1 pseudo-pass and 1 pseudo-fail
       - Good default for most cases

    2. "jeffrey" (Jeffreys): Beta(0.5, 0.5)
       - Reference prior (invariant under reparametrization)
       - Less informative than uniform
       - Better theoretical properties for low statistics
       - U-shaped: slightly favors extremes (0 and 1)

    ADVANTAGES:
    -----------
    - Smooth intervals, well-behaved at boundaries (0 and 1)
    - Natural interpretation: 68% credible interval = "68% probability ε is in this range"
    - Central value is posterior mean (incorporates prior information)
    - Better than Clopper-Pearson for very low statistics

    DISADVANTAGES:
    --------------
    - Prior choice affects result (especially for low statistics)
    - Not frequentist: intervals don't have coverage guarantee
    - Some reviewers/collaborations reject Bayesian methods
    - Requires understanding of Bayesian interpretation

    WHEN TO USE:
    ------------
    - Internal studies and MC-only analyses
    - Low statistics where Clopper-Pearson is too conservative
    - When you understand prior implications
    - Systematic studies where smoothness is valuable

    WHEN NOT TO USE:
    ----------------
    - Official results requiring frequentist methods
    - When reviewers insist on "standard" approach
    - When prior choice is contentious

    Args:
        weights_passed: Weights of events passing selection
        weights_failed: Weights of events failing selection
        prior: "uniform" (Beta(1,1)) or "jeffrey" (Beta(0.5,0.5))
        confidence_level: Confidence level for credible interval

    Returns:
        EfficiencyResult with posterior mean and credible interval

    Example:
        >>> weights_pass = np.array([1.2, 0.9, 1.1])
        >>> weights_fail = np.array([0.8, 1.0])
        >>> result = efficiency_bayesian(weights_pass, weights_fail, prior="uniform")
        >>> print(f"ε = {result.efficiency:.3f} +{result.error_up:.3f}/-{result.error_low:.3f}")
    """
    n_events_passed = len(weights_passed)
    n_events_total = len(weights_passed) + len(weights_failed)
    n_eff_passed = effective_entries(weights_passed)
    n_eff_failed = effective_entries(weights_failed)

    return efficiency_bayesian_from_effective(n_eff_passed, n_eff_failed, prior, confidence_level, n_events_passed, n_events_total)


def efficiency_bayesian_from_effective(
    n_eff_passed: float,
    n_eff_failed: float,
    prior: str = "uniform",
    confidence_level: float = 0.683,
    n_events_passed: int = None,
    n_events_total: int = None,
) -> EfficiencyResult:
    """Bayesian efficiency from pre-calculated effective entries.

    USE CASE:
    ---------
    Direct calculation when you have effective entries (e.g., from histograms).
    Avoids re-computing effective entries from event weights.

    TECHNICAL NOTES:
    ----------------
    - No integer rounding (unlike Clopper-Pearson)
    - Uses scipy.stats.beta for quantile calculation
    - Central value is posterior mean: α'/(α'+β')
    - Credible interval from Beta CDF inverse

    Args:
        n_eff_passed: Effective number of passed events
        n_eff_failed: Effective number of failed events
        prior: "uniform" (Beta(1,1)) or "jeffrey" (Beta(0.5,0.5))
        confidence_level: Confidence level for credible interval
        n_events_passed: Raw number of passed events (optional, for bookkeeping)
        n_events_total: Raw number of total events (optional, for bookkeeping)

    Returns:
        EfficiencyResult with posterior mean and credible interval
    """
    if n_eff_passed + n_eff_failed <= 0:
        return EfficiencyResult(0.0, 0.0, 0.0, n_eff_passed, n_eff_passed + n_eff_failed, n_events_passed, n_events_total)

    # Set prior parameters
    if prior.lower() == "uniform":
        alpha_prior, beta_prior = 1.0, 1.0  # Flat prior
    elif prior.lower() == "jeffrey":
        alpha_prior, beta_prior = 0.5, 0.5  # Jeffreys prior
    else:
        raise ValueError(f"Unknown prior: {prior}. Use 'uniform' or 'jeffrey'")

    # Posterior parameters (conjugate update)
    alpha_post = n_eff_passed + alpha_prior
    beta_post = n_eff_failed + beta_prior

    # Posterior mean (NOT mode or median)
    efficiency = alpha_post / (alpha_post + beta_post)

    # Credible interval from Beta quantiles
    tail_prob = (1 - confidence_level) / 2
    lower_bound = beta.ppf(tail_prob, alpha_post, beta_post)
    upper_bound = beta.ppf(1 - tail_prob, alpha_post, beta_post)

    return EfficiencyResult(
        efficiency,
        efficiency - lower_bound,  # Error is distance from central value
        upper_bound - efficiency,
        n_eff_passed,
        n_eff_passed + n_eff_failed,
        n_events_passed,
        n_events_total,
    )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================
def efficiency_from_mask(
    weights: Union[list, np.ndarray],
    selection_mask: Union[list, np.ndarray],
    method: str = "bayesian",
    **kwargs,
) -> EfficiencyResult:
    """Calculate efficiency from weights and boolean selection mask.

    CONVENIENCE WRAPPER:
    --------------------
    Most common use case: You have event weights and a boolean mask indicating
    which events passed a selection. This function handles the splitting for you.

    USAGE EXAMPLE:
    --------------
    >>> weights = df['event_weight'].values
    >>> passed_trigger = df['trigger_fired'].values  # Boolean array
    >>> result = efficiency_from_mask(weights, passed_trigger, method="clopper_pearson")

    METHOD RECOMMENDATION:
    ----------------------
    - Use method="clopper_pearson" for publication results (DEFAULT SHOULD BE THIS!)
    - Use method="bayesian" for internal studies and low statistics

    Note: Current default is "bayesian" but consider changing to "clopper_pearson"
          for better alignment with HEP standards.

    Args:
        weights: Event weights
        selection_mask: Boolean mask for passed events (True = passed)
        method: "bayesian" or "clopper_pearson"
        **kwargs: Additional arguments passed to efficiency function
                  (e.g., confidence_level, prior for Bayesian)

    Returns:
        EfficiencyResult

    Raises:
        ValueError: If method is not recognized
    """
    weights = np.asarray(weights)
    selection_mask = np.asarray(selection_mask, dtype=bool)

    weights_passed = weights[selection_mask]

    if method.lower() == "bayesian":
        weights_failed = weights[~selection_mask]
        return efficiency_bayesian(weights_passed, weights_failed, **kwargs)
    elif method.lower() == "clopper_pearson":
        return efficiency_clopper_pearson_approx(weights_passed, weights, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")


# ============================================================================
# TESTING AND COMPARISON
# ============================================================================
def _run_comparison_test():
    """Internal test function comparing methods.

    DEMONSTRATES:
    -------------
    1. Both methods produce similar results for reasonable statistics
    2. Effect of weighted vs unweighted events (N_eff vs N_raw)
    3. How to use the direct effective entry methods
    4. Differences between sum of weights and effective entries
    """
    rng = np.random.default_rng(42)

    # Test with varied weights to see differences
    n_events = 200
    weights = rng.uniform(0.91, 20.0, n_events)  # Varied weights
    selection = rng.random(n_events) < 0.1  # 10% efficiency

    # Compare methods
    result_bayes = efficiency_from_mask(weights, selection, method="bayesian")
    result_cp = efficiency_from_mask(weights, selection, method="clopper_pearson")

    print("=== Weighted MC Efficiency Comparison ===")
    print(f"Clopper-Pearson: {result_cp.efficiency:.4f} (+{result_cp.error_up:.4f}/-{result_cp.error_low:.4f})")
    print(f"Bayesian:       {result_bayes.efficiency:.4f} (+{result_bayes.error_up:.4f}/-{result_bayes.error_low:.4f})")
    print(f"N_eff: {result_bayes.n_eff_total:.1f} vs N_raw: {len(weights)}")

    # Test direct effective entry methods
    print("\n=== Testing Direct Effective Entry Methods ===")
    selection_mask = np.asarray(selection, dtype=bool)

    # Calculate effective entries
    weights_passed = np.asarray(weights)[selection_mask]
    weights_failed = np.asarray(weights)[~selection_mask]

    n_eff_passed = effective_entries(weights_passed)
    n_eff_total = effective_entries(weights)
    n_eff_failed = effective_entries(weights_failed)

    result_cp_direct = efficiency_clopper_pearson_from_effective(n_eff_passed, n_eff_total)
    result_bayes_direct = efficiency_bayesian_from_effective(n_eff_passed, n_eff_failed)

    print(f"CP (direct):     {result_cp_direct.efficiency:.4f} (+{result_cp_direct.error_up:.4f}/-{result_cp_direct.error_low:.4f})")
    print(f"Bayes (direct):  {result_bayes_direct.efficiency:.4f} (+{result_bayes_direct.error_up:.4f}/-{result_bayes_direct.error_low:.4f})")

    # Show the difference between sum of weights vs effective entries
    print(f"\n=== Debugging Info ===")
    print(f"Sum of passed weights: {weights_passed.sum():.2f}")
    print(f"Effective passed entries: {n_eff_passed:.2f}")
    print(f"Sum of total weights: {weights.sum():.2f}")
    print(f"Effective total entries: {n_eff_total:.2f}")


if __name__ == "__main__":
    _run_comparison_test()
