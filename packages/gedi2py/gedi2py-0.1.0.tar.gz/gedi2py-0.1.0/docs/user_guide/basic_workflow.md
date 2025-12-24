# Basic Workflow

This tutorial demonstrates a complete gedi2py analysis workflow using PBMC data.

## Setup

```python
import gedi2py as gd
import scanpy as sc
import matplotlib.pyplot as plt

# Configure settings
gd.settings.verbosity = 1  # Show progress
gd.settings.n_jobs = 4     # Use 4 threads
```

## Load Data

gedi2py works with AnnData objects. Load your data using scanpy or gedi2py:

```python
# From H5AD file
adata = sc.read_h5ad("pbmc_data.h5ad")

# Or from 10X format
# adata = gd.read_10x_h5("filtered_feature_bc_matrix.h5")

print(f"Loaded: {adata.n_obs} cells x {adata.n_vars} genes")
print(f"Samples: {adata.obs['sample'].nunique()}")
```

## Preprocessing

Use scanpy for standard preprocessing:

```python
# Basic QC filtering
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)

# Remove mitochondrial genes (optional)
adata = adata[:, ~adata.var_names.str.startswith('MT-')]

# Normalize and log-transform
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# Select highly variable genes (optional, for large datasets)
sc.pp.highly_variable_genes(adata, n_top_genes=2000)
adata = adata[:, adata.var.highly_variable]

print(f"After filtering: {adata.n_obs} cells x {adata.n_vars} genes")
```

## Run GEDI

Train the GEDI model to learn latent representations:

```python
# Run GEDI with default parameters
gd.tl.gedi(
    adata,
    batch_key="sample",      # Column with sample/batch labels
    n_latent=10,             # Number of latent factors
    max_iterations=100,      # Optimization iterations
    track_interval=5,        # Track convergence every N iterations
)
```

### Monitor Convergence

Check that the model converged properly:

```python
# Plot convergence metrics
gd.pl.convergence(adata, which="all")
plt.show()

# Check final noise variance
sigma2 = adata.uns['gedi']['sigma2']
print(f"Final sigma2: {sigma2:.6f}")
```

## Compute Embeddings

### UMAP

```python
# Compute UMAP on GEDI embedding
gd.tl.umap(adata)

# Visualize
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

gd.pl.umap(adata, color="sample", ax=axes[0], title="By Sample")
gd.pl.umap(adata, color="cell_type", ax=axes[1], title="By Cell Type")

plt.tight_layout()
plt.show()
```

### PCA

```python
# Compute PCA on GEDI embedding
gd.tl.pca(adata)

# Visualize variance explained
gd.pl.variance_explained(adata)
plt.show()
```

## Explore Projections

GEDI provides multiple projections for different analyses:

```python
# ZDB: Full projection (shared manifold)
gd.tl.get_projection(adata, which="zdb")

# DB: Latent factors only
gd.tl.get_projection(adata, which="db")
```

## Gene Expression Features

Visualize gene expression on the GEDI embedding:

```python
# Plot marker genes
gd.pl.features(
    adata,
    features=["CD3D", "CD14", "MS4A1", "NKG7"],
    basis="X_gedi_umap",
    ncols=2,
)
plt.show()
```

## Imputation

Impute denoised expression values:

```python
# Impute expression for all samples
gd.tl.impute(adata)

# Access imputed values
imputed = adata.layers['gedi_imputed']
```

## Save Results

```python
# Save the full AnnData with GEDI results
adata.write_h5ad("pbmc_with_gedi.h5ad")

# Save just the GEDI model (smaller)
gd.io.save_model(adata, "gedi_model.h5")
```

## Load Saved Model

```python
# Load model into a new AnnData
adata_new = sc.read_h5ad("pbmc_data.h5ad")
gd.io.load_model(adata_new, "gedi_model.h5")
```

## Summary

This workflow covered:

1. Loading and preprocessing data
2. Running GEDI for batch correction
3. Computing UMAP/PCA embeddings
4. Visualizing results
5. Exploring projections and imputation
6. Saving and loading models

For multi-sample batch correction and comparison, see the [Batch Correction](batch_correction.md) tutorial.
