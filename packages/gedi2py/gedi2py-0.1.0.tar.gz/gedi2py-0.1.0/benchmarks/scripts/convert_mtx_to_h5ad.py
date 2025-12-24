#!/usr/bin/env python
"""
convert_mtx_to_h5ad.py - Convert MTX files from R preprocessing to h5ad

This script reads the Matrix Market files exported by preprocess_200k.R
and creates an h5ad file for Python benchmarking.
"""

import os
import pandas as pd
import numpy as np
import scipy.io as sio
import scipy.sparse as sp
import anndata as ad

# Configuration
DATA_DIR = "/home/saberi/projects/gedi/gedipy/benchmarks/data"
PREFIX = "benchmark_data_200k"

print("=" * 50)
print("Converting MTX to H5AD")
print("=" * 50)

# Read Matrix Market file
mtx_file = os.path.join(DATA_DIR, f"{PREFIX}_matrix.mtx")
print(f"Reading matrix: {mtx_file}")
# MTX is in genes x cells format from R
X = sio.mmread(mtx_file).T.tocsr()  # Transpose to cells x genes
print(f"  Shape (cells x genes): {X.shape}")

# Read gene names
genes_file = os.path.join(DATA_DIR, f"{PREFIX}_genes.csv")
print(f"Reading genes: {genes_file}")
genes_df = pd.read_csv(genes_file)
gene_names = genes_df['gene'].values
print(f"  Genes: {len(gene_names)}")

# Read cell metadata
cells_file = os.path.join(DATA_DIR, f"{PREFIX}_cells.csv")
print(f"Reading cells: {cells_file}")
cells_df = pd.read_csv(cells_file)
print(f"  Cells: {len(cells_df)}")

# Verify dimensions match
assert X.shape[0] == len(cells_df), f"Cell count mismatch: {X.shape[0]} vs {len(cells_df)}"
assert X.shape[1] == len(gene_names), f"Gene count mismatch: {X.shape[1]} vs {len(gene_names)}"

# Create AnnData object
print("\nCreating AnnData...")
obs_df = pd.DataFrame({
    'sample': cells_df['sample'].values
}, index=cells_df['cell'].values)

var_df = pd.DataFrame({
    'gene_name': gene_names
}, index=gene_names)

adata = ad.AnnData(
    X=X,
    obs=obs_df,
    var=var_df
)

# Save as h5ad
h5ad_out = os.path.join(DATA_DIR, f"{PREFIX}.h5ad")
print(f"\nSaving h5ad: {h5ad_out}")
adata.write_h5ad(h5ad_out)

# Print summary
h5ad_size = os.path.getsize(h5ad_out) / 1024**2
print(f"\nDone!")
print(f"  Output: {h5ad_out}")
print(f"  Size: {h5ad_size:.1f} MB")
print(f"  Shape: {adata.shape}")
print(f"  Samples: {adata.obs['sample'].nunique()}")

# Clean up intermediate files (optional)
cleanup = input("\nRemove intermediate MTX/CSV files? [y/N]: ").strip().lower()
if cleanup == 'y':
    for f in [mtx_file, genes_file, cells_file]:
        if os.path.exists(f):
            os.remove(f)
            print(f"  Removed: {f}")
