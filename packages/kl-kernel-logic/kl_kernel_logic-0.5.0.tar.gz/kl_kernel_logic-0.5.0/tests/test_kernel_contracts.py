# Contract tests derived from KL Execution Theory

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Iterator

import pytest

from kl_kernel_logic import FailureCode, Kernel, PsiDefinition


def _sequence_provider(values: Iterable):
    items = list(values)
    it: Iterator = iter(items)
    last = items[-1] if items else None

    def _next():
        nonlocal it
        try:
            return next(it)
        except StopIteration:
            return last

    return _next


def _kernel_with_determinism(
    *,
    run_id: str = "run-1",
    now_values: Iterable[datetime],
    perf_values: Iterable[float],
) -> Kernel:
    return Kernel(
        run_id_factory=lambda: run_id,
        now_provider=_sequence_provider(now_values),
        perf_counter_provider=_sequence_provider(perf_values),
    )


def test_execute_calls_task_exactly_once_success():
    psi = PsiDefinition(psi_type="test", name="once")
    counter = {"calls": 0}

    def task(x: int) -> int:
        counter["calls"] += 1
        return x + 1

    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    kernel = _kernel_with_determinism(
        now_values=[t0, t1],
        perf_values=[10.0, 10.0],
    )

    trace = kernel.execute(psi=psi, task=task, x=1)

    assert counter["calls"] == 1
    assert trace.success is True
    assert trace.failure_code is FailureCode.OK
    assert trace.output == 2
    assert trace.error is None
    assert trace.exception_type is None
    assert trace.exception_repr is None


def test_execute_never_raises_and_captures_error():
    psi = PsiDefinition(psi_type="test", name="fail")

    def task() -> None:
        raise ValueError("boom")

    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    kernel = _kernel_with_determinism(
        now_values=[t0, t1],
        perf_values=[5.0, 5.0],
    )

    trace = kernel.execute(psi=psi, task=task)

    assert trace.success is False
    assert trace.failure_code is FailureCode.TASK_EXCEPTION
    assert trace.output is None
    assert trace.error == "boom"
    assert trace.exception_type == "ValueError"
    assert trace.exception_repr is not None


def test_trace_time_and_runtime_invariants():
    psi = PsiDefinition(psi_type="test", name="timing")

    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2025, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
    kernel = _kernel_with_determinism(
        now_values=[t0, t1],
        perf_values=[10.0, 9.0],
    )

    trace = kernel.execute(psi=psi, task=lambda: "ok")

    assert trace.started_at == t0
    assert trace.finished_at == t1
    assert trace.runtime_ms >= 0.0
    assert trace.runtime_ms == 0.0


def test_metadata_pass_through_is_frozen():
    psi = PsiDefinition(psi_type="test", name="meta")
    metadata = {"key": "value"}

    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    kernel = _kernel_with_determinism(
        now_values=[t0, t1],
        perf_values=[1.0, 1.0],
    )

    trace = kernel.execute(psi=psi, task=lambda: "ok", metadata=metadata)

    metadata["key"] = "mutated"

    assert trace.metadata["key"] == "value"
    with pytest.raises(TypeError):
        trace.metadata["key"] = "x"  # type: ignore[misc]


def test_trace_kernel_meta_has_stable_keys():
    psi = PsiDefinition(psi_type="test", name="kernel_meta")

    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    kernel = _kernel_with_determinism(
        now_values=[t0, t1],
        perf_values=[1.0, 1.0],
    )

    trace = kernel.execute(psi=psi, task=lambda: "ok")

    kernel_meta = trace.kernel_meta
    assert isinstance(kernel_meta, dict) or hasattr(kernel_meta, "items")
    for key in ["run_id", "started_at", "finished_at", "runtime_ms", "failure_code", "success"]:
        assert key in kernel_meta


def test_canonical_serialization_and_digest():
    psi = PsiDefinition(psi_type="test", name="canonical")

    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    kernel = _kernel_with_determinism(
        now_values=[t0, t1],
        perf_values=[2.0, 2.0],
    )

    trace = kernel.execute(psi=psi, task=lambda: "ok", metadata={"a": 1})

    d1 = trace.to_dict(include_observational=True)
    d2 = trace.to_dict(include_observational=True)
    assert d1 == d2

    j1 = trace.to_json(include_observational=True)
    j2 = trace.to_json(include_observational=True)
    assert j1 == j2

    h1 = trace.digest()
    h2 = trace.digest()
    assert h1 == h2


def test_digest_excludes_observational_fields():
    psi = PsiDefinition(psi_type="test", name="digest")

    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t2 = datetime(2025, 1, 2, tzinfo=timezone.utc)
    kernel_a = _kernel_with_determinism(
        run_id="run-a",
        now_values=[t0, t1],
        perf_values=[1.0, 2.0],
    )
    kernel_b = _kernel_with_determinism(
        run_id="run-b",
        now_values=[t2, t2],
        perf_values=[5.0, 6.0],
    )

    trace_a = kernel_a.execute(psi=psi, task=lambda: "ok", metadata={"x": 1})
    trace_b = kernel_b.execute(psi=psi, task=lambda: "ok", metadata={"x": 2})

    assert trace_a.digest() == trace_b.digest()


def test_deterministic_mode_fixed_observables():
    psi = PsiDefinition(psi_type="test", name="deterministic")
    kernel = Kernel(deterministic_mode=True)

    trace = kernel.execute(psi=psi, task=lambda: "ok")

    assert trace.run_id == "deterministic"
    assert trace.runtime_ms == 0.0
    assert trace.started_at == datetime(1970, 1, 1, tzinfo=timezone.utc)
    assert trace.finished_at == datetime(1970, 1, 1, tzinfo=timezone.utc)


def test_invalid_input_is_normalized_and_task_not_called():
    counter = {"calls": 0}

    def task() -> None:
        counter["calls"] += 1

    kernel = Kernel()
    trace = kernel.execute(psi="not-psi", task=task)  # type: ignore[arg-type]

    assert counter["calls"] == 0
    assert trace.success is False
    assert trace.failure_code is FailureCode.INVALID_INPUT
