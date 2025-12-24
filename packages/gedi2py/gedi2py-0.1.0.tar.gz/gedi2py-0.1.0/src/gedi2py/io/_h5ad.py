"""H5AD file I/O functions for GEDI.

Enhanced H5AD read/write functions with GEDI model support.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anndata import AnnData


def read_h5ad(
    filename: str | Path,
    *,
    backed: str | None = None,
) -> AnnData:
    r"""Read H5AD file.

    Wrapper around :func:`anndata.read_h5ad` with consistent interface.

    Parameters
    ----------
    filename
        Path to the H5AD file.
    backed
        If ``'r'``, open in read-only backed mode.
        If ``'r+'``, open in read-write backed mode.
        If ``None``, load into memory.

    Returns
    -------
    Annotated data matrix.

    Examples
    --------
    >>> import gedi2py as gd
    >>> adata = gd.read_h5ad("data.h5ad")
    """
    import anndata

    return anndata.read_h5ad(filename, backed=backed)


def write_h5ad(
    adata: AnnData,
    filename: str | Path,
    *,
    compression: str | None = "gzip",
    compression_opts: int | None = None,
) -> None:
    r"""Write AnnData to H5AD file.

    Wrapper around :meth:`anndata.AnnData.write_h5ad` with consistent interface.

    Parameters
    ----------
    adata
        Annotated data matrix to write.
    filename
        Path to output H5AD file.
    compression
        Compression algorithm. Options: ``'gzip'``, ``'lzf'``, ``None``.
    compression_opts
        Compression level (for gzip, 1-9).

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.write_h5ad(adata, "results.h5ad")
    """
    adata.write_h5ad(
        filename,
        compression=compression,
        compression_opts=compression_opts,
    )


def save_model(
    adata: AnnData,
    filename: str | Path,
    *,
    key: str = "gedi",
    compression: str = "gzip",
) -> None:
    r"""Save GEDI model parameters to file.

    Saves the GEDI model parameters stored in ``adata.uns[key]`` to a
    separate file for later loading.

    Parameters
    ----------
    adata
        Annotated data matrix with GEDI results.
    filename
        Path to output file (will use .npz format).
    key
        Key in ``adata.uns`` where GEDI results are stored.
    compression
        Compression for numpy save.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.tl.gedi(adata, batch_key="sample")
    >>> gd.io.save_model(adata, "gedi_model.npz")
    """
    import numpy as np

    if key not in adata.uns:
        raise ValueError(
            f"No GEDI results found at adata.uns['{key}']. "
            f"Run gd.tl.gedi() first."
        )

    gedi_data = adata.uns[key]

    # Extract model parameters
    model_params = gedi_data.get("model", {})
    params = gedi_data.get("params", {})
    tracking = gedi_data.get("tracking", {})
    svd_data = gedi_data.get("svd", {})

    # Prepare for saving
    save_dict = {}

    # Model parameters
    for k, v in model_params.items():
        if isinstance(v, np.ndarray):
            save_dict[f"model_{k}"] = v
        elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], np.ndarray):
            # List of arrays (e.g., Bi_list)
            for i, arr in enumerate(v):
                save_dict[f"model_{k}_{i}"] = arr
            save_dict[f"model_{k}_count"] = np.array([len(v)])

    # Scalar parameters
    params_array = {k: v for k, v in params.items() if isinstance(v, (int, float, str))}
    save_dict["params_json"] = np.array([str(params_array)])

    # Tracking data
    for k, v in tracking.items():
        save_dict[f"tracking_{k}"] = np.asarray(v)

    # SVD data
    for k, v in svd_data.items():
        save_dict[f"svd_{k}"] = np.asarray(v)

    # Save
    filename = Path(filename)
    if not filename.suffix:
        filename = filename.with_suffix(".npz")

    np.savez_compressed(filename, **save_dict)


def load_model(
    adata: AnnData,
    filename: str | Path,
    *,
    key: str = "gedi",
) -> None:
    r"""Load GEDI model parameters from file.

    Loads previously saved GEDI model parameters and stores them in
    ``adata.uns[key]``.

    Parameters
    ----------
    adata
        Annotated data matrix to store model in.
    filename
        Path to saved model file.
    key
        Key in ``adata.uns`` to store results.

    Examples
    --------
    >>> import gedi2py as gd
    >>> gd.io.load_model(adata, "gedi_model.npz")
    >>> adata.uns["gedi"]["model"]["Z"]  # Loaded metagenes
    """
    import json

    import numpy as np

    filename = Path(filename)
    data = np.load(filename, allow_pickle=True)

    model_params = {}
    params = {}
    tracking = {}
    svd_data = {}

    # Reconstruct model parameters
    list_params = {}  # Track list parameters

    for k in data.files:
        v = data[k]

        if k.startswith("model_"):
            param_name = k[6:]  # Remove "model_"

            # Check if it's a list element
            if "_" in param_name and param_name.split("_")[-1].isdigit():
                base_name = "_".join(param_name.split("_")[:-1])
                idx = int(param_name.split("_")[-1])
                if base_name not in list_params:
                    list_params[base_name] = {}
                list_params[base_name][idx] = v
            elif param_name.endswith("_count"):
                pass  # Skip count entries
            else:
                model_params[param_name] = v

        elif k == "params_json":
            params = eval(str(v[0]))

        elif k.startswith("tracking_"):
            tracking[k[9:]] = v

        elif k.startswith("svd_"):
            svd_data[k[4:]] = v

    # Reconstruct lists
    for name, indices in list_params.items():
        sorted_indices = sorted(indices.keys())
        model_params[name] = [indices[i] for i in sorted_indices]

    # Store in adata
    adata.uns[key] = {
        "model": model_params,
        "params": params,
        "tracking": tracking,
        "svd": svd_data,
    }
