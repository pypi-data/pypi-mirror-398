"""Example: Bayesian Mendelian Randomization Analysis.

Demonstrates the use of BayesianMR for full posterior inference,
including model comparison and Bayes factors.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pymr import BayesianMR, MR, harmonize

# Set random seed for reproducibility
np.random.seed(42)


def main():
    """Run Bayesian MR analysis example."""
    # Create sample harmonized data
    print("Creating sample GWAS data...")
    n_snps = 30
    data = pd.DataFrame({
        "SNP": [f"rs{i}" for i in range(n_snps)],
        "beta_exp": np.random.normal(0.1, 0.02, n_snps),
        "se_exp": np.abs(np.random.normal(0.01, 0.002, n_snps)),
        "beta_out": np.random.normal(0.05, 0.02, n_snps),
        "se_out": np.abs(np.random.normal(0.02, 0.005, n_snps)),
    })

    # Traditional frequentist MR
    print("\n" + "=" * 60)
    print("FREQUENTIST MR ANALYSIS")
    print("=" * 60)
    mr = MR(data)
    freq_results = mr.run(methods=["IVW", "MR-Egger"])
    print("\nFrequentist Results:")
    print(freq_results[["method", "beta", "se", "pval"]].to_string(index=False))

    # Bayesian MR with IVW
    print("\n" + "=" * 60)
    print("BAYESIAN MR ANALYSIS - IVW")
    print("=" * 60)
    bmr = BayesianMR(data, prior_mean=0, prior_sd=1)
    print("\nRunning MCMC sampling (10,000 samples, 4 chains)...")
    bmr.sample(n_samples=10000, n_chains=4, warmup=1000, model="ivw")

    summary = bmr.summary()
    print("\nPosterior Summary (IVW):")
    print(f"  Mean:             {summary['mean']:.4f}")
    print(f"  SD:               {summary['sd']:.4f}")
    print(f"  95% CI:           [{summary['ci_lower']:.4f}, {summary['ci_upper']:.4f}]")
    print(f"  R-hat:            {summary['rhat']:.4f} (should be ~1.0)")
    print(f"  Effective N:      {summary['n_eff']:.0f}")

    # Bayes factor
    bf = bmr.bayes_factor(null_value=0)
    print(f"\nBayes Factor (vs null): {bf:.2f}")
    if bf > 10:
        print("  → Strong evidence for causal effect")
    elif bf > 3:
        print("  → Moderate evidence for causal effect")
    elif bf < 1 / 3:
        print("  → Moderate evidence for null")
    elif bf < 1 / 10:
        print("  → Strong evidence for null")
    else:
        print("  → Inconclusive evidence")

    # Bayesian Egger
    print("\n" + "=" * 60)
    print("BAYESIAN MR ANALYSIS - EGGER")
    print("=" * 60)
    bmr_egger = BayesianMR(
        data,
        prior_mean=0,
        prior_sd=1,
        intercept_prior_mean=0,
        intercept_prior_sd=0.5,
    )
    print("\nRunning MCMC sampling (10,000 samples, 4 chains)...")
    bmr_egger.sample(n_samples=10000, n_chains=4, warmup=1000, model="egger")

    egger_summary = bmr_egger.summary()
    print("\nPosterior Summary (Egger):")
    print(f"  Beta Mean:        {egger_summary['beta_mean']:.4f}")
    print(f"  Beta 95% CI:      [{egger_summary['ci_lower']:.4f}, {egger_summary['ci_upper']:.4f}]")
    print(f"  Intercept Mean:   {egger_summary['intercept_mean']:.4f}")
    print(
        f"  Intercept 95% CI: [{egger_summary['intercept_ci_lower']:.4f}, "
        f"{egger_summary['intercept_ci_upper']:.4f}]"
    )

    # Check if intercept credible interval contains zero
    if (
        egger_summary["intercept_ci_lower"] < 0 < egger_summary["intercept_ci_upper"]
    ):
        print("  → No evidence of directional pleiotropy (intercept contains 0)")
    else:
        print("  → Evidence of directional pleiotropy (intercept excludes 0)")

    # Robust Bayesian MR
    print("\n" + "=" * 60)
    print("BAYESIAN MR ANALYSIS - ROBUST (t-distribution)")
    print("=" * 60)
    bmr_robust = BayesianMR(data, prior_mean=0, prior_sd=1)
    print("\nRunning MCMC sampling (10,000 samples, 4 chains)...")
    bmr_robust.sample(n_samples=10000, n_chains=4, warmup=1000, model="robust_ivw")

    robust_summary = bmr_robust.summary()
    print("\nPosterior Summary (Robust IVW):")
    print(f"  Mean:             {robust_summary['mean']:.4f}")
    print(f"  SD:               {robust_summary['sd']:.4f}")
    print(f"  95% CI:           [{robust_summary['ci_lower']:.4f}, {robust_summary['ci_upper']:.4f}]")
    print(f"  Degrees freedom:  {robust_summary['nu_mean']:.2f}")

    # Model comparison
    print("\n" + "=" * 60)
    print("BAYESIAN MODEL COMPARISON (WAIC)")
    print("=" * 60)
    print("\nComparing IVW and Egger models...")
    bmr_compare = BayesianMR(data, prior_mean=0, prior_sd=1)
    comparison = bmr_compare.model_comparison(models=["ivw", "egger"])

    print("\nWAIC Results (lower is better):")
    print(f"  IVW:    {comparison['ivw']['waic']:.2f} ± {comparison['ivw']['se']:.2f}")
    print(f"  Egger:  {comparison['egger']['waic']:.2f} ± {comparison['egger']['se']:.2f}")

    if comparison["ivw"]["waic"] < comparison["egger"]["waic"]:
        print("  → IVW model preferred (simpler, no pleiotropy detected)")
    else:
        print("  → Egger model preferred (accounts for pleiotropy)")

    # Create visualization
    print("\n" + "=" * 60)
    print("CREATING POSTERIOR PLOTS")
    print("=" * 60)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Plot IVW posterior
    bmr.plot_posterior(ax=axes[0])
    axes[0].set_title("Bayesian IVW Posterior")

    # Plot Egger posterior
    bmr_egger.plot_posterior(ax=axes[1])
    axes[1].set_title("Bayesian Egger Posterior")

    # Plot Robust posterior
    bmr_robust.plot_posterior(ax=axes[2])
    axes[2].set_title("Robust Bayesian IVW Posterior")

    plt.tight_layout()
    plt.savefig("bayesian_mr_posteriors.png", dpi=150)
    print("\nPosterior plots saved to: bayesian_mr_posteriors.png")

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
