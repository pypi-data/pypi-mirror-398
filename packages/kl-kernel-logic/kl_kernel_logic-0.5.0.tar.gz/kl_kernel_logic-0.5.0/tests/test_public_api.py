# test_public_api.py
#
# Smoke tests for public API surface.
# Ensures the documented imports and basic usage work.

from kl_kernel_logic import (
    Kernel,
    PsiDefinition,
    CAEL,
    ExecutionTrace,
    CaelResult,
    FailureCode,
)


def test_psi_definition_creation() -> None:
    psi = PsiDefinition(psi_type="test", name="smoke")
    assert psi.psi_type == "test"
    assert psi.name == "smoke"


def test_kernel_instantiation() -> None:
    kernel = Kernel()
    assert kernel is not None


def test_kernel_execute_returns_execution_trace() -> None:
    kernel = Kernel()
    psi = PsiDefinition(psi_type="test", name="smoke")
    trace = kernel.execute(psi=psi, task=lambda: "ok")
    assert isinstance(trace, ExecutionTrace)


def test_cael_instantiation() -> None:
    kernel = Kernel()
    cael = CAEL(kernel=kernel)
    assert cael is not None


def test_cael_run_returns_cael_result() -> None:
    kernel = Kernel()
    cael = CAEL(kernel=kernel)
    psi = PsiDefinition(psi_type="test", name="smoke")
    result = cael.run([(psi, lambda: 1, {})])
    assert isinstance(result, CaelResult)


def test_execution_trace_fields() -> None:
    kernel = Kernel()
    psi = PsiDefinition(psi_type="test", name="fields")
    trace = kernel.execute(psi=psi, task=lambda: 42)

    assert hasattr(trace, "run_id")
    assert hasattr(trace, "psi")
    assert hasattr(trace, "started_at")
    assert hasattr(trace, "finished_at")
    assert hasattr(trace, "runtime_ms")
    assert hasattr(trace, "success")
    assert hasattr(trace, "output")
    assert hasattr(trace, "error")
    assert hasattr(trace, "metadata")
    assert hasattr(trace, "failure_code")
    assert hasattr(trace, "kernel_meta")


def test_cael_result_fields() -> None:
    kernel = Kernel()
    cael = CAEL(kernel=kernel)
    psi = PsiDefinition(psi_type="test", name="fields")
    result = cael.run([(psi, lambda: 1, {})])

    assert hasattr(result, "traces")
    assert hasattr(result, "final_output")
    assert hasattr(result, "success")
    assert hasattr(result, "failure_code")
    assert hasattr(result, "failure_message")

