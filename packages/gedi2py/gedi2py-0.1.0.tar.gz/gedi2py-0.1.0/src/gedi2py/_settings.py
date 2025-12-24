"""Global settings for gedi2py."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
import os


@dataclass
class GedipyConfig:
    """Configuration for gedi2py.

    Attributes
    ----------
    verbosity
        Verbosity level: 0 (silent), 1 (normal), 2 (verbose), 3 (debug).
    n_jobs
        Number of parallel jobs. -1 means all available cores.
    random_state
        Default random state for reproducibility.
    """

    verbosity: Literal[0, 1, 2, 3] = 1
    n_jobs: int = -1
    random_state: int = 0

    def __repr__(self) -> str:
        return (
            f"GedipyConfig(\n"
            f"    verbosity={self.verbosity},\n"
            f"    n_jobs={self.n_jobs},\n"
            f"    random_state={self.random_state},\n"
            f")"
        )

    @property
    def effective_n_jobs(self) -> int:
        """Return actual number of jobs to use."""
        if self.n_jobs == -1:
            return os.cpu_count() or 1
        return self.n_jobs


# Global settings instance
settings = GedipyConfig()
