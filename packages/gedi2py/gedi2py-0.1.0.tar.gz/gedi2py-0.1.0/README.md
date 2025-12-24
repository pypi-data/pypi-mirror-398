# gedi2py

[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://csglab.github.io/gedi2py)
[![PyPI version](https://img.shields.io/pypi/v/gedi2py)](https://pypi.org/project/gedi2py/)
[![Python](https://img.shields.io/pypi/pyversions/gedi2py)](https://pypi.org/project/gedi2py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Gene Expression Decomposition for Integration**

A scverse-compliant Python package for single-cell RNA-seq batch correction and dimensionality reduction using the GEDI algorithm.

## Overview

gedi2py implements a latent variable model for integrating single-cell RNA sequencing data across multiple samples and batches. It learns shared gene expression patterns while correcting for technical batch effects, producing batch-corrected cell embeddings suitable for downstream analysis.

## Installation

### pip (recommended)

```bash
pip install gedi2py
```

### From source

```bash
git clone https://github.com/csglab/gedi2py.git
cd gedi2py
pip install -e .
```

### Requirements

- Python >= 3.10
- C++14 compiler
- Eigen3 >= 3.3.0
- CMake >= 3.15

See the [Installation Guide](https://csglab.github.io/gedi2py/installation.html) for detailed instructions.

## Quick Start

```python
import gedi2py as gd
import scanpy as sc

# Load data
adata = sc.read_h5ad("data.h5ad")

# Preprocess
sc.pp.normalize_total(adata)
sc.pp.log1p(adata)

# Run GEDI batch correction
gd.tl.gedi(adata, batch_key="sample", n_latent=10)

# Visualize
gd.tl.umap(adata)
gd.pl.embedding(adata, color=["sample", "cell_type"])
```

## Features

- **Memory-efficient**: C++ backend keeps large matrices in native memory
- **Fast**: OpenMP parallelization for multi-threaded optimization
- **scverse-compliant**: Works seamlessly with AnnData and scanpy
- **Flexible**: Supports counts, log-transformed data, and binary indicators
- **Comprehensive**: Includes projections, embeddings, imputation, and differential analysis

## Documentation

Full documentation is available at [csglab.github.io/gedi2py](https://csglab.github.io/gedi2py):

- [Installation Guide](https://csglab.github.io/gedi2py/installation.html)
- [Quick Start Tutorial](https://csglab.github.io/gedi2py/user_guide/quickstart.html)
- [User Guide](https://csglab.github.io/gedi2py/user_guide/index.html)
- [API Reference](https://csglab.github.io/gedi2py/api/index.html)

## API Overview

gedi2py follows the scanpy convention with submodules:

| Module | Description |
|--------|-------------|
| `gd.tl` | Tools: model training, projections, embeddings, imputation, differential |
| `gd.pl` | Plotting: embeddings, convergence, features |
| `gd.io` | I/O: H5AD, 10X formats, model persistence |

```python
import gedi2py as gd

# Tools
gd.tl.gedi(adata, batch_key="sample")
gd.tl.umap(adata)

# Plotting
gd.pl.embedding(adata, color="cell_type")
gd.pl.convergence(adata)

# I/O
adata = gd.read_h5ad("data.h5ad")
gd.io.save_model(adata, "model.h5")
```

## Citation

If you use gedi2py in your research, please cite:

> Mikaeili Namini, A., & Najafabadi, H.S. (2024). GEDI: Gene Expression Decomposition for Integration of single-cell RNA-seq data.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://csglab.github.io/gedi2py)
- [GitHub Repository](https://github.com/csglab/gedi2py)
- [Issue Tracker](https://github.com/csglab/gedi2py/issues)
- [CSGLab](https://csglab.org)
