"""Visualization tools for Hierarchical Bayes importance sampling diagnostics.

This module provides diagnostic visualizations for assessing the quality
of importance sampling approximations, including marginal and joint posterior
distributions, and for visualizing single proportion posteriors.
"""

import numpy as np
import matplotlib.pyplot as plt

from proportions.diagnostics.importance_sampling import ImportanceSamples
from proportions.inference import empirical_bayes
from proportions.core.models import (
    BinomialData,
    PosteriorResult,
    EmpiricalBayesResult,
    HierarchicalBayesResult,
)
from proportions.distributions.truncated_beta import truncated_beta_pdf
from proportions.inference.single_proportion import conf_interval_proportion


def plot_mk_distributions(
    samples: ImportanceSamples,
    data: BinomialData | None = None,
    eb_comparison: bool = False,
    figsize: tuple[float, float] = (15, 5),
) -> plt.Figure:
    """Create 3-panel diagnostic figure showing distributions of m and k.

    Panels:
    1. Marginal posterior for m (weighted vs unweighted)
    2. Marginal posterior for k (weighted vs unweighted)
    3. 2D joint posterior p(m, k | data) using rectangular kernels

    Note: Panel 3 uses 2D histogram with rectangular kernels (not KDE).
    This provides better visualization for highly concentrated posteriors.
    Number of bins is chosen to have ~10 samples per bin.

    Args:
        samples: ImportanceSamples from extract_importance_samples().
        data: Optional BinomialData (kept for backward compatibility, not used).
        eb_comparison: Deprecated parameter (kept for backward compatibility, ignored).
        figsize: Figure size (width, height).

    Returns:
        Matplotlib Figure object.

    Example:
        >>> from proportions.diagnostics.importance_sampling import extract_importance_samples
        >>> from proportions.diagnostics.visualization import plot_mk_distributions
        >>>
        >>> samples = extract_importance_samples(data, random_seed=42)
        >>> fig = plot_mk_distributions(samples)
        >>> fig.savefig('mk_distributions.png', dpi=150, bbox_inches='tight')
        >>> plt.show()
    """
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    fig.suptitle(f'Distribution of (m, k) | data\n'
                f'ESS = {samples.effective_sample_size:.1f} / {samples.n_samples} '
                f'({samples.effective_sample_size/samples.n_samples:.1%})',
                fontsize=14, fontweight='bold')

    # Weighted posterior means
    m_mean = np.sum(samples.weights * samples.m_samples)
    k_mean = np.sum(samples.weights * samples.k_samples)

    # ============================================================
    # Panel 1: Marginal posterior for m
    # ============================================================
    ax = axes[0]
    ax.hist(samples.m_samples, bins=50, alpha=0.3, color='gray',
           density=True, label='Prior samples (unweighted)')
    ax.hist(samples.m_samples, bins=50, weights=samples.weights,
           alpha=0.7, color='purple', density=True,
           label='Posterior (weighted)')
    ax.axvline(m_mean, color='purple', linestyle='--', linewidth=2,
              label=f'HB: m={m_mean:.3f}')
    ax.set_xlabel('m (mean parameter)', fontsize=11)
    ax.set_ylabel('Density', fontsize=11)
    ax.set_title('Marginal Posterior p(m | data)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ============================================================
    # Panel 2: Marginal posterior for k
    # ============================================================
    ax = axes[1]
    # Use log scale for k if range is large
    k_range = samples.k_prior_max - samples.k_prior_min
    if k_range > 100:
        bins = np.logspace(np.log10(max(samples.k_prior_min, 1)),
                          np.log10(samples.k_prior_max), 50)
        ax.set_xscale('log')
    else:
        bins = 50

    ax.hist(samples.k_samples, bins=bins, alpha=0.3, color='gray',
           density=True, label='Prior samples (unweighted)')
    ax.hist(samples.k_samples, bins=bins, weights=samples.weights,
           alpha=0.7, color='orange', density=True,
           label='Posterior (weighted)')
    ax.axvline(k_mean, color='orange', linestyle='--', linewidth=2,
              label=f'HB: k={k_mean:.1f}')
    ax.set_xlabel('k (concentration parameter)', fontsize=11)
    ax.set_ylabel('Density', fontsize=11)
    ax.set_title('Marginal Posterior p(k | data)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ============================================================
    # Panel 3: 2D joint posterior p(m, k | data)
    # ============================================================
    ax = axes[2]
    try:
        # Use 2D histogram with rectangular kernels (better for concentrated posteriors)
        # Determine number of bins: aim for ~10 samples per bin
        n_bins = max(10, int(np.sqrt(samples.n_samples / 10)))

        # Create 2D weighted histogram
        H, m_edges, k_edges = np.histogram2d(
            samples.m_samples, samples.k_samples,
            bins=n_bins, weights=samples.weights, density=True
        )

        # Create meshgrid for plotting
        m_centers = (m_edges[:-1] + m_edges[1:]) / 2
        k_centers = (k_edges[:-1] + k_edges[1:]) / 2
        M, K = np.meshgrid(m_centers, k_centers)

        # Plot as pcolormesh (rectangular kernels)
        pcm = ax.pcolormesh(m_edges, k_edges, H.T, cmap='viridis',
                           shading='flat', alpha=0.8)
        plt.colorbar(pcm, ax=ax, label='Posterior Density')


        # Mark HB weighted mean
        ax.plot(m_mean, k_mean, 'r*', markersize=15, label='HB weighted mean',
               markeredgecolor='white', markeredgewidth=1)

    except Exception as e:
        # Fallback to scatter if histogram fails
        ax.scatter(samples.m_samples, samples.k_samples,
                  c=samples.weights, cmap='viridis', alpha=0.5, s=20)
        ax.plot(m_mean, k_mean, 'r*', markersize=15, label='HB')

    ax.set_xlabel('m (mean parameter)', fontsize=11)
    ax.set_ylabel('k (concentration parameter)', fontsize=11)
    ax.set_title('Joint Posterior p(m, k | data)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_importance_sampling_diagnostics(
    samples: ImportanceSamples,
    data: BinomialData | None = None,
    eb_comparison: bool = False,
    figsize: tuple[float, float] = (16, 10),
) -> plt.Figure:
    """Create comprehensive 6-panel diagnostic figure for importance sampling.

    Panels:
    1. Marginal posterior for m (weighted vs unweighted)
    2. Marginal posterior for k (weighted vs unweighted)
    3. 2D joint posterior p(m, k | data) using rectangular kernels
    4. 2D joint posterior p(α, β | data) using rectangular kernels
    5. Scatter plot in (α, β) space with sizes proportional to weight
    6. Weight distribution histogram

    Note: Panels 3 and 4 use 2D histograms with rectangular kernels (not KDE).
    This provides better visualization for highly concentrated posteriors.
    Number of bins is chosen to have ~20 samples per bin.

    Args:
        samples: ImportanceSamples from extract_importance_samples().
        data: Optional BinomialData (kept for backward compatibility, not used).
        eb_comparison: Deprecated parameter (kept for backward compatibility, ignored).
        figsize: Figure size (width, height).

    Returns:
        Matplotlib Figure object.

    Example:
        >>> from proportions.diagnostics.importance_sampling import extract_importance_samples
        >>> from proportions.diagnostics.visualization import plot_importance_sampling_diagnostics
        >>>
        >>> samples = extract_importance_samples(data, random_seed=42)
        >>> fig = plot_importance_sampling_diagnostics(samples, data=data)
        >>> fig.savefig('hb_diagnostics.png', dpi=150, bbox_inches='tight')
        >>> plt.show()
    """
    fig, axes = plt.subplots(2, 3, figsize=figsize)
    fig.suptitle(f'Hierarchical Bayes Importance Sampling Diagnostics\n'
                f'ESS = {samples.effective_sample_size:.1f} / {samples.n_samples} '
                f'({samples.effective_sample_size/samples.n_samples:.1%})',
                fontsize=14, fontweight='bold')

    # Weighted posterior means
    m_mean = np.sum(samples.weights * samples.m_samples)
    k_mean = np.sum(samples.weights * samples.k_samples)
    alpha_mean = np.sum(samples.weights * samples.alpha_samples)
    beta_mean = np.sum(samples.weights * samples.beta_samples)

    # ============================================================
    # Panel 1: Marginal posterior for m
    # ============================================================
    ax = axes[0, 0]
    ax.hist(samples.m_samples, bins=50, alpha=0.3, color='gray',
           density=True, label='Prior samples (unweighted)')
    ax.hist(samples.m_samples, bins=50, weights=samples.weights,
           alpha=0.7, color='purple', density=True,
           label='Posterior (weighted)')
    ax.axvline(m_mean, color='purple', linestyle='--', linewidth=2,
              label=f'HB: m={m_mean:.3f}')
    ax.set_xlabel('m (mean parameter)', fontsize=11)
    ax.set_ylabel('Density', fontsize=11)
    ax.set_title('Marginal Posterior p(m | data)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ============================================================
    # Panel 2: Marginal posterior for k
    # ============================================================
    ax = axes[0, 1]
    # Use log scale for k if range is large
    k_range = samples.k_prior_max - samples.k_prior_min
    if k_range > 100:
        bins = np.logspace(np.log10(max(samples.k_prior_min, 1)),
                          np.log10(samples.k_prior_max), 50)
        ax.set_xscale('log')
    else:
        bins = 50

    ax.hist(samples.k_samples, bins=bins, alpha=0.3, color='gray',
           density=True, label='Prior samples (unweighted)')
    ax.hist(samples.k_samples, bins=bins, weights=samples.weights,
           alpha=0.7, color='orange', density=True,
           label='Posterior (weighted)')
    ax.axvline(k_mean, color='orange', linestyle='--', linewidth=2,
              label=f'HB: k={k_mean:.1f}')
    ax.set_xlabel('k (concentration parameter)', fontsize=11)
    ax.set_ylabel('Density', fontsize=11)
    ax.set_title('Marginal Posterior p(k | data)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ============================================================
    # Panel 3: 2D joint posterior p(m, k | data)
    # ============================================================
    ax = axes[0, 2]
    try:
        # Use 2D histogram with rectangular kernels (better for concentrated posteriors)
        # Determine number of bins: aim for ~10 samples per bin
        n_bins = max(10, int(np.sqrt(samples.n_samples / 10)))

        # Create 2D weighted histogram
        H, m_edges, k_edges = np.histogram2d(
            samples.m_samples, samples.k_samples,
            bins=n_bins, weights=samples.weights, density=True
        )

        # Create meshgrid for plotting
        m_centers = (m_edges[:-1] + m_edges[1:]) / 2
        k_centers = (k_edges[:-1] + k_edges[1:]) / 2
        M, K = np.meshgrid(m_centers, k_centers)

        # Plot as pcolormesh (rectangular kernels)
        pcm = ax.pcolormesh(m_edges, k_edges, H.T, cmap='viridis',
                           shading='flat', alpha=0.8)
        plt.colorbar(pcm, ax=ax, label='Posterior Density')

        # Mark HB weighted mean
        ax.plot(m_mean, k_mean, 'r*', markersize=15, label='HB weighted mean',
               markeredgecolor='white', markeredgewidth=1)

    except Exception as e:
        # Fallback to scatter if histogram fails
        ax.scatter(samples.m_samples, samples.k_samples,
                  c=samples.weights, cmap='viridis', alpha=0.5, s=20)
        ax.plot(m_mean, k_mean, 'r*', markersize=15, label='HB')

    ax.set_xlabel('m (mean parameter)', fontsize=11)
    ax.set_ylabel('k (concentration parameter)', fontsize=11)
    ax.set_title('Joint Posterior p(m, k | data)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ============================================================
    # Panel 4: 2D joint posterior p(α, β | data)
    # ============================================================
    ax = axes[1, 0]
    try:
        # Use 2D histogram with rectangular kernels (better for concentrated posteriors)
        # Determine number of bins: aim for ~10 samples per bin
        n_bins = max(10, int(np.sqrt(samples.n_samples / 10)))

        # Create 2D weighted histogram
        H, alpha_edges, beta_edges = np.histogram2d(
            samples.alpha_samples, samples.beta_samples,
            bins=n_bins, weights=samples.weights, density=True
        )

        # Create meshgrid for plotting
        alpha_centers = (alpha_edges[:-1] + alpha_edges[1:]) / 2
        beta_centers = (beta_edges[:-1] + beta_edges[1:]) / 2
        A, B = np.meshgrid(alpha_centers, beta_centers)

        # Plot as pcolormesh (rectangular kernels)
        pcm = ax.pcolormesh(alpha_edges, beta_edges, H.T, cmap='plasma',
                           shading='flat', alpha=0.8)
        plt.colorbar(pcm, ax=ax, label='Posterior Density')

        # Mark HB weighted mean
        ax.plot(alpha_mean, beta_mean, 'r*', markersize=15, label='HB weighted mean',
               markeredgecolor='white', markeredgewidth=1)

    except Exception as e:
        # Fallback to scatter if histogram fails
        ax.scatter(samples.alpha_samples, samples.beta_samples,
                  c=samples.weights, cmap='plasma', alpha=0.5, s=20)
        ax.plot(alpha_mean, beta_mean, 'r*', markersize=15, label='HB')

    ax.set_xlabel('α (Beta alpha parameter)', fontsize=11)
    ax.set_ylabel('β (Beta beta parameter)', fontsize=11)
    ax.set_title('Joint Posterior p(α, β | data)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ============================================================
    # Panel 5: Scatter plot with sizes proportional to weight
    # ============================================================
    ax = axes[1, 1]
    # Scale marker sizes: larger weights = larger markers
    marker_sizes = 1000 * samples.weights / np.max(samples.weights)
    scatter = ax.scatter(samples.alpha_samples, samples.beta_samples,
                        s=marker_sizes, c=samples.weights, cmap='cool',
                        alpha=0.6, edgecolors='black', linewidths=0.5)
    ax.plot(alpha_mean, beta_mean, 'r*', markersize=20, label='HB weighted mean',
           markeredgecolor='white', markeredgewidth=1.5, zorder=10)

    plt.colorbar(scatter, ax=ax, label='Weight')
    ax.set_xlabel('α (Beta alpha parameter)', fontsize=11)
    ax.set_ylabel('β (Beta beta parameter)', fontsize=11)
    ax.set_title('Weighted Samples (size proportional to weight)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ============================================================
    # Panel 6: Weight distribution
    # ============================================================
    ax = axes[1, 2]
    ax.hist(samples.weights, bins=50, color='steelblue', alpha=0.7, edgecolor='black')
    ax.axvline(np.mean(samples.weights), color='red', linestyle='--',
              linewidth=2, label=f'Mean = {np.mean(samples.weights):.6f}')
    ax.axvline(np.max(samples.weights), color='orange', linestyle=':',
              linewidth=2, label=f'Max = {np.max(samples.weights):.6f}')
    ax.set_xlabel('Normalized Weight', fontsize=11)
    ax.set_ylabel('Count', fontsize=11)
    ax.set_title(f'Weight Distribution\n(ESS = {samples.effective_sample_size:.1f})',
                fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')

    plt.tight_layout()
    return fig

def plot_posterior_proportion(
    success: int,
    counts: int,
    confidence: float = 0.95,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
    resolution: int = 1000,
    xlim: tuple[float, float] | None = None,
    thresholds: list[float] | None = None,
    figsize: tuple[float, float] = (10, 6),
    title: str | None = None,
) -> plt.Figure:
    """Plot posterior distribution for a single binomial proportion.

    Creates a visualization showing:
    - Posterior density curve
    - Credible interval with shaded region
    - Optional threshold lines

    Args:
        success: Number of successes (must be >= 0).
        counts: Total number of trials (must be >= success).
        confidence: Credible interval level (default: 0.95).
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
        lower: Lower bound of prior truncation (default: 0.0).
        upper: Upper bound of prior truncation (default: 1.0).
        resolution: Number of points for plotting curve (default: 1000).
        xlim: Optional (xmin, xmax) tuple for x-axis limits.
              If None, auto-determines based on 99.99% credible interval.
        thresholds: Optional list of threshold values to mark with vertical lines.
        figsize: Figure size as (width, height) tuple (default: (10, 6)).
        title: Optional custom title. If None, generates descriptive title.

    Returns:
        Matplotlib Figure object.

    Raises:
        ValueError: If inputs are invalid.

    Example:
        >>> from proportions.diagnostics.visualization import plot_posterior_proportion
        >>> import matplotlib.pyplot as plt
        >>>
        >>> # 30 successes out of 100 trials
        >>> fig = plot_posterior_proportion(30, 100, confidence=0.95)
        >>> fig.savefig('posterior.png', dpi=150, bbox_inches='tight')
        >>> plt.show()
        >>>
        >>> # With truncated prior and threshold lines
        >>> fig = plot_posterior_proportion(
        ...     30, 100,
        ...     confidence=0.95,
        ...     lower=0.2, upper=0.8,
        ...     thresholds=[0.25, 0.35],
        ...     title="Posterior with Truncated Prior"
        ... )
        >>> plt.show()
    """
    # Input validation
    if success < 0:
        raise ValueError(f"success must be non-negative, got {success}")
    if counts < 0:
        raise ValueError(f"counts must be non-negative, got {counts}")
    if success > counts:
        raise ValueError(f"success ({success}) cannot exceed counts ({counts})")
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0, 1), got {confidence}")
    if prior_alpha <= 0:
        raise ValueError(f"prior_alpha must be positive, got {prior_alpha}")
    if prior_beta <= 0:
        raise ValueError(f"prior_beta must be positive, got {prior_beta}")
    if not (0.0 <= lower < upper <= 1.0):
        raise ValueError(
            f"Must have 0 <= lower < upper <= 1, got lower={lower}, upper={upper}"
        )

    # Posterior parameters
    alpha_post = success + prior_alpha
    beta_post = counts - success + prior_beta

    # Determine x-axis range
    if xlim is None:
        # Auto-determine based on very wide credible interval (99.99%)
        ci_wide = conf_interval_proportion(
            success, counts, confidence=0.9999,
            prior_alpha=prior_alpha, prior_beta=prior_beta,
            lower=lower, upper=upper
        )
        xmin, xmax = ci_wide[0], ci_wide[1]

        # Ensure within truncation bounds
        xmin = max(xmin, lower)
        xmax = min(xmax, upper)
    else:
        xmin, xmax = xlim
        # Ensure within truncation bounds
        xmin = max(xmin, lower)
        xmax = min(xmax, upper)

    # Generate x values for plotting
    x = np.linspace(xmin, xmax, resolution)

    # Compute posterior PDF
    pdf = np.array([truncated_beta_pdf(xi, alpha_post, beta_post, lower, upper)
                    for xi in x])

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot posterior curve
    ax.plot(x, pdf, 'b-', linewidth=2, label='Posterior')

    # Get credible interval bounds
    ci = conf_interval_proportion(
        success, counts, confidence=confidence,
        prior_alpha=prior_alpha, prior_beta=prior_beta,
        lower=lower, upper=upper
    )
    ci_lower, ci_upper = ci[0], ci[1]

    # Compute PDF at interval bounds
    pdf_lower = truncated_beta_pdf(ci_lower, alpha_post, beta_post, lower, upper)
    pdf_upper = truncated_beta_pdf(ci_upper, alpha_post, beta_post, lower, upper)

    # Plot vertical lines at interval bounds
    ax.plot([ci_lower, ci_lower], [0, pdf_lower], 'r--', linewidth=1.5,
            label=f'{confidence:.0%} CI')
    ax.plot([ci_upper, ci_upper], [0, pdf_upper], 'r--', linewidth=1.5)

    # Shade credible interval region
    x_fill = x[(x >= ci_lower) & (x <= ci_upper)]
    y_fill = np.array([truncated_beta_pdf(xi, alpha_post, beta_post, lower, upper)
                      for xi in x_fill])
    ax.fill_between(x_fill, y_fill, color='red', alpha=0.3)

    # Add threshold lines if specified
    if thresholds is not None:
        pdf_max = np.max(pdf)
        for threshold in thresholds:
            if lower <= threshold <= upper:
                ax.plot([threshold, threshold], [0, pdf_max], 'k--',
                       linewidth=1, alpha=0.7)

    # Labels and title
    ax.set_xlabel('Proportion', fontsize=12)
    ax.set_ylabel('Posterior Density', fontsize=12)

    if title is None:
        # Generate descriptive title
        point_estimate = success / counts if counts > 0 else 0
        title_text = (f'Posterior Distribution: {success}/{counts} '
                     f'(p̂ = {point_estimate:.3f})\n'
                     f'{confidence:.0%} CI: [{ci_lower:.3f}, {ci_upper:.3f}]')
        if lower > 0.0 or upper < 1.0:
            title_text += f'\nTruncated Prior: [{lower:.2f}, {upper:.2f}]'
    else:
        title_text = title

    ax.set_title(title_text, fontsize=13, fontweight='bold')

    # Set y-axis to start at 0
    ylim = ax.get_ylim()
    ax.set_ylim(0, ylim[1] * 1.1)

    # Grid and legend
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    plt.tight_layout()
    return fig
