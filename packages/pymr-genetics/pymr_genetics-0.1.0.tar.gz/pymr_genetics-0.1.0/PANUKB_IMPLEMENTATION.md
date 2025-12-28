# Pan-UKB Direct Access Implementation

## Overview

This document describes the implementation of Pan-UKB direct access in PyMR, enabling users to load GWAS summary statistics from the Pan-UK Biobank project directly without manual downloads.

## Implementation Date

December 24, 2024

## What is Pan-UKB?

Pan-UKB (Pan-ancestry analysis of UK Biobank) provides pre-computed GWAS for thousands of phenotypes across multiple ancestry groups:
- EUR (European)
- AFR (African)
- AMR (Admixed American)
- CSA (Central/South Asian)
- EAS (East Asian)
- MID (Middle Eastern)

Reference: https://pan.ukbb.broadinstitute.org/

## Features Implemented

### 1. List Available Phenotypes

```python
from pymr import panukb_list_phenotypes

# Get all available phenotypes
phenotypes = panukb_list_phenotypes()
print(phenotypes[["phenocode", "description", "trait_type"]].head())
```

Returns a DataFrame with:
- `phenocode`: UK Biobank field ID
- `description`: Human-readable trait name
- `trait_type`: continuous, binary, categorical, etc.
- `n_cases`, `n_controls`: Sample sizes
- Other metadata

### 2. Search Phenotypes by Keyword

```python
from pymr import panukb_search

# Search for BMI-related phenotypes (case-insensitive)
bmi_phenotypes = panukb_search("BMI")
print(bmi_phenotypes[["phenocode", "description"]])
```

### 3. Load GWAS Summary Statistics

```python
from pymr import panukb_load_gwas

# Load BMI GWAS for Europeans
bmi_gwas = panukb_load_gwas("21001", ancestry="EUR")

# Load height GWAS for Africans
height_gwas = panukb_load_gwas("50", ancestry="AFR")
```

Returns a DataFrame with standardized columns:
- `chr`, `pos`: Chromosome and position
- `rsid`: SNP identifier
- `ea`, `nea`: Effect and non-effect alleles
- `beta`, `se`: Effect size and standard error
- `pval`: P-value
- `eaf`: Effect allele frequency

## Technical Details

### Data Source

- **Manifest URL**: `https://pan-ukb-us-east-1.s3.amazonaws.com/sumstats_release/phenotype_manifest.tsv.bgz`
- **GWAS Files**: `https://pan-ukb-us-east-1.s3.amazonaws.com/sumstats_release/{trait_type}-{phenocode}-both_sexes-{ancestry}.tsv.bgz`

### File Handling

- Files are served as bgzip-compressed TSV files
- PyMR automatically decompresses using `gzip.decompress()`
- Column names are standardized to PyMR conventions for compatibility with other functions

### Column Mapping

Pan-UKB columns → PyMR standard columns:
- `snp` → `rsid`
- `alt` → `ea` (effect allele)
- `ref` → `nea` (non-effect allele)
- `AF` → `eaf` (effect allele frequency)

## Test Coverage

All functions are fully tested with mocked API responses:

1. `test_panukb_list_phenotypes` - Verify phenotype listing
2. `test_panukb_search` - Verify keyword search
3. `test_panukb_search_case_insensitive` - Verify case-insensitive search
4. `test_panukb_load_gwas_basic` - Verify GWAS loading
5. `test_panukb_load_gwas_default_ancestry` - Verify EUR is default ancestry
6. `test_panukb_load_gwas_invalid_phenotype` - Verify error handling

All tests pass ✓

## Example Usage

See `/Users/maxghenis/pymr/examples/panukb_example.py` for comprehensive examples including:
- Listing and searching phenotypes
- Loading GWAS for single and multiple ancestries
- Complete MR workflow with Pan-UKB data
- Memory-efficient strategies for large files

## Integration with PyMR Workflow

Pan-UKB data integrates seamlessly with existing PyMR functions:

```python
from pymr import panukb_load_gwas, harmonize, MR

# 1. Load exposure and outcome GWAS
bmi_gwas = panukb_load_gwas("21001", ancestry="EUR")  # BMI
t2d_gwas = panukb_load_gwas("E11", ancestry="EUR")   # Type 2 Diabetes

# 2. Filter to genome-wide significant variants
instruments = bmi_gwas[bmi_gwas["pval"] < 5e-8]

# 3. Harmonize
harmonized = harmonize(instruments, t2d_gwas)

# 4. Run MR
mr = MR(harmonized)
results = mr.run()
```

## Files Modified/Created

### Modified Files
1. `/Users/maxghenis/pymr/src/pymr/api.py`
   - Added `PANUKB_MANIFEST_URL` and `PANUKB_BASE_URL` constants
   - Implemented `panukb_list_phenotypes()`
   - Implemented `panukb_search()`
   - Implemented `panukb_load_gwas()`

2. `/Users/maxghenis/pymr/src/pymr/__init__.py`
   - Exported new Pan-UKB functions

3. `/Users/maxghenis/pymr/tests/test_api.py`
   - Added `TestPanUKBFunctions` test class with 6 test methods

4. `/Users/maxghenis/pymr/docs/roadmap.md`
   - Checked off "Pan-UKB direct access" as completed

### Created Files
1. `/Users/maxghenis/pymr/examples/panukb_example.py`
   - Comprehensive example demonstrating all Pan-UKB features

## Performance Considerations

- **File Sizes**: Pan-UKB GWAS files can be several GB uncompressed
- **Recommendation**: Filter to genome-wide significant variants (p < 5e-8) immediately after loading
- **Memory Management**: Delete full GWAS DataFrame after filtering to free memory

## Future Enhancements

Potential improvements for future versions:

1. **Caching**: Cache downloaded GWAS files locally to avoid re-downloading
2. **Chunked Loading**: Support loading large files in chunks
3. **LD Clumping**: Integrate with LD clumping to reduce instrument count
4. **Multi-ancestry MR**: Helper functions for cross-ancestry MR analysis
5. **Phenotype Recommendations**: Suggest related phenotypes for mediation analysis

## References

- Pan-UKB Browser: https://pan.ukbb.broadinstitute.org/
- Pan-UKB Paper: https://doi.org/10.1016/j.cell.2020.10.035
- PyMR Documentation: https://maxghenis.github.io/pymr

## TDD Approach

This implementation followed Test-Driven Development:

1. **Red**: Wrote failing tests first
2. **Green**: Implemented minimal code to make tests pass
3. **Refactor**: (Not needed - implementation was clean on first pass)

All tests passed on first implementation after fixing test mocking setup.
