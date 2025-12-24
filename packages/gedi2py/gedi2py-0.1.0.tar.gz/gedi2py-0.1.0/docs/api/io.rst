I/O (gd.io)
===========

.. module:: gedi2py.io
   :synopsis: Input/output functions for data and models

The I/O module provides functions for reading and writing data files
and persisting GEDI models.

.. currentmodule:: gedi2py.io

Reading Data
------------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   read_h5ad
   read_10x_h5
   read_10x_mtx

.. autofunction:: read_h5ad

   **Example**

   .. code-block:: python

      import gedi2py as gd

      # Read H5AD file
      adata = gd.read_h5ad("data.h5ad")

      # Read with backed mode (for large files)
      adata = gd.read_h5ad("large_data.h5ad", backed="r")

.. autofunction:: read_10x_h5

   **Example**

   .. code-block:: python

      # Read 10X Genomics H5 file
      adata = gd.read_10x_h5("filtered_feature_bc_matrix.h5")

      # Read specific genome
      adata = gd.read_10x_h5("multi_genome.h5", genome="GRCh38")

      # Include non-gene-expression features
      adata = gd.read_10x_h5("multimodal.h5", gex_only=False)

.. autofunction:: read_10x_mtx

   **Example**

   .. code-block:: python

      # Read 10X MTX directory
      adata = gd.read_10x_mtx("filtered_feature_bc_matrix/")

      # With caching for faster subsequent reads
      adata = gd.read_10x_mtx("filtered_feature_bc_matrix/", cache=True)

Writing Data
------------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   write_h5ad

.. autofunction:: write_h5ad

   **Example**

   .. code-block:: python

      # Write H5AD file with compression
      gd.write_h5ad(adata, "output.h5ad", compression="gzip")

      # Write without compression (faster, larger file)
      gd.write_h5ad(adata, "output.h5ad", compression=None)

Model Persistence
-----------------

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   save_model
   load_model

.. autofunction:: save_model

   Save just the GEDI model parameters, which is more compact than
   saving the entire AnnData object.

   **Example**

   .. code-block:: python

      # Run GEDI
      gd.tl.gedi(adata, batch_key="sample", n_latent=10)

      # Save model
      gd.io.save_model(adata, "gedi_model.h5")

   **Saved Parameters**

   - Z matrix (shared metagenes)
   - D vector (scaling factors)
   - Bi matrices (sample-specific factors)
   - Qi matrices (sample-specific deviations)
   - Offset vectors (o, oi, si)
   - sigma2 (noise variance)
   - Convergence tracking data

.. autofunction:: load_model

   Load a saved GEDI model into an AnnData object.

   **Example**

   .. code-block:: python

      # Load into new AnnData
      adata = gd.read_h5ad("data.h5ad")
      gd.io.load_model(adata, "gedi_model.h5")

      # Results are now available
      Z = adata.varm['gedi_Z']
      embeddings = adata.obsm['X_gedi']

   .. note::

      The AnnData object must have the same genes and samples as when
      the model was saved.

Convenience Functions
---------------------

These functions are also available at the top level:

.. code-block:: python

   import gedi2py as gd

   # These are equivalent
   adata = gd.read_h5ad("data.h5ad")
   adata = gd.io.read_h5ad("data.h5ad")

   gd.write_h5ad(adata, "output.h5ad")
   gd.io.write_h5ad(adata, "output.h5ad")

File Formats
------------

**H5AD**

The H5AD format is the standard file format for AnnData objects, based on HDF5.
It efficiently stores:

- Expression matrices (dense or sparse)
- Cell metadata (obs)
- Gene metadata (var)
- Embeddings (obsm)
- Loadings (varm)
- Unstructured data (uns)

**10X Formats**

10X Genomics provides two main formats:

- **H5**: Single HDF5 file with all data
- **MTX**: Directory with matrix.mtx, barcodes.tsv, features.tsv

gedi2py can read both formats and convert to AnnData.

Workflow Example
----------------

.. code-block:: python

   import gedi2py as gd
   import scanpy as sc

   # Load raw data
   adata = gd.read_10x_h5("raw_feature_bc_matrix.h5")

   # Preprocess
   sc.pp.filter_cells(adata, min_genes=200)
   sc.pp.filter_genes(adata, min_cells=3)
   sc.pp.normalize_total(adata)
   sc.pp.log1p(adata)

   # Save preprocessed data
   gd.write_h5ad(adata, "preprocessed.h5ad")

   # Run GEDI
   gd.tl.gedi(adata, batch_key="sample", n_latent=10)

   # Save model separately (smaller file)
   gd.io.save_model(adata, "gedi_model.h5")

   # Save full results
   gd.write_h5ad(adata, "with_gedi.h5ad")

   # Later: reload just the model
   adata2 = gd.read_h5ad("preprocessed.h5ad")
   gd.io.load_model(adata2, "gedi_model.h5")
