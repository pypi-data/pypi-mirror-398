"""Tests for MR-PRESSO (Pleiotropy RESidual Sum and Outlier) method.

MR-PRESSO detects and corrects for horizontal pleiotropy by:
1. Global test: Tests for presence of pleiotropy via residual sum of squares
2. Outlier test: Identifies SNPs with significant residuals
3. Distortion test: Tests if removing outliers changes the estimate

Reference: Verbanck et al. 2018 Nature Genetics
"""

import numpy as np
import pytest

from pymr.methods import mr_presso, ivw


class TestMRPRESSOGlobalTest:
    """Test MR-PRESSO global test for horizontal pleiotropy."""

    def test_presso_basic_structure(self):
        """MR-PRESSO should return expected output structure."""
        # Arrange: Clean data with no pleiotropy
        np.random.seed(42)
        n = 20
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        # True causal effect = 0.5
        beta_out = 0.5 * beta_exp + np.random.normal(0, 0.01, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        # Act
        result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=1000)

        # Assert: Check all expected keys are present
        assert "global_test_pval" in result
        assert "outlier_indices" in result
        assert "corrected_beta" in result
        assert "corrected_se" in result
        assert "corrected_pval" in result
        assert "distortion_test_pval" in result
        assert "original_beta" in result
        assert "original_se" in result
        assert "nsnp" in result

    def test_presso_detects_no_pleiotropy(self):
        """MR-PRESSO should not detect pleiotropy in clean data."""
        # Arrange: Clean data with true causal effect
        np.random.seed(42)
        n = 30
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        # True causal effect = 0.5, small noise
        beta_out = 0.5 * beta_exp + np.random.normal(0, 0.005, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        # Act
        result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=1000)

        # Assert: Global test should not be significant (p > 0.05)
        assert result["global_test_pval"] > 0.05
        # Should find no outliers
        assert len(result["outlier_indices"]) == 0
        # No distortion since no outliers removed
        assert np.isnan(result["distortion_test_pval"])

    def test_presso_detects_horizontal_pleiotropy(self):
        """MR-PRESSO should detect outliers with horizontal pleiotropy."""
        # Arrange: Add horizontal pleiotropy to some SNPs
        np.random.seed(42)
        n = 30
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        beta_out = 0.5 * beta_exp + np.random.normal(0, 0.005, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        # Add strong horizontal pleiotropy to 3 SNPs
        pleiotropic_indices = [5, 10, 15]
        beta_out[pleiotropic_indices] += np.array([0.15, -0.12, 0.18])

        # Act
        result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=1000)

        # Assert: Should detect pleiotropy
        assert result["global_test_pval"] < 0.05
        # Should detect some outliers (may not catch all 3)
        assert len(result["outlier_indices"]) > 0
        # At least one pleiotropic SNP should be detected
        assert any(idx in result["outlier_indices"] for idx in pleiotropic_indices)


class TestMRPRESSOOutlierTest:
    """Test MR-PRESSO outlier detection."""

    def test_presso_outlier_indices_are_valid(self):
        """Outlier indices should be within valid range."""
        np.random.seed(42)
        n = 20
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        beta_out = 0.5 * beta_exp + np.random.normal(0, 0.01, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        # Add outlier
        beta_out[7] += 0.2

        result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=1000)

        # All indices should be valid
        for idx in result["outlier_indices"]:
            assert 0 <= idx < n

    def test_presso_without_outlier_test(self):
        """MR-PRESSO should skip outlier detection when disabled."""
        np.random.seed(42)
        n = 20
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        beta_out = 0.5 * beta_exp + np.random.normal(0, 0.01, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        # Add outlier
        beta_out[5] += 0.3

        result = mr_presso(
            beta_exp, se_exp, beta_out, se_out,
            n_simulations=1000, outlier_test=False
        )

        # Should still have global test
        assert "global_test_pval" in result
        # Should have empty outlier list
        assert len(result["outlier_indices"]) == 0


class TestMRPRESSODistortionTest:
    """Test MR-PRESSO distortion test."""

    def test_presso_distortion_when_outliers_removed(self):
        """Distortion test should detect when outlier removal changes estimate."""
        # Arrange: Data with outliers that bias the estimate
        np.random.seed(42)
        n = 30
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        # True effect = 0.3
        beta_out = 0.3 * beta_exp + np.random.normal(0, 0.005, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        # Add systematic bias to several SNPs (increases estimate)
        beta_out[[5, 10, 15]] += 0.15

        # Act
        result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=1000)

        # Assert: If outliers detected, distortion test should be performed
        if len(result["outlier_indices"]) > 0:
            assert not np.isnan(result["distortion_test_pval"])
            # Corrected estimate should be closer to true value (0.3)
            assert abs(result["corrected_beta"] - 0.3) < abs(result["original_beta"] - 0.3)

    def test_presso_no_distortion_without_outliers(self):
        """Distortion test should be NaN when no outliers detected."""
        np.random.seed(42)
        n = 20
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        beta_out = 0.5 * beta_exp + np.random.normal(0, 0.005, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=1000)

        # If no outliers, distortion test is not applicable
        if len(result["outlier_indices"]) == 0:
            assert np.isnan(result["distortion_test_pval"])

    def test_presso_without_distortion_test(self):
        """MR-PRESSO should skip distortion test when disabled."""
        np.random.seed(42)
        n = 20
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        beta_out = 0.5 * beta_exp + np.random.normal(0, 0.01, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        # Add outlier
        beta_out[5] += 0.3

        result = mr_presso(
            beta_exp, se_exp, beta_out, se_out,
            n_simulations=1000, distortion_test=False
        )

        # Distortion test should be NaN
        assert np.isnan(result["distortion_test_pval"])


class TestMRPRESSOCorrectedEstimate:
    """Test MR-PRESSO corrected estimates after outlier removal."""

    def test_presso_corrected_estimate_uses_ivw(self):
        """Corrected estimate should use IVW after removing outliers."""
        np.random.seed(42)
        n = 20
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        beta_out = 0.5 * beta_exp + np.random.normal(0, 0.01, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        # Add strong outlier
        beta_out[7] += 0.4

        result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=1000)

        # If outliers detected, verify corrected estimate
        if len(result["outlier_indices"]) > 0:
            # Manually compute IVW excluding outliers
            keep_mask = np.ones(n, dtype=bool)
            keep_mask[result["outlier_indices"]] = False

            manual_ivw = ivw(
                beta_exp[keep_mask],
                se_exp[keep_mask],
                beta_out[keep_mask],
                se_out[keep_mask]
            )

            # Should match
            assert result["corrected_beta"] == pytest.approx(manual_ivw["beta"], rel=1e-6)
            assert result["corrected_se"] == pytest.approx(manual_ivw["se"], rel=1e-6)

    def test_presso_original_estimate_matches_ivw(self):
        """Original estimate should match full IVW."""
        np.random.seed(42)
        n = 20
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        beta_out = 0.5 * beta_exp + np.random.normal(0, 0.01, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=1000)
        ivw_result = ivw(beta_exp, se_exp, beta_out, se_out)

        # Original estimates should match IVW
        assert result["original_beta"] == pytest.approx(ivw_result["beta"], rel=1e-6)
        assert result["original_se"] == pytest.approx(ivw_result["se"], rel=1e-6)


class TestMRPRESSOEdgeCases:
    """Test MR-PRESSO edge cases and error handling."""

    def test_presso_minimum_snps(self):
        """MR-PRESSO should require minimum number of SNPs."""
        beta_exp = np.array([0.1, 0.2])
        se_exp = np.array([0.01, 0.02])
        beta_out = np.array([0.05, 0.10])
        se_out = np.array([0.02, 0.03])

        # Should raise error or handle gracefully with < 3 SNPs
        with pytest.raises(ValueError, match="at least 3"):
            mr_presso(beta_exp, se_exp, beta_out, se_out)

    def test_presso_simulation_count(self):
        """MR-PRESSO should accept custom simulation counts."""
        np.random.seed(42)
        n = 20
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        beta_out = 0.5 * beta_exp + np.random.normal(0, 0.01, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        # Should run with fewer simulations (faster)
        result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=100)

        assert "global_test_pval" in result
        assert 0 <= result["global_test_pval"] <= 1

    def test_presso_reproducibility(self):
        """MR-PRESSO should give consistent results with same random seed."""
        n = 20
        beta_exp = np.random.normal(0.1, 0.02, n)
        se_exp = np.abs(np.random.normal(0.01, 0.002, n))
        beta_out = 0.5 * beta_exp + np.random.normal(0, 0.01, n)
        se_out = np.abs(np.random.normal(0.02, 0.005, n))

        # Run twice with controlled randomness
        np.random.seed(123)
        result1 = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=100)

        np.random.seed(123)
        result2 = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=100)

        # Should be identical
        assert result1["global_test_pval"] == result2["global_test_pval"]
        assert result1["outlier_indices"] == result2["outlier_indices"]
