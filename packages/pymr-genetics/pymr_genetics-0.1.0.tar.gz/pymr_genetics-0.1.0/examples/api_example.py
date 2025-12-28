"""Example usage of PyMR IEU OpenGWAS API integration.

This example demonstrates how to use the PyMR API integration to:
1. Search for GWAS datasets
2. Fetch genetic instruments for an exposure
3. Look up SNPs in an outcome dataset
4. Prepare data for Mendelian Randomization analysis

Note: Requires OPENGWAS_JWT environment variable to be set.
Get your token from: https://api.opengwas.io/profile/
"""

import os

from pymr import get_instruments, get_outcome, list_gwas, search_gwas

# Check if JWT token is available
if not os.environ.get("OPENGWAS_JWT"):
    print("Warning: OPENGWAS_JWT environment variable not set.")
    print("Visit https://api.opengwas.io/profile/ to get your token.")
    print("\nThis example will use mock data for demonstration.\n")

# Example 1: Search for GWAS datasets
print("=" * 60)
print("Example 1: Search for GWAS datasets")
print("=" * 60)
print("\n# Search for BMI-related GWAS:")
print('results = search_gwas("body mass index")')
print("\nThis would return a DataFrame with matching GWAS datasets.")

# Example 2: List all available GWAS
print("\n" + "=" * 60)
print("Example 2: List all available GWAS datasets")
print("=" * 60)
print("\n# Get all available GWAS:")
print("all_gwas = list_gwas()")
print("print(f'Total datasets: {len(all_gwas)}')")

# Example 3: Get genetic instruments
print("\n" + "=" * 60)
print("Example 3: Fetch genetic instruments for exposure")
print("=" * 60)
print("\n# Get BMI instruments (genome-wide significant, clumped):")
print('instruments = get_instruments("ieu-a-2", p_threshold=5e-8)')
print("print(instruments.head())")
print("\nColumns include: rsid, chr, position, ea, nea, beta, se, pval, eaf")

# Example 4: Get outcome data
print("\n" + "=" * 60)
print("Example 4: Look up SNPs in outcome dataset")
print("=" * 60)
print("\n# Extract SNP list from instruments:")
print('snp_list = instruments["rsid"].tolist()')
print("\n# Get associations in Type 2 Diabetes outcome:")
print('outcome = get_outcome("ieu-a-7", snp_list)')
print("print(outcome.head())")

# Example 5: Complete workflow
print("\n" + "=" * 60)
print("Example 5: Complete MR workflow")
print("=" * 60)
print("""
# Complete workflow for BMI -> Type 2 Diabetes MR analysis:

# 1. Get instruments
instruments = get_instruments("ieu-a-2")  # BMI
print(f"Found {len(instruments)} genetic instruments for BMI")

# 2. Extract SNP list
snp_list = instruments["rsid"].tolist()

# 3. Get outcome associations
outcome = get_outcome("ieu-a-7", snp_list)  # T2D
print(f"Found {len(outcome)} SNPs in outcome dataset")

# 4. The data is now ready for harmonization and MR analysis
# using PyMR's harmonize() and MR() functions
""")

# Example 6: Using LD proxies
print("\n" + "=" * 60)
print("Example 6: Using LD proxies for missing SNPs")
print("=" * 60)
print("""
# If some SNPs are missing in the outcome, use LD proxies:
outcome_with_proxies = get_outcome(
    "ieu-a-7",
    snp_list,
    proxies=True  # Enable LD proxy lookup
)
print(f"With proxies: {len(outcome_with_proxies)} SNPs")
""")

# Example 7: Custom p-value threshold
print("\n" + "=" * 60)
print("Example 7: Custom significance threshold")
print("=" * 60)
print("""
# Use a more lenient threshold (e.g., for smaller GWAS):
instruments_lenient = get_instruments(
    "ieu-a-2",
    p_threshold=1e-6,  # Less stringent
    clump=True,
    r2=0.01,  # Stricter clumping
    kb=500,  # Smaller clumping window
)
print(f"Found {len(instruments_lenient)} instruments at p<1e-6")
""")

print("\n" + "=" * 60)
print("For more information:")
print("  - API docs: https://gwas-api.mrcieu.ac.uk/")
print("  - Get JWT: https://api.opengwas.io/profile/")
print("  - PyMR docs: https://maxghenis.github.io/pymr")
print("=" * 60)
