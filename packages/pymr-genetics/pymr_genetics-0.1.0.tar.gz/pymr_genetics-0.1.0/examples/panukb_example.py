"""Example usage of PyMR Pan-UKB integration.

This example demonstrates how to use PyMR to access Pan-UKB GWAS data:
1. List available phenotypes
2. Search for specific traits
3. Load GWAS summary statistics
4. Use Pan-UKB data for MR analysis

Pan-UKB provides pre-computed GWAS for UK Biobank phenotypes across
multiple ancestry groups (EUR, AFR, AMR, CSA, EAS, MID).

Reference: https://pan.ukbb.broadinstitute.org/
"""

from pymr import panukb_list_phenotypes, panukb_load_gwas, panukb_search

# Example 1: List available phenotypes
print("=" * 60)
print("Example 1: List available Pan-UKB phenotypes")
print("=" * 60)
print("""
# Get all available phenotypes:
phenotypes = panukb_list_phenotypes()
print(f"Total phenotypes: {len(phenotypes)}")
print(phenotypes[["phenocode", "description", "trait_type"]].head())

# Columns include:
# - phenocode: UK Biobank field ID
# - description: Human-readable trait name
# - trait_type: continuous, binary, categorical, etc.
# - n_cases, n_controls: Sample sizes
""")

# Example 2: Search for specific traits
print("\n" + "=" * 60)
print("Example 2: Search for phenotypes by keyword")
print("=" * 60)
print("""
# Search for BMI-related phenotypes:
bmi_phenotypes = panukb_search("BMI")
print(f"Found {len(bmi_phenotypes)} BMI-related phenotypes")
print(bmi_phenotypes[["phenocode", "description"]])

# Search is case-insensitive:
diabetes = panukb_search("diabetes")
print(f"Found {len(diabetes)} diabetes-related phenotypes")
""")

# Example 3: Load GWAS summary statistics
print("\n" + "=" * 60)
print("Example 3: Load GWAS summary statistics")
print("=" * 60)
print("""
# Load BMI GWAS (phenocode 21001) for Europeans:
bmi_gwas = panukb_load_gwas("21001", ancestry="EUR")
print(f"Loaded {len(bmi_gwas)} variants")
print(bmi_gwas.head())

# Columns include:
# - chr, pos: Chromosome and position
# - rsid: SNP identifier
# - ea, nea: Effect and non-effect alleles
# - beta, se: Effect size and standard error
# - pval: P-value
# - eaf: Effect allele frequency

# Filter to genome-wide significant variants:
gwas_significant = bmi_gwas[bmi_gwas["pval"] < 5e-8]
print(f"Genome-wide significant SNPs: {len(gwas_significant)}")
""")

# Example 4: Load GWAS for different ancestries
print("\n" + "=" * 60)
print("Example 4: Multi-ancestry analysis")
print("=" * 60)
print("""
# Load height GWAS (phenocode 50) for different ancestries:
height_eur = panukb_load_gwas("50", ancestry="EUR")  # Europeans
height_afr = panukb_load_gwas("50", ancestry="AFR")  # Africans
height_eas = panukb_load_gwas("50", ancestry="EAS")  # East Asians

print(f"EUR: {len(height_eur)} variants")
print(f"AFR: {len(height_afr)} variants")
print(f"EAS: {len(height_eas)} variants")

# Compare effect sizes across ancestries:
# (This requires merging the datasets on rsid)
""")

# Example 5: Complete MR workflow with Pan-UKB
print("\n" + "=" * 60)
print("Example 5: MR analysis with Pan-UKB data")
print("=" * 60)
print("""
# Complete workflow for BMI -> Type 2 Diabetes MR analysis:

# 1. Load BMI GWAS (exposure)
bmi_gwas = panukb_load_gwas("21001", ancestry="EUR")  # BMI
print(f"Loaded {len(bmi_gwas)} BMI variants")

# 2. Filter to genome-wide significant variants
instruments = bmi_gwas[bmi_gwas["pval"] < 5e-8].copy()
print(f"Found {len(instruments)} genome-wide significant variants")

# 3. Extract SNP list
snp_list = instruments["rsid"].tolist()

# 4. Load Type 2 Diabetes GWAS (outcome)
# Search for T2D phenotype:
t2d_phenotypes = panukb_search("Type 2 diabetes")
print(t2d_phenotypes[["phenocode", "description"]])

# Load T2D GWAS (example phenocode - check actual code in search results)
# t2d_gwas = panukb_load_gwas("E11", ancestry="EUR")

# 5. The data is now ready for harmonization and MR analysis
# using PyMR's harmonize() and MR() functions
""")

# Example 6: Memory-efficient analysis
print("\n" + "=" * 60)
print("Example 6: Memory-efficient analysis for large GWAS")
print("=" * 60)
print("""
# Pan-UKB files can be very large (several GB)
# For MR analysis, you typically only need genome-wide significant SNPs

# Strategy 1: Filter immediately after loading
gwas = panukb_load_gwas("21001", ancestry="EUR")
instruments = gwas[gwas["pval"] < 5e-8]
del gwas  # Free memory

# Strategy 2: For extremely large files, consider:
# - Loading in chunks using pandas chunk iterator
# - Pre-filtering files externally using tabix/bcftools
# - Using only top hits (e.g., p < 1e-100) for initial exploration

# Note: Pan-UKB files are bgzipped, so they're already compressed
""")

print("\n" + "=" * 60)
print("For more information:")
print("  - Pan-UKB browser: https://pan.ukbb.broadinstitute.org/")
print("  - Pan-UKB paper: https://doi.org/10.1016/j.cell.2020.10.035")
print("  - PyMR docs: https://maxghenis.github.io/pymr")
print("=" * 60)
