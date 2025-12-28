"""Pytest configuration and fixtures."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_harmonized_data():
    """Create sample harmonized data for testing."""
    np.random.seed(42)
    n = 50
    return pd.DataFrame({
        "SNP": [f"rs{i}" for i in range(n)],
        "beta_exp": np.random.normal(0.1, 0.02, n),
        "se_exp": np.abs(np.random.normal(0.01, 0.002, n)),
        "beta_out": np.random.normal(0.05, 0.02, n),
        "se_out": np.abs(np.random.normal(0.02, 0.005, n)),
    })


@pytest.fixture
def small_harmonized_data():
    """Small dataset for simple tests."""
    return pd.DataFrame({
        "SNP": ["rs1", "rs2", "rs3", "rs4", "rs5"],
        "beta_exp": [0.1, 0.2, 0.15, 0.12, 0.18],
        "se_exp": [0.01, 0.02, 0.015, 0.01, 0.02],
        "beta_out": [0.05, 0.10, 0.075, 0.06, 0.09],
        "se_out": [0.02, 0.03, 0.025, 0.02, 0.03],
    })
