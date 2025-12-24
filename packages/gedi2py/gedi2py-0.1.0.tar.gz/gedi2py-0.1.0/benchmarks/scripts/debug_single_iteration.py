#!/usr/bin/env python3
"""
Debug single iteration to find where R and Python diverge.

This script runs a SINGLE iteration and compares intermediate values.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from gedi._gedi_cpp import GEDI, compute_DB

def main():
    n_cells = 10000
    r_init_dir = Path("../data/r_init")
    r_1iter_dir = Path("../data/r_init")  # Files with _1iter_ prefix

    print("=" * 60)
    print("GEDI Single Iteration Debug")
    print("=" * 60)

    # Load all parameters from R's POST-INIT state
    print("\n[1/4] Loading R's POST-INIT parameters...")

    # Load Yi matrices
    Yi_list = []
    num_samples = 49
    for i in range(num_samples):
        Yi = pd.read_csv(r_init_dir / f"Yi_{n_cells}_sample{i}.csv").values
        Yi_list.append(np.ascontiguousarray(Yi.astype(np.float64)))
    print(f"  Loaded {len(Yi_list)} Yi matrices")

    # Load Bi
    Bi_init = []
    for i in range(num_samples):
        Bi = pd.read_csv(r_init_dir / f"Bi_init_{n_cells}_sample{i}.csv").values
        Bi_init.append(np.ascontiguousarray(Bi.astype(np.float64)))
    print(f"  Loaded {len(Bi_init)} Bi matrices")

    # Load Qi
    Qi_init = []
    for i in range(num_samples):
        Qi = pd.read_csv(r_init_dir / f"Qi_init_{n_cells}_sample{i}.csv").values
        Qi_init.append(np.ascontiguousarray(Qi.astype(np.float64)))
    print(f"  Loaded {len(Qi_init)} Qi matrices")

    # Load si
    si_init = []
    for i in range(num_samples):
        si = pd.read_csv(r_init_dir / f"si_init_{n_cells}_sample{i}.csv").values.flatten()
        si_init.append(np.ascontiguousarray(si.astype(np.float64)))
    print(f"  Loaded {len(si_init)} si vectors")

    # Load oi
    oi_init = []
    for i in range(num_samples):
        oi = pd.read_csv(r_init_dir / f"oi_init_{n_cells}_sample{i}.csv").values.flatten()
        oi_init.append(np.ascontiguousarray(oi.astype(np.float64)))
    print(f"  Loaded {len(oi_init)} oi vectors")

    # Load Z, D, U, S, o, sigma2
    Z_init = pd.read_csv(r_init_dir / f"Z_init_{n_cells}.csv").values
    Z_init = np.ascontiguousarray(Z_init.astype(np.float64))

    D_init = pd.read_csv(r_init_dir / f"D_init_{n_cells}.csv").values.flatten()
    D_init = np.ascontiguousarray(D_init.astype(np.float64))

    U_init = pd.read_csv(r_init_dir / f"U_init_{n_cells}.csv").values
    U_init = np.ascontiguousarray(U_init.astype(np.float64))

    S_init = pd.read_csv(r_init_dir / f"S_init_{n_cells}.csv").values.flatten()
    S_init = np.ascontiguousarray(S_init.astype(np.float64))

    o_init = pd.read_csv(r_init_dir / f"o_init_{n_cells}.csv").values.flatten()
    o_init = np.ascontiguousarray(o_init.astype(np.float64))

    sigma2_init = pd.read_csv(r_init_dir / f"sigma2_init_{n_cells}.csv").values.flatten()[0]

    J, K = Z_init.shape
    N = sum(Yi.shape[1] for Yi in Yi_list)

    print(f"  Z: {Z_init.shape}")
    print(f"  D: {D_init}")
    print(f"  sigma2_init: {sigma2_init}")

    # Load hyperparameters
    print("\n[2/4] Loading hyperparameters...")
    S_Z = float(pd.read_csv(r_init_dir / f"hyperparams_S_Z_{n_cells}.csv").values.flatten()[0])
    S_A = float(pd.read_csv(r_init_dir / f"hyperparams_S_A_{n_cells}.csv").values.flatten()[0])
    S_R = float(pd.read_csv(r_init_dir / f"hyperparams_S_R_{n_cells}.csv").values.flatten()[0])
    S_o = float(pd.read_csv(r_init_dir / f"hyperparams_S_o_{n_cells}.csv").values.flatten()[0])
    S_si = float(pd.read_csv(r_init_dir / f"hyperparams_S_si_{n_cells}.csv").values.flatten()[0])
    S_oi = pd.read_csv(r_init_dir / f"hyperparams_S_oi_{n_cells}.csv").values.flatten()
    S_oi = np.ascontiguousarray(S_oi.astype(np.float64))
    S_Qi = pd.read_csv(r_init_dir / f"hyperparams_S_Qi_{n_cells}.csv").values.flatten()
    S_Qi = np.ascontiguousarray(S_Qi.astype(np.float64))
    o_0 = pd.read_csv(r_init_dir / f"hyperparams_o_0_{n_cells}.csv").values.flatten()
    o_0 = np.ascontiguousarray(o_0.astype(np.float64))

    si_0_list = []
    for i in range(num_samples):
        si_0 = pd.read_csv(r_init_dir / f"hyperparams_si_0_{n_cells}_sample{i}.csv").values.flatten()
        si_0_list.append(np.ascontiguousarray(si_0.astype(np.float64)))

    O_matrix = pd.read_csv(r_init_dir / f"hyperparams_O_{n_cells}.csv").values
    O_matrix = np.ascontiguousarray(O_matrix.astype(np.float64))

    print(f"  S_Z: {S_Z}")
    print(f"  S_si: {S_si}")
    print(f"  S_o: {S_o}")

    # Create model and run 1 iteration
    print("\n[3/4] Creating model and running 1 iteration...")

    model = GEDI(
        J, N, K, 0, 0, num_samples,
        Bi_init, Qi_init, si_init, oi_init,
        o_init, Z_init, U_init, S_init, D_init,
        sigma2_init,
        Yi_list,
        "Y", "Bsphere", True, True, False, 2, 8
    )

    model.set_hyperparams(
        S_Qi, S_oi, S_Z, S_A, S_R, S_si, S_o,
        o_0, si_0_list, O_matrix
    )

    model.set_initialized(True)
    model.compute_initial_caches()

    # Run only 1 iteration
    model.optimize(1, 1)

    # Get results after 1 iteration
    Z_py = model.get_Z()
    D_py = model.get_D()
    sigma2_py = model.get_sigma2()
    Bi_py = model.get_Bi()
    Qi_py = model.get_Qi()
    si_py = model.get_si()
    oi_py = model.get_oi()
    o_py = model.get_o()

    print(f"\n  Python after 1 iteration:")
    print(f"  sigma2: {sigma2_py:.10f}")
    print(f"  D: {D_py}")
    print(f"  Z[0,:5]: {Z_py[0, :5]}")

    # Load R's state after 1 iteration
    print("\n[4/4] Comparing with R's iteration 1 results...")

    # Check if R's 1-iteration files exist
    r_1iter_files = list(r_1iter_dir.glob("*_1iter_*.csv"))
    if r_1iter_files:
        # Load R's D after 1 iteration
        D_r = pd.read_csv(r_1iter_dir / f"D_1iter_{n_cells}.csv").values.flatten()
        print(f"\n  R after 1 iteration:")
        print(f"  D: {D_r}")

        # Load R's Z after 1 iteration
        Z_r = pd.read_csv(r_1iter_dir / f"Z_1iter_{n_cells}.csv").values
        print(f"  Z[0,:5]: {Z_r[0, :5]}")

        # Compare D
        d_corr = np.corrcoef(D_r, D_py)[0, 1]
        print(f"\n  D correlation: {d_corr:.6f}")

        # Compare Z
        z_corr = np.mean([np.corrcoef(Z_r[:, k], Z_py[:, k])[0, 1] for k in range(K)])
        print(f"  Z mean correlation: {z_corr:.6f}")

    else:
        print("  R's 1-iteration files not found.")
        print("  Run export_r_1iter.R to generate them.")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
