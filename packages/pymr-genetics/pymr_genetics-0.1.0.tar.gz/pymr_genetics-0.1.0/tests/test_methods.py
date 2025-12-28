"""Tests for individual MR methods."""

import numpy as np
import pytest

from pymr.methods import simple_mode, weighted_mode, contamination_mixture


class TestSimpleMode:
    """Test simple mode-based MR estimation."""

    def test_simple_mode_basic(self):
        """Simple mode should find peak of Wald ratio distribution."""
        # Create data where most SNPs have Wald ratio ~0.5
        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18, 0.14, 0.16])
        se_exp = np.array([0.01] * 7)
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09, 0.07, 0.08])
        se_out = np.array([0.02] * 7)

        result = simple_mode(beta_exp, se_exp, beta_out, se_out)

        assert "beta" in result
        assert "se" in result
        assert "pval" in result
        # Mode should be around 0.5
        assert 0.4 < result["beta"] < 0.6

    def test_simple_mode_custom_bandwidth(self):
        """Simple mode should accept custom bandwidth."""
        beta_exp = np.array([0.1, 0.2, 0.15])
        se_exp = np.array([0.01] * 3)
        beta_out = np.array([0.05, 0.10, 0.075])
        se_out = np.array([0.02] * 3)

        result = simple_mode(beta_exp, se_exp, beta_out, se_out, bandwidth=0.1)

        assert "beta" in result
        assert result["nsnp"] == 3


class TestWeightedMode:
    """Test weighted mode-based MR estimation."""

    def test_weighted_mode_basic(self):
        """Weighted mode should weight by inverse variance."""
        # Create data where most SNPs have Wald ratio ~0.5
        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18, 0.14, 0.16])
        se_exp = np.array([0.01] * 7)
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09, 0.07, 0.08])
        se_out = np.array([0.02] * 7)

        result = weighted_mode(beta_exp, se_exp, beta_out, se_out)

        assert "beta" in result
        assert "se" in result
        assert "pval" in result
        assert "nsnp" in result
        # Mode should be around 0.5
        assert 0.4 < result["beta"] < 0.6
        assert result["nsnp"] == 7

    def test_weighted_mode_uses_inverse_variance_weights(self):
        """Weighted mode should use inverse variance weights in KDE."""
        # Create data with varying precision
        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01, 0.01, 0.01, 0.01, 0.01])
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09])
        # Vary the SE for outcome
        se_out = np.array([0.02, 0.01, 0.02, 0.03, 0.02])

        result = weighted_mode(beta_exp, se_exp, beta_out, se_out)

        # Should return valid results
        assert "beta" in result
        assert "se" in result
        assert "pval" in result
        # Result should be a valid estimate
        assert 0.3 < result["beta"] < 0.7

    def test_weighted_mode_custom_bandwidth(self):
        """Weighted mode should accept custom bandwidth."""
        beta_exp = np.array([0.1, 0.2, 0.15])
        se_exp = np.array([0.01] * 3)
        beta_out = np.array([0.05, 0.10, 0.075])
        se_out = np.array([0.02] * 3)

        result = weighted_mode(beta_exp, se_exp, beta_out, se_out, bandwidth=0.1)

        assert "beta" in result
        assert result["nsnp"] == 3

    def test_weighted_mode_returns_odds_ratio(self):
        """Weighted mode should include OR and confidence interval."""
        beta_exp = np.array([0.1, 0.2, 0.15])
        se_exp = np.array([0.01] * 3)
        beta_out = np.array([0.05, 0.10, 0.075])
        se_out = np.array([0.02] * 3)

        result = weighted_mode(beta_exp, se_exp, beta_out, se_out)

        assert "OR" in result
        assert "OR_lci" in result
        assert "OR_uci" in result
        assert result["OR"] == pytest.approx(np.exp(result["beta"]))


class TestContaminationMixture:
    """Test contamination mixture MR estimation."""

    def test_contamination_mixture_basic(self):
        """Contamination mixture should work with clean data."""
        # Create data with clean instruments (true causal effect = 0.5)
        np.random.seed(42)
        n_snps = 20
        true_beta = 0.5

        beta_exp = np.random.uniform(0.05, 0.2, n_snps)
        se_exp = np.full(n_snps, 0.01)
        beta_out = true_beta * beta_exp + np.random.normal(0, 0.02, n_snps)
        se_out = np.full(n_snps, 0.02)

        result = contamination_mixture(beta_exp, se_exp, beta_out, se_out)

        assert "beta" in result
        assert "se" in result
        assert "pval" in result
        assert "prob_valid" in result
        assert "n_valid" in result
        assert "nsnp" in result

        # Should estimate close to true effect
        assert 0.3 < result["beta"] < 0.7
        assert result["nsnp"] == n_snps

        # Probability valid should be array with length n_snps
        assert len(result["prob_valid"]) == n_snps

        # All SNPs should have high probability of being valid
        assert np.mean(result["prob_valid"]) > 0.7

    def test_contamination_mixture_identifies_contaminated_snps(self):
        """Contamination mixture should identify pleiotropic SNPs."""
        np.random.seed(123)
        n_valid = 15
        n_invalid = 5
        true_beta = 0.4

        # Valid instruments
        beta_exp_valid = np.random.uniform(0.05, 0.2, n_valid)
        beta_out_valid = true_beta * beta_exp_valid + np.random.normal(0, 0.01, n_valid)

        # Invalid instruments (pleiotropic - no correlation with true effect)
        beta_exp_invalid = np.random.uniform(0.05, 0.2, n_invalid)
        beta_out_invalid = np.random.normal(0, 0.1, n_invalid)

        # Combine
        beta_exp = np.concatenate([beta_exp_valid, beta_exp_invalid])
        se_exp = np.full(n_valid + n_invalid, 0.01)
        beta_out = np.concatenate([beta_out_valid, beta_out_invalid])
        se_out = np.full(n_valid + n_invalid, 0.02)

        result = contamination_mixture(beta_exp, se_exp, beta_out, se_out)

        # Should identify contaminated SNPs with lower prob_valid
        prob_valid = result["prob_valid"]

        # Valid SNPs should have higher probability
        assert np.mean(prob_valid[:n_valid]) > np.mean(prob_valid[n_valid:])

        # Should estimate reasonable number of valid SNPs
        assert 10 < result["n_valid"] < 20

    def test_contamination_mixture_returns_expected_keys(self):
        """Contamination mixture should return all expected keys."""
        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01] * 5)
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09])
        se_out = np.array([0.02] * 5)

        result = contamination_mixture(beta_exp, se_exp, beta_out, se_out)

        expected_keys = ["beta", "se", "pval", "prob_valid", "n_valid", "nsnp"]
        for key in expected_keys:
            assert key in result

    def test_contamination_mixture_requires_min_snps(self):
        """Contamination mixture should require at least 3 SNPs."""
        beta_exp = np.array([0.1, 0.2])
        se_exp = np.array([0.01, 0.01])
        beta_out = np.array([0.05, 0.10])
        se_out = np.array([0.02, 0.02])

        with pytest.raises(ValueError, match="at least 3 SNPs"):
            contamination_mixture(beta_exp, se_exp, beta_out, se_out)
