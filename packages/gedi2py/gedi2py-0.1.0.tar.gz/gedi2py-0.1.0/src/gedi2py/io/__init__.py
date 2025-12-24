"""I/O module for GEDI (gd.io).

Functions for reading and writing data and GEDI models.

File formats:
    - H5AD: :func:`read_h5ad`, :func:`write_h5ad`
    - 10X H5: :func:`read_10x_h5`
    - 10X MTX: :func:`read_10x_mtx`

Model persistence:
    - :func:`save_model`: Save GEDI model to file
    - :func:`load_model`: Load GEDI model from file
"""

from ._h5ad import (
    load_model,
    read_h5ad,
    save_model,
    write_h5ad,
)

from ._h5 import (
    read_10x_h5,
    read_10x_mtx,
)

__all__ = [
    # H5AD
    "read_h5ad",
    "write_h5ad",
    # 10X
    "read_10x_h5",
    "read_10x_mtx",
    # Model persistence
    "save_model",
    "load_model",
]
