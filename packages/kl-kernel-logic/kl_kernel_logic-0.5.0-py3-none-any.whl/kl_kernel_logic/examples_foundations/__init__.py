"""
Foundational deterministic examples for KL.

These operations are small, inspectable building blocks that exercise
Psi + CAEL + Kernel end-to-end.
"""

from .operations import (
    Grid1D,
    solve_poisson_1d,
    integrate_trajectory_1d,
    smooth_measurements,
)
from .runners import (
    run_poisson_example,
    run_trajectory_example,
    run_smoothing_example,
    run_all_examples,
)

__all__ = [
    "Grid1D",
    "solve_poisson_1d",
    "integrate_trajectory_1d",
    "smooth_measurements",
    "run_poisson_example",
    "run_trajectory_example",
    "run_smoothing_example",
    "run_all_examples",
]
