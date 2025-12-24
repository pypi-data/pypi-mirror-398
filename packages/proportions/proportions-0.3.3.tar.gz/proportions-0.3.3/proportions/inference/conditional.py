"""Conditional inference with selection/filtering.

This module provides functions for estimating posterior distributions
conditioned on observing k successes out of k trials (winner's curse problem).
"""

import numpy as np
from scipy.stats import beta as beta_dist  # For rvs (sampling)

from proportions.core.models import ConditionalPosteriorResult
from proportions.distributions import beta_mode, log_beta
from proportions.aggregation.moment_matching import fit_beta_from_moments


def conditional_inference_k_out_of_k(
    # Task A parameters (filtering task)
    alpha_task_a: np.ndarray,
    beta_task_a: np.ndarray,
    # Task B parameters (target task, optional)
    alpha_task_b: np.ndarray | None = None,
    beta_task_b: np.ndarray | None = None,
    # Filter and success criteria
    k: float = 10,
    m: float = 1,
    # Monte Carlo parameters
    n_samples: int = 100000,
    random_seed: int | None = None,
    # Output options
    fit_beta: bool = True,
    ci_level: float = 0.95,
) -> ConditionalPosteriorResult:
    """Estimate posterior distribution of E[θ_B^m | k/k successes on task A].

    This addresses the winner's curse / selection bias problem: scenarios
    that show k successes out of k trials on Task A may be truly good OR just lucky.

    **General Formula (from LaTeX Equation 191):**
    The weighted average is computed as:
        μ = (Σ θ_A_i^k · θ_B_i^m) / (Σ θ_A_i^k)

    where:
    - θ_A_i: success probability on Task A for scenario i
    - θ_B_i: success probability on Task B for scenario i
    - k: filter exponent (typically k/k successes on Task A)
    - m: success metric exponent (typically m/m successes on Task B)

    **IMPORTANT:** This function expects SUCCESS RATE posteriors. If your data
    represents failure rates, you must swap the parameters before calling:
        - If θ_failure ~ Beta(α, β), then θ_success ~ Beta(β, α)

    Uses Monte Carlo sampling:
    - Weight for scenario i: w_i = θ_A_i^k (probability of k/k successes)
    - Target value for scenario i: v_i = θ_B_i^m (probability of m/m successes)
    - Posterior mean: E[θ_B^m | filter] = Σ w_i · v_i / Σ w_i

    Args:
        alpha_task_a: Alpha parameters for task A SUCCESS rate posteriors (n_scenarios,).
        beta_task_a: Beta parameters for task A SUCCESS rate posteriors (n_scenarios,).
        alpha_task_b: Alpha parameters for task B SUCCESS rate posteriors (optional).
                      If None, uses task A parameters (self-conditional).
        beta_task_b: Beta parameters for task B SUCCESS rate posteriors (optional).
        k: Filter criterion exponent (default: 10). Typically represents k/k successes.
        m: Success metric exponent (default: 1). Typically represents m/m successes.
        n_samples: Number of Monte Carlo samples (default: 100000).
        random_seed: Random seed for reproducibility.
        fit_beta: Whether to fit Beta distribution to posterior via moment matching.
        ci_level: Credible interval level (default: 0.95).

    Returns:
        ConditionalPosteriorResult with posterior statistics, samples,
        and fitted Beta parameters.

    Raises:
        ValueError: If inputs have incompatible shapes or invalid values.

    Example:
        >>> # If you have FAILURE rate posteriors, swap parameters first:
        >>> alpha_success = beta_failure  # Swap!
        >>> beta_success = alpha_failure
        >>>
        >>> # Self-conditional: E[θ_A | k/k successes on Task A] with m=1
        >>> result = conditional_inference_k_out_of_k(
        ...     alpha_task_a=alpha_success,
        ...     beta_task_a=beta_success,
        ...     k=10,
        ...     m=1,  # Default: single-trial success probability
        ...     random_seed=42
        ... )
        >>> print(f"E[θ_A | 10/10 successes]: {result.mean:.4f}")
        >>> print(f"95% CI: [{result.ci_lower:.4f}, {result.ci_upper:.4f}]")
        >>>
        >>> # Self-conditional: E[θ_A^3 | 10/10 successes] (probability of 3/3 future successes)
        >>> result = conditional_inference_k_out_of_k(
        ...     alpha_task_a=alpha_success,
        ...     beta_task_a=beta_success,
        ...     k=10,
        ...     m=3,  # Probability of 3 consecutive successes
        ...     random_seed=42
        ... )
        >>> print(f"E[θ_A^3 | 10/10 successes]: {result.mean:.4f}")
        >>>
        >>> # Cross-conditional: Task B performance given Task A filter
        >>> result = conditional_inference_k_out_of_k(
        ...     alpha_task_a=alpha_success_a,
        ...     beta_task_a=beta_success_a,
        ...     alpha_task_b=alpha_success_b,
        ...     beta_task_b=beta_success_b,
        ...     k=3,
        ...     m=5  # E[θ_B^5] given 3/3 successes on Task A
        ... )
    """
    # Validate inputs
    alpha_task_a = np.asarray(alpha_task_a)
    beta_task_a = np.asarray(beta_task_a)

    if alpha_task_a.shape != beta_task_a.shape:
        raise ValueError(
            f"alpha_task_a and beta_task_a must have same shape: "
            f"{alpha_task_a.shape} vs {beta_task_a.shape}"
        )

    n_scenarios = len(alpha_task_a)

    if n_scenarios == 0:
        raise ValueError("Must have at least one scenario")

    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")

    if m <= 0:
        raise ValueError(f"m must be positive, got {m}")

    if not (0.0 < ci_level < 1.0):
        raise ValueError(f"ci_level must be in (0, 1), got {ci_level}")

    # Handle task B parameters (default to task A if not provided)
    if alpha_task_b is None:
        alpha_task_b = alpha_task_a
        beta_task_b = beta_task_a
    else:
        alpha_task_b = np.asarray(alpha_task_b)
        beta_task_b = np.asarray(beta_task_b)

        if alpha_task_b.shape != beta_task_b.shape:
            raise ValueError(
                f"alpha_task_b and beta_task_b must have same shape: "
                f"{alpha_task_b.shape} vs {beta_task_b.shape}"
            )

        if len(alpha_task_b) != n_scenarios:
            raise ValueError(
                f"Task B must have same number of scenarios as task A: "
                f"{len(alpha_task_b)} vs {n_scenarios}"
            )

    # ==========================================================================
    # MONTE CARLO SAMPLING
    # ==========================================================================

    if random_seed is not None:
        np.random.seed(random_seed)

    # Sample from posteriors for all scenarios
    theta_a_samples = np.zeros((n_samples, n_scenarios))

    for i in range(n_scenarios):
        theta_a_samples[:, i] = beta_dist.rvs(
            alpha_task_a[i], beta_task_a[i], size=n_samples
        )

    # For cross-conditional case, sample task B separately
    # For self-conditional, use task A samples for both weights and average
    if alpha_task_b is not alpha_task_a:  # Check if truly cross-conditional
        theta_b_samples = np.zeros((n_samples, n_scenarios))
        for i in range(n_scenarios):
            theta_b_samples[:, i] = beta_dist.rvs(
                alpha_task_b[i], beta_task_b[i], size=n_samples
            )
    else:
        # Self-conditional: use same samples for both
        theta_b_samples = theta_a_samples

    # Compute weights and weighted average for each MC sample
    mu_samples = np.zeros(n_samples)

    for j in range(n_samples):
        # Weights: w_i = θ_A_i^k (probability of k/k successes on Task A)
        weights = theta_a_samples[j, :] ** k

        # Target values: v_i = θ_B_i^m (probability of m/m successes on Task B)
        theta_b_powered = theta_b_samples[j, :] ** m

        # Weighted average: μ = Σ w_i · v_i / Σ w_i
        mu_samples[j] = np.sum(weights * theta_b_powered) / np.sum(weights)

    # ==========================================================================
    # COMPUTE STATISTICS
    # ==========================================================================

    mu_mean = float(mu_samples.mean())
    mu_std = float(mu_samples.std())
    mu_median = float(np.median(mu_samples))

    # Credible intervals
    ci_lower_pct = (1 - ci_level) / 2
    ci_upper_pct = 1 - ci_lower_pct
    ci_lower = float(np.percentile(mu_samples, 100 * ci_lower_pct))
    ci_upper = float(np.percentile(mu_samples, 100 * ci_upper_pct))

    # ==========================================================================
    # FIT BETA DISTRIBUTION (MOMENT MATCHING)
    # ==========================================================================

    alpha_fitted = None
    beta_fitted = None
    mode_fitted = None
    fitted_beta_success = False

    if fit_beta:
        mu_var = float(mu_samples.var())
        try:
            alpha_fitted, beta_fitted = fit_beta_from_moments(mu_mean, mu_var)
            mode_fitted = float(beta_mode(alpha_fitted, beta_fitted))
            fitted_beta_success = True
        except ValueError:
            # Moment matching failed (variance too large, etc.)
            fitted_beta_success = False

    # ==========================================================================
    # COMPUTE EXPECTED WEIGHTS (for visualization)
    # ==========================================================================

    # Compute expected weights: E[θ_A_i^k] for each scenario
    # For Beta(α, β) it can be shown E[θ^k] = B(α + k, β) / B(α, β)
    # These expected weights shall be close to the average of the MC weeights
    weights_expected = np.zeros(n_scenarios)
    for i in range(n_scenarios):
        log_weight = (
            log_beta(alpha_task_a[i] + k, beta_task_a[i])
            - log_beta(alpha_task_a[i], beta_task_a[i])
        )
        weights_expected[i] = np.exp(log_weight)

    # Normalize
    weights_expected /= weights_expected.sum()

    # ==========================================================================
    # RETURN RESULT
    # ==========================================================================

    return ConditionalPosteriorResult(
        mean=mu_mean,
        median=mu_median,
        mode=mode_fitted,
        std=mu_std,
        ci_level=ci_level,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        samples=mu_samples,
        n_samples=n_samples,
        fitted_beta=fitted_beta_success,
        alpha_fitted=alpha_fitted,
        beta_fitted=beta_fitted,
        k=k,
        m=m,
        n_scenarios=n_scenarios,
        scenario_weights=weights_expected,
    )
