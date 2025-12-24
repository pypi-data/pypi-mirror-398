#!/usr/bin/env python3
"""
benchmark_python.py - Benchmark Python gedi-py implementation
Usage: python benchmark_python.py <threads> <n_cells> [iterations] [output_dir]
"""

import sys
import os
import time
import gc
import tracemalloc
import json
import traceback
import numpy as np
import scipy.sparse as sp
import anndata as ad
from pathlib import Path

# Add gedi-py to path if running from source
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import gedi
from gedi._gedi_cpp import GEDI, compute_DB


def format_time(seconds):
    """Format time in human-readable format."""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.2f} minutes"
    else:
        return f"{seconds/3600:.2f} hours"


def main():
    # Parse arguments
    if len(sys.argv) < 3:
        print("Usage: python benchmark_python.py <threads> <n_cells> [iterations] [output_dir]")
        sys.exit(1)

    n_threads = int(sys.argv[1])
    n_cells = int(sys.argv[2])
    iterations = int(sys.argv[3]) if len(sys.argv) >= 4 else 100
    output_dir = sys.argv[4] if len(sys.argv) >= 5 else "../results/python"

    # Configuration
    K = 10
    track_interval = 10
    random_seed = 42

    print("=" * 60)
    print("GEDI Python Benchmark")
    print("=" * 60)
    print(f"Threads: {n_threads}")
    print(f"Cells: {n_cells}")
    print(f"Latent factors (K): {K}")
    print(f"Iterations: {iterations}")
    print(f"Random seed: {random_seed}")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    print()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Start memory tracking
    tracemalloc.start()

    # Load data
    print("[1/5] Loading data...")
    script_dir = Path(__file__).parent
    data_path = script_dir.parent / "data" / "benchmark_data.h5ad"
    if not data_path.exists():
        data_path = Path("/home/saberi/projects/gedi/gedi-py/benchmarks/data/benchmark_data.h5ad")
    if not data_path.exists():
        print(f"ERROR: Data file not found at: {data_path}")
        print("Please run preprocess_single_file.py first.")
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

    # Subsample cells
    print(f"[2/5] Subsampling to {n_cells} cells...")
    np.random.seed(random_seed)
    if n_cells < M.shape[1]:
        select_idx = np.random.choice(M.shape[1], n_cells, replace=False)
        select_idx = np.sort(select_idx)  # Keep sorted for consistency
        M = M[:, select_idx]
        sample_vec = sample_vec[select_idx]

    print(f"  Final matrix: {M.shape[0]} genes x {M.shape[1]} cells")

    unique_samples = np.unique(sample_vec)
    n_samples = len(unique_samples)
    print(f"  Number of samples: {n_samples}")
    print()

    # Prepare data for GEDI
    print("[3/5] Preparing data for GEDI...")
    t_prep_start = time.time()

    # Group cells by sample
    sample_to_idx = {s: np.where(sample_vec == s)[0] for s in unique_samples}

    # Convert to log1p expression and organize by sample
    Yi_list = []
    Ni_list = []

    for sample in unique_samples:
        idx = sample_to_idx[sample]
        Mi = M[:, idx]
        Yi = np.log1p(Mi).astype(np.float64)  # log(M + 1)
        Yi_list.append(np.ascontiguousarray(Yi))
        Ni_list.append(len(idx))

    J = M.shape[0]  # genes
    N = M.shape[1]  # total cells
    num_samples = n_samples

    # Initialize parameters
    np.random.seed(random_seed)

    # Initialize Bi (K x Ni for each sample)
    Bi_init = [np.ascontiguousarray(np.random.randn(K, Ni) * 0.01)
               for Ni in Ni_list]

    # Initialize Qi (J x K for each sample) - sample-specific metagenes
    Qi_init = [np.ascontiguousarray(np.zeros((J, K)))
               for _ in range(num_samples)]

    # Initialize si (cell size factors)
    si_init = [np.ascontiguousarray(np.zeros(Ni)) for Ni in Ni_list]

    # Initialize oi (sample gene offsets)
    oi_init = [np.ascontiguousarray(np.zeros(J)) for _ in range(num_samples)]

    # Initialize global parameters
    o_init = np.ascontiguousarray(np.zeros(J))
    Z_init = np.ascontiguousarray(np.random.randn(J, K) * 0.01)
    U_init = np.ascontiguousarray(np.eye(J, K))
    S_init = np.ascontiguousarray(np.ones(K))
    D_init = np.ascontiguousarray(np.ones(K))
    sigma2_init = 1.0

    t_prep_end = time.time()
    print(f"  Preparation time: {t_prep_end - t_prep_start:.2f} seconds")
    print()

    # Memory before training
    current_mem, peak_mem_before = tracemalloc.get_traced_memory()

    # Create GEDI model
    print("[4/5] Creating and training GEDI model...")
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
            "M",        # obs_type
            "Bsphere",  # mode
            True,       # orthoZ
            True,       # adjustD
            False,      # is_si_fixed
            1,          # verbose
            n_threads   # num_threads
        )

        # Train model
        model.train(iterations, track_interval, False)  # multimodal=False

    except Exception as e:
        print(f"ERROR during training: {e}")
        traceback.print_exc()
        sys.exit(1)

    t_train_end = time.time()
    training_time = t_train_end - t_train_start
    print("-" * 40)
    print(f"  Training time: {format_time(training_time)}")
    print()

    # Memory after training
    current_mem_after, peak_mem_after = tracemalloc.get_traced_memory()

    # Extract results
    print("[5/5] Extracting and saving results...")

    Z = model.get_Z()
    D = model.get_D()
    sigma2 = model.get_sigma2()
    Bi = model.get_Bi()

    # Compute DB projection
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
    output_prefix = f"gedi_python_{n_cells}cells_{n_threads}threads"

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

    # Save benchmark metrics
    metrics = {
        'implementation': f'Python (gedi-py v{gedi.__version__})',
        'version': gedi.__version__,
        'n_cells': n_cells,
        'n_genes': J,
        'n_samples': n_samples,
        'n_threads': n_threads,
        'K': K,
        'iterations': iterations,
        'random_seed': random_seed,
        'load_time_sec': t_load_end - t_load_start,
        'prep_time_sec': t_prep_end - t_prep_start,
        'training_time_sec': training_time,
        'total_time_sec': time.time() - t_load_start,
        'peak_mem_mb': peak_mem_after / (1024 * 1024),
        'final_sigma2': float(sigma2)
    }

    with open(os.path.join(output_dir, f"{output_prefix}_metrics.json"), 'w') as f:
        json.dump(metrics, f, indent=2)

    tracemalloc.stop()

    # Print summary
    print()
    print("=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"Implementation:    Python (gedi-py v{gedi.__version__})")
    print(f"Dataset:           {J} genes x {n_cells} cells x {n_samples} samples")
    print(f"Threads:           {n_threads}")
    print(f"Training time:     {format_time(training_time)}")
    print(f"Peak memory:       {peak_mem_after / (1024 * 1024):.1f} MB")
    print(f"Final sigma2:      {sigma2:.6f}")
    print(f"Results saved to:  {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
