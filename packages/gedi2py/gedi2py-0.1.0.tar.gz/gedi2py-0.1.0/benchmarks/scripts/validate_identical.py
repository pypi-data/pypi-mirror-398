#!/usr/bin/env python3
"""
Validate IDENTICAL results between R and Python GEDI implementations.
Usage: python validate_identical.py <results_dir> <config_name>

This script computes Pearson correlations for each parameter column,
handling sign flips that may occur in latent factor models.
"""

import sys
import os
import json
import numpy as np
import pandas as pd
from scipy.stats import pearsonr


def load_matrix(path):
    """Load a CSV matrix into numpy array."""
    return pd.read_csv(path).values


def column_correlation(r_mat, py_mat):
    """
    Compute per-column Pearson correlation with sign-flip handling.

    Latent factor columns can have arbitrary sign, so we check both
    positive and negative correlation and take the higher absolute value.
    """
    assert r_mat.shape == py_mat.shape, f"Shape mismatch: {r_mat.shape} vs {py_mat.shape}"

    correlations = []
    sign_flips = []

    for i in range(r_mat.shape[1]):
        r_col = r_mat[:, i]
        py_col = py_mat[:, i]

        # Handle near-zero columns
        if np.std(r_col) < 1e-10 or np.std(py_col) < 1e-10:
            if np.allclose(r_col, py_col, atol=1e-6):
                correlations.append(1.0)
                sign_flips.append(False)
            else:
                correlations.append(0.0)
                sign_flips.append(False)
            continue

        corr_pos, _ = pearsonr(r_col, py_col)

        # For SVD and latent factors, sign is arbitrary
        # Store absolute correlation, track if sign was flipped
        if corr_pos >= 0:
            correlations.append(corr_pos)
            sign_flips.append(False)
        else:
            correlations.append(-corr_pos)  # Store absolute value
            sign_flips.append(True)

    return np.array(correlations), sign_flips


def validate_results(results_dir, config_name):
    """Validate R vs Python results for a configuration."""

    r_dir = os.path.join(results_dir, "r")
    py_dir = os.path.join(results_dir, "python")

    # Parameters to validate
    params = ["Z", "DB", "svd_u", "svd_v"]

    results = {}
    all_pass = True
    threshold = 0.999

    print(f"\n{'='*60}")
    print(f"Validating: {config_name}")
    print(f"{'='*60}")
    print(f"Threshold: correlation >= {threshold}")
    print()

    for param in params:
        r_file = os.path.join(r_dir, f"{param}.csv")
        py_file = os.path.join(py_dir, f"{param}.csv")

        if not os.path.exists(r_file):
            print(f"  {param}: MISSING (R file not found)")
            results[param] = {"status": "MISSING", "error": "R file not found"}
            all_pass = False
            continue

        if not os.path.exists(py_file):
            print(f"  {param}: MISSING (Python file not found)")
            results[param] = {"status": "MISSING", "error": "Python file not found"}
            all_pass = False
            continue

        r_mat = load_matrix(r_file)
        py_mat = load_matrix(py_file)

        if r_mat.shape != py_mat.shape:
            print(f"  {param}: FAIL (shape mismatch: R={r_mat.shape}, Python={py_mat.shape})")
            results[param] = {
                "status": "FAIL",
                "error": f"Shape mismatch: R={r_mat.shape}, Python={py_mat.shape}"
            }
            all_pass = False
            continue

        corrs, sign_flips = column_correlation(r_mat, py_mat)

        min_corr = float(np.min(corrs))
        mean_corr = float(np.mean(corrs))
        max_corr = float(np.max(corrs))
        n_sign_flips = sum(sign_flips)
        passes = bool(np.all(corrs >= threshold))

        if not passes:
            all_pass = False

        status_str = "PASS" if passes else "FAIL"
        flip_str = f" ({n_sign_flips} sign-flipped)" if n_sign_flips > 0 else ""

        print(f"  {param:8s}: {status_str}  min={min_corr:.6f}  mean={mean_corr:.6f}  "
              f"max={max_corr:.6f}  shape={r_mat.shape}{flip_str}")

        results[param] = {
            "status": status_str,
            "shape": list(r_mat.shape),
            "min_corr": min_corr,
            "mean_corr": mean_corr,
            "max_corr": max_corr,
            "all_above_threshold": passes,
            "n_sign_flips": n_sign_flips,
            "per_column_corr": corrs.tolist()
        }

    # Load timing metrics
    r_metrics = {}
    py_metrics = {}

    r_metrics_file = os.path.join(r_dir, "metrics.json")
    py_metrics_file = os.path.join(py_dir, "metrics.json")

    if os.path.exists(r_metrics_file):
        with open(r_metrics_file) as f:
            r_metrics = json.load(f)

    if os.path.exists(py_metrics_file):
        with open(py_metrics_file) as f:
            py_metrics = json.load(f)

    # Print timing comparison
    if r_metrics and py_metrics:
        print()
        print("Performance Comparison:")

        r_total = r_metrics.get("total_time_sec", 0)
        py_total = py_metrics.get("total_time_sec", 0)

        if r_total > 0 and py_total > 0:
            speedup = r_total / py_total
            print(f"  R total:      {r_total:.2f} seconds")
            print(f"  Python total: {py_total:.2f} seconds")
            print(f"  Speedup:      {speedup:.2f}x {'(Python faster)' if speedup > 1 else '(R faster)'}")

    # Overall result
    print()
    overall_status = "PASS" if all_pass else "FAIL"
    print(f"Overall Validation: {overall_status}")
    print("=" * 60)

    # Save comparison results
    output = {
        "config_name": config_name,
        "validation_status": overall_status,
        "threshold": threshold,
        "parameters": results,
        "r_metrics": r_metrics,
        "python_metrics": py_metrics
    }

    comparison_file = os.path.join(results_dir, "comparison.json")
    with open(comparison_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Comparison saved to: {comparison_file}")

    return all_pass


def main():
    if len(sys.argv) != 3:
        print("Usage: python validate_identical.py <results_dir> <config_name>")
        print("Example: python validate_identical.py ../results/small 'Small Configuration (10K cells)'")
        sys.exit(1)

    results_dir = sys.argv[1]
    config_name = sys.argv[2]

    if not os.path.exists(results_dir):
        print(f"ERROR: Results directory not found: {results_dir}")
        sys.exit(1)

    success = validate_results(results_dir, config_name)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
