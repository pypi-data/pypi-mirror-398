"""Tools module for GEDI analysis functions (gd.tl).

This module follows the scanpy convention for computational analysis tools,
providing functions for:

- Model training: :func:`gedi`
- Projections: :func:`get_projection`, :func:`compute_zdb`, :func:`compute_db`, :func:`compute_adb`
- Embeddings: :func:`svd`, :func:`pca`, :func:`umap`
- Imputation: :func:`impute`, :func:`variance`, :func:`dispersion`
- Differential: :func:`differential`, :func:`diff_q`, :func:`diff_o`
- Pathways: :func:`pathway_associations`, :func:`pathway_scores`, :func:`top_pathway_genes`
- Dynamics: :func:`vector_field`, :func:`gradient`, :func:`pseudotime`
"""

# Main GEDI function
from ._gedi import gedi

# Projections
from ._projections import (
    compute_adb,
    compute_db,
    compute_zdb,
    get_projection,
)

# Embeddings
from ._embeddings import (
    pca,
    svd,
    umap,
)

# Imputation
from ._imputation import (
    dispersion,
    impute,
    variance,
)

# Differential expression
from ._differential import (
    diff_o,
    diff_q,
    differential,
)

# Pathway analysis
from ._pathways import (
    pathway_associations,
    pathway_scores,
    top_pathway_genes,
)

# Dynamics / trajectory
from ._dynamics import (
    gradient,
    pseudotime,
    vector_field,
)

__all__ = [
    # Main
    "gedi",
    # Projections
    "get_projection",
    "compute_zdb",
    "compute_db",
    "compute_adb",
    # Embeddings
    "svd",
    "pca",
    "umap",
    # Imputation
    "impute",
    "variance",
    "dispersion",
    # Differential
    "differential",
    "diff_q",
    "diff_o",
    # Pathways
    "pathway_associations",
    "pathway_scores",
    "top_pathway_genes",
    # Dynamics
    "vector_field",
    "gradient",
    "pseudotime",
]
