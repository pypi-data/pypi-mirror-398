"""Convergence visualization functions for GEDI.

Provides plots to visualize model training convergence.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    from anndata import AnnData
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


def convergence(
    adata: AnnData,
    *,
    which: Literal["sigma2", "dZ", "dA", "do", "all"] = "all",
    key: str = "gedi",
    log_scale: bool = True,
    title: str | None = None,
    figsize: tuple[float, float] | None = None,
    show: bool | None = None,
    save: str | None = None,
    ax: Axes | None = None,
    return_fig: bool = False,
) -> Figure | Axes | None:
    r"""Plot GEDI training convergence.

    Visualizes how model parameters evolved during training to assess
    convergence. Available metrics:

    - ``sigma2``: Noise variance (should stabilize)
    - ``dZ``: Change in metagenes Z per iteration
    - ``dA``: Change in pathway coefficients A (if using pathway priors)
    - ``do``: Change in offsets o

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    which
        Which convergence metric(s) to plot:
        - ``"sigma2"``: Only noise variance
        - ``"dZ"``: Only metagene changes
        - ``"dA"``: Only pathway coefficient changes
        - ``"do"``: Only offset changes
        - ``"all"``: All available metrics (default)
    key
        Key in ``adata.uns`` where GEDI results are stored.
    log_scale
        If ``True``, use log scale for y-axis (except sigma2).
    title
        Plot title.
    figsize
        Figure size (width, height) in inches.
    show
        If ``True``, show the figure.
    save
        Path to save the figure.
    ax
        Pre-existing axes for the plot. Only valid for single metric.
    return_fig
        If ``True``, return the figure object.

    Returns
    -------
    Depending on ``return_fig``: Figure, Axes, or ``None``.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.gedi(adata, batch_key="sample", n_latent=10)
    >>> gd.pl.convergence(adata)
    >>> gd.pl.convergence(adata, which="sigma2", log_scale=False)
    """
    import matplotlib.pyplot as plt

    # Get tracking data
    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    gedi_data = adata.uns[key]
    tracking = gedi_data.get("tracking", {})

    if not tracking:
        raise ValueError(
            f"No tracking data found. Ensure gd.tl.gedi() was run with "
            f"tracking enabled."
        )

    # Determine what to plot
    if which == "all":
        metrics = [k for k in ["sigma2", "dZ", "dA", "do"] if k in tracking]
    else:
        if which not in tracking:
            available = list(tracking.keys())
            raise ValueError(
                f"Metric '{which}' not found in tracking data. "
                f"Available: {available}"
            )
        metrics = [which]

    n_metrics = len(metrics)

    # Create figure
    if ax is not None and n_metrics > 1:
        raise ValueError("ax can only be used with a single metric")

    if figsize is None:
        figsize = (5 * n_metrics, 4)

    if ax is None:
        fig, axes = plt.subplots(1, n_metrics, figsize=figsize, squeeze=False)
        axes = axes.flatten()
    else:
        fig = ax.figure
        axes = [ax]

    # Plot each metric
    for i, metric in enumerate(metrics):
        ax_i = axes[i]
        values = np.asarray(tracking[metric])
        iterations = np.arange(len(values))

        ax_i.plot(iterations, values, marker="o", markersize=3, linewidth=1.5)

        ax_i.set_xlabel("Iteration")
        ax_i.set_ylabel(_get_metric_label(metric))

        # Log scale for change metrics
        if log_scale and metric != "sigma2":
            ax_i.set_yscale("log")

        ax_i.set_title(metric if title is None else title)
        ax_i.grid(True, alpha=0.3)

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
    elif ax is not None:
        return ax
    else:
        return None


def _get_metric_label(metric: str) -> str:
    """Get y-axis label for convergence metric."""
    labels = {
        "sigma2": r"$\sigma^2$ (noise variance)",
        "dZ": r"$\Delta Z$ (metagene change)",
        "dA": r"$\Delta A$ (pathway coef. change)",
        "do": r"$\Delta o$ (offset change)",
    }
    return labels.get(metric, metric)


def loss(
    adata: AnnData,
    *,
    key: str = "gedi",
    title: str = "Training Loss",
    figsize: tuple[float, float] = (6, 4),
    show: bool | None = None,
    save: str | None = None,
    ax: Axes | None = None,
    return_fig: bool = False,
) -> Figure | Axes | None:
    """Plot GEDI training loss (negative log-likelihood).

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    key
        Key in ``adata.uns`` where GEDI results are stored.
    title
        Plot title.
    figsize
        Figure size.
    show
        If ``True``, show the figure.
    save
        Path to save the figure.
    ax
        Pre-existing axes.
    return_fig
        If ``True``, return the figure.

    Returns
    -------
    Depending on ``return_fig``: Figure, Axes, or ``None``.
    """
    import matplotlib.pyplot as plt

    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    tracking = adata.uns[key].get("tracking", {})
    sigma2_history = tracking.get("sigma2")

    if sigma2_history is None:
        raise ValueError("No sigma2 tracking data found.")

    # Loss is proportional to log(sigma2)
    sigma2 = np.asarray(sigma2_history)
    loss_values = np.log(sigma2)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    iterations = np.arange(len(loss_values))
    ax.plot(iterations, loss_values, marker="o", markersize=3, linewidth=1.5)

    ax.set_xlabel("Iteration")
    ax.set_ylabel(r"Loss ($\log \sigma^2$)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    # Handle save/show
    if show is None:
        show = save is None

    if save is not None:
        plt.savefig(save, dpi=150, bbox_inches="tight")

    if show:
        plt.show()

    if return_fig:
        return fig
    elif ax is not None:
        return ax
    else:
        return None
