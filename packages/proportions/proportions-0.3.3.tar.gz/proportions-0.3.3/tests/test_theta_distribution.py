"""Tests for theta distribution computation in proportions.aggregation.theta_distribution."""

import numpy as np
import pytest
from scipy.stats import beta as beta_dist

from proportions.core.models import ThetaPosterior
from proportions.aggregation.theta_distribution import (
    compute_theta_posterior,
    compute_theta_prior,
)


class TestComputeThetaPosterior:
    """Tests for compute_theta_posterior function."""

    def test_basic_computation(self):
        """Test basic posterior computation."""
        # Create simple test data
        n_samples = 1000
        alpha_samples = np.ones(n_samples) * 2.0  # All same for simplicity
        beta_samples = np.ones(n_samples) * 3.0
        weights = np.ones(n_samples) / n_samples  # Uniform weights

        result = compute_theta_posterior(
            alpha_samples,
            beta_samples,
            weights,
            n_resample=100,
            random_seed=42
        )

        # Check return type
        assert isinstance(result, ThetaPosterior)

        # Check shapes
        assert len(result.theta_grid) == 1000  # Default grid size
        assert len(result.density) == 1000
        assert result.individual_densities.shape == (100, 1000)
        assert result.n_resample == 100

        # Check density is non-negative
        assert np.all(result.density >= 0)

        # Check resampled values are reasonable
        assert np.all(result.alpha_resampled > 0)
        assert np.all(result.beta_resampled > 0)

    def test_with_custom_theta_grid(self):
        """Test with custom theta grid."""
        n_samples = 100
        alpha_samples = np.random.rand(n_samples) * 5 + 1
        beta_samples = np.random.rand(n_samples) * 5 + 1
        weights = np.ones(n_samples) / n_samples

        custom_grid = np.linspace(0.2, 0.8, 50)

        result = compute_theta_posterior(
            alpha_samples,
            beta_samples,
            weights,
            n_resample=10,
            theta_grid=custom_grid,
            random_seed=42
        )

        assert len(result.theta_grid) == 50
        assert np.allclose(result.theta_grid, custom_grid)
        assert result.individual_densities.shape == (10, 50)

    def test_reproducibility_with_seed(self):
        """Test that results are reproducible with same seed."""
        n_samples = 100
        alpha_samples = np.random.rand(n_samples) * 5 + 1
        beta_samples = np.random.rand(n_samples) * 5 + 1
        weights = np.ones(n_samples) / n_samples

        result1 = compute_theta_posterior(
            alpha_samples, beta_samples, weights, n_resample=50, random_seed=42
        )
        result2 = compute_theta_posterior(
            alpha_samples, beta_samples, weights, n_resample=50, random_seed=42
        )

        assert np.allclose(result1.density, result2.density)
        assert np.allclose(result1.alpha_resampled, result2.alpha_resampled)

    def test_importance_weighting(self):
        """Test that importance weights affect the result."""
        n_samples = 1000
        alpha_samples = np.concatenate([np.ones(500) * 2, np.ones(500) * 10])
        beta_samples = np.concatenate([np.ones(500) * 2, np.ones(500) * 10])

        # Uniform weights - should get mix of both
        uniform_weights = np.ones(n_samples) / n_samples
        result_uniform = compute_theta_posterior(
            alpha_samples, beta_samples, uniform_weights, n_resample=100, random_seed=42
        )

        # Concentrated weights - should favor first half
        concentrated_weights = np.concatenate([np.ones(500) * 0.002, np.zeros(500)])
        result_concentrated = compute_theta_posterior(
            alpha_samples, beta_samples, concentrated_weights, n_resample=100, random_seed=42
        )

        # Results should be different
        assert not np.allclose(result_uniform.density, result_concentrated.density)

    def test_validates_input_lengths(self):
        """Test that mismatched input lengths are rejected."""
        with pytest.raises(ValueError, match="same length"):
            compute_theta_posterior(
                np.ones(100),
                np.ones(50),  # Different length
                np.ones(100) / 100,
                n_resample=10
            )

    def test_validates_weights_sum(self):
        """Test that weights must sum to 1."""
        with pytest.raises(ValueError, match="sum to 1"):
            compute_theta_posterior(
                np.ones(100),
                np.ones(100),
                np.ones(100) * 0.5,  # Sum to 50, not 1
                n_resample=10
            )


class TestComputeThetaPrior:
    """Tests for compute_theta_prior function."""

    def test_basic_computation(self):
        """Test basic prior computation."""
        n_samples = 1000
        alpha_samples = np.random.rand(n_samples) * 5 + 1
        beta_samples = np.random.rand(n_samples) * 5 + 1

        result = compute_theta_prior(
            alpha_samples,
            beta_samples,
            n_resample=100,
            random_seed=42
        )

        # Check return type
        assert isinstance(result, ThetaPosterior)

        # Check shapes
        assert len(result.theta_grid) == 1000
        assert len(result.density) == 1000
        assert result.individual_densities.shape == (100, 1000)

    def test_uses_uniform_weights(self):
        """Test that prior uses uniform weights."""
        n_samples = 100
        # Create bimodal samples
        alpha_samples = np.concatenate([np.ones(50) * 2, np.ones(50) * 10])
        beta_samples = np.concatenate([np.ones(50) * 2, np.ones(50) * 10])

        result_prior = compute_theta_prior(
            alpha_samples, beta_samples, n_resample=100, random_seed=42
        )

        # Manually compute with uniform weights for comparison
        uniform_weights = np.ones(n_samples) / n_samples
        result_uniform = compute_theta_posterior(
            alpha_samples, beta_samples, uniform_weights, n_resample=100, random_seed=42
        )

        # Should give same result
        assert np.allclose(result_prior.density, result_uniform.density)

    def test_reproducibility(self):
        """Test reproducibility with seed."""
        alpha_samples = np.random.rand(100) * 5 + 1
        beta_samples = np.random.rand(100) * 5 + 1

        result1 = compute_theta_prior(alpha_samples, beta_samples, n_resample=50, random_seed=42)
        result2 = compute_theta_prior(alpha_samples, beta_samples, n_resample=50, random_seed=42)

        assert np.allclose(result1.density, result2.density)
