"""IEU OpenGWAS API integration for PyMR.

This module provides access to the IEU OpenGWAS database API for:
- Fetching genetic instruments (top hits with clumping)
- Looking up SNPs in outcome GWAS datasets
- Searching and listing available GWAS studies

It also provides access to Pan-UKB GWAS data:
- Listing available phenotypes
- Searching for phenotypes by keyword
- Loading GWAS summary statistics for specific phenotypes

NHGRI-EBI GWAS Catalog integration:
- Searching published GWAS studies by trait
- Retrieving study metadata
- Fetching SNP associations with automatic pagination

FinnGen R12 integration:
- Listing available Finnish population phenotypes
- Searching for phenotypes by keyword
- Loading GWAS summary statistics for Finnish disease endpoints

References:
    IEU OpenGWAS API: https://gwas-api.mrcieu.ac.uk/
    ieugwasr R package: https://mrcieu.github.io/ieugwasr/
    Pan-UKB: https://pan.ukbb.broadinstitute.org/
    GWAS Catalog API: https://www.ebi.ac.uk/gwas/rest/docs/api
    FinnGen R12: https://r12.finngen.fi/
"""

import gzip
import os
from io import BytesIO
from typing import Any, Optional

import pandas as pd
import requests


class IEUClient:
    """Client for accessing the IEU OpenGWAS API.

    Args:
        base_url: Base URL for the API (default: https://gwas-api.mrcieu.ac.uk)
        jwt: JSON Web Token for authentication. If not provided, reads from
            OPENGWAS_JWT environment variable.

    Example:
        >>> client = IEUClient(jwt="your_token_here")
        >>> instruments = client.get_tophits("ieu-a-2")
    """

    def __init__(
        self,
        base_url: str = "https://gwas-api.mrcieu.ac.uk",
        jwt: Optional[str] = None,
    ) -> None:
        """Initialize the IEU OpenGWAS API client."""
        self.base_url = base_url
        self.jwt = jwt or os.environ.get("OPENGWAS_JWT")

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests.

        Returns:
            Dictionary of headers including authentication if JWT is available.
        """
        headers = {"Content-Type": "application/json"}
        if self.jwt:
            headers["Authorization"] = f"Bearer {self.jwt}"
        return headers

    def get_tophits(
        self,
        gwas_id: str,
        pval: float = 5e-8,
        clump: bool = True,
        r2: float = 0.001,
        kb: int = 10000,
    ) -> list[dict[str, Any]]:
        """Fetch top hits (genetic instruments) from a GWAS dataset.

        Args:
            gwas_id: GWAS dataset identifier (e.g., "ieu-a-2")
            pval: P-value threshold for significance (default: 5e-8)
            clump: Whether to perform LD clumping (default: True)
            r2: LD clumping r² threshold (default: 0.001)
            kb: LD clumping distance in kb (default: 10000)

        Returns:
            List of dictionaries containing variant information.
        """
        url = f"{self.base_url}/tophits/{gwas_id}"
        params = {
            "pval": pval,
            "clump": 1 if clump else 0,
            "r2": r2,
            "kb": kb,
        }
        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def get_associations(
        self,
        gwas_id: str,
        variants: list[str],
        proxies: bool = False,
    ) -> list[dict[str, Any]]:
        """Look up specific variants in a GWAS dataset.

        Args:
            gwas_id: GWAS dataset identifier (e.g., "ieu-a-7")
            variants: List of variant identifiers (rsIDs)
            proxies: Whether to use LD proxies for missing variants (default: False)

        Returns:
            List of dictionaries containing association statistics.
        """
        url = f"{self.base_url}/associations/{gwas_id}"
        data = {
            "variant": variants,
            "proxies": 1 if proxies else 0,
        }
        response = requests.post(url, json=data, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def get_gwasinfo(self, query: Optional[str] = None) -> list[dict[str, Any]]:
        """Get information about available GWAS datasets.

        Args:
            query: Optional search query to filter datasets

        Returns:
            List of dictionaries containing GWAS metadata.
        """
        url = f"{self.base_url}/gwasinfo"
        params = {}
        if query:
            params["trait"] = query
        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json()


def get_instruments(
    exposure_id: str,
    p_threshold: float = 5e-8,
    clump: bool = True,
    r2: float = 0.001,
    kb: int = 10000,
    jwt: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch genetic instruments (clumped top hits) for an exposure.

    This is a convenience function that wraps IEUClient.get_tophits().

    Args:
        exposure_id: GWAS dataset identifier for exposure (e.g., "ieu-a-2")
        p_threshold: P-value threshold for significance (default: 5e-8)
        clump: Whether to perform LD clumping (default: True)
        r2: LD clumping r² threshold (default: 0.001)
        kb: LD clumping distance in kb (default: 10000)
        jwt: Optional JWT token for authentication

    Returns:
        DataFrame with columns: rsid, chr, position, ea, nea, beta, se, pval, eaf

    Example:
        >>> instruments = get_instruments("ieu-a-2")  # BMI GWAS
        >>> print(instruments.head())
    """
    client = IEUClient(jwt=jwt)
    results = client.get_tophits(
        gwas_id=exposure_id,
        pval=p_threshold,
        clump=clump,
        r2=r2,
        kb=kb,
    )
    return pd.DataFrame(results)


def get_outcome(
    outcome_id: str,
    snps: list[str],
    proxies: bool = False,
    jwt: Optional[str] = None,
) -> pd.DataFrame:
    """Look up SNPs in an outcome GWAS dataset.

    This is a convenience function that wraps IEUClient.get_associations().

    Args:
        outcome_id: GWAS dataset identifier for outcome (e.g., "ieu-a-7")
        snps: List of SNP rsIDs to look up
        proxies: Whether to use LD proxies for missing SNPs (default: False)
        jwt: Optional JWT token for authentication

    Returns:
        DataFrame with association statistics for the requested SNPs

    Example:
        >>> outcome = get_outcome("ieu-a-7", ["rs123", "rs456"])
        >>> print(outcome[["rsid", "beta", "pval"]])
    """
    client = IEUClient(jwt=jwt)
    results = client.get_associations(
        gwas_id=outcome_id,
        variants=snps,
        proxies=proxies,
    )
    return pd.DataFrame(results)


def search_gwas(query: str, jwt: Optional[str] = None) -> pd.DataFrame:
    """Search for GWAS datasets by keyword.

    Args:
        query: Search query (e.g., "body mass index")
        jwt: Optional JWT token for authentication

    Returns:
        DataFrame with matching GWAS datasets

    Example:
        >>> results = search_gwas("diabetes")
        >>> print(results[["id", "trait", "sample_size"]])
    """
    client = IEUClient(jwt=jwt)
    results = client.get_gwasinfo(query=query)
    return pd.DataFrame(results)


def list_gwas(jwt: Optional[str] = None) -> pd.DataFrame:
    """List all available GWAS datasets.

    Args:
        jwt: Optional JWT token for authentication

    Returns:
        DataFrame with all available GWAS datasets

    Example:
        >>> all_gwas = list_gwas()
        >>> print(f"Total datasets: {len(all_gwas)}")
    """
    client = IEUClient(jwt=jwt)
    results = client.get_gwasinfo()
    return pd.DataFrame(results)


# Pan-UKB GWAS data access
PANUKB_MANIFEST_URL = "https://pan-ukb-us-east-1.s3.amazonaws.com/sumstats_release/phenotype_manifest.tsv.bgz"
PANUKB_BASE_URL = "https://pan-ukb-us-east-1.s3.amazonaws.com/sumstats_release"


def panukb_list_phenotypes() -> pd.DataFrame:
    """List all available Pan-UKB phenotypes.

    Downloads and parses the Pan-UKB phenotype manifest to return information
    about all available GWAS phenotypes.

    Returns:
        DataFrame with columns including phenocode, description, trait_type,
        n_cases, n_controls, and other metadata.

    Example:
        >>> phenotypes = panukb_list_phenotypes()
        >>> print(phenotypes[["phenocode", "description"]].head())
    """
    response = requests.get(PANUKB_MANIFEST_URL)
    response.raise_for_status()

    # Decompress bgzipped content
    decompressed = gzip.decompress(response.content)

    # Parse TSV
    df = pd.read_csv(BytesIO(decompressed), sep="\t")
    return df


def panukb_search(query: str) -> pd.DataFrame:
    """Search for Pan-UKB phenotypes by keyword.

    Searches phenotype descriptions (case-insensitive) for the given query string.

    Args:
        query: Search term to look for in phenotype descriptions

    Returns:
        DataFrame with matching phenotypes

    Example:
        >>> bmi_phenotypes = panukb_search("BMI")
        >>> diabetes = panukb_search("diabetes")
    """
    phenotypes = panukb_list_phenotypes()

    # Case-insensitive search in description column
    mask = phenotypes["description"].str.contains(query, case=False, na=False)
    return phenotypes[mask]


def panukb_load_gwas(
    phenotype_code: str,
    ancestry: str = "EUR",
) -> pd.DataFrame:
    """Load GWAS summary statistics for a Pan-UKB phenotype.

    Downloads and parses GWAS summary statistics from Pan-UKB for the specified
    phenotype and ancestry group.

    Args:
        phenotype_code: Pan-UKB phenotype code (e.g., "21001" for BMI)
        ancestry: Ancestry group code (default: "EUR"). Other options include
            "AFR", "AMR", "CSA", "EAS", "MID"

    Returns:
        DataFrame with GWAS summary statistics including columns:
        chr, pos, snp (or rsid), ref, alt, beta, se, pval, AF

    Example:
        >>> bmi_gwas = panukb_load_gwas("21001")  # BMI in Europeans
        >>> height_afr = panukb_load_gwas("50", ancestry="AFR")  # Height in Africans

    Notes:
        Files are large (can be several GB). Consider filtering to specific
        regions or p-value thresholds for downstream analysis.
    """
    # Construct URL for GWAS file
    # Format: continuous-{phenocode}-{ancestry}-{version}.tsv.bgz
    # We'll try to find the file using the manifest first to get proper naming
    phenotypes = panukb_list_phenotypes()
    pheno_info = phenotypes[phenotypes["phenocode"].astype(str) == str(phenotype_code)]

    if len(pheno_info) == 0:
        raise ValueError(f"Phenotype code {phenotype_code} not found in manifest")

    trait_type = pheno_info.iloc[0]["trait_type"]

    # Construct filename pattern - Pan-UKB uses this format:
    # {trait_type}-{phenocode}-both_sexes-{ancestry}.tsv.bgz
    filename = f"{trait_type}-{phenotype_code}-both_sexes-{ancestry}.tsv.bgz"
    url = f"{PANUKB_BASE_URL}/{filename}"

    # Download GWAS file
    response = requests.get(url)
    response.raise_for_status()

    # Decompress and parse
    decompressed = gzip.decompress(response.content)
    df = pd.read_csv(BytesIO(decompressed), sep="\t")

    # Rename columns to standard format for compatibility with PyMR
    # Pan-UKB uses: chr, pos, snp, ref, alt, beta, se, pval, AF
    # PyMR expects: chr, pos, rsid, ea (effect allele), nea (non-effect allele),
    #               beta, se, pval, eaf (effect allele frequency)
    column_mapping = {
        "snp": "rsid",
        "alt": "ea",  # Alternative allele is effect allele
        "ref": "nea",  # Reference allele is non-effect allele
        "AF": "eaf",  # Allele frequency
    }

    # Only rename columns that exist
    existing_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=existing_mappings)

    return df


# GWAS Catalog integration
GWAS_CATALOG_API = "https://www.ebi.ac.uk/gwas/rest/api"


def gwas_catalog_search(trait: str) -> pd.DataFrame:
    """Search GWAS Catalog for studies by trait name.

    Searches the NHGRI-EBI GWAS Catalog for published GWAS studies matching
    the specified trait. Handles pagination automatically.

    Args:
        trait: Trait name to search for (e.g., "body mass index", "diabetes")

    Returns:
        DataFrame with columns: study_id, trait, author, publication_date,
        pubmed_id, sample_size

    Example:
        >>> studies = gwas_catalog_search("body mass index")
        >>> print(studies[["study_id", "trait", "author"]])

    References:
        GWAS Catalog API: https://www.ebi.ac.uk/gwas/rest/docs/api
    """
    all_studies = []
    page = 0

    while True:
        # Search with pagination
        url = f"{GWAS_CATALOG_API}/studies/search/findByDiseaseTraitContaining"
        params = {
            "trait": trait,
            "size": 20,
            "page": page
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract studies from embedded response
        if "_embedded" not in data or "studies" not in data["_embedded"]:
            break

        studies = data["_embedded"]["studies"]
        if not studies:
            break

        # Parse each study
        for study in studies:
            study_data = {
                "study_id": study.get("accessionId"),
                "trait": study.get("diseaseTrait", {}).get("trait"),
                "author": study.get("publicationInfo", {}).get("author", {}).get("fullname"),
                "publication_date": study.get("publicationInfo", {}).get("publicationDate"),
                "pubmed_id": study.get("publicationInfo", {}).get("pubmedId"),
                "sample_size": study.get("initialSampleSize"),
            }
            all_studies.append(study_data)

        # Check if there are more pages
        page_info = data.get("page", {})
        current_page = page_info.get("number", 0)
        total_pages = page_info.get("totalPages", 1)

        if current_page >= total_pages - 1:
            break

        page += 1

    return pd.DataFrame(all_studies)


def gwas_catalog_get_study(study_id: str) -> dict[str, Any]:
    """Get metadata for a specific GWAS Catalog study.

    Retrieves detailed information about a published GWAS study from the
    GWAS Catalog.

    Args:
        study_id: GWAS Catalog study accession ID (e.g., "GCST001234")

    Returns:
        Dictionary with study metadata including:
        - study_id: Accession ID
        - trait: Disease/trait name
        - author: First author
        - pubmed_id: PubMed ID
        - publication_date: Publication date
        - title: Study title
        - sample_size: Sample size description

    Example:
        >>> study = gwas_catalog_get_study("GCST001234")
        >>> print(study["trait"], study["author"])

    References:
        GWAS Catalog API: https://www.ebi.ac.uk/gwas/rest/docs/api
    """
    url = f"{GWAS_CATALOG_API}/studies/{study_id}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    return {
        "study_id": data.get("accessionId"),
        "trait": data.get("diseaseTrait", {}).get("trait"),
        "author": data.get("publicationInfo", {}).get("author", {}).get("fullname"),
        "pubmed_id": data.get("publicationInfo", {}).get("pubmedId"),
        "publication_date": data.get("publicationInfo", {}).get("publicationDate"),
        "title": data.get("publicationInfo", {}).get("title"),
        "sample_size": data.get("initialSampleSize"),
    }


def gwas_catalog_get_associations(study_id: str) -> pd.DataFrame:
    """Get SNP associations for a GWAS Catalog study.

    Retrieves all SNP-trait associations from a published GWAS study in the
    GWAS Catalog. Handles pagination automatically.

    Args:
        study_id: GWAS Catalog study accession ID (e.g., "GCST001234")

    Returns:
        DataFrame with columns:
        - rsid: SNP rsID
        - chr: Chromosome
        - position: Base pair position
        - ea: Effect allele (risk allele)
        - beta: Effect size (beta coefficient, if available)
        - or_value: Odds ratio (if available, for binary traits)
        - se: Standard error
        - pval: P-value
        - eaf: Effect allele frequency

    Example:
        >>> assocs = gwas_catalog_get_associations("GCST001234")
        >>> print(assocs[["rsid", "chr", "position", "beta", "pval"]])

    Notes:
        - GWAS Catalog stores p-values as mantissa and exponent
        - Effect alleles are extracted from risk allele names (format: "rsID-allele")
        - Some studies report OR instead of beta
        - Not all associations have complete data

    References:
        GWAS Catalog API: https://www.ebi.ac.uk/gwas/rest/docs/api
    """
    all_associations = []
    page = 0

    while True:
        # Get associations with pagination
        url = f"{GWAS_CATALOG_API}/studies/{study_id}/associations"
        params = {
            "size": 20,
            "page": page,
            "projection": "associationByStudy"  # Get detailed association data
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract associations from embedded response
        if "_embedded" not in data or "associations" not in data["_embedded"]:
            break

        associations = data["_embedded"]["associations"]
        if not associations:
            break

        # Parse each association
        for assoc in associations:
            # Extract chromosome and position from SNP locations
            chr_val = None
            position = None
            if "snps" in assoc and assoc["snps"]:
                snp = assoc["snps"][0]
                if "locations" in snp and snp["locations"]:
                    location = snp["locations"][0]
                    chr_val = location.get("chromosomeName")
                    position = location.get("chromosomePosition")

            # Extract effect allele from risk allele name
            ea = None
            if "loci" in assoc and assoc["loci"]:
                locus = assoc["loci"][0]
                if "strongestRiskAlleles" in locus and locus["strongestRiskAlleles"]:
                    risk_allele = locus["strongestRiskAlleles"][0]
                    allele_name = risk_allele.get("riskAlleleName", "")
                    # Format is typically "rsID-allele"
                    if "-" in allele_name:
                        ea = allele_name.split("-")[-1]

            # Calculate p-value from mantissa and exponent
            pval = None
            if assoc.get("pvalueMantissa") is not None and assoc.get("pvalueExponent") is not None:
                mantissa = assoc["pvalueMantissa"]
                exponent = assoc["pvalueExponent"]
                pval = mantissa * (10 ** exponent)

            # Convert risk frequency to float
            eaf = None
            if assoc.get("riskFrequency"):
                try:
                    eaf = float(assoc["riskFrequency"])
                except (ValueError, TypeError):
                    pass

            assoc_data = {
                "rsid": assoc.get("rsId"),
                "chr": chr_val,
                "position": position,
                "ea": ea,
                "beta": assoc.get("betaNum"),
                "or_value": assoc.get("orPerCopyNum"),
                "se": assoc.get("standardError"),
                "pval": pval,
                "eaf": eaf,
            }
            all_associations.append(assoc_data)

        # Check if there are more pages
        page_info = data.get("page", {})
        current_page = page_info.get("number", 0)
        total_pages = page_info.get("totalPages", 1)

        if current_page >= total_pages - 1:
            break

        page += 1

    return pd.DataFrame(all_associations)


# FinnGen R12 integration
FINNGEN_API_BASE = "https://r12.finngen.fi/api"


def finngen_list_phenotypes() -> pd.DataFrame:
    """List all available FinnGen R12 phenotypes.

    Retrieves the FinnGen R12 phenotype manifest containing information about
    all available GWAS phenotypes from the Finnish population.

    Returns:
        DataFrame with columns including phenocode, phenostring, category,
        num_cases, num_controls, num_gw_significant, and other metadata.

    Example:
        >>> phenotypes = finngen_list_phenotypes()
        >>> print(phenotypes[["phenocode", "phenostring"]].head())

    References:
        FinnGen R12: https://r12.finngen.fi/
    """
    url = f"{FINNGEN_API_BASE}/phenos"
    response = requests.get(url)
    response.raise_for_status()

    # Parse JSON response
    data = response.json()
    return pd.DataFrame(data)


def finngen_search(query: str) -> pd.DataFrame:
    """Search for FinnGen phenotypes by keyword.

    Searches phenotype descriptions (case-insensitive) for the given query string.

    Args:
        query: Search term to look for in phenotype descriptions

    Returns:
        DataFrame with matching phenotypes

    Example:
        >>> diabetes_phenotypes = finngen_search("diabetes")
        >>> chd = finngen_search("coronary heart")

    References:
        FinnGen R12: https://r12.finngen.fi/
    """
    phenotypes = finngen_list_phenotypes()

    # Case-insensitive search in phenostring column
    mask = phenotypes["phenostring"].str.contains(query, case=False, na=False)
    return phenotypes[mask]


def finngen_load_gwas(endpoint: str) -> pd.DataFrame:
    """Load GWAS summary statistics for a FinnGen phenotype.

    Downloads and parses GWAS summary statistics from FinnGen R12 for the
    specified phenotype endpoint.

    Args:
        endpoint: FinnGen phenotype code (e.g., "T2D" for Type 2 diabetes)

    Returns:
        DataFrame with GWAS summary statistics including columns:
        rsid, chr, position, ref, alt, beta, se, pval, eaf

    Example:
        >>> t2d_gwas = finngen_load_gwas("T2D")  # Type 2 diabetes
        >>> chd_gwas = finngen_load_gwas("I9_CHD")  # Coronary heart disease

    Notes:
        FinnGen provides GWAS for the Finnish population with unique disease
        endpoints. Files may be large depending on the number of variants.

    References:
        FinnGen R12: https://r12.finngen.fi/
    """
    # Verify phenotype exists in manifest
    phenotypes = finngen_list_phenotypes()
    pheno_info = phenotypes[phenotypes["phenocode"] == endpoint]

    if len(pheno_info) == 0:
        raise ValueError(f"Phenotype code {endpoint} not found in FinnGen manifest")

    # Construct URL for GWAS data
    url = f"{FINNGEN_API_BASE}/pheno/{endpoint}"

    # Download GWAS data
    response = requests.get(url)
    response.raise_for_status()

    # Parse JSON response
    data = response.json()

    # Extract data array from response
    if "data" in data:
        df = pd.DataFrame(data["data"])
    else:
        df = pd.DataFrame(data)

    # Rename columns to standard format for compatibility with PyMR
    # FinnGen uses: chromosome, position, rsid, ref, alt, beta, sebeta, pval, maf
    # PyMR expects: chr, pos, rsid, ea (effect allele), nea (non-effect allele),
    #               beta, se, pval, eaf (effect allele frequency)
    column_mapping = {
        "chromosome": "chr",
        "position": "pos",
        "alt": "ea",  # Alternative allele is effect allele
        "ref": "nea",  # Reference allele is non-effect allele
        "sebeta": "se",  # Standard error of beta
        "maf": "eaf",  # Minor allele frequency as effect allele frequency
    }

    # Only rename columns that exist
    existing_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=existing_mappings)

    return df
