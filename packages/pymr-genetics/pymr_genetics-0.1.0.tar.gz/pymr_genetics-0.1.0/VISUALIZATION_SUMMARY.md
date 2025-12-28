# PyMR Visualization Suite - Implementation Summary

## Overview

Created a comprehensive visualization suite for PyMR with 5 publication-ready plotting functions, following Test-Driven Development (TDD) principles.

## Files Created

### 1. Core Implementation: `src/pymr/plots.py` (517 lines)

**Functions implemented:**

1. **`forest_plot(results)`** - Forest plot of MR estimates across methods
   - Displays point estimates with 95% confidence intervals
   - Compares multiple MR methods (IVW, Weighted Median, MR-Egger, Simple Mode)
   - Vertical line at null effect for reference
   - Returns matplotlib Figure object

2. **`scatter_plot(harmonized, method="IVW")`** - SNP effects scatter plot
   - Plots exposure vs outcome effects for each SNP
   - Shows regression line with causal estimate
   - Supports IVW, MR-Egger, and Weighted Median methods
   - Error bars for 95% CIs on SNP effects

3. **`funnel_plot(harmonized)`** - Publication bias assessment
   - Per-SNP Wald ratios vs precision (1/SE)
   - IVW estimate reference line
   - Funnel-shaped 95% CI region
   - Detects asymmetry suggesting bias or pleiotropy

4. **`leave_one_out_plot(loo_results)`** - Sensitivity analysis
   - Shows estimate when each SNP is excluded
   - Identifies influential instruments
   - Dashed line at mean estimate
   - Configurable max_snps parameter for large datasets

5. **`radial_plot(harmonized)`** - Radial/Galbraith plot
   - Standardized SNP effects weighted by precision
   - IVW regression line through origin
   - 95% CI bands for outlier detection
   - Based on Bowden et al. (2018) methodology

**Features:**
- Publication-ready academic styling
- All functions return matplotlib Figure objects
- Support for custom axes (ax parameter) for subplots
- Customizable colors for points and lines
- Comprehensive docstrings with examples
- Type hints for all parameters
- Sensible defaults for all options

### 2. Test Suite: `tests/test_plots.py` (254 lines)

**13 comprehensive tests:**

- `TestForestPlot` (3 tests)
  - test_forest_plot_creates_figure
  - test_forest_plot_with_ax_parameter
  - test_forest_plot_shows_all_methods

- `TestScatterPlot` (3 tests)
  - test_scatter_plot_creates_figure
  - test_scatter_plot_with_method
  - test_scatter_plot_with_ax

- `TestFunnelPlot` (2 tests)
  - test_funnel_plot_creates_figure
  - test_funnel_plot_with_ax

- `TestLeaveOneOutPlot` (2 tests)
  - test_leave_one_out_plot_creates_figure
  - test_leave_one_out_plot_with_ax

- `TestRadialPlot` (2 tests)
  - test_radial_plot_creates_figure
  - test_radial_plot_with_ax

- `TestIntegration` (1 test)
  - test_all_plots_work_together

**Test results:**
- All 13 tests passing
- 97% code coverage (517 lines, 3 missed in edge cases)
- Tests verify figure creation, ax parameter support, and integration with MR workflow

### 3. Example Script: `examples/plot_example.py` (79 lines)

**Complete working demonstration:**
- Generates simulated harmonized GWAS data
- Runs full MR analysis with multiple methods
- Creates all 5 plot types
- Saves plots as high-resolution PNG files (300 DPI)
- Prints MR results summary

**Generated plots:**
- `mr_forest_plot.png` (62K)
- `mr_scatter_plot.png` (191K)
- `mr_funnel_plot.png` (176K)
- `mr_loo_plot.png` (172K)
- `mr_radial_plot.png` (219K)

### 4. Documentation: `docs/plots.md` (348 lines)

**Comprehensive user guide including:**
- Quick start guide
- Detailed documentation for each function
- Interpretation guidelines for each plot type
- Customization examples (colors, axes, export formats)
- Complete example workflow
- Style guidelines for publication
- Tips for academic publishing
- Troubleshooting section
- API reference
- Further reading with citations

## Technical Implementation

### TDD Approach (Red-Green-Refactor)

1. **Red**: Wrote failing tests first (test_plots.py)
2. **Green**: Implemented functions to pass tests (plots.py)
3. **Refactor**: Cleaned up code, fixed linting issues

### Dependencies Added

Updated `pyproject.toml`:
```toml
dependencies = [
    "matplotlib>=3.5",
    "seaborn>=0.12",
]
```

### Code Quality

- **Linting**: All ruff checks passed
- **Type hints**: Full type annotations using typing.Literal for enums
- **Docstrings**: Google-style docstrings for all functions
- **Style**: Academic publication-ready formatting
- **Coverage**: 97% test coverage

### Design Principles

1. **Return Figure objects** - All functions return matplotlib.figure.Figure for flexibility
2. **Optional ax parameter** - Support for creating subplots/multi-panel figures
3. **Sensible defaults** - Work out-of-the-box with minimal configuration
4. **Customizable** - Color schemes, labels, and formatting can be customized
5. **Academic styling** - Clean, professional appearance suitable for journals
6. **Consistent API** - Similar parameter names and patterns across functions

## Usage Examples

### Basic Usage

```python
from pymr import MR
from pymr.plots import forest_plot, scatter_plot

# Run MR analysis
mr = MR(harmonized_data)
results = mr.run()

# Create forest plot
fig = forest_plot(results)
fig.savefig("forest.png", dpi=300, bbox_inches="tight")

# Create scatter plot
fig = scatter_plot(harmonized_data, method="IVW")
fig.savefig("scatter.png", dpi=300, bbox_inches="tight")
```

### Multi-Panel Figure

```python
import matplotlib.pyplot as plt
from pymr.plots import forest_plot, scatter_plot, funnel_plot, radial_plot

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

forest_plot(results, ax=axes[0, 0])
scatter_plot(harmonized, ax=axes[0, 1])
funnel_plot(harmonized, ax=axes[1, 0])
radial_plot(harmonized, ax=axes[1, 1])

fig.tight_layout()
fig.savefig("mr_summary.png", dpi=300, bbox_inches="tight")
```

### Custom Colors

```python
# Use custom color scheme
fig = forest_plot(results, color="#319795")  # Teal
fig = scatter_plot(
    harmonized,
    point_color="#E63946",  # Red
    line_color="#1D3557"    # Navy
)
```

## Integration with PyMR

The plots module integrates seamlessly with PyMR's existing workflow:

```python
from pymr import MR, load_gwas, harmonize
from pymr.plots import forest_plot, leave_one_out_plot

# Load GWAS data
exposure = load_gwas("bmi_gwas.tsv.gz")
outcome = load_gwas("diabetes_gwas.tsv.gz")

# Harmonize
harmonized = harmonize(exposure, outcome)

# Run MR
mr = MR(harmonized)
results = mr.run()
loo = mr.leave_one_out()

# Visualize
forest_plot(results).savefig("forest.png", dpi=300, bbox_inches="tight")
leave_one_out_plot(loo).savefig("loo.png", dpi=300, bbox_inches="tight")
```

## Testing

Run tests with:
```bash
pytest tests/test_plots.py -v
```

All 13 tests pass with 97% coverage:
```
tests/test_plots.py::TestForestPlot::test_forest_plot_creates_figure PASSED
tests/test_plots.py::TestForestPlot::test_forest_plot_with_ax_parameter PASSED
tests/test_plots.py::TestForestPlot::test_forest_plot_shows_all_methods PASSED
tests/test_plots.py::TestScatterPlot::test_scatter_plot_creates_figure PASSED
tests/test_plots.py::TestScatterPlot::test_scatter_plot_with_method PASSED
tests/test_plots.py::TestScatterPlot::test_scatter_plot_with_ax PASSED
tests/test_plots.py::TestFunnelPlot::test_funnel_plot_creates_figure PASSED
tests/test_plots.py::TestFunnelPlot::test_funnel_plot_with_ax PASSED
tests/test_plots.py::TestLeaveOneOutPlot::test_leave_one_out_plot_creates_figure PASSED
tests/test_plots.py::TestLeaveOneOutPlot::test_leave_one_out_plot_with_ax PASSED
tests/test_plots.py::TestRadialPlot::test_radial_plot_creates_figure PASSED
tests/test_plots.py::TestRadialPlot::test_radial_plot_with_ax PASSED
tests/test_plots.py::TestIntegration::test_all_plots_work_together PASSED
```

## File Locations

```
pymr/
├── src/pymr/
│   ├── __init__.py          (updated to export plots module)
│   └── plots.py             ✓ NEW (517 lines)
├── tests/
│   └── test_plots.py        ✓ NEW (254 lines)
├── examples/
│   ├── plot_example.py      ✓ NEW (79 lines)
│   ├── mr_forest_plot.png   ✓ GENERATED
│   ├── mr_scatter_plot.png  ✓ GENERATED
│   ├── mr_funnel_plot.png   ✓ GENERATED
│   ├── mr_loo_plot.png      ✓ GENERATED
│   └── mr_radial_plot.png   ✓ GENERATED
└── docs/
    └── plots.md             ✓ NEW (348 lines)
```

## Summary Statistics

- **Total lines of code**: 1,198 lines
  - plots.py: 517 lines
  - test_plots.py: 254 lines
  - plot_example.py: 79 lines
  - plots.md: 348 lines

- **Functions created**: 5 plotting functions
- **Tests written**: 13 comprehensive tests
- **Test coverage**: 97%
- **Generated plots**: 5 example plots (800K total)

## Next Steps

The visualization suite is complete and ready for use. Potential future enhancements:

1. Add more plot types (e.g., leave-one-out for all methods)
2. Interactive plots with plotly
3. Automated report generation
4. Custom themes for different journals
5. Animation support for sensitivity analyses

## References

1. Hemani G, et al. (2018). The MR-Base platform supports systematic causal inference across the human phenome. eLife, 7:e34408.

2. Bowden J, et al. (2018). Improving the visualization, interpretation and analysis of two-sample summary data Mendelian randomization via the Radial plot and Radial regression. Int J Epidemiol, 47(6):2100-2114.

3. Burgess S, Thompson SG (2015). Mendelian Randomization: Methods for Using Genetic Variants in Causal Estimation. Chapman & Hall/CRC.
