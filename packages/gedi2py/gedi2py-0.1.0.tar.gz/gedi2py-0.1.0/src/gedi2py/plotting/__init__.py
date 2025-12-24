"""Plotting module for GEDI visualizations (gd.pl).

This module follows scanpy conventions for visualization, providing:

- Embedding plots: :func:`embedding`, :func:`umap`, :func:`pca`
- Convergence: :func:`convergence`, :func:`loss`
- Features: :func:`features`, :func:`dispersion`, :func:`metagenes`, :func:`variance_explained`
"""

# Embedding plots
from ._embedding import (
    embedding,
    pca,
    umap,
)

# Convergence plots
from ._convergence import (
    convergence,
    loss,
)

# Feature plots
from ._features import (
    dispersion,
    features,
    metagenes,
    variance_explained,
)

__all__ = [
    # Embedding
    "embedding",
    "umap",
    "pca",
    # Convergence
    "convergence",
    "loss",
    # Features
    "features",
    "dispersion",
    "metagenes",
    "variance_explained",
]
