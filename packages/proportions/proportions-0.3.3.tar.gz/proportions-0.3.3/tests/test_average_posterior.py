"""Tests for average posterior computation functions."""

import numpy as np
import pytest

from proportions.aggregation.average_posterior import (
    compute_posterior_t_empirical_bayes,
    compute_posterior_t_from_group_posteriors,
    compute_posterior_t_hierarchical_bayes,
    compute_prior_t_hierarchical_bayes,
    compute_scenario_posteriors_hierarchical_bayes,
)
from proportions.core.models import BinomialData


class TestComputePosteriorTFromGroupPosteriors:
    """Tests for compute_posterior_t_from_group_posteriors function."""

    def test_standard_case(self):
        """Test with standard posterior parameters."""
        alpha_post = np.array([10.0, 15.0, 12.0])
        beta_post = np.array([2.0, 3.0, 2.5])

        result = compute_posterior_t_from_group_posteriors(alpha_post, beta_post)

        # Check result structure
        assert 0 < result.mu < 1
        assert result.variance > 0
        assert result.alpha_fitted > 0
        assert result.beta_fitted > 0
        assert result.ci_lower < result.mu < result.ci_upper
        assert result.ci_level == 0.95

    def test_group_indices_subset(self):
        """Test group_indices parameter with subset of groups."""
        alpha_post = np.array([10.0, 15.0, 12.0, 8.0, 20.0])
        beta_post = np.array([2.0, 3.0, 2.5, 3.0, 4.0])

        # Compute for all groups
        result_all = compute_posterior_t_from_group_posteriors(alpha_post, beta_post)

        # Compute for first 3 groups only
        result_subset = compute_posterior_t_from_group_posteriors(
            alpha_post, beta_post, group_indices=[0, 1, 2]
        )

        # Should give same result as manually subsetting
        result_manual = compute_posterior_t_from_group_posteriors(
            alpha_post[:3], beta_post[:3]
        )

        assert np.isclose(result_subset.mu, result_manual.mu, rtol=1e-10)
        assert np.isclose(result_subset.variance, result_manual.variance, rtol=1e-10)
        assert np.isclose(result_subset.ci_lower, result_manual.ci_lower, rtol=1e-10)
        assert np.isclose(result_subset.ci_upper, result_manual.ci_upper, rtol=1e-10)

        # Subset should differ from all groups
        assert not np.isclose(result_subset.mu, result_all.mu, rtol=1e-3)

    def test_group_indices_single_group(self):
        """Test group_indices with single group."""
        alpha_post = np.array([10.0, 15.0, 12.0])
        beta_post = np.array([2.0, 3.0, 2.5])

        # Select only group 1
        result = compute_posterior_t_from_group_posteriors(
            alpha_post, beta_post, group_indices=[1]
        )

        # Should match the individual group's posterior
        expected_mean = alpha_post[1] / (alpha_post[1] + beta_post[1])
        assert np.isclose(result.mu, expected_mean, rtol=1e-6)

    def test_group_indices_out_of_bounds(self):
        """Test that out-of-bounds group indices are rejected."""
        alpha_post = np.array([10.0, 15.0, 12.0])
        beta_post = np.array([2.0, 3.0, 2.5])

        with pytest.raises(ValueError, match="group_indices must be in range"):
            compute_posterior_t_from_group_posteriors(
                alpha_post, beta_post, group_indices=[0, 1, 5]  # 5 is out of bounds
            )

        with pytest.raises(ValueError, match="group_indices must be in range"):
            compute_posterior_t_from_group_posteriors(
                alpha_post, beta_post, group_indices=[-1]  # negative index
            )

    def test_group_indices_empty(self):
        """Test that empty group_indices is rejected."""
        alpha_post = np.array([10.0, 15.0, 12.0])
        beta_post = np.array([2.0, 3.0, 2.5])

        with pytest.raises(ValueError, match="group_indices cannot be empty"):
            compute_posterior_t_from_group_posteriors(
                alpha_post, beta_post, group_indices=[]
            )

    def test_identical_groups(self):
        """Test with identical posteriors for all groups."""
        # All groups have same posterior: Beta(10, 2)
        alpha_post = np.array([10.0, 10.0, 10.0])
        beta_post = np.array([2.0, 2.0, 2.0])

        result = compute_posterior_t_from_group_posteriors(alpha_post, beta_post)

        # T should have same mean as individual θᵢ
        expected_mean = 10.0 / 12.0
        assert np.isclose(result.mu, expected_mean, rtol=1e-6)

        # Variance should be reduced (divided by k² = 9 for 3 groups with weight 1/3 each)
        individual_var = (10.0 * 2.0) / (12.0**2 * 13.0)
        expected_var = individual_var / 3.0  # Var[T] = sum(w²*var) = 3*(1/3)²*var = var/3
        assert np.isclose(result.variance, expected_var, rtol=1e-6)

    def test_heterogeneous_groups(self):
        """Test with very different posteriors."""
        # One group high, one low, one medium
        alpha_post = np.array([20.0, 2.0, 10.0])
        beta_post = np.array([2.0, 20.0, 10.0])

        result = compute_posterior_t_from_group_posteriors(alpha_post, beta_post)

        # Mean should be roughly average of group means
        group_means = alpha_post / (alpha_post + beta_post)
        expected_mean = np.mean(group_means)
        assert np.isclose(result.mu, expected_mean, rtol=1e-6)

    def test_single_group(self):
        """Test with a single group."""
        alpha_post = np.array([10.0])
        beta_post = np.array([2.0])

        result = compute_posterior_t_from_group_posteriors(alpha_post, beta_post)

        # T = θ for single group
        expected_mean = 10.0 / 12.0
        assert np.isclose(result.mu, expected_mean, rtol=1e-6)

    def test_custom_ci_level(self):
        """Test with custom credible interval level."""
        alpha_post = np.array([10.0, 15.0, 12.0])
        beta_post = np.array([2.0, 3.0, 2.5])

        result = compute_posterior_t_from_group_posteriors(
            alpha_post, beta_post, ci_level=0.90
        )

        assert result.ci_level == 0.90
        # 90% CI should be narrower than 95% CI
        result_95 = compute_posterior_t_from_group_posteriors(
            alpha_post, beta_post, ci_level=0.95
        )
        assert (result.ci_upper - result.ci_lower) < (
            result_95.ci_upper - result_95.ci_lower
        )

    def test_length_mismatch_rejected(self):
        """Test that mismatched array lengths are rejected."""
        alpha_post = np.array([10.0, 15.0, 12.0])
        beta_post = np.array([2.0, 3.0])  # Different length

        with pytest.raises(ValueError, match="Length mismatch"):
            compute_posterior_t_from_group_posteriors(alpha_post, beta_post)

    def test_many_groups(self):
        """Test with many groups to verify variance reduction."""
        # 100 groups with similar posteriors
        np.random.seed(42)
        alpha_post = np.random.uniform(15.0, 20.0, size=100)
        beta_post = np.random.uniform(3.0, 5.0, size=100)

        result = compute_posterior_t_from_group_posteriors(alpha_post, beta_post)

        # With many groups, variance should be small
        assert result.variance < 0.001
        # CI should be narrow
        assert (result.ci_upper - result.ci_lower) < 0.1


class TestComputePosteriorTEmpiricalBayes:
    """Tests for compute_posterior_t_empirical_bayes function."""

    def test_standard_case(self):
        """Test with standard EB parameters and data."""
        alpha_hat = 8.0
        beta_hat = 2.0
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result = compute_posterior_t_empirical_bayes(alpha_hat, beta_hat, data)

        # Check result structure
        assert 0 < result.mu < 1
        assert result.variance > 0
        assert result.ci_lower < result.mu < result.ci_upper

    def test_strong_prior(self):
        """Test with strong prior (large α, β)."""
        # Strong prior centered at 0.8
        alpha_hat = 80.0
        beta_hat = 20.0
        # Data contradicts prior (low success rates)
        data = BinomialData(x=np.array([2, 3, 2]), n=np.array([10, 10, 10]))

        result = compute_posterior_t_empirical_bayes(alpha_hat, beta_hat, data)

        # Posterior should be pulled toward prior
        # Observed mean is 0.23, prior mean is 0.8
        # Posterior should be between but closer to prior
        observed_mean = np.sum(data.x) / np.sum(data.n)
        prior_mean = alpha_hat / (alpha_hat + beta_hat)
        assert observed_mean < result.mu < prior_mean

    def test_weak_prior(self):
        """Test with weak prior (small α, β)."""
        # Weak uniform-ish prior
        alpha_hat = 1.0
        beta_hat = 1.0
        # Strong data
        data = BinomialData(x=np.array([45, 48, 47]), n=np.array([50, 50, 50]))

        result = compute_posterior_t_empirical_bayes(alpha_hat, beta_hat, data)

        # Posterior should be close to observed data
        observed_mean = np.sum(data.x) / np.sum(data.n)
        assert np.isclose(result.mu, observed_mean, rtol=0.05)

    def test_perfect_success(self):
        """Test with all successes."""
        alpha_hat = 5.0
        beta_hat = 5.0
        data = BinomialData(x=np.array([10, 10, 10]), n=np.array([10, 10, 10]))

        result = compute_posterior_t_empirical_bayes(alpha_hat, beta_hat, data)

        # Posterior: each group is Beta(5+10, 5+0) = Beta(15, 5)
        # Mean of each group: 15/20 = 0.75
        # Prior (5,5) with mean 0.5 pulls it down from observed 1.0
        assert np.isclose(result.mu, 0.75, rtol=0.01)
        assert result.mu < 1.0  # Prior prevents exactly 1.0

    def test_perfect_failure(self):
        """Test with all failures."""
        alpha_hat = 5.0
        beta_hat = 5.0
        data = BinomialData(x=np.array([0, 0, 0]), n=np.array([10, 10, 10]))

        result = compute_posterior_t_empirical_bayes(alpha_hat, beta_hat, data)

        # Posterior: each group is Beta(5+0, 5+10) = Beta(5, 15)
        # Mean of each group: 5/20 = 0.25
        # Prior (5,5) with mean 0.5 pulls it up from observed 0.0
        assert np.isclose(result.mu, 0.25, rtol=0.01)
        assert result.mu > 0.0  # Prior prevents exactly 0.0

    def test_single_group(self):
        """Test with single group."""
        alpha_hat = 8.0
        beta_hat = 2.0
        data = BinomialData(x=np.array([7]), n=np.array([10]))

        result = compute_posterior_t_empirical_bayes(alpha_hat, beta_hat, data)

        # Should work correctly
        assert 0 < result.mu < 1
        assert result.variance > 0


class TestComputePosteriorTHierarchicalBayes:
    """Tests for compute_posterior_t_hierarchical_bayes function."""

    def test_uniform_weights(self):
        """Test with uniform weights (standard MCMC samples)."""
        # Samples from posterior of (α, β)
        np.random.seed(42)
        alpha_samples = np.random.uniform(15.0, 20.0, size=100)
        beta_samples = np.random.uniform(3.0, 5.0, size=100)

        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result = compute_posterior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data
        )

        # Check result structure
        assert 0 < result.mu < 1
        assert result.variance > 0
        assert result.ci_lower < result.mu < result.ci_upper

    def test_importance_sampling_weights(self):
        """Test with importance sampling weights."""
        np.random.seed(42)
        n_samples = 1000

        # Samples from prior
        alpha_samples = np.random.uniform(10.0, 30.0, size=n_samples)
        beta_samples = np.random.uniform(1.0, 10.0, size=n_samples)

        # Create artificial weights (peaked around α≈17, β≈3)
        weights = np.exp(
            -((alpha_samples - 17.0) ** 2) / 20.0
            - ((beta_samples - 3.0) ** 2) / 2.0
        )
        weights = weights / np.sum(weights)

        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result = compute_posterior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data, weights=weights
        )

        # Posterior should reflect the weighting
        assert 0 < result.mu < 1

    def test_hb_wider_ci_than_fixed_hyperparams(self):
        """Test that HB has wider CI than using fixed hyperparameters."""
        np.random.seed(42)
        # Variable samples around mean values
        alpha_samples = np.random.normal(17.0, 2.0, size=500)
        beta_samples = np.random.normal(3.0, 0.5, size=500)

        # Ensure positive
        alpha_samples = np.abs(alpha_samples)
        beta_samples = np.abs(beta_samples)

        data = BinomialData(x=np.array([8, 7, 9, 8, 9]), n=np.array([10, 10, 10, 10, 10]))

        # HB result (accounts for hyperparameter uncertainty)
        result_hb = compute_posterior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data
        )

        # EB-style result (fixed at mean hyperparameters)
        alpha_mean = np.mean(alpha_samples)
        beta_mean = np.mean(beta_samples)
        alpha_post = alpha_mean + data.x
        beta_post = beta_mean + (data.n - data.x)
        result_fixed = compute_posterior_t_from_group_posteriors(alpha_post, beta_post)

        # HB should have wider CI due to hyperparameter uncertainty
        hb_width = result_hb.ci_upper - result_hb.ci_lower
        fixed_width = result_fixed.ci_upper - result_fixed.ci_lower
        assert hb_width > fixed_width

        # But means should be similar
        assert np.isclose(result_hb.mu, result_fixed.mu, rtol=0.1)

    def test_length_mismatch_samples_rejected(self):
        """Test that mismatched sample lengths are rejected."""
        alpha_samples = np.array([17.0, 18.0, 16.0])
        beta_samples = np.array([3.0, 3.5])  # Different length

        data = BinomialData(x=np.array([8]), n=np.array([10]))

        with pytest.raises(ValueError, match="Length mismatch"):
            compute_posterior_t_hierarchical_bayes(alpha_samples, beta_samples, data)

    def test_length_mismatch_weights_rejected(self):
        """Test that mismatched weight length is rejected."""
        alpha_samples = np.array([17.0, 18.0, 16.0])
        beta_samples = np.array([3.0, 3.5, 2.8])
        weights = np.array([0.5, 0.5])  # Different length

        data = BinomialData(x=np.array([8]), n=np.array([10]))

        with pytest.raises(ValueError, match="Length mismatch"):
            compute_posterior_t_hierarchical_bayes(
                alpha_samples, beta_samples, data, weights=weights
            )

    def test_weights_auto_normalized(self):
        """Test that weights are automatically normalized."""
        np.random.seed(42)
        alpha_samples = np.array([17.0, 18.0, 16.0, 17.5])
        beta_samples = np.array([3.0, 3.5, 2.8, 3.2])

        # Unnormalized weights
        weights_unnorm = np.array([2.0, 3.0, 1.0, 2.5])

        data = BinomialData(x=np.array([8, 7]), n=np.array([10, 10]))

        result = compute_posterior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data, weights=weights_unnorm
        )

        # Should work (weights get normalized internally)
        assert 0 < result.mu < 1

    def test_single_sample(self):
        """Test with single sample (degenerates to fixed hyperparams)."""
        alpha_samples = np.array([17.0])
        beta_samples = np.array([3.0])

        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result = compute_posterior_t_hierarchical_bayes(alpha_samples, beta_samples, data)

        # Should match result from fixed hyperparameters
        alpha_post = 17.0 + data.x
        beta_post = 3.0 + (data.n - data.x)
        result_fixed = compute_posterior_t_from_group_posteriors(alpha_post, beta_post)

        assert np.isclose(result.mu, result_fixed.mu, rtol=1e-6)
        assert np.isclose(result.variance, result_fixed.variance, rtol=1e-6)


class TestAveragePosteriorIntegration:
    """Integration tests comparing different aggregation methods."""

    def test_eb_hb_consistency_with_point_estimate(self):
        """Test that EB and HB agree when hyperparameters are certain."""
        # HB with no uncertainty (all samples identical)
        alpha_samples = np.full(100, 17.0)
        beta_samples = np.full(100, 3.0)

        data = BinomialData(x=np.array([8, 7, 9, 8, 9]), n=np.array([10, 10, 10, 10, 10]))

        result_hb = compute_posterior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data
        )

        result_eb = compute_posterior_t_empirical_bayes(17.0, 3.0, data)

        # Should be nearly identical
        assert np.isclose(result_hb.mu, result_eb.mu, rtol=1e-6)
        assert np.isclose(result_hb.variance, result_eb.variance, rtol=1e-6)
        assert np.isclose(result_hb.ci_lower, result_eb.ci_lower, rtol=1e-5)
        assert np.isclose(result_hb.ci_upper, result_eb.ci_upper, rtol=1e-5)

    def test_variance_increases_with_hyperparameter_uncertainty(self):
        """Test that HB variance increases with hyperparameter uncertainty."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        # Low uncertainty
        np.random.seed(42)
        alpha_low = np.random.normal(17.0, 0.5, size=1000)
        beta_low = np.random.normal(3.0, 0.1, size=1000)
        alpha_low = np.abs(alpha_low)
        beta_low = np.abs(beta_low)

        result_low = compute_posterior_t_hierarchical_bayes(alpha_low, beta_low, data)

        # High uncertainty
        alpha_high = np.random.normal(17.0, 3.0, size=1000)
        beta_high = np.random.normal(3.0, 1.0, size=1000)
        alpha_high = np.abs(alpha_high)
        beta_high = np.abs(beta_high)

        result_high = compute_posterior_t_hierarchical_bayes(alpha_high, beta_high, data)

        # Higher hyperparameter uncertainty should lead to wider intervals
        assert result_high.variance > result_low.variance
        assert (result_high.ci_upper - result_high.ci_lower) > (
            result_low.ci_upper - result_low.ci_lower
        )


class TestComputePriorTHierarchicalBayes:
    """Tests for compute_prior_t_hierarchical_bayes function."""

    def test_basic_prior_computation(self):
        """Test basic prior computation from hyperparameter samples."""
        # Generate some hyperparameter samples
        np.random.seed(42)
        n_samples = 1000
        m_samples = np.random.beta(2.0, 2.0, size=n_samples)
        k_samples = np.random.uniform(1.0, 50.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result = compute_prior_t_hierarchical_bayes(alpha_samples, beta_samples, data)

        # Check result structure
        assert 0 < result.mu < 1
        assert result.variance > 0
        assert result.alpha_fitted > 0
        assert result.beta_fitted > 0
        assert result.ci_lower < result.mu < result.ci_upper
        assert result.ci_level == 0.95

    def test_prior_wider_than_posterior(self):
        """Test that prior is wider than posterior with same hyperparameter samples."""
        np.random.seed(42)
        n_samples = 1000
        m_samples = np.random.beta(2.0, 2.0, size=n_samples)
        k_samples = np.random.uniform(1.0, 50.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        # Compute prior (uniform weights)
        prior = compute_prior_t_hierarchical_bayes(alpha_samples, beta_samples, data)

        # Compute posterior with importance weights
        log_weights = np.zeros(n_samples)
        from proportions.distributions.beta import log_beta
        for i in range(n_samples):
            ll = 0.0
            for xi, ni in zip(data.x, data.n):
                ll += log_beta(alpha_samples[i] + xi, beta_samples[i] + ni - xi)
                ll -= log_beta(alpha_samples[i], beta_samples[i])
            log_weights[i] = ll

        # Normalize weights
        log_weights_normalized = log_weights - np.max(log_weights)
        weights = np.exp(log_weights_normalized)
        weights = weights / np.sum(weights)

        posterior = compute_posterior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data, weights=weights
        )

        # Prior should be wider than posterior
        assert prior.variance > posterior.variance
        assert prior.ci_width > posterior.ci_width

    def test_prior_uses_uniform_weights(self):
        """Test that prior uses uniform weights, not importance weights."""
        # Create samples with very different likelihoods
        alpha_samples = np.array([1.0, 1.0, 100.0])  # Last sample has high α
        beta_samples = np.array([1.0, 1.0, 10.0])

        # Data with many successes (should favor high α)
        data = BinomialData(x=np.array([9, 9, 9]), n=np.array([10, 10, 10]))

        # Compute prior (should weight all samples equally)
        prior = compute_prior_t_hierarchical_bayes(alpha_samples, beta_samples, data)

        # Prior mean should be close to mean of the prior means
        # E[θ] for each sample
        mean_1 = 1.0 / 2.0  # α/(α+β) = 0.5
        mean_2 = 1.0 / 2.0  # α/(α+β) = 0.5
        mean_3 = 100.0 / 110.0  # α/(α+β) ≈ 0.909

        expected_prior_mean = (mean_1 + mean_2 + mean_3) / 3

        # Should be close since we use uniform weights
        assert np.isclose(prior.mu, expected_prior_mean, rtol=0.01)

    def test_prior_with_different_ci_levels(self):
        """Test prior computation with different credible interval levels."""
        np.random.seed(42)
        alpha_samples = np.random.gamma(2.0, 5.0, size=500)
        beta_samples = np.random.gamma(2.0, 2.0, size=500)

        data = BinomialData(x=np.array([5]), n=np.array([10]))

        result_90 = compute_prior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data, ci_level=0.90
        )
        result_95 = compute_prior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data, ci_level=0.95
        )
        result_99 = compute_prior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data, ci_level=0.99
        )

        # Higher confidence level should give wider intervals
        assert result_90.ci_width < result_95.ci_width < result_99.ci_width

    def test_prior_with_group_indices(self):
        """Test prior computation with group_indices parameter."""
        np.random.seed(42)
        alpha_samples = np.random.gamma(3.0, 3.0, size=200)
        beta_samples = np.random.gamma(2.0, 1.0, size=200)

        data = BinomialData(
            x=np.array([8, 7, 9, 6, 8]),
            n=np.array([10, 10, 10, 10, 10])
        )

        # All groups
        result_all = compute_prior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data
        )

        # First 3 groups
        result_subset = compute_prior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data, group_indices=[0, 1, 2]
        )

        # Results should be different (different number of scenarios)
        # but both should be valid
        assert 0 < result_all.mu < 1
        assert 0 < result_subset.mu < 1
        assert result_all.variance > 0
        assert result_subset.variance > 0

    def test_prior_low_variance_samples(self):
        """Test prior with low variance hyperparameter samples."""
        # Use samples with low but not negligible variance
        np.random.seed(42)
        alpha_samples = np.random.normal(10.0, 0.5, size=100)
        beta_samples = np.random.normal(5.0, 0.25, size=100)
        # Ensure positive values
        alpha_samples = np.abs(alpha_samples)
        beta_samples = np.abs(beta_samples)

        data = BinomialData(x=np.array([8, 7]), n=np.array([10, 10]))

        result = compute_prior_t_hierarchical_bayes(alpha_samples, beta_samples, data)

        # With low variance samples, prior should be close to the mean value
        expected_mean = 10.0 / 15.0  # α/(α+β) ≈ 0.6667
        assert np.abs(result.mu - expected_mean) < 0.05

        # Variance should be small but positive
        assert 0 < result.variance < 0.01

    def test_prior_length_mismatch_rejected(self):
        """Test that length mismatch between alpha and beta samples is rejected."""
        alpha_samples = np.array([10.0, 12.0, 15.0])
        beta_samples = np.array([2.0, 3.0])  # Wrong length

        data = BinomialData(x=np.array([8]), n=np.array([10]))

        with pytest.raises(ValueError, match="Length mismatch"):
            compute_prior_t_hierarchical_bayes(alpha_samples, beta_samples, data)

    def test_prior_reproduces_hyperprior_mean(self):
        """Test that prior mean approximates hyperprior mean for symmetric case."""
        # Use symmetric hyperprior: m ~ Beta(2, 2) centered at 0.5
        np.random.seed(123)
        n_samples = 2000
        m_samples = np.random.beta(2.0, 2.0, size=n_samples)
        k_samples = np.random.uniform(5.0, 20.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        # Use many groups so average converges to population mean
        data = BinomialData(
            x=np.array([5, 5, 5, 5, 5]),
            n=np.array([10, 10, 10, 10, 10])
        )

        result = compute_prior_t_hierarchical_bayes(alpha_samples, beta_samples, data)

        # Prior mean should be close to 0.5 (mean of Beta(2,2))
        assert np.abs(result.mu - 0.5) < 0.05

    def test_prior_generates_actual_samples(self):
        """Test that generate_samples=True produces actual μ samples, not just conditional means."""
        np.random.seed(42)
        n_samples = 10000

        # Use tight priors that concentrate around α≈1, β≈1
        # This should give μ ≈ average of two Uniform[0,1] = triangular distribution
        m_samples = np.random.beta(50.0, 50.0, size=n_samples)  # Tight around 0.5
        k_samples = np.random.uniform(1.99, 2.01, size=n_samples)  # Tight around 2
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        # 2 groups
        data = BinomialData(x=np.array([1, 1]), n=np.array([2, 2]))

        # Get prior with samples
        result = compute_prior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data, generate_samples=True
        )

        # Check that samples were generated
        assert result.samples is not None
        assert len(result.samples) == n_samples

        # All samples should be in [0, 1]
        assert np.all((result.samples >= 0) & (result.samples <= 1))

        # With α≈1, β≈1, and k=2, we should get a triangular distribution
        # The variance of averaging 2 Uniform[0,1] variables is Var[Uniform]/k = (1/12)/2 ≈ 0.042
        # Plus small hyperprior uncertainty
        sample_var = np.var(result.samples)
        assert 0.035 < sample_var < 0.050  # Allow some tolerance for sampling variation

        # Mean should be close to 0.5
        sample_mean = np.mean(result.samples)
        assert np.abs(sample_mean - 0.5) < 0.01

        # The moment-matched mean should match the sample mean closely
        assert np.abs(result.mu - sample_mean) < 0.01

    def test_prior_without_samples(self):
        """Test that generate_samples=False does not generate samples."""
        np.random.seed(42)
        n_samples = 1000
        m_samples = np.random.beta(2.0, 2.0, size=n_samples)
        k_samples = np.random.uniform(1.0, 50.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result = compute_prior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data, generate_samples=False
        )

        # Samples should be None when not generated
        assert result.samples is None

        # But all other fields should still be computed
        assert 0 < result.mu < 1
        assert result.variance > 0
        assert result.alpha_fitted > 0
        assert result.beta_fitted > 0

    def test_posterior_generates_actual_samples(self):
        """Test that generate_samples=True produces actual μ samples for posterior."""
        np.random.seed(42)
        n_samples = 5000

        # Use tight priors that concentrate around α≈17, β≈3
        m_samples = np.random.beta(100.0, 100.0, size=n_samples) * 0.85  # Tight around 0.85
        k_samples = np.random.uniform(19.5, 20.5, size=n_samples)  # Tight around 20
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        # Data with high success rate
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        # Compute posterior with samples
        weights = np.ones(n_samples) / n_samples  # Uniform weights for simplicity
        result = compute_posterior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data, weights, generate_samples=True
        )

        # Check that samples were generated
        assert result.samples is not None
        assert len(result.samples) == n_samples

        # All samples should be in [0, 1]
        assert np.all((result.samples >= 0) & (result.samples <= 1))

        # Samples should be centered around the posterior mean
        sample_mean = np.mean(result.samples)
        assert abs(sample_mean - result.mu) < 0.02  # Should be close

        # Sample variance should be reasonable (not a spike)
        sample_var = np.var(result.samples)
        assert sample_var > 0.0001  # Should have meaningful spread

    def test_posterior_without_samples(self):
        """Test that generate_samples=False does not generate posterior samples."""
        np.random.seed(42)
        n_samples = 1000
        m_samples = np.random.beta(2.0, 2.0, size=n_samples)
        k_samples = np.random.uniform(1.0, 50.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1.0 - m_samples) * k_samples

        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))

        result = compute_posterior_t_hierarchical_bayes(
            alpha_samples, beta_samples, data, generate_samples=False
        )

        # Samples should be None when not generated
        assert result.samples is None

        # But all other fields should still be computed
        assert 0 < result.mu < 1
        assert result.variance > 0
        assert result.alpha_fitted > 0
        assert result.beta_fitted > 0

