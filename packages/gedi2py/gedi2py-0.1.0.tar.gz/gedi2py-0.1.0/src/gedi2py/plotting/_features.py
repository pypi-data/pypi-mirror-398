"""Feature visualization functions for GEDI.

Provides plots for gene expression and feature analysis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import numpy as np

if TYPE_CHECKING:
    from anndata import AnnData
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


def features(
    adata: AnnData,
    features: str | Sequence[str],
    *,
    basis: str = "X_gedi_umap",
    layer: str | None = None,
    cmap: str = "viridis",
    vmin: float | None = None,
    vmax: float | None = None,
    size: float | None = None,
    alpha: float = 1.0,
    ncols: int = 4,
    figsize: tuple[float, float] | None = None,
    show: bool | None = None,
    save: str | None = None,
    return_fig: bool = False,
) -> Figure | None:
    r"""Plot gene expression on GEDI embedding.

    Parameters
    ----------
    adata
        Annotated data matrix.
    features
        Gene name(s) to plot.
    basis
        Key in ``adata.obsm`` for embedding coordinates.
    layer
        Layer to use for expression values. If ``None``, uses ``adata.X``.
    cmap
        Colormap for expression values.
    vmin
        Minimum value for color scale.
    vmax
        Maximum value for color scale.
    size
        Point size. If ``None``, automatically determined.
    alpha
        Point transparency.
    ncols
        Number of columns for multi-panel plots.
    figsize
        Figure size.
    show
        If ``True``, show the figure.
    save
        Path to save the figure.
    return_fig
        If ``True``, return the figure.

    Returns
    -------
    Figure if ``return_fig=True``, else ``None``.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.pl.features(adata, ["CD4", "CD8A", "FOXP3"])
    """
    import matplotlib.pyplot as plt

    # Handle single feature
    if isinstance(features, str):
        features = [features]

    n_features = len(features)

    # Validate features exist
    missing = [f for f in features if f not in adata.var_names]
    if missing:
        raise ValueError(f"Features not found in adata.var_names: {missing}")

    # Get embedding
    if basis not in adata.obsm:
        raise ValueError(f"Basis '{basis}' not found in adata.obsm.")

    coords = adata.obsm[basis]

    # Auto-size
    if size is None:
        size = 120000 / adata.n_obs
        size = max(0.5, min(size, 50))

    if figsize is None:
        nrows = int(np.ceil(n_features / ncols))
        ncols_actual = min(n_features, ncols)
        figsize = (4 * ncols_actual, 4 * nrows)

    # Create figure
    nrows = int(np.ceil(n_features / ncols))
    ncols_actual = min(n_features, ncols)
    fig, axes = plt.subplots(nrows, ncols_actual, figsize=figsize, squeeze=False)
    axes = axes.flatten()

    # Plot each feature
    for i, gene in enumerate(features):
        ax = axes[i]

        # Get expression values
        if layer is not None:
            expr = adata[:, gene].layers[layer]
        else:
            expr = adata[:, gene].X

        if hasattr(expr, "toarray"):
            expr = expr.toarray()
        expr = expr.flatten()

        # Plot
        sc = ax.scatter(
            coords[:, 0],
            coords[:, 1],
            c=expr,
            s=size,
            alpha=alpha,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
        )

        plt.colorbar(sc, ax=ax, shrink=0.5, pad=0.01)
        ax.set_title(gene)
        ax.axis("off")

    # Hide unused axes
    for j in range(n_features, len(axes)):
        axes[j].axis("off")

    plt.tight_layout()

    # Handle save/show
    if show is None:
        show = save is None

    if save is not None:
        plt.savefig(save, dpi=150, bbox_inches="tight")

    if show:
        plt.show()

    if return_fig:
        return fig
    return None


def dispersion(
    adata: AnnData,
    *,
    key: str = "gedi",
    n_top: int = 20,
    log_scale: bool = True,
    figsize: tuple[float, float] = (10, 6),
    show: bool | None = None,
    save: str | None = None,
    return_fig: bool = False,
) -> Figure | None:
    r"""Plot gene dispersion from GEDI model.

    Visualizes the dispersion (variance/mean ratio) of genes, which
    can help identify highly variable genes.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI dispersion computed.
    key
        Key prefix for GEDI results.
    n_top
        Number of top dispersed genes to label.
    log_scale
        If ``True``, use log scale for axes.
    figsize
        Figure size.
    show
        If ``True``, show the figure.
    save
        Path to save the figure.
    return_fig
        If ``True``, return the figure.

    Returns
    -------
    Figure if ``return_fig=True``, else ``None``.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.dispersion(adata)
    >>> gd.pl.dispersion(adata, n_top=30)
    """
    import matplotlib.pyplot as plt

    disp_key = f"{key}_dispersion"
    var_key = f"{key}_variance"

    if disp_key not in adata.var.columns:
        raise ValueError(
            f"Dispersion not found at adata.var['{disp_key}']. "
            f"Run gd.tl.dispersion() first."
        )

    dispersion = adata.var[disp_key].values
    variance = adata.var.get(var_key, np.ones_like(dispersion))

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Left: Dispersion histogram
    ax1 = axes[0]
    valid = (dispersion > 0) & np.isfinite(dispersion)
    if log_scale:
        ax1.hist(np.log10(dispersion[valid] + 1e-10), bins=50, edgecolor="white")
        ax1.set_xlabel("log10(Dispersion)")
    else:
        ax1.hist(dispersion[valid], bins=50, edgecolor="white")
        ax1.set_xlabel("Dispersion")
    ax1.set_ylabel("Number of genes")
    ax1.set_title("Dispersion Distribution")

    # Right: Mean vs Dispersion
    ax2 = axes[1]
    mean_expr = adata.X.mean(axis=0)
    if hasattr(mean_expr, "A1"):
        mean_expr = mean_expr.A1

    if log_scale:
        ax2.scatter(
            np.log10(mean_expr + 1e-10),
            np.log10(dispersion + 1e-10),
            s=1,
            alpha=0.5,
        )
        ax2.set_xlabel("log10(Mean expression)")
        ax2.set_ylabel("log10(Dispersion)")
    else:
        ax2.scatter(mean_expr, dispersion, s=1, alpha=0.5)
        ax2.set_xlabel("Mean expression")
        ax2.set_ylabel("Dispersion")

    # Label top genes
    top_idx = np.argsort(dispersion)[::-1][:n_top]
    for idx in top_idx:
        x = np.log10(mean_expr[idx] + 1e-10) if log_scale else mean_expr[idx]
        y = np.log10(dispersion[idx] + 1e-10) if log_scale else dispersion[idx]
        ax2.annotate(
            adata.var_names[idx],
            (x, y),
            fontsize=7,
            alpha=0.8,
        )

    ax2.set_title("Mean vs Dispersion")

    plt.tight_layout()

    # Handle save/show
    if show is None:
        show = save is None

    if save is not None:
        plt.savefig(save, dpi=150, bbox_inches="tight")

    if show:
        plt.show()

    if return_fig:
        return fig
    return None


def metagenes(
    adata: AnnData,
    *,
    n_genes: int = 10,
    key: str = "gedi",
    figsize: tuple[float, float] | None = None,
    show: bool | None = None,
    save: str | None = None,
    return_fig: bool = False,
) -> Figure | None:
    r"""Plot top genes per GEDI metagene (latent factor).

    Shows a heatmap of the top genes with highest loadings for each
    latent factor in the Z matrix.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    n_genes
        Number of top genes to show per metagene.
    key
        Key prefix for GEDI results.
    figsize
        Figure size.
    show
        If ``True``, show the figure.
    save
        Path to save the figure.
    return_fig
        If ``True``, return the figure.

    Returns
    -------
    Figure if ``return_fig=True``, else ``None``.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.gedi(adata, batch_key="sample", n_latent=10)
    >>> gd.pl.metagenes(adata, n_genes=15)
    """
    import matplotlib.pyplot as plt

    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    Z = adata.uns[key]["model"]["Z"]
    K = Z.shape[1]

    if figsize is None:
        figsize = (3 * K, 0.3 * n_genes + 2)

    fig, axes = plt.subplots(1, K, figsize=figsize, sharey=True)
    if K == 1:
        axes = [axes]

    for k in range(K):
        ax = axes[k]
        loadings = Z[:, k]

        # Get top genes (by absolute loading)
        top_idx = np.argsort(np.abs(loadings))[::-1][:n_genes]
        top_genes = adata.var_names[top_idx]
        top_loadings = loadings[top_idx]

        # Sort by actual loading for display
        sort_order = np.argsort(top_loadings)
        top_genes = top_genes[sort_order]
        top_loadings = top_loadings[sort_order]

        # Horizontal bar plot
        colors = ["steelblue" if l >= 0 else "coral" for l in top_loadings]
        ax.barh(range(n_genes), top_loadings, color=colors)
        ax.set_yticks(range(n_genes))
        ax.set_yticklabels(top_genes, fontsize=8)
        ax.axvline(0, color="black", linewidth=0.5)
        ax.set_xlabel("Loading")
        ax.set_title(f"LV{k + 1}")

    plt.tight_layout()

    # Handle save/show
    if show is None:
        show = save is None

    if save is not None:
        plt.savefig(save, dpi=150, bbox_inches="tight")

    if show:
        plt.show()

    if return_fig:
        return fig
    return None


def variance_explained(
    adata: AnnData,
    *,
    key: str = "gedi",
    n_components: int | None = None,
    figsize: tuple[float, float] = (8, 4),
    show: bool | None = None,
    save: str | None = None,
    return_fig: bool = False,
) -> Figure | None:
    r"""Plot variance explained by GEDI components.

    Shows the proportion of variance explained by each latent factor
    based on the SVD singular values.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI SVD computed.
    key
        Key prefix for GEDI results.
    n_components
        Number of components to show. If ``None``, shows all.
    figsize
        Figure size.
    show
        If ``True``, show the figure.
    save
        Path to save the figure.
    return_fig
        If ``True``, return the figure.

    Returns
    -------
    Figure if ``return_fig=True``, else ``None``.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.svd(adata)
    >>> gd.pl.variance_explained(adata)
    """
    import matplotlib.pyplot as plt

    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    svd_data = adata.uns[key].get("svd")
    if svd_data is None:
        raise ValueError("No SVD data found. Run gd.tl.svd() first.")

    d = svd_data["d"]
    variance = d**2
    var_explained = variance / variance.sum()
    cum_var = np.cumsum(var_explained)

    if n_components is None:
        n_components = len(d)
    n_components = min(n_components, len(d))

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Left: Individual variance
    ax1 = axes[0]
    ax1.bar(range(1, n_components + 1), var_explained[:n_components] * 100)
    ax1.set_xlabel("Component")
    ax1.set_ylabel("Variance Explained (%)")
    ax1.set_title("Individual Variance")

    # Right: Cumulative variance
    ax2 = axes[1]
    ax2.plot(
        range(1, n_components + 1),
        cum_var[:n_components] * 100,
        marker="o",
        markersize=4,
    )
    ax2.set_xlabel("Number of Components")
    ax2.set_ylabel("Cumulative Variance (%)")
    ax2.set_title("Cumulative Variance")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # Handle save/show
    if show is None:
        show = save is None

    if save is not None:
        plt.savefig(save, dpi=150, bbox_inches="tight")

    if show:
        plt.show()

    if return_fig:
        return fig
    return None
