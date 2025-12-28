"""Example demonstrating PyMR visualization functions.

This script shows how to create publication-ready plots from MR analysis results.
"""

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

# Generate simulated harmonized GWAS data
np.random.seed(42)
n_snps = 50

# Simulate exposure effects (e.g., BMI)
beta_exp = np.random.normal(0.1, 0.02, n_snps)
se_exp = np.abs(np.random.normal(0.01, 0.002, n_snps))

# Simulate outcome effects (e.g., diabetes) with true causal effect of 0.5
true_causal_effect = 0.5
beta_out = true_causal_effect * beta_exp + np.random.normal(0, 0.01, n_snps)
se_out = np.abs(np.random.normal(0.02, 0.005, n_snps))

# Create harmonized data
harmonized = pd.DataFrame({
    "SNP": [f"rs{i}" for i in range(n_snps)],
    "beta_exp": beta_exp,
    "se_exp": se_exp,
    "beta_out": beta_out,
    "se_out": se_out,
})

# Run MR analysis
mr = MR(harmonized)
results = mr.run()
loo_results = mr.leave_one_out()

print("MR Results:")
print(results[["method", "beta", "se", "pval", "OR", "OR_lci", "OR_uci"]])
print()

# Create all plots
print("Creating plots...")

# 1. Forest plot - compare estimates across methods
fig1 = forest_plot(results)
fig1.savefig("mr_forest_plot.png", dpi=300, bbox_inches="tight")
print("✓ Forest plot saved to mr_forest_plot.png")

# 2. Scatter plot - SNP effects with IVW regression line
fig2 = scatter_plot(harmonized, method="IVW")
fig2.savefig("mr_scatter_plot.png", dpi=300, bbox_inches="tight")
print("✓ Scatter plot saved to mr_scatter_plot.png")

# 3. Funnel plot - assess publication bias
fig3 = funnel_plot(harmonized)
fig3.savefig("mr_funnel_plot.png", dpi=300, bbox_inches="tight")
print("✓ Funnel plot saved to mr_funnel_plot.png")

# 4. Leave-one-out plot - sensitivity analysis
fig4 = leave_one_out_plot(loo_results)
fig4.savefig("mr_loo_plot.png", dpi=300, bbox_inches="tight")
print("✓ Leave-one-out plot saved to mr_loo_plot.png")

# 5. Radial plot - identify outliers
fig5 = radial_plot(harmonized)
fig5.savefig("mr_radial_plot.png", dpi=300, bbox_inches="tight")
print("✓ Radial plot saved to mr_radial_plot.png")

print()
print("All plots created successfully!")
print("These plots are publication-ready and can be used in academic papers.")
