"""Single proportion Bayesian inference with truncated Beta priors.

This module implements Bayesian inference for a single binomial proportion
with support for truncated Beta priors. These functions are useful when you have
a single (success, counts) pair rather than grouped data.

The standard Beta-Binomial conjugate model is:
    θ ~ Beta(α, β)           # Prior (optionally truncated to [lower, upper])
    x ~ Binomial(n, θ)       # Likelihood
    θ | x ~ Beta(α + x, β + n - x)  # Posterior (truncated)

When lower=0.0 and upper=1.0 (default), this reduces to the standard Beta-Binomial model.
"""

import numpy as np

from proportions.distributions.truncated_beta import (
    truncated_beta_cdf,
    truncated_beta_ppf,
)


def _validate_inputs(
    success: int,
    counts: int,
    prior_alpha: float,
    prior_beta: float,
    lower: float,
    upper: float,
    confidence: float | None = None,
) -> None:
    """Validate common input parameters.

    Args:
        success: Number of successes.
        counts: Total number of trials.
        prior_alpha: Prior alpha parameter.
        prior_beta: Prior beta parameter.
        lower: Lower truncation bound.
        upper: Upper truncation bound.
        confidence: Optional confidence level.

    Raises:
        ValueError: If any parameter is invalid.
    """
    if success < 0:
        raise ValueError(f"success must be non-negative, got {success}")
    if counts < 0:
        raise ValueError(f"counts must be non-negative, got {counts}")
    if success > counts:
        raise ValueError(f"success ({success}) cannot exceed counts ({counts})")

    if prior_alpha <= 0:
        raise ValueError(f"prior_alpha must be positive, got {prior_alpha}")
    if prior_beta <= 0:
        raise ValueError(f"prior_beta must be positive, got {prior_beta}")

    if not (0.0 <= lower < upper <= 1.0):
        raise ValueError(
            f"Must have 0 <= lower < upper <= 1, got lower={lower}, upper={upper}"
        )

    if confidence is not None:
        if not (0.0 < confidence < 1.0):
            raise ValueError(f"confidence must be in (0, 1), got {confidence}")


def conf_interval_proportion(
    success: int,
    counts: int,
    confidence: float = 0.95,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
) -> np.ndarray:
    """Compute equal-tails credible interval for a binomial proportion.

    Uses Beta-Binomial conjugate updating with optional truncation.

    Args:
        success: Number of successes (must be >= 0).
        counts: Total number of trials (must be >= success).
        confidence: Credible interval level between 0 and 1 (default: 0.95).
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
        lower: Lower bound of prior truncation (default: 0.0).
        upper: Upper bound of prior truncation (default: 1.0).

    Returns:
        Array [lower_bound, upper_bound] of the credible interval.

    Example:
        >>> # 30 successes out of 100 trials with uniform prior
        >>> interval = conf_interval_proportion(30, 100, confidence=0.95)
        >>> interval[0] < 0.3 < interval[1]  # Should contain point estimate
        True

        >>> # With truncated prior [0.2, 0.8]
        >>> interval_trunc = conf_interval_proportion(30, 100, lower=0.2, upper=0.8)
        >>> 0.2 <= interval_trunc[0] < interval_trunc[1] <= 0.8
        True
    """
    _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper, confidence)

    # Posterior parameters (Beta-Binomial conjugate update)
    alpha_post = success + prior_alpha
    beta_post = counts - success + prior_beta

    # Compute equal-tails credible interval
    alpha_level = (1 - confidence) / 2.0
    lower_bound = truncated_beta_ppf(alpha_level, alpha_post, beta_post, lower, upper)
    upper_bound = truncated_beta_ppf(1 - alpha_level, alpha_post, beta_post, lower, upper)

    return np.array([lower_bound, upper_bound])


def upper_bound_proportion(
    success: int,
    counts: int,
    confidence: float = 0.95,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
) -> float:
    """Compute upper credible bound for a binomial proportion.

    The upper bound u satisfies P(θ ≤ u | data) = confidence.

    Args:
        success: Number of successes (must be >= 0).
        counts: Total number of trials (must be >= success).
        confidence: Confidence level between 0 and 1 (default: 0.95).
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
        lower: Lower bound of prior truncation (default: 0.0).
        upper: Upper bound of prior truncation (default: 1.0).

    Returns:
        Upper credible bound such that P(θ ≤ bound | data) = confidence.

    Example:
        >>> # 30 successes out of 100 trials
        >>> ub = upper_bound_proportion(30, 100, confidence=0.95)
        >>> ub > 0.3  # Should be above point estimate
        True
    """
    _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper, confidence)

    # Posterior parameters
    alpha_post = success + prior_alpha
    beta_post = counts - success + prior_beta

    return float(truncated_beta_ppf(confidence, alpha_post, beta_post, lower, upper))


def lower_bound_proportion(
    success: int,
    counts: int,
    confidence: float = 0.95,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
) -> float:
    """Compute lower credible bound for a binomial proportion.

    The lower bound l satisfies P(θ ≥ l | data) = confidence.

    Args:
        success: Number of successes (must be >= 0).
        counts: Total number of trials (must be >= success).
        confidence: Confidence level between 0 and 1 (default: 0.95).
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
        lower: Lower bound of prior truncation (default: 0.0).
        upper: Upper bound of prior truncation (default: 1.0).

    Returns:
        Lower credible bound such that P(θ ≥ bound | data) = confidence.

    Example:
        >>> # 30 successes out of 100 trials
        >>> lb = lower_bound_proportion(30, 100, confidence=0.95)
        >>> lb < 0.3  # Should be below point estimate
        True
    """
    _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper, confidence)

    # Posterior parameters
    alpha_post = success + prior_alpha
    beta_post = counts - success + prior_beta

    # Lower bound at confidence level means we want the (1-confidence) quantile
    return float(truncated_beta_ppf(1 - confidence, alpha_post, beta_post, lower, upper))


def prob_larger_than_threshold(
    success: int,
    counts: int,
    threshold: float,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
) -> float:
    """Compute probability that proportion is larger than a threshold.

    Computes P(θ > threshold | data).

    Args:
        success: Number of successes (must be >= 0).
        counts: Total number of trials (must be >= success).
        threshold: Threshold value between 0 and 1.
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
        lower: Lower bound of prior truncation (default: 0.0).
        upper: Upper bound of prior truncation (default: 1.0).

    Returns:
        Probability that θ > threshold.

    Raises:
        ValueError: If threshold is not in [0, 1].

    Example:
        >>> # 30 successes out of 100 trials
        >>> # What's the probability that true rate > 0.25?
        >>> prob = prob_larger_than_threshold(30, 100, threshold=0.25)
        >>> prob > 0.5  # Should be fairly high
        True
    """
    _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper)

    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"threshold must be in [0, 1], got {threshold}")

    # Posterior parameters
    alpha_post = success + prior_alpha
    beta_post = counts - success + prior_beta

    # P(θ > threshold) = 1 - P(θ ≤ threshold) = 1 - CDF(threshold)
    cdf_val = truncated_beta_cdf(threshold, alpha_post, beta_post, lower, upper)
    return float(1.0 - cdf_val)


def prob_smaller_than_threshold(
    success: int,
    counts: int,
    threshold: float,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
) -> float:
    """Compute probability that proportion is smaller than a threshold.

    Computes P(θ < threshold | data).

    Args:
        success: Number of successes (must be >= 0).
        counts: Total number of trials (must be >= success).
        threshold: Threshold value between 0 and 1.
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
        lower: Lower bound of prior truncation (default: 0.0).
        upper: Upper bound of prior truncation (default: 1.0).

    Returns:
        Probability that θ < threshold.

    Raises:
        ValueError: If threshold is not in [0, 1].

    Example:
        >>> # 30 successes out of 100 trials
        >>> # What's the probability that true rate < 0.35?
        >>> prob = prob_smaller_than_threshold(30, 100, threshold=0.35)
        >>> prob > 0.5  # Should be fairly high
        True
    """
    _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper)

    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"threshold must be in [0, 1], got {threshold}")

    # Posterior parameters
    alpha_post = success + prior_alpha
    beta_post = counts - success + prior_beta

    # P(θ < threshold) = CDF(threshold)
    return float(truncated_beta_cdf(threshold, alpha_post, beta_post, lower, upper))


def prob_of_interval(
    success: int,
    counts: int,
    lb: float,
    ub: float,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
) -> float:
    """Compute probability that proportion falls within an interval.

    Computes P(lb ≤ θ ≤ ub | data).

    Args:
        success: Number of successes (must be >= 0).
        counts: Total number of trials (must be >= success).
        lb: Lower bound of query interval (must be in [0, 1]).
        ub: Upper bound of query interval (must be in [0, 1] and >= lb).
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
        lower: Lower bound of prior truncation (default: 0.0).
        upper: Upper bound of prior truncation (default: 1.0).

    Returns:
        Probability that θ ∈ [lb, ub].

    Raises:
        ValueError: If lb or ub are invalid or lb > ub.

    Example:
        >>> # 30 successes out of 100 trials
        >>> # What's the probability that true rate is in [0.25, 0.35]?
        >>> prob = prob_of_interval(30, 100, lb=0.25, ub=0.35)
        >>> 0.0 < prob < 1.0
        True
    """
    _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper)

    if not (0.0 <= lb <= 1.0):
        raise ValueError(f"lb must be in [0, 1], got {lb}")
    if not (0.0 <= ub <= 1.0):
        raise ValueError(f"ub must be in [0, 1], got {ub}")
    if lb > ub:
        raise ValueError(f"lb ({lb}) must be <= ub ({ub})")

    # Posterior parameters
    alpha_post = success + prior_alpha
    beta_post = counts - success + prior_beta

    # P(lb ≤ θ ≤ ub) = CDF(ub) - CDF(lb)
    cdf_lb = truncated_beta_cdf(lb, alpha_post, beta_post, lower, upper)
    cdf_ub = truncated_beta_cdf(ub, alpha_post, beta_post, lower, upper)

    return float(cdf_ub - cdf_lb)
