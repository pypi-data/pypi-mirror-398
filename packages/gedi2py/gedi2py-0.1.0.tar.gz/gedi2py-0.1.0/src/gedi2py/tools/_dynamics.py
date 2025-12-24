"""Trajectory and dynamics functions for GEDI.

Provides vector field and gradient computations for trajectory analysis
based on GEDI model parameters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from anndata import AnnData

from .._logging import debug, info, warning


def vector_field(
    adata: AnnData,
    start_contrast: np.ndarray | list,
    end_contrast: np.ndarray | list,
    *,
    n_steps: int = 10,
    key: str = "gedi",
    key_added: str | None = None,
    copy: bool = False,
) -> AnnData | dict | None:
    r"""Compute vector field for trajectory between two conditions.

    Uses the differential expression framework to compute a vector field
    representing the transcriptional trajectory from one condition to another.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    start_contrast
        Contrast vector defining the starting condition.
    end_contrast
        Contrast vector defining the ending condition.
    n_steps
        Number of interpolation steps between conditions.
    key
        Key in ``adata.uns`` where GEDI results are stored.
    key_added
        Key to store results. Defaults to ``{key}_vector_field``.
    copy
        If ``True``, return the vector field dict instead of storing in ``adata``.

    Returns
    -------
    If ``copy=True``, returns dict with keys:
        - ``vectors``: (n_steps, n_genes) array of expression changes
        - ``positions``: (n_steps, L) array of contrast positions
    Otherwise, stores in ``adata.uns[key_added]`` and returns ``None``.

    Notes
    -----
    The vector field represents the direction and magnitude of transcriptional
    change at each point along the trajectory from start to end condition.

    This requires that a covariate matrix H was provided during model training.

    Examples
    --------
    >>> import gedi2py as gd
    >>> import numpy as np
    >>> # Define trajectory from control to treatment
    >>> start = np.array([0, 1])  # control
    >>> end = np.array([1, 0])    # treatment
    >>> gd.tl.vector_field(adata, start, end, n_steps=20)
    >>> adata.uns["gedi_vector_field"]
    """
    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    gedi_data = adata.uns[key]
    model_params = gedi_data.get("model", {})

    # Check if H was provided
    if model_params.get("Rk") is None:
        raise ValueError(
            "Vector field computation requires covariate matrix H. "
            "Pass H parameter to gd.tl.gedi()."
        )

    start_contrast = np.asarray(start_contrast)
    end_contrast = np.asarray(end_contrast)

    if start_contrast.shape != end_contrast.shape:
        raise ValueError(
            f"start_contrast shape {start_contrast.shape} does not match "
            f"end_contrast shape {end_contrast.shape}."
        )

    debug(f"Computing vector field with {n_steps} steps")

    # Compute differential effect at each step
    from ._differential import differential

    n_genes = adata.n_vars
    vectors = np.zeros((n_steps, n_genes))
    positions = np.zeros((n_steps, len(start_contrast)))

    for i in range(n_steps):
        # Interpolate between start and end
        alpha = i / (n_steps - 1) if n_steps > 1 else 0
        contrast = (1 - alpha) * start_contrast + alpha * end_contrast
        positions[i] = contrast

        # Compute differential effect (gene-level, averaged across cells)
        diff = differential(adata, contrast, mode="offset", key=key, copy=True)
        vectors[i] = diff

    result = {
        "vectors": vectors,
        "positions": positions,
        "start_contrast": start_contrast,
        "end_contrast": end_contrast,
        "n_steps": n_steps,
    }

    if copy:
        return result

    if key_added is None:
        key_added = f"{key}_vector_field"

    adata.uns[key_added] = result
    info(f"Added vector field to adata.uns['{key_added}']")

    return None


def gradient(
    adata: AnnData,
    pathway_idx: int | None = None,
    *,
    key: str = "gedi",
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    r"""Compute gradient of pathway activity across cells.

    Uses the pathway coefficient matrix A and cell loadings B to compute
    the gradient of pathway activity in the latent space.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    pathway_idx
        Index of the pathway to compute gradient for. If ``None``,
        computes gradients for all pathways.
    key
        Key in ``adata.uns`` where GEDI results are stored.
    copy
        If ``True``, return the gradient array instead of storing in ``adata``.

    Returns
    -------
    If ``copy=True``:
        - If ``pathway_idx`` is specified: (n_cells, K) gradient array
        - If ``pathway_idx`` is ``None``: (n_cells, K, n_pathways) gradient array
    Otherwise, stores in ``adata.obsm['{key}_gradient']`` and returns ``None``.

    Notes
    -----
    The gradient represents the direction in latent space that maximally
    increases pathway activity. This can be used for trajectory analysis
    or identifying cells transitioning along a pathway.

    This requires that a pathway prior matrix C was provided during model training.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.gedi(adata, batch_key="sample", C=pathway_matrix)
    >>> gd.tl.gradient(adata, pathway_idx=0)
    >>> adata.obsm["gedi_gradient"]  # direction to increase pathway 0
    """
    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    gedi_data = adata.uns[key]
    model_params = gedi_data.get("model", {})

    A = model_params.get("A")
    if A is None:
        raise ValueError(
            "Gradient computation requires pathway prior matrix C. "
            "Pass C parameter to gd.tl.gedi()."
        )

    D = model_params["D"]
    Bi_list = model_params["Bi"]

    P, K = A.shape
    B = np.hstack(Bi_list)  # (K, N)
    N = B.shape[1]

    debug(f"Computing gradient for {'all pathways' if pathway_idx is None else f'pathway {pathway_idx}'}")

    # Gradient of pathway activity w.r.t. cell position in latent space
    # For pathway p: grad_p = A[p, :] (the direction in K-space)
    # Scaled by D for proper magnitude

    if pathway_idx is not None:
        if pathway_idx >= P:
            raise ValueError(
                f"pathway_idx {pathway_idx} out of range. "
                f"Maximum index is {P - 1}."
            )
        # Single pathway: gradient is A[p, :] * D, broadcast to all cells
        grad_direction = A[pathway_idx, :] * D  # (K,)
        # Result shape: (N, K)
        gradient_result = np.tile(grad_direction, (N, 1))
    else:
        # All pathways: (N, K, P)
        grad_directions = A * D[np.newaxis, :]  # (P, K)
        gradient_result = np.tile(grad_directions.T, (N, 1, 1))  # (N, K, P)

    if copy:
        return gradient_result

    key_added = f"{key}_gradient"
    if pathway_idx is not None:
        key_added = f"{key}_gradient_p{pathway_idx}"

    adata.obsm[key_added] = gradient_result
    info(f"Added gradient to adata.obsm['{key_added}']")

    return None


def pseudotime(
    adata: AnnData,
    start_cells: np.ndarray | list,
    *,
    use_rep: str | None = None,
    key: str = "gedi",
    key_added: str = "gedi_pseudotime",
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    r"""Compute pseudotime ordering based on GEDI embeddings.

    Uses diffusion-based pseudotime computation on the GEDI latent
    representation to order cells along a trajectory.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    start_cells
        Indices or boolean mask of cells to use as trajectory start points.
    use_rep
        Representation to use. Defaults to ``X_{key}_pca`` or ``X_{key}``.
    key
        Key in ``adata.uns`` where GEDI results are stored.
    key_added
        Key to store pseudotime in ``adata.obs``.
    copy
        If ``True``, return pseudotime array instead of storing in ``adata``.

    Returns
    -------
    If ``copy=True``, returns pseudotime array (n_cells,).
    Otherwise, stores in ``adata.obs[key_added]`` and returns ``None``.

    Notes
    -----
    This is a simple geodesic distance-based pseudotime. For more
    sophisticated trajectory inference, consider using specialized
    tools like scanpy's PAGA or scvelo.

    Examples
    --------
    >>> import gedi2py as gd
    >>> # Use cells in cluster 0 as starting point
    >>> start_cells = adata.obs["cluster"] == "0"
    >>> gd.tl.pseudotime(adata, start_cells)
    >>> adata.obs["gedi_pseudotime"]
    """
    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    # Determine representation to use
    if use_rep is None:
        candidates = [f"X_{key}_pca", f"X_{key}"]
        for rep in candidates:
            if rep in adata.obsm:
                use_rep = rep
                break
        if use_rep is None:
            raise ValueError(
                f"No suitable representation found. "
                f"Compute PCA first with gd.tl.pca()."
            )

    X = adata.obsm[use_rep]
    debug(f"Computing pseudotime using {use_rep}")

    # Convert start_cells to boolean mask
    start_cells = np.asarray(start_cells)
    if start_cells.dtype != bool:
        mask = np.zeros(adata.n_obs, dtype=bool)
        mask[start_cells] = True
        start_cells = mask

    # Compute centroid of starting cells
    start_centroid = X[start_cells].mean(axis=0)

    # Pseudotime = distance from start centroid
    distances = np.linalg.norm(X - start_centroid, axis=1)

    # Normalize to [0, 1]
    pseudotime = (distances - distances.min()) / (distances.max() - distances.min() + 1e-10)

    if copy:
        return pseudotime

    adata.obs[key_added] = pseudotime
    info(f"Added pseudotime to adata.obs['{key_added}']")

    return None
