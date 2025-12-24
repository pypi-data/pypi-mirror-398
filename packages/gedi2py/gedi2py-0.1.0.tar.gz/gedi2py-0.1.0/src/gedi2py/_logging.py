"""Logging utilities for gedi2py."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from ._settings import settings

if TYPE_CHECKING:
    from typing import Any


def _get_logger() -> logging.Logger:
    """Get the gedi2py logger."""
    logger = logging.getLogger("gedi2py")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    return logger


def info(msg: str, *, time: float | None = None, deep: str | None = None) -> float:
    """Log an info message.

    Parameters
    ----------
    msg
        Message to log.
    time
        Start time for elapsed time calculation.
    deep
        Additional details to show.

    Returns
    -------
    Current time for timing subsequent operations.
    """
    logger = _get_logger()
    if settings.verbosity >= 1:
        if time is not None:
            elapsed = _format_time(time)
            msg = f"{msg} ({elapsed})"
        if deep is not None:
            msg = f"{msg}\n    {deep}"
        logger.info(msg)
    return _now()


def debug(msg: str) -> None:
    """Log a debug message."""
    if settings.verbosity >= 3:
        _get_logger().debug(f"    {msg}")


def warning(msg: str) -> None:
    """Log a warning message."""
    if settings.verbosity >= 1:
        _get_logger().warning(f"WARNING: {msg}")


def error(msg: str) -> None:
    """Log an error message."""
    _get_logger().error(f"ERROR: {msg}")


def _now() -> float:
    """Return current time."""
    return time.time()


def _format_time(start: float) -> str:
    """Format elapsed time since start."""
    elapsed = time.time() - start
    if elapsed < 1:
        return f"{elapsed * 1000:.0f}ms"
    elif elapsed < 60:
        return f"{elapsed:.1f}s"
    elif elapsed < 3600:
        return f"{elapsed / 60:.1f}min"
    else:
        return f"{elapsed / 3600:.1f}h"
