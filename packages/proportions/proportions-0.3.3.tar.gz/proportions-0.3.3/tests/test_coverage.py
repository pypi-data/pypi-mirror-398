"""Tests for coverage diagnostics module."""

import numpy as np
import pytest
from proportions.diagnostics.coverage import (
    CoverageSimulationConfig,
    CoverageMetrics,
    CoverageSimulationResult,
    generate_binomial_data,
    run_single_simulation,
    run_coverage_simulation
)


class TestCoverageSimulationConfig:
    """Tests for CoverageSimulationConfig."""

    def test_valid_config_alpha_beta(self):
        """Test creating valid configuration with (alpha, beta)."""
        config = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=50,
            n_samples_min=10,
            n_samples_max=100,
            n_simulations=100,
            ci_level=0.95,
            random_seed=42
        )
        assert config.true_alpha == 17.0
        assert config.true_beta == 3.0
        assert config.n_groups == 50

    def test_valid_config_m_k(self):
        """Test creating valid configuration with (m, k)."""
        config = CoverageSimulationConfig(
            true_m=0.85,
            true_k=20.0,
            n_groups=50,
            n_samples_min=10,
            n_samples_max=100,
            n_simulations=100,
            ci_level=0.95,
            random_seed=42
        )
        assert config.true_m == 0.85
        assert config.true_k == 20.0
        assert config.n_groups == 50

    def test_get_alpha_beta_from_m_k(self):
        """Test conversion from (m, k) to (alpha, beta)."""
        config = CoverageSimulationConfig(
            true_m=0.85,
            true_k=20.0,
            n_groups=50,
            n_samples_min=10,
            n_samples_max=100,
            n_simulations=100
        )
        alpha, beta = config.get_alpha_beta()
        assert abs(alpha - 17.0) < 1e-10
        assert abs(beta - 3.0) < 1e-10

    def test_get_m_k_from_alpha_beta(self):
        """Test conversion from (alpha, beta) to (m, k)."""
        config = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=50,
            n_samples_min=10,
            n_samples_max=100,
            n_simulations=100
        )
        m, k = config.get_m_k()
        assert abs(m - 0.85) < 1e-10
        assert abs(k - 20.0) < 1e-10

    def test_true_T_property(self):
        """Test computation of true T."""
        config = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=50,
            n_samples_min=10,
            n_samples_max=100,
            n_simulations=100
        )
        expected_T = 17.0 / (17.0 + 3.0)
        assert abs(config.true_T - expected_T) < 1e-10

    def test_true_T_from_m_k(self):
        """Test computation of true T from (m, k)."""
        config = CoverageSimulationConfig(
            true_m=0.85,
            true_k=20.0,
            n_groups=50,
            n_samples_min=10,
            n_samples_max=100,
            n_simulations=100
        )
        assert abs(config.true_T - 0.85) < 1e-10

    def test_missing_both_parameterizations(self):
        """Test that missing both parameterizations raises error."""
        with pytest.raises(ValueError, match="Must specify either"):
            CoverageSimulationConfig(
                n_groups=50,
                n_samples_min=10,
                n_samples_max=100,
                n_simulations=100
            )

    def test_both_parameterizations_rejected(self):
        """Test that providing both parameterizations raises error."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            CoverageSimulationConfig(
                true_alpha=17.0,
                true_beta=3.0,
                true_m=0.85,
                true_k=20.0,
                n_groups=50,
                n_samples_min=10,
                n_samples_max=100,
                n_simulations=100
            )

    def test_invalid_alpha(self):
        """Test that negative alpha raises error."""
        with pytest.raises(ValueError):
            CoverageSimulationConfig(
                true_alpha=-1.0,
                true_beta=3.0,
                n_groups=50,
                n_samples_min=10,
                n_samples_max=100,
                n_simulations=100
            )

    def test_invalid_m_out_of_range(self):
        """Test that m >= 1 raises error."""
        with pytest.raises(ValueError):
            CoverageSimulationConfig(
                true_m=1.5,
                true_k=20.0,
                n_groups=50,
                n_samples_min=10,
                n_samples_max=100,
                n_simulations=100
            )

    def test_invalid_sample_bounds(self):
        """Test that n_samples_max < n_samples_min raises error."""
        with pytest.raises(ValueError):
            CoverageSimulationConfig(
                true_alpha=17.0,
                true_beta=3.0,
                n_groups=50,
                n_samples_min=100,
                n_samples_max=10,
                n_simulations=100
            )


class TestGenerateBinomialData:
    """Tests for generate_binomial_data."""

    def test_data_generation(self):
        """Test that generated data has correct shape and properties."""
        rng = np.random.default_rng(42)
        data = generate_binomial_data(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=50,
            n_samples_min=10,
            n_samples_max=100,
            rng=rng
        )

        assert len(data.x) == 50
        assert len(data.n) == 50
        assert np.all(data.n >= 10)
        assert np.all(data.n <= 100)
        assert np.all(data.x >= 0)
        assert np.all(data.x <= data.n)

    def test_reproducibility(self):
        """Test that same seed produces same data."""
        data1 = generate_binomial_data(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=20,
            n_samples_min=10,
            n_samples_max=50,
            rng=np.random.default_rng(42)
        )

        data2 = generate_binomial_data(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=20,
            n_samples_min=10,
            n_samples_max=50,
            rng=np.random.default_rng(42)
        )

        assert np.array_equal(data1.x, data2.x)
        assert np.array_equal(data1.n, data2.n)


class TestRunSingleSimulation:
    """Tests for run_single_simulation."""

    def test_single_simulation_runs(self):
        """Test that single simulation completes."""
        config = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=20,
            n_samples_min=20,
            n_samples_max=50,
            n_simulations=1,
            random_seed=42
        )
        rng = np.random.default_rng(42)

        results = run_single_simulation(config, rng)

        assert 'empirical_bayes' in results
        assert 'hierarchical_bayes' in results
        assert 'single_theta' in results
        assert 'clopper_pearson' in results

    def test_result_structure(self):
        """Test that results have expected structure."""
        config = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=20,
            n_samples_min=20,
            n_samples_max=50,
            n_simulations=1,
            random_seed=42
        )
        rng = np.random.default_rng(42)

        results = run_single_simulation(config, rng)

        for method_result in results.values():
            assert 'ci_lower' in method_result
            assert 'ci_upper' in method_result
            assert 'T_hat' in method_result
            assert 'covered' in method_result
            assert 'ci_width' in method_result
            assert 'error' in method_result

    def test_ci_properties(self):
        """Test that CIs have valid properties."""
        config = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=30,
            n_samples_min=30,
            n_samples_max=60,
            n_simulations=1,
            random_seed=42
        )
        rng = np.random.default_rng(42)

        results = run_single_simulation(config, rng)

        for method_name, method_result in results.items():
            # CI lower <= upper
            if not np.isnan(method_result['ci_lower']):
                assert method_result['ci_lower'] <= method_result['ci_upper'], \
                    f"{method_name}: CI lower > upper"

                # CI width is positive
                assert method_result['ci_width'] >= 0, \
                    f"{method_name}: negative CI width"


class TestRunCoverageSimulation:
    """Tests for run_coverage_simulation."""

    def test_small_simulation(self):
        """Test running small coverage simulation."""
        config = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=20,
            n_samples_min=20,
            n_samples_max=50,
            n_simulations=10,
            random_seed=42
        )

        result = run_coverage_simulation(config, verbose=False)

        assert result.n_simulations_completed == 10
        assert len(result.metrics) == 4
        assert result.true_T == config.true_T

    def test_metrics_structure(self):
        """Test that metrics have correct structure."""
        config = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=20,
            n_samples_min=20,
            n_samples_max=50,
            n_simulations=10,
            random_seed=42
        )

        result = run_coverage_simulation(config, verbose=False)

        for method_name, metrics in result.metrics.items():
            assert isinstance(metrics, CoverageMetrics)
            assert metrics.method_name == method_name
            assert 0 <= metrics.empirical_coverage <= 1
            assert metrics.coverage_se >= 0
            assert metrics.mean_ci_width >= 0 or np.isnan(metrics.mean_ci_width)

    def test_format_table(self):
        """Test that format_table produces output."""
        config = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=20,
            n_samples_min=20,
            n_samples_max=50,
            n_simulations=10,
            random_seed=42
        )

        result = run_coverage_simulation(config, verbose=False)
        table = result.format_table()

        assert isinstance(table, str)
        assert len(table) > 0
        assert "Coverage" in table
        assert "RMSE" in table
        assert "Bias" in table

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        config1 = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=20,
            n_samples_min=20,
            n_samples_max=50,
            n_simulations=10,
            random_seed=42
        )

        config2 = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=20,
            n_samples_min=20,
            n_samples_max=50,
            n_simulations=10,
            random_seed=42
        )

        result1 = run_coverage_simulation(config1, verbose=False)
        result2 = run_coverage_simulation(config2, verbose=False)

        # Check that coverage is similar (but HB has randomness, so allow tolerance)
        for method in result1.metrics.keys():
            if method == 'hierarchical_bayes':
                # HB uses random sampling, so coverage may vary slightly
                assert abs(result1.metrics[method].empirical_coverage -
                          result2.metrics[method].empirical_coverage) < 0.2
                assert abs(result1.metrics[method].rmse -
                          result2.metrics[method].rmse) < 0.01
            else:
                # Other methods should be fully reproducible
                assert abs(result1.metrics[method].empirical_coverage -
                          result2.metrics[method].empirical_coverage) < 1e-10
                assert abs(result1.metrics[method].rmse -
                          result2.metrics[method].rmse) < 1e-10

    def test_moderate_heterogeneity(self):
        """Test with moderate heterogeneity (reduced for speed)."""
        config = CoverageSimulationConfig(
            true_alpha=17.0,
            true_beta=3.0,
            n_groups=20,  # Reduced from 50
            n_samples_min=30,
            n_samples_max=60,
            n_simulations=20,  # Reduced from 100
            random_seed=42
        )

        result = run_coverage_simulation(config, verbose=False)

        # Check that methods completed without all failing
        # Note: Single-theta may have low coverage with heterogeneity - that's expected
        for method_name, metrics in result.metrics.items():
            if method_name != 'single_theta':
                # Bayesian methods should have some coverage (not zero, not one)
                assert 0.5 <= metrics.empirical_coverage <= 1.0, \
                    f"{method_name} has unreasonable coverage: {metrics.empirical_coverage}"

            # RMSE should be reasonable (not too large) if not all NaN
            if not np.isnan(metrics.rmse):
                assert metrics.rmse < 0.1, \
                    f"{method_name} has large RMSE: {metrics.rmse}"
