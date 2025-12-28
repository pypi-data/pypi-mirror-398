# Bayesian Mendelian Randomization

PyMR implements Bayesian Mendelian Randomization using Metropolis-Hastings MCMC sampling. Bayesian MR provides full posterior inference, credible intervals, Bayes factors, and model comparison - without requiring PyMC or Stan.

## Features

- **Bayesian IVW**: Normal likelihood with customizable priors
- **Bayesian Egger**: Joint estimation of slope and intercept with prior specifications
- **Robust Bayesian MR**: t-distribution likelihood for outlier resistance
- **Bayes Factors**: Quantify evidence for/against causal effects
- **Model Comparison**: WAIC-based comparison of IVW vs Egger
- **MCMC Diagnostics**: R-hat convergence and effective sample size
- **Posterior Visualization**: Built-in plotting functions

## Quick Start

```python
from pymr import BayesianMR
import pandas as pd

# Harmonized GWAS data
data = pd.DataFrame({
    "beta_exp": [0.1, 0.2, 0.15],
    "se_exp": [0.01, 0.02, 0.015],
    "beta_out": [0.05, 0.10, 0.075],
    "se_out": [0.02, 0.03, 0.025],
})

# Run Bayesian IVW
bmr = BayesianMR(data, prior_mean=0, prior_sd=1)
bmr.sample(n_samples=10000, n_chains=4, warmup=1000)

# Get posterior summary
summary = bmr.summary()
print(f"Posterior mean: {summary['mean']:.3f}")
print(f"95% CI: [{summary['ci_lower']:.3f}, {summary['ci_upper']:.3f}]")

# Bayes factor vs null
bf = bmr.bayes_factor(null_value=0)
print(f"Bayes factor: {bf:.2f}")

# Plot posterior
bmr.plot_posterior()
```

## Bayesian Models

### 1. Bayesian IVW

Uses normal likelihood with inverse variance weighting:

```python
bmr = BayesianMR(data, prior_mean=0, prior_sd=1)
bmr.sample(n_samples=10000, n_chains=4, warmup=1000, model="ivw")
```

**Model specification:**
- Likelihood: `beta_out / beta_exp ~ N(beta, se_out^2 / beta_exp^2)`
- Prior: `beta ~ N(prior_mean, prior_sd^2)`

**When to use:**
- Standard MR analysis
- No suspected pleiotropy
- Want to incorporate prior information

### 2. Bayesian Egger

Jointly estimates causal effect and intercept:

```python
bmr = BayesianMR(
    data,
    prior_mean=0,
    prior_sd=1,
    intercept_prior_mean=0,
    intercept_prior_sd=0.5,
)
bmr.sample(n_samples=10000, n_chains=4, warmup=1000, model="egger")

summary = bmr.summary()
print(f"Intercept: {summary['intercept_mean']:.3f}")
print(f"95% CI: [{summary['intercept_ci_lower']:.3f}, {summary['intercept_ci_upper']:.3f}]")
```

**Model specification:**
- Likelihood: `beta_out ~ N(intercept + beta * beta_exp, se_out^2)`
- Priors:
  - `beta ~ N(prior_mean, prior_sd^2)`
  - `intercept ~ N(intercept_prior_mean, intercept_prior_sd^2)`

**When to use:**
- Testing for directional pleiotropy
- Non-zero intercept indicates pleiotropy
- Want to correct for pleiotropy

**Interpreting the intercept:**
- If 95% CI contains 0: No evidence of pleiotropy
- If 95% CI excludes 0: Evidence of directional pleiotropy

### 3. Robust Bayesian MR

Uses t-distribution for heavy-tailed errors (robust to outliers):

```python
bmr = BayesianMR(data, prior_mean=0, prior_sd=1)
bmr.sample(n_samples=10000, n_chains=4, warmup=1000, model="robust_ivw")

summary = bmr.summary()
print(f"Degrees of freedom: {summary['nu_mean']:.2f}")
```

**Model specification:**
- Likelihood: `(beta_out / beta_exp - beta) / se ~ t(nu)`
- Priors:
  - `beta ~ N(prior_mean, prior_sd^2)`
  - `nu ~ Exponential(1/8) + 2` (ensures finite variance)

**When to use:**
- Suspected outliers in data
- Want robust estimates
- Data has heavy tails

**Interpreting degrees of freedom (nu):**
- Low nu (3-5): Heavy tails, data has outliers
- High nu (>30): Approaches normal distribution
- Very low nu (<3): Infinite variance, poor model fit

## Bayes Factors

Quantify evidence for causal effect vs null hypothesis:

```python
# After sampling
bf = bmr.bayes_factor(null_value=0)

if bf > 10:
    print("Strong evidence for causal effect")
elif bf > 3:
    print("Moderate evidence for causal effect")
elif bf < 1/3:
    print("Moderate evidence for null")
elif bf < 1/10:
    print("Strong evidence for null")
else:
    print("Inconclusive")
```

**Interpretation:**
- BF > 10: Strong evidence for alternative
- BF > 3: Moderate evidence for alternative
- BF ~ 1: No evidence either way
- BF < 1/3: Moderate evidence for null
- BF < 1/10: Strong evidence for null

## Model Comparison

Compare IVW and Egger using WAIC (Watanabe-Akaike Information Criterion):

```python
bmr = BayesianMR(data)
comparison = bmr.model_comparison(models=["ivw", "egger"])

print(f"IVW WAIC:   {comparison['ivw']['waic']:.2f}")
print(f"Egger WAIC: {comparison['egger']['waic']:.2f}")

if comparison['ivw']['waic'] < comparison['egger']['waic']:
    print("IVW preferred (no pleiotropy)")
else:
    print("Egger preferred (pleiotropy present)")
```

**WAIC properties:**
- Lower WAIC = better model fit
- Accounts for model complexity (like AIC)
- Fully Bayesian (uses posterior distribution)
- Asymptotically equivalent to leave-one-out cross-validation

## Prior Selection

### Weakly Informative Priors (Default)

```python
bmr = BayesianMR(
    data,
    prior_mean=0,      # No prior belief about effect direction
    prior_sd=1,        # Wide prior (allows data to dominate)
)
```

Use when:
- You have little prior information
- Want data to drive inference
- Standard analysis approach

### Informative Priors

```python
bmr = BayesianMR(
    data,
    prior_mean=0.5,    # Prior belief of positive effect
    prior_sd=0.2,      # Strong prior (narrow distribution)
)
```

Use when:
- You have strong prior evidence (e.g., from previous studies)
- Want to incorporate external information
- Regularization to prevent overfitting

### Effect of Priors

```python
# Weak prior - data dominates
bmr_weak = BayesianMR(data, prior_mean=0, prior_sd=10)
bmr_weak.sample(n_samples=5000, n_chains=4)
print(f"Weak prior mean: {bmr_weak.summary()['mean']:.3f}")

# Strong prior - prior influences estimate
bmr_strong = BayesianMR(data, prior_mean=1, prior_sd=0.1)
bmr_strong.sample(n_samples=5000, n_chains=4)
print(f"Strong prior mean: {bmr_strong.summary()['mean']:.3f}")
```

## MCMC Diagnostics

### R-hat (Gelman-Rubin Statistic)

Measures convergence across chains:

```python
summary = bmr.summary()
rhat = summary['rhat']

if rhat < 1.01:
    print("Excellent convergence")
elif rhat < 1.05:
    print("Good convergence")
else:
    print("Poor convergence - run more iterations")
```

**Guidelines:**
- R-hat < 1.01: Excellent convergence
- R-hat < 1.05: Acceptable convergence
- R-hat > 1.1: Poor convergence, increase warmup/samples

### Effective Sample Size

Accounts for autocorrelation in MCMC samples:

```python
summary = bmr.summary()
n_eff = summary['n_eff']

print(f"Effective samples: {n_eff:.0f}")
# Higher is better (closer to actual number of samples)
```

**Guidelines:**
- n_eff / n_samples > 0.5: Good mixing
- n_eff / n_samples > 0.1: Acceptable
- n_eff / n_samples < 0.1: Poor mixing, increase samples

### Tuning MCMC

If diagnostics indicate problems:

```python
# Increase warmup for better initialization
bmr.sample(n_samples=10000, n_chains=4, warmup=5000)

# Increase total samples for better posterior approximation
bmr.sample(n_samples=50000, n_chains=4, warmup=2000)

# Increase chains for better R-hat estimation
bmr.sample(n_samples=10000, n_chains=8, warmup=1000)
```

## Visualization

### Posterior Distribution

```python
import matplotlib.pyplot as plt

# Single plot
bmr.plot_posterior()
plt.show()

# Multiple models
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

bmr_ivw.plot_posterior(ax=axes[0])
axes[0].set_title("IVW")

bmr_egger.plot_posterior(ax=axes[1])
axes[1].set_title("Egger")

bmr_robust.plot_posterior(ax=axes[2])
axes[2].set_title("Robust")

plt.tight_layout()
plt.show()
```

The plot shows:
- Histogram: Posterior distribution
- Red dashed line: Prior distribution
- Black solid line: Posterior mean
- Black dotted lines: 95% credible interval

## Comparison with Frequentist MR

| Aspect | Frequentist | Bayesian |
|--------|-------------|----------|
| Output | Point estimate + SE | Full posterior distribution |
| Uncertainty | Confidence intervals | Credible intervals |
| Interpretation | "If we repeat, 95% of CIs contain true value" | "95% probability true value in interval" |
| Prior info | Cannot incorporate | Can incorporate via priors |
| Model comparison | Likelihood ratio tests | Bayes factors, WAIC |
| Small samples | May be unreliable | More stable with priors |
| Computation | Fast (analytical) | Slower (MCMC) |

### When to use Bayesian MR

**Advantages:**
- Full uncertainty quantification
- Can incorporate prior information
- Natural interpretation of credible intervals
- Robust model comparison via WAIC
- Better with small sample sizes

**Disadvantages:**
- Computationally slower (MCMC)
- Requires prior specification
- Need to check MCMC convergence

### Concordance with Frequentist Results

With weak priors and sufficient data, Bayesian and frequentist MR should give similar results:

```python
from pymr import MR, BayesianMR

# Frequentist
mr = MR(data)
freq_result = mr.run(methods=["IVW"])
print(f"Frequentist beta: {freq_result.iloc[0]['beta']:.3f}")

# Bayesian with weak prior
bmr = BayesianMR(data, prior_mean=0, prior_sd=10)
bmr.sample(n_samples=10000, n_chains=4)
print(f"Bayesian beta: {bmr.summary()['mean']:.3f}")
```

## Advanced Examples

### Sequential Analysis (Update Prior with New Data)

```python
# Initial study
bmr1 = BayesianMR(data1, prior_mean=0, prior_sd=1)
bmr1.sample(n_samples=10000, n_chains=4)
posterior1 = bmr1.summary()

# Use posterior as prior for new study
bmr2 = BayesianMR(
    data2,
    prior_mean=posterior1['mean'],
    prior_sd=posterior1['sd'],
)
bmr2.sample(n_samples=10000, n_chains=4)
```

### Sensitivity to Prior Specification

```python
import numpy as np

priors = [0.1, 0.5, 1.0, 5.0, 10.0]
results = []

for prior_sd in priors:
    bmr = BayesianMR(data, prior_mean=0, prior_sd=prior_sd)
    bmr.sample(n_samples=5000, n_chains=4)
    results.append({
        'prior_sd': prior_sd,
        'posterior_mean': bmr.summary()['mean'],
    })

import pandas as pd
df = pd.DataFrame(results)
print(df)
```

### Custom Model Selection Workflow

```python
# 1. Fit all models
models = {}

# IVW
bmr_ivw = BayesianMR(data)
bmr_ivw.sample(n_samples=10000, n_chains=4, model="ivw")
models['IVW'] = bmr_ivw

# Egger
bmr_egger = BayesianMR(data)
bmr_egger.sample(n_samples=10000, n_chains=4, model="egger")
models['Egger'] = bmr_egger

# Robust
bmr_robust = BayesianMR(data)
bmr_robust.sample(n_samples=10000, n_chains=4, model="robust_ivw")
models['Robust'] = bmr_robust

# 2. Compare summaries
for name, model in models.items():
    s = model.summary()
    print(f"{name}: {s['mean']:.3f} [{s['ci_lower']:.3f}, {s['ci_upper']:.3f}]")

# 3. Model comparison
comparison = BayesianMR(data).model_comparison()
best_model = min(comparison, key=lambda k: comparison[k]['waic'])
print(f"Best model: {best_model}")
```

## References

1. Burgess S, Zuber V, Gkatzionis A, et al. (2018). Modal-based estimation via the ratio estimate. *Genetic Epidemiology*, 42(8), 746-758.

2. Watanabe S (2010). Asymptotic equivalence of Bayes cross validation and widely applicable information criterion in singular learning theory. *Journal of Machine Learning Research*, 11, 3571-3594.

3. Gelman A, Rubin DB (1992). Inference from iterative simulation using multiple sequences. *Statistical Science*, 7(4), 457-472.

4. Kass RE, Raftery AE (1995). Bayes factors. *Journal of the American Statistical Association*, 90(430), 773-795.
