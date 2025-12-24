#!/usr/bin/env python3
"""
benchmark_python_r_init.py - Benchmark Python gedi-py using R's POST-INIT values
Uses exported post-initialization data from R to ensure identical starting conditions.
Python skips its own initialization and uses R's post-SVD values directly.
"""

import sys
import os
import time
import json
import traceback
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import gedi
from gedi._gedi_cpp import GEDI, compute_DB


def main():
    if len(sys.argv) < 3:
        print("Usage: python benchmark_python_r_init.py <threads> <n_cells> [output_dir]")
        sys.exit(1)

    n_threads = int(sys.argv[1])
    n_cells = int(sys.argv[2])
    output_dir = sys.argv[3] if len(sys.argv) >= 4 else "../results/python_r_init"

    K = 10
    iterations = 100
    track_interval = 10

    print("=" * 60)
    print("GEDI Python Benchmark (using R POST-INIT values)")
    print("=" * 60)
    print(f"Threads: {n_threads}")
    print(f"Cells: {n_cells}")
    print(f"Latent factors (K): {K}")
    print(f"Iterations: {iterations}")
    print("-" * 60)
    print()

    os.makedirs(output_dir, exist_ok=True)

    # Load R's exported POST-INIT data
    r_init_dir = Path("/home/saberi/projects/gedi/gedi-py/benchmarks/data/r_init")

    print("[1/4] Loading R's POST-INIT values...")
    t_load_start = time.time()

    # Load sample info
    sample_info = pd.read_csv(r_init_dir / f"sample_info_{n_cells}.csv")
    num_samples = len(sample_info)
    print(f"  Number of samples: {num_samples}")

    # Load Yi matrices
    Yi_list = []
    Ni_list = []
    for i in range(num_samples):
        Yi = pd.read_csv(r_init_dir / f"Yi_{n_cells}_sample{i}.csv").values
        Yi_list.append(np.ascontiguousarray(Yi.astype(np.float64)))
        Ni_list.append(Yi.shape[1])

    J = Yi_list[0].shape[0]  # genes
    N = sum(Ni_list)  # total cells

    print(f"  Loaded Yi matrices: {J} genes, {N} total cells")

    # Load POST-INIT Bi
    Bi_init = []
    for i in range(num_samples):
        Bi = pd.read_csv(r_init_dir / f"Bi_init_{n_cells}_sample{i}.csv").values
        Bi_init.append(np.ascontiguousarray(Bi.astype(np.float64)))
    print(f"  Loaded Bi: {len(Bi_init)} matrices, first shape: {Bi_init[0].shape}")

    # Load POST-INIT Qi
    Qi_init = []
    for i in range(num_samples):
        Qi = pd.read_csv(r_init_dir / f"Qi_init_{n_cells}_sample{i}.csv").values
        Qi_init.append(np.ascontiguousarray(Qi.astype(np.float64)))
    print(f"  Loaded Qi: {len(Qi_init)} matrices, first shape: {Qi_init[0].shape}")

    # Load POST-INIT oi
    oi_init = []
    for i in range(num_samples):
        oi = pd.read_csv(r_init_dir / f"oi_init_{n_cells}_sample{i}.csv").values.flatten()
        oi_init.append(np.ascontiguousarray(oi.astype(np.float64)))
    print(f"  Loaded oi: {len(oi_init)} vectors")

    # Load POST-INIT si
    si_init = []
    for i in range(num_samples):
        si = pd.read_csv(r_init_dir / f"si_init_{n_cells}_sample{i}.csv").values.flatten()
        si_init.append(np.ascontiguousarray(si.astype(np.float64)))
    print(f"  Loaded si: {len(si_init)} vectors")

    # Load POST-INIT Z
    Z_init = pd.read_csv(r_init_dir / f"Z_init_{n_cells}.csv").values
    Z_init = np.ascontiguousarray(Z_init.astype(np.float64))
    print(f"  Loaded Z: {Z_init.shape}")

    # Load POST-INIT D
    D_init = pd.read_csv(r_init_dir / f"D_init_{n_cells}.csv").values.flatten()
    D_init = np.ascontiguousarray(D_init.astype(np.float64))
    print(f"  Loaded D: {D_init.shape}, values: {D_init[:5]}...")

    # Load POST-INIT o
    o_init = pd.read_csv(r_init_dir / f"o_init_{n_cells}.csv").values.flatten()
    o_init = np.ascontiguousarray(o_init.astype(np.float64))
    print(f"  Loaded o: {o_init.shape}")

    # Load POST-INIT sigma2
    sigma2_init = pd.read_csv(r_init_dir / f"sigma2_init_{n_cells}.csv").values.flatten()[0]
    print(f"  Loaded sigma2: {sigma2_init}")

    t_load_end = time.time()
    print(f"  Load time: {t_load_end - t_load_start:.2f} seconds")
    print()

    # Load POST-INIT U and S (CRITICAL for solve_Z_orthogonal!)
    print("[2/4] Loading U, S, and hyperparameters from R...")
    U_init = pd.read_csv(r_init_dir / f"U_init_{n_cells}.csv").values
    U_init = np.ascontiguousarray(U_init.astype(np.float64))
    print(f"  Loaded U: {U_init.shape}")

    S_init = pd.read_csv(r_init_dir / f"S_init_{n_cells}.csv").values.flatten()
    S_init = np.ascontiguousarray(S_init.astype(np.float64))
    print(f"  Loaded S: {S_init.shape}, values: {S_init[:5]}...")

    # Load hyperparameters from R
    print("  Loading hyperparameters...")
    S_o = pd.read_csv(r_init_dir / f"hyperparams_S_o_{n_cells}.csv").values.flatten()[0]
    S_si = pd.read_csv(r_init_dir / f"hyperparams_S_si_{n_cells}.csv").values.flatten()[0]
    S_Z = pd.read_csv(r_init_dir / f"hyperparams_S_Z_{n_cells}.csv").values.flatten()[0]
    S_A = pd.read_csv(r_init_dir / f"hyperparams_S_A_{n_cells}.csv").values.flatten()[0]
    S_R = pd.read_csv(r_init_dir / f"hyperparams_S_R_{n_cells}.csv").values.flatten()[0]
    S_oi = pd.read_csv(r_init_dir / f"hyperparams_S_oi_{n_cells}.csv").values.flatten()
    S_Qi = pd.read_csv(r_init_dir / f"hyperparams_S_Qi_{n_cells}.csv").values.flatten()
    o_0 = pd.read_csv(r_init_dir / f"hyperparams_o_0_{n_cells}.csv").values.flatten()
    O_matrix = pd.read_csv(r_init_dir / f"hyperparams_O_{n_cells}.csv").values

    # Ensure correct types
    S_oi = np.ascontiguousarray(S_oi.astype(np.float64))
    S_Qi = np.ascontiguousarray(S_Qi.astype(np.float64))
    o_0 = np.ascontiguousarray(o_0.astype(np.float64))
    O_matrix = np.ascontiguousarray(O_matrix.astype(np.float64))

    # Load si_0 per sample
    si_0_list = []
    for i in range(num_samples):
        si_0_i = pd.read_csv(r_init_dir / f"hyperparams_si_0_{n_cells}_sample{i}.csv").values.flatten()
        si_0_list.append(np.ascontiguousarray(si_0_i.astype(np.float64)))

    print(f"  S_o: {S_o}")
    print(f"  S_si: {S_si}")
    print(f"  S_Z: {S_Z}")
    print(f"  S_Qi: {S_Qi[:3]}...")
    print(f"  S_oi: {S_oi[:3]}...")
    print(f"  o_0: shape {o_0.shape}, first values: {o_0[:3]}")
    print(f"  si_0: {len(si_0_list)} vectors")
    print(f"  O_matrix: shape {O_matrix.shape}")
    print()

    # Create GEDI model and run ONLY optimize (skip initialize)
    print("[3/4] Creating model and running ONLY optimize (skipping init)...")
    print("-" * 40)

    t_train_start = time.time()

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
            "Y",        # obs_type - Y since we're passing log-transformed data
            "Bsphere",  # mode
            True,       # orthoZ
            True,       # adjustD
            False,      # is_si_fixed
            1,          # verbose
            n_threads   # num_threads
        )

        # Set hyperparameters from R (critical for matching results!)
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
        print("  Hyperparameters set successfully!")

        # Mark as initialized
        model.set_initialized(True)

        # CRITICAL: Compute initial caches (ZDBi, QiDBi) from loaded parameters
        # Without this, the caches are zeros and the first iteration diverges from R
        print("  Computing initial caches (ZDBi, QiDBi)...")
        model.compute_initial_caches()

        # Run ONLY optimize (not train which calls initialize)
        model.optimize(iterations, track_interval)

    except Exception as e:
        print(f"ERROR during training: {e}")
        traceback.print_exc()
        sys.exit(1)

    t_train_end = time.time()
    training_time = t_train_end - t_train_start
    print("-" * 40)
    print(f"  Training time: {training_time:.2f} seconds")
    print()

    # Extract results
    print("[4/4] Extracting and saving results...")

    Z = model.get_Z()
    D = model.get_D()
    sigma2 = model.get_sigma2()
    Bi = model.get_Bi()

    print("  Computing DB projection...")
    DB = compute_DB(D, Bi, 0)

    # Compute factorized SVD embeddings
    print("  Computing factorized SVD...")
    from gedi._gedi_cpp import compute_svd_factorized
    svd_result = compute_svd_factorized(Z, D, Bi, 0)
    svd_u = svd_result.u  # J x K (left singular vectors, genes)
    svd_v = svd_result.v  # N x K (right singular vectors, cells)
    svd_d = svd_result.d  # K (singular values)

    # Save results with all 4 required outputs
    output_prefix = f"gedi_python_rinit_{n_cells}cells_{n_threads}threads"

    np.savez(
        os.path.join(output_dir, f"{output_prefix}_results.npz"),
        Z=Z,
        D=D,
        sigma2=sigma2,
        DB=DB,
        svd_u=svd_u,
        svd_v=svd_v,
        svd_d=svd_d,
        tracking_sigma2=np.array(model.get_tracking_sigma2())
    )

    metrics = {
        'implementation': f'Python (gedi-py v{gedi.__version__}) with R init',
        'version': gedi.__version__,
        'n_cells': n_cells,
        'n_genes': J,
        'n_samples': num_samples,
        'n_threads': n_threads,
        'K': K,
        'iterations': iterations,
        'training_time_sec': training_time,
        'final_sigma2': float(sigma2)
    }

    with open(os.path.join(output_dir, f"{output_prefix}_metrics.json"), 'w') as f:
        json.dump(metrics, f, indent=2)

    print()
    print("=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"Implementation:    Python (gedi-py) with R initialization")
    print(f"Dataset:           {J} genes x {n_cells} cells x {num_samples} samples")
    print(f"Threads:           {n_threads}")
    print(f"Training time:     {training_time:.2f} seconds")
    print(f"Final sigma2:      {sigma2:.6f}")
    print(f"Results saved to:  {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
