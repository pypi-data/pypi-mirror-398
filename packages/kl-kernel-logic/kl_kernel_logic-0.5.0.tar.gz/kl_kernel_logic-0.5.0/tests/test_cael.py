# Tests for CAEL

from kl_kernel_logic import PsiDefinition, Kernel, CAEL


def test_cael_run_single_step():
    psi = PsiDefinition(psi_type="test", name="single")
    cael = CAEL(kernel=Kernel())

    result = cael.run([
        (psi, lambda x: x * 2, {"x": 5}),
    ])

    assert result.success is True
    assert result.final_output == 10
    assert len(result.traces) == 1
    assert result.failure_code is None


def test_cael_run_multiple_steps():
    psi_a = PsiDefinition(psi_type="math", name="step_a")
    psi_b = PsiDefinition(psi_type="math", name="step_b")
    cael = CAEL(kernel=Kernel())

    result = cael.run([
        (psi_a, lambda x: x + 1, {"x": 5}),
        (psi_b, lambda x: x * 2, {"x": 6}),
    ])

    assert result.success is True
    assert result.final_output == 12
    assert len(result.traces) == 2
    assert result.failure_code is None


def test_cael_stops_on_failure():
    psi_a = PsiDefinition(psi_type="test", name="ok")
    psi_b = PsiDefinition(psi_type="test", name="fail")
    psi_c = PsiDefinition(psi_type="test", name="never")
    cael = CAEL(kernel=Kernel())

    def failing():
        raise RuntimeError("stop")

    result = cael.run([
        (psi_a, lambda: "ok", {}),
        (psi_b, failing, {}),
        (psi_c, lambda: "never reached", {}),
    ])

    assert result.success is False
    assert result.final_output is None
    assert len(result.traces) == 2  # third step not executed
    assert result.failure_code == "TASK_EXCEPTION"


def test_cael_validates_steps_before_execution():
    psi = PsiDefinition(psi_type="test", name="ok")
    cael = CAEL(kernel=Kernel())

    result = cael.run([
        (psi, "not-callable", {}),  # invalid task
    ])

    assert result.success is False
    assert result.final_output is None
    assert result.failure_code == "INVALID_STEP"
    assert result.traces == []
