"""Importance sampling diagnostics for Hierarchical Bayes.

This module provides diagnostic functions and visualizations for assessing
the quality of importance sampling approximations in Hierarchical Bayes.
"""

from dataclasses import dataclass

import numpy as np

from proportions.core.models import BinomialData, HierarchicalBayesResult
from proportions.distributions.beta import log_beta


@dataclass
class ImportanceSamples:
    """Samples and weights from importance sampling for diagnostics.

    These samples represent an empirical approximation of the posterior
    p(m, k | data), where the normalized weights w̃ᵢ ≈ p(mᵢ, kᵢ | data).

    Attributes:
        m_samples: Samples of m parameter (shape: n_samples).
        k_samples: Samples of k parameter (shape: n_samples).
        alpha_samples: Samples of α = m·k (shape: n_samples).
        beta_samples: Samples of β = (1-m)·k (shape: n_samples).
        weights: Normalized importance weights (sum to 1).
        log_weights: Unnormalized log weights.
        n_samples: Number of samples.
        effective_sample_size: ESS = 1 / Σw̃ᵢ².
        m_prior_alpha: Prior alpha for m.
        m_prior_beta: Prior beta for m.
        k_prior_min: Prior lower bound for k.
        k_prior_max: Prior upper bound for k.
    """
    m_samples: np.ndarray
    k_samples: np.ndarray
    alpha_samples: np.ndarray
    beta_samples: np.ndarray
    weights: np.ndarray
    log_weights: np.ndarray
    n_samples: int
    effective_sample_size: float

    # Prior parameters (for reference)
    m_prior_alpha: float
    m_prior_beta: float
    k_prior_min: float
    k_prior_max: float


def extract_importance_samples(
    data: BinomialData,
    n_samples: int = 2000,
    m_prior_alpha: float = 1.0,
    m_prior_beta: float = 1.0,
    k_prior_min: float = 0.1,
    k_prior_max: float = 100.0,
    random_seed: int | None = None,
) -> ImportanceSamples:
    """Extract importance samples from Hierarchical Bayes for diagnostics.

    This function runs the importance sampling procedure and returns the
    samples and weights for diagnostic analysis and visualization.

    The normalized weights approximate the posterior:
        w̃ᵢ ≈ p(mᵢ, kᵢ | data)

    Args:
        data: Binomial data (success and trial counts per group).
        n_samples: Number of samples to draw from prior (default: 2000).
        m_prior_alpha: Beta prior alpha for m (default: 1.0 for uniform).
        m_prior_beta: Beta prior beta for m (default: 1.0 for uniform).
        k_prior_min: Lower bound for uniform prior on k (default: 0.1).
        k_prior_max: Upper bound for uniform prior on k (default: 100.0).
        random_seed: Random seed for reproducibility.

    Returns:
        ImportanceSamples with samples, weights, and metadata for diagnostics.

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> from proportions.diagnostics.importance_sampling import extract_importance_samples
        >>>
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> samples = extract_importance_samples(data, random_seed=42)
        >>>
        >>> print(f"ESS: {samples.effective_sample_size:.1f} / {samples.n_samples}")
        >>> print(f"Posterior mean: m={np.sum(samples.weights * samples.m_samples):.3f}")
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # Step 1: Sample (m, k) from prior
    m_samples = np.random.beta(m_prior_alpha, m_prior_beta, size=n_samples)
    k_samples = np.random.uniform(k_prior_min, k_prior_max, size=n_samples)

    # Convert to (α, β) parameterization
    alpha_samples = m_samples * k_samples
    beta_samples = (1.0 - m_samples) * k_samples

    # Step 2: Compute log importance weights = log p(data | α, β)
    log_weights = np.zeros(n_samples)

    for i in range(n_samples):
        alpha_i = alpha_samples[i]
        beta_i = beta_samples[i]

        # Log marginal likelihood for this (α, β)
        ll = 0.0
        for xi, ni in zip(data.x, data.n):
            ll += log_beta(alpha_i + xi, beta_i + ni - xi) - log_beta(alpha_i, beta_i)

        log_weights[i] = ll

    # Step 3: Normalize weights (using log-sum-exp trick for stability)
    log_weights_normalized = log_weights - np.max(log_weights)
    weights = np.exp(log_weights_normalized)
    weights = weights / np.sum(weights)

    # Step 4: Compute effective sample size
    ess = 1.0 / np.sum(weights**2)

    return ImportanceSamples(
        m_samples=m_samples,
        k_samples=k_samples,
        alpha_samples=alpha_samples,
        beta_samples=beta_samples,
        weights=weights,
        log_weights=log_weights,
        n_samples=n_samples,
        effective_sample_size=ess,
        m_prior_alpha=m_prior_alpha,
        m_prior_beta=m_prior_beta,
        k_prior_min=k_prior_min,
        k_prior_max=k_prior_max,
    )


def compute_weighted_statistics(
    samples: ImportanceSamples,
) -> dict:
    """Compute weighted statistics from importance samples.

    Args:
        samples: ImportanceSamples from extract_importance_samples().

    Returns:
        Dictionary with weighted posterior statistics:
            - m_mean, m_std, m_q05, m_q50, m_q95
            - k_mean, k_std, k_q05, k_q50, k_q95
            - alpha_mean, alpha_std
            - beta_mean, beta_std
            - ess, ess_ratio
            - max_weight, min_weight
    """
    # Weighted means
    m_mean = float(np.sum(samples.weights * samples.m_samples))
    k_mean = float(np.sum(samples.weights * samples.k_samples))
    alpha_mean = float(np.sum(samples.weights * samples.alpha_samples))
    beta_mean = float(np.sum(samples.weights * samples.beta_samples))

    # Weighted standard deviations
    m_std = float(np.sqrt(np.sum(samples.weights * (samples.m_samples - m_mean)**2)))
    k_std = float(np.sqrt(np.sum(samples.weights * (samples.k_samples - k_mean)**2)))
    alpha_std = float(np.sqrt(np.sum(samples.weights * (samples.alpha_samples - alpha_mean)**2)))
    beta_std = float(np.sqrt(np.sum(samples.weights * (samples.beta_samples - beta_mean)**2)))

    # Weighted quantiles (approximate via weighted percentiles)
    # Sort by value
    m_sorted_idx = np.argsort(samples.m_samples)
    k_sorted_idx = np.argsort(samples.k_samples)

    m_cumsum = np.cumsum(samples.weights[m_sorted_idx])
    k_cumsum = np.cumsum(samples.weights[k_sorted_idx])

    m_q05 = float(samples.m_samples[m_sorted_idx][np.searchsorted(m_cumsum, 0.05)])
    m_q50 = float(samples.m_samples[m_sorted_idx][np.searchsorted(m_cumsum, 0.50)])
    m_q95 = float(samples.m_samples[m_sorted_idx][np.searchsorted(m_cumsum, 0.95)])

    k_q05 = float(samples.k_samples[k_sorted_idx][np.searchsorted(k_cumsum, 0.05)])
    k_q50 = float(samples.k_samples[k_sorted_idx][np.searchsorted(k_cumsum, 0.50)])
    k_q95 = float(samples.k_samples[k_sorted_idx][np.searchsorted(k_cumsum, 0.95)])

    return {
        'm_mean': m_mean,
        'm_std': m_std,
        'm_q05': m_q05,
        'm_q50': m_q50,
        'm_q95': m_q95,
        'k_mean': k_mean,
        'k_std': k_std,
        'k_q05': k_q05,
        'k_q50': k_q50,
        'k_q95': k_q95,
        'alpha_mean': alpha_mean,
        'alpha_std': alpha_std,
        'beta_mean': beta_mean,
        'beta_std': beta_std,
        'ess': samples.effective_sample_size,
        'ess_ratio': samples.effective_sample_size / samples.n_samples,
        'max_weight': float(np.max(samples.weights)),
        'min_weight': float(np.min(samples.weights)),
    }
