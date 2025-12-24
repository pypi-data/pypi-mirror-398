Core
====

The core module contains the main GEDIModel class and global settings.

GEDIModel
---------

.. currentmodule:: gedi2py

.. autoclass:: GEDIModel
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   The GEDIModel class provides fine-grained control over the GEDI algorithm.

   **Basic Usage**

   .. code-block:: python

      import gedi2py as gd

      # Create model
      model = gd.GEDIModel(
          adata,
          batch_key="sample",
          n_latent=10,
      )

      # Train
      model.train(max_iterations=100)

      # Get results
      Z = model.get_Z()
      embeddings = model.get_latent_representation()

   **Step-by-Step Training**

   For more control, initialize and optimize separately:

   .. code-block:: python

      model = gd.GEDIModel(adata, batch_key="sample", n_latent=10)

      # Initialize parameters
      model.initialize()

      # Run optimization in batches
      for i in range(10):
          model.optimize(iterations=10)
          print(f"sigma2: {model.get_sigma2()}")

   **Parameters**

   .. list-table::
      :header-rows: 1
      :widths: 20 15 65

      * - Parameter
        - Type
        - Description
      * - adata
        - AnnData
        - Annotated data matrix with cells as observations
      * - batch_key
        - str
        - Column in ``adata.obs`` containing sample/batch labels
      * - n_latent
        - int
        - Number of latent factors (default: 10)
      * - layer
        - str | None
        - Layer to use (default: None uses ``adata.X``)
      * - mode
        - str
        - Constraint mode: "Bsphere" or "Bl2" (default: "Bsphere")
      * - ortho_Z
        - bool
        - Orthogonalize Z matrix (default: True)
      * - C
        - NDArray | None
        - Gene-pathway prior matrix (default: None)
      * - H
        - NDArray | None
        - Covariate-sample prior matrix (default: None)
      * - random_state
        - int | None
        - Random seed for reproducibility
      * - verbose
        - int | None
        - Verbosity level (0-3)
      * - n_jobs
        - int | None
        - Number of threads (-1 for all)

   **Attributes**

   .. list-table::
      :header-rows: 1
      :widths: 20 80

      * - Attribute
        - Description
      * - is_trained
        - Whether the model has been trained
      * - n_iter
        - Number of optimization iterations completed

   **Methods**

   .. list-table::
      :header-rows: 1
      :widths: 30 70

      * - Method
        - Description
      * - initialize()
        - Initialize model parameters using randomized SVD
      * - optimize(iterations, track_interval)
        - Run optimization iterations
      * - train(max_iterations, track_interval)
        - Full training (initialize + optimize)
      * - get_Z()
        - Get shared metagenes (n_genes × n_latent)
      * - get_D()
        - Get scaling factors (n_latent,)
      * - get_sigma2()
        - Get noise variance
      * - get_Bi()
        - Get sample-specific cell factors
      * - get_latent_representation()
        - Get DB projection (n_cells × n_latent)
      * - get_tracking()
        - Get convergence tracking data

Settings
--------

.. autodata:: gedi2py.settings
   :annotation:

Global configuration settings for gedi2py.

.. code-block:: python

   import gedi2py as gd

   # Set verbosity (0=silent, 1=progress, 2=detailed, 3=debug)
   gd.settings.verbosity = 1

   # Set number of threads (-1 for all available)
   gd.settings.n_jobs = 4

   # Set random seed for reproducibility
   gd.settings.random_state = 42

**Available Settings**

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Setting
     - Default
     - Description
   * - verbosity
     - 1
     - Verbosity level (0-3)
   * - n_jobs
     - -1
     - Number of threads for parallel operations
   * - random_state
     - 0
     - Default random seed
