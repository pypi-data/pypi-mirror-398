"""Tests for single proportion inference.

This module tests Bayesian inference functions for a single binomial proportion
with support for truncated Beta priors.
"""

import numpy as np
import pytest
from scipy.stats import beta as scipy_beta

from proportions.inference.single_proportion import (
    conf_interval_proportion,
    lower_bound_proportion,
    upper_bound_proportion,
    prob_larger_than_threshold,
    prob_smaller_than_threshold,
    prob_of_interval,
)


class TestConfidenceIntervals:
    """Tests for credible interval functions."""

    def test_conf_interval_basic(self):
        """Test basic confidence interval computation."""
        # 30 successes out of 100 trials
        interval = conf_interval_proportion(30, 100, confidence=0.95)

        assert len(interval) == 2
        assert interval[0] < interval[1]
        # Should be roughly centered around 0.3
        assert 0.2 < interval[0] < 0.3
        assert 0.3 < interval[1] < 0.4

    def test_conf_interval_uniform_prior(self):
        """Test with uniform prior (default)."""
        interval = conf_interval_proportion(
            30, 100, confidence=0.95, prior_alpha=1.0, prior_beta=1.0
        )

        # Posterior is Beta(31, 71)
        # Should match scipy quantiles
        expected_lower = scipy_beta.ppf(0.025, 31, 71)
        expected_upper = scipy_beta.ppf(0.975, 31, 71)

        assert np.isclose(interval[0], expected_lower, rtol=1e-6)
        assert np.isclose(interval[1], expected_upper, rtol=1e-6)

    def test_conf_interval_jeffreys_prior(self):
        """Test with Jeffreys prior."""
        interval = conf_interval_proportion(
            30, 100, confidence=0.95, prior_alpha=0.5, prior_beta=0.5
        )

        # Posterior is Beta(30.5, 70.5)
        expected_lower = scipy_beta.ppf(0.025, 30.5, 70.5)
        expected_upper = scipy_beta.ppf(0.975, 30.5, 70.5)

        assert np.isclose(interval[0], expected_lower, rtol=1e-6)
        assert np.isclose(interval[1], expected_upper, rtol=1e-6)

    def test_conf_interval_edge_case_zero_successes(self):
        """Test with 0 successes."""
        interval = conf_interval_proportion(0, 100, confidence=0.95)

        assert interval[0] >= 0.0
        assert interval[1] < 0.1  # Should be small
        assert interval[0] < interval[1]

    def test_conf_interval_edge_case_all_successes(self):
        """Test with all successes."""
        interval = conf_interval_proportion(100, 100, confidence=0.95)

        assert interval[0] > 0.9  # Should be high
        assert interval[1] <= 1.0
        assert interval[0] < interval[1]

    def test_conf_interval_with_truncation(self):
        """Test confidence interval with truncated prior."""
        # Truncate to [0.2, 0.8]
        interval = conf_interval_proportion(
            30, 100, confidence=0.95, lower=0.2, upper=0.8
        )

        # Interval should be within truncation bounds
        assert interval[0] >= 0.2
        assert interval[1] <= 0.8
        assert interval[0] < interval[1]

    def test_conf_interval_different_confidence_levels(self):
        """Test that wider confidence gives wider intervals."""
        interval_90 = conf_interval_proportion(30, 100, confidence=0.90)
        interval_95 = conf_interval_proportion(30, 100, confidence=0.95)
        interval_99 = conf_interval_proportion(30, 100, confidence=0.99)

        width_90 = interval_90[1] - interval_90[0]
        width_95 = interval_95[1] - interval_95[0]
        width_99 = interval_99[1] - interval_99[0]

        # Higher confidence should give wider intervals
        assert width_90 < width_95 < width_99

    def test_conf_interval_returns_array(self):
        """Test that result is a numpy array."""
        interval = conf_interval_proportion(30, 100)
        assert isinstance(interval, np.ndarray)
        assert interval.shape == (2,)


class TestOneSidedBounds:
    """Tests for one-sided credible bounds."""

    def test_upper_bound_basic(self):
        """Test basic upper bound computation."""
        ub = upper_bound_proportion(30, 100, confidence=0.95)

        # Should be above the point estimate
        assert ub > 0.3
        # But not too high
        assert ub < 0.5

    def test_upper_bound_matches_quantile(self):
        """Test that upper bound matches Beta quantile."""
        ub = upper_bound_proportion(30, 100, confidence=0.95, prior_alpha=1.0, prior_beta=1.0)

        # Posterior is Beta(31, 71)
        expected = scipy_beta.ppf(0.95, 31, 71)
        assert np.isclose(ub, expected, rtol=1e-6)

    def test_lower_bound_basic(self):
        """Test basic lower bound computation."""
        lb = lower_bound_proportion(30, 100, confidence=0.95)

        # Should be below the point estimate
        assert lb < 0.3
        # But not too low
        assert lb > 0.1

    def test_lower_bound_matches_quantile(self):
        """Test that lower bound matches Beta quantile."""
        lb = lower_bound_proportion(30, 100, confidence=0.95, prior_alpha=1.0, prior_beta=1.0)

        # Posterior is Beta(31, 71)
        # Lower bound at 95% confidence means P(θ > lb) = 0.95, so lb is 5th percentile
        expected = scipy_beta.ppf(0.05, 31, 71)
        assert np.isclose(lb, expected, rtol=1e-6)

    def test_bounds_consistency_with_interval(self):
        """Test that one-sided bounds are consistent with two-sided interval."""
        interval = conf_interval_proportion(30, 100, confidence=0.90)
        lb = lower_bound_proportion(30, 100, confidence=0.95)
        ub = upper_bound_proportion(30, 100, confidence=0.95)

        # 95% one-sided bounds should match 90% two-sided interval
        assert np.isclose(lb, interval[0], rtol=1e-6)
        assert np.isclose(ub, interval[1], rtol=1e-6)

    def test_upper_bound_with_truncation(self):
        """Test upper bound with truncated prior."""
        ub = upper_bound_proportion(30, 100, confidence=0.95, lower=0.2, upper=0.8)

        # Should be within truncation bounds
        assert 0.2 <= ub <= 0.8

    def test_lower_bound_with_truncation(self):
        """Test lower bound with truncated prior."""
        lb = lower_bound_proportion(30, 100, confidence=0.95, lower=0.2, upper=0.8)

        # Should be within truncation bounds
        assert 0.2 <= lb <= 0.8

    def test_bounds_edge_case_zero_successes(self):
        """Test bounds with 0 successes."""
        lb = lower_bound_proportion(0, 100, confidence=0.95)
        ub = upper_bound_proportion(0, 100, confidence=0.95)

        assert lb >= 0.0
        assert ub < 0.1
        assert lb < ub

    def test_bounds_edge_case_all_successes(self):
        """Test bounds with all successes."""
        lb = lower_bound_proportion(100, 100, confidence=0.95)
        ub = upper_bound_proportion(100, 100, confidence=0.95)

        assert lb > 0.9
        assert ub <= 1.0
        assert lb < ub


class TestThresholdProbabilities:
    """Tests for threshold probability functions."""

    def test_prob_larger_than_threshold_basic(self):
        """Test basic probability larger than threshold."""
        # 30 successes out of 100
        prob = prob_larger_than_threshold(30, 100, threshold=0.25)

        # Should be fairly high probability (point estimate is 0.3)
        assert 0.5 < prob < 1.0

    def test_prob_larger_than_threshold_matches_cdf(self):
        """Test that prob_larger matches 1 - CDF."""
        # Posterior is Beta(31, 71) with uniform prior
        prob = prob_larger_than_threshold(30, 100, threshold=0.25, prior_alpha=1.0, prior_beta=1.0)

        expected = 1 - scipy_beta.cdf(0.25, 31, 71)
        assert np.isclose(prob, expected, rtol=1e-6)

    def test_prob_smaller_than_threshold_basic(self):
        """Test basic probability smaller than threshold."""
        # 30 successes out of 100
        prob = prob_smaller_than_threshold(30, 100, threshold=0.35)

        # Should be fairly high probability (point estimate is 0.3)
        assert 0.5 < prob < 1.0

    def test_prob_smaller_than_threshold_matches_cdf(self):
        """Test that prob_smaller matches CDF."""
        # Posterior is Beta(31, 71) with uniform prior
        prob = prob_smaller_than_threshold(30, 100, threshold=0.35, prior_alpha=1.0, prior_beta=1.0)

        expected = scipy_beta.cdf(0.35, 31, 71)
        assert np.isclose(prob, expected, rtol=1e-6)

    def test_prob_larger_and_smaller_sum_to_one(self):
        """Test that P(θ > t) + P(θ < t) ≈ 1 (ignoring P(θ = t) = 0)."""
        threshold = 0.3
        prob_larger = prob_larger_than_threshold(30, 100, threshold)
        prob_smaller = prob_smaller_than_threshold(30, 100, threshold)

        # Should sum to approximately 1
        assert np.isclose(prob_larger + prob_smaller, 1.0, rtol=1e-6)

    def test_prob_larger_extreme_thresholds(self):
        """Test probability larger with extreme thresholds."""
        # Very low threshold - should be nearly 1
        prob_low = prob_larger_than_threshold(30, 100, threshold=0.01)
        assert prob_low > 0.99

        # Very high threshold - should be nearly 0
        prob_high = prob_larger_than_threshold(30, 100, threshold=0.99)
        assert prob_high < 0.01

    def test_prob_smaller_extreme_thresholds(self):
        """Test probability smaller with extreme thresholds."""
        # Very low threshold - should be nearly 0
        prob_low = prob_smaller_than_threshold(30, 100, threshold=0.01)
        assert prob_low < 0.01

        # Very high threshold - should be nearly 1
        prob_high = prob_smaller_than_threshold(30, 100, threshold=0.99)
        assert prob_high > 0.99

    def test_prob_larger_with_truncation(self):
        """Test probability larger with truncated prior."""
        prob = prob_larger_than_threshold(
            30, 100, threshold=0.3, lower=0.2, upper=0.8
        )

        # Should be valid probability
        assert 0.0 <= prob <= 1.0

    def test_prob_smaller_with_truncation(self):
        """Test probability smaller with truncated prior."""
        prob = prob_smaller_than_threshold(
            30, 100, threshold=0.3, lower=0.2, upper=0.8
        )

        # Should be valid probability
        assert 0.0 <= prob <= 1.0


class TestIntervalProbabilities:
    """Tests for interval probability function."""

    def test_prob_of_interval_basic(self):
        """Test basic interval probability."""
        # 30 successes out of 100
        prob = prob_of_interval(30, 100, lb=0.25, ub=0.35)

        # Should be fairly high (point estimate is 0.3)
        assert 0.3 < prob < 1.0

    def test_prob_of_interval_matches_cdf_difference(self):
        """Test that prob_of_interval matches CDF(ub) - CDF(lb)."""
        # Posterior is Beta(31, 71) with uniform prior
        prob = prob_of_interval(30, 100, lb=0.25, ub=0.35, prior_alpha=1.0, prior_beta=1.0)

        cdf_lb = scipy_beta.cdf(0.25, 31, 71)
        cdf_ub = scipy_beta.cdf(0.35, 31, 71)
        expected = cdf_ub - cdf_lb

        assert np.isclose(prob, expected, rtol=1e-6)

    def test_prob_of_interval_full_range(self):
        """Test that full range [0, 1] gives probability 1."""
        prob = prob_of_interval(30, 100, lb=0.0, ub=1.0)

        assert np.isclose(prob, 1.0, atol=1e-6)

    def test_prob_of_interval_narrow(self):
        """Test with very narrow interval."""
        prob = prob_of_interval(30, 100, lb=0.299, ub=0.301)

        # Should be small but positive
        assert 0.0 < prob < 0.1

    def test_prob_of_interval_wide(self):
        """Test with wide interval."""
        prob = prob_of_interval(30, 100, lb=0.1, ub=0.9)

        # Should be very high
        assert prob > 0.95

    def test_prob_of_interval_with_truncation(self):
        """Test interval probability with truncated prior."""
        prob = prob_of_interval(30, 100, lb=0.25, ub=0.35, lower=0.2, upper=0.8)

        # Should be valid probability
        assert 0.0 <= prob <= 1.0

    def test_prob_of_interval_consistency(self):
        """Test consistency: P([0, t]) = P(θ < t)."""
        threshold = 0.35
        prob_interval = prob_of_interval(30, 100, lb=0.0, ub=threshold)
        prob_smaller = prob_smaller_than_threshold(30, 100, threshold)

        assert np.isclose(prob_interval, prob_smaller, rtol=1e-6)

    def test_prob_of_interval_edge_case_lb_equals_ub(self):
        """Test that P([t, t]) = 0 for continuous distribution."""
        prob = prob_of_interval(30, 100, lb=0.3, ub=0.3)

        # Should be essentially 0 (or very close)
        assert prob < 1e-10


class TestInputValidation:
    """Tests for input validation and edge cases."""

    def test_invalid_success_count(self):
        """Test that negative success count raises error."""
        with pytest.raises(ValueError):
            conf_interval_proportion(-1, 100)

    def test_invalid_trial_count(self):
        """Test that negative trial count raises error."""
        with pytest.raises(ValueError):
            conf_interval_proportion(30, -100)

    def test_success_greater_than_trials(self):
        """Test that success > trials raises error."""
        with pytest.raises(ValueError):
            conf_interval_proportion(101, 100)

    def test_invalid_confidence_level(self):
        """Test that invalid confidence level raises error."""
        with pytest.raises(ValueError):
            conf_interval_proportion(30, 100, confidence=1.5)

        with pytest.raises(ValueError):
            conf_interval_proportion(30, 100, confidence=-0.1)

    def test_invalid_prior_alpha(self):
        """Test that invalid prior alpha raises error."""
        with pytest.raises(ValueError):
            conf_interval_proportion(30, 100, prior_alpha=-1.0)

        with pytest.raises(ValueError):
            conf_interval_proportion(30, 100, prior_alpha=0.0)

    def test_invalid_prior_beta(self):
        """Test that invalid prior beta raises error."""
        with pytest.raises(ValueError):
            conf_interval_proportion(30, 100, prior_beta=-1.0)

        with pytest.raises(ValueError):
            conf_interval_proportion(30, 100, prior_beta=0.0)

    def test_invalid_truncation_bounds(self):
        """Test that invalid truncation bounds raise error."""
        # lower >= upper
        with pytest.raises(ValueError):
            conf_interval_proportion(30, 100, lower=0.8, upper=0.2)

        # lower = upper
        with pytest.raises(ValueError):
            conf_interval_proportion(30, 100, lower=0.5, upper=0.5)

        # lower < 0
        with pytest.raises(ValueError):
            conf_interval_proportion(30, 100, lower=-0.1, upper=0.8)

        # upper > 1
        with pytest.raises(ValueError):
            conf_interval_proportion(30, 100, lower=0.2, upper=1.1)

    def test_invalid_threshold(self):
        """Test that invalid threshold raises error."""
        with pytest.raises(ValueError):
            prob_larger_than_threshold(30, 100, threshold=-0.1)

        with pytest.raises(ValueError):
            prob_larger_than_threshold(30, 100, threshold=1.1)

    def test_invalid_interval_bounds(self):
        """Test that invalid interval bounds raise error."""
        # lb > ub
        with pytest.raises(ValueError):
            prob_of_interval(30, 100, lb=0.6, ub=0.4)
