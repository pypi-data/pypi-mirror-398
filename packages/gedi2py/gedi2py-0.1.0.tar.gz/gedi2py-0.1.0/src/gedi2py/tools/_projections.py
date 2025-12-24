"""Projection functions for GEDI results.

Projections transform GEDI model parameters into interpretable cell-space
or gene-space representations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    from anndata import AnnData

from .._logging import debug, info


def get_projection(
    adata: AnnData,
    which: Literal["zdb", "db", "adb"] = "zdb",
    *,
    key: str = "gedi",
    key_added: str | None = None,
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    r"""Compute and retrieve GEDI projections.

    Projections transform the learned GEDI parameters into interpretable
    representations:

    - **ZDB**: Shared manifold projection (genes × cells) = Z @ diag(D) @ B
    - **DB**: Latent factor embedding (K × cells) = diag(D) @ B
    - **ADB**: Pathway activity projection (pathways × cells) = C_rot @ A @ diag(D) @ B

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results in ``.uns[key]``.
    which
        Which projection to compute: ``"zdb"``, ``"db"``, or ``"adb"``.
    key
        Key in ``adata.uns`` where GEDI results are stored.
    key_added
        Key to store the result in ``adata.obsm``. If ``None``, defaults to
        ``X_{key}_{which}`` (e.g., ``X_gedi_zdb``).
    copy
        If ``True``, return a copy of the projection array instead of
        storing in ``adata``.

    Returns
    -------
    If ``copy=True``, returns the projection as a numpy array.
    Otherwise, stores the result in ``adata.obsm[key_added]`` and returns ``None``.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.gedi(adata, batch_key="sample", n_latent=10)
    >>> gd.tl.get_projection(adata, "zdb")
    >>> adata.obsm["X_gedi_zdb"]  # (n_cells, n_genes)
    """
    from .._core import GEDIModel

    # Validate GEDI results exist
    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    gedi_data = adata.uns[key]
    if "model" not in gedi_data:
        raise ValueError(
            f"No model parameters found in adata.uns['{key}']. "
            f"Ensure gd.tl.gedi() completed successfully."
        )

    model_params = gedi_data["model"]
    which_lower = which.lower()

    # Compute projection based on type
    if which_lower == "zdb":
        projection = _compute_zdb(model_params)
    elif which_lower == "db":
        projection = _compute_db(model_params)
    elif which_lower == "adb":
        projection = _compute_adb(model_params)
    else:
        raise ValueError(
            f"Invalid projection type: {which}. "
            f"Must be one of: 'zdb', 'db', 'adb'."
        )

    if copy:
        return projection

    # Store in adata.obsm
    if key_added is None:
        key_added = f"X_{key}_{which_lower}"

    adata.obsm[key_added] = projection
    info(f"Added projection to adata.obsm['{key_added}']")

    return None


def _compute_zdb(model_params: dict) -> np.ndarray:
    """Compute ZDB = Z @ diag(D) @ B projection.

    Returns (n_cells, n_genes) array - transposed from R's (genes × cells).
    """
    Z = model_params["Z"]  # (n_genes, K)
    D = model_params["D"]  # (K,)
    Bi_list = model_params["Bi"]  # list of (K, n_cells_i)

    debug("Computing ZDB projection")

    # Concatenate all Bi matrices
    B = np.hstack(Bi_list)  # (K, n_cells)

    # ZDB = Z @ diag(D) @ B
    ZDB = Z @ np.diag(D) @ B  # (n_genes, n_cells)

    # Transpose to (n_cells, n_genes) for AnnData convention
    return ZDB.T


def _compute_db(model_params: dict) -> np.ndarray:
    """Compute DB = diag(D) @ B projection.

    Returns (n_cells, K) array - latent factor embedding.
    """
    D = model_params["D"]  # (K,)
    Bi_list = model_params["Bi"]  # list of (K, n_cells_i)

    debug("Computing DB projection")

    # Concatenate all Bi matrices
    B = np.hstack(Bi_list)  # (K, n_cells)

    # DB = diag(D) @ B
    DB = np.diag(D) @ B  # (K, n_cells)

    # Transpose to (n_cells, K) for AnnData convention
    return DB.T


def _compute_adb(model_params: dict) -> np.ndarray:
    """Compute ADB = C_rotation @ A @ diag(D) @ B projection.

    Returns (n_cells, n_pathways) array - pathway activity scores.
    """
    # Check if pathway-related parameters exist
    if "A" not in model_params or model_params["A"] is None:
        raise ValueError(
            "ADB projection requires pathway priors (C matrix). "
            "Pass C parameter to gd.tl.gedi()."
        )

    A = model_params["A"]  # (P, K)
    D = model_params["D"]  # (K,)
    Bi_list = model_params["Bi"]  # list of (K, n_cells_i)
    C_rotation = model_params.get("C_rotation")  # (P, P) or None

    if C_rotation is None:
        raise ValueError(
            "C_rotation not found in model parameters. "
            "Ensure pathway priors were properly processed."
        )

    debug("Computing ADB projection")

    # Concatenate all Bi matrices
    B = np.hstack(Bi_list)  # (K, n_cells)

    # ADB = C_rotation @ A @ diag(D) @ B
    ADB = C_rotation @ A @ np.diag(D) @ B  # (P, n_cells)

    # Transpose to (n_cells, P) for AnnData convention
    return ADB.T


def compute_zdb(
    adata: AnnData,
    *,
    key: str = "gedi",
    key_added: str | None = None,
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    """Compute ZDB (shared manifold) projection.

    Alias for ``get_projection(adata, "zdb", ...)``.

    See :func:`get_projection` for full documentation.
    """
    return get_projection(adata, "zdb", key=key, key_added=key_added, copy=copy)


def compute_db(
    adata: AnnData,
    *,
    key: str = "gedi",
    key_added: str | None = None,
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    """Compute DB (latent factor embedding) projection.

    Alias for ``get_projection(adata, "db", ...)``.

    See :func:`get_projection` for full documentation.
    """
    return get_projection(adata, "db", key=key, key_added=key_added, copy=copy)


def compute_adb(
    adata: AnnData,
    *,
    key: str = "gedi",
    key_added: str | None = None,
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    """Compute ADB (pathway activity) projection.

    Alias for ``get_projection(adata, "adb", ...)``.

    See :func:`get_projection` for full documentation.
    """
    return get_projection(adata, "adb", key=key, key_added=key_added, copy=copy)
