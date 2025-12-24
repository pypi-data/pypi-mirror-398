"""Tests for conditional inference (winner's curse)."""

import numpy as np
import pytest

from proportions.inference.conditional import conditional_inference_k_out_of_k
from proportions.core.models import ConditionalPosteriorResult


class TestConditionalInferenceKOutOfK:
    """Tests for conditional_inference_k_out_of_k function."""

    def test_self_conditional_basic(self):
        """Test self-conditional inference with simple parameters."""
        # Create simple posteriors: all scenarios have same posterior
        n_scenarios = 5
        alpha = np.full(n_scenarios, 10.0)
        beta = np.full(n_scenarios, 90.0)

        result = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            n_samples=10000,
            random_seed=42,
            fit_beta=True,
            ci_level=0.95
        )

        # Check result type
        assert isinstance(result, ConditionalPosteriorResult)

        # Check basic properties
        assert 0.0 <= result.mean <= 1.0
        assert 0.0 <= result.median <= 1.0
        assert result.std > 0
        assert result.ci_lower < result.mean < result.ci_upper
        assert result.ci_level == 0.95

        # Check MC samples
        assert len(result.samples) == 10000
        assert result.n_samples == 10000

        # Check filter info
        assert result.k == 3
        assert result.n_scenarios == n_scenarios

        # Check weights
        assert len(result.scenario_weights) == n_scenarios
        assert np.isclose(result.scenario_weights.sum(), 1.0)

    def test_self_conditional_winner_curse(self):
        """Test that conditioning increases expected success rate (winner's curse)."""
        # Create scenarios with modest success rate
        n_scenarios = 10
        alpha = np.full(n_scenarios, 5.0)
        beta = np.full(n_scenarios, 95.0)

        # Unconditional mean
        unconditional_mean = alpha[0] / (alpha[0] + beta[0])

        # Conditional on k/k successes
        result = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=5,
            n_samples=50000,
            random_seed=42
        )

        # Conditional mean should be higher (winner's curse)
        assert result.mean > unconditional_mean

    def test_cross_conditional(self):
        """Test cross-conditional inference (Task B given Task A filter)."""
        n_scenarios = 5

        # Task A: filtering task
        alpha_a = np.array([10.0, 15.0, 8.0, 12.0, 11.0])
        beta_a = np.array([90.0, 85.0, 92.0, 88.0, 89.0])

        # Task B: target task (different from A)
        alpha_b = np.array([20.0, 25.0, 18.0, 22.0, 21.0])
        beta_b = np.array([80.0, 75.0, 82.0, 78.0, 79.0])

        result = conditional_inference_k_out_of_k(
            alpha_task_a=alpha_a,
            beta_task_a=beta_a,
            alpha_task_b=alpha_b,
            beta_task_b=beta_b,
            k=3,
            n_samples=10000,
            random_seed=42
        )

        # Should return valid result
        assert 0.0 <= result.mean <= 1.0
        assert result.n_scenarios == n_scenarios

    def test_beta_fitting(self):
        """Test that Beta fitting works when enabled."""
        n_scenarios = 5
        alpha = np.full(n_scenarios, 10.0)
        beta = np.full(n_scenarios, 90.0)

        # With fitting
        result_with_fit = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            n_samples=10000,
            random_seed=42,
            fit_beta=True
        )

        assert result_with_fit.fitted_beta is True
        assert result_with_fit.alpha_fitted is not None
        assert result_with_fit.beta_fitted is not None
        assert result_with_fit.alpha_fitted > 0
        assert result_with_fit.beta_fitted > 0
        assert result_with_fit.mode is not None

        # Without fitting
        result_without_fit = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            n_samples=10000,
            random_seed=42,
            fit_beta=False
        )

        assert result_without_fit.fitted_beta is False
        assert result_without_fit.alpha_fitted is None
        assert result_without_fit.beta_fitted is None
        assert result_without_fit.mode is None

    def test_reproducibility(self):
        """Test that random seed gives reproducible results."""
        n_scenarios = 5
        alpha = np.full(n_scenarios, 10.0)
        beta = np.full(n_scenarios, 90.0)

        result1 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            n_samples=10000,
            random_seed=42
        )

        result2 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            n_samples=10000,
            random_seed=42
        )

        # Results should be identical with same seed
        assert np.allclose(result1.mean, result2.mean)
        assert np.allclose(result1.std, result2.std)
        assert np.allclose(result1.samples, result2.samples)

    def test_different_k_values(self):
        """Test that larger k gives stronger conditioning effect."""
        n_scenarios = 10
        alpha = np.full(n_scenarios, 5.0)
        beta = np.full(n_scenarios, 95.0)

        result_k2 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=2,
            n_samples=50000,
            random_seed=42
        )

        result_k10 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=10,
            n_samples=50000,
            random_seed=42
        )

        # Stronger filter (k=10) should give higher mean
        assert result_k10.mean > result_k2.mean

    def test_ci_level(self):
        """Test different credible interval levels."""
        n_scenarios = 5
        alpha = np.full(n_scenarios, 10.0)
        beta = np.full(n_scenarios, 90.0)

        result_95 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            n_samples=10000,
            random_seed=42,
            ci_level=0.95
        )

        result_90 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            n_samples=10000,
            random_seed=42,
            ci_level=0.90
        )

        # 90% CI should be narrower than 95% CI
        width_95 = result_95.ci_upper - result_95.ci_lower
        width_90 = result_90.ci_upper - result_90.ci_lower
        assert width_90 < width_95

    def test_scenario_weights(self):
        """Test that scenario weights are computed correctly."""
        n_scenarios = 5
        # Give scenarios different success rates
        alpha = np.array([5.0, 10.0, 15.0, 20.0, 25.0])
        beta = np.array([95.0, 90.0, 85.0, 80.0, 75.0])

        result = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            n_samples=10000,
            random_seed=42
        )

        # Weights should sum to 1
        assert np.isclose(result.scenario_weights.sum(), 1.0)

        # Scenarios with higher success rates should get higher weights
        # (more likely to pass k/k filter)
        assert result.scenario_weights[-1] > result.scenario_weights[0]

    def test_invalid_inputs(self):
        """Test that invalid inputs raise appropriate errors."""

        # Mismatched alpha/beta shapes
        with pytest.raises(ValueError, match="same shape"):
            conditional_inference_k_out_of_k(
                alpha_task_a=np.array([1.0, 2.0]),
                beta_task_a=np.array([1.0, 2.0, 3.0]),
                k=3
            )

        # Empty arrays
        with pytest.raises(ValueError, match="at least one"):
            conditional_inference_k_out_of_k(
                alpha_task_a=np.array([]),
                beta_task_a=np.array([]),
                k=3
            )

        # Invalid k
        with pytest.raises(ValueError, match="positive"):
            conditional_inference_k_out_of_k(
                alpha_task_a=np.array([1.0, 2.0]),
                beta_task_a=np.array([1.0, 2.0]),
                k=0
            )

        # Invalid ci_level
        with pytest.raises(ValueError, match="ci_level"):
            conditional_inference_k_out_of_k(
                alpha_task_a=np.array([1.0, 2.0]),
                beta_task_a=np.array([1.0, 2.0]),
                k=3,
                ci_level=1.5
            )

        # Mismatched task B shapes
        with pytest.raises(ValueError, match="same shape"):
            conditional_inference_k_out_of_k(
                alpha_task_a=np.array([1.0, 2.0]),
                beta_task_a=np.array([1.0, 2.0]),
                alpha_task_b=np.array([1.0]),
                beta_task_b=np.array([1.0, 2.0]),
                k=3
            )

        # Wrong number of scenarios for task B
        with pytest.raises(ValueError, match="same number of scenarios"):
            conditional_inference_k_out_of_k(
                alpha_task_a=np.array([1.0, 2.0]),
                beta_task_a=np.array([1.0, 2.0]),
                alpha_task_b=np.array([1.0, 2.0, 3.0]),
                beta_task_b=np.array([1.0, 2.0, 3.0]),
                k=3
            )

    def test_single_scenario(self):
        """Test with single scenario."""
        result = conditional_inference_k_out_of_k(
            alpha_task_a=np.array([10.0]),
            beta_task_a=np.array([90.0]),
            k=3,
            n_samples=10000,
            random_seed=42
        )

        assert result.n_scenarios == 1
        assert len(result.scenario_weights) == 1
        assert np.isclose(result.scenario_weights[0], 1.0)

        # With single scenario, conditioning doesn't change the distribution shape
        # (but MC estimate still computes E[θ^(k+1)] / E[θ^k])
        assert 0.0 <= result.mean <= 1.0

    def test_m_parameter_default(self):
        """Test that m defaults to 1 for backward compatibility."""
        n_scenarios = 5
        alpha = np.full(n_scenarios, 10.0)
        beta = np.full(n_scenarios, 90.0)

        # Call without specifying m
        result_default = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            n_samples=10000,
            random_seed=42
        )

        # Call with explicit m=1
        result_explicit = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            m=1,
            n_samples=10000,
            random_seed=42
        )

        # Results should be identical
        assert result_default.m == 1
        assert result_explicit.m == 1
        assert np.allclose(result_default.mean, result_explicit.mean)
        assert np.allclose(result_default.samples, result_explicit.samples)

    def test_m_greater_than_1(self):
        """Test that m > 1 produces lower values (θ^m < θ for θ < 1)."""
        n_scenarios = 5
        alpha = np.full(n_scenarios, 10.0)
        beta = np.full(n_scenarios, 90.0)

        result_m1 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            m=1,
            n_samples=50000,
            random_seed=42
        )

        result_m5 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            m=5,
            n_samples=50000,
            random_seed=42
        )

        result_m10 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            m=10,
            n_samples=50000,
            random_seed=42
        )

        # For θ < 1, θ^m decreases as m increases
        assert result_m1.mean > result_m5.mean
        assert result_m5.mean > result_m10.mean

        # All results should have correct m values stored
        assert result_m1.m == 1
        assert result_m5.m == 5
        assert result_m10.m == 10

    def test_m_fractional_values(self):
        """Test that fractional m values work correctly."""
        n_scenarios = 5
        alpha = np.full(n_scenarios, 10.0)
        beta = np.full(n_scenarios, 90.0)

        result_m1_5 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            m=1.5,
            n_samples=10000,
            random_seed=42
        )

        result_m2_5 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=3,
            m=2.5,
            n_samples=10000,
            random_seed=42
        )

        # Check that fractional m values are accepted and stored
        assert result_m1_5.m == 1.5
        assert result_m2_5.m == 2.5

        # Should follow the same ordering: smaller m → larger mean
        assert result_m1_5.mean > result_m2_5.mean

    def test_cross_conditional_with_m(self):
        """Test cross-conditional inference with m > 1."""
        n_scenarios = 5

        # Task A: filtering task
        alpha_a = np.array([10.0, 15.0, 8.0, 12.0, 11.0])
        beta_a = np.array([90.0, 85.0, 92.0, 88.0, 89.0])

        # Task B: target task (different from A)
        alpha_b = np.array([20.0, 25.0, 18.0, 22.0, 21.0])
        beta_b = np.array([80.0, 75.0, 82.0, 78.0, 79.0])

        result_m1 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha_a,
            beta_task_a=beta_a,
            alpha_task_b=alpha_b,
            beta_task_b=beta_b,
            k=3,
            m=1,
            n_samples=50000,
            random_seed=42
        )

        result_m3 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha_a,
            beta_task_a=beta_a,
            alpha_task_b=alpha_b,
            beta_task_b=beta_b,
            k=3,
            m=3,
            n_samples=50000,
            random_seed=42
        )

        # Both should return valid results
        assert 0.0 <= result_m1.mean <= 1.0
        assert 0.0 <= result_m3.mean <= 1.0

        # m=3 should give lower mean than m=1
        assert result_m3.mean < result_m1.mean

        # Check m values are stored correctly
        assert result_m1.m == 1
        assert result_m3.m == 3

    def test_invalid_m_values(self):
        """Test that invalid m values raise appropriate errors."""
        n_scenarios = 5
        alpha = np.full(n_scenarios, 10.0)
        beta = np.full(n_scenarios, 90.0)

        # Zero m
        with pytest.raises(ValueError, match="m must be positive"):
            conditional_inference_k_out_of_k(
                alpha_task_a=alpha,
                beta_task_a=beta,
                k=3,
                m=0
            )

        # Negative m
        with pytest.raises(ValueError, match="m must be positive"):
            conditional_inference_k_out_of_k(
                alpha_task_a=alpha,
                beta_task_a=beta,
                k=3,
                m=-1
            )

    def test_k_and_m_fractional(self):
        """Test that both k and m can be fractional simultaneously."""
        n_scenarios = 5
        alpha = np.full(n_scenarios, 10.0)
        beta = np.full(n_scenarios, 90.0)

        result = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=2.5,
            m=1.5,
            n_samples=10000,
            random_seed=42
        )

        # Check that both fractional values are accepted and stored
        assert result.k == 2.5
        assert result.m == 1.5
        assert 0.0 <= result.mean <= 1.0

    def test_m_interpretation(self):
        """Test interpretation: m represents probability of m/m consecutive successes."""
        n_scenarios = 3
        # Scenarios with relatively high success rates
        alpha = np.array([50.0, 60.0, 70.0])
        beta = np.array([50.0, 40.0, 30.0])

        # E[θ] ~ 0.5, 0.6, 0.7
        # E[θ^3] ~ 0.125, 0.216, 0.343 (much lower!)

        result_m1 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=1,  # Minimal filtering
            m=1,
            n_samples=50000,
            random_seed=42
        )

        result_m3 = conditional_inference_k_out_of_k(
            alpha_task_a=alpha,
            beta_task_a=beta,
            k=1,  # Minimal filtering
            m=3,
            n_samples=50000,
            random_seed=42
        )

        # With minimal filtering (k=1), result should be close to unconditional mean
        # m=1 should give ~0.6, m=3 should give significantly lower value
        assert result_m1.mean > 0.5  # High success rate scenarios
        assert result_m3.mean < result_m1.mean  # θ^3 < θ for θ < 1
        # By Jensen's inequality (g(x)=x^3 is convex): E[θ^3] ≥ (E[θ])^3
        assert result_m3.mean >= result_m1.mean ** 3 * 0.95  # Allow small tolerance
