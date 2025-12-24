"""Uncoupled Thetas Bayesian inference for binomial data.

This module implements independent Bayesian inference for each scenario,
with no information sharing between scenarios (no hierarchical structure).
"""

import numpy as np

from proportions.core.models import BinomialData, UncoupledThetasResult, PosteriorResult
from proportions.distributions.beta import beta_quantiles, log_beta
from proportions.aggregation.moment_matching import fit_beta_from_moments


def uncoupled_thetas(
    data: BinomialData,
    alpha_prior: float = 1.0,
    beta_prior: float = 1.0,
    ci_level: float = 0.95,
    n_mu_samples: int = 100000,
    random_seed: int | None = None,
) -> UncoupledThetasResult:
    """Perform independent Bayesian inference for each scenario.

    This approach treats each scenario's θᵢ independently with the same prior.
    No information sharing or shrinkage across scenarios - each posterior is
    computed using only that scenario's data.

    Model:
        θᵢ ~ Beta(α_prior, β_prior)  for i = 1, ..., K (independent)
        xᵢ ~ Binomial(nᵢ, θᵢ)
        θᵢ | xᵢ ~ Beta(α_prior + xᵢ, β_prior + nᵢ - xᵢ)

    Aggregate μ = (1/K)Σθᵢ:
        - Computed via Monte Carlo sampling from independent posteriors
        - Beta distribution fitted to samples for visualization compatibility

    This approach is appropriate when:
    - Scenarios are believed to be heterogeneous (different underlying rates)
    - You want to avoid any pooling/shrinkage across scenarios
    - You have sufficient data per scenario for reliable individual estimates
    - You want a baseline without hierarchical structure

    Args:
        data: Binomial data (success and trial counts per scenario).
        alpha_prior: Prior alpha parameter for Beta(α, β) on each θᵢ (default: 1.0).
        beta_prior: Prior beta parameter for Beta(α, β) on each θᵢ (default: 1.0).
        ci_level: Credible interval level (default: 0.95).
        n_mu_samples: Number of MC samples for μ = (1/K)Σθᵢ distribution (default: 100000).
        random_seed: Random seed for reproducibility (default: None).

    Returns:
        UncoupledThetasResult with:
            - scenario_posteriors: Independent posterior for each scenario
            - mu_samples: MC samples from posterior of μ = (1/K)Σθᵢ
            - aggregate_posterior: Beta-fitted posterior for μ
            - log_marginal_likelihood: Log evidence (product of independent marginals)

    Raises:
        ValueError: If alpha_prior or beta_prior are not positive.

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> from proportions.inference import uncoupled_thetas
        >>>
        >>> # Bimodal data
        >>> data = BinomialData(x=np.array([90, 10]), n=np.array([100, 100]))
        >>>
        >>> # Uncoupled inference (no shrinkage)
        >>> result = uncoupled_thetas(data, alpha_prior=1.0, beta_prior=1.0)
        >>> print(f"Scenario 1: θ₁ = {result.scenario_posteriors[0].mu:.3f}")
        >>> print(f"Scenario 2: θ₂ = {result.scenario_posteriors[1].mu:.3f}")
        >>> print(f"Aggregate: μ = {result.aggregate_posterior.mu:.3f}")
    """
    if alpha_prior <= 0:
        raise ValueError(f"alpha_prior must be positive, got {alpha_prior}")
    if beta_prior <= 0:
        raise ValueError(f"beta_prior must be positive, got {beta_prior}")

    # Set random seed if provided
    if random_seed is not None:
        np.random.seed(random_seed)

    n_scenarios = data.n_groups
    scenario_posteriors = []
    log_evidence = 0.0

    # Compute independent posterior for each scenario
    for i in range(n_scenarios):
        x_i = data.x[i]
        n_i = data.n[i]

        # Beta-Binomial conjugate update
        alpha_post = alpha_prior + x_i
        beta_post = beta_prior + (n_i - x_i)

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
        scenario_posteriors.append(posterior)

        # Add to log evidence (product of independent marginals)
        log_evidence += log_beta(alpha_post, beta_post) - log_beta(alpha_prior, beta_prior)

    # Compute posterior of μ = (1/K)Σθᵢ via Monte Carlo
    # Sample from each independent posterior and average
    theta_samples = np.zeros((n_mu_samples, n_scenarios))
    for i in range(n_scenarios):
        alpha_post = scenario_posteriors[i].alpha_fitted
        beta_post = scenario_posteriors[i].beta_fitted
        theta_samples[:, i] = np.random.beta(alpha_post, beta_post, size=n_mu_samples)

    # Compute μ = average of θᵢ samples
    mu_samples = theta_samples.mean(axis=1)

    # Fit Beta to μ samples for compatibility with visualization functions
    mu_mean = mu_samples.mean()
    mu_variance = mu_samples.var()

    # Fit Beta using moment matching
    try:
        alpha_mu, beta_mu = fit_beta_from_moments(mu_mean, mu_variance)
    except ValueError:
        # Fallback: if moment matching fails, use empirical quantiles
        alpha_lower = (1 - ci_level) / 2
        alpha_upper = 1 - alpha_lower
        ci_lower_mu = float(np.quantile(mu_samples, alpha_lower))
        ci_upper_mu = float(np.quantile(mu_samples, alpha_upper))

        # Create aggregate posterior with empirical values
        aggregate_posterior = PosteriorResult(
            mu=float(mu_mean),
            variance=float(mu_variance),
            alpha_fitted=1.0,  # Placeholder
            beta_fitted=1.0,  # Placeholder
            ci_level=ci_level,
            ci_lower=ci_lower_mu,
            ci_upper=ci_upper_mu,
        )
    else:
        # Compute CI using fitted Beta
        quantiles_mu = beta_quantiles([alpha_lower, alpha_upper], alpha_mu, beta_mu)
        ci_lower_mu = float(quantiles_mu[0])
        ci_upper_mu = float(quantiles_mu[1])

        aggregate_posterior = PosteriorResult(
            mu=float(mu_mean),
            variance=float(mu_variance),
            alpha_fitted=float(alpha_mu),
            beta_fitted=float(beta_mu),
            ci_level=ci_level,
            ci_lower=ci_lower_mu,
            ci_upper=ci_upper_mu,
        )

    return UncoupledThetasResult(
        prior_alpha=float(alpha_prior),
        prior_beta=float(beta_prior),
        scenario_posteriors=scenario_posteriors,
        mu_samples=mu_samples,
        aggregate_posterior=aggregate_posterior,
        log_marginal_likelihood=float(log_evidence),
        n_scenarios=n_scenarios,
    )
