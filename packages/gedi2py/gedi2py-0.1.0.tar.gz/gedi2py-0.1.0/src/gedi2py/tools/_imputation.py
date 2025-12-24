"""Imputation functions for GEDI.

Provides imputed expression values, variance, and dispersion estimates
based on the GEDI model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from anndata import AnnData

from .._logging import debug, info


def impute(
    adata: AnnData,
    *,
    samples: list[int] | None = None,
    key: str = "gedi",
    layer_added: str | None = None,
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    r"""Compute imputed expression values from GEDI model.

    Imputed values are computed as the expected expression under the
    GEDI model: ``Y_imputed = Z @ Q_i @ D @ B_i + o + o_i + s_i`` for
    each sample.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    samples
        List of sample indices to impute. If ``None``, imputes all samples.
    key
        Key in ``adata.uns`` where GEDI results are stored.
    layer_added
        Layer name to store imputed values. If ``None``, defaults to
        ``{key}_imputed``.
    copy
        If ``True``, return the imputed matrix instead of storing in ``adata``.

    Returns
    -------
    If ``copy=True``, returns imputed expression matrix (n_cells, n_genes).
    Otherwise, stores in ``adata.layers[layer_added]`` and returns ``None``.

    Notes
    -----
    The imputed expression is computed sample-by-sample to preserve the
    sample-specific components (Q_i, o_i, s_i).

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.gedi(adata, batch_key="sample", n_latent=10)
    >>> gd.tl.impute(adata)
    >>> adata.layers["gedi_imputed"]
    """
    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    gedi_data = adata.uns[key]
    model_params = gedi_data.get("model", {})
    params = gedi_data.get("params", {})

    # Get required parameters
    Z = model_params.get("Z")
    D = model_params.get("D")
    Bi_list = model_params.get("Bi")
    o = model_params.get("o")
    Qi_list = model_params.get("Qi")
    oi_list = model_params.get("oi")
    si_list = model_params.get("si")

    if Z is None or D is None or Bi_list is None:
        raise ValueError(
            f"Missing model parameters for imputation. "
            f"Ensure gd.tl.gedi() completed successfully."
        )

    n_samples = len(Bi_list)
    if samples is None:
        samples = list(range(n_samples))

    debug(f"Computing imputed expression for {len(samples)} samples")

    # Get sample sizes
    sample_sizes = [Bi.shape[1] for Bi in Bi_list]
    n_cells_total = sum(sample_sizes[i] for i in samples)
    n_genes = Z.shape[0]

    # Allocate output
    Y_imputed = np.zeros((n_cells_total, n_genes))

    # Impute sample by sample
    cell_offset = 0
    for i in samples:
        n_cells_i = sample_sizes[i]
        Bi = Bi_list[i]

        # Get sample-specific parameters (may be None)
        Qi = Qi_list[i] if Qi_list is not None else np.eye(Z.shape[1])
        oi = oi_list[i] if oi_list is not None else np.zeros(n_genes)
        si = si_list[i] if si_list is not None else np.zeros(n_cells_i)

        # Y_i = Z @ Qi @ diag(D) @ Bi + o + oi (broadcast) + si (broadcast)
        # Shape: (J, K) @ (K, K) @ (K,) @ (K, n_i) = (J, n_i)
        Y_i = Z @ Qi @ np.diag(D) @ Bi

        # Add offsets
        if o is not None:
            Y_i = Y_i + o[:, np.newaxis]
        Y_i = Y_i + oi[:, np.newaxis]
        Y_i = Y_i + si[np.newaxis, :]

        # Store (transpose to cells × genes)
        Y_imputed[cell_offset : cell_offset + n_cells_i, :] = Y_i.T
        cell_offset += n_cells_i

    if copy:
        return Y_imputed

    # Store in adata.layers
    if layer_added is None:
        layer_added = f"{key}_imputed"

    adata.layers[layer_added] = Y_imputed
    info(f"Added imputed expression to adata.layers['{layer_added}']")

    return None


def variance(
    adata: AnnData,
    *,
    key: str = "gedi",
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    r"""Compute gene variance explained by GEDI model.

    Variance is computed across the imputed expression values,
    representing the systematic variation captured by the model.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    key
        Key in ``adata.uns`` where GEDI results are stored.
    copy
        If ``True``, return variance vector instead of storing in ``adata``.

    Returns
    -------
    If ``copy=True``, returns variance vector (n_genes,).
    Otherwise, stores in ``adata.var['{key}_variance']`` and returns ``None``.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.gedi(adata, batch_key="sample", n_latent=10)
    >>> gd.tl.variance(adata)
    >>> adata.var["gedi_variance"]
    """
    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    # Check if imputed layer exists, compute if not
    layer_key = f"{key}_imputed"
    if layer_key not in adata.layers:
        impute(adata, key=key)

    Y_imputed = adata.layers[layer_key]

    debug("Computing gene variance from imputed expression")
    gene_variance = np.var(Y_imputed, axis=0)

    if copy:
        return gene_variance

    adata.var[f"{key}_variance"] = gene_variance
    info(f"Added variance to adata.var['{key}_variance']")

    return None


def dispersion(
    adata: AnnData,
    *,
    key: str = "gedi",
    copy: bool = False,
) -> AnnData | np.ndarray | None:
    r"""Compute gene dispersion from GEDI model.

    Dispersion is computed as variance / mean (coefficient of variation squared)
    from the imputed expression values.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    key
        Key in ``adata.uns`` where GEDI results are stored.
    copy
        If ``True``, return dispersion vector instead of storing in ``adata``.

    Returns
    -------
    If ``copy=True``, returns dispersion vector (n_genes,).
    Otherwise, stores in ``adata.var['{key}_dispersion']`` and returns ``None``.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.gedi(adata, batch_key="sample", n_latent=10)
    >>> gd.tl.dispersion(adata)
    >>> adata.var["gedi_dispersion"]
    """
    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    # Check if imputed layer exists, compute if not
    layer_key = f"{key}_imputed"
    if layer_key not in adata.layers:
        impute(adata, key=key)

    Y_imputed = adata.layers[layer_key]

    debug("Computing gene dispersion from imputed expression")
    gene_mean = np.mean(Y_imputed, axis=0)
    gene_var = np.var(Y_imputed, axis=0)

    # Dispersion = var / mean, with protection against division by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        gene_dispersion = np.where(gene_mean > 0, gene_var / gene_mean, 0.0)

    if copy:
        return gene_dispersion

    adata.var[f"{key}_dispersion"] = gene_dispersion
    info(f"Added dispersion to adata.var['{key}_dispersion']")

    return None
