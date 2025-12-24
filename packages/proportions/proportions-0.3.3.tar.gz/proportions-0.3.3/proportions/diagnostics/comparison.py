"""Comparison utilities for multiple inference methods.

This module provides tools for comparing results from different inference
methods, including formatted tables and summary statistics.
"""

from typing import Any

from proportions.core.models import (
    EmpiricalBayesResult,
    HierarchicalBayesResult,
    PosteriorResult,
)


def print_comparison_table(
    results: dict[str, PosteriorResult | EmpiricalBayesResult | HierarchicalBayesResult],
    true_value: float | None = None,
) -> None:
    """Print formatted comparison table for multiple inference methods.

    Args:
        results: Dictionary mapping method names to results.
                 Values can be PosteriorResult or full inference results
                 (EB, HB, etc.) - will extract .posterior if needed.
        true_value: Optional true value of T for coverage checking.

    Example:
        >>> from proportions.inference import empirical_bayes, hierarchical_bayes
        >>> from proportions.diagnostics import print_comparison_table
        >>>
        >>> eb_result = empirical_bayes(data)
        >>> hb_result = hierarchical_bayes(data, random_seed=42)
        >>>
        >>> results = {
        ...     "Empirical Bayes": eb_result,
        ...     "Hierarchical Bayes": hb_result,
        ... }
        >>> print_comparison_table(results, true_value=0.85)
    """
    # Extract posteriors from results
    posteriors = {}
    for name, result in results.items():
        if isinstance(result, (EmpiricalBayesResult, HierarchicalBayesResult)):
            posteriors[name] = result.posterior
        elif isinstance(result, PosteriorResult):
            posteriors[name] = result
        else:
            raise ValueError(
                f"Result for '{name}' must be PosteriorResult, "
                f"EmpiricalBayesResult, or HierarchicalBayesResult"
            )

    # Determine column widths
    name_width = max(len(name) for name in posteriors.keys())
    name_width = max(name_width, 20)  # Minimum width

    # Print header
    print("=" * (name_width + 65))
    print(f"{'Method':<{name_width}}  {'Mean':>10}  {'CI Lower':>10}  "
          f"{'CI Upper':>10}  {'CI Width':>10}  {'Coverage':>8}")
    print("-" * (name_width + 65))

    # Print each method
    for name, posterior in posteriors.items():
        mean = posterior.mu
        ci_low = posterior.ci_lower
        ci_high = posterior.ci_upper
        ci_width = posterior.ci_width

        # Check coverage
        if true_value is not None:
            if ci_low <= true_value <= ci_high:
                coverage = "[OK]"
            else:
                coverage = "[MISS]"
        else:
            coverage = "---"

        print(f"{name:<{name_width}}  {mean:>10.4f}  {ci_low:>10.4f}  "
              f"{ci_high:>10.4f}  {ci_width:>10.4f}  {coverage:>8}")

    print("=" * (name_width + 65))

    # Summary statistics if true_value provided
    if true_value is not None:
        print(f"\nTrue Value: {true_value:.4f}")
        n_covered = sum(
            1 for p in posteriors.values()
            if p.ci_lower <= true_value <= p.ci_upper
        )
        n_total = len(posteriors)
        print(f"Coverage: {n_covered}/{n_total} ({n_covered/n_total:.1%})")

        # Find closest estimate
        errors = {name: abs(p.mu - true_value) for name, p in posteriors.items()}
        best_method = min(errors, key=errors.get)
        print(f"Closest Estimate: {best_method} (error = {errors[best_method]:.4f})")

        # Find narrowest CI
        widths = {name: p.ci_width for name, p in posteriors.items()}
        narrowest_method = min(widths, key=widths.get)
        print(f"Narrowest CI: {narrowest_method} (width = {widths[narrowest_method]:.4f})")
