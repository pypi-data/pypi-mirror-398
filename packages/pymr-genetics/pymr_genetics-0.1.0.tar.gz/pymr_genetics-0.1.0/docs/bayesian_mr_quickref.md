# Bayesian MR Quick Reference

## Basic Usage

```python
from pymr import BayesianMR

# Initialize with harmonized data
bmr = BayesianMR(data, prior_mean=0, prior_sd=1)

# Run MCMC
bmr.sample(n_samples=10000, n_chains=4, warmup=1000)

# Get results
summary = bmr.summary()
print(f"Effect: {summary['mean']:.3f} [{summary['ci_lower']:.3f}, {summary['ci_upper']:.3f}]")
```

## Three Models

```python
# 1. Bayesian IVW (default)
bmr.sample(model="ivw")

# 2. Bayesian Egger (tests pleiotropy)
bmr.sample(model="egger")

# 3. Robust IVW (outlier-resistant)
bmr.sample(model="robust_ivw")
```

## Key Functions

| Function | Purpose | Output |
|----------|---------|--------|
| `sample()` | Run MCMC sampling | Posterior samples |
| `summary()` | Get statistics | mean, sd, CI, R-hat, n_eff |
| `bayes_factor()` | Evidence for effect | BF (>10 = strong evidence) |
| `model_comparison()` | Compare IVW vs Egger | WAIC (lower = better) |
| `plot_posterior()` | Visualize | Matplotlib figure |

## Prior Specification

```python
# Weakly informative (default)
BayesianMR(data, prior_mean=0, prior_sd=1)

# Informative (strong prior belief)
BayesianMR(data, prior_mean=0.5, prior_sd=0.2)

# For Egger model
BayesianMR(
    data,
    prior_mean=0,
    prior_sd=1,
    intercept_prior_mean=0,
    intercept_prior_sd=0.5,
)
```

## Interpreting Results

### Credible Intervals
```python
summary = bmr.summary()
ci = (summary['ci_lower'], summary['ci_upper'])
# 95% probability the true effect is in this interval
```

### Bayes Factors
```python
bf = bmr.bayes_factor(null_value=0)
```
- BF > 10: Strong evidence for causal effect
- BF > 3: Moderate evidence for causal effect
- BF ~ 1: Inconclusive
- BF < 1/3: Moderate evidence for null
- BF < 1/10: Strong evidence for null

### R-hat (Convergence)
```python
summary['rhat']
```
- < 1.01: Excellent convergence ✓
- < 1.05: Acceptable convergence
- > 1.1: Poor convergence (increase samples)

### Effective Sample Size
```python
summary['n_eff']
```
- Higher is better
- n_eff / n_samples > 0.1 is acceptable

### Egger Intercept (Pleiotropy)
```python
bmr.sample(model="egger")
summary = bmr.summary()
```
- If 95% CI contains 0: No pleiotropy ✓
- If 95% CI excludes 0: Directional pleiotropy detected

## Model Comparison

```python
comparison = bmr.model_comparison(models=["ivw", "egger"])

if comparison["ivw"]["waic"] < comparison["egger"]["waic"]:
    print("Use IVW (no pleiotropy)")
else:
    print("Use Egger (pleiotropy present)")
```

## Complete Workflow

```python
from pymr import BayesianMR, MR
import matplotlib.pyplot as plt

# 1. Compare with frequentist
mr = MR(data)
freq = mr.run(methods=["IVW"])
print(f"Frequentist: {freq.iloc[0]['beta']:.3f}")

# 2. Run Bayesian IVW
bmr = BayesianMR(data, prior_mean=0, prior_sd=1)
bmr.sample(n_samples=10000, n_chains=4, warmup=1000)
summary = bmr.summary()
print(f"Bayesian: {summary['mean']:.3f} [{summary['ci_lower']:.3f}, {summary['ci_upper']:.3f}]")

# 3. Check convergence
print(f"R-hat: {summary['rhat']:.4f}")
print(f"n_eff: {summary['n_eff']:.0f}")

# 4. Bayes factor
bf = bmr.bayes_factor(null_value=0)
print(f"BF: {bf:.2f}")

# 5. Test for pleiotropy
bmr_egger = BayesianMR(data)
bmr_egger.sample(n_samples=10000, n_chains=4, model="egger")
egger_summary = bmr_egger.summary()
print(f"Intercept: {egger_summary['intercept_mean']:.3f}")

# 6. Model comparison
comparison = bmr.model_comparison()
print(f"IVW WAIC: {comparison['ivw']['waic']:.2f}")
print(f"Egger WAIC: {comparison['egger']['waic']:.2f}")

# 7. Visualize
bmr.plot_posterior()
plt.savefig("posterior.png")
```

## Common Issues

### Poor convergence (R-hat > 1.1)
```python
# Increase warmup
bmr.sample(n_samples=10000, n_chains=4, warmup=5000)
```

### Low effective sample size
```python
# Increase total samples
bmr.sample(n_samples=50000, n_chains=4, warmup=2000)
```

### Results differ from frequentist
```python
# Use weaker prior (let data dominate)
bmr = BayesianMR(data, prior_mean=0, prior_sd=10)
```

## When to Use Bayesian MR

**Use Bayesian if:**
- Want full uncertainty quantification
- Have prior information to incorporate
- Need probabilistic interpretation
- Small sample size
- Want to compare models formally

**Use Frequentist if:**
- Need fast computation
- Standard analysis is sufficient
- Don't want to specify priors
- Large sample size

## Performance Tips

```python
# Fast (for testing)
bmr.sample(n_samples=1000, n_chains=2, warmup=100)

# Standard (recommended)
bmr.sample(n_samples=10000, n_chains=4, warmup=1000)

# High quality (publication)
bmr.sample(n_samples=50000, n_chains=4, warmup=2000)
```

## See Also

- Full documentation: `docs/bayesian_mr.md`
- Example script: `examples/bayesian_mr_example.py`
- Tests: `tests/test_bayesian.py`
