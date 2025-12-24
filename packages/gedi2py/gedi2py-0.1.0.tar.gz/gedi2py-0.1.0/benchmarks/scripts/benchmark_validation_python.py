#!/usr/bin/env python3
"""
GEDI Python Benchmark for Validation
Usage: python benchmark_validation_python.py <threads> <n_cells> <iterations> <output_dir>

This script runs the Python GEDI implementation and exports results in CSV format
for cross-language comparison with R.
"""

import sys
import os
import time
import json
import traceback
import numpy as np
import pandas as pd
import scipy.sparse as sp
import anndata as ad
from pathlib import Path

# Add gedipy to path if running from source
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import gedipy
from gedipy._gedipy_cpp import GEDI, compute_DB, compute_svd_factorized


def main():
    # Parse arguments
    if len(sys.argv) != 5:
        print("Usage: python benchmark_validation_python.py <threads> <n_cells> <iterations> <output_dir>")
        sys.exit(1)

    n_threads = int(sys.argv[1])
    n_cells = int(sys.argv[2])
    iterations = int(sys.argv[3])
    output_dir = sys.argv[4]

    # Configuration
    K = 10
    track_interval = 10
    random_seed = 42

    print("=" * 60)
    print("GEDI Python Benchmark for Validation")
    print("=" * 60)
    print(f"Threads:     {n_threads}")
    print(f"Cells:       {n_cells}")
    print(f"Iterations:  {iterations}")
    print(f"K:           {K}")
    print(f"Output:      {output_dir}")
    print("-" * 60)
    print()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    print("[1/4] Loading data...")
    data_dir = Path("/home/saberi/projects/gedi/gedipy/benchmarks/data")

    if n_cells > 100000:
        data_path = data_dir / "benchmark_data_200k.h5ad"
    else:
        data_path = data_dir / "benchmark_data.h5ad"

    if not data_path.exists():
        print(f"ERROR: Data file not found at: {data_path}")
        sys.exit(1)

    t_load_start = time.time()
    adata = ad.read_h5ad(str(data_path))
    t_load_end = time.time()

    print(f"  Data loaded: {adata.n_vars} genes x {adata.n_obs} cells")
    print(f"  Load time: {t_load_end - t_load_start:.2f} seconds")
    print()

    # Get expression matrix (cells x genes in anndata)
    M = adata.X
    if sp.issparse(M):
        M = M.toarray()

    # Transpose to genes x cells (matching R convention)
    M = M.T

    # Get sample labels
    if 'sample' in adata.obs.columns:
        sample_vec = adata.obs['sample'].values
    elif 'library_label' in adata.obs.columns:
        sample_vec = adata.obs['library_label'].values
    else:
        sample_vec = np.array(['sample1'] * adata.n_obs)

    # Load R cell indices for IDENTICAL cell selection
    r_output_dir = str(Path(output_dir).parent / "r")
    r_indices_file = os.path.join(r_output_dir, "cell_indices.csv")

    if os.path.exists(r_indices_file):
        print(f"[2/4] Using SAME cells as R (from {r_indices_file})...")
        r_indices = pd.read_csv(r_indices_file)
        select_idx = r_indices['idx'].values - 1  # R is 1-indexed
        select_idx = select_idx[:n_cells]  # Take first n_cells
    else:
        print(f"[2/4] Subsampling to {n_cells} cells (seed={random_seed})...")
        np.random.seed(random_seed)
        if n_cells < M.shape[1]:
            select_idx = np.random.choice(M.shape[1], n_cells, replace=False)
            select_idx = np.sort(select_idx)
        else:
            select_idx = np.arange(M.shape[1])

    M = M[:, select_idx]
    sample_vec = sample_vec[select_idx]

    print(f"  Final matrix: {M.shape[0]} genes x {M.shape[1]} cells")

    unique_samples = np.unique(sample_vec)
    n_samples = len(unique_samples)
    print(f"  Number of samples: {n_samples}")
    print()

    # Load R's POST-INIT values for identical initialization
    print("[3/4] Loading R POST-INIT values and creating GEDI model...")
    t_prep_start = time.time()

    r_init_dir = os.path.join(r_output_dir, "init")

    if not os.path.exists(r_init_dir):
        print(f"ERROR: R init directory not found: {r_init_dir}")
        print("Please run the R benchmark first to export POST-INIT values.")
        sys.exit(1)

    # Load sample info to get R's exact sample ordering (CRITICAL!)
    sample_info = pd.read_csv(os.path.join(r_init_dir, "sample_info.csv"))
    num_samples = len(sample_info)
    r_sample_order = sample_info['sample_name'].values

    print(f"  Using R sample ordering: {r_sample_order[:3]}... ({num_samples} samples)")

    J = M.shape[0]  # genes
    N = M.shape[1]  # total cells

    # Load Yi matrices from R (ensures identical data AND sample order)
    Yi_list = []
    Ni_list = []
    for i in range(num_samples):
        Yi = pd.read_csv(os.path.join(r_init_dir, f"Yi_sample{i}.csv")).values.astype(np.float64)
        Yi_list.append(np.ascontiguousarray(Yi))
        Ni_list.append(Yi.shape[1])

    # Load initialized parameters from R
    Z_init = pd.read_csv(os.path.join(r_init_dir, "Z_init.csv")).values.astype(np.float64)
    D_init = pd.read_csv(os.path.join(r_init_dir, "D_init.csv")).values.flatten().astype(np.float64)
    U_init = pd.read_csv(os.path.join(r_init_dir, "U_init.csv")).values.astype(np.float64)
    S_init = pd.read_csv(os.path.join(r_init_dir, "S_init.csv")).values.flatten().astype(np.float64)
    o_init = pd.read_csv(os.path.join(r_init_dir, "o_init.csv")).values.flatten().astype(np.float64)
    sigma2_init = pd.read_csv(os.path.join(r_init_dir, "sigma2_init.csv")).values.flatten()[0]

    # Load per-sample parameters from R
    Bi_init = []
    Qi_init = []
    si_init = []
    oi_init = []

    for i in range(num_samples):
        Bi = pd.read_csv(os.path.join(r_init_dir, f"Bi_init_sample{i}.csv")).values.astype(np.float64)
        Qi = pd.read_csv(os.path.join(r_init_dir, f"Qi_init_sample{i}.csv")).values.astype(np.float64)
        si = pd.read_csv(os.path.join(r_init_dir, f"si_init_sample{i}.csv")).values.flatten().astype(np.float64)
        oi = pd.read_csv(os.path.join(r_init_dir, f"oi_init_sample{i}.csv")).values.flatten().astype(np.float64)

        Bi_init.append(np.ascontiguousarray(Bi))
        Qi_init.append(np.ascontiguousarray(Qi))
        si_init.append(np.ascontiguousarray(si))
        oi_init.append(np.ascontiguousarray(oi))

    # Ensure all arrays are contiguous
    Z_init = np.ascontiguousarray(Z_init)
    D_init = np.ascontiguousarray(D_init)
    U_init = np.ascontiguousarray(U_init)
    S_init = np.ascontiguousarray(S_init)
    o_init = np.ascontiguousarray(o_init)

    # Load hyperparameters from R (CRITICAL for identical results!)
    print("  Loading hyperparameters from R...")
    S_Z = pd.read_csv(os.path.join(r_init_dir, "hyperparams_S_Z.csv")).values.flatten()[0]
    S_A = pd.read_csv(os.path.join(r_init_dir, "hyperparams_S_A.csv")).values.flatten()[0]
    S_R = pd.read_csv(os.path.join(r_init_dir, "hyperparams_S_R.csv")).values.flatten()[0]
    S_o = pd.read_csv(os.path.join(r_init_dir, "hyperparams_S_o.csv")).values.flatten()[0]
    S_si = pd.read_csv(os.path.join(r_init_dir, "hyperparams_S_si.csv")).values.flatten()[0]
    S_oi = pd.read_csv(os.path.join(r_init_dir, "hyperparams_S_oi.csv")).values.flatten().astype(np.float64)
    S_Qi = pd.read_csv(os.path.join(r_init_dir, "hyperparams_S_Qi.csv")).values.flatten().astype(np.float64)
    o_0 = pd.read_csv(os.path.join(r_init_dir, "hyperparams_o_0.csv")).values.flatten().astype(np.float64)
    O_matrix = pd.read_csv(os.path.join(r_init_dir, "hyperparams_O.csv")).values.astype(np.float64)

    # Load si_0 per sample
    si_0_list = []
    for i in range(num_samples):
        si_0_i = pd.read_csv(os.path.join(r_init_dir, f"hyperparams_si_0_sample{i}.csv")).values.flatten().astype(np.float64)
        si_0_list.append(np.ascontiguousarray(si_0_i))

    # Ensure contiguous
    S_oi = np.ascontiguousarray(S_oi)
    S_Qi = np.ascontiguousarray(S_Qi)
    o_0 = np.ascontiguousarray(o_0)
    O_matrix = np.ascontiguousarray(O_matrix)

    t_prep_end = time.time()
    print(f"  Loaded R POST-INIT values from: {r_init_dir}")
    print(f"  Preparation time: {t_prep_end - t_prep_start:.2f} seconds")

    # Create model with R's initialized values
    print(f"  Creating model with R POST-INIT values...")

    t_init_start = time.time()

    try:
        model = GEDI(
            J, N, K,
            0,  # P (pathways)
            0,  # L (covariates)
            num_samples,
            Bi_init,
            Qi_init,
            si_init,
            oi_init,
            o_init,
            Z_init,
            U_init,
            S_init,
            D_init,
            sigma2_init,
            Yi_list,
            "Y",        # obs_type - "Y" because Yi is already log-transformed!
            "Bsphere",  # mode
            True,       # orthoZ
            True,       # adjustD
            False,      # is_si_fixed
            1,          # verbose
            n_threads   # num_threads
        )

        # Set hyperparameters from R (CRITICAL for identical results!)
        print("  Setting hyperparameters from R...")
        model.set_hyperparams(
            S_Qi,      # VectorXd
            S_oi,      # VectorXd
            S_Z,       # double
            S_A,       # double
            S_R,       # double
            S_si,      # double
            S_o,       # double
            o_0,       # VectorXd
            si_0_list, # vector<VectorXd>
            O_matrix   # MatrixXd
        )

        # Mark model as initialized since we loaded R's POST-INIT values
        model.set_initialized(True)
        # Compute initial caches
        model.compute_initial_caches()
        t_init_end = time.time()
        init_time = t_init_end - t_init_start

        print(f"  Training for {iterations} iterations...")

        # Optimize
        t_opt_start = time.time()
        model.optimize(iterations, track_interval)
        t_opt_end = time.time()
        opt_time = t_opt_end - t_opt_start

    except Exception as e:
        print(f"ERROR during training: {e}")
        traceback.print_exc()
        sys.exit(1)

    print(f"  Initialize time: {init_time:.2f} seconds")
    print(f"  Optimize time:   {opt_time:.2f} seconds")
    print()

    # Extract results
    print("[4/4] Extracting and exporting results...")

    Z = model.get_Z()  # J x K
    D = model.get_D()  # K
    sigma2 = model.get_sigma2()
    Bi = model.get_Bi()  # List of K x Ni

    # Compute DB projection
    print("  Computing DB projection...")
    DB = compute_DB(D, Bi, 0)  # K x N

    # Compute factorized SVD embeddings
    print("  Computing factorized SVD...")
    svd_result = compute_svd_factorized(Z, D, Bi, 0)
    svd_u = svd_result.u  # J x K (left singular vectors, genes)
    svd_v = svd_result.v  # N x K (right singular vectors, cells)
    svd_d = svd_result.d  # K (singular values)

    # Export results as CSV for cross-language comparison
    print(f"  Saving Z ({Z.shape[0]} x {Z.shape[1]})...")
    pd.DataFrame(Z).to_csv(os.path.join(output_dir, "Z.csv"), index=False)

    print(f"  Saving DB ({DB.shape[1]} x {DB.shape[0]}) [N x K]...")
    # Transpose DB to N x K for consistency with R export
    pd.DataFrame(DB.T).to_csv(os.path.join(output_dir, "DB.csv"), index=False)

    print(f"  Saving svd_u ({svd_u.shape[0]} x {svd_u.shape[1]})...")
    pd.DataFrame(svd_u).to_csv(os.path.join(output_dir, "svd_u.csv"), index=False)

    print(f"  Saving svd_v ({svd_v.shape[0]} x {svd_v.shape[1]})...")
    pd.DataFrame(svd_v).to_csv(os.path.join(output_dir, "svd_v.csv"), index=False)

    # Get sample values for report
    sample_values = {
        "Z_sample": Z[:min(5, Z.shape[0]), :min(3, Z.shape[1])].tolist(),
        "DB_sample": DB[:min(3, DB.shape[0]), :min(5, DB.shape[1])].tolist(),
        "svd_u_sample": svd_u[:min(5, svd_u.shape[0]), :min(3, svd_u.shape[1])].tolist(),
        "svd_v_sample": svd_v[:min(5, svd_v.shape[0]), :min(3, svd_v.shape[1])].tolist()
    }

    # Save metrics as JSON
    metrics = {
        "language": "Python",
        "package": f"gedipy v{gedipy.__version__}",
        "threads": n_threads,
        "n_cells": n_cells,
        "n_genes": J,
        "n_samples": num_samples,
        "K": K,
        "iterations": iterations,
        "init_time_sec": round(init_time, 3),
        "opt_time_sec": round(opt_time, 3),
        "total_time_sec": round(init_time + opt_time, 3),
        "final_sigma2": float(sigma2),
        "Z_shape": list(Z.shape),
        "DB_shape": list(DB.shape),
        "svd_u_shape": list(svd_u.shape),
        "svd_v_shape": list(svd_v.shape),
        "sample_values": sample_values
    }

    with open(os.path.join(output_dir, "metrics.json"), 'w') as f:
        json.dump(metrics, f, indent=2)

    # Also save as NPZ for detailed analysis
    np.savez(
        os.path.join(output_dir, "full_results.npz"),
        Z=Z, D=D, DB=DB,
        svd_u=svd_u, svd_v=svd_v, svd_d=svd_d,
        sigma2=sigma2,
        tracking_sigma2=np.array(model.get_tracking_sigma2())
    )

    # Print summary
    print()
    print("=" * 60)
    print("PYTHON BENCHMARK COMPLETE")
    print("=" * 60)
    print(f"Initialize time: {init_time:.2f} seconds")
    print(f"Optimize time:   {opt_time:.2f} seconds")
    print(f"Total time:      {init_time + opt_time:.2f} seconds")
    print(f"Final sigma2:    {sigma2:.6f}")
    print()
    print("Output files:")
    print(f"  - Z.csv ({Z.shape[0]} x {Z.shape[1]})")
    print(f"  - DB.csv ({DB.shape[1]} x {DB.shape[0]}) [N x K]")
    print(f"  - svd_u.csv ({svd_u.shape[0]} x {svd_u.shape[1]})")
    print(f"  - svd_v.csv ({svd_v.shape[0]} x {svd_v.shape[1]})")
    print(f"  - metrics.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
