"""Example of LD-based clumping using 1000 Genomes reference panels.

This example demonstrates how to clump SNPs based on linkage disequilibrium
using the LDlink API and 1000 Genomes reference data.
"""

import pandas as pd
from pymr import ld_clump, get_ld_matrix

# Note: You need a free LDlink API token from https://ldlink.nih.gov/?tab=apiaccess
# Store it in an environment variable or replace 'your_token_here' below
import os
LDLINK_TOKEN = os.environ.get("LDLINK_TOKEN", "your_token_here")


def example_basic_clumping():
    """Basic example of LD clumping."""
    print("\n=== Basic LD Clumping Example ===\n")

    # Create sample GWAS summary statistics
    gwas_data = pd.DataFrame({
        "SNP": ["rs1", "rs2", "rs3", "rs4", "rs5"],
        "chr": [1, 1, 1, 2, 2],
        "pos": [1000000, 1005000, 1020000, 2000000, 2008000],
        "pval": [1e-8, 5e-7, 1e-6, 2e-8, 3e-7],
        "beta": [0.1, 0.08, 0.05, 0.12, 0.09],
        "se": [0.02, 0.02, 0.02, 0.02, 0.02],
    })

    print("Original GWAS data:")
    print(gwas_data)
    print(f"\nTotal SNPs: {len(gwas_data)}")

    # Clump SNPs using LD
    # Note: This example won't actually run without a valid token
    # Uncomment the following when you have a token:
    # clumped = ld_clump(
    #     gwas_data,
    #     r2_threshold=0.1,  # Clump SNPs with r² > 0.1
    #     kb_window=10000,   # Within 10Mb windows
    #     population="EUR",  # European ancestry
    #     token=LDLINK_TOKEN,
    # )
    #
    # print("\nClumped data (independent SNPs):")
    # print(clumped)
    # print(f"\nIndependent SNPs: {len(clumped)}")

    print("\nTo run this example, you need a free LDlink API token.")
    print("Get one at: https://ldlink.nih.gov/?tab=apiaccess")


def example_different_populations():
    """Example of clumping with different ancestry populations."""
    print("\n=== Multi-Ancestry Clumping Example ===\n")

    gwas_data = pd.DataFrame({
        "SNP": ["rs1234", "rs5678", "rs9012"],
        "chr": [1, 1, 2],
        "pos": [1000000, 1005000, 2000000],
        "pval": [1e-8, 5e-7, 1e-6],
        "beta": [0.1, 0.08, 0.05],
    })

    populations = {
        "EUR": "European",
        "EAS": "East Asian",
        "AFR": "African",
        "AMR": "American",
        "SAS": "South Asian",
    }

    print("Available 1000 Genomes populations:")
    for code, name in populations.items():
        print(f"  {code}: {name}")

    print("\nExample usage for each population:")
    for code, name in populations.items():
        print(f"\n# {name} ({code}):")
        print(f"clumped = ld_clump(gwas_data, population='{code}', token=LDLINK_TOKEN)")


def example_get_ld_matrix():
    """Example of getting LD matrix for specific SNPs."""
    print("\n=== LD Matrix Retrieval Example ===\n")

    # List of SNPs to get LD for
    snps = ["rs1", "rs2", "rs3", "rs4", "rs5"]

    print(f"Getting LD matrix for SNPs: {snps}")
    print("\nExample code:")
    print(f"ld_matrix = get_ld_matrix({snps}, population='EUR', token=LDLINK_TOKEN)")
    print("\nReturns a pandas DataFrame with r² values:")
    print("""
         rs1   rs2   rs3   rs4   rs5
    rs1  1.0   0.8   0.1   0.0   0.0
    rs2  0.8   1.0   0.1   0.0   0.0
    rs3  0.1   0.1   1.0   0.0   0.0
    rs4  0.0   0.0   0.0   1.0   0.3
    rs5  0.0   0.0   0.0   0.3   1.0
    """)


def example_realistic_workflow():
    """Example of realistic MR workflow with clumping."""
    print("\n=== Realistic MR Workflow with Clumping ===\n")

    print("""
    Typical workflow for Mendelian Randomization with LD clumping:

    1. Load GWAS summary statistics
       exposure = pd.read_csv("bmi_gwas.tsv.gz", sep="\\t")

    2. Filter to genome-wide significant SNPs
       significant = exposure[exposure["pval"] < 5e-8]

    3. Clump to get independent SNPs
       instruments = ld_clump(
           significant,
           r2_threshold=0.001,  # Very strict: r² < 0.001
           kb_window=10000,      # 10Mb window
           population="EUR",
           token=LDLINK_TOKEN,
       )

    4. Extract these SNPs from outcome GWAS
       outcome_snps = outcome[outcome["SNP"].isin(instruments["SNP"])]

    5. Harmonize exposure and outcome
       from pymr import harmonize
       harmonized = harmonize(instruments, outcome_snps)

    6. Run MR analysis
       from pymr import MR
       mr = MR(harmonized)
       results = mr.run()

    Benefits of LD clumping:
    - Removes correlated SNPs (violates MR independence assumption)
    - Reduces winner's curse and weak instrument bias
    - Improves statistical power in some cases
    - Standard practice in published MR studies
    """)


def main():
    """Run all examples."""
    print("=" * 70)
    print("PyMR: LD-Based Clumping Examples")
    print("=" * 70)

    example_basic_clumping()
    example_different_populations()
    example_get_ld_matrix()
    example_realistic_workflow()

    print("\n" + "=" * 70)
    print("For more information, see the documentation:")
    print("https://maxghenis.github.io/pymr")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
