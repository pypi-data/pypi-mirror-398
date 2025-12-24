"""10X H5 file I/O functions for GEDI.

Functions for reading 10X Genomics HDF5 files.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anndata import AnnData


def read_10x_h5(
    filename: str | Path,
    *,
    genome: str | None = None,
    gex_only: bool = True,
) -> AnnData:
    r"""Read 10X Genomics H5 file.

    Reads gene expression data from 10X Genomics HDF5 format files,
    including those from Cell Ranger.

    Parameters
    ----------
    filename
        Path to the 10X H5 file.
    genome
        Genome name to read (for multi-genome references).
        If ``None``, reads the first available genome.
    gex_only
        If ``True``, only read gene expression features (exclude
        antibody capture, CRISPR, etc. for multi-modal data).

    Returns
    -------
    Annotated data matrix with:
        - ``X``: Sparse count matrix (cells × genes)
        - ``obs``: Cell barcodes
        - ``var``: Gene information (id, name, feature_type)

    Notes
    -----
    Compatible with:
        - Cell Ranger v2 (matrix.h5)
        - Cell Ranger v3+ (filtered_feature_bc_matrix.h5)
        - Multi-modal outputs

    Examples
    --------
    >>> import gedi2py as gd
    >>> adata = gd.read_10x_h5("filtered_feature_bc_matrix.h5")
    >>> adata
    AnnData object with n_obs × n_vars = 5000 × 20000
    """
    import h5py
    import numpy as np
    import pandas as pd
    from anndata import AnnData
    from scipy import sparse

    filename = Path(filename)

    with h5py.File(filename, "r") as f:
        # Determine format version
        if "matrix" in f:
            # Cell Ranger v3+ format
            return _read_10x_h5_v3(f, genome, gex_only)
        else:
            # Cell Ranger v2 format
            return _read_10x_h5_v2(f, genome)


def _read_10x_h5_v3(f, genome: str | None, gex_only: bool) -> AnnData:
    """Read Cell Ranger v3+ format."""
    import numpy as np
    import pandas as pd
    from anndata import AnnData
    from scipy import sparse

    grp = f["matrix"]

    # Read matrix
    data = grp["data"][:]
    indices = grp["indices"][:]
    indptr = grp["indptr"][:]
    shape = grp["shape"][:]

    X = sparse.csc_matrix((data, indices, indptr), shape=shape).T.tocsr()

    # Read barcodes
    barcodes = grp["barcodes"][:].astype(str)
    obs = pd.DataFrame(index=barcodes)
    obs.index.name = "barcode"

    # Read features
    features = grp["features"]
    gene_ids = features["id"][:].astype(str)
    gene_names = features["name"][:].astype(str)
    feature_types = features["feature_type"][:].astype(str)

    var = pd.DataFrame({
        "gene_ids": gene_ids,
        "feature_types": feature_types,
    }, index=gene_names)
    var.index.name = "gene"

    # Filter to gene expression only if requested
    if gex_only:
        gex_mask = feature_types == "Gene Expression"
        if gex_mask.sum() < len(gex_mask):
            X = X[:, gex_mask]
            var = var[gex_mask]

    return AnnData(X=X, obs=obs, var=var)


def _read_10x_h5_v2(f, genome: str | None) -> AnnData:
    """Read Cell Ranger v2 format."""
    import numpy as np
    import pandas as pd
    from anndata import AnnData
    from scipy import sparse

    # Get genome
    genomes = list(f.keys())
    if genome is None:
        genome = genomes[0]
    elif genome not in genomes:
        raise ValueError(
            f"Genome '{genome}' not found. Available: {genomes}"
        )

    grp = f[genome]

    # Read matrix
    data = grp["data"][:]
    indices = grp["indices"][:]
    indptr = grp["indptr"][:]
    shape = grp["shape"][:]

    X = sparse.csc_matrix((data, indices, indptr), shape=shape).T.tocsr()

    # Read barcodes
    barcodes = grp["barcodes"][:].astype(str)
    obs = pd.DataFrame(index=barcodes)
    obs.index.name = "barcode"

    # Read genes
    gene_ids = grp["genes"][:].astype(str)
    gene_names = grp["gene_names"][:].astype(str)

    var = pd.DataFrame({
        "gene_ids": gene_ids,
    }, index=gene_names)
    var.index.name = "gene"

    return AnnData(X=X, obs=obs, var=var)


def read_10x_mtx(
    path: str | Path,
    *,
    var_names: str = "gene_symbols",
    make_unique: bool = True,
) -> AnnData:
    r"""Read 10X Genomics MTX directory.

    Reads gene expression data from 10X Genomics Market Exchange format
    directory (matrix.mtx, genes.tsv/features.tsv, barcodes.tsv).

    Parameters
    ----------
    path
        Path to the directory containing matrix files.
    var_names
        Which column to use for variable names: ``'gene_symbols'`` or
        ``'gene_ids'``.
    make_unique
        If ``True``, make variable names unique by appending suffixes.

    Returns
    -------
    Annotated data matrix.

    Examples
    --------
    >>> import gedi2py as gd
    >>> adata = gd.read_10x_mtx("filtered_feature_bc_matrix/")
    """
    import scanpy as sc

    return sc.read_10x_mtx(
        path,
        var_names=var_names,
        make_unique=make_unique,
    )
