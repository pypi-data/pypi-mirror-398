# Quick Start

This guide shows the minimal steps to run GEDI on your single-cell data.

## Minimal Example

```python
import gedi2py as gd
import scanpy as sc

# 1. Load data (AnnData with sample/batch labels)
adata = sc.read_h5ad("your_data.h5ad")

# 2. Preprocess with scanpy
sc.pp.filter_genes(adata, min_cells=3)
sc.pp.normalize_total(adata)
sc.pp.log1p(adata)

# 3. Run GEDI
gd.tl.gedi(adata, batch_key="sample", n_latent=10)

# 4. Visualize
gd.tl.umap(adata)
gd.pl.embedding(adata, color="sample")
```

## What This Does

1. **Load data**: Reads an H5AD file containing your expression matrix and cell metadata
2. **Preprocess**: Standard single-cell preprocessing (filter, normalize, log-transform)
3. **Run GEDI**: Trains the GEDI model to learn:
   - Shared metagenes across samples
   - Sample-specific cell embeddings
   - Batch-corrected representations
4. **Visualize**: Computes UMAP and plots cells colored by sample

## Understanding the Output

After running `gd.tl.gedi()`, your AnnData object contains:

```python
# Cell embeddings (batch-corrected)
adata.obsm['X_gedi']        # shape: (n_cells, n_latent)

# Gene loadings
adata.varm['gedi_Z']        # shape: (n_genes, n_latent)

# Model parameters
adata.uns['gedi']['D']      # Scaling factors
adata.uns['gedi']['sigma2'] # Noise variance
adata.uns['gedi']['params'] # Full parameter dictionary
```

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `batch_key` | required | Column in `adata.obs` with sample/batch labels |
| `n_latent` | 10 | Number of latent factors (metagenes) |
| `max_iterations` | 100 | Maximum optimization iterations |
| `mode` | "Bsphere" | Constraint on B matrices ("Bsphere" or "Bl2") |

## Next Steps

- See [Basic Workflow](basic_workflow.md) for a complete analysis pipeline
- Learn about [Batch Correction](batch_correction.md) for multi-sample integration
- Check the [API Reference](../api/index.rst) for all available functions
