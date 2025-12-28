# MR-PRESSO: Pleiotropy RESidual Sum and Outlier Test

## Overview

MR-PRESSO (Mendelian Randomization Pleiotropy RESidual Sum and Outlier) is a method for detecting and correcting horizontal pleiotropy in Mendelian randomization studies.

Reference: Verbanck M, et al. (2018) Detection of widespread horizontal pleiotropy in causal relationships inferred from Mendelian randomization between complex traits and diseases. Nature Genetics 50:693-698.

## Algorithm

MR-PRESSO performs three main tests:

### 1. Global Test
Tests for the presence of horizontal pleiotropy by comparing the observed residual sum of squares to a null distribution generated via simulation.

**Null hypothesis**: No horizontal pleiotropy is present

**Method**:
- Computes IVW estimate and residuals for each SNP
- Calculates observed residual sum of squares (RSS)
- Simulates null distribution by drawing from normal distribution centered on IVW estimate
- P-value = proportion of simulated RSS >= observed RSS

**Interpretation**:
- Low p-value (< 0.05) suggests presence of horizontal pleiotropy

### 2. Outlier Test
Identifies specific SNPs with extreme residuals that may be violating instrumental variable assumptions.

**Method**:
- For each SNP, compute leave-one-out IVW estimate
- Calculate residual for excluded SNP
- Simulate null distribution for each SNP's residual
- Apply Bonferroni correction (α = 0.05 / n_snps)

**Interpretation**:
- SNPs with p-value < (0.05 / n_snps) are flagged as outliers

### 3. Distortion Test
Tests whether removing outliers significantly changes the causal estimate.

**Null hypothesis**: Original and corrected estimates are not significantly different

**Method**:
- Compute IVW estimate after removing outliers
- Calculate standard error of the difference
- Perform z-test for difference

**Interpretation**:
- Significant p-value indicates outliers were biasing the estimate
- Non-significant suggests outliers were not substantially distorting results

## Usage

### Basic Usage

```python
from pymr import mr_presso
import numpy as np

# Your GWAS data
beta_exp = np.array([0.1, 0.2, 0.15, ...])  # Exposure effects
se_exp = np.array([0.01, 0.02, 0.015, ...])  # Exposure SEs
beta_out = np.array([0.05, 0.10, 0.075, ...])  # Outcome effects
se_out = np.array([0.02, 0.03, 0.025, ...])  # Outcome SEs

# Run MR-PRESSO
result = mr_presso(beta_exp, se_exp, beta_out, se_out)

# Check results
print(f"Global test p-value: {result['global_test_pval']:.3f}")
print(f"Outliers detected: {result['outlier_indices']}")
print(f"Original beta: {result['original_beta']:.3f}")
print(f"Corrected beta: {result['corrected_beta']:.3f}")
```

### Parameters

- `beta_exp`: Effect sizes for exposure (numpy array)
- `se_exp`: Standard errors for exposure (numpy array)
- `beta_out`: Effect sizes for outcome (numpy array)
- `se_out`: Standard errors for outcome (numpy array)
- `n_simulations`: Number of simulations for null distribution (default: 10000)
- `outlier_test`: Whether to perform outlier detection (default: True)
- `distortion_test`: Whether to test for distortion (default: True)

### Return Values

The function returns a dictionary with:

- `global_test_pval`: P-value for presence of horizontal pleiotropy
- `outlier_indices`: List of detected outlier indices
- `corrected_beta`: IVW estimate after outlier removal
- `corrected_se`: Standard error after outlier removal
- `corrected_pval`: P-value after outlier removal
- `distortion_test_pval`: P-value for significant difference (NaN if no outliers)
- `original_beta`: Original IVW estimate
- `original_se`: Original IVW standard error
- `nsnp`: Number of SNPs

## Examples

See `examples/demo_presso.py` for complete working examples including:

1. Clean data without pleiotropy
2. Data with horizontal pleiotropy
3. Effect of simulation count on precision

## Interpretation Guidelines

### When to use MR-PRESSO

1. You have at least 3 SNPs (method requirement)
2. You suspect horizontal pleiotropy may be present
3. You want to identify specific outlier SNPs
4. You want a corrected estimate robust to pleiotropy

### Interpreting Results

**Global Test**:
- p < 0.05: Evidence of horizontal pleiotropy present
- p >= 0.05: No strong evidence of pleiotropy

**Outlier Test**:
- Empty list: No outliers detected
- Non-empty list: Specific SNPs violating IV assumptions

**Distortion Test**:
- p < 0.05: Removing outliers significantly changed estimate (bias was present)
- p >= 0.05: Estimate not substantially affected by outliers
- NaN: No outliers detected, test not applicable

**Recommendations**:
1. If global test significant AND outliers detected → Use corrected estimate
2. If global test significant but NO outliers → Consider other pleiotropy-robust methods (MR-Egger, Weighted Median)
3. If global test not significant → Standard IVW likely appropriate

## Computational Considerations

### Simulation Count
- Default: 10,000 simulations
- Faster: 1,000 simulations (less precise p-values)
- More precise: 50,000+ simulations (slower)

### Performance
- Computational complexity: O(n_snps × n_simulations)
- For n=50 SNPs with 10k simulations: ~1-2 seconds
- Outlier test is most computationally intensive (leave-one-out for each SNP)

### Reproducibility
Uses `np.random.RandomState()` which respects `np.random.seed()` for reproducibility:

```python
np.random.seed(42)
result1 = mr_presso(beta_exp, se_exp, beta_out, se_out)

np.random.seed(42)
result2 = mr_presso(beta_exp, se_exp, beta_out, se_out)
# result1 == result2
```

## Limitations

1. **Requires multiple SNPs**: Minimum 3 SNPs (more is better)
2. **Simulation-based**: Results can vary slightly between runs (use more simulations for stability)
3. **Assumes IVW model**: Corrected estimate uses IVW after outlier removal
4. **Bonferroni correction**: Conservative for outlier detection (may miss weak outliers)
5. **No directional pleiotropy test**: Only detects presence, not direction (use MR-Egger for that)

## Comparison with Other Methods

| Method | Detects Pleiotropy | Identifies Outliers | Corrects Estimate | Robust to 50% Invalid |
|--------|-------------------|---------------------|-------------------|----------------------|
| MR-PRESSO | ✓ | ✓ | ✓ | ✗ |
| MR-Egger | ✓ | ✗ | ✓ | ✗ |
| Weighted Median | ✗ | ✗ | ✓ | ✓ |
| IVW | ✗ | ✗ | ✗ | ✗ |

**Use MR-PRESSO when**:
- You want to identify specific problematic SNPs
- You suspect a small number of pleiotropic variants
- You want a data-driven outlier removal approach

**Use MR-Egger when**:
- You suspect widespread directional pleiotropy
- You want to test for pleiotropy via intercept
- You don't need to identify specific outliers

**Use Weighted Median when**:
- You suspect up to 50% of SNPs may be invalid
- You want a robust estimate without removing SNPs
- You have enough SNPs for stable median estimation
