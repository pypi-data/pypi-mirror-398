# PyMR Visualization Guide

PyMR provides publication-ready visualization functions for Mendelian Randomization analyses. All plots are created with matplotlib/seaborn and follow academic styling conventions.

## Quick Start

```python
from pymr import MR
from pymr.plots import forest_plot, scatter_plot, funnel_plot

# Run MR analysis
mr = MR(harmonized_data)
results = mr.run()

# Create forest plot
fig = forest_plot(results)
fig.savefig("forest.png", dpi=300, bbox_inches="tight")
```

## Available Plots

### 1. Forest Plot

Displays MR estimates and confidence intervals across multiple methods.

```python
from pymr.plots import forest_plot

fig = forest_plot(
    results,           # DataFrame from MR.run()
    estimate_col="beta",
    se_col="se",
    color="#2E86AB"
)
```

**Use case**: Compare estimates from different MR methods (IVW, MR-Egger, Weighted Median, etc.)

**Interpretation**:
- Points show causal estimates
- Error bars show 95% confidence intervals
- Dashed line at zero represents null effect
- Consistency across methods strengthens causal inference

---

### 2. Scatter Plot

Plots SNP effects on exposure vs outcome with regression line.

```python
from pymr.plots import scatter_plot

fig = scatter_plot(
    harmonized,        # Harmonized exposure-outcome data
    method="IVW",      # "IVW", "MR-Egger", or "Weighted Median"
    point_color="#A23B72",
    line_color="#2E86AB"
)
```

**Use case**: Visualize individual SNP contributions to the causal estimate

**Interpretation**:
- Each point represents one SNP
- Error bars show 95% CIs for SNP effects
- Regression line slope = causal estimate
- Points deviating from line may indicate pleiotropy

---

### 3. Funnel Plot

Assesses publication bias and pleiotropy using per-SNP estimates.

```python
from pymr.plots import funnel_plot

fig = funnel_plot(
    harmonized,
    point_color="#A23B72",
    line_color="#2E86AB"
)
```

**Use case**: Detect publication bias and directional pleiotropy

**Interpretation**:
- Vertical line shows IVW estimate
- Funnel shape shows expected 95% CI region
- Asymmetry suggests bias or pleiotropy
- Points outside funnel may be outliers

---

### 4. Leave-One-Out Plot

Shows sensitivity analysis results when each SNP is excluded.

```python
from pymr.plots import leave_one_out_plot

loo_results = mr.leave_one_out()
fig = leave_one_out_plot(
    loo_results,
    estimate_col="beta",
    se_col="se",
    max_snps=30  # Limit displayed SNPs
)
```

**Use case**: Identify influential SNPs driving the causal estimate

**Interpretation**:
- Each point shows estimate with that SNP excluded
- Dashed line shows mean estimate
- Large changes indicate influential SNPs
- Consistent estimates suggest robustness

---

### 5. Radial Plot

Galbraith plot for identifying outliers and assessing heterogeneity.

```python
from pymr.plots import radial_plot

fig = radial_plot(
    harmonized,
    point_color="#A23B72",
    line_color="#2E86AB"
)
```

**Use case**: Detect outlier SNPs and visualize heterogeneity

**Interpretation**:
- Points are SNPs weighted by precision
- Solid line shows IVW estimate through origin
- Dashed lines show 95% CI
- Points far from line are potential outliers

**Reference**: Bowden J, et al. (2018). Int J Epidemiol, 47(6):2100-2114.

---

## Customization

All plotting functions support:

### Custom Axes

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

forest_plot(results, ax=axes[0, 0])
scatter_plot(harmonized, ax=axes[0, 1])
funnel_plot(harmonized, ax=axes[1, 0])
radial_plot(harmonized, ax=axes[1, 1])

fig.tight_layout()
fig.savefig("mr_summary.png", dpi=300, bbox_inches="tight")
```

### Custom Colors

```python
# Use custom color schemes
fig = forest_plot(results, color="#319795")  # Teal
fig = scatter_plot(harmonized, point_color="#E63946", line_color="#1D3557")
```

### Export Options

```python
# High-resolution PNG
fig.savefig("plot.png", dpi=300, bbox_inches="tight")

# PDF for publications
fig.savefig("plot.pdf", bbox_inches="tight")

# SVG for editing
fig.savefig("plot.svg", bbox_inches="tight")

# Multiple formats
for fmt in ["png", "pdf", "svg"]:
    fig.savefig(f"plot.{fmt}", dpi=300, bbox_inches="tight")
```

---

## Complete Example

```python
import numpy as np
import pandas as pd
from pymr import MR
from pymr.plots import (
    forest_plot,
    scatter_plot,
    funnel_plot,
    leave_one_out_plot,
    radial_plot,
)

# Load or create harmonized data
harmonized = pd.DataFrame({
    "SNP": [f"rs{i}" for i in range(50)],
    "beta_exp": np.random.normal(0.1, 0.02, 50),
    "se_exp": np.abs(np.random.normal(0.01, 0.002, 50)),
    "beta_out": np.random.normal(0.05, 0.02, 50),
    "se_out": np.abs(np.random.normal(0.02, 0.005, 50)),
})

# Run MR analysis
mr = MR(harmonized)
results = mr.run()
loo_results = mr.leave_one_out()

# Create all plots
fig1 = forest_plot(results)
fig1.savefig("forest.png", dpi=300, bbox_inches="tight")

fig2 = scatter_plot(harmonized, method="IVW")
fig2.savefig("scatter.png", dpi=300, bbox_inches="tight")

fig3 = funnel_plot(harmonized)
fig3.savefig("funnel.png", dpi=300, bbox_inches="tight")

fig4 = leave_one_out_plot(loo_results)
fig4.savefig("loo.png", dpi=300, bbox_inches="tight")

fig5 = radial_plot(harmonized)
fig5.savefig("radial.png", dpi=300, bbox_inches="tight")
```

---

## Style Guidelines

PyMR visualizations follow these principles:

1. **Academic styling**: Clean, professional appearance suitable for publication
2. **High resolution**: Default 100 DPI, export at 300+ DPI for print
3. **Colorblind-friendly**: Default colors chosen for accessibility
4. **Labeled axes**: Clear, descriptive axis labels with units
5. **Legends**: Informative legends with method details
6. **Grid lines**: Subtle gridlines for readability

---

## Tips for Publication

1. **Use vector formats** (PDF, SVG) when possible for crisp scaling
2. **Export at 300 DPI** minimum for print journals
3. **Check journal style guides** for specific requirements
4. **Combine plots** in multi-panel figures for comprehensive results
5. **Include uncertainty** - always show confidence intervals
6. **Caption thoroughly** - describe methods, sample sizes, and interpretation

---

## API Reference

All functions return `matplotlib.figure.Figure` objects and accept optional `ax` parameters for subplot integration.

### forest_plot
```python
forest_plot(
    results: pd.DataFrame,
    ax: Axes | None = None,
    estimate_col: str = "beta",
    se_col: str = "se",
    method_col: str = "method",
    color: str = "#2E86AB"
) -> Figure
```

### scatter_plot
```python
scatter_plot(
    harmonized: pd.DataFrame,
    method: Literal["IVW", "MR-Egger", "Weighted Median"] = "IVW",
    ax: Axes | None = None,
    point_color: str = "#A23B72",
    line_color: str = "#2E86AB"
) -> Figure
```

### funnel_plot
```python
funnel_plot(
    harmonized: pd.DataFrame,
    ax: Axes | None = None,
    point_color: str = "#A23B72",
    line_color: str = "#2E86AB"
) -> Figure
```

### leave_one_out_plot
```python
leave_one_out_plot(
    loo_results: pd.DataFrame,
    ax: Axes | None = None,
    estimate_col: str = "beta",
    se_col: str = "se",
    snp_col: str = "excluded_snp",
    color: str = "#2E86AB",
    max_snps: int = 30
) -> Figure
```

### radial_plot
```python
radial_plot(
    harmonized: pd.DataFrame,
    ax: Axes | None = None,
    point_color: str = "#A23B72",
    line_color: str = "#2E86AB"
) -> Figure
```

---

## Troubleshooting

**Issue**: Plots look pixelated
- **Solution**: Increase DPI: `fig.savefig("plot.png", dpi=300)`

**Issue**: Text is too small/large
- **Solution**: Adjust figure size: `fig, ax = plt.subplots(figsize=(10, 8))`

**Issue**: Colors don't match journal style
- **Solution**: Use custom colors: `forest_plot(results, color="#your_color")`

**Issue**: Too many SNPs in leave-one-out plot
- **Solution**: Use `max_snps` parameter: `leave_one_out_plot(loo, max_snps=20)`

---

## Further Reading

- [Hemani et al. (2018) - MR visualization best practices](https://doi.org/10.7554/eLife.34408)
- [Bowden et al. (2018) - Radial plots](https://doi.org/10.1093/ije/dyy101)
- [Burgess & Thompson (2015) - MR methods book](https://www.crcpress.com/Mendelian-Randomization-Methods-for-Using-Genetic-Variants-in-Causal-Estimation/Burgess-Thompson/p/book/9781466573178)
