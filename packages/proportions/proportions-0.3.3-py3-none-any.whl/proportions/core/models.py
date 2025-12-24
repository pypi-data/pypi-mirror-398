"""Core data models for the proportions library.

This module defines Pydantic models for all data structures used throughout
the library, ensuring type safety and automatic validation.
"""

from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field, model_validator


class BinomialData(BaseModel):
    """Input data for Beta-Binomial analysis.

    Attributes:
        x: Success counts per group (must be non-negative integers).
        n: Trial counts per group (must be positive integers).

    Validation:
        - Arrays must be non-empty and same length
        - n > 0 for all groups
        - x >= 0 for all groups
        - x <= n for all groups

    Example:
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> print(f"{data.n_groups} groups, {data.n_total_trials} total trials")
        3 groups, 30 total trials
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    x: np.ndarray = Field(..., description="Success counts per group")
    n: np.ndarray = Field(..., description="Trial counts per group")

    @field_validator('x', 'n')
    @classmethod
    def validate_array_non_empty(cls, v: np.ndarray) -> np.ndarray:
        """Validate that arrays are non-empty."""
        if len(v) == 0:
            raise ValueError("Arrays must be non-empty")
        return v

    @field_validator('n')
    @classmethod
    def validate_n_positive(cls, v: np.ndarray) -> np.ndarray:
        """Validate that all trial counts are positive."""
        if np.any(v <= 0):
            raise ValueError("All trial counts (n) must be positive")
        return v

    @field_validator('x')
    @classmethod
    def validate_x_non_negative(cls, v: np.ndarray) -> np.ndarray:
        """Validate that all success counts are non-negative."""
        if np.any(v < 0):
            raise ValueError("All success counts (x) must be non-negative")
        return v

    def model_post_init(self, __context) -> None:
        """Additional validation after model initialization."""
        if len(self.x) != len(self.n):
            raise ValueError(
                f"x and n must have same length, got {len(self.x)} and {len(self.n)}"
            )
        if np.any(self.x > self.n):
            raise ValueError("Success counts (x) cannot exceed trial counts (n)")

    @computed_field
    @property
    def n_groups(self) -> int:
        """Number of groups."""
        return len(self.x)

    @computed_field
    @property
    def n_total_trials(self) -> int:
        """Total number of trials across all groups."""
        return int(np.sum(self.n))

    @computed_field
    @property
    def n_total_successes(self) -> int:
        """Total number of successes across all groups."""
        return int(np.sum(self.x))

    @computed_field
    @property
    def pooled_rate(self) -> float:
        """Pooled success rate across all groups."""
        return float(self.n_total_successes / self.n_total_trials)

    @computed_field
    @property
    def observed_rates(self) -> np.ndarray:
        """Observed success rates per group."""
        return self.x / self.n


class PosteriorResult(BaseModel):
    """Result from posterior computation for T = average(θ).

    This represents the posterior distribution of the average success rate
    across all groups, approximated by a Beta distribution.

    Attributes:
        mu: Posterior mean of T (or point estimate for frequentist methods).
        variance: Posterior variance of T.
        std: Posterior standard deviation of T.
        alpha_fitted: Fitted Beta distribution alpha parameter (None for frequentist methods).
        beta_fitted: Fitted Beta distribution beta parameter (None for frequentist methods).
        ci_level: Credible/confidence interval level (default 0.95).
        ci_lower: Lower bound of credible/confidence interval.
        ci_upper: Upper bound of credible/confidence interval.
        samples: Optional array of samples used to compute the distribution (for visualization).

    Note:
        For frequentist methods (e.g., Clopper-Pearson), alpha_fitted and beta_fitted
        are None, as these methods don't produce posterior distributions.

    Example:
        >>> result = PosteriorResult(
        ...     mu=0.85, variance=0.0001, alpha_fitted=100, beta_fitted=20,
        ...     ci_lower=0.82, ci_upper=0.88
        ... )
        >>> print(f"T = {result.mu:.3f} [{result.ci_lower:.3f}, {result.ci_upper:.3f}]")
        T = 0.850 [0.820, 0.880]
    """

    model_config = {"arbitrary_types_allowed": True}

    mu: float = Field(..., ge=0.0, le=1.0, description="Posterior mean or point estimate")
    variance: float = Field(..., ge=0.0, description="Posterior variance")
    alpha_fitted: float | None = Field(default=None, gt=0.0, description="Fitted Beta alpha (None for frequentist)")
    beta_fitted: float | None = Field(default=None, gt=0.0, description="Fitted Beta beta (None for frequentist)")
    ci_level: float = Field(default=0.95, ge=0.0, le=1.0, description="Credible/confidence interval level")
    ci_lower: float = Field(..., ge=0.0, le=1.0, description="Lower CI bound")
    ci_upper: float = Field(..., ge=0.0, le=1.0, description="Upper CI bound")
    samples: np.ndarray | None = Field(default=None, exclude=True, description="Optional samples for visualization")

    @computed_field
    @property
    def std(self) -> float:
        """Posterior standard deviation."""
        return float(np.sqrt(self.variance))

    @computed_field
    @property
    def ci_width(self) -> float:
        """Width of credible interval."""
        return self.ci_upper - self.ci_lower

    def model_post_init(self, __context) -> None:
        """Additional validation after model initialization."""
        if self.ci_lower > self.ci_upper:
            raise ValueError(
                f"ci_lower ({self.ci_lower}) must be <= ci_upper ({self.ci_upper})"
            )
        if not (self.ci_lower <= self.mu <= self.ci_upper):
            raise ValueError(
                f"Mean {self.mu} must be within CI [{self.ci_lower}, {self.ci_upper}]"
            )


class EmpiricalBayesResult(BaseModel):
    """Results from Empirical Bayes analysis.

    Empirical Bayes estimates hyperparameters (α, β) from the data via
    maximum likelihood, then uses these fixed estimates for inference.

    Attributes:
        m_hat: Estimated mean parameter (α/(α+β)).
        k_hat: Estimated concentration parameter (α+β).
        alpha_hat: Estimated Beta prior alpha parameter.
        beta_hat: Estimated Beta prior beta parameter.
        log_marginal_likelihood: Log marginal likelihood at MLE.
        posterior: Posterior distribution for T = average(θ).
        n_groups: Number of groups in the data.
        n_total_trials: Total number of trials.
        n_total_successes: Total number of successes.
    """

    method: Literal['empirical_bayes'] = 'empirical_bayes'

    # Estimated hyperparameters
    m_hat: float = Field(..., ge=0.0, le=1.0, description="Estimated mean parameter")
    k_hat: float = Field(..., gt=0.0, description="Estimated concentration parameter")
    alpha_hat: float = Field(..., gt=0.0, description="Estimated alpha = m*k")
    beta_hat: float = Field(..., gt=0.0, description="Estimated beta = (1-m)*k")

    # Log marginal likelihood at MLE
    log_marginal_likelihood: float = Field(..., description="Log marginal likelihood")

    # Posterior for T
    posterior: PosteriorResult

    # Metadata
    n_groups: int = Field(..., gt=0)
    n_total_trials: int = Field(..., gt=0)
    n_total_successes: int = Field(..., ge=0)

    def model_post_init(self, __context) -> None:
        """Validate consistency of hyperparameters."""
        expected_alpha = self.m_hat * self.k_hat
        expected_beta = (1 - self.m_hat) * self.k_hat

        if not np.isclose(self.alpha_hat, expected_alpha, rtol=1e-4):
            raise ValueError(
                f"alpha_hat ({self.alpha_hat}) inconsistent with m_hat*k_hat ({expected_alpha})"
            )
        if not np.isclose(self.beta_hat, expected_beta, rtol=1e-4):
            raise ValueError(
                f"beta_hat ({self.beta_hat}) inconsistent with (1-m_hat)*k_hat ({expected_beta})"
            )


class SingleThetaResult(BaseModel):
    """Results from Single-Theta Bayesian analysis.

    Single-Theta assumes all groups share a common success rate θ,
    pooling all data for inference with a specified prior.

    Attributes:
        posterior: Posterior distribution for θ (= T in this case).
        log_marginal_likelihood: Log marginal likelihood (evidence).
        prior_alpha: Prior alpha parameter used.
        prior_beta: Prior beta parameter used.
        n_groups: Number of groups in the data.
        n_total_trials: Total number of trials.
        n_total_successes: Total number of successes.
    """

    method: Literal['single_theta'] = 'single_theta'

    # Prior hyperparameters used
    prior_alpha: float = Field(..., gt=0.0, description="Prior alpha parameter")
    prior_beta: float = Field(..., gt=0.0, description="Prior beta parameter")

    # Log marginal likelihood
    log_marginal_likelihood: float = Field(..., description="Log marginal likelihood")

    # Posterior for θ (= T)
    posterior: PosteriorResult

    # Metadata
    n_groups: int = Field(..., gt=0)
    n_total_trials: int = Field(..., gt=0)
    n_total_successes: int = Field(..., ge=0)


class UncoupledThetasResult(BaseModel):
    """Results from Uncoupled Thetas Bayesian analysis.

    Uncoupled Thetas treats each scenario's θᵢ independently with the same prior.
    No information sharing between scenarios (no shrinkage/pooling).

    Model:
        θᵢ ~ Beta(α_prior, β_prior)  for i = 1, ..., K (independent)
        xᵢ ~ Binomial(nᵢ, θᵢ)
        θᵢ | xᵢ ~ Beta(α_prior + xᵢ, β_prior + nᵢ - xᵢ)

    Attributes:
        scenario_posteriors: Independent posterior for each scenario's θᵢ.
        mu_samples: MC samples from posterior of μ = (1/K)Σθᵢ (average rate).
        aggregate_posterior: Beta-fitted posterior for μ (for compatibility).
        log_marginal_likelihood: Log marginal likelihood (evidence).
        prior_alpha: Prior alpha parameter used.
        prior_beta: Prior beta parameter used.
        n_scenarios: Number of scenarios in the data.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    method: Literal['uncoupled_thetas'] = 'uncoupled_thetas'

    # Prior hyperparameters used
    prior_alpha: float = Field(..., gt=0.0, description="Prior alpha parameter")
    prior_beta: float = Field(..., gt=0.0, description="Prior beta parameter")

    # Independent posteriors for each scenario
    scenario_posteriors: list[PosteriorResult] = Field(
        ..., description="Independent posterior for each scenario"
    )

    # Aggregate posterior for μ = (1/K)Σθᵢ
    mu_samples: np.ndarray | None = Field(
        default=None, description="MC samples from posterior of μ"
    )
    aggregate_posterior: PosteriorResult = Field(
        ..., description="Beta-fitted posterior for μ"
    )

    # Log marginal likelihood
    log_marginal_likelihood: float = Field(..., description="Log marginal likelihood")

    # Metadata
    n_scenarios: int = Field(..., gt=0)


class ImportanceSamplingDiagnostics(BaseModel):
    """Diagnostics from importance sampling for Hierarchical Bayes.

    These diagnostics help assess the quality of the importance sampling
    approximation and detect potential issues with prior specification.

    Attributes:
        n_samples: Number of samples drawn from the prior.
        effective_sample_size: Effective sample size (1 / Σw²).
        ess_ratio: ESS / n_samples (should be > 0.01 ideally).
        k_mean: Posterior mean of concentration parameter k.
        k_std: Posterior standard deviation of k.
        k_q05: 5th percentile of k posterior.
        k_q95: 95th percentile of k posterior.
        k_at_boundary: True if k posterior is near prior boundaries.
        k_at_lower: True if k is near lower boundary.
        k_at_upper: True if k is near upper boundary.
        m_mean: Posterior mean of m parameter.
        m_std: Posterior standard deviation of m.
        m_q05: 5th percentile of m posterior.
        m_q95: 95th percentile of m posterior.
    """

    n_samples: int = Field(..., gt=0)
    effective_sample_size: float = Field(..., gt=0.0)

    # k diagnostics
    k_mean: float = Field(..., gt=0.0)
    k_std: float = Field(..., ge=0.0)
    k_q05: float = Field(..., gt=0.0)
    k_q95: float = Field(..., gt=0.0)
    k_at_boundary: bool
    k_at_lower: bool
    k_at_upper: bool

    # m diagnostics
    m_mean: float = Field(..., ge=0.0, le=1.0)
    m_std: float = Field(..., ge=0.0)
    m_q05: float = Field(..., ge=0.0, le=1.0)
    m_q95: float = Field(..., ge=0.0, le=1.0)

    @computed_field
    @property
    def ess_ratio(self) -> float:
        """Ratio of effective sample size to total samples."""
        return self.effective_sample_size / self.n_samples


class HierarchicalBayesResult(BaseModel):
    """Results from Hierarchical Bayes analysis.

    Hierarchical Bayes treats hyperparameters (α, β) as random variables
    with their own prior distributions, fully accounting for uncertainty.

    Attributes:
        m_posterior_mean: Posterior mean of m = α/(α+β).
        k_posterior_mean: Posterior mean of k = α+β.
        alpha_posterior_mean: Posterior mean of α.
        beta_posterior_mean: Posterior mean of β.
        posterior: Posterior distribution for T = average(θ).
        variance_within: E[Var[T | α, β]] - data uncertainty.
        variance_between: Var[E[T | α, β]] - hyperparameter uncertainty.
        diagnostics: Importance sampling diagnostics.
        log_marginal_likelihood: Log marginal likelihood (evidence).
        n_groups: Number of groups in the data.
        n_total_trials: Total number of trials.
        n_total_successes: Total number of successes.
        alpha_samples: Optional array of α samples from hyperprior (for prior computation).
        beta_samples: Optional array of β samples from hyperprior (for prior computation).
    """

    model_config = {"arbitrary_types_allowed": True}

    method: Literal['hierarchical_bayes'] = 'hierarchical_bayes'

    # Posterior estimates for hyperparameters
    m_posterior_mean: float = Field(..., ge=0.0, le=1.0)
    k_posterior_mean: float = Field(..., gt=0.0)
    alpha_posterior_mean: float = Field(..., gt=0.0)
    beta_posterior_mean: float = Field(..., gt=0.0)

    # Posterior for T
    posterior: PosteriorResult

    # Variance decomposition
    variance_within: float = Field(..., ge=0.0, description="E[Var[T | α, β]]")
    variance_between: float = Field(..., ge=0.0, description="Var[E[T | α, β]]")

    # Diagnostics
    diagnostics: ImportanceSamplingDiagnostics

    # Log marginal likelihood (evidence)
    log_marginal_likelihood: float

    # Metadata
    n_groups: int = Field(..., gt=0)
    n_total_trials: int = Field(..., gt=0)
    n_total_successes: int = Field(..., ge=0)

    # Optional: hyperparameter samples (for computing prior)
    alpha_samples: np.ndarray | None = Field(default=None, exclude=True)
    beta_samples: np.ndarray | None = Field(default=None, exclude=True)
    importance_weights: np.ndarray | None = Field(default=None, exclude=True)

    def model_post_init(self, __context) -> None:
        """Validate consistency and variance decomposition."""
        expected_alpha = self.m_posterior_mean * self.k_posterior_mean
        expected_beta = (1 - self.m_posterior_mean) * self.k_posterior_mean

        if not np.isclose(self.alpha_posterior_mean, expected_alpha, rtol=1e-4):
            raise ValueError(
                f"alpha inconsistent with m*k: {self.alpha_posterior_mean} vs {expected_alpha}"
            )
        if not np.isclose(self.beta_posterior_mean, expected_beta, rtol=1e-4):
            raise ValueError(
                f"beta inconsistent with (1-m)*k: {self.beta_posterior_mean} vs {expected_beta}"
            )

        # Verify law of total variance
        total_var = self.variance_within + self.variance_between
        if not np.isclose(total_var, self.posterior.variance, rtol=1e-4):
            raise ValueError(
                f"Variance decomposition doesn't match: "
                f"within ({self.variance_within}) + between ({self.variance_between}) "
                f"= {total_var} != posterior variance ({self.posterior.variance})"
            )


class ConditionalPosteriorResult(BaseModel):
    """Result from conditional inference given k/k successes filter.

    This model contains results from estimating E[θ_B^m | k/k successes on task A],
    addressing the winner's curse / selection bias problem.

    The result represents the posterior distribution of the weighted average:
        μ = (Σ θ_A_i^k · θ_B_i^m) / (Σ θ_A_i^k)

    where θ_A_i is the success probability on Task A for scenario i,
    and θ_B_i is the success probability on Task B for scenario i.

    Attributes:
        mean: Posterior mean of the conditional expectation.
        median: Posterior median.
        mode: Posterior mode (None if Beta fitting failed).
        std: Posterior standard deviation.
        ci_level: Credible interval confidence level.
        ci_lower: Lower bound of credible interval.
        ci_upper: Upper bound of credible interval.
        samples: Monte Carlo samples of μ.
        n_samples: Number of MC samples.
        fitted_beta: Whether Beta distribution was successfully fitted.
        alpha_fitted: Alpha parameter of fitted Beta (None if fitting failed).
        beta_fitted: Beta parameter of fitted Beta (None if fitting failed).
        k: Filter criterion (k successes out of k trials on Task A).
        m: Success metric (m successes out of m trials on Task B).
        n_scenarios: Number of scenarios.
        scenario_weights: Expected weights for each scenario (for visualization).

    Example:
        >>> # Self-conditional: E[θ_A^m | k/k successes on Task A]
        >>> result = conditional_inference_k_out_of_k(
        ...     alpha_task_a=alphas,
        ...     beta_task_a=betas,
        ...     k=10,
        ...     m=1
        ... )
        >>> print(f"E[θ_A | 10/10 successes]: {result.mean:.4f}")
        >>> print(f"95% CI: [{result.ci_lower:.4f}, {result.ci_upper:.4f}]")
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Basic statistics
    mean: float = Field(..., description="Posterior mean")
    median: float = Field(..., description="Posterior median")
    mode: float | None = Field(None, description="Posterior mode (None if fitting failed)")
    std: float = Field(..., description="Posterior standard deviation")

    # Credible intervals
    ci_level: float = Field(..., description="Credible interval level", ge=0.0, le=1.0)
    ci_lower: float = Field(..., description="Lower bound of credible interval")
    ci_upper: float = Field(..., description="Upper bound of credible interval")

    # Monte Carlo samples
    samples: np.ndarray = Field(..., description="MC samples of μ")
    n_samples: int = Field(..., description="Number of MC samples", gt=0)

    # Fitted Beta distribution
    fitted_beta: bool = Field(..., description="Whether Beta was successfully fitted")
    alpha_fitted: float | None = Field(None, description="Alpha of fitted Beta", gt=0)
    beta_fitted: float | None = Field(None, description="Beta of fitted Beta", gt=0)

    # Filter info
    k: float = Field(..., description="Filter criterion exponent (typically k/k successes on Task A)", gt=0)
    m: float = Field(..., description="Success metric exponent (typically m/m successes on Task B)", gt=0)
    n_scenarios: int = Field(..., description="Number of scenarios", gt=0)

    # Expected weights (for visualization)
    scenario_weights: np.ndarray = Field(..., description="Expected weights per scenario")

    @field_validator('samples')
    @classmethod
    def validate_samples_length(cls, v: np.ndarray, info) -> np.ndarray:
        """Validate samples array has correct length."""
        n_samples = info.data.get('n_samples')
        if n_samples is not None and len(v) != n_samples:
            raise ValueError(f"samples length {len(v)} != n_samples {n_samples}")
        return v

    @field_validator('scenario_weights')
    @classmethod
    def validate_weights_length(cls, v: np.ndarray, info) -> np.ndarray:
        """Validate weights array has correct length."""
        n_scenarios = info.data.get('n_scenarios')
        if n_scenarios is not None and len(v) != n_scenarios:
            raise ValueError(f"weights length {len(v)} != n_scenarios {n_scenarios}")
        return v

    @field_validator('scenario_weights')
    @classmethod
    def validate_weights_sum(cls, v: np.ndarray) -> np.ndarray:
        """Validate that weights sum to 1."""
        if not np.isclose(v.sum(), 1.0, rtol=1e-6):
            raise ValueError(f"Weights must sum to 1, got {v.sum()}")
        return v


class ThetaPosterior(BaseModel):
    """Distribution p(θ) or p(θ | data) for a new scenario.

    Represents the prior p(θ) or posterior p(θ | data) distribution of θ
    for a hypothetical new scenario, obtained by marginalizing over the
    hyperparameter distribution p(α, β) or p(α, β | data).

    For prior: p(θ) = ∫∫ Beta(θ; α, β) p(α, β) dα dβ
    For posterior: p(θ | data) = ∫∫ Beta(θ; α, β) p(α, β | data) dα dβ

    Attributes:
        theta_grid: Grid of θ values where density is evaluated
        density: Average density p(θ) across resampled (α, β) pairs
        individual_densities: Individual Beta(θ; α_i, β_i) densities for each resample
        alpha_resampled: Resampled α values from p(α, β) or p(α, β | data)
        beta_resampled: Resampled β values from p(α, β) or p(α, β | data)
        n_resample: Number of (α, β) pairs resampled

    Example:
        >>> # After hierarchical_bayes with return_samples=True
        >>> theta_post = compute_theta_posterior(
        ...     result.alpha_samples, result.beta_samples, result.importance_weights
        ... )
        >>> print(f"θ grid: {len(theta_post.theta_grid)} points")
        >>> print(f"Density shape: {theta_post.density.shape}")
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    theta_grid: np.ndarray = Field(..., description="Grid of θ values")
    density: np.ndarray = Field(..., description="Average density p(θ) across resamples")
    individual_densities: np.ndarray = Field(..., description="(n_resample, n_grid) individual Beta densities")
    alpha_resampled: np.ndarray = Field(..., description="Resampled α values")
    beta_resampled: np.ndarray = Field(..., description="Resampled β values")
    n_resample: int = Field(..., description="Number of (α, β) resamples", gt=0)

    @field_validator('theta_grid')
    @classmethod
    def validate_theta_grid(cls, v: np.ndarray) -> np.ndarray:
        """Validate theta grid is non-empty and in [0, 1]."""
        if len(v) == 0:
            raise ValueError("theta_grid must be non-empty")
        if np.any(v < 0) or np.any(v > 1):
            raise ValueError("theta_grid values must be in [0, 1]")
        return v

    @field_validator('density')
    @classmethod
    def validate_density(cls, v: np.ndarray, info) -> np.ndarray:
        """Validate density has correct shape."""
        theta_grid = info.data.get('theta_grid')
        if theta_grid is not None and len(v) != len(theta_grid):
            raise ValueError(f"density length {len(v)} != theta_grid length {len(theta_grid)}")
        if np.any(v < 0):
            raise ValueError("density values must be non-negative")
        return v

    @field_validator('individual_densities')
    @classmethod
    def validate_individual_densities(cls, v: np.ndarray) -> np.ndarray:
        """Validate individual densities are non-negative."""
        if np.any(v < 0):
            raise ValueError("individual_densities values must be non-negative")
        return v

    @model_validator(mode='after')
    def validate_shapes(self) -> 'ThetaPosterior':
        """Validate that all shapes are consistent."""
        expected_shape = (self.n_resample, len(self.theta_grid))
        if self.individual_densities.shape != expected_shape:
            raise ValueError(
                f"individual_densities shape {self.individual_densities.shape} != expected {expected_shape}"
            )
        return self
