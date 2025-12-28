import { useState } from 'react'
import { Copy, Check, ExternalLink } from 'lucide-react'

const examples = [
  {
    title: 'Basic MR Analysis',
    description: 'Load GWAS data and run standard MR methods',
    code: `from pymr import MR, load_gwas, harmonize

# Load exposure and outcome GWAS
exposure = load_gwas("bmi_gwas.tsv.gz")
outcome = load_gwas("diabetes_gwas.tsv.gz")

# Harmonize alleles
data = harmonize(exposure, outcome)

# Run MR
mr = MR(data)
results = mr.run()
print(results)

#    Method     Beta       SE      Pval    N_SNP
# 0  IVW       0.452    0.041    <0.001     192
# 1  Egger     0.398    0.089     0.002     192
# 2  Median    0.445    0.052    <0.001     192`,
  },
  {
    title: 'Using IEU OpenGWAS API',
    description: 'Fetch GWAS directly from the OpenGWAS database',
    code: `from pymr import ieu_gwas_search, ieu_gwas_associations

# Search for BMI GWAS
bmi_studies = ieu_gwas_search("body mass index")
print(bmi_studies[["id", "trait", "sample_size"]])

# Get associations for a specific study
bmi_gwas = ieu_gwas_associations("ukb-b-19953")

# Filter to genome-wide significant
significant = bmi_gwas[bmi_gwas["pval"] < 5e-8]
print(f"Found {len(significant)} significant SNPs")`,
  },
  {
    title: 'Bayesian MR',
    description: 'Full posterior inference with uncertainty quantification',
    code: `from pymr import BayesianMR

# Initialize with harmonized data
bmr = BayesianMR(data, prior_mean=0, prior_sd=1)

# Run MCMC sampling
bmr.sample(n_samples=10000, n_chains=4, warmup=1000)

# Get posterior summary
summary = bmr.summary()
print(f"Effect: {summary['mean']:.3f}")
print(f"95% CI: [{summary['ci_lower']:.3f}, {summary['ci_upper']:.3f}]")

# Compute Bayes factor vs null
bf = bmr.bayes_factor(null_value=0)
print(f"Bayes Factor: {bf:.2f}")

# Visualize posterior
bmr.plot_posterior()`,
  },
  {
    title: 'MR-PRESSO Outlier Detection',
    description: 'Detect and remove pleiotropic SNPs',
    code: `from pymr import mr_presso

# Run MR-PRESSO
result = mr_presso(
    beta_exp, se_exp,
    beta_out, se_out,
    n_simulations=10000
)

# Check for pleiotropy
print(f"Global test p-value: {result['global_test_pval']:.4f}")
print(f"Outliers detected: {result['outlier_indices']}")

# Corrected estimate
print(f"Original beta: {result['original_beta']:.3f}")
print(f"Corrected beta: {result['corrected_beta']:.3f}")`,
  },
  {
    title: 'Sensitivity Analyses',
    description: 'Comprehensive sensitivity checks',
    code: `from pymr import (
    cochrans_q, rucker_q, steiger_filtering,
    leave_one_out, funnel_asymmetry
)

# Heterogeneity test
het = cochrans_q(beta_exp, se_exp, beta_out, se_out,
                 causal_estimate=0.45)
print(f"Q statistic: {het['Q']:.2f}, p={het['Q_pval']:.4f}")
print(f"I² = {het['I2']:.1f}%")

# Rucker's Q (IVW vs Egger comparison)
rucker = rucker_q(beta_exp, se_exp, beta_out, se_out)
print(f"Pleiotropy detected: {rucker['pleiotropy_detected']}")

# Steiger directionality test
steiger = steiger_filtering(beta_exp, se_exp, beta_out, se_out,
                           n_exp=10000, n_out=10000)
print(f"Correct direction: {steiger['direction_correct']}")

# Leave-one-out analysis
loo = leave_one_out(beta_exp, se_exp, beta_out, se_out)
print(loo[["excluded_snp", "beta", "pval"]])`,
  },
  {
    title: 'Multivariable MR',
    description: 'Multiple exposures simultaneously',
    code: `from pymr import MVMR

# Create MVMR object with multiple exposures
mvmr = MVMR()
mvmr.add_exposure("BMI", bmi_gwas)
mvmr.add_exposure("WHR", whr_gwas)
mvmr.add_outcome("T2D", t2d_gwas)

# Harmonize and run
mvmr.harmonize()
results = mvmr.run()

# Direct effects of each exposure
print(results[["exposure", "beta", "se", "pval"]])

# Conditional F-statistics for instrument strength
f_stats = mvmr.conditional_f()
print(f_stats)`,
  },
]

export function CodeExamples() {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  const copyCode = async (code: string, index: number) => {
    await navigator.clipboard.writeText(code)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  return (
    <section className="section">
      <h2>Code Examples</h2>
      <p className="intro">
        Get started with PyMR in minutes. Install with <code>pip install pymr</code>
      </p>

      <div className="examples-grid">
        {examples.map((example, index) => (
          <div key={index} className="example-card">
            <div className="example-header">
              <div>
                <h4>{example.title}</h4>
                <p>{example.description}</p>
              </div>
              <button
                className="copy-btn"
                onClick={() => copyCode(example.code, index)}
              >
                {copiedIndex === index ? (
                  <Check size={16} />
                ) : (
                  <Copy size={16} />
                )}
              </button>
            </div>
            <pre className="code-block">
              <code>{example.code}</code>
            </pre>
          </div>
        ))}
      </div>

      <div className="resources">
        <h3>Resources</h3>
        <div className="resource-links">
          <a href="https://maxghenis.github.io/pymr" target="_blank" rel="noopener">
            <ExternalLink size={16} />
            Full Documentation
          </a>
          <a href="https://github.com/maxghenis/pymr" target="_blank" rel="noopener">
            <ExternalLink size={16} />
            GitHub Repository
          </a>
          <a href="https://pypi.org/project/pymr" target="_blank" rel="noopener">
            <ExternalLink size={16} />
            PyPI Package
          </a>
        </div>
      </div>
    </section>
  )
}
