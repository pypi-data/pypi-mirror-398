Tools (gd.tl)
=============

.. module:: gedi2py.tools
   :synopsis: Analysis tools for GEDI

The tools module provides functions for model training, computing projections,
dimensionality reduction, imputation, and differential analysis.

.. currentmodule:: gedi2py.tools

Model Training
--------------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   gedi

.. autofunction:: gedi

   **Example**

   .. code-block:: python

      import gedi2py as gd

      # Basic usage
      gd.tl.gedi(adata, batch_key="sample", n_latent=10)

      # With more options
      gd.tl.gedi(
          adata,
          batch_key="sample",
          n_latent=20,
          max_iterations=200,
          mode="Bsphere",
          ortho_Z=True,
          key_added="gedi",
      )

   **Stored Results**

   - ``adata.obsm['X_gedi']``: Cell embeddings (n_cells × n_latent)
   - ``adata.varm['gedi_Z']``: Gene loadings (n_genes × n_latent)
   - ``adata.uns['gedi']``: Model parameters and metadata

Projections
-----------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   get_projection
   compute_zdb
   compute_db
   compute_adb

.. autofunction:: get_projection

.. autofunction:: compute_zdb

.. autofunction:: compute_db

.. autofunction:: compute_adb

**Projection Types**

.. list-table::
   :header-rows: 1
   :widths: 15 25 60

   * - Type
     - Shape
     - Description
   * - zdb
     - (n_genes, n_cells)
     - Full projection: shared manifold
   * - db
     - (n_latent, n_cells)
     - Latent factors: batch-corrected cell embeddings
   * - adb
     - (n_pathways, n_cells)
     - Pathway activity scores (requires C matrix)

**Example**

.. code-block:: python

   # Get DB projection (latent factors)
   gd.tl.get_projection(adata, which="db")
   db = adata.obsm['X_gedi_db']

   # Compute ZDB (full projection)
   zdb = gd.tl.compute_zdb(adata)

Embeddings
----------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   svd
   pca
   umap

.. autofunction:: svd

.. autofunction:: pca

.. autofunction:: umap

**Example**

.. code-block:: python

   # Compute all embeddings
   gd.tl.pca(adata)
   gd.tl.umap(adata)

   # Access results
   pca_coords = adata.obsm['X_gedi_pca']
   umap_coords = adata.obsm['X_gedi_umap']

Imputation
----------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   impute
   variance
   dispersion

.. autofunction:: impute

.. autofunction:: variance

.. autofunction:: dispersion

**Example**

.. code-block:: python

   # Impute denoised expression
   gd.tl.impute(adata)
   imputed = adata.layers['gedi_imputed']

   # Compute variance and dispersion
   gd.tl.variance(adata)
   gd.tl.dispersion(adata)

Differential Expression
-----------------------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   differential
   diff_q
   diff_o

.. autofunction:: differential

.. autofunction:: diff_q

.. autofunction:: diff_o

**Example**

.. code-block:: python

   import numpy as np

   # Create contrast: sample 0 vs sample 1
   n_samples = len(adata.obs['sample'].unique())
   contrast = np.zeros(n_samples)
   contrast[0] = 1
   contrast[1] = -1

   # Compute differential expression
   gd.tl.differential(adata, contrast=contrast)

   # Access results
   de = adata.varm['gedi_differential']

Pathway Analysis
----------------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   pathway_associations
   pathway_scores
   top_pathway_genes

.. autofunction:: pathway_associations

.. autofunction:: pathway_scores

.. autofunction:: top_pathway_genes

**Example**

.. code-block:: python

   # Run GEDI with pathway prior
   C = load_pathway_matrix()  # genes × pathways
   gd.tl.gedi(adata, batch_key="sample", C=C)

   # Get pathway associations
   gd.tl.pathway_associations(adata)

   # Get top genes per pathway
   top_genes = gd.tl.top_pathway_genes(adata, pathway_idx=0, n_genes=10)

Dynamics / Trajectory
---------------------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   vector_field
   gradient
   pseudotime

.. autofunction:: vector_field

.. autofunction:: gradient

.. autofunction:: pseudotime

**Example**

.. code-block:: python

   # Define start and end contrasts
   start = np.array([1, 0, 0, 0])
   end = np.array([0, 0, 0, 1])

   # Compute vector field
   gd.tl.vector_field(adata, start_contrast=start, end_contrast=end)

   # Compute pseudotime
   gd.tl.pseudotime(adata, root_contrast=start)
