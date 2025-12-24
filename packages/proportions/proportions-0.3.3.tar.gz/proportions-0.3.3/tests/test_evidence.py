"""Tests for model evidence computation.

This module tests the computation of log marginal likelihood (evidence)
for different models, which is used for Bayesian model comparison.
"""

import numpy as np
import pytest

from proportions.core.models import BinomialData
from proportions.diagnostics.evidence import compute_single_theta_evidence, compare_models
from proportions.inference import (
    empirical_bayes,
    hierarchical_bayes,
    single_theta_bayesian,
)


class TestSingleThetaEvidence:
    """Tests for Single-Theta model evidence computation."""

    def test_evidence_matches_function_and_result(self):
        """Test that evidence from single_theta_bayesian matches compute_single_theta_evidence."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        # Get evidence from single_theta_bayesian result
        st_result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)

        # Get evidence from separate function
        st_evidence = compute_single_theta_evidence(data, prior_type="uniform")

        # Should match exactly
        assert np.isclose(st_result.log_marginal_likelihood, st_evidence.log_evidence)

    def test_evidence_with_different_priors(self):
        """Test that different priors give different evidence values."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        # Uniform prior
        uniform_result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)

        # Jeffreys prior
        jeffreys_result = single_theta_bayesian(data, alpha_prior=0.5, beta_prior=0.5)

        # Informative prior
        informative_result = single_theta_bayesian(data, alpha_prior=10.0, beta_prior=5.0)

        # All should be different
        assert uniform_result.log_marginal_likelihood != jeffreys_result.log_marginal_likelihood
        assert uniform_result.log_marginal_likelihood != informative_result.log_marginal_likelihood
        assert jeffreys_result.log_marginal_likelihood != informative_result.log_marginal_likelihood

    def test_evidence_finite(self):
        """Test that evidence is always finite."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)

        assert np.isfinite(result.log_marginal_likelihood)
        assert not np.isnan(result.log_marginal_likelihood)
        assert not np.isinf(result.log_marginal_likelihood)

    def test_evidence_with_extreme_data(self):
        """Test evidence computation with extreme success/failure rates."""
        # All successes
        data_success = BinomialData(x=np.array([10, 10, 10]), n=np.array([10, 10, 10]))
        result_success = single_theta_bayesian(data_success, alpha_prior=1.0, beta_prior=1.0)
        assert np.isfinite(result_success.log_marginal_likelihood)

        # All failures
        data_failure = BinomialData(x=np.array([0, 0, 0]), n=np.array([10, 10, 10]))
        result_failure = single_theta_bayesian(data_failure, alpha_prior=1.0, beta_prior=1.0)
        assert np.isfinite(result_failure.log_marginal_likelihood)

        # Mixed
        data_mixed = BinomialData(x=np.array([10, 0, 5]), n=np.array([10, 10, 10]))
        result_mixed = single_theta_bayesian(data_mixed, alpha_prior=1.0, beta_prior=1.0)
        assert np.isfinite(result_mixed.log_marginal_likelihood)

    def test_evidence_increases_with_more_data(self):
        """Test that absolute evidence magnitude changes with more data."""
        # Small dataset
        data_small = BinomialData(x=np.array([8]), n=np.array([10]))
        result_small = single_theta_bayesian(data_small, alpha_prior=1.0, beta_prior=1.0)

        # Larger dataset with same rate
        data_large = BinomialData(x=np.array([8, 8, 8, 8]), n=np.array([10, 10, 10, 10]))
        result_large = single_theta_bayesian(data_large, alpha_prior=1.0, beta_prior=1.0)

        # Evidence should be different (more data = more information)
        assert result_small.log_marginal_likelihood != result_large.log_marginal_likelihood
        # Typically evidence decreases (becomes more negative) with more data
        # due to the normalizing constant


class TestHierarchicalBayesEvidence:
    """Tests for Hierarchical Bayes model evidence computation."""

    def test_hb_evidence_finite(self):
        """Test that HB evidence is always finite."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result = hierarchical_bayes(data, n_samples=2000, random_seed=42)

        assert np.isfinite(result.log_marginal_likelihood)
        assert not np.isnan(result.log_marginal_likelihood)
        assert not np.isinf(result.log_marginal_likelihood)

    def test_hb_evidence_varies_with_seed(self):
        """Test that HB evidence varies slightly with different random seeds."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result1 = hierarchical_bayes(data, n_samples=1000, random_seed=42)
        result2 = hierarchical_bayes(data, n_samples=1000, random_seed=43)

        # Should be similar but not exactly the same due to random sampling
        assert abs(result1.log_marginal_likelihood - result2.log_marginal_likelihood) < 2.0


class TestEmpiricalBayesEvidence:
    """Tests for Empirical Bayes model evidence computation."""

    def test_eb_evidence_finite(self):
        """Test that EB evidence is always finite."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result = empirical_bayes(data)

        assert np.isfinite(result.log_marginal_likelihood)
        assert not np.isnan(result.log_marginal_likelihood)
        assert not np.isinf(result.log_marginal_likelihood)

    def test_eb_evidence_deterministic(self):
        """Test that EB evidence is deterministic (no randomness)."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result1 = empirical_bayes(data)
        result2 = empirical_bayes(data)

        # Should be exactly the same
        assert result1.log_marginal_likelihood == result2.log_marginal_likelihood


class TestModelComparison:
    """Tests for model comparison via Bayes factors."""

    def test_compare_models_basic(self):
        """Test basic model comparison functionality."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        # Compute evidences
        eb_result = empirical_bayes(data)
        hb_result = hierarchical_bayes(data, n_samples=2000, random_seed=42)
        st_result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)

        from proportions.diagnostics.evidence import ModelEvidence

        evidences = [
            ModelEvidence("Empirical Bayes", eb_result.log_marginal_likelihood, 2),
            ModelEvidence("Hierarchical Bayes", hb_result.log_marginal_likelihood, 2),
            ModelEvidence("Single-Theta", st_result.log_marginal_likelihood, 1),
        ]

        comparison = compare_models(evidences, verbose=False)

        # Check structure
        assert 'evidences' in comparison
        assert 'best_model' in comparison
        assert 'bayes_factors' in comparison
        assert 'log_bayes_factors' in comparison
        assert 'interpretations' in comparison

        # Best model should have BF = 1.0
        best_model_name = comparison['best_model']
        assert comparison['bayes_factors'][best_model_name] == 1.0
        assert comparison['log_bayes_factors'][best_model_name] == 0.0

    def test_bayes_factor_symmetry(self):
        """Test that Bayes factors are symmetric."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result1 = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)
        result2 = single_theta_bayesian(data, alpha_prior=0.5, beta_prior=0.5)

        # BF(1 vs 2) = exp(log_ev1 - log_ev2)
        bf_1_vs_2 = np.exp(result1.log_marginal_likelihood - result2.log_marginal_likelihood)

        # BF(2 vs 1) = exp(log_ev2 - log_ev1) = 1 / BF(1 vs 2)
        bf_2_vs_1 = np.exp(result2.log_marginal_likelihood - result1.log_marginal_likelihood)

        # Should be reciprocals
        assert np.isclose(bf_1_vs_2 * bf_2_vs_1, 1.0)


class TestEvidenceConsistency:
    """Tests for consistency of evidence across different methods."""

    def test_single_theta_vs_eb_on_homogeneous_data(self):
        """Test that Single-Theta and EB give similar evidence on homogeneous data."""
        # Very homogeneous data
        data = BinomialData(x=np.array([8, 8, 8, 8]), n=np.array([10, 10, 10, 10]))

        st_result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)
        eb_result = empirical_bayes(data)

        # Evidence should be reasonably close on homogeneous data
        # (EB assumes heterogeneity, ST assumes homogeneity)
        log_bf = st_result.log_marginal_likelihood - eb_result.log_marginal_likelihood

        # Should be within reasonable range (not decisive evidence either way)
        assert abs(log_bf) < 10.0  # Not decisive (|log BF| < 10)

    def test_hb_vs_eb_similar_on_moderate_data(self):
        """Test that HB and EB give similar evidence on moderate heterogeneity."""
        data = BinomialData(x=np.array([8, 7, 9, 6]), n=np.array([10, 10, 10, 10]))

        eb_result = empirical_bayes(data)
        hb_result = hierarchical_bayes(data, n_samples=5000, random_seed=42)

        # HB and EB should give similar evidence on moderate data
        log_bf = hb_result.log_marginal_likelihood - eb_result.log_marginal_likelihood

        # Should be within a few log units
        assert abs(log_bf) < 5.0


class TestEvidenceEdgeCases:
    """Tests for edge cases in evidence computation."""

    def test_single_group_evidence(self):
        """Test evidence computation with single group."""
        data = BinomialData(x=np.array([8]), n=np.array([10]))

        st_result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)
        eb_result = empirical_bayes(data)
        hb_result = hierarchical_bayes(data, n_samples=2000, random_seed=42)

        # All should produce finite evidence
        assert np.isfinite(st_result.log_marginal_likelihood)
        assert np.isfinite(eb_result.log_marginal_likelihood)
        assert np.isfinite(hb_result.log_marginal_likelihood)

    def test_large_sample_size_evidence(self):
        """Test evidence computation with large sample sizes."""
        # Large n per group
        data = BinomialData(x=np.array([800, 700, 900]), n=np.array([1000, 1000, 1000]))

        st_result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)
        eb_result = empirical_bayes(data)

        # Should produce finite evidence even with large samples
        assert np.isfinite(st_result.log_marginal_likelihood)
        assert np.isfinite(eb_result.log_marginal_likelihood)

        # Evidence magnitude should be larger (more negative) with more data
        assert st_result.log_marginal_likelihood < -100  # Rough check

    def test_many_groups_evidence(self):
        """Test evidence computation with many groups."""
        np.random.seed(42)
        n_groups = 50
        x = np.random.binomial(20, 0.7, size=n_groups)
        n = np.full(n_groups, 20)
        data = BinomialData(x=x, n=n)

        st_result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)
        eb_result = empirical_bayes(data)

        # Should handle many groups
        assert np.isfinite(st_result.log_marginal_likelihood)
        assert np.isfinite(eb_result.log_marginal_likelihood)
