#!/usr/bin/env python3
"""
compare_results.py - Compare R and Python GEDI results
Usage: python compare_results.py <n_cells> <n_threads> [results_dir]
"""

import sys
import os
import json
import numpy as np
from pathlib import Path
from scipy.stats import pearsonr, spearmanr
import matplotlib.pyplot as plt


def load_r_results(filepath):
    """Load R results from RDS file using rpy2."""
    import rpy2.robjects as ro
    from rpy2.robjects import numpy2ri

    numpy2ri.activate()

    readRDS = ro.r['readRDS']
    results = readRDS(filepath)

    # Convert to Python dict
    data = {
        'Z': np.array(results.rx2('Z')),
        'D': np.array(results.rx2('D')),
        'sigma2': float(results.rx2('sigma2')[0]),
        'DB': np.array(results.rx2('DB')),
        'tracking_sigma2': np.array(results.rx2('tracking_sigma2'))
    }

    # Load SVD results if present
    try:
        data['svd_u'] = np.array(results.rx2('svd_u'))
        data['svd_v'] = np.array(results.rx2('svd_v'))
        data['svd_d'] = np.array(results.rx2('svd_d'))
    except Exception:
        data['svd_u'] = None
        data['svd_v'] = None
        data['svd_d'] = None

    numpy2ri.deactivate()
    return data


def load_python_results(filepath):
    """Load Python results from NPZ file."""
    data = np.load(filepath)
    result = {
        'Z': data['Z'],
        'D': data['D'],
        'sigma2': float(data['sigma2']),
        'DB': data['DB'],
        'tracking_sigma2': data['tracking_sigma2']
    }

    # Load SVD results if present
    if 'svd_u' in data:
        result['svd_u'] = data['svd_u']
        result['svd_v'] = data['svd_v']
        result['svd_d'] = data['svd_d']
    else:
        result['svd_u'] = None
        result['svd_v'] = None
        result['svd_d'] = None

    return result


def load_r_metrics(filepath):
    """Load R metrics from RDS file."""
    import rpy2.robjects as ro
    from rpy2.robjects import numpy2ri

    numpy2ri.activate()
    readRDS = ro.r['readRDS']
    metrics = readRDS(filepath)

    data = {}
    for name in metrics.names:
        val = metrics.rx2(name)
        if len(val) == 1:
            data[name] = val[0]
        else:
            data[name] = list(val)

    numpy2ri.deactivate()
    return data


def load_python_metrics(filepath):
    """Load Python metrics from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def compare_matrices(A, B, name):
    """Compare two matrices and return similarity metrics."""
    # Handle potential sign flips in factors
    # For each column, check if negating improves correlation
    A_aligned = A.copy()
    B_aligned = B.copy()

    if A.ndim == 2 and A.shape[1] == B.shape[1]:
        for k in range(A.shape[1]):
            corr_pos = np.corrcoef(A[:, k], B[:, k])[0, 1]
            corr_neg = np.corrcoef(A[:, k], -B[:, k])[0, 1]
            if corr_neg > corr_pos:
                B_aligned[:, k] = -B[:, k]

    # Flatten for overall comparison
    a_flat = A_aligned.flatten()
    b_flat = B_aligned.flatten()

    # Calculate metrics
    pearson_r, pearson_p = pearsonr(a_flat, b_flat)
    spearman_r, spearman_p = spearmanr(a_flat, b_flat)
    rmse = np.sqrt(np.mean((a_flat - b_flat) ** 2))
    mae = np.mean(np.abs(a_flat - b_flat))
    frobenius = np.linalg.norm(A_aligned - B_aligned, 'fro')
    relative_error = frobenius / np.linalg.norm(A_aligned, 'fro')

    return {
        'name': name,
        'shape': A.shape,
        'pearson_r': pearson_r,
        'pearson_p': pearson_p,
        'spearman_r': spearman_r,
        'spearman_p': spearman_p,
        'rmse': rmse,
        'mae': mae,
        'frobenius_norm': frobenius,
        'relative_error': relative_error
    }


def plot_comparison(r_data, py_data, output_dir, prefix):
    """Generate comparison plots."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Z matrix correlation (first 3 factors)
    for k in range(min(3, r_data['Z'].shape[1])):
        ax = axes[0, k]
        z_r = r_data['Z'][:, k]
        z_py = py_data['Z'][:, k]

        # Check for sign flip
        if np.corrcoef(z_r, z_py)[0, 1] < 0:
            z_py = -z_py

        ax.scatter(z_r, z_py, alpha=0.5, s=1)
        ax.set_xlabel(f'R Z[:,{k}]')
        ax.set_ylabel(f'Python Z[:,{k}]')
        r = np.corrcoef(z_r, z_py)[0, 1]
        ax.set_title(f'Z factor {k+1} (r={r:.4f})')

        # Add diagonal line
        lims = [min(ax.get_xlim()[0], ax.get_ylim()[0]),
                max(ax.get_xlim()[1], ax.get_ylim()[1])]
        ax.plot(lims, lims, 'r--', alpha=0.5)

    # DB embedding correlation (subsample)
    n_plot = min(5000, r_data['DB'].shape[1])
    idx = np.random.choice(r_data['DB'].shape[1], n_plot, replace=False)

    for k in range(min(3, r_data['DB'].shape[0])):
        ax = axes[1, k]
        db_r = r_data['DB'][k, idx]
        db_py = py_data['DB'][k, idx]

        # Check for sign flip
        if np.corrcoef(db_r, db_py)[0, 1] < 0:
            db_py = -db_py

        ax.scatter(db_r, db_py, alpha=0.3, s=1)
        ax.set_xlabel(f'R DB[{k},:]')
        ax.set_ylabel(f'Python DB[{k},:]')
        r = np.corrcoef(db_r, db_py)[0, 1]
        ax.set_title(f'DB factor {k+1} (r={r:.4f})')

        lims = [min(ax.get_xlim()[0], ax.get_ylim()[0]),
                max(ax.get_xlim()[1], ax.get_ylim()[1])]
        ax.plot(lims, lims, 'r--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{prefix}_matrix_comparison.png'), dpi=150)
    plt.close()

    # Sigma2 convergence plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(r_data['tracking_sigma2'], label='R (gedi2)', linewidth=2)
    ax.plot(py_data['tracking_sigma2'], label='Python (gedi-py)', linewidth=2, linestyle='--')
    ax.set_xlabel('Iteration')
    ax.set_ylabel('sigma2')
    ax.set_title('Convergence: sigma2 over iterations')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{prefix}_convergence.png'), dpi=150)
    plt.close()


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_results.py <n_cells> <n_threads> [results_dir]")
        sys.exit(1)

    n_cells = int(sys.argv[1])
    n_threads = int(sys.argv[2])
    results_dir = sys.argv[3] if len(sys.argv) >= 4 else "../results"

    r_dir = os.path.join(results_dir, "r")
    py_dir = os.path.join(results_dir, "python")
    compare_dir = os.path.join(results_dir, "comparison")
    os.makedirs(compare_dir, exist_ok=True)

    prefix = f"{n_cells}cells_{n_threads}threads"

    print("=" * 60)
    print("GEDI R vs Python Comparison")
    print("=" * 60)
    print(f"Cells: {n_cells}")
    print(f"Threads: {n_threads}")
    print("-" * 60)

    # Load results
    print("\n[1/4] Loading R results...")
    r_results_file = os.path.join(r_dir, f"gedi_r_{prefix}_results.rds")
    r_metrics_file = os.path.join(r_dir, f"gedi_r_{prefix}_metrics.rds")

    if not os.path.exists(r_results_file):
        print(f"ERROR: R results not found: {r_results_file}")
        sys.exit(1)

    r_data = load_r_results(r_results_file)
    r_metrics = load_r_metrics(r_metrics_file)
    print(f"  R: Z shape = {r_data['Z'].shape}, DB shape = {r_data['DB'].shape}")

    print("\n[2/4] Loading Python results...")
    py_results_file = os.path.join(py_dir, f"gedi_python_{prefix}_results.npz")
    py_metrics_file = os.path.join(py_dir, f"gedi_python_{prefix}_metrics.json")

    if not os.path.exists(py_results_file):
        print(f"ERROR: Python results not found: {py_results_file}")
        sys.exit(1)

    py_data = load_python_results(py_results_file)
    py_metrics = load_python_metrics(py_metrics_file)
    print(f"  Python: Z shape = {py_data['Z'].shape}, DB shape = {py_data['DB'].shape}")

    # Compare numerical results
    print("\n[3/4] Comparing numerical results...")
    print("\n--- USER-REQUIRED OUTPUTS (must match with r > 0.999) ---")

    comparisons = []
    svd_u_comp = None
    svd_v_comp = None

    # Compare Z matrices (USER-REQUIRED OUTPUT #1)
    z_comp = compare_matrices(r_data['Z'], py_data['Z'], 'Z (metagenes)')
    comparisons.append(z_comp)
    print(f"  1. Z matrix (model$Z): Pearson r = {z_comp['pearson_r']:.6f}, "
          f"Relative error = {z_comp['relative_error']:.6f}")

    # Compare DB matrices (USER-REQUIRED OUTPUT #2)
    db_comp = compare_matrices(r_data['DB'], py_data['DB'], 'DB (embeddings)')
    comparisons.append(db_comp)
    print(f"  2. DB matrix (model$projections$DB): Pearson r = {db_comp['pearson_r']:.6f}, "
          f"Relative error = {db_comp['relative_error']:.6f}")

    # Compare SVD u (USER-REQUIRED OUTPUT #3)
    if r_data['svd_u'] is not None and py_data['svd_u'] is not None:
        svd_u_comp = compare_matrices(r_data['svd_u'], py_data['svd_u'], 'svd_u (left singular vectors)')
        comparisons.append(svd_u_comp)
        print(f"  3. svd$u (model$embeddings$svd$u): Pearson r = {svd_u_comp['pearson_r']:.6f}, "
              f"Relative error = {svd_u_comp['relative_error']:.6f}")
    else:
        print("  3. svd$u: NOT AVAILABLE (re-run benchmarks with updated scripts)")

    # Compare SVD v (USER-REQUIRED OUTPUT #4)
    if r_data['svd_v'] is not None and py_data['svd_v'] is not None:
        svd_v_comp = compare_matrices(r_data['svd_v'], py_data['svd_v'], 'svd_v (right singular vectors)')
        comparisons.append(svd_v_comp)
        print(f"  4. svd$v (model$embeddings$svd$v): Pearson r = {svd_v_comp['pearson_r']:.6f}, "
              f"Relative error = {svd_v_comp['relative_error']:.6f}")
    else:
        print("  4. svd$v: NOT AVAILABLE (re-run benchmarks with updated scripts)")

    print("\n--- INTERNAL PARAMETERS (diagnostic) ---")

    # Compare D vectors
    d_comp = compare_matrices(r_data['D'].reshape(-1, 1), py_data['D'].reshape(-1, 1), 'D (scaling)')
    comparisons.append(d_comp)
    print(f"  D vector: Pearson r = {d_comp['pearson_r']:.6f}, "
          f"Relative error = {d_comp['relative_error']:.6f}")

    # Compare sigma2
    sigma2_diff = abs(r_data['sigma2'] - py_data['sigma2'])
    sigma2_rel = sigma2_diff / r_data['sigma2']
    print(f"  sigma2: R = {r_data['sigma2']:.6f}, Python = {py_data['sigma2']:.6f}, "
          f"Relative diff = {sigma2_rel:.6f}")

    # Generate plots
    print("\n[4/4] Generating comparison plots...")
    plot_comparison(r_data, py_data, compare_dir, prefix)
    print(f"  Plots saved to: {compare_dir}")

    # Performance comparison
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    print(f"{'Metric':<25} {'R (gedi2)':<20} {'Python (gedi-py)':<20}")
    print("-" * 65)
    print(f"{'Training time (sec)':<25} {r_metrics['training_time_sec']:<20.2f} {py_metrics['training_time_sec']:<20.2f}")
    print(f"{'Peak memory (MB)':<25} {r_metrics.get('peak_mem_mb', 'N/A'):<20} {py_metrics['peak_mem_mb']:<20.1f}")
    print(f"{'Final sigma2':<25} {r_metrics['final_sigma2']:<20.6f} {py_metrics['final_sigma2']:<20.6f}")

    speedup = r_metrics['training_time_sec'] / py_metrics['training_time_sec']
    print(f"\nSpeedup (R/Python): {speedup:.2f}x")

    # Save comparison summary
    summary = {
        'n_cells': n_cells,
        'n_threads': n_threads,
        'user_required_outputs': {
            'Z_pearson_r': z_comp['pearson_r'],
            'Z_relative_error': z_comp['relative_error'],
            'DB_pearson_r': db_comp['pearson_r'],
            'DB_relative_error': db_comp['relative_error'],
            'svd_u_pearson_r': svd_u_comp['pearson_r'] if svd_u_comp else None,
            'svd_u_relative_error': svd_u_comp['relative_error'] if svd_u_comp else None,
            'svd_v_pearson_r': svd_v_comp['pearson_r'] if svd_v_comp else None,
            'svd_v_relative_error': svd_v_comp['relative_error'] if svd_v_comp else None,
        },
        'internal_parameters': {
            'D_pearson_r': d_comp['pearson_r'],
            'sigma2_r': r_data['sigma2'],
            'sigma2_python': py_data['sigma2'],
            'sigma2_relative_diff': sigma2_rel
        },
        'performance_comparison': {
            'r_training_time_sec': r_metrics['training_time_sec'],
            'python_training_time_sec': py_metrics['training_time_sec'],
            'speedup': speedup,
            'r_peak_mem_mb': r_metrics.get('peak_mem_mb'),
            'python_peak_mem_mb': py_metrics['peak_mem_mb']
        }
    }

    with open(os.path.join(compare_dir, f'{prefix}_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print("USER-REQUIRED OUTPUTS ACCURACY SUMMARY")
    print("=" * 60)
    print("Required threshold: Pearson r > 0.999 for all outputs")
    print("-" * 60)

    passed = True
    threshold = 0.999

    # Check all 4 user-required outputs
    if z_comp['pearson_r'] < threshold:
        print(f"FAIL: Z matrix (model$Z) correlation = {z_comp['pearson_r']:.6f} < {threshold}")
        passed = False
    else:
        print(f"PASS: Z matrix (model$Z) correlation = {z_comp['pearson_r']:.6f}")

    if db_comp['pearson_r'] < threshold:
        print(f"FAIL: DB matrix (model$projections$DB) correlation = {db_comp['pearson_r']:.6f} < {threshold}")
        passed = False
    else:
        print(f"PASS: DB matrix (model$projections$DB) correlation = {db_comp['pearson_r']:.6f}")

    if svd_u_comp is not None:
        if svd_u_comp['pearson_r'] < threshold:
            print(f"FAIL: svd$u (model$embeddings$svd$u) correlation = {svd_u_comp['pearson_r']:.6f} < {threshold}")
            passed = False
        else:
            print(f"PASS: svd$u (model$embeddings$svd$u) correlation = {svd_u_comp['pearson_r']:.6f}")
    else:
        print("SKIP: svd$u not available (re-run benchmarks)")

    if svd_v_comp is not None:
        if svd_v_comp['pearson_r'] < threshold:
            print(f"FAIL: svd$v (model$embeddings$svd$v) correlation = {svd_v_comp['pearson_r']:.6f} < {threshold}")
            passed = False
        else:
            print(f"PASS: svd$v (model$embeddings$svd$v) correlation = {svd_v_comp['pearson_r']:.6f}")
    else:
        print("SKIP: svd$v not available (re-run benchmarks)")

    print("-" * 60)
    if passed and svd_u_comp is not None and svd_v_comp is not None:
        print("ALL 4 USER-REQUIRED OUTPUTS MATCH (r > 0.999)")
    elif passed:
        print("Available outputs match, but SVD outputs not yet computed")
    else:
        print("\nSome outputs did not meet accuracy threshold (r > 0.999).")
        print("Root cause is likely missing U and S parameters.")
        print("Please fix U/S export and re-run benchmarks.")

    print("=" * 60)


if __name__ == "__main__":
    main()
