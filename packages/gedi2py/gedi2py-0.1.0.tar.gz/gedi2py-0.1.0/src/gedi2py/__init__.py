"""gedi2py: Gene Expression Decomposition for Integration.

A scverse-compliant Python package for single-cell RNA-seq batch correction
and dimensionality reduction using the GEDI algorithm.

Usage
-----
>>> import gedi2py as gd
>>> import scanpy as sc

>>> # Load data
>>> adata = sc.read_h5ad("data.h5ad")

>>> # Run GEDI batch correction
>>> gd.tl.gedi(adata, batch_key="sample", n_latent=10)

>>> # Compute embeddings
>>> gd.tl.umap(adata)

>>> # Visualize
>>> gd.pl.embedding(adata, color="sample")

Modules
-------
- ``gd.tl``: Tools for analysis (gedi, projections, embeddings, etc.)
- ``gd.pp``: Preprocessing functions
- ``gd.pl``: Plotting functions
- ``gd.io``: Input/output functions
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gedi2py")
except PackageNotFoundError:
    __version__ = "0.1.0.dev"

# Import submodules following scverse convention
from . import io
from . import plotting as pl
from . import preprocessing as pp
from . import tools as tl

# Import main model class for direct access
from ._core import GEDIModel

# Import settings
from ._settings import settings

# Convenience I/O functions at top level
from .io import (
    read_10x_h5,
    read_10x_mtx,
    read_h5ad,
    write_h5ad,
)

__all__ = [
    # Version
    "__version__",
    # Submodules
    "tl",
    "pp",
    "pl",
    "io",
    # Core class
    "GEDIModel",
    # Settings
    "settings",
    # Convenience I/O functions
    "read_h5ad",
    "write_h5ad",
    "read_10x_h5",
    "read_10x_mtx",
]
