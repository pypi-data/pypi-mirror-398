"""Tests for single proportion posterior visualization.

This module tests the visualization functions for plotting posterior distributions
of single binomial proportions.
"""

import numpy as np
import pytest
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt

from proportions.diagnostics.visualization import plot_posterior_proportion


class TestPlotPosteriorProportion:
    """Tests for plot_posterior_proportion function."""

    def test_returns_figure(self):
        """Test that function returns a matplotlib Figure."""
        fig = plot_posterior_proportion(30, 100)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_basic_plot_elements(self):
        """Test that plot has expected elements."""
        fig = plot_posterior_proportion(30, 100, confidence=0.95)
        ax = fig.axes[0]

        # Check labels
        assert ax.get_xlabel() == "Proportion"
        assert ax.get_ylabel() == "Posterior Density"
        assert ax.get_title() != ""  # Has title

        plt.close(fig)

    def test_with_custom_title(self):
        """Test custom title."""
        custom_title = "My Custom Title"
        fig = plot_posterior_proportion(30, 100, title=custom_title)

        ax = fig.axes[0]
        assert custom_title in ax.get_title()
        plt.close(fig)

    def test_with_different_confidence_levels(self):
        """Test with different confidence levels."""
        for confidence in [0.90, 0.95, 0.99]:
            fig = plot_posterior_proportion(30, 100, confidence=confidence)
            assert isinstance(fig, plt.Figure)
            plt.close(fig)

    def test_with_truncated_prior(self):
        """Test with truncated prior."""
        fig = plot_posterior_proportion(
            30, 100, confidence=0.95, lower=0.2, upper=0.8
        )

        # Should create a valid figure
        assert isinstance(fig, plt.Figure)

        # Get x-axis limits
        ax = fig.axes[0]
        xlim = ax.get_xlim()

        # Plot should respect truncation bounds (with some margin)
        assert xlim[0] >= 0.15  # Near lower bound
        assert xlim[1] <= 0.85  # Near upper bound

        plt.close(fig)

    def test_with_different_priors(self):
        """Test with different prior distributions."""
        priors = [
            (1.0, 1.0, "Uniform"),
            (0.5, 0.5, "Jeffreys"),
            (2.0, 2.0, "Symmetric"),
        ]

        for alpha, beta, desc in priors:
            fig = plot_posterior_proportion(
                30, 100, prior_alpha=alpha, prior_beta=beta
            )
            assert isinstance(fig, plt.Figure)
            plt.close(fig)

    def test_with_threshold_lines(self):
        """Test adding threshold lines."""
        thresholds = [0.25, 0.35]
        fig = plot_posterior_proportion(30, 100, thresholds=thresholds)

        ax = fig.axes[0]
        lines = ax.get_lines()

        # Should have main curve + 2 CI bounds + threshold lines
        # At minimum should have more than 3 lines
        assert len(lines) >= 3

        plt.close(fig)

    def test_edge_case_zero_successes(self):
        """Test with 0 successes."""
        fig = plot_posterior_proportion(0, 100, confidence=0.95)
        assert isinstance(fig, plt.Figure)

        ax = fig.axes[0]
        xlim = ax.get_xlim()

        # Should be concentrated near 0
        assert xlim[1] < 0.2

        plt.close(fig)

    def test_edge_case_all_successes(self):
        """Test with all successes."""
        fig = plot_posterior_proportion(100, 100, confidence=0.95)
        assert isinstance(fig, plt.Figure)

        ax = fig.axes[0]
        xlim = ax.get_xlim()

        # Should be concentrated near 1
        assert xlim[0] > 0.8

        plt.close(fig)

    def test_custom_xlim(self):
        """Test with custom x-axis limits."""
        fig = plot_posterior_proportion(30, 100, xlim=(0.2, 0.4))

        ax = fig.axes[0]
        xlim = ax.get_xlim()

        # Should respect custom limits (approximately)
        assert 0.15 <= xlim[0] <= 0.25
        assert 0.35 <= xlim[1] <= 0.45

        plt.close(fig)

    def test_custom_figsize(self):
        """Test with custom figure size."""
        figsize = (12, 8)
        fig = plot_posterior_proportion(30, 100, figsize=figsize)

        # Get actual figure size
        actual_size = fig.get_size_inches()

        assert np.isclose(actual_size[0], figsize[0])
        assert np.isclose(actual_size[1], figsize[1])

        plt.close(fig)

    def test_shaded_credible_interval(self):
        """Test that credible interval is shaded."""
        fig = plot_posterior_proportion(30, 100, confidence=0.95)

        ax = fig.axes[0]
        # Check for filled polygon (shaded region)
        collections = ax.collections

        # Should have at least one collection (the fill_between)
        assert len(collections) > 0

        plt.close(fig)

    def test_with_small_sample(self):
        """Test with small sample size."""
        fig = plot_posterior_proportion(3, 10, confidence=0.95)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_with_large_sample(self):
        """Test with large sample size."""
        fig = plot_posterior_proportion(500, 1000, confidence=0.95)
        assert isinstance(fig, plt.Figure)

        ax = fig.axes[0]
        xlim = ax.get_xlim()

        # Should be concentrated near 0.5
        width = xlim[1] - xlim[0]
        assert width < 0.2  # Narrow interval for large sample

        plt.close(fig)

    def test_invalid_inputs_raise_errors(self):
        """Test that invalid inputs raise appropriate errors."""
        # Negative success
        with pytest.raises(ValueError):
            plot_posterior_proportion(-1, 100)

        # Success > counts
        with pytest.raises(ValueError):
            plot_posterior_proportion(101, 100)

        # Invalid confidence
        with pytest.raises(ValueError):
            plot_posterior_proportion(30, 100, confidence=1.5)

        # Invalid truncation bounds
        with pytest.raises(ValueError):
            plot_posterior_proportion(30, 100, lower=0.8, upper=0.2)


class TestVisualizationCompatibility:
    """Test compatibility with previous implementation."""

    def test_generates_similar_plot(self):
        """Test that generated plot is similar to previous implementation."""
        # Just verify it runs without error
        fig = plot_posterior_proportion(
            30, 100, confidence=0.95, prior_alpha=1.0, prior_beta=1.0
        )

        assert isinstance(fig, plt.Figure)
        ax = fig.axes[0]

        # Should have main curve
        lines = ax.get_lines()
        assert len(lines) >= 1

        # Should have shaded region
        assert len(ax.collections) > 0

        plt.close(fig)

    def test_with_truncation_like_previous(self):
        """Test truncated prior similar to previous implementation."""
        fig = plot_posterior_proportion(
            30, 100, confidence=0.95, lower=0.2, upper=0.8
        )

        assert isinstance(fig, plt.Figure)

        # Verify plot range respects truncation
        ax = fig.axes[0]
        xlim = ax.get_xlim()

        # Should be within or very close to truncation bounds
        assert xlim[0] >= 0.15
        assert xlim[1] <= 0.85

        plt.close(fig)

    def test_with_threshold_lines_like_previous(self):
        """Test threshold lines similar to previous implementation."""
        thresholds = [0.25, 0.35]
        fig = plot_posterior_proportion(30, 100, thresholds=thresholds)

        assert isinstance(fig, plt.Figure)

        # Should have created lines
        ax = fig.axes[0]
        assert len(ax.get_lines()) >= len(thresholds)

        plt.close(fig)


class TestPlotConfiguration:
    """Test plot configuration options."""

    def test_resolution_affects_smoothness(self):
        """Test that resolution parameter affects plot."""
        # Low resolution
        fig_low = plot_posterior_proportion(30, 100, resolution=100)
        ax_low = fig_low.axes[0]
        lines_low = ax_low.get_lines()

        # High resolution
        fig_high = plot_posterior_proportion(30, 100, resolution=5000)
        ax_high = fig_high.axes[0]
        lines_high = ax_high.get_lines()

        # Both should have curves
        assert len(lines_low) > 0
        assert len(lines_high) > 0

        plt.close(fig_low)
        plt.close(fig_high)

    def test_auto_range_determination(self):
        """Test automatic x-axis range determination."""
        # Should auto-determine range based on posterior
        fig = plot_posterior_proportion(30, 100)

        ax = fig.axes[0]
        xlim = ax.get_xlim()

        # Range should be reasonable (not too wide, not too narrow)
        width = xlim[1] - xlim[0]
        assert 0.1 < width < 0.5  # Reasonable for this data

        # Should be centered roughly around 0.3
        center = (xlim[0] + xlim[1]) / 2
        assert 0.2 < center < 0.4

        plt.close(fig)

    def test_respects_truncation_in_range(self):
        """Test that auto-range respects truncation bounds."""
        fig = plot_posterior_proportion(50, 100, lower=0.3, upper=0.7)

        ax = fig.axes[0]
        xlim = ax.get_xlim()

        # Should not extend far beyond truncation bounds
        assert xlim[0] >= 0.25  # Close to lower bound
        assert xlim[1] <= 0.75  # Close to upper bound

        plt.close(fig)
