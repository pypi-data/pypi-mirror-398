#!/usr/bin/env python
"""
preprocess_single_file.py - Preprocess single h5ad file for benchmarking

This script processes a single h5ad file from Allen Brain Atlas
and prepares it for R vs Python benchmarking using anndata's
memory-efficient backed mode.
"""

import gc
import os
import numpy as np
import scipy.sparse as sp
import anndata as ad

# Configuration
H5AD_FILE = "/home/saberi/projects/gedi/gedi2_manuscript/data/Allen-brain-10X-V3/WMB-10Xv3-CB-raw.h5ad"
OUTPUT_DIR = "/home/saberi/projects/gedi/gedi-py/benchmarks/data"
N_HVG = 2000  # Number of highly variable genes
MAX_CELLS = 100000  # Maximum cells to keep (enough for all benchmarks)

print("=" * 40)
print("GEDI Benchmark Data Preprocessing")
print("=" * 40)
print(f"Input file: {H5AD_FILE}")
print(f"Output dir: {OUTPUT_DIR}")
print(f"Number of HVGs: {N_HVG}")
print(f"Max cells: {MAX_CELLS}")
print()

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read h5ad file in backed mode (memory-efficient)
print("Reading h5ad file (backed mode)...")
adata = ad.read_h5ad(H5AD_FILE, backed='r')

print(f"Raw data dimensions:")
print(f"  Genes: {adata.n_vars}")
print(f"  Cells: {adata.n_obs}")
print()

# Get cell metadata
print("Extracting metadata...")
obs = adata.obs.copy()
var = adata.var.copy()

# Get sample labels (library_label is batch identifier)
if 'library_label' in obs.columns:
    sample_labels = obs['library_label'].values
else:
    sample_labels = np.array(['sample1'] * adata.n_obs)

print(f"Sample distribution:")
unique, counts = np.unique(sample_labels, return_counts=True)
for s, c in zip(unique, counts):
    print(f"  {s}: {c}")
print()

# Subsample cells if needed (stratified by sample)
if adata.n_obs > MAX_CELLS:
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

    selected_indices = np.sort(selected_indices)
    print(f"  Selected {len(selected_indices)} cells")
else:
    selected_indices = np.arange(adata.n_obs)

# Load expression matrix for selected cells
print("Loading expression matrix for selected cells...")
# Read in chunks to avoid memory issues
chunk_size = 10000
n_chunks = (len(selected_indices) + chunk_size - 1) // chunk_size

X_chunks = []
for i in range(n_chunks):
    start = i * chunk_size
    end = min((i + 1) * chunk_size, len(selected_indices))
    chunk_indices = selected_indices[start:end]

    print(f"  Loading chunk {i+1}/{n_chunks} ({len(chunk_indices)} cells)...")

    # Read chunk
    chunk_data = adata.X[chunk_indices, :].toarray() if sp.issparse(adata.X[chunk_indices, :]) else adata.X[chunk_indices, :]
    X_chunks.append(sp.csr_matrix(chunk_data))

    gc.collect()

# Combine chunks
print("Combining chunks...")
X = sp.vstack(X_chunks)
del X_chunks
gc.collect()

print(f"Loaded matrix shape: {X.shape}")

# Update metadata for selected cells
obs_selected = obs.iloc[selected_indices].copy()
sample_labels_selected = sample_labels[selected_indices]

# Calculate HVG statistics
print("Selecting highly variable genes...")

# Gene means and variances
gene_means = np.array(X.mean(axis=0)).flatten()
gene_sq_means = np.array(X.power(2).mean(axis=0)).flatten()
gene_vars = gene_sq_means - gene_means**2
gene_cv2 = gene_vars / (gene_means**2 + 1e-10)

# Filter genes with at least some expression
min_cells = X.shape[0] * 0.001  # At least 0.1% of cells
gene_detection = np.array((X > 0).sum(axis=0)).flatten()
expressed_genes = gene_detection >= min_cells

print(f"  Genes detected in >= {min_cells:.0f} cells: {expressed_genes.sum()}")

# Select top HVGs by CV2 among expressed genes
cv2_filtered = gene_cv2.copy()
cv2_filtered[~expressed_genes] = -np.inf

hvg_idx = np.argsort(cv2_filtered)[::-1][:min(N_HVG, expressed_genes.sum())]
hvg_idx = np.sort(hvg_idx)  # Keep original order

# Get gene names
if 'gene_identifier' in var.columns:
    gene_names = var['gene_identifier'].values
else:
    gene_names = var.index.values

hvg_names = gene_names[hvg_idx]
print(f"  Selected {len(hvg_names)} highly variable genes")
print()

# Subset to HVGs
X_hvg = X[:, hvg_idx]

print(f"Final data dimensions:")
print(f"  Genes: {X_hvg.shape[1]}")
print(f"  Cells: {X_hvg.shape[0]}")
print()

# Close backed file
adata.file.close()

# Create cell barcodes
if 'cell_barcode' in obs_selected.columns:
    cell_barcodes = obs_selected['cell_barcode'].values
else:
    cell_barcodes = obs_selected.index.values

if 'library_label' in obs_selected.columns:
    cell_barcodes = np.array([f"{bc}-{lib}" for bc, lib in
                              zip(cell_barcodes, obs_selected['library_label'].values)])

# Save as h5ad (for Python)
print("Saving as h5ad (for Python)...")
adata_out = ad.AnnData(
    X=X_hvg,
    obs=obs_selected,
    var=var.iloc[hvg_idx].copy()
)
adata_out.obs['sample'] = sample_labels_selected
adata_out.obs_names = cell_barcodes
adata_out.var_names = hvg_names

h5ad_out = os.path.join(OUTPUT_DIR, "benchmark_data.h5ad")
adata_out.write_h5ad(h5ad_out)
print(f"  Saved: {h5ad_out}")

# Save as RDS (for R) using rpy2
print("Saving as RDS (for R)...")
try:
    import rpy2.robjects as ro
    from rpy2.robjects import numpy2ri, pandas2ri
    from rpy2.robjects.packages import importr

    numpy2ri.activate()
    pandas2ri.activate()

    base = importr('base')
    Matrix = importr('Matrix')

    # Convert sparse matrix to R dgCMatrix
    # Need genes x cells for R (transpose)
    X_t = X_hvg.T.tocsc()

    # Create R sparse matrix
    r_sparse = Matrix.sparseMatrix(
        i=ro.IntVector(X_t.indices + 1),  # R is 1-indexed
        p=ro.IntVector(X_t.indptr),
        x=ro.FloatVector(X_t.data),
        dims=ro.IntVector([X_t.shape[0], X_t.shape[1]])
    )

    # Set dimnames
    r_rownames = ro.StrVector(hvg_names)
    r_colnames = ro.StrVector(cell_barcodes)
    r_sparse = base.structure(r_sparse,
                              dimnames=ro.ListVector({'': r_rownames, '': r_colnames}))

    # Create output list
    r_samples = ro.StrVector(sample_labels_selected)
    r_samples.names = ro.StrVector(cell_barcodes)

    output_list = ro.ListVector({
        'M': r_sparse,
        'samples': r_samples,
        'hvg_names': ro.StrVector(hvg_names)
    })

    rds_out = os.path.join(OUTPUT_DIR, "benchmark_data.rds")
    base.saveRDS(output_list, rds_out)
    print(f"  Saved: {rds_out}")

except ImportError as e:
    print(f"  WARNING: Could not save RDS (rpy2 not available): {e}")
    print("  The R benchmark will need to load the h5ad file directly.")

# Print summary
print()
print("=" * 40)
print("Preprocessing complete!")
print("=" * 40)
print(f"Output files:")
print(f"  Python: {h5ad_out}")
if 'rds_out' in locals():
    print(f"  R: {rds_out}")

# File sizes
h5ad_size = os.path.getsize(h5ad_out) / 1024**2
print(f"\nFile sizes:")
print(f"  h5ad: {h5ad_size:.1f} MB")
if 'rds_out' in locals() and os.path.exists(rds_out):
    rds_size = os.path.getsize(rds_out) / 1024**2
    print(f"  rds: {rds_size:.1f} MB")
