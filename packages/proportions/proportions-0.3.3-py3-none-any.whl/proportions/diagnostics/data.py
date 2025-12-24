"""Data quality diagnostics for binomial proportion analysis.

This module provides comprehensive data characterization, including:
- Summary statistics for sample sizes and success rates
- Heterogeneity assessment
- Variance ratio calculations
- Recommendations for appropriate models
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field

from proportions.core.models import BinomialData


class DataDiagnostics(BaseModel):
    """Comprehensive data diagnostics for binomial proportion data.

    Attributes:
        n_groups: Number of groups.
        n_total_trials: Total number of trials across all groups.
        n_total_successes: Total number of successes across all groups.
        pooled_rate: Overall pooled success rate.

        sample_size_min: Minimum sample size across groups.
        sample_size_max: Maximum sample size across groups.
        sample_size_mean: Mean sample size.
        sample_size_median: Median sample size.
        sample_size_std: Standard deviation of sample sizes.

        success_rate_mean: Mean of observed success rates.
        success_rate_std: Standard deviation of observed success rates.
        success_rate_min: Minimum observed success rate.
        success_rate_max: Maximum observed success rate.
        success_rate_median: Median observed success rate.

        heterogeneity_level: Classification of heterogeneity (low/moderate/high).
        variance_ratio: Ratio of observed variance to binomial variance.

        has_extreme_rates: True if any group has rate < 0.01 or > 0.99.
        has_small_samples: True if any group has n < 5.
        has_imbalanced_samples: True if max_n / min_n > 10.

        recommended_models: List of recommended models based on data characteristics.
        warnings: List of warnings about data quality issues.
    """

    # Basic counts
    n_groups: int = Field(..., gt=0)
    n_total_trials: int = Field(..., gt=0)
    n_total_successes: int = Field(..., ge=0)
    pooled_rate: float = Field(..., ge=0.0, le=1.0)

    # Sample size statistics
    sample_size_min: int = Field(..., gt=0)
    sample_size_max: int = Field(..., gt=0)
    sample_size_mean: float = Field(..., gt=0.0)
    sample_size_median: float = Field(..., gt=0.0)
    sample_size_std: float = Field(..., ge=0.0)

    # Success rate statistics
    success_rate_mean: float = Field(..., ge=0.0, le=1.0)
    success_rate_std: float = Field(..., ge=0.0)
    success_rate_min: float = Field(..., ge=0.0, le=1.0)
    success_rate_max: float = Field(..., ge=0.0, le=1.0)
    success_rate_median: float = Field(..., ge=0.0, le=1.0)

    # Heterogeneity assessment
    heterogeneity_level: Literal["low", "moderate", "high"]
    variance_ratio: float = Field(..., ge=0.0)

    # Quality flags
    has_extreme_rates: bool
    has_small_samples: bool
    has_imbalanced_samples: bool

    # Recommendations
    recommended_models: list[str]
    warnings: list[str]

    def format_report(self) -> str:
        """Format a human-readable diagnostic report.

        Returns:
            Formatted string with all diagnostic information.
        """
        lines = []
        lines.append("=" * 80)
        lines.append("DATA DIAGNOSTICS REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Basic statistics
        lines.append("BASIC STATISTICS:")
        lines.append(f"  Groups: {self.n_groups}")
        lines.append(f"  Total trials: {self.n_total_trials:,}")
        lines.append(f"  Total successes: {self.n_total_successes:,}")
        lines.append(f"  Pooled rate: {self.pooled_rate:.4f}")
        lines.append("")

        # Sample sizes
        lines.append("SAMPLE SIZE DISTRIBUTION:")
        lines.append(f"  Min: {self.sample_size_min}")
        lines.append(f"  Max: {self.sample_size_max}")
        lines.append(f"  Mean: {self.sample_size_mean:.1f}")
        lines.append(f"  Median: {self.sample_size_median:.1f}")
        lines.append(f"  Std: {self.sample_size_std:.1f}")
        lines.append("")

        # Success rates
        lines.append("SUCCESS RATE DISTRIBUTION:")
        lines.append(f"  Min: {self.success_rate_min:.4f}")
        lines.append(f"  Max: {self.success_rate_max:.4f}")
        lines.append(f"  Mean: {self.success_rate_mean:.4f}")
        lines.append(f"  Median: {self.success_rate_median:.4f}")
        lines.append(f"  Std: {self.success_rate_std:.4f}")
        lines.append("")

        # Heterogeneity
        lines.append("HETEROGENEITY ASSESSMENT:")
        lines.append(f"  Level: {self.heterogeneity_level.upper()}")
        lines.append(f"  Variance ratio: {self.variance_ratio:.2f}")
        lines.append(f"    (Observed variance / Binomial variance)")
        if self.variance_ratio > 2.0:
            lines.append(f"    → Overdispersion detected (ratio > 2)")
        elif self.variance_ratio < 0.5:
            lines.append(f"    → Underdispersion detected (ratio < 0.5)")
        else:
            lines.append(f"    → Variance consistent with binomial model")
        lines.append("")

        # Quality flags
        lines.append("DATA QUALITY FLAGS:")
        lines.append(f"  Extreme rates (< 0.01 or > 0.99): {self.has_extreme_rates}")
        lines.append(f"  Small samples (n < 5): {self.has_small_samples}")
        lines.append(f"  Imbalanced samples (max/min > 10): {self.has_imbalanced_samples}")
        lines.append("")

        # Warnings
        if self.warnings:
            lines.append("⚠ WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  • {warning}")
            lines.append("")

        # Recommendations
        lines.append("📊 RECOMMENDED MODELS:")
        for i, model in enumerate(self.recommended_models, 1):
            lines.append(f"  {i}. {model}")
        lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)


def compute_data_diagnostics(
    data: BinomialData,
    group_indices: list[int] | np.ndarray | None = None,
) -> DataDiagnostics:
    """Compute comprehensive diagnostics for binomial proportion data.

    Analyzes data quality, heterogeneity, and provides model recommendations
    based on data characteristics.

    Args:
        data: Binomial data (success and trial counts per group).
        group_indices: Optional list of group indices to analyze.
                       If None, analyzes all groups.

    Returns:
        DataDiagnostics with complete diagnostic information.

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> from proportions.diagnostics.data import compute_data_diagnostics
        >>>
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> diagnostics = compute_data_diagnostics(data)
        >>> print(diagnostics.format_report())
        >>> print(f"Heterogeneity: {diagnostics.heterogeneity_level}")
        >>> print(f"Recommended: {diagnostics.recommended_models}")
    """
    # Select subset if requested
    if group_indices is not None:
        group_indices_arr = np.asarray(group_indices, dtype=int)
        if len(group_indices_arr) == 0:
            raise ValueError("group_indices cannot be empty")
        if np.any(group_indices_arr < 0) or np.any(group_indices_arr >= data.n_groups):
            raise ValueError(
                f"group_indices must be in range [0, {data.n_groups-1}]"
            )
        x_subset = data.x[group_indices_arr]
        n_subset = data.n[group_indices_arr]
    else:
        x_subset = data.x
        n_subset = data.n

    # Basic counts
    n_groups = len(x_subset)
    n_total_trials = int(np.sum(n_subset))
    n_total_successes = int(np.sum(x_subset))
    pooled_rate = n_total_successes / n_total_trials

    # Sample size statistics
    sample_size_min = int(np.min(n_subset))
    sample_size_max = int(np.max(n_subset))
    sample_size_mean = float(np.mean(n_subset))
    sample_size_median = float(np.median(n_subset))
    sample_size_std = float(np.std(n_subset))

    # Success rate statistics
    success_rates = x_subset / n_subset
    success_rate_mean = float(np.mean(success_rates))
    success_rate_std = float(np.std(success_rates))
    success_rate_min = float(np.min(success_rates))
    success_rate_max = float(np.max(success_rates))
    success_rate_median = float(np.median(success_rates))

    # Heterogeneity level (from notebook thresholds)
    if success_rate_std > 0.15:
        heterogeneity_level = "high"
    elif success_rate_std > 0.08:
        heterogeneity_level = "moderate"
    else:
        heterogeneity_level = "low"

    # Variance ratio: observed variance / binomial variance
    # Binomial variance for each group: p(1-p)/n
    # Expected variance of means: mean of p(1-p)/n
    expected_variance = float(np.mean(success_rates * (1 - success_rates) / n_subset))
    observed_variance = success_rate_std ** 2
    variance_ratio = observed_variance / expected_variance if expected_variance > 0 else 0.0

    # Quality flags
    has_extreme_rates = bool(np.any(success_rates < 0.01) or np.any(success_rates > 0.99))
    has_small_samples = bool(np.any(n_subset < 5))
    has_imbalanced_samples = bool(sample_size_max / sample_size_min > 10)

    # Generate warnings
    warnings = []
    if has_extreme_rates:
        warnings.append("Some groups have extreme rates (< 1% or > 99%). Results may be unstable.")
    if has_small_samples:
        warnings.append("Some groups have very small samples (n < 5). Consider pooling or removing.")
    if has_imbalanced_samples:
        warnings.append(f"Sample sizes vary greatly (max/min = {sample_size_max/sample_size_min:.1f}). "
                       "Consider weighted analysis.")
    if variance_ratio > 5.0:
        warnings.append("Very high overdispersion detected. Simple models may be inappropriate.")

    # Model recommendations based on data characteristics
    recommended_models = []

    if heterogeneity_level == "low":
        # Homogeneous data: simple models work well
        recommended_models.append("Single-Theta Bayesian (pooling assumed)")
        recommended_models.append("Clopper-Pearson (frequentist)")
        recommended_models.append("Empirical Bayes (for comparison)")
    elif heterogeneity_level == "moderate":
        # Moderate heterogeneity: EB is ideal
        recommended_models.append("Empirical Bayes (optimal for moderate heterogeneity)")
        recommended_models.append("Hierarchical Bayes (if uncertainty quantification critical)")
        recommended_models.append("Multi-Theta Bayesian (full group-level inference)")
    else:  # high
        # High heterogeneity: need full Bayes
        recommended_models.append("Hierarchical Bayes (accounts for high uncertainty)")
        recommended_models.append("Empirical Bayes (may underestimate uncertainty)")
        if variance_ratio > 5.0:
            recommended_models.append("⚠ Consider checking for data quality issues")

    # Additional recommendations based on sample size
    if n_groups < 10:
        if "Empirical Bayes" in recommended_models[0]:
            warnings.append("Few groups (< 10). EB may be unstable; consider Hierarchical Bayes.")

    if n_groups > 100 and heterogeneity_level != "low":
        if "Hierarchical Bayes" not in recommended_models[0]:
            recommended_models.insert(0, "Empirical Bayes (efficient for many groups)")

    return DataDiagnostics(
        n_groups=n_groups,
        n_total_trials=n_total_trials,
        n_total_successes=n_total_successes,
        pooled_rate=pooled_rate,
        sample_size_min=sample_size_min,
        sample_size_max=sample_size_max,
        sample_size_mean=sample_size_mean,
        sample_size_median=sample_size_median,
        sample_size_std=sample_size_std,
        success_rate_mean=success_rate_mean,
        success_rate_std=success_rate_std,
        success_rate_min=success_rate_min,
        success_rate_max=success_rate_max,
        success_rate_median=success_rate_median,
        heterogeneity_level=heterogeneity_level,
        variance_ratio=variance_ratio,
        has_extreme_rates=has_extreme_rates,
        has_small_samples=has_small_samples,
        has_imbalanced_samples=has_imbalanced_samples,
        recommended_models=recommended_models,
        warnings=warnings,
    )
