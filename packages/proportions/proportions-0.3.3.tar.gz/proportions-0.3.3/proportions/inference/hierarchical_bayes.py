"""Hierarchical Bayes inference for Beta-Binomial models using importance sampling.

This module implements Hierarchical Bayesian inference, which treats hyperparameters
(α, β) as random variables with their own prior distributions, fully accounting for
uncertainty in both the data and the hyperparameters.

The implementation uses importance sampling to approximate the posterior distribution
of the hyperparameters.
"""

import numpy as np

from proportions.aggregation.average_posterior import compute_posterior_t_hierarchical_bayes
from proportions.core.models import (
    BinomialData,
    HierarchicalBayesResult,
    ImportanceSamplingDiagnostics,
)
from proportions.distributions.beta import log_beta


def hierarchical_bayes(
    data: BinomialData,
    n_samples: int = 2000,
    m_prior_alpha: float = 1.0,
    m_prior_beta: float = 1.0,
    k_prior_min: float = 0.1,
    k_prior_max: float = 100.0,
    ci_level: float = 0.95,
    group_indices: list[int] | np.ndarray | None = None,
    random_seed: int | None = None,
    return_samples: bool = False,
) -> HierarchicalBayesResult:
    """Perform Hierarchical Bayes inference using importance sampling.

    Hierarchical Bayes treats hyperparameters (α, β) as random variables with
    their own prior distributions, fully accounting for uncertainty. This
    implementation uses importance sampling:

    1. Sample (m, k) from PRIOR
       - m ~ Beta(m_prior_alpha, m_prior_beta)
       - k ~ Uniform(k_prior_min, k_prior_max)
    2. Compute importance weights: w ∝ p(data | α, β)
    3. Use weighted samples to compute posterior for T = average(θ)
    4. Apply Law of Total Variance for proper uncertainty quantification

    Args:
        data: Binomial data (success and trial counts per group).
        n_samples: Number of samples to draw from prior (default: 2000).
        m_prior_alpha: Beta prior alpha for m (default: 1.0 for uniform).
        m_prior_beta: Beta prior beta for m (default: 1.0 for uniform).
        k_prior_min: Lower bound for uniform prior on k (default: 0.1).
        k_prior_max: Upper bound for uniform prior on k (default: 100.0).
        ci_level: Credible interval level (default: 0.95).
        group_indices: Optional list of group indices to include in analysis.
                       If None, includes all groups.
        random_seed: Random seed for reproducibility.
        return_samples: If True, include alpha_samples and beta_samples in result
                        for computing prior distribution (default: False).

    Returns:
        HierarchicalBayesResult with:
            - Posterior means for m, k, α, β
            - Posterior distribution for T = average(θ)
            - Variance decomposition (within + between)
            - Importance sampling diagnostics (ESS, boundary checks)
            - Log marginal likelihood (evidence)
            - Metadata: n_groups, n_total_trials, n_total_successes
            - (Optional) alpha_samples, beta_samples if return_samples=True

    Notes:
        - The key difference from Empirical Bayes is accounting for
          hyperparameter uncertainty via Law of Total Variance:
          Var[T] = E[Var[T | α, β]] + Var[E[T | α, β]]
        - Effective Sample Size (ESS) measures quality of importance sampling
        - Low ESS (<10% of n_samples) is normal when likelihood is peaked
        - Boundary warnings indicate k posterior is near prior limits

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> result = hierarchical_bayes(data, random_seed=42)
        >>> print(f"Estimated prior: Beta({result.alpha_posterior_mean:.2f}, "
        ...       f"{result.beta_posterior_mean:.2f})")
        >>> print(f"E[T] = {result.posterior.mu:.3f}")
        >>> print(f"95% CI: [{result.posterior.ci_lower:.3f}, "
        ...       f"{result.posterior.ci_upper:.3f}]")
        >>> print(f"ESS: {result.diagnostics.effective_sample_size:.0f} / "
        ...       f"{result.diagnostics.n_samples}")
        >>> print(f"Variance decomposition: within={result.variance_within:.6f}, "
        ...       f"between={result.variance_between:.6f}")
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
            # log p(xᵢ | α, β) = log B(α + xᵢ, β + nᵢ - xᵢ) - log B(α, β)
            ll += log_beta(alpha_i + xi, beta_i + ni - xi) - log_beta(alpha_i, beta_i)

        log_weights[i] = ll

    # Step 3: Normalize weights (using log-sum-exp trick for stability)
    log_weights_normalized = log_weights - np.max(log_weights)
    weights = np.exp(log_weights_normalized)
    weights = weights / np.sum(weights)

    # Step 4: Compute effective sample size
    ess = 1.0 / np.sum(weights**2)

    # Step 5: Compute weighted posterior means for hyperparameters
    m_posterior_mean = float(np.sum(weights * m_samples))
    k_posterior_mean = float(np.sum(weights * k_samples))

    # Compute alpha and beta from m and k to ensure consistency
    # (weighted mean of product ≠ product of weighted means)
    alpha_posterior_mean = m_posterior_mean * k_posterior_mean
    beta_posterior_mean = (1.0 - m_posterior_mean) * k_posterior_mean

    # Step 6: Compute diagnostics
    k_std = float(np.sqrt(np.sum(weights * (k_samples - k_posterior_mean) ** 2)))
    k_q05 = float(np.percentile(k_samples, 5))
    k_q95 = float(np.percentile(k_samples, 95))

    m_std = float(np.sqrt(np.sum(weights * (m_samples - m_posterior_mean) ** 2)))
    m_q05 = float(np.percentile(m_samples, 5))
    m_q95 = float(np.percentile(m_samples, 95))

    # Check if k posterior is hitting boundaries
    k_range = k_prior_max - k_prior_min
    k_at_lower = (k_q05 - k_prior_min) < 0.1 * k_range
    k_at_upper = (k_prior_max - k_q95) < 0.1 * k_range
    k_at_boundary = k_at_lower or k_at_upper

    diagnostics = ImportanceSamplingDiagnostics(
        n_samples=n_samples,
        effective_sample_size=ess,
        k_mean=k_posterior_mean,
        k_std=k_std,
        k_q05=k_q05,
        k_q95=k_q95,
        k_at_boundary=k_at_boundary,
        k_at_lower=k_at_lower,
        k_at_upper=k_at_upper,
        m_mean=m_posterior_mean,
        m_std=m_std,
        m_q05=m_q05,
        m_q95=m_q95,
    )

    # Step 7: Compute posterior for T using aggregation utilities
    # This handles the law of total variance internally
    posterior_result = compute_posterior_t_hierarchical_bayes(
        alpha_samples, beta_samples, data, weights, ci_level, group_indices,
        generate_samples=return_samples  # Generate samples if requested
    )

    # Step 8: Compute variance decomposition for the result
    # We need to recompute this to extract the components
    if group_indices is not None:
        group_indices_arr = np.asarray(group_indices, dtype=int)
        x_subset = data.x[group_indices_arr]
        n_subset = data.n[group_indices_arr]
        k_groups = len(group_indices_arr)
    else:
        x_subset = data.x
        n_subset = data.n
        k_groups = data.n_groups

    w = np.ones(k_groups) / k_groups

    # For each (αⱼ, βⱼ) sample, compute moments of T | αⱼ, βⱼ, data
    mu_T_samples = np.zeros(n_samples)
    var_T_samples = np.zeros(n_samples)

    for j in range(n_samples):
        alpha_j = alpha_samples[j]
        beta_j = beta_samples[j]

        # Posterior parameters for each θᵢ given this (αⱼ, βⱼ)
        alpha_post = alpha_j + x_subset
        beta_post = beta_j + (n_subset - x_subset)

        # Moments of each θᵢ | αⱼ, βⱼ, data
        means = alpha_post / (alpha_post + beta_post)
        variances = (alpha_post * beta_post) / (
            (alpha_post + beta_post) ** 2 * (alpha_post + beta_post + 1.0)
        )

        # Moments of T = mean(θᵢ) given this (αⱼ, βⱼ)
        mu_T_samples[j] = float(np.sum(w * means))
        var_T_samples[j] = float(np.sum(w**2 * variances))

    # Weighted variance decomposition
    mu_T = float(np.sum(weights * mu_T_samples))
    variance_within = float(np.sum(weights * var_T_samples))  # E[Var[T | α, β]]
    variance_between = float(
        np.sum(weights * (mu_T_samples - mu_T) ** 2)
    )  # Var[E[T | α, β]]

    # Step 9: Compute log marginal likelihood (evidence)
    # For importance sampling with prior proposal q(α,β) = p(α,β):
    #   p(data) = ∫ p(data|α,β) p(α,β) dα dβ
    #          ≈ (1/N) Σⱼ p(data|αⱼ,βⱼ)    [Monte Carlo with samples from p(α,β)]
    #          = (1/N) Σⱼ wⱼ                [where wⱼ are unnormalized weights]
    #
    # We need: log p(data) = log(mean(wⱼ)) = log(mean(exp(log wⱼ)))
    #
    # LOG-SUM-EXP TRICK for numerical stability:
    # Direct computation of exp(log wⱼ) causes overflow/underflow because
    # log wⱼ can range from -1000 to +1000, making exp(log wⱼ) ∈ [10^-434, 10^434].
    #
    # Instead, factor out the maximum M = max(log wⱼ):
    #   mean(exp(log wⱼ)) = mean(exp(log wⱼ - M + M))
    #                     = exp(M) · mean(exp(log wⱼ - M))
    #
    # Taking logs:
    #   log(mean(exp(log wⱼ))) = M + log(mean(exp(log wⱼ - M)))
    #
    # Now exp(log wⱼ - M) ∈ [0, 1] for all j, which is numerically stable.
    log_marginal_likelihood = float(
        np.max(log_weights) + np.log(np.mean(np.exp(log_weights - np.max(log_weights))))
    )

    # Step 10: Determine metadata (respecting group_indices if provided)
    if group_indices is not None:
        group_indices_arr = np.asarray(group_indices, dtype=int)
        n_groups_result = len(group_indices_arr)
        n_total_trials = int(np.sum(data.n[group_indices_arr]))
        n_total_successes = int(np.sum(data.x[group_indices_arr]))
    else:
        n_groups_result = data.n_groups
        n_total_trials = data.n_total_trials
        n_total_successes = data.n_total_successes

    return HierarchicalBayesResult(
        m_posterior_mean=m_posterior_mean,
        k_posterior_mean=k_posterior_mean,
        alpha_posterior_mean=alpha_posterior_mean,
        beta_posterior_mean=beta_posterior_mean,
        posterior=posterior_result,
        variance_within=variance_within,
        variance_between=variance_between,
        diagnostics=diagnostics,
        log_marginal_likelihood=log_marginal_likelihood,
        n_groups=n_groups_result,
        n_total_trials=n_total_trials,
        n_total_successes=n_total_successes,
        alpha_samples=alpha_samples if return_samples else None,
        beta_samples=beta_samples if return_samples else None,
        importance_weights=weights if return_samples else None,
    )
