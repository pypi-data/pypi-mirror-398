# LD-Based Clumping

PyMR provides LD-based clumping functionality using 1000 Genomes reference panels via the LDlink API. This is essential for ensuring instrument independence in Mendelian Randomization studies.

## Why Clump SNPs?

In Mendelian Randomization, one key assumption is that instrumental variables (genetic variants) are independent. However, nearby SNPs on the same chromosome are often in linkage disequilibrium (LD) - they're correlated due to physical proximity and population history.

Clumping removes redundant SNPs that are in LD, keeping only independent variants. This:

1. **Preserves statistical validity**: Ensures instruments are truly independent
2. **Reduces bias**: Minimizes winner's curse and weak instrument bias
3. **Improves efficiency**: Removes redundant information
4. **Follows best practices**: Standard in published MR studies

## Quick Start

### Installation Requirements

You need a free LDlink API token:
1. Visit https://ldlink.nih.gov/?tab=apiaccess
2. Request a token (instant, no approval needed)
3. Store in environment variable: `export LDLINK_TOKEN=your_token`

### Basic Example

```python
import pandas as pd
from pymr import ld_clump

# Load GWAS summary statistics
gwas = pd.DataFrame({
    "SNP": ["rs1", "rs2", "rs3", "rs4", "rs5"],
    "chr": [1, 1, 1, 2, 2],
    "pos": [1000000, 1005000, 1020000, 2000000, 2008000],
    "pval": [1e-8, 5e-7, 1e-6, 2e-8, 3e-7],
    "beta": [0.1, 0.08, 0.05, 0.12, 0.09],
})

# Clump to independent SNPs
clumped = ld_clump(
    gwas,
    r2_threshold=0.001,  # Clump SNPs with r² > 0.001
    kb_window=10000,      # Within 10Mb windows
    population="EUR",     # European ancestry
    token="your_token",
)

print(f"Original: {len(gwas)} SNPs")
print(f"Independent: {len(clumped)} SNPs")
```

## Function Reference

### `ld_clump()`

Clump SNPs based on linkage disequilibrium.

**Parameters:**

- `snps` (DataFrame): GWAS summary statistics with required columns:
  - `SNP`: rsID (e.g., "rs1234")
  - `chr`: Chromosome number
  - `pos`: Base pair position
  - `pval`: Association p-value

- `r2_threshold` (float, default=0.01): LD threshold. SNPs with r² > this are clumped together
  - Standard: 0.001 (very strict)
  - Relaxed: 0.01
  - Lenient: 0.1

- `kb_window` (int, default=10000): Distance window in kilobases
  - Only SNPs within this distance are considered for clumping
  - Standard: 10000 (10Mb)
  - Chromosome-specific: 1000 (1Mb) for fine-mapping

- `population` (str, default="EUR"): 1000 Genomes population
  - `"EUR"`: European
  - `"EAS"`: East Asian
  - `"AFR"`: African
  - `"AMR"`: American (admixed)
  - `"SAS"`: South Asian
  - `"ALL"`: All populations combined

- `token` (str, required): LDlink API token

**Returns:**

DataFrame with independent index SNPs (subset of input with same columns)

**Example:**

```python
# Strict clumping (recommended for MR)
instruments = ld_clump(
    gwas,
    r2_threshold=0.001,
    kb_window=10000,
    population="EUR",
    token=token,
)
```

### `get_ld_matrix()`

Get pairwise LD matrix for a list of SNPs.

**Parameters:**

- `snps` (list): List of SNP rsIDs (e.g., `["rs1", "rs2", "rs3"]`)
- `population` (str, default="EUR"): 1000 Genomes population
- `token` (str, required): LDlink API token

**Returns:**

Symmetric DataFrame with r² values between all SNP pairs

**Example:**

```python
from pymr import get_ld_matrix

# Get LD between specific SNPs
ld_matrix = get_ld_matrix(
    ["rs1234", "rs5678", "rs9012"],
    population="EUR",
    token=token,
)

print(ld_matrix.loc["rs1234", "rs5678"])  # r² between rs1234 and rs5678
```

## Usage Patterns

### Standard MR Workflow

```python
from pymr import ld_clump, harmonize, MR
import pandas as pd

# 1. Load exposure GWAS
exposure = pd.read_csv("bmi_gwas.tsv.gz", sep="\t")

# 2. Filter to genome-wide significant
significant = exposure[exposure["pval"] < 5e-8]

# 3. Clump to independent instruments
instruments = ld_clump(
    significant,
    r2_threshold=0.001,
    kb_window=10000,
    population="EUR",
    token=token,
)

# 4. Extract from outcome
outcome = pd.read_csv("diabetes_gwas.tsv.gz", sep="\t")
outcome_snps = outcome[outcome["SNP"].isin(instruments["SNP"])]

# 5. Harmonize
harmonized = harmonize(instruments, outcome_snps)

# 6. Run MR
mr = MR(harmonized)
results = mr.run()
```

### Multi-Ancestry Analysis

```python
# Analyze each ancestry separately
populations = {
    "EUR": european_gwas,
    "EAS": east_asian_gwas,
    "AFR": african_gwas,
}

results = {}
for pop, gwas in populations.items():
    clumped = ld_clump(
        gwas,
        population=pop,  # Use matching ancestry
        token=token,
    )
    results[pop] = clumped
```

### Custom LD Threshold

```python
# Very strict (for large GWAS)
strict = ld_clump(gwas, r2_threshold=0.0001, token=token)

# Standard
standard = ld_clump(gwas, r2_threshold=0.001, token=token)

# Relaxed (for smaller GWAS)
relaxed = ld_clump(gwas, r2_threshold=0.01, token=token)

print(f"Strict: {len(strict)} SNPs")
print(f"Standard: {len(standard)} SNPs")
print(f"Relaxed: {len(relaxed)} SNPs")
```

## Algorithm Details

PyMR uses a greedy clumping algorithm:

1. **Sort SNPs by p-value** (most significant first)
2. **Select top SNP** as index SNP
3. **Calculate LD** with remaining SNPs using 1000 Genomes
4. **Remove SNPs in LD** (r² > threshold and within kb window)
5. **Repeat** with remaining SNPs until none left

This ensures the most significant SNP in each LD block is retained.

### Position-Based Filtering

SNPs are only clumped if they're:
- On the same chromosome
- Within `kb_window` kilobases of each other
- In LD (r² > `r2_threshold`)

### Chromosome Handling

Clumping is performed separately for each chromosome, then results are combined. This is more efficient than calculating LD across the entire genome.

## Best Practices

### Choosing r² Threshold

| Use Case | r² Threshold | Rationale |
|----------|--------------|-----------|
| Large GWAS (>100k samples) | 0.0001 - 0.001 | Strict independence |
| Standard MR | 0.001 | Recommended default |
| Small GWAS (<50k samples) | 0.01 | Preserve power |
| Fine-mapping | 0.1 | Keep more variants |

### Choosing kb Window

| Use Case | Window (kb) | Rationale |
|----------|-------------|-----------|
| Standard MR | 10000 (10Mb) | Standard practice |
| Trans-ethnic | 5000 (5Mb) | LD decays faster |
| Fine-mapping | 1000 (1Mb) | Localized analysis |

### Choosing Population

**Match your GWAS ancestry:**
- European GWAS → `population="EUR"`
- East Asian GWAS → `population="EAS"`
- African GWAS → `population="AFR"`
- Multi-ancestry → Use `"ALL"` or analyze separately

**Why it matters:**
LD patterns differ dramatically across ancestries. Using the wrong reference panel can:
- Fail to clump truly correlated SNPs
- Over-clump independent SNPs
- Bias effect estimates

## Performance Notes

### API Rate Limits

LDlink has usage limits:
- **Free tier**: ~1000 requests/day
- **Chromosome-based**: Each `ld_clump()` call makes 1 request per chromosome

For large-scale analyses (>10 GWAS per day), consider:
1. Caching results locally
2. Using pre-computed LD matrices
3. Running PLINK locally with 1000 Genomes VCF files

### Caching Strategy

```python
import pickle
import os

def cached_ld_clump(gwas, cache_file="ld_clumped.pkl", **kwargs):
    """Clump with caching to avoid repeated API calls."""
    if os.path.exists(cache_file):
        print(f"Loading cached results from {cache_file}")
        return pickle.load(open(cache_file, "rb"))

    print("Clumping (this may take a minute)...")
    clumped = ld_clump(gwas, **kwargs)

    pickle.dump(clumped, open(cache_file, "wb"))
    return clumped
```

## Troubleshooting

### "LDlink API request failed"

**Cause**: Invalid token, rate limit, or network issue

**Solution**:
```python
# Check token
import os
print(os.environ.get("LDLINK_TOKEN"))

# Verify token works
from pymr import get_ld_matrix
ld = get_ld_matrix(["rs1234"], token=your_token)
```

### "SNPs not found in LD reference"

**Cause**: SNP not in 1000 Genomes reference panel

**Solution**: This is normal for rare variants. PyMR will:
- Print a warning listing missing SNPs
- Continue clumping with available SNPs
- Keep missing SNPs (assume independent)

### "Missing required columns"

**Cause**: Input DataFrame missing `SNP`, `chr`, `pos`, or `pval`

**Solution**: Ensure all required columns are present:
```python
required = ["SNP", "chr", "pos", "pval"]
missing = [col for col in required if col not in gwas.columns]
if missing:
    print(f"Missing columns: {missing}")
```

## Comparison with Other Tools

| Tool | Method | Reference | Speed | Ancestry |
|------|--------|-----------|-------|----------|
| **PyMR** | LDlink API | 1000G | Moderate | All 1000G |
| PLINK | Local VCF | Custom | Fast | Custom |
| TwoSampleMR | IEU API | 1000G | Fast | EUR only |

**PyMR advantages:**
- No local reference data needed
- Multiple ancestries supported
- Pure Python (no external dependencies)
- Reproducible (same reference for all users)

**When to use PLINK instead:**
- Analyzing >100 GWAS (rate limits)
- Need custom reference panel
- Already have 1000G VCF locally

## See Also

- [LDlink documentation](https://ldlink.nih.gov/LDlink/Help/LDmatrix)
- [1000 Genomes Project](https://www.internationalgenome.org/)
- [PLINK clumping](https://www.cog-genomics.org/plink/1.9/postproc#clump)
