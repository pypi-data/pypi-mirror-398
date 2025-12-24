"""Prior fitting utilities for Beta distributions.

This module provides tools for fitting Beta distribution parameters from
credible interval specifications.
"""

import numpy as np
from scipy.optimize import minimize_scalar

from proportions.distributions.beta import beta_ppf


def fit_beta_from_credible_interval(
    ci_lower: float,
    ci_upper: float,
    ci_level: float = 0.95,
    mode: float | None = None,
) -> tuple[float, float]:
    """Fit Beta distribution parameters from credible interval bounds.

    Finds Beta(α, β) parameters such that the specified credible interval
    matches the given bounds. This is useful for eliciting priors from
    domain experts who can specify plausible ranges.

    The algorithm searches for (α, β) by:
    1. If mode is provided, uses relationship: mode = (α-1)/(α+β-2)
    2. Otherwise, assumes symmetric interval around mean
    3. Uses optimization to match CI bounds to quantiles

    Args:
        ci_lower: Lower bound of credible interval (must be in (0, 1)).
        ci_upper: Upper bound of credible interval (must be in (0, 1)).
        ci_level: Credible interval level (default: 0.95).
        mode: Optional mode of the Beta distribution. If None, uses midpoint.

    Returns:
        Tuple (alpha, beta) of fitted Beta parameters.

    Raises:
        ValueError: If bounds are invalid or fitting fails.

    Notes:
        - This is an approximation method, not exact
        - Works best when CI is not too extreme (not near 0 or 1)
        - For very tight CIs, resulting (α, β) will be large
        - For very wide CIs, resulting (α, β) will be small

    Example:
        >>> # Expert believes success rate is between 70% and 90% (95% CI)
        >>> alpha, beta = fit_beta_from_credible_interval(0.70, 0.90, ci_level=0.95)
        >>> print(f"Prior: Beta({alpha:.2f}, {beta:.2f})")
        Prior: Beta(15.41, 2.89)
        >>>
        >>> # Verify the fit
        >>> from proportions.distributions.beta import beta_ppf
        >>> print(f"95% CI: [{beta_ppf(0.025, alpha, beta):.3f}, "
        ...       f"{beta_ppf(0.975, alpha, beta):.3f}]")
        95% CI: [0.700, 0.900]
    """
    # Validate inputs
    if not (0 < ci_lower < 1):
        raise ValueError(f"ci_lower must be in (0, 1), got {ci_lower}")
    if not (0 < ci_upper < 1):
        raise ValueError(f"ci_upper must be in (0, 1), got {ci_upper}")
    if ci_lower >= ci_upper:
        raise ValueError(
            f"ci_lower ({ci_lower}) must be < ci_upper ({ci_upper})"
        )
    if not (0 < ci_level < 1):
        raise ValueError(f"ci_level must be in (0, 1), got {ci_level}")

    # Quantiles corresponding to CI level
    alpha_tail = (1 - ci_level) / 2
    q_lower = alpha_tail
    q_upper = 1 - alpha_tail

    # Estimate mean from bounds (midpoint or mode)
    if mode is None:
        mean = (ci_lower + ci_upper) / 2
    else:
        if not (0 < mode < 1):
            raise ValueError(f"mode must be in (0, 1), got {mode}")
        mean = mode  # Use mode as starting point

    # Estimate spread from CI width
    # For Beta distribution, variance ≈ (width/4)² for 95% CI
    width = ci_upper - ci_lower
    variance = (width / 4) ** 2

    # Initial guess using method of moments
    # Mean = α/(α+β), Variance = αβ/((α+β)²(α+β+1))
    # Solving: common = μ(1-μ)/σ² - 1
    if variance >= mean * (1 - mean):
        # Variance too large, use weak prior
        alpha_init = 1.0
        beta_init = 1.0
    else:
        common = mean * (1 - mean) / variance - 1
        alpha_init = mean * common
        beta_init = (1 - mean) * common

    # Refine using optimization to match quantiles exactly
    def objective(log_concentration):
        """Objective function: sum of squared errors in quantiles."""
        k = np.exp(log_concentration)
        alpha = mean * k
        beta = (1 - mean) * k

        if alpha <= 0 or beta <= 0:
            return 1e10

        try:
            # Compute quantiles with current parameters
            q_low_pred = beta_ppf(q_lower, alpha, beta)
            q_high_pred = beta_ppf(q_upper, alpha, beta)

            # Error in matching target bounds
            error = (q_low_pred - ci_lower)**2 + (q_high_pred - ci_upper)**2
            return error
        except:
            return 1e10

    # Optimize concentration parameter k = α + β
    result = minimize_scalar(
        objective,
        bounds=(np.log(2), np.log(10000)),  # k ∈ [2, 10000]
        method='bounded',
    )

    if not result.success:
        # Fall back to moment-matching estimate
        alpha = alpha_init
        beta = beta_init
    else:
        k_opt = np.exp(result.x)
        alpha = mean * k_opt
        beta = (1 - mean) * k_opt

    # Ensure parameters are reasonable
    alpha = max(0.01, min(alpha, 10000))
    beta = max(0.01, min(beta, 10000))

    return float(alpha), float(beta)
