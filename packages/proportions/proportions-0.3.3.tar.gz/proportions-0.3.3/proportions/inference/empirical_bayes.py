"""Empirical Bayes inference for Beta-Binomial hierarchical models.

This module implements Empirical Bayes estimation, which finds hyperparameters
(α, β) by maximizing the marginal likelihood, then treats them as fixed for
posterior inference.
"""

import math

import numpy as np

from proportions.aggregation.average_posterior import compute_posterior_t_empirical_bayes
from proportions.core.models import BinomialData, EmpiricalBayesResult
from proportions.distributions.beta import log_beta


def log_marginal_likelihood(
    m: float, k: float, data: BinomialData
) -> float:
    """Compute log marginal likelihood for Beta-Binomial model.

    Model:
        θᵢ ~ Beta(α, β), where α = m·k, β = (1-m)·k
        xᵢ ~ Binomial(nᵢ, θᵢ)

    The marginal likelihood integrates out θᵢ:
        p(xᵢ | m, k, nᵢ) = B(α + xᵢ, β + nᵢ - xᵢ) / B(α, β)

    Args:
        m: Mean parameter (0 < m < 1), where E[θ] = m.
        k: Concentration parameter (k > 0), controls variance.
        data: Binomial data (success and trial counts).

    Returns:
        Log marginal likelihood summed over all groups.

    Example:
        >>> import numpy as np
        >>> data = BinomialData(x=np.array([8, 7]), n=np.array([10, 10]))
        >>> ll = log_marginal_likelihood(0.8, 10.0, data)
        >>> print(f"Log likelihood: {ll:.2f}")
    """
    alpha = m * k
    beta = (1.0 - m) * k

    if alpha <= 0.0 or beta <= 0.0:
        return -1e300  # Invalid parameters

    ll = 0.0
    for xi, ni in zip(data.x, data.n):
        # log p(xᵢ | m, k, nᵢ) = log B(α + xᵢ, β + nᵢ - xᵢ) - log B(α, β)
        ll += log_beta(alpha + xi, beta + ni - xi) - log_beta(alpha, beta)

    return ll


def empirical_bayes(
    data: BinomialData,
    m_range: tuple[float, float] = (0.7, 0.99),
    k_range: tuple[float, float] = (5.0, 1000.0),
    m_grid: int = 50,
    k_grid: int = 50,
    ci_level: float = 0.95,
    group_indices: list[int] | np.ndarray | None = None,
) -> EmpiricalBayesResult:
    """Perform Empirical Bayes inference for Beta-Binomial hierarchical model.

    WARNING: NOT RECOMMENDED FOR GENERAL USE
    =========================================
    Empirical Bayes systematically under-covers (produces intervals that are too narrow)
    because it treats hyperparameters as fixed at their MLE point estimates, ignoring
    hyperparameter uncertainty. Coverage can be as low as 17% when nominal coverage is 95%.

    For proper uncertainty quantification, use hierarchical_bayes() instead.

    This method is provided for completeness and comparison purposes only.

    ---

    Empirical Bayes estimates hyperparameters (α̂, β̂) by maximizing the marginal
    likelihood, then uses these fixed estimates for posterior inference on
    T = average(θ₁, ..., θₖ).

    The algorithm:
    1. Grid search over (m, k) to maximize marginal likelihood
    2. Convert to (α̂, β̂) via α̂ = m̂·k̂, β̂ = (1-m̂)·k̂
    3. Compute group posteriors: θᵢ | data ~ Beta(α̂ + xᵢ, β̂ + nᵢ - xᵢ)
    4. Aggregate to get posterior for T via moment matching

    Args:
        data: Binomial data (success and trial counts per group).
        m_range: Search range for mean parameter (min, max).
                 Default (0.7, 0.99) works well for high success rates.
        k_range: Search range for concentration parameter (min, max).
                 Default (5.0, 1000.0) covers low to high concentration.
        m_grid: Number of grid points for m (default: 50).
        k_grid: Number of grid points for k (default: 50).
        ci_level: Credible interval level (default: 0.95).
        group_indices: Optional list of group indices to include in analysis.
                       If None, includes all groups.

    Returns:
        EmpiricalBayesResult with:
            - m_hat, k_hat: Estimated hyperparameters in (m, k) parameterization
            - alpha_hat, beta_hat: Estimated hyperparameters in (α, β) parameterization
            - log_marginal_likelihood: Log evidence at maximum
            - posterior: Posterior distribution for T = average(θ)
            - Metadata: n_groups, n_total_trials, n_total_successes

    Notes:
        - Grid search is simple but effective for 2D optimization
        - k_grid uses log-spacing since k spans orders of magnitude
        - Treats hyperparameters as fixed (no hyperparameter uncertainty)
        - For hyperparameter uncertainty, use hierarchical_bayes() instead

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> result = empirical_bayes(data)
        >>> print(f"Estimated prior: Beta({result.alpha_hat:.2f}, {result.beta_hat:.2f})")
        >>> print(f"E[T] = {result.posterior.mu:.3f}")
        >>> print(f"95% CI: [{result.posterior.ci_lower:.3f}, {result.posterior.ci_upper:.3f}]")
    """
    # Grid search for optimal (m, k)
    m_vals = np.linspace(m_range[0], m_range[1], m_grid)
    k_vals = np.logspace(np.log10(k_range[0]), np.log10(k_range[1]), k_grid)

    best_ll = -1e300
    best_m = None
    best_k = None

    for m in m_vals:
        for k in k_vals:
            ll = log_marginal_likelihood(m, k, data)
            if ll > best_ll:
                best_ll = ll
                best_m = m
                best_k = k

    if best_m is None or best_k is None:
        raise ValueError(
            "Grid search failed to find valid parameters. "
            "Try adjusting m_range or k_range."
        )

    # Convert to (α, β) parameterization
    alpha_hat = best_m * best_k
    beta_hat = (1.0 - best_m) * best_k

    # Compute posterior for T using our aggregation utilities
    posterior = compute_posterior_t_empirical_bayes(
        alpha_hat, beta_hat, data, ci_level, group_indices
    )

    # Determine metadata (respecting group_indices if provided)
    if group_indices is not None:
        group_indices_arr = np.asarray(group_indices, dtype=int)
        n_groups = len(group_indices_arr)
        n_total_trials = int(np.sum(data.n[group_indices_arr]))
        n_total_successes = int(np.sum(data.x[group_indices_arr]))
    else:
        n_groups = data.n_groups
        n_total_trials = data.n_total_trials
        n_total_successes = data.n_total_successes

    return EmpiricalBayesResult(
        m_hat=float(best_m),
        k_hat=float(best_k),
        alpha_hat=float(alpha_hat),
        beta_hat=float(beta_hat),
        log_marginal_likelihood=float(best_ll),
        posterior=posterior,
        n_groups=n_groups,
        n_total_trials=n_total_trials,
        n_total_successes=n_total_successes,
    )
