# Tests for Kernel

from kl_kernel_logic import PsiDefinition, Kernel, FailureCode


def test_kernel_execute_success():
    psi = PsiDefinition(psi_type="test", name="echo")
    kernel = Kernel()

    trace = kernel.execute(psi=psi, task=lambda x: x.upper(), x="hello")

    assert trace.success is True
    assert trace.output == "HELLO"
    assert trace.error is None
    assert trace.failure_code is FailureCode.OK
    assert trace.runtime_ms >= 0.0


def test_kernel_execute_failure():
    psi = PsiDefinition(psi_type="test", name="fail")
    kernel = Kernel()

    def failing_task():
        raise ValueError("test error")

    trace = kernel.execute(psi=psi, task=failing_task)

    assert trace.success is False
    assert trace.output is None
    assert trace.error == "test error"
    assert trace.exception_type == "ValueError"
    assert trace.failure_code is FailureCode.TASK_EXCEPTION


def test_kernel_captures_psi():
    psi = PsiDefinition(psi_type="math", name="add")
    kernel = Kernel()

    trace = kernel.execute(psi=psi, task=lambda a, b: a + b, a=1, b=2)

    assert trace.psi.psi_type == "math"
    assert trace.psi.name == "add"


def test_kernel_passes_metadata():
    psi = PsiDefinition(psi_type="test", name="meta")
    kernel = Kernel()

    trace = kernel.execute(
        psi=psi,
        task=lambda: "ok",
        metadata={"key": "value"},
    )

    assert trace.metadata["key"] == "value"

