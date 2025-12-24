"""Tests for uncoupled thetas Bayesian inference."""

import numpy as np
import pytest

from proportions.core.models import BinomialData, UncoupledThetasResult, PosteriorResult
from proportions.inference.uncoupled_thetas import uncoupled_thetas
from proportions.diagnostics.evidence import compute_uncoupled_thetas_evidence, ModelEvidence


class TestUncoupledThetas:
    """Tests for uncoupled_thetas function."""

    def test_basic_inference_uniform_prior(self):
        """Test basic uncoupled thetas inference with uniform prior."""
        # Simple test case: 2 scenarios
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        result = uncoupled_thetas(
            data,
            alpha_prior=1.0,
            beta_prior=1.0,
            ci_level=0.95,
            random_seed=42
        )

        # Check result type
        assert isinstance(result, UncoupledThetasResult)
        assert result.method == 'uncoupled_thetas'

        # Check prior parameters
        assert result.prior_alpha == 1.0
        assert result.prior_beta == 1.0

        # Check number of scenarios
        assert result.n_scenarios == 2

        # Check scenario posteriors
        assert len(result.scenario_posteriors) == 2
        assert all(isinstance(p, PosteriorResult) for p in result.scenario_posteriors)

        # Scenario 1: 8/10 -> Beta(1+8, 1+2) = Beta(9, 3)
        assert result.scenario_posteriors[0].alpha_fitted == 9.0
        assert result.scenario_posteriors[0].beta_fitted == 3.0
        assert np.isclose(result.scenario_posteriors[0].mu, 9.0/12.0, rtol=1e-6)

        # Scenario 2: 2/10 -> Beta(1+2, 1+8) = Beta(3, 9)
        assert result.scenario_posteriors[1].alpha_fitted == 3.0
        assert result.scenario_posteriors[1].beta_fitted == 9.0
        assert np.isclose(result.scenario_posteriors[1].mu, 3.0/12.0, rtol=1e-6)

    def test_mu_samples_stored(self):
        """Test that mu samples are stored and have correct shape."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        result = uncoupled_thetas(
            data,
            n_mu_samples=100000,
            random_seed=42
        )

        # Check mu_samples exist and have correct shape
        assert result.mu_samples is not None
        assert len(result.mu_samples) == 100000

        # Check mu_samples are in valid range [0, 1]
        assert np.all(result.mu_samples >= 0)
        assert np.all(result.mu_samples <= 1)

    def test_aggregate_posterior(self):
        """Test that aggregate posterior is reasonable."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        result = uncoupled_thetas(data, random_seed=42)

        # Check aggregate posterior exists
        assert isinstance(result.aggregate_posterior, PosteriorResult)

        # Aggregate mean should be close to average of scenario means
        scenario_mean_avg = np.mean([p.mu for p in result.scenario_posteriors])
        assert np.isclose(result.aggregate_posterior.mu, scenario_mean_avg, rtol=0.1)

        # Check aggregate has CI
        assert result.aggregate_posterior.ci_lower < result.aggregate_posterior.mu
        assert result.aggregate_posterior.mu < result.aggregate_posterior.ci_upper

    def test_independence_of_scenarios(self):
        """Test that scenarios are truly independent (no shrinkage)."""
        # Extreme bimodal: one high, one low
        data = BinomialData(x=np.array([95, 5]), n=np.array([100, 100]))

        result = uncoupled_thetas(data, random_seed=42)

        # Scenario 1: should stay near 95/100 = 0.95
        # No shrinkage toward the middle
        assert result.scenario_posteriors[0].mu > 0.90

        # Scenario 2: should stay near 5/100 = 0.05
        # No shrinkage toward the middle
        assert result.scenario_posteriors[1].mu < 0.10

        # Check exact posterior parameters (no shrinkage)
        # Beta(1+95, 1+5) = Beta(96, 6)
        assert result.scenario_posteriors[0].alpha_fitted == 96.0
        assert result.scenario_posteriors[0].beta_fitted == 6.0

    def test_custom_prior(self):
        """Test with non-uniform prior."""
        data = BinomialData(x=np.array([5]), n=np.array([10]))

        # Jeffreys prior: Beta(0.5, 0.5)
        result = uncoupled_thetas(
            data,
            alpha_prior=0.5,
            beta_prior=0.5,
            random_seed=42
        )

        assert result.prior_alpha == 0.5
        assert result.prior_beta == 0.5

        # Posterior: Beta(0.5+5, 0.5+5) = Beta(5.5, 5.5)
        assert result.scenario_posteriors[0].alpha_fitted == 5.5
        assert result.scenario_posteriors[0].beta_fitted == 5.5

    def test_single_scenario(self):
        """Test with single scenario (edge case)."""
        data = BinomialData(x=np.array([7]), n=np.array([10]))

        result = uncoupled_thetas(data, random_seed=42)

        assert result.n_scenarios == 1
        assert len(result.scenario_posteriors) == 1

        # mu should equal the single scenario posterior mean
        assert np.isclose(
            result.aggregate_posterior.mu,
            result.scenario_posteriors[0].mu,
            rtol=0.01
        )

    def test_many_scenarios(self):
        """Test with many scenarios."""
        # 10 scenarios with varying success rates
        np.random.seed(42)
        n_scenarios = 10
        data = BinomialData(
            x=np.array([8, 7, 9, 6, 5, 8, 7, 8, 9, 7]),
            n=np.array([10] * n_scenarios)
        )

        result = uncoupled_thetas(data, random_seed=42)

        assert result.n_scenarios == 10
        assert len(result.scenario_posteriors) == 10
        assert len(result.mu_samples) == 100000

    def test_reproducibility_with_seed(self):
        """Test that results are reproducible with same seed."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        result1 = uncoupled_thetas(data, random_seed=42)
        result2 = uncoupled_thetas(data, random_seed=42)

        # mu_samples should be identical
        assert np.allclose(result1.mu_samples, result2.mu_samples)

        # Aggregate posteriors should be identical
        assert np.isclose(result1.aggregate_posterior.mu, result2.aggregate_posterior.mu)

    def test_different_sample_sizes(self):
        """Test with different sample sizes per scenario."""
        # Large sample vs small sample
        data = BinomialData(x=np.array([90, 5]), n=np.array([100, 10]))

        result = uncoupled_thetas(data, random_seed=42)

        # Both should have independent posteriors
        assert len(result.scenario_posteriors) == 2

        # Large sample scenario should have tighter CI
        large_ci_width = (result.scenario_posteriors[0].ci_upper -
                         result.scenario_posteriors[0].ci_lower)
        small_ci_width = (result.scenario_posteriors[1].ci_upper -
                         result.scenario_posteriors[1].ci_lower)

        assert small_ci_width > large_ci_width

    def test_validates_prior_parameters(self):
        """Test that invalid prior parameters are rejected."""
        data = BinomialData(x=np.array([5]), n=np.array([10]))

        with pytest.raises(ValueError, match="alpha_prior must be positive"):
            uncoupled_thetas(data, alpha_prior=0.0)

        with pytest.raises(ValueError, match="beta_prior must be positive"):
            uncoupled_thetas(data, beta_prior=-1.0)

    def test_log_marginal_likelihood_computed(self):
        """Test that log marginal likelihood is computed."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        result = uncoupled_thetas(data, random_seed=42)

        # Should have log evidence
        assert isinstance(result.log_marginal_likelihood, float)
        assert np.isfinite(result.log_marginal_likelihood)


class TestComputeUncoupledThetasEvidence:
    """Tests for compute_uncoupled_thetas_evidence function."""

    def test_uniform_prior_evidence(self):
        """Test evidence computation with uniform prior."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        evidence = compute_uncoupled_thetas_evidence(data, prior_type="uniform")

        assert isinstance(evidence, ModelEvidence)
        assert evidence.model_name == "Uncoupled Thetas"
        assert evidence.prior_type == "Uniform(0,1)"
        assert isinstance(evidence.log_evidence, float)
        assert np.isfinite(evidence.log_evidence)
        assert evidence.n_parameters == 2.0  # Two independent thetas

    def test_jeffreys_prior_evidence(self):
        """Test evidence computation with Jeffreys prior."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        evidence = compute_uncoupled_thetas_evidence(data, prior_type="jeffreys")

        assert evidence.model_name == "Uncoupled Thetas"
        assert evidence.prior_type == "Jeffreys"
        assert isinstance(evidence.log_evidence, float)
        assert np.isfinite(evidence.log_evidence)

    def test_evidence_matches_result(self):
        """Test that standalone evidence matches result.log_marginal_likelihood."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        # Get evidence from inference result
        result = uncoupled_thetas(data, alpha_prior=1.0, beta_prior=1.0)

        # Get evidence from standalone function
        evidence = compute_uncoupled_thetas_evidence(data, prior_type="uniform")

        # Should match (uniform prior = Beta(1,1))
        assert np.isclose(result.log_marginal_likelihood, evidence.log_evidence)

    def test_evidence_is_product_of_marginals(self):
        """Test that evidence is product of independent marginals."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        # Get combined evidence
        evidence_combined = compute_uncoupled_thetas_evidence(data, prior_type="uniform")

        # Get individual evidences
        data1 = BinomialData(x=np.array([8]), n=np.array([10]))
        data2 = BinomialData(x=np.array([2]), n=np.array([10]))

        evidence1 = compute_uncoupled_thetas_evidence(data1, prior_type="uniform")
        evidence2 = compute_uncoupled_thetas_evidence(data2, prior_type="uniform")

        # Combined should equal sum of individual log evidences
        assert np.isclose(
            evidence_combined.log_evidence,
            evidence1.log_evidence + evidence2.log_evidence,
            rtol=1e-10
        )

    def test_many_scenarios_evidence(self):
        """Test evidence computation with many scenarios."""
        data = BinomialData(
            x=np.array([8, 7, 9, 6, 5]),
            n=np.array([10, 10, 10, 10, 10])
        )

        evidence = compute_uncoupled_thetas_evidence(data, prior_type="uniform")

        assert evidence.n_parameters == 5.0  # Five independent thetas
        assert np.isfinite(evidence.log_evidence)
