"""Tests for IEU OpenGWAS API integration (TDD - tests written first)."""

import os
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from pymr.api import (
    IEUClient,
    get_instruments,
    get_outcome,
    list_gwas,
    search_gwas,
)


class TestIEUClient:
    """Test the IEUClient class for API access."""

    def test_client_initialization_default(self):
        """Client should initialize with default base URL."""
        client = IEUClient()
        assert client.base_url == "https://gwas-api.mrcieu.ac.uk"
        assert client.jwt is None

    def test_client_initialization_with_jwt(self):
        """Client should accept JWT token."""
        token = "test_jwt_token_123"
        client = IEUClient(jwt=token)
        assert client.jwt == token

    def test_client_initialization_from_env(self):
        """Client should read JWT from environment variable."""
        with patch.dict(os.environ, {"OPENGWAS_JWT": "env_token"}):
            client = IEUClient()
            assert client.jwt == "env_token"

    def test_client_get_headers_without_jwt(self):
        """Client should return basic headers without JWT."""
        client = IEUClient()
        headers = client._get_headers()
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers

    def test_client_get_headers_with_jwt(self):
        """Client should include Authorization header with JWT."""
        client = IEUClient(jwt="test_token")
        headers = client._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"


class TestGetInstruments:
    """Test get_instruments function for fetching clumped instruments."""

    @patch("pymr.api.requests.get")
    def test_get_instruments_basic(self, mock_get):
        """get_instruments should fetch tophits with default p-threshold."""
        # Arrange: Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "rsid": "rs123",
                "chr": "1",
                "position": 100000,
                "ea": "A",
                "nea": "G",
                "beta": 0.1,
                "se": 0.01,
                "pval": 1e-10,
                "eaf": 0.3,
            },
            {
                "rsid": "rs456",
                "chr": "2",
                "position": 200000,
                "ea": "C",
                "nea": "T",
                "beta": 0.15,
                "se": 0.02,
                "pval": 1e-12,
                "eaf": 0.4,
            },
        ]
        mock_get.return_value = mock_response

        # Act
        result = get_instruments("ieu-a-2")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "rsid" in result.columns
        assert "beta" in result.columns
        assert "pval" in result.columns
        assert result.iloc[0]["rsid"] == "rs123"
        # Default p-threshold should be 5e-8
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "pval=5e-08" in call_args[0][0] or "pval" in str(call_args)

    @patch("pymr.api.requests.get")
    def test_get_instruments_custom_threshold(self, mock_get):
        """get_instruments should accept custom p-value threshold."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = get_instruments("ieu-a-2", p_threshold=1e-6)

        assert isinstance(result, pd.DataFrame)
        # Should use custom threshold in API call
        call_args = mock_get.call_args
        assert "1e-06" in str(call_args) or "0.000001" in str(call_args)

    @patch("pymr.api.requests.get")
    def test_get_instruments_with_clumping(self, mock_get):
        """get_instruments should request clumped results by default."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = get_instruments("ieu-a-2", clump=True)

        assert isinstance(result, pd.DataFrame)
        call_args = mock_get.call_args
        # Should include clump parameter
        assert "clump=1" in str(call_args) or "clump" in str(call_args)

    @patch("pymr.api.requests.get")
    def test_get_instruments_api_error(self, mock_get):
        """get_instruments should raise error on API failure."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.return_value = mock_response

        with pytest.raises(Exception):
            get_instruments("invalid-id")


class TestGetOutcome:
    """Test get_outcome function for looking up SNPs in outcome GWAS."""

    @patch("pymr.api.requests.post")
    def test_get_outcome_basic(self, mock_post):
        """get_outcome should lookup SNPs in outcome dataset."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "rsid": "rs123",
                "chr": "1",
                "position": 100000,
                "ea": "A",
                "nea": "G",
                "beta": 0.05,
                "se": 0.02,
                "pval": 0.01,
                "eaf": 0.3,
            },
            {
                "rsid": "rs456",
                "chr": "2",
                "position": 200000,
                "ea": "C",
                "nea": "T",
                "beta": 0.08,
                "se": 0.03,
                "pval": 0.005,
                "eaf": 0.4,
            },
        ]
        mock_post.return_value = mock_response

        # Act
        snps = ["rs123", "rs456"]
        result = get_outcome("ieu-a-7", snps)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "rsid" in result.columns
        assert "beta" in result.columns
        assert result.iloc[0]["rsid"] == "rs123"
        # Should POST with SNP list
        mock_post.assert_called_once()

    @patch("pymr.api.requests.post")
    def test_get_outcome_with_proxies(self, mock_post):
        """get_outcome should support LD proxy lookup."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_post.return_value = mock_response

        result = get_outcome("ieu-a-7", ["rs123"], proxies=True)

        assert isinstance(result, pd.DataFrame)
        # Should include proxies parameter
        call_args = mock_post.call_args
        assert call_args is not None

    @patch("pymr.api.requests.post")
    def test_get_outcome_missing_snps(self, mock_post):
        """get_outcome should handle missing SNPs gracefully."""
        # Return empty results for missing SNPs
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_post.return_value = mock_response

        result = get_outcome("ieu-a-7", ["rs_nonexistent"])

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestSearchGWAS:
    """Test search_gwas function for searching available GWAS."""

    @patch("pymr.api.requests.get")
    def test_search_gwas_basic(self, mock_get):
        """search_gwas should search GWAS by keyword."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "ieu-a-2",
                "trait": "Body mass index",
                "author": "Locke AE",
                "year": 2015,
                "consortium": "GIANT",
                "sample_size": 339224,
            },
            {
                "id": "ieu-a-95",
                "trait": "Childhood body mass index",
                "author": "Felix JF",
                "year": 2016,
                "consortium": "EGG",
                "sample_size": 47541,
            },
        ]
        mock_get.return_value = mock_response

        # Act
        result = search_gwas("body mass index")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "id" in result.columns
        assert "trait" in result.columns
        assert "body mass index" in result.iloc[0]["trait"].lower()

    @patch("pymr.api.requests.get")
    def test_search_gwas_no_results(self, mock_get):
        """search_gwas should return empty DataFrame when no results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = search_gwas("nonexistent trait xyz")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestListGWAS:
    """Test list_gwas function for listing all available GWAS."""

    @patch("pymr.api.requests.get")
    def test_list_gwas_basic(self, mock_get):
        """list_gwas should return all available GWAS IDs."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "ieu-a-2",
                "trait": "Body mass index",
                "sample_size": 339224,
            },
            {
                "id": "ieu-a-7",
                "trait": "Type 2 diabetes",
                "sample_size": 159208,
            },
            {
                "id": "ieu-a-95",
                "trait": "Childhood body mass index",
                "sample_size": 47541,
            },
        ]
        mock_get.return_value = mock_response

        # Act
        result = list_gwas()

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "id" in result.columns
        assert "trait" in result.columns

    @patch("pymr.api.requests.get")
    def test_list_gwas_pagination(self, mock_get):
        """list_gwas should handle paginated results if needed."""
        # This test assumes the API might paginate large results
        mock_response = Mock()
        mock_response.status_code = 200
        # Return a large number of results
        mock_response.json.return_value = [
            {"id": f"ieu-a-{i}", "trait": f"Trait {i}", "sample_size": 10000}
            for i in range(100)
        ]
        mock_get.return_value = mock_response

        result = list_gwas()

        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 100


class TestIntegrationWorkflow:
    """Test end-to-end workflow with mocked API responses."""

    @patch("pymr.api.requests.post")
    @patch("pymr.api.requests.get")
    def test_full_mr_workflow(self, mock_get, mock_post):
        """Test complete workflow: get instruments -> get outcome -> harmonize."""
        # Mock get_instruments response
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = [
            {
                "rsid": "rs1",
                "chr": "1",
                "position": 100000,
                "ea": "A",
                "nea": "G",
                "beta": 0.1,
                "se": 0.01,
                "pval": 1e-10,
                "eaf": 0.3,
            },
            {
                "rsid": "rs2",
                "chr": "2",
                "position": 200000,
                "ea": "C",
                "nea": "T",
                "beta": 0.15,
                "se": 0.02,
                "pval": 1e-12,
                "eaf": 0.4,
            },
        ]
        mock_get.return_value = mock_get_response

        # Mock get_outcome response
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = [
            {
                "rsid": "rs1",
                "chr": "1",
                "position": 100000,
                "ea": "A",
                "nea": "G",
                "beta": 0.05,
                "se": 0.02,
                "pval": 0.01,
                "eaf": 0.3,
            },
            {
                "rsid": "rs2",
                "chr": "2",
                "position": 200000,
                "ea": "C",
                "nea": "T",
                "beta": 0.08,
                "se": 0.03,
                "pval": 0.005,
                "eaf": 0.4,
            },
        ]
        mock_post.return_value = mock_post_response

        # Act: Complete workflow
        # 1. Get instruments for exposure
        instruments = get_instruments("ieu-a-2")  # BMI
        assert len(instruments) == 2

        # 2. Extract SNP list
        snp_list = instruments["rsid"].tolist()
        assert snp_list == ["rs1", "rs2"]

        # 3. Get outcome data
        outcome = get_outcome("ieu-a-7", snp_list)  # T2D
        assert len(outcome) == 2

        # 4. Verify data is ready for harmonization
        assert all(col in instruments.columns for col in ["rsid", "beta", "se"])
        assert all(col in outcome.columns for col in ["rsid", "beta", "se"])


class TestPanUKBFunctions:
    """Test Pan-UKB GWAS data access functions (TDD - tests written first)."""

    @patch("pymr.api.requests.get")
    def test_panukb_list_phenotypes(self, mock_get):
        """panukb_list_phenotypes should return DataFrame of available phenotypes."""
        # Arrange: Mock manifest response
        import gzip
        mock_response = Mock()
        mock_response.status_code = 200
        # Simulate TSV content with phenotype manifest (must be gzipped)
        tsv_content = b"trait_type\tphenocode\tdescription\tn_cases\tn_controls\tsaige_version\n"
        tsv_content += b"continuous\t50\tStanding height\tNA\tNA\t0.44.5\n"
        tsv_content += b"continuous\t21001\tBody mass index (BMI)\tNA\tNA\t0.44.5\n"
        tsv_content += b"biomarkers\t30690\tCholesterol\tNA\tNA\t0.44.5\n"
        mock_response.content = gzip.compress(tsv_content)
        mock_get.return_value = mock_response

        # Act
        from pymr.api import panukb_list_phenotypes
        result = panukb_list_phenotypes()

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "phenocode" in result.columns
        assert "description" in result.columns
        assert "trait_type" in result.columns
        assert "21001" in result["phenocode"].astype(str).values

    @patch("pymr.api.requests.get")
    def test_panukb_search(self, mock_get):
        """panukb_search should search phenotypes by keyword."""
        # Arrange: Mock manifest response
        import gzip
        mock_response = Mock()
        mock_response.status_code = 200
        tsv_content = b"trait_type\tphenocode\tdescription\tn_cases\tn_controls\tsaige_version\n"
        tsv_content += b"continuous\t50\tStanding height\tNA\tNA\t0.44.5\n"
        tsv_content += b"continuous\t21001\tBody mass index (BMI)\tNA\tNA\t0.44.5\n"
        tsv_content += b"biomarkers\t30690\tCholesterol\tNA\tNA\t0.44.5\n"
        mock_response.content = gzip.compress(tsv_content)
        mock_get.return_value = mock_response

        # Act
        from pymr.api import panukb_search
        result = panukb_search("BMI")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1  # Should find at least the BMI phenotype
        assert any("BMI" in str(desc) for desc in result["description"].values)

    @patch("pymr.api.requests.get")
    def test_panukb_search_case_insensitive(self, mock_get):
        """panukb_search should be case-insensitive."""
        # Arrange
        import gzip
        mock_response = Mock()
        mock_response.status_code = 200
        tsv_content = b"trait_type\tphenocode\tdescription\tn_cases\tn_controls\tsaige_version\n"
        tsv_content += b"continuous\t21001\tBody mass index (BMI)\tNA\tNA\t0.44.5\n"
        mock_response.content = gzip.compress(tsv_content)
        mock_get.return_value = mock_response

        # Act
        from pymr.api import panukb_search
        result = panukb_search("bmi")  # lowercase

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1

    @patch("pymr.api.requests.get")
    def test_panukb_load_gwas_basic(self, mock_get):
        """panukb_load_gwas should load GWAS summary statistics for a phenotype."""
        # Arrange: Mock responses for manifest and GWAS file
        import gzip
        mock_responses = []

        # First call: manifest (must be gzipped)
        manifest_response = Mock()
        manifest_response.status_code = 200
        manifest_content = b"trait_type\tphenocode\tdescription\tn_cases\tn_controls\tsaige_version\n"
        manifest_content += b"continuous\t21001\tBody mass index (BMI)\tNA\tNA\t0.44.5\n"
        manifest_response.content = gzip.compress(manifest_content)
        mock_responses.append(manifest_response)

        # Second call: GWAS summary stats (bgzipped TSV)
        gwas_data = b"chr\tpos\tsnp\tref\talt\tbeta\tse\tpval\tlow_confidence_variant\tn_complete_samples\tAF\n"
        gwas_data += b"1\t100000\trs123\tA\tG\t0.05\t0.01\t1.2e-8\tFALSE\t100000\t0.3\n"
        gwas_data += b"2\t200000\trs456\tC\tT\t0.08\t0.02\t3.4e-10\tFALSE\t100000\t0.45\n"
        gwas_response = Mock()
        gwas_response.status_code = 200
        gwas_response.content = gzip.compress(gwas_data)
        mock_responses.append(gwas_response)

        mock_get.side_effect = mock_responses

        # Act
        from pymr.api import panukb_load_gwas
        result = panukb_load_gwas("21001", ancestry="EUR")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "snp" in result.columns or "rsid" in result.columns
        assert "beta" in result.columns
        assert "se" in result.columns
        assert "pval" in result.columns

    @patch("pymr.api.requests.get")
    def test_panukb_load_gwas_default_ancestry(self, mock_get):
        """panukb_load_gwas should default to EUR ancestry."""
        # Arrange
        import gzip
        mock_responses = []

        manifest_response = Mock()
        manifest_response.status_code = 200
        manifest_content = b"trait_type\tphenocode\tdescription\tn_cases\tn_controls\tsaige_version\n"
        manifest_content += b"continuous\t21001\tBody mass index (BMI)\tNA\tNA\t0.44.5\n"
        manifest_response.content = gzip.compress(manifest_content)
        mock_responses.append(manifest_response)

        gwas_data = b"chr\tpos\tsnp\tref\talt\tbeta\tse\tpval\tlow_confidence_variant\tn_complete_samples\tAF\n"
        gwas_data += b"1\t100000\trs123\tA\tG\t0.05\t0.01\t1.2e-8\tFALSE\t100000\t0.3\n"
        gwas_response = Mock()
        gwas_response.status_code = 200
        gwas_response.content = gzip.compress(gwas_data)
        mock_responses.append(gwas_response)

        mock_get.side_effect = mock_responses

        # Act
        from pymr.api import panukb_load_gwas
        result = panukb_load_gwas("21001")  # No ancestry specified

        # Assert
        assert isinstance(result, pd.DataFrame)
        # Should have called with EUR in URL
        assert any("EUR" in str(call) for call in mock_get.call_args_list)

    @patch("pymr.api.requests.get")
    def test_panukb_load_gwas_invalid_phenotype(self, mock_get):
        """panukb_load_gwas should raise error for invalid phenotype code."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.return_value = mock_response

        # Act & Assert
        from pymr.api import panukb_load_gwas
        with pytest.raises(Exception):
            panukb_load_gwas("INVALID_PHENO")


class TestGWASCatalogSearch:
    """Test gwas_catalog_search function for searching by trait."""

    @patch("pymr.api.requests.get")
    def test_gwas_catalog_search_basic(self, mock_get):
        """gwas_catalog_search should search for studies by trait name."""
        # Arrange: Mock paginated API response
        mock_response_page1 = Mock()
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {
            "_embedded": {
                "studies": [
                    {
                        "accessionId": "GCST001234",
                        "diseaseTrait": {
                            "trait": "Body mass index"
                        },
                        "publicationInfo": {
                            "author": {
                                "fullname": "Locke AE"
                            },
                            "publicationDate": "2015-02-01",
                            "pubmedId": "25673413"
                        },
                        "initialSampleSize": "339,224 European ancestry individuals",
                        "replicateSampleSize": "N/A"
                    },
                    {
                        "accessionId": "GCST002783",
                        "diseaseTrait": {
                            "trait": "Childhood body mass index"
                        },
                        "publicationInfo": {
                            "author": {
                                "fullname": "Felix JF"
                            },
                            "publicationDate": "2016-03-15",
                            "pubmedId": "26961502"
                        },
                        "initialSampleSize": "47,541 European ancestry children",
                        "replicateSampleSize": "10,000"
                    }
                ]
            },
            "page": {
                "size": 20,
                "totalElements": 2,
                "totalPages": 1,
                "number": 0
            }
        }
        mock_get.return_value = mock_response_page1

        # Act
        from pymr.api import gwas_catalog_search
        result = gwas_catalog_search("body mass index")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "study_id" in result.columns
        assert "trait" in result.columns
        assert "author" in result.columns
        assert result.iloc[0]["study_id"] == "GCST001234"
        assert "body mass index" in result.iloc[0]["trait"].lower()
        # Should have called API with correct parameters
        mock_get.assert_called()
        call_args = mock_get.call_args[0][0]
        assert "www.ebi.ac.uk/gwas/rest/api" in call_args

    @patch("pymr.api.requests.get")
    def test_gwas_catalog_search_pagination(self, mock_get):
        """gwas_catalog_search should handle paginated results."""
        # Mock two pages of results
        mock_response_page1 = Mock()
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {
            "_embedded": {
                "studies": [
                    {
                        "accessionId": f"GCST{i:06d}",
                        "diseaseTrait": {"trait": f"Trait {i}"},
                        "publicationInfo": {
                            "author": {"fullname": "Author A"},
                            "publicationDate": "2020-01-01",
                            "pubmedId": "12345678"
                        },
                        "initialSampleSize": "10000",
                        "replicateSampleSize": "N/A"
                    }
                    for i in range(20)
                ]
            },
            "page": {"size": 20, "totalElements": 25, "totalPages": 2, "number": 0}
        }

        mock_response_page2 = Mock()
        mock_response_page2.status_code = 200
        mock_response_page2.json.return_value = {
            "_embedded": {
                "studies": [
                    {
                        "accessionId": f"GCST{i:06d}",
                        "diseaseTrait": {"trait": f"Trait {i}"},
                        "publicationInfo": {
                            "author": {"fullname": "Author B"},
                            "publicationDate": "2020-01-01",
                            "pubmedId": "12345678"
                        },
                        "initialSampleSize": "10000",
                        "replicateSampleSize": "N/A"
                    }
                    for i in range(20, 25)
                ]
            },
            "page": {"size": 20, "totalElements": 25, "totalPages": 2, "number": 1}
        }

        mock_get.side_effect = [mock_response_page1, mock_response_page2]

        # Act
        from pymr.api import gwas_catalog_search
        result = gwas_catalog_search("diabetes")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 25
        assert mock_get.call_count == 2


class TestGWASCatalogGetStudy:
    """Test gwas_catalog_get_study function for retrieving study metadata."""

    @patch("pymr.api.requests.get")
    def test_gwas_catalog_get_study_basic(self, mock_get):
        """gwas_catalog_get_study should fetch study metadata."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "accessionId": "GCST001234",
            "diseaseTrait": {
                "trait": "Body mass index"
            },
            "publicationInfo": {
                "author": {
                    "fullname": "Locke AE"
                },
                "publicationDate": "2015-02-01",
                "pubmedId": "25673413",
                "title": "Genetic studies of body mass index yield new insights"
            },
            "initialSampleSize": "339,224 European ancestry individuals",
            "replicateSampleSize": "N/A",
            "ancestryInitial": [
                {"type": "European", "numberOfIndividuals": 339224}
            ]
        }
        mock_get.return_value = mock_response

        # Act
        from pymr.api import gwas_catalog_get_study
        result = gwas_catalog_get_study("GCST001234")

        # Assert
        assert isinstance(result, dict)
        assert result["study_id"] == "GCST001234"
        assert result["trait"] == "Body mass index"
        assert result["author"] == "Locke AE"
        assert "25673413" in str(result["pubmed_id"])


class TestGWASCatalogGetAssociations:
    """Test gwas_catalog_get_associations function for retrieving associations."""

    @patch("pymr.api.requests.get")
    def test_gwas_catalog_get_associations_basic(self, mock_get):
        """gwas_catalog_get_associations should fetch SNP associations for a study."""
        # Arrange: Mock paginated response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "_embedded": {
                "associations": [
                    {
                        "rsId": "rs9939609",
                        "orPerCopyNum": None,
                        "betaNum": 0.39,
                        "standardError": 0.013,
                        "pvalueExponent": -271,
                        "pvalueMantissa": 1.2,
                        "riskFrequency": "0.42",
                        "loci": [
                            {
                                "strongestRiskAlleles": [
                                    {
                                        "riskAlleleName": "rs9939609-A"
                                    }
                                ]
                            }
                        ],
                        "snps": [
                            {
                                "locations": [
                                    {
                                        "chromosomeName": "16",
                                        "chromosomePosition": 53820527
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "rsId": "rs571312",
                        "orPerCopyNum": None,
                        "betaNum": 0.06,
                        "standardError": 0.009,
                        "pvalueExponent": -12,
                        "pvalueMantissa": 2.4,
                        "riskFrequency": "0.78",
                        "loci": [
                            {
                                "strongestRiskAlleles": [
                                    {
                                        "riskAlleleName": "rs571312-C"
                                    }
                                ]
                            }
                        ],
                        "snps": [
                            {
                                "locations": [
                                    {
                                        "chromosomeName": "18",
                                        "chromosomePosition": 57851097
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            "page": {
                "size": 20,
                "totalElements": 2,
                "totalPages": 1,
                "number": 0
            }
        }
        mock_get.return_value = mock_response

        # Act
        from pymr.api import gwas_catalog_get_associations
        result = gwas_catalog_get_associations("GCST001234")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "rsid" in result.columns
        assert "beta" in result.columns
        assert "se" in result.columns
        assert "pval" in result.columns
        assert "chr" in result.columns
        assert "position" in result.columns
        assert "ea" in result.columns
        assert "eaf" in result.columns
        assert result.iloc[0]["rsid"] == "rs9939609"
        assert result.iloc[0]["beta"] == 0.39
        assert result.iloc[0]["se"] == 0.013
        assert result.iloc[0]["chr"] == "16"

    @patch("pymr.api.requests.get")
    def test_gwas_catalog_get_associations_pagination(self, mock_get):
        """gwas_catalog_get_associations should handle multiple pages."""
        # Mock two pages
        mock_page1 = Mock()
        mock_page1.status_code = 200
        mock_page1.json.return_value = {
            "_embedded": {
                "associations": [
                    {
                        "rsId": f"rs{i}",
                        "betaNum": 0.1,
                        "standardError": 0.01,
                        "pvalueExponent": -10,
                        "pvalueMantissa": 1.0,
                        "riskFrequency": "0.5",
                        "loci": [{"strongestRiskAlleles": [{"riskAlleleName": f"rs{i}-A"}]}],
                        "snps": [{"locations": [{"chromosomeName": "1", "chromosomePosition": i * 1000}]}]
                    }
                    for i in range(20)
                ]
            },
            "page": {"size": 20, "totalElements": 25, "totalPages": 2, "number": 0}
        }

        mock_page2 = Mock()
        mock_page2.status_code = 200
        mock_page2.json.return_value = {
            "_embedded": {
                "associations": [
                    {
                        "rsId": f"rs{i}",
                        "betaNum": 0.1,
                        "standardError": 0.01,
                        "pvalueExponent": -10,
                        "pvalueMantissa": 1.0,
                        "riskFrequency": "0.5",
                        "loci": [{"strongestRiskAlleles": [{"riskAlleleName": f"rs{i}-A"}]}],
                        "snps": [{"locations": [{"chromosomeName": "1", "chromosomePosition": i * 1000}]}]
                    }
                    for i in range(20, 25)
                ]
            },
            "page": {"size": 20, "totalElements": 25, "totalPages": 2, "number": 1}
        }

        mock_get.side_effect = [mock_page1, mock_page2]

        # Act
        from pymr.api import gwas_catalog_get_associations
        result = gwas_catalog_get_associations("GCST001234")

        # Assert
        assert len(result) == 25
        assert mock_get.call_count == 2


class TestFinnGenFunctions:
    """Test FinnGen R12 GWAS data access functions (TDD - tests written first)."""

    @patch("pymr.api.requests.get")
    def test_finngen_list_phenotypes(self, mock_get):
        """finngen_list_phenotypes should return DataFrame of available phenotypes."""
        # Arrange: Mock FinnGen manifest response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "phenocode": "T2D",
                "phenostring": "Type 2 diabetes",
                "category": "Endocrine",
                "num_cases": 18217,
                "num_controls": 338468,
                "num_gw_significant": 125,
            },
            {
                "phenocode": "I9_CHD",
                "phenostring": "Coronary heart disease",
                "category": "Circulatory system",
                "num_cases": 29123,
                "num_controls": 327562,
                "num_gw_significant": 89,
            },
            {
                "phenocode": "C3_BREAST",
                "phenostring": "Breast cancer",
                "category": "Neoplasms",
                "num_cases": 8246,
                "num_controls": 348439,
                "num_gw_significant": 34,
            },
        ]
        mock_get.return_value = mock_response

        # Act
        from pymr.api import finngen_list_phenotypes
        result = finngen_list_phenotypes()

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "phenocode" in result.columns
        assert "phenostring" in result.columns
        assert "category" in result.columns
        assert "num_cases" in result.columns
        assert "num_controls" in result.columns
        assert "T2D" in result["phenocode"].values
        # Should have called FinnGen API
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0][0]
        assert "r12.finngen.fi" in call_args or "finngen.fi" in call_args

    @patch("pymr.api.requests.get")
    def test_finngen_search(self, mock_get):
        """finngen_search should search phenotypes by keyword."""
        # Arrange: Mock manifest response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "phenocode": "T2D",
                "phenostring": "Type 2 diabetes",
                "category": "Endocrine",
                "num_cases": 18217,
                "num_controls": 338468,
                "num_gw_significant": 125,
            },
            {
                "phenocode": "T1D",
                "phenostring": "Type 1 diabetes",
                "category": "Endocrine",
                "num_cases": 5253,
                "num_controls": 351432,
                "num_gw_significant": 67,
            },
            {
                "phenocode": "I9_CHD",
                "phenostring": "Coronary heart disease",
                "category": "Circulatory system",
                "num_cases": 29123,
                "num_controls": 327562,
                "num_gw_significant": 89,
            },
        ]
        mock_get.return_value = mock_response

        # Act
        from pymr.api import finngen_search
        result = finngen_search("diabetes")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 2  # Should find T1D and T2D
        assert any("diabetes" in str(s).lower() for s in result["phenostring"].values)
        # Should NOT find coronary heart disease
        assert all("coronary" not in str(s).lower() for s in result["phenostring"].values)

    @patch("pymr.api.requests.get")
    def test_finngen_search_case_insensitive(self, mock_get):
        """finngen_search should be case-insensitive."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "phenocode": "T2D",
                "phenostring": "Type 2 diabetes",
                "category": "Endocrine",
                "num_cases": 18217,
                "num_controls": 338468,
                "num_gw_significant": 125,
            },
        ]
        mock_get.return_value = mock_response

        # Act
        from pymr.api import finngen_search
        result = finngen_search("DIABETES")  # Uppercase

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1

    @patch("pymr.api.requests.get")
    def test_finngen_load_gwas_basic(self, mock_get):
        """finngen_load_gwas should load GWAS summary statistics for a phenotype."""
        # Arrange: Mock responses for manifest and GWAS file
        mock_responses = []

        # First call: manifest
        manifest_response = Mock()
        manifest_response.status_code = 200
        manifest_response.json.return_value = [
            {
                "phenocode": "T2D",
                "phenostring": "Type 2 diabetes",
                "category": "Endocrine",
                "num_cases": 18217,
                "num_controls": 338468,
                "num_gw_significant": 125,
            },
        ]
        mock_responses.append(manifest_response)

        # Second call: GWAS summary stats (JSON format)
        gwas_response = Mock()
        gwas_response.status_code = 200
        gwas_response.json.return_value = {
            "data": [
                {
                    "variant": "1:100000:A:G",
                    "rsid": "rs123",
                    "chromosome": "1",
                    "position": 100000,
                    "ref": "A",
                    "alt": "G",
                    "beta": 0.05,
                    "sebeta": 0.01,
                    "pval": 1.2e-8,
                    "maf": 0.3,
                    "maf_cases": 0.35,
                    "maf_controls": 0.29,
                },
                {
                    "variant": "2:200000:C:T",
                    "rsid": "rs456",
                    "chromosome": "2",
                    "position": 200000,
                    "ref": "C",
                    "alt": "T",
                    "beta": 0.08,
                    "sebeta": 0.02,
                    "pval": 3.4e-10,
                    "maf": 0.45,
                    "maf_cases": 0.48,
                    "maf_controls": 0.44,
                },
            ]
        }
        mock_responses.append(gwas_response)

        mock_get.side_effect = mock_responses

        # Act
        from pymr.api import finngen_load_gwas
        result = finngen_load_gwas("T2D")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "rsid" in result.columns
        assert "beta" in result.columns
        assert "se" in result.columns
        assert "pval" in result.columns
        assert "chr" in result.columns
        assert "pos" in result.columns  # FinnGen uses 'pos' after renaming
        assert result.iloc[0]["rsid"] == "rs123"
        assert result.iloc[0]["beta"] == 0.05
        assert result.iloc[0]["se"] == 0.01

    @patch("pymr.api.requests.get")
    def test_finngen_load_gwas_invalid_phenotype(self, mock_get):
        """finngen_load_gwas should raise error for invalid phenotype code."""
        # Arrange: Mock manifest with no matching phenotype
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "phenocode": "T2D",
                "phenostring": "Type 2 diabetes",
                "category": "Endocrine",
                "num_cases": 18217,
                "num_controls": 338468,
                "num_gw_significant": 125,
            },
        ]
        mock_get.return_value = mock_response

        # Act & Assert
        from pymr.api import finngen_load_gwas
        with pytest.raises(ValueError, match="Phenotype code .* not found"):
            finngen_load_gwas("INVALID_PHENO")
