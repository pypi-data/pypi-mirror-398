"""Main GEDI integration function."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    from anndata import AnnData
    from numpy.typing import NDArray


def gedi(
    adata: AnnData,
    batch_key: str,
    *,
    n_latent: int = 10,
    layer: str | None = None,
    max_iterations: int = 100,
    track_interval: int = 5,
    mode: Literal["Bl2", "Bsphere"] = "Bsphere",
    ortho_Z: bool = True,
    C: NDArray | None = None,
    H: NDArray | None = None,
    key_added: str = "gedi",
    random_state: int | None = None,
    verbose: bool = True,
    n_jobs: int = -1,
    copy: bool = False,
) -> AnnData | None:
    r"""Run GEDI batch correction and dimensionality reduction.

    Gene Expression Decomposition for Integration (GEDI) learns shared
    metagenes and sample-specific factors for batch effect correction.

    Parameters
    ----------
    adata
        Annotated data matrix with cells as observations.
    batch_key
        Key in ``adata.obs`` for batch/sample labels.
    n_latent
        Number of latent factors (K).
    layer
        Layer to use instead of ``adata.X``. If None, uses ``adata.X``.
    max_iterations
        Maximum number of optimization iterations.
    track_interval
        Interval for tracking convergence metrics.
    mode
        Normalization mode for B matrices: "Bsphere" (recommended) or "Bl2".
    ortho_Z
        Whether to orthogonalize Z matrix.
    C
        Gene × pathway prior matrix for pathway analysis. Optional.
    H
        Covariate × sample prior matrix. Optional.
    key_added
        Base key for storing results. Results stored as:
        - ``adata.obsm[f'X_{key_added}']``: Cell embeddings
        - ``adata.varm[f'{key_added}_Z']``: Gene loadings
        - ``adata.uns[key_added]``: Parameters and metadata
    random_state
        Random seed for reproducibility. If None, uses global settings.
    verbose
        Whether to print progress messages.
    n_jobs
        Number of parallel jobs. -1 uses all available cores.
    copy
        Whether to return a copy of ``adata``.

    Returns
    -------
    Returns ``None`` if ``copy=False``, else returns an :class:`~anndata.AnnData`.
    Sets the following fields:

    ``.obsm['X_gedi']`` : :class:`numpy.ndarray`
        Cell embeddings (n_cells × n_latent).
    ``.varm['gedi_Z']`` : :class:`numpy.ndarray`
        Shared metagenes (n_genes × n_latent).
    ``.uns['gedi']`` : :class:`dict`
        Model parameters and metadata.

    Examples
    --------
    >>> import gedi2py as gd
    >>> import scanpy as sc
    >>> adata = sc.read_h5ad("data.h5ad")
    >>> gd.tl.gedi(adata, batch_key="sample", n_latent=10)
    >>> sc.pp.neighbors(adata, use_rep="X_gedi")
    >>> sc.tl.umap(adata)
    >>> gd.pl.embedding(adata, color="sample")
    """
    from .._core import GEDIModel

    adata = adata.copy() if copy else adata

    # Determine verbosity level
    verbosity = 1 if verbose else 0

    # Create and train model
    model = GEDIModel(
        adata=adata,
        batch_key=batch_key,
        n_latent=n_latent,
        layer=layer,
        mode=mode,
        ortho_Z=ortho_Z,
        C=C,
        H=H,
        random_state=random_state,
        verbose=verbosity,
        n_jobs=n_jobs,
    )

    model.train(
        max_iterations=max_iterations,
        track_interval=track_interval,
    )

    # Store results in AnnData following scverse conventions
    obsm_key = f"X_{key_added}"
    varm_key = f"{key_added}_Z"

    adata.obsm[obsm_key] = model.get_latent_representation()
    adata.varm[varm_key] = model.get_Z()
    adata.uns[key_added] = {
        "params": {
            "batch_key": batch_key,
            "n_latent": n_latent,
            "mode": mode,
            "ortho_Z": ortho_Z,
            "max_iterations": max_iterations,
            "random_state": random_state,
        },
        "model": {
            "D": model.get_D(),
            "sigma2": model.get_sigma2(),
        },
        "tracking": model.get_tracking(),
        "n_iter": model.n_iter,
    }

    return adata if copy else None
