"""
Deterministic foundational operations used to exercise KL end-to-end.

These are intentionally simple numeric placeholders that emphasise
structure, policy checks, and traceability rather than performance.
"""

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class Grid1D:
    values: List[float]
    spacing: float

    def __post_init__(self) -> None:
        if self.spacing <= 0:
            raise ValueError("Grid spacing must be positive")
        if len(self.values) < 3:
            raise ValueError("Grid must contain at least 3 points")
        if len(self.values) > 4096:
            raise ValueError("Grid length must be <= 4096")

    @property
    def length(self) -> int:
        return len(self.values)


def solve_poisson_1d(rho: Grid1D) -> Grid1D:
    """
    Solve d2phi/dx2 = rho with Dirichlet boundaries phi[0] = phi[-1] = 0.

    Uses a tridiagonal solve (Thomas algorithm) over the interior nodes.
    Deterministic and intended for small grids where transparency matters
    more than performance.
    """
    interior_count = rho.length - 2
    if interior_count < 1:
        raise ValueError("Grid must contain interior points")

    dx2 = rho.spacing * rho.spacing
    a = [-1.0] * (interior_count - 1)
    b = [2.0] * interior_count
    c = [-1.0] * (interior_count - 1)
    d = [value * dx2 for value in rho.values[1:-1]]

    # Forward elimination
    for i in range(1, interior_count):
        factor = a[i - 1] / b[i - 1]
        b[i] -= factor * c[i - 1]
        d[i] -= factor * d[i - 1]

    # Back substitution
    phi_internal = [0.0] * interior_count
    phi_internal[-1] = d[-1] / b[-1]
    for i in range(interior_count - 2, -1, -1):
        phi_internal[i] = (d[i] - c[i] * phi_internal[i + 1]) / b[i]

    phi = [0.0] + phi_internal + [0.0]
    return Grid1D(values=phi, spacing=rho.spacing)


def integrate_trajectory_1d(
    x0: float,
    v0: float,
    dt: float,
    steps: int,
    force: float,
    mass: float,
) -> List[float]:
    """
    Integrate position over discrete steps under constant force.
    Returns the list of positions (including the initial position).
    """
    if dt <= 0:
        raise ValueError("dt must be positive")
    if steps < 1:
        raise ValueError("steps must be at least 1")
    if mass == 0:
        raise ValueError("mass must be non-zero")

    positions = [x0]
    acceleration = force / mass
    velocity = v0
    position = x0

    for _ in range(steps):
        velocity += acceleration * dt
        position += velocity * dt
        positions.append(position)

    return positions


def smooth_measurements(values: Iterable[float]) -> List[float]:
    """
    Apply a fixed three point moving average.
    Edges use the available values without padding.
    """
    vals = list(values)
    if not vals:
        return []
    if len(vals) > 10_000:
        raise ValueError("Series length must be <= 10_000")

    smoothed: List[float] = []
    for i in range(len(vals)):
        start = max(0, i - 1)
        end = min(len(vals), i + 2)
        window_vals = vals[start:end]
        smoothed.append(sum(window_vals) / len(window_vals))

    return smoothed
