"""Pathway analysis functions for GEDI.

Provides pathway association analysis based on the gene-level prior
matrix C and learned pathway coefficients A.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scipy import sparse

if TYPE_CHECKING:
    from anndata import AnnData

from .._logging import debug, info


def pathway_associations(
    adata: AnnData,
    *,
    sparse_output: bool = False,
    key: str = "gedi",
    key_added: str | None = None,
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    r"""Compute pathway-gene associations from GEDI model.

    Uses the pathway coefficient matrix A and gene loading matrix Z to
    compute associations between pathways and genes, accounting for
    the learned latent structure.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    sparse_output
        If ``True``, return a sparse matrix. Useful for large pathway sets.
    key
        Key in ``adata.uns`` where GEDI results are stored.
    key_added
        Key to store results in ``adata.varm``. Defaults to
        ``{key}_pathway_assoc``.
    copy
        If ``True``, return the association matrix instead of storing in ``adata``.

    Returns
    -------
    If ``copy=True``, returns pathway association matrix (n_genes, n_pathways).
    Otherwise, stores in ``adata.varm[key_added]`` and returns ``None``.

    Notes
    -----
    Pathway associations require that a gene-level prior matrix C was provided
    during model training via ``gd.tl.gedi(..., C=pathway_matrix)``.

    The association matrix represents how strongly each gene is associated
    with each pathway through the learned latent factors.

    Examples
    --------
    >>> import gedi2py as gd
    >>> # C is (n_genes, n_pathways) pathway membership matrix
    >>> gd.tl.gedi(adata, batch_key="sample", C=pathway_matrix)
    >>> gd.tl.pathway_associations(adata)
    >>> adata.varm["gedi_pathway_assoc"]  # (n_genes, n_pathways)
    """
    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    gedi_data = adata.uns[key]
    model_params = gedi_data.get("model", {})
    params = gedi_data.get("params", {})

    # Check if C was provided
    A = model_params.get("A")
    Z = model_params.get("Z")
    C_rotation = model_params.get("C_rotation")

    if A is None:
        raise ValueError(
            "Pathway analysis requires gene-level prior matrix C. "
            "Pass C parameter to gd.tl.gedi()."
        )

    P = params.get("P", A.shape[0])
    debug(f"Computing pathway associations for {P} pathways")

    # Compute gene-pathway associations
    # Association = Z @ A^T gives how each gene relates to each pathway
    # through the latent factors
    associations = Z @ A.T  # (J, P)

    if sparse_output:
        associations = sparse.csr_matrix(associations)

    if copy:
        return associations

    # Store in adata.varm
    if key_added is None:
        key_added = f"{key}_pathway_assoc"

    adata.varm[key_added] = associations
    info(f"Added pathway associations to adata.varm['{key_added}']")

    return None


def pathway_scores(
    adata: AnnData,
    *,
    key: str = "gedi",
    key_added: str | None = None,
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    r"""Compute per-cell pathway activity scores.

    Uses the ADB projection (pathway activity) to compute pathway scores
    for each cell.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    key
        Key in ``adata.uns`` where GEDI results are stored.
    key_added
        Key to store results in ``adata.obsm``. Defaults to
        ``X_{key}_pathway_scores``.
    copy
        If ``True``, return the score matrix instead of storing in ``adata``.

    Returns
    -------
    If ``copy=True``, returns pathway score matrix (n_cells, n_pathways).
    Otherwise, stores in ``adata.obsm[key_added]`` and returns ``None``.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.gedi(adata, batch_key="sample", C=pathway_matrix)
    >>> gd.tl.pathway_scores(adata)
    >>> adata.obsm["X_gedi_pathway_scores"]  # (n_cells, n_pathways)
    """
    from ._projections import get_projection

    # ADB projection gives pathway activity scores
    if copy:
        return get_projection(adata, "adb", key=key, copy=True)

    if key_added is None:
        key_added = f"X_{key}_pathway_scores"

    get_projection(adata, "adb", key=key, key_added=key_added)
    return None


def top_pathway_genes(
    adata: AnnData,
    pathway_idx: int,
    *,
    n_genes: int = 20,
    key: str = "gedi",
) -> list[str]:
    r"""Get top genes associated with a pathway.

    Returns the genes with the highest association scores for a given
    pathway, based on the pathway association matrix.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    pathway_idx
        Index of the pathway to query.
    n_genes
        Number of top genes to return.
    key
        Key in ``adata.uns`` where GEDI results are stored.

    Returns
    -------
    List of gene names with highest pathway associations.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.pathway_associations(adata)
    >>> top_genes = gd.tl.top_pathway_genes(adata, pathway_idx=0, n_genes=10)
    >>> print(top_genes)
    """
    # Ensure pathway associations are computed
    assoc_key = f"{key}_pathway_assoc"
    if assoc_key not in adata.varm:
        pathway_associations(adata, key=key)

    associations = adata.varm[assoc_key]

    # Get pathway column
    if pathway_idx >= associations.shape[1]:
        raise ValueError(
            f"pathway_idx {pathway_idx} out of range. "
            f"Maximum index is {associations.shape[1] - 1}."
        )

    pathway_scores = associations[:, pathway_idx]

    # Handle sparse matrices
    if sparse.issparse(pathway_scores):
        pathway_scores = pathway_scores.toarray().ravel()

    # Get top gene indices
    top_indices = np.argsort(np.abs(pathway_scores))[::-1][:n_genes]

    # Return gene names
    gene_names = adata.var_names[top_indices].tolist()

    return gene_names
