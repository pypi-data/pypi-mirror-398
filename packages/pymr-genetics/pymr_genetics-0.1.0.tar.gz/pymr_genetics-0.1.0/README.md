# PyMR: Mendelian Randomization in Python

[![Tests](https://github.com/maxghenis/pymr/actions/workflows/test.yml/badge.svg)](https://github.com/maxghenis/pymr/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/maxghenis/pymr/branch/main/graph/badge.svg)](https://codecov.io/gh/maxghenis/pymr)
[![PyPI](https://img.shields.io/pypi/v/pymr.svg)](https://pypi.org/project/pymr/)
[![Documentation](https://img.shields.io/badge/docs-jupyter--book-blue)](https://maxghenis.github.io/pymr)

A modern, test-driven Python package for Mendelian Randomization (MR) analysis.

## Features

- **Multiple MR methods**: IVW, weighted median, MR-Egger, mode-based
- **Bayesian MR**: Full posterior inference, Bayes factors, model comparison
- **Sensitivity analyses**: Heterogeneity tests, MR-PRESSO, leave-one-out
- **Data harmonization**: Automatic allele alignment and strand flipping
- **GWAS integration**: Load from Pan-UKB, IEU OpenGWAS, or custom files
- **Visualization**: Forest plots, scatter plots, funnel plots, posterior distributions
- **No external dependencies**: Pure Python (no PLINK, PyMC, or Stan required)

## Installation

```bash
pip install pymr
```

## Quick Start

### Frequentist MR

```python
from pymr import MR, load_gwas

# Load GWAS summary statistics
exposure = load_gwas("bmi_gwas.tsv.gz")
outcome = load_gwas("diabetes_gwas.tsv.gz")

# Run MR analysis
mr = MR(exposure, outcome)
results = mr.run()

print(results)
#              method      beta        se        OR      pval  nsnp
# 0               IVW  0.924740  0.030497  2.521214  5.83e-202   192
# 1   Weighted Median  1.039266  0.021565  2.827140  0.00e+00    192
# 2          MR-Egger  0.911587  0.075401  2.488269  1.19e-33    192
```

### Bayesian MR

```python
from pymr import BayesianMR

# Run Bayesian MR with full posterior inference
bmr = BayesianMR(harmonized_data, prior_mean=0, prior_sd=1)
bmr.sample(n_samples=10000, n_chains=4, warmup=1000)

# Get posterior summary
summary = bmr.summary()
print(f"Effect: {summary['mean']:.3f} [{summary['ci_lower']:.3f}, {summary['ci_upper']:.3f}]")
print(f"Bayes Factor: {bmr.bayes_factor(null_value=0):.2f}")

# Visualize posterior
bmr.plot_posterior()
```

See [docs/bayesian_mr.md](docs/bayesian_mr.md) for comprehensive Bayesian MR documentation.

## Development

```bash
# Clone repository
git clone https://github.com/maxghenis/pymr.git
cd pymr

# Install in development mode
pip install -e ".[dev,docs]"

# Run tests
pytest

# Build documentation
jupyter-book build docs
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

MIT License - see [LICENSE](LICENSE) for details.
