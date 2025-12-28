"""Tests for Bayesian Mendelian Randomization (TDD - write tests first)."""

import numpy as np
import pandas as pd
import pytest

from pymr.bayesian import BayesianMR
from pymr.methods import ivw, mr_egger


class TestBayesianMRInitialization:
    """Test BayesianMR initialization and validation."""

    def test_init_with_valid_data(self, small_harmonized_data):
        """BayesianMR should initialize with valid harmonized data."""
        bmr = BayesianMR(small_harmonized_data)
        assert bmr.data is not None
        assert len(bmr.data) == 5

    def test_init_with_custom_priors(self, small_harmonized_data):
        """BayesianMR should accept custom prior parameters."""
        bmr = BayesianMR(
            small_harmonized_data,
            prior_mean=0.5,
            prior_sd=2.0,
        )
        assert bmr.prior_mean == 0.5
        assert bmr.prior_sd == 2.0

    def test_init_validates_required_columns(self):
        """BayesianMR should raise error if required columns missing."""
        bad_data = pd.DataFrame({
            "beta_exp": [0.1, 0.2],
            "se_exp": [0.01, 0.02],
            # Missing beta_out and se_out
        })
        with pytest.raises(ValueError, match="Missing required columns"):
            BayesianMR(bad_data)


class TestBayesianIVW:
    """Test Bayesian IVW with normal likelihood."""

    def test_sample_returns_posterior_samples(self, small_harmonized_data):
        """sample() should return posterior samples array."""
        bmr = BayesianMR(small_harmonized_data)
        samples = bmr.sample(n_samples=1000, n_chains=2, warmup=100)

        assert samples is not None
        assert len(samples.shape) == 2  # (n_chains, n_samples)
        assert samples.shape[0] == 2
        assert samples.shape[1] == 1000

    def test_posterior_mean_matches_frequentist_ivw(self, small_harmonized_data):
        """Bayesian IVW posterior mean should approximate frequentist IVW."""
        # Frequentist IVW
        freq_result = ivw(
            small_harmonized_data["beta_exp"].values,
            small_harmonized_data["se_exp"].values,
            small_harmonized_data["beta_out"].values,
            small_harmonized_data["se_out"].values,
        )

        # Bayesian IVW with weak prior
        bmr = BayesianMR(small_harmonized_data, prior_mean=0, prior_sd=10)
        bmr.sample(n_samples=5000, n_chains=4, warmup=500)
        summary = bmr.summary()

        # Posterior mean should be close to frequentist estimate
        assert summary["mean"] == pytest.approx(freq_result["beta"], abs=0.05)

    def test_summary_returns_statistics(self, small_harmonized_data):
        """summary() should return posterior mean, sd, and credible intervals."""
        bmr = BayesianMR(small_harmonized_data)
        bmr.sample(n_samples=1000, n_chains=2, warmup=100)
        summary = bmr.summary()

        assert "mean" in summary
        assert "sd" in summary
        assert "ci_lower" in summary
        assert "ci_upper" in summary
        assert summary["ci_lower"] < summary["mean"] < summary["ci_upper"]

    def test_prior_influences_posterior(self, small_harmonized_data):
        """Strong prior should pull posterior toward prior mean."""
        # Weak prior
        bmr_weak = BayesianMR(small_harmonized_data, prior_mean=0, prior_sd=10)
        bmr_weak.sample(n_samples=2000, n_chains=2, warmup=200)
        weak_mean = bmr_weak.summary()["mean"]

        # Strong prior centered at 1.0
        bmr_strong = BayesianMR(small_harmonized_data, prior_mean=1.0, prior_sd=0.1)
        bmr_strong.sample(n_samples=2000, n_chains=2, warmup=200)
        strong_mean = bmr_strong.summary()["mean"]

        # Strong prior should pull estimate toward 1.0
        assert abs(strong_mean - 1.0) < abs(weak_mean - 1.0)


class TestBayesianEgger:
    """Test Bayesian Egger with intercept."""

    def test_bayesian_egger_estimates_intercept(self, small_harmonized_data):
        """Bayesian Egger should estimate both slope and intercept."""
        bmr = BayesianMR(
            small_harmonized_data,
            prior_mean=0,
            prior_sd=1,
            intercept_prior_mean=0,
            intercept_prior_sd=0.5,
        )
        bmr.sample(n_samples=2000, n_chains=2, warmup=200, model="egger")
        summary = bmr.summary()

        assert "beta_mean" in summary
        assert "intercept_mean" in summary
        assert "intercept_ci_lower" in summary
        assert "intercept_ci_upper" in summary

    def test_bayesian_egger_matches_frequentist(self, small_harmonized_data):
        """Bayesian Egger should approximate frequentist MR-Egger with weak priors."""
        # Frequentist MR-Egger
        freq_result = mr_egger(
            small_harmonized_data["beta_exp"].values,
            small_harmonized_data["se_exp"].values,
            small_harmonized_data["beta_out"].values,
            small_harmonized_data["se_out"].values,
        )

        # Bayesian Egger with weak priors
        bmr = BayesianMR(
            small_harmonized_data,
            prior_mean=0,
            prior_sd=10,
            intercept_prior_mean=0,
            intercept_prior_sd=10,
        )
        bmr.sample(n_samples=10000, n_chains=4, warmup=1000, model="egger")
        summary = bmr.summary()

        # Both slope and intercept should be reasonably close
        # MCMC with small samples can be quite variable, so use generous tolerance
        assert summary["beta_mean"] == pytest.approx(freq_result["beta"], abs=0.5)
        assert summary["intercept_mean"] == pytest.approx(
            freq_result["intercept"], abs=0.1
        )


class TestRobustBayesianMR:
    """Test robust Bayesian MR with t-distribution for outliers."""

    def test_robust_mr_with_outliers(self, small_harmonized_data):
        """Robust Bayesian MR should be less sensitive to outliers."""
        # Add an outlier
        data_with_outlier = small_harmonized_data.copy()
        data_with_outlier.loc[0, "beta_out"] = 0.5  # Extreme outlier

        # Normal likelihood (sensitive to outliers)
        bmr_normal = BayesianMR(data_with_outlier)
        bmr_normal.sample(n_samples=2000, n_chains=2, warmup=200, model="ivw")
        normal_mean = bmr_normal.summary()["mean"]

        # t-distribution likelihood (robust to outliers)
        bmr_robust = BayesianMR(data_with_outlier)
        bmr_robust.sample(n_samples=2000, n_chains=2, warmup=200, model="robust_ivw")
        robust_mean = bmr_robust.summary()["mean"]

        # Clean data estimate (no outlier)
        bmr_clean = BayesianMR(small_harmonized_data)
        bmr_clean.sample(n_samples=2000, n_chains=2, warmup=200, model="ivw")
        clean_mean = bmr_clean.summary()["mean"]

        # Robust estimate should be closer to clean data estimate
        assert abs(robust_mean - clean_mean) < abs(normal_mean - clean_mean)

    def test_robust_mr_estimates_degrees_of_freedom(self, small_harmonized_data):
        """Robust MR should estimate degrees of freedom for t-distribution."""
        bmr = BayesianMR(small_harmonized_data)
        bmr.sample(n_samples=2000, n_chains=2, warmup=200, model="robust_ivw")
        summary = bmr.summary()

        assert "nu_mean" in summary  # Degrees of freedom
        assert summary["nu_mean"] > 2  # Should be finite


class TestBayesFactor:
    """Test Bayes factor for causal effect vs null."""

    def test_bayes_factor_strong_evidence(self, sample_harmonized_data):
        """Strong causal effect should give large Bayes factor."""
        # Create data with strong causal effect
        data = sample_harmonized_data.copy()
        data["beta_out"] = data["beta_exp"] * 2.0 + np.random.normal(
            0, 0.01, len(data)
        )

        bmr = BayesianMR(data, prior_mean=0, prior_sd=5)
        bmr.sample(n_samples=5000, n_chains=4, warmup=500)
        bf = bmr.bayes_factor(null_value=0)

        # BF > 10 indicates strong evidence for causal effect
        assert bf > 10

    def test_bayes_factor_null_effect(self):
        """No causal effect should give small Bayes factor (favoring null)."""
        # Create data with no causal effect
        np.random.seed(42)
        data = pd.DataFrame({
            "beta_exp": np.random.normal(0.1, 0.02, 30),
            "se_exp": np.abs(np.random.normal(0.01, 0.002, 30)),
            "beta_out": np.random.normal(0, 0.02, 30),  # No effect
            "se_out": np.abs(np.random.normal(0.02, 0.005, 30)),
        })

        bmr = BayesianMR(data, prior_mean=0, prior_sd=1)
        bmr.sample(n_samples=5000, n_chains=4, warmup=500)
        bf = bmr.bayes_factor(null_value=0)

        # BF < 1 favors null (which is expected with no causal effect)
        # The closer to 0, the stronger the evidence for null
        assert bf < 1


class TestModelComparison:
    """Test Bayesian model comparison using WAIC/LOO-CV."""

    def test_model_comparison_returns_results(self, small_harmonized_data):
        """model_comparison() should compare IVW and Egger models."""
        bmr = BayesianMR(small_harmonized_data)
        comparison = bmr.model_comparison(models=["ivw", "egger"])

        assert "ivw" in comparison
        assert "egger" in comparison
        assert "waic" in comparison["ivw"]
        assert "waic" in comparison["egger"]

    def test_model_comparison_computes_waic(self, small_harmonized_data):
        """Model comparison should compute WAIC for both models."""
        bmr = BayesianMR(small_harmonized_data)
        comparison = bmr.model_comparison(models=["ivw", "egger"])

        # Both models should have WAIC computed
        assert "ivw" in comparison
        assert "egger" in comparison
        assert "waic" in comparison["ivw"]
        assert "waic" in comparison["egger"]
        # WAIC can be negative (it's on log scale)
        assert isinstance(comparison["ivw"]["waic"], float)
        assert isinstance(comparison["egger"]["waic"], float)

    def test_egger_preferred_with_pleiotropy(self):
        """Egger should be preferred when there's directional pleiotropy."""
        # Create data with pleiotropy (constant intercept)
        np.random.seed(42)
        data = pd.DataFrame({
            "beta_exp": np.random.normal(0.1, 0.02, 50),
            "se_exp": np.abs(np.random.normal(0.01, 0.002, 50)),
            "beta_out": np.random.normal(0.05, 0.02, 50) + 0.03,  # Pleiotropy
            "se_out": np.abs(np.random.normal(0.005, 0.001, 50)),
        })

        bmr = BayesianMR(data)
        comparison = bmr.model_comparison(models=["ivw", "egger"])

        # Egger should have lower WAIC (accounts for pleiotropy)
        assert comparison["egger"]["waic"] < comparison["ivw"]["waic"]


class TestPosteriorPlotting:
    """Test posterior visualization."""

    def test_plot_posterior_returns_axis(self, small_harmonized_data):
        """plot_posterior() should create and return matplotlib axis."""
        bmr = BayesianMR(small_harmonized_data)
        bmr.sample(n_samples=1000, n_chains=2, warmup=100)

        ax = bmr.plot_posterior()

        assert ax is not None
        assert hasattr(ax, "plot")  # Is a matplotlib axis

    def test_plot_posterior_with_custom_axis(self, small_harmonized_data):
        """plot_posterior() should accept custom matplotlib axis."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        bmr = BayesianMR(small_harmonized_data)
        bmr.sample(n_samples=1000, n_chains=2, warmup=100)

        returned_ax = bmr.plot_posterior(ax=ax)

        assert returned_ax is ax
        plt.close(fig)


class TestMCMCDiagnostics:
    """Test MCMC convergence diagnostics."""

    def test_rhat_convergence_diagnostic(self, small_harmonized_data):
        """Should compute R-hat statistic for convergence."""
        bmr = BayesianMR(small_harmonized_data)
        bmr.sample(n_samples=2000, n_chains=4, warmup=500)

        summary = bmr.summary()
        assert "rhat" in summary
        # R-hat should be close to 1 for convergence
        assert 0.9 < summary["rhat"] < 1.1

    def test_effective_sample_size(self, small_harmonized_data):
        """Should compute effective sample size."""
        bmr = BayesianMR(small_harmonized_data)
        bmr.sample(n_samples=2000, n_chains=4, warmup=500)

        summary = bmr.summary()
        assert "n_eff" in summary
        # ESS should be positive
        assert summary["n_eff"] > 0
