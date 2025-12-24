"""Diagnostics module for model comparison and evaluation.

This module provides tools for:
- Computing model evidence (marginal likelihood)
- Bayes factors for model comparison
- Data quality diagnostics
- Importance sampling diagnostics
- Diagnostic visualizations
- Monte Carlo coverage simulations
"""

from proportions.diagnostics.data import (
    compute_data_diagnostics,
    DataDiagnostics,
)
from proportions.diagnostics.evidence import (
    compute_single_theta_evidence,
    compute_uncoupled_thetas_evidence,
    ModelEvidence,
    compare_models,
)
from proportions.diagnostics.importance_sampling import (
    extract_importance_samples,
    ImportanceSamples,
    compute_weighted_statistics,
)
from proportions.diagnostics.visualization import (
    plot_importance_sampling_diagnostics,
    plot_mk_distributions,
    plot_posterior_proportion,
)
from proportions.diagnostics.coverage import (
    CoverageSimulationConfig,
    CoverageMetrics,
    CoverageSimulationResult,
    run_coverage_simulation,
)

__all__ = [
    "compute_single_theta_evidence",
    "compute_uncoupled_thetas_evidence",
    "ModelEvidence",
    "compare_models",
    "compute_data_diagnostics",
    "DataDiagnostics",
    "extract_importance_samples",
    "ImportanceSamples",
    "compute_weighted_statistics",
    "plot_importance_sampling_diagnostics",
    "plot_mk_distributions",
    "plot_posterior_proportion",
    "CoverageSimulationConfig",
    "CoverageMetrics",
    "CoverageSimulationResult",
    "run_coverage_simulation",
]
