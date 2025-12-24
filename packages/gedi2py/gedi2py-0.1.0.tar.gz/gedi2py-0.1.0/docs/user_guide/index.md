# User Guide

This guide provides tutorials and examples for using gedi2py to integrate single-cell RNA-seq data.

## Tutorials

```{toctree}
:maxdepth: 2

quickstart
basic_workflow
batch_correction
```

## Overview

gedi2py uses the GEDI (Gene Expression Decomposition for Integration) algorithm to learn a shared gene expression space across multiple samples while correcting for batch effects.

### The GEDI Model

GEDI models gene expression as:

$$Y_i = ZDB_i + Q_i B_i + \mathbf{1}s_i^T + o_i\mathbf{1}^T + o\mathbf{1}^T + \epsilon$$

Where:
- $Y_i$ is the log-transformed expression matrix for sample $i$
- $Z$ is the shared metagene matrix (genes × latent factors)
- $D$ is a diagonal scaling matrix
- $B_i$ is the sample-specific cell factor matrix
- $Q_i$ captures sample-specific deviations
- $s_i$ and $o_i$ are cell and gene offsets
- $o$ is the global gene offset

### Workflow

A typical gedi2py workflow consists of:

1. **Load data** - Read H5AD files or other formats
2. **Preprocess** - Filter, normalize, log-transform (using scanpy)
3. **Run GEDI** - Train the model to learn latent factors
4. **Analyze** - Compute projections, embeddings, differential expression
5. **Visualize** - Plot results using gedi2py or scanpy

### API Convention

gedi2py follows the scanpy API convention:

```python
import gedi2py as gd

# Tools module (gd.tl)
gd.tl.gedi(adata, ...)        # Run GEDI
gd.tl.umap(adata, ...)        # Compute UMAP

# Plotting module (gd.pl)
gd.pl.embedding(adata, ...)   # Plot embeddings
gd.pl.convergence(adata, ...) # Plot convergence

# I/O module (gd.io)
gd.read_h5ad(...)             # Read data
gd.write_h5ad(...)            # Write data
```

Results are stored in the AnnData object:
- `adata.obsm['X_gedi']` - Cell embeddings (DB projection)
- `adata.varm['gedi_Z']` - Gene loadings (Z matrix)
- `adata.uns['gedi']` - Model parameters and metadata

## Next Steps

- Start with the [Quick Start](quickstart.md) for a minimal example
- See [Basic Workflow](basic_workflow.md) for a complete analysis
- Learn about [Batch Correction](batch_correction.md) for multi-sample integration
