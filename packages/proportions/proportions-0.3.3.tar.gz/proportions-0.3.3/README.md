# Proportions: Bayesian Inference for Grouped Binomial Data

[![PyPI version](https://badge.fury.io/py/proportions.svg)](https://pypi.org/project/proportions/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A Python library for estimating average success rates across multiple groups using Bayesian and frequentist methods.

## Installation

```bash
pip install proportions
```

That's it! No need to clone the repository unless you want to contribute (see Developer Setup below).

## Quick Start

```python
import numpy as np
from proportions.core.models import BinomialData
from proportions.inference import hierarchical_bayes, single_theta_bayesian

# Your data: success counts (x) and trial counts (n) per group
x = np.array([8, 7, 9, 6, 8])  # successes
n = np.array([10, 10, 10, 10, 10])  # trials
data = BinomialData(x=x, n=n)

# Hierarchical Bayes (RECOMMENDED - accounts for all uncertainty)
hb_result = hierarchical_bayes(data, random_seed=42)
print(f"Average success rate: {hb_result.posterior.mu:.3f}")
print(f"95% CI: [{hb_result.posterior.ci_lower:.3f}, {hb_result.posterior.ci_upper:.3f}]")

# Single-Theta Bayesian (simpler, assumes homogeneity)
st_result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)
print(f"Average success rate: {st_result.posterior.mu:.3f}")
print(f"95% CI: [{st_result.posterior.ci_lower:.3f}, {st_result.posterior.ci_upper:.3f}]")
```

## When to Use This Library

When you have binomial data from multiple groups and want to:

1. **Estimate the average success rate** across all groups
2. **Quantify uncertainty** with credible/confidence intervals
3. **Account for heterogeneity** between groups
4. **Compare different modeling approaches** with automatic diagnostics

**Examples:** Success rates across experiments, conversion rates across user segments, test pass rates across scenarios.

## Available Methods

| Method | Description | When to Use |
|--------|-------------|-------------|
| **Hierarchical Bayes** ⭐ | Full Bayesian with importance sampling | Default choice - honest uncertainty |
| **Single-Theta Bayesian** | Pooled model (homogeneous groups) | Groups believed identical |
| **Clopper-Pearson** | Frequentist exact confidence intervals | Baseline comparison |

## Comparing Methods

```python
from proportions.core.models import BinomialData
from proportions.inference import hierarchical_bayes, single_theta_bayesian
import numpy as np

# Prepare data
x = np.array([8, 7, 9, 6, 8])
n = np.array([10, 10, 10, 10, 10])
data = BinomialData(x=x, n=n)

# Fit multiple methods
hb_result = hierarchical_bayes(data, random_seed=42)
st_result = single_theta_bayesian(data, alpha_prior=1.0, beta_prior=1.0)

# Compare via model evidence (marginal likelihood)
print("Model Evidence Comparison:")
print(f"Hierarchical Bayes: {hb_result.log_marginal_likelihood:.2f}")
print(f"Single-Theta: {st_result.log_marginal_likelihood:.2f}")

# Calculate Bayes Factor
log_bf = hb_result.log_marginal_likelihood - st_result.log_marginal_likelihood
bf = np.exp(log_bf)
print(f"\nBayes Factor (HB vs ST): {bf:.2e}")
```

## Single Proportion Inference

For analyzing a **single binomial proportion** (not grouped data), the library provides specialized functions with support for **truncated Beta priors**:

```python
from proportions.inference import (
    conf_interval_proportion,
    upper_bound_proportion,
    prob_larger_than_threshold,
)
from proportions.diagnostics import plot_posterior_proportion

# Example: Rare failure rate estimation
# Domain knowledge: failure rate is between 1-10 per million
n_trials = 500_000
n_failures = 1

# Credible interval with truncated prior
interval = conf_interval_proportion(
    n_failures, n_trials,
    confidence=0.95,
    prior_alpha=1.0,      # Uniform prior
    prior_beta=1.0,
    lower=1e-6,           # 1 per million (lower bound)
    upper=10e-6           # 10 per million (upper bound)
)
print(f"95% CI: [{interval[0]*1e6:.2f}, {interval[1]*1e6:.2f}] per million")

# One-sided bounds
upper_95 = upper_bound_proportion(n_failures, n_trials, confidence=0.95,
                                  lower=1e-6, upper=10e-6)
print(f"95% upper bound: {upper_95*1e6:.2f} per million")

# Threshold probabilities
prob = prob_larger_than_threshold(n_failures, n_trials, threshold=3e-6,
                                  lower=1e-6, upper=10e-6)
print(f"P(rate > 3/million): {prob:.1%}")

# Visualize posterior
fig = plot_posterior_proportion(
    n_failures, n_trials,
    confidence=0.95,
    lower=1e-6,
    upper=10e-6,
    title="Failure Rate Posterior"
)
fig.savefig('posterior.png', dpi=150, bbox_inches='tight')
```

**Available Functions:**
- `conf_interval_proportion()` - Equal-tails credible intervals
- `upper_bound_proportion()` - Upper credible bounds
- `lower_bound_proportion()` - Lower credible bounds
- `prob_larger_than_threshold()` - P(θ > threshold | data)
- `prob_smaller_than_threshold()` - P(θ < threshold | data)
- `prob_of_interval()` - P(θ ∈ [a,b] | data)
- `plot_posterior_proportion()` - Visualize posterior distribution

**Key Features:**
- **Truncated priors** - Incorporate domain knowledge about plausible ranges
- **Standard Beta priors** - Use `lower=0.0, upper=1.0` (default) for standard Beta
- **All priors supported** - Uniform, Jeffreys, or custom Beta(α, β)
- **Comprehensive inference** - Intervals, bounds, probabilities, visualization

See `demo_failure_rate.py` for a complete example.

## Features

- **Multiple estimation methods** with unified API
- **Single proportion inference** with truncated Beta priors
- **Automatic validation** of input data (Pydantic models)
- **Model evidence** (marginal likelihood) for method comparison
- **Bayes factors** with interpretation
- **Effective Sample Size (ESS)** for importance sampling diagnostics
- **Variance decomposition** (within-group vs between-group uncertainty)
- **Numerically stable** Beta distribution functions (log-space computation)
- **Visualization tools** for posterior distributions

## Custom Priors

```python
from proportions.inference import hierarchical_bayes

# Hierarchical Bayes with custom prior parameters
result = hierarchical_bayes(
    data,
    m_prior_alpha=2.0,    # Beta prior for m: E[m] = 2/(2+2) = 0.5
    m_prior_beta=2.0,     # More informative than uniform
    k_prior_min=0.1,      # Allow low concentration (high heterogeneity)
    k_prior_max=100.0,    # Moderate maximum concentration
    n_samples=10000,      # More samples for better approximation
    random_seed=42
)

# Check diagnostics
print(f"Posterior mean for m: {result.m_posterior_mean:.3f}")
print(f"Posterior mean for k: {result.k_posterior_mean:.3f}")
print(f"Effective Sample Size: {result.diagnostics.effective_sample_size:.1f}")
```

## Documentation

- **Repository:** https://gitlab.com/movellan/proportions
- **Examples:** See `examples/` directory in the repository
- **Theory:** Based on Beta-Binomial hierarchical models with conjugate priors

## License

MIT License

## Citation

If you use this library in your research, please cite:

```bibtex
@software{proportions2025,
  author = {Movellan, Javier},
  title = {Proportions: Bayesian and Frequentist Inference for Grouped Binomial Data},
  year = {2025},
  url = {https://pypi.org/project/proportions/}
}
```

---

## Developer Setup (Optional)

Only needed if you want to contribute to the library or run examples from the repository.

### Using uv (Recommended - Fast and Modern)

**First, install uv if you don't have it:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

**Then, set up the project:**
```bash
# Clone the repository
git clone git@gitlab.com:movellan/proportions.git
cd proportions

# Install with uv (automatically creates .venv and installs all dependencies)
uv sync

# Run tests to verify installation
uv run pytest tests/ -v

# Run commands with uv (no activation needed!)
uv run python examples/demo_script.py
```

**Why uv?**
- No need to activate: `uv run` automatically uses the project venv
- Fast installation (10-100x faster than pip)
- Reproducible builds with uv.lock

### Using pip (Alternative)

```bash
# Clone the repository
git clone git@gitlab.com:movellan/proportions.git
cd proportions

# Create virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests to verify installation
pytest tests/ -v
```

### Running Tests

```bash
# With uv
uv run pytest                      # All tests
uv run pytest -v --cov=proportions # With coverage

# With pip (after activation)
pytest                             # All tests
pytest -v --cov=proportions        # With coverage
```

### Code Quality

```bash
# With uv
uv run ruff format .       # Format code
uv run ruff check .        # Lint
uv run mypy proportions/   # Type check

# With pip (after activation)
ruff format .              # Format code
ruff check .               # Lint
mypy proportions/          # Type check
```

## Contact

**Author:** Javier Movellan
**Email:** jrmovellan@gmail.com
**Repository:** https://gitlab.com/movellan/proportions
