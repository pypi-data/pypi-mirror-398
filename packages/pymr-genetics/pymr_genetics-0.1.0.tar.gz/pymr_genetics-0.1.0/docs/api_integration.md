# IEU OpenGWAS API Integration

PyMR now includes built-in integration with the [IEU OpenGWAS database](https://gwas.mrcieu.ac.uk/), providing programmatic access to over 50,000 curated GWAS summary statistics.

## Features

- **Fetch genetic instruments** with automatic LD clumping
- **Look up SNPs** in outcome datasets with optional LD proxy support
- **Search and browse** available GWAS studies
- **Seamless integration** with PyMR's harmonization and MR analysis functions

## Authentication

Most API operations require a JSON Web Token (JWT) for authentication:

1. Visit https://api.opengwas.io/profile/
2. Sign in and generate a token (valid for 14 days)
3. Set the environment variable:

```bash
export OPENGWAS_JWT="your_token_here"
```

Or pass the token directly when calling functions:

```python
instruments = get_instruments("ieu-a-2", jwt="your_token_here")
```

## Quick Start

```python
from pymr import get_instruments, get_outcome, harmonize, MR

# 1. Get genetic instruments for BMI
instruments = get_instruments("ieu-a-2")  # BMI GWAS
print(f"Found {len(instruments)} instruments")

# 2. Extract SNP list
snp_list = instruments["rsid"].tolist()

# 3. Look up SNPs in Type 2 Diabetes outcome
outcome = get_outcome("ieu-a-7", snp_list)

# 4. Harmonize and run MR analysis
# (This part uses existing PyMR functionality)
# harmonized = harmonize(instruments, outcome)
# mr = MR(harmonized)
# results = mr.run()
```

## Available Functions

### `get_instruments(exposure_id, p_threshold=5e-8, ...)`

Fetch genome-wide significant genetic instruments with LD clumping.

**Parameters:**
- `exposure_id` (str): GWAS dataset ID (e.g., "ieu-a-2")
- `p_threshold` (float): P-value threshold (default: 5e-8)
- `clump` (bool): Perform LD clumping (default: True)
- `r2` (float): Clumping r² threshold (default: 0.001)
- `kb` (int): Clumping window in kb (default: 10000)
- `jwt` (str, optional): Authentication token

**Returns:** DataFrame with columns: rsid, chr, position, ea, nea, beta, se, pval, eaf

**Example:**
```python
# Standard GWAS instrument selection
instruments = get_instruments("ieu-a-2")

# Custom threshold for smaller studies
instruments = get_instruments("ieu-a-95", p_threshold=1e-6)

# Stricter clumping parameters
instruments = get_instruments("ieu-a-2", r2=0.01, kb=500)
```

### `get_outcome(outcome_id, snps, proxies=False, ...)`

Look up specific SNPs in an outcome GWAS dataset.

**Parameters:**
- `outcome_id` (str): GWAS dataset ID
- `snps` (list): List of rsIDs to look up
- `proxies` (bool): Use LD proxies for missing SNPs (default: False)
- `jwt` (str, optional): Authentication token

**Returns:** DataFrame with association statistics

**Example:**
```python
snps = ["rs123", "rs456", "rs789"]
outcome = get_outcome("ieu-a-7", snps)

# With LD proxy lookup
outcome = get_outcome("ieu-a-7", snps, proxies=True)
```

### `search_gwas(query, ...)`

Search for GWAS datasets by keyword.

**Parameters:**
- `query` (str): Search term (e.g., "body mass index")
- `jwt` (str, optional): Authentication token

**Returns:** DataFrame with matching GWAS metadata

**Example:**
```python
# Search for diabetes studies
results = search_gwas("diabetes")
print(results[["id", "trait", "author", "sample_size"]])
```

### `list_gwas(...)`

List all available GWAS datasets.

**Parameters:**
- `jwt` (str, optional): Authentication token

**Returns:** DataFrame with all GWAS metadata

**Example:**
```python
all_gwas = list_gwas()
print(f"Total datasets: {len(all_gwas)}")
```

### `IEUClient`

Low-level client for custom API interactions.

**Example:**
```python
from pymr import IEUClient

client = IEUClient(jwt="your_token")

# Get top hits
tophits = client.get_tophits("ieu-a-2", pval=5e-8)

# Get associations
associations = client.get_associations("ieu-a-7", ["rs123", "rs456"])

# Get GWAS info
info = client.get_gwasinfo(query="diabetes")
```

## Common GWAS Dataset IDs

| ID | Trait | Author | Year | Sample Size |
|----|-------|--------|------|-------------|
| ieu-a-2 | Body mass index | Locke AE | 2015 | 339,224 |
| ieu-a-7 | Type 2 diabetes | Scott RA | 2017 | 159,208 |
| ieu-a-6 | Coronary heart disease | CARDIoGRAMplusC4D | 2015 | 184,305 |
| ieu-a-89 | Intelligence | Savage JE | 2018 | 269,867 |
| ieu-a-90 | Years of education | Okbay A | 2016 | 328,917 |

See the [OpenGWAS database](https://gwas.mrcieu.ac.uk/) for the full catalog.

## Error Handling

```python
import requests

try:
    instruments = get_instruments("invalid-id")
except requests.HTTPError as e:
    print(f"API error: {e}")
```

## Rate Limits

The API has tiered rate limits based on your account:
- **Trial**: 1,000 credits per 10 minutes
- **Standard**: 100,000 credits per 10 minutes
- **Commercial**: 100,000 credits per 10 minutes

See https://api.opengwas.io/profile/ for your current allowance.

## References

- **API Documentation**: https://gwas-api.mrcieu.ac.uk/
- **OpenGWAS Database**: https://gwas.mrcieu.ac.uk/
- **ieugwasr (R package)**: https://mrcieu.github.io/ieugwasr/
- **Hemani et al. (2018)**: [The MR-Base platform](https://doi.org/10.7554/eLife.34408)

## See Also

- [PyMR Harmonization Guide](harmonization.md)
- [MR Analysis Tutorial](mr_analysis.md)
- [API Example Script](../examples/api_example.py)
