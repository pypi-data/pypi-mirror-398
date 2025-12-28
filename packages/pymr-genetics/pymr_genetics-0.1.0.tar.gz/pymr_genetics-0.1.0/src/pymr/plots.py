"""Visualization functions for Mendelian Randomization analyses.

Publication-ready plots for MR results, including forest plots, scatter plots,
funnel plots, leave-one-out sensitivity analyses, and radial plots.

Example:
    >>> from pymr import MR
    >>> from pymr.plots import forest_plot, scatter_plot
    >>> mr = MR(harmonized_data)
    >>> results = mr.run()
    >>> fig = forest_plot(results)
    >>> fig.savefig("mr_forest_plot.png", dpi=300, bbox_inches="tight")

"""

from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pymr import methods

# Set publication-ready style
sns.set_style("whitegrid")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 100,
})


def forest_plot(
    results: pd.DataFrame,
    ax: Axes | None = None,
    estimate_col: str = "beta",
    se_col: str = "se",
    method_col: str = "method",
    color: str = "#2E86AB",
) -> Figure:
    """Create forest plot of MR estimates across methods.

    Displays point estimates and confidence intervals for each MR method,
    allowing easy comparison of results.

    Args:
        results: DataFrame with MR results (from MR.run())
        ax: Optional matplotlib Axes. If None, creates new figure.
        estimate_col: Column name for point estimates (default: "beta")
        se_col: Column name for standard errors (default: "se")
        method_col: Column name for method names (default: "method")
        color: Color for points and error bars (default: "#2E86AB")

    Returns:
        matplotlib Figure object

    Example:
        >>> mr = MR(harmonized_data)
        >>> results = mr.run()
        >>> fig = forest_plot(results)
        >>> fig.savefig("forest.png", dpi=300, bbox_inches="tight")

    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, len(results) * 0.6 + 1))
    else:
        fig = ax.figure

    # Extract estimates and CIs
    beta = results[estimate_col].values
    se = results[se_col].values
    methods_list = results[method_col].values

    # Compute 95% CIs
    ci_lower = beta - 1.96 * se
    ci_upper = beta + 1.96 * se

    # Create forest plot
    y_pos = np.arange(len(methods_list))

    # Plot error bars
    ax.errorbar(
        beta,
        y_pos,
        xerr=np.vstack([beta - ci_lower, ci_upper - beta]),
        fmt="o",
        color=color,
        ecolor=color,
        elinewidth=2,
        markersize=8,
        capsize=4,
        capthick=2,
    )

    # Add vertical line at null (beta = 0)
    ax.axvline(x=0, color="gray", linestyle="--", linewidth=1, alpha=0.7)

    # Customize axes
    ax.set_yticks(y_pos)
    ax.set_yticklabels(methods_list)
    ax.set_xlabel(f"{estimate_col.capitalize()} (95% CI)", fontweight="bold")
    ax.set_ylabel("")
    ax.set_title("MR Estimates Across Methods", fontweight="bold", pad=15)

    # Add grid for readability
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    # Invert y-axis so first method is at top
    ax.invert_yaxis()

    fig.tight_layout()
    return fig


def scatter_plot(
    harmonized: pd.DataFrame,
    method: Literal["IVW", "MR-Egger", "Weighted Median"] = "IVW",
    ax: Axes | None = None,
    point_color: str = "#A23B72",
    line_color: str = "#2E86AB",
) -> Figure:
    """Create scatter plot of SNP effects with MR regression line.

    Plots exposure vs outcome effects for each SNP, with regression line
    showing the estimated causal effect.

    Args:
        harmonized: Harmonized exposure-outcome data with columns:
            beta_exp, se_exp, beta_out, se_out
        method: MR method for regression line (default: "IVW")
        ax: Optional matplotlib Axes. If None, creates new figure.
        point_color: Color for SNP points (default: "#A23B72")
        line_color: Color for regression line (default: "#2E86AB")

    Returns:
        matplotlib Figure object

    Example:
        >>> fig = scatter_plot(harmonized, method="IVW")
        >>> fig.savefig("scatter.png", dpi=300, bbox_inches="tight")

    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    else:
        fig = ax.figure

    # Extract data
    beta_exp = harmonized["beta_exp"].values
    se_exp = harmonized["se_exp"].values
    beta_out = harmonized["beta_out"].values
    se_out = harmonized["se_out"].values

    # Compute MR estimate for regression line
    method_func = {
        "IVW": methods.ivw,
        "MR-Egger": methods.mr_egger,
        "Weighted Median": methods.weighted_median,
    }[method]

    result = method_func(beta_exp, se_exp, beta_out, se_out)
    beta_mr = result["beta"]

    # Plot SNPs with error bars
    ax.errorbar(
        beta_exp,
        beta_out,
        xerr=1.96 * se_exp,
        yerr=1.96 * se_out,
        fmt="o",
        color=point_color,
        ecolor=point_color,
        alpha=0.6,
        elinewidth=1,
        markersize=5,
        capsize=0,
        label="SNPs (95% CI)",
    )

    # Plot regression line
    x_range = np.array([beta_exp.min(), beta_exp.max()])
    if method == "MR-Egger":
        intercept = result["intercept"]
        y_pred = intercept + beta_mr * x_range
        label = f"{method} (β={beta_mr:.2f}, intercept={intercept:.3f})"
    else:
        y_pred = beta_mr * x_range
        label = f"{method} (β={beta_mr:.2f})"

    ax.plot(x_range, y_pred, "-", color=line_color, linewidth=2, label=label)

    # Customize axes
    ax.set_xlabel("SNP effect on exposure (95% CI)", fontweight="bold")
    ax.set_ylabel("SNP effect on outcome (95% CI)", fontweight="bold")
    ax.set_title("MR Scatter Plot", fontweight="bold", pad=15)
    ax.legend(loc="best", frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    fig.tight_layout()
    return fig


def funnel_plot(
    harmonized: pd.DataFrame,
    ax: Axes | None = None,
    point_color: str = "#A23B72",
    line_color: str = "#2E86AB",
    show_contours: bool = False,
    show_asymmetry_test: bool = False,
) -> Figure:
    """Create funnel plot for assessing publication bias.

    Plots per-SNP Wald ratios against their precision (inverse SE).
    Asymmetry may suggest publication bias or pleiotropy.

    Args:
        harmonized: Harmonized exposure-outcome data
        ax: Optional matplotlib Axes. If None, creates new figure.
        point_color: Color for SNP points (default: "#A23B72")
        line_color: Color for IVW estimate line (default: "#2E86AB")
        show_contours: Show significance contour lines (p=0.05, 0.01)
        show_asymmetry_test: Show Egger's asymmetry test results in legend

    Returns:
        matplotlib Figure object

    Example:
        >>> fig = funnel_plot(harmonized)
        >>> fig.savefig("funnel.png", dpi=300, bbox_inches="tight")
        >>> # With asymmetry test
        >>> fig = funnel_plot(harmonized, show_asymmetry_test=True)

    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    else:
        fig = ax.figure

    # Compute per-SNP Wald ratios
    beta_exp = harmonized["beta_exp"].values
    se_exp = harmonized["se_exp"].values
    beta_out = harmonized["beta_out"].values
    se_out = harmonized["se_out"].values

    wald_ratio = beta_out / beta_exp
    wald_se = np.abs(se_out / beta_exp)
    precision = 1 / wald_se

    # Compute IVW estimate for reference line
    result = methods.ivw(beta_exp, se_exp, beta_out, se_out)
    beta_ivw = result["beta"]

    # Plot SNPs
    ax.scatter(
        wald_ratio,
        precision,
        color=point_color,
        alpha=0.6,
        s=50,
        edgecolors="white",
        linewidth=0.5,
        label="SNPs",
    )

    # Add vertical line at IVW estimate
    ax.axvline(
        x=beta_ivw,
        color=line_color,
        linestyle="-",
        linewidth=2,
        label=f"IVW estimate (β={beta_ivw:.2f})",
    )

    # Add pseudo 95% CI region (funnel shape)
    y_range = np.array([precision.min(), precision.max()])
    ci_width = 1.96 / y_range
    ax.plot(
        beta_ivw - ci_width,
        y_range,
        "--",
        color=line_color,
        alpha=0.5,
        linewidth=1,
    )
    ax.plot(
        beta_ivw + ci_width,
        y_range,
        "--",
        color=line_color,
        alpha=0.5,
        linewidth=1,
    )
    ax.fill_betweenx(
        y_range,
        beta_ivw - ci_width,
        beta_ivw + ci_width,
        color=line_color,
        alpha=0.1,
        label="95% CI region",
    )

    # Add significance contours if requested
    if show_contours:
        # Create contour lines for p=0.05 and p=0.01
        for z_score, alpha, label in [(1.96, 0.3, "p=0.05"), (2.576, 0.2, "p=0.01")]:
            contour_width = z_score / y_range
            ax.plot(
                beta_ivw - contour_width,
                y_range,
                ":",
                color="gray",
                alpha=alpha,
                linewidth=1,
            )
            ax.plot(
                beta_ivw + contour_width,
                y_range,
                ":",
                color="gray",
                alpha=alpha,
                linewidth=1,
                label=label,
            )

    # Add asymmetry test results if requested
    if show_asymmetry_test and len(beta_exp) >= 3:
        from pymr.sensitivity import funnel_asymmetry

        try:
            asym_result = funnel_asymmetry(beta_exp, se_exp, beta_out, se_out)
            # Add result to legend
            asym_text = (
                f"Asymmetry test: p={asym_result['intercept_pval']:.3f}"
            )
            ax.plot([], [], " ", label=asym_text)  # Invisible line for legend entry
        except (ValueError, np.linalg.LinAlgError):
            # Skip if test fails
            pass

    # Customize axes
    ax.set_xlabel("Per-SNP causal estimate (Wald ratio)", fontweight="bold")
    ax.set_ylabel("Precision (1 / SE)", fontweight="bold")
    ax.set_title("Funnel Plot", fontweight="bold", pad=15)
    ax.legend(loc="best", frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    fig.tight_layout()
    return fig


def leave_one_out_plot(
    loo_results: pd.DataFrame,
    ax: Axes | None = None,
    estimate_col: str = "beta",
    se_col: str = "se",
    snp_col: str = "excluded_snp",
    color: str = "#2E86AB",
    max_snps: int = 30,
) -> Figure:
    """Create leave-one-out sensitivity plot.

    Shows how the MR estimate changes when each SNP is excluded,
    helping identify influential instruments.

    Args:
        loo_results: Leave-one-out results (from MR.leave_one_out())
        ax: Optional matplotlib Axes. If None, creates new figure.
        estimate_col: Column name for estimates (default: "beta")
        se_col: Column name for standard errors (default: "se")
        snp_col: Column name for SNP identifiers (default: "excluded_snp")
        color: Color for points and error bars (default: "#2E86AB")
        max_snps: Maximum number of SNPs to display (default: 30)

    Returns:
        matplotlib Figure object

    Example:
        >>> loo = mr.leave_one_out()
        >>> fig = leave_one_out_plot(loo)
        >>> fig.savefig("loo.png", dpi=300, bbox_inches="tight")

    """
    if ax is None:
        n_snps = min(len(loo_results), max_snps)
        fig, ax = plt.subplots(figsize=(8, n_snps * 0.4 + 1))
    else:
        fig = ax.figure

    # Limit to max_snps if needed
    if len(loo_results) > max_snps:
        loo_results = loo_results.head(max_snps).copy()

    # Extract estimates and CIs
    beta = loo_results[estimate_col].values
    se = loo_results[se_col].values
    snps = loo_results[snp_col].values

    # Compute 95% CIs
    ci_lower = beta - 1.96 * se
    ci_upper = beta + 1.96 * se

    # Create plot
    y_pos = np.arange(len(snps))

    # Plot error bars
    ax.errorbar(
        beta,
        y_pos,
        xerr=np.vstack([beta - ci_lower, ci_upper - beta]),
        fmt="o",
        color=color,
        ecolor=color,
        elinewidth=1.5,
        markersize=6,
        capsize=3,
        capthick=1.5,
    )

    # Add vertical line at overall mean
    mean_beta = np.mean(beta)
    ax.axvline(x=mean_beta, color="gray", linestyle="--", linewidth=1, alpha=0.7)

    # Customize axes
    ax.set_yticks(y_pos)
    ax.set_yticklabels([str(s) for s in snps], fontsize=8)
    ax.set_xlabel(f"{estimate_col.capitalize()} (95% CI)", fontweight="bold")
    ax.set_ylabel("Excluded SNP", fontweight="bold")
    ax.set_title("Leave-One-Out Sensitivity Analysis", fontweight="bold", pad=15)

    # Add grid for readability
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    # Invert y-axis so first SNP is at top
    ax.invert_yaxis()

    fig.tight_layout()
    return fig


def radial_plot(
    harmonized: pd.DataFrame,
    ax: Axes | None = None,
    point_color: str = "#A23B72",
    line_color: str = "#2E86AB",
) -> Figure:
    """Create radial MR plot (Galbraith plot).

    Plots standardized SNP effects (x-axis) against their weights (y-axis).
    Helps identify outliers and assess heterogeneity.

    Args:
        harmonized: Harmonized exposure-outcome data
        ax: Optional matplotlib Axes. If None, creates new figure.
        point_color: Color for SNP points (default: "#A23B72")
        line_color: Color for IVW regression line (default: "#2E86AB")

    Returns:
        matplotlib Figure object

    Example:
        >>> fig = radial_plot(harmonized)
        >>> fig.savefig("radial.png", dpi=300, bbox_inches="tight")

    Reference:
        Bowden J, et al. (2018). Improving the visualization, interpretation
        and analysis of two-sample summary data Mendelian randomization via
        the Radial plot and Radial regression. Int J Epidemiol, 47(6):2100-2114.

    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    else:
        fig = ax.figure

    # Extract data
    beta_exp = harmonized["beta_exp"].values
    se_exp = harmonized["se_exp"].values
    beta_out = harmonized["beta_out"].values
    se_out = harmonized["se_out"].values

    # Compute radial transformation
    # Per-SNP Wald ratios and weights
    wald_se = np.abs(se_out / beta_exp)
    weights = 1 / wald_se

    # Radial coordinates
    # x: standardized exposure effect (exposure effect * sqrt(weight))
    # y: standardized outcome effect (outcome effect * sqrt(weight))
    x = beta_exp * np.sqrt(weights)
    y = beta_out * np.sqrt(weights)

    # Compute IVW estimate for regression line
    result = methods.ivw(beta_exp, se_exp, beta_out, se_out)
    beta_ivw = result["beta"]

    # Plot SNPs
    ax.scatter(
        x,
        y,
        color=point_color,
        alpha=0.6,
        s=50,
        edgecolors="white",
        linewidth=0.5,
        label="SNPs",
    )

    # Plot regression line through origin (radial IVW)
    x_range = np.array([x.min(), x.max()])
    y_pred = beta_ivw * x_range
    ax.plot(
        x_range,
        y_pred,
        "-",
        color=line_color,
        linewidth=2,
        label=f"IVW estimate (β={beta_ivw:.2f})",
    )

    # Add 95% CI lines
    se_ivw = result["se"]
    ci_lower = (beta_ivw - 1.96 * se_ivw) * x_range
    ci_upper = (beta_ivw + 1.96 * se_ivw) * x_range
    ax.plot(x_range, ci_lower, "--", color=line_color, alpha=0.5, linewidth=1)
    ax.plot(x_range, ci_upper, "--", color=line_color, alpha=0.5, linewidth=1)
    ax.fill_between(
        x_range,
        ci_lower,
        ci_upper,
        color=line_color,
        alpha=0.1,
        label="95% CI",
    )

    # Customize axes
    ax.set_xlabel("√Weight × SNP effect on exposure", fontweight="bold")
    ax.set_ylabel("√Weight × SNP effect on outcome", fontweight="bold")
    ax.set_title("Radial MR Plot", fontweight="bold", pad=15)
    ax.legend(loc="best", frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    # Add origin lines
    ax.axhline(y=0, color="gray", linestyle="-", linewidth=0.5, alpha=0.5)
    ax.axvline(x=0, color="gray", linestyle="-", linewidth=0.5, alpha=0.5)

    fig.tight_layout()
    return fig
