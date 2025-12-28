"""Main MR analysis class.

The MR class orchestrates Mendelian Randomization analyses, providing
a unified interface for running multiple methods and sensitivity analyses.
"""

from typing import Literal

import numpy as np
import pandas as pd

from pymr import methods


class MR:
    """Mendelian Randomization analysis.

    Args:
        data: Harmonized exposure-outcome data with columns:
            - beta_exp: Exposure effect sizes
            - se_exp: Exposure standard errors
            - beta_out: Outcome effect sizes
            - se_out: Outcome standard errors
            - SNP (optional): SNP identifiers

    Example:
        >>> mr = MR(harmonized_data)
        >>> results = mr.run()
        >>> print(results)
    """

    METHODS = {
        "IVW": methods.ivw,
        "Weighted Median": methods.weighted_median,
        "MR-Egger": methods.mr_egger,
        "Simple Mode": methods.simple_mode,
    }

    def __init__(self, data: pd.DataFrame) -> None:
        """Initialize MR analysis with harmonized data."""
        self._validate_data(data)
        self.data = data.copy()
        self._beta_exp = data["beta_exp"].values
        self._se_exp = data["se_exp"].values
        self._beta_out = data["beta_out"].values
        self._se_out = data["se_out"].values

    def _validate_data(self, data: pd.DataFrame) -> None:
        """Validate input data has required columns."""
        required = ["beta_exp", "se_exp", "beta_out", "se_out"]
        missing = [c for c in required if c not in data.columns]
        if missing:
            msg = f"Missing required columns: {missing}"
            raise ValueError(msg)

    def run(
        self,
        methods: list[str] | None = None,
    ) -> pd.DataFrame:
        """Run MR analysis using specified methods.

        Args:
            methods: List of method names. Default: all available methods.

        Returns:
            DataFrame with columns: method, beta, se, pval, OR, OR_lci,
            OR_uci, nsnp, and method-specific columns.
        """
        if methods is None:
            methods = list(self.METHODS.keys())

        results = []
        for method_name in methods:
            if method_name not in self.METHODS:
                msg = f"Unknown method: {method_name}"
                raise ValueError(msg)

            func = self.METHODS[method_name]
            try:
                result = func(
                    self._beta_exp,
                    self._se_exp,
                    self._beta_out,
                    self._se_out,
                )
                result["method"] = method_name
                results.append(result)
            except (ValueError, np.linalg.LinAlgError) as e:
                # Skip methods that fail (e.g., weighted median with <3 SNPs)
                pass

        return pd.DataFrame(results)

    def heterogeneity(
        self,
        method: Literal["IVW", "MR-Egger"] = "IVW",
    ) -> dict[str, float]:
        """Compute heterogeneity statistics.

        Tests whether all instruments estimate the same causal effect.
        Significant heterogeneity may indicate pleiotropy.

        Args:
            method: Which method's residuals to use

        Returns:
            Dictionary with Q statistic, Q_pval, and I2
        """
        wald_ratio = self._beta_out / self._beta_exp
        wald_se = np.abs(self._se_out / self._beta_exp)
        weights = 1 / wald_se**2

        # Get point estimate
        if method == "IVW":
            beta = np.sum(wald_ratio * weights) / np.sum(weights)
        else:
            # MR-Egger uses slope from regression
            result = methods.mr_egger(
                self._beta_exp,
                self._se_exp,
                self._beta_out,
                self._se_out,
            )
            beta = result["beta"]

        # Cochran's Q
        q = float(np.sum(weights * (wald_ratio - beta) ** 2))
        df = len(self._beta_exp) - 1 if method == "IVW" else len(self._beta_exp) - 2
        q_pval = 1 - float(stats.chi2.cdf(q, df)) if df > 0 else 1.0

        # I-squared
        i2 = max(0, (q - df) / q * 100) if q > 0 else 0.0

        return {
            "Q": q,
            "Q_df": df,
            "Q_pval": q_pval,
            "I2": i2,
        }

    def leave_one_out(
        self,
        method: str = "IVW",
    ) -> pd.DataFrame:
        """Leave-one-out sensitivity analysis.

        Reruns the analysis excluding each SNP in turn to identify
        influential instruments.

        Args:
            method: Which method to use

        Returns:
            DataFrame with one row per SNP, showing estimate when that
            SNP is excluded
        """
        if method not in self.METHODS:
            msg = f"Unknown method: {method}"
            raise ValueError(msg)

        func = self.METHODS[method]
        results = []

        snp_ids = (
            self.data["SNP"].values
            if "SNP" in self.data.columns
            else np.arange(len(self.data))
        )

        for i in range(len(self.data)):
            mask = np.ones(len(self.data), dtype=bool)
            mask[i] = False

            try:
                result = func(
                    self._beta_exp[mask],
                    self._se_exp[mask],
                    self._beta_out[mask],
                    self._se_out[mask],
                )
                result["excluded_snp"] = snp_ids[i]
                results.append(result)
            except (ValueError, np.linalg.LinAlgError):
                pass

        return pd.DataFrame(results)


# Import stats here to avoid circular import
from scipy import stats
