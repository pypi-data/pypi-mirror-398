"""Tests for MR analysis methods (TDD - write tests first)."""

import numpy as np
import pandas as pd
import pytest

from pymr import MR
from pymr.methods import ivw, weighted_median, mr_egger


class TestIVW:
    """Test Inverse Variance Weighted MR."""

    def test_ivw_basic(self):
        """IVW should compute weighted average of Wald ratios."""
        # Arrange: Simple case with 3 SNPs
        beta_exp = np.array([0.1, 0.2, 0.15])
        se_exp = np.array([0.01, 0.02, 0.015])
        beta_out = np.array([0.05, 0.10, 0.075])
        se_out = np.array([0.02, 0.03, 0.025])

        # Act
        result = ivw(beta_exp, se_exp, beta_out, se_out)

        # Assert
        assert "beta" in result
        assert "se" in result
        assert "pval" in result
        # Wald ratio should be ~0.5 (beta_out / beta_exp)
        assert 0.4 < result["beta"] < 0.6

    def test_ivw_returns_odds_ratio(self):
        """IVW should include OR and confidence interval."""
        beta_exp = np.array([0.1, 0.2])
        se_exp = np.array([0.01, 0.02])
        beta_out = np.array([0.05, 0.10])
        se_out = np.array([0.02, 0.03])

        result = ivw(beta_exp, se_exp, beta_out, se_out)

        assert "OR" in result
        assert "OR_lci" in result
        assert "OR_uci" in result
        assert result["OR"] == pytest.approx(np.exp(result["beta"]))

    def test_ivw_single_snp(self):
        """IVW with single SNP should equal Wald ratio."""
        beta_exp = np.array([0.1])
        se_exp = np.array([0.01])
        beta_out = np.array([0.05])
        se_out = np.array([0.02])

        result = ivw(beta_exp, se_exp, beta_out, se_out)

        expected_wald = beta_out[0] / beta_exp[0]
        assert result["beta"] == pytest.approx(expected_wald)


class TestWeightedMedian:
    """Test Weighted Median MR (robust to 50% invalid instruments)."""

    def test_weighted_median_basic(self):
        """Weighted median should return median of Wald ratios."""
        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01] * 5)
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09])
        se_out = np.array([0.02] * 5)

        result = weighted_median(beta_exp, se_exp, beta_out, se_out)

        assert "beta" in result
        assert "se" in result
        # Median Wald ratio should be ~0.5
        assert 0.4 < result["beta"] < 0.6

    def test_weighted_median_requires_min_snps(self):
        """Weighted median needs at least 3 SNPs."""
        beta_exp = np.array([0.1, 0.2])
        se_exp = np.array([0.01, 0.02])
        beta_out = np.array([0.05, 0.10])
        se_out = np.array([0.02, 0.03])

        with pytest.raises(ValueError, match="at least 3"):
            weighted_median(beta_exp, se_exp, beta_out, se_out)


class TestMREgger:
    """Test MR-Egger regression (tests for pleiotropy)."""

    def test_egger_basic(self):
        """MR-Egger should return slope, intercept, and p-values."""
        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01] * 5)
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09])
        se_out = np.array([0.02] * 5)

        result = mr_egger(beta_exp, se_exp, beta_out, se_out)

        assert "beta" in result
        assert "intercept" in result
        assert "intercept_pval" in result

    def test_egger_intercept_interpretation(self):
        """Non-zero intercept suggests directional pleiotropy."""
        # Create data with pleiotropy (constant offset)
        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01] * 5)
        # Add constant pleiotropy effect of 0.02
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09]) + 0.02
        se_out = np.array([0.005] * 5)  # Low SE to detect effect

        result = mr_egger(beta_exp, se_exp, beta_out, se_out)

        # Intercept should be detectable
        assert abs(result["intercept"]) > 0.01


class TestMRClass:
    """Test the main MR orchestrator class."""

    @pytest.fixture
    def sample_data(self):
        """Create sample harmonized data for testing."""
        np.random.seed(42)
        n = 50
        return pd.DataFrame({
            "SNP": [f"rs{i}" for i in range(n)],
            "beta_exp": np.random.normal(0.1, 0.02, n),
            "se_exp": np.abs(np.random.normal(0.01, 0.002, n)),
            "beta_out": np.random.normal(0.05, 0.02, n),
            "se_out": np.abs(np.random.normal(0.02, 0.005, n)),
        })

    def test_mr_run_all_methods(self, sample_data):
        """MR.run() should return results for all methods."""
        mr = MR(sample_data)
        results = mr.run()

        assert isinstance(results, pd.DataFrame)
        assert "IVW" in results["method"].values
        assert "Weighted Median" in results["method"].values
        assert "MR-Egger" in results["method"].values

    def test_mr_run_specific_methods(self, sample_data):
        """MR.run() should accept specific methods."""
        mr = MR(sample_data)
        results = mr.run(methods=["IVW"])

        assert len(results) == 1
        assert results.iloc[0]["method"] == "IVW"

    def test_mr_heterogeneity(self, sample_data):
        """MR should compute heterogeneity statistics."""
        mr = MR(sample_data)
        het = mr.heterogeneity()

        assert "Q" in het
        assert "Q_pval" in het
        assert "I2" in het

    def test_mr_leave_one_out(self, sample_data):
        """MR.leave_one_out() should return n results."""
        mr = MR(sample_data)
        loo = mr.leave_one_out()

        assert len(loo) == len(sample_data)
        assert "excluded_snp" in loo.columns


class TestDataHarmonization:
    """Test GWAS data harmonization."""

    def test_harmonize_aligns_alleles(self):
        """Harmonization should flip betas for misaligned alleles."""
        from pymr.harmonize import harmonize

        exposure = pd.DataFrame({
            "SNP": ["rs1", "rs2"],
            "effect_allele": ["A", "C"],
            "other_allele": ["G", "T"],
            "beta": [0.1, 0.2],
            "se": [0.01, 0.02],
        })
        outcome = pd.DataFrame({
            "SNP": ["rs1", "rs2"],
            "effect_allele": ["A", "T"],  # rs2 flipped
            "other_allele": ["G", "C"],
            "beta": [0.05, -0.10],  # Already flipped in source
            "se": [0.02, 0.03],
        })

        harmonized = harmonize(exposure, outcome)

        # rs2 should be flipped to align with exposure
        assert harmonized.loc[harmonized["SNP"] == "rs2", "beta_out"].values[0] > 0

    def test_harmonize_removes_palindromic(self):
        """Harmonization should handle palindromic SNPs."""
        from pymr.harmonize import harmonize

        exposure = pd.DataFrame({
            "SNP": ["rs1", "rs2"],
            "effect_allele": ["A", "A"],
            "other_allele": ["G", "T"],  # rs2 is palindromic (A/T)
            "beta": [0.1, 0.2],
            "se": [0.01, 0.02],
            "eaf": [0.3, 0.5],  # Ambiguous MAF for rs2
        })
        outcome = pd.DataFrame({
            "SNP": ["rs1", "rs2"],
            "effect_allele": ["A", "T"],
            "other_allele": ["G", "A"],
            "beta": [0.05, 0.10],
            "se": [0.02, 0.03],
            "eaf": [0.3, 0.5],
        })

        harmonized = harmonize(exposure, outcome, remove_palindromic=True)

        # rs2 should be removed (palindromic with MAF ~0.5)
        assert len(harmonized) == 1
        assert harmonized.iloc[0]["SNP"] == "rs1"
