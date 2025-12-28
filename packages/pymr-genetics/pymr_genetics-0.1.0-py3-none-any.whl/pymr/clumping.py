"""LD-based clumping using 1000 Genomes reference panels.

This module provides functionality to clump SNPs based on linkage disequilibrium (LD)
using the LDlink API or pre-computed LD matrices from 1000 Genomes.
"""

import io
from typing import Optional

import numpy as np
import pandas as pd
import requests


# Valid 1000 Genomes populations
VALID_POPULATIONS = ["EUR", "EAS", "AFR", "AMR", "SAS", "ALL"]

# LDlink API base URL
LDLINK_API_BASE = "https://ldlink.nih.gov/LDlinkRest"


def _parse_ldlink_response(response_text: str) -> pd.DataFrame:
    """Parse LDlink API response into LD matrix.

    Args:
        response_text: Tab-separated text from LDlink API

    Returns:
        Symmetric LD matrix (r² values) as DataFrame

    Raises:
        ValueError: If response cannot be parsed
    """
    try:
        # Parse tab-separated response
        df = pd.read_csv(io.StringIO(response_text), sep="\t", index_col=0)

        # Convert to numeric (handle any string values)
        df = df.apply(pd.to_numeric, errors="coerce")

        # Ensure symmetry (average with transpose)
        df = (df + df.T) / 2

        # Ensure diagonal is 1.0
        np.fill_diagonal(df.values, 1.0)

        return df

    except Exception as e:
        raise ValueError(f"Failed to parse LDlink response: {e}") from e


def get_ld_matrix(
    snps: list[str],
    population: str = "EUR",
    token: Optional[str] = None,
) -> pd.DataFrame:
    """Get LD matrix for a list of SNPs using LDlink API.

    Args:
        snps: List of SNP rsIDs (e.g., ["rs1", "rs2"])
        population: 1000 Genomes population code (EUR, EAS, AFR, AMR, SAS, ALL)
        token: LDlink API token (get free token at https://ldlink.nih.gov/?tab=apiaccess)

    Returns:
        Symmetric LD matrix with r² values

    Raises:
        ValueError: If input is invalid
        RuntimeError: If API request fails

    Note:
        LDlink has rate limits. For large-scale analyses, consider using
        pre-computed LD matrices or local PLINK calculations.

    Example:
        >>> ld_matrix = get_ld_matrix(["rs1", "rs2", "rs3"], token="your_token")
        >>> print(ld_matrix.loc["rs1", "rs2"])  # r² between rs1 and rs2
    """
    if not snps:
        raise ValueError("Must provide at least one SNP")

    if population not in VALID_POPULATIONS:
        raise ValueError(
            f"Invalid population: {population}. Must be one of {VALID_POPULATIONS}"
        )

    if token is None:
        raise ValueError(
            "LDlink API token required. Get free token at "
            "https://ldlink.nih.gov/?tab=apiaccess"
        )

    # Build API request
    url = f"{LDLINK_API_BASE}/ldmatrix"
    params = {
        "snps": "\n".join(snps),
        "pop": population,
        "r2_d": "r2",  # Return r² values
        "token": token,
    }

    # Make API request
    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            raise RuntimeError(
                f"LDlink API request failed with status {response.status_code}: "
                f"{response.text}"
            )

        # Parse response
        ld_matrix = _parse_ldlink_response(response.text)

        # Verify we got all SNPs
        missing_snps = set(snps) - set(ld_matrix.index)
        if missing_snps:
            print(f"Warning: SNPs not found in LD reference: {missing_snps}")

        return ld_matrix

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"LDlink API request failed: {e}") from e


def _select_index_snps(
    snps: pd.DataFrame,
    ld_matrix: pd.DataFrame,
    r2_threshold: float,
) -> list[str]:
    """Select independent index SNPs based on LD.

    Uses greedy algorithm:
    1. Sort SNPs by p-value
    2. Select top SNP as index
    3. Remove all SNPs in LD (r² > threshold) with index
    4. Repeat until no SNPs remain

    Args:
        snps: DataFrame with columns: SNP, pval
        ld_matrix: LD matrix (r² values)
        r2_threshold: LD threshold (SNPs with r² > threshold are clumped)

    Returns:
        List of independent index SNP rsIDs
    """
    # Sort by p-value
    snps_sorted = snps.sort_values("pval").copy()

    # Track which SNPs are still available
    available_snps = set(snps_sorted["SNP"])
    index_snps = []

    # Greedy selection
    for _, row in snps_sorted.iterrows():
        snp = row["SNP"]

        if snp not in available_snps:
            continue

        # Select this SNP as index
        index_snps.append(snp)

        # Find SNPs in LD with this index SNP
        if snp in ld_matrix.index:
            ld_values = ld_matrix.loc[snp]
            in_ld = ld_values[ld_values > r2_threshold].index.tolist()

            # Remove SNPs in LD (except the index SNP itself)
            for ld_snp in in_ld:
                if ld_snp != snp:
                    available_snps.discard(ld_snp)

    return index_snps


def ld_clump(
    snps: pd.DataFrame,
    r2_threshold: float = 0.01,
    kb_window: int = 10000,
    population: str = "EUR",
    token: Optional[str] = None,
) -> pd.DataFrame:
    """Clump SNPs based on linkage disequilibrium.

    Retains independent SNPs by removing those in LD (r² > threshold) with
    more significant SNPs. Uses 1000 Genomes reference panel via LDlink API.

    Args:
        snps: DataFrame with required columns:
            - SNP: rsID
            - chr: Chromosome
            - pos: Base pair position
            - pval: Association p-value
        r2_threshold: LD threshold (SNPs with r² > this are clumped together)
        kb_window: Only clump SNPs within this many kb
        population: 1000 Genomes population (EUR, EAS, AFR, AMR, SAS, ALL)
        token: LDlink API token (required)

    Returns:
        DataFrame with independent index SNPs (subset of input)

    Raises:
        ValueError: If required columns are missing

    Example:
        >>> snps = pd.DataFrame({
        ...     "SNP": ["rs1", "rs2", "rs3"],
        ...     "chr": [1, 1, 2],
        ...     "pos": [1000000, 1005000, 2000000],
        ...     "pval": [1e-8, 5e-7, 1e-6],
        ... })
        >>> clumped = ld_clump(snps, token="your_token")
        >>> print(f"Kept {len(clumped)} independent SNPs")

    Note:
        - SNPs on different chromosomes are never clumped together
        - SNPs beyond kb_window are not clumped even if in LD
        - Uses greedy algorithm: most significant SNP in each LD block is kept
        - Requires LDlink API token (free at https://ldlink.nih.gov/?tab=apiaccess)
    """
    # Validate input
    required_cols = ["SNP", "chr", "pos", "pval"]
    missing_cols = [col for col in required_cols if col not in snps.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    if snps.empty:
        return snps.copy()

    # Process each chromosome separately
    clumped_snps = []

    for chr_num in snps["chr"].unique():
        chr_snps = snps[snps["chr"] == chr_num].copy()

        # Sort by position
        chr_snps = chr_snps.sort_values("pos")

        # Group SNPs within kb_window
        # For each SNP, only consider LD with SNPs within window
        chr_snps["pos_kb"] = chr_snps["pos"] / 1000

        # Get LD matrix for this chromosome
        snp_list = chr_snps["SNP"].tolist()

        if len(snp_list) == 1:
            # Single SNP - automatically independent
            clumped_snps.append(chr_snps)
            continue

        # Get LD matrix from LDlink
        try:
            ld_matrix = get_ld_matrix(snp_list, population=population, token=token)
        except Exception as e:
            print(f"Warning: Failed to get LD for chr {chr_num}: {e}")
            # If LD lookup fails, keep all SNPs
            clumped_snps.append(chr_snps)
            continue

        # Apply kb_window filter to LD matrix
        # Set LD to 0 for SNPs beyond window
        for i, snp_i in enumerate(snp_list):
            pos_i = chr_snps[chr_snps["SNP"] == snp_i]["pos"].iloc[0]

            for j, snp_j in enumerate(snp_list):
                if i == j:
                    continue

                pos_j = chr_snps[chr_snps["SNP"] == snp_j]["pos"].iloc[0]
                dist_kb = abs(pos_i - pos_j) / 1000

                if dist_kb > kb_window:
                    # Beyond window - set LD to 0
                    if snp_i in ld_matrix.index and snp_j in ld_matrix.columns:
                        ld_matrix.loc[snp_i, snp_j] = 0.0
                        ld_matrix.loc[snp_j, snp_i] = 0.0

        # Select independent SNPs
        index_snps = _select_index_snps(chr_snps, ld_matrix, r2_threshold)

        # Keep only index SNPs
        chr_clumped = chr_snps[chr_snps["SNP"].isin(index_snps)]
        clumped_snps.append(chr_clumped)

    # Combine chromosomes
    result = pd.concat(clumped_snps, ignore_index=True)

    # Sort by p-value
    result = result.sort_values("pval").reset_index(drop=True)

    return result
