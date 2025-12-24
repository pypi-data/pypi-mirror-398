"""GEDIModel class for single-cell data integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal
import os

import numpy as np
import scipy.sparse as sp

from .._settings import settings
from .. import _logging as logg

if TYPE_CHECKING:
    from anndata import AnnData
    from numpy.typing import NDArray


class GEDIModel:
    """GEDI model for single-cell RNA-seq data integration.

    Gene Expression Decomposition for Integration (GEDI) learns shared
    metagenes and sample-specific factors for batch effect correction.

    Parameters
    ----------
    adata
        Annotated data matrix with cells as observations (n_cells x n_genes).
    batch_key
        Key in ``adata.obs`` containing batch/sample labels.
    n_latent
        Number of latent factors (K). Default: 10.
    layer
        Layer to use instead of ``adata.X``. If None, uses ``adata.X``.
    mode
        Normalization mode for B matrices: "Bsphere" (recommended) or "Bl2".
    ortho_Z
        Whether to orthogonalize Z matrix. Default: True.
    C
        Gene × pathway prior matrix for pathway analysis. Optional.
    H
        Covariate × sample prior matrix. Optional.
    random_state
        Random seed for reproducibility.
    verbose
        Verbosity level (0-3). If None, uses global settings.
    n_jobs
        Number of parallel jobs. -1 uses all available cores.

    Attributes
    ----------
    is_trained
        Whether the model has been trained.
    n_iter
        Number of iterations completed.

    Examples
    --------
    >>> import gedi2py as gd
    >>> import scanpy as sc
    >>> adata = sc.read_h5ad("data.h5ad")
    >>> model = gd.GEDIModel(adata, batch_key="sample", n_latent=10)
    >>> model.train(max_iterations=100)
    >>> Z = model.get_Z()
    >>> embeddings = model.get_latent_representation()
    """

    def __init__(
        self,
        adata: AnnData,
        batch_key: str,
        *,
        n_latent: int = 10,
        layer: str | None = None,
        mode: Literal["Bl2", "Bsphere"] = "Bsphere",
        ortho_Z: bool = True,
        C: NDArray | None = None,
        H: NDArray | None = None,
        random_state: int | None = None,
        verbose: int | None = None,
        n_jobs: int | None = None,
    ) -> None:
        self.adata = adata
        self.batch_key = batch_key
        self.n_latent = n_latent
        self.layer = layer
        self.mode = mode
        self.ortho_Z = ortho_Z
        self.C = C
        self.H = H
        self.random_state = random_state if random_state is not None else settings.random_state
        self.verbose = verbose if verbose is not None else settings.verbosity
        self.n_jobs = n_jobs if n_jobs is not None else settings.n_jobs

        self._is_trained = False
        self._is_initialized = False
        self.n_iter = 0
        self._cpp_model = None
        self._tracking: dict = {}

        # Validate inputs
        self._validate_inputs()

        # Prepare data for C++ backend
        self._prepare_data()

    def _validate_inputs(self) -> None:
        """Validate input data and parameters."""
        if self.batch_key not in self.adata.obs.columns:
            raise ValueError(
                f"batch_key '{self.batch_key}' not found in adata.obs. "
                f"Available keys: {list(self.adata.obs.columns)}"
            )

        if self.n_latent < 1:
            raise ValueError(f"n_latent must be >= 1, got {self.n_latent}")

        n_cells, n_genes = self.adata.shape
        if self.n_latent >= min(n_cells, n_genes):
            raise ValueError(
                f"n_latent ({self.n_latent}) must be < min(n_cells, n_genes) "
                f"= min({n_cells}, {n_genes}) = {min(n_cells, n_genes)}"
            )

        if self.mode not in ("Bl2", "Bsphere"):
            raise ValueError(f"mode must be 'Bl2' or 'Bsphere', got '{self.mode}'")

    def _prepare_data(self) -> None:
        """Prepare data matrices for C++ backend."""
        # Get expression matrix
        if self.layer is not None:
            X = self.adata.layers[self.layer]
        else:
            X = self.adata.X

        # Store dimensions (AnnData: cells x genes, GEDI C++: genes x cells)
        self.n_cells, self.n_genes = X.shape

        # Get sample labels
        self.sample_labels = self.adata.obs[self.batch_key].values.astype(str)
        self.unique_samples = np.unique(self.sample_labels)
        self.n_samples = len(self.unique_samples)

        # Create sample index mapping
        self.sample_indices = {
            sample: np.where(self.sample_labels == sample)[0]
            for sample in self.unique_samples
        }

        # Convert to dense and transpose for C++ (genes x cells)
        if sp.issparse(X):
            X_dense = X.toarray()
        else:
            X_dense = np.asarray(X)

        # Log-transform: Y = log1p(X)
        self._Y = np.log1p(X_dense).T  # Transpose to genes x cells

        # Create per-sample Yi matrices
        self._Yi_list = []
        for sample in self.unique_samples:
            idx = self.sample_indices[sample]
            Yi = np.ascontiguousarray(self._Y[:, idx], dtype=np.float64)
            self._Yi_list.append(Yi)

        if self.verbose >= 1:
            logg.info(
                f"GEDI model created",
                deep=f"{self.n_cells} cells × {self.n_genes} genes, "
                     f"{self.n_samples} samples, K={self.n_latent}"
            )

    def _init_cpp_model(self) -> None:
        """Initialize the C++ GEDI model."""
        from .._gedi2py_cpp import GEDI

        # Get effective number of threads
        n_threads = self.n_jobs if self.n_jobs > 0 else (os.cpu_count() or 1)

        # Dimensions
        J = self.n_genes
        N = self.n_cells
        K = self.n_latent
        P = self.C.shape[1] if self.C is not None else 0
        L = self.H.shape[0] if self.H is not None else 0

        # Initialize parameters (will be set by initialize())
        np.random.seed(self.random_state)

        # Create initial Bi, Qi, si, oi for each sample
        Bi_init = []
        Qi_init = []
        si_init = []
        oi_init = []

        for sample in self.unique_samples:
            Ni = len(self.sample_indices[sample])
            # Initialize with small random values (will be overwritten by initialize)
            Bi = np.ascontiguousarray(np.random.randn(K, Ni) * 0.01, dtype=np.float64)
            Qi = np.ascontiguousarray(np.zeros((J, K), dtype=np.float64))
            si = np.ascontiguousarray(np.zeros(Ni, dtype=np.float64))
            oi = np.ascontiguousarray(np.zeros(J, dtype=np.float64))
            Bi_init.append(Bi)
            Qi_init.append(Qi)
            si_init.append(si)
            oi_init.append(oi)

        # Initialize global parameters
        o_init = np.ascontiguousarray(np.zeros(J, dtype=np.float64))
        Z_init = np.ascontiguousarray(np.random.randn(J, K) * 0.01, dtype=np.float64)
        U_init = np.ascontiguousarray(np.eye(K, dtype=np.float64))
        S_init = np.ascontiguousarray(np.ones(K, dtype=np.float64))
        D_init = np.ascontiguousarray(np.ones(K, dtype=np.float64))
        sigma2_init = 1.0

        # Create C++ model
        self._cpp_model = GEDI(
            J, N, K, P, L, self.n_samples,
            Bi_init, Qi_init, si_init, oi_init,
            o_init, Z_init, U_init, S_init, D_init,
            sigma2_init,
            self._Yi_list,
            "Y",  # obs_type
            self.mode,
            self.ortho_Z,
            True,  # adjustD
            False,  # multimodal
            self.verbose,
            n_threads
        )

        # Set optional priors
        if self.C is not None:
            self._cpp_model.set_C(np.ascontiguousarray(self.C, dtype=np.float64))
        if self.H is not None:
            self._cpp_model.set_H(np.ascontiguousarray(self.H, dtype=np.float64))

    def initialize(self) -> None:
        """Initialize model parameters using randomized SVD.

        This is called automatically by :meth:`train`, but can be called
        separately for more control.
        """
        if self._cpp_model is None:
            self._init_cpp_model()

        start = logg.info("Initializing model parameters...")
        self._cpp_model.initialize(False)  # multimodal=False
        self._is_initialized = True
        logg.info("    finished", time=start)

    def optimize(
        self,
        iterations: int = 100,
        track_interval: int = 5,
    ) -> None:
        """Run optimization iterations.

        Parameters
        ----------
        iterations
            Number of optimization iterations.
        track_interval
            Interval for tracking convergence metrics.
        """
        if not self._is_initialized:
            raise RuntimeError("Model must be initialized before optimizing. Call initialize() first.")

        start = logg.info(f"Optimizing for {iterations} iterations...")
        self._cpp_model.optimize(iterations, track_interval)
        self.n_iter += iterations
        self._is_trained = True
        logg.info("    finished", time=start, deep=f"sigma2={self.get_sigma2():.6f}")

        # Store tracking data
        self._tracking["sigma2"] = np.array(self._cpp_model.get_tracking_sigma2())

    def train(
        self,
        max_iterations: int = 100,
        track_interval: int = 5,
    ) -> None:
        """Train the GEDI model (initialize + optimize).

        Parameters
        ----------
        max_iterations
            Maximum number of optimization iterations.
        track_interval
            Interval for tracking convergence metrics.
        """
        if not self._is_initialized:
            self.initialize()
        self.optimize(max_iterations, track_interval)

    @property
    def is_trained(self) -> bool:
        """Whether the model has been trained."""
        return self._is_trained

    def get_Z(self) -> NDArray:
        """Get shared metagenes matrix.

        Returns
        -------
        np.ndarray
            Shared metagenes of shape (n_genes, n_latent).
        """
        self._check_trained()
        return self._cpp_model.get_Z()

    def get_D(self) -> NDArray:
        """Get scaling factors.

        Returns
        -------
        np.ndarray
            Scaling factors of shape (n_latent,).
        """
        self._check_trained()
        return self._cpp_model.get_D()

    def get_sigma2(self) -> float:
        """Get estimated noise variance.

        Returns
        -------
        float
            Noise variance (sigma^2).
        """
        self._check_trained()
        return self._cpp_model.get_sigma2()

    def get_Bi(self) -> list[NDArray]:
        """Get sample-specific cell factor matrices.

        Returns
        -------
        list of np.ndarray
            List of Bi matrices, each of shape (n_latent, n_cells_in_sample).
        """
        self._check_trained()
        return self._cpp_model.get_Bi()

    def get_latent_representation(self) -> NDArray:
        """Get cell embeddings in latent space (DB projection).

        Returns
        -------
        np.ndarray
            Cell embeddings of shape (n_cells, n_latent).
        """
        self._check_trained()
        from .._gedi2py_cpp import compute_DB

        D = self.get_D()
        Bi = self.get_Bi()
        DB = compute_DB(D, Bi, 0)  # K x N
        return DB.T  # Return as N x K

    def get_tracking(self) -> dict:
        """Get tracking data from optimization.

        Returns
        -------
        dict
            Dictionary with tracking data (sigma2, etc.).
        """
        return self._tracking

    def _check_trained(self) -> None:
        """Check if model is trained."""
        if not self._is_trained:
            raise RuntimeError("Model must be trained first. Call train() or optimize().")

    def __repr__(self) -> str:
        status = "trained" if self._is_trained else "untrained"
        return (
            f"GEDIModel({status}, "
            f"n_cells={self.n_cells}, "
            f"n_genes={self.n_genes}, "
            f"n_samples={self.n_samples}, "
            f"n_latent={self.n_latent})"
        )
