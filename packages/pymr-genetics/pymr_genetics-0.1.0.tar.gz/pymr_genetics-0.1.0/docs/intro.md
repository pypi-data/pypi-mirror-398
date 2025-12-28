# PyMR: Mendelian Randomization in Python

PyMR is a modern, test-driven Python package for Mendelian Randomization (MR) analysis.

## What is Mendelian Randomization?

Mendelian Randomization uses genetic variants as instrumental variables to estimate causal effects of exposures on outcomes. Because genetic variants are assigned at conception (like a randomized trial), MR can provide causal estimates even from observational data.

```{figure} images/mr-concept.png
---
width: 80%
name: mr-concept
---
The MR triangle: genetic variants (G) affect exposure (X) which affects outcome (Y). If G only affects Y through X, we can estimate the causal effect of X on Y.
```

## Key Features

- **Multiple MR methods**: IVW, weighted median, MR-Egger, mode-based
- **Sensitivity analyses**: Heterogeneity tests, MR-PRESSO, leave-one-out
- **Data harmonization**: Automatic allele alignment and strand flipping
- **GWAS integration**: Load from Pan-UKB, IEU OpenGWAS, or custom files
- **Pure Python**: No external dependencies like PLINK

## Quick Example

```python
from pymr import MR, load_gwas, harmonize

# Load data
exposure = load_gwas("bmi_gwas.tsv.gz")
outcome = load_gwas("diabetes_gwas.tsv.gz")

# Harmonize alleles
data = harmonize(exposure, outcome)

# Run MR
mr = MR(data)
results = mr.run()
print(results)
```

## Installation

```bash
pip install pymr
```

## Citation

If you use PyMR in your research, please cite:

```bibtex
@software{pymr2025,
  author = {Ghenis, Max},
  title = {PyMR: Mendelian Randomization in Python},
  year = {2025},
  url = {https://github.com/maxghenis/pymr}
}
```

## License

PyMR is released under the MIT License.
