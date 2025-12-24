"""Visualization utilities for posterior distributions.

This module provides plotting functions for visualizing prior and posterior
distributions from Hierarchical Bayes and Flat Bayes (Single-Theta) inference.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta as beta_dist

from proportions.core.models import HierarchicalBayesResult, SingleThetaResult, BinomialData
from proportions.aggregation import compute_prior_t_hierarchical_bayes


def plot_posterior_mu(
    result: HierarchicalBayesResult,
    figsize: tuple[float, float] = (10, 6),
    title: str | None = None,
    show_ci: bool = True,
    ci_level: float = 0.95,
    color: str = 'blue',
    xlim: tuple[float, float] | None = None,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot posterior distribution of μ (average success rate).

    Creates a visualization showing the posterior distribution of μ (the average
    success rate across all groups) from Hierarchical Bayes inference, using the
    fitted Beta distribution.

    Args:
        result: HierarchicalBayesResult from hierarchical_bayes().
        figsize: Figure size as (width, height) tuple (default: (10, 6)).
                 Ignored if ax is provided.
        title: Optional custom title. If None, generates descriptive title.
        show_ci: If True, shows credible interval bounds as vertical lines (default: True).
        ci_level: Credible interval level to display (default: 0.95).
        color: Color for the posterior curve (default: 'blue').
        xlim: Optional (xmin, xmax) tuple for x-axis limits. If None, auto-determines
              from credible interval.
        ax: Optional matplotlib Axes to plot into. If None, creates new figure.

    Returns:
        Matplotlib Figure object.

    Raises:
        ValueError: If result doesn't have fitted posterior parameters.

    Example:
        >>> from proportions.core.models import BinomialData
        >>> from proportions.inference.hierarchical_bayes import hierarchical_bayes
        >>> from proportions.visualization.posterior_plots import plot_posterior_mu
        >>>
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> result = hierarchical_bayes(data, random_seed=42)
        >>> fig = plot_posterior_mu(result)
        >>> fig.savefig('posterior_mu.png', dpi=150, bbox_inches='tight')
        >>> plt.show()
    """
    if result.posterior.alpha_fitted is None or result.posterior.beta_fitted is None:
        raise ValueError("Result must have fitted posterior parameters (alpha_fitted, beta_fitted)")

    # Determine x-axis range
    if xlim is None:
        # Use credible interval with some padding
        ci_width = result.posterior.ci_upper - result.posterior.ci_lower
        xmin = max(0.0, result.posterior.ci_lower - 0.2 * ci_width)
        xmax = min(1.0, result.posterior.ci_upper + 0.2 * ci_width)
    else:
        xmin, xmax = xlim

    # Generate x values and compute PDF
    x = np.linspace(xmin, xmax, 1000)
    y = beta_dist.pdf(x, result.posterior.alpha_fitted, result.posterior.beta_fitted)

    # Create figure or use provided axes
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        created_figure = True
    else:
        fig = ax.get_figure()
        created_figure = False

    # Plot weighted histogram if samples and weights are available
    if (result.posterior.samples is not None and
        result.importance_weights is not None):
        ax.hist(result.posterior.samples, bins=60, weights=result.importance_weights,
                density=True, alpha=0.6, color=color, edgecolor='black',
                linewidth=0.5, label='Posterior samples (weighted)')

    # Plot posterior curve
    ax.plot(x, y, color=color, linewidth=2.5, label='Fitted Beta', alpha=0.9)

    # Mark mean
    ax.axvline(result.posterior.mu, color=color, linestyle='--', linewidth=2,
               alpha=0.7, label=f'Mean: {result.posterior.mu:.4f}')

    # Show credible interval if requested
    if show_ci:
        ci_lower = result.posterior.ci_lower
        ci_upper = result.posterior.ci_upper

        pdf_lower = beta_dist.pdf(ci_lower, result.posterior.alpha_fitted, result.posterior.beta_fitted)
        pdf_upper = beta_dist.pdf(ci_upper, result.posterior.alpha_fitted, result.posterior.beta_fitted)

        ax.plot([ci_lower, ci_lower], [0, pdf_lower], color=color, linestyle=':',
                linewidth=2, alpha=0.6)
        ax.plot([ci_upper, ci_upper], [0, pdf_upper], color=color, linestyle=':',
                linewidth=2, alpha=0.6)

        # Shade CI region
        x_ci = x[(x >= ci_lower) & (x <= ci_upper)]
        y_ci = beta_dist.pdf(x_ci, result.posterior.alpha_fitted, result.posterior.beta_fitted)
        ax.fill_between(x_ci, y_ci, color=color, alpha=0.3)

    # Labels and title
    ax.set_xlabel('μ (Average Success Rate)', fontsize=12)
    ax.set_ylabel('Posterior Density', fontsize=12)

    if title is None:
        title = (f'Posterior Distribution of μ\n'
                f'Mean: {result.posterior.mu:.4f}, '
                f'{int(ci_level*100)}% CI: [{result.posterior.ci_lower:.4f}, {result.posterior.ci_upper:.4f}]')
    ax.set_title(title, fontsize=13, fontweight='bold')

    # Set y-axis to start at 0
    ylim = ax.get_ylim()
    ax.set_ylim(0, ylim[1] * 1.05)

    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    if created_figure:
        plt.tight_layout()
    return fig


def plot_prior_mu(
    alpha_samples: np.ndarray,
    beta_samples: np.ndarray,
    data: BinomialData,
    figsize: tuple[float, float] = (10, 6),
    title: str | None = None,
    show_ci: bool = True,
    ci_level: float = 0.95,
    color: str = 'gray',
    xlim: tuple[float, float] | None = None,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot prior distribution of μ (average success rate).

    Creates a visualization showing the prior distribution of μ (the average
    success rate across all groups) from hyperparameter samples, using uniform
    weights across samples (not importance weights).

    Args:
        alpha_samples: Array of α samples from hyperprior.
        beta_samples: Array of β samples from hyperprior.
        data: BinomialData (used only to determine number of groups).
        figsize: Figure size as (width, height) tuple (default: (10, 6)).
                 Ignored if ax is provided.
        title: Optional custom title. If None, generates descriptive title.
        show_ci: If True, shows credible interval bounds as vertical lines (default: True).
        ci_level: Credible interval level to display (default: 0.95).
        color: Color for the prior curve (default: 'gray').
        xlim: Optional (xmin, xmax) tuple for x-axis limits. If None, auto-determines
              from credible interval.
        ax: Optional matplotlib Axes to plot into. If None, creates new figure.

    Returns:
        Matplotlib Figure object.

    Raises:
        ValueError: If alpha_samples and beta_samples have different lengths.

    Example:
        >>> from proportions.core.models import BinomialData
        >>> from proportions.inference.hierarchical_bayes import hierarchical_bayes
        >>> from proportions.visualization.posterior_plots import plot_prior_mu
        >>>
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> result = hierarchical_bayes(data, random_seed=42, return_samples=True)
        >>> fig = plot_prior_mu(result.alpha_samples, result.beta_samples, data)
        >>> fig.savefig('prior_mu.png', dpi=150, bbox_inches='tight')
        >>> plt.show()
    """
    # Compute prior distribution
    prior = compute_prior_t_hierarchical_bayes(
        alpha_samples, beta_samples, data, ci_level=ci_level
    )

    if prior.alpha_fitted is None or prior.beta_fitted is None:
        raise ValueError("Prior fitting failed - could not compute fitted parameters")

    # Determine x-axis range
    if xlim is None:
        # Use credible interval with some padding
        ci_width = prior.ci_upper - prior.ci_lower
        xmin = max(0.0, prior.ci_lower - 0.2 * ci_width)
        xmax = min(1.0, prior.ci_upper + 0.2 * ci_width)
    else:
        xmin, xmax = xlim

    # Generate x values and compute PDF
    x = np.linspace(xmin, xmax, 1000)
    y = beta_dist.pdf(x, prior.alpha_fitted, prior.beta_fitted)

    # Create figure or use provided axes
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        created_figure = True
    else:
        fig = ax.get_figure()
        created_figure = False

    # Plot histogram if samples are available
    if prior.samples is not None:
        ax.hist(prior.samples, bins=60, density=True, alpha=0.6,
                color=color, edgecolor='black', linewidth=0.5, label='Prior samples')

    # Plot prior curve
    ax.plot(x, y, color=color, linewidth=2.5, label='Fitted Beta', alpha=0.9)

    # Mark mean
    ax.axvline(prior.mu, color=color, linestyle='--', linewidth=2,
               alpha=0.7, label=f'Mean: {prior.mu:.4f}')

    # Show credible interval if requested
    if show_ci:
        ci_lower = prior.ci_lower
        ci_upper = prior.ci_upper

        pdf_lower = beta_dist.pdf(ci_lower, prior.alpha_fitted, prior.beta_fitted)
        pdf_upper = beta_dist.pdf(ci_upper, prior.alpha_fitted, prior.beta_fitted)

        ax.plot([ci_lower, ci_lower], [0, pdf_lower], color=color, linestyle=':',
                linewidth=2, alpha=0.6)
        ax.plot([ci_upper, ci_upper], [0, pdf_upper], color=color, linestyle=':',
                linewidth=2, alpha=0.6)

        # Shade CI region
        x_ci = x[(x >= ci_lower) & (x <= ci_upper)]
        y_ci = beta_dist.pdf(x_ci, prior.alpha_fitted, prior.beta_fitted)
        ax.fill_between(x_ci, y_ci, color=color, alpha=0.3)

    # Labels and title
    ax.set_xlabel('μ (Average Success Rate)', fontsize=12)
    ax.set_ylabel('Prior Density', fontsize=12)

    if title is None:
        title = (f'Prior Distribution of μ\n'
                f'Mean: {prior.mu:.4f}, '
                f'{int(ci_level*100)}% CI: [{prior.ci_lower:.4f}, {prior.ci_upper:.4f}]')
    ax.set_title(title, fontsize=13, fontweight='bold')

    # Set y-axis to start at 0
    ylim = ax.get_ylim()
    ax.set_ylim(0, ylim[1] * 1.05)

    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    if created_figure:
        plt.tight_layout()
    return fig


def plot_prior_posterior_mu(
    result: HierarchicalBayesResult,
    data: BinomialData,
    figsize: tuple[float, float] = (10, 6),
    title: str | None = None,
    show_ci: bool = True,
    ci_level: float = 0.95,
    prior_color: str = 'gray',
    posterior_color: str = 'blue',
    xlim: tuple[float, float] | None = None,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot prior and posterior distributions of μ on the same axes.

    Creates a comparison visualization showing both the prior and posterior
    distributions of μ (average success rate) from Hierarchical Bayes inference.
    The prior uses uniform weights across hyperparameter samples, while the
    posterior uses importance weights based on the data likelihood.

    Args:
        result: HierarchicalBayesResult from hierarchical_bayes() with return_samples=True.
        data: BinomialData used in the analysis.
        figsize: Figure size as (width, height) tuple (default: (10, 6)).
                 Ignored if ax is provided.
        title: Optional custom title. If None, generates descriptive title.
        show_ci: If True, shows credible interval bounds for both distributions (default: True).
        ci_level: Credible interval level to display (default: 0.95).
        prior_color: Color for the prior curve (default: 'gray').
        posterior_color: Color for the posterior curve (default: 'blue').
        xlim: Optional (xmin, xmax) tuple for x-axis limits. If None, auto-determines
              to show both distributions.
        ax: Optional matplotlib Axes to plot into. If None, creates new figure.

    Returns:
        Matplotlib Figure object.

    Raises:
        ValueError: If result doesn't have hyperparameter samples (need return_samples=True)
                    or fitted posterior parameters.

    Example:
        >>> from proportions.core.models import BinomialData
        >>> from proportions.inference.hierarchical_bayes import hierarchical_bayes
        >>> from proportions.visualization.posterior_plots import plot_prior_posterior_mu
        >>>
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> result = hierarchical_bayes(data, random_seed=42, return_samples=True)
        >>> fig = plot_prior_posterior_mu(result, data)
        >>> fig.savefig('prior_posterior_mu.png', dpi=150, bbox_inches='tight')
        >>> plt.show()
    """
    # Validate inputs
    if result.alpha_samples is None or result.beta_samples is None:
        raise ValueError(
            "Result must have hyperparameter samples. "
            "Call hierarchical_bayes() with return_samples=True"
        )

    if result.posterior.alpha_fitted is None or result.posterior.beta_fitted is None:
        raise ValueError("Result must have fitted posterior parameters")

    # Compute prior distribution
    prior = compute_prior_t_hierarchical_bayes(
        result.alpha_samples, result.beta_samples, data, ci_level=ci_level,
        generate_samples=True  # Generate samples for histogram
    )

    if prior.alpha_fitted is None or prior.beta_fitted is None:
        raise ValueError("Prior fitting failed - could not compute fitted parameters")

    # Determine x-axis range to show both distributions
    if xlim is None:
        # Find range that covers both distributions
        all_bounds = [
            prior.ci_lower, prior.ci_upper,
            result.posterior.ci_lower, result.posterior.ci_upper
        ]
        xmin = max(0.0, min(all_bounds) - 0.05)
        xmax = min(1.0, max(all_bounds) + 0.05)
    else:
        xmin, xmax = xlim

    # Generate x values
    x = np.linspace(xmin, xmax, 1000)

    # Compute PDFs
    y_prior = beta_dist.pdf(x, prior.alpha_fitted, prior.beta_fitted)
    y_posterior = beta_dist.pdf(x, result.posterior.alpha_fitted, result.posterior.beta_fitted)

    # Create figure or use provided axes
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        created_figure = True
    else:
        fig = ax.get_figure()
        created_figure = False

    # Plot prior histogram if samples available
    if prior.samples is not None:
        ax.hist(prior.samples, bins=50, density=True, alpha=0.3,
                color=prior_color, edgecolor='black', linewidth=0.3)

    # Plot prior curve
    ax.plot(x, y_prior, color=prior_color, linewidth=2.5, label='Prior', alpha=0.8)
    ax.fill_between(x, y_prior, color=prior_color, alpha=0.15)

    # Plot posterior histogram if samples and weights available
    if (result.posterior.samples is not None and
        result.importance_weights is not None):
        ax.hist(result.posterior.samples, bins=50, weights=result.importance_weights,
                density=True, alpha=0.4, color=posterior_color, edgecolor='black',
                linewidth=0.3)

    # Plot posterior curve
    ax.plot(x, y_posterior, color=posterior_color, linewidth=2.5, label='Posterior', alpha=0.8)
    ax.fill_between(x, y_posterior, color=posterior_color, alpha=0.15)

    # Mark means
    ax.axvline(prior.mu, color=prior_color, linestyle='--', linewidth=2,
               alpha=0.6, label=f'Prior mean: {prior.mu:.4f}')
    ax.axvline(result.posterior.mu, color=posterior_color, linestyle='--', linewidth=2,
               alpha=0.6, label=f'Posterior mean: {result.posterior.mu:.4f}')

    # Show credible intervals if requested
    if show_ci:
        # Prior CI
        prior_ci_lower = prior.ci_lower
        prior_ci_upper = prior.ci_upper
        pdf_prior_lower = beta_dist.pdf(prior_ci_lower, prior.alpha_fitted, prior.beta_fitted)
        pdf_prior_upper = beta_dist.pdf(prior_ci_upper, prior.alpha_fitted, prior.beta_fitted)

        ax.plot([prior_ci_lower, prior_ci_lower], [0, pdf_prior_lower],
                color=prior_color, linestyle=':', linewidth=1.5, alpha=0.5)
        ax.plot([prior_ci_upper, prior_ci_upper], [0, pdf_prior_upper],
                color=prior_color, linestyle=':', linewidth=1.5, alpha=0.5)

        # Posterior CI
        post_ci_lower = result.posterior.ci_lower
        post_ci_upper = result.posterior.ci_upper
        pdf_post_lower = beta_dist.pdf(post_ci_lower, result.posterior.alpha_fitted,
                                        result.posterior.beta_fitted)
        pdf_post_upper = beta_dist.pdf(post_ci_upper, result.posterior.alpha_fitted,
                                        result.posterior.beta_fitted)

        ax.plot([post_ci_lower, post_ci_lower], [0, pdf_post_lower],
                color=posterior_color, linestyle=':', linewidth=1.5, alpha=0.5)
        ax.plot([post_ci_upper, post_ci_upper], [0, pdf_post_upper],
                color=posterior_color, linestyle=':', linewidth=1.5, alpha=0.5)

    # Labels and title
    ax.set_xlabel('μ (Average Success Rate)', fontsize=12)
    ax.set_ylabel('Density', fontsize=12)

    if title is None:
        title = (f'Prior vs Posterior Distribution of μ\n'
                f'Prior: {prior.mu:.4f} [{prior.ci_lower:.4f}, {prior.ci_upper:.4f}] | '
                f'Posterior: {result.posterior.mu:.4f} '
                f'[{result.posterior.ci_lower:.4f}, {result.posterior.ci_upper:.4f}]')
    ax.set_title(title, fontsize=13, fontweight='bold')

    # Set y-axis to start at 0
    ylim = ax.get_ylim()
    ax.set_ylim(0, ylim[1] * 1.05)

    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10, loc='best')

    if created_figure:
        plt.tight_layout()
    return fig


# ==============================================================================
# Flat Bayes (Single-Theta) Visualization Functions
# ==============================================================================


def plot_flat_bayes_prior(
    alpha_prior: float,
    beta_prior: float,
    figsize: tuple[float, float] = (10, 6),
    title: str | None = None,
    show_ci: bool = True,
    ci_level: float = 0.95,
    color: str = 'gray',
    xlim: tuple[float, float] | None = None,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot prior distribution for Flat Bayes (Single-Theta) model.

    Creates a visualization showing the Beta prior distribution on θ used in
    the Flat Bayes model, which assumes all groups share a common success rate.

    Args:
        alpha_prior: Prior alpha parameter for Beta(α, β).
        beta_prior: Prior beta parameter for Beta(α, β).
        figsize: Figure size as (width, height) tuple (default: (10, 6)).
                 Ignored if ax is provided.
        title: Optional custom title. If None, generates descriptive title.
        show_ci: If True, shows credible interval bounds as vertical lines (default: True).
        ci_level: Credible interval level to display (default: 0.95).
        color: Color for the prior curve (default: 'gray').
        xlim: Optional (xmin, xmax) tuple for x-axis limits. If None, uses (0, 1).
        ax: Optional matplotlib Axes to plot into. If None, creates new figure.

    Returns:
        Matplotlib Figure object.

    Example:
        >>> from proportions.visualization.posterior_plots import plot_flat_bayes_prior
        >>> import matplotlib.pyplot as plt
        >>>
        >>> # Uniform prior
        >>> fig = plot_flat_bayes_prior(1.0, 1.0, title='Flat Bayes Prior: Uniform(0,1)')
        >>> fig.savefig('flat_bayes_prior.png', dpi=150, bbox_inches='tight')
        >>> plt.show()
    """
    # Determine x-axis range
    if xlim is None:
        xmin, xmax = 0.0, 1.0
    else:
        xmin, xmax = xlim

    # Generate x values and compute PDF
    x = np.linspace(xmin, xmax, 1000)
    y = beta_dist.pdf(x, alpha_prior, beta_prior)

    # Create figure or use provided axes
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        created_figure = True
    else:
        fig = ax.get_figure()
        created_figure = False

    # Plot prior curve
    ax.plot(x, y, color=color, linewidth=2.5, label='Prior', alpha=0.9)
    ax.fill_between(x, y, color=color, alpha=0.15)

    # Mark mean
    mean_prior = alpha_prior / (alpha_prior + beta_prior)
    ax.axvline(mean_prior, color=color, linestyle='--', linewidth=2,
               alpha=0.7, label=f'Mean: {mean_prior:.4f}')

    # Show credible interval if requested
    if show_ci:
        alpha_lower = (1 - ci_level) / 2
        alpha_upper = 1 - alpha_lower
        from proportions.distributions.beta import beta_quantiles
        quantiles = beta_quantiles([alpha_lower, alpha_upper], alpha_prior, beta_prior)
        ci_lower = float(quantiles[0])
        ci_upper = float(quantiles[1])

        pdf_lower = beta_dist.pdf(ci_lower, alpha_prior, beta_prior)
        pdf_upper = beta_dist.pdf(ci_upper, alpha_prior, beta_prior)

        ax.plot([ci_lower, ci_lower], [0, pdf_lower], color=color, linestyle=':',
                linewidth=2, alpha=0.6)
        ax.plot([ci_upper, ci_upper], [0, pdf_upper], color=color, linestyle=':',
                linewidth=2, alpha=0.6)

        # Shade CI region
        x_ci = x[(x >= ci_lower) & (x <= ci_upper)]
        y_ci = beta_dist.pdf(x_ci, alpha_prior, beta_prior)
        ax.fill_between(x_ci, y_ci, color=color, alpha=0.3)

    # Labels and title
    ax.set_xlabel('θ (Success Rate)', fontsize=12)
    ax.set_ylabel('Prior Density', fontsize=12)

    if title is None:
        title = (f'Flat Bayes Prior: Beta({alpha_prior:.1f}, {beta_prior:.1f})\n'
                f'Mean: {mean_prior:.4f}')
    ax.set_title(title, fontsize=13, fontweight='bold')

    # Set y-axis to start at 0
    ylim = ax.get_ylim()
    ax.set_ylim(0, ylim[1] * 1.05)

    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    if created_figure:
        plt.tight_layout()
    return fig


def plot_flat_bayes_posterior(
    result: SingleThetaResult,
    figsize: tuple[float, float] = (10, 6),
    title: str | None = None,
    show_ci: bool = True,
    ci_level: float = 0.95,
    color: str = 'blue',
    xlim: tuple[float, float] | None = None,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot posterior distribution for Flat Bayes (Single-Theta) model.

    Creates a visualization showing the posterior distribution of θ (the pooled
    success rate) from Flat Bayes inference, using the fitted Beta distribution.

    Args:
        result: SingleThetaResult from single_theta_bayesian().
        figsize: Figure size as (width, height) tuple (default: (10, 6)).
                 Ignored if ax is provided.
        title: Optional custom title. If None, generates descriptive title.
        show_ci: If True, shows credible interval bounds as vertical lines (default: True).
        ci_level: Credible interval level to display (default: 0.95).
        color: Color for the posterior curve (default: 'blue').
        xlim: Optional (xmin, xmax) tuple for x-axis limits. If None, auto-determines
              from credible interval.
        ax: Optional matplotlib Axes to plot into. If None, creates new figure.

    Returns:
        Matplotlib Figure object.

    Raises:
        ValueError: If result doesn't have fitted posterior parameters.

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> from proportions.inference.single_theta import single_theta_bayesian
        >>> from proportions.visualization.posterior_plots import plot_flat_bayes_posterior
        >>>
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)
        >>> fig = plot_flat_bayes_posterior(result)
        >>> fig.savefig('flat_bayes_posterior.png', dpi=150, bbox_inches='tight')
        >>> plt.show()
    """
    if result.posterior.alpha_fitted is None or result.posterior.beta_fitted is None:
        raise ValueError("Result must have fitted posterior parameters (alpha_fitted, beta_fitted)")

    # Determine x-axis range
    if xlim is None:
        # Use credible interval with some padding
        ci_width = result.posterior.ci_upper - result.posterior.ci_lower
        xmin = max(0.0, result.posterior.ci_lower - 0.2 * ci_width)
        xmax = min(1.0, result.posterior.ci_upper + 0.2 * ci_width)
    else:
        xmin, xmax = xlim

    # Generate x values and compute PDF
    x = np.linspace(xmin, xmax, 1000)
    y = beta_dist.pdf(x, result.posterior.alpha_fitted, result.posterior.beta_fitted)

    # Create figure or use provided axes
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        created_figure = True
    else:
        fig = ax.get_figure()
        created_figure = False

    # Plot posterior curve
    ax.plot(x, y, color=color, linewidth=2.5, label='Posterior', alpha=0.9)
    ax.fill_between(x, y, color=color, alpha=0.15)

    # Mark mean
    ax.axvline(result.posterior.mu, color=color, linestyle='--', linewidth=2,
               alpha=0.7, label=f'Mean: {result.posterior.mu:.4f}')

    # Show credible interval if requested
    if show_ci:
        ci_lower = result.posterior.ci_lower
        ci_upper = result.posterior.ci_upper

        pdf_lower = beta_dist.pdf(ci_lower, result.posterior.alpha_fitted, result.posterior.beta_fitted)
        pdf_upper = beta_dist.pdf(ci_upper, result.posterior.alpha_fitted, result.posterior.beta_fitted)

        ax.plot([ci_lower, ci_lower], [0, pdf_lower], color=color, linestyle=':',
                linewidth=2, alpha=0.6)
        ax.plot([ci_upper, ci_upper], [0, pdf_upper], color=color, linestyle=':',
                linewidth=2, alpha=0.6)

        # Shade CI region
        x_ci = x[(x >= ci_lower) & (x <= ci_upper)]
        y_ci = beta_dist.pdf(x_ci, result.posterior.alpha_fitted, result.posterior.beta_fitted)
        ax.fill_between(x_ci, y_ci, color=color, alpha=0.3)

    # Labels and title
    ax.set_xlabel('θ (Success Rate)', fontsize=12)
    ax.set_ylabel('Posterior Density', fontsize=12)

    if title is None:
        title = (f'Flat Bayes Posterior: Beta({result.posterior.alpha_fitted:.1f}, {result.posterior.beta_fitted:.1f})\n'
                f'Mean: {result.posterior.mu:.4f}, '
                f'{int(ci_level*100)}% CI: [{result.posterior.ci_lower:.4f}, {result.posterior.ci_upper:.4f}]')
    ax.set_title(title, fontsize=13, fontweight='bold')

    # Set y-axis to start at 0
    ylim = ax.get_ylim()
    ax.set_ylim(0, ylim[1] * 1.05)

    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    if created_figure:
        plt.tight_layout()
    return fig


def plot_flat_bayes_prior_posterior(
    result: SingleThetaResult,
    figsize: tuple[float, float] = (10, 6),
    title: str | None = None,
    show_ci: bool = True,
    ci_level: float = 0.95,
    prior_color: str = 'gray',
    posterior_color: str = 'blue',
    xlim: tuple[float, float] | None = None,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot prior and posterior distributions for Flat Bayes model on same axes.

    Creates a comparison visualization showing both the prior and posterior
    distributions of θ (pooled success rate) from Flat Bayes inference.

    Args:
        result: SingleThetaResult from single_theta_bayesian().
        figsize: Figure size as (width, height) tuple (default: (10, 6)).
                 Ignored if ax is provided.
        title: Optional custom title. If None, generates descriptive title.
        show_ci: If True, shows credible interval bounds for both distributions (default: True).
        ci_level: Credible interval level to display (default: 0.95).
        prior_color: Color for the prior curve (default: 'gray').
        posterior_color: Color for the posterior curve (default: 'blue').
        xlim: Optional (xmin, xmax) tuple for x-axis limits. If None, auto-determines
              to show both distributions.
        ax: Optional matplotlib Axes to plot into. If None, creates new figure.

    Returns:
        Matplotlib Figure object.

    Raises:
        ValueError: If result doesn't have fitted posterior parameters.

    Example:
        >>> import numpy as np
        >>> from proportions.core.models import BinomialData
        >>> from proportions.inference.single_theta import single_theta_bayesian
        >>> from proportions.visualization.posterior_plots import plot_flat_bayes_prior_posterior
        >>>
        >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
        >>> result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)
        >>> fig = plot_flat_bayes_prior_posterior(result)
        >>> fig.savefig('flat_bayes_prior_posterior.png', dpi=150, bbox_inches='tight')
        >>> plt.show()
    """
    if result.posterior.alpha_fitted is None or result.posterior.beta_fitted is None:
        raise ValueError("Result must have fitted posterior parameters")

    # Determine x-axis range to show both distributions
    if xlim is None:
        # Use posterior credible interval with some padding
        ci_width = result.posterior.ci_upper - result.posterior.ci_lower
        xmin = max(0.0, result.posterior.ci_lower - 0.2 * ci_width)
        xmax = min(1.0, result.posterior.ci_upper + 0.2 * ci_width)
    else:
        xmin, xmax = xlim

    # Generate x values
    x = np.linspace(xmin, xmax, 1000)

    # Compute PDFs
    y_prior = beta_dist.pdf(x, result.prior_alpha, result.prior_beta)
    y_posterior = beta_dist.pdf(x, result.posterior.alpha_fitted, result.posterior.beta_fitted)

    # Create figure or use provided axes
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        created_figure = True
    else:
        fig = ax.get_figure()
        created_figure = False

    # Plot prior curve
    ax.plot(x, y_prior, color=prior_color, linewidth=2.5, label='Prior', alpha=0.8)
    ax.fill_between(x, y_prior, color=prior_color, alpha=0.15)

    # Plot posterior curve
    ax.plot(x, y_posterior, color=posterior_color, linewidth=2.5, label='Posterior', alpha=0.8)
    ax.fill_between(x, y_posterior, color=posterior_color, alpha=0.15)

    # Mark means
    mean_prior = result.prior_alpha / (result.prior_alpha + result.prior_beta)
    ax.axvline(mean_prior, color=prior_color, linestyle='--', linewidth=2,
               alpha=0.6, label=f'Prior mean: {mean_prior:.4f}')
    ax.axvline(result.posterior.mu, color=posterior_color, linestyle='--', linewidth=2,
               alpha=0.6, label=f'Posterior mean: {result.posterior.mu:.4f}')

    # Show credible intervals if requested
    if show_ci:
        # Prior CI
        alpha_lower = (1 - ci_level) / 2
        alpha_upper = 1 - alpha_lower
        from proportions.distributions.beta import beta_quantiles
        quantiles_prior = beta_quantiles([alpha_lower, alpha_upper], result.prior_alpha, result.prior_beta)
        prior_ci_lower = float(quantiles_prior[0])
        prior_ci_upper = float(quantiles_prior[1])

        pdf_prior_lower = beta_dist.pdf(prior_ci_lower, result.prior_alpha, result.prior_beta)
        pdf_prior_upper = beta_dist.pdf(prior_ci_upper, result.prior_alpha, result.prior_beta)

        ax.plot([prior_ci_lower, prior_ci_lower], [0, pdf_prior_lower],
                color=prior_color, linestyle=':', linewidth=1.5, alpha=0.5)
        ax.plot([prior_ci_upper, prior_ci_upper], [0, pdf_prior_upper],
                color=prior_color, linestyle=':', linewidth=1.5, alpha=0.5)

        # Posterior CI
        post_ci_lower = result.posterior.ci_lower
        post_ci_upper = result.posterior.ci_upper
        pdf_post_lower = beta_dist.pdf(post_ci_lower, result.posterior.alpha_fitted,
                                        result.posterior.beta_fitted)
        pdf_post_upper = beta_dist.pdf(post_ci_upper, result.posterior.alpha_fitted,
                                        result.posterior.beta_fitted)

        ax.plot([post_ci_lower, post_ci_lower], [0, pdf_post_lower],
                color=posterior_color, linestyle=':', linewidth=1.5, alpha=0.5)
        ax.plot([post_ci_upper, post_ci_upper], [0, pdf_post_upper],
                color=posterior_color, linestyle=':', linewidth=1.5, alpha=0.5)

    # Labels and title
    ax.set_xlabel('θ (Success Rate)', fontsize=12)
    ax.set_ylabel('Density', fontsize=12)

    if title is None:
        title = (f'Flat Bayes: Prior vs Posterior\n'
                f'Prior: Beta({result.prior_alpha:.1f}, {result.prior_beta:.1f}) | '
                f'Posterior: Beta({result.posterior.alpha_fitted:.1f}, {result.posterior.beta_fitted:.1f})')
    ax.set_title(title, fontsize=13, fontweight='bold')

    # Set y-axis to start at 0
    ylim = ax.get_ylim()
    ax.set_ylim(0, ylim[1] * 1.05)

    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10, loc='best')

    if created_figure:
        plt.tight_layout()
    return fig


def plot_theta_distribution(
    theta_dist: 'ThetaPosterior',
    title: str = "Population Distribution p(θ)",
    color: str = "darkblue",
    n_display: int = 100,
    show_components: bool = True,
    ylim: tuple[float, float] = (0, 10),
    figsize: tuple[float, float] = (10, 6),
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot population distribution p(θ) or p(θ | data) with mixture components.

    Visualizes the distribution of θ for a hypothetical new scenario, showing both
    individual Beta(θ; α_i, β_i) components and their average.

    Args:
        theta_dist: ThetaPosterior object from compute_theta_posterior() or compute_theta_prior().
        title: Plot title (default: "Population Distribution p(θ)").
        color: Color for averaged density curve (default: "darkblue").
        n_display: Number of individual Beta components to display (default: 100).
        show_components: If True, show individual Beta curves in light color (default: True).
        ylim: Y-axis limits as (ymin, ymax) tuple (default: (0, 10)).
        figsize: Figure size as (width, height) tuple (default: (10, 6)).
                 Ignored if ax is provided.
        ax: Optional matplotlib Axes to plot into. If None, creates new figure.

    Returns:
        Matplotlib Figure object.

    Example:
        >>> from proportions.inference import hierarchical_bayes
        >>> from proportions.aggregation import compute_theta_posterior
        >>> from proportions.visualization.posterior_plots import plot_theta_distribution
        >>>
        >>> data = BinomialData(x=np.array([90, 10]), n=np.array([100, 100]))
        >>> result = hierarchical_bayes(data, n_samples=10000, return_samples=True)
        >>> theta_post = compute_theta_posterior(
        ...     result.alpha_samples, result.beta_samples, result.importance_weights
        ... )
        >>> fig = plot_theta_distribution(theta_post, title="Posterior p(θ | data)")
        >>> plt.show()
    """
    from proportions.core.models import ThetaPosterior

    # Create figure or use provided axes
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        created_figure = True
    else:
        fig = ax.get_figure()
        created_figure = False

    # Plot individual Beta components if requested
    if show_components:
        n_to_show = min(n_display, theta_dist.n_resample)
        component_color = 'lightgray' if 'prior' in title.lower() else 'lightblue'
        for i in range(n_to_show):
            ax.plot(
                theta_dist.theta_grid,
                theta_dist.individual_densities[i],
                color=component_color,
                linewidth=0.5,
                alpha=0.4
            )

    # Plot averaged distribution
    ax.plot(
        theta_dist.theta_grid,
        theta_dist.density,
        color=color,
        linewidth=3,
        label=f'Average over {theta_dist.n_resample} samples',
        alpha=0.9
    )

    # Formatting
    ax.set_xlabel('θ (Success Rate)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Density', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1)
    ax.set_ylim(ylim)

    if created_figure:
        fig.tight_layout()

    return fig


def plot_theta_comparison(
    result: HierarchicalBayesResult,
    n_resample: int = 1000,
    n_display: int = 100,
    ylim: tuple[float, float] = (0, 10),
    figsize: tuple[float, float] = (18, 7),
) -> plt.Figure:
    """Plot prior p(θ) vs posterior p(θ | data) side-by-side.

    Creates a two-panel figure comparing the prior and posterior distributions of θ
    for a hypothetical new scenario, showing how the data updates our beliefs.

    Args:
        result: HierarchicalBayesResult with return_samples=True.
        n_resample: Number of (α, β) pairs to resample for density computation (default: 1000).
        n_display: Number of individual Beta components to display (default: 100).
        ylim: Y-axis limits as (ymin, ymax) tuple (default: (0, 10)).
        figsize: Figure size as (width, height) tuple (default: (18, 7)).

    Returns:
        Matplotlib Figure with two panels (prior and posterior).

    Raises:
        ValueError: If result doesn't have samples (need return_samples=True).

    Example:
        >>> from proportions.core.models import BinomialData
        >>> from proportions.inference import hierarchical_bayes
        >>> from proportions.visualization.posterior_plots import plot_theta_comparison
        >>>
        >>> data = BinomialData(x=np.array([90, 10]), n=np.array([100, 100]))
        >>> result = hierarchical_bayes(data, n_samples=10000, return_samples=True)
        >>> fig = plot_theta_comparison(result)
        >>> fig.savefig('theta_comparison.png', dpi=300, bbox_inches='tight')
        >>> plt.show()
    """
    from proportions.aggregation import compute_theta_prior, compute_theta_posterior

    # Validate that we have samples
    if result.alpha_samples is None or result.beta_samples is None:
        raise ValueError(
            "result must have alpha_samples and beta_samples. "
            "Call hierarchical_bayes() with return_samples=True"
        )
    if result.importance_weights is None:
        raise ValueError(
            "result must have importance_weights. "
            "Call hierarchical_bayes() with return_samples=True"
        )

    # Compute prior and posterior distributions
    theta_prior = compute_theta_prior(
        result.alpha_samples,
        result.beta_samples,
        n_resample=n_resample,
        random_seed=42
    )

    theta_posterior = compute_theta_posterior(
        result.alpha_samples,
        result.beta_samples,
        result.importance_weights,
        n_resample=n_resample,
        random_seed=43  # Different seed
    )

    # Create figure with two panels
    fig, (ax_prior, ax_posterior) = plt.subplots(1, 2, figsize=figsize)

    # Plot prior
    plot_theta_distribution(
        theta_prior,
        title='PRIOR Population Distribution p(θ)\nBefore Observing Data',
        color='darkgray',
        n_display=n_display,
        show_components=True,
        ylim=ylim,
        ax=ax_prior
    )

    # Add prior mean line
    prior_mean = (theta_prior.theta_grid * theta_prior.density).sum() / theta_prior.density.sum()
    ax_prior.axvline(
        prior_mean,
        color='black',
        linestyle=':',
        linewidth=2,
        alpha=0.5,
        label=f'Prior mean = {prior_mean:.3f}'
    )
    ax_prior.legend(fontsize=10)

    # Plot posterior
    plot_theta_distribution(
        theta_posterior,
        title='POSTERIOR Population Distribution p(θ | data)\nAfter Observing Data',
        color='darkblue',
        n_display=n_display,
        show_components=True,
        ylim=ylim,
        ax=ax_posterior
    )

    # Add posterior mean line
    ax_posterior.axvline(
        result.posterior.mu,
        color='purple',
        linestyle=':',
        linewidth=2,
        label=f'Posterior μ = {result.posterior.mu:.3f}'
    )
    ax_posterior.legend(fontsize=10)

    # Add overall title
    fig.suptitle(
        f'Population Distribution: Prior vs Posterior (n_resample={n_resample}, showing {n_display} components)',
        fontsize=16,
        fontweight='bold'
    )

    fig.tight_layout()

    return fig


def plot_prior_mu_uncoupled(
    alpha_prior: float,
    beta_prior: float,
    n_scenarios: int,
    n_samples: int = 10000,
    figsize: tuple[float, float] = (10, 6),
    title: str | None = None,
    color: str = 'gray',
    ax: plt.Axes | None = None,
    random_seed: int | None = None,
) -> plt.Figure:
    """Plot prior distribution of μ for uncoupled thetas model.

    Computes prior distribution of μ = (1/K)Σθᵢ by sampling from independent
    priors θᵢ ~ Beta(α, β) and averaging.

    Args:
        alpha_prior: Prior alpha parameter for each θᵢ.
        beta_prior: Prior beta parameter for each θᵢ.
        n_scenarios: Number of scenarios (K).
        n_samples: Number of MC samples for μ distribution (default: 10000).
        figsize: Figure size (default: (10, 6)).
        title: Plot title (default: auto-generated).
        color: Histogram/line color (default: 'gray').
        ax: Optional axes to plot on (default: create new figure).
        random_seed: Random seed for reproducibility (default: None).

    Returns:
        Matplotlib Figure containing the plot.

    Raises:
        ValueError: If alpha_prior, beta_prior, or n_scenarios are not positive.

    Example:
        >>> from proportions.visualization.posterior_plots import plot_prior_mu_uncoupled
        >>> fig = plot_prior_mu_uncoupled(alpha_prior=1.0, beta_prior=1.0, n_scenarios=3)
        >>> fig.savefig('prior_mu_uncoupled.png')
    """
    if alpha_prior <= 0:
        raise ValueError(f"alpha_prior must be positive, got {alpha_prior}")
    if beta_prior <= 0:
        raise ValueError(f"beta_prior must be positive, got {beta_prior}")
    if n_scenarios <= 0:
        raise ValueError(f"n_scenarios must be positive, got {n_scenarios}")

    # Set random seed if provided
    if random_seed is not None:
        np.random.seed(random_seed)

    # Sample from prior: θᵢ ~ Beta(α, β) for each scenario
    theta_samples = np.random.beta(alpha_prior, beta_prior, size=(n_samples, n_scenarios))

    # Compute μ = (1/K)Σθᵢ
    mu_samples = theta_samples.mean(axis=1)

    # Create figure if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Plot histogram
    ax.hist(mu_samples, bins=50, density=True, alpha=0.6, color=color, edgecolor='black')

    # Add mean line
    mu_mean = mu_samples.mean()
    ax.axvline(mu_mean, color='black', linestyle='--', linewidth=2,
               label=f'Prior mean = {mu_mean:.3f}')

    # Labels and title
    ax.set_xlabel('μ (Average Success Rate)', fontsize=12)
    ax.set_ylabel('Density', fontsize=12)

    if title is None:
        title = f'Uncoupled Thetas Prior: p(μ) with K={n_scenarios}\nBeta({alpha_prior:.1f}, {beta_prior:.1f}) per scenario'
    ax.set_title(title, fontsize=13, fontweight='bold')

    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    return fig


def plot_posterior_mu_uncoupled(
    result,  # UncoupledThetasResult
    figsize: tuple[float, float] = (10, 6),
    title: str | None = None,
    color: str = 'darkblue',
    show_fitted: bool = True,
    show_histogram: bool = True,
    show_ci: bool = True,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot posterior distribution of μ for uncoupled thetas model.

    Uses stored MC samples from result.mu_samples to show the posterior
    distribution of μ = (1/K)Σθᵢ, optionally overlaying the fitted Beta.

    Args:
        result: UncoupledThetasResult with mu_samples.
        figsize: Figure size (default: (10, 6)).
        title: Plot title (default: auto-generated).
        color: Plot color (default: 'darkblue').
        show_fitted: Show fitted Beta distribution (default: True).
        show_histogram: Show histogram of samples (default: True).
        show_ci: Show 95% credible interval (default: True).
        ax: Optional axes to plot on (default: create new figure).

    Returns:
        Matplotlib Figure containing the plot.

    Raises:
        ValueError: If result doesn't have mu_samples.

    Example:
        >>> from proportions.inference import uncoupled_thetas
        >>> from proportions.visualization.posterior_plots import plot_posterior_mu_uncoupled
        >>> result = uncoupled_thetas(data, random_seed=42)
        >>> fig = plot_posterior_mu_uncoupled(result)
        >>> fig.savefig('posterior_mu_uncoupled.png')
    """
    if result.mu_samples is None:
        raise ValueError(
            "result must have mu_samples. This should not happen with "
            "normal uncoupled_thetas() usage."
        )

    # Create figure if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    mu_samples = result.mu_samples

    # Plot histogram if requested
    if show_histogram:
        ax.hist(mu_samples, bins=50, density=True, alpha=0.6, color=color,
                edgecolor='black', label='MC samples')

    # Plot fitted Beta if requested
    if show_fitted:
        x = np.linspace(0, 1, 1000)
        from scipy.stats import beta as beta_dist
        alpha_fit = result.aggregate_posterior.alpha_fitted
        beta_fit = result.aggregate_posterior.beta_fitted
        y = beta_dist.pdf(x, alpha_fit, beta_fit)
        ax.plot(x, y, 'r-', linewidth=2.5, label=f'Fitted Beta({alpha_fit:.2f}, {beta_fit:.2f})')

    # Add mean line
    mu_mean = result.aggregate_posterior.mu
    ax.axvline(mu_mean, color='purple', linestyle=':', linewidth=2,
               label=f'Posterior mean = {mu_mean:.3f}')

    # Add credible interval if requested
    if show_ci:
        ci_lower = result.aggregate_posterior.ci_lower
        ci_upper = result.aggregate_posterior.ci_upper
        ax.axvline(ci_lower, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
        ax.axvline(ci_upper, color='red', linestyle='--', linewidth=1.5, alpha=0.7,
                   label=f'95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]')

        # Shade CI region if showing fitted
        if show_fitted:
            x_fill = x[(x >= ci_lower) & (x <= ci_upper)]
            y_fill = beta_dist.pdf(x_fill, alpha_fit, beta_fit)
            ax.fill_between(x_fill, y_fill, alpha=0.2, color='red')

    # Labels and title
    ax.set_xlabel('μ (Average Success Rate)', fontsize=12)
    ax.set_ylabel('Density', fontsize=12)

    if title is None:
        title = f'Uncoupled Thetas Posterior: p(μ | data) with K={result.n_scenarios}'
    ax.set_title(title, fontsize=13, fontweight='bold')

    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    return fig
