"""Tests for funnel plot with asymmetry test (TDD)."""

import numpy as np
import pandas as pd
import pytest

from pymr.plots import funnel_plot


class TestFunnelPlotAsymmetry:
    """Test funnel plot with asymmetry test integration."""

    @pytest.fixture
    def harmonized_data(self):
        """Create sample harmonized data."""
        np.random.seed(42)
        n = 20
        return pd.DataFrame({
            "beta_exp": np.random.uniform(0.1, 0.3, n),
            "se_exp": np.random.uniform(0.01, 0.03, n),
            "beta_out": np.random.uniform(0.05, 0.15, n),
            "se_out": np.random.uniform(0.02, 0.04, n),
        })

    def test_funnel_plot_basic(self, harmonized_data):
        """Basic funnel plot should work without optional parameters."""
        fig = funnel_plot(harmonized_data)
        assert fig is not None

    def test_funnel_plot_with_asymmetry_test(self, harmonized_data):
        """Funnel plot should show asymmetry test results when requested."""
        fig = funnel_plot(harmonized_data, show_asymmetry_test=True)
        assert fig is not None

        # Check that legend contains asymmetry test
        ax = fig.axes[0]
        legend_text = ax.get_legend().get_texts()
        legend_labels = [text.get_text() for text in legend_text]

        # Should have "Asymmetry test: p=..." in legend
        assert any("Asymmetry test" in label for label in legend_labels)

    def test_funnel_plot_with_contours(self, harmonized_data):
        """Funnel plot should show significance contours when requested."""
        fig = funnel_plot(harmonized_data, show_contours=True)
        assert fig is not None

        # Check that legend contains contour labels
        ax = fig.axes[0]
        legend_text = ax.get_legend().get_texts()
        legend_labels = [text.get_text() for text in legend_text]

        # Should have p-value labels in legend
        assert any("p=0.05" in label for label in legend_labels)
        assert any("p=0.01" in label for label in legend_labels)

    def test_funnel_plot_with_both_options(self, harmonized_data):
        """Funnel plot should work with both contours and asymmetry test."""
        fig = funnel_plot(
            harmonized_data,
            show_contours=True,
            show_asymmetry_test=True,
        )
        assert fig is not None

    def test_funnel_plot_with_few_snps(self):
        """Funnel plot should handle case with <3 SNPs gracefully."""
        # Only 2 SNPs - asymmetry test won't run
        small_data = pd.DataFrame({
            "beta_exp": [0.1, 0.2],
            "se_exp": [0.01, 0.02],
            "beta_out": [0.05, 0.10],
            "se_out": [0.02, 0.03],
        })

        # Should not crash even with show_asymmetry_test=True
        fig = funnel_plot(small_data, show_asymmetry_test=True)
        assert fig is not None
