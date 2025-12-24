"""Tests for truncated Beta distribution.

This module tests the truncated Beta distribution functions, which extend
the standard Beta distribution to support truncation to arbitrary intervals [lower, upper].
"""

import numpy as np
import pytest
from scipy.stats import beta as scipy_beta

from proportions.distributions.truncated_beta import (
    log_truncated_beta_partition,
    truncated_beta_partition,
    truncated_beta_pdf,
    truncated_beta_cdf,
    truncated_beta_ppf,
)


class TestTruncatedBetaPartition:
    """Tests for truncated Beta partition function."""

    def test_no_truncation_equals_one(self):
        """Test that partition with no truncation equals 1."""
        # Standard Beta (no truncation) should have partition = 1
        Z = truncated_beta_partition(2.0, 3.0, lower=0.0, upper=1.0)
        assert np.isclose(Z, 1.0)

    def test_log_partition_no_truncation_equals_zero(self):
        """Test that log partition with no truncation equals 0."""
        log_Z = log_truncated_beta_partition(2.0, 3.0, lower=0.0, upper=1.0)
        assert np.isclose(log_Z, 0.0)

    def test_partition_with_truncation(self):
        """Test partition with actual truncation bounds."""
        # Truncate to [0.2, 0.8]
        Z = truncated_beta_partition(2.0, 3.0, lower=0.2, upper=0.8)

        # Should be less than 1 (some probability mass removed)
        assert Z < 1.0
        assert Z > 0.0

        # Should match scipy calculation
        expected = scipy_beta.cdf(0.8, 2.0, 3.0) - scipy_beta.cdf(0.2, 2.0, 3.0)
        assert np.isclose(Z, expected)

    def test_partition_consistency_with_log(self):
        """Test that exp(log_partition) equals partition."""
        alpha, beta_param = 5.0, 7.0
        lower, upper = 0.1, 0.9

        Z = truncated_beta_partition(alpha, beta_param, lower, upper)
        log_Z = log_truncated_beta_partition(alpha, beta_param, lower, upper)

        assert np.isclose(Z, np.exp(log_Z))

    def test_partition_full_range_various_parameters(self):
        """Test partition equals 1 for various parameter combinations."""
        test_params = [
            (0.5, 0.5),  # Jeffreys prior
            (1.0, 1.0),  # Uniform
            (2.0, 5.0),  # Informative
            (10.0, 2.0), # Informative skewed
        ]

        for alpha, beta_param in test_params:
            Z = truncated_beta_partition(alpha, beta_param, 0.0, 1.0)
            assert np.isclose(Z, 1.0, atol=1e-10)

    def test_partition_narrow_truncation(self):
        """Test partition with very narrow truncation bounds."""
        # Narrow interval [0.49, 0.51]
        Z = truncated_beta_partition(2.0, 2.0, lower=0.49, upper=0.51)

        # Should be small but positive
        assert 0.0 < Z < 0.1
        assert np.isfinite(Z)

    def test_partition_extreme_parameters(self):
        """Test numerical stability with extreme parameters."""
        # Large alpha, beta
        Z_large = truncated_beta_partition(100.0, 100.0, 0.4, 0.6)
        assert np.isfinite(Z_large)
        assert Z_large > 0

        # Small alpha, beta
        Z_small = truncated_beta_partition(0.1, 0.1, 0.1, 0.9)
        assert np.isfinite(Z_small)
        assert Z_small > 0


class TestTruncatedBetaPDF:
    """Tests for truncated Beta PDF."""

    def test_pdf_no_truncation_matches_standard_beta(self):
        """Test that PDF with no truncation matches standard Beta."""
        alpha, beta_param = 2.0, 3.0
        x_vals = np.linspace(0.01, 0.99, 20)

        for x in x_vals:
            pdf_truncated = truncated_beta_pdf(x, alpha, beta_param, 0.0, 1.0)
            pdf_scipy = scipy_beta.pdf(x, alpha, beta_param)
            assert np.isclose(pdf_truncated, pdf_scipy, rtol=1e-10)

    def test_pdf_zero_outside_bounds(self):
        """Test that PDF is zero outside truncation bounds."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.2, 0.8

        # Test single values
        assert truncated_beta_pdf(0.1, alpha, beta_param, lower, upper) == 0.0
        assert truncated_beta_pdf(0.9, alpha, beta_param, lower, upper) == 0.0
        assert truncated_beta_pdf(0.0, alpha, beta_param, lower, upper) == 0.0
        assert truncated_beta_pdf(1.0, alpha, beta_param, lower, upper) == 0.0

    def test_pdf_positive_inside_bounds(self):
        """Test that PDF is positive inside truncation bounds."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.2, 0.8

        x_vals = np.linspace(0.21, 0.79, 10)
        for x in x_vals:
            pdf_val = truncated_beta_pdf(x, alpha, beta_param, lower, upper)
            assert pdf_val > 0.0

    def test_pdf_integrates_to_one(self):
        """Test that PDF integrates to approximately 1 over truncation bounds."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.3, 0.7

        # Numerical integration using trapezoidal rule
        x_vals = np.linspace(lower, upper, 1000)
        pdf_vals = np.array([truncated_beta_pdf(x, alpha, beta_param, lower, upper)
                            for x in x_vals])
        integral = np.trapz(pdf_vals, x_vals)

        assert np.isclose(integral, 1.0, atol=1e-3)

    def test_pdf_vectorized(self):
        """Test that PDF works with array inputs."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.2, 0.8

        x_vals = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        pdf_vals = truncated_beta_pdf(x_vals, alpha, beta_param, lower, upper)

        assert pdf_vals.shape == x_vals.shape
        assert pdf_vals[0] == 0.0  # Outside bounds
        assert pdf_vals[1] > 0.0   # Inside bounds
        assert pdf_vals[2] > 0.0   # Inside bounds
        assert pdf_vals[3] > 0.0   # Inside bounds
        assert pdf_vals[4] == 0.0  # Outside bounds

    def test_pdf_normalization_factor(self):
        """Test that truncated PDF is scaled correctly relative to standard Beta."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.3, 0.7
        x = 0.5

        # Get partition constant
        Z = truncated_beta_partition(alpha, beta_param, lower, upper)

        # Truncated PDF should be standard PDF divided by Z
        pdf_standard = scipy_beta.pdf(x, alpha, beta_param)
        pdf_truncated = truncated_beta_pdf(x, alpha, beta_param, lower, upper)

        assert np.isclose(pdf_truncated, pdf_standard / Z, rtol=1e-10)


class TestTruncatedBetaCDF:
    """Tests for truncated Beta CDF."""

    def test_cdf_no_truncation_matches_standard_beta(self):
        """Test that CDF with no truncation matches standard Beta."""
        alpha, beta_param = 2.0, 3.0
        x_vals = np.linspace(0.01, 0.99, 20)

        for x in x_vals:
            cdf_truncated = truncated_beta_cdf(x, alpha, beta_param, 0.0, 1.0)
            cdf_scipy = scipy_beta.cdf(x, alpha, beta_param)
            assert np.isclose(cdf_truncated, cdf_scipy, rtol=1e-10)

    def test_cdf_bounds(self):
        """Test CDF boundary conditions."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.2, 0.8

        # CDF should be 0 below lower bound
        assert truncated_beta_cdf(0.0, alpha, beta_param, lower, upper) == 0.0
        assert truncated_beta_cdf(0.1, alpha, beta_param, lower, upper) == 0.0
        assert truncated_beta_cdf(lower - 0.01, alpha, beta_param, lower, upper) == 0.0

        # CDF should be 1 above upper bound
        assert truncated_beta_cdf(1.0, alpha, beta_param, lower, upper) == 1.0
        assert truncated_beta_cdf(0.9, alpha, beta_param, lower, upper) == 1.0
        assert truncated_beta_cdf(upper + 0.01, alpha, beta_param, lower, upper) == 1.0

    def test_cdf_at_truncation_points(self):
        """Test CDF at exactly the truncation bounds."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.3, 0.7

        # At lower bound, CDF should be 0
        cdf_lower = truncated_beta_cdf(lower, alpha, beta_param, lower, upper)
        assert np.isclose(cdf_lower, 0.0, atol=1e-10)

        # At upper bound, CDF should be 1
        cdf_upper = truncated_beta_cdf(upper, alpha, beta_param, lower, upper)
        assert np.isclose(cdf_upper, 1.0, atol=1e-10)

    def test_cdf_monotonically_increasing(self):
        """Test that CDF is monotonically increasing."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.2, 0.8

        x_vals = np.linspace(0.0, 1.0, 50)
        cdf_vals = np.array([truncated_beta_cdf(x, alpha, beta_param, lower, upper)
                            for x in x_vals])

        # Check monotonicity
        diffs = np.diff(cdf_vals)
        assert np.all(diffs >= -1e-10)  # Allow small numerical errors

    def test_cdf_vectorized(self):
        """Test that CDF works with array inputs."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.2, 0.8

        x_vals = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        cdf_vals = truncated_beta_cdf(x_vals, alpha, beta_param, lower, upper)

        assert cdf_vals.shape == x_vals.shape
        assert cdf_vals[0] == 0.0     # Below lower
        assert 0.0 < cdf_vals[1] < 1.0  # Inside
        assert 0.0 < cdf_vals[2] < 1.0  # Inside
        assert 0.0 < cdf_vals[3] < 1.0  # Inside
        assert cdf_vals[4] == 1.0     # Above upper

    def test_cdf_formula_consistency(self):
        """Test that CDF formula is correct."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.3, 0.7
        x = 0.5

        # Manual calculation
        Z = truncated_beta_partition(alpha, beta_param, lower, upper)
        cdf_lower = scipy_beta.cdf(lower, alpha, beta_param)
        cdf_x = scipy_beta.cdf(x, alpha, beta_param)
        expected_cdf = (cdf_x - cdf_lower) / Z

        # Library function
        actual_cdf = truncated_beta_cdf(x, alpha, beta_param, lower, upper)

        assert np.isclose(actual_cdf, expected_cdf, rtol=1e-10)


class TestTruncatedBetaPPF:
    """Tests for truncated Beta PPF (inverse CDF)."""

    def test_ppf_no_truncation_matches_standard_beta(self):
        """Test that PPF with no truncation matches standard Beta."""
        alpha, beta_param = 2.0, 3.0
        q_vals = np.linspace(0.01, 0.99, 20)

        for q in q_vals:
            ppf_truncated = truncated_beta_ppf(q, alpha, beta_param, 0.0, 1.0)
            ppf_scipy = scipy_beta.ppf(q, alpha, beta_param)
            assert np.isclose(ppf_truncated, ppf_scipy, rtol=1e-6)

    def test_ppf_bounds(self):
        """Test PPF boundary conditions."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.2, 0.8

        # q=0 should give lower bound
        ppf_0 = truncated_beta_ppf(0.0, alpha, beta_param, lower, upper)
        assert np.isclose(ppf_0, lower, atol=1e-10)

        # q=1 should give upper bound
        ppf_1 = truncated_beta_ppf(1.0, alpha, beta_param, lower, upper)
        assert np.isclose(ppf_1, upper, atol=1e-10)

    def test_ppf_monotonically_increasing(self):
        """Test that PPF is monotonically increasing."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.3, 0.7

        q_vals = np.linspace(0.0, 1.0, 50)
        ppf_vals = np.array([truncated_beta_ppf(q, alpha, beta_param, lower, upper)
                            for q in q_vals])

        # Check monotonicity
        diffs = np.diff(ppf_vals)
        assert np.all(diffs >= -1e-10)  # Allow small numerical errors

    def test_ppf_within_truncation_bounds(self):
        """Test that PPF always returns values within truncation bounds."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.2, 0.8

        q_vals = np.linspace(0.0, 1.0, 100)
        for q in q_vals:
            ppf_val = truncated_beta_ppf(q, alpha, beta_param, lower, upper)
            assert lower <= ppf_val <= upper

    def test_ppf_inverse_of_cdf(self):
        """Test that PPF is the inverse of CDF."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.3, 0.7

        # Test q -> x -> q' round trip
        q_vals = np.array([0.1, 0.25, 0.5, 0.75, 0.9])
        for q in q_vals:
            x = truncated_beta_ppf(q, alpha, beta_param, lower, upper)
            q_recovered = truncated_beta_cdf(x, alpha, beta_param, lower, upper)
            assert np.isclose(q, q_recovered, rtol=1e-6)

        # Test x -> q -> x' round trip
        x_vals = np.linspace(lower + 0.01, upper - 0.01, 10)
        for x in x_vals:
            q = truncated_beta_cdf(x, alpha, beta_param, lower, upper)
            x_recovered = truncated_beta_ppf(q, alpha, beta_param, lower, upper)
            assert np.isclose(x, x_recovered, rtol=1e-6)

    def test_ppf_median(self):
        """Test that PPF at q=0.5 gives reasonable median."""
        alpha, beta_param = 2.0, 2.0  # Symmetric
        lower, upper = 0.2, 0.8

        median = truncated_beta_ppf(0.5, alpha, beta_param, lower, upper)

        # For symmetric Beta(2,2), median should be at 0.5
        # With truncation [0.2, 0.8], should still be near 0.5
        assert 0.4 < median < 0.6

    def test_ppf_vectorized(self):
        """Test that PPF works with array inputs."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.2, 0.8

        q_vals = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        ppf_vals = truncated_beta_ppf(q_vals, alpha, beta_param, lower, upper)

        assert ppf_vals.shape == q_vals.shape
        assert np.isclose(ppf_vals[0], lower)
        assert lower < ppf_vals[1] < upper
        assert lower < ppf_vals[2] < upper
        assert lower < ppf_vals[3] < upper
        assert np.isclose(ppf_vals[4], upper)


class TestTruncatedBetaEdgeCases:
    """Tests for edge cases and numerical stability."""

    def test_jeffreys_prior(self):
        """Test with Jeffreys prior (alpha=0.5, beta=0.5)."""
        alpha, beta_param = 0.5, 0.5
        lower, upper = 0.1, 0.9

        Z = truncated_beta_partition(alpha, beta_param, lower, upper)
        assert np.isfinite(Z)
        assert Z > 0

        pdf_val = truncated_beta_pdf(0.5, alpha, beta_param, lower, upper)
        assert np.isfinite(pdf_val)
        assert pdf_val > 0

    def test_uniform_prior(self):
        """Test with uniform prior (alpha=1, beta=1)."""
        alpha, beta_param = 1.0, 1.0
        lower, upper = 0.25, 0.75

        # Partition should be 0.5 (width of interval)
        Z = truncated_beta_partition(alpha, beta_param, lower, upper)
        assert np.isclose(Z, 0.5)

        # PDF should be constant at 2.0 (1 / 0.5)
        x_vals = np.linspace(0.3, 0.7, 10)
        pdf_vals = [truncated_beta_pdf(x, alpha, beta_param, lower, upper) for x in x_vals]
        assert np.allclose(pdf_vals, 2.0, rtol=1e-10)

    def test_highly_informative_prior(self):
        """Test with highly peaked prior."""
        alpha, beta_param = 100.0, 100.0
        lower, upper = 0.4, 0.6

        Z = truncated_beta_partition(alpha, beta_param, lower, upper)
        assert np.isfinite(Z)

        # Most mass should be near 0.5
        median = truncated_beta_ppf(0.5, alpha, beta_param, lower, upper)
        assert np.isclose(median, 0.5, atol=0.01)

    def test_narrow_truncation(self):
        """Test with very narrow truncation interval."""
        alpha, beta_param = 2.0, 3.0
        lower, upper = 0.499, 0.501

        Z = truncated_beta_partition(alpha, beta_param, lower, upper)
        assert np.isfinite(Z)
        assert Z > 0

        # All quantiles should be close to 0.5
        q_vals = np.array([0.1, 0.5, 0.9])
        ppf_vals = truncated_beta_ppf(q_vals, alpha, beta_param, lower, upper)
        assert np.all(np.abs(ppf_vals - 0.5) < 0.002)

    def test_extreme_truncation_bounds(self):
        """Test with truncation near 0 or 1."""
        alpha, beta_param = 2.0, 2.0

        # Near 0
        Z_low = truncated_beta_partition(alpha, beta_param, 0.01, 0.1)
        assert np.isfinite(Z_low)

        # Near 1
        Z_high = truncated_beta_partition(alpha, beta_param, 0.9, 0.99)
        assert np.isfinite(Z_high)

    def test_skewed_prior_with_truncation(self):
        """Test skewed prior with asymmetric truncation."""
        alpha, beta_param = 8.0, 2.0  # Right-skewed
        lower, upper = 0.3, 0.9

        # Should handle correctly
        median = truncated_beta_ppf(0.5, alpha, beta_param, lower, upper)
        assert lower < median < upper

        # Median should be relatively high (right-skewed)
        assert median > 0.6
