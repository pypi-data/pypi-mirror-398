"""Inference algorithms for Beta-Binomial hierarchical models.

This module provides the main inference algorithms:
- Empirical Bayes: Estimate hyperparameters via maximum likelihood
- Hierarchical Bayes: Fully Bayesian with hyperparameter uncertainty
- Single-Theta: Pool all data, assume single success rate
- Uncoupled Thetas: Independent posteriors for each scenario (no pooling)
- Clopper-Pearson: Frequentist exact confidence interval
- Single Proportion: Bayesian inference for a single binomial proportion
- Conditional Inference: Inference conditioned on k/k successes (winner's curse)
"""

from proportions.inference.clopper_pearson import clopper_pearson
from proportions.inference.empirical_bayes import empirical_bayes
from proportions.inference.hierarchical_bayes import hierarchical_bayes
from proportions.inference.single_theta import single_theta_bayesian
from proportions.inference.uncoupled_thetas import uncoupled_thetas
from proportions.inference.single_proportion import (
    conf_interval_proportion,
    lower_bound_proportion,
    upper_bound_proportion,
    prob_larger_than_threshold,
    prob_smaller_than_threshold,
    prob_of_interval,
)
from proportions.inference.conditional import conditional_inference_k_out_of_k

__all__ = [
    # Grouped data inference
    "empirical_bayes",
    "hierarchical_bayes",
    "single_theta_bayesian",
    "uncoupled_thetas",
    "clopper_pearson",
    # Single proportion inference
    "conf_interval_proportion",
    "lower_bound_proportion",
    "upper_bound_proportion",
    "prob_larger_than_threshold",
    "prob_smaller_than_threshold",
    "prob_of_interval",
    # Conditional inference
    "conditional_inference_k_out_of_k",
]
