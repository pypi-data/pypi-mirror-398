"""Embedding visualization functions for GEDI.

Provides UMAP, PCA, and other embedding plots.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import numpy as np

if TYPE_CHECKING:
    from anndata import AnnData
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

from .._logging import debug


def embedding(
    adata: AnnData,
    *,
    basis: str = "X_gedi_umap",
    color: str | Sequence[str] | None = None,
    layer: str | None = None,
    size: float | None = None,
    alpha: float = 1.0,
    title: str | Sequence[str] | None = None,
    legend_loc: str = "right margin",
    legend_fontsize: int | float = 10,
    cmap: str = "viridis",
    palette: str | Sequence[str] | None = None,
    frameon: bool = False,
    ncols: int = 4,
    wspace: float = 0.4,
    show: bool | None = None,
    save: str | None = None,
    ax: Axes | None = None,
    return_fig: bool = False,
    **kwargs,
) -> Figure | Axes | list[Axes] | None:
    r"""Plot GEDI embedding colored by various attributes.

    Parameters
    ----------
    adata
        Annotated data matrix.
    basis
        Key in ``adata.obsm`` for the embedding coordinates.
        Defaults to ``X_gedi_umap``.
    color
        Key(s) for annotation in ``adata.obs`` or gene names to color by.
        Can be a single key or a list of keys.
    layer
        Layer to use for gene expression values.
    size
        Point size. If ``None``, automatically determined.
    alpha
        Point transparency (0-1).
    title
        Panel title(s). If ``None``, uses the ``color`` key(s).
    legend_loc
        Location of the legend. Options: ``'right margin'``, ``'on data'``,
        ``'best'``, ``'upper right'``, etc.
    legend_fontsize
        Font size for legend text.
    cmap
        Colormap for continuous variables.
    palette
        Color palette for categorical variables.
    frameon
        Whether to show axis frame.
    ncols
        Number of columns for multi-panel plots.
    wspace
        Width space between panels.
    show
        If ``True``, show the figure. If ``None``, defaults to ``True``
        unless ``save`` is specified.
    save
        Path to save the figure.
    ax
        Pre-existing axes for the plot. Only valid when ``color`` is a
        single key.
    return_fig
        If ``True``, return the figure object.
    **kwargs
        Additional arguments passed to ``matplotlib.pyplot.scatter``.

    Returns
    -------
    Depending on ``return_fig`` and ``ax``:
        - If ``return_fig=True``: Returns the Figure object
        - If ``ax`` is provided: Returns the Axes object
        - Otherwise: Returns ``None``

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.gedi(adata, batch_key="sample", n_latent=10)
    >>> gd.tl.umap(adata)
    >>> gd.pl.embedding(adata, color="cell_type")
    >>> gd.pl.embedding(adata, color=["batch", "cell_type", "total_counts"])
    """
    import matplotlib.pyplot as plt

    # Validate basis
    if basis not in adata.obsm:
        available = list(adata.obsm.keys())
        raise ValueError(
            f"Basis '{basis}' not found in adata.obsm. "
            f"Available: {available}. "
            f"Run gd.tl.umap() or gd.tl.pca() first."
        )

    coords = adata.obsm[basis]

    # Handle color as list
    if color is None:
        color_list = [None]
    elif isinstance(color, str):
        color_list = [color]
    else:
        color_list = list(color)

    n_panels = len(color_list)

    # Create figure if needed
    if ax is not None and n_panels > 1:
        raise ValueError("ax can only be used with a single color key")

    if ax is None:
        nrows = int(np.ceil(n_panels / ncols))
        ncols_actual = min(n_panels, ncols)
        fig, axes = plt.subplots(
            nrows,
            ncols_actual,
            figsize=(4 * ncols_actual, 4 * nrows),
            squeeze=False,
        )
        axes = axes.flatten()
    else:
        fig = ax.figure
        axes = [ax]

    # Auto-determine point size
    if size is None:
        n_cells = adata.n_obs
        size = 120000 / n_cells
        size = max(0.5, min(size, 50))

    # Plot each panel
    for i, c in enumerate(color_list):
        ax_i = axes[i] if i < len(axes) else axes[-1]

        if c is None:
            # No coloring
            ax_i.scatter(
                coords[:, 0],
                coords[:, 1],
                s=size,
                alpha=alpha,
                c="grey",
                **kwargs,
            )
            panel_title = basis
        elif c in adata.obs.columns:
            # Color by observation annotation
            values = adata.obs[c]
            if values.dtype.name == "category" or values.dtype == object:
                # Categorical
                _plot_categorical(
                    ax_i, coords, values, size, alpha, palette, legend_loc, legend_fontsize, **kwargs
                )
            else:
                # Continuous
                sc = ax_i.scatter(
                    coords[:, 0],
                    coords[:, 1],
                    s=size,
                    alpha=alpha,
                    c=values,
                    cmap=cmap,
                    **kwargs,
                )
                plt.colorbar(sc, ax=ax_i, shrink=0.5, pad=0.01)
            panel_title = c
        elif c in adata.var_names:
            # Color by gene expression
            if layer is not None:
                expr = adata[:, c].layers[layer].flatten()
            else:
                expr = adata[:, c].X
                if hasattr(expr, "toarray"):
                    expr = expr.toarray()
                expr = expr.flatten()
            sc = ax_i.scatter(
                coords[:, 0],
                coords[:, 1],
                s=size,
                alpha=alpha,
                c=expr,
                cmap=cmap,
                **kwargs,
            )
            plt.colorbar(sc, ax=ax_i, shrink=0.5, pad=0.01)
            panel_title = c
        else:
            raise ValueError(
                f"'{c}' not found in adata.obs or adata.var_names."
            )

        # Set title
        if title is not None:
            if isinstance(title, str):
                panel_title = title
            elif i < len(title):
                panel_title = title[i]
        ax_i.set_title(panel_title)

        # Formatting
        ax_i.set_xlabel(f"{basis.replace('X_', '')} 1")
        ax_i.set_ylabel(f"{basis.replace('X_', '')} 2")
        if not frameon:
            ax_i.axis("off")

    # Hide unused axes
    for j in range(n_panels, len(axes)):
        axes[j].axis("off")

    plt.tight_layout()

    # Handle save/show
    if show is None:
        show = save is None

    if save is not None:
        plt.savefig(save, dpi=150, bbox_inches="tight")
        debug(f"Saved figure to {save}")

    if show:
        plt.show()

    if return_fig:
        return fig
    elif ax is not None:
        return ax
    else:
        return None


def _plot_categorical(
    ax,
    coords: np.ndarray,
    values,
    size: float,
    alpha: float,
    palette,
    legend_loc: str,
    legend_fontsize: float,
    **kwargs,
):
    """Helper to plot categorical coloring with legend."""
    import matplotlib.pyplot as plt

    categories = values.unique()
    n_cats = len(categories)

    # Get colors
    if palette is None:
        if n_cats <= 10:
            colors = plt.cm.tab10(np.linspace(0, 1, 10))[:n_cats]
        elif n_cats <= 20:
            colors = plt.cm.tab20(np.linspace(0, 1, 20))[:n_cats]
        else:
            colors = plt.cm.viridis(np.linspace(0, 1, n_cats))
    else:
        if isinstance(palette, str):
            cmap = plt.get_cmap(palette)
            colors = cmap(np.linspace(0, 1, n_cats))
        else:
            colors = palette

    # Plot each category
    for i, cat in enumerate(categories):
        mask = values == cat
        ax.scatter(
            coords[mask, 0],
            coords[mask, 1],
            s=size,
            alpha=alpha,
            c=[colors[i]],
            label=str(cat),
            **kwargs,
        )

    # Add legend
    if legend_loc == "right margin":
        ax.legend(
            bbox_to_anchor=(1.02, 0.5),
            loc="center left",
            fontsize=legend_fontsize,
            frameon=False,
        )
    elif legend_loc != "none":
        ax.legend(loc=legend_loc, fontsize=legend_fontsize, frameon=False)


def umap(
    adata: AnnData,
    *,
    color: str | Sequence[str] | None = None,
    key: str = "gedi",
    **kwargs,
) -> Figure | Axes | list[Axes] | None:
    """Plot GEDI UMAP embedding.

    Convenience wrapper for :func:`embedding` with ``basis='X_{key}_umap'``.

    See :func:`embedding` for full parameter documentation.
    """
    return embedding(adata, basis=f"X_{key}_umap", color=color, **kwargs)


def pca(
    adata: AnnData,
    *,
    color: str | Sequence[str] | None = None,
    components: tuple[int, int] = (1, 2),
    key: str = "gedi",
    **kwargs,
) -> Figure | Axes | list[Axes] | None:
    """Plot GEDI PCA embedding.

    Parameters
    ----------
    adata
        Annotated data matrix.
    color
        Key(s) for annotation to color by.
    components
        Which principal components to plot (1-indexed).
    key
        Key prefix for GEDI results.
    **kwargs
        Additional arguments passed to :func:`embedding`.

    See :func:`embedding` for full parameter documentation.
    """
    import matplotlib.pyplot as plt

    basis = f"X_{key}_pca"
    if basis not in adata.obsm:
        raise ValueError(
            f"PCA not found at adata.obsm['{basis}']. "
            f"Run gd.tl.pca() first."
        )

    pca_coords = adata.obsm[basis]

    # Extract requested components (convert to 0-indexed)
    pc1, pc2 = components[0] - 1, components[1] - 1
    if pc1 >= pca_coords.shape[1] or pc2 >= pca_coords.shape[1]:
        raise ValueError(
            f"Requested components {components} exceed available "
            f"({pca_coords.shape[1]} components)."
        )

    # Create temporary obsm entry with just these components
    temp_key = f"_temp_pca_{pc1}_{pc2}"
    adata.obsm[temp_key] = pca_coords[:, [pc1, pc2]]

    try:
        result = embedding(adata, basis=temp_key, color=color, **kwargs)
    finally:
        del adata.obsm[temp_key]

    return result
