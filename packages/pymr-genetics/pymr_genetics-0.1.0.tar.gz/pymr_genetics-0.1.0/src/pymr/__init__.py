"""PyMR: Mendelian Randomization in Python.

A modern, test-driven Python package for Mendelian Randomization analysis.

Example:
    >>> from pymr import MR, load_gwas
    >>> exposure = load_gwas("bmi_gwas.tsv.gz")
    >>> outcome = load_gwas("diabetes_gwas.tsv.gz")
    >>> mr = MR(exposure, outcome)
    >>> results = mr.run()
"""

from pymr.mr import MR
from pymr.io import load_gwas
from pymr.harmonize import harmonize
from pymr.methods import mr_presso, ivw, weighted_median, mr_egger, simple_mode, weighted_mode, mr_raps, contamination_mixture
from pymr import plots
from pymr.api import (
    IEUClient,
    get_instruments,
    get_outcome,
    search_gwas,
    list_gwas,
    panukb_list_phenotypes,
    panukb_search,
    panukb_load_gwas,
    gwas_catalog_search,
    gwas_catalog_get_study,
    gwas_catalog_get_associations,
    finngen_list_phenotypes,
    finngen_search,
    finngen_load_gwas,
)
from pymr.sensitivity import (
    steiger_filtering,
    cochrans_q,
    rucker_q,
    leave_one_out,
    single_snp,
    funnel_asymmetry,
)
from pymr.multivariable import MultivariableMR, mvmr_ivw
from pymr.bayesian import BayesianMR
from pymr.clumping import ld_clump, get_ld_matrix

__version__ = "0.1.0"
__all__ = [
    "MR",
    "load_gwas",
    "harmonize",
    "plots",
    "mr_presso",
    "ivw",
    "weighted_median",
    "mr_egger",
    "simple_mode",
    "weighted_mode",
    "mr_raps",
    "contamination_mixture",
    "IEUClient",
    "get_instruments",
    "get_outcome",
    "search_gwas",
    "list_gwas",
    "panukb_list_phenotypes",
    "panukb_search",
    "panukb_load_gwas",
    "gwas_catalog_search",
    "gwas_catalog_get_study",
    "gwas_catalog_get_associations",
    "finngen_list_phenotypes",
    "finngen_search",
    "finngen_load_gwas",
    "steiger_filtering",
    "cochrans_q",
    "rucker_q",
    "leave_one_out",
    "single_snp",
    "funnel_asymmetry",
    "MultivariableMR",
    "mvmr_ivw",
    "BayesianMR",
    "ld_clump",
    "get_ld_matrix",
]
