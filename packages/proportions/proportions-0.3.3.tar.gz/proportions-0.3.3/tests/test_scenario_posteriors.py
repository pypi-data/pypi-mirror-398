"""Tests for individual scenario posterior computation."""

import numpy as np
import pytest

from proportions.aggregation.average_posterior import (
    compute_scenario_posteriors_hierarchical_bayes,
)
from proportions.core.models import BinomialData


class TestComputeScenarioPosteriors:
    """Tests for compute_scenario_posteriors_hierarchical_bayes function."""

    def test_basic_computation(self):
        """Test basic scenario posterior computation."""
        np.random.seed(42)
        n_samples = 1000
        m_samples = np.random.beta(5.0, 5.0, size=n_samples)
        k_samples = np.random.uniform(5.0, 15.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        scenario_posteriors = compute_scenario_posteriors_hierarchical_bayes(
            alpha_samples, beta_samples, data
        )

        # Should return list with one posterior per scenario
        assert len(scenario_posteriors) == 2

        # Check each posterior has valid structure
        for i, posterior in enumerate(scenario_posteriors):
            assert 0 < posterior.mu < 1
            assert posterior.variance > 0
            assert posterior.alpha_fitted > 0
            assert posterior.beta_fitted > 0
            assert posterior.ci_lower < posterior.mu < posterior.ci_upper
            assert posterior.ci_level == 0.95

        # Scenario 1 (8/10) should have higher mean than Scenario 2 (2/10)
        assert scenario_posteriors[0].mu > scenario_posteriors[1].mu

    def test_with_importance_weights(self):
        """Test scenario posteriors with importance sampling weights."""
        np.random.seed(42)
        n_samples = 1000
        m_samples = np.random.beta(5.0, 5.0, size=n_samples)
        k_samples = np.random.uniform(5.0, 15.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        # Create non-uniform weights (simulating importance sampling)
        weights = np.random.exponential(1.0, size=n_samples)

        data = BinomialData(x=np.array([9, 1]), n=np.array([10, 10]))

        scenario_posteriors = compute_scenario_posteriors_hierarchical_bayes(
            alpha_samples, beta_samples, data, weights=weights
        )

        assert len(scenario_posteriors) == 2

        # Check validity
        for posterior in scenario_posteriors:
            assert 0 < posterior.mu < 1
            assert posterior.variance > 0
            assert posterior.ci_lower < posterior.mu < posterior.ci_upper

    def test_bimodal_scenario(self):
        """Test with bimodal data (high vs low success rate)."""
        np.random.seed(42)
        n_samples = 2000
        m_samples = np.random.beta(1.0, 1.0, size=n_samples)
        k_samples = np.random.uniform(0.1, 100.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        # Bimodal: 90/100 vs 0/4
        data = BinomialData(x=np.array([90, 0]), n=np.array([100, 4]))

        scenario_posteriors = compute_scenario_posteriors_hierarchical_bayes(
            alpha_samples, beta_samples, data
        )

        # Scenario 1: high success rate (90/100)
        # With very wide prior (uniform m, k in [0.1, 100]), posterior is pulled down
        assert scenario_posteriors[0].mu > 0.7

        # Scenario 2: borrowing strength, not at 0 despite 0/4
        assert scenario_posteriors[1].mu > 0.1
        assert scenario_posteriors[1].mu < 0.5

    def test_single_scenario(self):
        """Test with single scenario."""
        np.random.seed(42)
        n_samples = 500
        m_samples = np.random.beta(3.0, 3.0, size=n_samples)
        k_samples = np.random.uniform(5.0, 20.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        data = BinomialData(x=np.array([7]), n=np.array([10]))

        scenario_posteriors = compute_scenario_posteriors_hierarchical_bayes(
            alpha_samples, beta_samples, data
        )

        assert len(scenario_posteriors) == 1
        assert 0 < scenario_posteriors[0].mu < 1
        assert scenario_posteriors[0].variance > 0

    def test_many_scenarios(self):
        """Test with many scenarios."""
        np.random.seed(42)
        n_samples = 1000
        m_samples = np.random.beta(5.0, 5.0, size=n_samples)
        k_samples = np.random.uniform(10.0, 20.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        # 10 scenarios with varying success rates
        data = BinomialData(
            x=np.array([8, 7, 9, 6, 5, 8, 7, 6, 9, 8]),
            n=np.array([10, 10, 10, 10, 10, 10, 10, 10, 10, 10])
        )

        scenario_posteriors = compute_scenario_posteriors_hierarchical_bayes(
            alpha_samples, beta_samples, data
        )

        assert len(scenario_posteriors) == 10

        # All posteriors should be valid
        for posterior in scenario_posteriors:
            assert 0 < posterior.mu < 1
            assert posterior.variance > 0
            assert posterior.ci_lower < posterior.mu < posterior.ci_upper

    def test_custom_ci_level(self):
        """Test with custom credible interval level."""
        np.random.seed(42)
        n_samples = 500
        m_samples = np.random.beta(4.0, 4.0, size=n_samples)
        k_samples = np.random.uniform(5.0, 15.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        scenario_posteriors = compute_scenario_posteriors_hierarchical_bayes(
            alpha_samples, beta_samples, data, ci_level=0.90
        )

        for posterior in scenario_posteriors:
            assert posterior.ci_level == 0.90
            assert posterior.ci_lower < posterior.mu < posterior.ci_upper

    def test_length_mismatch_samples(self):
        """Test that length mismatch between alpha and beta samples raises error."""
        alpha_samples = np.array([5.0, 6.0, 7.0])
        beta_samples = np.array([2.0, 3.0])  # Different length

        data = BinomialData(x=np.array([8]), n=np.array([10]))

        with pytest.raises(ValueError, match="Length mismatch.*alpha_samples"):
            compute_scenario_posteriors_hierarchical_bayes(
                alpha_samples, beta_samples, data
            )

    def test_length_mismatch_weights(self):
        """Test that length mismatch between samples and weights raises error."""
        alpha_samples = np.array([5.0, 6.0, 7.0])
        beta_samples = np.array([2.0, 3.0, 2.5])
        weights = np.array([0.5, 0.5])  # Different length

        data = BinomialData(x=np.array([8]), n=np.array([10]))

        with pytest.raises(ValueError, match="Length mismatch.*weights"):
            compute_scenario_posteriors_hierarchical_bayes(
                alpha_samples, beta_samples, data, weights=weights
            )

    def test_weights_auto_normalized(self):
        """Test that weights are automatically normalized."""
        np.random.seed(42)
        n_samples = 500
        m_samples = np.random.beta(4.0, 4.0, size=n_samples)
        k_samples = np.random.uniform(5.0, 15.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        # Unnormalized weights - create exactly n_samples weights
        weights = np.tile([1.0, 2.0, 3.0], n_samples // 3 + 1)[:n_samples]

        data = BinomialData(x=np.array([8]), n=np.array([10]))

        # Should not raise error (weights are auto-normalized)
        scenario_posteriors = compute_scenario_posteriors_hierarchical_bayes(
            alpha_samples, beta_samples, data, weights=weights
        )

        assert len(scenario_posteriors) == 1
        assert 0 < scenario_posteriors[0].mu < 1

    def test_extreme_success(self):
        """Test with scenario having all successes."""
        np.random.seed(42)
        n_samples = 500
        m_samples = np.random.beta(5.0, 2.0, size=n_samples)  # Biased toward success
        k_samples = np.random.uniform(5.0, 15.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        data = BinomialData(x=np.array([10]), n=np.array([10]))

        scenario_posteriors = compute_scenario_posteriors_hierarchical_bayes(
            alpha_samples, beta_samples, data
        )

        # Should have high mean but not exactly 1
        assert scenario_posteriors[0].mu > 0.85
        assert scenario_posteriors[0].mu < 1.0

    def test_extreme_failure(self):
        """Test with scenario having all failures."""
        np.random.seed(42)
        n_samples = 500
        m_samples = np.random.beta(2.0, 5.0, size=n_samples)  # Biased toward failure
        k_samples = np.random.uniform(5.0, 15.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        data = BinomialData(x=np.array([0]), n=np.array([10]))

        scenario_posteriors = compute_scenario_posteriors_hierarchical_bayes(
            alpha_samples, beta_samples, data
        )

        # Should have low mean but not exactly 0 (borrowing strength)
        assert scenario_posteriors[0].mu > 0.0
        assert scenario_posteriors[0].mu < 0.3

    def test_uniform_weights_equivalent_to_none(self):
        """Test that uniform weights give same result as None."""
        np.random.seed(42)
        n_samples = 500
        m_samples = np.random.beta(4.0, 4.0, size=n_samples)
        k_samples = np.random.uniform(5.0, 15.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))

        # Without weights
        posteriors_none = compute_scenario_posteriors_hierarchical_bayes(
            alpha_samples, beta_samples, data
        )

        # With uniform weights
        uniform_weights = np.ones(n_samples) / n_samples
        posteriors_uniform = compute_scenario_posteriors_hierarchical_bayes(
            alpha_samples, beta_samples, data, weights=uniform_weights
        )

        # Should be very close
        for p_none, p_uniform in zip(posteriors_none, posteriors_uniform):
            assert abs(p_none.mu - p_uniform.mu) < 1e-10
            assert abs(p_none.variance - p_uniform.variance) < 1e-10
