"""Bayesian Mendelian Randomization with full posterior inference.

Implements Bayesian MR methods using Metropolis-Hastings MCMC sampling:
- Bayesian IVW (normal likelihood)
- Bayesian Egger (with intercept prior)
- Robust Bayesian MR (t-distribution for outliers)

Uses scipy for simple MCMC - no PyMC/Stan dependency.

References:
    Burgess S, Zuber V, Gkatzionis A, et al. (2018).
    Modal-based estimation via the ratio estimate.
    Genetic Epidemiology, 42(8), 746-758.
"""

from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy import stats


class BayesianMR:
    """Bayesian Mendelian Randomization with full posterior inference.

    Args:
        data: Harmonized exposure-outcome data with columns:
            - beta_exp: Exposure effect sizes
            - se_exp: Exposure standard errors
            - beta_out: Outcome effect sizes
            - se_out: Outcome standard errors
        prior_mean: Prior mean for causal effect (beta)
        prior_sd: Prior standard deviation for causal effect
        intercept_prior_mean: Prior mean for Egger intercept
        intercept_prior_sd: Prior standard deviation for Egger intercept

    Example:
        >>> bmr = BayesianMR(harmonized_data)
        >>> samples = bmr.sample(n_samples=10000, n_chains=4)
        >>> summary = bmr.summary()
        >>> print(summary)
    """

    def __init__(
        self,
        data: pd.DataFrame,
        prior_mean: float = 0,
        prior_sd: float = 1,
        intercept_prior_mean: float = 0,
        intercept_prior_sd: float = 0.5,
    ) -> None:
        """Initialize Bayesian MR with harmonized data and priors."""
        self._validate_data(data)
        self.data = data.copy()
        self.prior_mean = prior_mean
        self.prior_sd = prior_sd
        self.intercept_prior_mean = intercept_prior_mean
        self.intercept_prior_sd = intercept_prior_sd

        # Extract data arrays
        self._beta_exp = data["beta_exp"].values
        self._se_exp = data["se_exp"].values
        self._beta_out = data["beta_out"].values
        self._se_out = data["se_out"].values

        # Compute Wald ratios and weights
        self._wald_ratio = self._beta_out / self._beta_exp
        self._wald_se = np.abs(self._se_out / self._beta_exp)
        self._weights = 1 / self._wald_se**2

        # Store samples after running MCMC
        self._samples: NDArray[np.floating[Any]] | None = None
        self._intercept_samples: NDArray[np.floating[Any]] | None = None
        self._nu_samples: NDArray[np.floating[Any]] | None = None
        self._model: str | None = None

    def _validate_data(self, data: pd.DataFrame) -> None:
        """Validate input data has required columns."""
        required = ["beta_exp", "se_exp", "beta_out", "se_out"]
        missing = [c for c in required if c not in data.columns]
        if missing:
            msg = f"Missing required columns: {missing}"
            raise ValueError(msg)

    def sample(
        self,
        n_samples: int = 10000,
        n_chains: int = 4,
        warmup: int = 1000,
        model: Literal["ivw", "egger", "robust_ivw"] = "ivw",
    ) -> NDArray[np.floating[Any]]:
        """Run MCMC sampling using Metropolis-Hastings.

        Args:
            n_samples: Number of posterior samples per chain
            n_chains: Number of independent chains
            warmup: Number of warmup/burn-in samples to discard
            model: Which model to fit ("ivw", "egger", or "robust_ivw")

        Returns:
            Posterior samples array of shape (n_chains, n_samples)
        """
        self._model = model
        rng = np.random.default_rng(42)

        all_samples = []
        all_intercept_samples = []
        all_nu_samples = []

        for chain in range(n_chains):
            if model == "ivw":
                samples = self._sample_ivw(n_samples + warmup, rng)
                all_samples.append(samples[warmup:])
            elif model == "egger":
                beta_samples, intercept_samples = self._sample_egger(
                    n_samples + warmup, rng
                )
                all_samples.append(beta_samples[warmup:])
                all_intercept_samples.append(intercept_samples[warmup:])
            elif model == "robust_ivw":
                beta_samples, nu_samples = self._sample_robust_ivw(
                    n_samples + warmup, rng
                )
                all_samples.append(beta_samples[warmup:])
                all_nu_samples.append(nu_samples[warmup:])
            else:
                msg = f"Unknown model: {model}"
                raise ValueError(msg)

        self._samples = np.array(all_samples)
        if all_intercept_samples:
            self._intercept_samples = np.array(all_intercept_samples)
        if all_nu_samples:
            self._nu_samples = np.array(all_nu_samples)

        return self._samples

    def _sample_ivw(
        self,
        n_samples: int,
        rng: np.random.Generator,
    ) -> NDArray[np.floating[Any]]:
        """Sample from Bayesian IVW posterior using Metropolis-Hastings.

        Uses normal likelihood with inverse variance weighting.
        """
        samples = np.zeros(n_samples)

        # Initialize at weighted mean
        current = np.sum(self._wald_ratio * self._weights) / np.sum(self._weights)

        # Proposal standard deviation (tuned for ~25% acceptance)
        proposal_sd = 1 / np.sqrt(np.sum(self._weights))

        n_accepted = 0

        for i in range(n_samples):
            # Propose new value
            proposed = current + rng.normal(0, proposal_sd)

            # Log posterior = log likelihood + log prior
            log_post_current = self._log_posterior_ivw(current)
            log_post_proposed = self._log_posterior_ivw(proposed)

            # Metropolis acceptance ratio
            log_accept_ratio = log_post_proposed - log_post_current

            if np.log(rng.uniform()) < log_accept_ratio:
                current = proposed
                n_accepted += 1

            samples[i] = current

        return samples

    def _log_posterior_ivw(self, beta: float) -> float:
        """Compute log posterior for IVW model."""
        # Log likelihood: weighted sum of squared deviations
        log_lik = -0.5 * np.sum(self._weights * (self._wald_ratio - beta) ** 2)

        # Log prior: normal
        log_prior = stats.norm.logpdf(beta, loc=self.prior_mean, scale=self.prior_sd)

        return float(log_lik + log_prior)

    def _sample_egger(
        self,
        n_samples: int,
        rng: np.random.Generator,
    ) -> tuple[NDArray[np.floating[Any]], NDArray[np.floating[Any]]]:
        """Sample from Bayesian Egger posterior.

        Samples both slope (beta) and intercept jointly.
        """
        beta_samples = np.zeros(n_samples)
        intercept_samples = np.zeros(n_samples)

        # Initialize at weighted regression estimates
        # Ensure positive exposure effects
        sign = np.sign(self._beta_exp)
        beta_exp_oriented = np.abs(self._beta_exp)
        beta_out_oriented = self._beta_out * sign

        weights = 1 / self._se_out**2
        X = np.column_stack([np.ones(len(self._beta_exp)), beta_exp_oriented])
        W = np.diag(weights)
        XtWX = X.T @ W @ X
        XtWy = X.T @ W @ beta_out_oriented

        try:
            coef = np.linalg.solve(XtWX, XtWy)
            current_intercept, current_beta = coef
        except np.linalg.LinAlgError:
            current_beta = np.mean(beta_out_oriented / beta_exp_oriented)
            current_intercept = 0.0

        # Proposal SDs (tuned for ~25% acceptance)
        # Use se_out for weighting
        proposal_sd_beta = 0.05  # Start with reasonable value
        proposal_sd_intercept = 0.02

        n_accepted = 0

        for i in range(n_samples):
            # Propose new values
            proposed_beta = current_beta + rng.normal(0, proposal_sd_beta)
            proposed_intercept = current_intercept + rng.normal(0, proposal_sd_intercept)

            # Log posterior
            log_post_current = self._log_posterior_egger(current_beta, current_intercept)
            log_post_proposed = self._log_posterior_egger(
                proposed_beta, proposed_intercept
            )

            # Metropolis acceptance
            log_accept_ratio = log_post_proposed - log_post_current

            if np.log(rng.uniform()) < log_accept_ratio:
                current_beta = proposed_beta
                current_intercept = proposed_intercept
                n_accepted += 1

            beta_samples[i] = current_beta
            intercept_samples[i] = current_intercept

        return beta_samples, intercept_samples

    def _log_posterior_egger(self, beta: float, intercept: float) -> float:
        """Compute log posterior for Egger model.

        The Egger model is: beta_out = intercept + beta * beta_exp + error
        where error ~ N(0, se_out^2)
        """
        # Ensure positive exposure effects (InSIDE assumption)
        sign = np.sign(self._beta_exp)
        beta_exp_oriented = np.abs(self._beta_exp)
        beta_out_oriented = self._beta_out * sign

        # Expected outcome values
        expected = intercept + beta * beta_exp_oriented

        # Log likelihood: weighted regression
        weights = 1 / self._se_out**2
        log_lik = -0.5 * np.sum(weights * (beta_out_oriented - expected) ** 2)

        # Log priors
        log_prior_beta = stats.norm.logpdf(beta, loc=self.prior_mean, scale=self.prior_sd)
        log_prior_intercept = stats.norm.logpdf(
            intercept, loc=self.intercept_prior_mean, scale=self.intercept_prior_sd
        )

        return float(log_lik + log_prior_beta + log_prior_intercept)

    def _sample_robust_ivw(
        self,
        n_samples: int,
        rng: np.random.Generator,
    ) -> tuple[NDArray[np.floating[Any]], NDArray[np.floating[Any]]]:
        """Sample from robust Bayesian IVW with t-distribution likelihood.

        The t-distribution has heavier tails than normal, making it robust
        to outliers. Also samples degrees of freedom (nu).
        """
        beta_samples = np.zeros(n_samples)
        nu_samples = np.zeros(n_samples)

        # Initialize
        current_beta = np.sum(self._wald_ratio * self._weights) / np.sum(self._weights)
        current_nu = 10.0  # Start with moderate tail weight

        # Proposal SDs
        proposal_sd_beta = 1 / np.sqrt(np.sum(self._weights))
        proposal_sd_nu = 2.0

        for i in range(n_samples):
            # Propose beta
            proposed_beta = current_beta + rng.normal(0, proposal_sd_beta)

            log_post_current = self._log_posterior_robust_ivw(current_beta, current_nu)
            log_post_proposed = self._log_posterior_robust_ivw(proposed_beta, current_nu)

            if np.log(rng.uniform()) < log_post_proposed - log_post_current:
                current_beta = proposed_beta

            # Propose nu (on log scale for better sampling)
            log_nu_current = np.log(current_nu)
            log_nu_proposed = log_nu_current + rng.normal(0, 0.3)
            proposed_nu = np.exp(log_nu_proposed)

            # Ensure nu > 2 (for finite variance)
            if proposed_nu > 2:
                log_post_current = self._log_posterior_robust_ivw(current_beta, current_nu)
                log_post_proposed = self._log_posterior_robust_ivw(current_beta, proposed_nu)

                # Include Jacobian for log transformation
                log_accept = (
                    log_post_proposed - log_post_current + log_nu_proposed - log_nu_current
                )

                if np.log(rng.uniform()) < log_accept:
                    current_nu = proposed_nu

            beta_samples[i] = current_beta
            nu_samples[i] = current_nu

        return beta_samples, nu_samples

    def _log_posterior_robust_ivw(self, beta: float, nu: float) -> float:
        """Compute log posterior for robust IVW with t-distribution."""
        # Standardized residuals
        residuals = (self._wald_ratio - beta) / self._wald_se

        # Log likelihood: sum of log t-distribution PDFs
        log_lik = np.sum(stats.t.logpdf(residuals, df=nu))

        # Log priors
        log_prior_beta = stats.norm.logpdf(beta, loc=self.prior_mean, scale=self.prior_sd)
        # Prior for nu: exponential with mean 10
        log_prior_nu = stats.expon.logpdf(nu - 2, scale=8)

        return float(log_lik + log_prior_beta + log_prior_nu)

    def summary(self) -> dict[str, float]:
        """Return posterior summary statistics.

        Returns:
            Dictionary with:
                - mean: Posterior mean
                - sd: Posterior standard deviation
                - ci_lower: Lower 95% credible interval
                - ci_upper: Upper 95% credible interval
                - rhat: Gelman-Rubin convergence diagnostic
                - n_eff: Effective sample size
                - For Egger: beta_mean, intercept_mean, intercept_ci_lower, intercept_ci_upper
                - For robust: nu_mean (degrees of freedom)
        """
        if self._samples is None:
            msg = "Must call sample() before summary()"
            raise RuntimeError(msg)

        # Flatten chains for summary statistics
        samples_flat = self._samples.flatten()

        summary: dict[str, float] = {
            "mean": float(np.mean(samples_flat)),
            "sd": float(np.std(samples_flat)),
            "ci_lower": float(np.percentile(samples_flat, 2.5)),
            "ci_upper": float(np.percentile(samples_flat, 97.5)),
            "rhat": float(self._compute_rhat(self._samples)),
            "n_eff": float(self._compute_n_eff(samples_flat)),
        }

        # Add model-specific summaries
        if self._model == "egger" and self._intercept_samples is not None:
            intercept_flat = self._intercept_samples.flatten()
            summary.update(
                {
                    "beta_mean": summary["mean"],
                    "intercept_mean": float(np.mean(intercept_flat)),
                    "intercept_sd": float(np.std(intercept_flat)),
                    "intercept_ci_lower": float(np.percentile(intercept_flat, 2.5)),
                    "intercept_ci_upper": float(np.percentile(intercept_flat, 97.5)),
                }
            )

        if self._model == "robust_ivw" and self._nu_samples is not None:
            nu_flat = self._nu_samples.flatten()
            summary["nu_mean"] = float(np.mean(nu_flat))
            summary["nu_sd"] = float(np.std(nu_flat))

        return summary

    def _compute_rhat(self, samples: NDArray[np.floating[Any]]) -> float:
        """Compute Gelman-Rubin R-hat convergence diagnostic.

        R-hat compares within-chain and between-chain variance.
        Values close to 1 indicate convergence.
        """
        n_chains, n_samples = samples.shape

        if n_chains < 2:
            return 1.0

        # Within-chain variance
        W = np.mean(np.var(samples, axis=1, ddof=1))

        # Between-chain variance
        chain_means = np.mean(samples, axis=1)
        B = n_samples * np.var(chain_means, ddof=1)

        # Pooled variance estimate
        var_plus = ((n_samples - 1) * W + B) / n_samples

        # R-hat
        rhat = np.sqrt(var_plus / W) if W > 0 else 1.0

        return float(rhat)

    def _compute_n_eff(self, samples: NDArray[np.floating[Any]]) -> float:
        """Compute effective sample size accounting for autocorrelation."""
        n = len(samples)

        # Compute autocorrelation
        samples_centered = samples - np.mean(samples)
        autocorr = np.correlate(samples_centered, samples_centered, mode="full")
        autocorr = autocorr[len(autocorr) // 2 :]
        autocorr = autocorr / autocorr[0]

        # Sum autocorrelations until they become negative
        rho_sum = 1.0
        for i in range(1, min(len(autocorr), 100)):
            if autocorr[i] < 0:
                break
            rho_sum += 2 * autocorr[i]

        n_eff = n / rho_sum if rho_sum > 0 else n

        return float(max(n_eff, 1.0))

    def bayes_factor(self, null_value: float = 0) -> float:
        """Compute Bayes factor for causal effect vs null.

        Uses Savage-Dickey density ratio at the null value.

        Args:
            null_value: Null hypothesis value (default: 0)

        Returns:
            Bayes factor (BF > 1 favors alternative, BF < 1 favors null)
        """
        if self._samples is None:
            msg = "Must call sample() before bayes_factor()"
            raise RuntimeError(msg)

        samples_flat = self._samples.flatten()

        # Posterior density at null using kernel density estimation
        kde = stats.gaussian_kde(samples_flat)
        posterior_density = kde.evaluate([null_value])[0]

        # Prior density at null
        prior_density = stats.norm.pdf(null_value, loc=self.prior_mean, scale=self.prior_sd)

        # Savage-Dickey ratio
        bf = prior_density / posterior_density if posterior_density > 0 else np.inf

        return float(bf)

    def model_comparison(
        self,
        models: list[str] | None = None,
    ) -> dict[str, dict[str, float]]:
        """Compare models using WAIC (Watanabe-Akaike Information Criterion).

        WAIC is a Bayesian alternative to AIC that accounts for posterior
        uncertainty. Lower WAIC indicates better model fit.

        Args:
            models: List of model names to compare (default: ["ivw", "egger"])

        Returns:
            Dictionary mapping model name to dict with "waic" and "se" keys
        """
        if models is None:
            models = ["ivw", "egger"]

        results = {}

        for model_name in models:
            # Fit model
            self.sample(n_samples=5000, n_chains=4, warmup=500, model=model_name)  # type: ignore

            # Compute WAIC
            waic = self._compute_waic()
            results[model_name] = waic

        return results

    def _compute_waic(self) -> dict[str, float]:
        """Compute WAIC for current model."""
        if self._samples is None:
            msg = "Must call sample() before computing WAIC"
            raise RuntimeError(msg)

        samples_flat = self._samples.flatten()
        n_samples = len(samples_flat)

        # Compute log pointwise predictive density for each data point
        lppd = np.zeros(len(self._beta_out))
        pwaic = np.zeros(len(self._beta_out))

        for i in range(len(self._beta_out)):
            # Log likelihood for each sample
            if self._model == "ivw":
                log_liks = np.array(
                    [
                        stats.norm.logpdf(
                            self._wald_ratio[i],
                            loc=beta,
                            scale=self._wald_se[i],
                        )
                        for beta in samples_flat
                    ]
                )
            elif self._model == "egger" and self._intercept_samples is not None:
                intercept_flat = self._intercept_samples.flatten()
                sign = np.sign(self._beta_exp[i])
                beta_exp_oriented = np.abs(self._beta_exp[i])
                beta_out_oriented = self._beta_out[i] * sign
                log_liks = np.array(
                    [
                        stats.norm.logpdf(
                            beta_out_oriented,
                            loc=intercept_flat[j] + samples_flat[j] * beta_exp_oriented,
                            scale=self._se_out[i],
                        )
                        for j in range(n_samples)
                    ]
                )
            else:
                log_liks = np.array(
                    [
                        stats.norm.logpdf(
                            self._wald_ratio[i],
                            loc=beta,
                            scale=self._wald_se[i],
                        )
                        for beta in samples_flat
                    ]
                )

            # Log pointwise predictive density
            lppd[i] = np.log(np.mean(np.exp(log_liks)))

            # Effective number of parameters
            pwaic[i] = np.var(log_liks)

        # WAIC = -2 * (lppd - pwaic)
        waic = -2 * (np.sum(lppd) - np.sum(pwaic))
        se_waic = 2 * np.std(lppd - pwaic) * np.sqrt(len(self._wald_ratio))

        return {"waic": float(waic), "se": float(se_waic)}

    def plot_posterior(
        self,
        ax: plt.Axes | None = None,
    ) -> plt.Axes:
        """Plot posterior density.

        Args:
            ax: Matplotlib axis (creates new if None)

        Returns:
            Matplotlib axis with posterior plot
        """
        if self._samples is None:
            msg = "Must call sample() before plot_posterior()"
            raise RuntimeError(msg)

        if ax is None:
            _, ax = plt.subplots(figsize=(8, 5))

        samples_flat = self._samples.flatten()

        # Plot posterior density
        ax.hist(samples_flat, bins=50, density=True, alpha=0.6, label="Posterior")

        # Plot prior
        x_range = np.linspace(
            min(samples_flat.min(), self.prior_mean - 3 * self.prior_sd),
            max(samples_flat.max(), self.prior_mean + 3 * self.prior_sd),
            200,
        )
        prior_density = stats.norm.pdf(x_range, loc=self.prior_mean, scale=self.prior_sd)
        ax.plot(x_range, prior_density, "r--", label="Prior", linewidth=2)

        # Add credible interval
        summary = self.summary()
        ax.axvline(summary["mean"], color="black", linestyle="-", linewidth=2, label="Posterior mean")
        ax.axvline(summary["ci_lower"], color="black", linestyle=":", alpha=0.7)
        ax.axvline(summary["ci_upper"], color="black", linestyle=":", alpha=0.7)

        ax.set_xlabel("Causal Effect (β)")
        ax.set_ylabel("Density")
        ax.set_title("Bayesian MR Posterior Distribution")
        ax.legend()
        ax.grid(True, alpha=0.3)

        return ax
