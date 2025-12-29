# test_axioms.py

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

import pytest

from kl_kernel_logic import (
    PsiDefinition,
    Kernel,
    ExecutionTrace,
    CAEL,
    FailureCode,
)


# ---------------------------------------------------------------------------
# Δ – Atomicity / "always produces a trace"
# ---------------------------------------------------------------------------


def test_delta_produces_trace_on_success() -> None:
    kernel = Kernel()
    psi = PsiDefinition(psi_type="test", name="success_case")

    def task(x: int) -> int:
        return x + 1

    trace = kernel.execute(psi=psi, task=task, metadata={"case": "success"}, x=41)

    assert isinstance(trace, ExecutionTrace)
    assert trace.success is True
    assert trace.output == 42
    assert trace.error is None
    assert trace.failure_code is FailureCode.OK
    assert trace.psi == psi


def test_delta_produces_trace_on_failure_never_raises() -> None:
    kernel = Kernel()
    psi = PsiDefinition(psi_type="test", name="failure_case")

    def task() -> None:
        raise ValueError("boom")

    # must not raise
    trace = kernel.execute(psi=psi, task=task)

    assert isinstance(trace, ExecutionTrace)
    assert trace.success is False
    assert trace.output is None
    assert trace.error is not None
    assert trace.failure_code is FailureCode.TASK_EXCEPTION
    assert "ValueError" in trace.exception_repr
    assert trace.psi == psi


# ---------------------------------------------------------------------------
# V – Behaviour / Ordering via CAEL
# ---------------------------------------------------------------------------


def test_behaviour_preserves_order_in_cael_pipeline() -> None:
    kernel = Kernel()
    cael = CAEL(kernel)

    psi1 = PsiDefinition(psi_type="test", name="step_1")
    psi2 = PsiDefinition(psi_type="test", name="step_2")

    def step1() -> str:
        return "a"

    def step2(value: str) -> str:
        return value + "b"

    steps = [
        (psi1, step1, {}),
        (psi2, step2, {"value": "a"}),
    ]

    result = cael.run(steps, metadata={"pipeline": "ordering"})

    assert result.success is True
    assert len(result.traces) == 2
    assert result.traces[0].psi == psi1
    assert result.traces[1].psi == psi2
    assert result.traces[0].success is True
    assert result.traces[1].success is True


def test_behaviour_stops_on_first_failure_in_cael_pipeline() -> None:
    kernel = Kernel()
    cael = CAEL(kernel)

    psi_ok = PsiDefinition(psi_type="test", name="ok")
    psi_fail = PsiDefinition(psi_type="test", name="fail")
    psi_after = PsiDefinition(psi_type="test", name="after_failure")

    def ok_step() -> str:
        return "ok"

    def failing_step() -> None:
        raise RuntimeError("stop here")

    def should_not_run() -> str:
        return "nope"

    steps = [
        (psi_ok, ok_step, {}),
        (psi_fail, failing_step, {}),
        (psi_after, should_not_run, {}),
    ]

    result = cael.run(steps)

    # pipeline must stop at failing step
    assert result.success is False
    assert len(result.traces) == 2
    assert result.traces[0].psi == psi_ok
    assert result.traces[1].psi == psi_fail
    # no trace for psi_after
    assert all(t.psi != psi_after for t in result.traces)


# ---------------------------------------------------------------------------
# t – Logical time
# ---------------------------------------------------------------------------


def test_logical_time_ordering() -> None:
    # controlled providers to make the ordering explicit
    base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
    offsets = [0, 1, 2, 3]
    idx = {"value": 0}

    def now_provider() -> datetime:
        i = idx["value"]
        idx["value"] += 1
        return base_time + timedelta(milliseconds=offsets[i])

    perf_ticks = [0.0, 0.01, 0.02, 0.03]
    jdx = {"value": 0}

    def perf_provider() -> float:
        j = jdx["value"]
        jdx["value"] += 1
        return perf_ticks[j]

    kernel = Kernel(
        now_provider=now_provider,
        perf_counter_provider=perf_provider,
    )

    psi1 = PsiDefinition(psi_type="test", name="t1")
    psi2 = PsiDefinition(psi_type="test", name="t2")

    def noop() -> None:
        return None

    t1 = kernel.execute(psi=psi1, task=noop)
    t2 = kernel.execute(psi=psi2, task=noop)

    # per-trace: started_at < finished_at
    assert t1.started_at <= t1.finished_at
    assert t2.started_at <= t2.finished_at

    # logical time: second trace must not start before first finished
    assert t1.finished_at <= t2.started_at


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_determinism_same_input_same_output() -> None:
    kernel = Kernel()
    psi = PsiDefinition(psi_type="test", name="deterministic")

    def add(a: int, b: int) -> int:
        return a + b

    t1 = kernel.execute(psi=psi, task=add, a=2, b=3)
    t2 = kernel.execute(psi=psi, task=add, a=2, b=3)

    assert t1.success is True
    assert t2.success is True
    assert t1.output == 5
    assert t2.output == 5
    # run_id and timestamps may differ; determinism is on behaviour, not IDs


# ---------------------------------------------------------------------------
# SS – Trace completeness and immutability
# ---------------------------------------------------------------------------


def test_trace_contains_complete_state() -> None:
    kernel = Kernel()
    psi = PsiDefinition(psi_type="test", name="complete_state")

    def task(x: int) -> int:
        return x * 2

    trace = kernel.execute(psi=psi, task=task, metadata={"key": "value"}, x=21)

    # basic completeness checks
    assert trace.run_id
    assert trace.psi == psi
    assert trace.started_at <= trace.finished_at
    assert trace.runtime_ms >= 0.0
    assert trace.success is True
    assert trace.output == 42
    assert trace.error is None
    assert trace.failure_code is FailureCode.OK
    assert trace.exception_type is None
    assert trace.exception_repr is None
    assert trace.failure_code is FailureCode.OK
    assert isinstance(trace.metadata, dict) or hasattr(trace.metadata, "items")


def test_trace_is_immutable() -> None:
    kernel = Kernel()
    psi = PsiDefinition(psi_type="test", name="immutable")

    def task() -> str:
        return "ok"

    trace = kernel.execute(psi=psi, task=task)

    with pytest.raises(FrozenInstanceError):
        trace.output = "modified"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Composability – chained steps via CAEL
# ---------------------------------------------------------------------------


def test_composability_chained_steps() -> None:
    kernel = Kernel()
    cael = CAEL(kernel)

    psi1 = PsiDefinition(psi_type="test", name="step_1")
    psi2 = PsiDefinition(psi_type="test", name="step_2")
    psi3 = PsiDefinition(psi_type="test", name="step_3")

    def s1() -> int:
        return 1

    def s2(v: int) -> int:
        return v + 2

    def s3(v: int) -> int:
        return v * 10

    steps: List[tuple[Any, Any, Dict[str, Any]]] = [
        (psi1, s1, {}),
        (psi2, s2, {"v": 1}),
        (psi3, s3, {"v": 3}),
    ]

    result = cael.run(steps)

    assert result.success is True
    assert result.final_output == 30
    assert len(result.traces) == 3
    assert [t.psi for t in result.traces] == [psi1, psi2, psi3]

