"""Computing posterior for T = average(θ) across all groups.

This module provides functions to compute the posterior distribution of
T = average(θ₁, ..., θₖ) using moment matching to approximate with a Beta
distribution.

It also provides functions to compute posteriors for individual scenario
success rates θᵢ.

The key insight is that all methods (Flat Bayes, Empirical Bayes,
Hierarchical Bayes) use the same aggregation approach via moment matching,
but differ in how they account for uncertainty in the hyperparameters.
"""

import numpy as np

from proportions.aggregation.moment_matching import fit_beta_from_moments, beta_mean
from proportions.core.models import BinomialData, PosteriorResult
from proportions.distributions.beta import beta_quantiles


def compute_prior_t_hierarchical_bayes(
    alpha_samples: np.ndarray,
    beta_samples: np.ndarray,
    data: BinomialData,
    ci_level: float = 0.95,
    group_indices: list[int] | np.ndarray | None = None,
    generate_samples: bool = True,
) -> PosteriorResult:
    """Compute prior distribution of T = average(θᵢ) from hyperparameter samples.

    This computes the PRIOR distribution of the average success rate μ by using
    uniform weights across hyperparameter samples, unlike the posterior which
    uses importance weights based on the likelihood.

    For each (α_j, β_j) sample from the hyperprior:
    1. Compute E[μ | α_j, β_j] assuming no data (using prior α_j, β_j)
    2. Use uniform weights to compute overall prior moments
    3. Fit Beta distribution via moment matching

    Args:
        alpha_samples: Array of α samples from hyperprior (shape: n_samples).
        beta_samples: Array of β samples from hyperprior (shape: n_samples).
        data: Binomial data (used only to determine number of scenarios).
        ci_level: Credible interval level (default: 0.95).
        group_indices: Optional list of group indices to include in the average.
                       If None, includes all groups.

    Returns:
        PosteriorResult with prior distribution for T, including:
            - mu: Prior mean E[T]
            - variance: Prior variance
            - alpha_fitted: Fitted Beta distribution alpha parameter
            - beta_fitted: Fitted Beta distribution beta parameter
            - ci_lower: Lower bound of credible interval
            - ci_upper: Upper bound of credible interval
            - ci_width: Width of credible interval

    Example:
        >>> # Get hyperparameter samples from hierarchical_bayes
        >>> prior_result = compute_prior_t_hierarchical_bayes(
        ...     alpha_samples, beta_samples, data
        ... )
        >>> print(f"Prior E[μ] = {prior_result.mu:.3f}")
        >>> print(f"Prior 95% CI: [{prior_result.ci_lower:.3f}, "
        ...       f"{prior_result.ci_upper:.3f}]")
    """
    n_samples = len(alpha_samples)
    if len(beta_samples) != n_samples:
        raise ValueError(
            f"Length mismatch: alpha_samples has {n_samples} elements, "
            f"beta_samples has {len(beta_samples)} elements"
        )

    # Determine which groups to include
    if group_indices is not None:
        k_groups = len(group_indices)
    else:
        k_groups = data.n_groups

    # Uniform weights across all groups
    w = np.ones(k_groups) / k_groups

    # For each (α_j, β_j) sample, compute moments of μ | α_j, β_j
    # where μ = (θ₁ + ... + θₖ)/k and θᵢ ~ Beta(α_j, β_j) independently
    mu_T_samples = np.zeros(n_samples)
    var_T_samples = np.zeros(n_samples)

    # If generate_samples is True, we actually sample θ values and average them
    # to get the true distribution of μ (for visualization)
    actual_mu_samples = None
    if generate_samples:
        actual_mu_samples = np.zeros(n_samples)

    for j in range(n_samples):
        alpha_j = alpha_samples[j]
        beta_j = beta_samples[j]

        # Prior moments for each θᵢ given (α_j, β_j)
        # E[θᵢ | α_j, β_j] = α_j / (α_j + β_j)
        mean_theta = alpha_j / (alpha_j + beta_j)

        # Var[θᵢ | α_j, β_j] = (α_j * β_j) / [(α_j + β_j)² * (α_j + β_j + 1)]
        var_theta = (alpha_j * beta_j) / ((alpha_j + beta_j) ** 2 * (alpha_j + beta_j + 1.0))

        # For μ = (θ₁ + ... + θₖ)/k where θᵢ are independent given (α_j, β_j):
        # E[μ | α_j, β_j] = E[θᵢ | α_j, β_j] = mean_theta
        mu_T_samples[j] = mean_theta

        # Var[μ | α_j, β_j] = Var[(θ₁ + ... + θₖ)/k] = (1/k²) * k * Var[θᵢ] = Var[θᵢ]/k
        var_T_samples[j] = var_theta / k_groups

        # Generate actual sample of μ by sampling θ₁, ..., θₖ and averaging
        if generate_samples:
            theta_samples = np.random.beta(alpha_j, beta_j, size=k_groups)
            actual_mu_samples[j] = np.mean(theta_samples)

    # Use UNIFORM weights (not importance weights) for prior
    uniform_weights = np.ones(n_samples) / n_samples

    # Compute prior moments using Law of Total Variance
    # E[μ] = E[E[μ | α, β]]
    mu_T = float(np.sum(uniform_weights * mu_T_samples))

    # Var[μ] = E[Var[μ | α, β]] + Var[E[μ | α, β]]
    variance_within = float(np.sum(uniform_weights * var_T_samples))  # E[Var[μ | α, β]]
    variance_between = float(np.sum(uniform_weights * (mu_T_samples - mu_T) ** 2))  # Var[E[μ | α, β]]
    variance_T = variance_within + variance_between

    # Fit Beta distribution via moment matching
    alpha_fitted, beta_fitted = fit_beta_from_moments(mu_T, variance_T)

    # Compute credible intervals
    alpha_lower = (1 - ci_level) / 2
    alpha_upper = 1 - alpha_lower
    quantiles = beta_quantiles([alpha_lower, alpha_upper], alpha_fitted, beta_fitted)
    ci_lower = float(quantiles[0])
    ci_upper = float(quantiles[1])

    return PosteriorResult(
        mu=mu_T,
        variance=variance_T,
        alpha_fitted=alpha_fitted,
        beta_fitted=beta_fitted,
        ci_level=ci_level,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        ci_width=ci_upper - ci_lower,
        samples=actual_mu_samples,  # Use actual sampled μ values, not conditional means
    )


def compute_posterior_t_from_group_posteriors(
    alpha_post: np.ndarray,
    beta_post: np.ndarray,
    ci_level: float = 0.95,
    group_indices: list[int] | np.ndarray | None = None,
) -> PosteriorResult:
    """Compute posterior distribution of T = average(θᵢ) from group posteriors.

    Given independent posterior distributions θᵢ ~ Beta(alpha_post[i], beta_post[i]),
    computes the distribution of T = (1/k) Σ θᵢ via:
    1. Analytical computation of E[T] and Var[T]
    2. Moment matching to a Beta distribution
    3. Computing credible intervals from the fitted Beta

    This approach is used by both Flat Bayes and Empirical Bayes methods,
    which treat hyperparameters as fixed.

    Args:
        alpha_post: Posterior alpha parameters for each group (shape: n_groups).
        beta_post: Posterior beta parameters for each group (shape: n_groups).
        ci_level: Credible interval level (default: 0.95).
        group_indices: Optional list of group indices to include in the average.
                       If None, includes all groups. Useful for computing posteriors
                       for subsets of groups.

    Returns:
        PosteriorResult with posterior distribution for T, including:
            - mu: Posterior mean (also available as E[T])
            - variance: Posterior variance
            - alpha_fitted: Fitted Beta distribution alpha parameter
            - beta_fitted: Fitted Beta distribution beta parameter
            - ci_lower: Lower bound of credible interval
            - ci_upper: Upper bound of credible interval
            - std: Posterior standard deviation (computed field)
            - ci_width: Width of credible interval (computed field)

        The median can be computed separately using beta_ppf(0.5, alpha_fitted, beta_fitted).

    Notes:
        Since θᵢ are independent:
            E[T] = (1/k) Σ E[θᵢ]
            Var[T] = (1/k²) Σ Var[θᵢ]

    Example:
        >>> import numpy as np
        >>> from proportions.distributions.beta import beta_ppf
        >>> alpha_post = np.array([10.0, 15.0, 12.0])
        >>> beta_post = np.array([2.0, 3.0, 2.5])
        >>>
        >>> # All groups
        >>> result = compute_posterior_t_from_group_posteriors(alpha_post, beta_post)
        >>> print(f"E[T] = {result.mu:.3f}")
        E[T] = 0.831
        >>> print(f"Median = {beta_ppf(0.5, result.alpha_fitted, result.beta_fitted):.3f}")
        >>> print(f"95% CI: [{result.ci_lower:.3f}, {result.ci_upper:.3f}]")
        >>>
        >>> # Subset of groups (first two only)
        >>> result_subset = compute_posterior_t_from_group_posteriors(
        ...     alpha_post, beta_post, group_indices=[0, 1]
        ... )
        >>> print(f"E[T] for groups 0,1 = {result_subset.mu:.3f}")
        E[T] for groups 0,1 = 0.825
    """
    k_groups = len(alpha_post)
    if len(beta_post) != k_groups:
        raise ValueError(
            f"Length mismatch: alpha_post has {k_groups} elements, "
            f"beta_post has {len(beta_post)} elements"
        )

    # Apply group selection if specified
    if group_indices is not None:
        group_indices = np.asarray(group_indices, dtype=int)
        if len(group_indices) == 0:
            raise ValueError("group_indices cannot be empty")
        if np.any(group_indices < 0) or np.any(group_indices >= k_groups):
            raise ValueError(
                f"group_indices must be in range [0, {k_groups-1}], "
                f"got min={group_indices.min()}, max={group_indices.max()}"
            )
        alpha_post = alpha_post[group_indices]
        beta_post = beta_post[group_indices]
        k_groups = len(group_indices)

    # Uniform weights for average
    w = np.ones(k_groups) / k_groups

    # Posterior mean and variance of each θᵢ
    means = alpha_post / (alpha_post + beta_post)
    variances = (alpha_post * beta_post) / (
        (alpha_post + beta_post) ** 2 * (alpha_post + beta_post + 1.0)
    )

    # Posterior mean and variance of T = Σ wᵢθᵢ
    # Since θᵢ are independent:
    mu_T = float(np.sum(w * means))
    var_T = float(np.sum(w**2 * variances))

    # Moment-match to Beta distribution
    if var_T <= 0 or mu_T <= 0 or mu_T >= 1:
        raise ValueError(
            f"Cannot fit Beta distribution: mu_T={mu_T:.6f}, var_T={var_T:.6f}. "
            "Mean must be in (0, 1) and variance must be positive."
        )

    alpha_T, beta_T = fit_beta_from_moments(mu_T, var_T)

    # Compute credible intervals
    alpha_lower = (1 - ci_level) / 2
    alpha_upper = 1 - alpha_lower
    quantiles = beta_quantiles([alpha_lower, alpha_upper], alpha_T, beta_T)
    ci_lower = float(quantiles[0])
    ci_upper = float(quantiles[1])

    return PosteriorResult(
        mu=mu_T,
        variance=var_T,
        alpha_fitted=alpha_T,
        beta_fitted=beta_T,
        ci_level=ci_level,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
    )


def compute_posterior_t_empirical_bayes(
    alpha_hat: float,
    beta_hat: float,
    data: BinomialData,
    ci_level: float = 0.95,
    group_indices: list[int] | np.ndarray | None = None,
) -> PosteriorResult:
    """Compute posterior distribution of T for Empirical Bayes.

    Given estimated hyperparameters (α̂, β̂) from empirical Bayes, computes
    posterior distribution of T = average(θᵢ).

    This is equivalent to computing posteriors for each group and then
    aggregating via compute_posterior_t_from_group_posteriors().

    Args:
        alpha_hat: Estimated prior alpha parameter.
        beta_hat: Estimated prior beta parameter.
        data: Binomial data (success counts and trial counts).
        ci_level: Credible interval level (default: 0.95).
        group_indices: Optional list of group indices to include in the average.
                       If None, includes all groups.

    Returns:
        PosteriorResult with posterior distribution for T.

    Notes:
        Empirical Bayes treats hyperparameters as fixed at their MLE values,
        so this only accounts for data uncertainty, not hyperparameter uncertainty.

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> result = compute_posterior_t_empirical_bayes(8.0, 2.0, data)
        >>> print(f"E[T] = {result.mu:.3f}, 95% CI: [{result.ci_lower:.3f}, {result.ci_upper:.3f}]")
        E[T] = 0.800, 95% CI: [0.742, 0.851]
    """
    # Posterior parameters for each group: θᵢ | data ~ Beta(α̂ + xᵢ, β̂ + nᵢ - xᵢ)
    alpha_post = alpha_hat + data.x
    beta_post = beta_hat + (data.n - data.x)

    return compute_posterior_t_from_group_posteriors(
        alpha_post, beta_post, ci_level, group_indices
    )


def compute_posterior_t_hierarchical_bayes(
    alpha_samples: np.ndarray,
    beta_samples: np.ndarray,
    data: BinomialData,
    weights: np.ndarray | None = None,
    ci_level: float = 0.95,
    group_indices: list[int] | np.ndarray | None = None,
    generate_samples: bool = False,
) -> PosteriorResult:
    """Compute posterior distribution of T for Hierarchical Bayes.

    Given samples (or weighted samples) from the posterior of hyperparameters
    (α, β), computes the posterior distribution of T = average(θᵢ) by:
    1. For each (αⱼ, βⱼ) sample, compute E[T | αⱼ, βⱼ, data] and Var[T | αⱼ, βⱼ, data]
    2. Average across samples: E[T] = E[E[T | α, β]] and apply Law of Total Variance
    3. Moment-match to Beta and compute credible intervals

    This approach properly accounts for uncertainty in the hyperparameters.

    Args:
        alpha_samples: Samples from posterior of α (shape: n_samples).
        beta_samples: Samples from posterior of β (shape: n_samples).
        data: Binomial data (success counts and trial counts).
        weights: Optional importance sampling weights (shape: n_samples).
                 If None, assumes uniform weights (standard MCMC samples).
        ci_level: Credible interval level (default: 0.95).
        group_indices: Optional list of group indices to include in the average.
                       If None, includes all groups.

    Returns:
        PosteriorResult with posterior distribution for T.

    Notes:
        The key difference from Empirical Bayes is the variance decomposition:
            Var[T] = E[Var[T | α, β]] + Var[E[T | α, β]]

        The second term (between-hyperparameter variance) accounts for uncertainty
        in the hyperparameters, making HB intervals wider than EB intervals.

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> # Assume we have samples from HB
        >>> alpha_samples = np.array([16.5, 17.2, 16.8])  # from MCMC/importance sampling
        >>> beta_samples = np.array([2.9, 3.1, 3.0])
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> result = compute_posterior_t_hierarchical_bayes(alpha_samples, beta_samples, data)
        >>> print(f"E[T] = {result.mu:.3f}")
        E[T] = 0.845
    """
    n_samples = len(alpha_samples)
    if len(beta_samples) != n_samples:
        raise ValueError(
            f"Length mismatch: alpha_samples has {n_samples} elements, "
            f"beta_samples has {len(beta_samples)} elements"
        )

    # Handle group selection
    if group_indices is not None:
        group_indices = np.asarray(group_indices, dtype=int)
        if len(group_indices) == 0:
            raise ValueError("group_indices cannot be empty")
        if np.any(group_indices < 0) or np.any(group_indices >= data.n_groups):
            raise ValueError(
                f"group_indices must be in range [0, {data.n_groups-1}], "
                f"got min={group_indices.min()}, max={group_indices.max()}"
            )
        # Select subset of data
        x_subset = data.x[group_indices]
        n_subset = data.n[group_indices]
        k_groups = len(group_indices)
    else:
        x_subset = data.x
        n_subset = data.n
        k_groups = data.n_groups

    # Set up weights (uniform if not provided)
    if weights is None:
        weights = np.ones(n_samples) / n_samples
    else:
        if len(weights) != n_samples:
            raise ValueError(
                f"Length mismatch: weights has {len(weights)} elements, "
                f"expected {n_samples}"
            )
        # Ensure weights are normalized
        weights = weights / np.sum(weights)

    # Uniform weights for averaging across groups
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

    # Weighted average across all (α, β) samples
    # This marginalizes over hyperparameter uncertainty
    mu_T = float(np.sum(weights * mu_T_samples))  # E[E[T | α, β]]

    # Law of Total Variance: Var[T] = E[Var[T | α, β]] + Var[E[T | α, β]]
    var_within = float(np.sum(weights * var_T_samples))  # E[Var[T | α, β]]
    var_between = float(
        np.sum(weights * (mu_T_samples - mu_T) ** 2)
    )  # Var[E[T | α, β]]
    var_T = var_within + var_between

    # Moment-match to Beta distribution
    if var_T <= 0 or mu_T <= 0 or mu_T >= 1:
        raise ValueError(
            f"Cannot fit Beta distribution: mu_T={mu_T:.6f}, var_T={var_T:.6f}. "
            "Mean must be in (0, 1) and variance must be positive."
        )

    alpha_T, beta_T = fit_beta_from_moments(mu_T, var_T)

    # Compute credible intervals
    alpha_lower = (1 - ci_level) / 2
    alpha_upper = 1 - alpha_lower
    quantiles = beta_quantiles([alpha_lower, alpha_upper], alpha_T, beta_T)
    ci_lower = float(quantiles[0])
    ci_upper = float(quantiles[1])

    # Generate actual μ samples if requested (for visualization)
    # Instead of using conditional means, we sample actual θ values
    actual_mu_samples = None
    if generate_samples:
        actual_mu_samples = np.zeros(n_samples)
        for j in range(n_samples):
            alpha_j = alpha_samples[j]
            beta_j = beta_samples[j]

            # Posterior parameters for each θᵢ given this (αⱼ, βⱼ)
            alpha_post = alpha_j + x_subset
            beta_post = beta_j + (n_subset - x_subset)

            # Sample θᵢ from posterior Beta distributions and compute μ
            theta_samples = np.random.beta(alpha_post, beta_post)
            actual_mu_samples[j] = np.mean(theta_samples)

    return PosteriorResult(
        mu=mu_T,
        variance=var_T,
        alpha_fitted=alpha_T,
        beta_fitted=beta_T,
        ci_level=ci_level,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        samples=actual_mu_samples,
    )


def compute_scenario_posteriors_hierarchical_bayes(
    alpha_samples: np.ndarray,
    beta_samples: np.ndarray,
    data: BinomialData,
    weights: np.ndarray | None = None,
    ci_level: float = 0.95,
) -> list[PosteriorResult]:
    """Compute posterior distributions for individual scenario success rates.

    Given samples (or weighted samples) from the posterior of hyperparameters
    (α, β), computes the posterior distribution of θᵢ for each scenario i by:
    1. For each (αⱼ, βⱼ) sample, compute E[θᵢ | αⱼ, βⱼ, data] and Var[θᵢ | αⱼ, βⱼ, data]
    2. Average across samples: E[θᵢ] = E[E[θᵢ | α, β]] and apply Law of Total Variance
    3. Moment-match to Beta and compute credible intervals

    This approach properly accounts for uncertainty in the hyperparameters.

    Args:
        alpha_samples: Samples from posterior of α (shape: n_samples).
        beta_samples: Samples from posterior of β (shape: n_samples).
        data: Binomial data (success counts and trial counts).
        weights: Optional importance sampling weights (shape: n_samples).
                 If None, assumes uniform weights (standard MCMC samples).
        ci_level: Credible interval level (default: 0.95).

    Returns:
        List of PosteriorResult objects, one for each scenario, containing:
            - mu: Posterior mean E[θᵢ]
            - variance: Posterior variance
            - alpha_fitted: Fitted Beta distribution alpha parameter
            - beta_fitted: Fitted Beta distribution beta parameter
            - ci_lower: Lower bound of credible interval
            - ci_upper: Upper bound of credible interval

    Notes:
        The posterior for θᵢ is a mixture of Beta distributions:
            p(θᵢ | s, o) = Σⱼ wⱼ · Beta(θᵢ; αⱼ + sᵢ, βⱼ + oᵢ - sᵢ)

        We moment-match this mixture to a single Beta for summarization.

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> from proportions.inference.hierarchical_bayes import hierarchical_bayes
        >>>
        >>> data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))
        >>> result = hierarchical_bayes(data, return_samples=True)
        >>>
        >>> # Compute individual scenario posteriors
        >>> scenario_posteriors = compute_scenario_posteriors_hierarchical_bayes(
        ...     result.alpha_samples,
        ...     result.beta_samples,
        ...     data,
        ...     result.importance_weights
        ... )
        >>>
        >>> print(f"Scenario 1: E[θ₁] = {scenario_posteriors[0].mu:.3f}, "
        ...       f"95% CI = [{scenario_posteriors[0].ci_lower:.3f}, {scenario_posteriors[0].ci_upper:.3f}]")
        >>> print(f"Scenario 2: E[θ₂] = {scenario_posteriors[1].mu:.3f}, "
        ...       f"95% CI = [{scenario_posteriors[1].ci_lower:.3f}, {scenario_posteriors[1].ci_upper:.3f}]")
    """
    n_samples = len(alpha_samples)
    if len(beta_samples) != n_samples:
        raise ValueError(
            f"Length mismatch: alpha_samples has {n_samples} elements, "
            f"beta_samples has {len(beta_samples)} elements"
        )

    # Set up weights (uniform if not provided)
    if weights is None:
        weights = np.ones(n_samples) / n_samples
    else:
        if len(weights) != n_samples:
            raise ValueError(
                f"Length mismatch: weights has {len(weights)} elements, "
                f"expected {n_samples}"
            )
        # Ensure weights are normalized
        weights = weights / np.sum(weights)

    n_scenarios = data.n_groups
    scenario_posteriors = []

    # For each scenario, compute posterior moments
    for i in range(n_scenarios):
        s_i = data.x[i]
        o_i = data.n[i]

        # For each (αⱼ, βⱼ) sample, compute moments of θᵢ | αⱼ, βⱼ, data
        mean_theta_samples = np.zeros(n_samples)
        var_theta_samples = np.zeros(n_samples)

        for j in range(n_samples):
            alpha_j = alpha_samples[j]
            beta_j = beta_samples[j]

            # Posterior parameters: θᵢ | αⱼ, βⱼ, data ~ Beta(αⱼ + sᵢ, βⱼ + oᵢ - sᵢ)
            alpha_post = alpha_j + s_i
            beta_post = beta_j + (o_i - s_i)

            # Moments of θᵢ | αⱼ, βⱼ, data
            mean_theta_samples[j] = alpha_post / (alpha_post + beta_post)
            var_theta_samples[j] = (alpha_post * beta_post) / (
                (alpha_post + beta_post) ** 2 * (alpha_post + beta_post + 1.0)
            )

        # Weighted average across all (α, β) samples (Law of Total Variance)
        mean_theta = float(np.sum(weights * mean_theta_samples))  # E[E[θᵢ | α, β]]

        # Var[θᵢ] = E[Var[θᵢ | α, β]] + Var[E[θᵢ | α, β]]
        var_within = float(np.sum(weights * var_theta_samples))  # E[Var[θᵢ | α, β]]
        var_between = float(
            np.sum(weights * (mean_theta_samples - mean_theta) ** 2)
        )  # Var[E[θᵢ | α, β]]
        var_theta = var_within + var_between

        # Moment-match to Beta distribution
        if var_theta <= 0 or mean_theta <= 0 or mean_theta >= 1:
            raise ValueError(
                f"Cannot fit Beta distribution for scenario {i}: "
                f"mean={mean_theta:.6f}, var={var_theta:.6f}. "
                "Mean must be in (0, 1) and variance must be positive."
            )

        alpha_fitted, beta_fitted = fit_beta_from_moments(mean_theta, var_theta)

        # Compute credible intervals
        alpha_lower = (1 - ci_level) / 2
        alpha_upper = 1 - alpha_lower
        quantiles = beta_quantiles([alpha_lower, alpha_upper], alpha_fitted, beta_fitted)
        ci_lower = float(quantiles[0])
        ci_upper = float(quantiles[1])

        # Store result for this scenario
        scenario_posteriors.append(
            PosteriorResult(
                mu=mean_theta,
                variance=var_theta,
                alpha_fitted=alpha_fitted,
                beta_fitted=beta_fitted,
                ci_level=ci_level,
                ci_lower=ci_lower,
                ci_upper=ci_upper,
            )
        )

    return scenario_posteriors
