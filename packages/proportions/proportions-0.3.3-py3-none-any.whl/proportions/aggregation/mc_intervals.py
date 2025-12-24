"""Monte Carlo confidence intervals from weighted samples.

This module provides functions to compute credible intervals directly from
weighted Monte Carlo samples using the empirical quantile method, without
assuming any parametric distribution form.
"""

from typing import Union
import numpy as np


def weighted_quantiles(
    samples: np.ndarray,
    weights: np.ndarray,
    quantiles: Union[list[float], np.ndarray],
) -> np.ndarray:
    """Compute weighted quantiles from samples.

    Uses the empirical cumulative distribution function (ECDF) approach:
    sorts samples by value, computes cumulative sum of weights, and finds
    the sample values corresponding to the requested quantile levels.

    Args:
        samples: Array of sample values (shape: n_samples).
        weights: Array of sample weights (shape: n_samples).
                 Must be non-negative and sum to 1.
        quantiles: List or array of quantile levels in [0, 1].
                   Example: [0.025, 0.975] for 95% interval.

    Returns:
        Array of quantile values (shape: len(quantiles)).

    Raises:
        ValueError: If inputs are invalid or weights don't sum to 1.

    Example:
        >>> samples = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        >>> weights = np.array([0.1, 0.2, 0.4, 0.2, 0.1])
        >>> quantiles = weighted_quantiles(samples, weights, [0.25, 0.75])
        >>> # Returns approximate quartiles based on weighted distribution
    """
    # Input validation
    if len(samples) != len(weights):
        raise ValueError(
            f"samples and weights must have same length: "
            f"got {len(samples)} vs {len(weights)}"
        )

    if len(samples) == 0:
        raise ValueError("samples and weights cannot be empty")

    if not np.all(weights >= 0):
        raise ValueError("All weights must be non-negative")

    weight_sum = np.sum(weights)
    if not np.isclose(weight_sum, 1.0):
        raise ValueError(
            f"Weights must sum to 1.0, got {weight_sum:.6f}. "
            f"Normalize weights before calling this function."
        )

    quantiles_array = np.asarray(quantiles)
    if not np.all((quantiles_array >= 0) & (quantiles_array <= 1)):
        raise ValueError("All quantiles must be in [0, 1]")

    # Sort samples and corresponding weights
    sorted_indices = np.argsort(samples)
    sorted_samples = samples[sorted_indices]
    sorted_weights = weights[sorted_indices]

    # Compute cumulative sum of weights (ECDF)
    cumulative_weights = np.cumsum(sorted_weights)

    # Find quantile values by interpolation
    result = np.interp(quantiles_array, cumulative_weights, sorted_samples)

    return result


def mc_confidence_interval(
    samples: np.ndarray,
    weights: np.ndarray,
    confidence: float = 0.95,
) -> tuple[float, float, float]:
    """Compute Monte Carlo confidence interval from weighted samples.

    Uses empirical quantiles to compute equal-tails credible intervals
    directly from weighted samples without assuming a parametric distribution.

    Args:
        samples: Array of sample values (shape: n_samples).
        weights: Array of sample weights (shape: n_samples).
                 Will be normalized to sum to 1 if they don't already.
        confidence: Credible interval level between 0 and 1 (default: 0.95).

    Returns:
        Tuple of (mean, ci_lower, ci_upper):
            - mean: Weighted mean of samples
            - ci_lower: Lower bound of credible interval
            - ci_upper: Upper bound of credible interval

    Raises:
        ValueError: If inputs are invalid.

    Example:
        >>> # From importance sampling
        >>> samples = result.posterior.samples
        >>> weights = result.importance_weights
        >>> mean, ci_lower, ci_upper = mc_confidence_interval(samples, weights)
        >>> print(f"Mean: {mean:.4f}, 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    """
    # Input validation
    if len(samples) != len(weights):
        raise ValueError(
            f"samples and weights must have same length: "
            f"got {len(samples)} vs {len(weights)}"
        )

    if len(samples) == 0:
        raise ValueError("samples and weights cannot be empty")

    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0, 1), got {confidence}")

    if not np.all(weights >= 0):
        raise ValueError("All weights must be non-negative")

    # Normalize weights to sum to 1
    weights_normalized = weights / np.sum(weights)

    # Compute weighted mean
    mean = float(np.sum(weights_normalized * samples))

    # Compute quantiles for equal-tails interval
    alpha = 1.0 - confidence
    quantile_levels = [alpha / 2, 1.0 - alpha / 2]
    quantiles = weighted_quantiles(samples, weights_normalized, quantile_levels)

    ci_lower = float(quantiles[0])
    ci_upper = float(quantiles[1])

    return mean, ci_lower, ci_upper
