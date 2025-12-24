API Reference
=============

This section provides detailed API documentation for all gedi2py modules and functions.

.. toctree::
   :maxdepth: 2

   core
   tools
   plotting
   io

Overview
--------

gedi2py is organized into modules following the scanpy convention:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Module
     - Description
   * - :mod:`gedi2py`
     - Top-level imports (GEDIModel, settings, I/O functions)
   * - :mod:`gedi2py.tl <gedi2py.tools>`
     - Tools for model training, projections, embeddings, and analysis
   * - :mod:`gedi2py.pl <gedi2py.plotting>`
     - Plotting functions for visualization
   * - :mod:`gedi2py.io <gedi2py.io>`
     - Input/output for data and models

Import Convention
-----------------

.. code-block:: python

   import gedi2py as gd

   # Access modules
   gd.tl.gedi(...)        # Tools
   gd.pl.embedding(...)   # Plotting
   gd.io.read_h5ad(...)   # I/O

   # Or import directly
   from gedi2py import GEDIModel
   from gedi2py import settings

Quick Reference
---------------

**Core**

- :class:`~gedi2py.GEDIModel` - Main model class for GEDI analysis

**Tools (gd.tl)**

*Model Training*

- :func:`~gedi2py.tools.gedi` - Run GEDI batch correction

*Projections*

- :func:`~gedi2py.tools.get_projection` - Get computed projections
- :func:`~gedi2py.tools.compute_zdb` - Compute ZDB projection
- :func:`~gedi2py.tools.compute_db` - Compute DB projection
- :func:`~gedi2py.tools.compute_adb` - Compute ADB projection (pathway activity)

*Embeddings*

- :func:`~gedi2py.tools.svd` - Compute SVD on GEDI embedding
- :func:`~gedi2py.tools.pca` - Compute PCA on GEDI embedding
- :func:`~gedi2py.tools.umap` - Compute UMAP on GEDI embedding

*Imputation*

- :func:`~gedi2py.tools.impute` - Impute denoised expression
- :func:`~gedi2py.tools.variance` - Compute variance
- :func:`~gedi2py.tools.dispersion` - Compute dispersion

*Differential Expression*

- :func:`~gedi2py.tools.differential` - Differential expression analysis
- :func:`~gedi2py.tools.diff_q` - Sample-specific differential effects
- :func:`~gedi2py.tools.diff_o` - Offset differential effects

*Pathway Analysis*

- :func:`~gedi2py.tools.pathway_associations` - Compute pathway associations
- :func:`~gedi2py.tools.pathway_scores` - Compute pathway scores
- :func:`~gedi2py.tools.top_pathway_genes` - Get top genes per pathway

*Dynamics*

- :func:`~gedi2py.tools.vector_field` - Compute vector field
- :func:`~gedi2py.tools.gradient` - Compute gradient
- :func:`~gedi2py.tools.pseudotime` - Compute pseudotime

**Plotting (gd.pl)**

*Embedding Plots*

- :func:`~gedi2py.plotting.embedding` - General embedding plot
- :func:`~gedi2py.plotting.umap` - UMAP plot
- :func:`~gedi2py.plotting.pca` - PCA plot

*Convergence Plots*

- :func:`~gedi2py.plotting.convergence` - Plot convergence metrics
- :func:`~gedi2py.plotting.loss` - Plot loss function

*Feature Plots*

- :func:`~gedi2py.plotting.features` - Plot gene expression
- :func:`~gedi2py.plotting.metagenes` - Plot metagene patterns
- :func:`~gedi2py.plotting.dispersion` - Plot dispersion
- :func:`~gedi2py.plotting.variance_explained` - Plot variance explained

**I/O (gd.io)**

*Reading*

- :func:`~gedi2py.io.read_h5ad` - Read H5AD file
- :func:`~gedi2py.io.read_10x_h5` - Read 10X H5 file
- :func:`~gedi2py.io.read_10x_mtx` - Read 10X MTX directory

*Writing*

- :func:`~gedi2py.io.write_h5ad` - Write H5AD file

*Model Persistence*

- :func:`~gedi2py.io.save_model` - Save GEDI model
- :func:`~gedi2py.io.load_model` - Load GEDI model
