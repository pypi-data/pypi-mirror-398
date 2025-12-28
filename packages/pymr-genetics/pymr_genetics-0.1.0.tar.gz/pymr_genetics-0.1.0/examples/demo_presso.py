"""Demonstration of MR-PRESSO for detecting horizontal pleiotropy.

This example shows how MR-PRESSO detects and corrects for horizontal pleiotropy
by identifying outlier SNPs that violate the instrumental variable assumptions.
"""

import numpy as np
from pymr.methods import mr_presso, ivw

# Set random seed for reproducibility
np.random.seed(42)

# Example 1: Clean data without pleiotropy
print("=" * 70)
print("Example 1: Clean data (no horizontal pleiotropy)")
print("=" * 70)

n_snps = 30
beta_exp = np.random.normal(0.1, 0.02, n_snps)
se_exp = np.abs(np.random.normal(0.01, 0.002, n_snps))

# True causal effect = 0.5
beta_out = 0.5 * beta_exp + np.random.normal(0, 0.005, n_snps)
se_out = np.abs(np.random.normal(0.02, 0.005, n_snps))

# Run MR-PRESSO
result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=1000)

print(f"\nOriginal IVW estimate: {result['original_beta']:.3f} ± {result['original_se']:.3f}")
print(f"Global test p-value: {result['global_test_pval']:.3f}")
print(f"Number of outliers detected: {len(result['outlier_indices'])}")
print(f"Corrected estimate: {result['corrected_beta']:.3f} ± {result['corrected_se']:.3f}")

if not np.isnan(result['distortion_test_pval']):
    print(f"Distortion test p-value: {result['distortion_test_pval']:.3f}")
else:
    print("Distortion test: Not applicable (no outliers)")


# Example 2: Data with horizontal pleiotropy
print("\n" + "=" * 70)
print("Example 2: Data with horizontal pleiotropy")
print("=" * 70)

# Create data with true effect = 0.3
beta_exp = np.random.normal(0.1, 0.02, n_snps)
se_exp = np.abs(np.random.normal(0.01, 0.002, n_snps))
beta_out = 0.3 * beta_exp + np.random.normal(0, 0.005, n_snps)
se_out = np.abs(np.random.normal(0.02, 0.005, n_snps))

# Add horizontal pleiotropy to 3 SNPs (bias the estimate upward)
pleiotropic_snps = [5, 10, 15]
beta_out[pleiotropic_snps] += np.array([0.15, 0.12, 0.18])

print(f"\nPleiotropic SNPs added at indices: {pleiotropic_snps}")

# Compare standard IVW with MR-PRESSO
ivw_result = ivw(beta_exp, se_exp, beta_out, se_out)
presso_result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=1000)

print(f"\nStandard IVW estimate: {ivw_result['beta']:.3f} ± {ivw_result['se']:.3f}")
print(f"  (biased by pleiotropic SNPs)")

print(f"\nMR-PRESSO results:")
print(f"  Global test p-value: {presso_result['global_test_pval']:.3f}")
print(f"  Number of outliers detected: {len(presso_result['outlier_indices'])}")
print(f"  Detected outliers: {presso_result['outlier_indices']}")

# Check if pleiotropic SNPs were detected
detected = [idx for idx in pleiotropic_snps if idx in presso_result['outlier_indices']]
print(f"  Correctly identified pleiotropic SNPs: {detected}")

print(f"\n  Original estimate: {presso_result['original_beta']:.3f} ± {presso_result['original_se']:.3f}")
print(f"  Corrected estimate: {presso_result['corrected_beta']:.3f} ± {presso_result['corrected_se']:.3f}")
print(f"    (closer to true effect of 0.3)")

if not np.isnan(presso_result['distortion_test_pval']):
    print(f"  Distortion test p-value: {presso_result['distortion_test_pval']:.3f}")
    if presso_result['distortion_test_pval'] < 0.05:
        print("    Significant distortion detected - corrected estimate differs from original")


# Example 3: Comparing different simulation counts
print("\n" + "=" * 70)
print("Example 3: Effect of simulation count on precision")
print("=" * 70)

# Use the pleiotropic data from Example 2
for n_sims in [100, 1000, 5000]:
    result = mr_presso(beta_exp, se_exp, beta_out, se_out, n_simulations=n_sims)
    print(f"\nWith {n_sims:,} simulations:")
    print(f"  Global test p-value: {result['global_test_pval']:.4f}")
    print(f"  Outliers detected: {len(result['outlier_indices'])}")

print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
print("""
MR-PRESSO helps detect and correct for horizontal pleiotropy by:

1. Global test: Tests whether any horizontal pleiotropy is present
   - Low p-value indicates presence of pleiotropy

2. Outlier test: Identifies specific SNPs violating IV assumptions
   - Uses Bonferroni correction for multiple testing

3. Distortion test: Tests if removing outliers changes the estimate
   - Significant distortion suggests bias was present

4. Corrected estimate: IVW estimate after removing outliers
   - Should be less biased if outliers were truly pleiotropic

Reference: Verbanck et al. (2018) Nature Genetics 50:693-698
""")
