#!/usr/bin/env python3
"""
Compare R and Python GEDI results using CSV files.

This script avoids the rpy2 dependency by using CSV exports.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path


def load_r_csv_results(csv_dir: Path, n_cells: int, threads: int) -> dict:
    """Load R results from CSV files."""
    results = {}

    # Z matrix
    z_file = csv_dir / f"Z_{n_cells}_{threads}.csv"
    if z_file.exists():
        results['Z'] = pd.read_csv(z_file).values
        print(f"  Loaded Z: {results['Z'].shape}")

    # D vector
    d_file = csv_dir / f"D_{n_cells}_{threads}.csv"
    if d_file.exists():
        results['D'] = pd.read_csv(d_file).values.flatten()
        print(f"  Loaded D: {results['D'].shape}")

    # sigma2
    s_file = csv_dir / f"sigma2_{n_cells}_{threads}.csv"
    if s_file.exists():
        results['sigma2'] = pd.read_csv(s_file).values.flatten()[0]
        print(f"  Loaded sigma2: {results['sigma2']}")

    # DB matrix
    db_file = csv_dir / f"DB_{n_cells}_{threads}.csv"
    if db_file.exists():
        results['DB'] = pd.read_csv(db_file).values
        print(f"  Loaded DB: {results['DB'].shape}")

    # SVD components
    svd_u_file = csv_dir / f"svd_u_{n_cells}_{threads}.csv"
    if svd_u_file.exists():
        results['svd_u'] = pd.read_csv(svd_u_file).values
        print(f"  Loaded svd_u: {results['svd_u'].shape}")

    svd_v_file = csv_dir / f"svd_v_{n_cells}_{threads}.csv"
    if svd_v_file.exists():
        results['svd_v'] = pd.read_csv(svd_v_file).values
        print(f"  Loaded svd_v: {results['svd_v'].shape}")

    svd_d_file = csv_dir / f"svd_d_{n_cells}_{threads}.csv"
    if svd_d_file.exists():
        results['svd_d'] = pd.read_csv(svd_d_file).values.flatten()
        print(f"  Loaded svd_d: {results['svd_d'].shape}")

    # Tracking sigma2
    ts_file = csv_dir / f"tracking_sigma2_{n_cells}_{threads}.csv"
    if ts_file.exists():
        results['tracking_sigma2'] = pd.read_csv(ts_file).values.flatten()
        print(f"  Loaded tracking_sigma2: {results['tracking_sigma2'].shape}")

    return results


def load_python_results(npz_file: Path) -> dict:
    """Load Python results from NPZ file."""
    data = np.load(npz_file)
    results = {}

    for key in ['Z', 'D', 'sigma2', 'DB', 'svd_u', 'svd_v', 'svd_d', 'tracking_sigma2']:
        if key in data:
            results[key] = data[key]
            if key == 'sigma2':
                results[key] = float(results[key])
                print(f"  Loaded {key}: {results[key]}")
            else:
                print(f"  Loaded {key}: {results[key].shape}")

    return results


def compute_correlation(r_mat, py_mat, name: str) -> dict:
    """Compute correlation between R and Python matrices, handling sign ambiguity."""
    if r_mat is None or py_mat is None:
        return {'pearson_r': None, 'status': 'MISSING'}

    # Check dimensions
    if r_mat.shape != py_mat.shape:
        print(f"    WARNING: Shape mismatch for {name}: R={r_mat.shape}, Python={py_mat.shape}")
        return {'pearson_r': None, 'status': 'SHAPE_MISMATCH'}

    if r_mat.ndim == 1:
        # Vector correlation
        corr = np.corrcoef(r_mat, py_mat)[0, 1]
        return {'pearson_r': corr, 'correlations': [corr]}

    # Matrix: compute column-wise correlation with sign correction
    n_cols = r_mat.shape[1]
    correlations = []

    for i in range(n_cols):
        r_col = r_mat[:, i]
        py_col = py_mat[:, i]

        # Handle sign ambiguity (columns may be negated)
        corr = np.corrcoef(r_col, py_col)[0, 1]
        corr_neg = np.corrcoef(r_col, -py_col)[0, 1]

        # Use the better correlation (higher absolute value)
        best_corr = corr if abs(corr) >= abs(corr_neg) else corr_neg
        correlations.append(abs(best_corr))

    mean_corr = np.mean(correlations)
    min_corr = np.min(correlations)

    return {
        'pearson_r': mean_corr,
        'min_corr': min_corr,
        'correlations': correlations
    }


def main():
    if len(sys.argv) < 4:
        print("Usage: python compare_csv_results.py <n_cells> <threads> <results_dir>")
        sys.exit(1)

    n_cells = int(sys.argv[1])
    threads = int(sys.argv[2])
    results_dir = Path(sys.argv[3])

    print("=" * 60)
    print("GEDI R vs Python Comparison (CSV-based)")
    print("=" * 60)
    print(f"Cells: {n_cells}")
    print(f"Threads: {threads}")
    print("-" * 60)

    # Load R results from CSV
    print("\n[1/3] Loading R results from CSV...")
    r_csv_dir = results_dir / "r_csv"
    if not r_csv_dir.exists():
        print(f"ERROR: R CSV directory not found: {r_csv_dir}")
        print("Run: Rscript export_r_results_to_csv.R <n_cells> <threads> <results_dir>")
        sys.exit(1)

    r_data = load_r_csv_results(r_csv_dir, n_cells, threads)

    # Load Python results
    print("\n[2/3] Loading Python results...")
    py_npz = results_dir / "python_r_init" / f"gedi_python_rinit_{n_cells}cells_{threads}threads_results.npz"
    if not py_npz.exists():
        print(f"ERROR: Python results not found: {py_npz}")
        sys.exit(1)

    py_data = load_python_results(py_npz)

    # Compare
    print("\n[3/3] Comparing results...")
    print("-" * 60)

    threshold = 0.999  # Target correlation threshold
    all_passed = True

    # 1. Compare Z (USER-REQUIRED OUTPUT #1)
    print("\n1. Z (shared metagenes) - USER-REQUIRED:")
    z_comp = compute_correlation(r_data.get('Z'), py_data.get('Z'), 'Z')
    if z_comp['pearson_r'] is not None:
        status = "PASS" if z_comp['pearson_r'] >= threshold else "FAIL"
        print(f"   Mean correlation: {z_comp['pearson_r']:.6f} [{status}]")
        print(f"   Min correlation:  {z_comp['min_corr']:.6f}")
        print(f"   Per-factor: {[f'{c:.4f}' for c in z_comp['correlations']]}")
        if status == "FAIL":
            all_passed = False

    # 2. Compare DB (USER-REQUIRED OUTPUT #2)
    print("\n2. DB (cell embeddings) - USER-REQUIRED:")
    db_comp = compute_correlation(r_data.get('DB'), py_data.get('DB'), 'DB')
    if db_comp['pearson_r'] is not None:
        status = "PASS" if db_comp['pearson_r'] >= threshold else "FAIL"
        print(f"   Mean correlation: {db_comp['pearson_r']:.6f} [{status}]")
        print(f"   Min correlation:  {db_comp['min_corr']:.6f}")
        if status == "FAIL":
            all_passed = False

    # 3. Compare svd_u (USER-REQUIRED OUTPUT #3)
    print("\n3. svd_u (left singular vectors) - USER-REQUIRED:")
    svd_u_comp = compute_correlation(r_data.get('svd_u'), py_data.get('svd_u'), 'svd_u')
    if svd_u_comp['pearson_r'] is not None:
        status = "PASS" if svd_u_comp['pearson_r'] >= threshold else "FAIL"
        print(f"   Mean correlation: {svd_u_comp['pearson_r']:.6f} [{status}]")
        print(f"   Min correlation:  {svd_u_comp['min_corr']:.6f}")
        if status == "FAIL":
            all_passed = False

    # 4. Compare svd_v (USER-REQUIRED OUTPUT #4)
    print("\n4. svd_v (right singular vectors) - USER-REQUIRED:")
    svd_v_comp = compute_correlation(r_data.get('svd_v'), py_data.get('svd_v'), 'svd_v')
    if svd_v_comp['pearson_r'] is not None:
        status = "PASS" if svd_v_comp['pearson_r'] >= threshold else "FAIL"
        print(f"   Mean correlation: {svd_v_comp['pearson_r']:.6f} [{status}]")
        print(f"   Min correlation:  {svd_v_comp['min_corr']:.6f}")
        if status == "FAIL":
            all_passed = False

    # 5. Compare D (intermediate parameter)
    print("\n5. D (scaling factors) - INTERMEDIATE:")
    d_comp = compute_correlation(r_data.get('D'), py_data.get('D'), 'D')
    if d_comp['pearson_r'] is not None:
        status = "PASS" if d_comp['pearson_r'] >= threshold else "FAIL"
        print(f"   Correlation: {d_comp['pearson_r']:.6f} [{status}]")

    # 6. Compare sigma2 (convergence indicator)
    print("\n6. sigma2 (noise variance) - CONVERGENCE:")
    r_sigma2 = r_data.get('sigma2')
    py_sigma2 = py_data.get('sigma2')
    if r_sigma2 is not None and py_sigma2 is not None:
        rel_diff = abs(r_sigma2 - py_sigma2) / r_sigma2
        status = "PASS" if rel_diff < 0.001 else "FAIL"
        print(f"   R sigma2:      {r_sigma2:.10f}")
        print(f"   Python sigma2: {py_sigma2:.10f}")
        print(f"   Relative diff: {rel_diff:.6f} [{status}]")

    # 7. Compare iteration 1 sigma2
    print("\n7. Iteration 1 sigma2 - DIAGNOSTIC:")
    r_ts = r_data.get('tracking_sigma2')
    py_ts = py_data.get('tracking_sigma2')
    if r_ts is not None and py_ts is not None and len(r_ts) > 0 and len(py_ts) > 0:
        r_iter1 = r_ts[0]
        py_iter1 = py_ts[0]
        rel_diff = abs(r_iter1 - py_iter1) / r_iter1
        print(f"   R iteration 1:      {r_iter1:.10f}")
        print(f"   Python iteration 1: {py_iter1:.10f}")
        print(f"   Relative diff:      {rel_diff:.6f}")

    print("\n" + "=" * 60)
    if all_passed:
        print("RESULT: ALL USER-REQUIRED OUTPUTS PASS (correlation >= 0.999)")
    else:
        print("RESULT: SOME USER-REQUIRED OUTPUTS FAIL (correlation < 0.999)")
    print("=" * 60)


if __name__ == "__main__":
    main()
