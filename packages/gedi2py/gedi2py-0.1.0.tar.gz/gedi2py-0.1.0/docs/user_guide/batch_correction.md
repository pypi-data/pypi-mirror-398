# Batch Correction

This tutorial demonstrates how to use GEDI for integrating multiple samples with batch effects.

## The Problem

When combining single-cell data from multiple samples, batches, or experiments, technical variation can obscure biological signals. GEDI learns a shared gene expression space that separates biological variation from technical batch effects.

## Setup

```python
import gedi2py as gd
import scanpy as sc
import matplotlib.pyplot as plt
import numpy as np

gd.settings.n_jobs = -1  # Use all available threads
```

## Load Multi-Sample Data

```python
# Load combined dataset with multiple samples
adata = sc.read_h5ad("multi_sample_data.h5ad")

# Check sample distribution
print(adata.obs['sample'].value_counts())

# Visualize samples
print(f"Total: {adata.n_obs} cells from {adata.obs['sample'].nunique()} samples")
```

## Preprocess

```python
# Standard preprocessing
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# Keep highly variable genes
sc.pp.highly_variable_genes(adata, n_top_genes=3000, batch_key="sample")
adata = adata[:, adata.var.highly_variable]
```

## Uncorrected Baseline

First, see the data without batch correction:

```python
# Standard PCA + UMAP (no batch correction)
sc.tl.pca(adata)
sc.pp.neighbors(adata)
sc.tl.umap(adata)

# Plot uncorrected
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
sc.pl.umap(adata, color="sample", ax=axes[0], title="Uncorrected - by Sample")
sc.pl.umap(adata, color="cell_type", ax=axes[1], title="Uncorrected - by Cell Type")
plt.tight_layout()
plt.savefig("uncorrected.png", dpi=150)
plt.show()
```

## Run GEDI Batch Correction

```python
# Run GEDI
gd.tl.gedi(
    adata,
    batch_key="sample",
    n_latent=15,              # More factors for complex data
    max_iterations=100,
    mode="Bsphere",           # Spherical constraint on B
    ortho_Z=True,             # Orthogonalize Z matrix
)

# Check convergence
gd.pl.convergence(adata)
plt.savefig("convergence.png", dpi=150)
plt.show()
```

## Corrected Embedding

```python
# Compute UMAP on GEDI-corrected embedding
gd.tl.umap(adata)

# Plot corrected
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
gd.pl.umap(adata, color="sample", ax=axes[0], title="GEDI Corrected - by Sample")
gd.pl.umap(adata, color="cell_type", ax=axes[1], title="GEDI Corrected - by Cell Type")
plt.tight_layout()
plt.savefig("gedi_corrected.png", dpi=150)
plt.show()
```

## Compare Before and After

```python
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Uncorrected
sc.pl.umap(adata, color="sample", ax=axes[0, 0], title="Uncorrected - Sample", show=False)
sc.pl.umap(adata, color="cell_type", ax=axes[0, 1], title="Uncorrected - Cell Type", show=False)

# GEDI corrected
gd.pl.embedding(adata, basis="X_gedi_umap", color="sample", ax=axes[1, 0],
                title="GEDI - Sample")
gd.pl.embedding(adata, basis="X_gedi_umap", color="cell_type", ax=axes[1, 1],
                title="GEDI - Cell Type")

plt.tight_layout()
plt.savefig("comparison.png", dpi=150)
plt.show()
```

## Quantify Batch Mixing

Use standard metrics to quantify batch correction quality:

```python
# kBET, LISI, or silhouette scores can be computed
# using scib or other evaluation packages

# Simple silhouette score comparison
from sklearn.metrics import silhouette_score

# Silhouette by cell type (should be HIGH - preserve biology)
sil_bio = silhouette_score(adata.obsm['X_gedi'], adata.obs['cell_type'])
print(f"Silhouette (cell type): {sil_bio:.3f}")

# Silhouette by batch (should be LOW - good mixing)
sil_batch = silhouette_score(adata.obsm['X_gedi'], adata.obs['sample'])
print(f"Silhouette (batch): {sil_batch:.3f}")
```

## Differential Expression

Find genes that differ between conditions after batch correction:

```python
# Create contrast vector for condition comparison
# Example: Compare condition A vs condition B
conditions = adata.obs['condition'].unique()
contrast = np.zeros(len(adata.obs['sample'].unique()))

for i, sample in enumerate(adata.obs['sample'].unique()):
    sample_condition = adata.obs.loc[adata.obs['sample'] == sample, 'condition'].iloc[0]
    if sample_condition == conditions[0]:
        contrast[i] = 1
    else:
        contrast[i] = -1

# Normalize contrast
contrast = contrast / np.abs(contrast).sum()

# Compute differential expression
gd.tl.differential(adata, contrast=contrast)

# Access results
de_genes = adata.varm['gedi_differential']
top_genes = adata.var_names[np.argsort(np.abs(de_genes.flatten()))[::-1][:20]]
print("Top differential genes:", top_genes.tolist())
```

## Advanced: Using GEDIModel Directly

For more control, use the GEDIModel class:

```python
# Create model
model = gd.GEDIModel(
    adata,
    batch_key="sample",
    n_latent=15,
    mode="Bsphere",
    ortho_Z=True,
    verbose=2,
    n_jobs=-1,
)

# Initialize
model.initialize()

# Run optimization in steps
for i in range(10):
    model.optimize(iterations=10, track_interval=1)
    print(f"Iteration {(i+1)*10}: sigma2 = {model.get_sigma2():.6f}")

# Get results
Z = model.get_Z()           # Shared metagenes
D = model.get_D()           # Scaling factors
embeddings = model.get_latent_representation()  # Cell embeddings
```

## Tips for Best Results

### Choosing n_latent

- Start with 10-20 for typical datasets
- More complex data may need 30-50
- Too few: lose biological variation
- Too many: overfit to noise

### Preprocessing

- Always log-transform count data
- Consider highly variable gene selection for large datasets
- Remove low-quality cells and genes

### Convergence

- Check that sigma2 stabilizes
- If not converging, try more iterations or different n_latent
- Monitor dZ and dA for stability

## Summary

GEDI batch correction:
1. Learns shared gene expression patterns (Z)
2. Models sample-specific factors (B, Q, o)
3. Produces batch-corrected embeddings (DB)
4. Preserves biological variation while removing technical effects

The corrected embeddings can be used for clustering, trajectory analysis, and visualization.
