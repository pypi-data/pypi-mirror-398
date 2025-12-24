"""Differential expression functions for GEDI.

Provides differential expression analysis based on GEDI model parameters
and sample-level covariates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    from anndata import AnnData

from .._logging import debug, info, warning


def differential(
    adata: AnnData,
    contrast: np.ndarray | list,
    *,
    mode: Literal["full", "offset", "metagene"] = "full",
    include_offset: bool = True,
    key: str = "gedi",
    key_added: str | None = None,
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    r"""Compute differential expression effects from GEDI model.

    Uses the sample-level covariate matrix H and learned regression
    coefficients (Rk, Ro) to compute differential expression effects
    for a given contrast.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    contrast
        Contrast vector of length L (number of covariates). Specifies
        the linear combination of covariate effects to compute.
    mode
        Type of differential effect to compute:
        - ``"full"``: Full cell-specific effect (diffQ, J × N matrix)
        - ``"offset"``: Global gene offset effect (diffO, J vector)
        - ``"metagene"``: Effect on metagene loadings
    include_offset
        If ``True`` and mode is ``"full"``, add the offset effect (diffO)
        to the cell-specific effect.
    key
        Key in ``adata.uns`` where GEDI results are stored.
    key_added
        Key to store results. Defaults depend on mode:
        - ``"full"``: ``adata.layers['{key}_diff']``
        - ``"offset"``: ``adata.var['{key}_diff_offset']``
    copy
        If ``True``, return the result instead of storing in ``adata``.

    Returns
    -------
    Depending on mode and copy:
    - ``mode="full"``, ``copy=True``: (n_cells, n_genes) array
    - ``mode="offset"``, ``copy=True``: (n_genes,) array
    - Otherwise: ``None`` (stores in adata)

    Notes
    -----
    Differential effects require that a covariate matrix H was provided
    during model training via ``gd.tl.gedi(..., H=covariate_matrix)``.

    The contrast vector defines a linear combination of covariate effects.
    For example, with covariates [treatment, sex], a contrast of [1, 0]
    computes the treatment effect, while [1, -1] computes the interaction.

    Examples
    --------
    >>> import gedi2py as gd
    >>> import numpy as np
    >>> # Assuming H is (n_samples, 2) with [treatment, control]
    >>> gd.tl.gedi(adata, batch_key="sample", H=H_matrix)
    >>> contrast = np.array([1, -1])  # treatment - control
    >>> gd.tl.differential(adata, contrast)
    >>> adata.layers["gedi_diff"]  # (n_cells, n_genes)
    """
    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    gedi_data = adata.uns[key]
    model_params = gedi_data.get("model", {})
    params = gedi_data.get("params", {})

    # Check if H was provided
    Rk_list = model_params.get("Rk")
    Ro = model_params.get("Ro")
    H_rotation = model_params.get("H_rotation")

    if Rk_list is None or Ro is None:
        raise ValueError(
            "Differential analysis requires covariate matrix H. "
            "Pass H parameter to gd.tl.gedi()."
        )

    # Validate contrast
    contrast = np.asarray(contrast)
    L = params.get("L", len(contrast))

    if len(contrast) != L:
        raise ValueError(
            f"Contrast length ({len(contrast)}) does not match "
            f"number of covariates ({L})."
        )

    if mode == "offset":
        result = _compute_diff_offset(Ro, H_rotation, contrast)
    elif mode == "full":
        result = _compute_diff_full(
            Rk_list,
            model_params["D"],
            model_params["Bi"],
            H_rotation,
            contrast,
            include_offset=include_offset,
            Ro=Ro if include_offset else None,
        )
    elif mode == "metagene":
        result = _compute_diff_metagene(Rk_list, H_rotation, contrast)
    else:
        raise ValueError(
            f"Invalid mode: {mode}. Must be 'full', 'offset', or 'metagene'."
        )

    if copy:
        return result

    # Store results
    if mode == "full":
        if key_added is None:
            key_added = f"{key}_diff"
        adata.layers[key_added] = result
        info(f"Added differential expression to adata.layers['{key_added}']")
    elif mode == "offset":
        if key_added is None:
            key_added = f"{key}_diff_offset"
        adata.var[key_added] = result
        info(f"Added differential offset to adata.var['{key_added}']")
    elif mode == "metagene":
        if key_added is None:
            key_added = f"{key}_diff_metagene"
        # Store as varm (genes × K effect)
        adata.varm[key_added] = result
        info(f"Added differential metagene effect to adata.varm['{key_added}']")

    return None


def _compute_diff_offset(
    Ro: np.ndarray,
    H_rotation: np.ndarray | None,
    contrast: np.ndarray,
) -> np.ndarray:
    """Compute differential offset effect (diffO).

    diffO = Ro @ H_rotation^T @ contrast

    Returns (n_genes,) vector.
    """
    debug("Computing differential offset effect")

    if H_rotation is not None:
        # Transform contrast through rotation
        contrast_rot = H_rotation.T @ contrast
    else:
        contrast_rot = contrast

    # Ro: (J, L) or (J, L_rot)
    diff_o = Ro @ contrast_rot

    return diff_o


def _compute_diff_full(
    Rk_list: list[np.ndarray],
    D: np.ndarray,
    Bi_list: list[np.ndarray],
    H_rotation: np.ndarray | None,
    contrast: np.ndarray,
    include_offset: bool = True,
    Ro: np.ndarray | None = None,
) -> np.ndarray:
    """Compute full cell-specific differential effect (diffQ).

    diffQ_i = sum_k (Rk @ H_rotation^T @ contrast)_k * D_k * Bi[k, :]

    Returns (n_cells, n_genes) matrix.
    """
    debug("Computing full differential expression effect")

    if H_rotation is not None:
        contrast_rot = H_rotation.T @ contrast
    else:
        contrast_rot = contrast

    # Get dimensions
    K = len(D)
    J = Rk_list[0].shape[0] if Rk_list else 0

    # Compute per-metagene effect: Rk @ contrast_rot for each k
    # Rk_list: list of K matrices, each (J, L)
    # Result: (J, K) matrix where each column is the effect for that factor
    delta_per_k = np.zeros((J, K))
    for k, Rk in enumerate(Rk_list):
        delta_per_k[:, k] = Rk @ contrast_rot

    # Concatenate B matrices
    B = np.hstack(Bi_list)  # (K, N)
    N = B.shape[1]

    # diffQ = delta_per_k @ diag(D) @ B
    diffQ = delta_per_k @ np.diag(D) @ B  # (J, N)

    # Add offset effect if requested
    if include_offset and Ro is not None:
        diff_o = _compute_diff_offset(Ro, H_rotation, contrast)
        diffQ = diffQ + diff_o[:, np.newaxis]

    # Transpose to (N, J) for AnnData convention
    return diffQ.T


def _compute_diff_metagene(
    Rk_list: list[np.ndarray],
    H_rotation: np.ndarray | None,
    contrast: np.ndarray,
) -> np.ndarray:
    """Compute differential effect on metagene loadings.

    Returns (n_genes, K) matrix of effects per metagene.
    """
    debug("Computing differential metagene effect")

    if H_rotation is not None:
        contrast_rot = H_rotation.T @ contrast
    else:
        contrast_rot = contrast

    K = len(Rk_list)
    J = Rk_list[0].shape[0] if Rk_list else 0

    result = np.zeros((J, K))
    for k, Rk in enumerate(Rk_list):
        result[:, k] = Rk @ contrast_rot

    return result


def diff_q(
    adata: AnnData,
    contrast: np.ndarray | list,
    *,
    include_offset: bool = True,
    key: str = "gedi",
    key_added: str | None = None,
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    """Compute cell-specific differential expression (diffQ).

    Alias for ``differential(adata, contrast, mode="full", ...)``.

    See :func:`differential` for full documentation.
    """
    return differential(
        adata,
        contrast,
        mode="full",
        include_offset=include_offset,
        key=key,
        key_added=key_added,
        copy=copy,
    )


def diff_o(
    adata: AnnData,
    contrast: np.ndarray | list,
    *,
    key: str = "gedi",
    key_added: str | None = None,
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    """Compute global offset differential effect (diffO).

    Alias for ``differential(adata, contrast, mode="offset", ...)``.

    See :func:`differential` for full documentation.
    """
    return differential(
        adata,
        contrast,
        mode="offset",
        key=key,
        key_added=key_added,
        copy=copy,
    )
