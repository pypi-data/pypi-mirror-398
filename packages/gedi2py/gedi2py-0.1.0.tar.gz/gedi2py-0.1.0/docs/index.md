# gedi2py

**Gene Expression Decomposition for Integration**

*A scverse-compliant Python package for single-cell RNA-seq batch correction and dimensionality reduction.*

---

gedi2py implements the GEDI algorithm for integrating single-cell RNA sequencing data across multiple samples and batches. It uses a latent variable model with block coordinate descent optimization to learn shared gene expression patterns while correcting for batch effects.

## Quick Install

```bash
pip install gedi2py
```

## Quick Start

```python
import gedi2py as gd
import scanpy as sc

# Load your data
adata = sc.read_h5ad("data.h5ad")

# Run GEDI batch correction
gd.tl.gedi(adata, batch_key="sample", n_latent=10)

# Compute UMAP embedding
gd.tl.umap(adata)

# Visualize
gd.pl.embedding(adata, color=["sample", "cell_type"])
```

## Key Features

- **Memory-efficient**: C++ backend keeps large matrices in native memory
- **Fast**: OpenMP parallelization for multi-threaded optimization
- **scverse-compliant**: Works seamlessly with AnnData, scanpy, and the scverse ecosystem
- **Flexible**: Supports multiple input types (counts, log-transformed, binary)
- **Comprehensive**: Includes projections, embeddings, imputation, and differential analysis

## Documentation

```{toctree}
:maxdepth: 2
:caption: Getting Started

installation
user_guide/index
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/index
```

## Modules

gedi2py follows the scanpy convention with submodules for different functionality:

| Module | Description |
|--------|-------------|
| `gd.tl` | Tools for model training, projections, embeddings, imputation, and analysis |
| `gd.pl` | Plotting functions for embeddings, convergence, and feature visualization |
| `gd.io` | Input/output for H5AD, 10X formats, and model persistence |

## Citation

If you use gedi2py in your research, please cite:

> Mikaeili Namini, A., & Najafabadi, H.S. (2024). GEDI: Gene Expression Decomposition for Integration of single-cell RNA-seq data.

## Links

- [GitHub Repository](https://github.com/csglab/gedi2py)
- [Issue Tracker](https://github.com/csglab/gedi2py/issues)
- [CSGLab](https://csglab.org)

## License

gedi2py is released under the MIT License.
