# cael.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, List, Mapping, Optional, Sequence, Tuple, TypeVar

from .psi import PsiDefinition
from .kernel import Kernel, ExecutionTrace

T = TypeVar("T")


@dataclass(frozen=True)
class CaelResult(Generic[T]):
    """
    Aggregated result of a CAEL pipeline.

    Contract:
    - traces: ordered list of ExecutionTrace objects (one per step)
    - success: False if any step fails
    - final_output: output of the last successful step or None
    """

    traces: List[ExecutionTrace[Any]]
    final_output: Optional[T]
    success: bool
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None


class CAEL:
    """
    Composable Atomic Execution Layer.

    Responsibilities:
    - execute a sequence of steps via a single Kernel instance
    - each step is defined as (psi, task, kwargs)
    - no governance, routing or retry logic
    """

    def __init__(self, kernel: Kernel) -> None:
        self._kernel = kernel

    def run(
        self,
        steps: Sequence[
            Tuple[
                PsiDefinition,
                Callable[..., Any],
                Mapping[str, Any],  # kwargs for the task
            ]
        ],
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> CaelResult[Any]:
        """
        Execute all steps in order using the kernel.

        Each step:
        - uses its PsiDefinition
        - calls task(**kwargs)
        - generates an ExecutionTrace through Kernel.execute
        """
        is_valid, error = self._validate_steps(steps)
        if not is_valid:
            return CaelResult(
                traces=[],
                final_output=None,
                success=False,
                failure_code="INVALID_STEP",
                failure_message=error,
            )

        traces: List[ExecutionTrace[Any]] = []
        last_output: Any = None
        pipeline_success = True
        failure_code: Optional[str] = None
        failure_message: Optional[str] = None

        for psi, task, kwargs in steps:
            trace = self._kernel.execute(
                psi=psi,
                task=task,
                metadata=metadata,
                **dict(kwargs),
            )
            traces.append(trace)

            if not trace.success:
                pipeline_success = False
                last_output = None
                failure_code = trace.failure_code.value
                failure_message = trace.error
                break

            last_output = trace.output

        return CaelResult(
            traces=traces,
            final_output=last_output,
            success=pipeline_success,
            failure_code=failure_code,
            failure_message=failure_message,
        )

    def _validate_steps(
        self,
        steps: Sequence[Tuple[PsiDefinition, Callable[..., Any], Mapping[str, Any]]],
    ) -> tuple[bool, Optional[str]]:
        for idx, step in enumerate(steps):
            if not isinstance(step, tuple) or len(step) != 3:
                return False, f"Step {idx} must be (psi, task, kwargs)"
            psi, task, kwargs = step
            if not isinstance(psi, PsiDefinition):
                return False, f"Step {idx} psi must be PsiDefinition"
            if not callable(task):
                return False, f"Step {idx} task must be callable"
            if not isinstance(kwargs, Mapping):
                return False, f"Step {idx} kwargs must be a Mapping"
        return True, None
