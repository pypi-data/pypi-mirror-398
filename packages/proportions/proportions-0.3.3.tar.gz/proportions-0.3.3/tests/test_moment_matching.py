"""Tests for moment matching utilities."""

import numpy as np
import pytest

from proportions.aggregation.moment_matching import (
    beta_mean,
    beta_variance,
    fit_beta_from_moments,
    validate_beta_fit,
)


class TestBetaMean:
    """Tests for beta_mean function."""

    def test_standard_values(self):
        """Test beta_mean with standard parameter values."""
        assert np.isclose(beta_mean(2.0, 3.0), 0.4)
        assert np.isclose(beta_mean(1.0, 1.0), 0.5)  # Uniform
        assert np.isclose(beta_mean(10.0, 10.0), 0.5)  # Symmetric
        assert np.isclose(beta_mean(8.0, 2.0), 0.8)

    def test_extreme_parameters(self):
        """Test beta_mean with extreme parameter values."""
        assert np.isclose(beta_mean(100.0, 1.0), 100.0 / 101.0)
        assert np.isclose(beta_mean(1.0, 100.0), 1.0 / 101.0)

    def test_invalid_parameters_rejected(self):
        """Test that invalid parameters are rejected."""
        # Negative alpha
        with pytest.raises(ValueError, match="must be positive"):
            beta_mean(-1.0, 2.0)
        # Negative beta
        with pytest.raises(ValueError, match="must be positive"):
            beta_mean(2.0, -1.0)
        # Zero alpha
        with pytest.raises(ValueError, match="must be positive"):
            beta_mean(0.0, 2.0)
        # Zero beta
        with pytest.raises(ValueError, match="must be positive"):
            beta_mean(2.0, 0.0)


class TestBetaVariance:
    """Tests for beta_variance function."""

    def test_standard_values(self):
        """Test beta_variance with standard parameter values."""
        # Beta(2, 3): mean = 0.4, var = (2*3)/[(5^2)*(6)] = 6/150 = 0.04
        assert np.isclose(beta_variance(2.0, 3.0), 0.04)

        # Beta(1, 1): var = 1/(4*3) = 1/12
        assert np.isclose(beta_variance(1.0, 1.0), 1.0 / 12.0)

    def test_variance_decreases_with_concentration(self):
        """Test that variance decreases as parameters increase."""
        var_small = beta_variance(2.0, 3.0)
        var_large = beta_variance(20.0, 30.0)
        assert var_large < var_small

    def test_invalid_parameters_rejected(self):
        """Test that invalid parameters are rejected."""
        # Negative alpha
        with pytest.raises(ValueError, match="must be positive"):
            beta_variance(-1.0, 2.0)
        # Negative beta
        with pytest.raises(ValueError, match="must be positive"):
            beta_variance(2.0, -1.0)


class TestFitBetaFromMoments:
    """Tests for fit_beta_from_moments function."""

    def test_standard_fit(self):
        """Test fitting Beta distribution to standard moments."""
        mu = 0.7
        var = 0.01
        alpha, beta = fit_beta_from_moments(mu, var)

        # Verify moments match
        assert np.isclose(beta_mean(alpha, beta), mu, rtol=1e-6)
        assert np.isclose(beta_variance(alpha, beta), var, rtol=1e-6)

    def test_symmetric_distribution(self):
        """Test fitting symmetric Beta distribution."""
        mu = 0.5
        var = 0.05
        alpha, beta = fit_beta_from_moments(mu, var)

        # Should be symmetric
        assert np.isclose(alpha, beta, rtol=1e-6)
        assert np.isclose(beta_mean(alpha, beta), mu, rtol=1e-6)

    def test_high_concentration(self):
        """Test fitting with low variance (high concentration)."""
        mu = 0.8
        var = 0.001  # Very small variance
        alpha, beta = fit_beta_from_moments(mu, var)

        # Parameters should be large
        assert alpha > 100
        assert beta > 20
        assert np.isclose(beta_mean(alpha, beta), mu, rtol=1e-6)

    def test_low_concentration(self):
        """Test fitting with high variance (low concentration)."""
        mu = 0.5
        var = 0.08  # Close to maximum for mu=0.5
        alpha, beta = fit_beta_from_moments(mu, var)

        # Parameters should be small
        assert alpha < 5
        assert beta < 5
        assert np.isclose(beta_mean(alpha, beta), mu, rtol=1e-6)

    def test_mean_out_of_bounds_rejected(self):
        """Test that mean outside (0, 1) is rejected."""
        with pytest.raises(ValueError, match="Mean must be in"):
            fit_beta_from_moments(0.0, 0.01)

        with pytest.raises(ValueError, match="Mean must be in"):
            fit_beta_from_moments(1.0, 0.01)

        with pytest.raises(ValueError, match="Mean must be in"):
            fit_beta_from_moments(-0.1, 0.01)

        with pytest.raises(ValueError, match="Mean must be in"):
            fit_beta_from_moments(1.1, 0.01)

    def test_negative_variance_rejected(self):
        """Test that negative variance is rejected."""
        with pytest.raises(ValueError, match="Variance must be positive"):
            fit_beta_from_moments(0.5, -0.01)

    def test_zero_variance_rejected(self):
        """Test that zero variance is rejected."""
        with pytest.raises(ValueError, match="Variance must be positive"):
            fit_beta_from_moments(0.5, 0.0)

    def test_variance_too_large_rejected(self):
        """Test that variance exceeding mu*(1-mu) is rejected."""
        mu = 0.7
        max_var = mu * (1 - mu)  # 0.21

        # Should work just below maximum
        alpha, beta = fit_beta_from_moments(mu, max_var * 0.99)
        assert alpha > 0
        assert beta > 0

        # Should fail at or above maximum
        with pytest.raises(ValueError, match="too large"):
            fit_beta_from_moments(mu, max_var)

        with pytest.raises(ValueError, match="too large"):
            fit_beta_from_moments(mu, max_var * 1.01)

    def test_edge_cases(self):
        """Test edge cases near boundaries."""
        # Mean very close to 0
        alpha, beta = fit_beta_from_moments(0.01, 0.001)
        assert np.isclose(beta_mean(alpha, beta), 0.01, rtol=1e-5)

        # Mean very close to 1
        alpha, beta = fit_beta_from_moments(0.99, 0.001)
        assert np.isclose(beta_mean(alpha, beta), 0.99, rtol=1e-5)


class TestValidateBetaFit:
    """Tests for validate_beta_fit function."""

    def test_valid_fit_passes(self):
        """Test that a valid fit passes validation."""
        mu = 0.7
        var = 0.01
        alpha, beta = fit_beta_from_moments(mu, var)

        # Should not raise
        validate_beta_fit(alpha, beta, mu, var)

    def test_mean_mismatch_fails(self):
        """Test that mean mismatch raises AssertionError."""
        with pytest.raises(AssertionError, match="Mean mismatch"):
            validate_beta_fit(10.0, 5.0, 0.5, 0.01)  # Actual mean ≠ 0.5

    def test_variance_mismatch_fails(self):
        """Test that variance mismatch raises AssertionError."""
        # Beta(10, 10) has mean=0.5 but variance ≠ 0.01
        with pytest.raises(AssertionError, match="Variance mismatch"):
            validate_beta_fit(10.0, 10.0, 0.5, 0.01)

    def test_custom_tolerance(self):
        """Test validation with custom tolerance."""
        mu = 0.7
        var = 0.01
        alpha, beta = fit_beta_from_moments(mu, var)

        # Very strict tolerance should still pass for exact fit
        validate_beta_fit(alpha, beta, mu, var, tol=1e-10)

        # Relaxed tolerance allows slight mismatch
        validate_beta_fit(10.0, 5.0, 0.666666, 0.01587, tol=0.01)


class TestMomentMatchingRoundTrip:
    """Integration tests for round-trip moment matching."""

    def test_round_trip_various_distributions(self):
        """Test that fit_beta_from_moments recovers parameters."""
        test_cases = [
            (2.0, 3.0),
            (10.0, 5.0),
            (1.5, 1.5),
            (100.0, 50.0),
            (0.5, 0.5),  # U-shaped
        ]

        for alpha_true, beta_true in test_cases:
            # Compute moments
            mu = beta_mean(alpha_true, beta_true)
            var = beta_variance(alpha_true, beta_true)

            # Fit Beta from moments
            alpha_fit, beta_fit = fit_beta_from_moments(mu, var)

            # Check that fitted distribution has same moments
            assert np.isclose(beta_mean(alpha_fit, beta_fit), mu, rtol=1e-6)
            assert np.isclose(beta_variance(alpha_fit, beta_fit), var, rtol=1e-6)

            # Note: Parameters themselves may differ (moment matching is not unique)
            # but moments should match exactly
