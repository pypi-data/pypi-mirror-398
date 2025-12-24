"""Prior specification models for the proportions library.

This module defines Pydantic models for specifying priors in different ways,
allowing users to choose the most intuitive specification method.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BetaPriorSpec(BaseModel):
    """Specification for Beta prior distribution.

    Supports two specification modes:
    1. Direct: specify alpha and beta parameters directly
    2. Credible interval: specify via a credible interval (e.g., 95% CI)

    Attributes:
        mode: Specification mode ('parameters' or 'credible_interval').
        alpha: Direct alpha parameter (mode='parameters').
        beta: Direct beta parameter (mode='parameters').
        ci_lower: Lower bound of credible interval (mode='credible_interval').
        ci_upper: Upper bound of credible interval (mode='credible_interval').
        ci_level: Credible interval level (default 0.95).

    Examples:
        >>> # Direct specification
        >>> prior = BetaPriorSpec(mode='parameters', alpha=2.0, beta=2.0)

        >>> # Credible interval specification
        >>> prior = BetaPriorSpec(
        ...     mode='credible_interval',
        ...     ci_lower=0.7,
        ...     ci_upper=0.9,
        ...     ci_level=0.95
        ... )
    """

    mode: Literal['parameters', 'credible_interval'] = Field(
        ..., description="Specification mode"
    )

    # Direct specification
    alpha: float | None = Field(default=None, gt=0.0, description="Beta alpha parameter")
    beta: float | None = Field(default=None, gt=0.0, description="Beta beta parameter")

    # CI specification
    ci_lower: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Lower bound of CI"
    )
    ci_upper: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Upper bound of CI"
    )
    ci_level: float = Field(default=0.95, ge=0.0, le=1.0, description="CI level")

    @model_validator(mode='after')
    def validate_specification(self):
        """Validate that required fields are provided for the chosen mode."""
        if self.mode == 'parameters':
            if self.alpha is None or self.beta is None:
                raise ValueError("mode='parameters' requires both alpha and beta")
        elif self.mode == 'credible_interval':
            if self.ci_lower is None or self.ci_upper is None:
                raise ValueError(
                    "mode='credible_interval' requires both ci_lower and ci_upper"
                )
            if self.ci_lower >= self.ci_upper:
                raise ValueError(
                    f"ci_lower ({self.ci_lower}) must be < ci_upper ({self.ci_upper})"
                )
        return self


class UniformPriorSpec(BaseModel):
    """Specification for uniform prior distribution.

    Attributes:
        min_value: Minimum value (inclusive).
        max_value: Maximum value (inclusive).

    Example:
        >>> prior = UniformPriorSpec(min_value=1.0, max_value=1000.0)
    """

    min_value: float = Field(..., description="Minimum value")
    max_value: float = Field(..., description="Maximum value")

    @model_validator(mode='after')
    def validate_range(self):
        """Validate that min < max."""
        if self.min_value >= self.max_value:
            raise ValueError(
                f"min_value ({self.min_value}) must be < max_value ({self.max_value})"
            )
        return self


class HyperpriorSpec(BaseModel):
    """Specification for hyperpriors on (m, k) for Hierarchical Bayes.

    The hierarchical model uses:
    - m = α/(α+β): mean parameter of the Beta prior
    - k = α+β: concentration parameter of the Beta prior

    Attributes:
        m_prior: Prior specification for m (default: uniform Beta(1,1)).
        k_prior: Prior specification for k (default: Uniform(1, 1000)).

    Example:
        >>> # Default: uniform priors (non-informative)
        >>> hyperprior = HyperpriorSpec()

        >>> # Custom: informative prior on m, wide prior on k
        >>> hyperprior = HyperpriorSpec(
        ...     m_prior=BetaPriorSpec(
        ...         mode='credible_interval',
        ...         ci_lower=0.7,
        ...         ci_upper=0.9
        ...     ),
        ...     k_prior=UniformPriorSpec(min_value=5.0, max_value=500.0)
        ... )
    """

    m_prior: BetaPriorSpec = Field(
        default_factory=lambda: BetaPriorSpec(mode='parameters', alpha=1.0, beta=1.0),
        description="Prior on m = α/(α+β)",
    )

    k_prior: UniformPriorSpec = Field(
        default_factory=lambda: UniformPriorSpec(min_value=1.0, max_value=1000.0),
        description="Prior on k = α+β",
    )
