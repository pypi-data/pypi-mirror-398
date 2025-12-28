# PyMR Roadmap: Beyond R

## Vision

PyMR aims to be the **definitive Mendelian Randomization package** - not just matching TwoSampleMR but exceeding it with modern capabilities that R packages can't easily provide.

## Phase 1: Feature Parity with R (v0.2)

### Core Methods
- [x] IVW (inverse variance weighted)
- [x] Weighted median
- [x] MR-Egger
- [x] Simple mode
- [x] MR-PRESSO (pleiotropy residual sum and outlier)
- [x] Weighted mode
- [x] MR-RAPS (robust adjusted profile score)
- [x] Contamination mixture

### Sensitivity Analyses
- [x] Heterogeneity (Cochran's Q, I²)
- [x] Rucker's Q (IVW vs Egger comparison)
- [x] Leave-one-out
- [x] Single SNP analysis
- [x] Steiger filtering (directionality test)
- [x] Funnel plot asymmetry tests

### Data Integration
- [x] IEU OpenGWAS API (16,000+ GWAS)
- [x] Local file loading
- [x] GWAS Catalog integration
- [x] Pan-UKB direct access
- [x] FinnGen integration

### Clumping
- [x] Distance-based pruning
- [x] LD matrix-based clumping (1000 Genomes)
- [ ] In-memory LD calculation
- [ ] Ancestry-aware clumping

### Visualization
- [x] Forest plots
- [x] Scatter plots with regression lines
- [x] Funnel plots
- [x] Leave-one-out plots
- [x] Radial plots

### Multivariable MR
- [x] MVMR-IVW
- [x] MVMR-Egger
- [x] MVMR-Lasso (with L1 penalization)
- [x] Conditional F-statistics

### Bayesian MR
- [x] Bayesian IVW with full posterior inference
- [x] Bayesian Egger with intercept prior
- [x] Robust Bayesian MR (t-distribution for outliers)
- [x] MCMC sampling (Metropolis-Hastings)
- [x] Convergence diagnostics (R-hat, effective sample size)
- [x] Posterior visualization
- [x] Bayes factors
- [x] Model comparison (WAIC)

## Phase 2: Beyond R (v0.3)

### Network MR
```python
# Multiple exposures and outcomes simultaneously
network = MRNetwork()
network.add_exposure("BMI", bmi_gwas)
network.add_exposure("Physical Activity", pa_gwas)
network.add_outcome("T2DM", t2dm_gwas)
network.add_outcome("CVD", cvd_gwas)
network.fit()
network.plot_dag()  # Interactive DAG visualization
```

**Why this matters**: Real biology is complex. Analyze entire causal networks, not just pairs.

### Natural Language Interface
```python
from pymr import ask

# Plain English queries
result = ask("Does obesity cause type 2 diabetes?")
result = ask("What's the causal effect of education on income?")
result = ask("Compare alcohol's effect on liver disease vs cardiovascular disease")
```

**Why this matters**: Democratize MR for non-programmers. LLM selects appropriate GWAS, runs analysis, interprets results.

### Auto-Validation Against RCTs
```python
# Automatically compare MR estimates to published RCT results
mr = MR(data)
validation = mr.validate_against_rcts()
# Searches literature for relevant trials
# Compares effect sizes
# Flags discrepancies
```

### Real-Time GWAS Updates
```python
# Subscribe to new GWAS releases
pymr.subscribe("BMI", callback=update_model)
# Automatically re-run analyses when new data available
```

### GPU Acceleration
```python
# Process millions of variants in seconds
mr = MR(data, device="cuda")
# 100x speedup for large-scale analyses
```

### Interactive Dashboard
```python
pymr.launch_dashboard()
# Opens browser with:
# - Drag-and-drop GWAS upload
# - Point-and-click method selection
# - Interactive visualizations
# - Auto-generated reports
```

## Phase 3: OptiqAL Integration (v1.0)

### QALY Validation Badge
```python
from pymr.optiqal import validate_qaly_model

# Validate OptiqAL hazard ratios against MR causal estimates
report = validate_qaly_model(
    model_estimates={"BMI->T2DM": 1.75, "BMI->CVD": 1.40},
    genetic_data="auto"  # Auto-fetch from Pan-UKB
)
report.calibration_plot()
report.badge()  # "Validated against genetic causal estimates"
```

### Causal QALY Calculator
```python
from pymr.optiqal import CausalQALY

# Calculate QALYs with MR-validated causal effects
calculator = CausalQALY()
calculator.add_intervention("weight_loss", kg=-5)
qalys = calculator.estimate(
    use_mr_validation=True,
    uncertainty="bayesian"
)
print(f"Expected QALY gain: {qalys.mean:.2f} ({qalys.ci95})")
```

### Intervention Optimizer
```python
# Find optimal intervention portfolio using MR-validated effects
from pymr.optiqal import optimize_interventions

portfolio = optimize_interventions(
    budget=1000,  # dollars per person per year
    outcomes=["qalys", "dalys_averted"],
    constraints={"adherence": ">0.5"}
)
```

## Competitive Advantages

| Capability | TwoSampleMR | MendelianRandomization | PyMR |
|------------|-------------|------------------------|------|
| Point estimates | ✓ | ✓ | ✓ |
| Full posteriors (Bayesian) | ✗ | ✗ | **✓** |
| Multivariable MR | ✓ | ✓ | **✓** |
| MR-PRESSO | ✓ | ✗ | **✓** |
| OpenGWAS API | ✓ | ✗ | **✓** |
| Publication-ready plots | ✓ | ✓ | **✓** |
| Network MR | Limited | ✗ | Planned |
| Natural language | ✗ | ✗ | Planned |
| GPU acceleration | ✗ | ✗ | Planned |
| Interactive dashboard | ✗ | ✗ | Planned |
| QALY integration | ✗ | ✗ | Planned |
| Auto-validation | ✗ | ✗ | Planned |
| No PLINK needed | ✗ | ✓ | ✓ |
| Python ecosystem | ✗ | ✗ | **✓** |

## Timeline

- **v0.2** (Q1 2026): Feature parity with R
- **v0.3** (Q2 2026): Bayesian MR, Network MR, NL interface
- **v1.0** (Q3 2026): Full OptiqAL integration, production ready

## Contributing

We welcome contributions! Priority areas:
1. IEU API integration
2. MR-PRESSO implementation
3. Visualization suite
4. Documentation and tutorials
