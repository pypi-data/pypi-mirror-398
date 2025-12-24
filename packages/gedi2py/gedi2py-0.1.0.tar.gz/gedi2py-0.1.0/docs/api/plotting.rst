Plotting (gd.pl)
================

.. module:: gedi2py.plotting
   :synopsis: Visualization functions for GEDI

The plotting module provides functions for visualizing GEDI results,
including embeddings, convergence metrics, and feature plots.

.. currentmodule:: gedi2py.plotting

Embedding Plots
---------------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   embedding
   umap
   pca

.. autofunction:: embedding

   **Example**

   .. code-block:: python

      import gedi2py as gd
      import matplotlib.pyplot as plt

      # Basic embedding plot
      gd.pl.embedding(adata, color="cell_type")

      # Multiple colors
      gd.pl.embedding(adata, color=["sample", "cell_type"], ncols=2)

      # Customize appearance
      gd.pl.embedding(
          adata,
          basis="X_gedi_umap",
          color="cell_type",
          size=10,
          alpha=0.8,
          palette="tab20",
          legend_loc="right margin",
          frameon=False,
      )
      plt.show()

.. autofunction:: umap

   Convenience wrapper for ``embedding(basis="X_gedi_umap", ...)``.

   .. code-block:: python

      gd.pl.umap(adata, color="sample")

.. autofunction:: pca

   Convenience wrapper for ``embedding(basis="X_gedi_pca", ...)``.

   .. code-block:: python

      gd.pl.pca(adata, color="sample")

Convergence Plots
-----------------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   convergence
   loss

.. autofunction:: convergence

   **Example**

   .. code-block:: python

      # Plot all convergence metrics
      gd.pl.convergence(adata, which="all")

      # Plot specific metric
      gd.pl.convergence(adata, which="sigma2", log_scale=True)

      # Save figure
      gd.pl.convergence(adata, save="convergence.png")

   **Available Metrics**

   - ``sigma2``: Noise variance
   - ``dZ``: Change in Z matrix
   - ``dA``: Change in A matrix
   - ``do``: Change in offsets
   - ``all``: All metrics in subplots

.. autofunction:: loss

   Plot the loss/objective function over iterations.

   .. code-block:: python

      gd.pl.loss(adata, log_scale=False)

Feature Plots
-------------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   features
   metagenes
   dispersion
   variance_explained

.. autofunction:: features

   **Example**

   .. code-block:: python

      # Plot marker genes
      gd.pl.features(
          adata,
          features=["CD3D", "CD14", "MS4A1", "NKG7"],
          ncols=2,
      )

      # Use different colormap
      gd.pl.features(
          adata,
          features="CD3D",
          cmap="RdBu_r",
          vmin=-2,
          vmax=2,
      )

.. autofunction:: metagenes

   Visualize metagene patterns across cells.

   .. code-block:: python

      # Plot first 4 metagenes
      gd.pl.metagenes(adata, metagenes=[0, 1, 2, 3], ncols=2)

.. autofunction:: dispersion

   Plot gene dispersion vs mean expression.

   .. code-block:: python

      gd.pl.dispersion(adata, highlight_hvg=True)

.. autofunction:: variance_explained

   Plot variance explained by each latent factor.

   .. code-block:: python

      # Bar plot of variance explained
      gd.pl.variance_explained(adata)

      # Cumulative variance
      gd.pl.variance_explained(adata, cumulative=True)

Common Parameters
-----------------

Most plotting functions share these parameters:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Parameter
     - Type
     - Description
   * - show
     - bool | None
     - Show the plot (default: True in interactive mode)
   * - save
     - str | None
     - Path to save the figure
   * - ax
     - Axes | None
     - Matplotlib axes to plot on
   * - return_fig
     - bool
     - Return the Figure object instead of showing

**Using with Matplotlib**

.. code-block:: python

   import matplotlib.pyplot as plt

   # Create custom figure
   fig, axes = plt.subplots(1, 3, figsize=(15, 4))

   gd.pl.umap(adata, color="sample", ax=axes[0], show=False)
   gd.pl.umap(adata, color="cell_type", ax=axes[1], show=False)
   gd.pl.convergence(adata, which="sigma2", ax=axes[2], show=False)

   plt.tight_layout()
   plt.savefig("analysis.png", dpi=300)
   plt.show()
