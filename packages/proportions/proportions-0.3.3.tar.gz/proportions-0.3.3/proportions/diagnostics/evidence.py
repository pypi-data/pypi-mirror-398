"""Model evidence computation and comparison for Bayesian model selection.

This module computes log marginal likelihood (evidence) for different models,
enabling principled Bayesian model comparison via Bayes factors.
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np

from proportions.core.models import BinomialData
from proportions.distributions.beta import log_beta


@dataclass
class ModelEvidence:
    """Evidence (marginal likelihood) for a model.

    Attributes:
        model_name: Name of the model.
        log_evidence: Log marginal likelihood log p(data | model).
        n_parameters: Effective number of parameters (for reference).
        prior_type: Type of prior used (if applicable).
    """
    model_name: str
    log_evidence: float
    n_parameters: float
    prior_type: str | None = None

    def __repr__(self) -> str:
        if self.prior_type:
            return (f"ModelEvidence(model={self.model_name}, "
                   f"prior={self.prior_type}, "
                   f"log_evidence={self.log_evidence:.2f}, "
                   f"n_params={self.n_parameters})")
        return (f"ModelEvidence(model={self.model_name}, "
               f"log_evidence={self.log_evidence:.2f}, "
               f"n_params={self.n_parameters})")


def compute_single_theta_evidence(
    data: BinomialData,
    prior_type: Literal["uniform", "jeffreys"] = "uniform",
    group_indices: list[int] | np.ndarray | None = None,
) -> ModelEvidence:
    """Compute log marginal likelihood for Single-Theta model.

    The Single-Theta model assumes all groups share a common success rate θ,
    and pools all data for inference. The marginal likelihood depends on the
    prior choice.

    Model:
        θ ~ Prior (Uniform or Jeffreys)
        x_i ~ Binomial(n_i, θ)

    Marginal likelihood:
        p(data | model) = ∫ p(data | θ) p(θ) dθ

    For Beta(α, β) prior, this has closed form:
        p(data) = [B(α + x_total, β + n_total - x_total)] / B(α, β)

    Args:
        data: Binomial data (success and trial counts per group).
        prior_type: Type of prior on θ:
            - "uniform": θ ~ Beta(1, 1) = Uniform(0, 1)
            - "jeffreys": θ ~ Beta(0.5, 0.5) (Jeffreys prior for binomial)
        group_indices: Optional list of group indices to include.
                       If None, uses all groups.

    Returns:
        ModelEvidence with log marginal likelihood for the Single-Theta model.

    Notes:
        - Uniform prior: Treats all θ values equally a priori
        - Jeffreys prior: Invariant to reparameterization, proper but improper-like
        - Both are "uninformative" priors representing minimal prior knowledge
        - Log evidence can be compared across models using Bayes factors

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> from proportions.diagnostics.evidence import compute_single_theta_evidence
        >>>
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>>
        >>> # Uniform prior
        >>> ev_uniform = compute_single_theta_evidence(data, prior_type="uniform")
        >>> print(f"Log evidence (uniform): {ev_uniform.log_evidence:.2f}")
        >>>
        >>> # Jeffreys prior
        >>> ev_jeffreys = compute_single_theta_evidence(data, prior_type="jeffreys")
        >>> print(f"Log evidence (Jeffreys): {ev_jeffreys.log_evidence:.2f}")
    """
    # Determine which groups to pool
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

    # Pool data
    x_total = int(np.sum(x_subset))
    n_total = int(np.sum(n_subset))

    # Set prior hyperparameters
    if prior_type == "uniform":
        alpha_prior = 1.0
        beta_prior = 1.0
        prior_name = "Uniform(0,1)"
    elif prior_type == "jeffreys":
        alpha_prior = 0.5
        beta_prior = 0.5
        prior_name = "Jeffreys Beta(0.5,0.5)"
    else:
        raise ValueError(
            f"Unknown prior_type: {prior_type}. Must be 'uniform' or 'jeffreys'."
        )

    # Compute log marginal likelihood
    # p(data) = B(α + x, β + n - x) / B(α, β)
    log_evidence = (
        log_beta(alpha_prior + x_total, beta_prior + n_total - x_total)
        - log_beta(alpha_prior, beta_prior)
    )

    return ModelEvidence(
        model_name="Single-Theta",
        log_evidence=float(log_evidence),
        n_parameters=1.0,  # Single θ parameter
        prior_type=prior_name,
    )


def compute_uncoupled_thetas_evidence(
    data: BinomialData,
    prior_type: Literal["uniform", "jeffreys"] = "uniform",
) -> ModelEvidence:
    """Compute log marginal likelihood for Uncoupled Thetas model.

    The Uncoupled Thetas model treats each scenario's θᵢ independently with
    the same prior. The marginal likelihood is the product of independent
    Beta-Binomial marginals for each scenario.

    Model:
        θᵢ ~ Prior (Uniform or Jeffreys) for i = 1, ..., K (independent)
        xᵢ ~ Binomial(nᵢ, θᵢ)

    Marginal likelihood:
        p(data | model) = ∏ᵢ ∫ p(xᵢ | θᵢ) p(θᵢ) dθᵢ
                        = ∏ᵢ [B(α + xᵢ, β + nᵢ - xᵢ) / B(α, β)]

    Log marginal likelihood:
        log p(data) = Σᵢ [log B(α + xᵢ, β + nᵢ - xᵢ) - log B(α, β)]

    Args:
        data: Binomial data (success and trial counts per scenario).
        prior_type: Type of prior on each θᵢ:
            - "uniform": θᵢ ~ Beta(1, 1) = Uniform(0, 1)
            - "jeffreys": θᵢ ~ Beta(0.5, 0.5) (Jeffreys prior)

    Returns:
        ModelEvidence with log marginal likelihood for the Uncoupled Thetas model.

    Notes:
        - Each scenario contributes independently to the evidence
        - Number of parameters = number of scenarios (K independent θᵢ)
        - More flexible than Single-Theta (allows heterogeneity)
        - Less constrained than Hierarchical Bayes (no hyperparameter structure)

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> from proportions.diagnostics.evidence import compute_uncoupled_thetas_evidence
        >>>
        >>> data = BinomialData(x=np.array([90, 10]), n=np.array([100, 100]))
        >>> evidence = compute_uncoupled_thetas_evidence(data, prior_type="uniform")
        >>> print(f"Log evidence: {evidence.log_evidence:.2f}")
        >>> print(f"Parameters: {evidence.n_parameters}")
    """
    # Set prior parameters based on type
    if prior_type == "uniform":
        alpha_prior = 1.0
        beta_prior = 1.0
        prior_name = "Uniform(0,1)"
    elif prior_type == "jeffreys":
        alpha_prior = 0.5
        beta_prior = 0.5
        prior_name = "Jeffreys"
    else:
        raise ValueError(
            f"Unknown prior_type: {prior_type}. Must be 'uniform' or 'jeffreys'."
        )

    # Compute log marginal likelihood as sum of independent marginals
    log_evidence = 0.0
    for i in range(data.n_groups):
        x_i = data.x[i]
        n_i = data.n[i]

        # Log marginal for scenario i: log[B(α + xᵢ, β + nᵢ - xᵢ) / B(α, β)]
        log_evidence_i = (
            log_beta(alpha_prior + x_i, beta_prior + n_i - x_i)
            - log_beta(alpha_prior, beta_prior)
        )
        log_evidence += log_evidence_i

    return ModelEvidence(
        model_name="Uncoupled Thetas",
        log_evidence=float(log_evidence),
        n_parameters=float(data.n_groups),  # K independent θᵢ parameters
        prior_type=prior_name,
    )


def compare_models(
    evidences: list[ModelEvidence],
    verbose: bool = True,
) -> dict:
    """Compare models using Bayes factors based on marginal likelihoods.

    Bayes factor BF[i,j] = p(data | model i) / p(data | model j)
    measures the relative evidence for model i vs model j.

    Interpretation (Kass & Raftery, 1995):
        - BF > 100: Decisive evidence for model i
        - 30 < BF < 100: Very strong evidence
        - 10 < BF < 30: Strong evidence
        - 3 < BF < 10: Moderate evidence
        - 1 < BF < 3: Weak evidence
        - BF < 1: Evidence favors model j

    Args:
        evidences: List of ModelEvidence objects to compare.
        verbose: If True, prints formatted comparison table.

    Returns:
        Dictionary with:
            - 'evidences': Input list sorted by evidence (best first)
            - 'best_model': Name of model with highest evidence
            - 'bayes_factors': Dict of BF relative to best model
            - 'log_bayes_factors': Dict of log BF relative to best model
            - 'interpretations': Dict of interpretation strings

    Example:
        >>> from proportions.inference import empirical_bayes, hierarchical_bayes
        >>> from proportions.diagnostics.evidence import compute_single_theta_evidence, compare_models
        >>>
        >>> # Compute evidences for different models
        >>> eb_result = empirical_bayes(data)
        >>> hb_result = hierarchical_bayes(data, random_seed=42)
        >>> st_uniform = compute_single_theta_evidence(data, prior_type="uniform")
        >>> st_jeffreys = compute_single_theta_evidence(data, prior_type="jeffreys")
        >>>
        >>> # Compare
        >>> evidences = [
        ...     ModelEvidence("Empirical Bayes", eb_result.log_marginal_likelihood, 2),
        ...     ModelEvidence("Hierarchical Bayes", hb_result.log_marginal_likelihood, 2),
        ...     st_uniform,
        ...     st_jeffreys,
        ... ]
        >>> comparison = compare_models(evidences)
    """
    if len(evidences) == 0:
        raise ValueError("Need at least one model to compare")

    # Sort by evidence (highest first)
    sorted_evidences = sorted(evidences, key=lambda e: e.log_evidence, reverse=True)

    best_model = sorted_evidences[0]
    best_log_evidence = best_model.log_evidence

    # Compute Bayes factors relative to best model
    bayes_factors = {}
    log_bayes_factors = {}
    interpretations = {}

    for ev in sorted_evidences:
        log_bf = ev.log_evidence - best_log_evidence
        bf = np.exp(log_bf)

        # Interpret Bayes factor
        if bf > 100:
            interp = "Decisive"
        elif bf > 30:
            interp = "Very Strong"
        elif bf > 10:
            interp = "Strong"
        elif bf > 3:
            interp = "Moderate"
        elif bf > 1:
            interp = "Weak"
        else:
            interp = "---"

        model_key = f"{ev.model_name}" + (f" ({ev.prior_type})" if ev.prior_type else "")
        bayes_factors[model_key] = bf
        log_bayes_factors[model_key] = log_bf
        interpretations[model_key] = interp

    if verbose:
        print("=" * 80)
        print("Model Comparison via Bayes Factors")
        print("=" * 80)
        print(f"{'Model':<40} {'Log Evidence':>12} {'BF vs Best':>12} {'Evidence':>10}")
        print("-" * 80)

        for ev in sorted_evidences:
            model_key = f"{ev.model_name}" + (f" ({ev.prior_type})" if ev.prior_type else "")
            log_ev = ev.log_evidence
            log_bf = log_bayes_factors[model_key]
            bf = bayes_factors[model_key]
            interp = interpretations[model_key]

            # Format BF display
            if bf >= 1.0:
                bf_str = f"{bf:.2f}" if bf < 1000 else f"{bf:.2e}"
            else:
                bf_str = f"1/{1/bf:.2f}" if 1/bf < 1000 else f"1/{1/bf:.2e}"

            # Highlight best model
            marker = " ←" if ev == best_model else ""

            print(f"{model_key:<40} {log_ev:>12.2f} {bf_str:>12} {interp:>10}{marker}")

        print("-" * 80)
        print("\nInterpretation (Kass & Raftery, 1995):")
        print("  Decisive (BF > 100), Very Strong (30-100), Strong (10-30),")
        print("  Moderate (3-10), Weak (1-3)")
        print("=" * 80)

    best_model_name = f"{best_model.model_name}" + (
        f" ({best_model.prior_type})" if best_model.prior_type else ""
    )

    return {
        'evidences': sorted_evidences,
        'best_model': best_model_name,
        'bayes_factors': bayes_factors,
        'log_bayes_factors': log_bayes_factors,
        'interpretations': interpretations,
    }
