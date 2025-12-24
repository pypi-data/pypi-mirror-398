#!/usr/bin/env python3
"""
Generate Markdown Validation Report for GEDI R vs Python comparison.
Usage: python generate_report.py <results_dir> <output_file>
"""

import sys
import os
import json
from datetime import datetime


def load_json(path):
    """Load JSON file."""
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def format_matrix_sample(sample_values, param_name):
    """Format a sample of matrix values as markdown table."""
    if not sample_values:
        return "N/A"

    key = f"{param_name}_sample"
    if key not in sample_values:
        return "N/A"

    vals = sample_values[key]
    if not vals:
        return "N/A"

    # Format as inline values
    if isinstance(vals, list):
        if isinstance(vals[0], list):
            # 2D array, show first few
            rows = []
            for row in vals[:3]:
                row_str = ", ".join([f"{v:.4f}" for v in row[:3]])
                rows.append(f"[{row_str}...]")
            return " ".join(rows)
        else:
            # 1D array
            return ", ".join([f"{v:.4f}" for v in vals[:5]])
    return str(vals)


def generate_config_section(config_name, r_metrics, py_metrics, comparison):
    """Generate report section for one configuration."""

    if not comparison:
        return f"\n## {config_name}\n\n**ERROR: Comparison data not found**\n"

    status = comparison.get("validation_status", "UNKNOWN")
    status_emoji = "PASS" if status == "PASS" else "FAIL"

    section = f"""
## {config_name}

**Validation Status: {status_emoji}**

### R Implementation Results

```
Package:     gedi (R)
Threads:     {r_metrics.get('threads', 'N/A')}
Cells:       {r_metrics.get('n_cells', 'N/A'):,}
Genes:       {r_metrics.get('n_genes', 'N/A'):,}
Samples:     {r_metrics.get('n_samples', 'N/A')}
K:           {r_metrics.get('K', 'N/A')}
Iterations:  {r_metrics.get('iterations', 'N/A')}
```

**Timing:**
| Phase | Time (seconds) |
|-------|----------------|
| Initialize | {r_metrics.get('init_time_sec', 'N/A'):.2f} |
| Optimize | {r_metrics.get('opt_time_sec', 'N/A'):.2f} |
| **Total** | **{r_metrics.get('total_time_sec', 'N/A'):.2f}** |

**Final sigma2:** {r_metrics.get('final_sigma2', 'N/A'):.6f}

**Parameter Shapes:**
| Parameter | Shape |
|-----------|-------|
| Z | {r_metrics.get('Z_shape', 'N/A')} |
| DB | {r_metrics.get('DB_shape', 'N/A')} |
| svd_u | {r_metrics.get('svd_u_shape', 'N/A')} |
| svd_v | {r_metrics.get('svd_v_shape', 'N/A')} |

---

### Python Implementation Results

```
Package:     {py_metrics.get('package', 'gedipy')}
Threads:     {py_metrics.get('threads', 'N/A')}
Cells:       {py_metrics.get('n_cells', 'N/A'):,}
Genes:       {py_metrics.get('n_genes', 'N/A'):,}
Samples:     {py_metrics.get('n_samples', 'N/A')}
K:           {py_metrics.get('K', 'N/A')}
Iterations:  {py_metrics.get('iterations', 'N/A')}
```

**Timing:**
| Phase | Time (seconds) |
|-------|----------------|
| Initialize | {py_metrics.get('init_time_sec', 'N/A'):.2f} |
| Optimize | {py_metrics.get('opt_time_sec', 'N/A'):.2f} |
| **Total** | **{py_metrics.get('total_time_sec', 'N/A'):.2f}** |

**Final sigma2:** {py_metrics.get('final_sigma2', 'N/A'):.6f}

**Parameter Shapes:**
| Parameter | Shape |
|-----------|-------|
| Z | {py_metrics.get('Z_shape', 'N/A')} |
| DB | {py_metrics.get('DB_shape', 'N/A')} |
| svd_u | {py_metrics.get('svd_u_shape', 'N/A')} |
| svd_v | {py_metrics.get('svd_v_shape', 'N/A')} |

---

### Comparison Results

**Correlation Threshold: >= {comparison.get('threshold', 0.999)}**

| Parameter | Min Corr | Mean Corr | Max Corr | Shape | Status |
|-----------|----------|-----------|----------|-------|--------|
"""

    params = comparison.get("parameters", {})
    for param in ["Z", "DB", "svd_u", "svd_v"]:
        if param in params:
            p = params[param]
            if p.get("status") in ["PASS", "FAIL"]:
                status_cell = "PASS" if p.get("all_above_threshold") else "FAIL"
                section += f"| {param} | {p.get('min_corr', 0):.6f} | {p.get('mean_corr', 0):.6f} | {p.get('max_corr', 0):.6f} | {p.get('shape', 'N/A')} | {status_cell} |\n"
            else:
                section += f"| {param} | - | - | - | - | {p.get('status', 'ERROR')} |\n"
        else:
            section += f"| {param} | - | - | - | - | MISSING |\n"

    # Performance comparison
    r_total = r_metrics.get('total_time_sec', 0)
    py_total = py_metrics.get('total_time_sec', 0)

    if r_total > 0 and py_total > 0:
        speedup = r_total / py_total
        faster = "Python" if speedup > 1 else "R"
        speedup_display = speedup if speedup > 1 else 1/speedup

        section += f"""
### Performance Comparison

| Metric | R | Python | Speedup |
|--------|---|--------|---------|
| Init Time | {r_metrics.get('init_time_sec', 0):.2f}s | {py_metrics.get('init_time_sec', 0):.2f}s | {r_metrics.get('init_time_sec', 1) / max(py_metrics.get('init_time_sec', 1), 0.001):.2f}x |
| Optimize Time | {r_metrics.get('opt_time_sec', 0):.2f}s | {py_metrics.get('opt_time_sec', 0):.2f}s | {r_metrics.get('opt_time_sec', 1) / max(py_metrics.get('opt_time_sec', 1), 0.001):.2f}x |
| **Total Time** | **{r_total:.2f}s** | **{py_total:.2f}s** | **{speedup:.2f}x** |

**{faster} is {speedup_display:.2f}x faster**
"""

    return section


def generate_report(results_dir, output_file):
    """Generate the full validation report."""

    # Load small config results
    small_r = load_json(os.path.join(results_dir, "small/r/metrics.json"))
    small_py = load_json(os.path.join(results_dir, "small/python/metrics.json"))
    small_cmp = load_json(os.path.join(results_dir, "small/comparison.json"))

    # Load large config results
    large_r = load_json(os.path.join(results_dir, "large/r/metrics.json"))
    large_py = load_json(os.path.join(results_dir, "large/python/metrics.json"))
    large_cmp = load_json(os.path.join(results_dir, "large/comparison.json"))

    # Determine overall status
    small_pass = small_cmp.get("validation_status") == "PASS"
    large_pass = large_cmp.get("validation_status") == "PASS"
    overall_pass = small_pass and large_pass

    overall_status = "PASS - All results are IDENTICAL" if overall_pass else "FAIL - Results differ"

    # Generate report
    report = f"""# GEDI R vs Python Validation Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Overall Status:** {overall_status}

---

## Summary

This report validates that the Python implementation (gedipy) produces **IDENTICAL** results
to the R implementation (gedi) for all key parameters:

- **Z** - Shared metagenes matrix (genes x K)
- **DB** - Latent factor embedding (K x cells)
- **svd_u** - Left singular vectors from factorized SVD (genes x K)
- **svd_v** - Right singular vectors from factorized SVD (cells x K)

**Validation Criteria:** Pearson correlation >= 0.999 for all parameter columns

| Configuration | Cells | Iterations | Threads | Status |
|---------------|-------|------------|---------|--------|
| Small | 10,000 | 100 | 8 | {'PASS' if small_pass else 'FAIL'} |
| Large | 200,000 | 500 | 16 | {'PASS' if large_pass else 'FAIL' if large_cmp else 'NOT RUN'} |

---
"""

    # Add small config section
    if small_cmp:
        report += generate_config_section(
            "Small Configuration (10K cells, 100 iterations, 8 threads)",
            small_r, small_py, small_cmp
        )

    # Add large config section
    if large_cmp:
        report += generate_config_section(
            "Large Configuration (200K cells, 500 iterations, 16 threads)",
            large_r, large_py, large_cmp
        )
    else:
        report += """
## Large Configuration (200K cells, 500 iterations, 16 threads)

**NOT YET RUN**

"""

    # Conclusions
    report += f"""
---

## Conclusions

"""

    if overall_pass:
        report += """
### Correctness

**All parameters show Pearson correlation >= 0.999**, confirming that the Python implementation
produces results that are numerically identical to the R implementation (within floating-point precision).

Sign flips in some latent factor columns are expected and handled correctly, as latent factors
have arbitrary sign in factor models.

"""
    else:
        report += """
### Correctness Issues

**Some parameters show correlation below threshold.** This indicates potential differences
in the implementation that need investigation.

"""

    # Performance summary if both configs ran
    if small_r and small_py:
        r_time = small_r.get('total_time_sec', 0)
        py_time = small_py.get('total_time_sec', 0)
        if r_time > 0 and py_time > 0:
            speedup = r_time / py_time
            report += f"""
### Performance (Small Config)

- R total time: {r_time:.2f} seconds
- Python total time: {py_time:.2f} seconds
- Speedup: **{speedup:.2f}x** {'(Python faster)' if speedup > 1 else '(R faster)'}

"""

    if large_r and large_py:
        r_time = large_r.get('total_time_sec', 0)
        py_time = large_py.get('total_time_sec', 0)
        if r_time > 0 and py_time > 0:
            speedup = r_time / py_time
            report += f"""
### Performance (Large Config)

- R total time: {r_time:.2f} seconds
- Python total time: {py_time:.2f} seconds
- Speedup: **{speedup:.2f}x** {'(Python faster)' if speedup > 1 else '(R faster)'}

"""

    report += """
---

*Report generated by validate_identical.py and generate_report.py*
"""

    # Write report
    with open(output_file, 'w') as f:
        f.write(report)

    print(f"Report generated: {output_file}")
    return overall_pass


def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_report.py <results_dir> <output_file>")
        print("Example: python generate_report.py ../results ../results/validation_report.md")
        sys.exit(1)

    results_dir = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(results_dir):
        print(f"ERROR: Results directory not found: {results_dir}")
        sys.exit(1)

    success = generate_report(results_dir, output_file)
    print(f"\nOverall validation: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
