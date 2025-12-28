"""GWAS data I/O utilities.

Functions for loading GWAS summary statistics from various sources:
- Local files (TSV, CSV, gzipped)
- Pan-UKB S3 bucket
- IEU OpenGWAS API
"""

import gzip
from pathlib import Path
from typing import Literal

import pandas as pd


def load_gwas(
    path: str | Path,
    source: Literal["auto", "panukb", "ieu", "custom"] = "auto",
    chunksize: int | None = None,
    columns: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Load GWAS summary statistics.

    Args:
        path: Path to file or GWAS identifier
        source: Data source format:
            - "auto": Detect from file extension/path
            - "panukb": Pan-UK Biobank format
            - "ieu": IEU OpenGWAS format
            - "custom": User-specified columns
        chunksize: If provided, read in chunks for large files
        columns: Custom column name mapping (for source="custom")

    Returns:
        DataFrame with standardized columns: SNP, chr, pos, effect_allele,
        other_allele, beta, se, pval, eaf (if available)

    Example:
        >>> gwas = load_gwas("data/bmi.tsv.gz")
        >>> gwas = load_gwas("data/outcome.csv", columns={"BETA": "beta"})
    """
    path = Path(path)

    # Detect compression
    if path.suffix == ".gz" or str(path).endswith(".bgz"):
        opener = gzip.open
        mode = "rt"
    else:
        opener = open
        mode = "r"

    # Detect separator
    sep = "\t" if path.suffix in [".tsv", ".gz", ".bgz"] else ","

    # Read data
    if chunksize is not None:
        chunks = []
        with opener(path, mode) as f:
            reader = pd.read_csv(f, sep=sep, chunksize=chunksize)
            for chunk in reader:
                chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
    else:
        with opener(path, mode) as f:
            df = pd.read_csv(f, sep=sep)

    # Standardize columns based on source
    if source == "auto":
        source = _detect_source(df)

    if source == "panukb":
        df = _standardize_panukb(df)
    elif source == "ieu":
        df = _standardize_ieu(df)
    elif source == "custom" and columns is not None:
        df = df.rename(columns=columns)

    return df


def _detect_source(df: pd.DataFrame) -> str:
    """Detect GWAS source from column names."""
    cols = set(df.columns)

    if "neglog10_pval_EUR" in cols or "beta_EUR" in cols:
        return "panukb"
    if "b" in cols and "se" in cols and "p" in cols:
        return "ieu"
    return "custom"


def _standardize_panukb(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize Pan-UKB column names."""
    df = df.copy()

    # Determine if continuous or binary trait
    if "beta_EUR" in df.columns:
        # Continuous trait
        df = df.rename(
            columns={
                "chr": "chr",
                "pos": "pos",
                "ref": "other_allele",
                "alt": "effect_allele",
                "beta_EUR": "beta",
                "se_EUR": "se",
                "af_EUR": "eaf",
            }
        )
        if "neglog10_pval_EUR" in df.columns:
            df["pval"] = 10 ** (-df["neglog10_pval_EUR"])
    elif "beta_meta_hq" in df.columns:
        # Binary trait with meta-analysis
        df = df.rename(
            columns={
                "chr": "chr",
                "pos": "pos",
                "ref": "other_allele",
                "alt": "effect_allele",
                "beta_meta_hq": "beta",
                "se_meta_hq": "se",
                "af_controls_EUR": "eaf",
            }
        )
        if "neglog10_pval_meta_hq" in df.columns:
            df["pval"] = 10 ** (-df["neglog10_pval_meta_hq"])

    # Create SNP ID if not present
    if "SNP" not in df.columns:
        df["SNP"] = (
            df["chr"].astype(str)
            + ":"
            + df["pos"].astype(str)
            + ":"
            + df["other_allele"]
            + ":"
            + df["effect_allele"]
        )

    return df


def _standardize_ieu(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize IEU OpenGWAS column names."""
    return df.rename(
        columns={
            "b": "beta",
            "p": "pval",
            "eaf": "eaf",
            "ea": "effect_allele",
            "nea": "other_allele",
        }
    )


def load_instruments(
    exposure_id: str,
    p_threshold: float = 5e-8,
) -> pd.DataFrame:
    """Load pre-clumped instruments for an exposure.

    This is a placeholder for future IEU OpenGWAS API integration.

    Args:
        exposure_id: GWAS identifier (e.g., "ieu-a-2")
        p_threshold: P-value threshold for significance

    Returns:
        DataFrame of independent genetic instruments
    """
    msg = "IEU API integration not yet implemented. Use load_gwas() instead."
    raise NotImplementedError(msg)
