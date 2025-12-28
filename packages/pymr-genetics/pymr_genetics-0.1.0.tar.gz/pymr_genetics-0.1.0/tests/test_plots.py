"""Tests for MR visualization functions (TDD - write tests first)."""

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

from pymr import MR


class TestForestPlot:
    """Test forest plot of MR estimates across methods."""

    @pytest.fixture
    def sample_results(self):
        """Sample MR results DataFrame."""
        return pd.DataFrame({
            "method": ["IVW", "Weighted Median", "MR-Egger"],
            "beta": [0.5, 0.48, 0.52],
            "se": [0.1, 0.12, 0.15],
            "pval": [1e-5, 1e-4, 1e-3],
            "OR": [1.65, 1.62, 1.68],
            "OR_lci": [1.35, 1.28, 1.25],
            "OR_uci": [2.01, 2.05, 2.26],
            "nsnp": [50, 50, 50],
        })

    def test_forest_plot_creates_figure(self, sample_results):
        """forest_plot should return matplotlib Figure."""
        from pymr.plots import forest_plot

        fig = forest_plot(sample_results)

        assert isinstance(fig, Figure)

    def test_forest_plot_with_ax_parameter(self, sample_results):
        """forest_plot should accept optional ax parameter."""
        import matplotlib.pyplot as plt
        from pymr.plots import forest_plot

        fig, ax = plt.subplots()
        result_fig = forest_plot(sample_results, ax=ax)

        assert result_fig is fig
        plt.close(fig)

    def test_forest_plot_shows_all_methods(self, sample_results):
        """forest_plot should display all methods in results."""
        from pymr.plots import forest_plot

        fig = forest_plot(sample_results)
        ax = fig.axes[0]

        # Check that y-axis has all methods
        yticks = ax.get_yticklabels()
        method_labels = [t.get_text() for t in yticks]

        assert any("IVW" in label for label in method_labels)
        assert any("Weighted Median" in label for label in method_labels)


class TestScatterPlot:
    """Test scatter plot of SNP effects."""

    @pytest.fixture
    def sample_harmonized(self):
        """Sample harmonized data."""
        np.random.seed(42)
        n = 50
        return pd.DataFrame({
            "SNP": [f"rs{i}" for i in range(n)],
            "beta_exp": np.random.normal(0.1, 0.02, n),
            "se_exp": np.abs(np.random.normal(0.01, 0.002, n)),
            "beta_out": np.random.normal(0.05, 0.02, n),
            "se_out": np.abs(np.random.normal(0.02, 0.005, n)),
        })

    def test_scatter_plot_creates_figure(self, sample_harmonized):
        """scatter_plot should return matplotlib Figure."""
        from pymr.plots import scatter_plot

        fig = scatter_plot(sample_harmonized)

        assert isinstance(fig, Figure)

    def test_scatter_plot_with_method(self, sample_harmonized):
        """scatter_plot should accept method parameter."""
        from pymr.plots import scatter_plot

        fig = scatter_plot(sample_harmonized, method="IVW")

        assert isinstance(fig, Figure)

    def test_scatter_plot_with_ax(self, sample_harmonized):
        """scatter_plot should accept optional ax parameter."""
        import matplotlib.pyplot as plt
        from pymr.plots import scatter_plot

        fig, ax = plt.subplots()
        result_fig = scatter_plot(sample_harmonized, ax=ax)

        assert result_fig is fig
        plt.close(fig)


class TestFunnelPlot:
    """Test funnel plot for publication bias."""

    @pytest.fixture
    def sample_harmonized(self):
        """Sample harmonized data."""
        np.random.seed(42)
        n = 50
        return pd.DataFrame({
            "SNP": [f"rs{i}" for i in range(n)],
            "beta_exp": np.random.normal(0.1, 0.02, n),
            "se_exp": np.abs(np.random.normal(0.01, 0.002, n)),
            "beta_out": np.random.normal(0.05, 0.02, n),
            "se_out": np.abs(np.random.normal(0.02, 0.005, n)),
        })

    def test_funnel_plot_creates_figure(self, sample_harmonized):
        """funnel_plot should return matplotlib Figure."""
        from pymr.plots import funnel_plot

        fig = funnel_plot(sample_harmonized)

        assert isinstance(fig, Figure)

    def test_funnel_plot_with_ax(self, sample_harmonized):
        """funnel_plot should accept optional ax parameter."""
        import matplotlib.pyplot as plt
        from pymr.plots import funnel_plot

        fig, ax = plt.subplots()
        result_fig = funnel_plot(sample_harmonized, ax=ax)

        assert result_fig is fig
        plt.close(fig)


class TestLeaveOneOutPlot:
    """Test leave-one-out sensitivity plot."""

    @pytest.fixture
    def sample_loo_results(self):
        """Sample leave-one-out results."""
        np.random.seed(42)
        n = 50
        return pd.DataFrame({
            "excluded_snp": [f"rs{i}" for i in range(n)],
            "beta": np.random.normal(0.5, 0.02, n),
            "se": np.abs(np.random.normal(0.1, 0.01, n)),
            "OR": np.exp(np.random.normal(0.5, 0.02, n)),
            "OR_lci": np.exp(np.random.normal(0.4, 0.02, n)),
            "OR_uci": np.exp(np.random.normal(0.6, 0.02, n)),
        })

    def test_leave_one_out_plot_creates_figure(self, sample_loo_results):
        """leave_one_out_plot should return matplotlib Figure."""
        from pymr.plots import leave_one_out_plot

        fig = leave_one_out_plot(sample_loo_results)

        assert isinstance(fig, Figure)

    def test_leave_one_out_plot_with_ax(self, sample_loo_results):
        """leave_one_out_plot should accept optional ax parameter."""
        import matplotlib.pyplot as plt
        from pymr.plots import leave_one_out_plot

        fig, ax = plt.subplots()
        result_fig = leave_one_out_plot(sample_loo_results, ax=ax)

        assert result_fig is fig
        plt.close(fig)


class TestRadialPlot:
    """Test radial MR plot."""

    @pytest.fixture
    def sample_harmonized(self):
        """Sample harmonized data."""
        np.random.seed(42)
        n = 50
        return pd.DataFrame({
            "SNP": [f"rs{i}" for i in range(n)],
            "beta_exp": np.random.normal(0.1, 0.02, n),
            "se_exp": np.abs(np.random.normal(0.01, 0.002, n)),
            "beta_out": np.random.normal(0.05, 0.02, n),
            "se_out": np.abs(np.random.normal(0.02, 0.005, n)),
        })

    def test_radial_plot_creates_figure(self, sample_harmonized):
        """radial_plot should return matplotlib Figure."""
        from pymr.plots import radial_plot

        fig = radial_plot(sample_harmonized)

        assert isinstance(fig, Figure)

    def test_radial_plot_with_ax(self, sample_harmonized):
        """radial_plot should accept optional ax parameter."""
        import matplotlib.pyplot as plt
        from pymr.plots import radial_plot

        fig, ax = plt.subplots()
        result_fig = radial_plot(sample_harmonized, ax=ax)

        assert result_fig is fig
        plt.close(fig)


class TestIntegration:
    """Test plots with real MR workflow."""

    @pytest.fixture
    def real_mr_results(self):
        """Run actual MR analysis for realistic plots."""
        np.random.seed(42)
        n = 50
        data = pd.DataFrame({
            "SNP": [f"rs{i}" for i in range(n)],
            "beta_exp": np.random.normal(0.1, 0.02, n),
            "se_exp": np.abs(np.random.normal(0.01, 0.002, n)),
            "beta_out": np.random.normal(0.05, 0.02, n),
            "se_out": np.abs(np.random.normal(0.02, 0.005, n)),
        })

        mr = MR(data)
        results = mr.run()
        loo = mr.leave_one_out()

        return {"data": data, "results": results, "loo": loo}

    def test_all_plots_work_together(self, real_mr_results):
        """All plots should work with real MR workflow output."""
        from pymr.plots import (
            forest_plot,
            scatter_plot,
            funnel_plot,
            leave_one_out_plot,
            radial_plot,
        )

        # Should all create figures without errors
        fig1 = forest_plot(real_mr_results["results"])
        fig2 = scatter_plot(real_mr_results["data"])
        fig3 = funnel_plot(real_mr_results["data"])
        fig4 = leave_one_out_plot(real_mr_results["loo"])
        fig5 = radial_plot(real_mr_results["data"])

        assert all(isinstance(f, Figure) for f in [fig1, fig2, fig3, fig4, fig5])
