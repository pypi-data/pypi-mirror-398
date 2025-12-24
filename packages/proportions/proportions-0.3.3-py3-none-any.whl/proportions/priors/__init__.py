"""Prior specification and fitting utilities.

This module provides tools for specifying and fitting prior distributions
for Bayesian inference on binomial proportions.
"""

from proportions.priors.fitting import fit_beta_from_credible_interval
from proportions.priors.specification import (
    BetaPriorSpec,
    HyperpriorSpec,
    UniformPriorSpec,
)

__all__ = [
    "BetaPriorSpec",
    "HyperpriorSpec",
    "UniformPriorSpec",
    "fit_beta_from_credible_interval",
]
