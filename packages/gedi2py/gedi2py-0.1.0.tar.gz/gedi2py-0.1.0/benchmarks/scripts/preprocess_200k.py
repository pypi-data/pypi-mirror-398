#!/usr/bin/env python
"""
preprocess_200k.py - Create 200K cell benchmark dataset from Allen Brain data

This script loads the 380K cells Allen Brain dataset and creates 200K cell
subsampled versions for both Python (h5ad) and R (RDS) benchmarking.
"""

import gc
import os
import numpy as np
import scipy.sparse as sp
import anndata as ad

# Configuration
INPUT_RDS = "/home/saberi/projects/gedi/gedi2-test/380K_cells_allen_brain_institure.rds"
OUTPUT_DIR = "/home/saberi/projects/gedi/gedipy/benchmarks/data"
N_HVG = 2000  # Number of highly variable genes
MAX_CELLS = 200000  # 200K cells for large benchmark

print("=" * 50)
print("GEDI 200K Cell Benchmark Data Preprocessing")
print("=" * 50)
print(f"Input file: {INPUT_RDS}")
print(f"Output dir: {OUTPUT_DIR}")
print(f"Number of HVGs: {N_HVG}")
print(f"Max cells: {MAX_CELLS}")
print()

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load RDS file using rpy2
print("Loading RDS file using rpy2...")
try:
    import rpy2.robjects as ro
    from rpy2.robjects import numpy2ri, pandas2ri
    from rpy2.robjects.packages import importr

    numpy2ri.activate()
    pandas2ri.activate()

    base = importr('base')
    Matrix = importr('Matrix')

    # Load RDS
    rds_data = base.readRDS(INPUT_RDS)

    # Check structure of RDS file
    print("Checking RDS structure...")
    rds_names = list(base.names(rds_data))
    print(f"  RDS contains: {rds_names}")

    # The RDS file might be a sparse matrix directly or a list
    if 'M' in rds_names:
        # It's a list with M (matrix) and samples
        M_r = rds_data.rx2('M')
        samples_r = rds_data.rx2('samples') if 'samples' in rds_names else None
    else:
        # It's likely a matrix directly
        M_r = rds_data
        samples_r = None

    # Get dimensions
    dims = base.dim(M_r)
    n_genes = int(dims[0])
    n_cells = int(dims[1])

    print(f"Raw data dimensions:")
    print(f"  Genes: {n_genes}")
    print(f"  Cells: {n_cells}")

    # Get gene and cell names
    dimnames = base.dimnames(M_r)
    if dimnames[0] is not ro.NULL:
        gene_names = np.array(dimnames[0])
    else:
        gene_names = np.array([f"gene_{i}" for i in range(n_genes)])

    if dimnames[1] is not ro.NULL:
        cell_names = np.array(dimnames[1])
    else:
        cell_names = np.array([f"cell_{i}" for i in range(n_cells)])

    # Get sample labels
    if samples_r is not None:
        sample_labels = np.array(samples_r)
    else:
        # Try to extract from cell names (format: "barcode-sample")
        sample_labels = np.array([cn.split('-')[-1] if '-' in cn else 'sample1' for cn in cell_names])

    print(f"\nSample distribution:")
    unique, counts = np.unique(sample_labels, return_counts=True)
    for s, c in list(zip(unique, counts))[:10]:  # Show first 10
        print(f"  {s}: {c}")
    if len(unique) > 10:
        print(f"  ... and {len(unique) - 10} more samples")
    print()

except ImportError as e:
    print(f"ERROR: rpy2 required for loading RDS files: {e}")
    print("Install with: pip install rpy2")
    exit(1)

# Subsample cells (stratified by sample)
if n_cells > MAX_CELLS:
    print(f"Subsampling to {MAX_CELLS} cells (stratified by sample)...")
    np.random.seed(42)

    # Calculate cells per sample proportionally
    sample_props = counts / counts.sum()
    cells_per_sample = (sample_props * MAX_CELLS).astype(int)

    # Make sure we get exactly MAX_CELLS
    diff = MAX_CELLS - cells_per_sample.sum()
    cells_per_sample[0] += diff

    selected_indices = []
    for s, n in zip(unique, cells_per_sample):
        sample_idx = np.where(sample_labels == s)[0]
        if len(sample_idx) > n:
            selected = np.random.choice(sample_idx, n, replace=False)
        else:
            selected = sample_idx
        selected_indices.extend(selected)

    selected_indices = np.sort(np.array(selected_indices))
    print(f"  Selected {len(selected_indices)} cells")
else:
    selected_indices = np.arange(n_cells)

# Convert R sparse matrix to Python scipy sparse
print("Converting R sparse matrix to scipy sparse...")

# Get sparse matrix components from R
# For dgCMatrix: i (row indices), p (column pointers), x (values)
i_idx = np.array(M_r.slots['i'])  # 0-indexed row indices
p_ptr = np.array(M_r.slots['p'])  # Column pointers
x_data = np.array(M_r.slots['x'])  # Values

# Create scipy sparse matrix (CSC format)
X_full = sp.csc_matrix((x_data, i_idx, p_ptr), shape=(n_genes, n_cells))

# Subset to selected cells
X_sub = X_full[:, selected_indices]
X_sub = X_sub.T  # Transpose to cells x genes for Python convention

# Update metadata for selected cells
sample_labels_selected = sample_labels[selected_indices]
cell_names_selected = cell_names[selected_indices]

print(f"Subsetted matrix shape: {X_sub.shape} (cells x genes)")

# Calculate HVG statistics
print("Selecting highly variable genes...")

# Gene means and variances (on cells x genes matrix)
gene_means = np.array(X_sub.mean(axis=0)).flatten()
gene_sq_means = np.array(X_sub.power(2).mean(axis=0)).flatten()
gene_vars = gene_sq_means - gene_means**2
gene_cv2 = gene_vars / (gene_means**2 + 1e-10)

# Filter genes with at least some expression
min_cells = X_sub.shape[0] * 0.001  # At least 0.1% of cells
gene_detection = np.array((X_sub > 0).sum(axis=0)).flatten()
expressed_genes = gene_detection >= min_cells

print(f"  Genes detected in >= {min_cells:.0f} cells: {expressed_genes.sum()}")

# Select top HVGs by CV2 among expressed genes
cv2_filtered = gene_cv2.copy()
cv2_filtered[~expressed_genes] = -np.inf

hvg_idx = np.argsort(cv2_filtered)[::-1][:min(N_HVG, expressed_genes.sum())]
hvg_idx = np.sort(hvg_idx)  # Keep original order

hvg_names = gene_names[hvg_idx]
print(f"  Selected {len(hvg_names)} highly variable genes")
print()

# Subset to HVGs
X_hvg = X_sub[:, hvg_idx]

print(f"Final data dimensions:")
print(f"  Cells: {X_hvg.shape[0]}")
print(f"  Genes: {X_hvg.shape[1]}")
print()

# Clean up R objects
del M_r, rds_data, X_full, X_sub
gc.collect()

# Save as h5ad (for Python)
print("Saving as h5ad (for Python)...")
import pandas as pd

obs_df = pd.DataFrame({
    'sample': sample_labels_selected,
    'barcode': cell_names_selected
}, index=cell_names_selected)

var_df = pd.DataFrame({
    'gene_name': hvg_names
}, index=hvg_names)

adata_out = ad.AnnData(
    X=X_hvg.tocsr(),  # CSR is more efficient for row operations
    obs=obs_df,
    var=var_df
)

h5ad_out = os.path.join(OUTPUT_DIR, "benchmark_data_200k.h5ad")
adata_out.write_h5ad(h5ad_out)
print(f"  Saved: {h5ad_out}")

# Save as RDS (for R)
print("Saving as RDS (for R)...")

# Convert back to genes x cells for R convention
X_r = X_hvg.T.tocsc()  # genes x cells, CSC format

# Create R sparse matrix
r_sparse = Matrix.sparseMatrix(
    i=ro.IntVector(X_r.indices + 1),  # R is 1-indexed
    p=ro.IntVector(X_r.indptr),
    x=ro.FloatVector(X_r.data),
    dims=ro.IntVector([X_r.shape[0], X_r.shape[1]])
)

# Set dimnames
r_rownames = ro.StrVector(hvg_names)
r_colnames = ro.StrVector(cell_names_selected)
r_sparse = base.structure(r_sparse,
                          dimnames=ro.ListVector({'': r_rownames, '': r_colnames}))

# Create output list
r_samples = ro.StrVector(sample_labels_selected)

output_list = ro.ListVector({
    'M': r_sparse,
    'samples': r_samples,
    'hvg_names': ro.StrVector(hvg_names),
    'cell_names': ro.StrVector(cell_names_selected)
})

rds_out = os.path.join(OUTPUT_DIR, "benchmark_data_200k.rds")
base.saveRDS(output_list, rds_out)
print(f"  Saved: {rds_out}")

# Print summary
print()
print("=" * 50)
print("Preprocessing complete!")
print("=" * 50)
print(f"Output files:")
print(f"  Python: {h5ad_out}")
print(f"  R: {rds_out}")

# File sizes
h5ad_size = os.path.getsize(h5ad_out) / 1024**2
rds_size = os.path.getsize(rds_out) / 1024**2
print(f"\nFile sizes:")
print(f"  h5ad: {h5ad_size:.1f} MB")
print(f"  rds: {rds_size:.1f} MB")

# Verify data integrity
print("\nVerification:")
print(f"  Cells: {len(sample_labels_selected)}")
print(f"  Genes: {len(hvg_names)}")
print(f"  Samples: {len(np.unique(sample_labels_selected))}")

# Save cell indices for reproducibility
indices_file = os.path.join(OUTPUT_DIR, "200k_cell_indices.csv")
pd.DataFrame({
    'original_index': selected_indices,
    'cell_name': cell_names_selected,
    'sample': sample_labels_selected
}).to_csv(indices_file, index=False)
print(f"  Cell indices saved to: {indices_file}")
