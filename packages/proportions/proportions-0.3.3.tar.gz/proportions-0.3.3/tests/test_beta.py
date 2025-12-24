"""Tests for Beta distribution utilities in proportions.distributions.beta."""

import math

import numpy as np
import pytest
from scipy import stats as scipy_stats

from proportions.distributions.beta import (
    log_beta,
    beta_cdf,
    beta_ppf,
    beta_quantiles,
    beta_mode,
)


class TestLogBeta:
    """Tests for log_beta function."""

    def test_standard_values(self):
        """Test against known values."""
        # Beta(2, 3) = Γ(2)Γ(3)/Γ(5) = 1*2/24 = 1/12
        expected = math.log(1.0 / 12.0)
        result = log_beta(2.0, 3.0)
        assert np.isclose(result, expected, rtol=1e-10)

    def test_compare_to_scipy(self):
        """Compare against scipy.special.betaln."""
        from scipy.special import betaln

        test_cases = [
            (1.0, 1.0),
            (2.0, 2.0),
            (0.5, 0.5),
            (10.0, 5.0),
            (100.0, 50.0),
        ]

        for a, b in test_cases:
            expected = betaln(a, b)
            result = log_beta(a, b)
            assert np.isclose(result, expected, rtol=1e-12), f"Failed for Beta({a}, {b})"

    def test_symmetry(self):
        """Test that log_beta(a, b) == log_beta(b, a)."""
        assert np.isclose(log_beta(5.0, 10.0), log_beta(10.0, 5.0))
        assert np.isclose(log_beta(2.5, 7.3), log_beta(7.3, 2.5))


class TestBetaCDF:
    """Tests for beta_cdf function."""

    def test_boundary_values(self):
        """Test CDF at boundaries."""
        # CDF(0) should be 0
        assert np.isclose(beta_cdf(0.0, 2.0, 3.0), 0.0)

        # CDF(1) should be 1
        assert np.isclose(beta_cdf(1.0, 2.0, 3.0), 1.0)

    def test_median_symmetric_beta(self):
        """Test that CDF(0.5) = 0.5 for Beta(a, a)."""
        # For symmetric Beta(a, a), the median is 0.5
        assert np.isclose(beta_cdf(0.5, 2.0, 2.0), 0.5, rtol=1e-10)
        assert np.isclose(beta_cdf(0.5, 5.0, 5.0), 0.5, rtol=1e-10)

    def test_compare_to_scipy(self):
        """Compare against scipy.stats.beta.cdf."""
        test_cases = [
            (0.3, 2.0, 3.0),
            (0.5, 2.0, 2.0),
            (0.7, 5.0, 2.0),
            (0.9, 10.0, 5.0),
            (0.1, 0.5, 0.5),
        ]

        for x, a, b in test_cases:
            expected = scipy_stats.beta.cdf(x, a, b)
            result = beta_cdf(x, a, b)
            assert np.isclose(result, expected, rtol=1e-8), \
                f"Failed for Beta({a}, {b}) at x={x}"

    def test_monotonicity(self):
        """Test that CDF is monotonically increasing."""
        a, b = 2.0, 3.0
        x_vals = np.linspace(0.0, 1.0, 100)
        cdf_vals = [beta_cdf(x, a, b) for x in x_vals]

        # Check that CDF is non-decreasing
        for i in range(1, len(cdf_vals)):
            assert cdf_vals[i] >= cdf_vals[i-1], "CDF is not monotonic"


class TestBetaPPF:
    """Tests for beta_ppf (quantile) function."""

    def test_boundary_values(self):
        """Test quantile function at boundaries."""
        # Q(0) should be 0
        assert beta_ppf(0.0, 2.0, 3.0) == 0.0

        # Q(1) should be 1
        assert beta_ppf(1.0, 2.0, 3.0) == 1.0

    def test_median_symmetric_beta(self):
        """Test that Q(0.5) = 0.5 for Beta(a, a)."""
        assert np.isclose(beta_ppf(0.5, 2.0, 2.0), 0.5, rtol=1e-6)
        assert np.isclose(beta_ppf(0.5, 5.0, 5.0), 0.5, rtol=1e-6)

    def test_compare_to_scipy(self):
        """Compare against scipy.stats.beta.ppf."""
        test_cases = [
            (0.025, 2.0, 2.0),
            (0.5, 2.0, 3.0),
            (0.975, 2.0, 2.0),
            (0.1, 5.0, 2.0),
            (0.9, 10.0, 5.0),
        ]

        for p, a, b in test_cases:
            expected = scipy_stats.beta.ppf(p, a, b)
            result = beta_ppf(p, a, b)
            assert np.isclose(result, expected, rtol=1e-6), \
                f"Failed for Beta({a}, {b}) at p={p}"

    def test_inverse_of_cdf(self):
        """Test that ppf is inverse of cdf."""
        test_cases = [
            (0.3, 2.0, 3.0),
            (0.5, 2.0, 2.0),
            (0.7, 5.0, 2.0),
        ]

        for x, a, b in test_cases:
            # CDF then PPF should return x
            p = beta_cdf(x, a, b)
            x_recovered = beta_ppf(p, a, b)
            assert np.isclose(x_recovered, x, rtol=1e-6), \
                f"PPF not inverse of CDF for Beta({a}, {b})"

    def test_ppf_then_cdf(self):
        """Test that cdf(ppf(p)) = p."""
        test_cases = [
            (0.025, 2.0, 3.0),
            (0.5, 2.0, 2.0),
            (0.975, 5.0, 2.0),
        ]

        for p, a, b in test_cases:
            # PPF then CDF should return p
            x = beta_ppf(p, a, b)
            p_recovered = beta_cdf(x, a, b)
            assert np.isclose(p_recovered, p, rtol=1e-6), \
                f"CDF not inverse of PPF for Beta({a}, {b})"

    def test_quantiles_increasing(self):
        """Test that quantiles are monotonically increasing."""
        a, b = 2.0, 3.0
        probs = np.linspace(0.0, 1.0, 20)
        quantiles = [beta_ppf(p, a, b) for p in probs]

        # Check that quantiles are non-decreasing
        for i in range(1, len(quantiles)):
            assert quantiles[i] >= quantiles[i-1], "Quantiles are not monotonic"


class TestBetaQuantiles:
    """Tests for beta_quantiles vectorized function."""

    def test_vectorized_matches_scalar(self):
        """Test that vectorized version matches scalar calls."""
        probs = np.array([0.025, 0.5, 0.975])
        a, b = 2.0, 3.0

        # Vectorized
        quantiles_vec = beta_quantiles(probs, a, b)

        # Scalar
        quantiles_scalar = np.array([beta_ppf(p, a, b) for p in probs])

        np.testing.assert_allclose(quantiles_vec, quantiles_scalar, rtol=1e-10)

    def test_compare_to_scipy(self):
        """Compare vectorized version against scipy."""
        probs = np.array([0.025, 0.1, 0.5, 0.9, 0.975])
        a, b = 5.0, 2.0

        expected = scipy_stats.beta.ppf(probs, a, b)
        result = beta_quantiles(probs, a, b)

        np.testing.assert_allclose(result, expected, rtol=1e-6)


class TestNumericalStability:
    """Tests for numerical stability with extreme parameters."""

    def test_large_parameters(self):
        """Test with large shape parameters."""
        # Beta(100, 100) is very concentrated around 0.5
        p = 0.5
        a, b = 100.0, 100.0

        # Should not overflow/underflow
        x = beta_ppf(p, a, b)
        assert 0.0 < x < 1.0
        assert np.isfinite(x)

        # Check it's close to the mode (which is 0.5 for symmetric)
        assert np.isclose(x, 0.5, rtol=1e-3)

    def test_small_parameters(self):
        """Test with small shape parameters."""
        # Beta(0.5, 0.5) is U-shaped
        p = 0.5
        a, b = 0.5, 0.5

        x = beta_ppf(p, a, b)
        assert 0.0 < x < 1.0
        assert np.isfinite(x)

        # For Beta(0.5, 0.5), median is 0.5
        assert np.isclose(x, 0.5, rtol=1e-3)

    def test_extreme_quantiles(self):
        """Test extreme quantiles don't cause issues."""
        a, b = 2.0, 3.0

        # Very small probability
        x_low = beta_ppf(1e-10, a, b)
        assert 0.0 <= x_low < 0.1
        assert np.isfinite(x_low)

        # Very high probability
        x_high = beta_ppf(1.0 - 1e-10, a, b)
        assert 0.9 < x_high <= 1.0
        assert np.isfinite(x_high)

    def test_skewed_distributions(self):
        """Test with highly skewed distributions."""
        # Very skewed right
        a, b = 0.5, 10.0
        x = beta_ppf(0.5, a, b)
        assert 0.0 < x < 0.2  # Median should be very low
        assert np.isfinite(x)

        # Very skewed left
        a, b = 10.0, 0.5
        x = beta_ppf(0.5, a, b)
        assert 0.8 < x < 1.0  # Median should be very high
        assert np.isfinite(x)


class TestConvergenceErrors:
    """Tests for convergence error handling."""

    def test_beta_ppf_max_iterations_exceeded(self):
        """Test that beta_ppf raises RuntimeError when max iterations exceeded."""
        from proportions.distributions.beta import beta_ppf

        # Use maxiter=1 with a non-trivial quantile to force non-convergence
        with pytest.raises(RuntimeError, match="beta_ppf did not converge"):
            beta_ppf(0.5, 2.0, 3.0, tol=1e-15, maxiter=1)

    def test_betacf_convergence_error(self):
        """Test betacf raises RuntimeError when maxiter is insufficient."""
        from proportions.distributions.beta import betacf

        # Force non-convergence by setting maxiter=1
        with pytest.raises(RuntimeError, match="betacf did not converge"):
            betacf(2.0, 3.0, 0.5, maxiter=1)


class TestEdgeCases:
    """Tests for edge cases and special values."""

    def test_uniform_distribution(self):
        """Test Beta(1, 1) which is uniform."""
        # For uniform, CDF(x) = x and PPF(p) = p
        x_vals = [0.0, 0.25, 0.5, 0.75, 1.0]

        for x in x_vals:
            assert np.isclose(beta_cdf(x, 1.0, 1.0), x, rtol=1e-10)

        p_vals = [0.0, 0.25, 0.5, 0.75, 1.0]
        for p in p_vals:
            assert np.isclose(beta_ppf(p, 1.0, 1.0), p, rtol=1e-6)

    def test_consistency_across_range(self):
        """Test consistency across full range of probabilities."""
        a, b = 3.0, 7.0
        probs = np.linspace(0.01, 0.99, 50)

        for p in probs:
            x = beta_ppf(p, a, b)
            p_recovered = beta_cdf(x, a, b)
            assert np.isclose(p_recovered, p, rtol=1e-5), \
                f"Inconsistent at p={p}: got {p_recovered}"


class TestBetaMode:
    """Tests for beta_mode function."""

    def test_interior_mode_symmetric(self):
        """Test mode for symmetric Beta distribution."""
        # Beta(2, 2) has mode at 0.5
        assert np.isclose(beta_mode(2.0, 2.0), 0.5, rtol=1e-10)

        # Beta(5, 5) has mode at 0.5
        assert np.isclose(beta_mode(5.0, 5.0), 0.5, rtol=1e-10)

        # Beta(10, 10) has mode at 0.5
        assert np.isclose(beta_mode(10.0, 10.0), 0.5, rtol=1e-10)

    def test_interior_mode_asymmetric(self):
        """Test mode for asymmetric Beta distributions."""
        # Beta(5, 2): mode = (5-1)/(5+2-2) = 4/5 = 0.8
        assert np.isclose(beta_mode(5.0, 2.0), 0.8, rtol=1e-10)

        # Beta(2, 5): mode = (2-1)/(2+5-2) = 1/5 = 0.2
        assert np.isclose(beta_mode(2.0, 5.0), 0.2, rtol=1e-10)

        # Beta(10, 3): mode = (10-1)/(10+3-2) = 9/11
        expected = 9.0 / 11.0
        assert np.isclose(beta_mode(10.0, 3.0), expected, rtol=1e-10)

    def test_right_boundary_mode(self):
        """Test mode at right boundary when beta <= 1."""
        # Beta(22.15, 0.99): mode = 1.0 (right boundary)
        assert beta_mode(22.15, 0.99) == 1.0

        # Beta(5, 1): mode = 1.0
        assert beta_mode(5.0, 1.0) == 1.0

        # Beta(10, 0.5): mode = 1.0
        assert beta_mode(10.0, 0.5) == 1.0

        # Beta(2, 0.1): mode = 1.0
        assert beta_mode(2.0, 0.1) == 1.0

    def test_left_boundary_mode(self):
        """Test mode at left boundary when alpha <= 1."""
        # Beta(0.5, 5): mode = 0.0 (left boundary)
        assert beta_mode(0.5, 5.0) == 0.0

        # Beta(1, 5): mode = 0.0
        assert beta_mode(1.0, 5.0) == 0.0

        # Beta(0.1, 10): mode = 0.0
        assert beta_mode(0.1, 10.0) == 0.0

        # Beta(0.99, 2): mode = 0.0
        assert beta_mode(0.99, 2.0) == 0.0

    def test_bimodal_fallback_to_mean(self):
        """Test fallback to mean for bimodal distributions."""
        # Beta(0.5, 0.5): bimodal at 0 and 1, mean = 0.5
        assert np.isclose(beta_mode(0.5, 0.5), 0.5, rtol=1e-10)

        # Beta(1, 1): uniform, mean = 0.5
        assert np.isclose(beta_mode(1.0, 1.0), 0.5, rtol=1e-10)

        # Beta(0.8, 0.3): bimodal, mean = 0.8/(0.8+0.3)
        expected = 0.8 / (0.8 + 0.3)
        assert np.isclose(beta_mode(0.8, 0.3), expected, rtol=1e-10)

    def test_mode_matches_scipy_when_interior(self):
        """Test that mode matches scipy for interior modes."""
        from scipy.stats import beta as scipy_beta

        test_cases = [
            (2.0, 2.0),
            (5.0, 2.0),
            (2.0, 5.0),
            (10.0, 3.0),
            (3.5, 7.2),
        ]

        for a, b in test_cases:
            # For interior modes, scipy doesn't have a direct mode method,
            # but we can compute it manually
            expected = (a - 1) / (a + b - 2)
            result = beta_mode(a, b)
            assert np.isclose(result, expected, rtol=1e-10), \
                f"Failed for Beta({a}, {b})"

    def test_mode_maximizes_pdf(self):
        """Test that mode is the value that maximizes the PDF."""
        from scipy.stats import beta as scipy_beta

        test_cases = [
            (2.0, 2.0),
            (5.0, 2.0),
            (2.0, 5.0),
            (22.15, 0.99),  # Right boundary mode
            (0.5, 5.0),      # Left boundary mode
        ]

        for a, b in test_cases:
            mode = beta_mode(a, b)

            # For boundary modes, check near the boundary
            if mode == 0.0:
                test_points = [0.01, 0.05, 0.1, 0.2]
            elif mode == 1.0:
                test_points = [0.99, 0.95, 0.9, 0.8]
            else:
                # For interior modes, test nearby points
                test_points = [mode - 0.01, mode + 0.01, mode - 0.05, mode + 0.05]
                test_points = [p for p in test_points if 0 < p < 1]

            pdf_at_mode = scipy_beta.pdf(mode, a, b)

            for test_point in test_points:
                pdf_at_test = scipy_beta.pdf(test_point, a, b)
                # Mode should have PDF >= any other point
                assert pdf_at_mode >= pdf_at_test - 1e-8, \
                    f"Mode {mode} doesn't maximize PDF for Beta({a}, {b})"

    def test_invalid_parameters(self):
        """Test that invalid parameters raise ValueError."""
        with pytest.raises(ValueError, match="Shape parameters must be positive"):
            beta_mode(0.0, 2.0)

        with pytest.raises(ValueError, match="Shape parameters must be positive"):
            beta_mode(2.0, 0.0)

        with pytest.raises(ValueError, match="Shape parameters must be positive"):
            beta_mode(-1.0, 2.0)

        with pytest.raises(ValueError, match="Shape parameters must be positive"):
            beta_mode(2.0, -1.0)

    def test_mode_type(self):
        """Test that mode returns a float."""
        result = beta_mode(2.0, 3.0)
        assert isinstance(result, float)

    def test_real_world_posteriors(self):
        """Test mode computation for real posterior distributions."""
        # Example from commit analysis: 2025-11-08
        # Beta(22.15, 0.99) - high failure rate with right boundary mode
        assert beta_mode(22.15, 0.99) == 1.0

        # Example from commit analysis: 2025-12-05
        # Beta(646.55, 684.32) - balanced posterior
        mode = beta_mode(646.55, 684.32)
        expected = (646.55 - 1) / (646.55 + 684.32 - 2)
        assert np.isclose(mode, expected, rtol=1e-10)

        # Check it's near 0.5 as expected
        assert 0.48 < mode < 0.50

