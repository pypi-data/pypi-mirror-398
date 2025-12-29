"""
Runnable helpers for foundational examples.

These are convenience entrypoints to demonstrate KL end-to-end on deterministic
operations.
"""

from typing import Any, Dict

from kl_kernel_logic import PsiDefinition, Kernel, CAEL

from .operations import (
    Grid1D,
    solve_poisson_1d,
    integrate_trajectory_1d,
    smooth_measurements,
)


def run_poisson_example() -> Dict[str, Any]:
    psi = PsiDefinition(
        psi_type="foundations.poisson_1d",
        name="poisson_solver",
    )

    rho_grid = Grid1D(values=[0.0, 1.0, 0.0], spacing=0.1)
    kernel = Kernel()
    trace = kernel.execute(psi=psi, task=solve_poisson_1d, rho=rho_grid)

    return {
        "psi": psi.describe(),
        "success": trace.success,
        "output": trace.output,
        "runtime_ms": trace.runtime_ms,
    }


def run_trajectory_example() -> Dict[str, Any]:
    psi = PsiDefinition(
        psi_type="foundations.trajectory_1d",
        name="trajectory_integrator",
    )

    kernel = Kernel()
    trace = kernel.execute(
        psi=psi,
        task=integrate_trajectory_1d,
        x0=0.0,
        v0=0.0,
        dt=0.01,
        steps=100,
        force=1.0,
        mass=1.0,
    )

    return {
        "psi": psi.describe(),
        "success": trace.success,
        "output": trace.output,
        "runtime_ms": trace.runtime_ms,
    }


def run_smoothing_example() -> Dict[str, Any]:
    psi = PsiDefinition(
        psi_type="foundations.smoothing",
        name="moving_average",
    )

    kernel = Kernel()
    trace = kernel.execute(
        psi=psi,
        task=smooth_measurements,
        values=[1.0, 2.0, 3.0, 4.0],
    )

    return {
        "psi": psi.describe(),
        "success": trace.success,
        "output": trace.output,
        "runtime_ms": trace.runtime_ms,
    }


def run_cael_example() -> Dict[str, Any]:
    """Run multiple operations via CAEL."""
    psi_smooth = PsiDefinition(psi_type="foundations.smoothing", name="smooth")
    psi_traj = PsiDefinition(psi_type="foundations.trajectory", name="traj")

    cael = CAEL(kernel=Kernel())

    result = cael.run([
        (psi_smooth, smooth_measurements, {"values": [1.0, 2.0, 3.0]}),
        (psi_traj, integrate_trajectory_1d, {
            "x0": 0.0, "v0": 1.0, "dt": 0.1, "steps": 10, "force": 0.0, "mass": 1.0
        }),
    ])

    return {
        "success": result.success,
        "final_output": result.final_output,
        "trace_count": len(result.traces),
    }


def run_all_examples() -> None:
    from pprint import pprint
    print("=== Poisson ===")
    pprint(run_poisson_example())
    print("\n=== Trajectory ===")
    pprint(run_trajectory_example())
    print("\n=== Smoothing ===")
    pprint(run_smoothing_example())
    print("\n=== CAEL ===")
    pprint(run_cael_example())


if __name__ == "__main__":
    run_all_examples()
