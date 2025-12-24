"""Beta distribution utilities and extensions.

This module provides numerically stable implementations of Beta distribution
functions and truncated Beta distributions.
"""

from proportions.distributions.beta import (
    beta_cdf,
    beta_mode,
    beta_ppf,
    beta_quantiles,
    log_beta,
    log_beta_cdf,
)
from proportions.distributions.truncated_beta import (
    log_truncated_beta_partition,
    truncated_beta_cdf,
    truncated_beta_partition,
    truncated_beta_pdf,
    truncated_beta_ppf,
)

__all__ = [
    # Standard Beta functions
    "beta_cdf",
    "beta_mode",
    "beta_ppf",
    "beta_quantiles",
    "log_beta",
    "log_beta_cdf",
    # Truncated Beta functions
    "log_truncated_beta_partition",
    "truncated_beta_cdf",
    "truncated_beta_partition",
    "truncated_beta_pdf",
    "truncated_beta_ppf",
]
