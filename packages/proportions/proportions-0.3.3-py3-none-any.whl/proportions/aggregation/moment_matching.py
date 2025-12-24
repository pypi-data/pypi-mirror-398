"""Moment matching utilities for Beta distributions.

This module provides functions to fit Beta distributions to match specified
moments (mean and variance), which is essential for approximating posterior
distributions in the aggregation step.
"""

import numpy as np


def beta_mean(alpha: float, beta: float) -> float:
    """Compute mean of Beta(α, β) distribution.

    Args:
        alpha: First shape parameter (must be > 0).
        beta: Second shape parameter (must be > 0).

    Returns:
        Mean of the Beta distribution.

    Raises:
        ValueError: If parameters are not positive.

    Example:
        >>> beta_mean(2.0, 3.0)
        0.4
    """
    if alpha <= 0 or beta <= 0:
        raise ValueError(f"Parameters must be positive: α={alpha}, β={beta}")
    return alpha / (alpha + beta)


def beta_variance(alpha: float, beta: float) -> float:
    """Compute variance of Beta(α, β) distribution.

    Args:
        alpha: First shape parameter (must be > 0).
        beta: Second shape parameter (must be > 0).

    Returns:
        Variance of the Beta distribution.

    Raises:
        ValueError: If parameters are not positive.

    Example:
        >>> beta_variance(2.0, 3.0)
        0.03333333333333333
    """
    if alpha <= 0 or beta <= 0:
        raise ValueError(f"Parameters must be positive: α={alpha}, β={beta}")

    ab_sum = alpha + beta
    return (alpha * beta) / (ab_sum**2 * (ab_sum + 1))


def fit_beta_from_moments(mu: float, variance: float) -> tuple[float, float]:
    """Fit Beta(α, β) parameters to match given mean and variance.

    Uses the method of moments to find Beta distribution parameters that
    exactly match the specified mean and variance.

    Args:
        mu: Desired mean (must be in (0, 1)).
        variance: Desired variance (must be > 0 and < mu*(1-mu)).

    Returns:
        Tuple of (alpha, beta) parameters for Beta distribution.

    Raises:
        ValueError: If mu or variance are out of valid range, or if the
            variance is too large for the given mean.

    Notes:
        The Beta distribution has:
            E[X] = α / (α + β) = mu
            Var[X] = αβ / [(α+β)²(α+β+1)]

        Solving for α and β:
            common = mu(1-mu)/variance - 1
            α = mu × common
            β = (1-mu) × common

        The common term must be positive, which requires:
            variance < mu(1-mu)

    Example:
        >>> alpha, beta = fit_beta_from_moments(0.7, 0.01)
        >>> print(f"Beta({alpha:.2f}, {beta:.2f})")
        Beta(14.70, 6.30)
    """
    # Validate inputs
    if not (0 < mu < 1):
        raise ValueError(f"Mean must be in (0, 1), got {mu}")

    if variance <= 0:
        raise ValueError(f"Variance must be positive, got {variance}")

    max_variance = mu * (1 - mu)
    if variance >= max_variance:
        raise ValueError(
            f"Variance {variance:.6f} is too large for mean {mu:.6f}. "
            f"Maximum allowed variance is {max_variance:.6f}"
        )

    # Compute Beta parameters using method of moments
    common = mu * (1 - mu) / variance - 1

    if common <= 0:
        raise ValueError(
            f"Cannot fit Beta distribution: computed common={common:.6f}. "
            f"This indicates variance {variance:.6f} is too large for mean {mu:.6f}."
        )

    alpha = mu * common
    beta = (1 - mu) * common

    # Sanity check
    if alpha <= 0 or beta <= 0:
        raise ValueError(
            f"Computed invalid Beta parameters: α={alpha:.6f}, β={beta:.6f}"
        )

    return float(alpha), float(beta)


def validate_beta_fit(
    alpha: float, beta: float, target_mu: float, target_var: float, tol: float = 1e-6
) -> None:
    """Validate that Beta(α, β) matches target moments within tolerance.

    Args:
        alpha: First Beta parameter.
        beta: Second Beta parameter.
        target_mu: Target mean.
        target_var: Target variance.
        tol: Tolerance for numerical comparison (default: 1e-6).

    Raises:
        AssertionError: If moments don't match within tolerance.

    Example:
        >>> alpha, beta = fit_beta_from_moments(0.7, 0.01)
        >>> validate_beta_fit(alpha, beta, 0.7, 0.01)
    """
    actual_mu = beta_mean(alpha, beta)
    actual_var = beta_variance(alpha, beta)

    if not np.isclose(actual_mu, target_mu, atol=tol, rtol=tol):
        raise AssertionError(
            f"Mean mismatch: target={target_mu:.6f}, actual={actual_mu:.6f}"
        )

    if not np.isclose(actual_var, target_var, atol=tol, rtol=tol):
        raise AssertionError(
            f"Variance mismatch: target={target_var:.6f}, actual={actual_var:.6f}"
        )
