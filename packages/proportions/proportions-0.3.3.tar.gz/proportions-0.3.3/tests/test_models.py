"""Tests for core data models in proportions.core.models."""

import numpy as np
import pytest

from proportions.core.models import (
    BinomialData,
    PosteriorResult,
    EmpiricalBayesResult,
    ImportanceSamplingDiagnostics,
    HierarchicalBayesResult,
    ThetaPosterior,
)


class TestBinomialData:
    """Tests for BinomialData model."""

    def test_valid_data(self):
        """Test creation with valid data."""
        data = BinomialData(
            x=np.array([8, 7, 9]),
            n=np.array([10, 10, 10])
        )
        assert data.n_groups == 3
        assert data.n_total_trials == 30
        assert data.n_total_successes == 24
        assert np.isclose(data.pooled_rate, 0.8)

    def test_empty_arrays_rejected(self):
        """Test that empty arrays are rejected."""
        with pytest.raises(ValueError, match="non-empty"):
            BinomialData(x=np.array([]), n=np.array([]))

    def test_mismatched_lengths_rejected(self):
        """Test that mismatched array lengths are rejected."""
        with pytest.raises(ValueError, match="same length"):
            BinomialData(
                x=np.array([8, 7]),
                n=np.array([10, 10, 10])
            )

    def test_negative_x_rejected(self):
        """Test that negative success counts are rejected."""
        with pytest.raises(ValueError, match="non-negative"):
            BinomialData(
                x=np.array([8, -1, 9]),
                n=np.array([10, 10, 10])
            )

    def test_zero_n_rejected(self):
        """Test that zero trial counts are rejected."""
        with pytest.raises(ValueError, match="positive"):
            BinomialData(
                x=np.array([8, 7, 9]),
                n=np.array([10, 0, 10])
            )

    def test_negative_n_rejected(self):
        """Test that negative trial counts are rejected."""
        with pytest.raises(ValueError, match="positive"):
            BinomialData(
                x=np.array([8, 7, 9]),
                n=np.array([10, -5, 10])
            )

    def test_x_exceeds_n_rejected(self):
        """Test that x > n is rejected."""
        with pytest.raises(ValueError, match="cannot exceed"):
            BinomialData(
                x=np.array([8, 11, 9]),
                n=np.array([10, 10, 10])
            )

    def test_boundary_cases(self):
        """Test boundary cases: all successes, all failures."""
        # All successes
        data = BinomialData(
            x=np.array([10, 10, 10]),
            n=np.array([10, 10, 10])
        )
        assert data.pooled_rate == 1.0

        # All failures
        data = BinomialData(
            x=np.array([0, 0, 0]),
            n=np.array([10, 10, 10])
        )
        assert data.pooled_rate == 0.0

    def test_observed_rates(self):
        """Test that observed rates are computed correctly."""
        data = BinomialData(
            x=np.array([8, 7, 9]),
            n=np.array([10, 10, 10])
        )
        expected = np.array([0.8, 0.7, 0.9])
        np.testing.assert_array_almost_equal(data.observed_rates, expected)

    def test_single_group(self):
        """Test with a single group."""
        data = BinomialData(
            x=np.array([8]),
            n=np.array([10])
        )
        assert data.n_groups == 1
        assert data.pooled_rate == 0.8


class TestPosteriorResult:
    """Tests for PosteriorResult model."""

    def test_valid_posterior(self):
        """Test creation with valid posterior."""
        result = PosteriorResult(
            mu=0.8,
            variance=0.001,
            alpha_fitted=100.0,
            beta_fitted=20.0,
            ci_lower=0.75,
            ci_upper=0.85
        )
        assert result.mu == 0.8
        assert np.isclose(result.std, np.sqrt(0.001))
        assert np.isclose(result.ci_width, 0.1)

    def test_mu_out_of_bounds_rejected(self):
        """Test that mu outside [0,1] is rejected."""
        with pytest.raises(ValueError):
            PosteriorResult(
                mu=1.5,
                variance=0.001,
                alpha_fitted=100.0,
                beta_fitted=20.0,
                ci_lower=0.75,
                ci_upper=0.85
            )

    def test_negative_variance_rejected(self):
        """Test that negative variance is rejected."""
        with pytest.raises(ValueError):
            PosteriorResult(
                mu=0.8,
                variance=-0.001,
                alpha_fitted=100.0,
                beta_fitted=20.0,
                ci_lower=0.75,
                ci_upper=0.85
            )

    def test_inverted_ci_rejected(self):
        """Test that ci_lower > ci_upper is rejected."""
        with pytest.raises(ValueError, match="ci_lower"):
            PosteriorResult(
                mu=0.8,
                variance=0.001,
                alpha_fitted=100.0,
                beta_fitted=20.0,
                ci_lower=0.85,
                ci_upper=0.75
            )

    def test_mu_outside_ci_rejected(self):
        """Test that mu outside CI is rejected."""
        with pytest.raises(ValueError, match="within CI"):
            PosteriorResult(
                mu=0.9,
                variance=0.001,
                alpha_fitted=100.0,
                beta_fitted=20.0,
                ci_lower=0.75,
                ci_upper=0.85
            )

    def test_custom_ci_level(self):
        """Test with custom CI level."""
        result = PosteriorResult(
            mu=0.8,
            variance=0.001,
            alpha_fitted=100.0,
            beta_fitted=20.0,
            ci_level=0.90,
            ci_lower=0.76,
            ci_upper=0.84
        )
        assert result.ci_level == 0.90


class TestEmpiricalBayesResult:
    """Tests for EmpiricalBayesResult model."""

    def test_valid_result(self):
        """Test creation with valid result."""
        posterior = PosteriorResult(
            mu=0.8,
            variance=0.001,
            alpha_fitted=100.0,
            beta_fitted=20.0,
            ci_lower=0.75,
            ci_upper=0.85
        )
        result = EmpiricalBayesResult(
            m_hat=0.8,
            k_hat=120.0,
            alpha_hat=96.0,
            beta_hat=24.0,
            log_marginal_likelihood=-100.0,
            posterior=posterior,
            n_groups=10,
            n_total_trials=100,
            n_total_successes=80
        )
        assert result.method == 'empirical_bayes'
        assert result.m_hat == 0.8
        assert result.k_hat == 120.0

    def test_inconsistent_alpha_rejected(self):
        """Test that inconsistent alpha is rejected."""
        posterior = PosteriorResult(
            mu=0.8,
            variance=0.001,
            alpha_fitted=100.0,
            beta_fitted=20.0,
            ci_lower=0.75,
            ci_upper=0.85
        )
        with pytest.raises(ValueError, match="alpha_hat.*inconsistent"):
            EmpiricalBayesResult(
                m_hat=0.8,
                k_hat=120.0,
                alpha_hat=100.0,  # Should be 0.8 * 120 = 96
                beta_hat=24.0,
                log_marginal_likelihood=-100.0,
                posterior=posterior,
                n_groups=10,
                n_total_trials=100,
                n_total_successes=80
            )

    def test_inconsistent_beta_rejected(self):
        """Test that inconsistent beta is rejected."""
        posterior = PosteriorResult(
            mu=0.8,
            variance=0.001,
            alpha_fitted=100.0,
            beta_fitted=20.0,
            ci_lower=0.75,
            ci_upper=0.85
        )
        with pytest.raises(ValueError, match="beta_hat.*inconsistent"):
            EmpiricalBayesResult(
                m_hat=0.8,
                k_hat=120.0,
                alpha_hat=96.0,
                beta_hat=30.0,  # Should be 0.2 * 120 = 24
                log_marginal_likelihood=-100.0,
                posterior=posterior,
                n_groups=10,
                n_total_trials=100,
                n_total_successes=80
            )


class TestImportanceSamplingDiagnostics:
    """Tests for ImportanceSamplingDiagnostics model."""

    def test_valid_diagnostics(self):
        """Test creation with valid diagnostics."""
        diag = ImportanceSamplingDiagnostics(
            n_samples=2000,
            effective_sample_size=150.0,
            k_mean=50.0,
            k_std=10.0,
            k_q05=35.0,
            k_q95=65.0,
            k_at_boundary=False,
            k_at_lower=False,
            k_at_upper=False,
            m_mean=0.85,
            m_std=0.05,
            m_q05=0.75,
            m_q95=0.92
        )
        assert diag.n_samples == 2000
        assert diag.effective_sample_size == 150.0
        assert np.isclose(diag.ess_ratio, 150.0 / 2000)

    def test_boundary_flags(self):
        """Test boundary detection flags."""
        diag = ImportanceSamplingDiagnostics(
            n_samples=2000,
            effective_sample_size=10.0,
            k_mean=950.0,
            k_std=30.0,
            k_q05=900.0,
            k_q95=990.0,
            k_at_boundary=True,
            k_at_lower=False,
            k_at_upper=True,
            m_mean=0.85,
            m_std=0.05,
            m_q05=0.75,
            m_q95=0.92
        )
        assert diag.k_at_boundary is True
        assert diag.k_at_upper is True
        assert diag.k_at_lower is False


class TestHierarchicalBayesResult:
    """Tests for HierarchicalBayesResult model."""

    def test_valid_result(self):
        """Test creation with valid result."""
        posterior = PosteriorResult(
            mu=0.8,
            variance=0.002,
            alpha_fitted=100.0,
            beta_fitted=20.0,
            ci_lower=0.74,
            ci_upper=0.86
        )
        diagnostics = ImportanceSamplingDiagnostics(
            n_samples=2000,
            effective_sample_size=150.0,
            k_mean=50.0,
            k_std=10.0,
            k_q05=35.0,
            k_q95=65.0,
            k_at_boundary=False,
            k_at_lower=False,
            k_at_upper=False,
            m_mean=0.85,
            m_std=0.05,
            m_q05=0.75,
            m_q95=0.92
        )
        result = HierarchicalBayesResult(
            m_posterior_mean=0.8,
            k_posterior_mean=120.0,
            alpha_posterior_mean=96.0,
            beta_posterior_mean=24.0,
            posterior=posterior,
            variance_within=0.001,
            variance_between=0.001,
            diagnostics=diagnostics,
            log_marginal_likelihood=-100.0,
            n_groups=10,
            n_total_trials=100,
            n_total_successes=80
        )
        assert result.method == 'hierarchical_bayes'
        assert result.variance_within == 0.001
        assert result.variance_between == 0.001

    def test_inconsistent_alpha_posterior_rejected(self):
        """Test that inconsistent alpha_posterior is rejected."""
        posterior = PosteriorResult(
            mu=0.8,
            variance=0.002,
            alpha_fitted=100.0,
            beta_fitted=20.0,
            ci_lower=0.74,
            ci_upper=0.86
        )
        diagnostics = ImportanceSamplingDiagnostics(
            n_samples=2000,
            effective_sample_size=150.0,
            k_mean=50.0,
            k_std=10.0,
            k_q05=35.0,
            k_q95=65.0,
            k_at_boundary=False,
            k_at_lower=False,
            k_at_upper=False,
            m_mean=0.85,
            m_std=0.05,
            m_q05=0.75,
            m_q95=0.92
        )

        # This should fail because alpha != m*k (100 != 0.8*120=96)
        with pytest.raises(ValueError, match="alpha inconsistent with m\\*k"):
            HierarchicalBayesResult(
                m_posterior_mean=0.8,
                k_posterior_mean=120.0,
                alpha_posterior_mean=100.0,  # Should be 96
                beta_posterior_mean=24.0,
                posterior=posterior,
                variance_within=0.001,
                variance_between=0.001,
                diagnostics=diagnostics,
                log_marginal_likelihood=-100.0,
                n_groups=10,
                n_total_trials=100,
                n_total_successes=80
            )

    def test_inconsistent_beta_posterior_rejected(self):
        """Test that inconsistent beta_posterior is rejected."""
        posterior = PosteriorResult(
            mu=0.8,
            variance=0.002,
            alpha_fitted=100.0,
            beta_fitted=20.0,
            ci_lower=0.74,
            ci_upper=0.86
        )
        diagnostics = ImportanceSamplingDiagnostics(
            n_samples=2000,
            effective_sample_size=150.0,
            k_mean=50.0,
            k_std=10.0,
            k_q05=35.0,
            k_q95=65.0,
            k_at_boundary=False,
            k_at_lower=False,
            k_at_upper=False,
            m_mean=0.85,
            m_std=0.05,
            m_q05=0.75,
            m_q95=0.92
        )

        # This should fail because beta != (1-m)*k (30 != 0.2*120=24)
        with pytest.raises(ValueError, match="beta inconsistent with"):
            HierarchicalBayesResult(
                m_posterior_mean=0.8,
                k_posterior_mean=120.0,
                alpha_posterior_mean=96.0,
                beta_posterior_mean=30.0,  # Should be 24
                posterior=posterior,
                variance_within=0.001,
                variance_between=0.001,
                diagnostics=diagnostics,
                log_marginal_likelihood=-100.0,
                n_groups=10,
                n_total_trials=100,
                n_total_successes=80
            )

    def test_variance_decomposition_validated(self):
        """Test that variance decomposition is validated."""
        posterior = PosteriorResult(
            mu=0.8,
            variance=0.003,  # Should equal within + between
            alpha_fitted=100.0,
            beta_fitted=20.0,
            ci_lower=0.74,
            ci_upper=0.86
        )
        diagnostics = ImportanceSamplingDiagnostics(
            n_samples=2000,
            effective_sample_size=150.0,
            k_mean=50.0,
            k_std=10.0,
            k_q05=35.0,
            k_q95=65.0,
            k_at_boundary=False,
            k_at_lower=False,
            k_at_upper=False,
            m_mean=0.85,
            m_std=0.05,
            m_q05=0.75,
            m_q95=0.92
        )

        # This should fail because 0.001 + 0.001 = 0.002 != 0.003
        with pytest.raises(ValueError, match="Variance decomposition"):
            HierarchicalBayesResult(
                m_posterior_mean=0.8,
                k_posterior_mean=120.0,
                alpha_posterior_mean=96.0,
                beta_posterior_mean=24.0,
                posterior=posterior,
                variance_within=0.001,
                variance_between=0.001,  # Sum = 0.002, but posterior.variance = 0.003
                diagnostics=diagnostics,
                log_marginal_likelihood=-100.0,
                n_groups=10,
                n_total_trials=100,
                n_total_successes=80
            )


class TestThetaPosterior:
    """Tests for ThetaPosterior model."""

    def test_valid_theta_posterior(self):
        """Test creation with valid data."""
        theta_grid = np.linspace(0, 1, 100)
        n_resample = 50
        individual_densities = np.random.rand(n_resample, 100)

        theta_post = ThetaPosterior(
            theta_grid=theta_grid,
            density=individual_densities.mean(axis=0),
            individual_densities=individual_densities,
            alpha_resampled=np.random.rand(n_resample) * 5 + 1,
            beta_resampled=np.random.rand(n_resample) * 5 + 1,
            n_resample=n_resample
        )

        assert len(theta_post.theta_grid) == 100
        assert len(theta_post.density) == 100
        assert theta_post.individual_densities.shape == (50, 100)
        assert theta_post.n_resample == 50

    def test_empty_theta_grid_rejected(self):
        """Test that empty theta grid is rejected."""
        with pytest.raises(ValueError, match="non-empty"):
            ThetaPosterior(
                theta_grid=np.array([]),
                density=np.array([]),
                individual_densities=np.array([[]]),
                alpha_resampled=np.array([1.0]),
                beta_resampled=np.array([1.0]),
                n_resample=1
            )

    def test_theta_grid_outside_bounds_rejected(self):
        """Test that theta grid values outside [0,1] are rejected."""
        with pytest.raises(ValueError, match="must be in"):
            ThetaPosterior(
                theta_grid=np.array([0.0, 0.5, 1.5]),  # 1.5 > 1
                density=np.array([1.0, 1.0, 1.0]),
                individual_densities=np.array([[1.0, 1.0, 1.0]]),
                alpha_resampled=np.array([2.0]),
                beta_resampled=np.array([2.0]),
                n_resample=1
            )

    def test_negative_density_rejected(self):
        """Test that negative density values are rejected."""
        with pytest.raises(ValueError, match="non-negative"):
            ThetaPosterior(
                theta_grid=np.linspace(0, 1, 10),
                density=np.array([-0.1] + [1.0] * 9),  # Negative value
                individual_densities=np.ones((5, 10)),
                alpha_resampled=np.ones(5),
                beta_resampled=np.ones(5),
                n_resample=5
            )

    def test_density_shape_mismatch_rejected(self):
        """Test that density with wrong shape is rejected."""
        with pytest.raises(ValueError, match="density length"):
            ThetaPosterior(
                theta_grid=np.linspace(0, 1, 10),
                density=np.ones(5),  # Should be length 10
                individual_densities=np.ones((5, 10)),
                alpha_resampled=np.ones(5),
                beta_resampled=np.ones(5),
                n_resample=5
            )

    def test_individual_densities_shape_mismatch_rejected(self):
        """Test that individual_densities with wrong shape is rejected."""
        with pytest.raises(ValueError, match="individual_densities shape"):
            ThetaPosterior(
                theta_grid=np.linspace(0, 1, 10),
                density=np.ones(10),
                individual_densities=np.ones((5, 8)),  # Should be (5, 10)
                alpha_resampled=np.ones(5),
                beta_resampled=np.ones(5),
                n_resample=5
            )

    def test_zero_n_resample_rejected(self):
        """Test that n_resample <= 0 is rejected."""
        with pytest.raises(ValueError):
            ThetaPosterior(
                theta_grid=np.linspace(0, 1, 10),
                density=np.ones(10),
                individual_densities=np.ones((0, 10)),
                alpha_resampled=np.array([]),
                beta_resampled=np.array([]),
                n_resample=0
            )
