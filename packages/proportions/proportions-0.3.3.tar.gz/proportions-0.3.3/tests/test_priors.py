"""Tests for prior specification models in proportions.priors.specification."""

import pytest

from proportions.priors.specification import (
    BetaPriorSpec,
    UniformPriorSpec,
    HyperpriorSpec,
)


class TestBetaPriorSpec:
    """Tests for BetaPriorSpec model."""

    def test_parameters_mode(self):
        """Test direct parameter specification."""
        prior = BetaPriorSpec(
            mode='parameters',
            alpha=2.0,
            beta=3.0
        )
        assert prior.mode == 'parameters'
        assert prior.alpha == 2.0
        assert prior.beta == 3.0

    def test_parameters_mode_missing_alpha(self):
        """Test that parameters mode requires alpha."""
        with pytest.raises(ValueError, match="requires both alpha and beta"):
            BetaPriorSpec(
                mode='parameters',
                beta=3.0
            )

    def test_parameters_mode_missing_beta(self):
        """Test that parameters mode requires beta."""
        with pytest.raises(ValueError, match="requires both alpha and beta"):
            BetaPriorSpec(
                mode='parameters',
                alpha=2.0
            )

    def test_credible_interval_mode(self):
        """Test credible interval specification."""
        prior = BetaPriorSpec(
            mode='credible_interval',
            ci_lower=0.7,
            ci_upper=0.9
        )
        assert prior.mode == 'credible_interval'
        assert prior.ci_lower == 0.7
        assert prior.ci_upper == 0.9
        assert prior.ci_level == 0.95  # Default

    def test_credible_interval_mode_missing_lower(self):
        """Test that CI mode requires ci_lower."""
        with pytest.raises(ValueError, match="requires both ci_lower and ci_upper"):
            BetaPriorSpec(
                mode='credible_interval',
                ci_upper=0.9
            )

    def test_credible_interval_mode_missing_upper(self):
        """Test that CI mode requires ci_upper."""
        with pytest.raises(ValueError, match="requires both ci_lower and ci_upper"):
            BetaPriorSpec(
                mode='credible_interval',
                ci_lower=0.7
            )

    def test_credible_interval_inverted_rejected(self):
        """Test that inverted CI bounds are rejected."""
        with pytest.raises(ValueError, match="ci_lower.*must be < ci_upper"):
            BetaPriorSpec(
                mode='credible_interval',
                ci_lower=0.9,
                ci_upper=0.7
            )

    def test_credible_interval_equal_rejected(self):
        """Test that equal CI bounds are rejected."""
        with pytest.raises(ValueError, match="ci_lower.*must be < ci_upper"):
            BetaPriorSpec(
                mode='credible_interval',
                ci_lower=0.8,
                ci_upper=0.8
            )

    def test_custom_ci_level(self):
        """Test custom CI level."""
        prior = BetaPriorSpec(
            mode='credible_interval',
            ci_lower=0.7,
            ci_upper=0.9,
            ci_level=0.90
        )
        assert prior.ci_level == 0.90

    def test_negative_alpha_rejected(self):
        """Test that negative alpha is rejected."""
        with pytest.raises(ValueError):
            BetaPriorSpec(
                mode='parameters',
                alpha=-1.0,
                beta=3.0
            )

    def test_zero_alpha_rejected(self):
        """Test that zero alpha is rejected."""
        with pytest.raises(ValueError):
            BetaPriorSpec(
                mode='parameters',
                alpha=0.0,
                beta=3.0
            )

    def test_ci_out_of_bounds_rejected(self):
        """Test that CI bounds outside [0,1] are rejected."""
        with pytest.raises(ValueError):
            BetaPriorSpec(
                mode='credible_interval',
                ci_lower=-0.1,
                ci_upper=0.9
            )

        with pytest.raises(ValueError):
            BetaPriorSpec(
                mode='credible_interval',
                ci_lower=0.7,
                ci_upper=1.1
            )

    def test_uniform_prior(self):
        """Test uniform Beta(1,1) prior."""
        prior = BetaPriorSpec(
            mode='parameters',
            alpha=1.0,
            beta=1.0
        )
        assert prior.alpha == 1.0
        assert prior.beta == 1.0


class TestUniformPriorSpec:
    """Tests for UniformPriorSpec model."""

    def test_valid_uniform(self):
        """Test valid uniform prior."""
        prior = UniformPriorSpec(
            min_value=1.0,
            max_value=100.0
        )
        assert prior.min_value == 1.0
        assert prior.max_value == 100.0

    def test_inverted_bounds_rejected(self):
        """Test that inverted bounds are rejected."""
        with pytest.raises(ValueError, match="min_value.*must be < max_value"):
            UniformPriorSpec(
                min_value=100.0,
                max_value=1.0
            )

    def test_equal_bounds_rejected(self):
        """Test that equal bounds are rejected."""
        with pytest.raises(ValueError, match="min_value.*must be < max_value"):
            UniformPriorSpec(
                min_value=50.0,
                max_value=50.0
            )

    def test_negative_bounds_allowed(self):
        """Test that negative bounds are allowed."""
        prior = UniformPriorSpec(
            min_value=-10.0,
            max_value=10.0
        )
        assert prior.min_value == -10.0
        assert prior.max_value == 10.0

    def test_wide_range(self):
        """Test very wide range."""
        prior = UniformPriorSpec(
            min_value=0.001,
            max_value=10000.0
        )
        assert prior.min_value == 0.001
        assert prior.max_value == 10000.0


class TestHyperpriorSpec:
    """Tests for HyperpriorSpec model."""

    def test_default_hyperprior(self):
        """Test default hyperprior (uniform on both m and k)."""
        hyperprior = HyperpriorSpec()

        # Default m_prior is Beta(1, 1) - uniform on [0,1]
        assert hyperprior.m_prior.mode == 'parameters'
        assert hyperprior.m_prior.alpha == 1.0
        assert hyperprior.m_prior.beta == 1.0

        # Default k_prior is Uniform(1, 1000)
        assert hyperprior.k_prior.min_value == 1.0
        assert hyperprior.k_prior.max_value == 1000.0

    def test_custom_m_prior_parameters(self):
        """Test custom m prior with direct parameters."""
        hyperprior = HyperpriorSpec(
            m_prior=BetaPriorSpec(
                mode='parameters',
                alpha=2.0,
                beta=2.0
            )
        )
        assert hyperprior.m_prior.alpha == 2.0
        assert hyperprior.m_prior.beta == 2.0

    def test_custom_m_prior_ci(self):
        """Test custom m prior with CI specification."""
        hyperprior = HyperpriorSpec(
            m_prior=BetaPriorSpec(
                mode='credible_interval',
                ci_lower=0.7,
                ci_upper=0.9
            )
        )
        assert hyperprior.m_prior.mode == 'credible_interval'
        assert hyperprior.m_prior.ci_lower == 0.7
        assert hyperprior.m_prior.ci_upper == 0.9

    def test_custom_k_prior(self):
        """Test custom k prior."""
        hyperprior = HyperpriorSpec(
            k_prior=UniformPriorSpec(
                min_value=5.0,
                max_value=500.0
            )
        )
        assert hyperprior.k_prior.min_value == 5.0
        assert hyperprior.k_prior.max_value == 500.0

    def test_custom_both_priors(self):
        """Test custom priors for both m and k."""
        hyperprior = HyperpriorSpec(
            m_prior=BetaPriorSpec(
                mode='credible_interval',
                ci_lower=0.75,
                ci_upper=0.95,
                ci_level=0.90
            ),
            k_prior=UniformPriorSpec(
                min_value=10.0,
                max_value=200.0
            )
        )

        # Check m prior
        assert hyperprior.m_prior.mode == 'credible_interval'
        assert hyperprior.m_prior.ci_lower == 0.75
        assert hyperprior.m_prior.ci_upper == 0.95
        assert hyperprior.m_prior.ci_level == 0.90

        # Check k prior
        assert hyperprior.k_prior.min_value == 10.0
        assert hyperprior.k_prior.max_value == 200.0

    def test_informative_priors(self):
        """Test setup with informative priors."""
        hyperprior = HyperpriorSpec(
            m_prior=BetaPriorSpec(
                mode='parameters',
                alpha=8.0,  # Mode near 0.8
                beta=2.0
            ),
            k_prior=UniformPriorSpec(
                min_value=20.0,  # Expect moderate to high concentration
                max_value=100.0
            )
        )

        assert hyperprior.m_prior.alpha == 8.0
        assert hyperprior.m_prior.beta == 2.0
        assert hyperprior.k_prior.min_value == 20.0
        assert hyperprior.k_prior.max_value == 100.0

    def test_very_wide_k_prior(self):
        """Test with very wide k prior for adversarial data."""
        hyperprior = HyperpriorSpec(
            k_prior=UniformPriorSpec(
                min_value=0.1,   # Allow U-shaped priors
                max_value=5000.0  # Allow very concentrated priors
            )
        )
        assert hyperprior.k_prior.min_value == 0.1
        assert hyperprior.k_prior.max_value == 5000.0
