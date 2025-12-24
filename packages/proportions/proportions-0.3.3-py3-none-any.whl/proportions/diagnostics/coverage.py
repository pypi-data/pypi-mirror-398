"""Monte Carlo coverage diagnostics for inference methods.

This module provides tools to evaluate the frequentist coverage properties
of Bayesian and frequentist inference methods under known ground truth.
"""

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal

from proportions.core.models import BinomialData
from proportions.inference.empirical_bayes import empirical_bayes
from proportions.inference.hierarchical_bayes import hierarchical_bayes
from proportions.inference.single_theta import single_theta_bayesian
from proportions.inference.clopper_pearson import clopper_pearson


class CoverageSimulationConfig(BaseModel):
    """Configuration for Monte Carlo coverage simulation.

    Can specify the true distribution in two ways:
    1. Directly via (alpha, beta) parameters
    2. Via (m, k) parameterization where alpha = m*k, beta = (1-m)*k

    Attributes:
        true_alpha: True α parameter for Beta(α, β) distribution (optional if m, k provided)
        true_beta: True β parameter for Beta(α, β) distribution (optional if m, k provided)
        true_m: True mean parameter m ∈ (0, 1) (optional if alpha, beta provided)
        true_k: True concentration parameter k > 0 (optional if alpha, beta provided)
        n_groups: Number of groups to generate
        n_samples_min: Minimum number of samples per group (ignored if fixed_n provided)
        n_samples_max: Maximum number of samples per group (ignored if fixed_n provided)
        fixed_n: Fixed sample sizes for each group (optional, if provided overrides min/max)
        n_simulations: Number of Monte Carlo simulations to run
        ci_level: Confidence/credible interval level (default: 0.95)
        random_seed: Random seed for reproducibility (optional)
    """
    # Option 1: Specify via (alpha, beta)
    true_alpha: float | None = Field(default=None, gt=0)
    true_beta: float | None = Field(default=None, gt=0)

    # Option 2: Specify via (m, k)
    true_m: float | None = Field(default=None, gt=0, lt=1)
    true_k: float | None = Field(default=None, gt=0)

    # Required parameters
    n_groups: int = Field(gt=0)
    n_samples_min: int | None = Field(default=None, gt=0)
    n_samples_max: int | None = Field(default=None, gt=0)

    # Optional: fixed sample sizes
    fixed_n: np.ndarray | list | None = Field(default=None)

    n_simulations: int = Field(gt=0)
    ci_level: float = Field(default=0.95, gt=0, lt=1)
    random_seed: int | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator('n_samples_max')
    @classmethod
    def check_sample_bounds(cls, v: int | None, info) -> int | None:
        """Validate that n_samples_max >= n_samples_min."""
        if v is None:
            return None
        n_min = info.data.get('n_samples_min')
        if n_min is not None and v < n_min:
            raise ValueError("n_samples_max must be >= n_samples_min")
        return v

    @field_validator('fixed_n')
    @classmethod
    def check_fixed_n(cls, v, info) -> np.ndarray | None:
        """Validate fixed_n array."""
        if v is None:
            return None
        arr = np.asarray(v)
        if 'n_groups' in info.data and len(arr) != info.data['n_groups']:
            raise ValueError(f"fixed_n length ({len(arr)}) must match n_groups ({info.data['n_groups']})")
        if np.any(arr <= 0):
            raise ValueError("All values in fixed_n must be positive")
        return arr

    def model_post_init(self, __context) -> None:
        """Validate that exactly one parameterization is provided."""
        has_alpha_beta = self.true_alpha is not None and self.true_beta is not None
        has_m_k = self.true_m is not None and self.true_k is not None

        if not has_alpha_beta and not has_m_k:
            raise ValueError(
                "Must specify either (true_alpha, true_beta) or (true_m, true_k)"
            )

        if has_alpha_beta and has_m_k:
            raise ValueError(
                "Cannot specify both (true_alpha, true_beta) and (true_m, true_k). "
                "Use only one parameterization."
            )

        # Check that either fixed_n or (min, max) is provided
        if self.fixed_n is None:
            if self.n_samples_min is None or self.n_samples_max is None:
                raise ValueError(
                    "Must provide either fixed_n or both n_samples_min and n_samples_max"
                )

    def get_alpha_beta(self) -> tuple[float, float]:
        """Get (alpha, beta) parameters, computing from (m, k) if needed.

        Returns:
            Tuple of (alpha, beta) parameters.
        """
        if self.true_alpha is not None and self.true_beta is not None:
            return self.true_alpha, self.true_beta
        else:
            # Compute from (m, k)
            assert self.true_m is not None and self.true_k is not None
            alpha = self.true_m * self.true_k
            beta = (1 - self.true_m) * self.true_k
            return alpha, beta

    def get_m_k(self) -> tuple[float, float]:
        """Get (m, k) parameters, computing from (alpha, beta) if needed.

        Returns:
            Tuple of (m, k) parameters.
        """
        if self.true_m is not None and self.true_k is not None:
            return self.true_m, self.true_k
        else:
            # Compute from (alpha, beta)
            assert self.true_alpha is not None and self.true_beta is not None
            k = self.true_alpha + self.true_beta
            m = self.true_alpha / k
            return m, k

    @property
    def true_T(self) -> float:
        """Compute true value of T = E[average(θ_i)]."""
        alpha, beta = self.get_alpha_beta()
        return alpha / (alpha + beta)


class CoverageMetrics(BaseModel):
    """Coverage metrics for a single inference method.

    Attributes:
        method_name: Name of the inference method
        empirical_coverage: Proportion of CIs containing true T
        coverage_se: Standard error of coverage proportion
        mean_ci_width: Mean width of confidence intervals
        rmse: Root mean squared error of point estimates
        mean_bias: Mean bias (T_hat - true_T)
    """
    method_name: str
    empirical_coverage: float
    coverage_se: float
    mean_ci_width: float
    rmse: float
    mean_bias: float


class CoverageSimulationResult(BaseModel):
    """Results from Monte Carlo coverage simulation.

    Attributes:
        config: Simulation configuration
        true_T: True value of T = E[average(θ)]
        metrics: Coverage metrics for each method
        n_simulations_completed: Number of simulations actually completed
    """
    config: CoverageSimulationConfig
    true_T: float
    metrics: dict[str, CoverageMetrics]
    n_simulations_completed: int

    def format_table(self) -> str:
        """Format results as ASCII table.

        Returns:
            Formatted table with coverage, width, RMSE, and bias for each method.
        """
        lines = []
        lines.append(f"\nCoverage Simulation Results")

        # Show both parameterizations
        alpha, beta = self.config.get_alpha_beta()
        m, k = self.config.get_m_k()
        lines.append(f"True parameters: α={alpha:.2f}, β={beta:.2f}  (m={m:.4f}, k={k:.2f})")
        lines.append(f"True T = {self.true_T:.4f}")
        lines.append(f"Simulations: {self.n_simulations_completed}")

        # Sample sizes info
        if self.config.fixed_n is not None:
            n_arr = self.config.fixed_n
            lines.append(f"Groups: {self.config.n_groups}, Samples: FIXED (min={n_arr.min():.0f}, max={n_arr.max():.0f}, mean={n_arr.mean():.1f})")
        else:
            lines.append(f"Groups: {self.config.n_groups}, Samples: [{self.config.n_samples_min}, {self.config.n_samples_max}]")

        lines.append(f"Nominal coverage: {self.config.ci_level:.2%}")
        lines.append("")

        # Header
        lines.append("Method               Coverage    Width(mean)    RMSE      Bias")
        lines.append("-" * 70)

        # Sort methods for consistent ordering
        method_order = ['empirical_bayes', 'hierarchical_bayes', 'single_theta', 'clopper_pearson']
        sorted_methods = sorted(
            self.metrics.items(),
            key=lambda x: method_order.index(x[0]) if x[0] in method_order else 999
        )

        for method_name, metrics in sorted_methods:
            # Format method name
            display_name = method_name.replace('_', ' ').title()

            # Coverage with indicator
            coverage_str = f"{metrics.empirical_coverage:.3f}"
            if abs(metrics.empirical_coverage - self.config.ci_level) > 0.02:
                coverage_str += "*"  # Flag if far from nominal

            line = (
                f"{display_name:20s} "
                f"{coverage_str:10s} "
                f"{metrics.mean_ci_width:10.4f}   "
                f"{metrics.rmse:8.4f}  "
                f"{metrics.mean_bias:+8.4f}"
            )
            lines.append(line)

        lines.append("")
        lines.append("* Coverage differs from nominal by >2%")

        return "\n".join(lines)


def generate_binomial_data(
    true_alpha: float,
    true_beta: float,
    n_groups: int,
    n_samples_min: int | None,
    n_samples_max: int | None,
    rng: np.random.Generator,
    fixed_n: np.ndarray | None = None
) -> BinomialData:
    """Generate binomial data from Beta-Binomial model.

    Args:
        true_alpha: True α parameter for Beta(α, β)
        true_beta: True β parameter for Beta(α, β)
        n_groups: Number of groups
        n_samples_min: Minimum samples per group (ignored if fixed_n provided)
        n_samples_max: Maximum samples per group (ignored if fixed_n provided)
        rng: NumPy random generator
        fixed_n: Optional fixed sample sizes for each group

    Returns:
        BinomialData with generated x and n arrays.
    """
    # Use fixed sample sizes or sample from uniform distribution
    if fixed_n is not None:
        n = fixed_n.copy()
    else:
        if n_samples_min is None or n_samples_max is None:
            raise ValueError("Must provide n_samples_min and n_samples_max if fixed_n is not provided")
        n = rng.integers(n_samples_min, n_samples_max + 1, size=n_groups)

    # Sample true rates from Beta(α, β)
    theta = rng.beta(true_alpha, true_beta, size=n_groups)

    # Sample successes from Binomial(n_i, θ_i)
    x = np.array([rng.binomial(n_i, theta_i) for n_i, theta_i in zip(n, theta)])

    return BinomialData(x=x, n=n)


def run_single_simulation(
    config: CoverageSimulationConfig,
    rng: np.random.Generator
) -> dict[str, dict[str, float]]:
    """Run a single simulation and collect results from all methods.

    Args:
        config: Simulation configuration
        rng: NumPy random generator

    Returns:
        Dictionary mapping method names to result dictionaries with keys:
        - 'ci_lower': Lower CI bound
        - 'ci_upper': Upper CI bound
        - 'T_hat': Point estimate
        - 'covered': Boolean indicating if true_T is in CI
        - 'ci_width': Width of CI
        - 'error': T_hat - true_T
    """
    # Get alpha, beta from config (handles both parameterizations)
    true_alpha, true_beta = config.get_alpha_beta()

    # Generate data
    data = generate_binomial_data(
        true_alpha,
        true_beta,
        config.n_groups,
        config.n_samples_min,
        config.n_samples_max,
        rng,
        fixed_n=config.fixed_n
    )

    true_T = config.true_T
    results = {}

    # Method 1: Empirical Bayes
    try:
        eb_result = empirical_bayes(data, ci_level=config.ci_level)
        results['empirical_bayes'] = {
            'ci_lower': eb_result.posterior.ci_lower,
            'ci_upper': eb_result.posterior.ci_upper,
            'T_hat': eb_result.posterior.mu,
            'covered': eb_result.posterior.ci_lower <= true_T <= eb_result.posterior.ci_upper,
            'ci_width': eb_result.posterior.ci_upper - eb_result.posterior.ci_lower,
            'error': eb_result.posterior.mu - true_T
        }
    except Exception:
        # Record failure as NaN
        results['empirical_bayes'] = {
            'ci_lower': np.nan, 'ci_upper': np.nan, 'T_hat': np.nan,
            'covered': False, 'ci_width': np.nan, 'error': np.nan
        }

    # Method 2: Hierarchical Bayes
    try:
        hb_result = hierarchical_bayes(data, ci_level=config.ci_level)
        results['hierarchical_bayes'] = {
            'ci_lower': hb_result.posterior.ci_lower,
            'ci_upper': hb_result.posterior.ci_upper,
            'T_hat': hb_result.posterior.mu,
            'covered': hb_result.posterior.ci_lower <= true_T <= hb_result.posterior.ci_upper,
            'ci_width': hb_result.posterior.ci_upper - hb_result.posterior.ci_lower,
            'error': hb_result.posterior.mu - true_T
        }
    except Exception:
        results['hierarchical_bayes'] = {
            'ci_lower': np.nan, 'ci_upper': np.nan, 'T_hat': np.nan,
            'covered': False, 'ci_width': np.nan, 'error': np.nan
        }

    # Method 3: Single-Theta (use weakly informative prior)
    try:
        st_result = single_theta_bayesian(
            data,
            alpha_prior=1.0,
            beta_prior=1.0,
            ci_level=config.ci_level
        )
        results['single_theta'] = {
            'ci_lower': st_result.posterior.ci_lower,
            'ci_upper': st_result.posterior.ci_upper,
            'T_hat': st_result.posterior.mu,
            'covered': st_result.posterior.ci_lower <= true_T <= st_result.posterior.ci_upper,
            'ci_width': st_result.posterior.ci_upper - st_result.posterior.ci_lower,
            'error': st_result.posterior.mu - true_T
        }
    except Exception:
        results['single_theta'] = {
            'ci_lower': np.nan, 'ci_upper': np.nan, 'T_hat': np.nan,
            'covered': False, 'ci_width': np.nan, 'error': np.nan
        }

    # Method 4: Clopper-Pearson
    try:
        cp_result = clopper_pearson(data, ci_level=config.ci_level)
        results['clopper_pearson'] = {
            'ci_lower': cp_result.ci_lower,
            'ci_upper': cp_result.ci_upper,
            'T_hat': cp_result.mu,
            'covered': cp_result.ci_lower <= true_T <= cp_result.ci_upper,
            'ci_width': cp_result.ci_upper - cp_result.ci_lower,
            'error': cp_result.mu - true_T
        }
    except Exception as e:
        # Debug: print exception
        import warnings
        warnings.warn(f"Clopper-Pearson failed: {type(e).__name__}: {e}")
        results['clopper_pearson'] = {
            'ci_lower': np.nan, 'ci_upper': np.nan, 'T_hat': np.nan,
            'covered': False, 'ci_width': np.nan, 'error': np.nan
        }

    return results


def run_coverage_simulation(
    config: CoverageSimulationConfig,
    verbose: bool = True
) -> CoverageSimulationResult:
    """Run Monte Carlo coverage simulation.

    Args:
        config: Simulation configuration
        verbose: If True, print progress (default: True)

    Returns:
        CoverageSimulationResult with aggregated metrics for all methods.
    """
    # Initialize random generator
    rng = np.random.default_rng(config.random_seed)

    # Storage for all simulation results
    all_results = {
        'empirical_bayes': [],
        'hierarchical_bayes': [],
        'single_theta': [],
        'clopper_pearson': []
    }

    # Run simulations
    if verbose:
        print(f"Running {config.n_simulations} simulations...")

    for i in range(config.n_simulations):
        # Show progress more frequently for smaller runs
        if verbose:
            if config.n_simulations <= 100:
                # For small runs, print every 10
                if (i + 1) % 10 == 0:
                    print(f"  Completed {i + 1}/{config.n_simulations}")
            else:
                # For large runs, print every 100
                if (i + 1) % 100 == 0:
                    print(f"  Completed {i + 1}/{config.n_simulations}")

        sim_results = run_single_simulation(config, rng)

        for method_name, method_result in sim_results.items():
            all_results[method_name].append(method_result)

    # Aggregate metrics for each method
    metrics = {}
    true_T = config.true_T

    for method_name, results_list in all_results.items():
        # Extract arrays (filtering out NaN values)
        covered = np.array([r['covered'] for r in results_list])
        widths = np.array([r['ci_width'] for r in results_list])
        errors = np.array([r['error'] for r in results_list])

        # Remove NaN values for metrics computation
        valid_mask = ~np.isnan(widths)
        widths_valid = widths[valid_mask]
        errors_valid = errors[valid_mask]

        # Compute metrics
        n_valid = np.sum(valid_mask)
        empirical_coverage = np.sum(covered) / len(covered)
        coverage_se = np.sqrt(empirical_coverage * (1 - empirical_coverage) / len(covered))
        mean_ci_width = np.mean(widths_valid) if n_valid > 0 else np.nan
        rmse = np.sqrt(np.mean(errors_valid ** 2)) if n_valid > 0 else np.nan
        mean_bias = np.mean(errors_valid) if n_valid > 0 else np.nan

        metrics[method_name] = CoverageMetrics(
            method_name=method_name,
            empirical_coverage=empirical_coverage,
            coverage_se=coverage_se,
            mean_ci_width=mean_ci_width,
            rmse=rmse,
            mean_bias=mean_bias
        )

    if verbose:
        print("Done!")

    return CoverageSimulationResult(
        config=config,
        true_T=true_T,
        metrics=metrics,
        n_simulations_completed=config.n_simulations
    )
