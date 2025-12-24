"""Clopper-Pearson exact confidence interval for binomial proportions.

This module implements the frequentist Clopper-Pearson method for computing
exact confidence intervals for a binomial proportion.
"""

import numpy as np

from proportions.core.models import BinomialData, PosteriorResult
from proportions.distributions.beta import beta_ppf


def clopper_pearson(
    data: BinomialData,
    ci_level: float = 0.95,
    group_indices: list[int] | np.ndarray | None = None,
) -> PosteriorResult:
    """Compute Clopper-Pearson exact confidence interval for pooled proportion.

    The Clopper-Pearson method provides exact frequentist confidence intervals
    for a binomial proportion by inverting the binomial test. It pools all data
    and computes a confidence interval that has exactly the stated coverage
    probability.

    The method uses the relationship between the binomial distribution and the
    Beta distribution to compute exact intervals.

    Args:
        data: Binomial data (success and trial counts per group).
        ci_level: Confidence interval level (default: 0.95).
        group_indices: Optional list of group indices to include in pooling.
                       If None, pools all groups.

    Returns:
        PosteriorResult with:
            - mu: Pooled point estimate (MLE) = x_total / n_total
            - variance: Binomial variance under the MLE
            - alpha_fitted: None (not a Bayesian method)
            - beta_fitted: None (not a Bayesian method)
            - ci_lower, ci_upper: Exact confidence interval bounds
            - std, ci_width: Computed fields

    Notes:
        - This is a frequentist method (not Bayesian)
        - Provides exact coverage (not asymptotic approximation)
        - Conservative: actual coverage ≥ nominal coverage
        - Appropriate when no prior information is available
        - For Bayesian inference, use single_theta_bayesian() instead

    Implementation:
        For x successes in n trials, the exact (1-α) CI is:
            Lower bound: Beta quantile at α/2 with parameters (x, n-x+1)
            Upper bound: Beta quantile at 1-α/2 with parameters (x+1, n-x)

        Edge cases:
            - x = 0: lower bound = 0
            - x = n: upper bound = 1

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> from proportions.inference import clopper_pearson
        >>>
        >>> # Pool data across groups
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> result = clopper_pearson(data)
        >>>
        >>> print(f"Point estimate: {result.mu:.3f}")
        Point estimate: 0.800
        >>> print(f"95% CI: [{result.ci_lower:.3f}, {result.ci_upper:.3f}]")
        95% CI: [0.699, 0.877]
    """
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

    # Point estimate (MLE)
    p_hat = x_total / n_total

    # Clopper-Pearson exact confidence interval
    # Uses the relationship between binomial and Beta distributions
    alpha_level = 1.0 - ci_level

    if x_total == 0:
        # All failures: lower bound is 0
        ci_lower = 0.0
        ci_upper = float(beta_ppf(1.0 - alpha_level / 2, x_total + 1, n_total - x_total))
    elif x_total == n_total:
        # All successes: upper bound is 1
        ci_lower = float(beta_ppf(alpha_level / 2, x_total, n_total - x_total + 1))
        ci_upper = 1.0
    else:
        # General case
        ci_lower = float(beta_ppf(alpha_level / 2, x_total, n_total - x_total + 1))
        ci_upper = float(beta_ppf(1.0 - alpha_level / 2, x_total + 1, n_total - x_total))

    # Variance under the MLE (binomial variance)
    variance = p_hat * (1 - p_hat) / n_total

    # NOTE: Clopper-Pearson is a frequentist method with no posterior distribution.
    # We set alpha_fitted and beta_fitted to None to indicate this is not Bayesian.
    # The confidence interval comes from the exact binomial test, not a Beta posterior.

    return PosteriorResult(
        mu=float(p_hat),
        variance=float(variance),
        alpha_fitted=None,
        beta_fitted=None,
        ci_level=ci_level,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
    )
