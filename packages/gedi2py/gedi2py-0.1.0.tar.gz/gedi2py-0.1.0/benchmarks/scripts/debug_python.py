#!/usr/bin/env python3
"""
debug_python.py - Debug Python gedi-py segfault
"""

import sys
import numpy as np
import scipy.sparse as sp
import anndata as ad
from pathlib import Path

# Add gedi-py to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import gedi
from gedi._gedi_cpp import GEDI

def main():
    # Load small subset
    print("Loading data...")
    data_path = Path("/home/saberi/projects/gedi/gedi-py/benchmarks/data/benchmark_data.h5ad")
    adata = ad.read_h5ad(str(data_path))

    # Use smaller subset for debugging
    n_cells = 1000
    K = 3

    np.random.seed(42)
    select_idx = np.random.choice(adata.n_obs, n_cells, replace=False)
    select_idx = np.sort(select_idx)

    M = adata.X[select_idx, :]
    if sp.issparse(M):
        M = M.toarray()
    M = M.T  # genes x cells

    sample_vec = adata.obs['sample'].values[select_idx]
    unique_samples = np.unique(sample_vec)
    n_samples = len(unique_samples)

    print(f"Data: {M.shape[0]} genes x {M.shape[1]} cells, {n_samples} samples")

    # Prepare data
    sample_to_idx = {s: np.where(sample_vec == s)[0] for s in unique_samples}

    Yi_list = []
    Ni_list = []
    for sample in unique_samples:
        idx = sample_to_idx[sample]
        Mi = M[:, idx]
        Yi = np.log1p(Mi).astype(np.float64)
        Yi_list.append(np.ascontiguousarray(Yi))
        Ni_list.append(len(idx))

    J = M.shape[0]  # genes
    N = M.shape[1]  # total cells
    num_samples = n_samples

    print(f"J={J}, N={N}, K={K}, num_samples={num_samples}")
    print(f"Ni_list: {Ni_list}")

    # Initialize parameters
    np.random.seed(42)

    Bi_init = [np.ascontiguousarray(np.random.randn(K, Ni) * 0.01)
               for Ni in Ni_list]
    Qi_init = [np.ascontiguousarray(np.zeros((J, K)))
               for _ in range(num_samples)]
    si_init = [np.ascontiguousarray(np.zeros(Ni)) for Ni in Ni_list]
    oi_init = [np.ascontiguousarray(np.zeros(J)) for _ in range(num_samples)]

    o_init = np.ascontiguousarray(np.zeros(J))
    Z_init = np.ascontiguousarray(np.random.randn(J, K) * 0.01)
    U_init = np.ascontiguousarray(np.eye(J, K))
    S_init = np.ascontiguousarray(np.ones(K))
    D_init = np.ascontiguousarray(np.ones(K))
    sigma2_init = 1.0

    print("\nArray shapes:")
    print(f"  Bi_init[0]: {Bi_init[0].shape}")
    print(f"  Qi_init[0]: {Qi_init[0].shape}")
    print(f"  si_init[0]: {si_init[0].shape}")
    print(f"  oi_init[0]: {oi_init[0].shape}")
    print(f"  o_init: {o_init.shape}")
    print(f"  Z_init: {Z_init.shape}")
    print(f"  U_init: {U_init.shape}")
    print(f"  S_init: {S_init.shape}")
    print(f"  D_init: {D_init.shape}")
    print(f"  Yi_list[0]: {Yi_list[0].shape}")

    print("\nCreating GEDI model with verbose=2...")
    sys.stdout.flush()

    try:
        model = GEDI(
            J, N, K,
            0,  # P
            0,  # L
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
            "M",        # obs_type
            "Bsphere",  # mode
            True,       # orthoZ
            True,       # adjustD
            False,      # is_si_fixed
            2,          # verbose=2 for debug
            1           # num_threads
        )

        print("\nTraining model...")
        sys.stdout.flush()
        model.train(5, 1, False)  # 5 iterations

        print("\nSuccess!")
        print(f"sigma2: {model.get_sigma2()}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
