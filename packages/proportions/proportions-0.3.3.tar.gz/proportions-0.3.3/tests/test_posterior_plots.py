"""Tests for posterior_plots visualization functions."""

import numpy as np
import pytest
import matplotlib.pyplot as plt

from proportions.core.models import BinomialData
from proportions.inference.hierarchical_bayes import hierarchical_bayes
from proportions.visualization.posterior_plots import (
    plot_posterior_mu,
    plot_prior_mu,
    plot_prior_posterior_mu,
)


class TestPlotPosteriorMu:
    """Tests for plot_posterior_mu function."""

    def test_basic_plot(self):
        """Test basic posterior plotting without samples."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        result = hierarchical_bayes(data, random_seed=42)

        fig = plot_posterior_mu(result)
        assert fig is not None
        assert len(fig.axes) == 1
        plt.close(fig)

    def test_plot_with_samples(self):
        """Test posterior plotting with samples and importance weights."""
        data = BinomialData(x=np.array([45, 55]), n=np.array([100, 100]))
        result = hierarchical_bayes(data, n_samples=1000, random_seed=42, return_samples=True)

        # Should have samples and weights
        assert result.posterior.samples is not None
        assert result.importance_weights is not None

        fig = plot_posterior_mu(result)
        assert fig is not None
        plt.close(fig)

    def test_custom_parameters(self):
        """Test posterior plotting with custom parameters."""
        data = BinomialData(x=np.array([8, 7]), n=np.array([10, 10]))
        result = hierarchical_bayes(data, random_seed=42)

        fig = plot_posterior_mu(
            result,
            figsize=(8, 6),
            title="Custom Title",
            show_ci=False,
            color='red',
            xlim=(0.6, 0.9)
        )
        assert fig is not None
        plt.close(fig)


class TestPlotPriorMu:
    """Tests for plot_prior_mu function."""

    def test_basic_prior_plot(self):
        """Test basic prior plotting."""
        np.random.seed(42)
        n_samples = 1000

        # Generate hyperparameter samples
        m_samples = np.random.beta(2.0, 2.0, size=n_samples)
        k_samples = np.random.uniform(1.0, 50.0, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1 - m_samples) * k_samples

        data = BinomialData(x=np.array([8, 7]), n=np.array([10, 10]))

        fig = plot_prior_mu(alpha_samples, beta_samples, data)
        assert fig is not None
        assert len(fig.axes) == 1
        plt.close(fig)

    def test_prior_with_tight_hyperpriors(self):
        """Test prior plotting with tight hyperpriors."""
        np.random.seed(42)
        n_samples = 1000

        # Tight priors around m=0.5, k=2
        m_samples = np.random.beta(50.0, 50.0, size=n_samples)
        k_samples = np.random.uniform(1.99, 2.01, size=n_samples)
        alpha_samples = m_samples * k_samples
        beta_samples = (1 - m_samples) * k_samples

        data = BinomialData(x=np.array([45, 55]), n=np.array([100, 100]))

        fig = plot_prior_mu(alpha_samples, beta_samples, data, color='purple')
        assert fig is not None
        plt.close(fig)


class TestPlotPriorPosteriorMu:
    """Tests for plot_prior_posterior_mu function."""

    def test_prior_posterior_comparison(self):
        """Test prior and posterior comparison plot."""
        data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        result = hierarchical_bayes(data, n_samples=1000, random_seed=42, return_samples=True)

        # Need samples for this function
        assert result.alpha_samples is not None
        assert result.beta_samples is not None

        fig = plot_prior_posterior_mu(result, data)
        assert fig is not None
        assert len(fig.axes) == 1
        plt.close(fig)

    def test_missing_samples_raises_error(self):
        """Test that missing samples raises appropriate error."""
        data = BinomialData(x=np.array([8, 7]), n=np.array([10, 10]))
        result = hierarchical_bayes(data, random_seed=42, return_samples=False)

        with pytest.raises(ValueError, match="must have hyperparameter samples"):
            plot_prior_posterior_mu(result, data)


class TestPlotIntegration:
    """Integration tests for plotting functions."""

    def test_all_plots_for_same_data(self):
        """Test that all three plotting functions work for the same data."""
        data = BinomialData(x=np.array([45, 55]), n=np.array([100, 100]))
        result = hierarchical_bayes(
            data,
            n_samples=1000,
            m_prior_alpha=50.0,
            m_prior_beta=50.0,
            k_prior_min=1.99,
            k_prior_max=2.01,
            random_seed=42,
            return_samples=True
        )

        # All three plots should work
        fig1 = plot_prior_mu(result.alpha_samples, result.beta_samples, data)
        assert fig1 is not None
        plt.close(fig1)

        fig2 = plot_posterior_mu(result)
        assert fig2 is not None
        plt.close(fig2)

        fig3 = plot_prior_posterior_mu(result, data)
        assert fig3 is not None
        plt.close(fig3)


class TestPlotThetaDistribution:
    """Tests for plot_theta_distribution function."""

    def test_basic_plot(self):
        """Test basic theta distribution plotting."""
        from proportions.aggregation import compute_theta_posterior
        from proportions.visualization.posterior_plots import plot_theta_distribution
        
        # Create simple theta posterior
        alpha_samples = np.ones(100) * 2.0
        beta_samples = np.ones(100) * 3.0
        weights = np.ones(100) / 100
        
        theta_post = compute_theta_posterior(
            alpha_samples, beta_samples, weights, n_resample=50, random_seed=42
        )
        
        fig = plot_theta_distribution(theta_post)
        assert fig is not None
        assert len(fig.axes) == 1
        plt.close(fig)

    def test_plot_with_custom_parameters(self):
        """Test plotting with custom parameters."""
        from proportions.aggregation import compute_theta_prior
        from proportions.visualization.posterior_plots import plot_theta_distribution
        
        alpha_samples = np.random.rand(100) * 5 + 1
        beta_samples = np.random.rand(100) * 5 + 1
        
        theta_prior = compute_theta_prior(
            alpha_samples, beta_samples, n_resample=30, random_seed=42
        )
        
        fig = plot_theta_distribution(
            theta_prior,
            title="Custom Prior",
            color="darkgreen",
            n_display=10,
            show_components=True,
            ylim=(0, 5)
        )
        assert fig is not None
        plt.close(fig)

    def test_plot_without_components(self):
        """Test plotting without showing individual components."""
        from proportions.aggregation import compute_theta_posterior
        from proportions.visualization.posterior_plots import plot_theta_distribution
        
        alpha_samples = np.ones(50) * 2.0
        beta_samples = np.ones(50) * 2.0
        weights = np.ones(50) / 50
        
        theta_post = compute_theta_posterior(
            alpha_samples, beta_samples, weights, n_resample=20, random_seed=42
        )
        
        fig = plot_theta_distribution(theta_post, show_components=False)
        assert fig is not None
        plt.close(fig)


class TestPlotThetaComparison:
    """Tests for plot_theta_comparison function."""

    def test_basic_comparison(self):
        """Test basic prior vs posterior comparison."""
        from proportions.inference.hierarchical_bayes import hierarchical_bayes
        from proportions.visualization.posterior_plots import plot_theta_comparison
        
        data = BinomialData(x=np.array([90, 10]), n=np.array([100, 100]))
        result = hierarchical_bayes(
            data, n_samples=1000, random_seed=42, return_samples=True
        )
        
        fig = plot_theta_comparison(result)
        assert fig is not None
        assert len(fig.axes) == 2  # Prior and posterior panels
        plt.close(fig)

    def test_comparison_with_custom_parameters(self):
        """Test comparison with custom parameters."""
        from proportions.inference.hierarchical_bayes import hierarchical_bayes
        from proportions.visualization.posterior_plots import plot_theta_comparison
        
        data = BinomialData(x=np.array([45, 55]), n=np.array([100, 100]))
        result = hierarchical_bayes(
            data, n_samples=500, random_seed=42, return_samples=True
        )
        
        fig = plot_theta_comparison(
            result,
            n_resample=100,
            n_display=20,
            ylim=(0, 8),
            figsize=(16, 6)
        )
        assert fig is not None
        assert len(fig.axes) == 2
        plt.close(fig)

    def test_comparison_requires_samples(self):
        """Test that comparison requires return_samples=True."""
        from proportions.inference.hierarchical_bayes import hierarchical_bayes
        from proportions.visualization.posterior_plots import plot_theta_comparison
        
        data = BinomialData(x=np.array([8, 7]), n=np.array([10, 10]))
        result = hierarchical_bayes(data, random_seed=42, return_samples=False)
        
        with pytest.raises(ValueError, match="return_samples=True"):
            plot_theta_comparison(result)
