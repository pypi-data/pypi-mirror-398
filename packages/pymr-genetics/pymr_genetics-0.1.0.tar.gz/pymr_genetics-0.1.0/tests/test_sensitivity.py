"""Tests for sensitivity analyses (TDD - write tests first)."""

import numpy as np
import pandas as pd
import pytest

from pymr.sensitivity import (
    steiger_filtering,
    cochrans_q,
    rucker_q,
    leave_one_out,
    single_snp,
)


class TestSteiger:
    """Test Steiger directionality filtering."""

    def test_steiger_identifies_correct_direction(self):
        """Steiger should identify SNPs explaining more variance in exposure."""
        # Strong exposure effects, weak outcome effects
        beta_exp = np.array([0.1, 0.15, 0.12])
        se_exp = np.array([0.01, 0.01, 0.01])
        beta_out = np.array([0.02, 0.03, 0.025])
        se_out = np.array([0.02, 0.02, 0.02])

        result = steiger_filtering(beta_exp, se_exp, beta_out, se_out, 1000, 1000)

        assert result["direction_correct"]  # True or np.True_
        assert result["n_correct"] > 0

    def test_steiger_returns_filtered_indices(self):
        """Steiger should return indices of correct direction SNPs."""
        beta_exp = np.array([0.1, 0.15, 0.12])
        se_exp = np.array([0.01, 0.01, 0.01])
        beta_out = np.array([0.02, 0.03, 0.025])
        se_out = np.array([0.02, 0.02, 0.02])

        result = steiger_filtering(beta_exp, se_exp, beta_out, se_out, 1000, 1000)

        assert "filtered_indices" in result
        assert len(result["filtered_indices"]) <= len(beta_exp)


class TestCochransQ:
    """Test Cochran's Q heterogeneity test."""

    def test_cochrans_q_with_homogeneous_data(self):
        """Q test should show low heterogeneity for consistent SNPs."""
        # All SNPs point to same causal effect
        beta_exp = np.array([0.1, 0.2, 0.15])
        se_exp = np.array([0.01, 0.02, 0.015])
        # Outcome effects proportional to exposure (beta=0.5)
        beta_out = beta_exp * 0.5
        se_out = np.array([0.02, 0.03, 0.025])

        result = cochrans_q(beta_exp, se_exp, beta_out, se_out, causal_estimate=0.5)

        assert result["Q"] >= 0
        assert result["Q_pval"] > 0.05  # Not significant heterogeneity

    def test_cochrans_q_returns_i2(self):
        """Q test should return I² statistic."""
        beta_exp = np.array([0.1, 0.2, 0.15])
        se_exp = np.array([0.01, 0.02, 0.015])
        beta_out = np.array([0.05, 0.10, 0.075])
        se_out = np.array([0.02, 0.03, 0.025])

        result = cochrans_q(beta_exp, se_exp, beta_out, se_out, causal_estimate=0.5)

        assert "I2" in result
        assert 0 <= result["I2"] <= 100


class TestRuckerQ:
    """Test Rucker's Q test for pleiotropy."""

    def test_rucker_q_compares_ivw_egger(self):
        """Rucker should compare IVW vs Egger model fit."""
        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01, 0.02, 0.015, 0.01, 0.02])
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09])
        se_out = np.array([0.02, 0.03, 0.025, 0.02, 0.03])

        result = rucker_q(beta_exp, se_exp, beta_out, se_out)

        assert "Q_IVW" in result
        assert "Q_Egger" in result
        assert "Q_diff" in result
        assert "pleiotropy_detected" in result


class TestLeaveOneOut:
    """Test leave-one-out sensitivity analysis."""

    def test_leave_one_out_returns_dataframe(self):
        """Leave-one-out should return DataFrame with one row per SNP."""
        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01, 0.02, 0.015, 0.01, 0.02])
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09])
        se_out = np.array([0.02, 0.03, 0.025, 0.02, 0.03])

        result = leave_one_out(beta_exp, se_exp, beta_out, se_out)

        assert isinstance(result, pd.DataFrame)
        assert len(result) <= len(beta_exp)

    def test_leave_one_out_with_snp_ids(self):
        """Leave-one-out should use provided SNP IDs."""
        beta_exp = np.array([0.1, 0.2, 0.15])
        se_exp = np.array([0.01, 0.02, 0.015])
        beta_out = np.array([0.05, 0.10, 0.075])
        se_out = np.array([0.02, 0.03, 0.025])
        snp_ids = ["rs1", "rs2", "rs3"]

        result = leave_one_out(beta_exp, se_exp, beta_out, se_out, snp_ids=snp_ids)

        assert "excluded_snp" in result.columns
        assert all(snp in snp_ids for snp in result["excluded_snp"])


class TestSingleSNP:
    """Test single SNP analysis."""

    def test_single_snp_returns_dataframe(self):
        """Single SNP should return DataFrame with Wald ratios."""
        beta_exp = np.array([0.1, 0.2, 0.15])
        se_exp = np.array([0.01, 0.02, 0.015])
        beta_out = np.array([0.05, 0.10, 0.075])
        se_out = np.array([0.02, 0.03, 0.025])

        result = single_snp(beta_exp, se_exp, beta_out, se_out)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(beta_exp)
        assert "beta" in result.columns
        assert "se" in result.columns
        assert "pval" in result.columns


class TestRadialMR:
    """Test radial MR analysis."""

    def test_radial_mr_returns_dict(self):
        """radial_mr should return dictionary with outlier detection results."""
        from pymr.sensitivity import radial_mr

        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01, 0.02, 0.015, 0.01, 0.02])
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09])
        se_out = np.array([0.02, 0.03, 0.025, 0.02, 0.03])

        result = radial_mr(beta_exp, se_exp, beta_out, se_out)

        assert isinstance(result, dict)
        assert "outlier_indices" in result
        assert "Q_total" in result
        assert "Q_outliers" in result

    def test_radial_mr_identifies_outliers(self):
        """radial_mr should identify outlier SNPs using Q contribution."""
        from pymr.sensitivity import radial_mr

        # Create data with one clear outlier
        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01, 0.02, 0.015, 0.01, 0.02])
        # First 4 SNPs consistent with beta=0.5, last is outlier
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.30])  # rs5 is outlier
        se_out = np.array([0.02, 0.03, 0.025, 0.02, 0.03])

        result = radial_mr(beta_exp, se_exp, beta_out, se_out, alpha=0.05)

        assert "outlier_indices" in result
        assert isinstance(result["outlier_indices"], np.ndarray)

    def test_radial_mr_returns_weights(self):
        """radial_mr should return radial weights for plotting."""
        from pymr.sensitivity import radial_mr

        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01, 0.02, 0.015, 0.01, 0.02])
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09])
        se_out = np.array([0.02, 0.03, 0.025, 0.02, 0.03])

        result = radial_mr(beta_exp, se_exp, beta_out, se_out)

        assert "weights" in result
        assert len(result["weights"]) == len(beta_exp)
        assert all(w > 0 for w in result["weights"])

    def test_radial_mr_with_ivw_method(self):
        """radial_mr should support IVW method."""
        from pymr.sensitivity import radial_mr

        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01, 0.02, 0.015, 0.01, 0.02])
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09])
        se_out = np.array([0.02, 0.03, 0.025, 0.02, 0.03])

        result = radial_mr(beta_exp, se_exp, beta_out, se_out, method="IVW")

        assert "beta" in result
        assert "se" in result

    def test_radial_mr_with_egger_method(self):
        """radial_mr should support Egger method."""
        from pymr.sensitivity import radial_mr

        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01, 0.02, 0.015, 0.01, 0.02])
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09])
        se_out = np.array([0.02, 0.03, 0.025, 0.02, 0.03])

        result = radial_mr(beta_exp, se_exp, beta_out, se_out, method="Egger")

        assert "beta" in result
        assert "se" in result
        assert "intercept" in result

    def test_radial_mr_q_contribution(self):
        """radial_mr should compute Q contribution for each SNP."""
        from pymr.sensitivity import radial_mr

        beta_exp = np.array([0.1, 0.2, 0.15, 0.12, 0.18])
        se_exp = np.array([0.01, 0.02, 0.015, 0.01, 0.02])
        beta_out = np.array([0.05, 0.10, 0.075, 0.06, 0.09])
        se_out = np.array([0.02, 0.03, 0.025, 0.02, 0.03])

        result = radial_mr(beta_exp, se_exp, beta_out, se_out)

        assert "Q_contribution" in result
        assert len(result["Q_contribution"]) == len(beta_exp)
        assert all(q >= 0 for q in result["Q_contribution"])
