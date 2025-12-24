"""Tests for uncoupled thetas visualization functions."""

import numpy as np
import pytest
import matplotlib.pyplot as plt

from proportions.core.models import BinomialData
from proportions.inference.uncoupled_thetas import uncoupled_thetas
from proportions.visualization.posterior_plots import (
    plot_prior_mu_uncoupled,
    plot_posterior_mu_uncoupled,
)


class TestPlotPriorMuUncoupled:
    """Tests for plot_prior_mu_uncoupled function."""

    def test_basic_prior_plot(self):
        """Test basic prior plotting for μ with uniform prior."""
        fig = plot_prior_mu_uncoupled(
            alpha_prior=1.0,
            beta_prior=1.0,
            n_scenarios=2,
            n_samples=10000,
            random_seed=42
        )

        assert fig is not None
        assert len(fig.axes) == 1
        plt.close(fig)

    def test_jeffreys_prior(self):
        """Test prior plotting with Jeffreys prior."""
        fig = plot_prior_mu_uncoupled(
            alpha_prior=0.5,
            beta_prior=0.5,
            n_scenarios=3,
            n_samples=5000,
            random_seed=42
        )

        assert fig is not None
        plt.close(fig)

    def test_custom_parameters(self):
        """Test prior plotting with custom parameters."""
        fig = plot_prior_mu_uncoupled(
            alpha_prior=2.0,
            beta_prior=3.0,
            n_scenarios=5,
            n_samples=10000,
            figsize=(10, 6),
            title="Custom Prior Title",
            color='gray',
            random_seed=42
        )

        assert fig is not None
        assert fig.get_figwidth() == 10
        assert fig.get_figheight() == 6
        plt.close(fig)

    def test_many_scenarios(self):
        """Test prior plotting with many scenarios."""
        fig = plot_prior_mu_uncoupled(
            alpha_prior=1.0,
            beta_prior=1.0,
            n_scenarios=10,
            n_samples=10000,
            random_seed=42
        )

        assert fig is not None
        plt.close(fig)

    def test_with_ax_parameter(self):
        """Test plotting to existing axes."""
        fig, ax = plt.subplots(figsize=(8, 6))

        result_fig = plot_prior_mu_uncoupled(
            alpha_prior=1.0,
            beta_prior=1.0,
            n_scenarios=2,
            n_samples=10000,
            ax=ax,
            random_seed=42
        )

        # Should return the same figure
        assert result_fig is fig
        plt.close(fig)

    def test_validates_parameters(self):
        """Test that invalid parameters are rejected."""
        with pytest.raises(ValueError, match="alpha_prior must be positive"):
            plot_prior_mu_uncoupled(
                alpha_prior=0.0,
                beta_prior=1.0,
                n_scenarios=2
            )

        with pytest.raises(ValueError, match="n_scenarios must be positive"):
            plot_prior_mu_uncoupled(
                alpha_prior=1.0,
                beta_prior=1.0,
                n_scenarios=0
            )


class TestPlotPosteriorMuUncoupled:
    """Tests for plot_posterior_mu_uncoupled function."""

    def test_basic_posterior_plot(self):
        """Test basic posterior plotting for μ."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))
        result = uncoupled_thetas(data, random_seed=42)

        fig = plot_posterior_mu_uncoupled(result)

        assert fig is not None
        assert len(fig.axes) == 1
        plt.close(fig)

    def test_plot_with_fitted_beta(self):
        """Test that fitted Beta is shown."""
        data = BinomialData(x=np.array([90, 10]), n=np.array([100, 100]))
        result = uncoupled_thetas(data, random_seed=42)

        fig = plot_posterior_mu_uncoupled(result, show_fitted=True)

        assert fig is not None
        plt.close(fig)

    def test_custom_parameters(self):
        """Test posterior plotting with custom parameters."""
        data = BinomialData(x=np.array([8, 7]), n=np.array([10, 10]))
        result = uncoupled_thetas(data, random_seed=42)

        fig = plot_posterior_mu_uncoupled(
            result,
            figsize=(10, 6),
            title="Custom Posterior Title",
            color='darkblue',
            show_ci=True
        )

        assert fig is not None
        assert fig.get_figwidth() == 10
        assert fig.get_figheight() == 6
        plt.close(fig)

    def test_bimodal_data(self):
        """Test plotting with bimodal data (extreme heterogeneity)."""
        data = BinomialData(x=np.array([95, 5]), n=np.array([100, 100]))
        result = uncoupled_thetas(data, random_seed=42)

        fig = plot_posterior_mu_uncoupled(result)

        assert fig is not None
        plt.close(fig)

    def test_many_scenarios(self):
        """Test posterior plotting with many scenarios."""
        data = BinomialData(
            x=np.array([8, 7, 9, 6, 5, 8, 7, 8, 9, 7]),
            n=np.array([10] * 10)
        )
        result = uncoupled_thetas(data, random_seed=42)

        fig = plot_posterior_mu_uncoupled(result)

        assert fig is not None
        plt.close(fig)

    def test_with_ax_parameter(self):
        """Test plotting to existing axes."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))
        result = uncoupled_thetas(data, random_seed=42)

        fig, ax = plt.subplots(figsize=(8, 6))

        result_fig = plot_posterior_mu_uncoupled(result, ax=ax)

        # Should return the same figure
        assert result_fig is fig
        plt.close(fig)

    def test_without_mu_samples(self):
        """Test error when result doesn't have mu_samples."""
        # This shouldn't happen with normal use, but test defensive coding
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))
        result = uncoupled_thetas(data, random_seed=42)

        # Manually remove mu_samples to test error handling
        result.mu_samples = None

        with pytest.raises(ValueError, match="mu_samples"):
            plot_posterior_mu_uncoupled(result)

    def test_histogram_vs_fitted(self):
        """Test that both histogram and fitted Beta are visible when requested."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))
        result = uncoupled_thetas(data, random_seed=42)

        fig = plot_posterior_mu_uncoupled(result, show_fitted=True, show_histogram=True)

        assert fig is not None
        # Should have histogram + fitted line
        ax = fig.axes[0]
        assert len(ax.patches) > 0  # Histogram bars
        assert len(ax.lines) > 0    # Fitted line
        plt.close(fig)

    def test_credible_interval_shown(self):
        """Test that credible interval is shown when requested."""
        data = BinomialData(x=np.array([8, 2]), n=np.array([10, 10]))
        result = uncoupled_thetas(data, random_seed=42)

        fig = plot_posterior_mu_uncoupled(result, show_ci=True)

        assert fig is not None
        ax = fig.axes[0]
        # Should have vertical lines for CI
        assert len([line for line in ax.lines if line.get_linestyle() == '--']) >= 2
        plt.close(fig)
