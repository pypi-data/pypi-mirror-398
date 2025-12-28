"""Tests for LD-based clumping functionality."""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from pymr.clumping import (
    ld_clump,
    get_ld_matrix,
    _parse_ldlink_response,
    _select_index_snps,
)


@pytest.fixture
def sample_snps_with_positions():
    """Create sample SNP data with positions for clumping."""
    return pd.DataFrame({
        "SNP": ["rs1", "rs2", "rs3", "rs4", "rs5"],
        "chr": [1, 1, 1, 2, 2],
        "pos": [1000000, 1005000, 1020000, 2000000, 2008000],
        "pval": [1e-8, 5e-7, 1e-6, 2e-8, 3e-7],
        "beta": [0.1, 0.08, 0.05, 0.12, 0.09],
    })


@pytest.fixture
def sample_ld_matrix():
    """Create sample LD matrix (r² values)."""
    # 5x5 symmetric LD matrix
    ld = np.array([
        [1.0, 0.8, 0.1, 0.0, 0.0],  # rs1 highly correlated with rs2
        [0.8, 1.0, 0.05, 0.0, 0.0], # rs2 highly correlated with rs1
        [0.1, 0.05, 1.0, 0.0, 0.0], # rs3 independent
        [0.0, 0.0, 0.0, 1.0, 0.3],  # rs4 weakly correlated with rs5
        [0.0, 0.0, 0.0, 0.3, 1.0],  # rs5 weakly correlated with rs4
    ])
    return pd.DataFrame(
        ld,
        index=["rs1", "rs2", "rs3", "rs4", "rs5"],
        columns=["rs1", "rs2", "rs3", "rs4", "rs5"],
    )


@pytest.fixture
def mock_ldlink_response():
    """Mock LDlink API response for LD matrix."""
    # Tab-separated response format from LDlink
    return """RS_number\trs1\trs2\trs3\trs4\trs5
rs1\t1.0\t0.8\t0.1\t0.0\t0.0
rs2\t0.8\t1.0\t0.05\t0.0\t0.0
rs3\t0.1\t0.05\t1.0\t0.0\t0.0
rs4\t0.0\t0.0\t0.0\t1.0\t0.3
rs5\t0.0\t0.0\t0.0\t0.3\t1.0"""


class TestLDMatrixCalculation:
    """Tests for LD matrix calculation."""

    def test_parse_ldlink_response(self, mock_ldlink_response):
        """Test parsing of LDlink API response."""
        ld_matrix = _parse_ldlink_response(mock_ldlink_response)

        assert isinstance(ld_matrix, pd.DataFrame)
        assert ld_matrix.shape == (5, 5)
        assert list(ld_matrix.index) == ["rs1", "rs2", "rs3", "rs4", "rs5"]
        assert list(ld_matrix.columns) == ["rs1", "rs2", "rs3", "rs4", "rs5"]

        # Check symmetry
        assert ld_matrix.loc["rs1", "rs2"] == ld_matrix.loc["rs2", "rs1"]

        # Check diagonal is 1.0
        assert all(ld_matrix.values.diagonal() == 1.0)

        # Check specific values
        assert ld_matrix.loc["rs1", "rs2"] == 0.8
        assert ld_matrix.loc["rs4", "rs5"] == 0.3

    @patch("pymr.clumping.requests.get")
    def test_get_ld_matrix_api_call(self, mock_get, sample_snps_with_positions):
        """Test LD matrix retrieval via LDlink API."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """RS_number\trs1\trs2\trs3
rs1\t1.0\t0.8\t0.1
rs2\t0.8\t1.0\t0.05
rs3\t0.1\t0.05\t1.0"""
        mock_get.return_value = mock_response

        snps = ["rs1", "rs2", "rs3"]
        ld_matrix = get_ld_matrix(snps, population="EUR", token="fake_token")

        # Verify API was called
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "ldmatrix" in call_args[0][0].lower()

        # Verify result
        assert isinstance(ld_matrix, pd.DataFrame)
        assert ld_matrix.shape == (3, 3)

    @patch("pymr.clumping.requests.get")
    def test_get_ld_matrix_handles_errors(self, mock_get):
        """Test error handling in LD matrix retrieval."""
        # Mock failed API response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        with pytest.raises(RuntimeError, match="LDlink API request failed"):
            get_ld_matrix(["rs1", "rs2"], token="fake_token")

    def test_get_ld_matrix_validates_input(self):
        """Test input validation for LD matrix calculation."""
        # Empty SNP list
        with pytest.raises(ValueError, match="at least one SNP"):
            get_ld_matrix([])

        # Invalid population
        with pytest.raises(ValueError, match="Invalid population"):
            get_ld_matrix(["rs1"], population="INVALID")


class TestSelectIndexSNPs:
    """Tests for index SNP selection algorithm."""

    def test_select_index_snps_basic(self, sample_snps_with_positions, sample_ld_matrix):
        """Test basic index SNP selection."""
        index_snps = _select_index_snps(
            sample_snps_with_positions,
            sample_ld_matrix,
            r2_threshold=0.1,
        )

        # Should select rs4 (lowest p-value) and rs1 (lowest p-value in chr1)
        # rs2 should be removed (LD r² > 0.1 with rs1)
        assert "rs4" in index_snps  # Lowest p-value overall
        assert "rs1" in index_snps  # Lowest p-value on chr1
        assert "rs2" not in index_snps  # High LD with rs1

        # Check that selected SNPs are independent
        selected_ld = sample_ld_matrix.loc[index_snps, index_snps]
        # Off-diagonal elements should be below threshold
        off_diag = selected_ld.values[~np.eye(len(index_snps), dtype=bool)]
        assert all(off_diag <= 0.1)

    def test_select_index_snps_strict_threshold(self, sample_snps_with_positions, sample_ld_matrix):
        """Test index SNP selection with strict r² threshold."""
        # With r² = 0.01, rs4 and rs5 should both be kept (r² = 0.3 > 0.01)
        index_snps = _select_index_snps(
            sample_snps_with_positions,
            sample_ld_matrix,
            r2_threshold=0.01,
        )

        # rs1, rs2 highly correlated - only one should be kept
        assert not (("rs1" in index_snps) and ("rs2" in index_snps))

        # More stringent threshold = fewer SNPs
        assert len(index_snps) <= 4

    def test_select_index_snps_all_independent(self):
        """Test when all SNPs are independent."""
        snps = pd.DataFrame({
            "SNP": ["rs1", "rs2", "rs3"],
            "chr": [1, 1, 2],
            "pos": [1000, 2000, 3000],
            "pval": [1e-8, 1e-7, 1e-6],
        })

        # Identity matrix = all SNPs independent
        ld = pd.DataFrame(
            np.eye(3),
            index=["rs1", "rs2", "rs3"],
            columns=["rs1", "rs2", "rs3"],
        )

        index_snps = _select_index_snps(snps, ld, r2_threshold=0.1)

        # All should be kept
        assert len(index_snps) == 3


class TestLDClump:
    """Tests for main ld_clump function."""

    @patch("pymr.clumping.get_ld_matrix")
    def test_ld_clump_basic(self, mock_get_ld, sample_snps_with_positions, sample_ld_matrix):
        """Test basic LD-based clumping."""
        # Mock the LD matrix API call
        # Return appropriate subset based on which SNPs are requested
        def get_ld_subset(snp_list, **kwargs):
            return sample_ld_matrix.loc[snp_list, snp_list]

        mock_get_ld.side_effect = get_ld_subset

        clumped = ld_clump(
            sample_snps_with_positions,
            r2_threshold=0.1,
            kb_window=10000,
            population="EUR",
            token="fake_token",
        )

        # Verify LD matrix was requested (once per chromosome)
        assert mock_get_ld.call_count >= 1

        # Verify result
        assert isinstance(clumped, pd.DataFrame)
        assert len(clumped) < len(sample_snps_with_positions)

        # All original columns should be preserved
        for col in sample_snps_with_positions.columns:
            assert col in clumped.columns

    @patch("pymr.clumping.get_ld_matrix")
    def test_ld_clump_with_r2_threshold(self, mock_get_ld, sample_snps_with_positions, sample_ld_matrix):
        """Test that r² threshold is respected."""
        def get_ld_subset(snp_list, **kwargs):
            return sample_ld_matrix.loc[snp_list, snp_list]

        mock_get_ld.side_effect = get_ld_subset

        # Lenient threshold - more SNPs retained
        clumped_lenient = ld_clump(
            sample_snps_with_positions,
            r2_threshold=0.5,
            token="fake_token",
        )

        # Strict threshold - fewer SNPs retained
        clumped_strict = ld_clump(
            sample_snps_with_positions,
            r2_threshold=0.01,
            token="fake_token",
        )

        assert len(clumped_lenient) >= len(clumped_strict)

    @patch("pymr.clumping.get_ld_matrix")
    def test_ld_clump_with_kb_window(self, mock_get_ld, sample_ld_matrix):
        """Test that kb window is respected."""
        # Create SNPs far apart
        snps_far = pd.DataFrame({
            "SNP": ["rs1", "rs2", "rs3"],
            "chr": [1, 1, 1],
            "pos": [1000000, 2000000, 3000000],  # 1Mb apart
            "pval": [1e-8, 1e-7, 1e-6],
        })

        # Even though they're in high LD, kb_window should prevent clumping
        ld_high = pd.DataFrame(
            [[1.0, 0.9, 0.9], [0.9, 1.0, 0.9], [0.9, 0.9, 1.0]],
            index=["rs1", "rs2", "rs3"],
            columns=["rs1", "rs2", "rs3"],
        )
        mock_get_ld.return_value = ld_high

        # 10kb window - SNPs are 1000kb apart, should not clump
        clumped = ld_clump(
            snps_far,
            r2_threshold=0.1,
            kb_window=10,  # 10kb window
            token="fake_token",
        )

        # All SNPs should be kept (outside window)
        assert len(clumped) == 3

    def test_ld_clump_requires_position_columns(self, sample_snps_with_positions):
        """Test that chr and pos columns are required."""
        # Remove position columns
        snps_no_pos = sample_snps_with_positions.drop(columns=["chr", "pos"])

        with pytest.raises(ValueError, match="chr.*pos"):
            ld_clump(snps_no_pos, token="fake_token")

    def test_ld_clump_requires_pval_column(self, sample_snps_with_positions):
        """Test that pval column is required."""
        snps_no_pval = sample_snps_with_positions.drop(columns=["pval"])

        with pytest.raises(ValueError, match="pval"):
            ld_clump(snps_no_pval, token="fake_token")

    @patch("pymr.clumping.get_ld_matrix")
    def test_ld_clump_handles_single_snp(self, mock_get_ld):
        """Test clumping with single SNP."""
        single_snp = pd.DataFrame({
            "SNP": ["rs1"],
            "chr": [1],
            "pos": [1000000],
            "pval": [1e-8],
        })

        mock_get_ld.return_value = pd.DataFrame(
            [[1.0]], index=["rs1"], columns=["rs1"]
        )

        clumped = ld_clump(single_snp, token="fake_token")

        assert len(clumped) == 1
        assert clumped.iloc[0]["SNP"] == "rs1"

    @patch("pymr.clumping.get_ld_matrix")
    def test_ld_clump_different_populations(self, mock_get_ld, sample_snps_with_positions, sample_ld_matrix):
        """Test clumping with different ancestry populations."""
        def get_ld_subset(snp_list, **kwargs):
            return sample_ld_matrix.loc[snp_list, snp_list]

        mock_get_ld.side_effect = get_ld_subset

        for pop in ["EUR", "EAS", "AFR", "AMR", "SAS"]:
            mock_get_ld.reset_mock()
            clumped = ld_clump(
                sample_snps_with_positions,
                population=pop,
                token="fake_token",
            )

            assert isinstance(clumped, pd.DataFrame)
            # Verify population was passed to get_ld_matrix
            assert any(
                call_args[1].get("population") == pop
                for call_args in mock_get_ld.call_args_list
            )

    @patch("pymr.clumping.get_ld_matrix")
    def test_ld_clump_preserves_snp_order_by_pvalue(self, mock_get_ld, sample_ld_matrix):
        """Test that clumped SNPs are ordered by p-value."""
        snps = pd.DataFrame({
            "SNP": ["rs1", "rs2", "rs3"],
            "chr": [1, 1, 1],
            "pos": [1000, 2000, 3000],
            "pval": [1e-5, 1e-8, 1e-6],  # rs2 has lowest p-value
        })

        mock_get_ld.return_value = sample_ld_matrix.iloc[:3, :3]

        clumped = ld_clump(snps, token="fake_token")

        # First SNP should have lowest p-value
        assert clumped.iloc[0]["SNP"] == "rs2"

        # P-values should be in ascending order
        assert all(clumped["pval"].iloc[i] <= clumped["pval"].iloc[i+1]
                   for i in range(len(clumped)-1))


class TestIntegration:
    """Integration tests with realistic scenarios."""

    @patch("pymr.clumping.get_ld_matrix")
    def test_realistic_clumping_scenario(self, mock_get_ld):
        """Test realistic clumping with multiple chromosomes and LD blocks."""
        # Create realistic GWAS data
        np.random.seed(42)
        n_snps = 20

        snps = pd.DataFrame({
            "SNP": [f"rs{i}" for i in range(n_snps)],
            "chr": [1] * 10 + [2] * 10,
            "pos": list(range(1000000, 1000000 + 10*5000, 5000)) +  # Chr1: 5kb apart
                   list(range(2000000, 2000000 + 10*5000, 5000)),   # Chr2: 5kb apart
            "pval": np.random.exponential(1e-6, n_snps),
            "beta": np.random.normal(0.1, 0.05, n_snps),
        })

        # Create block LD structure
        # Chr1 SNPs 0-4 in LD, 5-9 in LD
        # Chr2 SNPs 10-14 in LD, 15-19 in LD
        ld = np.eye(n_snps)
        for i in range(5):
            for j in range(5):
                ld[i, j] = 0.8 if i != j else 1.0
                ld[i+5, j+5] = 0.8 if i != j else 1.0
                ld[i+10, j+10] = 0.8 if i != j else 1.0
                ld[i+15, j+15] = 0.8 if i != j else 1.0

        mock_get_ld.return_value = pd.DataFrame(
            ld,
            index=snps["SNP"],
            columns=snps["SNP"],
        )

        clumped = ld_clump(snps, r2_threshold=0.1, kb_window=10, token="fake_token")

        # Should keep ~4 SNPs (one from each LD block)
        assert len(clumped) <= 8
        assert len(clumped) >= 2

        # Verify SNPs from different blocks are kept
        chr1_count = sum(clumped["chr"] == 1)
        chr2_count = sum(clumped["chr"] == 2)
        assert chr1_count >= 1
        assert chr2_count >= 1
