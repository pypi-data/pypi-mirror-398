"""Single-Theta Bayesian inference for pooled binomial data.

This module implements the simplest Bayesian approach: assume all groups share
a single common success rate θ, and pool all data for inference.
"""

import numpy as np

from proportions.core.models import BinomialData, SingleThetaResult, PosteriorResult
from proportions.distributions.beta import beta_quantiles, log_beta


def single_theta_bayesian(
    data: BinomialData,
    alpha_prior: float,
    beta_prior: float,
    ci_level: float = 0.95,
    group_indices: list[int] | np.ndarray | None = None,
) -> SingleThetaResult:
    """Perform Single-Theta Bayesian inference on pooled data.

    This is the simplest Bayesian approach: assume all groups share a single
    common success rate θ, pool all the data, and perform standard Beta-Binomial
    conjugate updating.

    Model:
        θ ~ Beta(α_prior, β_prior)
        x_total ~ Binomial(n_total, θ)
        θ | data ~ Beta(α_prior + x_total, β_prior + n_total - x_total)

    This approach is appropriate when:
    - Groups are believed to be homogeneous (same underlying rate)
    - Sample sizes are small and you want to borrow strength across groups
    - You want a simple baseline for comparison

    Args:
        data: Binomial data (success and trial counts per group).
        alpha_prior: Prior alpha parameter for Beta(α, β) on θ.
        beta_prior: Prior beta parameter for Beta(α, β) on θ.
        ci_level: Credible interval level (default: 0.95).
        group_indices: Optional list of group indices to include in pooling.
                       If None, pools all groups.

    Returns:
        SingleThetaResult with:
            - posterior: PosteriorResult for θ (= T in this case)
            - log_marginal_likelihood: Log evidence for model comparison
            - prior_alpha, prior_beta: Prior parameters used
            - n_groups, n_total_trials, n_total_successes: Data summary

    Notes:
        - This is NOT the same as averaging group-level posteriors
        - It assumes perfect homogeneity across groups
        - For heterogeneous groups, use empirical_bayes() or hierarchical_bayes()
        - The prior should typically come from empirical_bayes() hyperparameter estimates

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> from proportions.inference import empirical_bayes, single_theta_bayesian
        >>>
        >>> # Get data
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>>
        >>> # Get prior from Empirical Bayes
        >>> eb_result = empirical_bayes(data)
        >>> alpha_prior = eb_result.alpha_hat
        >>> beta_prior = eb_result.beta_hat
        >>>
        >>> # Single-Theta Bayesian with EB prior
        >>> result = single_theta_bayesian(data, alpha_prior, beta_prior)
        >>> print(f"θ = {result.mu:.3f} [{result.ci_lower:.3f}, {result.ci_upper:.3f}]")
        θ = 0.800 [0.754, 0.842]
    """
    if alpha_prior <= 0:
        raise ValueError(f"alpha_prior must be positive, got {alpha_prior}")
    if beta_prior <= 0:
        raise ValueError(f"beta_prior must be positive, got {beta_prior}")

    # Determine which groups to pool
    if group_indices is not None:
        group_indices_arr = np.asarray(group_indices, dtype=int)
        if len(group_indices_arr) == 0:
            raise ValueError("group_indices cannot be empty")
        if np.any(group_indices_arr < 0) or np.any(group_indices_arr >= data.n_groups):
            raise ValueError(
                f"group_indices must be in range [0, {data.n_groups-1}], "
                f"got min={group_indices_arr.min()}, max={group_indices_arr.max()}"
            )
        x_subset = data.x[group_indices_arr]
        n_subset = data.n[group_indices_arr]
    else:
        x_subset = data.x
        n_subset = data.n

    # Pool all data
    x_total = int(np.sum(x_subset))
    n_total = int(np.sum(n_subset))

    # Beta-Binomial conjugate update
    alpha_post = alpha_prior + x_total
    beta_post = beta_prior + (n_total - x_total)

    # Posterior moments
    mu = alpha_post / (alpha_post + beta_post)
    variance = (alpha_post * beta_post) / (
        (alpha_post + beta_post) ** 2 * (alpha_post + beta_post + 1.0)
    )

    # Compute credible interval
    alpha_lower = (1 - ci_level) / 2
    alpha_upper = 1 - alpha_lower
    quantiles = beta_quantiles([alpha_lower, alpha_upper], alpha_post, beta_post)
    ci_lower = float(quantiles[0])
    ci_upper = float(quantiles[1])

    # Compute log marginal likelihood (evidence)
    # p(data) = B(α + x, β + n - x) / B(α, β)
    log_evidence = (
        log_beta(alpha_prior + x_total, beta_prior + (n_total - x_total))
        - log_beta(alpha_prior, beta_prior)
    )

    # Create posterior result
    posterior = PosteriorResult(
        mu=float(mu),
        variance=float(variance),
        alpha_fitted=float(alpha_post),
        beta_fitted=float(beta_post),
        ci_level=ci_level,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
    )

    # Determine number of groups used
    if group_indices is not None:
        n_groups_used = len(group_indices_arr)
    else:
        n_groups_used = data.n_groups

    return SingleThetaResult(
        prior_alpha=float(alpha_prior),
        prior_beta=float(beta_prior),
        log_marginal_likelihood=float(log_evidence),
        posterior=posterior,
        n_groups=n_groups_used,
        n_total_trials=n_total,
        n_total_successes=x_total,
    )
