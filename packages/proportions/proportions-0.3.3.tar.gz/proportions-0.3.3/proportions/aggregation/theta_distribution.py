"""Compute theta distributions for hierarchical Bayes.

This module provides functions to compute p(θ) and p(θ | data) distributions
for a hypothetical new scenario, marginalizing over hyperparameter uncertainty.
"""

import numpy as np
from scipy.stats import beta as beta_dist

from proportions.core.models import ThetaPosterior


def compute_theta_posterior(
    alpha_samples: np.ndarray,
    beta_samples: np.ndarray,
    weights: np.ndarray,
    n_resample: int = 1000,
    theta_grid: np.ndarray | None = None,
    random_seed: int | None = None
) -> ThetaPosterior:
    """Compute p(θ | data) by marginalizing over posterior of (α, β).

    This function computes the posterior distribution of θ for a hypothetical
    new scenario by integrating over the hyperparameter posterior:

        p(θ | data) = ∫∫ Beta(θ; α, β) p(α, β | data) dα dβ

    The integral is approximated by:
    1. Resampling n_resample (α, β) pairs from the importance-weighted posterior
    2. Computing Beta(θ; α_i, β_i) for each resampled pair
    3. Averaging the densities

    Parameters
    ----------
    alpha_samples : np.ndarray
        Array of α samples from the prior distribution p(α, β)
    beta_samples : np.ndarray
        Array of β samples from the prior distribution p(α, β)
    weights : np.ndarray
        Importance weights proportional to p(data | α, β)
        Must sum to 1
    n_resample : int, default=1000
        Number of (α, β) pairs to resample from weighted posterior
    theta_grid : np.ndarray | None, default=None
        Grid of θ values where density is evaluated
        If None, uses linspace(0, 1, 1000)
    random_seed : int | None, default=None
        Random seed for reproducibility

    Returns
    -------
    ThetaPosterior
        Object containing theta_grid, density, individual_densities,
        alpha_resampled, beta_resampled, and n_resample

    Raises
    ------
    ValueError
        If alpha_samples and beta_samples have different lengths
        If weights don't sum to 1
        If n_resample <= 0

    Examples
    --------
    >>> from proportions.inference import hierarchical_bayes
    >>> result = hierarchical_bayes(data, n_samples=10000, return_samples=True)
    >>> theta_post = compute_theta_posterior(
    ...     result.alpha_samples,
    ...     result.beta_samples,
    ...     result.importance_weights,
    ...     n_resample=1000
    ... )
    >>> print(f"θ posterior mean: {(theta_post.theta_grid * theta_post.density).sum() / theta_post.density.sum():.3f}")
    """
    # Validate inputs
    if len(alpha_samples) != len(beta_samples):
        raise ValueError(
            f"alpha_samples and beta_samples must have same length: "
            f"{len(alpha_samples)} != {len(beta_samples)}"
        )

    if len(weights) != len(alpha_samples):
        raise ValueError(
            f"weights must have same length as alpha_samples: "
            f"{len(weights)} != {len(alpha_samples)}"
        )

    if not np.isclose(weights.sum(), 1.0, rtol=1e-6):
        raise ValueError(f"weights must sum to 1, got {weights.sum()}")

    if n_resample <= 0:
        raise ValueError(f"n_resample must be positive, got {n_resample}")

    # Create theta grid if not provided
    # Exclude boundaries (0, 1) to avoid inf density when α < 1 or β < 1
    if theta_grid is None:
        theta_grid = np.linspace(0, 1, 1002)[1:-1]  # Excludes 0.0 and 1.0

    # Set random seed for reproducibility
    if random_seed is not None:
        np.random.seed(random_seed)

    # Resample (α, β) pairs from importance-weighted posterior
    indices = np.random.choice(
        len(alpha_samples),
        size=n_resample,
        replace=True,
        p=weights
    )
    alpha_resampled = alpha_samples[indices]
    beta_resampled = beta_samples[indices]

    # Vectorized computation of Beta densities
    # Shape: theta_grid (1, n_grid), alpha/beta (n_resample, 1) → (n_resample, n_grid)
    individual_densities = beta_dist.pdf(
        theta_grid[np.newaxis, :],           # (1, n_grid)
        alpha_resampled[:, np.newaxis],      # (n_resample, 1)
        beta_resampled[:, np.newaxis]        # (n_resample, 1)
    )

    # Average over resamples
    density = individual_densities.mean(axis=0)

    return ThetaPosterior(
        theta_grid=theta_grid,
        density=density,
        individual_densities=individual_densities,
        alpha_resampled=alpha_resampled,
        beta_resampled=beta_resampled,
        n_resample=n_resample
    )


def compute_theta_prior(
    alpha_samples: np.ndarray,
    beta_samples: np.ndarray,
    n_resample: int = 1000,
    theta_grid: np.ndarray | None = None,
    random_seed: int | None = None
) -> ThetaPosterior:
    """Compute p(θ) by marginalizing over prior of (α, β).

    This function computes the prior distribution of θ for a hypothetical
    new scenario by integrating over the hyperparameter prior:

        p(θ) = ∫∫ Beta(θ; α, β) p(α, β) dα dβ

    This is a convenience wrapper around compute_theta_posterior() that
    uses uniform weights (no data conditioning).

    Parameters
    ----------
    alpha_samples : np.ndarray
        Array of α samples from the prior distribution p(α, β)
    beta_samples : np.ndarray
        Array of β samples from the prior distribution p(α, β)
    n_resample : int, default=1000
        Number of (α, β) pairs to resample
    theta_grid : np.ndarray | None, default=None
        Grid of θ values where density is evaluated
        If None, uses linspace(0, 1, 1000)
    random_seed : int | None, default=None
        Random seed for reproducibility

    Returns
    -------
    ThetaPosterior
        Object containing theta_grid, density, individual_densities,
        alpha_resampled, beta_resampled, and n_resample

    Examples
    --------
    >>> from proportions.inference import hierarchical_bayes
    >>> result = hierarchical_bayes(data, n_samples=10000, return_samples=True)
    >>> theta_prior = compute_theta_prior(
    ...     result.alpha_samples,
    ...     result.beta_samples,
    ...     n_resample=1000
    ... )
    >>> # Compare prior vs posterior
    >>> theta_post = compute_theta_posterior(...)
    """
    # Create uniform weights for prior
    n_samples = len(alpha_samples)
    uniform_weights = np.ones(n_samples) / n_samples

    return compute_theta_posterior(
        alpha_samples,
        beta_samples,
        uniform_weights,
        n_resample,
        theta_grid,
        random_seed
    )
